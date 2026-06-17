#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS/Atom Feed 生成器 — 生成全量聚合 feed + 每站独立 feed。

输出:
  feed.xml          — 全量聚合（所有来源）
  feeds/线报酷.xml   — 按来源拆分的独立 feed
  feeds/白菜哦.xml   — ...
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from common import (
    get_beijing_time,
    load_items_db,
    ITEMS_DB_FILE,
)

# XML 1.0 不允许的控制字符和 Unicode 代理对
_INVALID_XML_RE = re.compile(
    '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufffe\uffff]'
)

# ============================================================
# 配置
# ============================================================

SITE_URL = "https://gitfox-enter.github.io/site-update-monitor/"
FEEDS_DIR = "feeds"
FEED_TITLE = "线报聚合 - 实时监控全网羊毛线报"
FEED_DESCRIPTION = "自动聚合全网羊毛线报、优惠信息、活动促销，实时更新"

# 来源名 → 安全文件名映射
def _safe_filename(name: str) -> str:
    """将来源名称转为安全的文件名。"""
    return re.sub(r'[^\w\u4e00-\u9fff]', '', name)


def _sanitize_xml(text: str) -> str:
    """Remove characters invalid in XML 1.0."""
    if not text:
        return text
    return _INVALID_XML_RE.sub('', text)


def _to_iso8601(time_str: str) -> str:
    """Convert 'YYYY-MM-DD HH:MM:SS' to ISO 8601."""
    if not time_str:
        return datetime.now(timezone(timedelta(hours=8))).isoformat()
    try:
        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
        return dt.isoformat()
    except (ValueError, TypeError):
        return datetime.now(timezone(timedelta(hours=8))).isoformat()


def _build_atom_feed(items: List[Dict], title: str, feed_url: str,
                     description: str = "", updated_at: str = "") -> ET.Element:
    """构建 Atom feed 根元素（不写文件）。"""
    NS = 'http://www.w3.org/2005/Atom'
    ET.register_namespace('', NS)

    root = ET.Element(f'{{{NS}}}feed')

    ET.SubElement(root, f'{{{NS}}}title').text = _sanitize_xml(title)
    if description:
        ET.SubElement(root, f'{{{NS}}}subtitle').text = _sanitize_xml(description)
    ET.SubElement(root, f'{{{NS}}}link', href=SITE_URL, rel='alternate')
    ET.SubElement(root, f'{{{NS}}}link', href=feed_url, rel='self', type='application/atom+xml')
    ET.SubElement(root, f'{{{NS}}}id').text = feed_url
    ET.SubElement(root, f'{{{NS}}}updated').text = _to_iso8601(updated_at)
    ET.SubElement(root, f'{{{NS}}}generator', uri='https://github.com/gitfox-enter/site-update-monitor').text = 'site-update-monitor'

    author = ET.SubElement(root, f'{{{NS}}}author')
    ET.SubElement(author, f'{{{NS}}}name').text = '线报聚合'

    for item in items:
        entry = ET.SubElement(root, f'{{{NS}}}entry')

        title_text = _sanitize_xml(item.get('text', '无标题'))
        title_el = ET.SubElement(entry, f'{{{NS}}}title')
        title_el.text = title_text
        title_el.set('type', 'text')

        url = _sanitize_xml(item.get('url', ''))
        ET.SubElement(entry, f'{{{NS}}}link', href=url, rel='alternate')
        ET.SubElement(entry, f'{{{NS}}}id').text = url or f"tag:gitfox-enter,{updated_at[:10]}:{hash(title_text)}"

        time_str = item.get('time', updated_at)
        ET.SubElement(entry, f'{{{NS}}}updated').text = _to_iso8601(time_str)
        ET.SubElement(entry, f'{{{NS}}}published').text = _to_iso8601(time_str)

        source = _sanitize_xml(item.get('source', ''))
        category = _sanitize_xml(item.get('category', ''))
        content_parts = []
        if source:
            content_parts.append(f"来源: {source}")
        if category:
            content_parts.append(f"分类: {category}")
        content_parts.append(f"链接: {url}")
        content_text = ' | '.join(content_parts)

        content_el = ET.SubElement(entry, f'{{{NS}}}content')
        content_el.text = _sanitize_xml(content_text)
        content_el.set('type', 'text')

        if category:
            ET.SubElement(entry, f'{{{NS}}}category', term=category)

    return root


def _write_feed(root: ET.Element, output_path: str) -> bool:
    """将 Atom feed 写入文件（原子写入）。"""
    tmp_path = output_path + '.tmp'
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            tree.write(f, encoding='unicode', xml_declaration=False)
        os.replace(tmp_path, output_path)
        return True
    except Exception as e:
        print(f"写入 feed 失败 {output_path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def generate_all_feeds() -> Dict[str, int]:
    """生成全量聚合 feed + 每站独立 feed。

    Returns:
        dict: {'total': N, 'per_site': {name: count}, 'feeds_generated': M}
    """
    db = load_items_db()
    items = db.get('items', [])
    updated_at = db.get('updated_at', '')

    if not items:
        print("无数据，跳过 feed 生成")
        return {'total': 0, 'per_site': {}, 'feeds_generated': 0}

    stats = {'total': len(items), 'per_site': {}, 'feeds_generated': 0}

    # 1. 全量聚合 feed
    all_feed_url = SITE_URL + "feed.xml"
    root = _build_atom_feed(items, FEED_TITLE, all_feed_url, FEED_DESCRIPTION, updated_at)
    if _write_feed(root, "feed.xml"):
        stats['feeds_generated'] += 1
        print(f"全量 feed: {len(items)} 条")

    # 2. 按来源拆分的 per-site feed
    os.makedirs(FEEDS_DIR, exist_ok=True)

    by_source: Dict[str, List[Dict]] = {}
    for item in items:
        source = item.get('source', '未知')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)

    for source, source_items in by_source.items():
        safe_name = _safe_filename(source)
        filename = f"{FEEDS_DIR}/{safe_name}.xml"
        feed_url = SITE_URL + filename
        title = f"{source} - 线报聚合"
        desc = f"来自 {source} 的线报更新"

        root = _build_atom_feed(source_items, title, feed_url, desc, updated_at)
        if _write_feed(root, filename):
            stats['feeds_generated'] += 1
            stats['per_site'][source] = len(source_items)

    print(f"按来源生成 {len(by_source)} 个独立 feed")
    return stats


if __name__ == '__main__':
    result = generate_all_feeds()
    if result['total'] > 0:
        print(f"完成: {result['total']} 条数据, {result['feeds_generated']} 个 feed 文件")
    else:
        print("无数据，未生成 feed")
