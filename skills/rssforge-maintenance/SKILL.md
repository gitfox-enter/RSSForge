# RSSForge Maintenance Skill

> **Mission**: Automatically maintain RSSForge project health through monitoring, auto-fixing, and self-healing mechanisms.

---

## 🎯 What This Skill Does

This skill transforms any agent into an RSSForge maintenance specialist with:

1. **Automatic Problem Diagnosis** - Identify feed health issues
2. **Auto-Fix Mechanisms** - Repair data and configuration problems
3. **Link Monitoring** - Check RSS feeds and source sites
4. **Scheduled Maintenance** - Run periodic health checks
5. **Self-Recovery** - Restore agent context from GitHub

---

## 🚀 Quick Start

### Activate Skill

```
Read this SKILL.md file to activate RSSForge maintenance capabilities.
```

### Run Health Check

```bash
python3 scripts/monitor_enhanced.py --pat YOUR_GITHUB_PAT
```

### Run Auto-Fix

```bash
python3 scripts/auto_fix.py --pat YOUR_GITHUB_PAT
```

---

## 📊 Core Capabilities

### 1. Feed Health Monitoring

**Checks**:
- GitHub Actions status
- feeds_meta.json freshness
- Feed count (healthy vs zero-count)
- RSS link accessibility
- Source site availability

**Frequency**: 4x daily (7:05, 12:05, 18:05, 23:05)

**Output**: `cron-logs/monitor_*.log`

---

### 2. Automatic Data Repair

**Fixes**:
- Missing URL fields in feeds_meta.json
- Stale feed metadata
- Configuration mismatches

**Trigger**: Weekly (Sunday 23:00) or on-demand

**Output**: GitHub commit with fix

---

### 3. Link Validation

**RSS Feed Links**:
- Target: `https://gitfox-enter.github.io/RSSForge/feeds/`
- Check: GitHub Pages accessibility
- Validate: Sample feed files

**Official Source Sites**:
- 线报酷: https://www.xianbao.co
- 汇发部: https://www.huifabu.com
- 线报ICU: https://www.xianbao.icu

**Action**: Mark dead sites for removal

---

### 4. Agent Recovery

**If platform fails**:

1. Agent reads this SKILL.md
2. Clones RSSForge repository
3. Restores context from GitHub
4. Resumes maintenance operations

**Recovery Command**:
```bash
git clone https://github.com/gitfox-enter/RSSForge.git
cd RSSForge
cat agent-maintenance/README.md
```

---

## 🔧 Tools Included

### monitor_enhanced.py

**Purpose**: Comprehensive health monitoring

**Features**:
- GitHub Actions check
- Feed health analysis
- Link accessibility test
- Source site validation
- Alert generation

**Usage**:
```bash
python3 scripts/monitor_enhanced.py \
  --pat YOUR_PAT \
  --log-dir /path/to/logs
```

**Output**:
- Console log
- File log
- Exit code (0=healthy, 1=alerts)

---

### auto_fix.py

**Purpose**: Automatic data repair

**Features**:
- Fix feeds_meta.json URL field
- Sync with sites.yaml
- Commit fixes to GitHub
- Generate fix report

**Usage**:
```bash
python3 scripts/auto_fix.py --pat YOUR_PAT
```

**Output**:
- GitHub commit
- Fix report in `/tmp/rssforge-autofix/`

---

### diagnose_feeds.py

**Purpose**: Problem diagnosis

**Features**:
- Check feeds_meta.json structure
- Verify sites.yaml config
- List feeds directory
- Analyze crawl_status.json

**Usage**:
```bash
python3 scripts/diagnose_feeds.py --pat YOUR_PAT
```

**Output**:
- Diagnostic report
- `/tmp/feed_diagnostic_results.json`

---

## 📁 Project Structure

