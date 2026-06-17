# Paginated Crawling & Historical Backfill

When you first add a site, it usually already contains a large amount of historical content. RSSForge supports paginated crawling to bring all that historical content into your feed.

## The Problem

Most sites only display their latest content on the homepage, with older entries pushed to pages 2, 3, 4, and beyond. If you only crawl the homepage, all that older content is lost:

```
Site homepage (crawl scope):
  Items 1-30   — Today's and recent content
  Items 31-500 — Older content (missed)
```

## Enabling Paginated Crawling

Add a `max_pages` field to your site entry in `sites.yaml`:

```yaml
sites:
  - url: "https://www.example.com/"
    name: 示例论坛
    max_pages: 5    # Crawl 5 pages of historical content
    interval: 60
```

## How Pagination Works

When `max_pages > 1`, the crawler will:

1. **Crawl page 1** - Parse entries and detect the "next page" link
2. **Follow the next page link** - Continue to page 2
3. **Repeat until `max_pages` is reached or no more pages are found**

### Next Page Detection

The crawler automatically identifies the following common pagination patterns:

| Pattern | Examples |
|---------|----------|
| Chinese text | "下一页", "下页" |
| English text | `next`, `older`, `later` |
| Special symbols | `»`, `›`, `→` |
| HTML attributes | `rel="next"` |
| CSS selectors | `.pagination .next`, `.pager li.next` |

## Example: Douban Group Historical Backfill

```yaml
sites:
  - url: "https://www.douban.com/group/711811/"
    name: 豆瓣某小组
    max_pages: 10    # Crawl 10 pages, roughly 300 historical posts
    interval: 120
    tier: mid
```

## Automatic Deduplication

During paginated crawling, entries with the same URL are only kept once. There is no risk of duplicates across pages.

## Important Notes

- **Initial backfill generates many requests**: The more pages you configure, the longer the first run will take
- **Use a larger `interval`**: After the initial backfill is complete, a longer crawl interval is usually sufficient for daily use
- **Not all sites support pagination**: Sites that use infinite scroll cannot be paginated
- **Avoid excessively high `max_pages`**: Setting it to 5-10 pages is usually enough. Very high values may cause timeouts

## Recommended Settings

| Site Type | Recommended `max_pages` | Notes |
|-----------|------------------------|-------|
| Forums / Communities | 5-10 | Posts tend to be valuable; worth preserving more history |
| Deal / News aggregators | 1-3 | High update frequency; historical value is limited |
| Software sites | 3-5 | Slow release cycles; older versions are often useful |
| E-commerce / Price monitoring | 1-2 | Focus on new listings; limited historical value |
