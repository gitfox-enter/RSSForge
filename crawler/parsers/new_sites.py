#!/usr/bin/env python3
"""
New site parsers for RSSForge
果粉GoFans, Mergeek, 折送网

Author: RSSForge Team
Date: 2026-08-22
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from html.parser import HTMLParser
import urllib.request
import urllib.error
import ssl
import time


# ============================================================================
# HTML Parsers (标准库实现，无第三方依赖)
# ============================================================================

class DetailParser(HTMLParser):
    """解析文章详情页，提取标题和描述"""

    def __init__(self):
        super().__init__()
        self.reset_data()

    def reset_data(self):
        self.title = None
        self.description = None
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        if tag == 'meta':
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '')

            if name == 'description' or prop == 'og:description':
                self.description = content
            elif (name == 'title' or prop == 'og:title') and content and not self.title:
                self.title = content

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.current_tag == 'title' and not self.title:
            self.title = data

    def handle_endtag(self, tag):
        if tag == self.current_tag:
            self.current_tag = None


class LinkParser(HTMLParser):
    """提取页面所有链接"""

    def __init__(self):
        super().__init__()
        self.links = []
        self.current_tag = None
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

        if tag == 'a' and 'href' in self.current_attrs:
            self.links.append({
                'href': self.current_attrs['href'],
                'text': '',
            })

    def handle_data(self, data):
        if self.current_tag == 'a' and self.links:
            self.links[-1]['text'] += data.strip()


# ============================================================================
# HTTP 工具函数
# ============================================================================

def fetch_url(url: str, timeout: int = 25) -> str:
    """获取网页内容（SSL 跳过验证，适合内网/测试环境）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    )

    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read().decode('utf-8', errors='ignore')


def get_detail(url: str) -> Dict:
    """获取文章详情页的标题和描述"""
    try:
        html = fetch_url(url, timeout=15)
        parser = DetailParser()
        parser.feed(html)
        return {
            'title': parser.title,
            'description': parser.description,
        }
    except Exception as e:
        return {'title': None, 'description': None, 'error': str(e)}


# ============================================================================
# 站点 Parser
# ============================================================================

def parse_gofans_items(url: str, max_items: int = 20, max_detail: int = 15) -> List[Dict]:
    """
    果粉GoFans (gofans.cn) - Apple 软件限免/折扣

    Args:
        url: 站点URL (通常为首页)
        max_items: 最大返回条目数
        max_detail: 最大访问详情页数（控制请求频率）

    Returns:
        [{title, url, description, pub_date, author, tags}, ...]
    """
    try:
        html = fetch_url(url, timeout=30)
    except Exception as e:
        print(f"[GoFans] 获取页面失败: {e}")
        return []

    parser = LinkParser()
    parser.feed(html)

    items = []
    seen_urls = set()
    app_pattern = re.compile(r'^/app/[a-f0-9-]{36}$')

    # 提取所有应用链接
    app_links = []
    for link in parser.links:
        href = link.get('href', '')
        if app_pattern.match(href):
            app_links.append(href)

    # 去重并限制数量
    app_links = list(dict.fromkeys(app_links))[:max_detail]

    print(f"[GoFans] 找到 {len(app_links)} 个应用，正在提取详情...")

    for i, href in enumerate(app_links):
        full_url = f"https://gofans.cn{href}"

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        try:
            # 访问详情页获取标题
            detail = get_detail(full_url)
            title = detail.get('title') or f"Apple App - {href.split('/')[-1][:8]}"
            description = detail.get('description', '')

            # 清理标题（移除 " - 果粉GoFans" 后缀）
            if ' - ' in title:
                title = title.split(' - ')[0]

            items.append({
                'title': title,
                'url': full_url,
                'description': description[:200] if description else f"Apple 软件限免/折扣 - {title}",
                'pub_date': datetime.now().isoformat(),
                'author': 'GoFans',
                'tags': ['Apple', 'iOS', 'macOS', '限免', '折扣']
            })

            # 控制请求频率
            if i < len(app_links) - 1:
                time.sleep(0.3)

        except Exception as e:
            print(f"[GoFans] 获取详情失败 [{href}]: {e}")
            continue

    return items[:max_items]


