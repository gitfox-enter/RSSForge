#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 维护引擎 (Maintenance Engine)
======================================

作为 RSSForge 的「全权维护者」运行的统一维护脚本，把原先散落在已废弃
外部环境 (openclaw) 里的 monitor_enhanced.py / auto_fix.py / diagnose_feeds.py
整合为一个贴合真实数据格式的、可在 GitHub Actions 上独立运行的工具。

设计原则
--------
1. 平台无关：只用内置 GITHUB_TOKEN + gh CLI，不依赖任何外部 PAT 或私有路径。
2. 只读优先：``--report`` 模式只读取本地数据 + 做 HTTP 探针，仅写出报告 JSON，
   不改动任何源配置；``--deep`` 模式才应用修复（且仅对「硬死站」做可逆迁移）。
3. 自愈闭环：配合 health-monitor.yml（每 6h）与 weekly-maintenance.yml（每周日）
   形成「监测 → 告警 → 深度修复」的实时定时任务链。

数据格式（实测）
----------------
- sites.yaml: 顶层 ``sites``(list of dict: url/name/tier/interval/fast_check/js_render)
            顶层 ``dead_sites``(dict: url -> {reason, confirmed_at, test_result})
- feeds_meta.json: key 为站点名(e.g. "线报酷")，含 count/feed_url/site_url/items_hash
- crawl_status.json / scheduler_state.json / adaptive_tiers.json: 调度器状态

用法
----
    python agent-maintenance/maintain.py --report [--no-network]
    python agent-maintenance/maintain.py --deep
    python agent-maintenance/maintain.py --self-test
