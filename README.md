# RSSForge

💗 Everything is RSSible

RSSForge is an open source, easy to use, and extensible RSS feed aggregator built on GitHub Actions, capable of generating RSS feeds from pretty much everything.

**Unlike RSSHub**, RSSForge provides **pre-built, ready-to-subscribe feeds** for all monitored sites. Fork the project, enable GitHub Pages, and you have your own RSS service instantly.

## RSS Feeds

Each monitored site has its own RSS feed at:

```
https://{username}.github.io/RSSForge/feeds/{site-slug}.xml
```

## OPML Subscription

Import the unified OPML file to subscribe all feeds at once.
Choose the mirror that works best for your network:

| Mirror | OPML URL |
|--------|----------|
| Official (GitHub Pages) | `https://gitfox-enter.github.io/RSSForge/opml.xml` |
| ghfast.top (CN accelerated) | `https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.xml` |
| jsDelivr CDN | `https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.xml` |

> **Tip:** Each OPML contains feed URLs pointing to the same mirror — import the one matching your network environment.

## Quick Start

1. **Fork** this repository
2. **Enable GitHub Pages** — Settings → Pages → Deploy from branch → `main` (docs/ folder)
3. **Customize sites.yaml** — Add the sites you want to monitor
4. **Subscribe** — Import one of the OPML files (see above) into any RSS reader

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
| Paywall | `paid_required` | Requires paid account to register or access content |
| Aggressive anti-crawl | `anti_crawl` | Returns 403, blocks known bot patterns, or blocks our fetch methods |
| Malicious download | `spam_download` | Bundles malware, excessive ads, homepage hijacking, misleading download buttons |
| User rejected | `user_hated` | Owner explicitly doesn't want this site monitored |
| Inaccessible | `inaccessible` | Domain expired, parked, or unreachable |
| Non-content site | `not_content` | Pure navigation portals, site directories, link collections, or tool pages with no original article/content listing |

### Current Blacklist (11 sites)

| Domain | Category | Reason |
|--------|----------|--------|
| `store.steampowered.com` | user_hated | Owner explicitly dislikes Steam |
| `store.epicgames.com` | user_hated | Owner explicitly rejects Epic Games Store |
| `ypojie.com` | paid_required | Requires paid registration |
| `52hb.com` | paid_required | Requires paid registration |
| `xdowns.com` | spam_download | Malicious download site |
| `downza.com` | spam_download | Malicious download site |
| `pc6.com` | spam_download | Malicious download site |
| `crsky.com` | anti_crawl | Returns 403 anti-bot |
| `smzdm.com` | anti_crawl | Aggressive anti-crawl, WebFetch cannot retrieve content |
| `hisprice.com` | not_content | Pure tool page (price comparison), no content listing to monitor |
| `ziyuanting.com` | not_content | Site navigation/resource directory, no real-time content to crawl |

### Site Quality Score (How to Evaluate New Sites)

Before adding a new site, score it honestly:

**Must have (all required)**
- Content site (produces original articles/posts, not a directory)
- No paywall or forced login
- Accessible without JavaScript rendering (or only need Playwright for specific pages)
- Provides a list/index page with recent content (can be homepage)
- Not on the blacklist

**Good to have (score each 1 point)**
- Clean HTML, predictable structure (no heavy SPA)
- Consistent URL patterns for articles
- Publication date visible in HTML
- RSS/Atom feed already exists (we can supplement it)
- Reasonable robots.txt policy
- No excessive anti-bot measures

**Immediate rejection**
- Requires payment to read content
- Heavily obfuscated HTML or anti-debugging
- Site is primarily a link directory / navigation portal
- Known bundling of malware or browser hijacking
- User has expressed dislike

**Score >= 3** → Consider adding
**Score < 3** → Probably not worth it

### Enforcement

- **CI guard** — `.github/workflows/blacklist-check.yml` runs on every push to `sites.yaml` / `blacklist.json` and fails if a blacklisted domain is found in the config
- **Import guard** — `crawler/__init__.py` validates against the blacklist at import time and exits with code 1 if violations are found

Any PR that adds a blacklisted site will be automatically rejected by CI.

## Features

- Zero server cost — GitHub Actions free compute, 24/7 auto-run
- Per-site RSS — Each monitored site has its own independent feed
- Real favicons — Automatically fetches and caches website favicons
- Unified OPML — One OPML file to import all feeds into any RSS reader
- Smart scheduling — Per-site intervals (15 min ~ 8 hrs), auto night-mode throttle
- Auto deduplication — MD5 + URL + fuzzy title dedup, 7-day rolling window
- Full article content — Smart content extraction for selected sites
- Public feed directory — Browse all feeds at the index page
- Custom sources — Add your own feeds via `custom_sources.yaml` (no code changes needed)

## Related Projects

- [RSSHub](https://github.com/DIYgod/RSSHub) | Open source RSS feed aggregator, the inspiration for RSSForge
- [RSS-Bridge](https://github.com/RSS-Bridge/rss-bridge) | PHP-based RSS generator
- [RSSHub Radar](https://github.com/DIYgod/RSSHub-Radar) | Browser extension to discover and subscribe to RSS feeds

## License

MIT

---

## 📖 feedforge — 在线 RSS 阅读器

RSSForge 生成的 RSS 订阅源，现在可以直接在网页中阅读！

**访问方式：** 将订阅源 URL 填入下方输入框，或直接访问 `/{username}.github.io/reader/` 路径（需部署后）。

> 阅读器源码位于 [`reader/`](reader/) 目录，由 GitHub Actions 自动更新。

---

## 🚀 在线阅读

打开 [RSSForge 阅读器](https://gitfox-enter.github.io/RSSForge/)，粘贴 RSS 链接即可阅读！📖

> 内置阅读器已替代旧版订阅页，可直接浏览所有生成的 RSS 内容。

---

## 🤖 ima 知识库集成

RSSForge 支持将抓取的 RSS 内容自动导入 [ima 知识库](https://ima.qq.com/)，实现信息聚合与知识管理的一体化流程。

### 配置方式

1. 在仓库根目录创建 `config/sites_to_folders.yaml`，配置站点与 ima 知识库文件夹的映射关系：

```yaml
# config/sites_to_folders.yaml
site_slug_1: folder_id_1
site_slug_2: folder_id_2
```

2. 设置以下环境变量（GitHub Secrets）：
   - `IMA_COOKIE` — ima 知识库的登录 Cookie
   - `IMA_CSRF_TOKEN` — ima 知识库的 CSRF Token

### 工作流程

每次 RSS 抓取完成后，自动触发 `scripts/ima_import_workflow.py`：

1. 读取 `items_latest.json` 中的最新 RSS 条目
2. 根据 `sites_to_folders.yaml` 映射到对应 ima 文件夹
3. 批量导入（10条/批，失败自动重试3次）
4. 自动跳过已导入的条目（基于 MD5 去重）

### 相关文件

- `scripts/ima_import_workflow.py` — 主导入脚本
- `config/sites_to_folders.yaml` — 文件夹映射配置
- `config/sample.sites_to_folders.yaml` — 配置示例

> 此功能为可选集成，不配置映射文件则不会触发 ima 导入。
