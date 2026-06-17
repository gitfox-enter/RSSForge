#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPML 生成器 — 从 sites.yaml 生成 OPML 订阅列表。

输出:
  opml.xml          — 全量 OPML
  opml-线报站.xml    — 按分类拆分
  opml-软件站.xml
  opml-论坛.xml
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

SITE_URL = "https://gitfox-enter.github.io/site-update-monitor/"
FEEDS_DIR = "feeds"

# sites.yaml 中的分类注释 → 分类名
CATEGORY_MAP = {
    '综合线报站': '线报站',
    '购物比价': '购物比价',
    '软件资源': '软件站',
    '社区论坛': '论坛',
    '其他': '其他',
}


def _safe_filename(name: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fff]', '', name)


def _load_sites_config() -> Dict[str, List[Dict]]:
    """从 sites.yaml 加载站点配置，按分类分组。"""
    try:
        import yaml
        yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sites.yaml")
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"sites.yaml 加载失败: {e}")
        return {}

    sites = data.get('sites', [])
    # 按分类分组 — 需要从注释推断分类
    # 因为 YAML 不保留注释，我们用 tier + url 特征来分组
    categorized: Dict[str, List[Dict]] = {
        '线报站': [],
        '购物比价': [],
        '软件站': [],
        '论坛': [],
        '其他': [],
    }

    # 软件/资源站 URL 特征
    software_urls = {
        'ghxi.com', '423down.com', 'appinn.com', 'lsapk.com',
        'thosefree.com', 'foxirj.com', 'ddooo.com', 'onlinedown.net',
        'apprcn.com', 'iplaysoft.com',
    }
    # 购物比价站
    shop_urls = {
        'manmanbuy.com', 'baicaio.com', 'bacaoo.com', 'yxssp.com',
    }
    # 论坛站
    forum_urls = {
        'douban.com', 'kxdao.net', '51kanong.com', 'ithome.com',
    }

    for site in sites:
        url = site.get('url', '')
        name = site.get('name', '')
        domain = ''
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).hostname or ''
        except Exception:
            pass

        # 分类判断
        if any(s in domain for s in software_urls):
            cat = '软件站'
        elif any(s in domain for s in shop_urls):
            cat = '购物比价'
        elif any(s in domain for s in forum_urls):
            cat = '论坛'
        elif '10000yun.com' in domain:
            cat = '其他'
        else:
            cat = '线报站'

        entry = {
            'name': name,
            'url': url,
            'feed_url': SITE_URL + f"{FEEDS_DIR}/{_safe_filename(name)}.xml",
        }
        categorized[cat].append(entry)

    # 去掉空分类
    return {k: v for k, v in categorized.items() if v}


def _build_opml(outlines: List[Dict], title: str) -> ET.Element:
    """构建 OPML 根元素。"""
    root = ET.Element('opml')
    root.set('version', '2.0')

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'title').text = title
    ET.SubElement(head, 'ownerName').text = '线报聚合'
    ET.SubElement(head, 'ownerId').text = SITE_URL

    body = ET.SubElement(root, 'body')

    for outline in outlines:
        if 'children' in outline:
            # 分类文件夹
            folder = ET.SubElement(body, 'outline')
            folder.set('text', outline['text'])
            folder.set('title', outline['text'])
            for child in outline['children']:
                o = ET.SubElement(folder, 'outline')
                o.set('type', 'rss')
                o.set('text', child['name'])
                o.set('title', child['name'])
                o.set('xmlUrl', child['feed_url'])
                o.set('htmlUrl', child.get('url', ''))
        else:
            # 单个订阅
            o = ET.SubElement(body, 'outline')
            o.set('type', 'rss')
            o.set('text', outline['name'])
            o.set('title', outline['name'])
            o.set('xmlUrl', outline['feed_url'])
            o.set('htmlUrl', outline.get('url', ''))

    return root


def _write_opml(root: ET.Element, output_path: str) -> bool:
    """写入 OPML 文件。"""
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
        print(f"写入 OPML 失败 {output_path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def generate_all_opml() -> Dict[str, int]:
    """生成全量 OPML + 按分类 OPML。"""
    categorized = _load_sites_config()
    if not categorized:
        print("无站点配置")
        return {'opml_generated': 0}

    stats = {'opml_generated': 0}
    all_sites: List[Dict] = []

    # 1. 全量 OPML（带分类文件夹）
    folder_outlines = []
    for cat, sites in categorized.items():
        folder_outlines.append({
            'text': cat,
            'children': sites,
        })
        all_sites.extend(sites)

    root = _build_opml(folder_outlines, "线报聚合 - 全部订阅")
    if _write_opml(root, "opml.xml"):
        stats['opml_generated'] += 1
        print(f"全量 OPML: {len(all_sites)} 个源")

    # 2. 按分类 OPML
    for cat, sites in categorized.items():
        safe_cat = _safe_filename(cat)
        root = _build_opml(sites, f"线报聚合 - {cat}")
        filename = f"opml-{safe_cat}.xml"
        if _write_opml(root, filename):
            stats['opml_generated'] += 1
            print(f"分类 OPML {cat}: {len(sites)} 个源")

    return stats


if __name__ == '__main__':
    result = generate_all_opml()
    print(f"完成: {result['opml_generated']} 个 OPML 文件")
