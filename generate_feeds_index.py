#!/usr/bin/env python3
# generate_feeds_index.py — Excel 风格订阅源目录（含 ghfast / jsDelivr 加速链接）
import json, os, textwrap

BASE = "https://gitfox-enter.github.io/RSSForge"

# slug -> 中文名 映射表
NAME_MAP = {
    "12345-xian-bao":       "12345线报",
    "app-miao":             "APP喵",
    "appmiu":               "应用学堂",
    "fy6b":                 "FY6B",
    "fx1290":               "风向129",
    "gengxin":              "笔点更新",
    "hacker-daily":         "Hacker Daily",
    "ithome":              "IT之家",
    "jike":                "即刻",
    "kcyuntao":            "折扣买手",
    "liequ":               "乐购插件",
    "mefcl":               "免恶魔",
    "mtoou":               "馒头资源",
    "onetwo":              "一起沃",
    "plugin-org":           "插件阁",
    "pptbone":             "PPT模板站",
    "producthunt":         "Product Hunt",
    "producthunt-daily":   "PH日报",
    "realpha":             "ReAlpha",
    "ruike":               "锐克导航",
    "runoob":              "菜鸟教程",
    "sankebank":           "三可银行",
    "shui-myi":            "水母线报",
    "smzdm":               "什么值得买",
    "tuitui":              "推推导航",
    "wainao":              "歪脑网",
    "wanghou":             "网猴线报",
    "weishen":             "微社",
    "wo443":               "WO443",
    "xian-bao-ku":          "线报酷",
    "xian-bao-icu":         "线报ICU",
    "xianbao":             "每日线报",
    "xianbaowu":           "线报屋",
    "xiaoetong":           "小鹅通",
    "xiaojukeji":          "小桔科技",
    "xiazai":              "下载街",
    "xiuxian":             "咸鱼日记",
    "xyzc":                "xyzc",
    "yahoo-tech":          "Yahoo Tech",
    "yangmaoqun":           "羊毛群",
    "yxzhi":               "鸭先知",
    "yrxq":                "亿人星球",
    "yuanzhibo":           "直播盒子",
    "zaike":               "赚客吧",
    "zhanjiang":           "湛江圈",
    "zhihu":               "知乎日报",
    "zhuikey":             "追客",
}

def get_name(slug):
    return NAME_MAP.get(slug, slug)

def load_meta():
    with open("feeds_meta.json") as f:
        data = json.load(f)
    result = []
    for slug, info in data.items():
        info["slug"] = slug
        info["name"] = get_name(slug)
        result.append(info)
    return result