```
RSSForge/
├── agent-maintenance/              # Agent documentation
│   ├── README.md                   # Agent handbook
│   ├── MAINTENANCE_PLAN.md         # Maintenance plan
│   ├── ROADMAP.md                  # Project roadmap
│   ├── issues/ISSUES.md            # Issue tracker
│   ├── logs/                       # Dev logs
│   └── cron-logs/                  # Cron execution logs
│
├── agent-artifacts/                # Work outputs
│   ├── README.md                   # Work index
│   ├── scripts/                    # Maintenance scripts
│   │   ├── monitor_enhanced.py
│   │   ├── auto_fix.py
│   │   └── diagnose_feeds.py
│   ├── data/                       # Snapshots
│   └── task-summaries/             # Task reports
│
├── RECOVERY_GUIDE.md               # Recovery procedures
├── sites.yaml                      # Site configuration
├── feeds_meta.json                 # Feed metadata
└── feeds/                          # RSS feed files
```

---

## ⏰ Scheduled Tasks

### Daily Quality Check (4x)

**Cron**: `5 7,12,18,23 * * *`

**Task**: Run `monitor_enhanced.py`

**Alert Conditions**:
- Actions failed > 1
- Zero-count feeds > 30
- GitHub Pages down
- Source sites down > 3

---

### Weekly Deep Maintenance

**Cron**: `0 23 * * 0` (Sunday 23:00)

**Task**:
1. Run `auto_fix.py`
2. Full HTTP check
3. Clean dead sites
4. Update documentation
5. Generate weekly report

---

## 🚨 Alert System

### Current Implementation

**Output**: Console + log file

**Format**:
```
⚠️  Alerts: [Actions:2 failed] [Feeds:36 zero-count] [Sources:3 down]
```

### Planned Enhancements

- [ ] QClaw message notification
- [ ] GitHub Issue auto-creation
- [ ] Email alerts (optional)

---

## 🎯 Success Metrics

### Current State

```
Health Ratio:  25% (12/48 healthy)
Actions:       100% success
Monitoring:    ✅ Active
Auto-Fix:      ✅ Ready
```

### Target State

```
Health Ratio:  >90% (43/48 healthy)
Uptime:        99.9%
Response:      <1 hour
Fix Time:      <24 hours
```

---

## 🔐 Authorization

### Automatic Actions (No Confirmation Needed)

✅ Fix feeds_meta.json data issues
✅ Monitor all links and sites
✅ Remove confirmed dead sites
✅ Add new RSS sources
✅ Update documentation

### Actions Requiring Confirmation

⚠️ Large-scale site removal (>10 sites)
⚠️ Parser logic changes
⚠️ Performance optimizations

---

## 📚 Documentation

- **Maintenance Plan**: `docs/MAINTENANCE_PLAN.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Recovery Guide**: Repository `RECOVERY_GUIDE.md`
- **Agent Handbook**: Repository `agent-maintenance/README.md`

---

## 🔄 How Recovery Works

### Step 1: Skill Activation

User says: "Use RSSForge maintenance skill"

Agent reads this SKILL.md

### Step 2: Context Restore

```bash
git clone https://github.com/gitfox-enter/RSSForge.git
cd RSSForge
cat agent-maintenance/README.md
cat agent-maintenance/ROADMAP.md
cat agent-artifacts/README.md
```

### Step 3: Resume Operations

```bash
# Check current state
python3 agent-artifacts/scripts/monitor_enhanced.py --pat $PAT

# Fix issues
python3 agent-artifacts/scripts/auto_fix.py --pat $PAT

