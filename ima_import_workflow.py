#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge -> ima 知识库导入工具

在 crawler/engine 采集完成后，读取 items_latest.json 并通过 ima API 导入知识库。
保留爬虫引擎的 hash_diff 增量机制，避免重复导入。
支持按 pubDate 时间过滤（DAYS 环境变量）和最大导入条数限制（MAX_ITEMS 环境变量）。
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

KB_ID = os.environ.get("IMA_KB_ID", "8UWnCJWk0DlQ15ppsKOIeyNofz8ZBOJVt7e9Taeu7bg=")
BASE = "https://ima.qq.com/openapi/wiki/v1"
CLIENT_ID = os.environ.get("IMA_CLIENT_ID")
API_KEY = os.environ.get("IMA_API_KEY")
DEFAULT_FOLDER_ID = os.environ.get("IMA_DEFAULT_FOLDER_ID", "")
LOG_FILE = os.environ.get("IMA_LOG_FILE", "ima_import.log")
IMPORTED_URLS_FILE = "imported_urls.json"

SITE_FOLDER_MAP = {}


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_site_folder_map():
    global SITE_FOLDER_MAP
    try:
        if os.path.exists("sites_to_folders.yaml"):
            import yaml
            with open("sites_to_folders.yaml", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                SITE_FOLDER_MAP = data.get("folders", {})
            log("已加载 %d 个站点文件夹映射" % len(SITE_FOLDER_MAP))
        else:
            log("sites_to_folders.yaml 不存在，将使用默认文件夹")
    except Exception as e:
        log("加载失败: %s" % e)


def get_folder_id(site_name):
    return SITE_FOLDER_MAP.get(site_name, DEFAULT_FOLDER_ID)


def call_api(path, payload, timeout=120):
    if not CLIENT_ID or not API_KEY:
        log("错误: 缺少 IMA_CLIENT_ID 或 IMA_API_KEY")
        return {"code": -1, "error": "Missing credentials"}
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "ima-openapi-clientid": CLIENT_ID,
            "ima-openapi-apikey": API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        return {"code": e.code, "error": body}
    except Exception as e:
        return {"error": str(e)}


def load_imported_urls():
    if os.path.exists(IMPORTED_URLS_FILE):
        try:
            with open(IMPORTED_URLS_FILE, encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_imported_urls(urls):
    with open(IMPORTED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(urls), f, ensure_ascii=False)


def parse_pubdate(pubdate_str):
    """解析 RFC 2822 日期字符串，返回 datetime 对象；失败返回 None"""
    if not pubdate_str:
        return None
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(pubdate_str)
        return parsed
    except Exception:
        try:
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
            ]:
                try:
                    return datetime.strptime(pubdate_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        except Exception:
            pass
    return None


def get_new_items(all_items, imported_urls, max_items=200, days=None):
    new_items = []
    cutoff = None
    if days is not None and days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        log("时间过滤: 只保留最近 %d 天内的内容 (截止 %s)" % (days, cutoff.strftime("%Y-%m-%d %H:%M:%S")))

    for item in all_items:
        url = item.get("link", item.get("url", ""))
        if not url or url in imported_urls:
            continue

        # 时间过滤
        if cutoff is not None:
            pubdate_str = item.get("pubDate", "")
            item_date = parse_pubdate(pubdate_str)
            if item_date is not None and item_date < cutoff:
                continue

        new_items.append(item)
        if len(new_items) >= max_items:
            break

    if cutoff is not None:
        log("时间过滤后: %d 条 (共 %d 条在时间范围内)" % (len(new_items), len(all_items)))
    return new_items


def import_items(new_items):
    if not new_items:
        log("没有新内容需要导入")
        return 0, 0

    imported_urls = load_imported_urls()
    total_imported = 0
    total_failed = 0

    by_folder = {}
    for item in new_items:
        source = item.get("source", item.get("site_name", ""))
        folder_id = get_folder_id(source)
        by_folder.setdefault(folder_id, []).append(item)

    for folder_id, items in by_folder.items():
        urls = [item.get("link", item.get("url", "")) for item in items]
        log("导入文件夹 %s: %d 篇" % (folder_id or "默认", len(items)))

        for i in range(0, len(urls), 10):
            batch = urls[i:i + 10]
            res = call_api("/import_urls", {
                "knowledge_base_id": KB_ID,
                "folder_id": folder_id,
                "urls": batch,
            }, timeout=120)

            if res.get("code") == 0:
                results = res.get("data", {}).get("results", {})
                for u in batch:
                    r = results.get(u, {})
                    if r.get("ret_code") == 0:
                        total_imported += 1
                        imported_urls.add(u)
                    else:
                        total_failed += 1
                        log("  FAIL: %s -> %s" % (u, str(r)[:200]))
            else:
                ok = False
                for attempt in range(1, 4):
                    time.sleep(3)
                    res = call_api("/import_urls", {
                        "knowledge_base_id": KB_ID,
                        "folder_id": folder_id,
                        "urls": batch,
                    }, timeout=120)
                    if res.get("code") == 0:
                        ok = True
                        results = res.get("data", {}).get("results", {})
                        for u in batch:
                            r = results.get(u, {})
                            if r.get("ret_code") == 0:
                                total_imported += 1
                                imported_urls.add(u)
                            else:
                                total_failed += 1
                        break
                if not ok:
                    total_failed += len(batch)
                    log("  BATCH FAILED: %s" % batch[0])
            time.sleep(1.5)
        log("  文件夹导入完成: %d 篇" % len(items))

    save_imported_urls(imported_urls)
    return total_imported, total_failed


def main():
    log("=" * 60)
    log("RSSForge -> ima 知识库导入")
    log("=" * 60)

    load_site_folder_map()

    # 读取环境变量
    max_items = int(os.environ.get("MAX_ITEMS", "200"))
    days = int(os.environ.get("DAYS", "0"))
    if days <= 0:
        days = None  # 不限时间

    log("配置: MAX_ITEMS=%s, DAYS=%s" % (max_items, days or "不限"))

    items_file = "items_latest.json"
    if not os.path.exists(items_file):
        log("未找到 %s，尝试读取 items.json" % items_file)
        items_file = "items.json"

    if not os.path.exists(items_file):
        log("未找到数据文件，跳过导入")
        return

    with open(items_file, encoding="utf-8") as f:
        all_items = json.load(f)

    if not isinstance(all_items, list):
        all_items = all_items.get("items", all_items.get("articles", []))

    log("总计 %d 条待处理" % len(all_items))

    imported_urls = load_imported_urls()
    log("已有 %d 条已导入 URL 记录" % len(imported_urls))

    new_items = get_new_items(all_items, imported_urls, max_items=max_items, days=days)
    log("新内容: %d 条" % len(new_items))

    if new_items:
        imported, failed = import_items(new_items)
        log("导入汇总: 成功 %d, 失败 %d" % (imported, failed))
    else:
        log("无新内容，跳过导入")

    log("=" * 60)


if __name__ == "__main__":
    main()
