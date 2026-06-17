# Filtering & Blacklist

RSSForge provides a multi-layered filtering system to help you keep only the content that truly matters.

## Content Filtering Rules

### Keyword Filtering

Add blacklist keywords to `blacklist.json`. Any content containing these keywords will be automatically filtered out:

```json
{
  "keywords": [
    "广告",
    "推广",
    "[招聘]",
    "【限时】"
  ],
  "domains": [],
  "patterns": []
}
```

### Regex Filtering

Use regular expressions for more flexible matching:

```json
{
  "patterns": [
    "^\\[广告\\]",
    "请点击查看全文",
    "^抢.*红包"
  ]
}
```

### Domain Blacklist

If a particular subdomain of a site consistently produces low-quality content, you can block it:

```json
{
  "domains": [
    "ads.example.com",
    "click.example.com"
  ]
}
```

## Site-Level Blacklist

You can disable entire sites via the `sites` section in `blacklist.json`:

```json
{
  "sites": {
    "https://spam.example.com/": "已停用，转向新站"
  }
}
```

Blacklisted sites will be marked as `dead` in `crawl_status.json`.

## Generic Parser vs. Dedicated Parser

| Parser | Description | Use Case |
|--------|-------------|----------|
| **Dedicated Parser** | Tailored to the HTML structure of specific sites for high accuracy | 40+ sites already included in `deal_sites.py` |
| **Generic Parser** | Attempts to extract all `<a>` links and titles; flexible but may produce noise | Sites not in the dedicated parser list |

If a dedicated parser produces poor-quality results for a site, you can switch to the generic parser by removing the corresponding entry from `deal_sites.py`.

## Content Deduplication

RSSForge uses two layers of deduplication:

### 1. URL Deduplication
Entries with the same URL are kept as a single record. This is used for cross-page deduplication during paginated crawling.

### 2. Content Similarity Deduplication
Entries are deduplicated based on MD5 hashes of titles and content. Items with more than 90% similarity are filtered out.

```python
# Core similarity calculation logic (from common.py)
similarity = jaccard(words1, words2)
if similarity > 0.9:
    # Filter duplicate content
    pass
```

## Junk Content Filtering

The `is_junk()` function automatically filters out the following types of content:

- Titles consisting only of numbers or symbols
- Titles shorter than 3 characters
- Titles longer than 999 characters
- Content containing common spam phrases such as "click to view", "log in", or "sign up"

## Minimum Entry Count Protection

Some parsers include a minimum entry count safeguard (e.g., `parse_423down_items` requires at least 3 entries) to prevent false "empty page" detection when only navigation links are captured.
