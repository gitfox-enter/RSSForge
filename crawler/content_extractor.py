# -*- coding: utf-8 -*-
"""
Content Extractor - 智能文章内容提取模块

支持：
- 自定义 CSS 选择器（从 sites.yaml 的 content_selector 配置）
- 自定义提取函数（从 sites.yaml 的 content_extractor 配置）
- 内置通用提取器（基于文本密度算法）
"""

import re
import logging
import hashlib
from typing import Any, Callable, Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger('content_extractor')

# ============================================================
# BeautifulSoup 懒加载
# ============================================================

BeautifulSoup = None
SoupStrainer = None


def _ensure_bs():
    """Lazy import BeautifulSoup on first use."""
    global BeautifulSoup, SoupStrainer
    if BeautifulSoup is None:
        try:
            from bs4 import BeautifulSoup as BS, SoupStrainer
            BeautifulSoup = BS
            return True
        except ImportError:
            logger.warning("content_extractor 需要 beautifulsoup4: pip install beautifulsoup4")
            return False
    return True


# ============================================================
# 全局配置缓存（避免每次抓取都重新加载 YAML）
# ============================================================

_SITE_CONFIG_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_site_configs() -> Dict[str, Dict[str, Any]]:
    """从 sites.yaml 加载所有站点的 content 配置。"""
    if _SITE_CONFIG_CACHE:
        return _SITE_CONFIG_CACHE

    try:
        import yaml
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sites.yaml"
        )
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("sites.yaml 加载失败: %s", e)
        return {}

    # 构建 URL → 配置映射
    sites = data.get('sites', [])
    for site in sites:
        url = site.get('url', '')
        if url:
            _SITE_CONFIG_CACHE[url] = {
                'selector': site.get('content_selector'),
                'extractor': site.get('content_extractor'),
            }

    return _SITE_CONFIG_CACHE


def _get_site_config(url: str) -> Dict[str, Any]:
    """获取站点的内容提取配置。"""
    configs = _load_site_configs()
    return configs.get(url, {})


# ============================================================
# 自定义提取器注册表
# ============================================================

_CONTENT_EXTRACTORS: Dict[str, Callable] = {}


def register_extractor(domain: str, func: Callable):
    """注册自定义内容提取器。

    Args:
        domain: 匹配的域名（如 'appinn.com'）
        func: 提取函数，签名为 func(url: str) -> Dict[str, str]
              返回 {'content': html_str, 'title': str, 'author': str, 'tags': list}
    """
    _CONTENT_EXTRACTORS[domain.lower()] = func


