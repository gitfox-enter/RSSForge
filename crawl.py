#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Slim entry point — all logic moved to crawler/ package.

Re-exports all public symbols from the crawler package so that
``import crawl; crawl.get_beijing_time()`` works (backward compatibility
with tests and legacy scripts).
"""

import sys

# Re-export everything from the crawler package and its submodules
from common import *  # noqa: F401,F403
# Re-export CATEGORY_KEYWORDS and ITEMS_DB_FILE from common (not in __all__)
from common import CATEGORY_KEYWORDS, ITEMS_DB_FILE  # noqa: F401
from crawler.config import (
    MONITOR_SITES, SOURCE_NAME_MAP, SITE_INTERVALS,
    get_source_name, get_site_tier, is_dead_site, JS_RENDER_SITES,
    REQUEST_TIMEOUT, MAX_RETRIES, RETRY_BASE_DELAY, BROWSER_PROFILES,
    NOTIFIED_ITEMS_FILE, HASH_RECORD_FILE, MAX_ITEMS_DB,
    DEAD_SITES, RUN_LOG_FILE,
)
from crawler.network import (
    MetricsTracker, metrics, rate_limiter,
    is_allowed_by_robots, get_session, get_conditional_headers,
    update_conditional_cache,
)
from crawler.storage import (
    load_items_db, save_items_db, load_blacklist, is_blacklisted,
    get_current_round, load_notified_items, save_notified_items,
    filter_new_items, merge_items_into_db, load_hash_records,
    save_hash_records, export_items_latest_json,
    get_random_delay, get_random_profile, get_referer,
    # Re-export constants for backward compat with tests
    NOTIFIED_ITEMS_FILE, HASH_RECORD_FILE, ITEMS_DB_FILE,
)
from crawler.parsers import (
    _match_parser, extract_article_items, parse_rss_feed,
    parse_ghxi_items, fetch_page_content,
    # Re-export all deal/software/forum parsers for backward compatibility with tests
    parse_423down_items, parse_wycad_items, parse_h6room_items, parse_xzba_items,
    parse_apprcn_items, parse_daydayzhuan_items, parse_007ymd_items,
    parse_baicaio_items_v2, parse_manmanbuy_items, parse_12345pro_items,
    parse_ym2cc_items, parse_wobangzhao_items, parse_haodanku_items,
    parse_hybase_items, parse_huodong5_items, parse_yangmaodang_items,
    parse_xianbaomi_items, parse_yangmao_wang_items, parse_iqnew_items,
    parse_51kanong_items, parse_ymxianbao_items, parse_linejia_items,
    parse_10000yun_items,
    parse_yxssp_items, parse_foxirj_items, parse_appinn_items,
    parse_lsapk_items, parse_thosefree_items, parse_ithome_xijiayi_items,
    parse_discuz_items, parse_douban_group_items,
)

# Import the main function from the crawler engine
from crawler.engine import main

# Lazy-load engine functions and anything not yet defined
_engine_names = {
    'main', 'check_site_update', 'git_commit_if_changed',
    'load_run_log', 'append_run_log', 'analyze_and_fix',
    'export_crawl_status',
    '_handle_signal', '_needs_playwright',
    'PLAYWRIGHT_AVAILABLE',
    'fetch_page_content_async', 'fetch_with_playwright',
    'close_playwright', 'check_one_async', 'main_async',
    'check_site_update_async',
}


def __getattr__(name):
    if name in _engine_names:
        from crawler import engine as _engine
        val = getattr(_engine, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module 'crawl' has no attribute {name!r}")


if __name__ == '__main__':
    main()

# Make crawl.requests accessible for tests that do @patch("crawl.requests.get")
import requests  # noqa: F401
