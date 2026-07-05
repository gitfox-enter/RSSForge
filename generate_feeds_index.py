#!/usr/bin/env python3
"""重新生成 docs/index.html —— 真正的在线 Excel 表格风格"""
import json, os, textwrap

BASE = "https://gitfox-enter.github.io/RSSForge"

def load_meta():
    with open("feeds_meta.json") as f:
        data = json.load(f)
    if isinstance(data, dict):
        result = []
        for slug, info in data.items():
            info["slug"] = slug
            result.append(info)
        return result
    else:
        return data

def css():
    return textwrap.dedent("""\
    :root {
      --excel-green: #217346;
      --excel-green-light: #e8f5e9;
      --excel-green-dark: #185c37;
      --header-bg: #217346;
      --row-alt: #f7f9fc;
      --row-hover: #e3f2fd;
      --border: #d6dce4;
      --text-primary: #1a1a2e;
      --text-secondary: #5f6368;
      --badge-high-bg: #fce8e6; --badge-high-color: #c5221f;
      --badge-medium-bg: #fef7e0; --badge-medium-color: #e37400;
      --badge-low-bg: #e8f5e9; --badge-low-color: #188038;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: 'Segoe UI', -apple-system, 'Noto Sans SC', sans-serif;
           background: #e8eaed; color: var(--text-primary); }

    /* ── Top ribbon (Excel-style) ── */
    .ribbon {
      background: var(--excel-green); color: #fff; padding: 6px 16px;
      display: flex; align-items: center; gap: 16px; font-size: 13px;
      border-bottom: 2px solid var(--excel-green-dark);
    }
    .ribbon .brand { font-size: 16px; font-weight: 700; letter-spacing: -.3px; }
    .ribbon .sep { width:1px; height:18px; background:rgba(255,255,255,.3); }
    .ribbon .stat-chip { background:rgba(255,255,255,.15); padding:3px 10px; border-radius:3px; font-size:12px; }
    .ribbon .stat-chip b { margin-right:2px; }

    /* ── Toolbar (formula bar style) ── */
    .toolbar {
      background: #f3f3f3; border-bottom: 1px solid var(--border);
      padding: 6px 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    }
    .toolbar label { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
    .toolbar input[type="text"] {
      border: 1px solid var(--border); padding: 5px 10px; font-size: 13px;
      border-radius: 2px; width: 260px; outline: none;
      background: #fff; transition: border .2s;
    }
    .toolbar input[type="text"]:focus { border-color: var(--excel-green); box-shadow: 0 0 0 1px var(--excel-green); }
    .toolbar select {
      border: 1px solid var(--border); padding: 5px 8px; font-size: 13px;
      border-radius: 2px; background: #fff; outline: none; cursor: pointer;
    }
    .toolbar select:focus { border-color: var(--excel-green); }
    .toolbar .btn-opml {
      background: var(--excel-green); color: #fff; border: none; padding: 5px 12px;
      font-size: 12px; border-radius: 2px; cursor: pointer; font-weight: 500;
      text-decoration: none; display: inline-flex; align-items: center; gap: 4px;
    }
    .toolbar .btn-opml:hover { background: var(--excel-green-dark); text-decoration: none; color: #fff; }
    .toolbar .spacer { flex: 1; }

    /* ── Sheet tab bar ── */
    .sheet-tabs {
      background: #f3f3f3; border-bottom: 1px solid var(--border);
      padding: 0 12px; display: flex; gap: 0;
    }
    .sheet-tab {
      padding: 6px 20px; font-size: 12px; cursor: pointer;
      border: 1px solid transparent; border-bottom: none;
      color: var(--text-secondary); font-weight: 500; background: transparent;
      border-radius: 4px 4px 0 0; margin-bottom: -1px; transition: all .15s;
    }
    .sheet-tab.active {
      background: #fff; color: var(--excel-green); border-color: var(--border);
      border-bottom: 1px solid #fff; font-weight: 600;
    }
    .sheet-tab:hover:not(.active) { background: #e8eaed; }

    /* ── Table ── */
    .table-wrap {
      background: #fff; overflow: auto; max-height: calc(100vh - 130px);
      border-top: 1px solid var(--border);
    }
    table { width:100%; border-collapse:collapse; font-size:13px; table-layout: fixed; }
    col.col-no   { width: 48px; }
    col.col-cat  { width: 72px; }
    col.col-name { width: 180px; }
    col.col-url  { width: auto; }
    col.col-feed { width: 260px; }
    thead { position: sticky; top: 0; z-index: 2; }
    thead th {
      background: #f3f3f3; color: var(--text-secondary); font-weight: 600;
      text-align: left; padding: 7px 10px; border-right: 1px solid var(--border);
      border-bottom: 2px solid var(--excel-green); white-space: nowrap;
      cursor: pointer; user-select: none; font-size: 12px;
    }
    thead th:hover { background: #e8eaed; }
    thead th .sort-arrow { font-size: 10px; opacity: .4; margin-left: 2px; }
    tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
    tbody tr:nth-child(even) { background: var(--row-alt); }
    tbody tr:hover { background: var(--row-hover); }
    tbody td {
      padding: 6px 10px; border-right: 1px solid #eef1f5;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    /* Row number (like Excel row header) */
    td.row-no {
      background: #f3f3f3; color: var(--text-secondary); text-align: center;
      font-size: 11px; font-weight: 500; border-right: 1px solid var(--border);
    }

    /* Category badge */
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 2px;
      font-size: 11px; font-weight: 600; letter-spacing: .2px;
    }
    .badge-high   { background: var(--badge-high-bg); color: var(--badge-high-color); }
    .badge-medium { background: var(--badge-medium-bg); color: var(--badge-medium-color); }
    .badge-low    { background: var(--badge-low-bg); color: var(--badge-low-color); }

    /* Feed links */
    .feed-links { display: flex; gap: 4px; }
    .feed-link {
      display: inline-block; padding: 2px 8px; border-radius: 2px;
      font-size: 11px; font-weight: 500; text-decoration: none;
      white-space: nowrap; transition: filter .15s;
    }
    .feed-link:hover { filter: brightness(.9); text-decoration: none; }
    .feed-official { background: #e8f5e9; color: #2e7d32; }
    .feed-mirror1  { background: #e3f2fd; color: #1565c0; }
    .feed-mirror2  { background: #fce4ec; color: #c62828; }

    /* Site name with favicon */
    .site-name { display: flex; align-items: center; gap: 6px; }
    .site-name img { width: 16px; height: 16px; border-radius: 2px; flex-shrink: 0; }
    .site-name span { overflow: hidden; text-overflow: ellipsis; }

    /* URL cell */
    td.cell-url a { color: var(--text-secondary); font-size: 12px; text-decoration: none; }
    td.cell-url a:hover { color: var(--excel-green); text-decoration: underline; }

    /* Footer status bar (Excel-style) */
    .status-bar {
      background: var(--excel-green); color: #fff; padding: 4px 16px;
      font-size: 11px; display: flex; justify-content: space-between; align-items: center;
    }
    .status-bar .left { opacity: .9; }
    .status-bar .right { display: flex; gap: 16px; opacity: .85; }

    /* Responsive */
    @media (max-width:768px) {
      .toolbar input[type="text"] { width: 160px; }
      table { min-width: 700px; }
    }
    """)