def css():
    return textwrap.dedent('''\\
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: -apple-system,\'Segoe UI\',Roboto,\'Noto Sans SC\',sans-serif;
           background:#f4f5f7; color:#24292f; }
    a { color:#15803d; text-decoration:none; }
    a:hover { text-decoration:underline; }

    header { background:linear-gradient(135deg,#16a34a,#14532d);
             color:#fff; padding:32px 24px 24px; text-align:center; }
    header h1 { font-size:28px; font-weight:700; margin-bottom:4px; }
    header .subtitle { font-size:14px; opacity:.85; margin-bottom:16px; }
    .stats { display:flex; justify-content:center; gap:24px; margin-bottom:20px; flex-wrap:wrap; }
    .stat { text-align:center; }
    .stat-value { font-size:24px; font-weight:700; }
    .stat-label { font-size:12px; opacity:.8; }
    .opml-bar { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin-bottom:8px; }
    .opml-btn { display:inline-block; padding:8px 18px; border-radius:20px;
                 background:rgba(255,255,255,.18); color:#fff; font-size:14px; font-weight:500;
                 transition:background .2s; }
    .opml-btn:hover { background:rgba(255,255,255,.32); text-decoration:none; color:#fff; }
    .container { max-width:1200px; margin:0 auto; padding:24px 16px; }
    .table-wrap { background:#fff; border-radius:8px;
                  box-shadow:0 1px 3px rgba(0,0,0,.12); overflow:hidden; }
    table { width:100%; border-collapse:collapse; font-size:14px; }
    thead { position:sticky; top:0; z-index:1; }
    thead th { background:#e8eaed; color:#24292f; font-weight:600; text-align:left;
               padding:10px 12px; border-bottom:2px solid #c0c4cc;
               white-space:nowrap; cursor:pointer; user-select:none; }
    td.icon { width:24px; text-align:center; padding:4px 8px !important; vertical-align:middle; }
    thead th:hover { background:#d2d5da; }
    tbody tr { border-bottom:1px solid #eaeef2; transition:background .12s; }
    tbody tr:nth-child(even) { background:#f6f8fa; }
    tbody tr:hover { background:#e8f0fe; }
    tbody td { padding:8px 12px; vertical-align:middle; }
    td.num { color:#6e7781; font-size:13px; text-align:center; width:40px; }
    td.title { font-weight:500; color:#1f2328; max-width:180px;
               overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    td.site a { color:#15803d; font-size:13px; max-width:180px;
                overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:inline-block; }
    td.feed a { display:inline-block; padding:3px 9px; border-radius:4px;
                font-size:12px; font-weight:500; white-space:nowrap; margin-right:4px; }
    td.feed .official { background:#dcfce7; color:#15803d; }
    td.feed .mirror1  { background:#dcfce7; color:#15803d; }
    td.feed .mirror2  { background:#fae8ff; color:#7e22ce; }
    td.feed a:hover { opacity:.75; text-decoration:none; }
    .filter-bar { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
    .filter-bar label { font-size:13px; color:#57606a; }
    .filter-bar input { padding:6px 10px; border:1px solid #d0d7de; border-radius:6px;
                         font-size:13px; width:220px; }
    .filter-bar input:focus { outline:2px solid #15803d; border-color:#15803d; }
    @media(max-width:768px) { .table-wrap{overflow-x:auto} table{min-width:900px} }
    ''')

def favicon_url(s):
    icon = s.get("icon", "")
    if icon and icon.startswith("https://"):
        return icon
    site = s.get("site_url", "")
    if site:
        domain = site.replace("https://", "").replace("http://", "").split("/")[0]
        return "https://" + domain + "/favicon.ico"
    return ""

def build_row(i, s):
    slug = s["slug"]
    name = s["name"]
    site = s.get("site_url", "")
    icon = favicon_url(s)
    icon_img = '<img src="' + icon + '" style="width:16px;height:16px;border-radius:2px;" loading="lazy" onerror="this.style.opacity=.3">' if icon else ""
    # 从 feed_url 提取文件名（如 xian-bao-ku.xml），不用 slug（中文 key）
    feed_url = s.get("feed_url", "")
    fname = feed_url.split("/")[-1] if feed_url else (slug + ".xml")
    official = "https://gitfox-enter.github.io/RSSForge/feeds/" + fname
    m1 = "https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/feeds/" + fname
    m2 = "https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/feeds/" + fname
    return (
        "        <tr>\n"
        "          <td class=\"num\">" + str(i) + "</td>\n"
        "          <td class=\"title\">" + name + "</td>\n"
        "          <td class=\"site\"><a href=\"" + site + "\" target=\"_blank\">" + site + "</a></td>\n"
        "          <td class=\"feed\"><a class=\"official\" href=\"" + official + "\" target=\"_blank\">&#x1F4E1; 官方</a></td>\n"
        "          <td class=\"feed\"><a class=\"mirror1\"  href=\"" + m1 + "\" target=\"_blank\">&#x1F680; ghfast</a></td>\n"
        "          <td class=\"feed\"><a class=\"mirror2\"  href=\"" + m2 + "\" target=\"_blank\">&#x1F4E6; jsDelivr</a></td>\n"
        "        </tr>"
    )

