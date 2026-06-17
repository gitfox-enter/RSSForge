# Update Frequency & Scheduling

RSSForge controls the crawl frequency for each site through the `interval` field and `tier` level in `sites.yaml`.

## interval — Crawl Interval

```yaml
sites:
  - url: "https://news.ixbk.fun/"
    name: 线报酷
    interval: 15    # Check every 15 minutes
```

| interval Value | Actual Frequency (Daytime) | Actual Frequency (Nighttime 23:00-07:00) |
|---------------|---------------------------|------------------------------------------|
| `15` | ~15 minutes | ~45 minutes |
| `30` | ~30 minutes | ~90 minutes |
| `60` | ~1 hour | ~3 hours |
| `120` | ~2 hours | ~6 hours |
| `480` | ~8 hours | ~24 hours |

## tier — Priority Level

`tier` affects the dispatch order within the Actions workflow:

| tier | Recommended Use Case | Characteristics |
|------|---------------------|-----------------|
| `high` | Deal sites, news, real-time feeds | High-frequency crawling, priority access |
| `mid` | Software sites, forums | Moderate frequency |
| `low` | Slowly updating sites | Low frequency, conserves resources |

```yaml
sites:
  - url: "https://news.ixbk.fun/"
    name: 线报酷
    tier: high
    interval: 15

  - url: "https://www.423down.com/"
    name: 423down
    tier: mid
    interval: 60
```

## Nighttime Frequency Reduction

To conserve GitHub Actions runtime, crawl frequency is automatically reduced during nighttime hours (23:00-07:00). The actual interval becomes `interval x 3`.

## fast_check — Quick Check Mode

When enabled, the crawler only checks whether a page has changed without parsing its content, significantly reducing resource usage:

```yaml
sites:
  - url: "https://status.example.com/"
    name: 服务状态页
    fast_check: true
```

Suitable scenarios:
- You only need to know whether a page has been updated, without extracting detailed content
- The page contains a large amount of data but changes infrequently
- You want to reduce Actions runtime

## Smart Scheduling (adaptive_tiers)

RSSForge also supports dynamically adjusting site priority based on activity:

- **Updated within the last 7 days** - Automatically promoted to a higher tier
- **No updates for 3 consecutive days** - Automatically demoted to a lower tier
- **No updates for 7 consecutive days** - Marked as a dead site; crawling paused

Adjustment records are saved in `adaptive_tiers.json` and can be manually restored.

## Actual Update Frequency

Since GitHub Actions has a minimum trigger interval of 1 minute, the actual update frequency depends on:
1. The cron configuration of the Actions workflow
2. The site's `interval` setting
3. The number of sites currently in the queue

Recommended `interval` settings:
- **Mission-critical sites**: `15` minutes
- **Important sites**: `30-60` minutes
- **General sites**: `120-480` minutes
