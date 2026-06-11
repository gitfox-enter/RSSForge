# -*- coding: utf-8 -*-
"""Crawler package — modular refactor of crawl.py.

Re-exports the most commonly used symbols from submodules for backward
compatibility with any code that imports from the old monolithic crawl.py.
"""

# Lazy imports to avoid circular dependencies.
# Import engine last since it brings in Playwright + all heavy deps.
from crawler.config import (
    MONITOR_SITES,
    URL_SHORT_TO_FULL,
    ITEMS_JSON_PATH,
    HASH_RECORD_PATH,
    NOTIFIED_PATH,
    PAUSE_STATE_PATH,
    RUN_LOG_PATH,
    BLACKLIST_PATH,
    SQLITE_DB_PATH,
    MAX_RETRIES,
    RETRY_DELAY,
    CRAWL_TIMEOUT,
    PLAYWRIGHT_TIMEOUT_MS,
    MAX_SITES_PER_ROUND,
    MAX_WORKERS,
    MAX_ITEMS_DB_SIZE,
    IS_GITHUB_ACTIONS,
    GITHUB_ACTOR,
    GITHUB_RUN_ID,
    GITHUB_REPOSITORY,
    BROWSER_PROFILES,
    DEAD_SITES,
)

from crawler.network import (
    MetricsTracker,
    CircuitBreaker,
    get_session,
    get_conditional_headers,
    update_conditional_cache,
    is_allowed_by_robots,
    DomainRateLimiter,
)

from crawler.storage import (
    get_current_round,
    get_random_profile,
    get_random_ua,
    get_random_fingerprint,
    get_random_accept_language,
    get_random_delay,
    get_referer,
    load_hash_records,
    save_hash_records,
    load_notified_items,
    save_notified_items,
    filter_new_items,
    merge_items_into_db,
)

from crawler.parsers import (
    parse_ypojie,
    parse_discuz_threadlist,
    parse_discuz_items,
    parse_yxssp_items,
    parse_423down,
    parse_423down_items,
    parse_ziyuanting_items,
    parse_ziyuanting,
    parse_wycad_items,
    parse_h6room_items,
    parse_xzba_items,
    parse_apprcn_items,
    parse_daydayzhuan_items,
    parse_007ymd_items,
    parse_baicaio_items_v2,
    parse_manmanbuy_items,
    parse_axutongxue_items,
    parse_rss_feed,
    parse_ghxi,
    parse_ghxi_items,
    parse_ym2cc_items,
    parse_wobangzhao_items,
    parse_foxirj_items,
    parse_ddooo_items,
    parse_onlinedown_items,
    extract_article_items,
    parse_12345pro_items,
    parse_appinn_items,
    parse_ithome_xijiayi_items,
    parse_lsapk_items,
    parse_thosefree_items,
    parse_douban_group_items,
    parse_haodanku_items,
    parse_hybase_items,
    parse_huodong5_items,
    parse_yangmaodang_items,
    parse_xianbaomi_items,
    parse_yangmao_wang_items,
    parse_iqnew_items,
    parse_51kanong_items,
    parse_ymxianbao_items,
    parse_linejia_items,
    PARSER_REGISTRY,
    _match_parser,
    fetch_page_content,
)

# engine imports (lazy to avoid circular)
def __getattr__(name):
    if name == 'main':
        from crawler.engine import main
        return main
    if name == 'check_site_update':
        from crawler.engine import check_site_update
        return check_site_update
    if name == 'git_commit_if_changed':
        from crawler.engine import git_commit_if_changed
        return git_commit_if_changed
    if name == 'load_run_log':
        from crawler.engine import load_run_log
        return load_run_log
    if name == 'append_run_log':
        from crawler.engine import append_run_log
        return append_run_log
    if name == 'analyze_and_fix':
        from crawler.engine import analyze_and_fix
        return analyze_and_fix
    if name == 'load_paused_sites':
        from crawler.engine import load_paused_sites
        return load_paused_sites
    if name == 'save_paused_sites':
        from crawler.engine import save_paused_sites
        return save_paused_sites
    if name == '_handle_signal':
        from crawler.engine import _handle_signal
        return _handle_signal
    if name == '_needs_playwright':
        from crawler.engine import _needs_playwright
        return _needs_playwright
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # config
    'MONITOR_SITES', 'URL_SHORT_TO_FULL',
    'ITEMS_JSON_PATH', 'HASH_RECORD_PATH', 'NOTIFIED_PATH', 'PAUSE_STATE_PATH',
    'RUN_LOG_PATH', 'BLACKLIST_PATH', 'SQLITE_DB_PATH',
    'MAX_RETRIES', 'RETRY_DELAY', 'CRAWL_TIMEOUT', 'PLAYWRIGHT_TIMEOUT_MS',
    'MAX_SITES_PER_ROUND', 'MAX_WORKERS', 'MAX_ITEMS_DB_SIZE',
    'IS_GITHUB_ACTIONS', 'GITHUB_ACTOR', 'GITHUB_RUN_ID', 'GITHUB_REPOSITORY',
    'BROWSER_PROFILES', 'DEAD_SITES',
    # network
    'MetricsTracker', 'CircuitBreaker', 'get_session',
    'get_conditional_headers', 'update_conditional_cache',
    'is_allowed_by_robots', 'DomainRateLimiter',
    # storage
    'get_current_round', 'get_random_profile', 'get_random_ua',
    'get_random_fingerprint', 'get_random_accept_language',
    'get_random_delay', 'get_referer',
    'load_hash_records', 'save_hash_records',
    'load_notified_items', 'save_notified_items',
    'filter_new_items', 'merge_items_into_db',
    # parsers
    'parse_ypojie', 'parse_discuz_threadlist', 'parse_discuz_items',
    'parse_yxssp_items', 'parse_423down', 'parse_423down_items',
    'parse_ziyuanting_items', 'parse_ziyuanting', 'parse_wycad_items',
    'parse_h6room_items', 'parse_xzba_items', 'parse_apprcn_items',
    'parse_daydayzhuan_items', 'parse_007ymd_items', 'parse_baicaio_items_v2',
    'parse_manmanbuy_items', 'parse_axutongxue_items', 'parse_rss_feed',
    'parse_ghxi', 'parse_ghxi_items', 'parse_ym2cc_items', 'parse_wobangzhao_items',
    'parse_foxirj_items', 'parse_ddooo_items', 'parse_onlinedown_items',
    'extract_article_items', 'parse_12345pro_items', 'parse_appinn_items',
    'parse_ithome_xijiayi_items', 'parse_lsapk_items', 'parse_thosefree_items',
    'parse_douban_group_items', 'parse_haodanku_items', 'parse_hybase_items',
    'parse_huodong5_items', 'parse_yangmaodang_items', 'parse_xianbaomi_items',
    'parse_yangmao_wang_items', 'parse_iqnew_items', 'parse_51kanong_items',
    'parse_ymxianbao_items', 'parse_linejia_items',
    'PARSER_REGISTRY', '_match_parser', 'fetch_page_content',
    # engine (lazy)
    'main', 'check_site_update', 'git_commit_if_changed',
    'load_run_log', 'append_run_log', 'analyze_and_fix',
    'load_paused_sites', 'save_paused_sites',
    '_handle_signal', '_needs_playwright',
]