"""

import argparse
import json
import os
import re
import ssl
import sys
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO = os.environ.get("GITHUB_REPOSITORY", "gitfox-enter/RSSForge")
ROOT = Path(__file__).resolve().parent.parent          # 仓库根目录
SITES_YAML = ROOT / "sites.yaml"
FEEDS_META = ROOT / "feeds_meta.json"
CRAWL_STATUS = ROOT / "crawl_status.json"
SCHEDULER_STATE = ROOT / "scheduler_state.json"
ADAPTIVE_TIERS = ROOT / "adaptive_tiers.json"
REPORT_DIR = ROOT / "agent-maintenance" / "logs"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# 健康阈值（健康率低于此值即触发告警 Issue）
HEALTH_RATIO_ALERT = 0.50
# 单轮诊断并发数
DIAG_CONCURRENCY = 8
DIAG_TIMEOUT = 12

# 探针结果分类
CAT_OK = "OK"                       # 可访问、有内容
CAT_DNS_FAIL = "DNS_FAIL"           # 域名无法解析
CAT_CONN_REFUSED = "CONN_REFUSED"   # 连接被拒
CAT_CONN_TIMEOUT = "CONN_TIMEOUT"    # 连接超时
CAT_HTTP_4XX = "HTTP_4XX"          # 404/410 等
CAT_HTTP_5XX = "HTTP_5XX"          # 5xx 服务端错误
CAT_EMPTY = "EMPTY"                 # 200 但响应体过小（站点已空）
CAT_JS_REDIRECT = "JS_REDIRECT"     # 需 JS 渲染（静态无内容）
CAT_SPA = "SPA"                     # 单页应用，静态无列表
CAT_SMALL = "SMALL"                 # 内容偏少，疑似反爬/登录墙
CAT_UNKNOWN = "UNKNOWN"

# 硬死站分类（--deep 模式下迁移到 dead_sites，可逆）
HARD_DEAD = {CAT_DNS_FAIL, CAT_CONN_REFUSED, CAT_CONN_TIMEOUT, CAT_HTTP_4XX, CAT_EMPTY}

_lock = threading.Lock()


# ============================================================
# 1. 数据加载
# ============================================================

def load_sites_yaml():
    """返回 (active_sites:list[dict], dead_sites:dict)。"""
    if not SITES_YAML.exists() or yaml is None:
        return [], {}
    data = yaml.safe_load(SITES_YAML.read_text(encoding="utf-8")) or {}
    active = data.get("sites", []) or []
    dead = data.get("dead_sites", {}) or {}
    return active, dead


def load_feeds_meta():
    if not FEEDS_META.exists():
        return {}
    try:
        return json.loads(FEEDS_META.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_json_safe(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None


# ============================================================
# 2. HTTP 探针
# ============================================================

def _make_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def diagnose_url(url: str):
    """对单个 URL 做轻量 HTTP 探针，返回分类与元信息。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=DIAG_TIMEOUT, context=_make_ctx()) as resp:
            body = resp.read()
            code = getattr(resp, "status", resp.getcode())
    except urllib.error.HTTPError as e:
        code = e.code
        if 400 <= code < 500:
            return {"url": url, "status": CAT_HTTP_4XX, "code": code, "size": 0}
        return {"url": url, "status": CAT_HTTP_5XX, "code": code, "size": 0}
    except urllib.error.URLError as e:
        reason = str(getattr(e, "reason", e))
        if "Name or service not known" in reason or "getaddrinfo" in reason or "NameResolutionError" in reason:
            return {"url": url, "status": CAT_DNS_FAIL, "code": 0, "size": 0, "reason": reason}
        if "Connection refused" in reason:
            return {"url": url, "status": CAT_CONN_REFUSED, "code": 0, "size": 0, "reason": reason}
        if "timed out" in reason or "Timeout" in reason:
            return {"url": url, "status": CAT_CONN_TIMEOUT, "code": 0, "size": 0, "reason": reason}
        return {"url": url, "status": CAT_CONN_TIMEOUT, "code": 0, "size": 0, "reason": reason}
    except ssl.SSLError as e:
        return {"url": url, "status": CAT_CONN_TIMEOUT, "code": 0, "size": 0, "reason": f"SSL:{e}"}
    except Exception as e:  # noqa: BLE001
        return {"url": url, "status": CAT_UNKNOWN, "code": 0, "size": 0, "reason": f"{type(e).__name__}:{e}"}

    size = len(body)
    text = body.decode("utf-8", "ignore")
    if size < 200:
        return {"url": url, "status": CAT_EMPTY, "code": code, "size": size}
    if size < 3000:
        # 进一步判断是否 JS 重定向 / SPA / 登录墙
        low = text[:1500].lower()
        if "setTimeout(" in text and "reload" in text.lower():
            return {"url": url, "status": CAT_JS_REDIRECT, "code": code, "size": size}
        if "window.location" in text:
            return {"url": url, "status": CAT_JS_REDIRECT, "code": code, "size": size}
        if 'id="app"' in text or 'id="root"' in text:
            return {"url": url, "status": CAT_SPA, "code": code, "size": size}
        return {"url": url, "status": CAT_SMALL, "code": code, "size": size}
    if 'id="app"' in text[:20000] and text.count("href=") < 3:
        return {"url": url, "status": CAT_SPA, "code": code, "size": size}
    return {"url": url, "status": CAT_OK, "code": code, "size": size}


def diagnose_many(urls):
    """并发探针，返回 {url: result}。"""
    results = {}
    if not urls:
        return results
    with ThreadPoolExecutor(max_workers=DIAG_CONCURRENCY) as ex:
        futs = {ex.submit(diagnose_url, u): u for u in urls}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                results[u] = fut.result()
            except Exception as e:  # noqa: BLE001
                results[u] = {"url": u, "status": CAT_UNKNOWN, "code": 0, "size": 0, "reason": str(e)}
    return results


# ============================================================
# 3. 健康计算
# ============================================================

