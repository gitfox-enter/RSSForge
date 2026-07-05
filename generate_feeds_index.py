#!/usr/bin/env python3
"""重新生成 docs/index.html —— Excel 风格表格布局"""
import json, os, textwrap

BASE = "https://gitfox-enter.github.io/RSSForge"

def load_meta():
    with open("feeds_meta.json") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # 字典结构 {slug: {name, url, category, ...}}
        result = []
        for slug, info in data.items():
            info["slug"] = slug
            result.append(info)
        return result
    else:
        # 列表结构 [{slug, name, url, category, ...}, ...]
        return data

def css():
    return textwrap.dedent("""\
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: -apple-system, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif;
           background: #f0f2f5; color: #222; }
    a { color: #1a73e8; text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* Header */
    header { background: linear-gradient(135deg, #1a73e8, #0d47a1);
             color: #fff; padding: 32px 24px 24px; text-align: center; }
    header h1 { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
    header .subtitle { font-size: 14px; opacity: .85; margin-bottom: 16px; }
    .stats { display:flex; justify-content:center; gap:24px; margin-bottom:20px; flex-wrap:wrap; }
    .stat { text-align:center; }
    .stat-value { font-size:24px; font-weight:700; }
    .stat-label { font-size:12px; opacity:.8; }

    /* OPML bar */
    .opml-bar { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin-bottom:8px; }
    .opml-btn { display:inline-block; padding:8px 18px; border-radius:20px;
                background:rgba(255,255,255,.18); color:#fff; font-size:14px; font-weight:500;
                transition: background .2s; }
    .opml-btn:hover { background:rgba(255,255,255,.32); text-decoration:none; color:#fff; }

    /* Container */
    .container { max-width:1200px; margin:0 auto; padding:24px 16px; }

    /* Excel-style table */
    .table-wrap { background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.12);
                  overflow:hidden; }
    table { width:100%; border-collapse:collapse; font-size:14px; }
    thead { position:sticky; top:0; z-index:1; }
    thead th { background:#e8eaed; color:#202124; font-weight:600; text-align:left;
               padding:10px 12px; border-bottom:2px solid #c0c4cc;
               white-space:nowrap; cursor:pointer; user-select:none; }
    thead th:hover { background:#d2d5da; }
    tbody tr { border-bottom:1px solid #e0e0e0; transition:background .15s; }
    tbody tr:nth-child(even) { background:#f8f9fa; }
    tbody tr:hover { background:#e8f0fe; }
    tbody td { padding:8px 12px; vertical-align:middle; }
    td.title { font-weight:500; color:#202124; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    td.url   { max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    td.url a { color:#5f6368; font-size:13px; }
    td.feed a { display:inline-block; padding:3px 10px; border-radius:4px;
                 font-size:12px; font-weight:500; white-space:nowrap; }
    td.feed .official { background:#e8f5e9; color:#2e7d32; }
    td.feed .mirror1 { background:#e3f2fd; color:#1565c0; }
    td.feed .mirror2 { background:#fce4ec; color:#c62828; }
    td.feed a:hover { opacity:.8; text-decoration:none; }

    /* Category tag */
    .cat { display:inline-block; padding:2px 8px; border-radius:10px;
           font-size:11px; font-weight:600; margin-right:6px; }
    .cat-high   { background:#fce8e6; color:#c5221f; }
    .cat-medium { background:#fef7e0; color:#e37400; }
    .cat-low    { background:#e8f5e9; color:#188038; }

    /* Filter bar */
    .filter-bar { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
    .filter-bar label { font-size:13px; color:#5f6368; }
    .filter-bar select, .filter-bar input {
        padding:6px 10px; border:1px solid #dadce0; border-radius:6px;
        font-size:13px; background:#fff; }
    .filter-bar input { width:220px; }

    /* Responsive */
    @media (max-width:768px) {
        .table-wrap { overflow-x:auto; }
        table { min-width:800px; }
    }
    """)

