#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSSForge -> ima 知识库导入工具

在 crawler/engine 采集完成后，读取 items_latest.json 并通过 ima API 导入知识库。
保留爬虫引擎的 hash_diff 增量机制，避免重复导入。
支持按 pubDate 时间过滤（DAYS 环境变量）和最大导入条数限制（MAX_ITEMS 环境变量）。

2026-08-23 变更：不再按站点分发到各自文件夹（sites_to_folders.yaml 不再使用），
全部内容导入知识库下指定名称的子文件夹（默认 "2026."，可用 IMA_TARGET_FOLDER_NAME 覆盖）。默认知识库为「羊毛网站线报」（IMA_KB_ID 可覆盖）。

2026-08-25 变更：
  1) 默认目标文件夹改为 "2026."（旧的 "2026" 文件夹请手动在 ima 中删除）。
  2) 新增 MIN_CONTENT_LEN 阈值（默认 200 字符）：剔除正文过短的"线报/优惠"类条目，
     避免 ima 知识库因"内容太薄"导致解析失败。设 MIN_CONTENT_LEN=0 可关闭过滤。
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

KB_ID = os.environ.get("IMA_KB_ID", "Nq1Mwk9IL5jSjWWkpPPpOGqv3waXQm-Bv2RrnhrPW3s=")
BASE = "https://ima.qq.com/openapi/wiki/v1"
CLIENT_ID = os.environ.get("IMA_CLIENT_ID")
API_KEY = os.environ.get("IMA_API_KEY")
DEFAULT_FOLDER_ID = os.environ.get("IMA_DEFAULT_FOLDER_ID", "")
TARGET_FOLDER_NAME = os.environ.get("IMA_TARGET_FOLDER_NAME", "2026.")
LOG_FILE = os.environ.get("IMA_LOG_FILE", "ima_import.log")
IMPORTED_URLS_FILE = "imported_urls.json"
# 正文过短的条目（如纯线报/优惠）会被跳过，避免 ima 解析失败；设为 0 关闭过滤
MIN_CONTENT_LEN = int(os.environ.get("MIN_CONTENT_LEN", "200"))


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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


def find_folder_by_name(kb_id, name):
    """在知识库中查找指定名称的文件夹（media_type=99），返回 folder_id；找不到返回 None"""
    # 方法1: search_knowledge 按名称搜索（推荐）
    try:
        res = call_api("/search_knowledge", {
            "query": name,
            "knowledge_base_id": kb_id,
            "cursor": "",
        }, timeout=60)
        if res.get("code") == 0:
            info_list = res.get("data", {}).get("info_list", []) or res.get("info_list", [])
            for item in info_list:
                if item.get("media_type") == 99 and item.get("title") == name:
                    return item.get("media_id")
    except Exception as e:
        log("search_knowledge 查找失败: %s" % e)

    # 方法2: get_knowledge_list 浏览根目录
    try:
        res = call_api("/get_knowledge_list", {
            "knowledge_base_id": kb_id,
            "cursor": "",
            "limit": 50,
        }, timeout=60)
        if res.get("code") == 0:
            kl = res.get("data", {}).get("knowledge_list", []) or res.get("knowledge_list", [])
            for item in kl:
                if item.get("media_type") == 99 and item.get("title") == name:
                    return item.get("media_id")
    except Exception as e:
        log("get_knowledge_list 查找失败: %s" % e)

    return None


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
    """解析日期字符串，返回带时区的 datetime；失败返回 None。
    无时区的时间（如 engine 写入的 "2026-08-23 17:00:00"）按北京时间(UTC+8)处理。"""
    if not pubdate_str:
        return None
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(pubdate_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=8)))
        return parsed
    except Exception:
        pass
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %z",
    ]:
        try:
            dt = datetime.strptime(pubdate_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
            return dt
        except ValueError:
            continue
    return None


def get_item_time_str(item):
    """从条目中提取时间字符串（兼容 engine 的 time 字段与 RSS 的 pubDate 等）"""
    for key in ("pubDate", "pub_date", "time", "date", "published", "updated"):
        v = item.get(key)
        if v:
            return v
    return ""


def _strip_html(text):
    """去掉 HTML 标签 + 空白，返回纯文本（用于内容长度判断）"""
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(text))
    s = re.sub(r"\s+", "", s)
    return s


