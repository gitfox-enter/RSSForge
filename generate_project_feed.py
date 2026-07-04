#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge 项目更新 Feed 生成器

从 git log 提取项目变更（feat/fix/chore/docs/重构），生成 Atom 格式的 RSS feed。
输出: feeds/project-updates.xml

分类规则:
  - feat:     新功能
  - fix:      Bug 修复
  - chore:    维护/清理
  - docs:     文档
  - 重构:     重构
  - hotfix:   紧急修复
  - 自动更新:  爬取自动提交（聚合为一条）
  - 快速更新:  fast_check 自动提交（聚合为一条）
  - 状态更新:  状态文件自动提交（聚合为一条）
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
    # 自动更新/快速更新/状态更新 是前缀匹配
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


def _aggregate_auto_commits(commits: List[Dict]) -> List[Dict]:
    """聚合自动提交（同一天的自动更新/快速更新/状态更新合并为一条）。"""
    by_day_type = defaultdict(list)
    non_auto = []

    for c in commits:
        cat = _classify_commit(c['subject'])
        if cat in ('自动更新', '快速更新', '状态更新'):
            # 按日期+类型分组
            date_key = c['date'][:10]  # YYYY-MM-DD
            by_day_type[(date_key, cat)].append(c)
        else:
            non_auto.append(c)

    aggregated = []
    for (date_key, cat), group in by_day_type.items():
        first = group[0]
        last = group[-1]
        count = len(group)
        label, emoji = CATEGORIES[cat]

        # 提取最新条目数等信息
        sample_subjects = [g['subject'] for g in group[:3]]

        aggregated.append({
            'sha': first['sha'],
            'author': 'github-actions[bot]',
            'date': last['date'],  # 用最后一条的时间
            'subject': f'{emoji} {label} x{count} ({date_key})',
            'detail': f'当日{label}共 {count} 次提交。示例:\n' + '\n'.join(f'  - {s}' for s in sample_subjects),
            'category': cat,
            'is_aggregated': True,
            'commit_url': f'{REPO_URL}/commit/{first["sha"]}',
        })

    # 合并并按时间倒序排序
    for c in non_auto:
        cat = _classify_commit(c['subject'])
        c['category'] = cat
        c['detail'] = _extract_detail(c['subject'], cat)
        c['is_aggregated'] = False
        c['commit_url'] = f'{REPO_URL}/commit/{c["sha"]}'
        if cat in CATEGORIES:
            label, emoji = CATEGORIES[cat]
            c['subject'] = f'{emoji} {c["detail"]}'

    all_entries = aggregated + non_auto
    all_entries.sort(key=lambda x: x['date'], reverse=True)
    return all_entries[:MAX_ENTRIES]


def _parse_git_date(date_str: str) -> datetime:
    """解析 git iso 日期: 2026-07-04 03:07:23 +0800"""
    try:
        # 去掉时区偏移的冒号: +08:00 -> +0800
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
    ET.SubElement(root, f'{{{ns}}}subtitle').text = '项目开发进展、Bug修复与维护记录'
    ET.SubElement(root, f'{{{ns}}}id').text = f'{SITE_URL}project-updates'
    ET.SubElement(root, f'{{{ns}}}updated').text = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    author = ET.SubElement(root, f'{{{ns}}}author')
    ET.SubElement(author, f'{{{ns}}}name').text = 'RSSForge'
    ET.SubElement(root, f'{{{ns}}}link').set('href', SITE_URL)
    ET.SubElement(root, f'{{{ns}}}link').set('rel', 'self', )
    ET.SubElement(root, f'{{{ns}}}link').set('href', f'{SITE_URL}feeds/project-updates.xml')

    for entry in entries:
        entry_el = ET.SubElement(root, f'{{{ns}}}entry')
        ET.SubElement(entry_el, f'{{{ns}}}title').text = entry['subject']
        ET.SubElement(entry_el, f'{{{ns}}}id').text = _entry_id(entry)

        dt = _parse_git_date(entry['date'])
        dt_iso = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        # 格式化时区: +0800 -> +08:00
        dt_iso = re.sub(r'([+-])(\d{2})(\d{2})$', r'\1\2:\3', dt_iso)
        ET.SubElement(entry_el, f'{{{ns}}}updated').text = dt_iso
        ET.SubElement(entry_el, f'{{{ns}}}published').text = dt_iso

        link = ET.SubElement(entry_el, f'{{{ns}}}link')
        link.set('href', entry['commit_url'])

        cat = entry.get('category', 'other')
        if cat in CATEGORIES:
            label, _ = CATEGORIES[cat]
            ET.SubElement(entry_el, f'{{{ns}}}category').set('term', label)

        # 内容
        detail = entry.get('detail', entry['subject'])
        content_parts = [f'<p>{detail}</p>']
        content_parts.append(f'<p>提交: <a href="{entry["commit_url"]}">{entry["sha"][:8]}</a></p>')
        if entry.get('is_aggregated'):
            content_parts.append('<p><em>（聚合提交，点击查看详情）</em></p>')
        content_el = ET.SubElement(entry_el, f'{{{ns}}}content')
        content_el.set('type', 'html')
        content_el.text = '\n'.join(content_parts)

    # 写入文件
    os.makedirs(FEEDS_DIR, exist_ok=True)
    tmp_path = OUTPUT_FILE + '.tmp'
    rough = ET.tostring(root, encoding='unicode')
    pretty = minidom.parseString(rough).toprettyxml(indent='  ', encoding='utf-8')

    with open(tmp_path, 'wb') as f:
        f.write(pretty)
    os.replace(tmp_path, OUTPUT_FILE)

    print(f"✓ 项目更新 feed 生成: {len(entries)} 条 -> {OUTPUT_FILE}")
    return {'entries': len(entries)}


if __name__ == '__main__':
    result = generate_feed()
    print(f"\n完成: {result}")
