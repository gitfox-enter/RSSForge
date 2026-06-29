# RSSForge

💗 Everything is RSSible

RSSForge is an open source, easy to use, and extensible RSS feed aggregator built on GitHub Actions, capable of generating RSS feeds from pretty much everything.

**Unlike RSSHub**, RSSForge provides **pre-built, ready-to-subscribe feeds** for all monitored sites. Fork the project, enable GitHub Pages, and you have your own RSS service instantly.

## RSS Feeds

Each monitored site has its own RSS feed at:

```
https://{username}.github.io/RSSForge/feeds/[站点名称].xml
```

## OPML Subscription

Import the unified OPML file to subscribe all feeds at once:

```
https://{username}.github.io/RSSForge/opml.xml
```

## Quick Start

1. **Fork** this repository
2. **Enable GitHub Pages** — Settings → Pages → Deploy from branch → `gh-pages`
3. **Customize sites.yaml** — Add the sites you want to monitor
4. **Subscribe** — Import `opml.xml` into any RSS reader

## Blacklist — What We Don't Monitor

Sites in `blacklist.json` will **never** be added to monitoring, even if someone submits a PR.

### Why

Many sites look promising on the surface but are fundamentally unsuitable as RSS sources:
- **Anti-crawl / paywall** — return 403, require login, or block bots
- **Malicious downloads** — bundling malware, aggressive ads, homepage hijacking
- **No real content** — pure navigation portals, site directories, or tool pages
- **User preferences** — sites the owner explicitly doesn't want

Before adding a new site, always check if it appears in `blacklist.json`.

### Categories

| Category | Code | Description |
|----------|------|-------------|
| 付费门槛 | `paid_required` | Requires paid account to register or access content |
| 反爬严格 | `anti_crawl` | Returns 403, blocks known bot patterns, or blocks our fetch methods |
| 流氓下载站 | `spam_download` | Bundles malware, excessive ads, homepage hijacking, misleading download buttons |
| 用户讨厌 | `user_hated` | Owner explicitly doesn't want this site monitored |
| 不可访问 | `inaccessible` | Domain expired, parked, or unreachable |
| 非内容站点 | `not_content` | Pure navigation portals, site directories, link collections, or tool pages with no original article/content listing |

### Current Blacklist (11 sites)

| Domain | Category | Reason |
|--------|----------|--------|
| `store.steampowered.com` | user_hated | 所有者明确讨厌 Steam |
| `store.epicgames.com` | user_hated | 所有者明确要求不要 Epic Games Store |
| `ypojie.com` | paid_required | 亿破解需要付费注册才能使用 |
| `52hb.com` | paid_required | 52破解需要付费注册才能使用 |
| `xdowns.com` | spam_download | 流氓下载站 |
| `downza.com` | spam_download | 流氓下载站 |
| `pc6.com` | spam_download | 流氓下载站 |
| `crsky.com` | anti_crawl | 返回 403 反爬 |
| `smzdm.com` | anti_crawl | 反爬严格，WebFetch 无法获取内容 |
| `hisprice.com` | not_content | 纯工具页（比价查询），无内容列表可监控 |
| `ziyuanting.com` | not_content | 网站导航/资源目录，非内容站点，无法抓取实时资源内容 |

### Site Quality Score (How to Evaluate New Sites)

Before adding a new site, score it honestly:

**✅ Must have (all required)**
- Content site (produces original articles/posts, not a directory)
- No paywall or forced login
- Accessible without JavaScript rendering (or only need Playwright for specific pages)
- Provides a list/index page with recent content (can be homepage)
- Not on the blacklist

**🔍 Good to have (score each 1 point)**
- Clean HTML, predictable structure (no heavy SPA)
- Consistent URL patterns for articles
- Publication date visible in HTML
- RSS/Atom feed already exists (we can supplement it)
- Reasonable robots.txt policy
- No excessive anti-bot measures

**❌ Immediate rejection**
- Requires payment to read content
- Heavily obfuscated HTML or anti-debugging
- Site is primarily a link directory / navigation portal
- Known bundling of malware or browser hijacking
- User has expressed dislike

**Score ≥ 3** → Consider adding
**Score < 3** → Probably not worth it

### Enforcement

- **CI guard** — `.github/workflows/blacklist-check.yml` runs on every push to `sites.yaml` / `blacklist.json` and fails if a blacklisted domain is found in the config
- **Import guard** — `crawler/__init__.py` validates against the blacklist at import time and exits with code 1 if violations are found

Any PR that adds a blacklisted site will be automatically rejected by CI.

## Features

- 🔧 **Zero server cost** — GitHub Actions free compute, 24/7 auto-run
- 📡 **Per-site RSS** — Each monitored site has its own independent feed
- 🖼️ **Real favicons** — Automatically fetches and caches website favicons
- 📋 **Unified OPML** — One OPML file to import all feeds into any RSS reader
- ⚡ **Smart scheduling** — Per-site intervals (15 min ~ 8 hrs), auto night-mode throttle
- 🔄 **Auto deduplication** — MD5 + URL + fuzzy title dedup, 7-day rolling window

## Related Projects

- [RSSHub](https://github.com/DIYgod/RSSHub) | Open source RSS feed aggregator, the inspiration for RSSForge
- [RSS-Bridge](https://github.com/RSS-Bridge/rss-bridge) | PHP-based RSS generator
- [RSSHub Radar](https://github.com/DIYgod/RSSHub-Radar) | Browser extension to discover and subscribe to RSS feeds

## License

MIT
