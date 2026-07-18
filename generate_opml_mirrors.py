#!/usr/bin/env python3
"""
Generate multi-mirror OPML files for RSSForge.

复用 opml_generator 的 feed 枚举（docs/feeds/*.xml + feeds_meta.json），
使镜像 OPML 与主 opml.xml 列出【同一份完整 feed 清单】（含当前无数据、
但被保留的历史 feed），而不是只列 feeds_meta.json 里的 10 个数据源。

输出 4 个 OPML 文件到 docs/：
  - docs/opml.official.xml  (github.io 官方)
  - docs/opml.ghfast.xml    (ghfast.top 镜像)
  - docs/opml.jsdelivr.xml  (jsDelivr CDN 镜像)
  - docs/opml.xml           (主文件，= official 版)
"""
import os
import xml.etree.ElementTree as ET
from opml_generator import _load_feeds, _load_project_feed

BASE = "https://gitfox-enter.github.io/RSSForge"

MIRRORS = {
    "official": (
        "RSSForge Feeds",
        f"{BASE}/feeds/{{slug}}.xml",
    ),
    "ghfast": (
        "RSSForge Feeds (ghfast)",
        "https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/{slug}.xml",
    ),
    "jsdelivr": (
        "RSSForge Feeds (jsDelivr)",
        "https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{slug}.xml",
    ),
}


def build_opml(title: str, feed_tpl: str, feeds: list) -> ET.Element:
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = title
    ET.SubElement(head, "ownerName").text = "RSSForge"
    body = ET.SubElement(root, "body")
    for feed in feeds:
        slug = feed["slug"]
        o = ET.SubElement(body, "outline")
        o.set("type", "rss")
        o.set("text", feed["name"])
        o.set("title", feed["name"])
        o.set("xmlUrl", feed_tpl.format(slug=slug))
        if feed.get("html_url"):
            o.set("htmlUrl", feed["html_url"])
        if feed.get("icon"):
            o.set("iconUrl", feed["icon"])
    return root


def main():
    # 复用主生成器的枚举逻辑，保证清单与 opml.xml 完全一致
    feeds = _load_feeds()
    project = _load_project_feed()
    if project:
        feeds.insert(0, project)

    os.makedirs("docs", exist_ok=True)

    for key, (title, feed_tpl) in MIRRORS.items():
        root = build_opml(title, feed_tpl, feeds)
        path = f"docs/opml.{key}.xml"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        print(f"  ✓ {path}  ({len(feeds)} feeds)")

    # 主 opml.xml = official 版（与 opml_generator.py 输出一致）
    root = build_opml("RSSForge Feeds", f"{BASE}/feeds/{{slug}}.xml", feeds)
    ET.ElementTree(root).write("docs/opml.xml", encoding="utf-8", xml_declaration=True)
    print(f"  ✓ docs/opml.xml (main file, {len(feeds)} feeds)")


if __name__ == "__main__":
    main()