def compute_health(active, dead, feeds_meta):
    """计算整体健康指标。"""
    active_count = len(active)
    dead_count = len(dead)
    meta_by_name = {k: v for k, v in feeds_meta.items()}
    working = {name: m for name, m in meta_by_name.items() if m.get("count", 0) > 0}

    # 把每个活跃站点匹配到 feeds_meta（按 name）
    working_names = sorted(n for n in working.keys() if n)
    zero_urls = []
    for s in active:
        nm = s.get("name")
        u = s.get("url")
        if nm and nm not in working and u:
            zero_urls.append(u)

    total_monitored = active_count + dead_count
    health_ratio = (len(working) / active_count) if active_count else 0.0
    return {
        "active_sites": active_count,
        "dead_sites": dead_count,
        "working_feeds": len(working),
        "zero_content_active": len(zero_urls),
        "total_monitored": total_monitored,
        "health_ratio": round(health_ratio, 4),
        "working_names": working_names,
        "zero_urls": sorted(zero_urls),
    }


# ============================================================
# 4. 报告
# ============================================================

def build_report(health, diags, meta_missing_url, hard_dead, soft_problems):
    now = datetime.now(timezone(timedelta(hours=8)))
    lines = []
    lines.append(f"# RSSForge 健康报告 · {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)\n")
    lines.append("> 由 `agent-maintenance/maintain.py` 自动生成\n")
    lines.append("## 概览\n")
    lines.append(f"- 活跃站点: **{health['active_sites']}**")
    lines.append(f"- 已标记死站: **{health['dead_sites']}**")
    lines.append(f"- 正常产出 feed: **{health['working_feeds']}**")
    lines.append(f"- 0 内容活跃站: **{health['zero_content_active']}**")
    ratio = health["health_ratio"] * 100
    emoji = "✅" if health["health_ratio"] >= HEALTH_RATIO_ALERT else "⚠️"
    lines.append(f"- 健康率: **{emoji} {ratio:.1f}%** （告警阈值 {HEALTH_RATIO_ALERT*100:.0f}%）\n")

    if hard_dead:
        lines.append("## 🔴 硬死站（建议迁移至 dead_sites）\n")
        lines.append("| 站点 | URL | 诊断 |")
        lines.append("|------|-----|------|")
        for d in hard_dead:
            lines.append(f"| {d.get('name','?')} | {d['url']} | {d['status']} |")
        lines.append("")
    if soft_problems:
        lines.append("## 🟡 软故障（需人工/JS渲染介入）\n")
        lines.append("| 站点 | URL | 诊断 |")
        lines.append("|------|-----|------|")
        for d in soft_problems:
            lines.append(f"| {d.get('name','?')} | {d['url']} | {d['status']} |")
        lines.append("")
    if meta_missing_url:
        lines.append(f"## 🟠 feeds_meta.json 缺失 url 字段: {len(meta_missing_url)} 个\n")
        lines.append("（可由 `--deep` 模式从 sites.yaml 自动补全）\n")
    lines.append("---\n*生成时间: " + now.isoformat() + "*")
    return "\n".join(lines)


# ============================================================
# 5. GitHub Issue 告警（去重）
# ============================================================

ISSUE_TITLE = "RSSForge 健康守卫 · 自动监测"


def _run_gh(args):
    import subprocess
    return subprocess.run(["gh", "issue"] + args, capture_output=True, text=True, timeout=30)


