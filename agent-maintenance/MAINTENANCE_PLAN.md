# RSSForge Maintenance Plan

> Automated maintenance and monitoring for RSSForge project

## 🎯 Mission

Keep RSSForge feeds healthy, accessible, and up-to-date through automated monitoring and self-healing mechanisms.

---

## 📊 Monitoring Schedule

### Daily Quality Check (4x per day)

**Time**: 7:05, 12:05, 18:05, 23:05 (aligned with Actions + 5 min)

**Checks**:
1. GitHub Actions status (success/failure)
2. feeds_meta.json freshness
3. Feed health ratio (healthy/zero-count)
4. RSS feed link accessibility (GitHub Pages)
5. Official source site availability

**Alert Conditions**:
- ❌ Actions failed > 1
- ❌ Zero-count feeds > 30
- ❌ GitHub Pages down
- ❌ Source sites down > 3

**Output**: Log to `cron-logs/monitor_YYYY-MM-DD_HH-MM.log`

---

### Weekly Deep Maintenance (Sundays 23:00)

**Tasks**:
1. Run auto-fix tool (fix feeds_meta.json)
2. Full HTTP check on all zero-count sites
3. Remove dead sites from configuration
4. Update documentation
5. Generate weekly report

**Output**:
- Update `feeds_meta.json`
- Update `ISSUES.md`
- Create `weekly-report_YYYY-MM-DD.md`

---

## 🔧 Automated Fix Mechanisms

### 1. feeds_meta.json Auto-Fix

**Problem**: Missing URL field in feeds_meta.json
**Solution**: `auto_fix.py` script

**Process**:
1. Fetch current `feeds_meta.json`
2. Fetch `sites.yaml` to get URLs
3. Populate missing `url` fields
4. Commit fix to repository

**Run**: Weekly or on-demand

**Script**: `rssforge-maintain/auto_fix.py`

---

### 2. Dead Site Cleanup

**Problem**: Source sites permanently down
**Solution**: HTTP status check + removal

**Process**:
1. HTTP check on zero-count sites
2. Mark sites with 404/timeout as dead
3. Move to `blacklist.json`
4. Remove from `sites.yaml`
5. Update documentation

**Run**: Weekly

---

### 3. Parser Update

**Problem**: Site structure changed, parser broken
**Solution**: Parser audit and update

**Process**:
1. Identify failed parsers
2. Analyze site structure
3. Update parser code
4. Test locally
5. Deploy fix

**Run**: On-demand (when alerts trigger)

---

## 🔗 Link Maintenance

### RSS Feed Links

**Target**: `https://gitfox-enter.github.io/RSSForge/feeds/`

**Check**: Every monitoring run

**Actions if down**:
1. Verify GitHub Pages deployment
2. Check `feeds/` directory
3. Rebuild if needed
4. Alert if persistent

---

### Official Source Sites

**Sites to Monitor**:
1. 线报酷 - https://www.xianbao.co
2. 汇发部 - https://www.huifabu.com
3. 线报ICU - https://www.xianbao.icu
4. 专栏吧 - (URL TBD)
5. 专业线报 - (URL TBD)

**Check**: Every monitoring run

**Actions if down**:
1. Retry with timeout
2. Check if temporary or permanent
3. Mark as dead if > 7 days down
4. Alert immediately

---

## 🚨 Alert Mechanisms

### Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Actions failed > 1 | High | Immediate investigation |
| Zero-count > 30 | High | Run auto-fix |
| GitHub Pages down | Critical | Immediate fix |
| Source sites down > 3 | Medium | Weekly cleanup |
| feeds_meta.json stale > 24h | High | Check crawler |

---

### Notification Channels

**Current**: Log file + console output

**Planned**:
- [ ] QClaw message to user
- [ ] GitHub Issue creation
- [ ] Email notification (optional)

---

## 📝 Maintenance Scripts

### 1. monitor_enhanced.py

**Purpose**: Comprehensive health check

**Checks**:
- GitHub Actions
- feeds_meta.json
- RSS feed links
- Source sites

**Output**: Log file + console

**Run**: 4x daily (cron)

---

### 2. auto_fix.py

**Purpose**: Automatic data repair

**Fixes**:
- feeds_meta.json URL field
- Missing feed files
- Stale data

**Output**: GitHub commit

**Run**: Weekly (cron)

---

### 3. diagnose_feeds.py

**Purpose**: Problem diagnosis

**Checks**:
- feeds_meta.json structure
- sites.yaml configuration
- feeds/ directory
- crawl_status.json

**Output**: Diagnostic report

