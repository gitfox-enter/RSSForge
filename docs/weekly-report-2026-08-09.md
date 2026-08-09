# RSSForge 每周深度维护报告 — 2026-08-09

> 维护周期：2026-08-02 → 2026-08-09（7 天）

---

## 一、CI / Actions 状态

### 主要 Workflow 近 7 天失败率

| Workflow | 运行次数 | 失败次数 | 状态 |
|---|---|---|---|
| 站点更新监控 (crawl) | 50 | **0** | ✅ 已修复 |
| 快速增量检查 (fast_check) | 50 | 1 | ✅ 基本正常 |
| 每日摘要 (daily_summary) | 50 | 6 | ⚠️ 非 fast-forward 冲突 |
| Tests | 50 | 43（均为 08-02 旧失败） | ✅ **已修复**（最新 08-05 通过） |
| 质量守卫 (quality-guard) | 50 | 1 | ✅ 正常 |
| Freshness Watchdog | 50 | 0 | ✅ 正常 |
| Blacklist Check | 24 | 2 | ⚠️ 轻微 |
| Git History Cleanup | 4 | 2 | ⚠️ 轻微 |

**结论：上周两项核心修复生效**
- `crawl.yml` workflows:write 权限（commit 5cfae2a）→ 34/50 失败 → **0/50 失败** ✅
- `test_crawler.py` 陈旧断言修正（commit 6cb31dd）→ 最新测试运行（08-05）**通过** ✅
- daily_summary 非 fast-forward 推冲突仍存在（6/50），轻微，不影响核心功能

---

## 二、订阅源健康状况

### 数据概览

| 指标 | 上周（08-02） | 本周（08-08） | 变化 |
|---|---|---|---|
| feeds_meta 收录源 | 11 | 14 | +3 |
| 总条目数 | 43,827 | 60,019 | **+16,192** (+37%) |
| 零内容源 | 0 | 0 | — |
| 活跃源（sites.yaml） | 22 | **25** | +3 |

**feeds_meta 收录（14 个）：**
线报酷(24,352) / 线报ICU(3,207) / 专业线报(2,809) / 汇发部(25,095) / 爱Q社区(277) / 白菜哦(1,955) / 赚客吧(1,453) / 超级线报(566) / 网猴线报(144) / 羊毛党(45) / 线报网(116) / **36氪(0)** / **爱范儿(0)** / **少数派(0)**

> 本次将 3 个新增 RSS 源（08-05 添加）加入 feeds_meta 追踪（条目待下次爬取后填充）。

### 零内容 / 长期无更新源
- ✅ 无零内容源
- ⚠️ 新增 RSS 源（36氪/爱范儿/少数派）条目数为 0，需确认 RSS parser 是否正常输出

### dead_sites（15 个，确认稳定）

| 域名 | 死因 |
|---|---|
| 007ymd.com | DNS 无法解析 |
| 907k.cn | DNS/连接失败 |
| xiaodigu.com | 502 Bad Gateway |
| ym2.cc | DNS 无法解析 |
| 79tao.linejia.com | 连接拒绝 |
| 0818tuan.com | Cloudflare 521 |
| foxirj.com | RSS Feed 为空 |
| 51kanong.com | JS 渲染后 RSS 仍空 |
| mefcl.com | HTTP 空响应 |
| huodong5.com | 域名停用，已迁移至 huodong8.com |
| yrxq.xliangxi.vip | JS 渲染后 RSS 仅 2 条导航内容 |
| xzba.cc | SSL 握手失败 |
| ghxi.com | TLS 连接 EOF |
| 0818tuan.com (http) | 连接拒绝 |
| 79tao.linejia.com (http) | 连接拒绝 |

> 注：foxirj/51kanong/ghxi 等 HTTP 探测返回 200，但 RSS 用途仍然失效（DNS/SSL/内容问题），维持 dead_sites 状态。

---

## 三、Issues 审计

