#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 健康巡检（零依赖，纯标准库）。

用途：
  快速核对「源配置 ↔ feed 文件 ↔ OPML ↔ 索引」四者是否一致，
  并列出空 feed / 偏少 feed / 孤儿 feed，便于日常维护。

用法：
  python3 health_check.py
"""
import os
import glob
import xml.etree.ElementTree as ET
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
FEEDS_DIR = os.path.join(DOCS, "feeds")
BASE = "https://gitfox-enter.github.io/RSSForge"


def _count_items(path):
    try:
        return sum(1 for _ in ET.parse(path).iter("item"))
    except Exception:
        return -1


def main():
    lines = []

    # 1) sites.yaml 源
    with open(os.path.join(ROOT, "sites.yaml"), encoding="utf-8") as f:
        sites = yaml.safe_load(f)["sites"]
    lines.append(f"[1] sites.yaml 源数: {len(sites)}")

    # 2) feed 文件
    feed_files = sorted(glob.glob(os.path.join(FEEDS_DIR, "*.xml")))
    lines.append(f"[2] docs/feeds/*.xml 文件数: {len(feed_files)}")

    # 3) OPML outline
    opml_path = os.path.join(DOCS, "opml.xml")
    if os.path.exists(opml_path):
        opml = ET.parse(opml_path).getroot()
        outlines = list(opml.iter("outline"))
        opml_files = {
            os.path.basename(u)
            for o in outlines
            if (u := o.get("xmlUrl")) and u.startswith(BASE + "/feeds/")
        }
        lines.append(f"[3] opml.xml outline 数: {len(outlines)}")
    else:
        outlines, opml_files = [], set()
        lines.append("[3] opml.xml 不存在 ⚠️")

    # 4) 各 feed 条目数 + 异常
    lines.append("\n[4] 各 feed 条目数（升序）：")
    empty, low = [], []
    rows = []
    for p in feed_files:
        n = _count_items(p)
        rows.append((os.path.basename(p), n))
    rows.sort(key=lambda x: (x[1] < 0, x[1]))
    for name, n in rows:
        if n < 0:
            lines.append(f"   ⚠️ 解析失败  {name}")
        elif n == 0:
            empty.append(name)
            lines.append(f"   {n:5d}  {name}  ⚠️ 空")
        elif n < 10:
            low.append(name)
            lines.append(f"   {n:5d}  {name}  ← 偏少")
        else:
            lines.append(f"   {n:5d}  {name}")
    if empty:
        lines.append(f"\n⚠️ 空 feed: {empty}")
    if low:
        lines.append(f"ℹ️  偏少(<10 条): {low}")

    # 5) 孤儿 feed
    orphans = [os.path.basename(p) for p in feed_files if os.path.basename(p) not in opml_files]
    lines.append(f"\n[5] 孤儿 feed（xml 存在但未在 opml.xml）: {orphans or '无'}")

    # 6) 一致性结论
    n_sites, n_feeds, n_opml = len(sites), len(feed_files), len(outlines)
    ok = (n_sites == n_feeds == n_opml) and not orphans and not empty
    lines.append("\n[6] 一致性：")
    lines.append(
        f"   sites={n_sites}  feeds={n_feeds}  opml={n_opml}  "
        f"-> {'✅ 一致' if ok else '❌ 不一致'}"
    )

    report = "\n".join(lines)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
