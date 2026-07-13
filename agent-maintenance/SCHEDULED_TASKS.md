# RSSForge 实时定时任务架构

> 作为项目全权维护者设计的定时任务系统。目标：把**维护/诊断/告警层**从已废弃的
> 外部 openclaw 环境彻底搬回 GitHub Actions（平台无关、环境重启不丢），与已有的
> **喂数据层**（crawl / fast_check / freshness-watchdog）拼成完整的「采集 → 健康 → 自愈」闭环。

---

## 1. 现状诊断（为什么需要这套定时任务）

前任自主 agent（运行在 `openclaw` 环境）撤离后，留下两类问题：

| 问题 | 证据 | 影响 |
|------|------|------|
| 维护脚本写死外部路径 | `diagnose_sources.py` 写 `/home/node/.openclaw/...`，该路径已不存在 | 诊断结果永远写不进仓库 |
| 维护脚本解析旧格式 | `auto_fix.py` / `diagnose_feeds.py` 解析 `- site_id:`，真实 `sites.yaml` 是 `- url:` | 解析出 0 个站点，形同虚设 |
| 维护脚本从未被调度 | `agent-artifacts/scripts/*` 从没被任何 workflow 调用 | 维护层整体离线 |
| 维护计划与实现脱节 | `MAINTENANCE_PLAN.md` 提到 `monitor_enhanced.py`/`auto_fix.py`，但逻辑错配 | 计划漂亮、落地为零 |
| 调度器状态未持久化 | `scheduler_state.json={}`、`adaptive_tiers.json={}` | 智能调度失效（见 issue #115） |

**结论**：GitHub Actions 的「喂数据」一直在跑（crawl/fast_check 最近运行均 success），
但「维护」是真空的。本项目约 **30% 健康率**（43 活跃 / 13 正常产出 / 28 零内容），
22 个长期未处理的 open issue 没人自动跟进。这套定时任务就是来填这个坑的。

---

## 2. 定时任务总览

| 任务 (workflow) | 触发频率 | 模式 | 职责 | 自愈/告警 |
|----------------|----------|------|------|------------|
| `crawl.yml` | 每 30 分 + 7/12/18/22 点保底 | 采集 | 全量爬取 → 生成 RSS/OPML/索引 | 失败重试 5 次 |
| `fast_check.yml` | 每 15 分 | 采集 | 高频增量，只动 `feeds_meta.json` | 停滞报警 |
| `freshness-watchdog.yml` | 每 20 分 | **自愈** | feed 超 55 分未重建 → 自动重触发 fast_check | ✅ 自愈闭环 |
| `blacklist-check.yml` | push/PR 改 sites/blacklist | 门禁 | 黑名单 CI 守卫 | 违规则构建失败 |
| `test.yml` | push/PR `**.py` | 质量 | pytest 回归 | 失败阻断合并 |
| `daily_summary.yml` | 每天 22:00 北京 | 报告 | `alerter.py` 每日摘要 | 提交摘要 |
| **`health-monitor.yml`** 🆕 | **每 6 小时** + 手动 | **健康守卫** | 健康率/零内容/硬死站探测 → 自动建/更新告警 Issue | ✅ 实时告警 |
| **`weekly-maintenance.yml`** 🆕 | **每周日 23:00 北京** + 手动 | **深度维护** | 补全 `feeds_meta` url、迁移硬死站、生成周报 | ✅ 自动修复+推送 |

> 🆕 = 本次新增。两个新 workflow 全部建立在 `agent-maintenance/maintain.py` 这一个引擎上。

---

## 3. 核心引擎：`agent-maintenance/maintain.py`

把原先散落、错配、离线的 `monitor_enhanced.py` / `auto_fix.py` / `diagnose_feeds.py`
整合为一个**贴合真实数据格式**、**可在 GitHub Actions 独立运行**的脚本。

### 3.1 设计原则
- **平台无关**：只用内置 `GITHUB_TOKEN` + `gh` CLI，不依赖任何外部 PAT 或私有路径。
- **只读优先**：`--report` 模式只读取本地数据 + 做 HTTP 探针，仅写出报告 JSON，**不改动任何源配置**。
- **可逆修复**：`--deep` 模式只做两种可逆操作——补全 `feeds_meta` 的 `url` 字段、把**硬死站**从 active 迁到 `dead_sites`（既有维护惯例，且可随时移回）。
- **保守判定**：软故障（SPA / JS 重定向 / 5xx / SSL）**只报告、不迁移**，避免误伤可用 `js_render` 恢复的站点。

### 3.2 两种模式
```
python agent-maintenance/maintain.py --report [--no-network]   # 监测：健康计算 + HTTP 探针 + 报告 + 告警 Issue
python agent-maintenance/maintain.py --deep                 # 深度：在 --report 基础上应用修复并提交推送
python agent-maintenance/maintain.py --self-test            # 自检
```

