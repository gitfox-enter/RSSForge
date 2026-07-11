# -*- coding: utf-8 -*-
"""RSS/Atom feed parsers and special content extractors."""

import asyncio
import logging
import re
import time
import random
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import warnings
try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass

import html as html_mod
import aiohttp
import requests

from crawler.parsers._utils import (
    _has_chinese, _is_valid_text, _add_item, _make_skip_set, COMMON_SKIP_WORDS,
)
from crawler.storage import get_random_ua
from crawler.config import REQUEST_TIMEOUT

logger = logging.getLogger('crawl')

def parse_rss_feed(content_bytes: bytes, base_url: str) -> List[Dict[str, str]]:
    """增强版 RSS/Atom Feed 解析器

    提取所有重要字段：
    - title: 文章标题
    - url: 文章链接
    - summary: 文章摘要/描述（从 HTML 中提取纯文本）
    - time: 发布时间
    - category: 分类
    - author: 作者

    Args:
        content_bytes: RSS/Atom feed 的原始字节内容
        base_url: feed 的基础 URL（用于备选）

    Returns:
        解析后的条目列表，每个条目是一个字典
    """
    items: List[Dict[str, str]] = []

    # 预处理：修复常见的 XML 格式问题
    text = content_bytes.decode('utf-8', errors='replace')
    # 去除 BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    # 截断 </rss> 之后的内容
    rss_end = text.rfind('</rss>')
    if rss_end > 0:
        text = text[:rss_end + len('</rss>')]
    # 同样处理 </feed>（Atom）
    feed_end = text.rfind('</feed>')
    if feed_end > 0:
        if rss_end < 0 or feed_end > rss_end:
            text = text[:feed_end + len('</feed>')]

    try:
        root = ET.fromstring(text.encode('utf-8'))

        # 检测格式：RSS 2.0 或 Atom
        if root.tag == 'rss' or root.find('.//item') is not None:
            # RSS 2.0
            items = _parse_rss2_items(root)
        elif root.tag.endswith('}feed') or '{http://www.w3.org/2005/Atom}' in root.tag or root.find('.//{http://www.w3.org/2005/Atom}entry') is not None:
            # Atom
            items = _parse_atom_items(root)

    except ET.ParseError as e:
        # 解析失败，尝试用 BeautifulSoup 兜底
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(text, 'html.parser')
                for item in soup.find_all('item') or soup.find_all('entry'):
                    title_el = item.find('title')
                    title = title_el.get_text(strip=True) if title_el else ''
                    if not title:
                        continue

                    link_el = item.find('link')
                    link = ''
                    if link_el:
                        link = link_el.get('href', '') or (link_el.get_text(strip=True) if link_el.get_text(strip=True) else '')
                    if not link:
                        link = base_url

                    # 提取描述
                    desc_el = item.find('description') or item.find('summary') or item.find('content')
                    summary = ''
                    if desc_el and desc_el.get_text(strip=True):
                        plain_text = _strip_html(desc_el.get_text())
                        summary = plain_text[:500] if plain_text else ''

                    item_dict = {'text': title, 'url': link}
                    if summary:
                        item_dict['summary'] = summary
                    items.append(item_dict)
            except Exception:
                pass

    # 限制返回数量
    return items[:30]


def _strip_html(html_text: str) -> str:
    """从 HTML 中提取纯文本，移除标签并合并空格"""
    if not html_text:
        return ''
    text = re.sub(r'<[^>]+>', '', html_text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _parse_rss2_items(root) -> list:
    """解析 RSS 2.0 格式"""
    items = []
    seen = set()

    for item in root.findall('.//item'):
        title_el = item.find('title')
        title = ''
        if title_el is not None and title_el.text:
            title = title_el.text.strip()

        if not title or title in seen:
            continue
        seen.add(title)

        link_el = item.find('link')
        link = ''
        if link_el is not None and link_el.text:
            link = link_el.text.strip()

        # 提取 description/summary
        desc_el = item.find('description')
        summary = ''
        if desc_el is not None and desc_el.text:
            raw_desc = desc_el.text
            plain_text = _strip_html(raw_desc)
            summary = plain_text[:500] if plain_text else ''
            if len(plain_text) < 20 and raw_desc:
                summary = raw_desc[:1000]

        # 提取 pubDate
        pub_el = item.find('pubDate')
        pub_date = ''
        if pub_el is not None and pub_el.text:
            pub_date = pub_el.text.strip()

        # 提取 category
        cat_el = item.find('category')
        category = ''
        if cat_el is not None and cat_el.text:
            category = cat_el.text.strip()

        # 提取 author
        author_el = item.find('author') or item.find('{http://purl.org/dc/elements/1.1/}creator')
        author = ''
        if author_el is not None and author_el.text:
            author = author_el.text.strip()

        item_dict = {'text': title, 'url': link}
        if summary:
            item_dict['summary'] = summary
        if pub_date:
            item_dict['time'] = pub_date
        if category:
            item_dict['category'] = category
        if author:
            item_dict['author'] = author

        items.append(item_dict)

    return items


def _parse_atom_items(root) -> list:
    """解析 Atom 格式"""
    items = []
    seen = set()

    ATOM_NS = 'http://www.w3.org/2005/Atom'

    for entry in root.findall(f'.//{{{ATOM_NS}}}entry'):
        title_el = entry.find(f'{{{ATOM_NS}}}title')
        title = ''
        if title_el is not None and title_el.text:
            title = title_el.text.strip()

        if not title or title in seen:
            continue
        seen.add(title)

        # 提取 link
        link = ''
        for link_el in entry.findall(f'{{{ATOM_NS}}}link'):
            rel = link_el.get('rel', 'alternate')
            if rel == 'alternate' or rel == '':
                href = link_el.get('href', '')
                if href:
                    link = href
                    break
        if not link:
            link_el = entry.find(f'{{{ATOM_NS}}}link')
            if link_el is not None:
                link = link_el.get('href', '')

        # 提取 summary/content
        summary = ''
        for content_el in [entry.find(f'{{{ATOM_NS}}}summary'), entry.find(f'{{{ATOM_NS}}}content')]:
            if content_el is not None and content_el.text:
                raw_text = content_el.text
                plain_text = _strip_html(raw_text)
                if len(plain_text) > 10:
                    summary = plain_text[:500]
                    break
                elif raw_text:
                    summary = raw_text[:1000]
                    break

        # 提取 published/updated
        pub_date = ''
        for time_el in [entry.find(f'{{{ATOM_NS}}}published'), entry.find(f'{{{ATOM_NS}}}updated')]:
            if time_el is not None and time_el.text:
                pub_date = time_el.text.strip()
                break

        # 提取 category
        category = ''
        cat_el = entry.find(f'{{{ATOM_NS}}}category')
        if cat_el is not None:
            term = cat_el.get('term', '')
            if term:
                category = term
            elif cat_el.text:
                category = cat_el.text.strip()

        # 提取 author
        author = ''
        author_el = entry.find(f'{{{ATOM_NS}}}author')
        if author_el is not None:
            name_el = author_el.find(f'{{{ATOM_NS}}}name')
            if name_el is not None and name_el.text:
                author = name_el.text.strip()

        item_dict = {'text': title, 'url': link}
        if summary:
            item_dict['summary'] = summary
        if pub_date:
            item_dict['time'] = pub_date
        if category:
            item_dict['category'] = category
        if author:
            item_dict['author'] = author

        items.append(item_dict)

    return items

