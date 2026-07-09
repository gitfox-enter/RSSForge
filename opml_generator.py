#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPML generator - builds a unified OPML subscription list from feeds directory and feeds_meta.json.

Features:
  - Uses feeds_meta.json as primary data source, feeds/ directory as fallback
  - Smart dedup: skip CJK-named files when a pinyin-slug version exists
  - Uses site display names as OPML titles
  - Auto-fills htmlUrl, iconUrl metadata
  - Auto percent-encodes CJK filenames (RSS reader compatible)
  - Dynamic dates (no hardcoding)
  - Flat structure (compatible with all RSS readers)
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote as url_quote
from common import slugify, SITE_URL_BASE

FEEDS_DIR = "docs/feeds"  # filesystem path
FEEDS_URL_PATH = "feeds"  # URL path
SITE_URL = SITE_URL_BASE  # fix #17: unified from common.py


def _has_cjk(s: str) -> bool:
    """Check if string contains CJK characters."""
    return bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', s))


def _safe_filename(name: str) -> str:
    """ASCII-safe filename (fix #9)."""
    return slugify(name)


def _feed_has_entries(filepath: str) -> bool:
    """Check if feed file contains at least one item (<entry> for Atom, <item> for RSS 2.0)."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        # Atom: <entry>
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        if not entries:
            entries = root.findall('entry')
        if entries:
            return True
        # RSS 2.0: <item>
        items = root.findall('item')
        return len(items) > 0
    except Exception:
        return False


def _load_feeds_meta() -> Dict:
    """Load feeds_meta.json."""
    try:
        if os.path.exists('feeds_meta.json'):
            with open('feeds_meta.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _build_slug_to_meta(feeds_meta: Dict) -> Dict[str, Tuple[str, Dict]]:
    """Build slug from feeds_meta.json -> (site name, metadata) mapping."""
    slug_map = {}
    for chinese_name, meta in feeds_meta.items():
        feed_url = meta.get('feed_url', '')
        if feed_url:
            basename = os.path.basename(feed_url)
            slug = os.path.splitext(basename)[0]
            if slug:
                slug_map[slug] = (chinese_name, meta)
    return slug_map


def _try_load_source_name_map() -> Dict[str, str]:
    """Try loading SOURCE_NAME_MAP (slug -> name) as fallback."""
    try:
        from crawler.config import SOURCE_NAME_MAP
        name_to_slug = {}
        for url, name in SOURCE_NAME_MAP.items():
            slug = slugify(name)
            name_to_slug[slug] = name
        return name_to_slug
    except Exception:
        return {}


def _encode_feed_url(filename: str) -> str:
    """Build feed URL with percent-encoding for non-ASCII chars."""
    encoded_filename = url_quote(filename, safe='')
    return f"{SITE_URL}{FEEDS_URL_PATH}/{encoded_filename}"


def _load_feeds() -> List[Dict]:
    """Load all valid feeds from feeds directory and feeds_meta.json.

    Strategy:
    1. Scan feeds/ directory, separate pinyin-slug files from CJK-named files
    2. CJK-named files: skip only if pinyin-slug version exists
    3. Look up display name and metadata for each feed
    4. Include only feeds with at least 1 entry
    """
    feeds_meta = _load_feeds_meta()
    slug_to_meta = _build_slug_to_meta(feeds_meta)
    slug_to_chinese = _try_load_source_name_map()

    if not os.path.exists(FEEDS_DIR):
        print(f"Warning: {FEEDS_DIR} directory does not exist")
        return []

    # First pass: collect all pinyin-slug filenames (for dedup)
    all_filenames = [f for f in os.listdir(FEEDS_DIR) if f.endswith('.xml')]
    pinyin_slugs: Set[str] = set()
    for filename in all_filenames:
        base = os.path.splitext(filename)[0]
        if not _has_cjk(base):
            pinyin_slugs.add(base)

    feeds = []
    skipped_dup = []

    for filename in sorted(all_filenames):
        feed_name = os.path.splitext(filename)[0]
        filepath = os.path.join(FEEDS_DIR, filename)

        # Skip project update feed (handled separately by _load_project_feed, pinned)
        if feed_name == 'project-updates':
            continue

        # CJK-named file: check if pinyin-slug version exists
        if _has_cjk(feed_name):
            expected_slug = slugify(feed_name)
            if expected_slug in pinyin_slugs:
                # Pinyin version exists -> skip this duplicate
                skipped_dup.append(filename)
                continue
            # No pinyin version -> keep this file, use CJK name as display name
            display_name = feed_name
        else:
            display_name = feed_name  # Use slug first, replace later

        # Skip empty feed (fix #1)
        if not _feed_has_entries(filepath):
            continue

        feed_url = _encode_feed_url(filename)
        html_url = ""
        icon_url = ""

        # Look up metadata from feeds_meta.json
        slug_key = feed_name if not _has_cjk(feed_name) else slugify(feed_name)
        if slug_key in slug_to_meta:
            chinese_name, meta = slug_to_meta[slug_key]
            display_name = chinese_name
            html_url = meta.get('site_url', '')
            icon_url = meta.get('icon', '')
        elif slug_key in slug_to_chinese:
            display_name = slug_to_chinese[slug_key]

        feeds.append({
            'name': display_name,
            'slug': feed_name,
            'feed_url': feed_url,
            'html_url': html_url,
            'icon': icon_url,
        })

    if skipped_dup:
        print(f"Skipped {len(skipped_dup)} CJK-named duplicate feed: "
              f"{', '.join(skipped_dup[:5])}{'...' if len(skipped_dup) > 5 else ''}")

    # Sort by site name
    feeds.sort(key=lambda x: x['name'])
    return feeds


def _build_opml(feeds: List[Dict], title: str) -> ET.Element:
    """Build OPML root element (flat structure)."""
    root = ET.Element('opml')
    root.set('version', '2.0')

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'title').text = title
    ET.SubElement(head, 'ownerName').text = 'RSSForge'
    ET.SubElement(head, 'ownerEmail').text = 'noreply@gitfox-enter.github.io'
    ET.SubElement(head, 'dateCreated').text = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    body = ET.SubElement(root, 'body')

    for feed in feeds:
        outline = ET.SubElement(body, 'outline')
        outline.set('type', 'rss')
        outline.set('text', feed['name'])
        outline.set('title', feed['name'])
        outline.set('xmlUrl', feed['feed_url'])
        if feed['html_url']:
            outline.set('htmlUrl', feed['html_url'])
        if feed.get('icon'):
            outline.set('iconUrl', feed['icon'])

    return root


def _write_opml(root: ET.Element, output_path: str) -> bool:
    """Write OPML file (atomic write)."""
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
        print(f"Failed to write OPML {output_path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def _cleanup_legacy_files() -> int:
    """Clean up legacy category OPML files and duplicate CJK-named feed files."""
    import glob
    removed = 0

    # Delete legacy category OPML files (opml-*.xml)
    for f in glob.glob('opml-*.xml'):
        try:
            os.remove(f)
            removed += 1
            print(f"  Cleaned up legacy OPML: {f}")
        except Exception as e:
            print(f"  Cleanup failed {f}: {e}")

    # Remove CJK-named duplicate feed files（only when pinyin-slug version exists）
    if os.path.exists(FEEDS_DIR):
        # Collect all pinyin-slug filenames first
        pinyin_slugs = set()
        for filename in os.listdir(FEEDS_DIR):
            if not filename.endswith('.xml'):
                continue
            base = os.path.splitext(filename)[0]
            if not _has_cjk(base):
                pinyin_slugs.add(base)

        for filename in os.listdir(FEEDS_DIR):
            if not filename.endswith('.xml'):
                continue
            feed_name = os.path.splitext(filename)[0]
            if _has_cjk(feed_name):
                expected_slug = slugify(feed_name)
                if expected_slug in pinyin_slugs:
                    filepath = os.path.join(FEEDS_DIR, filename)
                    try:
                        os.remove(filepath)
                        removed += 1
                        print(f"  Cleaned up duplicate feed: {filepath}")
                    except Exception as e:
                        print(f"  Cleanup failed {filepath}: {e}")

    return removed


def _load_project_feed() -> Optional[Dict]:
    """Load project update feed if it exists."""
    project_feed_path = os.path.join(FEEDS_DIR, 'project-updates.xml')
    if not os.path.exists(project_feed_path):
        return None
    if not _feed_has_entries(project_feed_path):
        return None
    return {
        'name': 'RSSForge Project Updates',
        'slug': 'project-updates',
        'feed_url': _encode_feed_url('project-updates.xml'),
        'html_url': SITE_URL,
        'icon': '',
    }


def generate_opml() -> Dict[str, int]:
    """Generate unified OPML file.

    Returns:
        dict: {'feeds_count': N, 'opml_generated': 0/1, 'cleaned': N}
    """
    cleaned = 0  # Cleaned up duplicate feed count
    feeds = _load_feeds()

    # Add project update feed (pinned to top)
    project_feed = _load_project_feed()
    if project_feed:
        feeds.insert(0, project_feed)

    if not feeds:
        print("Warning: no feeds found")
        return {'feeds_count': 0, 'opml_generated': 0, 'cleaned': cleaned}

    stats = {
        'feeds_count': len(feeds),
        'opml_generated': 0,
    }

    root = _build_opml(feeds, "RSSForge Feeds")

    if _write_opml(root, "docs/opml.xml"):
        stats['opml_generated'] = 1
        print(f"✓ OPML generated successfully: {len(feeds)} feeds")
        for feed in feeds:
            extra = []
            if feed['html_url']:
                extra.append(f"htmlUrl={feed['html_url']}")
            if feed.get('icon'):
                extra.append("has_icon")
            extra_str = f" ({', '.join(extra)})" if extra else ""
            print(f"  - {feed['name']}: {feed['feed_url']}{extra_str}")

    stats['cleaned'] = cleaned
    return stats


if __name__ == '__main__':
    result = generate_opml()
    print(f"\nDone: {result}")
