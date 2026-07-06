# -*- coding: utf-8 -*-
"""Auto-extracted parser module from parsers.py."""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import warnings
try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass

from crawler.parsers._utils import (
    _has_chinese, _is_valid_text, _add_item, _make_skip_set, COMMON_SKIP_WORDS,
)

logger = logging.getLogger('crawl')

def parse_discuz_items(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """Discuz论坛 - 结构化条目提取

    兼容两种 URL 格式：
    - 绝对路径：/thread-4409-1-1.html
    - 相对路径：thread-4409-1-1.html（Discuz 默认伪静态）
    """
    items: List[Dict[str, str]] = []
    seen: Set[str] = set()
    # 主选择器：覆盖常见 Discuz 列表结构 + 通用 thread- 链接
    for a in soup.select('.threadlist .t a, .tl .t a, #threadlist .t a, '
                         '.threadlist tr td a.xst, .threadlist tr td a, a[href*="thread-"]'):
        text = a.get_text(strip=True)
        href = a.get('href', '').strip()
        if not text or len(text) < 3 or text in seen:
            continue
        # 接受绝对 (/thread-...) 和相对 (thread-\d+...) 两种 Discuz 链接
        if '/thread-' not in href and not re.search(r'thread-\d+', href):
            continue
        # 相对 URL 必须用 urljoin 补全，否则不会被加入
        if not href.startswith('http'):
            href = urljoin(base_url, href)
        if href.startswith('http'):
            seen.add(text)
            items.append({'text': text, 'url': href})
    if not items:
        for tr in soup.select('.forum tbody tr, table tbody tr'):
            for a in tr.select('a'):
                text = a.get_text(strip=True)
                href = a.get('href', '').strip()
                if text and len(text) > 3 and text not in seen:
                    if '/thread-' in href or re.search(r'thread-\d+', href):
                        if not href.startswith('http'):
                            href = urljoin(base_url, href)
                        if href.startswith('http'):
                            seen.add(text)
                            items.append({'text': text, 'url': href})
                            break
    return items[:30]




def parse_douban_group_items(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """豆瓣小组 - 提取讨论帖子条目。

    帖子列表使用 table.olt，每行 tr 中 td.title a 包含帖子标题。
    链接格式为 douban.com/group/topic/{id}/。
    """
    items: List[Dict[str, str]] = []
    seen: Set[str] = set()

    # 策略1：精确选择器 - table.olt 中的帖子标题
    for a in soup.select('table.olt td.title a'):
        href = a.get('href', '').strip()
        # 优先使用 title 属性（完整标题），其次使用文本内容
        text = a.get('title', '').strip() or a.get_text(strip=True)
        if not _is_valid_text(text, min_len=3, max_len=150):
            continue
        if not re.search(r'/group/topic/\d+', href):
            continue
        if text in seen:
            continue
        seen.add(text)
        if href.startswith('/'):
            href = urljoin(base_url, href)
        # 清理 URL 中的查询参数
        href = re.sub(r'\?_spm_id=[^&]*', '', href)
        items.append({'text': text, 'url': href})

    # 策略2：通用兜底 - 匹配所有 group/topic/{id} 链接
    if len(items) < 3:
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').strip()
            text = a.get('title', '').strip() or a.get_text(strip=True)
            if not _is_valid_text(text, min_len=3, max_len=150):
                continue
            if not re.search(r'douban\.com/group/topic/\d+', href):
                continue
            if text in seen:
                continue
            skip_words = _make_skip_set('加入小组')
            if any(w in text for w in skip_words):
                continue
            seen.add(text)
            href = re.sub(r'\?_spm_id=[^&]*', '', href)
            items.append({'text': text, 'url': href})

    return items[:50]


# ---------------------------------------------------------------------------
# 7. haodanku.com  (好单库)
# ---------------------------------------------------------------------------




