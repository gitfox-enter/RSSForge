# RSSForge Agent Handbook

> I am the automated DevOps agent for RSSForge. This is my operational manual.

## Identity
- **Role**: RSSForge Full-Stack DevOps Agent
- **Mission**: Maintain RSSForge project stability, continuously improve quality and coverage
- **Repository**: https://github.com/gitfox-enter/RSSForge
- **Status**: Active

## Project Overview

RSSForge is an RSS feed aggregation and monitoring system that:
- Crawls 48 subscription sources
- Generates RSS/Atom/OPML feeds
- Monitors feed health and availability
- Auto-updates via GitHub Actions (every 30min + fixed schedules at 7:00, 12:00, 18:00, 22:00)

## Current Status

### Metrics (2026-07-11)
```
Total Sites:     48
Healthy:         12 (25%)
Suspected Down:  36 (75%)
Actions Status:  ✅ All recent runs successful
Last Update:     2026-07-11T06:10:19Z
```

### Healthy Feeds (Top Performers)
| Site | Items | Status | Priority |
|------|-------|--------|----------|
| 线报酷 | 7609 | ✅ Active | P0 - Core |
| 汇发部 | 7376 | ✅ Active | P0 - Core |
| 线报ICU | 1013 | ✅ Active | P1 |
| 专栏吧 | 524 | ✅ Active | P1 |

### Pending Verification (36 sites)
See `issues/ISSUES.md` for breakdown by priority.

## Recent Work

### 2026-07-11
- ✅ Fixed RSS pubDate timezone issue (-0000 → +0800)
  - Commit: f6d07d820d67be1c828559a1f9263b9467932010
  - Impact: Fixed time display in RSS readers (no longer +8 hours offset)

- ✅ Established GitHub-based memory system
  - Created `agent-maintenance/` for operational docs
  - Created `agent-artifacts/` for work outputs
  - Benefit: Platform-independent persistence

- ✅ Built automated monitoring system
  - Quality checks: 4x daily (7:05, 12:05, 18:05, 23:05)
  - Weekly maintenance: Every Sunday 23:00
  - Scripts: `monitor.sh`, `check.sh`

## Workflows

### Daily Quality Monitoring (Automated)
**Schedule**: 7:05, 12:05, 18:05, 23:05 (aligned with Actions + 5min)

**Checks**:
1. GitHub Actions run status (success/failure)
2. `feeds_meta.json` update timestamp
3. Stale feed detection (>2 hours without update)
4. Error log analysis for failed runs

**Actions on Anomaly**:
- Failed Actions: Analyze logs → fix issue → commit
- Stale feeds: Check workflow status → manual trigger if needed
- Multiple failures: Escalate to user notification

### Weekly Deep Maintenance (Sundays 23:00)
**Tasks**:
1. Feed health assessment
   - Parse `feeds_meta.json`
   - Identify `count=0` sites
   - HTTP status check for suspected down sites

2. Cleanup
   - Remove confirmed dead domains from `sites.yaml`
   - Fix parser issues for recoverable sites
   - Update documentation

3. Reporting
   - Generate weekly report
   - Update `agent-artifacts/data/`
   - Create/resolve issues in `issues/ISSUES.md`

4. Git operations
   - Commit changes with descriptive messages
   - Push to `origin/main`
   - Handle merge conflicts (prefer local data files)

### Ad-hoc Tasks
- Bug fixes → Commit → Update `issues/ISSUES.md`
- Feature planning → Create issue → Document in logs
- Performance optimization → Test → Deploy → Record results

## Monitoring Commands

### Quick Health Check
```bash
# Run monitoring script
bash /home/node/.openclaw/workspace/agent-606489db/rssforge-maintain/monitor.sh

# Check Actions status via API
curl -H "Authorization: token $PAT" \
  https://api.github.com/repos/gitfox-enter/RSSForge/actions/workflows/crawl.yml/runs?per_page=1

# Verify feeds_meta.json freshness
curl -s https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/feeds_meta.json | \
  grep -o '"updated_at":"[^"]*"' | head -1
```

## Architecture

```
GitHub Actions (Upstream)
    ↓ Every 30min + fixed schedules
    ↓ Crawls RSS feeds
    ↓ Updates feeds_meta.json
    ↓
Agent Monitoring (Aligned +5min)
    ↓ Checks Actions results
    ↓ Detects anomalies
    ↓ Auto-notifies on failures
    ↓
Agent Maintenance (Weekly)
    ↓ Deep health check
    ↓ Cleanup & optimization
    ↓ Documentation updates
```

## Key Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `sites.yaml` | Site configurations | Weekly or on changes |
| `feeds_meta.json` | Feed metadata | Every Actions run |
| `agent-maintenance/README.md` | This handbook | On workflow changes |
| `agent-maintenance/issues/ISSUES.md` | Issue tracking | As needed |
| `agent-maintenance/logs/*.md` | Daily logs | Daily |
| `agent-artifacts/` | Work outputs | Per task |

## Recovery Procedure

**If platform fails, restore from GitHub:**

1. **Read Recovery Guide**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/RECOVERY_GUIDE.md
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/gitfox-enter/RSSForge.git
   ```

3. **Read This Handbook**
   ```
   agent-maintenance/README.md
   ```

4. **Check Current Issues**
   ```
   agent-maintenance/issues/ISSUES.md
   ```

5. **Review Recent Logs**
   ```
   agent-maintenance/logs/
   ```

6. **Resume Operations**
   - Restore cron jobs
   - Run `monitor.sh`
   - Continue pending work

## Decision Log

### 2026-07-11: GitHub-based Memory System
**Problem**: Platform restarts cause memory loss
**Solution**: Store all context in GitHub repository
**Result**: ✅ Platform-independent persistence achieved

### 2026-07-11: Timezone Fix
**Problem**: RSS pubDate used `-0000`, readers interpreted as UTC (+8h error)
**Solution**: Modified `rss_feed.py` to emit explicit `+0800` timezone
**Result**: ✅ Correct time display in all readers

### 2026-07-11: Monitoring Alignment
**Problem**: Need to detect Actions failures quickly
**Solution**: Monitor runs 5 minutes after each Actions schedule
**Result**: ✅ Near real-time anomaly detection

## Priorities

### P0 - Critical
- Maintain core feeds (线报酷, 汇发部) availability
- Ensure Actions runs successfully
- Fix critical bugs within 24h

### P1 - High
- Verify suspected down sites
- Remove dead subscriptions
- Implement full-text extraction

### P2 - Medium
- Research RSS tool improvements
- Optimize crawl performance
- Expand quality sources

### P3 - Low
- UI/UX improvements
- Documentation refinements
- Code refactoring

## Contact

- **Agent ID**: agent-606489db
- **User**: u:1158536988
- **Repository**: https://github.com/gitfox-enter/RSSForge

---

**Last Updated**: 2026-07-11 16:15
**Version**: 2.0
