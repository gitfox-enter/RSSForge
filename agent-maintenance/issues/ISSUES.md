# RSSForge Issue Tracker

## Critical Issues

### ISSUE-001: Feed Availability Crisis
**Priority**: P0  
**Status**: 🔴 OPEN  
**Created**: 2026-07-11  
**Last Updated**: 2026-07-11 16:15  

**Description**:
75% of feeds (36/48) show `count=0` in latest `feeds_meta.json`. This could indicate:
- Domain failures
- Parser breakage
- Network issues
- Site structure changes

**Impact**:
- Users missing 75% of potential content
- Reduced value proposition
- Possible undetected failures

**Categories**:
- **P0 - High Frequency (13 sites)**: 线报迷, 小角落, ReadHub, 羊毛系列, 新赚吧, etc.
  - These were reliable sources, sudden drop suggests systemic issue
- **P1 - Medium Frequency (10 sites)**: 好赚网, 活动5, IT之家, etc.
- **P2 - Low Frequency (13 sites)**: Software downloads, news aggregators

**Investigation Plan**:
```bash
# 1. Sample HTTP status checks
for site in $(cat suspected_down.txt); do
  curl -sI "$site" | head -1
done

# 2. Check DNS resolution
for site in $(cat suspected_down.txt); do
  dig +short "$site"
done

# 3. Review recent Actions logs
grep -i "error\|failed" run_log.jsonl
```

**Next Steps**:
1. Run HTTP status check on 10 sample sites
2. Categorize as: (a) domain dead, (b) parser broken, (c) temporary network issue
3. Fix parsers for recoverable sites
4. Remove confirmed dead sites from `sites.yaml`
5. Update documentation

**Resolution Criteria**:
- All P0 sites verified and either fixed or removed
- Healthy feed ratio improved to >50%

---

## High Priority Issues

### ISSUE-002: Missing Full-Text Content
**Priority**: P1  
**Status**: 🟡 PLANNED  
**Created**: 2026-07-11  

**Description**:
RSS feeds currently contain only titles and links. Users must click through to read content, reducing engagement.

**Proposed Solution**:
```yaml
# sites.yaml enhancement
sites:
  - name: example.com
    url: https://example.com
    fetch_content: true  # NEW: Enable full-text extraction
    content_selector: .article-body  # CSS selector for content
```

**Implementation**:
1. Modify `crawler/engine.py` to support `fetch_content` flag
2. Use existing `fetch_page_content()` to extract article body
3. Store full content in feed `<description>` or `<content:encoded>`
4. Handle encoding and sanitization

**Estimation**: 4-6 hours development + testing

**Acceptance Criteria**:
- [ ] Config flag added to `sites.yaml`
- [ ] Engine supports full-text extraction
- [ ] At least 5 sites enabled with full content
- [ ] Feeds validate as valid RSS 2.0

---

### ISSUE-003: Monitoring Coverage Gap
**Priority**: P1  
**Status**: 🟢 IN PROGRESS  
**Created**: 2026-07-11  

**Description**:
No automated alerting for prolonged failures. If Actions fail repeatedly, could go unnoticed for days.

**Current Mitigation**:
- Daily quality checks (4x per day)
- Manual review of Actions logs

**Proposed Enhancement**:
- Alert after 3 consecutive failures
- Email/Message notification to user
- Auto-create GitHub issue for tracking

**Status**: Monitoring jobs configured (ID: 41b32748-dbd3-4169-91ff-1bcdf6939f07)

---

## Medium Priority Issues

### ISSUE-004: Parser Maintenance
**Priority**: P2  
**Status**: 🟡 BACKLOG  
**Created**: 2026-07-11  

**Description**:
Several sites using outdated parsers. Need to update CSS selectors and extraction logic.

**Sites Requiring Update**:
- IT之家: Structure changed, parser may be stale
- ReadHub: API endpoint potentially modified
- 羊毛系列: Pagination logic needs refresh

**Tasks**:
- [ ] Audit current parser configurations
- [ ] Test each parser manually
- [ ] Update CSS selectors/API endpoints
- [ ] Add parser health check to monitoring

---

### ISSUE-005: Performance Optimization
**Priority**: P2  
**Status**: 📝 PLANNED  
**Created**: 2026-07-11  

**Description**:
Crawl time averaging 15+ minutes. Can optimize with:
- Parallel crawling (currently sequential)
- Smart caching (skip unchanged pages)
- Delta updates (only fetch new items)

**Benchmark Goals**:
- Current: ~15 min for 48 sites
- Target: <5 min with parallelization

---

## Low Priority Issues

### ISSUE-006: Documentation Improvements
**Priority**: P3  
**Status**: 📝 BACKLOG  

**Tasks**:
- [ ] Add API documentation for public endpoints
- [ ] Create user guide for adding new feeds
- [ ] Document parser development workflow
- [ ] Add architecture diagrams

---

### ISSUE-007: Research RSS Best Practices
**Priority**: P3  
**Status**: 📝 ONGOING  

