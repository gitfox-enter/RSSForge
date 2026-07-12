# -*- coding: utf-8 -*-
"""Crawler package — modular refactor of crawl.py.

Re-exports commonly used symbols for backward compatibility.
"""

# --- Config ---
from crawler.config import (
    MONITOR_SITES,
    SOURCE_NAME_MAP,
    FAST_SITES,
    HASH_RECORD_FILE,
    NOTIFIED_ITEMS_FILE,
    RUN_LOG_FILE,
    ADAPTIVE_TIERS_FILE,
    MAX_ITEMS_DB,
    TIER_PROMOTE_SUCCESS_STREAK,
    TIER_DEMOTE_FAIL_STREAK,
    TIER_PROMOTE_ON_UPDATE,
    DEAD_THRESHOLD_FAIL_STREAK,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    REQUEST_TIMEOUT,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    JS_RENDER_SITES,
    RSS_FIRST_SITES,
    RESPECT_ROBOTS_TXT,
    BROWSER_PROFILES,
    DEAD_SITES,
    is_dead_site,
    get_source_name,
    get_site_tier,
    init_adaptive_tiers,
    update_adaptive_tier,
    save_adaptive_tiers,
    get_all_adaptive_tiers,
)

# --- Network ---
from crawler.network import (
    MetricsTracker,
    metrics,
)

# --- Storage ---
from crawler.storage import (
    load_hash_records,
    save_hash_records,
    load_notified_items,
    save_notified_items,
    filter_new_items,
    merge_items_into_db,
    get_current_round,
)

# --- Parsers ---
from crawler.parsers import (
    parse_423down_items,
    parse_discuz_items,
    parse_rss_feed,
    extract_article_items,
    parse_baicaio_items_v2,
    # --- deal_sites ---
    parse_wycad_items,
    parse_h6room_items,
    parse_xzba_items,
    parse_apprcn_items,
    parse_daydayzhuan_items,
    parse_007ymd_items,
    parse_12345pro_items,
    parse_wobangzhao_items,
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
    parse_10000yun_items,
    parse_manmanbuy_items,
    parse_ym2cc_items,
    # --- software_sites ---
    parse_yxssp_items,
    parse_foxirj_items,
    parse_appinn_items,
    parse_lsapk_items,
    parse_thosefree_items,
    parse_ithome_xijiayi_items,
    # --- forum_sites ---
    parse_douban_group_items,
    # --- rss_parsers ---
    fetch_rss_feed_async,
    fetch_ghxi_items_async,
)

# --- Common re-exports ---
from common import (
    ITEMS_DB_FILE,
    ITEMS_LATEST_FILE,
    CRAWL_STATUS_FILE,
    BLACKLIST_FILE,
    build_source_name_index,
    get_beijing_time,
    calculate_md5,
    auto_categorize,
    is_blacklisted,
    is_junk,
    ProxyPool,
    create_proxy_pool,
    DomainRateLimiter,
    sanitize_text,
    sanitize_href,
    upgrade_to_https,
)

# --- Blacklist guardrail: fail fast if sites.yaml contains blacklisted domains ---
def _validate_sites_against_blacklist() -> None:
    """Validate that no site in sites.yaml is in blacklist.json.

    This runs at import time to prevent blacklisted sites from being
    added to the monitoring pipeline by mistake.
    """
    import json, os, re, sys
    from pathlib import Path

    base_dir = Path(__file__).parent.parent
    blacklist_path = base_dir / "blacklist.json"
    sites_yaml_path = base_dir / "sites.yaml"

    if not blacklist_path.exists() or not sites_yaml_path.exists():
        return  # Skip in bare/minimal environments

    try:
        with open(blacklist_path, "r", encoding="utf-8") as f:
            blacklist = json.load(f)
        blocked = {item["domain"].lower() for item in blacklist["blacklist"]}
    except Exception:
        return  # Don't block on malformed json

    try:
        import yaml
        with open(sites_yaml_path, "r", encoding="utf-8") as f:
            sites = yaml.safe_load(f)
    except Exception:
        return  # Don't block on malformed yaml

    url_pattern = re.compile(r"https?://([^/]+)/?")
    violations = []

    def extract_domains(entry):
        if isinstance(entry, str):
            m = url_pattern.match(entry)
            yield m.group(1).lower() if m else None
        elif isinstance(entry, dict):
            for key in ("url", "site_url", "feed_url"):
                if key in entry:
                    m = url_pattern.match(entry[key])
                    if m:
                        yield m.group(1).lower()

    for group in sites.get("monitoring_groups", []):
        for entry in group.get("sites", []):
            for domain in extract_domains(entry):
                if domain and domain in blocked:
                    name = entry.get("name", domain) if isinstance(entry, dict) else domain
                    reason = next(
                        b["reason"] for b in blacklist["blacklist"]
                        if b["domain"].lower() == domain
                    )
                    violations.append(f"  {domain} (as '{name}'): {reason}")

    if violations:
        print("\n" + "=" * 60, file=sys.stderr)
        print("ERROR: The following sites in sites.yaml are BLACKLISTED:", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("Remove these sites from sites.yaml before running.", file=sys.stderr)
        print("If you believe this is a mistake, update blacklist.json.", file=sys.stderr)
        sys.exit(1)


_validate_sites_against_blacklist()
del _validate_sites_against_blacklist


# --- Engine (lazy) ---
def __getattr__(name):
    _engine_names = {
        'main', 'check_site_update', 'git_commit_if_changed',
        'load_run_log', 'append_run_log', 'analyze_and_fix',
        'export_crawl_status',
        '_handle_signal', '_needs_playwright',
    }
    if name in _engine_names:
        from crawler import engine as _engine
        val = getattr(_engine, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module 'crawler' has no attribute {name!r}")
