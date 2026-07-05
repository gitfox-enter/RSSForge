#!/usr/bin/env python3
"""
Generate multi-mirror OPML files for RSSForge.

Read feeds_meta.json and generate 3 sets of URLs per feed:
  1. Official (github.io)
  2. ghfast.top mirror
  3. jsDelivr CDN mirror

Output 3 OPML files to docs/ directory.
Usage: python generate_opml_mirrors.py
"""

import json
import re
import xml.etree.ElementTree as ET
import os


BASE = "https://gitfox-enter.github.io/RSSForge"
RAW  = "https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs"

MIRRORS = {
    "official": (
        "RSSForge Feeds",
        f"{BASE}/feeds/{{slug}}.xml",
        f"{BASE}/opml.xml",
    ),
    "ghfast": (
        "RSSForge Feeds (ghfast)",
        "https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/{slug}.xml",
        "https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.xml",
    ),
    "jsdelivr": (
        "RSSForge Feeds (jsDelivr)",
        "https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{slug}.xml",
        "https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.xml",
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

    # Main opml.xml = official version
    root = build_opml("RSSForge Feeds", f"{BASE}/feeds/{{slug}}.xml", meta)
    ET.ElementTree(root).write("docs/opml.xml", encoding="utf-8", xml_declaration=True)
    print(f"  ✓ docs/opml.xml (main file)")


if __name__ == "__main__":
    main()
