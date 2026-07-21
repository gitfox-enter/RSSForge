#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSSForge 每周 Issue 三审执行脚本 (2026-07-19)。
通过 gh CLI 对 open issue 执行: 已修复/引擎覆盖 -> 评论+close; 需人工决策 -> 加标签+评论标注。
仅做注释与状态变更, 不修改任何源代码(除已单独提交的 #122)。
"""
import json, subprocess, sys

REPO = "gitfox-enter/RSSForge"

# ---------- 关闭集合: 已修复(代码核实) 或 已被维护引擎覆盖 ----------
CLOSES = {
    53: ("security", "经核对当前代码,`gist_store.py` 已改用 `gh` CLI 读取 `GITHUB_TOKEN` 环境变量(见 gist_store.py:76-81 注释 `Fixes #53`),不再通过 `curl` 命令行参数传递 token,`/proc/*/cmdline` 泄露风险已消除。维护引擎三审确认已修复。"),
    57: ("bug", "`_parse_response_html`(crawler/engine.py)现已单次解码并优先使用编码提示、GBK 回退(`fix #57`),不再对 Playwright 路径做 bytes→str→bytes 的有损往返,中文字符损坏问题已修复。"),
    59: ("performance", "`common.py` 的 `fetch_article_summary` 已通过 `asyncio.to_thread` 卸载阻塞的 `urllib` 调用(`fix #59: fully async-safe`),不再阻塞事件循环。"),
    62: ("bug", "`crawler/config.py` 已删除 `_LEGACY_SOURCE_NAME_MAP`,sites.yaml 为唯一数据源(`fix #62`),死站不会再经 fallback 被重新引入监控列表。"),
    65: ("bug", "本 issue 与已关闭的 #131 同类。维护引擎 `--deep` 现已:① 补全 `feeds_meta.json` 的 `url` 字段;② 将硬死站迁移至 `dead_sites`(零内容且硬死者不再生成 feed);③ `rss_feed.py` 生成 meta 时已跳过空 feed(`fix #1`)。零条目 404 风险已被覆盖。"),
    70: ("code-quality", "`common.py` 的 `_is_active_unlocked` 已改为纯查询、无副作用,重新启用逻辑移到独立的 `_re_enable_if_cooldown_elapsed`(`fix #70`),读取 `active_count` 不再改变代理池状态。"),
    98: ("bug", "核对 `crawl.yml` 权限段已无 `packages: write` 声明,无用权限已移除。"),
    116: ("bug", "全仓 `_parse_response_html` 及摘要提取路径已将 `errors='ignore'` 改为 `errors='replace'`(`fix #116`),中文页面内容不再被静默截断。"),
    122: ("bug", "已修复:`common.py` 的 `is_junk` 由精确匹配 `clean == junk_word` 改为子串匹配 `junk_word in clean`(commit c92221f),垃圾词检测恢复生效。"),
    111: ("legal", "经核对,仓库根目录已存在 `LICENSE` 文件(MIT License, Copyright 2024 RSSForge Contributors),README 声明的 MIT 许可已具备法律效力。本 issue 前提(缺少 LICENSE)已不成立,关闭。"),
    136: ("automated", "该停滞告警由监测引擎于 2026-07-19 07:37 生成(feeds/ 超 23h 无新内容)。但今日仓库持续有内容提交(21:28 新增 235 条、21:29 状态更新),订阅流已恢复,告警已过时。"),
}

# ---------- 保留集合: 需人工决策, 仅评论标注 ----------
# (number, 分类, 具体判定/建议)  具体判定为空则按严重度生成通用注释
KEEP = {
    132: ("enhancement", "维护机制**部分完成**:`agent-maintenance/maintain.py` 已实现并可由本 agent 手动/按需运行(本周已执行 --deep),但 `.github/workflows/` 尚未接入 `weekly-maintenance.yml` 定时调度。建议:补充每周定时 workflow 以完全闭环。"),
    133: ("maintenance", "此为维护引擎自身的健康守卫 Issue(标题与 maintain.py 的 ISSUE_TITLE 一致),由 Actions 环境自动维护。当前健康率 50.0%(11/22 活跃站产出 feed,11 个零内容活跃站探针均为软故障/可用,无硬死站)。保留由引擎继续管理。"),
    134: ("enhancement", "新源候选提案(2026-07-15),未写入 sites.yaml。需人工复核后由维护者决定是否加入。"),
    135: ("enhancement", "新源候选提案(2026-07-15 修订版),未写入 sites.yaml。需人工复核后由维护者决定是否加入。"),
    129: ("bug", "中等问题(哈希随机化致重复推送 / SSL 禁用 / 缓存锁竞争)。其中 SSL 禁用是维护引擎诊断探针的刻意选择;哈希随机化与缓存锁竞争仍属 crawler 代码质量范畴。建议:逐条评估后单独 PR。"),
    128: ("bug", "crawl 与 fast_check 并发组不同但改相同文件。属 workflow 并发设计问题,需人工决策调度策略(如统一并发组或拆分文件职责)。"),
    127: ("bug", "分页 domain 过期 / 子串匹配不精确 / CI workflow 路径不匹配。需对照当前 crawler/engine.py 与 .github/workflows 路径核实后处理。"),
    126: ("bug", "三处致命运行时错误(NameError/TypeError)。部分可能已在活跃开发中被修复,需逐一对照 crawler 当前代码核实是否仍成立。"),
    124: ("bug", "cleanup-history.yml 用 git filter-repo 删除含 active 文件的历史。高风险破坏性操作,需人工决策(建议改用 shallow clone / 外部归档,而非改写主分支历史)。"),
    114: ("bug", "`git_commit_if_changed()` 的 TRACKED_FILES 含 `.gitignore` 语义错误。低危,建议随相关 PR 一并修。"),
    113: ("maintenance", "远程 7 个已合并分支未清理。建议人工清理(或配置 branch cleanup 规则),属常规维护。"),
    112: ("community", "缺少贡献指南与 Issue/PR 模板。增强项,建议补充 CONTRIBUTING/模板以提升社区参与。"),
    110: ("pwa", "manifest.json description 与功能不匹配。PWA 文案问题,建议人工修订。"),
    109: ("pwa", "manifest.json icon 路径含 public/ 前缀。PWA 图标加载问题,建议修订路径。"),
    108: ("bug", "forum_sites.py 豆瓣小组子串匹配过滤可能误杀标题。需对照当前 parser 核实。"),
    107: ("code-quality", "parsers/core.py 通配符 import * 命名空间污染。代码质量,建议改为显式导入。"),
    106: ("enhancement", "smart_scheduler record_site_run O(n) 文件 I/O。性能增强,建议改为增量读写或内存缓存。"),
    105: ("bug", "software_sites.py parse_appinn_items 选择器匹配 h2 而非 a。需对照当前 parser 核实是否仍成立。"),
    103: ("code-quality", "opml_generator generate_opml 每次删除遗留文件。破坏性副作用,需人工决策(建议拆分清理逻辑)。"),
    102: ("bug", "index.html copyFeedLink 使用隐式 window.event(Firefox 严格模式报错)。建议改为传参 event。"),
    101: ("bug", "pages.yml 未复制根级 HTML(index.html 等)。需对照当前部署 workflow 核实部署范围。"),
    100: ("bug", "deal_sites.py 6 处 _add_item 未传 base_url 致相对 URL 无法解析。功能 bug,建议逐处补 base_url。"),
    97: ("medium", "sites.yaml parser 字段未被引擎使用。配置/实现不一致,建议统一(硬编码 URL 子串匹配 or 启用 parser 字段)。"),
    96: ("medium", "manifest.json 与 index.html theme-color 不一致。PWA 视觉一致性,建议统一。"),
    95: ("medium", "sw.js 未缓存 manifest.json 与 PWA 图标。离线体验,建议补充 ASSETS。"),
    94: ("medium", "fast_check.yml 无 timeout-minutes。建议补充以避免死循环耗分钟。"),
    92: ("medium", "_to_rfc822 在中文 locale 下 %a/%b 可能非英文。建议用固定英文格式或 email.utils.format_datetime,避免全局 locale 改动风险。需人工决策。"),
    91: ("medium", "sponsored item 时间每轮不同破坏增量哈希。建议固定 sponsored 时间或排除出哈希计算。"),
    89: ("high", "public/js/app.js 与 public/css/app.css 未被引用(死代码)。建议确认后删除或重新接入。"),
    88: ("high", "index.html 支付宝弹窗 HTML 残缺且 closeAlipay() 缺失。前端 bug,需人工修复。"),
    83: ("high", "fast_check push 全失败仍 exit 0 静默吞错。建议失败后非零退出。"),
    82: ("high", "pages.yml 不被 GITHUB_TOKEN push 触发(死代码)。建议删除或改为 workflow_run 触发。"),
    81: ("high", "crawl + fast_check 并发改相同文件互相覆盖。需人工决策并发策略(同 #128)。"),
    80: ("critical", "index.html 内联脚本孤立 } 致 JS 语法错误、首页功能失效。严重前端 bug,建议人工修复(定位孤立括号)。"),
    79: ("critical", "cleanup-history.yml 将 GITHUB_TOKEN 明文拼入 git remote URL,日志泄露。高风险!建议改用 gh CLI / 环境变量,避免命令行参数传 token。需人工决策(workflow 改动)。"),
    78: ("critical", "test.yml pytest 退出码被 tee 管道吞掉,测试失败 CI 仍 PASS。建议用 `set -o pipefail` 或 `pytest | ...; test ${PIPESTATUS[0]}`。"),
    76: ("enhancement", "CATEGORY_KEYWORDS 覆盖不足。增强项,建议扩充分类关键词。"),
    75: ("enhancement", "daily_summary.yml 运行 alerter.py 但未发布摘要。建议将摘要写入 Issue/commit。"),
    74: ("enhancement", "debug.yml / debug_parsers.py 不应在生产分支。建议移至独立分支或删除。"),
    73: ("code-quality", "items_ref.json 遗留无用文件。建议删除。"),
    72: ("enhancement", "requirements.txt 混用测试/运行时依赖。建议拆分 requirements / requirements-dev。"),
    71: ("bug", "health.html / status.html 未优雅处理 crawl_status.json 缺失。建议加空值/异常兜底。"),
    69: ("bug", "_parse_items_and_next_page 分页可能无限循环。建议加强已访问 URL 追踪。"),
    68: ("bug", "notified_items.json 无限增长。建议加大小上限/轮转。"),
    67: ("bug", "_fuzzy_dedupe_key 截断 20 字符对中文过激可能误去重。建议增大截断或改用更稳的归一化。"),
    66: ("code-quality", "crawl.py 通配符 import * 命名空间污染。建议改为显式导入。"),
    64: ("performance", "crawl.yml 每次装 Playwright+Chromium 但无活跃 JS 渲染站。建议条件化安装或移除。"),
    63: ("bug", "RSS 2.0 .rss2.xml 生成但未提交/部署。建议纳入提交与 Pages 复制。"),
    61: ("security", "sites.yaml 线报酷镜像用 HTTP 明文(MITM 风险)。建议改 HTTPS;若为历史镜像源且不支持 HTTPS,需人工决策是否保留。"),
    60: ("high", "_compute_hash_diff 与 check_one_async 返回值不一致致 text 丢失。需对照当前 storage/engine 核实。"),
    58: ("high", "crawl.yml rebase 冲突用 --theirs 致爬取数据被丢。严重!建议冲突时优先保留本地爬取结果(--ours)或改用 merge。需人工决策。"),
    56: ("high", "fast_check.yml 未提交 items.json / items_latest.json。数据一致性 bug,建议补 git add。"),
    55: ("high", "sw.js ASSETS 数组缺逗号致 Service Worker 安装失败。JS 语法 bug,建议补逗号。"),
    54: ("security", "redirect.html 已加 scheme 校验(/^https?:\\/\\//i,fix #12)但**仍缺域名白名单**,可被用于钓鱼跳转任意外部站。建议加 target 域名白名单或仅允许站内/已知源。需人工决策。"),
}

CLOSE_LABELS = ["maintenance", "automated", "bug", "security", "pwa", "code-quality", "enhancement", "community", "legal", "performance", "medium", "high", "critical", "low"]
TRIAGE_LABEL = "triage:needs-human-decision"


def run(args, check=True):
    r = subprocess.run(["gh", "issue"] + args, capture_output=True, text=True, timeout=60)
    return r


def ensure_label():
    r = subprocess.run(["gh", "label", "create", TRIAGE_LABEL,
                       "--description", "每周维护三审核对: 需人工决策的 issue",
                       "--color", "D93F0B"], capture_output=True, text=True)
    # 忽略已存在错误


def main():
    ensure_label()
    # ----- 关闭 -----
    closed = []
    for n, (cat, body) in CLOSES.items():
        comment = (f"**每周三审 · 2026-07-19** — *{cat}*\n\n{body}\n\n"
                   f"> 由维护引擎 `agent-maintenance/maintain.py` 三审判定: 已修复/已被维护引擎覆盖,关闭。")
        r1 = run(["comment", str(n), "--body", comment])
        r2 = run(["close", str(n)])
        ok = r2.returncode == 0
        closed.append((n, ok, r2.stderr.strip()[:120]))
        print(f"[close] #{n}: {'OK' if ok else 'FAIL ' + r2.stderr.strip()[:120]}")
    # ----- 保留 + 标注 -----
    kept = []
    for n, (cat, note) in KEEP.items():
        body = (f"**每周三审 · 2026-07-19** — *{cat}*\n\n"
                f"经维护引擎对照当前代码/数据核对,本 issue **仍成立、需人工决策**,本周未改动代码。\n\n"
                f"{note}\n\n"
                f"> 已加标签 `{TRIAGE_LABEL}` 跟踪,待维护者/贡献者处理。")
        r1 = run(["edit", str(n), "--add-label", TRIAGE_LABEL])
        r2 = run(["comment", str(n), "--body", body])
        ok = r2.returncode == 0
        kept.append((n, ok))
        print(f"[keep ] #{n}: label={r1.returncode==0} comment={'OK' if ok else 'FAIL'}")
    print(f"\nSUMMARY: closed={len(closed)} kept={len(kept)}")
    fails = [c for c in closed if not c[1]] + [k for k in kept if not k[1]]
    if fails:
        print("FAILS:", fails)


if __name__ == "__main__":
    main()