def gen_html(meta):
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    lines = []
    w = lines.append
    w("<!DOCTYPE html>")
    w("<html lang=\"zh-CN\">")
    w("<head>")
    w("  <meta charset=\"utf-8\">")
    w("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    w("  <title>RSSForge - 订阅源目录</title>")
    w("  <link rel=\"alternate\" type=\"application/rss+xml\" title=\"RSSForge (官方)\" href=\"https://gitfox-enter.github.io/RSSForge/opml.xml\">")
    w("  <link rel=\"alternate\" type=\"application/rss+xml\" title=\"RSSForge (ghfast)\" href=\"https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml\">")
    w("  <link rel=\"alternate\" type=\"application/rss+xml\" title=\"RSSForge (jsDelivr)\" href=\"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml\">")
    w("  <style>" + css() + "</style>")
    w("</head><body>")

    w("  <header>")
    w("    <h1>&#x1F4E1; RSSForge</h1>")
    w("    <p class=\"subtitle\">订阅源目录 &middot; " + now + "</p>")
    w("    <div class=\"stats\">")
    w("      <div class=\"stat\"><div class=\"stat-value\">" + str(len(meta)) + "</div><div class=\"stat-label\">订阅源总数</div></div>")
    w("    </div>")
    w("    <div class=\"opml-bar\">")
    w("      <a class=\"opml-btn\" href=\"https://gitfox-enter.github.io/RSSForge/opml.xml\">&#x1F310; 官方 OPML</a>")
    w("      <a class=\"opml-btn\" href=\"https://ghfast.top/raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.ghfast.xml\">&#x1F680; ghfast 镜像</a>")
    w("      <a class=\"opml-btn\" href=\"https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.jsdelivr.xml\">&#x1F4E6; jsDelivr CDN</a>")
    w("    </div>")
    w("  </header>")

    w("  <div class=\"container>")
    w("    <div class=\"filter-bar\">")
    w("      <label>&#x1F50D;</label>")
    w("      <input type=\"text\" id=\"searchInput\" placeholder=\"搜索站点名称或网址...\" oninput=\"filterTable()\">")
    w("    </div>")
    w("    <div class=\"table-wrap\">")
    w("    <table id=\"feedTable\">")
    w("      <thead><tr>")
    w("        <th onclick=\"sortTable(0)\">#</th>")
    w("        <th onclick=\"sortTable(1)\">站点名称 &uttri;</th>")
    w("        <th onclick=\"sortTable(2)\">网址 &uttri;</th>")
    w("        <th>官方订阅</th>")
    w("        <th>加速链接 1</th>")
    w("        <th>加速链接 2</th>")
    w("      </tr></thead>")
    w("      <tbody>")
    for i, s in enumerate(meta, 1):
        w(build_row(i, s))
    w("      </tbody>")
    w("    </table>")
    w("    </div>")
    w("  </div>")

    w("<script>")
    w("function filterTable(){")
    w("  var q=document.getElementById('searchInput').value.toLowerCase();")
    w("  var rows=document.querySelectorAll('#feedTable tbody tr');")
    w("  rows.forEach(function(tr){")
    w("    var t=tr.cells[1].textContent.toLowerCase();")
    w("    var u=tr.cells[2].textContent.toLowerCase();")
    w("    tr.style.display=(!q||t.includes(q)||u.includes(q))?'':'none';")
    w("  });")
    w("}")
    w("function sortTable(col){")
    w("  var tb=document.querySelector('#feedTable tbody');")
    w("  var dir=tb.getAttribute('data-dir')==='asc'?'desc':'asc';")
    w("  tb.setAttribute('data-dir',dir);")
    w("  var rows=Array.from(tb.rows);")
    w("  rows.sort(function(a,b){")
    w("    var va=a.cells[col].textContent.trim();")
    w("    var vb=b.cells[col].textContent.trim();")
    w("    if(!isNaN(va)&&!isNaN(vb)){va=+va;vb=+vb;}")
    w("    return dir==='asc'?(va>vb?1:-1):(va>vb?-1:1);")
    w("  });")
    w("  rows.forEach(function(r){tb.appendChild(r);});")
    w("}")
    w("</script>")
    w("</body></html>")
    return "\n".join(lines)

def main():
    meta = load_meta()
    html = gen_html(meta)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w") as f:
        f.write(html)
    print("  " + chr(10003) + " docs/index.html (" + str(len(meta)) + " feeds, " + str(len(html)) + " bytes)")

if __name__ == "__main__":
    main()
