#!/usr/bin/env python3
"""
生成 RSSForge 订阅源目录页面 docs/index.html。

读取 feeds_meta.json，按频率分组，生成带 RSS autodiscovery 的美观页面。
用法：python generate_feeds_index.py
"""

import json
import os
from datetime import datetime

BASE = "https://gitfox-enter.github.io/RSSForge"

def load_meta():
    with open("feeds_meta.json", "r", encoding="utf-8") as f:
        return json.load(f)

def classify(freq_min):
    if freq_min <= 30:
        return "high"
    elif freq_min <= 120:
        return "medium"
    return "low"

LABELS = {
    "high":   ("高频更新", "⚡"),
    "medium":  ("中频更新", "📰"),
    "low":     ("低频更新", "📚"),
}

FREQ_LABEL = {
    "high":   "高频",
    "medium":  "中频",
    "low":     "低频",
}


def build_html(meta):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    groups = {"high": [], "medium": [], "low": []}
    for name, info in meta.items():
        freq = info.get("frequency", 30)
        cat = classify(freq)
        groups[cat].append((name, info))

    total = sum(len(v) for v in groups.values())

    for cat in groups:
        groups[cat].sort(key=lambda x: x[0])

    # ---- HTML ----
    HR = "⚡📰📚"[0]  # dummy, not used

    css = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f1f5f9;
      color: #1e293b;
      line-height: 1.6;
      padding: 1.5rem;
    }
    .container { max-width: 1100px; margin: 0 auto; }

    /* Header */
    header {
      text-align: center;
      padding: 2.5rem 2rem;
      background: linear-gradient(135deg, #6366f1 0%, #a78bfa 100%);
      color: #fff;
      border-radius: 14px;
      margin-bottom: 2rem;
    }
    header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { opacity: 0.85; font-size: 0.95rem; margin-bottom: 1.5rem; }

    .stats { display: flex; justify-content: center; gap: 2.5rem; flex-wrap: wrap; }
    .stat { text-align: center; }
    .stat-value { font-size: 1.75rem; font-weight: 700; }
    .stat-label { font-size: 0.8rem; opacity: 0.8; }

    /* OPML bar */
    .opml-bar { display: flex; justify-content: center; gap: 0.75rem; flex-wrap: wrap; margin-top: 1.5rem; }
    .opml-btn {
      display: inline-flex; align-items: center; gap: 0.4rem;
      padding: 0.5rem 1rem;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 8px;
      color: #fff; text-decoration: none; font-size: 0.85rem;
      transition: background 0.2s;
    }
    .opml-btn:hover { background: rgba(255,255,255,0.30); }

    /* Section */
    .section {
      background: #fff; border-radius: 14px;
      padding: 1.5rem; margin-bottom: 1.5rem;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .section-header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 1rem; padding-bottom: 0.75rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .section-header h2 { font-size: 1.15rem; font-weight: 600; }
    .badge {
      background: #eef2ff; color: #4f46e5;
      padding: 0.2rem 0.7rem; border-radius: 9999px;
      font-size: 0.75rem; font-weight: 500;
    }

    /* Grid */
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }

    /* Card */
    .card {
      border: 1px solid #e2e8f0; border-radius: 10px;
      padding: 1rem 1.1rem;
      display: flex; flex-direction: column; gap: 0.4rem;
      transition: box-shadow 0.2s, border-color 0.2s;
    }
    .card:hover {
      box-shadow: 0 4px 16px rgba(99,102,241,0.13);
      border-color: #6366f1;
    }
    .card-top { display: flex; align-items: center; justify-content: space-between; }
    .card-name { font-weight: 600; font-size: 1rem; color: #4f46e5; }
    .card-name a { color: inherit; text-decoration: none; }
    .card-name a:hover { text-decoration: underline; }
    .freq-tag { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 5px; font-weight: 500; }
    .freq-high   { background: #fef3c7; color: #92400e; }
    .freq-medium { background: #dbeafe; color: #1e40af; }
    .freq-low    { background: #dcfce7; color: #166534; }
    .card-site { font-size: 0.78rem; color: #64748b; word-break: break-all; }
    .card-site a { color: inherit; text-decoration: none; }
    .card-site a:hover { text-decoration: underline; }
    .card-meta { display: flex; gap: 0.5rem; flex-wrap: wrap;
                   font-size: 0.75rem; color: #64748b; margin-top: auto; padding-top: 0.3rem; }

    /* Footer */
    footer { text-align: center; margin-top: 2rem; padding: 1.5rem;
               color: #64748b; font-size: 0.85rem; }
    footer a { color: #4f46e5; text-decoration: none; }
    footer a:hover { text-decoration: underline; }

    @media (max-width: 640px) {
      body { padding: 0.75rem; }
      header h1 { font-size: 1.5rem; }
      .grid { grid-template-columns: 1fr; }
    }
    """

    # HTML 组装
    html = []
    html.append('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n')
    html.append('  <meta charset="UTF-8">\n')
    html.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
    html.append('  <title>RSSForge - 订阅源目录</title>\n')
    # RSS Autodiscovery links
    html.append(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (官方)" href="{BASE}/opml.xml">\n')
    html.append(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (ghfast 镜像)" href="https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.xml">\n')
    html.append(f'  <link rel="alternate" type="application/rss+xml" title="RSSForge (jsDelivr CDN)" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.xml">\n')
    html.append(f'  <style>\n{css}\n  </style>\n')
    html.append('</head>\n<body>\n')
    html.append('  <div class="container">\n')

    # Header
    html.append(f'    <header>\n')
    html.append(f'      <h1>📡 RSSForge</h1>\n')
    html.append(f'      <p class="subtitle">订阅源目录 · 更新时间：{now}</p>\n')
    html.append(f'      <div class="stats">\n')
    html.append(f'        <div class="stat"><div class="stat-value">{total}</div><div class="stat-label">总订阅源</div></div>\n')
    for cat in ["high", "medium", "low"]:
        label = {"high": "高频", "medium": "中频", "low": "低频"}[cat]
        html.append(f'        <div class="stat"><div class="stat-value">{len(groups[cat])}</div><div class="stat-label">{label}</div></div>\n')
    html.append(f'      </div>\n')
    html.append(f'      <div class="opml-bar">\n')
    html.append(f'        <a class="opml-btn" href="{BASE}/opml.xml" title="官方链接（GitHub Pages）">🌐 官方 OPML</a>\n')
    html.append(f'        <a class="opml-btn" href="https://ghfast.top/https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/docs/opml.xml" title="国内加速（ghfast.top）">🚀 ghfast 镜像</a>\n')
    html.append(f'        <a class="opml-btn" href="https://cdn.jsdelivr.net/gh/gitfox-enter/RSSForge@main/docs/opml.xml" title="CDN 加速（jsDelivr）">📦 jsDelivr CDN</a>\n')
    html.append(f'      </div>\n')
    html.append(f'    </header>\n')

    # Sections
    for cat in ["high", "medium", "low"]:
        items = groups[cat]
        if not items:
            continue
        icon, label = LABELS[cat]
        html.append(f'    <div class="section">\n')
        html.append(f'      <div class="section-header"><h2>{icon} {label}</h2><span class="badge">{len(items)} 个站点</span></div>\n')
        html.append(f'      <div class="grid">\n')
        for name, info in items:
            # 提取 slug
            feed_url = info.get("feed_url", "")
            if "/feeds/" in feed_url:
                slug = feed_url.split("/feeds/")[-1].replace(".xml", "")
            else:
                slug = name
            xml_url = f"{BASE}/feeds/{slug}.xml"
            site_url = info.get("site_url", "")
            freq_min = info.get("frequency", 30)
            freq_cls = f"freq-{cat}"

            site_link = ""
            if site_url:
                display = site_url.replace("https://", "").replace("http://", "")[:42]
                site_link = f'<div class="card-site"><a href="{site_url}" target="_blank" rel="noopener">{display}</a></div>\n'

            html.append(f'        <div class="card">\n')
            html.append(f'          <div class="card-top">\n')
            html.append(f'            <div class="card-name"><a href="{xml_url}" target="_blank">📡 {name}</a></div>\n')
            html.append(f'            <span class="freq-tag {freq_cls}">{FREQ_LABEL[cat]}</span>\n')
            html.append(f'          </div>\n')
            if site_link:
                html.append(f'          {site_link}')
            html.append(f'          <div class="card-meta"><span>每 {freq_min} 分钟</span></div>\n')
            html.append(f'        </div>\n')
        html.append(f'      </div>\n')
        html.append(f'    </div>\n')

    # Footer
    html.append(f'    <footer>\n')
    html.append(f'      <p>由 <a href="https://github.com/gitfox-enter/RSSForge">RSSForge</a> 驱动 · 自动更新</p>\n')
    html.append(f'    </footer>\n')
    html.append(f'  </div>\n')
    html.append(f'</body>\n</html>\n')

    return "".join(html)


def main():
    meta = load_meta()
    html = build_html(meta)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ docs/index.html 已生成（{len(meta)} 个订阅源）")


if __name__ == "__main__":
    main()
