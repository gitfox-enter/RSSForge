#!/usr/bin/env python3
"""重新生成 docs/index.html —— 简洁 Excel 表格风格，无分类"""
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
      --g: #217346; --g-dark: #185c37;
      --border: #d6dce4; --row-alt: #f7f9fc; --row-hover: #e3f2fd;
      --t1: #1a1a2e; --t2: #5f6368;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: 'Segoe UI', -apple-system, 'Noto Sans SC', sans-serif;
           background: #e8eaed; color: var(--t1); }

    .ribbon {
      background: var(--g); color: #fff; padding: 8px 20px;
      display: flex; align-items: center; gap: 20px; font-size: 14px;
    }
    .ribbon .brand { font-size: 20px; font-weight: 700; letter-spacing: -.5px; }
    .ribbon .sep { width:1px; height:20px; background:rgba(255,255,255,.25); }
    .ribbon .stat { opacity:.85; font-size:13px; }

    .toolbar {
      background: #f3f3f3; border-bottom: 1px solid var(--border);
      padding: 8px 16px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    }
    .toolbar input[type="text"] {
      border: 1px solid var(--border); padding: 6px 12px; font-size: 13px;
      border-radius: 3px; width: 300px; outline: none; background: #fff;
    }
    .toolbar input[type="text"]:focus { border-color: var(--g); box-shadow: 0 0 0 1px var(--g); }
    .toolbar .spacer { flex: 1; }
    .btn {
      display:inline-block; padding:6px 14px; border-radius:3px;
      font-size:12px; font-weight:600; text-decoration:none; color:#fff;
      cursor:pointer; border:none; transition: filter .15s;
    }
    .btn:hover { filter: brightness(.85); text-decoration:none; color:#fff; }
    .btn-green { background: var(--g); }
    .btn-blue  { background: #1565c0; }
    .btn-red   { background: #c62828; }

    .table-wrap {
      background: #fff; overflow: auto; max-height: calc(100vh - 100px);
    }
    table { width:100%; border-collapse:collapse; font-size:13px; table-layout: fixed; }
    col.c1 { width: 48px; }
    col.c2 { width: 200px; }
    col.c3 { width: auto; }
    col.c4 { width: 280px; }
    thead { position: sticky; top: 0; z-index: 2; }
    thead th {
      background: #f3f3f3; color: var(--t2); font-weight: 600;
      text-align: left; padding: 8px 12px; border-right: 1px solid var(--border);
      border-bottom: 2px solid var(--g); white-space: nowrap;
      cursor: pointer; user-select: none; font-size: 12px;
    }
    thead th:hover { background: #e8eaed; }
    tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
    tbody tr:nth-child(even) { background: var(--row-alt); }
    tbody tr:hover { background: var(--row-hover); }
    tbody td {
      padding: 7px 12px; border-right: 1px solid #eef1f5;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    td.row-no {
      background: #f3f3f3; color: var(--t2); text-align: center;
      font-size: 11px; font-weight: 500;
    }
    .site-name { display: flex; align-items: center; gap: 8px; font-weight: 500; }
    .site-name img { width: 16px; height: 16px; border-radius: 2px; flex-shrink: 0; }
    .site-name span { overflow: hidden; text-overflow: ellipsis; }
    td.cell-url a { color: var(--t2); font-size: 12px; text-decoration: none; }
    td.cell-url a:hover { color: var(--g); text-decoration: underline; }
    .feed-links { display: flex; gap: 6px; }
    .fl {
      display:inline-block; padding:3px 10px; border-radius:3px;
      font-size:11px; font-weight:500; text-decoration:none;
      white-space:nowrap; transition: filter .15s;
    }
    .fl:hover { filter: brightness(.85); text-decoration:none; }
    .fl-g { background:#e8f5e9; color:#2e7d32; }
    .fl-b { background:#e3f2fd; color:#1565c0; }
    .fl-r { background:#fce4ec; color:#c62828; }

    .status-bar {
      background: var(--g); color: #fff; padding: 5px 20px;
      font-size: 11px; display: flex; justify-content: space-between; align-items: center;
    }
    .status-bar .right { display: flex; gap: 20px; opacity:.8; }

    @media (max-width:768px) {
      .toolbar input[type="text"] { width: 180px; }
      table { min-width: 600px; }
    }
    """)

def gen_html(meta):
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    total = len(meta)

    # Count feeds with content
    active = sum(1 for s in meta if s.get("count", 0) > 0)

    lines = []
    w = lines.append

    w('<!DOCTYPE html>')
    w('<html lang="zh-CN">')
    w('<head>')
    w('  <meta charset="utf-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w('  <title>RSSForge - 订阅源目录</title>')
    w(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge" href="{BASE}/opml.xml">')
    w(f'  <style>{css()}</style>')
    w('</head><body>')

    # ── Ribbon ──
    w('  <div class="ribbon">')
    w('    <span class="brand">RSSForge</span>')
    w('    <span class="sep"></span>')
    w(f'    <span class="stat">{total} 个订阅源</span>')
    w(f'    <span class="stat">{active} 个活跃</span>')
    w('  </div>')

    # ── Toolbar ──
    w('  <div class="toolbar">')
    w('    <input type="text" id="searchInput" placeholder="搜索站点名称或网址…" oninput="filterTable()">')
    w('    <span class="spacer"></span>')
    w(f'    <a class="btn btn-green" href="{BASE}/opml.xml" target="_blank">OPML 官方</a>')
    w(f'    <a class="btn btn-blue" href="https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml" target="_blank">OPML ghfast</a>')
    w(f'    <a class="btn btn-red" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml" target="_blank">OPML jsDelivr</a>')
    w('  </div>')

    # ── Table ──
    w('  <div class="table-wrap">')
    w('  <table id="feedTable">')
    w('    <colgroup>')
    w('      <col class="c1">')
    w('      <col class="c2">')
    w('      <col class="c3">')
    w('      <col class="c4">')
    w('    </colgroup>')
    w('    <thead><tr>')
    w('      <th></th>')
    w('      <th onclick="sortTable(1)">站点名称 <span style="font-size:10px;opacity:.4">↕</span></th>')
    w('      <th onclick="sortTable(2)">网址 <span style="font-size:10px;opacity:.4">↕</span></th>')
    w('      <th>订阅地址</th>')
    w('    </tr></thead>')
    w('    <tbody>')

    for i, s in enumerate(meta, 1):
        slug  = s["slug"]
        title = s.get("name", slug)
        url   = s.get("url", "")
        icon  = s.get("icon", "")

        official = f"{BASE}/feeds/{slug}.xml"
        mirror1  = f"https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/{slug}.xml"
        mirror2  = f"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/{slug}.xml"

        icon_img = f'<img src="{icon}" alt="" onerror="this.style.display=\'none\'">' if icon else ''

        w(f'      <tr>')
        w(f'        <td class="row-no">{i}</td>')
        w(f'        <td><div class="site-name">{icon_img}<span>{title}</span></div></td>')
        w(f'        <td class="cell-url"><a href="{url}" target="_blank">{url}</a></td>')
        w(f'        <td><div class="feed-links">')
        w(f'          <a class="fl fl-g" href="{official}" target="_blank">官方</a>')
        w(f'          <a class="fl fl-b" href="{mirror1}" target="_blank">ghfast</a>')
        w(f'          <a class="fl fl-r" href="{mirror2}" target="_blank">jsDelivr</a>')
        w(f'        </div></td>')
        w(f'      </tr>')

    w('    </tbody>')
    w('  </table>')
    w('  </div>')

    # ── Status bar ──
    w('  <div class="status-bar">')
    w(f'    <span>就绪 | 更新：{now}</span>')
    w(f'    <span class="right"><span>共 {total} 条</span><span>活跃 {active}</span></span>')
    w('  </div>')

    # ── JS ──
    w(textwrap.dedent("""\
    <script>
    function filterTable(){
      const q=document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('#feedTable tbody tr').forEach(tr=>{
        const t=tr.cells[1].textContent.toLowerCase();
        const u=tr.cells[2].textContent.toLowerCase();
        tr.style.display=(!q||t.includes(q)||u.includes(q))?'':'none';
      });
    }
    let sd={};
    function sortTable(c){
      const tb=document.querySelector('#feedTable tbody');
      const rs=Array.from(tb.rows);
      sd[c]=!sd[c];const a=sd[c];
      rs.sort((x,y)=>{
        let va=x.cells[c].textContent.trim(),vb=y.cells[c].textContent.trim();
        if(!isNaN(va)&&!isNaN(vb)){va=+va;vb=+vb;}
        return va<vb?(a?-1:1):va>vb?(a?1:-1):0;
      });
      rs.forEach(r=>tb.appendChild(r));
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
