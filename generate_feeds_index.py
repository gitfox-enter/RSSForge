#!/usr/bin/env python3
"""
generate_feeds_index.py — v2
RSSForge 订阅源目录生成器
改进：
  - tier 分类标签（线报羊毛 / 优惠资讯 / 软件工具）
  - 更新频率 + 收录条目数显示
  - 深色模式支持
  - 桌面表格 + 移动端卡片双布局
  - 活跃源徽章
"""
import json, os, textwrap, re, glob, yaml
from datetime import datetime, timezone, timedelta

BASE = "https://gitfox-enter.github.io/RSSForge"
GHFAST_BASE = "https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs"
JSDELIVR_BASE = "https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs"

# ─────────────────────────────────────────────
# 1. 分类映射（tier → 标签）
# ─────────────────────────────────────────────
TIER_LABELS = {
    "high":   ("🔥", "线报羊毛"),
    "medium": ("📰", "优惠资讯"),
    "low":    ("📦", "软件工具"),
    "unknown": ("❓", "未分类"),
}
# 补充：site_url / name 中含关键词 → tier 覆盖
TIER_OVERRIDE_PATTERNS = [
    # 软件/工具类（域名）
    (r"ghxi\.com|423down\.com|appinn\.com|lsapk\.com|thosefree\.com|foxirj\.com|apprcn\.com|iplaysoft\.com"
     r"|appmiu|foxirj|sycx\.com|枫音|mefcl|免恶魔|APP喵|鸭先知|yxzhi",
     "low"),
    # 优惠/比价/省钱类
    (r"manmanbuy|baicaio|bacaoo|yxssp|优惠|白菜|拔草|省", "medium"),
    # 社区/豆瓣/论坛/科技资讯类
    (r"douban\.com|kxdao\.net|51kanong|iqnew|readhub|huodong|huifabu|yin-ruan|银软",
     "medium"),
    # IT科技/新闻类
    (r"ithome\.com|10000yun", "medium"),
    # 线报/羊毛/薅羊毛/赚（高频）
    (r"线报|羊毛|赚|zuankeba|zhuankeba|赚客吧|yangmao|我不找|汇发", "high"),
]

def guess_tier(site_url, name=""):
    """根据 site_url 和 name（中文名）推断 tier。"""
    text = (site_url or "") + " " + (name or "")
    for pattern, tier in TIER_OVERRIDE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return tier
    return "unknown"

# ─────────────────────────────────────────────
# 2. slug → 中文名（fallback）
# ─────────────────────────────────────────────
NAME_MAP = {
    "12345-xian-bao": "12345线报",
    "app-miao": "APP喵",
    "appmiu": "应用学堂",
    "fy6b": "枫音应用",
    "ithome": "IT之家",
    "mefcl": "免恶魔",
    "wanghou": "网猴线报",
    "yangmaoqun": "羊毛群",
    "yxzhi": "鸭先知",
    "yrxq": "银软星球",
    "zaike": "赚客吧",
    "xian-bao-ku": "线报酷",
    "xian-bao-icu": "线报ICU",
    "xianbaowu": "线报屋",
    "zhuan-ye-xian-bao": "专业线报",
}

def get_name(slug, meta_name=None):
    if meta_name:
        return meta_name
    return NAME_MAP.get(slug, slug)

# ─────────────────────────────────────────────
# 3a. 加载 blacklist
# ─────────────────────────────────────────────
def load_blacklist():
    path = os.path.join(os.path.dirname(__file__) or '.', 'blacklist.json')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data.get('blacklist', []), ensure_ascii=False)
    except Exception:
        return '[]'


