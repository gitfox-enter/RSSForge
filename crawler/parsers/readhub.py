# -*- coding: utf-8 -*-
"""ReadHub (readhub.cn) — 热门话题 (hot topics) via official public API.

readhub.cn/hot 是 Vue SPA，列表数据来自官方 JSON API：
    https://api.readhub.cn/topic/list?pageSize=N

本模块直接调用该 API 拉取热门话题并映射为 engine 的 article_items schema。
"""
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

READHUB_TOPIC_API = "https://api.readhub.cn/topic/list"
READHUB_TOPIC_URL = "https://readhub.cn/topic/{uid}"
READHUB_HOT_URL = "https://readhub.cn/hot"


def _normalize_time(iso_str: str) -> str:
    """ReadHub 时间为 ISO-8601 UTC（如 2026-07-06T02:16:08.945Z）。

    转为项目约定的 'YYYY-MM-DD HH:MM:SS'（Asia/Shanghai）字符串，
    以便 rss_feed._to_iso8601 正确解析并附加 UTC+8 时区。
    """
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        dt = dt.astimezone(timezone(timedelta(hours=8)))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return ''


def fetch_readhub_topic_api(page_size: int = 30) -> List[Dict[str, str]]:
    """拉取 ReadHub 热门话题，返回 article_items 列表。

    每条 item 字段：
        text    用于 RSS 标题与变更检测哈希
        url     话题页链接
        summary 话题摘要
        time    发布时间（Asia/Shanghai）
        id      话题 uid
        source  'ReadHub'
    """
    import requests
    from crawler.config import REQUEST_TIMEOUT
    from crawler.storage import get_random_ua

    items: List[Dict[str, str]] = []
    try:
        headers = {
            'User-Agent': get_random_ua(),
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': READHUB_HOT_URL,
        }
        resp = requests.get(
            READHUB_TOPIC_API,
            params={'pageSize': page_size},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("ReadHub API 请求失败: HTTP %s", resp.status_code)
            return items

        data = resp.json()
        topic_list = data.get('data', {}).get('items', [])
        for topic in topic_list:
            uid = topic.get('uid', '')
            title = (topic.get('title') or '').strip()
            if not title:
                continue
            summary = topic.get('summary') or ''
            pub = _normalize_time(topic.get('publishDate') or topic.get('createdAt') or '')
            items.append({
                'text': title,
                'title': title,
                'url': READHUB_TOPIC_URL.format(uid=uid) if uid else READHUB_HOT_URL,
                'summary': summary,
                'time': pub,
                'id': uid,
                'source': 'ReadHub',
            })
        logger.info("ReadHub 热门话题抓取成功: %d 条", len(items))
    except Exception as e:  # noqa: BLE001 - 单源失败不应中断整体抓取
        logger.warning("ReadHub API 请求异常: %s", e)
    return items


def parse_readhub_topic_items(soup: Any, base_url: str) -> List[Dict[str, str]]:
    """HTML 兜底解析（readhub.cn/hot 为 SPA，列表来自 API，这里返回空）。

    引擎在 readhub 策略分支中直接调用 fetch_readhub_topic_api，
    因此本函数仅作为 parser 注册占位，正常不产出。
    """
    return []
