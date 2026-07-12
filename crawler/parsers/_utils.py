# -*- coding: utf-8 -*-
"""Shared utilities for site parsers."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin

# ============================================================
# 预编译正则
# ============================================================

_RE_CHINESE = re.compile(r'[\u4e00-\u9fff]')


def _has_chinese(text: str, min_count: int = 2) -> bool:
    """检查文本中是否包含足够数量的中文字符。"""
    return len(_RE_CHINESE.findall(text)) >= min_count


def _is_valid_text(text: str, min_len: int = 4, max_len: int = 120) -> bool:
    """检查文本长度是否在有效范围内。"""
    return bool(text) and min_len <= len(text) <= max_len


def _add_item(items: List[Dict[str, str]], seen: Set[str],
              text: str, href: str, base_url: str = '',
              pub_date: str = '') -> bool:
    """去重、转换相对URL、追加条目到列表。

    Args:
        pub_date: 可选，条目在原文的发布时间（YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss）。

    Returns:
        True 如果条目被成功追加，False 表示已重复被跳过。
    """
    if not text or text in seen:
        return False
    seen.add(text)
    if base_url and href.startswith('/'):
        href = urljoin(base_url, href)
    item = {'text': text, 'url': href}
    if pub_date:
        item['pub_date'] = pub_date
    items.append(item)
    return True


# 通用导航/功能性文字集合 — 各站点 skip 列表的公共基础
COMMON_SKIP_WORDS: Set[str] = {
    '首页', '关于', '联系我们', '留言', '搜索', '登录', '注册',
    '下一页', '上一页', '返回顶部', '返回首页', '关于我们',
    '登录/注册', '找回密码', '立即注册', '收藏本站', '设为首页',
    '快捷导航', '更多', '最新', '热门', '分类', '标签',
    '回复', '删除', '举报', '推荐', '点赞', '评论', '浏览',
}


def _make_skip_set(*extra_words: str) -> Set[str]:
    """在 COMMON_SKIP_WORDS 基础上创建站点专用的过滤集合。"""
    return COMMON_SKIP_WORDS | set(extra_words)


def _mmdd_to_date(mmdd_str: str) -> str:
    """将 MM-DD 或 MM-DD HH:mm 格式转为 YYYY-MM-DD HH:00:00。

    年份按当前年；如果目标日期在当前日期之后，则回退一年
    （处理跨年场景，如 12-31 文章在一月初爬取）。
    """
    mmdd_str = mmdd_str.strip()
    now = datetime.now()
    year = now.year
    try:
        if ' ' in mmdd_str:
            date_part, time_part = mmdd_str.split(' ', 1)
            mm, dd = date_part.split('-', 1)
            dt = datetime(int(year), int(mm), int(dd))
        else:
            mm, dd = mmdd_str.split('-', 1)
            dt = datetime(int(year), int(mm), int(dd))
    except (ValueError, TypeError):
        return ''
    # 跨年回退
    if dt > now:
        dt = dt.replace(year=year - 1)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
