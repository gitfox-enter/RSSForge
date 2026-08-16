# RSSForge 每周深度维护报告 — 2026-08-16

> 维护周期：2026-08-09 → 2026-08-16（7 天）

---

## 一、CI / Actions 状态

| Workflow | 近7天运行 | 失败 | 状态 |
|---|---|---|---|
| 站点更新监控 (crawl) | ~50 | 0 | ✅ 稳定 |
| Tests | 3 | 0 | ✅ 连续通过 |
| 快速增量检查 (fast_check) | ~50 | **1** | ⚠️ 修复中（见下）|
| 每日摘要 (daily_summary) | 7 | 1 | ⚠️ 修复中（见下）|
| 其他 (blacklist/freshness/quality-guard 等) | — | 0-2 | ✅ 基本正常 |

### 🔴 根因修复：fast_check / daily_summary Push 冲突

**fast_check #992 失败根因**（08-16 05:42）：
- `docs/feeds/xian-bao-ku.xml` 和 `xian-bao-wang.xml` merge conflict
- 旧逻辑：冲突时用 `--theirs`（接受远程），但 **fast_check 才是 feeds 权威来源**，不应丢弃本地
- retry 时 git pull 失败（unmerged 文件），导致 all retry 失败

**修复方案**（commit `a1fc142`）：
- 改用 `git pull --rebase origin main --autostash`（保留本地为 authoritative）
- 冲突文件：docs/feeds/* 和 feeds_meta.json 用 `--ours`（本地权威），其他接受远程
- 改用 `--force-with-lease`（比 `--force` 安全）
- daily_summary：同样加 `git pull --rebase origin main`，并修复无 retry 逻辑

| 文件 | SHA |
|---|---|
| `.github/workflows/fast_check.yml` | `a1fc142` |
| `.github/workflows/daily_summary.yml` | `fe3beb9` |

---

## 二、订阅源健康状况

| 指标 | 上周（08-09）| 本周（08-16）| 变化 |
|---|---|---|---|
| sites.yaml 活跃源 | 25 | **28** | +3（08-12 批次）|
| feeds_meta 收录 | 14 | **28** | +14（本次修复）|
| 总条目数 | 60,019 | **84,643** | **+24,624 (+41%)** |
| 零内容源 | 0 | 0 | ✅ |
| dead_sites | 15 | 15 | — |

### 本周新增活跃源（08-12 第二批）

| 源 | RSS Feed |
|---|---|
| 阮一峰的网络日志 | https://www.ruanyifeng.com/blog/atom.xml |
| 美团技术团队 | https://tech.meituan.com/rss.xml |
| 极客公园 | https://www.geekpark.net/rss |

### feeds_meta 修复说明（系统性问题）

feeds_meta.json 在每次 crawler push 时被整体覆盖，只保留实际产出条目的源（11 个）。上周补的 3 个 RSS 源被覆盖丢失。本周补全所有 28 个活跃源（commit `2928ccc8`）。

**系统性建议**：`maintain.py` 应区分"活跃源清单（sites.yaml）"与"被追踪 feed 清单（feeds_meta）"，避免 crawler 覆盖非产出源。

### dead_sites（15 个，确认稳定）

与上周一致，无新增。

---

## 三、Issues 审计

**总 open：57 个**（上周 50 → 本周 57，新增 7 个）

本周无 issue 更新（08-09 以来无变更记录）。open 增量 7 个为用户/系统新建，待下次人工处理。

### 仍需优先处理的 BUG

| # | 标题 | 优先级 | 备注 |
|---|---|---|---|
| #79 | [CRITICAL] GITHUB_TOKEN 明文拼入 git remote | CRITICAL | Security |
| #54 | redirect.html 开放重定向 | CRITICAL | Security |
| #80 | index.html 内联脚本 JS 语法错误 | CRITICAL | 首页功能失效 |
| #81 | crawl + fast_check 并发数据竞争 | HIGH | 数据覆盖 |
| #82 | pages.yml 永远不会被触发（死代码）| HIGH | |
| #83 | fast_check push 失败后 exit 0 静默 | HIGH | 已部分改善 |
| #88 | 支付宝弹窗 HTML 残缺 | HIGH | |
| #100 | _add_item() 未传 base_url | HIGH | |
| #128 | crawl/fast_check 并发冲突 | HIGH | 仍是根因 |

### 本周解决的 Issue
- ✅ **#147**：[MAINTENANCE] feeds_meta 漂移（已修复并关闭）

---

## 四、本周改动记录

| SHA | 说明 |
|---|---|
| `a1fc142` | **fix(fast_check): pull --rebase --autostash + force-with-lease** |
| `fe3beb9` | **fix(daily_summary): add pull --rebase before push** |
| `2928ccc8` | **chore(feeds): add 17 missing sources to feeds_meta.json** |
| 📋 | **issue #147 closed**（feeds_meta drift 已修复）|

---

## 五、下周建议

1. 🔴 **优先级高**：修复 3 个 CRITICAL Security/功能失效问题（#79/#54/#80）
2. **crawl vs fast_check 并发根因**（#81/#128）：当前 concurrency group 隔离了 crawl 和 fast_check，但两者的 `docs/feeds/` 和 `feeds_meta.json` 写入仍可能冲突，考虑改为 crawl 写 feeds/、fast_check 写其他
3. **系统性**：修复 feeds_meta 被 crawler 整体覆盖问题
4. **新 issue 审计**：本周新增 7 个 open issue，建议人工审阅
5. 评估活跃 dev 分支（feat/batch4-6 等）合并时机

---

*维护时间：2026-08-16 15:05 CST | 开源管家（AI）*
