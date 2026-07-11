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

**Last Updated**: 2026-07-11 16:15
