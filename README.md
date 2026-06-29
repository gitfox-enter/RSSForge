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
