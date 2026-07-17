#!/usr/bin/env python3
"""
generate_feeds_index.py — v3
RSSForge 订阅源目录生成器（成果展示版）
改进：
  - 全新 Hero：徽章 + 大标题 + 价值主张 + 多镜像 OPML 入口
  - 悬浮统计条（5 项，玻璃拟态卡片，跨越 Hero 边界）
  - 订阅源改为卡片网格（非密集表格），更适合成果展示
  - 分类标签 + 名称/网址搜索过滤
  - 深色模式 / 响应式 / 桌面+移动双布局
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
    (r"ghxi\.com|423down\.com|appinn\.com|lsapk\.com|thosefree\.com|foxirj\.com|apprcn\.com|iplaysoft\.com"
     r"|appmiu|foxirj|sycx\.com|枫音|mefcl|免恶魔|APP喵|鸭先知|yxzhi",
     "low"),
    (r"manmanbuy|baicaio|bacaoo|yxssp|优惠|白菜|拔草|省", "medium"),
    (r"douban\.com|kxdao\.net|51kanong|iqnew|readhub|huodong|huifabu|yin-ruan|银软",
     "medium"),
    (r"ithome\.com|10000yun", "medium"),
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
# 3. 加载 feeds_meta（权威：已发布的 feed 文件）
# ─────────────────────────────────────────────
def load_meta():
    """从 docs/feeds/*.xml 读取【已发布】的 feed（权威源），
    解析名称/站点/图标/条目数，并按 tier 推断分类。"""
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
      --bg: #f6f8fa;
      --surface: #ffffff;
      --border: #e6e9ee;
      --text: #1f2328;
      --text-muted: #656d76;
      --accent: #1a7f37;
      --accent-2: #2da44e;
      --accent-soft: #dafbe1;
      --tag-bg-h:#ffeef0; --tag-color-h:#cf222e;
      --tag-bg-m:#fff3e6; --tag-color-m:#bc4c00;
      --tag-bg-l:#eaf6ec; --tag-color-l:#1a7f37;
      --tag-bg-u:#f0f2f5; --tag-color-u:#656d76;
      --hover-bg:#f0f7ff;
      --shadow: 0 1px 3px rgba(27,31,36,.08), 0 1px 2px rgba(27,31,36,.06);
      --shadow-lg: 0 10px 30px rgba(27,31,36,.14);
      --radius: 14px;
      --hero-grad: linear-gradient(135deg,#1a7f37 0%, #11632b 55%, #0c4a20 100%);
    }
    [data-theme="dark"] {
      --bg: #010409;
      --surface: #161b22;
      --border: #30363d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --accent: #3fb950;
      --accent-2: #2ea043;
      --accent-soft: #122d1c;
      --tag-bg-h:#3d1a1c; --tag-color-h:#ff7b72;
      --tag-bg-m:#3d2a0a; --tag-color-m:#ffa657;
      --tag-bg-l:#1a3d1e; --tag-color-l:#56d364;
      --tag-bg-u:#21262d; --tag-color-u:#8b949e;
      --hover-bg:#1f2d3d;
      --shadow: 0 1px 3px rgba(0,0,0,.4);
      --shadow-lg: 0 10px 30px rgba(0,0,0,.6);
      --hero-grad: linear-gradient(135deg,#0d4423 0%, #0a331a 55%, #062012 100%);
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans SC","PingFang SC",sans-serif;
      background:var(--bg); color:var(--text); line-height:1.6;
      -webkit-font-smoothing:antialiased;
    }
    a { color:var(--accent); text-decoration:none; }
    a:hover { text-decoration:underline; }

    /* ── Theme toggle ── */
    .theme-toggle {
      position:fixed; top:14px; right:16px; z-index:200;
      background:rgba(255,255,255,.85); border:1px solid var(--border);
      border-radius:10px; padding:6px 10px; cursor:pointer; font-size:16px;
      box-shadow:0 1px 4px rgba(0,0,0,.15); backdrop-filter:blur(6px);
    }
    .theme-toggle:hover { opacity:.85; }

    /* ── Hero ── */
    .hero {
      position:relative; background:var(--hero-grad); color:#fff;
      padding:60px 24px 96px; text-align:center; overflow:hidden;
    }
    .hero::before {
      content:""; position:absolute; inset:0;
      background-image: radial-gradient(rgba(255,255,255,.10) 1.5px, transparent 1.5px);
      background-size:24px 24px; opacity:.5;
    }
    .hero::after {
      content:""; position:absolute; left:0; right:0; bottom:0; height:80px;
      background:linear-gradient(to bottom, transparent, var(--bg));
    }
    .hero-inner { position:relative; max-width:780px; margin:0 auto; z-index:2; }
    .badge {
      display:inline-block; padding:5px 15px; border-radius:999px;
      background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.28);
      font-size:12px; font-weight:600; margin-bottom:18px; backdrop-filter:blur(4px);
      letter-spacing:.3px;
    }
    .hero h1 {
      font-size:46px; font-weight:800; letter-spacing:-1.2px;
      margin-bottom:10px; line-height:1.1;
    }
    .hero .tagline { font-size:16px; opacity:.92; margin-bottom:26px; font-weight:500; }
    .opml-bar { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }
    .opml-btn {
      display:inline-flex; align-items:center; gap:6px;
      padding:9px 18px; border-radius:10px;
      background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.30);
      color:#fff; font-size:13px; font-weight:600; transition:all .2s; backdrop-filter:blur(4px);
    }
    .opml-btn:hover { background:rgba(255,255,255,.32); color:#fff; text-decoration:none; transform:translateY(-1px); }

    /* ── Stats strip (overlaps hero) ── */
    .stats-strip {
      position:relative; z-index:5;
      max-width:1040px; margin:-58px auto 0; padding:0 16px;
      display:grid; grid-template-columns:repeat(5,1fr); gap:14px;
    }
    .stat-card {
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:18px 10px; text-align:center;
      box-shadow:var(--shadow-lg);
    }
    .stat-value { font-size:25px; font-weight:800; color:var(--text); line-height:1.1; }
    .stat-value.last { font-size:18px; letter-spacing:-.3px; }
    .stat-label { font-size:12px; color:var(--text-muted); margin-top:4px; }

    /* ── Container ── */
    .container { max-width:1100px; margin:0 auto; padding:36px 16px 24px; }

    /* ── Section heading ── */
    .section-head { display:flex; align-items:baseline; gap:10px; margin:8px 0 16px; }
    .section-head h2 { font-size:19px; font-weight:800; letter-spacing:-.3px; }
    .section-head .sub { font-size:13px; color:var(--text-muted); }

    /* ── About card ── */
    .about {
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:20px 22px; margin-bottom:26px;
      box-shadow:var(--shadow);
    }
    .about p { font-size:13.5px; color:var(--text-muted); line-height:1.75; }
    .about .features { list-style:none; margin:14px 0 0; display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
    .about .features li {
      position:relative; font-size:13px; color:var(--text); background:var(--bg);
      border:1px solid var(--border); border-radius:10px; padding:10px 12px 10px 44px;
    }
    .about .features li::before {
      content:attr(data-num); position:absolute; left:10px; top:10px;
      width:24px; height:24px; border-radius:50%;
      background:var(--accent-soft); color:var(--accent);
      display:flex; align-items:center; justify-content:center;
      font-size:11px; font-weight:800;
    }
    .about .features b { color:var(--accent); }

    /* ── Toolbar: category tabs + search ── */
    .toolbar { display:flex; gap:12px; margin-bottom:18px; flex-wrap:wrap; align-items:center; }
    .cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
    .cat-tab {
      padding:6px 15px; border-radius:999px; font-size:12.5px; font-weight:600;
      cursor:pointer; border:1.5px solid var(--border);
      background:var(--surface); color:var(--text-muted); transition:all .15s;
    }
    .cat-tab:hover, .cat-tab.active {
      border-color:var(--accent); color:var(--accent); background:var(--accent-soft);
    }
    .search-box { margin-left:auto; position:relative; }
    .search-box input {
      padding:8px 14px 8px 34px; border:1px solid var(--border); border-radius:10px;
      font-size:13px; width:240px; background:var(--surface); color:var(--text);
    }
    .search-box input:focus { outline:2px solid var(--accent); border-color:var(--accent); }
    .search-box::before {
      content:"🔍"; position:absolute; left:11px; top:50%; transform:translateY(-50%);
      font-size:13px; opacity:.6;
    }
    .count-hint { font-size:12.5px; color:var(--text-muted); width:100%; margin-top:2px; }

    /* ── Feed grid ── */
    .feed-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }
    .feed-card {
      background:var(--surface); border:1px solid var(--border);
      border-radius:var(--radius); padding:16px; box-shadow:var(--shadow);
      display:flex; flex-direction:column; gap:11px;
      transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .feed-card:hover { transform:translateY(-3px); box-shadow:var(--shadow-lg); border-color:var(--accent); }
    .card-head { display:flex; align-items:center; gap:11px; }
    .favicon-img { width:34px; height:34px; border-radius:9px; object-fit:contain; background:#fff; flex:none; }
    .favicon-placeholder {
      width:34px; height:34px; border-radius:9px; background:var(--bg);
      display:inline-flex; align-items:center; justify-content:center;
      font-size:14px; flex:none;
    }
    .card-title { flex:1; min-width:0; }
    .card-name { font-weight:700; font-size:14.5px; color:var(--text); line-height:1.3; }
    .card-name a { color:var(--text); }
    .card-name a:hover { color:var(--accent); text-decoration:none; }
    .card-site { font-size:11px; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .card-site a { color:var(--text-muted); font-size:11px; }
    .card-site a:hover { color:var(--accent); }

    .cat-tag {
      display:inline-flex; align-items:center; gap:3px; flex:none;
      padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700;
    }
    .cat-tag.high   { background:var(--tag-bg-h); color:var(--tag-color-h); }
    .cat-tag.medium { background:var(--tag-bg-m); color:var(--tag-color-m); }
    .cat-tag.low    { background:var(--tag-bg-l); color:var(--tag-color-l); }
    .cat-tag.unknown{ background:var(--tag-bg-u); color:var(--tag-color-u); }

    .card-meta { font-size:12px; color:var(--text-muted); display:flex; gap:12px; align-items:center; }
    .card-meta .count.has-items { color:var(--accent); font-weight:600; }
    .card-meta .dot { width:3px; height:3px; border-radius:50%; background:var(--text-muted); opacity:.5; }

    .card-feeds { display:flex; gap:7px; flex-wrap:wrap; margin-top:auto; }
    .card-feeds a {
      display:inline-flex; align-items:center; gap:4px;
      padding:5px 11px; border-radius:8px; font-size:11.5px; font-weight:700;
      transition:transform .12s, opacity .12s;
    }
    .card-feeds a.official { background:var(--accent-soft); color:var(--accent); }
    .card-feeds a.ghfast   { background:#e7f0ff; color:#1d4ed8; }
    .card-feeds a.jsdelivr { background:#f6e9ff; color:#7e22ce; }
    [data-theme="dark"] .card-feeds a.ghfast   { background:#16294a; color:#79c0ff; }
    [data-theme="dark"] .card-feeds a.jsdelivr { background:#2c1640; color:#d2a8ff; }
    .card-feeds a:hover { text-decoration:none; transform:translateY(-1px); opacity:.88; }

    .empty-hint { display:none; text-align:center; color:var(--text-muted); padding:40px 0; font-size:14px; }

    /* ── Footer ── */
    footer {
      text-align:center; padding:32px 16px; font-size:12.5px;
      color:var(--text-muted); border-top:1px solid var(--border); margin-top:24px;
    }
    footer .footer-pitch { font-weight:700; color:var(--text); margin-bottom:8px; font-size:13.5px; }
    footer .footer-links a { margin:0 6px; }
    footer .footer-note { font-size:11.5px; opacity:.75; margin-top:8px; }

    /* ── Mobile ── */
    @media (max-width:768px) {
      .stats-strip { grid-template-columns:repeat(3,1fr); gap:10px; }
      .hero { padding:48px 18px 84px; }
      .hero h1 { font-size:34px; }
      .about .features { grid-template-columns:1fr; }
      .search-box { width:100%; }
      .search-box input { width:100%; }
      .toolbar { gap:10px; }
      .feed-grid { grid-template-columns:1fr; }
    }
    @media (max-width:430px) {
      .stats-strip { grid-template-columns:repeat(2,1fr); }
    }
    ''')

# ─────────────────────────────────────────────
# 5. 卡片生成
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

def build_card(s):
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

    # 域名（卡片副标题）
    domain = site_url.replace("https://","").replace("http://","").split("/")[0] if site_url else ""

    # favicon
    icon_html = (
        f'<img class="favicon-img" src="{icon_url}" alt="" loading="lazy" '
        f'onerror="this.style.opacity=.15;this.onerror=null">'
        if icon_url else '<span class="favicon-placeholder">📡</span>'
    )

    count_cls  = "has-items" if count > 0 else ""
    count_disp = f'{count:,}' if count > 0 else "暂无"

    site_line = (
        f'<div class="card-site"><a href="{site_url}" target="_blank" rel="noopener">{domain}</a></div>'
        if domain else '<div class="card-site">—</div>'
    )

    return (
        f'<article class="feed-card" data-cat="{tier}" '
        f'data-name="{name.lower()}" data-site="{domain.lower()}">'
        f'<div class="card-head">'
        f'{icon_html}'
        f'<div class="card-title">'
        f'<div class="card-name"><a href="{site_url}" target="_blank" rel="noopener">{name}</a></div>'
        f'{site_line}'
        f'</div>'
        f'<span class="cat-tag {tier}" title="{tier_lbl}">{emoji} {tier_lbl}</span>'
        f'</div>'
        f'<div class="card-meta">'
        f'<span class="count {count_cls}">收录 {count_disp}</span>'
        f'<span class="dot"></span>'
        f'<span class="freq">{freq}</span>'
        f'</div>'
        f'<div class="card-feeds">'
        f'<a class="official" href="{official}" target="_blank" rel="noopener">官方</a>'
        f'<a class="ghfast"   href="{m1}"       target="_blank" rel="noopener">ghfast</a>'
        f'<a class="jsdelivr" href="{m2}"       target="_blank" rel="noopener">CDN</a>'
        f'</div>'
        f'</article>'
    )

# ─────────────────────────────────────────────
# 6. HTML 生成
# ─────────────────────────────────────────────
def gen_html(meta, last_crawl=""):
    from datetime import datetime, timezone, timedelta
    tz  = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    n   = len(meta)
    high_cnt    = sum(1 for s in meta if s.get("tier") == "high")
    medium_cnt  = sum(1 for s in meta if s.get("tier") == "medium")
    low_cnt     = sum(1 for s in meta if s.get("tier") == "low")
    total_items = sum(int(s.get("count", 0) or 0) for s in meta)
    lc = last_crawl or now
    last_disp = lc[5:16] if len(lc) >= 16 else lc

    def _tab(cat, label, cnt):
        if not cnt:
            return ""
        return (f'<span class="cat-tab" data-cat="{cat}" '
                f'onclick="filterCat(\'{cat}\')">{label} ({cnt})</span>')
    cat_tabs = [_tab("high", "🔥 线报羊毛", high_cnt),
                _tab("medium", "📰 优惠资讯", medium_cnt),
                _tab("low", "📦 软件工具", low_cnt)]
    cat_tabs_html = "\n        ".join(t for t in cat_tabs if t)

    cards_html = "\n      ".join(build_card(s) for s in meta)

    tmpl = f'''\
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>RSSForge · 订阅源目录</title>
      <meta name="description" content="RSSForge 自动化聚合 {n} 个线报 / 羊毛 / 优惠 RSS，支持官方 / ghfast / jsDelivr 多镜像一键订阅。">
      <link rel="alternate" type="application/rss+xml" title="RSSForge OPML" href="{BASE}/opml.xml">
      <link rel="alternate" type="application/rss+xml" title="RSSForge (ghfast)" href="{GHFAST_BASE}/opml.ghfast.xml">
      <link rel="alternate" type="application/rss+xml" title="RSSForge (jsDelivr)" href="{JSDELIVR_BASE}/opml.jsdelivr.xml">
      <style>{css()}</style>
    </head>
    <body>

    <button class="theme-toggle" onclick="toggleTheme()" title="切换深色模式" id="themeBtn">🌙</button>

    <header class="hero">
      <div class="hero-inner">
        <span class="badge">GitHub Actions 自动聚合</span>
        <h1>RSSForge</h1>
        <p class="tagline">聚合全网线报 · 羊毛 · 优惠 RSS，自动更新，多镜像一键订阅</p>
        <div class="opml-bar">
          <a class="opml-btn" href="{BASE}/opml.xml">📥 官方 OPML</a>
          <a class="opml-btn" href="{GHFAST_BASE}/opml.ghfast.xml">🚀 ghfast 镜像</a>
          <a class="opml-btn" href="{JSDELIVR_BASE}/opml.jsdelivr.xml">📦 jsDelivr CDN</a>
        </div>
      </div>
    </header>

    <div class="stats-strip">
      <div class="stat-card"><div class="stat-value">{n}</div><div class="stat-label">订阅源</div></div>
      <div class="stat-card"><div class="stat-value">{total_items:,}</div><div class="stat-label">收录条目</div></div>
      <div class="stat-card"><div class="stat-value">{high_cnt}</div><div class="stat-label">线报羊毛</div></div>
      <div class="stat-card"><div class="stat-value">{medium_cnt}</div><div class="stat-label">优惠资讯</div></div>
      <div class="stat-card"><div class="stat-value last">{last_disp}</div><div class="stat-label">最近更新</div></div>
    </div>

    <div class="container">

      <div class="about">
        <p><b>RSSForge</b> 是一个自动化 RSS 聚合项目：定时抓取多个线报 / 羊毛 / 优惠站点，统一生成标准 RSS 与 OPML，并部署到 GitHub Pages。一份 OPML 即可把全部源导入任意阅读器，无需逐个订阅。</p>
        <ol class="features">
          <li data-num="01"><b>多镜像</b>：官方 / ghfast / jsDelivr 三端同步，国内也可稳定访问</li>
          <li data-num="02"><b>自动更新</b>：按站点频率定时爬取，内容持续刷新</li>
          <li data-num="03"><b>一键订阅</b>：复制任一 OPML，在阅读器中导入即可</li>
        </ol>
      </div>

      <div class="section-head">
        <h2>订阅源目录</h2>
        <span class="sub">共 {n} 个 · 点击分类或搜索筛选</span>
      </div>

      <div class="toolbar">
        <div class="cat-tabs" id="catTabs">
          <span class="cat-tab active" data-cat="all" onclick="filterCat('all')">全部 ({n})</span>
          {cat_tabs_html}
        </div>
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="搜索站点名称或网址…" oninput="applyFilters()">
        </div>
        <span class="count-hint" id="countHint">当前显示 {n} 个订阅源</span>
      </div>

      <div class="feed-grid" id="feedGrid">
        {cards_html}
      </div>
      <p class="empty-hint" id="emptyHint">没有匹配的订阅源，换个关键词试试 🔍</p>

    </div>

    <footer>
      <p class="footer-pitch">RSSForge · 自动化 RSS 聚合与多镜像分发</p>
      <p class="footer-links">
         <a href="https://github.com/gitfox-enter/RSSForge" target="_blank" rel="noopener">⭐ GitHub</a> &middot;
         <a href="{BASE}/opml.xml" target="_blank" rel="noopener">📥 下载 OPML</a> &middot;
         <a href="https://github.com/gitfox-enter/RSSForge/issues/new/choose" target="_blank" rel="noopener">提交新源</a>
      </p>
      <p class="footer-note">订阅方式：复制上方任一 OPML 链接，在阅读器中「导入 / 添加订阅源」即可。</p>
    </footer>

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

    // ── Category filter + search ──
    var currentCat = 'all';
    function filterCat(cat) {{
      currentCat = cat;
      document.querySelectorAll('.cat-tab').forEach(function(el) {{
        el.classList.toggle('active', el.getAttribute('data-cat') === cat);
      }});
      applyFilters();
    }}
    function applyFilters() {{
      var q = document.getElementById('searchInput').value.trim().toLowerCase();
      var cards = document.querySelectorAll('#feedGrid .feed-card');
      var visible = 0;
      cards.forEach(function(c) {{
        var cat   = c.getAttribute('data-cat');
        var name  = c.getAttribute('data-name') || '';
        var site  = c.getAttribute('data-site') || '';
        var show  = (currentCat === 'all' || cat === currentCat)
                  && (!q || name.includes(q) || site.includes(q));
        c.style.display = show ? '' : 'none';
        if (show) visible++;
      }});
      document.getElementById('countHint').textContent = '当前显示 ' + visible + ' 个订阅源';
      document.getElementById('emptyHint').style.display = visible ? 'none' : 'block';
    }}
    </script>
    </body>
    </html>
    '''
    return textwrap.dedent(tmpl)

# ─────────────────────────────────────────────
# 7. 入口
# ─────────────────────────────────────────────
def load_last_crawl():
    """读取 crawl_status.json 的 last_run.check_time（真实最近爬取时间）。"""
    try:
        with open("crawl_status.json", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("last_run", {}).get("check_time") or ""
    except Exception:
        return ""

def main():
    meta = load_meta()
    last_crawl = load_last_crawl()
    html = gen_html(meta, last_crawl=last_crawl)
    os.makedirs("docs", exist_ok=True)
    out = "docs/index.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ {out}  ({len(meta)} feeds, {len(html):,} bytes)")
    with open("docs/version.txt", "w") as f:
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(hours=8))
        f.write(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S CST\n"))
        f.write(f"feeds: {len(meta)}\n")

if __name__ == "__main__":
    main()
