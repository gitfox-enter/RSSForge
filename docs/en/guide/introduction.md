# What is RSSForge

RSSForge is a **free RSS feed generator powered by GitHub Actions**.

## The Problem It Solves

Many websites don't offer RSS feeds, but you'd rather not visit each site manually to check for updates. RSSForge solves this for you:

- You want to subscribe to a deal aggregation site (like 线报酷), but it has no RSS
- You want to track new posts on a forum, but it offers no notification system
- You want to monitor price changes on a product page

**RSSForge handles all of this.**

## How It Works

```
Configure the sites you want to follow → GitHub Actions crawls them on a schedule → Generates RSS files → Subscribe with your reader
```

The entire workflow runs inside your GitHub repository. No server resources consumed, no money spent.

## RSSForge vs RSSHub

| | RSSHub | RSSForge |
|---|---|---|
| Deployment | Self-hosted server / Docker | Fork + GitHub Pages |
| Cost | Requires a server | Completely free |
| Feed generation | Real-time on each request | Pre-built static XML |
| Best for | Occasional browsing, few routes | Long-term stable subscriptions |
| Customization | Requires writing route rules | Just edit sites.yaml |

## Technical Features

- **Multiple parsers**: Ships with 40+ site-specific parsers and automatic site type detection
- **JS rendering support**: Playwright handles pages that require JavaScript rendering
- **Smart scheduling**: Automatically assigns crawl frequency based on site tier (high/mid/low), with reduced frequency during nighttime hours
- **Automatic deduplication**: Content-similarity-based dedup ensures no duplicate entries
- **Historical backfill**: Supports paginated crawling to fetch historical content when a site is first added
- **Site icons**: Each feed automatically displays the corresponding website's favicon

## License

RSSForge is open source under the MIT License. You are free to fork, modify, and use it commercially.
