# RSSForge Maintenance Skill - Examples

This directory contains example usage of the RSSForge maintenance skill.

---

## Example 1: Daily Monitoring

**Scenario**: Agent runs scheduled daily health check

**Command**:
```bash
python3 scripts/monitor_enhanced.py \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --log-dir /var/log/rssforge
```

**Expected Output**:
```
============================================================
RSSForge Enhanced Monitor
Time: 2026-07-11 16:36:52
============================================================

[16:36:52] [INFO] 📊 Checking GitHub Actions...
[16:36:54] [INFO] Recent runs: 5
[16:36:54] [INFO] ✅ Success: 3
[16:36:54] [INFO] 📅 Checking feeds_meta.json...
[16:36:55] [INFO] Total sites: 48
[16:36:55] [INFO] ✅ Healthy: 12 (25%)
[16:36:55] [INFO] ❌ Zero-count: 36 (75%)
[16:36:55] [INFO] 🔗 Checking RSS feed links...
[16:36:56] [INFO] ✅ GitHub Pages accessible
[16:36:56] [INFO] 🌐 Checking official source sites...
[16:36:57] [INFO] ✅ 线报酷
[16:36:58] [INFO] ✅ 汇发部
[16:36:59] [INFO] ✅ 线报ICU
[16:36:59] [INFO] Result: 3/3 accessible

============================================================
📊 RSSForge Monitor Summary
============================================================
✅ All systems healthy
```

---

## Example 2: Auto-Fix URL Fields

**Scenario**: Agent detects missing URLs and runs auto-fix

**Command**:
```bash
python3 scripts/auto_fix.py --pat ghp_xxxxxxxxxxxxxxxxxxxx
```

**Expected Output**:
```
============================================================
RSSForge Auto-Fix Tool
============================================================

[2026-07-11 16:40:00] [INFO] Fixing feeds_meta.json...
[2026-07-11 16:40:05] [INFO] Fixed URL for 线报迷: https://example.com
[2026-07-11 16:40:06] [INFO] Fixed URL for 小角落: https://example.org
...
[2026-07-11 16:40:30] [INFO] Fixed 36 sites, committing...
[2026-07-11 16:40:35] [INFO] ✅ Committed fix for 36 sites

============================================================
Auto-Fix Summary
============================================================
Total fixes applied: 1
Feeds meta fixed: 36

✅ Auto-fix completed successfully
```

---

## Example 3: Diagnose Feed Issues

**Scenario**: User reports feeds showing wrong time, agent runs diagnosis

**Command**:
```bash
python3 scripts/diagnose_feeds.py --pat ghp_xxxxxxxxxxxxxxxxxxxx
```

**Expected Output**:
```
============================================================
RSSForge Feed Health Diagnostic Report
============================================================

📊 Summary:
  Total sites:          48
  ✅ Healthy:           12 (25.0%)
  ⚠️  Zero count w/ URL: 0 (0.0%)
  ❌ Missing URL:       36 (75.0%)

🔍 Root Cause Analysis:
  1. feeds_meta.json 缺少 URL 字段
     影响: 36 个站点
     原因: generate_feeds_meta.py 未正确提取 URL
     解决: 修复 feeds_meta.json 生成逻辑

💡 Recommended Actions:
  P0: 修复 feeds_meta.json 生成脚本
      - 检查 generate_feeds_index.py
      - 确保 URL 字段正确填充

📝 Next Steps:
  1. 本地克隆仓库进行深入分析
  2. 检查爬虫日志
  3. 修复 feeds_meta.json
  4. HTTP 检查零内容站点
  5. 更新文档和 Issue Tracker

✅ Results saved to /tmp/feed_diagnostic_results.json
```

---

## Example 4: Check Specific Site

**Scenario**: User asks "Check if 线报酷 is accessible"

**Agent Action**:
```python
import requests

url = "https://www.xianbao.co"
try:
    response = requests.head(url, timeout=10)
    if response.status_code in [200, 301, 302]:
        print(f"✅ {url} is accessible")
    else:
        print(f"❌ {url} returned {response.status_code}")
except:
    print(f"❌ {url} is down")
```

**Expected Output**:
```
✅ https://www.xianbao.co is accessible
```

---

## Example 5: Schedule Cron Jobs

**Scenario**: Agent sets up scheduled maintenance tasks

**Commands**:

### Daily Quality Check (4x)
```bash
# Using qclaw-cron skill
qclaw-cron add \
  --name "rssforge-daily-monitor" \
  --schedule "5 7,12,18,23 * * *" \
  --task "python3 /path/to/scripts/monitor_enhanced.py --pat $PAT" \
  --timezone "Asia/Shanghai"
```

### Weekly Deep Maintenance
```bash
qclaw-cron add \
  --name "rssforge-weekly-maintenance" \
  --schedule "0 23 * * 0" \
  --task "python3 /path/to/scripts/auto_fix.py --pat $PAT" \
  --timezone "Asia/Shanghai"
```

