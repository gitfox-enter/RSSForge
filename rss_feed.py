#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS/Atom Feed 生成器 — 为每个订阅站点生成独立 feed。

功能:
  - 为 sites.yaml 中配置的每个站点生成独立 feed
  - 自动从网站获取真实 favicon 并缓存到 public/icons/
  - 不生成主聚合 feed.xml（仅 individual feeds + unified OPML）
"""

import json
import os
import re
import hashlib
from urllib.parse import urlparse
try:
    import httpx
except ImportError:
    httpx = None
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from common import (
    get_beijing_time,
    load_items_db,
    ITEMS_DB_FILE,
    slugify,
    SITE_URL_BASE,
    fetch_site_favicon,
)

# 导入站点配置
try:
    from crawler.config import (
        SOURCE_NAME_MAP, 
        get_source_name,
        SITE_INTERVALS,
        get_site_tier,
    )
except ImportError:
    SOURCE_NAME_MAP = {}
    SITE_INTERVALS = {}
    get_source_name = lambda url: url
    get_site_tier = lambda url: 'high'

# XML 1.0 不允许的控制字符和 Unicode 代理对
_INVALID_XML_RE = re.compile(
    '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ud800-\udfff\ufffe\uffff]'
)

# ============================================================
# 配置
# ============================================================

SITE_URL = SITE_URL_BASE  # fix #17: 统一从 common.py 获取
FEEDS_DIR = "docs/feeds"  # 文件系统输出目录（直接在 docs/ 下供 GitHub Pages 部署）
FEEDS_URL_PATH = "feeds"  # URL 路径（GitHub Pages 部署 docs/ 后，feeds/ 直接可访问）
FEED_TITLE = "RSSForge"
FEED_DESCRIPTION = "基于 GitHub Actions 的免费 RSS 订阅源生成器"
ICONS_DIR = "docs/icons"
ICONS_URL_PATH = "icons"  # 部署后 URL 路径


# ============================================================
# 工具函数
# ============================================================

def _safe_filename(name: str) -> str:
    """将来源名称转为 ASCII 安全的文件名 (fix #9)."""
    return slugify(name)


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


def _interval_to_update_period(interval_min: int) -> str:
    """Convert interval to sy:updatePeriod."""
    if interval_min <= 60:
        return 'hourly'
    return 'daily'


def _interval_to_update_frequency(interval_min: int) -> int:
    """Convert interval to sy:updateFrequency."""
    if interval_min <= 15:
        return 4
    elif interval_min <= 30:
        return 2
    elif interval_min <= 60:
        return 1
    elif interval_min <= 360:
        return 24 * 60 // interval_min
    return 1


def _compute_items_hash(items: List[Dict]) -> str:
    """计算站点条目列表的哈希值，用于增量生成判断 (#36).

    基于条目的 URL + time + text 生成 MD5，任何字段变化都会导致哈希变化。
    """
    h = hashlib.md5()
    for item in sorted(items, key=lambda x: x.get('url', '')):
        h.update(item.get('url', '').encode('utf-8'))
        h.update(b'|')
        h.update(item.get('time', '').encode('utf-8'))
        h.update(b'|')
        h.update(item.get('text', '').encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def _load_previous_hashes() -> Dict[str, str]:
    """从 feeds_meta.json 加载上次生成的 items_hash (#36)."""
    try:
        if os.path.exists('feeds_meta.json'):
            with open('feeds_meta.json', 'r', encoding='utf-8') as f:
                meta = json.load(f)
            return {
                name: info.get('items_hash', '')
                for name, info in meta.items()
                if isinstance(info, dict)
            }
    except Exception:
        pass
    return {}


# ============================================================
# Feed 生成
# ============================================================

def _build_atom_feed(
    items: List[Dict], 
    title: str, 
    feed_url: str,
    description: str = "",
    updated_at: str = "",
    interval_min: Optional[int] = None,
    site_name: str = '',
    site_url: str = '',
) -> ET.Element:
    """构建 Atom feed 根元素."""
    from html import escape as html_escape

    # 限制每个 feed 最多保留最近 N 条，防止无限增长
    MAX_FEED_ITEMS = 1000
    items = items[:MAX_FEED_ITEMS]

    NS = 'http://www.w3.org/2005/Atom'
    SY_NS = 'http://purl.org/syndication/1.0'
    MEDIA_NS = 'http://search.yahoo.com/mrss/'
    ET.register_namespace('', NS)
    ET.register_namespace('sy', SY_NS)
    ET.register_namespace('media', MEDIA_NS)

    root = ET.Element(f'{{{NS}}}feed')

    ET.SubElement(root, f'{{{NS}}}title').text = _sanitize_xml(title)
    if description:
        ET.SubElement(root, f'{{{NS}}}subtitle').text = _sanitize_xml(description)

    # rel='alternate' 应指向原始网站而非项目首页 (fix #4)
    alternate_url = site_url or SITE_URL
    ET.SubElement(root, f'{{{NS}}}link', href=alternate_url, rel='alternate')
    ET.SubElement(root, f'{{{NS}}}link', href=feed_url, rel='self', type='application/atom+xml')
    ET.SubElement(root, f'{{{NS}}}id').text = feed_url
    ET.SubElement(root, f'{{{NS}}}updated').text = _to_iso8601(updated_at)
    ET.SubElement(root, f'{{{NS}}}generator', uri='https://github.com/gitfox-enter/RSSForge').text = 'RSSForge'

    # 版权声明 (fix #7)
    ET.SubElement(root, f'{{{NS}}}rights').text = '内容版权归原作者所有，RSSForge 仅提供聚合索引'

    # 更新频率
    if interval_min is not None:
        ET.SubElement(root, f'{{{SY_NS}}}updatePeriod').text = _interval_to_update_period(interval_min)
        ET.SubElement(root, f'{{{SY_NS}}}updateFrequency').text = str(_interval_to_update_frequency(interval_min))
        ET.SubElement(root, f'{{{SY_NS}}}updateBase').text = '2000-01-01T00:00:00+08:00'

    author = ET.SubElement(root, f'{{{NS}}}author')
    ET.SubElement(author, f'{{{NS}}}name').text = 'RSSForge'
    ET.SubElement(author, f'{{{NS}}}uri').text = 'https://github.com/gitfox-enter/RSSForge'

    # Feed 图标 - 强制使用真实网站 favicon
    icon_url = fetch_site_favicon(site_url or feed_url, site_name or title)
    ET.SubElement(root, f'{{{NS}}}icon').text = icon_url

    # 条目
    for idx, item in enumerate(items):
        entry = ET.SubElement(root, f'{{{NS}}}entry')

        title_text = _sanitize_xml(item.get('text', item.get('title', '无标题')))
        title_el = ET.SubElement(entry, f'{{{NS}}}title')
        title_el.text = title_text
        title_el.set('type', 'text')

        url = _sanitize_xml(item.get('url', ''))
        if url:
            ET.SubElement(entry, f'{{{NS}}}link', href=url, rel='alternate')
            # 使用 tag URI 格式保证 id 永久唯一 (fix #7 + fix #dup-id)
            # 修复: ID 必须基于 URL 本身，不能包含日期，否则 feed 每天更新时会产生重复条目
            parsed = urlparse(url)
            domain = parsed.hostname or 'unknown'
            # 使用完整 URL（含路径和查询参数）的哈希作为唯一标识
            url_for_hash = parsed.path + ('?' + parsed.query if parsed.query else '')
            url_hash = hashlib.md5(url_for_hash.encode('utf-8')).hexdigest()[:16]
            # 使用固定日期（RFC 4151 要求）确保 ID 永久不变
            ET.SubElement(entry, f'{{{NS}}}id').text = f"tag:{domain},2024-01-01:{url_hash}"
        else:
            # 无 URL 时使用标题哈希，同样使用固定日期
            title_hash = hashlib.md5(title_text.encode('utf-8')).hexdigest()[:16]
            ET.SubElement(entry, f'{{{NS}}}id').text = f"tag:gitfox-enter,2024-01-01:{title_hash}"

        # 时间戳处理 (fix #3 + fix #duplicate-timestamp):
        # - <published> 优先用 item 的真实发布时间
        # - <updated> 用 item 时间或 feed 更新时间（取较新者）
        # - 无真实时间时，使用 URL 哈希生成稳定时间戳（避免每次重新生成 feed
        #   时老 item 时间变化，导致 RSS 阅读器判定为新条目 → 重复显示）
        item_time = item.get('time', '')
        if item_time:
            published_time = _to_iso8601(item_time)
            updated_time = published_time  # 无独立 updated 字段时与 published 相同
        else:
            # 无真实时间时，用 URL 哈希生成稳定时间戳
            # 同一个 URL 永远对应同一时间，跨多次 feed 生成保持一致
            stable_url = item.get('url', '') or item.get('text', '') or f"idx-{idx}"
            url_hash_int = int(hashlib.md5(stable_url.encode('utf-8')).hexdigest(), 16)
            # 基准时间: 2024-01-01 00:00:00 UTC+8
            # 时间偏移: 0 ~ ~68年（hash 取模 2^31 秒 ≈ 68年）
            base_epoch = int(datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=8))).timestamp())
            stable_offset = url_hash_int % (2**31)  # 最多 68 年
            stable_dt = datetime.fromtimestamp(base_epoch + stable_offset, tz=timezone(timedelta(hours=8)))
            published_time = stable_dt.isoformat()
            updated_time = published_time

        ET.SubElement(entry, f'{{{NS}}}updated').text = updated_time
        ET.SubElement(entry, f'{{{NS}}}published').text = published_time

        category = _sanitize_xml(item.get('category', ''))

        # 条目级 author：标注来源站点 (fix #7)
        if site_name:
            entry_author = ET.SubElement(entry, f'{{{NS}}}author')
            ET.SubElement(entry_author, f'{{{NS}}}name').text = site_name

        # 内容摘要 (fix #2 + #5)
        summary = item.get('summary', '')

        # 构建 <summary>：优先用 item.summary，其次用 title 截断
        summary_text = summary or (title_text[:200] if title_text else '')
        if summary_text:
            summary_el = ET.SubElement(entry, f'{{{NS}}}summary')
            summary_el.text = _sanitize_xml(summary_text)
            summary_el.set('type', 'text')

        # 构建 <content>：始终包含有意义的文本
        if summary:
            html_content = '<p>' + html_escape(summary) + '</p>'
            if url:
                html_content += f'<p><a href="{html_escape(url)}">查看原文 →</a></p>'
        elif title_text:
            # 没有 summary 时，用标题作为 content 正文
            html_content = '<p>' + html_escape(title_text) + '</p>'
            if url:
                html_content += f'<p><a href="{html_escape(url)}">查看原文 →</a></p>'
        elif url:
            html_content = f'<p><a href="{html_escape(url)}">查看原文 →</a></p>'
        else:
            html_content = '<p>暂无内容</p>'

        content_el = ET.SubElement(entry, f'{{{NS}}}content')
        content_el.text = _sanitize_xml(html_content)
        content_el.set('type', 'html')

        if category:
            ET.SubElement(entry, f'{{{NS}}}category', term=category)

    return root


