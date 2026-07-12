#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 项目更新 Feed 生成器

从 git log 提取项目变更，生成 Atom 格式的 RSS feed。
输出: feeds/project-updates.xml

核心功能：
  - 新增订阅源时，feed 条目包含订阅链接（https://gitfox-enter.github.io/RSSForge/feeds/xxx.xml）
  - 其他变更（fix/chore/docs）正常展示
  - 自动提交（爬取/fast_check/状态）聚合展示
"""

import os
import re
import subprocess
import hashlib
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

SITE_URL = "https://gitfox-enter.github.io/RSSForge/"
REPO_URL = "https://github.com/gitfox-enter/RSSForge"
FEEDS_DIR = "feeds"
OUTPUT_FILE = os.path.join(FEEDS_DIR, "project-updates.xml")
SITES_YAML = "sites.yaml"
MAX_ENTRIES = 50

# Commit 分类
CATEGORIES = {
    'feat': ('新功能', '🎉'),
    'fix': ('Bug修复', '🔧'),
    'hotfix': ('紧急修复', '🔥'),
    'chore': ('维护清理', '🧹'),
    'docs': ('文档', '📝'),
    '重构': ('重构', '♻️'),
    '自动更新': ('爬取更新', '📡'),
    '快速更新': ('线报更新', '⚡'),
    '状态更新': ('状态同步', '📊'),
}


def _load_sites_yaml() -> Dict[str, Dict]:
    """加载 sites.yaml，返回 {slug: site_info} 映射。

    不依赖 PyYAML，用正则解析。
    """
    sites = {}
    try:
        with open(SITES_YAML, 'r', encoding='utf-8') as f:
            content = f.read()
        # 匹配 url: "xxx" 和后续的 name: xxx
        # sites.yaml 格式：- url: "https://..."  后面跟着 name: 站点名
        url_pattern = re.compile(r'url:\s*"([^"]+)"')
        name_pattern = re.compile(r'name:\s*(\S+)')
        
        # 按行扫描，找到 url 行后找最近的 name 行
        lines = content.split('\n')
        current_url = None
        for line in lines:
            url_match = url_pattern.search(line)
            if url_match and line.strip().startswith('- url:') or (url_match and '- url:' in line):
                current_url = url_match.group(1)
            elif current_url and 'name:' in line:
                name_match = name_pattern.search(line)
                if name_match:
                    name = name_match.group(1)
                    slug = _url_to_slug(current_url)
                    sites[slug] = {
                        'name': name,
                        'url': current_url,
                        'feed_url': f'{SITE_URL}feeds/{slug}.xml',
                    }
                    current_url = None
        return sites
    except Exception as e:
        print(f"加载 sites.yaml 失败: {e}")
        return {}


def _url_to_slug(url: str) -> str:
    """从 URL 生成 feed 文件名 slug。

    与 crawler/config.py 中 SOURCE_NAME_MAP 的逻辑保持一致。
    """
    # 去掉协议
    domain = re.sub(r'^https?://', '', url)
    # 去掉路径
    domain = domain.split('/')[0]
    # 去掉 www.
    domain = domain.replace('www.', '')
    # 去掉端口
    domain = domain.split(':')[0]
    return domain


def _get_git_commits(since_days: int = 30) -> List[Dict]:
    """从 git log 提取提交记录。"""
    since_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime('%Y-%m-%d')
    try:
        result = subprocess.run(
            ['git', 'log', '--all', f'--since={since_date}',
             '--format=%H|%an|%ad|%s', '--date=iso'],
            capture_output=True, text=True, timeout=30
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) != 4:
                continue
            sha, author, date_str, subject = parts
            commits.append({
                'sha': sha,
                'author': author,
                'date': date_str.strip(),
                'subject': subject.strip(),
            })
        return commits
    except Exception as e:
        print(f"git log 失败: {e}")
        return []


def _classify_commit(subject: str) -> str:
    """分类 commit message。"""
    for prefix in CATEGORIES:
        if subject.startswith(prefix + ':') or subject.startswith(prefix + '：'):
            return prefix
        if subject.startswith(prefix):
            return prefix
    if '自动更新' in subject:
        return '自动更新'
    if '快速更新' in subject:
        return '快速更新'
    if '状态更新' in subject:
        return '状态更新'
    return 'other'


def _extract_detail(subject: str, category: str) -> str:
    """提取 commit message 的描述部分。"""
    for prefix in CATEGORIES:
        if subject.startswith(prefix + ':'):
            return subject[len(prefix) + 1:].strip()
        if subject.startswith(prefix + '：'):
            return subject[len(prefix) + 1:].strip()
    return subject


def _extract_new_sources(subject: str, detail: str) -> List[Dict]:
    """从 commit message 中提取新增的订阅源信息。

    支持格式：
      - feat: 新增订阅源 线报酷 (xianbao.icu)
      - feat: 新增订阅源 线报酷、线报ICU
      - feat: 新增 2 个订阅源：站点A、站点B

    返回 [{'name': '线报酷', 'slug': 'xian-bao-ku'}, ...]
    slug 使用 slugify（拼音化），与实际 feed 文件名一致。
    """
    sources = []

    # 格式1: 新增订阅源 XXX (domain.com) — 域名已知，用站点名生成 slug
    pattern1 = re.compile(r'新增订阅源\s+(.+?)\s*\(([^)]+)\)')
    for m in pattern1.finditer(subject + ' ' + detail):
        name = m.group(1).strip()
        domain = m.group(2).strip()
        slug = _name_to_slug_guess(name)
        sources.append({'name': name, 'slug': slug, 'domain': domain})

    # 格式2: 新增订阅源 XXX（没有域名信息）
    if not sources:
        pattern2 = re.compile(r'新增订阅源\s+(.+)')
        m2 = pattern2.search(subject + ' ' + detail)
        if m2:
            name_str = m2.group(1).strip()
            for part in re.split(r'[、,，和]', name_str):
                part = part.strip()
                if part:
                    slug = _name_to_slug_guess(part)
                    sources.append({'name': part, 'slug': slug, 'domain': ''})

    return sources


def _build_name_to_slug_map() -> Dict[str, str]:
    """从 feeds/ 目录的 XML 文件中提取 title→slug 映射。

    feed XML 的 <title> 格式：'站点名 - RSSForge'
    """
    mapping = {}
    if not os.path.isdir(FEEDS_DIR):
        return mapping
    try:
        import xml.etree.ElementTree as ET
        for f in os.listdir(FEEDS_DIR):
            if not f.endswith('.xml') or f == 'project-updates.xml':
                continue
            slug = f[:-4]
            tree = ET.parse(os.path.join(FEEDS_DIR, f))
            root = tree.getroot()
            title_elem = root.find('.//{*}title')
            if title_elem is not None and title_elem.text:
                # title 格式: '站点名 - RSSForge'
                name = title_elem.text.split(' - RSSForge')[0].strip()
                if name:
                    mapping[name] = slug
    except Exception:
        pass
    return mapping


def _name_to_slug_guess(name: str) -> str:
    """根据站点名生成 feed 文件 slug。

    与 common.py 的 slugify 保持一致：中文转拼音，非 ASCII 字符转连字符。
    """
    # 尝试用 pypinyin 转换中文（GitHub Actions 环境可用）
    try:
        from pypinyin import lazy_pinyin, Style
        parts = lazy_pinyin(name, style=Style.NORMAL)
        slug = '-'.join(parts)
    except ImportError:
        # 本地环境无 pypinyin：从已有 feed XML 中读 title 匹配
        name_map = _build_name_to_slug_map()
        if name in name_map:
            return name_map[name]
        slug = name

    # 保留字母、数字、连字符
    slug = re.sub(r'[^a-zA-Z0-9\-]', '-', slug)
    slug = re.sub(r'-{2,}', '-', slug)
    slug = slug.strip('-')
    return slug or 'unknown'


def _aggregate_auto_commits(commits: List[Dict]) -> List[Dict]:
    """聚合自动提交（同一天的自动更新/快速更新/状态更新合并为一条）。"""
    by_day_type = defaultdict(list)
    non_auto = []

    for c in commits:
        cat = _classify_commit(c['subject'])
        if cat in ('自动更新', '快速更新', '状态更新'):
            date_key = c['date'][:10]
            by_day_type[(date_key, cat)].append(c)
        else:
            non_auto.append(c)

    aggregated = []
    for (date_key, cat), group in by_day_type.items():
        first = group[0]
        last = group[-1]
        count = len(group)
        label, emoji = CATEGORIES[cat]

        sample_subjects = [g['subject'] for g in group[:3]]

        aggregated.append({
            'sha': first['sha'],
            'author': 'github-actions[bot]',
            'date': last['date'],
            'subject': f'{emoji} {label} x{count} ({date_key})',
            'detail': f'当日{label}共 {count} 次提交。示例:\n' + '\n'.join(f'  - {s}' for s in sample_subjects),
            'category': cat,
            'is_aggregated': True,
            'commit_url': f'{REPO_URL}/commit/{first["sha"]}',
            'new_sources': [],
        })

    for c in non_auto:
        cat = _classify_commit(c['subject'])
        c['category'] = cat
        c['detail'] = _extract_detail(c['subject'], cat)
        c['is_aggregated'] = False
        c['commit_url'] = f'{REPO_URL}/commit/{c["sha"]}'
        c['new_sources'] = _extract_new_sources(c['subject'], c.get('detail', ''))
        if cat in CATEGORIES:
            label, emoji = CATEGORIES[cat]
            c['subject'] = f'{emoji} {c["detail"]}'

    all_entries = aggregated + non_auto
    all_entries.sort(key=lambda x: x['date'], reverse=True)
    return all_entries[:MAX_ENTRIES]


def _parse_git_date(date_str: str) -> datetime:
    """解析 git iso 日期: 2026-07-04 03:07:23 +0800"""
    try:
        clean = re.sub(r'([+-]\d{2}):(\d{2})$', r'\1\2', date_str)
        dt = datetime.strptime(clean, '%Y-%m-%d %H:%M:%S %z')
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def _entry_id(entry: Dict) -> str:
    """生成稳定的 entry ID。"""
    if entry.get('is_aggregated'):
        raw = f"{entry['sha']}-{entry['subject']}"
    else:
        raw = entry['sha']
    return 'tag:rssforge,' + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_content_html(entry: Dict) -> str:
    """构建 entry 的 HTML 内容。

    对于新增订阅源的 commit，包含订阅链接。
    """
    detail = entry.get('detail', entry['subject'])
    parts = [f'<p>{detail}</p>']

    # 如果是新增订阅源，展示订阅链接
    new_sources = entry.get('new_sources', [])
    if new_sources:
        parts.append('<hr/>')
        parts.append('<p><strong>📢 新增订阅源：</strong></p>')
        parts.append('<ul>')
        for src in new_sources:
            name = src['name']
            slug = src['slug']
            feed_url = f'{SITE_URL}feeds/{slug}.xml'
            parts.append(
                f'<li><strong>{name}</strong><br/>'
                f'订阅地址: <a href="{feed_url}">{feed_url}</a></li>'
            )
        parts.append('</ul>')
        parts.append('<p>将以上链接添加到你的 RSS 阅读器即可订阅。</p>')

    parts.append(f'<p>提交: <a href="{entry["commit_url"]}">{entry["sha"][:8]}</a></p>')
    if entry.get('is_aggregated'):
        parts.append('<p><em>（聚合提交，点击查看详情）</em></p>')

    return '\n'.join(parts)


def generate_feed() -> Dict:
    """生成项目更新 Atom feed。"""
    commits = _get_git_commits(since_days=30)
    if not commits:
        print("无 git 提交记录")
        return {'entries': 0}

    entries = _aggregate_auto_commits(commits)

    # 构建 Atom XML
    ns = 'http://www.w3.org/2005/Atom'
    ET.register_namespace('', ns)
    root = ET.Element(f'{{{ns}}}feed')

    ET.SubElement(root, f'{{{ns}}}title').text = 'RSSForge 项目更新'
    ET.SubElement(root, f'{{{ns}}}subtitle').text = '新增订阅源通告、项目开发进展与维护记录'
    ET.SubElement(root, f'{{{ns}}}id').text = f'{SITE_URL}project-updates'
    ET.SubElement(root, f'{{{ns}}}updated').text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    author = ET.SubElement(root, f'{{{ns}}}author')
    ET.SubElement(author, f'{{{ns}}}name').text = 'RSSForge'
    ET.SubElement(root, f'{{{ns}}}link').set('href', SITE_URL)
    ET.SubElement(root, f'{{{ns}}}link').set('rel', 'self')
    ET.SubElement(root, f'{{{ns}}}link').set('href', f'{SITE_URL}feeds/project-updates.xml')

    for entry in entries:
        entry_el = ET.SubElement(root, f'{{{ns}}}entry')
        ET.SubElement(entry_el, f'{{{ns}}}title').text = entry['subject']
        ET.SubElement(entry_el, f'{{{ns}}}id').text = _entry_id(entry)

        dt = _parse_git_date(entry['date'])
        dt_iso = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        dt_iso = re.sub(r'([+-])(\d{2})(\d{2})$', r'\1\2:\3', dt_iso)
        ET.SubElement(entry_el, f'{{{ns}}}updated').text = dt_iso
        ET.SubElement(entry_el, f'{{{ns}}}published').text = dt_iso

        link = ET.SubElement(entry_el, f'{{{ns}}}link')
        link.set('href', entry['commit_url'])

        cat = entry.get('category', 'other')
        if cat in CATEGORIES:
            label, _ = CATEGORIES[cat]
            ET.SubElement(entry_el, f'{{{ns}}}category').set('term', label)

        content_html = _build_content_html(entry)
        content_el = ET.SubElement(entry_el, f'{{{ns}}}content')
        content_el.set('type', 'html')
        content_el.text = content_html

    # 回填已有订阅源的 RSS feed 链接（供 RSS 阅读器自动发现）
    # 从已有 feed XML 提取 name→slug 映射，在 project-updates feed 中添加 alternate link
    name_slug_map = _build_name_to_slug_map()
    for name, slug in name_slug_map.items():
        feed_link = ET.SubElement(root, f'{{{ns}}}link')
        feed_link.set('rel', 'alternate')
        feed_link.set('type', 'application/rss+xml')
        feed_link.set('title', name)
        feed_link.set('href', f'{SITE_URL}feeds/{slug}.xml')

    # 写入文件
    os.makedirs(FEEDS_DIR, exist_ok=True)
    tmp_path = OUTPUT_FILE + '.tmp'
    rough = ET.tostring(root, encoding='unicode')
    pretty = minidom.parseString(rough).toprettyxml(indent='  ', encoding='utf-8')

    with open(tmp_path, 'wb') as f:
        f.write(pretty)
    os.replace(tmp_path, OUTPUT_FILE)

    # 统计新增源数量
    total_new_sources = sum(len(e.get('new_sources', [])) for e in entries)
    print(f"✓ 项目更新 feed 生成: {len(entries)} 条 -> {OUTPUT_FILE}")
    if total_new_sources:
        print(f"  含 {total_new_sources} 个新订阅源通告")
    return {'entries': len(entries), 'new_sources': total_new_sources}


if __name__ == '__main__':
    result = generate_feed()
    print(f"\n完成: {result}")