def ensure_alert_issue(report_md, health):
    """若处于 Actions 环境且有异常，则创建/更新唯一告警 Issue。返回布尔。"""
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("[issue] 非 Actions 环境，跳过 Issue 创建")
        return False
    if health["health_ratio"] >= HEALTH_RATIO_ALERT and health["zero_content_active"] == 0:
        print("[issue] 健康率达标且无 0 内容站，无需告警")
        return False

    # 去重：查找已开放同名 Issue
    existing = _run_gh(["list", "--state", "open", "--search", ISSUE_TITLE, "--limit", "5"])
    issue_num = None
    for line in existing.stdout.strip().splitlines():
        if ISSUE_TITLE in line:
            m = re.match(r"\s*(\d+)", line)
            if m:
                issue_num = m.group(1)
                break

    body = report_md + f"\n\n---\n*自动维护引擎 · 健康率 {health['health_ratio']*100:.1f}%*"

    # 标签容错：确保标签存在，缺失则尝试创建（忽略失败）
    labels = ["maintenance", "automated"]
    import subprocess as _sp
    for lbl in labels:
        _sp.run(["gh", "label", "create", lbl, "--description", "RSSForge 自动维护引擎",
                   "--color", "0E8A16"], capture_output=True, text=True)

    if issue_num:
        r = _run_gh(["edit", issue_num, "--body", body])
        print(f"[issue] 已更新 Issue #{issue_num}" if r.returncode == 0 else f"[issue] 更新失败: {r.stderr[:120]}")
        return r.returncode == 0
    r = _run_gh(["create", "--title", ISSUE_TITLE, "--body", body, "--label", ",".join(labels)])
    print(f"[issue] 创建结果: {r.stdout.strip() or r.stderr[:120]}")
    return r.returncode == 0


# ============================================================
# 6. 深度修复（--deep，仅可逆操作）
# ============================================================

