# Site Update Monitor

A production-grade, multi-site content change monitoring system powered by GitHub Actions. Crawls 47 deal, coupon, and resource sites on schedule, detects content updates via MD5 fingerprinting, and aggregates results into a live SPA frontend.

## Architecture

```
GitHub Actions (cron)
    │
    ├── crawl.py (Full Crawl)         — 47 sites, 3× daily (Beijing 8/13/18)
    ├── fast_check.py (Fast Check)    — 12 priority sites, every 30 min (Beijing 9–21)
    │
    ├── items.json                    — data store (max 1500 items, deduplicated)
    ├── hash_record.json              — per-site content fingerprints
    ├── run_log.jsonl                 — structured run history (last 30 runs)
    │
    ├── index.html                    — PWA SPA frontend
    └── sw.js                         — service worker (network-first for data)
```

## Key Features

- **47 monitored sites** with site-specific parsers (WordPress, Discuz, RSS, custom CMS)
- **Plugin-based parser registry** (`PARSER_REGISTRY`) for easy site addition
- **Anti-detection**: 8 consistent browser profiles (UA + sec-ch-ua + language), random crawl order, referer spoofing, cookie persistence
- **Resilience**: exponential backoff retry (1s / 2s / 4s), per-domain circuit breaker, graceful SIGTERM / SIGINT shutdown
- **Security**: SSRF protection (redirect target validation), URL scheme validation, 10 MB response size limit, HTTPS auto-upgrade
- **Data integrity**: atomic file writes (write-to-tmp + os.replace), JSON hash records with schema versioning
- **Monitoring**: structured JSON logging, metrics tracking, SLA-aware self-analysis with run log rotation
- **Performance**: ThreadPoolExecutor (6 workers), per-domain rate limiting, HTTP conditional requests (ETag / Last-Modified), O(1) source name lookup
- **CI/CD**: automated test suite (162 tests), GitHub Actions with concurrency groups, timeout limits, and 5-attempt push with rebase conflict resolution

## Project Structure

| File | Purpose |
|------|---------|
| `common.py` | Shared utilities: JSON formatter, data persistence, blacklist, sanitization, metrics |
| `crawl.py` | Full crawl engine: 47-site parser registry, 6-thread pool, anti-detection, retry logic |
| `fast_check.py` | Lightweight checker for 12 priority sites with quick fingerprint comparison |
| `blacklist.json` | Configurable title / URL / domain blacklist |
| `index.html` | PWA SPA frontend with search, filtering, and pagination |
| `sw.js` | Service worker for offline support and network-first data fetching |
| `.github/workflows/crawl.yml` | Scheduled full crawl (3× daily) CI workflow |
| `.github/workflows/fast_check.yml` | Scheduled fast check (every 30 min) CI workflow |
| `.github/workflows/pages.yml` | GitHub Pages deployment workflow |

## Live Demo

Visit the live dashboard: [gitfox-enter.github.io/site-update-monitor](https://gitfox-enter.github.io/site-update-monitor/)

## License

MIT