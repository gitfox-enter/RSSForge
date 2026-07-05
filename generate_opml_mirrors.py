#!/usr/bin/env python3
"""
为 RSSForge 生成多镜像 OPML 文件。

读取 feeds_meta.json，为每个 feed 生成 3 套 URL：
  1. 官方 (github.io)
  2. ghfast.top 镜像
  3. jsDelivr CDN 镜像

输出 3 个 OPML 文件到 docs/ 目录。
用法: python generate_opml_mirrors.py
"""

import json
import re
import xml.etree.ElementTree as ET
import os


BASE = "https://gitfox-enter.github.io/RSSForge"
RAW  = "https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs"

MIRRORS = {
    "official": (
        "RSSForge - 官方订阅源",
        f"{BASE}/feeds/{{slug}}.xml",
        f"{BASE}/opml.xml",
    ),
    "ghfast": (
        "RSSForge - ghfast.top 镜像",
        f"https://ghfast.top/{RAW}/feeds/{{slug}}.xml",
        f"https://ghfast.top/{RAW}/opml.xml",
    ),
    "jsdelivr": (
        "RSSForge - jsDelivr CDN 镜像",
        f"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{{slug}}.xml",
        f"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.xml",
    ),
}


def slug_from_url(feed_url: str) -> str:
    m = re.search(r"/feeds/([^/]+)\.xml", feed_url)
    return m.group(1) if m else ""


def build_opml(title: str, feed_tpl: str, meta: dict) -> ET.Element:
    opml = ET.Element("opml", version="2.0")
    head = ET.SubElement(opml, "head")
    ET.SubElement(head, "title").text = title
    ET.SubElement(head, "ownerName").text = "RSSForge"
    body = ET.SubElement(opml, "body")

    for name, info in meta.items():
        slug = slug_from_url(info["feed_url"])
        if not slug:
            continue
        o = ET.SubElement(body, "outline")
        o.set("type", "rss")
        o.set("text", name)
        o.set("title", name)
        o.set("xmlUrl", feed_tpl.format(slug=slug))
        o.set("htmlUrl", info.get("site_url", ""))
        desc = info.get("description", "")
        if desc:
            o.set("description", desc)
    return opml


def main():
    with open("feeds_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    os.makedirs("docs", exist_ok=True)

    for key, (title, feed_tpl, _) in MIRRORS.items():
        root = build_opml(title, feed_tpl, meta)
        path = f"docs/opml.{key}.xml"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        print(f"  ✓ {path}  ({len(meta)} feeds)")

    # 主 opml.xml = official 版本
    root = build_opml("RSSForge - 订阅源", f"{BASE}/feeds/{{slug}}.xml", meta)
    ET.ElementTree(root).write("docs/opml.xml", encoding="utf-8", xml_declaration=True)
    print(f"  ✓ docs/opml.xml (主文件)")


if __name__ == "__main__":
    main()