def gen_html(meta):
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    total = len(meta)
    cats = {"high": [], "medium": [], "low": []}
    for s in meta:
        cats[s.get("category","low")].append(s)

    lines = []
    w = lines.append

    w('<!DOCTYPE html>')
    w('<html lang="zh-CN">')
    w('<head>')
    w('  <meta charset="utf-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w('  <title>RSSForge - 订阅源目录</title>')
    # RSS Autodiscovery
    w(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (官方)" href="{BASE}/opml.xml">')
    w(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (ghfast)" href="https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml">')
    w(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (jsDelivr)" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml">')
    w(f'  <style>{css()}</style>')
    w('</head><body>')

    # ── Header ──
    w('  <header>')
    w('    <h1>📡 RSSForge</h1>')
    w(f'   <p class="subtitle">订阅源目录 · 更新时间：{now}</p>')
    w('    <div class="stats">')
    w(f'     <div class="stat"><div class="stat-value">{total}</div><div class="stat-label">总订阅源</div></div>')
    for cat, label in [("high","高频"), ("medium","中频"), ("low","低频")]:
        w(f'     <div class="stat"><div class="stat-value">{len(cats[cat])}</div><div class="stat-label">{label}</div></div>')
    w('    </div>')
    # OPML buttons
    w('    <div class="opml-bar">')
    w(f'     <a class="opml-btn" href="{BASE}/opml.xml">🌐 官方 OPML</a>')
    w(f'     <a class="opml-btn" href="https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml">🚀 ghfast 镜像</a>')
    w(f'     <a class="opml-btn" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml">📦 jsDelivr CDN</a>')
    w('    </div>')
    w('  </header>')

    # ── Main ──
    w('  <div class="container">')

    # Filter bar
    w('    <div class="filter-bar">')
    w('      <label>🔍 搜索：</label>')
    w('      <input type="text" id="searchInput" placeholder="输入标题或网址过滤…" oninput="filterTable()">')
    w('      <label>分类：</label>')
    w('      <select id="catFilter" onchange="filterTable()">')
    w('        <option value="">全部</option>')
    w('        <option value="high">高频</option>')
    w('        <option value="medium">中频</option>')
    w('        <option value="low">低频</option>')
    w('      </select>')
    w('    </div>')

    # Table
    w('    <div class="table-wrap">')
    w('    <table id="feedTable">')
    w('      <thead><tr>')
    w('        <th onclick="sortTable(0)">#</th>')
    w('        <th onclick="sortTable(1)">网页标题 ↕</th>')
    w('        <th onclick="sortTable(2)">网址 ↕</th>')
    w('        <th>官方订阅源</th>')
    w('        <th>加速链接 1 (ghfast)</th>')
    w('        <th>加速链接 2 (jsDelivr)</th>')
    w('      </tr></thead>')
    w('      <tbody>')

    for i, s in enumerate(meta, 1):
        slug  = s["slug"]
        title = s.get("name", slug)
        url   = s.get("url", "")
        cat   = s.get("category", "low")
        cat_label = {"high":"高频","medium":"中频","low":"低频"}[cat]

        official = f"{BASE}/feeds/{slug}.xml"
        mirror1  = f"https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/{slug}.xml"
        mirror2  = f"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{slug}.xml"

        w(f'      <tr data-cat="{cat}">')
        w(f'        <td>{i}</td>')
        w(f'        <td class="title">')
        w(f'          <span class="cat cat-{cat}">{cat_label}</span>{title}')
        w(f'        </td>')
        w(f'        <td class="url"><a href="{url}" target="_blank">{url}</a></td>')
        w(f'        <td class="feed"><a class="official" href="{official}" target="_blank">📡 官方</a></td>')
        w(f'        <td class="feed"><a class="mirror1" href="{mirror1}" target="_blank">🚀 ghfast</a></td>')
        w(f'        <td class="feed"><a class="mirror2" href="{mirror2}" target="_blank">📦 jsDelivr</a></td>')
        w(f'      </tr>')

    w('      </tbody>')
    w('    </table>')
    w('    </div>')  # table-wrap
    w('  </div>')    # container

    # ── JS ──
    w(textwrap.dedent("""\
    <script>
    function filterTable() {
        const q = document.getElementById('searchInput').value.toLowerCase();
        const cat = document.getElementById('catFilter').value;
        const rows = document.querySelectorAll('#feedTable tbody tr');
        rows.forEach(tr => {
            const title = tr.cells[1].textContent.toLowerCase();
            const url   = tr.cells[2].textContent.toLowerCase();
            const matchCat = !cat || tr.dataset.cat === cat;
            const matchQ   = !q   || title.includes(q) || url.includes(q);
            tr.style.display = (matchCat && matchQ) ? '' : 'none';
        });
    }
    function sortTable(colIdx) {
        const tbody = document.querySelector('#feedTable tbody');
        const rows  = Array.from(tbody.rows);
        const asc   = tbody.getAttribute('data-sort-dir') !== 'asc';
        tbody.setAttribute('data-sort-dir', asc ? 'asc' : 'desc');
        rows.sort((a, b) => {
            let va = a.cells[colIdx].textContent.trim();
            let vb = b.cells[colIdx].textContent.trim();
            if (!isNaN(va) && !isNaN(vb)) { va = +va; vb = +vb; }
            if (va < vb) return asc ? -1 : 1;
            if (va > vb) return asc ? 1 : -1;
            return 0;
        });
        rows.forEach(r => tbody.appendChild(r));
    }
    </script>
    """))

    w('</body></html>')
    return "\n".join(lines)

def main():
    meta = load_meta()
    meta.sort(key=lambda x: x.get("name", x["slug"]))
    html = gen_html(meta)
    os.makedirs("docs", exist_ok=True)
    out = "docs/index.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"  ✓ {out} 已生成（{len(meta)} 个订阅源）")

if __name__ == "__main__":
    main()
