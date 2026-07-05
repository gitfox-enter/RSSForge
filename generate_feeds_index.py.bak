#!/usr/bin/env python3
"""
RSS Feed 订阅源目录页面生成器

生成 feeds/index.html，展示所有可用的 RSS 订阅源。
"""

import os
import re
import sys
from pathlib import Path


def simple_parse_yaml(content: str) -> dict:
    """简易 YAML 解析器，避免依赖 PyYAML。"""
    result = {}
    current_section = None
    current_list = []
    in_list = False
    in_multiline = False
    multiline_key = None
    multiline_value = []
    
    for line_num, line in enumerate(content.split('\n'), 1):
        # 跳过空行和注释
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # 处理多行值
        if in_multiline:
            if stripped and (stripped.startswith(' ') or stripped.startswith('\t')):
                multiline_value.append(stripped)
                continue
            else:
                # 多行结束，保存之前的值
                if multiline_key and multiline_value:
                    current_list[-1][multiline_key] = '\n'.join(multiline_value)
                in_multiline = False
                multiline_key = None
                multiline_value = []
        
        # 列表项
        if stripped.startswith('- '):
            item = {}
            current_list.append(item)
            in_list = True
            value_part = stripped[2:].strip()
            
            if ':' in value_part:
                key, val = value_part.split(':', 1)
                item[key.strip()] = val.strip().strip('"\'')
            continue
        
        # 键值对
        if ':' in stripped:
            # 如果在列表内，处理下一个键
            if in_list and not stripped.startswith('-'):
                in_list = False
            
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            if val == '' or val is None:
                # 可能开始多行值
                if key in ['description', 'instructions', 'content']:
                    in_multiline = True
                    multiline_key = key
                    multiline_value = []
                    current_section = key
                else:
                    current_section = key
                    result[key] = ''
            elif val.startswith('"') or val.startswith("'"):
                result[key] = val.strip('"\'')
            else:
                try:
                    result[key] = int(val) if val.isdigit() else val
                except:
                    result[key] = val
    
    return result