# ─────────────────────────────────────────────
# 3. 加载 feeds_meta
# ─────────────────────────────────────────────
def load_meta():
    """从 docs/feeds/*.xml 读取【已发布】的 feed（权威源），
    解析名称/站点/图标/条目数，并按 tier 推断分类。
    这样计数随实际发布的 feed 文件自愈，不再依赖不完整的
    feeds_meta.json（它只跟踪已爬取成功的源，会漏掉部分活跃源）。"""
    # 频率映射（来自 sites.yaml 的 interval，单位分钟）
    freq_map = {}
    try:
        _sites = yaml.safe_load(open("sites.yaml", encoding="utf-8")).get("sites", [])
        for _s in _sites:
            _u = (_s.get("url") or "").rstrip("/").lower()
            _n = _s.get("name")
            _iv = _s.get("interval")
            if _iv:
                _lab = f"每{_iv // 60}小时" if _iv % 60 == 0 else f"每{_iv}分钟"
                if _u:
                    freq_map[_u] = _lab
                if _n:
                    freq_map["name:" + str(_n)] = _lab
    except Exception:
        pass
    # feeds_meta（已有 freq_label 优先）
    try:
        _fm = json.load(open("feeds_meta.json", encoding="utf-8"))
    except Exception:
        _fm = {}

    results = []
    for path in sorted(glob.glob(os.path.join("docs", "feeds", "*.xml"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        try:
            txt = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        ch = txt.split("</channel>")[0] if "</channel>" in txt else txt
        tm = re.search(r"<title>(.*?)</title>", ch, re.S)
        lm = re.search(r"<link>(.*?)</link>", ch, re.S)
        im = re.search(r"<image>.*?<url>(.*?)</url>", ch, re.S)
        name = (tm.group(1).replace(" - RSSForge", "").strip()
                if tm else slug)
        site_url = lm.group(1).strip() if lm else ""
        icon = im.group(1).strip() if im else ""
        if not icon and site_url:
            domain = site_url.replace("https://", "").replace("http://", "").split("/")[0]
            icon = f"https://{domain}/favicon.ico"
        count = txt.count("<item>") + txt.count("<entry>")
        tier = guess_tier(site_url, name)
        emoji, label = TIER_LABELS.get(tier, TIER_LABELS["unknown"])
        # 频率：feeds_meta > sites.yaml interval
        freq = ""
        for k, v in _fm.items():
            if v.get("name") == name or k == slug:
                freq = v.get("freq_label") or ""
                break
        if not freq:
            freq = (freq_map.get(site_url.rstrip("/").lower())
                    or freq_map.get("name:" + str(name)) or "—")
        results.append({
            "slug": slug, "name": name, "site_url": site_url,
            "icon": icon, "tier": tier, "tier_emoji": emoji,
            "tier_label": label, "count": count, "freq_label": freq,
        })
    return results

# ─────────────────────────────────────────────
# 4. CSS
# ─────────────────────────────────────────────
def css():
    return textwrap.dedent('''
    :root {
      --bg: #f4f5f7;
      --surface: #ffffff;
      --border: #e1e4e8;
      --text: #24292f;
      --text-muted: #57606a;
      --accent: #16a34a;
      --accent-dark: #14532d;
      --tag-bg-h: #fff1f0;  --tag-color-h: #cf222e;   /* high / 线报羊毛 */
      --tag-bg-m: #fff7ed;  --tag-color-m: #bc4c00;   /* medium / 优惠资讯 */
      --tag-bg-l: #f0fdf4;  --tag-color-l: #15803d;   /* low / 软件工具 */
      --tag-bg-u: #f6f8fa;  --tag-color-u: #57606a;   /* unknown */
      --hover-bg: #e8f0fe;
      --even-bg: #f6f8fa;
      --header-bg: linear-gradient(135deg,#16a34a,#14532d);
    }
    [data-theme="dark"] {
      --bg: #0d1117;
      --surface: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #3fb950;
      --accent-dark: #238636;
      --tag-bg-h: #3d1a1c;  --tag-color-h: #ff7b72;
      --tag-bg-m: #3d2a0a;  --tag-color-m: #ffa657;
      --tag-bg-l: #1a3d1e;  --tag-color-l: #56d364;
      --tag-bg-u: #21262d;  --tag-color-u: #8b949e;
      --hover-bg: #1f2d3d;
      --even-bg: #161b22;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: -apple-system,"Segoe UI",Roboto,"Noto Sans SC",sans-serif;
      background:var(--bg); color:var(--text); line-height:1.6;
    }
    a { color:var(--accent); text-decoration:none; }
    a:hover { text-decoration:underline; }

    /* ── Header ── */
    header {
      background:var(--header-bg);
      color:#fff; padding:36px 24px 28px; text-align:center;
    }
    header h1 { font-size:30px; font-weight:800; letter-spacing:-.5px; margin-bottom:4px; }
    header .subtitle { font-size:13px; opacity:.8; margin-bottom:20px; }
    .stats { display:flex; justify-content:center; gap:32px; margin-bottom:20px; flex-wrap:wrap; }
    .stat { text-align:center; }
    .stat-value { font-size:26px; font-weight:700; }
    .stat-label { font-size:12px; opacity:.75; }
    .opml-bar { display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-bottom:6px; }
    .opml-btn {
      display:inline-block; padding:7px 16px; border-radius:18px;
      background:rgba(255,255,255,.18); color:#fff; font-size:13px; font-weight:500;
      transition:background .2s;
    }
    .opml-btn:hover { background:rgba(255,255,255,.3); text-decoration:none; color:#fff; }

    /* ── Theme toggle ── */
    .theme-toggle {
      position:fixed; top:14px; right:16px; z-index:100;
      background:var(--surface); border:1px solid var(--border);
      border-radius:8px; padding:6px 10px; cursor:pointer; font-size:16px;
      box-shadow:0 1px 4px rgba(0,0,0,.15);
    }
    .theme-toggle:hover { opacity:.8; }

    /* ── Container ── */
    .container { max-width:1100px; margin:0 auto; padding:24px 16px; }

    /* ── Category tabs ── */
    .cat-tabs { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
    .cat-tab {
      padding:5px 14px; border-radius:16px; font-size:12px; font-weight:600;
      cursor:pointer; border:1.5px solid var(--border);
      background:var(--surface); color:var(--text-muted);
      transition:all .15s;
    }
    .cat-tab:hover, .cat-tab.active {
      border-color:var(--accent); color:var(--accent); background:var(--surface);
    }

    /* ── Filter bar ── */
    .filter-bar { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
    .filter-bar label { font-size:13px; color:var(--text-muted); }
    .filter-bar input {
      padding:7px 12px; border:1px solid var(--border); border-radius:8px;
      font-size:13px; width:220px; background:var(--surface); color:var(--text);
    }
    .filter-bar input:focus { outline:2px solid var(--accent); border-color:var(--accent); }
    .filter-bar .count-hint { font-size:12px; color:var(--text-muted); margin-left:auto; }

    /* ── Table ── */
    .table-wrap { background:var(--surface); border-radius:12px;
                  box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    thead { position:sticky; top:0; z-index:1; }
    thead th {
      background:var(--bg); color:var(--text-muted); font-weight:600;
      text-align:left; padding:10px 12px; border-bottom:2px solid var(--border);
      white-space:nowrap; cursor:pointer; user-select:none; font-size:12px;
    }
    thead th:hover { color:var(--text); }
    tbody tr { border-bottom:1px solid var(--border); transition:background .12s; }
    tbody tr:nth-child(even) { background:var(--even-bg); }
    tbody tr:hover { background:var(--hover-bg); }
    tbody tr[data-hidden="true"] { display:none; }
    tbody td { padding:10px 12px; vertical-align:middle; }
    td.num { color:var(--text-muted); font-size:12px; text-align:center; width:36px; }

    /* Site name cell */
    td.title { min-width:130px; }
    .title-wrap { display:flex; align-items:center; gap:6px; }
    .title-name { font-weight:600; color:var(--text); font-size:13px; }
    .title-name a { color:var(--text); }
    .title-name a:hover { color:var(--accent); text-decoration:none; }

    /* Category tag */
    .cat-tag {
      display:inline-flex; align-items:center; gap:3px;
      padding:2px 7px; border-radius:10px; font-size:11px; font-weight:600;
    }
    .cat-tag.high   { background:var(--tag-bg-h); color:var(--tag-color-h); }
    .cat-tag.medium { background:var(--tag-bg-m); color:var(--tag-color-m); }
    .cat-tag.low    { background:var(--tag-bg-l); color:var(--tag-color-l); }
    .cat-tag.unknown{ background:var(--tag-bg-u); color:var(--tag-color-u); }

    /* Favicon */
    td.favicon { width:28px; text-align:center; padding:4px 8px !important; }
    .favicon-img {
      width:18px; height:18px; border-radius:4px; object-fit:contain;
      background:#fff;
    }
    .favicon-placeholder {
      width:18px; height:18px; border-radius:4px;
      background:var(--bg); display:inline-block;
    }

    /* Site URL */
    td.site { max-width:150px; }
    td.site a {
      color:var(--text-muted); font-size:12px;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:block;
    }
    td.site a:hover { color:var(--accent); }

    /* Feed links */
    td.feed a {
      display:inline-block; padding:3px 8px; border-radius:5px;
      font-size:11px; font-weight:600; white-space:nowrap; margin-right:3px; margin-top:2px;
    }
    td.feed a.official { background:#dcfce7; color:#15803d; }
    td.feed a.ghfast   { background:#dbeafe; color:#1d4ed8; }
    td.feed a.jsdelivr { background:#fae8ff; color:#7e22ce; }
    [data-theme="dark"] td.feed a.official { background:#1a3d1e; color:#56d364; }
    [data-theme="dark"] td.feed a.ghfast   { background:#1a2d4a; color:#79c0ff; }
    [data-theme="dark"] td.feed a.jsdelivr { background:#3d1a4a; color:#d2a8ff; }
    td.feed a:hover { opacity:.75; text-decoration:none; }

    /* Meta: freq + count */
    td.meta { white-space:nowrap; font-size:12px; color:var(--text-muted); }
    td.meta .freq { display:block; }
    td.meta .count { display:block; }
    td.meta .count.has-items { color:var(--accent); font-weight:600; }
    td.meta .count.no-items  { color:var(--text-muted); }

    /* Hot badge */
    .hot-badge { color:#f97316; font-size:11px; }

    /* Footer */
    footer {
      text-align:center; padding:24px 16px; font-size:12px;
      color:var(--text-muted); border-top:1px solid var(--border);
    }
    footer a { color:var(--accent); }

    /* ── Mobile cards ── */
    @media (max-width:640px) {
      .table-wrap { overflow:visible; }
      table, thead, tbody, tr, td { display:block; }
      thead { display:none; }
      tbody tr { padding:12px 14px; border-radius:10px; margin-bottom:8px;
                 box-shadow:0 1px 3px rgba(0,0,0,.06); }
      tbody tr:nth-child(even) { background:var(--surface); }
      tbody td { padding:2px 0; border:none; }
      td.num { display:none; }
      td.favicon { display:inline-block; margin-right:8px; vertical-align:middle; }
      td.title { display:inline; }
      .title-wrap { display:inline-flex; align-items:center; gap:6px; }
      td.site, td.feed, td.meta { margin-top:6px; }
      td.feed a { padding:4px 8px; }
      .cat-tag { font-size:10px; }
      .filter-bar input { width:160px; }
      header h1 { font-size:24px; }
    }

    @media (max-width:768px) {
      table { min-width:unset; }
    }

    /* ── Blacklist Section ── */
    #blacklist-section {
      margin: 40px auto;
      max-width: 900px;
      padding: 0 16px;
    }
    #blacklist-section h2 {
      font-size: 16px;
      color: var(--text-muted);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      user-select: none;
    }
    #blacklist-section h2:hover { color: var(--text); }
    #blacklist-toggle {
      font-size: 12px;
      background: var(--border);
      border: none;
      border-radius: 10px;
      padding: 2px 10px;
      cursor: pointer;
      color: var(--text-muted);
      font-family: inherit;
    }
    #blacklist-toggle:hover { background: var(--hover); }
    #blacklist-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 10px;
    }
    #blacklist-list.collapsed { display: none; }
    .bl-item {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 13px;
    }
    .bl-domain {
      font-family: monospace;
      font-size: 12px;
      color: var(--accent);
      word-break: break-all;
      margin-bottom: 4px;
    }
    .bl-reason { color: var(--text-muted); font-size: 12px; line-height: 1.4; }
    .bl-tag {
      display: inline-block;
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 4px;
      margin-top: 5px;
      background: var(--border);
      color: var(--text-muted);
    }
    ''')

# ─────────────────────────────────────────────
# 5. 行生成
# ─────────────────────────────────────────────
def favicon_url(s):
    icon = s.get("icon", "")
    if icon and icon.startswith("http"):
        return icon
    site = s.get("site_url", "")
    if site:
        domain = site.replace("https://","").replace("http://","").split("/")[0]
        return f"https://{domain}/favicon.ico"
    return ""

def build_row(i, s):
    slug     = s["slug"]
    name     = s["name"]
    site_url = s.get("site_url", "")
    icon_url = favicon_url(s)
    tier     = s.get("tier", "unknown")
    emoji    = s.get("tier_emoji", "❓")
    tier_lbl = s.get("tier_label", "未分类")
    freq     = s.get("freq_label", "—")
    count    = s.get("count", 0)

    feed_url = s.get("feed_url", "")
    fname    = feed_url.split("/")[-1] if feed_url else f"{slug}.xml"
    official = f"{BASE}/feeds/{fname}"
    m1       = f"{GHFAST_BASE}/feeds/{fname}"
    m2       = f"{JSDELIVR_BASE}/feeds/{fname}"

    hot_tag  = ' <span class="hot-badge" title="已有收录内容">🔥</span>' if count > 0 else ""

    icon_html = (
        f'<img class="favicon-img" src="{icon_url}" alt="" loading="lazy" '
        f'onerror="this.style.opacity=.2;this.onerror=null">'
        if icon_url else '<span class="favicon-placeholder"></span>'
    )

    count_cls  = "has-items" if count > 0 else "no-items"
    count_disp = f'{count:,}' if count > 0 else "—"

    return (
        f'<tr data-cat="{tier}">'
        f'<td class="num">{i}</td>'
        f'<td class="favicon">{icon_html}</td>'
        f'<td class="title">'
        f'<div class="title-wrap">'
        f'<span class="title-name"><a href="{site_url}" target="_blank">{name}</a></span>{hot_tag}'
        f'</div>'
        f'</td>'
        f'<td class="site"><a href="{site_url}" target="_blank">{site_url}</a></td>'
        f'<td class="feed">'
        f'<a class="official" href="{official}" target="_blank">官方</a>'
        f'<a class="ghfast"   href="{m1}"       target="_blank">ghfast</a>'
        f'<a class="jsdelivr" href="{m2}"       target="_blank">CDN</a>'
        f'</td>'
        f'<td class="meta">'
        f'<span class="freq">{freq}</span>'
        f'<span class="count {count_cls}">收录 {count_disp} 条</span>'
        f'</td>'
        f'<td><span class="cat-tag {tier}" title="{tier_lbl}">{emoji} {tier_lbl}</span></td>'
        f'</tr>'
    )

# ─────────────────────────────────────────────
# 6. HTML 生成
# ─────────────────────────────────────────────
def gen_html(meta, blacklist_json='[]'):
    from datetime import datetime, timezone, timedelta
    tz  = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    n   = len(meta)
    has_items   = sum(1 for s in meta if s.get("count", 0) > 0)
    high_cnt    = sum(1 for s in meta if s.get("tier") == "high")
    medium_cnt  = sum(1 for s in meta if s.get("tier") == "medium")
    low_cnt     = sum(1 for s in meta if s.get("tier") == "low")

    rows_html = "\n".join(build_row(i, s) for i, s in enumerate(meta, 1))
    bl_json = blacklist_json if blacklist_json else '[]'

    tmpl = f'''\
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>RSSForge - 订阅源目录</title>
      <meta name="description" content="RSSForge 订阅源目录，共收录 {n} 个订阅源，支持官方/ghfast/jsDelivr 多镜像。">
      <link rel="alternate" type="application/rss+xml" title="RSSForge OPML" href="{BASE}/opml.xml">
      <link rel="alternate" type="application/rss+xml" title="RSSForge (ghfast)" href="{GHFAST_BASE}/opml.ghfast.xml">
      <link rel="alternate" type="application/rss+xml" title="RSSForge (jsDelivr)" href="{JSDELIVR_BASE}/opml.jsdelivr.xml">
      <style>{css()}</style>
    </head>
    <body>

    <button class="theme-toggle" onclick="toggleTheme()" title="切换深色模式" id="themeBtn">🌙</button>

    <header>
      <h1>📡 RSSForge</h1>
      <p class="subtitle">订阅源目录 &middot; {now}</p>
      <div class="stats">
        <div class="stat"><div class="stat-value">{n}</div><div class="stat-label">订阅源</div></div>
        <div class="stat"><div class="stat-value">{has_items}</div><div class="stat-label">活跃源</div></div>
        <div class="stat"><div class="stat-value">{high_cnt}</div><div class="stat-label">线报羊毛</div></div>
        <div class="stat"><div class="stat-value">{medium_cnt}</div><div class="stat-label">优惠资讯</div></div>
        <div class="stat"><div class="stat-value">{low_cnt}</div><div class="stat-label">软件工具</div></div>
      </div>
      <div class="opml-bar">
        <a class="opml-btn" href="{BASE}/opml.xml">📥 官方 OPML</a>
        <a class="opml-btn" href="{GHFAST_BASE}/opml.ghfast.xml">🚀 ghfast 镜像</a>
        <a class="opml-btn" href="{JSDELIVR_BASE}/opml.jsdelivr.xml">📦 jsDelivr CDN</a>
      </div>
    </header>

    <div class="container">
      <!-- Category tabs -->
      <div class="cat-tabs" id="catTabs">
        <span class="cat-tab active" data-cat="all" onclick="filterCat('all')">全部</span>
        <span class="cat-tab" data-cat="high"   onclick="filterCat('high')">🔥 线报羊毛 ({high_cnt})</span>
        <span class="cat-tab" data-cat="medium" onclick="filterCat('medium')">📰 优惠资讯 ({medium_cnt})</span>
        <span class="cat-tab" data-cat="low"    onclick="filterCat('low')">📦 软件工具 ({low_cnt})</span>
      </div>

      <!-- Search -->
      <div class="filter-bar">
        <label>🔍</label>
        <input type="text" id="searchInput" placeholder="搜索站点名称或网址…" oninput="applyFilters()">
        <span class="count-hint" id="countHint">共 {n} 个订阅源</span>
      </div>

      <!-- Table -->
      <div class="table-wrap">
        <table id="feedTable">
          <thead>
            <tr>
              <th>#</th>
              <th></th>
              <th onclick="sortTable(2)">站点名称 ▾</th>
              <th onclick="sortTable(3)">网址 ▾</th>
              <th>订阅链接</th>
              <th>更新频率 / 条目</th>
              <th onclick="sortTable(6)">分类 ▾</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>

    <footer>
      <p>RSSForge &middot; 共收录 <strong>{n}</strong> 个订阅源 &middot;
         <a href="https://github.com/gitfox-enter/RSSForge" target="_blank">⭐ 在 GitHub 上查看</a> &middot;
         <a href="https://github.com/gitfox-enter/RSSForge/issues/new/choose" target="_blank">提交新的订阅源</a>
      </p>
    </footer>

    <div id="blacklist-section">
      <h2 onclick="toggleBlacklist()">🚫 已屏蔽站点 <button id="blacklist-toggle">展开</button></h2>
      <div id="blacklist-list" class="collapsed"></div>
    </div>

    <script>
    // ── Theme ──
    function toggleTheme() {{
      const d = document.documentElement;
      const isDark = d.getAttribute('data-theme') === 'dark';
      d.setAttribute('data-theme', isDark ? '' : 'dark');
      document.getElementById('themeBtn').textContent = isDark ? '🌙' : '☀️';
      localStorage.setItem('rssforge-theme', isDark ? 'light' : 'dark');
    }}
    (function() {{
      const saved = localStorage.getItem('rssforge-theme');
      if (saved === 'dark') {{
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('themeBtn').textContent = '☀️';
      }}
    }})();

    // ── Category filter ──
    var currentCat = 'all';

    function filterCat(cat) {{
      currentCat = cat;
      document.querySelectorAll('.cat-tab').forEach(function(el) {{
        el.classList.toggle('active', el.getAttribute('data-cat') === cat);
      }});
      applyFilters();
    }}

    // ── Search ──
    function applyFilters() {{
      var q = document.getElementById('searchInput').value.trim().toLowerCase();
      var rows = document.querySelectorAll('#feedTable tbody tr');
      var visible = 0;
      rows.forEach(function(tr) {{
        var cat   = tr.getAttribute('data-cat');
        var title = tr.cells[2].textContent.toLowerCase();
        var site  = tr.cells[3].textContent.toLowerCase();
        var show  = (currentCat === 'all' || cat === currentCat)
                  && (!q || title.includes(q) || site.includes(q));
        tr.setAttribute('data-hidden', show ? 'false' : 'true');
        if (show) visible++;
      }});
      document.getElementById('countHint').textContent = '当前 ' + visible + ' 个';
    }}

    // ── Sort ──
    function sortTable(col) {{
      var tb  = document.querySelector('#feedTable tbody');
      var dir = tb.getAttribute('data-dir') === 'asc' ? 'desc' : 'asc';
      tb.setAttribute('data-dir', dir);
      var rows = Array.from(tb.rows);
      rows.sort(function(a, b) {{
        var va = a.cells[col].textContent.trim();
        var vb = b.cells[col].textContent.trim();
        if (!isNaN(va) && !isNaN(vb)) {{ va = +va; vb = +vb; }}
        return dir === 'asc' ? (va > vb ? 1 : -1) : (va > vb ? -1 : 1);
      }});
      rows.forEach(function(r) {{ tb.appendChild(r); }});
    }}

    // ── Favicon lazy ──
    document.querySelectorAll('.favicon-img').forEach(function(img) {{
      if (!img.src || img.src.endsWith('/favicon.ico')) return;
    }});

    // ── Blacklist ──
    var BLACKLIST = {bl_json};
    var blExpanded = false;
    function toggleBlacklist() {{
      blExpanded = !blExpanded;
      var list = document.getElementById('blacklist-list');
      var btn  = document.getElementById('blacklist-toggle');
      list.classList.toggle('collapsed', !blExpanded);
      btn.textContent = blExpanded ? '收起' : '展开';
    }}
    function renderBlacklist() {{
      var list = document.getElementById('blacklist-list');
      if (!list) return;
      var frag = document.createDocumentFragment();
      BLACKLIST.forEach(function(item) {{
        var div = document.createElement('div');
        div.className = 'bl-item';
        div.innerHTML = '<div class="bl-domain">' + item.domain + '</div>' +
          '<div class="bl-reason">' + item.reason + '</div>' +
          '<span class="bl-tag">' + item.category + '</span>';
        frag.appendChild(div);
      }});
      list.appendChild(frag);
    }}
    renderBlacklist();
    </script>
    </body>
    </html>
    '''
    return textwrap.dedent(tmpl)

# ─────────────────────────────────────────────
# 7. 入口
# ─────────────────────────────────────────────
def main():
    meta = load_meta()
    blacklist_json = load_blacklist()
    html = gen_html(meta, blacklist_json)
    os.makedirs("docs", exist_ok=True)
    out = "docs/index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ {out}  ({len(meta)} feeds, {len(html):,} bytes)")
    # Also write the generated version marker
    with open("docs/version.txt", "w") as f:
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        f.write(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S CST\n"))
        f.write(f"feeds: {len(meta)}\n")

if __name__ == "__main__":
    main()