def fix_feeds_meta_urls(active, feeds_meta):
    """把 sites.yaml 的 url 补全到 feeds_meta.json（按 name 匹配）。返回修复数。"""
    name_to_url = {s.get("name"): s.get("url") for s in active if s.get("name") and s.get("url")}
    fixed = 0
    for name, m in feeds_meta.items():
        if not m.get("url") and name in name_to_url:
            m["url"] = name_to_url[name]
            fixed += 1
    if fixed:
        FEEDS_META.write_text(json.dumps(feeds_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return fixed


def move_hard_dead_to_config(active, dead, hard_dead):
    """把硬死站从 sites.yaml 的 active 列表迁移到 dead_sites（可逆）。返回 (新active, 新dead)。"""
    dead_urls = {d["url"] for d in hard_dead}
    today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    new_active = [s for s in active if s.get("url") not in dead_urls]
    new_dead = dict(dead)
    for d in hard_dead:
        new_dead[d["url"]] = {
            "reason": f"自动维护引擎判定为硬死站（{d['status']}）",
            "confirmed_at": today,
            "test_result": d.get("reason") or d["status"],
            "name": d.get("name"),
        }
    return new_active, new_dead


def write_sites_yaml(active, dead):
    # 仅重写 sites 与 dead_sites 两段，其余顶层键（如有）保留
    data = {}
    if SITES_YAML.exists() and yaml:
        data = yaml.safe_load(SITES_YAML.read_text(encoding="utf-8")) or {}
    data["sites"] = active
    data["dead_sites"] = dead
    SITES_YAML.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


# ============================================================
# 7. 主流程
# ============================================================

def run(mode, do_network):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d_%H-%M")

    active, dead = load_sites_yaml()
    feeds_meta = load_feeds_meta()
    health = compute_health(active, dead, feeds_meta)

    # feeds_meta 缺失 url 检测
    meta_missing_url = [n for n, m in feeds_meta.items() if not m.get("url")]

    diags = {}
    hard_dead = []
    soft_problems = []

    if do_network:
        # 对 0 内容且未在 dead_sites 的活跃站点做探针
        dead_url_set = set(dead.keys())
        targets = []
        for s in active:
            u = s.get("url")
            if u and u not in dead_url_set and u in set(health["zero_urls"]):
                targets.append(s)
        print(f"[diag] 对 {len(targets)} 个 0 内容活跃站点做 HTTP 探针 ...")
        results = diagnose_many([t["url"] for t in targets])
        for t in targets:
            r = results.get(t["url"], {"url": t["url"], "status": CAT_UNKNOWN})
            r["name"] = t.get("name")
            diags[t["url"]] = r
            if r["status"] in HARD_DEAD:
                hard_dead.append(r)
            elif r["status"] not in (CAT_OK,):
                soft_problems.append(r)

    report_md = build_report(health, diags, meta_missing_url, hard_dead, soft_problems)

    # 写出报告 JSON（report 模式也写，便于历史追溯）
    report_obj = {
        "generated_at": now.isoformat(),
        "health": health,
        "feeds_meta_missing_url": meta_missing_url,
        "hard_dead": hard_dead,
        "soft_problems": soft_problems,
        "diagnostics": diags,
    }
    report_path = REPORT_DIR / f"health_{stamp}.json"
    report_path.write_text(json.dumps(report_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "latest.json").write_text(json.dumps(report_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report_md)

    if mode == "report":
        ensure_alert_issue(report_md, health)
        print(f"[done] 报告已写入 {report_path.name}")
        return

    # ---- deep 模式 ----
    fixed = fix_feeds_meta_urls(active, feeds_meta)
    print(f"[deep] feeds_meta 补全 url: {fixed} 个")
    if hard_dead:
        new_active, new_dead = move_hard_dead_to_config(active, dead, hard_dead)
        write_sites_yaml(new_active, new_dead)
        print(f"[deep] 迁移 {len(hard_dead)} 个硬死站到 dead_sites")
    else:
        print("[deep] 无硬死站需迁移")

    # 生成周报
    weekly = REPORT_DIR.parent / f"weekly-report_{now.strftime('%Y-%m-%d')}.md"
    weekly.write_text(report_md, encoding="utf-8")
    print(f"[deep] 周报已写入 {weekly.name}")
    ensure_alert_issue(report_md, health)
    commit_and_push(fixed, len(hard_dead))


def commit_and_push(fixed_urls, moved_dead):
    import subprocess
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("[git] 非 Actions 环境，跳过提交")
        return
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=False)
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=False)
    files = ["feeds_meta.json", "sites.yaml", "agent-maintenance/logs/", "agent-maintenance/weekly-report_*.md"]
    subprocess.run(["git", "add", "-u", *files], check=False)
    # 也加入新增的周报文件
    subprocess.run(["git", "add", "agent-maintenance/"], check=False)
    msg = (f"maintain: 自动维护 — 补全 {fixed_urls} 个 url、迁移 {moved_dead} 个硬死站 "
            f"({datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')})")
    rc = subprocess.run(["git", "diff", "--staged", "--quiet"], check=False).returncode
    if rc != 0:
        subprocess.run(["git", "commit", "-m", msg], check=False)
        for _ in range(5):
            subprocess.run(["git", "pull", "--no-rebase", "--no-commit", "origin", "main"], check=False)
            if subprocess.run(["git", "push", "origin", "main"], check=False).returncode == 0:
                print("[git] 已提交并推送")
                return
            import time
            time.sleep(5)
        print("[git] 推送失败（已达重试上限）")
    else:
        print("[git] 无变更需提交")


def self_test():
    active, dead = load_sites_yaml()
    feeds_meta = load_feeds_meta()
    assert isinstance(active, list) and isinstance(dead, dict)
    h = compute_health(active, dead, feeds_meta)
    print("self-test OK:", json.dumps(h, ensure_ascii=False))
    # 单站点探针冒烟测试（用仓库里一个已知站点）
    if active:
        r = diagnose_url(active[0]["url"])
        print(f"probe {active[0]['url']} -> {r['status']}")


def main():
    ap = argparse.ArgumentParser(description="RSSForge 维护引擎")
    ap.add_argument("--report", action="store_true", help="监测模式（只读 + 报告 + 告警）")
    ap.add_argument("--deep", action="store_true", help="深度维护模式（应用修复并提交）")
    ap.add_argument("--no-network", action="store_true", help="跳过 HTTP 探针")
    ap.add_argument("--self-test", action="store_true", help="自检")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    mode = "deep" if args.deep else "report"
    do_network = not args.no_network
    run(mode, do_network)


if __name__ == "__main__":
    main()