### 3.3 探针分类与处置
| 分类 | 含义 | 自动处置 |
|------|------|----------|
| `OK` | 可访问、有内容 | — |
| `DNS_FAIL` | 域名无法解析 | 🔴 硬死站 → 迁移 |
| `CONN_REFUSED` | 连接被拒 | 🔴 硬死站 → 迁移 |
| `CONN_TIMEOUT` | 连接超时 | 🔴 硬死站 → 迁移 |
| `HTTP_4XX` | 404/410 等 | 🔴 硬死站 → 迁移 |
| `EMPTY` | 200 但响应体过小 | 🔴 硬死站 → 迁移 |
| `JS_REDIRECT` | 需 JS 渲染 | 🟡 报告，建议加 `js_render` |
| `SPA` | 单页应用静态无列表 | 🟡 报告，建议加 `js_render` |
| `HTTP_5XX` / `SMALL` | 服务端错 / 疑似反爬 | 🟡 报告，观察 |
| `UNKNOWN` | 其他异常 | 🟡 报告 |

### 3.4 健康指标（实测基线 2026-07-13）
```
活跃站点 active_sites   = 43
已标记死站 dead_sites    = 13
正常产出 feed working    = 13
0 内容活跃站 zero       = 28
健康率 health_ratio      = 30.2%   （告警阈值 50%）
feeds_meta 缺失 url     = 13 个  ← --deep 可自动补全
```

---

## 4. 自愈闭环（端到端）

```
┌─────────────────┐   每30分   ┌──────────────────┐
│  crawl.yml      │ ─────────► │  全量爬取 + 生成   │
│  fast_check.yml │ ──每15分─► │  RSS / OPML / 索引 │
└─────────────────┘            └──────────────────┘
        │                                  │
        │ 每20分                        │ feeds 写入 GitHub Pages
        ▼                                  ▼
┌─────────────────┐   feed 超 55 分?  ┌──────────────────┐
│ freshness-      │ ── 是 ──────────►│  自动重触发         │  ← 自愈①：新鲜度
│ watchdog.yml    │                   │  fast_check.yml      │
└─────────────────┘                   └──────────────────┘
                                                 
        ▼ 每 6 小时
┌─────────────────┐
│ health-monitor  │ ── 健康率<50% 或 出现硬死站? ──► 自动建/更新告警 Issue   ← 实时告警
│   .yml         │
└─────────────────┘
        │
        │ 每周日 23:00
        ▼
┌─────────────────┐
│ weekly-        │ ── 补全 feeds_meta.url + 迁移硬死站 + 生成周报 + 推送   ← 自愈②：修复
│ maintenance.yml │
└─────────────────┘
```

---

## 5. 与既有 issue 的衔接

新引擎直接服务于这些长期挂起的 issue：

| Issue | 由谁解决 |
|-------|------------|
| #130 31 个订阅源持续零内容 | `health-monitor` 持续探测并告警；`weekly` 迁移确认死站 |
| #131 feeds_meta.json 应过滤零内容源 | `--deep` 补全 `url`（同名问题：缺失字段自动修复） |
| #115 smart_scheduler 相对路径 → 状态丢失 | 本架构不依赖调度器状态文件，报告/修复均读本地真实数据 |
| #117 黑名单未解码 URL 编码可绕过 | `blacklist-check.yml` 门禁持续生效（非本次范围，但链路保留） |

---

## 6. 运维手册（恢复 / 手动触发）

```bash
# 手动跑一次健康检查（本地，不建 Issue）
python agent-maintenance/maintain.py --report --no-network

# 手动跑一次（含 HTTP 探针，非 Actions 环境不建 Issue）
python agent-maintenance/maintain.py --report

# 手动深度维护（会改 sites.yaml / feeds_meta.json 并提交）
python agent-maintenance/maintain.py --deep

# 在 GitHub 网页手动触发两个新 workflow：
#   Actions → Health Monitor → Run workflow
#   Actions → Weekly Maintenance → Run workflow

# 诊断零内容源（已修复写路径）
python diagnose_sources.py        # 输出 diagnose_results.json（仓库根）
```

---

## 7. 后续可扩展（不在本次范围）

- [ ] `weekly-maintenance` 增加「新源发现」：搜索线报/羊毛类新站，测活后开 PR。
- [ ] 把 22 个历史 open issue 中可自动修复的（#115/#117/#123…）纳入 `--deep` 流水线。
- [ ] 邮件/Webhook 通知：仓库已有 `SMTP_*` / `CLAWEMAIL_*` secret，可作为 Issue 告警的备用通道。
- [ ] 健康率达标（>90%）后，将 `health-monitor` 降频至每日 2 次以省额度。

---

**设计者**：RSSForge 全权维护者（WorkBuddy）
**生效日期**：2026-07-13
**状态**：✅ 引擎 + 两个 workflow 已落地，待首次自动运行验证