def _write_feed(root: ET.Element, output_path: str, feed_type: str = 'rss2') -> bool:
    """Write feed to file. feed_type: 'rss2' (default, no XSL) or 'atom' (with XSL).
    
    RSS 2.0 是通用标准格式，不加 XSL 以确保验证器兼容性。
    """
    tmp_path = output_path + '.tmp'
    try:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            # Atom 可选加 XSL 样式；RSS 2.0 不加，避免验证器误判
            if feed_type == 'atom':
                f.write('<?xml-stylesheet href="https://gitfox-enter.github.io/RSSForge/pretty-feed-v3.xsl" type="text/xsl"?>\n')
            tree.write(f, encoding='unicode', xml_declaration=False)
        os.replace(tmp_path, output_path)
        return True
    except Exception as e:
        print(f"Failed to write feed {output_path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False



def _build_rss2_feed(
    items: List[Dict],
    title: str,
    site_url: str,
    description: str = "",
    interval_min: Optional[int] = None,
    site_name: str = '',
) -> ET.Element:
    """构建 RSS 2.0 feed（fix: 切换为 RSS 2.0 格式，兼容验证器）."""
    from html import escape as html_escape
    from email.utils import formatdate

    MAX_FEED_ITEMS = 1000
    items = items[:MAX_FEED_ITEMS]

    # RSS 2.0 根元素
    rss = ET.Element('rss', version='2.0')
    ET.register_namespace('', '')

    channel = ET.SubElement(rss, 'channel')

    # 频道基本信息
    ET.SubElement(channel, 'title').text = _sanitize_xml(title)
    ET.SubElement(channel, 'link').text = site_url
    ET.SubElement(channel, 'description').text = _sanitize_xml(
        description or f'{title} 的 RSS 订阅源（由 RSSForge 生成）'
    )
    ET.SubElement(channel, 'language').text = 'zh-cn'
    ET.SubElement(channel, 'lastBuildDate').text = formatdate(localtime=True)
    ET.SubElement(channel, 'generator').text = 'RSSForge'
    ET.SubElement(channel, 'copyright').text = '内容版权归原作者所有，RSSForge 仅提供聚合索引'

    # TTL: 分钟为单位
    if interval_min is not None:
        ttl = max(1, interval_min)
        ET.SubElement(channel, 'ttl').text = str(ttl)

    # 图片（favicon）
    icon_url = fetch_site_favicon(site_url, site_name or title)
    if icon_url:
        image = ET.SubElement(channel, 'image')
        ET.SubElement(image, 'url').text = icon_url
        ET.SubElement(image, 'title').text = _sanitize_xml(title)
        ET.SubElement(image, 'link').text = site_url

    # 条目
    for idx, item in enumerate(items):
        entry = ET.SubElement(channel, 'item')

        title_text = _sanitize_xml(item.get('text', item.get('title', '无标题')))
        ET.SubElement(entry, 'title').text = title_text

        url = _sanitize_xml(item.get('url', ''))
        if url:
            ET.SubElement(entry, 'link').text = url
            # GUID: 用 URL 的 MD5 哈希作为永久唯一 ID
            parsed = urlparse(url)
            path_qs = parsed.path + ('?' + parsed.query if parsed.query else '')
            url_hash = hashlib.md5(path_qs.encode('utf-8')).hexdigest()[:16]
            guid = ET.SubElement(entry, 'guid', isPermaLink='false')
            guid.text = f"urn:md5:{url_hash}@{parsed.hostname}"

        # pubDate: RFC 822 格式
        item_time = item.get('time', '')
        try:
            if item_time:
                dt = datetime.strptime(item_time, '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            else:
                dt = datetime.now(timezone(timedelta(hours=8)))
        except Exception:
            dt = datetime.now(timezone(timedelta(hours=8)))
        # calendar.timegm 把 timetuple 当作 UTC解释，配合 UTC+8 tzinfo 得到正确 UTC 时间戳
        import calendar as _cal
        utc_ts = _cal.timegm(dt.timetuple())
        pub_date = formatdate(utc_ts, localtime=False)
        ET.SubElement(entry, 'pubDate').text = pub_date

        # 作者/来源
        if site_name:
            ET.SubElement(entry, 'author').text = site_name

        # 描述（summary + content 合并）
        summary = item.get('summary', '')
        if summary:
            html_content = html_escape(summary)
            if url:
                html_content += f'<br/><a href="{html_escape(url)}">查看原文 →</a>'
        elif title_text:
            html_content = html_escape(title_text)
            if url:
                html_content += f'<br/><a href="{html_escape(url)}">查看原文 →</a>'
        elif url:
            html_content = f'<a href="{html_escape(url)}">查看原文 →</a>'
        else:
            html_content = '暂无内容'

        desc_el = ET.SubElement(entry, 'description')
        desc_el.text = html_content
        desc_el.set('xml:space', 'preserve')

    return rss



# ============================================================
# 主函数: 为所有配置的站点生成 feed
# ============================================================

def generate_all_feeds() -> Dict[str, int]:
    """为 sites.yaml 中配置的每个站点生成独立 feed.
    
    即使站点暂无数据，也会生成一个空的占位 feed。
    不生成主聚合 feed.xml。
    
    Returns:
        dict: {'feeds_generated': N, 'feeds_skipped': M, 'total_sites': T}
    """
    db = load_items_db()
    items = db.get('items', [])
    updated_at = db.get('updated_at', '')

    stats = {
        'feeds_generated': 0,
        'feeds_skipped': 0,
        'feeds_empty_skipped': 0,
        'feeds_unchanged': 0,
        'total_sites': 0,
        'sites_with_items': 0,
    }

    # 加载上次生成的 items 哈希，用于增量生成 (#36)
    prev_hashes = _load_previous_hashes()

    # 按来源分组已有数据
    by_source: Dict[str, List[Dict]] = {}
    for item in items:
        source = item.get('source', '未知')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)

    # 确保 feeds 目录存在
    os.makedirs(FEEDS_DIR, exist_ok=True)
    
    # 确保 icons 目录存在
    os.makedirs(ICONS_DIR, exist_ok=True)

    # 构建 URL -> Name 映射（从 SOURCE_NAME_MAP）
    url_to_name: Dict[str, str] = {}
    for url, name in SOURCE_NAME_MAP.items():
        url_to_name[url] = name

    # 获取所有配置的站点
    from crawler.config import MONITOR_SITES
    all_sites = MONITOR_SITES if 'MONITOR_SITES' in dir() else []
    
    if not all_sites:
        # 如果无法导入，使用 sites.yaml 原始数据
        try:
            import yaml
            with open('sites.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            all_sites = [s['url'] for s in config.get('sites', [])]
        except Exception:
            all_sites = []

    stats['total_sites'] = len(all_sites)
    print(f"共配置 {len(all_sites)} 个站点")

    # 为每个站点生成 feed
    for site_url in all_sites:
        # 获取站点名称
        site_name = url_to_name.get(site_url, '')
        if not site_name:
            # 从 URL 提取域名作为备用名称
            parsed = urlparse(site_url)
            site_name = parsed.hostname or site_url
        
        safe_name = _safe_filename(site_name)
        filename = f"{FEEDS_DIR}/{safe_name}.xml"
        feed_url = f"{SITE_URL}{FEEDS_URL_PATH}/{safe_name}.xml"
        
        # 获取站点间隔配置
        interval = SITE_INTERVALS.get(site_url, 30)
        
        # 获取该站点的数据
        site_items = by_source.get(site_name, [])
        
        # 跳过空 feed：不生成无数据的 feed 文件 (fix #1)
        if not site_items:
            stats['feeds_empty_skipped'] += 1
            # 如果之前存在旧的空 feed 文件，删除它
            if os.path.exists(filename):
                os.remove(filename)
                print(f"  ✗ {site_name}: 移除旧的空 feed")
            else:
                print(f"  ○ {site_name}: 暂无数据，跳过")
            continue
        
        # 构建 feed
        title = f"{site_name} - RSSForge"
        desc = f"{site_name} 的 RSS 订阅源（由 RSSForge 生成）"
        
        # 按时间排序
        site_items = sorted(site_items, key=lambda x: x.get('time', ''), reverse=True)
        stats['sites_with_items'] += 1

        # ---- 增量生成：比对 items 哈希 (#36) ----
        current_hash = _compute_items_hash(site_items)
        prev_hash = prev_hashes.get(site_name, '')
        if prev_hash and prev_hash == current_hash and os.path.exists(filename):
            stats['feeds_unchanged'] += 1
            continue  # 数据无变化且 feed 文件存在，跳过生成

        root = _build_rss2_feed(
            site_items, title, site_url, desc,
            interval_min=interval,
            site_name=site_name,
        )

        if _write_feed(root, filename, feed_type='rss2'):
            stats['feeds_generated'] += 1
            print(f"  ✓ {site_name}: {len(site_items)} 条")
        else:
            stats['feeds_skipped'] += 1

    # ---- Clean up stale feed files ----
    # Only remove .xml files that are NOT in the current site list at all
    # (e.g. removed from sites.yaml). Keep files for sites with no data.
    if os.path.isdir(FEEDS_DIR):
        all_expected = set()
        for site_url_key, name in url_to_name.items():
            all_expected.add(_safe_filename(name) + '.xml')
        # Also keep files for sites in SOURCE_NAME_MAP that have no items
        for url, name in SOURCE_NAME_MAP.items():
            all_expected.add(_safe_filename(name) + '.xml')
        for f in os.listdir(FEEDS_DIR):
            if f.endswith('.xml') and f not in all_expected:
                old_path = os.path.join(FEEDS_DIR, f)
                os.remove(old_path)
                print(f"  Cleaned stale feed: {f}")

    # ---- Generate empty placeholder feeds for sites with no data ----
    _NS = 'http://www.w3.org/2005/Atom'
    tz = timezone(timedelta(hours=8))
    now_iso = datetime.now(tz).isoformat()
    for url, name in SOURCE_NAME_MAP.items():
        sn = _safe_filename(name)
        filepath = os.path.join(FEEDS_DIR, f"{sn}.xml")
        if os.path.exists(filepath):
            continue  # already generated with items or placeholder
        # Generate empty Atom feed placeholder
        feed_url = f"{SITE_URL}{FEEDS_URL_PATH}/{sn}.xml"
        root = ET.Element(f'{{{_NS}}}feed')
        ET.SubElement(root, f'{{{_NS}}}title').text = _sanitize_xml(name)
        ET.SubElement(root, f'{{{_NS}}}link', href=feed_url, rel='self', type='application/atom+xml')
        ET.SubElement(root, f'{{{_NS}}}link', href=url, rel='alternate', type='text/html')
        ET.SubElement(root, f'{{{_NS}}}id').text = feed_url
        ET.SubElement(root, f'{{{_NS}}}updated').text = now_iso
        ET.SubElement(root, f'{{{_NS}}}subtitle').text = _sanitize_xml(f'{name} - no items yet')
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        _write_feed(root, filepath)
        print(f"  Generated empty placeholder: {sn}.xml")

    # 删除 public/icons/ 中含中文的旧图标文件
    if os.path.isdir(ICONS_DIR):
        _chinese_re = re.compile(r'[\u4e00-\u9fff]')
        for f in os.listdir(ICONS_DIR):
            if _chinese_re.search(f):
                old_path = os.path.join(ICONS_DIR, f)
                os.remove(old_path)
                print(f"  🗑 清理旧 icon: {f}")

    # 生成 feeds_meta.json
    _generate_feeds_meta(stats, by_source)

    print(f"\n完成: {stats['feeds_generated']} 个 feed 生成, {stats['feeds_unchanged']} 个未变化跳过, "
          f"{stats['sites_with_items']} 个站点有数据, {stats['feeds_empty_skipped']} 个空 feed 跳过")
    return stats


def _generate_feeds_meta(stats: Dict, by_source: Dict[str, List[Dict]]) -> None:
    """生成 feeds_meta.json 用于前端展示.
    
    仅包含有数据的站点，空 feed 不写入 meta (fix #1)。
    同时记录每个站点的 items_hash 用于增量生成 (#36)。
    """
    meta = {}
    
    for url, name in SOURCE_NAME_MAP.items():
        # 跳过无数据的站点
        site_items = by_source.get(name, [])
        items_count = len(site_items)

        safe_name = _safe_filename(name)
        interval = SITE_INTERVALS.get(url, 30)
        
        # 强制获取本地 favicon
        icon_url = fetch_site_favicon(url, name)
        
        # 计算频率标签
        if interval <= 15:
            freq_label = "每15分钟"
        elif interval <= 30:
            freq_label = f"每{interval}分钟"
        elif interval <= 60:
            freq_label = "每小时"
        elif interval <= 120:
            freq_label = "每2小时"
        else:
            freq_label = f"每{interval // 60}小时"
        
        meta[name] = {
            'interval': interval,
            'freq_label': freq_label,
            'count': items_count,
            'feed_url': f"{SITE_URL}{FEEDS_URL_PATH}/{safe_name}.xml",
            'icon': icon_url,
            'site_url': url,
            'items_hash': _compute_items_hash(site_items) if site_items else '',  # (#36)
        }
    
    try:
        tmp_path = 'feeds_meta.json.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, 'feeds_meta.json')
        print(f"feeds_meta.json 已更新 ({len(meta)} 个站点)")
    except Exception as e:
        print(f"写入 feeds_meta.json 失败: {e}")


if __name__ == '__main__':
    result = generate_all_feeds()