**Expected Output**:
```
✅ Cron job created: rssforge-daily-monitor
   Schedule: 5 7,12,18,23 * * * (Asia/Shanghai)
   Next run: 2026-07-11 23:05:00

✅ Cron job created: rssforge-weekly-maintenance
   Schedule: 0 23 * * 0 (Asia/Shanghai)
   Next run: 2026-07-12 23:00:00
```

---

## Example 6: Recovery After Platform Restart

**Scenario**: Platform restarted, agent needs to restore context

**Step 1**: Read SKILL.md
```
User: "Use RSSForge maintenance skill"
Agent: Reads SKILL.md, activates RSSForge maintenance capabilities
```

**Step 2**: Clone Repository
```bash
git clone https://github.com/gitfox-enter/RSSForge.git
cd RSSForge
```

**Step 3**: Restore Context
```bash
cat agent-maintenance/README.md      # Agent handbook
cat agent-maintenance/ROADMAP.md     # Project roadmap
cat agent-artifacts/README.md        # Work outputs
cat agent-maintenance/issues/ISSUES.md  # Issue tracker
```

**Step 4**: Run Health Check
```bash
python3 agent-artifacts/scripts/monitor_enhanced.py --pat $PAT
```

**Step 5**: Resume Operations
```bash
# If issues found, run auto-fix
python3 agent-artifacts/scripts/auto_fix.py --pat $PAT

# Schedule cron jobs (see Example 5)
```

---

## Example 7: Handle Alert

**Scenario**: Monitor detects 3 source sites down

**Alert Message**:
```
⚠️  Alerts: [Sources:3 down]
Failed sites: 线报酷, 汇发部, 线报ICU
```

**Agent Actions**:

1. **Retry Check**:
```bash
# Retry each site with longer timeout
curl -I -m 30 https://www.xianbao.co
curl -I -m 30 https://www.huifabu.com
curl -I -m 30 https://www.xianbao.icu
```

2. **Diagnose Issue**:
```python
# Check if it's network issue or site issue
# Try alternative endpoints
# Check DNS resolution
```

3. **Mark as Dead** (if persistent > 7 days):
```python
# Add to blacklist.json
# Remove from sites.yaml
# Update ISSUE-001
# Notify user
```

4. **Update Documentation**:
```bash
# Update agent-maintenance/issues/ISSUES.md
# Add entry to logs/YYYY-MM-DD.md
# Create task summary
```

---

## Example 8: Add New RSS Source

**Scenario**: Agent discovers high-quality RSS source

**Process**:

1. **Identify Source**:
```
Site: Example News
URL: https://example.com
RSS: https://example.com/feed.xml
Content: Tech news, daily updates
Quality: High
```

2. **Test Feed**:
```bash
curl -I https://example.com/feed.xml
# Check: 200 OK, valid RSS/Atom format
```

3. **Add Configuration**:
```yaml
# sites.yaml
- site_id: example-news
  url: https://example.com
  feed_url: https://example.com/feed.xml
  parser: generic
  category: tech
  priority: P1
```

4. **Test Parser**:
```bash
python3 crawl.py --site-id example-news --test
```

5. **Commit Changes**:
```bash
git add sites.yaml
git commit -m "feat: add example-news RSS source"
git push
```

---

## Example 9: Weekly Report Generation

**Scenario**: Agent generates weekly maintenance report

**Template**:
```markdown
# Weekly Maintenance Report - 2026-W28

## Summary

- **Feeds Monitored**: 48
- **Healthy**: 43 (90%)
- **Issues Fixed**: 5
- **Sites Removed**: 2
- **Sites Added**: 1

## Actions Taken

1. Auto-fixed feeds_meta.json URLs (3 sites)
2. Removed dead sites: dead-site-1, dead-site-2
3. Added new source: example-news
4. Updated parser: site-with-new-structure

## Issues Resolved

- ISSUE-006: Feed timeout for site-xyz ✅
- ISSUE-007: Parser outdated for site-abc ✅

## Ongoing Issues

- ISSUE-001: Feed availability (down to 10% zero-count)
- ISSUE-002: Missing full-text content

## Next Week Plan

- [ ] Full HTTP check on all zero-count sites
- [ ] Parser audit for failed crawls
- [ ] Performance optimization
- [ ] Add 3 new RSS sources

## Metrics

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Health Ratio | 90% | 25% | ↑ +65% |
| Zero-Count | 5 | 36 | ↓ -31 |
| Actions Success | 100% | 100% | → |
| Response Time | <1h | N/A | ✅ |

---
**Report Generated**: 2026-07-18 23:00
**Agent**: RSSForge Maintenance Specialist
```

---

## Example 10: Coordinate with GitHub Actions

**Scenario**: Agent triggers Actions workflow manually

**Trigger Crawl**:
```bash
gh workflow run crawl.yml
```

**Check Status**:
```bash
gh run list --workflow=crawl.yml --limit 5
```

**View Logs**:
```bash
gh run view RUN_ID --log
```

**Expected Flow**:
1. Agent monitors and detects issue
2. Agent applies local fix
3. Agent triggers Actions to verify
4. Agent reviews Actions result
5. Agent updates documentation

---

**Last Updated**: 2026-07-11
**Skill Version**: 1.0.0