def get_new_items(all_items, imported_urls, max_items=200, days=None):
    """返回 (new_items, seen_urls)：new_items 为待导入条目，seen_urls 为本轮处理过的全部 URL（含被过滤的）"""
    new_items = []
    seen_urls = set()
    cutoff = None
    if days is not None and days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        log("时间过滤: 只保留最近 %d 天内的内容 (截止 %s)" % (days, cutoff.strftime("%Y-%m-%d %H:%M:%S")))
    # 无日期条目的兜底窗口：首次入库超过 3 天的视为旧内容，不再导入
    first_seen_cutoff = datetime.now(timezone.utc) - timedelta(days=3)

    skipped_old = 0
    skipped_no_date = 0
    skipped_thin = 0
    for item in all_items:
        url = item.get("link", item.get("url", ""))
        if not url:
            continue
        seen_urls.add(url)
        if url in imported_urls:
            continue

        # 时间过滤：以 engine 的 time 字段（发布时间，无则取爬取时间）为准
        if cutoff is not None:
            item_date = parse_pubdate(get_item_time_str(item))
            if item_date is None:
                # 完全无日期：用首次入库时间兜底，超 3 天视为旧内容跳过
                fs = parse_pubdate(item.get("first_seen_at", ""))
                if fs is None or fs < first_seen_cutoff:
                    skipped_no_date += 1
                    continue
            elif item_date < cutoff:
                skipped_old += 1
                continue

        # 内容长度过滤：剔除纯线报/优惠/超短内容（避免 ima 解析失败）
        if MIN_CONTENT_LEN > 0:
            desc = (
                item.get("description")
                or item.get("summary")
                or item.get("content")
                or item.get("content_text")
                or ""
            )
            text_len = len(_strip_html(desc))
            if text_len < MIN_CONTENT_LEN:
                skipped_thin += 1
                continue

        new_items.append(item)
        if len(new_items) >= max_items:
            break

    if cutoff is not None:
        log("时间过滤后: %d 条新内容 (跳过旧内容 %d 条, 跳过无日期 %d 条, 跳过短内容 %d 条, 共处理 %d 条)" % (
            len(new_items), skipped_old, skipped_no_date, skipped_thin, len(all_items)))
    elif skipped_thin > 0:
        log("内容过滤: 跳过短内容 %d 条 (阈值 %d 字符), 保留 %d 条" % (
            skipped_thin, MIN_CONTENT_LEN, len(new_items)))
    return new_items, seen_urls


def push_imported_urls_if_changed():
    """将 imported_urls.json 提交并推回仓库，保证下次运行可继续去重。
    仅在 git 环境（CI）中执行，失败仅告警不阻塞。"""
    try:
        import subprocess
        # 检查是否有变更
        rc = subprocess.run(["git", "status", "--porcelain", IMPORTED_URLS_FILE],
                            capture_output=True, text=True, timeout=30)
        if rc.returncode != 0 or not rc.stdout.strip():
            log("imported_urls.json 无变更，跳过 push")
            return
        # pull 再 push，避免并发冲突
        subprocess.run(["git", "pull", "--rebase", "origin", "main"],
                       capture_output=True, text=True, timeout=120)
        subprocess.run(["git", "add", IMPORTED_URLS_FILE], capture_output=True, timeout=30)
        subprocess.run(["git", "commit", "-m", "chore: 更新 imported_urls.json (ima 去重记录)"],
                       capture_output=True, timeout=30)
        prc = subprocess.run(["git", "push", "origin", "main"],
                             capture_output=True, text=True, timeout=120)
        if prc.returncode == 0:
            log("imported_urls.json 已推回仓库 (%d 条记录)" % len(load_imported_urls()))
        else:
            log("警告: imported_urls.json push 失败: %s" % prc.stderr.strip()[-300:])
    except Exception as e:
        log("警告: imported_urls.json 持久化失败（不影响本次导入）: %s" % e)