def load_sites_yaml():
    """加载 sites.yaml。"""
    sites_file = Path(__file__).parent / 'sites.yaml'
    if not sites_file.exists():
        print(f"警告: {sites_file} 不存在", file=sys.stderr)
        return {}
    
    with open(sites_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单解析
    sites = []
    current_site = {}
    current_key = None
    in_content = False
    content_lines = []
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # 处理多行内容
        if in_content:
            if stripped and (stripped.startswith('      ') or stripped.startswith('\t')):
                content_lines.append(stripped)
                continue
            else:
                # 多行结束
                if content_lines:
                    current_site['content'] = '\n'.join(content_lines)
                in_content = False
                content_lines = []
        
        if not stripped or stripped.startswith('#'):
            continue
        
        # 列表项
        if stripped.startswith('- '):
            if current_site and current_site.get('url'):
                sites.append(current_site)
            current_site = {}
            item = stripped[2:].strip()
            if ':' in item:
                key, val = item.split(':', 1)
                current_site[key.strip()] = val.strip().strip('"\'')
            continue
        
        # 键值对
        if ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            if val == '':
                if key == 'content':
                    in_content = True
                    content_lines = []
                current_key = key
            else:
                current_site[key] = val.strip('"\'')
    
    if current_site and current_site.get('url'):
        sites.append(current_site)
    
    return sites


def load_custom_sources():
    """加载 custom_sources.yaml（如果存在）。"""
    custom_file = Path(__file__).parent / 'custom_sources.yaml'
    if not custom_file.exists():
        return []
    
    with open(custom_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sites = []
    current_site = {}
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        if stripped.startswith('- '):
            if current_site and current_site.get('url'):
                sites.append(current_site)
            current_site = {}
            item = stripped[2:].strip()
            if ':' in item:
                key, val = item.split(':', 1)
                current_site[key.strip()] = val.strip().strip('"\'')
            continue
        
        if ':' in stripped:
            key, val = stripped.split(':', 1)
            current_site[key.strip()] = val.strip('"\'')
    
    if current_site and current_site.get('url'):
        sites.append(current_site)
    
    return sites


def generate_html(sites, custom_sites):
    """生成 HTML 页面。"""
    # 分类站点
    high_freq = [s for s in sites if s.get('tier') == 'high']
    medium_freq = [s for s in sites if s.get('tier') == 'medium']
    low_freq = [s for s in sites if s.get('tier') == 'low']
    
    # 统计
    total = len(sites) + len(custom_sites)
    high_count = len(high_freq)
    medium_count = len(medium_freq)
    low_count = len(low_freq)
    custom_count = len(custom_sites)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS 订阅源目录 - RSSForge</title>
    <style>
        :root {{
            --bg-color: #f5f5f5;
            --card-bg: #ffffff;
            --text-color: #333;
            --text-secondary: #666;
            --accent-color: #2563eb;
            --border-color: #e5e5e5;
            --badge-bg: #e0e7ff;
            --badge-text: #3730a3;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent-color);
        }}
        
        .stat-label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h2 {{
            font-size: 1.25rem;
        }}
        
        .badge {{
            background: var(--badge-bg);
            color: var(--badge-text);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        .feeds-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        
        .feed-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            transition: box-shadow 0.2s, border-color 0.2s;
        }}
        
        .feed-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: var(--accent-color);
        }}
        
        .feed-name {{
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--accent-color);
        }}
        
        .feed-url {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            word-break: break-all;
            margin-bottom: 0.5rem;
        }}
        
        .feed-meta {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            font-size: 0.75rem;
        }}
        
        .meta-tag {{
            background: var(--bg-color);
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            color: var(--text-secondary);
        }}
        
        .custom-badge {{
            background: #dcfce7;
            color: #166534;
        }}
        
        footer {{
            text-align: center;
            margin-top: 2rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        footer a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📡 RSS 订阅源目录</h1>
            <p class="subtitle">RSSForge 自动生成 · 更新时间: {update_time()}</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">总订阅源</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{high_count}</div>
                    <div class="stat-label">高频更新</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{medium_count}</div>
                    <div class="stat-label">中频更新</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{low_count}</div>
                    <div class="stat-label">低频更新</div>
                </div>
                {f'<div class="stat"><div class="stat-value">{custom_count}</div><div class="stat-label">自定义源</div></div>' if custom_count > 0 else ''}
            </div>
        </header>
'''
    
    # 高频站点
    if high_freq:
        html += f'''
        <div class="section">
            <div class="section-header">
                <h2>⚡ 高频更新</h2>
                <span class="badge">{len(high_freq)} 个站点</span>
            </div>
            <div class="feeds-grid">
'''
        for site in high_freq:
            name = site.get('name', site.get('url', '未知'))
            url = site.get('url', '')
            tier = site.get('tier', 'medium')
            interval = site.get('interval', 60)
            html += f'''
                <div class="feed-card">
                    <div class="feed-name">{escape_html(name)}</div>
                    <div class="feed-url">{escape_html(url)}</div>
                    <div class="feed-meta">
                        <span class="meta-tag">每 {interval} 分钟</span>
                        <span class="meta-tag">{tier}</span>
                    </div>
                </div>
'''
        html += '            </div>\n        </div>\n'
    
    # 中频站点
    if medium_freq:
        html += f'''
        <div class="section">
            <div class="section-header">
                <h2>📰 中频更新</h2>
                <span class="badge">{len(medium_freq)} 个站点</span>
            </div>
            <div class="feeds-grid">
'''
        for site in medium_freq:
            name = site.get('name', site.get('url', '未知'))
            url = site.get('url', '')
            tier = site.get('tier', 'medium')
            interval = site.get('interval', 60)
            html += f'''
                <div class="feed-card">
                    <div class="feed-name">{escape_html(name)}</div>
                    <div class="feed-url">{escape_html(url)}</div>
                    <div class="feed-meta">
                        <span class="meta-tag">每 {interval} 分钟</span>
                        <span class="meta-tag">{tier}</span>
                    </div>
                </div>
'''
        html += '            </div>\n        </div>\n'
    
    # 低频站点
    if low_freq:
        html += f'''
        <div class="section">
            <div class="section-header">
                <h2>📚 低频更新</h2>
                <span class="badge">{len(low_freq)} 个站点</span>
            </div>
            <div class="feeds-grid">
'''
        for site in low_freq:
            name = site.get('name', site.get('url', '未知'))
            url = site.get('url', '')
            tier = site.get('tier', 'low')
            interval = site.get('interval', 60)
            html += f'''
                <div class="feed-card">
                    <div class="feed-name">{escape_html(name)}</div>
                    <div class="feed-url">{escape_html(url)}</div>
                    <div class="feed-meta">
                        <span class="meta-tag">每 {interval} 分钟</span>
                        <span class="meta-tag">{tier}</span>
                    </div>
                </div>
'''
        html += '            </div>\n        </div>\n'
    
    # 自定义站点
    if custom_sites:
        html += f'''
        <div class="section">
            <div class="section-header">
                <h2>✨ 自定义源</h2>
                <span class="badge">{len(custom_sites)} 个站点</span>
            </div>
            <div class="feeds-grid">
'''
        for site in custom_sites:
            name = site.get('name', site.get('url', '未知'))
            url = site.get('url', '')
            interval = site.get('interval', 60)
            html += f'''
                <div class="feed-card">
                    <div class="feed-name">{escape_html(name)}</div>
                    <div class="feed-url">{escape_html(url)}</div>
                    <div class="feed-meta">
                        <span class="meta-tag">每 {interval} 分钟</span>
                        <span class="meta-tag custom-badge">自定义</span>
                    </div>
                </div>
'''
        html += '            </div>\n        </div>\n'
    
    html += f'''
        <footer>
            <p>由 <a href="https://github.com/gitfox-enter/rssforge">RSSForge</a> 驱动 · 自动更新</p>
        </footer>
    </div>
</body>
</html>'''
    
    return html


def escape_html(text):
    """转义 HTML 特殊字符。"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def update_time():
    """获取当前时间。"""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def main():
    """主函数。"""
    # 加载数据
    sites = load_sites_yaml()
    custom_sites = load_custom_sources()
    
    print(f"加载了 {len(sites)} 个订阅源 + {len(custom_sites)} 个自定义源")
    
    # 生成 HTML
    html = generate_html(sites, custom_sites)
    
    # 确保 feeds 目录存在
    feeds_dir = Path(__file__).parent / 'feeds'
    feeds_dir.mkdir(exist_ok=True)
    
    # 写入文件
    index_file = feeds_dir / 'index.html'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"生成完成: {index_file}")


if __name__ == '__main__':
    main()