# Schedule maintenance
# (cron jobs created automatically)
```

### Step 4: Update Skill

```bash
# After significant work, update skill files
cp -r agent-artifacts/scripts/* /path/to/skill/scripts/
cp agent-maintenance/MAINTENANCE_PLAN.md /path/to/skill/docs/
# Commit to skill repository
```

---

## 🛠️ Maintenance Workflow

### Daily (Automated)

1. **7:05** - Morning check
   - Monitor runs
   - Alerts generated
   - Log saved

2. **12:05** - Midday check
   - Monitor runs
   - Compare with morning

3. **18:05** - Evening check
   - Monitor runs
   - End-of-day status

4. **23:05** - Night check
   - Monitor runs
   - Daily summary

---

### Weekly (Automated + Manual Review)

**Sunday 23:00**:

1. Run auto-fix
2. Full site check
3. Clean dead sites
4. Update docs
5. Create weekly report
6. **Manual**: Review report, plan next week

---

### On-Demand (When Alerts Trigger)

1. Read alert details
2. Diagnose problem
3. Apply fix
4. Verify result
5. Update issue tracker

---

## 📝 Issue Tracking

All issues tracked in: `agent-maintenance/issues/ISSUES.md`

**Current Issues**:
- ISSUE-001: Feed Availability Crisis (P0)
- ISSUE-002: Missing Full-Text Content (P1)
- ISSUE-003: Monitoring Coverage Gap (P1) ✅ RESOLVED
- ISSUE-004: Parser Maintenance (P2)
- ISSUE-005: Performance Optimization (P2)

---

## 🔗 Important Links

**GitHub Repository**: https://github.com/gitfox-enter/RSSForge

**RSS Feeds**: https://gitfox-enter.github.io/RSSForge/feeds/

**Agent Handbook**: https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/README.md

**Recovery Guide**: https://github.com/gitfox-enter/RSSForge/blob/main/RECOVERY_GUIDE.md

---

## 💡 Usage Examples

### Example 1: Daily Monitoring

```python
# Agent reads SKILL.md
# Automatically runs at scheduled time

import subprocess

result = subprocess.run([
    "python3",
    "scripts/monitor_enhanced.py",
    "--pat", "YOUR_PAT",
    "--log-dir", "/var/log/rssforge"
], capture_output=True)

if result.returncode != 0:
    # Alerts triggered
    print("⚠️  Issues detected, check log")
else:
    print("✅ All systems healthy")
```

---

### Example 2: Fix Zero-Count Feeds

```python
# Agent detects zero-count > 30
# Runs auto-fix

import subprocess

result = subprocess.run([
    "python3",
    "scripts/auto_fix.py",
    "--pat", "YOUR_PAT"
], capture_output=True)

# Check fix report
with open('/tmp/rssforge-autofix/auto-fix-report.json') as f:
    report = json.load(f)
    print(f"Fixed {report['summary']['feeds_meta_fixed']} feeds")
```

---

### Example 3: Check Specific Site

```python
# User asks: "Check if 线报酷 is accessible"

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

---

## 🎓 Learning Path

### For New Agents

1. Read this SKILL.md
2. Review `agent-maintenance/README.md`
3. Run `diagnose_feeds.py` to understand current state
4. Run `monitor_enhanced.py` to see live status
5. Review `MAINTENANCE_PLAN.md` for procedures

### For Experienced Agents

1. Check latest issue tracker
2. Review recent cron logs
3. Run diagnostics if needed
4. Apply fixes
5. Update documentation

---

## 🔄 Skill Updates

### When to Update This Skill

- After significant fixes applied
- When new monitoring features added
- When maintenance procedures change
- When project structure evolves

### How to Update

```bash
# 1. Update scripts in skill directory
cp -r /path/to/rssforge/scripts/* ./scripts/

# 2. Update documentation
cp /path/to/rssforge/docs/*.md ./docs/

# 3. Commit to skill repository
git add .
git commit -m "chore: update RSSForge maintenance skill"
git push
```

---

## 🤝 Support

**Issues**: Check `agent-maintenance/issues/ISSUES.md`

**Logs**: Check `agent-maintenance/cron-logs/`

**Diagnosis**: Run `scripts/diagnose_feeds.py`

**GitHub**: https://github.com/gitfox-enter/RSSForge/issues

---

## 📋 Checklist for Agent Activation

When activating this skill, agent should:

- [ ] Read this SKILL.md completely
- [ ] Clone RSSForge repository
- [ ] Read agent-maintenance/README.md
- [ ] Run diagnose_feeds.py
- [ ] Run monitor_enhanced.py
- [ ] Check issue tracker
- [ ] Schedule cron jobs
- [ ] Report status to user

---

**Skill Version**: 1.0.0
**Last Updated**: 2026-07-11
**Repository**: https://github.com/gitfox-enter/RSSForge
**Agent**: RSSForge Maintenance Specialist