**Description**:
Research popular RSS tools for inspiration:
- PolitePol: Content extraction techniques
- Morss.it: Full-text parsing
- RSS-Bridge: Platform connectors

**Goal**: Identify 3-5 features to implement in RSSForge

---

### ISSUE-008: 零内容活跃站诊断误报复核（抽样审计）
**Priority**: P2
**Status**: 🟢 VERIFIED（待动作）
**Created**: 2026-07-15
**Last Updated**: 2026-07-15

**Description**:
`diagnose_results.json` 将 `free.apprcn.com` 与 `www.thosefree.com` 标记为 `HTML_OK` 但 `article_count=0`（归入"零内容活跃站"，疑似待清理）。本次维护 agent 人工复核（curl 静态 HTML 链接计数 + WebFetch 渲染）发现二者实际健康，诊断为**链接提取漏判（false negative）**。

**Investigation**:
- `https://free.apprcn.com/`（反斗限免 / Free App）：静态 HTML 含 **73 条**站内文章链接（如 `/aomei-cbackup-professional-4/`），最新文章日期 **2026-07-15**。非 SPA、非死站。
- `https://www.thosefree.com/`（那些免费的砖）：静态 HTML 含 **67 条**站内文章链接（如 `/fusion360`、`/clipsync`），最新文章日期 **2026-06-25**。非 SPA、非死站。
- 诊断报告原始标记：`free.apprcn.com` → `36480b,0links`；`thosefree.com` → 同型 `0links`。二者均存在真实 `<a href>` 文章列表，判定为诊断脚本链接抽取逻辑未覆盖（疑似仅匹配特定选择器，漏掉 WordPress 风格 `/<slug>/` 链接）。

**Conclusion（判断）**:
- 二者均**无需加 `js_render`**，**确未死亡**，应保留在 `sites.yaml` 活跃列表，**不应迁移至 dead_sites / blacklist**。
- 诊断 "0 links" 为误报；结合本周报告"27 个零内容活跃站"的规模，强烈提示 `diagnose_sources.py` 的链接抽取对大量站点失效，误报面可能很广。

**Proposed Solution**:
1. 复查 `diagnose_sources.py` 链接选择器为何漏掉 `/<slug>/` 风格（及可能的其他常见结构）。
2. 修复后重跑诊断，确认 `free.apprcn.com` / `thosefree.com` 文章数恢复正常。
3. 对报告中其余"零内容活跃站"抽样复核，区分真死站与误报，避免误删健康源。

**Acceptance Criteria**:
- [ ] 诊断链接抽取覆盖 `/<slug>/` 等常见文章 URL 形态
- [ ] `free.apprcn.com` / `thosefree.com` 不再报零内容
- [x] 抽样复核其余"零内容活跃站"（见 ISSUE-009，本_RUN 再抽 2 个）

---

### ISSUE-009: 零内容活跃站复核（本_RUN·根因定位）
**Priority**: P2
**Status**: 🟢 VERIFIED（待动作）
**Created**: 2026-07-15
**Last Updated**: 2026-07-15

**Description**:
ISSUE-008 已确认 `free.apprcn.com` / `thosefree.com` 为诊断误报（健康、保留）。本_RUN 维护 agent 基于 `items.json` 全量统计（40 活跃源仅 14 有内容，26 零内容），再抽审 2 个零内容活跃源，定位**根因是解析器/爬虫配置失效，而非站点死亡**。

**Investigation（WebFetch 真实验证）**:
- `https://free.apprcn.com/`（反斗限免）：HTTP 200，文章列表直链 `/<slug>/`（如 `/aomei-cbackup-professional-4/`），最新 **2026-07-15**。非 SPA、非死站。`sites.yaml` 仅配置 `url`、**无 `parser` 也无 `rss_feed`**，依赖通用爬虫 → 未正确提取（诊断误报）。
- `https://www.423down.com/`（423Down）：HTTP 200，今日**密集更新**（多篇文章 2026-07-15），直链 `/<id>.html`（如 `/10421.html`）。非 SPA、非死站。已配 `parser: 423down.com` 但产出 0 → **自定义 parser 疑似失效**。

**Conclusion（判断）**:
- 二者均**健康、可逆、未死亡**，应保留在 `sites.yaml` 活跃列表，**不应**迁移至 `dead_sites` / `blacklist`。
- 根因归类为：(a) 缺 parser/rss_feed 配置（free.apprcn.com）；(b) 自定义 parser 失效（423down.com）。
- 与 ISSUE-008 一致：本周"26 个零内容活跃站"中相当部分为配置/解析问题而非真死站，建议优先排查 parser 而非批量清理。

**Proposed Solution**:
1. 为 `free.apprcn.com` 增加专用 parser 或 `js_render: true`（WordPress 风格 `/<slug>/` 列表）。
2. 修复 `423down.com` 自定义 parser（`parsers/software_sites.py` 或对应模块的选择器/分页逻辑）。
3. 对剩余零内容活跃源按"是否健康直链 / 是否需 js_render / 是否真死"三分类批量复核。

