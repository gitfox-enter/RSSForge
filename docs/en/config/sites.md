# sites.yaml Site Configuration

`sites.yaml` is the core configuration file in RSSForge. It defines all the sites you want to subscribe to.

## File Location

Repository root: `sites.yaml`

## Full Field Reference

```yaml
sites:
  - url: "https://example.com/"
    name: 示例网站
    tier: high
    interval: 15
    fast_check: true
    max_pages: 3
    enabled: true
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | **Required** | The full URL of the target site. Must start with `http://` or `https://` |
| `name` | string | **Required** | Display name for the site, shown on the homepage and in feed titles |
| `tier` | string | `high` | Priority level that affects the Actions dispatch order: `high` / `mid` / `low` |
| `interval` | int | `30` | Crawl interval in minutes. The actual interval is also affected by `fast_check` and nighttime weighting |
| `fast_check` | bool | `false` | When enabled, only detects page hash changes without parsing content (saves resources) |
| `max_pages` | int | `1` | Number of historical pages to crawl on first backfill. Values greater than 1 enable paginated crawling |
| `enabled` | bool | `true` | Whether the site is active. Set to `false` to skip this site |

## Configuration Examples

### Basic Configuration

```yaml
sites:
  - url: "https://news.ixbk.fun/"
    name: 线报酷
```

### High-Frequency Update Sites

```yaml
sites:
  - url: "https://www.zhuanyes.com/xianbao/"
    name: 专业线报
    tier: high
    interval: 15
```

### Sites That Need Historical Backfill

```yaml
sites:
  - url: "https://www.douban.com/group/711811/"
    name: 豆瓣小组
    max_pages: 5        # Crawl 5 pages of history on first run
    interval: 60
```

### Change Detection Only (No Content Parsing)

```yaml
sites:
  - url: "https://status.example.com/"
    name: 服务状态页
    fast_check: true    # Only detect whether changes occur, skip content extraction
```

## Organizing by Category

We recommend organizing sites by category and using comments as separators:

```yaml
sites:
  # ============================================================
  # Aggregated deal sites (frequent updates, every 15-30 min)
  # ============================================================
  - url: "https://news.ixbk.fun/"
    name: 线报酷
    tier: high
    interval: 15

  - url: "https://xianbao.icu/"
    name: 线报ICU
    tier: high
    interval: 15

  # ============================================================
  # Software resource sites (slower updates, every 1-2 hours)
  # ============================================================
  - url: "https://www.423down.com/"
    name: 423down
    tier: mid
    interval: 60
```

## Important Notes

- **URLs must be unique**: No two sites can share the exact same URL
- **YAML indentation**: Use spaces (2 spaces per level), not tabs
- **Annotate long URLs**: Add comments for easier maintenance later
- **Clean up periodically**: Set unused sites to `enabled: false` rather than deleting them outright (preserves configuration history)
