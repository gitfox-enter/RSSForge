#!/usr/bin/env python3
"""
停滞报警脚本 - 检查 feeds/ 目录最新更新时间，若超过阈值则创建 GitHub Issue。
用法: python3 stale_alert.py <repository> <github_token>
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

THRESHOLD_HOURS = 6


def get_latest_feed_time() -> int | None:
    """返回 feeds/ 最新提交的 Unix 时间戳，若无则返回 None"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", "feeds/"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        return int(output) if output else None
    except (ValueError, subprocess.TimeoutExpired):
        return None


def create_issue(repo: str, token: str, hours: int, now_str: str) -> str:
    """在 GitHub 仓库创建 Issue，返回 Issue URL 或错误消息"""
    body = (
        f"RSSForge 订阅源停滞检测\n\n"
        f"发现时间: {now_str}\n\n"
        f"异常: feeds/ 目录已超过 {hours} 小时无新内容。\n\n"
        f"建议:\n"
        f"1. 查看最近的 Crawl 和 Fast Check 运行日志\n"
        f"2. 检查 GitHub Actions 页面确认是否有报错\n"
        f"3. 如有错误，查看 RSSForge 文档站排障\n\n"
        f"---\n"
        f"此 Issue 由自动停滞检测创建"
    )

    payload = json.dumps({
        "title": "⚠️ RSS 订阅停滞告警",
        "body": body,
        "labels": ["automated", "stale-feed"],
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return f"Issue #{result['number']}: {result['html_url']}"
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        msg = err.get("message", "")
        if "already_exists" in msg.lower():
            return "跳过: 已有相同内容的 Issue"
        return f"跳过: {msg}"


def main() -> int:
    repo = os.environ.get("REPO") or sys.argv[1]
    token = os.environ.get("GITHUB_TOKEN") or sys.argv[2]

    latest_ts = get_latest_feed_time()
    if latest_ts is None:
        print("feeds/ 没有提交历史，跳过")
        return 0

    now_ts = int(subprocess.run(
        ["date", "+%s"], capture_output=True, text=True, timeout=5
    ).stdout.strip())
    elapsed = (now_ts - latest_ts) // 3600

    print(f"feeds/ 最新更新: {elapsed} 小时前")

    if elapsed <= THRESHOLD_HOURS:
        print(f"feeds 正常（<={THRESHOLD_HOURS} 小时），跳过报警")
        return 0

    print(f"::warning title=停滞报警::feeds/ 已 {elapsed} 小时未更新")

    now_str = subprocess.run(
        ["sh", "-c", "TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S'"],
        capture_output=True, text=True, timeout=5,
    ).stdout.strip()

    result = create_issue(repo, token, elapsed, now_str)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
