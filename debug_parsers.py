#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script: test parsers on live sites."""

import sys
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

from common import *
from crawler.parsers import _match_parser
from crawler.parsers.core import fetch_page_content, PARSER_REGISTRY

# Target sites to debug
TARGETS = [
    ("https://yangmao.wang/", "羊毛王"),
    ("https://www.007ymd.com/", "007羊毛党"),
    ("https://m.hybase.com/", "好赚网"),
    ("https://www.huodong5.com/", "活动5"),
    ("https://www.wobangzhao.com/", "我不找"),
    ("https://10000yun.com/", "万云积分"),
    ("https://www.ghxi.com/", "果核剥壳"),
    ("https://xianbaomi.com/", "线报迷"),
]

def main():
    print("=" * 60)
    print("RSSForge Parser Debug Report")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    for url, name in TARGETS:
        print(f"\n{'='*60}")
        print(f"Site: {name} ({url})")
        print(f"{'='*60}")

        # 1. Check parser registry
        parser_pair = _match_parser(url)
        parser_name = "NONE"
        if parser_pair:
            parser_name = parser_pair[0].__name__ if parser_pair[0] else "NONE"
        print(f"Parser: {parser_name}")

        # 2. Fetch page
        print(f"Fetching {url} ...")
        start = time.time()
        ok, content = fetch_page_content(url)
        elapsed = time.time() - start

        if not ok:
            print(f"FETCH FAILED ({elapsed:.1f}s): {content}")
            results.append({
                "site": name, "url": url, "parser": parser_name,
                "fetch": "FAIL", "error": str(content),
                "items": 0, "html_snippet": ""
            })
            continue

        print(f"Fetch OK ({elapsed:.1f}s)")
        title = content.get('title', '')
        summary = content.get('summary', '')[:100]
        items = content.get('items', [])
        text = content.get('text', '')

        print(f"Title: {title}")
        print(f"Summary: {summary}...")
        print(f"Items extracted: {len(items)}")

        if items:
            print("First 5 items:")
            for i, item in enumerate(items[:5]):
                print(f"  [{i+1}] {item.get('text', '')[:80]}")
                print(f"      -> {item.get('url', '')[:100]}")
        else:
            print("NO ITEMS! Dumping HTML snippet for debugging...")
            print(f"HTML (first 2000 chars):\n{text[:2000]}")

        results.append({
            "site": name, "url": url, "parser": parser_name,
            "fetch": "OK", "error": "",
            "items": len(items),
            "title": title,
            "first_items": items[:5] if items else [],
            "html_snippet": text[:500] if not items else ""
        })

    # Write JSON report
    report_path = "debug_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n\nReport saved to {report_path}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "OK" if r['fetch'] == 'OK' and r['items'] > 0 else "FAIL"
        print(f"  [{status}] {r['site']}: {r['items']} items (parser: {r['parser']}, fetch: {r['fetch']})")

if __name__ == '__main__':
    main()
