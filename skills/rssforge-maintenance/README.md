# RSSForge Maintenance Skill

**Version**: 1.0.0
**Created**: 2026-07-11
**Author**: RSSForge Maintenance Agent
**Repository**: https://github.com/gitfox-enter/RSSForge

---

## Purpose

This skill enables any agent to maintain the RSSForge RSS aggregation project with automated monitoring, self-healing, and recovery capabilities.

---

## What's Included

```
rssforge-maintenance/
├── SKILL.md                    # This file - Skill definition
├── scripts/                    # Core maintenance tools
│   ├── monitor_enhanced.py     # Health monitoring
│   ├── auto_fix.py             # Automatic repair
│   └── diagnose_feeds.py       # Problem diagnosis
├── docs/                       # Documentation
│   ├── MAINTENANCE_PLAN.md     # Detailed maintenance plan
│   └── QUICK_REFERENCE.md      # Quick reference card
└── examples/                   # Usage examples
    └── EXAMPLES.md             # 10 detailed examples
```

---

## Quick Start

### 1. Activate Skill

Read `SKILL.md` to activate RSSForge maintenance capabilities.

### 2. Configure PAT

Set GitHub Personal Access Token:
```bash
export GITHUB_PAT="ghp_your_token_here"
```

### 3. Run Health Check

```bash
python3 scripts/monitor_enhanced.py --pat $GITHUB_PAT
```

### 4. View Results

Check console output or log files in `cron-logs/`

---

## Core Features

### ✅ Automated Monitoring
- GitHub Actions status
- Feed health (healthy vs zero-count)
- RSS link accessibility
- Source site availability

### ✅ Auto-Fix Mechanisms
- Repair feeds_meta.json URL fields
- Sync with sites.yaml
- Commit fixes to GitHub

### ✅ Link Validation
- Check RSS feed endpoints
- Validate source sites
- Mark dead sites for removal

### ✅ Agent Recovery
- Restore context from GitHub
- Resume operations immediately
- Self-documenting procedures

---

## Scheduled Tasks

**Daily** (4x):
- Time: 7:05, 12:05, 18:05, 23:05
- Task: Health monitoring

**Weekly** (Sundays):
- Time: 23:00
- Task: Deep maintenance + auto-fix

---

## Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Actions failed > 1 | 🔴 High | Investigate immediately |
| Zero-count > 30 | 🔴 High | Run auto-fix |
| GitHub Pages down | 🔴 Critical | Fix immediately |
| Source sites down > 3 | 🟡 Medium | Weekly cleanup |

---

## Key Links

**Repository**: https://github.com/gitfox-enter/RSSForge
**RSS Feeds**: https://gitfox-enter.github.io/RSSForge/feeds/
**Handbook**: https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/README.md
**Recovery Guide**: https://github.com/gitfox-enter/RSSForge/blob/main/RECOVERY_GUIDE.md

---

## Current Status

```
Health Ratio:  25% (12/48) → Target: >90%
Monitoring:    ✅ Active
Auto-Fix:      ✅ Ready
Last Check:    2026-07-11 16:36
```

---

## How to Update This Skill

After significant work:

```bash
# Update scripts
cp /path/to/rssforge/scripts/* ./scripts/

# Update docs
cp /path/to/rssforge/docs/* ./docs/

# Commit changes
git add .
git commit -m "chore: update RSSForge maintenance skill"
git push
```

---

## Support

**Issues**: Check `agent-maintenance/issues/ISSUES.md`
**Logs**: Check `agent-maintenance/cron-logs/`
**Diagnosis**: Run `scripts/diagnose_feeds.py`

---

## License

Part of RSSForge project. See repository for license details.

---

**Skill Status**: ✅ Production Ready
**Last Test**: 2026-07-11 16:36
**Next Review**: 2026-07-18