def _get_extractor(url: str) -> Optional[Callable]:
    """根据 URL 获取对应的自定义提取器。"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname or ''
        # 先精确匹配
        if host in _CONTENT_EXTRACTORS:
            return _CONTENT_EXTRACTORS[host]
        # 再尝试根域名匹配
        parts = host.split('.')
        if len(parts) >= 2:
            root_domain = '.'.join(parts[-2:])
            if root_domain in _CONTENT_EXTRACTORS:
                return _CONTENT_EXTRACTORS[root_domain]
    except Exception:
        pass
    return None


# ============================================================
# 内置通用提取器
# ============================================================


def _extract_by_selector(url: str, selector_config: Dict) -> Dict[str, str]:
    """使用 CSS 选择器提取内容。

    Args:
        url: 文章 URL（用于相对路径转换）
        selector_config: 包含 'content' (CSS选择器字符串) 的配置字典

    Returns:
        {'content': html_str, 'title': str, 'author': str, 'tags': list}
    """
    if not BeautifulSoup:
        raise ImportError("BeautifulSoup is required")

    import requests
    from bs4 import Comment
    from urllib.parse import urljoin

    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; RSSForge/1.0; +https://github.com/gitfox-enter/rssforge)',
        })
        response.raise_for_status()
        html = response.text
    except Exception as e:
        logger.warning("请求失败 [%s]: %s", url, e)
        return {'content': '', 'title': '', 'author': '', 'tags': []}

    soup = BeautifulSoup(html, 'html.parser')

    selector = selector_config.get('content', '')
    if not selector:
        return {'content': '', 'title': '', 'author': '', 'tags': []}

    # 提取标题
    title = ''
    title_tag = soup.find('meta', property='og:title') or soup.find('title')
    if title_tag:
        title = title_tag.get('content', title_tag.get_text(strip=True)) if hasattr(title_tag, 'get') else str(title_tag)

    # 使用选择器提取内容
    content_el = soup.select_one(selector)
    if not content_el:
        return {'content': '', 'title': title, 'author': '', 'tags': []}

    # 清理无用标签
    for tag in content_el.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 'aside', 'footer', 'header', 'form', 'button']):
        tag.decompose()
        # 过滤友链/板块分类区域
        for noise in content_el.select('.friend-link, .links-box, .link-box, .blogroll, .roll-links, .category-list, .sidebar-links, .friendly-link, .friendlink, .links, .交换链接, .友情链接, [class*=links], [class*=link-box], [class*=friend-link], [class*=blogroll], [class*=friendlink], [class*=roll-links], aside, .widget, .sidebar, .related-posts, .similar-posts'):
            noise.decompose()

    # 移除注释
    for comment in content_el.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 处理相对 URL
    for img in content_el.find_all('img'):
        src = img.get('src', '')
        if src:
            img['src'] = urljoin(url, src)
    for a in content_el.find_all('a'):
        href = a.get('href', '')
        if href:
            a['href'] = urljoin(url, href)

    return {
        'content': str(content_el),
        'title': title,
        'author': '',
        'tags': [],
    }


def _extract_generic(url: str) -> Dict[str, str]:
    """通用内容提取逻辑 - 增强版。

    策略:
    1. 先尝试常见的 meta og:description 描述
    2. 尝试多种常见的内容容器选择器
    3. 使用文本密度算法自动检测正文区域
    4. 提取 meta 信息作为补充
    """
    if not BeautifulSoup:
        raise ImportError("BeautifulSoup is required")

    import requests
    from bs4 import Comment
    from urllib.parse import urljoin

    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; RSSForge/1.0; +https://github.com/gitfox-enter/rssforge)',
        })
        response.raise_for_status()
        html = response.text
    except Exception as e:
        logger.warning("请求失败 [%s]: %s", url, e)
        return {'content': '', 'title': '', 'author': '', 'tags': []}

    soup = BeautifulSoup(html, 'html.parser')

    result = {
        'content': '',
        'title': '',
        'author': '',
        'tags': [],
    }

    # 0. 提取 meta 信息（用于标题和描述）
    # 标题
    title = ''
    title_tag = soup.find('meta', property='og:title') or \
                soup.find('meta', attrs={'name': 'title'}) or \
                soup.find('title')
    if title_tag:
        title = title_tag.get('content', title_tag.get_text(strip=True)) if hasattr(title_tag, 'get') else str(title_tag)

    # 描述
    description = ''
    desc_tag = soup.find('meta', property='og:description') or \
                soup.find('meta', attrs={'name': 'description'}) or \
                soup.find('meta', attrs={'name': 'Description'})
    if desc_tag:
        description = desc_tag.get('content', '')

    # 1. 尝试多种常见的内容容器选择器
    content_selectors = [
        # WordPress 常用
        'article .entry-content',
        '.post-content',
        '.entry-content',
        '.article-content',
        '.single-content',
        '.post-body',
        '.article-body',
        # 通用内容容器
        'article',
        'main article',
        '[role="main"]',
        'main',
        '.content',
        '.post',
        '.article',
        '#content',
        '#post-content',
        '#main-content',
        # 新闻/博客通用
        '.story-body',
        '.article-body',
        '.post-article',
    ]

    content_el = None
    for selector in content_selectors:
        content_el = soup.select_one(selector)
        if content_el and len(content_el.get_text(strip=True)) > 200:
            break

    # 2. 如果选择器没找到，使用文本密度算法
    if not content_el or len(content_el.get_text(strip=True)) < 100:
        content_el = _detect_content_by_density(soup)

    if content_el:
        # 清理无用标签
        for tag in content_el.find_all(['script', 'style', 'noscript', 'iframe', 'nav', 'aside', 'footer', 'header', 'form', 'input', 'button', 'svg', 'canvas']):
            tag.decompose()

        # 移除 comments
        for comment in content_el.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 处理相对 URL
        for img in content_el.find_all('img'):
            src = img.get('src', '')
            if src:
                if src.startswith('//'):
                    img['src'] = 'https:' + src
                elif src.startswith('/'):
                    img['src'] = urljoin(url, src)
                elif not src.startswith('http'):
                    img['src'] = urljoin(url, src)

        for a in content_el.find_all('a'):
            href = a.get('href', '')
            if href:
                if href.startswith('//'):
                    a['href'] = 'https:' + href
                elif href.startswith('/'):
                    a['href'] = urljoin(url, href)
                elif not href.startswith('http'):
                    a['href'] = urljoin(url, href)

        result['content'] = str(content_el)

    # 如果没有提取到正文，使用 meta description 作为 fallback
    if not result['content'] and description:
        result['content'] = f'<p>{description}</p>'

    result['title'] = title
    return result


def _detect_content_by_density(soup: Any) -> Any:
    """使用文本密度算法自动检测正文区域。

    策略:
    - 遍历所有块级元素
    - 计算每个元素的文本密度（文本长度 / (文本长度 + 标签长度)）
    - 选取密度最高且文本量足够的元素
    """
    if not BeautifulSoup:
        return None

    # 候选块级元素标签
    block_tags = ['div', 'section', 'article', 'main', 'td', 'li']

    candidates = []
    for tag in block_tags:
        for el in soup.find_all(tag):
            # 跳过太小的元素
            text = el.get_text(strip=True)
            if len(text) < 200:
                continue

            # 跳过明显不是正文的元素
            for skip_class in ['sidebar', 'nav', 'footer', 'header', 'menu', 'comment', 'advertisement', 'ad-', 'related', 'popular']:
                class_attr = el.get('class', [])
                if any(skip_class in str(c).lower() for c in class_attr):
                    break
            else:
                # 计算文本密度
                html_len = len(str(el))
                text_len = len(text)
                if html_len > 0:
                    density = text_len / html_len
                    # 考虑文本绝对长度作为加权
                    score = density * (min(text_len, 5000) / 1000)
                    if score > 0.5:
                        candidates.append((score, el))

    if candidates:
        # 返回得分最高的元素
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return None


# ============================================================
# 主提取函数
# ============================================================


def extract_content(url: str) -> Dict[str, str]:
    """提取文章内容的主入口。

    优先级:
    1. 自定义提取器（通过 register_extractor 注册）
    2. sites.yaml 中的 content_selector 配置
    3. sites.yaml 中的 content_extractor 配置（函数名）
    4. 内置通用提取器（文本密度算法）

    Args:
        url: 文章 URL

    Returns:
        {'content': html_str, 'title': str, 'author': str, 'tags': list}
        content 为空字符串表示提取失败
    """
    if not _ensure_bs():
        return {'content': '', 'title': '', 'author': '', 'tags': []}

    # 1. 尝试自定义提取器
    extractor = _get_extractor(url)
    if extractor:
        try:
            result = extractor(url)
            if result and result.get('content'):
                logger.info("使用自定义提取器 [%s]", url)
                return result
        except Exception as e:
            logger.warning("自定义提取器失败 [%s]: %s", url, e)

    # 2. 尝试 sites.yaml 中的选择器配置
    site_config = _get_site_config(url)
    if site_config.get('selector'):
        try:
            result = _extract_by_selector(url, {'content': site_config['selector']})
            if result and result.get('content'):
                logger.info("使用选择器提取 [%s]: %s", url, site_config['selector'])
                return result
        except Exception as e:
            logger.warning("选择器提取失败 [%s]: %s", url, e)

    # 3. 尝试 sites.yaml 中的自定义函数配置
    extractor_name = site_config.get('extractor')
    if extractor_name:
        func = _CONTENT_EXTRACTORS.get(extractor_name)
        if func:
            try:
                result = func(url)
                if result and result.get('content'):
                    logger.info("使用自定义函数提取 [%s]: %s", url, extractor_name)
                    return result
            except Exception as e:
                logger.warning("自定义函数提取失败 [%s]: %s", url, e)

    # 4. 使用通用提取器
    try:
        result = _extract_generic(url)
        if result and result.get('content'):
            logger.info("使用通用提取器 [%s]", url)
            return result
    except Exception as e:
        logger.warning("通用提取失败 [%s]: %s", url, e)

    return {'content': '', 'title': '', 'author': '', 'tags': []}


# ============================================================
# 注册内置提取器（可在 crawler/parsers/ 中导入并扩展）
# ============================================================

def _register_builtin_extractors():
    """注册内置的站点专用提取器。"""
    # 示例：可在此添加更多站点的提取器
    pass


# ============================================================
# 其他工具函数
# ============================================================

def get_content_hash(content: str) -> str:
    """计算内容的 MD5 哈希（用于去重）。"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def clean_html_content(html: str) -> str:
    """清理 HTML 内容，移除不必要的标签和属性。"""
    if not BeautifulSoup:
        return html

    soup = BeautifulSoup(html, 'html.parser')

    # 移除危险的标签
    for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'form', 'input', 'button']):
        tag.decompose()

    # 移除危险属性
    dangerous_attrs = ['onclick', 'onerror', 'onload', 'onmouseover', 'onfocus', 'onblur']
    for tag in soup.find_all(True):
        for attr in dangerous_attrs:
            if tag.has_attr(attr):
                del tag[attr]

    return str(soup)


# 注册内置提取器
_register_builtin_extractors()
