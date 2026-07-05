# Contributing Guide

Thank you for your interest in RSSForge! This document explains how to contribute to the project.

## How to Fork and Submit a PR

1. **Fork the repository** — Click the `Fork` button on the top right of the GitHub page to copy the project to your account.
2. **Create a branch** — Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-new-site
   ```
3. **Develop and test** — After making changes locally, make sure tests pass:
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```
4. **Commit your code** — Use clear commit messages:
   ```bash
   git commit -m "feat: add XX site parser"
   ```
5. **Push and create a PR** — Push to your Fork, then create a Pull Request on GitHub and fill in the required information in the PR template.

## Adding a New Site

### sites.yaml Format

Add a new site to the `sites` list in `sites.yaml`:

```yaml
- url: "https://example.com/"    # Site URL (required)
  name: Example Site              # Display name (required)
  tier: medium                    # Crawl priority: high / medium / low
  interval: 60                    # Minimum crawl interval (minutes)
  max_pages: 3                    # Maximum pagination depth
  fast_check: false               # Whether to participate in fast check
  js_render: false                # Whether Playwright JS rendering is needed
  rss_feed: ""                    # RSS feed URL (optional; use native RSS if available)
  parser: ""                      # Parser identifier (optional; see below)
```

**Tier descriptions:**
- `high` — Frequently updated deal sites (15-30 min interval)
- `medium` — Medium-frequency sites (1-2 hour interval)
- `low` — Low-frequency sites (4-12 hour interval)

### Parser Function Naming

1. Create a parser function in the corresponding module under `crawler/parsers/`:
   - Deal/coupon/price sites → `deal_sites.py`
   - Software/resource sites → `software_sites.py`
   - Community forums → `forum_sites.py`
   - RSS/special → `rss_parsers.py`

2. Unified function signature:
   ```python
   def parse_example_items(soup: BeautifulSoup, url: str) -> List[Dict[str, str]]:
       """Parse example.com page and return a list of items.
       
       Each item: {'url': 'item link', 'text': 'item title'}
       """
   ```

3. Register in `crawler/parsers/core.py` `PARSER_REGISTRY`:
   ```python
   'example.com': (parse_example_items, None),
   ```

4. Add the export in `crawler/parsers/__init__.py`.
