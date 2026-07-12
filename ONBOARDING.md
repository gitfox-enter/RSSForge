# RSSForge Onboarding Guide

> For people who are new to this project and want to understand how it works without reading code.

---

## TL;DR

RSSForge is a tool that **automatically turns website content into RSS feeds**, running on GitHub for **zero cost**.

## What Does This Project Do?

Imagine you follow 47 forums/websites and manually visiting each one every day is tedious. RSSForge is a bot that:
1. Automatically checks these websites every 30 minutes for new content
2. Formats the new content into standard RSS
3. Publishes it to a webpage that your RSS reader can subscribe to

## Core Concepts (Only 5)

| Concept | What It Is | File | When You Care |
|---------|-----------|------|--------------|
| Site config | Which websites to monitor | `sites.yaml` | Most frequently edited. Add/remove sites here |
| Crawl engine | How to fetch website content | `crawler/engine.py` | Rarely changed, unless crawling fails |
| Parsers | How to read webpage content | `crawler/parsers/*.py` | May need to write one when adding a new site |
| Feed generator | Turn content into RSS files | `rss_feed.py` | Rarely changed |
| Automation | Schedule the above steps | `.github/workflows/*.yml` | Change when adjusting run frequency |

## File Map

```
RSSForge/
├── sites.yaml                 ← MOST IMPORTANT: all site configurations
├── common.py                  ← shared utility functions
├── crawl.py                   ← entry point: run the crawler
├── rss_feed.py                ← entry point: generate RSS files
├── opml_generator.py          ← entry point: generate OPML (batch subscribe file)
├── generate_feeds_index.py    ← entry point: generate index page
├── crawler/
│   ├── engine.py              ← main crawl engine (async)
│   ├── config.py              ← reads sites.yaml config
│   ├── parsers/               ← per-site parsers
│   │   ├── core.py            ← parser registry (domain → function)
│   │   ├── deal_sites.py      ← deal/coupon site parsers
│   │   ├── software_sites.py  ← software site parsers
│   │   └── rss_parsers.py     ← native RSS feed parsers
│   └── ...
├── docs/                      ← GitHub Pages deployment directory
│   ├── index.html             ← index page
│   ├── feeds/*.xml            ← per-site RSS files
│   ├── opml.xml               ← batch subscribe file
│   └── icons/                 ← website favicons
└── .github/workflows/         ← GitHub Actions automation
    ├── crawl.yml              ← full crawl every 30 min
    ├── fast_check.yml         ← incremental check every 30 min
    └── daily_summary.yml      ← daily summary at 22:00
```

## How the Automation Works

```
GitHub Actions triggers on schedule (every 30 min)
    ↓
Run crawl.py → visit websites → fetch new content → save to items.json
    ↓
Run rss_feed.py → read items.json → generate docs/feeds/*.xml
    ↓
Run opml_generator.py → generate docs/opml.xml
    ↓
Run generate_feeds_index.py → generate docs/index.html
    ↓
git push → GitHub Pages updates → your RSS reader gets new content
```

## What You'll Do Day-to-Day

### 1. Add a New Site (Most Common)

Edit `sites.yaml`, add to the end of the `sites:` list:

```yaml
  - url: "https://example.com/"
    name: Example Site
    tier: medium        # high=15-30min, medium=1-2hr, low=4-12hr
    interval: 60        # minimum crawl interval (minutes)
    max_pages: 5        # max pagination depth
    fast_check: true    # participate in fast check
```

If the website has a native RSS feed, just add `rss_feed: "https://example.com/feed/"` — no parser needed.

If no RSS, you'll need to write a parser function in `crawler/parsers/` and register it in `crawler/parsers/core.py`.

### 2. Remove a Dead Site

Find the site in `sites.yaml` and delete the entry. Add a record under `dead_sites:`:

```yaml
dead_sites:
  "https://example.com/":
    reason: "Site shut down"
    confirmed_at: "2026-07-05"
```

### 3. Check Running Status

- GitHub repo **Actions** page → view run logs
- `docs/crawl_status.json` → last crawl status per site
- `feeds_meta.json` → item count per site

### 4. Manually Trigger a Crawl

GitHub repo → Actions → select "站点更新监控" → Run workflow

## sites.yaml Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | Website URL |
| `name` | Yes | Display name |
| `tier` | No | Priority: high/medium/low, default medium |
| `interval` | No | Minimum crawl interval (minutes), default 30 |
| `max_pages` | No | Max pagination depth, default 5 |
| `fast_check` | No | Participate in fast check, default false |
| `js_render` | No | Need Playwright for JS rendering, default false |
| `rss_feed` | No | Native RSS feed URL (no parser needed if present) |
| `parser` | No | Custom parser identifier |

## FAQ

**Q: Why do some sites have no content?**
A: The site may have anti-crawl measures, a broken parser, or simply no updates. Check the Actions log for errors.

**Q: How to increase crawl frequency?**
A: Change the site's `tier` to `high` and reduce `interval` (e.g. 15) in `sites.yaml`.

**Q: How to know which sites are active?**
A: Check `feeds_meta.json` — sites with `count > 0` have content.

**Q: How do my code changes take effect?**
A: Push to the `main` branch on GitHub. The next Actions run will use the new code automatically.

## Tech Stack

- **Language**: Python 3.11
- **Crawler**: aiohttp (async HTTP) + Playwright (JS rendering)
- **RSS**: Atom format (XML)
- **Hosting**: GitHub Pages (free static hosting)
- **Automation**: GitHub Actions (free CI/CD)
- **Storage**: JSON files (items.json, feeds_meta.json, etc.)

## Current Status (2026-07-05)

- Configured sites: 48
- Sites with content: 7
- Total items: 11,914
- Auto-run frequency: every 30 minutes
