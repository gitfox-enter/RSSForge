#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 内容质量检测器（零依赖，仅 pyyaml 读 sites.yaml）。

用途：
  定时「质量守卫」在每次运行时调用本脚本，对已发布内容做**内容级**体检
  （而非仅 health_check.py 的「一致性」体检）：

    1) feed 输出维度：扫描 docs/feeds/*.xml 每个条目的 URL，
       识别 fallback 误抓的导航/分类/板块/系统页垃圾；
    2) 库维度：扫描 items.json 全库（突破 feed 2000 条上限的掩盖），
       同样按 URL 级规则识别垃圾，防止脏库被下次 crawl 写回 feed；
    3) 一致性维度：复用 health_check 的 源↔feed↔OPML 核对。

== 高查准率设计（宁可漏报也不误删）==
  仅判定**明确垃圾**，绝不碰合法内容：
    ✅ 判定为垃圾（TIER-1，安全可自动清理）：
        - 空 URL
        - path 含 /category            → 分类页
        - /forum.php /plugin.php /portal.php /forum-  → 论坛/系统页
        - /about(?|$|/)              → 导航页
        - 标题以「广告」开头
    ❌ 明确**不**判定为垃圾（避免误删合法内容）：
        - 外站链接（u.jd.com / m.tb.cn / s.click.taobao.com 等
          是羊毛党站合法的京东/淘宝/商户跳转短链，删了会破坏 feed）
        - 根路径 '/'（多为 feed 自身频道 <link> 或首页条目）
        - /group/topic/（豆瓣小组真实帖子）
        - /docs、/tag/ 等（部分站点用作真实文章路径）

  历史残留（不在 sites.yaml 的死库源，如枫音/鸭先知/APP喵）的库内
  垃圾**不计入 junk_found 门控**（它们从不生成 feed，不影响输出），
  仅单独列示，保持库整洁。

输出：
    - 可读报告（stdout）
    - quality_report.json（机器可读，供 quality_fix.py / 守卫流读取）
退出码：
    - 0 = 无内容垃圾且一致
    - 1 = 发现内容垃圾（TIER-1）或一致性被破坏

用法：
    python3 quality_check.py
"""
import os
import re
import json
import glob
import datetime
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
FEEDS_DIR = os.path.join(DOCS, "feeds")
BASE = "https://gitfox-enter.github.io/RSSForge"

# TIER-1 明确垃圾（导航/分类/板块/系统页）。高查准：仅此数类。
_JUNK_RE = re.compile(
    r"/category"                         # 分类页
    r"|/(forum|plugin|portal)\.php"     # Discuz 系统页
    r"|/forum-"                          # 论坛板块列表
    r"|/about(\?|$|/)",                 # 关于/导航页
    re.I,
)


def classify_junk(url: str, text: str) -> str:
    """返回垃圾原因；非明确垃圾返回空串（宁可漏报也不误删）。"""
    url = (url or "").strip()
    if not url:
        return "空URL"
    path = (urlparse(url).path or "")
    if _JUNK_RE.search(path):
        seg = _JUNK_RE.search(path).group(0)
        return {
            "/category": "分类页",
            "/forum.php": "论坛/系统页",
            "/plugin.php": "论坛/系统页",
            "/portal.php": "论坛/系统页",
            "/forum-": "论坛板块",
            "/about": "导航页",
        }.get(seg.split("/")[-1] if "/" in seg else seg, "导航/分类页")
    if (text or "").strip().startswith("广告"):
        return "广告标题"
    # 以下一律视为合法，不判垃圾：
    #   外站链接（京东/淘宝合法跳转）、根路径（频道 link）、
    #   /group/topic/（豆瓣真实帖子）、/docs、/tag/
    return ""


def load_sites():
    """返回 (sites_by_name{name:host}, known_hosts:set)。"""
    sites_by_name: dict = {}
    known: set = set()
    path = os.path.join(ROOT, "sites.yaml")
    if not os.path.exists(path) or yaml is None:
        return sites_by_name, known
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        return sites_by_name, known
    groups = []
    if isinstance(cfg.get("sites"), list):
        groups.append(cfg["sites"])
    if isinstance(cfg.get("monitoring_groups"), list):
        for g in cfg["monitoring_groups"]:
            if isinstance(g, dict) and isinstance(g.get("sites"), list):
                groups.append(g["sites"])
    for grp in groups:
        for s in grp:
            if not isinstance(s, dict):
                continue
            name = s.get("name")
            url = s.get("url", "")
            if not url:
                continue
            host = (urlparse(url).hostname or "").lower()
            if name:
                sites_by_name[name] = host
            if host:
                known.add(host)
    return sites_by_name, known


def registered_hosts():
    """返回已注册专用 parser 的 host 集合（判断「无 parser 脏源」）。"""
    try:
        from crawler.parsers.core import PARSER_REGISTRY
        return {h.lower() for h in PARSER_REGISTRY.keys()}
    except Exception:
        return set()


def scan_feeds():
    """扫描所有 feed XML，返回 {feed_file: {'items':N, 'junk':[{url,text,reason}]}}。"""
    import xml.etree.ElementTree as ET

    result: dict = {}
    for p in sorted(glob.glob(os.path.join(FEEDS_DIR, "*.xml"))):
        name = os.path.basename(p)
        try:
            root = ET.parse(p).getroot()
        except Exception:
            result[name] = {"items": -1, "junk": [{"url": p, "text": "", "reason": "解析失败"}]}
            continue
        junk = []
        n = 0
        for it in root.iter("item"):
            n += 1
            link = (it.findtext("link") or "").strip()
            title = (it.findtext("title") or "").strip()
            reason = classify_junk(link, title)
            if reason:
                junk.append({"url": link, "text": title, "reason": reason})
        result[name] = {"items": n, "junk": junk}
    return result


def scan_db(sites_by_name):
    """扫描 items.json 全库。

    返回 (active, inactive)：
      active   = 在 sites.yaml 的源中发现的垃圾（计入门控）
      inactive = 不在 sites.yaml 的死库残留（不计入门控，仅列示）
    每个均为 {source: {'items':N, 'junk':[{url,text,reason}]}}。
    """
    import xml.etree.ElementTree as ET  # noqa 确保 ET 可用

    db_path = os.path.join(ROOT, "items.json")
    if not os.path.exists(db_path):
        return {}, {}
    try:
        with open(db_path, encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        return {}, {}
    items = db if isinstance(db, list) else db.get("items", db.get("data", []))

    by_src: dict = {}
    for it in items:
        by_src.setdefault(it.get("source", "?"), []).append(it)

    active: dict = {}
    inactive: dict = {}
    for src, its in by_src.items():
        junk = []
        for it in its:
            url = (it.get("url") or "").strip()
            text = (it.get("text") or it.get("title") or "")
            reason = classify_junk(url, text)
            if reason:
                junk.append({"url": url, "text": text, "reason": reason})
        entry = {"items": len(its), "junk": junk}
        if src in sites_by_name:
            active[src] = entry
        else:
            inactive[src] = entry
    return active, inactive


def consistency():
    """复用 health_check 的 源↔feed↔OPML 一致性核对。"""
    import xml.etree.ElementTree as ET
    import yaml as _yaml

    out = {"sites": -1, "feeds": -1, "opml": -1, "orphans": [], "ok": False}
    try:
        with open(os.path.join(ROOT, "sites.yaml"), encoding="utf-8") as f:
            out["sites"] = len(_yaml.safe_load(f).get("sites", []))
    except Exception:
        pass
    try:
        out["feeds"] = len(glob.glob(os.path.join(FEEDS_DIR, "*.xml")))
    except Exception:
        pass
    opml_files = set()
    opml_path = os.path.join(DOCS, "opml.xml")
    if os.path.exists(opml_path):
        try:
            root = ET.parse(opml_path).getroot()
            for o in root.iter("outline"):
                u = o.get("xmlUrl", "")
                if u.startswith(BASE + "/feeds/"):
                    opml_files.add(os.path.basename(u))
        except Exception:
            pass
    out["opml"] = len(opml_files)
    feed_files = {os.path.basename(p) for p in glob.glob(os.path.join(FEEDS_DIR, "*.xml"))}
    out["orphans"] = sorted(feed_files - opml_files)
    out["ok"] = (
        out["sites"] == out["feeds"] == out["opml"]
        and not out["orphans"]
    )
    return out


def main():
    sites_by_name, _known = load_sites()
    reg_hosts = registered_hosts()

    feeds = scan_feeds()
    db_active, db_inactive = scan_db(sites_by_name)
    cons = consistency()

    feed_junk_total = sum(len(v["junk"]) for v in feeds.values())
    feed_junk_feeds = sorted(n for n, v in feeds.items() if v["junk"])
    db_junk_total = sum(len(v["junk"]) for v in db_active.values())
    db_junk_sources = sorted(n for n, v in db_active.items() if v["junk"])
    inactive_total = sum(len(v["junk"]) for v in db_inactive.values())
    inactive_sources = sorted(n for n, v in db_inactive.items() if v["junk"])

    # 无 parser 的脏源（需加专用 parser 才能根治复发）
    parserless = []
    for src in db_junk_sources:
        host = sites_by_name.get(src, "")
        if host and host not in reg_hosts:
            parserless.append(src)

    ts = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime("%Y-%m-%d %H:%M:%S +0800")
    junk_found = (feed_junk_total > 0) or (db_junk_total > 0) or (not cons["ok"])

    L = []
    L.append(f"=== RSSForge 内容质量体检 @ {ts} ===")
    L.append(f"[feeds] 扫描 {len(feeds)} 个 feed，发现 TIER-1 垃圾 {feed_junk_total} 条")
    for n in feed_junk_feeds:
        reasons = {}
        for j in feeds[n]["junk"]:
            reasons[j["reason"]] = reasons.get(j["reason"], 0) + 1
        detail = ", ".join(f"{k}×{v}" for k, v in reasons.items())
        L.append(f"   ⚠ {n}（{feeds[n]['items']} 条）: {detail}")
    L.append(f"[db·活跃源] 扫描全库活跃源，发现 TIER-1 垃圾 {db_junk_total} 条")
    for n in db_junk_sources:
        reasons = {}
        for j in db_active[n]["junk"]:
            reasons[j["reason"]] = reasons.get(j["reason"], 0) + 1
        detail = ", ".join(f"{k}×{v}" for k, v in reasons.items())
        L.append(f"   ⚠ {n}（{db_active[n]['items']} 条）: {detail}")
    if parserless:
        L.append(f"[需根治] 以下脏源无专用 parser（CI 会复发，需加 parser）: {parserless}")
    if inactive_sources:
        L.append(
            f"[历史残留] 不在 sites.yaml 的死库源，库内垃圾 {inactive_total} 条"
            f"（从不生成 feed，不影响输出，仅列示）: {inactive_sources}"
        )
    L.append(
        f"[一致性] sites={cons['sites']} feeds={cons['feeds']} opml={cons['opml']} "
        f"孤儿={cons['orphans'] or '无'} -> {'✅' if cons['ok'] else '❌'}"
    )
    L.append(
        f"[结论] {'✅ 无 TIER-1 内容垃圾且一致' if not junk_found else '⚠ 发现需处理的内容垃圾/不一致'}"
    )

    report = "\n".join(L)
    print(report)

    summary = {
        "timestamp": ts,
        "junk_found": junk_found,
        "feeds": {n: {"items": v["items"], "junk": v["junk"]} for n, v in feeds.items() if v["junk"]},
        "db_active": {n: {"items": v["items"], "junk": v["junk"]} for n, v in db_active.items() if v["junk"]},
        "db_inactive_residue": {n: len(v["junk"]) for n, v in db_inactive.items() if v["junk"]},
        "consistency": cons,
        "summary": {
            "feed_junk_total": feed_junk_total,
            "db_junk_total": db_junk_total,
            "feeds_with_junk": feed_junk_feeds,
            "db_sources_with_junk": db_junk_sources,
            "parserless_junk_sources": parserless,
            "inactive_residue_total": inactive_total,
        },
    }
    with open(os.path.join(ROOT, "quality_report.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n已写出 quality_report.json（junk_found={junk_found}）")

    return 1 if junk_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
