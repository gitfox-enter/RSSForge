# Site Update Monitor

A production-grade, multi-site content change monitoring system powered by GitHub Actions. Crawls 47 deal/coupon/resource sites on schedule, detects content updates via MD5 fingerprinting, and aggregates results into a live SPA frontend.

## Architecture

```
GitHub Actions (cron)
    |
    +-- crawl.py (Full Crawl)     -- 47 sites, 3x daily (Beijing 8/13/18)
    +-- fast_check.py (Fast Check) -- 12 top sites, every 30 min (Beijing 9-21)
    |
    +-- items.json (data store, max 1500 items, deduplicated)
    +-- hash_record.json (per-site content fingerprints)
    +-- run_log.jsonl (structured run history, last 30 runs)
    |
    +-- index.html (PWA SPA frontend)
    +-- sw.js (service worker, network-first for data)
```

## Key Features

- **47 monitored sites** with site-specific parsers (WordPress, Discuz, RSS, custom CMS)
- **Plugin-based parser registry** (`PARSER_REGISTRY`) for easy site addition
- **Anti-detection**: 8 consistent browser profiles (UA + sec-ch-ua + language), random crawl order, referer spoofing, cookie persistence
- **Resilience**: exponential backoff retry (1s/2s/4s), per-domain circuit breaker, graceful SIGTERM/SIGINT shutdown
- **Security**: SSRF protection (redirect target validation), URL scheme validation, 10MB response size limit, HTTPS auto-upgrade
- **Data integrity**: atomic file writes (write-to-tmp + os.replace), JSON hash records with schema versioning
- **Monitoring**: structured JSON logging, metrics tracking, SLA-aware self-analysis with run log rotation
- **Performance**: ThreadPoolExecutor (6 workers), per-domain rate limiting, HTTP conditional requests (ETag/Last-Modified), O(1) source name lookup
- **CI/CD**: automated test suite (162 tests), GitHub Actions with concurrency groups, timeout limits, and 5-attempt push with rebase conflict resolution

## Project Structure

| File | Purpose |
|------|---------|
| `common.py` | Shared utilities: JSON formatter, data persistence, blacklist, sanitization, MD5, rate limiter |
| `crawl.py` | Full crawler: 47 sites, parsers, change detection, self-analysis, git commit |
| `fast_check.py` | Incremental checker: 12 top sites, high frequency, lightweight |
| `test_crawler.py` | 162 unit tests covering parsers, data management, blacklist, utilities |
| `index.html` | PWA SPA frontend with search, categories, infinite scroll |
| `items.json` | Aggregated content database (max 1500 items) |
| `hash_record.json` | Per-site content fingerprints for change detection |
| `blacklist.json` | Domain blacklist (user-hated, anti-crawl, spam sites) |

## Adding a New Site

1. Add the URL to `MONITOR_SITES` in `crawl.py`
2. Add a display name to `SOURCE_NAME_MAP`
3. (Optional) Write a site-specific parser function and register it in `PARSER_REGISTRY`
4. The generic extractor handles most sites automatically

## Local Development

```bash
pip install -r requirements.txt
python -m pytest test_crawler.py -v   # Run tests
python crawl.py                        # Full crawl
python fast_check.py                   # Fast check
```

## Requirements

- Python 3.10+
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.2
- charset-normalizer >= 3.0.0

## License

MIT