def parse_mergeek_items(url: str, max_items: int = 30) -> List[Dict]:
    """
    Mergeek (mergeek.com) - iOS/macOS 软件限免

    Args:
        url: 站点URL (通常为 /zh/deals)
        max_items: 最大返回条目数

    Returns:
        [{title, url, description, pub_date, author, tags}, ...]
    """
    try:
        html = fetch_url(url, timeout=30)
    except Exception as e:
        print(f"[Mergeek] 获取页面失败: {e}")
        return []

    items = []
    seen_urls = set()

    # 提取 meta 信息
    detail_parser = DetailParser()
    detail_parser.feed(html)

    # 提取链接
    link_parser = LinkParser()
    link_parser.feed(html)

    # 寻找相关链接
    for link in link_parser.links:
        href = link.get('href', '')
        text = link.get('text', '').strip()

        if not href or not text or len(text) < 2:
            continue

        # 跳过无关链接
        skip_patterns = ['/search', '/user', '/static', '/assets', '.css', '.js', '/publish', '/ruby_store']
        if any(s in href for s in skip_patterns):
            continue

        # 只保留相关链接
        keywords = ['限免', '免费', '折扣', 'deal', 'free', 'app', 'ios', 'mac', 'deals', '精选', '独家']
        href_lower = href.lower()
        text_lower = text.lower()

        if any(k in text_lower or k in href_lower for k in keywords):
            full_url = f"https://mergeek.com{href}" if href.startswith('/') else href

            if full_url not in seen_urls:
                seen_urls.add(full_url)
                items.append({
                    'title': text,
                    'url': full_url,
                    'description': f"Mergeek 推荐 - {text}",
                    'pub_date': datetime.now().isoformat(),
                    'author': 'Mergeek',
                    'tags': ['iOS', 'macOS', '限免']
                })

    return items[:max_items]


def parse_zhesong_items(url: str, max_items: int = 30) -> List[Dict]:
    """
    折送网 (zhesong.com) - 全网线报/折扣聚合

    Args:
        url: 站点URL (通常为 /listxb.php)
        max_items: 最大返回条目数

    Returns:
        [{title, url, description, pub_date, author, tags}, ...]
    """
    try:
        html = fetch_url(url, timeout=30)
    except Exception as e:
        print(f"[折送网] 获取页面失败: {e}")
        return []

    parser = LinkParser()
    parser.feed(html)

    items = []
    seen_urls = set()

    # 提取线报链接
    for link in parser.links:
        href = link.get('href', '')
        text = link.get('text', '').strip()

        if not href or not text or len(text) < 3:
            continue

        # 匹配线报相关链接
        is_xb = (
            href.endswith('.php') or
            '/xianbao' in href or
            '/youhui' in href or
            '线报' in text or
            '优惠' in text
        )

        if is_xb:
            if href.startswith('/'):
                full_url = f"https://zhesong.com{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = f"https://zhesong.com/{href}"

            if full_url not in seen_urls:
                seen_urls.add(full_url)
                items.append({
                    'title': text,
                    'url': full_url,
                    'description': f"线报/优惠 - {text}",
                    'pub_date': datetime.now().isoformat(),
                    'author': '折送网',
                    'tags': ['线报', '折扣', '羊毛']
                })

    return items[:max_items]


# ============================================================================
# 注册到 PARSER_REGISTRY
# ============================================================================

# 在 crawler/parsers/core.py 中添加:
# from crawler.parsers.new_sites import parse_gofans_items, parse_mergeek_items, parse_zhesong_items
#
# PARSER_REGISTRY = {
#     ...
#     'gofans.cn':        (parse_gofans_items,    None),
#     'mergeek.com':      (parse_mergeek_items,   None),
#     'zhesong.com':      (parse_zhesong_items,   None),
# }


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("RSSForge 新源 Parser 测试")
    print("="*60)

    test_cases = [
        ('果粉GoFans', 'https://gofans.cn/', parse_gofans_items),
        ('Mergeek', 'https://mergeek.com/zh/deals', parse_mergeek_items),
        ('折送网', 'https://zhesong.com/listxb.php', parse_zhesong_items),
    ]

    for name, url, parser in test_cases:
        print(f"\n测试 {name}...")
        start = time.time()
        items = parser(url)
        elapsed = time.time() - start

        print(f"✅ 找到 {len(items)} 条内容 ({elapsed:.1f}s)")
        for i, item in enumerate(items[:3], 1):
            print(f"  {i}. {item['title'][:50]}")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