**Acceptance Criteria**:
- [ ] `free.apprcn.com` 加入 parser 或 js_render 后恢复产出
- [ ] `423down.com` parser 修复后恢复产出
- [ ] 输出剩余零内容活跃源的三分类清单

---

### ISSUE-010: 零内容活跃站复核（RUN·2026-07-22 复验）
**Priority**: P2
**Status**: 🟢 VERIFIED（待动作）
**Created**: 2026-07-22
**Last Updated**: 2026-07-22

**Description**:
ISSUE-008 / ISSUE-009 已于 2026-07-15 判定 `free.apprcn.com` / `www.thosefree.com` 为诊断误报、健康保留。本 RUN 维护 agent 在"每周新源发现"任务中再次抽审这 2 个被 `diagnose_results.json` 标记为"零内容活跃站"的源，用 WebFetch 做**新鲜度复验**，结论一致并补充最新证据。

**Investigation（2026-07-22 WebFetch 真实验证）**:
- `https://free.apprcn.com/`（反斗限免）：HTTP 200，静态 HTML 含真实文章直链（如 `/limited-time-get-space-for-free/`、`/leawo-tunes-cleaner-19/`），最新文章 **2026-07-21**，非 SPA、非死站。`diagnose_results.json` 的 `36480b,0links` 为链接抽取漏判（WordPress `/<slug>/` 风格未被覆盖）。
- `https://www.thosefree.com/`（那些免费的砖）：RSS feed `thosefree.com/feed` 实测正常输出 **10 条**真实条目（最新 **2026-07-16**，如 `/king-james-royalty-free-music`），走 `sites.yaml` 已配 `rss_feed` 通道，非死站。诊断的 HTML `0links` 不影响产出。

**Conclusion（判断）**:
- 二者均**健康、可逆、未死亡**，**无需加 `js_render`**，应保留在 `sites.yaml` 活跃列表，**不应**迁移至 `dead_sites` / `blacklist`。
- 与 ISSUE-008 / ISSUE-009 结论一致，进一步佐证 `diagnose_sources.py` 链接抽取存在**系统性误报**（既漏 `/<slug>/` 直链，也未识别 `rss_feed` 通道站点）。建议优先修复诊断脚本，而非批量清理"零内容活跃站"。

**Proposed Solution**:
1. 修复 `diagnose_sources.py` 链接抽取：覆盖 WordPress `/<slug>/` 形态，且对配置了 `rss_feed` 的站点改查 feed 而非静态 HTML。
2. 修复后重跑诊断，确认 `free.apprcn.com` / `thosefree.com` 不再报零内容。
3. 对剩余"零内容活跃站"按"健康直链 / 需 js_render / 真死"三分类批量复核。

**Acceptance Criteria**:
- [ ] `diagnose_sources.py` 链接抽取覆盖 `/<slug>/` 与 `rss_feed` 站点
- [ ] 重跑后 `free.apprcn.com` / `thosefree.com` 不再报零内容
- [ ] 输出剩余零内容活跃源的三分类清单

---

## Resolved Issues

### ISSUE-000: RSS Timezone Bug ✅
**Priority**: P0  
**Status**: ✅ RESOLVED  
**Created**: 2026-07-11  
**Resolved**: 2026-07-11  

**Problem**:
RSS feeds used `-0000` timezone in `<pubDate>`. Readers interpreted this as UTC, causing +8 hour offset for users in Asia/Shanghai.

**Root Cause**:
```python
# Before (rss_feed.py)
formatdate(localtime=False)  # Returns -0000
```

**Fix**:
```python
# After (rss_feed.py)
datetime.now(pytz.timezone('Asia/Shanghai')).strftime(
    '%a, %d %b %Y %H:%M:%S +0800'
)
```

**Commit**: f6d07d820d67be1c828559a1f9263b9467932010

**Verification**:
```bash
# Check feed
curl -s https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/feeds/线报酷.xml | \
  grep -o '<pubDate>.*</pubDate>' | head -1
# Output: <pubDate>Sat, 11 Jul 2026 14:38:42 +0800</pubDate>
```

**Impact**: ✅ Time now displays correctly in all RSS readers

---

## Issue Workflow

### Creating Issues
```markdown
### ISSUE-XXX: [Title]
**Priority**: P0/P1/P2/P3
**Status**: 🔴 OPEN / 🟡 PLANNED / 🟢 IN PROGRESS / ✅ RESOLVED
**Created**: YYYY-MM-DD
**Last Updated**: YYYY-MM-DD

**Description**:
[Clear description of the problem]

**Impact**:
[User/business impact]

**Investigation**:
[Research findings, if any]

**Proposed Solution**:
[How to fix it]

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

**Resolution**:
[For resolved issues: what was done, commit hash, verification]
```

### Updating Issues
1. Change status when work begins
2. Update "Last Updated" date
3. Add findings to "Investigation" section
4. Document solution in "Resolution" section
5. Commit changes to GitHub

### Closing Issues
1. Verify all acceptance criteria met
2. Add verification steps
3. Update status to ✅ RESOLVED
4. Include commit hash
5. Commit to GitHub

---

**Last Updated**: 2026-07-22 20:30