def gen_html(meta):
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    total = len(meta)
    cats = {"high": [], "medium": [], "low": []}
    for s in meta:
        cats[s.get("category", "low")].append(s)

    lines = []
    w = lines.append

    w('<!DOCTYPE html>')
    w('<html lang="zh-CN">')
    w('<head>')
    w('  <meta charset="utf-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w('  <title>RSSForge - 订阅源目录</title>')
    w(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (官方)" href="{BASE}/opml.xml">')
    w(f'  <style>{css()}</style>')
    w('</head><body>')

    # ── Ribbon ──
    w('  <div class="ribbon">')
    w('    <span class="brand">RSSForge</span>')
    w('    <span class="sep"></span>')
    w(f'    <span class="stat-chip"><b>{total}</b> 源</span>')
    w(f'    <span class="stat-chip"><b>{len(cats["high"])}</b> 高频</span>')
    w(f'    <span class="stat-chip"><b>{len(cats["medium"])}</b> 中频</span>')
    w(f'    <span class="stat-chip"><b>{len(cats["low"])}</b> 低频</span>')
    w('  </div>')

    # ── Toolbar ──
    w('  <div class="toolbar">')
    w('    <label>搜索</label>')
    w('    <input type="text" id="searchInput" placeholder="输入站点名称或网址…" oninput="filterTable()">')
    w('    <label>分类</label>')
    w('    <select id="catFilter" onchange="filterTable()">')
    w('      <option value="">全部</option>')
    w('      <option value="high">高频</option>')
    w('      <option value="medium">中频</option>')
    w('      <option value="low">低频</option>')
    w('    </select>')
    w('    <span class="spacer"></span>')
    w(f'    <a class="btn-opml" href="{BASE}/opml.xml" target="_blank">OPML 官方</a>')
    w(f'    <a class="btn-opml" href="https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml" target="_blank" style="background:#1565c0">OPML ghfast</a>')
    w(f'    <a class="btn-opml" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml" target="_blank" style="background:#c62828">OPML jsDelivr</a>')
    w('  </div>')

    # ── Sheet tabs ──
    w('  <div class="sheet-tabs">')
    w('    <div class="sheet-tab active" data-cat="" onclick="switchTab(this, \'\')">全部订阅源</div>')
    w('    <div class="sheet-tab" data-cat="high" onclick="switchTab(this, \'high\')">高频源</div>')
    w('    <div class="sheet-tab" data-cat="medium" onclick="switchTab(this, \'medium\')">中频源</div>')
    w('    <div class="sheet-tab" data-cat="low" onclick="switchTab(this, \'low\')">低频源</div>')
    w('  </div>')

    # ── Table ──
    w('  <div class="table-wrap">')
    w('  <table id="feedTable">')
    w('    <colgroup>')
    w('      <col class="col-no">')
    w('      <col class="col-cat">')
    w('      <col class="col-name">')
    w('      <col class="col-url">')
    w('      <col class="col-feed">')
    w('    </colgroup>')
    w('    <thead><tr>')
    w('      <th onclick="sortTable(0)"><span class="sort-arrow"></span></th>')
    w('      <th onclick="sortTable(1)">分类 <span class="sort-arrow">↕</span></th>')
    w('      <th onclick="sortTable(2)">站点名称 <span class="sort-arrow">↕</span></th>')
    w('      <th onclick="sortTable(3)">网址 <span class="sort-arrow">↕</span></th>')
    w('      <th>订阅地址</th>')
    w('    </tr></thead>')
    w('    <tbody>')

    for i, s in enumerate(meta, 1):
        slug  = s["slug"]
        title = s.get("name", slug)
        url   = s.get("url", "")
        cat   = s.get("category", "low")
        cat_label = {"high": "高频", "medium": "中频", "low": "低频"}[cat]
        icon  = s.get("icon", "")

        official = f"{BASE}/feeds/{slug}.xml"
        mirror1  = f"https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/{slug}.xml"
        mirror2  = f"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{slug}.xml"

        icon_img = f'<img src="{icon}" alt="" onerror="this.style.display=\'none\'">' if icon else ''

        w(f'      <tr data-cat="{cat}">')
        w(f'        <td class="row-no">{i}</td>')
        w(f'        <td><span class="badge badge-{cat}">{cat_label}</span></td>')
        w(f'        <td><div class="site-name">{icon_img}<span>{title}</span></div></td>')
        w(f'        <td class="cell-url"><a href="{url}" target="_blank">{url}</a></td>')
        w(f'        <td><div class="feed-links">')
        w(f'          <a class="feed-link feed-official" href="{official}" target="_blank">官方</a>')
        w(f'          <a class="feed-link feed-mirror1" href="{mirror1}" target="_blank">ghfast</a>')
        w(f'          <a class="feed-link feed-mirror2" href="{mirror2}" target="_blank">jsDelivr</a>')
        w(f'        </div></td>')
        w(f'      </tr>')

    w('    </tbody>')
    w('  </table>')
    w('  </div>')

    # ── Status bar ──
    w('  <div class="status-bar">')
    w(f'    <span class="left">就绪 | 上次更新：{now}</span>')
    w(f'    <span class="right">')
    w(f'      <span>共 {total} 条记录</span>')
    w(f'      <span>高频 {len(cats["high"])} | 中频 {len(cats["medium"])} | 低频 {len(cats["low"])}</span>')
    w(f'    </span>')
    w('  </div>')

    # ── JS ──
    w(textwrap.dedent("""\
    <script>
    function filterTable() {
        const q = document.getElementById('searchInput').value.toLowerCase();
        const cat = document.getElementById('catFilter').value;
        const rows = document.querySelectorAll('#feedTable tbody tr');
        let visible = 0;
        rows.forEach(tr => {
            const title = tr.cells[2].textContent.toLowerCase();
            const url   = tr.cells[3].textContent.toLowerCase();
            const matchCat = !cat || tr.dataset.cat === cat;
            const matchQ   = !q   || title.includes(q) || url.includes(q);
            tr.style.display = (matchCat && matchQ) ? '' : 'none';
            if (matchCat && matchQ) visible++;
        });
        document.getElementById('visibleCount').textContent = visible;
    }
    function switchTab(el, cat) {
        document.querySelectorAll('.sheet-tab').forEach(t => t.classList.remove('active'));
        el.classList.add('active');
        document.getElementById('catFilter').value = cat;
        filterTable();
    }
    let sortDir = {};
    function sortTable(colIdx) {
        const tbody = document.querySelector('#feedTable tbody');
        const rows  = Array.from(tbody.rows);
        sortDir[colIdx] = !sortDir[colIdx];
        const asc = sortDir[colIdx];
        rows.sort((a, b) => {
            let va = a.cells[colIdx].textContent.trim();
            let vb = b.cells[colIdx].textContent.trim();
            if (!isNaN(va) && !isNaN(vb)) { va = +va; vb = +vb; }
            return va < vb ? (asc ? -1 : 1) : va > vb ? (asc ? 1 : -1) : 0;
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