def import_items(new_items, folder_id):
    if not new_items:
        log("没有新内容需要导入")
        return 0, 0

    imported_urls = load_imported_urls()
    total_imported = 0
    total_failed = 0

    urls = [item.get("link", item.get("url", "")) for item in new_items]
    log("导入文件夹 %s: %d 篇" % (folder_id or "知识库根目录", len(urls)))

    for i in range(0, len(urls), 10):
        batch = urls[i:i + 10]
        payload = {
            "knowledge_base_id": KB_ID,
            "urls": batch,
        }
        if folder_id:
            payload["folder_id"] = folder_id
        res = call_api("/import_urls", payload, timeout=120)

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
                res = call_api("/import_urls", payload, timeout=120)
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
    log("  导入完成: 成功 %d, 失败 %d" % (total_imported, total_failed))

    save_imported_urls(imported_urls)
    return total_imported, total_failed


def main():
    log("=" * 60)
    log("RSSForge -> ima 知识库导入")
    log("=" * 60)

    # 读取环境变量
    max_items = int(os.environ.get("MAX_ITEMS", "200"))
    days = int(os.environ.get("DAYS", "0"))
    if days <= 0:
        days = None  # 不限时间

    log("配置: MAX_ITEMS=%s, DAYS=%s, 目标文件夹='%s', MIN_CONTENT_LEN=%d" % (
        max_items, days or "不限", TARGET_FOLDER_NAME, MIN_CONTENT_LEN))

    # 查找目标文件夹：优先用环境变量指定的 folder_id，否则按名称查找
    target_folder_id = os.environ.get("IMA_TARGET_FOLDER_ID", "")
    if not target_folder_id:
        target_folder_id = find_folder_by_name(KB_ID, TARGET_FOLDER_NAME)
        if target_folder_id:
            log("已找到目标文件夹 '%s': %s" % (TARGET_FOLDER_NAME, target_folder_id))
        else:
            target_folder_id = DEFAULT_FOLDER_ID
            log("警告: 未找到名为 '%s' 的文件夹，回退到默认文件夹 %s (若为空则导入知识库根目录)" % (
                TARGET_FOLDER_NAME, target_folder_id or "根目录"))
    else:
        log("使用环境变量指定的目标文件夹: %s" % target_folder_id)

    items_file = "items_latest.json"
    if not os.path.exists(items_file):
        log("未找到 %s，尝试读取 items.json" % items_file)
        items_file = "items.json"

    if not os.path.exists(items_file):
        log("未找到数据文件，跳过导入")
        return

    # 首次运行（imported_urls.json 不存在）时收紧时间窗口到 2 天：
    # 历史从未做过 URL 去重，items_latest.json 里 60 天窗口的旧链接可能已被反复导入，
    # 首轮只导入最近 2 天内被抓取的内容，避免再次灌入老文章。
    first_run = not os.path.exists(IMPORTED_URLS_FILE)
    if first_run and days is not None:
        log("首次运行（无 imported_urls.json）：时间窗口收紧为 2 天，避免导入历史旧链接")
        days = min(days, 2)

    with open(items_file, encoding="utf-8") as f:
        all_items = json.load(f)

    if not isinstance(all_items, list):
        all_items = all_items.get("items", all_items.get("articles", []))

    log("总计 %d 条待处理" % len(all_items))

    imported_urls = load_imported_urls()
    log("已有 %d 条已导入 URL 记录" % len(imported_urls))

    new_items, seen_urls = get_new_items(all_items, imported_urls, max_items=max_items, days=days)
    log("新内容: %d 条 (本轮处理 URL %d 条)" % (len(new_items), len(seen_urls)))

    if new_items:
        imported, failed = import_items(new_items, target_folder_id)
        log("导入汇总: 成功 %d, 失败 %d" % (imported, failed))
    else:
        log("无新内容，跳过导入")

    # 首次运行（无历史去重记录）时：把所有见过的 URL 记入 imported_urls，
    # 避免下轮把被时间过滤跳过的老文章 URL 再捞回来处理
    if not os.path.exists(IMPORTED_URLS_FILE):
        merged = load_imported_urls() | seen_urls
        save_imported_urls(merged)
        log("首次运行：已记录 %d 条 URL 去重基准" % len(merged))

    push_imported_urls_if_changed()

    log("=" * 60)


if __name__ == "__main__":
    main()
