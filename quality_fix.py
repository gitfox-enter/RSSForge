#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 内容质量自动修复器（由 quality-guard 守卫流在发现垃圾时调用）。

做什么（仅清理「TIER-1 明确垃圾」，绝不误删合法内容）：
  1) 读 items.json 全库，删除 quality_check 判定的 TIER-1 垃圾
     （/category、/forum*.php、/forum-、/about、标题「广告」开头）；
  2) 对「有垃圾的源」强制重生 feed（先删其陈旧 XML，绕过 rss_feed.py
     的增量跳过，避免脏 XML 残留——这是此前网猴线报回潮的教训）；
  3) 重建 OPML（主+3 镜像）与订阅源目录 index.html；
  4) 打印修复摘要（不负责 push，由守卫流统一提交推送）。

设计原则（与 quality_check 一致的高查准）：
  - 只删 quality_check 判为 TIER-1 的条目；
  - 外站链接（京东/淘宝合法跳转）、根路径（频道 link）、/group/topic/（豆瓣真实帖子）
    不在此脚本删除范围，避免破坏合法 feed；
  - 对「不在 sites.yaml 的死库源」不做任何改动（其库内残留从不生成 feed）。

用法：
  python3 quality_fix.py
"""
import os
import sys
import json
import subprocess

# 复用 quality_check 的判定与扫描（单一事实来源，避免规则漂移）
from quality_check import (
    classify_junk,
    load_sites,
    scan_feeds,
    scan_db,
    ROOT,
    FEEDS_DIR,
)

try:
    from common import slugify
except Exception:  # pragma: no cover
    def slugify(name: str) -> str:
        import re
        s = (name or "").strip().lower()
        s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", s)
        return s.strip("-") or "feed"


def _run(script: str) -> bool:
    """在仓库根目录执行一个生成脚本。"""
    print(f"  ▶ python {script}")
    rc = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
    ).returncode
    return rc == 0


def main() -> int:
    sites_by_name, _ = load_sites()

    # 1) 扫描当前垃圾（feed + 活跃源库），确定受影响源
    feeds = scan_feeds()
    db_active, _db_inactive = scan_db(sites_by_name)

    feed_junk_files = {n for n, v in feeds.items() if v["junk"]}
    db_junk_sources = {n for n, v in db_active.items() if v["junk"]}

    if not feed_junk_files and not db_junk_sources:
        print("quality_fix: 未发现 TIER-1 垃圾，无需修复。")
        return 0

    affected_feeds = set(feed_junk_files)
    for src in db_junk_sources:
        affected_feeds.add(slugify(src) + ".xml")

    # 2) 清理 items.json 全库中的 TIER-1 垃圾（仅删明确垃圾）
    db_path = os.path.join(ROOT, "items.json")
    removed = 0
    if os.path.exists(db_path):
        with open(db_path, encoding="utf-8") as f:
            db = json.load(f)
        items = db if isinstance(db, list) else db.get("items", db.get("data", []))
        kept = []
        for it in items:
            url = it.get("url", "") or ""
            text = it.get("text", "") or it.get("title", "") or ""
            if classify_junk(url, text):
                removed += 1
                continue
            kept.append(it)
        if isinstance(db, list):
            new_db = kept
        else:
            new_db = dict(db)
            new_db["items"] = kept
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(new_db, f, ensure_ascii=False, indent=1)
    print(f"  ✓ items.json 删除 TIER-1 垃圾 {removed} 条（剩余 {len(kept)} 条）")

    # 3) 强制重生受影响 feed（先删陈旧 XML，绕过增量跳过）
    deleted = []
    for fn in sorted(affected_feeds):
        p = os.path.join(FEEDS_DIR, fn)
        if os.path.exists(p):
            os.remove(p)
            deleted.append(fn)
    print(f"  ✓ 删除 {len(deleted)} 个陈旧 feed XML: {deleted or '无'}")

    # 4) 重生 feed + 重建 OPML/index
    ok = True
    ok &= _run("rss_feed.py")
    ok &= _run("opml_generator.py")
    ok &= _run("generate_opml_mirrors.py")
    ok &= _run("generate_feeds_index.py")

    print(
        f"\nquality_fix 完成：删库垃圾 {removed} 条，重生 {len(deleted)} 个 feed，"
        f"OPML/index 重建 {'成功' if ok else '部分失败'}。"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
