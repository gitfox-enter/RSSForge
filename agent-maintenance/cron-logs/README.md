# Cron Job Execution Log

This directory contains execution logs for automated cron jobs.

## Naming Convention
```
YYYY-MM-DD_HH-MM_<job-name>.md
```

Example: `2026-07-11_23-05_quality-monitor.md`

## Log Template

```markdown
# Cron Execution: <Job Name>

**Job ID**: <UUID>
**Scheduled**: YYYY-MM-DD HH:MM
**Executed**: YYYY-MM-DD HH:MM
**Duration**: X seconds
**Status**: ✅ SUCCESS / ❌ FAILURE / ⚠️ WARNING

## Checks Performed

### 1. GitHub Actions Status
- Recent runs: X
- Success: X
- Failure: X
- Last run: YYYY-MM-DDTHH:MM:SSZ

### 2. Feed Freshness
- feeds_meta.json updated: YYYY-MM-DD HH:MM
- Time since update: X hours
- Status: ✅ Fresh / ⚠️ Stale / ❌ Critical

### 3. Feed Health
- Total sites: X
- Healthy: X (X%)
- Suspected down: X (X%)

## Findings

### Issues Detected
- [List any issues found]

### Metrics
- [Relevant metrics]

## Actions Taken

### Automatic
- [Any automatic fixes applied]

### Manual Intervention Required
- [Issues requiring user attention]

## Artifacts

- [ ] Updated monitoring snapshot
- [ ] Created/updated GitHub issues
- [ ] Generated reports

## Next Steps

1. [Action items for next run]
2. [Follow-up tasks]

---

**Agent**: agent-606489db
**Commit**: [If changes were made]
```

## Execution Frequency

### Quality Monitoring (Daily 4x)
- 7:05, 12:05, 18:05, 23:05
- Quick health check
- Alert on anomalies
- Log: Brief summary

### Weekly Maintenance (Sundays 23:00)
- Comprehensive audit
- Cleanup operations
- Report generation
- Log: Detailed report

## Log Retention

- Daily logs: Keep 30 days
- Weekly logs: Keep 90 days
- Critical events: Keep indefinitely

## GitHub Integration

All logs are committed to:
```
https://github.com/gitfox-enter/RSSForge/tree/main/agent-maintenance/cron-logs/
```

This ensures:
- Persistent record across platform restarts
- Git history for audit trail
- Easy access for debugging

---

**Created**: 2026-07-11