**总 open：50 个**（BUG 32 / 功能增强 12 / 自动告警 1 / 维护 2）

本周无新增/更新的 issue（2026-08-02 以来无变更）。

### 仍需人工处理的 BUG（按优先级）

| # | 标题 | 优先级 | 状态 |
|---|---|---|---|
| #54 | **Security: redirect.html 开放重定向** | CRITICAL | 未修复 |
| #128 | crawl 与 fast_check 并发冲突 | High | 未修复 |
| #129 | hash 随机化导致 CI 不稳定 | Medium | 未修复 |
| #143 | test_crawler.py 陈旧断言（已部分修复） | Medium | **已修复** |

### 建议处理的维护类 Issue
- #133 质量守卫自动监测（已识别，建议 human decision）
- #135 新源候选（36氪/ifanr/sspai 已添加）

---

## 四、已知问题 / 待调查

### 🔴 feeds_meta 与 sites.yaml 漂移（# 仍存在）
- **现象**：sites.yaml 活跃源 25 个，feeds_meta 收录 14 个（含 3 个新增），**11 个源游离于追踪之外**
- **排查范围**：线报迷 / 羊毛王 / 羊毛线报 / 12345线报 / 活动5 / 天天赚 / 慢慢买 / 拔草哦 / 豆瓣小组 / 羊毛群 / 线报屋
- **HTTP 状态**：以上 11 源全部返回 HTTP 200，站点存活
- **可能原因**：crawler push 权限不足（上周 crawl 修复前积压的 drift）、RSS parser 对新/特殊站不输出、或者爬取内容为空未写 feeds_meta
- **建议**：运行 `maintain.py fix_feeds_meta` 修正，或人工逐一排查

### 🟡 新增 RSS 源待确认（36氪/ifanr/少数派）
- sites.yaml 已配置 `parser: rss` 和 `rss_feed` URL
- feeds_meta 已添加，条目数 0（下次爬取后应更新）
- **建议**：观察下周爬取结果，确认 RSS 解析器输出正常

### 🟡 daily_summary 非 fast-forward 推冲突（6/50）
- 原因：并发 push 时无 pull/merge，GitHub 拒绝
- 不影响核心功能，建议后续在 workflow 中加 `--force-with-lease` 或先 pull

---

## 五、Active Development（分支概览）

仓库当前有 **8 个远程开发分支**：

| 分支 | 类型 |
|---|---|
| feat/batch4-enhancements-34-35-40-42 | 功能增强 |
| feat/batch5-enhancements-37-38-41-44 | 功能增强 |
| feat/batch6-37-24 | 功能增强 |
| feat/alipay-redpacket-feed | 专题功能 |
| fix/critical-bugs-26-28-29 | 关键 Bug |
| fix/batch2-maintenance-branding-dedup | 维护/清理 |
| fix/batch3-security-storage | 安全/存储 |
| fix/alipay-redpacket-image-path | 专题修复 |

> 这些分支已推送但未合入 main，也未创建 PR。本周维护不触碰这些分支。

---

## 六、本周改动记录

| SHA | 说明 |
|---|---|
| `5cfae2a` | fix(crawl): add workflows:write permission（08-02）|
| `6cb31dd` | fix(tests): update stale test assertions（08-02）|
| `d2b678a` | chore(feeds): add 36氪/爱范儿/少数派 to feeds_meta（08-09）|

---

## 七、下周建议

1. **优先级高**：处理 #54 Security（redirect.html 重定向）
2. **本周可做**：运行 maintain.py fix_feeds_meta 修正 11 个游离源
3. **观察确认**：36氪/ifanr/少数派 RSS 源下周是否有条目产出
4. **CI 优化**：修复 daily_summary 非 fast-forward 冲突
5. **合并计划**：评估 feat/batch4-6 及 fix/critical-bugs 是否可合并

---

*报告生成：2026-08-09 15:20 CST | 维护者：开源管家（AI）*
