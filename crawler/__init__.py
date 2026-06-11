# -*- coding: utf-8 -*-
"""Crawler package — modular refactor of crawl.py.

Re-exports the most commonly used symbols from submodules for backward
compatibility with any code that imports from the old monolithic crawl.py.
"""

# --- Config symbols ---
from crawler.config import (
    MONITOR_SITES,
    URL_SHORT_TO_FULL,
    SOURCE_NAME_MAP,
    ITEMS_JSON_PATH,
    HASH_RECORD_PATH,
    NOTIFIED_PATH,
    PAUSE_STATE_PATH,
    CRAWL_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    PLAYWRIGHT_TIMEOUT_MS,
    MAX_SITES_PER_ROUND,
    MAX_WORKERS,
    MAX_ITEMS_DB_SIZE,
    BROWSER_PROFILES,
    DEAD_SITES,
    is_dead_site,
    get_source_name,
)

# --- Network symbols ---
from crawler.network import (
    CircuitBreaker,
    MetricsTracker,
    metrics,
)

# --- Storage symbols ---
from crawler.storage import (
    load_hash_records,
    save_hash_records,
    load_notified_items,
    save_notified_items,
    load_items_db,
    save_items_db,
    filter_new_items,
    merge_items_into_db,
)

# --- Parser symbols ---
from crawler.parsers import (
    PARSER_REGISTRY,
    parse_423down_items,
    parse_discuz_items,
    parse_rss_feed,
    extract_article_items,
    parse_baicaio_items_v2,
)

# --- Common symbols (re-exported for convenience) ---
from common import (
    ITEMS_DB_FILE,
    ITEMS_LATEST_FILE,
    CRAWL_STATUS_FILE,
    HASH_RECORD_FILE,
    NOTIFIED_ITEMS_FILE,
    PAUSED_SITES_FILE,
    RUN_LOG_FILE,
    MAX_ITEMS_DB,
    SQLITE_DB_FILE,
    BLACKLIST_FILE,
    build_source_name_index,
    get_beijing_time,
    calculate_md5,
    auto_categorize,
    is_blacklisted,
    is_junk,
    sqlite_export_json,
    sqlite_export_latest_json,
    sqlite_init_db,
    sqlite_insert_items,
    sqlite_get_recent_items,
)

# --- Engine symbols (lazy to avoid circular deps) ---
def __getattr__(name):
    """Lazy import engine symbols to avoid circular imports."""
    _engine_names = {
        'main', 'check_site_update', 'git_commit_if_changed',
        'load_run_log', 'append_run_log', 'analyze_and_fix',
        'load_paused_sites', 'save_paused_sites',
        '_handle_signal', '_needs_playwright',
    }
    if name in _engine_names:
        from crawler.engine import main, check_site_update, git_commit_if_changed
        from crawler.engine import load_run_log, append_run_log, analyze_and_fix
        from crawler.engine import load_paused_sites, save_paused_sites
        from crawler.engine import _handle_signal, _needs_playwright
        globals()[name] = locals()[name]
        return locals()[name]
    raise AttributeError(f"module 'crawler' has no attribute {name!r}")


__all__ = [
    # Config
    'MONITOR_SITES', 'URL_SHORT_TO_FULL', 'SOURCE_NAME_MAP',
    'ITEMS_JSON_PATH', 'HASH_RECORD_PATH', 'NOTIFIED_PATH', 'PAUSE_STATE_PATH',
    'CRAWL_TIMEOUT', 'MAX_RETRIES', 'RETRY_DELAY',
    'PLAYWRIGHT_TIMEOUT_MS', 'MAX_SITES_PER_ROUND', 'MAX_WORKERS',
    'MAX_ITEMS_DB_SIZE', 'BROWSER_PROFILES', 'DEAD_SITES',
    'is_dead_site', 'get_source_name',
    # Network
    'CircuitBreaker', 'MetricsTracker', 'metrics',
    # Storage
    'load_hash_records', 'save_hash_records',
    'load_notified_items', 'save_notified_items',
    'load_items_db', 'save_items_db',
    'filter_new_items', 'merge_items_into_db',
    # Parsers
    'PARSER_REGISTRY', 'parse_423down_items', 'parse_discuz_items',
    'parse_rss_feed', 'extract_article_items', 'parse_baicaio_items_v2',
    # Common re-exports
    'ITEMS_DB_FILE', 'ITEMS_LATEST_FILE', 'CRAWL_STATUS_FILE',
    'HASH_RECORD_FILE', 'NOTIFIED_ITEMS_FILE', 'PAUSED_SITES_FILE',
    'RUN_LOG_FILE', 'MAX_ITEMS_DB', 'SQLITE_DB_FILE', 'BLACKLIST_FILE',
    'build_source_name_index', 'get_beijing_time', 'calculate_md5',
    'auto_categorize', 'is_blacklisted', 'is_junk',
    'sqlite_export_json', 'sqlite_export_latest_json',
    'sqlite_init_db', 'sqlite_insert_items', 'sqlite_get_recent_items',
    # Engine (lazy)
    'main', 'check_site_update', 'git_commit_if_changed',
    'load_run_log', 'append_run_log', 'analyze_and_fix',
    'load_paused_sites', 'save_paused_sites',
    '_handle_signal', '_needs_playwright',
]