**Run**: On-demand

---

## 📅 Weekly Tasks

### Monday: Review & Planning
- [ ] Review last week's alerts
- [ ] Check cron log files
- [ ] Plan fixes for the week

### Tuesday: Auto-Fix Run
- [ ] Run `auto_fix.py`
- [ ] Verify fixes
- [ ] Update documentation

### Wednesday: HTTP Check
- [ ] Run HTTP check on zero-count sites
- [ ] Identify dead sites
- [ ] Update blacklist

### Thursday: Parser Audit
- [ ] Check failed parsers
- [ ] Analyze site changes
- [ ] Update parsers if needed

### Friday: Documentation
- [ ] Update `ISSUES.md`
- [ ] Update `README.md`
- [ ] Generate weekly report

### Saturday: Testing
- [ ] Test all changes locally
- [ ] Verify all feeds
- [ ] Check GitHub Pages

### Sunday: Deep Maintenance
- [ ] Full system check
- [ ] Deploy all fixes
- [ ] Create weekly report

---

## 🎯 Success Metrics

### Target Health Ratio

```
Current:  25% (12/48 healthy)
Target:   >90% (43/48 healthy)
```

### Target Uptime

```
Feed Links:     99.9% (currently unknown)
Source Sites:   >95% (currently 0% in sandbox)
Actions:        100% (currently 100%)
```

### Target Response Time

```
Alert Response:     <1 hour
Fix Deployment:     <24 hours
Documentation:      <48 hours
```

---

## 🔄 Recovery Procedures

### If Platform Fails

1. **Read Recovery Guide**
   ```bash
   git clone https://github.com/gitfox-enter/RSSForge.git
   cat RECOVERY_GUIDE.md
   ```

2. **Restore Cron Jobs**
   ```bash
   # Monitor job
   qclaw-cron add --schedule "5 7,12,18,23 * * *" \
     --task "python3 monitor_enhanced.py --pat $PAT"

   # Weekly maintenance
   qclaw-cron add --schedule "0 23 * * 0" \
     --task "python3 auto_fix.py --pat $PAT"
   ```

3. **Resume Operations**
   ```bash
   python3 monitor_enhanced.py --pat $PAT
   ```

---

### If GitHub Pages Down

1. Check GitHub Actions deployment
2. Verify `feeds/` directory exists
3. Trigger Pages rebuild
4. Verify RSS feed accessibility

---

### If Source Sites Down

1. HTTP check with retry
2. Check if temporary (retry in 1h)
3. If persistent (>24h), investigate
4. If permanent (>7d), remove from config

---

## 📊 Reporting

### Daily Report

**Format**: Log file

**Content**:
- Actions status
- Feed health
- Link status
- Alerts

**Location**: `cron-logs/monitor_YYYY-MM-DD_HH-MM.log`

---

### Weekly Report

**Format**: Markdown

**Content**:
- Summary of fixes
- Sites removed/added
- Parser updates
- Health trend
- Issues encountered
- Next week plan

**Location**: `weekly-reports/YYYY-WW.md`

---

### Issue Report

**Format**: GitHub Issue

**Content**:
- Problem description
- Impact analysis
- Root cause
- Proposed solution
- Status

**Location**: `agent-maintenance/issues/ISSUES.md`

---

## 🚀 Automation Roadmap

### Phase 1: Core Monitoring ✅
- [x] Monitor script
- [x] Auto-fix script
- [x] Diagnose tool
- [x] Cron jobs

### Phase 2: Enhanced Features (Week 2)
- [ ] Auto HTTP check on all zero-count sites
- [ ] Auto-remove dead sites
- [ ] Auto-update documentation
- [ ] Alert notifications

### Phase 3: Advanced Features (Week 3)
- [ ] Auto-discover new RSS sources
- [ ] Auto-generate parsers
- [ ] Performance optimization
- [ ] Analytics dashboard

### Phase 4: Self-Improvement (Week 4)
- [ ] Learn from failures
- [ ] Optimize check frequency
- [ ] Improve fix accuracy
- [ ] Add new source types

---

## 📞 Contact & Support

**Repository**: https://github.com/gitfox-enter/RSSForge
**Agent**: agent-606489db
**Maintenance Lead**: Automated Agent System

**For Issues**:
1. Check `ISSUES.md`
2. Check cron logs
3. Run `diagnose_feeds.py`
4. Create GitHub Issue

---

**Last Updated**: 2026-07-11 16:40
**Status**: ✅ Maintenance system operational
**Next Review**: 2026-07-18 (Weekly)
