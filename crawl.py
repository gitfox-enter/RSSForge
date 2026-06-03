#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 多站点更新监控系统
功能：爬取46个站点 → MD5比对检测更新 → 163邮箱SMTP推送 → 本地备份归档
时间：每4小时执行一次（00:00, 04:00, 08:00, 12:00, 16:00, 20:00）
时区：Asia/Shanghai（北京时间）
"""

import os
import sys
import time
import hashlib
import requests
import smtplib
import warnings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import json
import subprocess

# 忽略 BeautifulSoup 的 XML 当 HTML 解析警告
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ============================================================
# 配置区域
# ============================================================

# 46个监控站点完整列表
MONITOR_SITES = [
    "https://xianbaomi.com/",
    "http://www.0818tuan.com/",
    "http://79tao.linejia.com/",
    "https://www.daydayzhuan.com/",
    "https://cjx8.com/",
    "https://907k.cn/",
    "https://ym2.cc/",
    "https://b1.ymxianbao.cn/",
    "https://www.007ymd.com/",
    "http://news.ixbk.net/",
    "https://www.zhuanyes.com/xianbao/",
    "https://www.iqshw.com/",
    "https://www.huodong5.com/",
    "https://www.yxssp.com/",
    "https://www.wobangzhao.com/",
    "https://www.kxdao.net/forum-42-1.html",
    "https://www.baicaio.com/",
    "https://yangmao.wang/",
    "https://www.12345pro.com/",
    "https://news.ixbk.fun/",
    "https://www.h6room.com/",
    "https://www.ithome.com/zt/xijiayi",
    "https://free.apprcn.com/",
    "https://www.lsapk.com/",
    "https://www.ghxi.com/category/all",
    "https://www.appinn.com/",
    "https://www.423down.com/",
    "https://foxirj.com/",
    "https://store.steampowered.com/search/?specials=1&os=win",
    "https://www.gog.com/partner/free_games",
    "https://store.steampowered.com/",
    "https://www.ziyuanting.com/",
    "https://www.wycad.com/",
    "https://www.ddooo.com/",
    "https://www.onlinedown.net/",
    "https://www.downxia.com/",
    "https://www.ypojie.com/",
    "https://www.52hb.com/forum.php",
    "https://m.hybase.com/",
    "https://xzba.cc/",
    "https://pc.qq.com/category/rank.html",
    "https://store.epicgames.com/zh-CN/free-games",
    "https://feed.iplaysoft.com",
    # anyfeeder 服务已关闭（2026-06-03 返回 404），移除以下站点：
    # "https://plink.anyfeeder.com/ign/cn",
    # "https://plink.anyfeeder.com/3dm",
    # "https://plink.anyfeeder.com/gamersky",
]

# 文件存储配置
HASH_RECORD_FILE = "hash_record.txt"
EMAIL_BACKUP_DIR = "email_backup"
DASHBOARD_DATA_DIR = "data"
DASHBOARD_RESULT_FILE = os.path.join(DASHBOARD_DATA_DIR, "inspection_result.json")
NOTIFIED_ITEMS_FILE = "notified_items.json"  # 记录已通知过的条目URL，避免重复推送
RUN_LOG_FILE = "run_log.jsonl"  # 每轮运行日志（JSONL格式），用于追踪历史与自检
FAILED_SITES_FILE = "failed_sites.json"  # 连续失败站点记录，自动建议移除

# 163邮箱SMTP配置
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "")  # 邮箱地址
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # 授权码
EMAIL_TO = os.getenv("SMTP_USER", "")  # 发送到自己

# 爬虫配置
REQUEST_TIMEOUT = 15  # 单个站点超时时间（秒）
REQUEST_DELAY_MIN = 0.5  # 请求间隔最小值（秒）
REQUEST_DELAY_MAX = 1.5  # 请求间隔最大值（秒）

# 随机User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# ============================================================
# 工具函数
# ============================================================

def get_beijing_time():
    """获取北京时间（Asia/Shanghai）"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz)


def get_current_round():
    """
    根据当前小时判断当日第几轮（固定映射，禁止计数器模式）
    - 00:00-03:59 → 第1轮
    - 04:00-07:59 → 第2轮
    - 08:00-11:59 → 第3轮
    - 12:00-15:59 → 第4轮
    - 16:00-19:59 → 第5轮
    - 20:00-23:59 → 第6轮
    """
    hour = get_beijing_time().hour
    if 0 <= hour < 4:
        return 1
    elif 4 <= hour < 8:
        return 2
    elif 8 <= hour < 12:
        return 3
    elif 12 <= hour < 16:
        return 4
    elif 16 <= hour < 20:
        return 5
    else:  # 20 <= hour < 24
        return 6


def get_random_ua():
    """随机返回一个User-Agent"""
    import random
    return random.choice(USER_AGENTS)


def get_random_delay():
    """随机返回请求延迟时间（秒）"""
    import random
    return random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)


# ============================================================
# 哈希记录管理
# ============================================================

def load_hash_records():
    """
    从文件加载哈希记录
    返回格式：{url: md5_hash}
    """
    records = {}
    if os.path.exists(HASH_RECORD_FILE):
        try:
            with open(HASH_RECORD_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        url, md5_hash = line.split('=', 1)
                        records[url.strip()] = md5_hash.strip()
        except Exception as e:
            print(f"[错误] 读取哈希文件失败: {e}")
    return records


def save_hash_records(records):
    """
    保存哈希记录到文件
    格式：url=md5值（每行一个）
    """
    try:
        with open(HASH_RECORD_FILE, 'w', encoding='utf-8') as f:
            f.write("# 站点哈希记录文件 - 格式: url=md5值\n")
            f.write("# 最后更新: {}\n".format(get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')))
            for url, md5_hash in records.items():
                f.write(f"{url}={md5_hash}\n")
        print(f"[信息] 哈希文件已更新: {HASH_RECORD_FILE}")
        return True
    except Exception as e:
        print(f"[错误] 保存哈希文件失败: {e}")
        return False


# ============================================================
# 已通知条目管理（去重）
# ============================================================

def load_notified_items():
    """
    加载已通知过的条目URL集合
    返回格式：set of item URLs
    """
    notified = set()
    if os.path.exists(NOTIFIED_ITEMS_FILE):
        try:
            with open(NOTIFIED_ITEMS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                notified = set(data.get('items', []))
        except Exception as e:
            print(f"[警告] 读取已通知条目文件失败: {e}")
    return notified


def save_notified_items(notified):
    """保存已通知条目URL集合到文件"""
    try:
        with open(NOTIFIED_ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'items': sorted(notified), 'updated_at': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}, f, ensure_ascii=False, indent=2)
        print(f"[信息] 已通知条目记录已更新: {NOTIFIED_ITEMS_FILE} ({len(notified)} 条)")
        return True
    except Exception as e:
        print(f"[错误] 保存已通知条目失败: {e}")
        return False


def filter_new_items(items, notified):
    """
    从条目列表中过滤出未通知过的新条目
    返回：(新条目列表, 本轮新增的URL集合)
    """
    new_items = []
    new_urls = set()
    for item in items:
        item_url = item['url'] if isinstance(item, dict) else item
        if item_url not in notified:
            new_items.append(item)
            new_urls.add(item_url)
    return new_items, new_urls


# ============================================================
# 爬虫核心逻辑
# ============================================================

def extract_article_items(soup, base_url=''):
    """
    从页面中提取独立文章条目列表（含链接）
    返回：[{'text': '标题', 'url': '链接'}, ...] 最多50条
    """
    import re
    # 移除干扰元素
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
        tag.decompose()

    body = soup.find('body')
    if not body:
        return []

    items = []
    seen = set()

    # 策略1: 提取 <a> 标签的文本 + href
    for a_tag in body.find_all('a', href=True):
        text = a_tag.get_text(strip=True)
        if not text or len(text) < 4 or len(text) > 120:
            continue
        text = ' '.join(text.split())
        if text in seen:
            continue
        # 过滤导航词/英文短词
        if text[0].isupper() and len(text) < 20:
            continue
        if len(re.findall(r'[^\w\u4e00-\u9fff\u3000-\u303f\s]', text)) > len(text) * 0.3:
            continue
        href = a_tag['href'].strip()
        # 转绝对链接
        if href.startswith('/'):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        elif not href.startswith('http'):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        seen.add(text)
        items.append({'text': text, 'url': href})

    # 策略2: 如果 <a> 标签太少，用正文分句作为备选
    if len(items) < 2:
        text = body.get_text()
        for sep in ['\n', '｜', '丨', '│']:
            text = text.replace(sep, '|SPLIT|')
        lines = text.split('|SPLIT|')
        for line in lines:
            line = ' '.join(line.split()).strip()
            if not line or len(line) < 4 or len(line) > 150:
                continue
            if line in seen:
                continue
            if line.startswith('http') or line.startswith('www') or line.isdigit():
                continue
            if len(re.findall(r'[a-zA-Z0-9]', line)) > len(line) * 0.7 and len(line) < 30:
                continue
            seen.add(line)
            items.append({'text': line, 'url': base_url})

    return items[:50]


def fetch_page_content(url):
    """
    爬取页面完整正文
    返回：(成功标志, 内容/错误信息)
    内容包含：(text, title, summary)
    """
    headers = {
        'User-Agent': get_random_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        print(f"[爬取] {url}")
        response = requests.get(
            url, 
            headers=headers, 
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        
        # 检查HTTP状态码
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        # 让 BeautifulSoup 直接用字节流自动检测编码（避免 requests 默认 ISO-8859-1 导致中文乱码）
        soup = BeautifulSoup(response.content, 'html.parser')

        # 如果 BS 没检测到编码，尝试 apparent_encoding（基于 chardet）
        if not soup.original_encoding:
            encoding = response.apparent_encoding or 'utf-8'
            if encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
                encoding = 'gbk'
            content = response.content.decode(encoding, errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
        
        # 获取页面标题
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else url
        
        # 提取文章条目列表（含链接）
        article_items = extract_article_items(soup, url)

        # 移除脚本、样式、注释等干扰内容
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # 获取正文文本
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)

        # 清理多余空白
        text = ' '.join(text.split())

        if not text:
            return False, "页面正文为空"

        # 生成摘要（前300个字符）
        summary = text[:300] + '...' if len(text) > 300 else text

        # 返回包含标题、摘要和文章条目的字典
        return True, {
            'text': text,
            'title': title,
            'summary': summary,
            'items': article_items
        }
        
    except requests.Timeout:
        return False, "请求超时"
    except requests.ConnectionError:
        return False, "连接失败"
    except requests.RequestException as e:
        return False, f"请求异常: {str(e)[:50]}"
    except Exception as e:
        return False, f"未知错误: {str(e)[:50]}"


def calculate_md5(text):
    """计算文本的MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def check_site_update(url, old_records):
    """
    检查单个站点是否有更新
    返回：(是否更新, 新哈希值, 错误信息, 页面信息)
    """
    success, result = fetch_page_content(url)
    
    if not success:
        return None, None, result, None  # 爬取失败
    
    # result现在是一个字典
    text = result['text']
    page_info = {
        'url': url,
        'title': result['title'],
        'summary': result['summary'],
        'items': result['items']
    }
    
    new_hash = calculate_md5(text)
    old_hash = old_records.get(url)
    
    if old_hash is None:
        # 首次监控，记录哈希但不视为更新
        return False, new_hash, "首次监控", page_info
    elif old_hash != new_hash:
        # 检测到更新
        return True, new_hash, "内容已更新", page_info
    else:
        # 无更新
        return False, new_hash, "无更新", page_info


# ============================================================
# 邮件推送（网易Claw）
# ============================================================

def generate_email_html(round_num, all_site_results, check_time, notified=None):
    """
    生成邮件内容 — 纯文本格式
    all_site_results: 列表，每个元素为 {'url':..., 'title':..., 'summary':..., 'items':..., 'status': 'updated'|'no_update'|'error'|'first', 'message':...}
    items 格式: [{'text': '标题', 'url': '链接'}, ...]
    notified: 已通知过的条目URL集合（set），传入则过滤重复条目
    排序规则：有更新的排在前面（按条目数降序），无更新的排在后面
    返回：(主题, HTML正文, 纯文本正文, 本轮新增条目URL集合)
    """
    if notified is None:
        notified = set()

    # 统计与排序
    updated_results = [r for r in all_site_results if r['status'] == 'updated']
    no_update_results = [r for r in all_site_results if r['status'] in ('no_update', 'first')]
    error_results = [r for r in all_site_results if r['status'] == 'error']

    # 过滤已通知过的条目，只保留真正新的
    all_new_urls = set()
    for r in updated_results:
        new_items, new_urls = filter_new_items(r.get('items', []), notified)
        r['items'] = new_items
        all_new_urls.update(new_urls)

    # 移除过滤后无条目的站点（之前发过了，不算真正更新）
    updated_results = [r for r in updated_results if r['items']]

    # 更新的站点按条目数降序
    updated_results.sort(key=lambda r: len(r.get('items', [])), reverse=True)

    total = len(all_site_results)
    updated_count = len(updated_results)
    total_new_items = sum(len(r.get('items', [])) for r in updated_results)

    if updated_count > 0:
        subject = f"【站点更新提醒】第{round_num}轮巡检 | {updated_count}个站点 {total_new_items}条新内容"
    else:
        subject = f"【站点巡检报告】第{round_num}轮巡检 | 暂无更新"

    # ===== 纯文本正文 =====
    lines = []
    lines.append("站点更新监控巡检报告")
    lines.append("")
    lines.append(f"第 {round_num} 轮巡检  {check_time}")
    lines.append(f"总计 {total} 个站点 | 更新 {updated_count} 个 | 无更新 {len(no_update_results)} 个 | 异常 {len(error_results)} 个")
    lines.append("")

    idx = 1
    for r in updated_results:
        items = r.get('items', [])
        item_count = len(items)
        title = r.get('title', r['url'])
        url = r['url']
        lines.append(f"{idx}. {title} ({url}) [{item_count}条新]")
        for item in items:
            item_text = item['text'] if isinstance(item, dict) else item
            item_url = item['url'] if isinstance(item, dict) else url
            lines.append(f"  - {item_text}")
            lines.append(f"    {item_url}")
        lines.append("")
        lines.append("---")
        lines.append("")
        idx += 1

    for r in no_update_results:
        title = r.get('title', r['url'])
        url = r['url']
        lines.append(f"{idx}. {title} ({url})")
        lines.append("  暂无新内容")
        lines.append("")
        lines.append("---")
        lines.append("")
        idx += 1

    for r in error_results:
        url = r['url']
        lines.append(f"{idx}. {url}")
        lines.append(f"  异常: {r['message']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        idx += 1

    lines.append("")
    lines.append("GitHub Actions 站点巡检机器人 | 每4小时自动巡检 | 163邮箱推送")

    text_body = '\n'.join(lines)

    # HTML 版本也生成一份纯文本（邮件备份用）
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:monospace;font-size:13px;white-space:pre-wrap;padding:20px;">
{html_escape(text_body)}
</body>
</html>"""

    return subject, html_body, text_body, all_new_urls


def html_escape(text):
    """转义HTML特殊字符"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def send_email_smtp(subject, html_body, text_body=None):
    """
    通过163邮箱SMTP发送邮件
    返回：(成功标志, 错误信息)
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, "邮箱配置缺失"
    
    try:
        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = SMTP_USER
        message['To'] = EMAIL_TO
        message['Subject'] = subject
        
        # 添加纯文本正文（邮件客户端会优先显示）
        if text_body:
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            message.attach(text_part)
        else:
            # 如果没有提供纯文本，从主题生成
            text_part = MIMEText(subject, 'plain', 'utf-8')
            message.attach(text_part)
        
        # 添加HTML正文
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        print(f"[邮件] 发送到: {EMAIL_TO}")
        
        # 连接SMTP服务器并发送
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, message.as_string())
        
        print(f"[邮件] ✓ 发送成功: {subject}")
        return True, None
        
    except smtplib.SMTPAuthenticationError:
        return False, "邮箱认证失败（检查授权码）"
    except smtplib.SMTPException as e:
        return False, f"SMTP错误: {e}"
    except Exception as e:
        return False, f"发送异常: {str(e)}"


def save_email_backup(round_num, html_body):
    """
    保存邮件HTML到本地备份
    文件名：yyyyMMdd_第N轮_站点更新邮件备份.html
    """
    try:
        # 确保备份目录存在
        os.makedirs(EMAIL_BACKUP_DIR, exist_ok=True)
        
        # 生成文件名
        today = get_beijing_time().strftime('%Y%m%d')
        filename = f"{today}_第{round_num}轮_站点更新邮件备份.html"
        filepath = os.path.join(EMAIL_BACKUP_DIR, filename)
        
        # 保存HTML文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_body)
        
        print(f"[备份] 邮件已保存: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"[错误] 邮件备份失败: {e}")
        return None


# ============================================================
# Dashboard 数据生成
# ============================================================

def save_dashboard_data(round_num, all_site_results, check_time):
    """
    保存巡检结果为 JSON，供 GitHub Pages 仪表盘读取
    """
    try:
        os.makedirs(DASHBOARD_DATA_DIR, exist_ok=True)

        # 转换状态格式：下划线 → 连字符（前端约定）
        sites_for_dashboard = []
        for r in all_site_results:
            status = r['status'].replace('_', '-')
            sites_for_dashboard.append({
                'url': r['url'],
                'title': r.get('title', r['url']),
                'summary': r.get('summary', ''),
                'items': r.get('items', []),
                'status': status,
                'message': r.get('message', '')
            })

        dashboard_data = {
            'round_num': round_num,
            'check_time': check_time,
            'total': len(sites_for_dashboard),
            'updated': len([s for s in sites_for_dashboard if s['status'] == 'updated']),
            'sites': sites_for_dashboard
        }

        with open(DASHBOARD_RESULT_FILE, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

        print(f"[Dashboard] 仪表盘数据已保存: {DASHBOARD_RESULT_FILE}")
        return True
    except Exception as e:
        print(f"[错误] Dashboard数据保存失败: {e}")
        return False


# ============================================================
# Git提交管理
# ============================================================

def git_commit_if_changed():
    """
    检查是否有变更，仅在有变更时执行commit & push
    变更条件：哈希文件修改 或 新增邮件备份
    
    注意：此函数在GitHub Actions环境中会跳过git操作，
    因为workflow有专门的提交步骤
    """
    # 检查是否在GitHub Actions环境中
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print("[Git] 在GitHub Actions环境中，跳过脚本内git操作")
        print("[Git] 变更将由workflow的提交步骤处理")
        return False
    
    try:
        # 检查工作区状态
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        changes = result.stdout.strip()
        if not changes:
            print("[Git] 无变更，跳过提交")
            return False
        
        # 有变更，执行提交
        now = get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"站点更新检测 - {now}"
        
        # Git add所有变更
        subprocess.run(['git', 'add', '-A'], check=True, timeout=30)
        
        # Git commit
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, timeout=30)
        
        # Git pull --rebase 再 push（避免远程有更新的推送冲突）
        try:
            subprocess.run(['git', 'pull', '--rebase'], check=True, timeout=60)
        except subprocess.CalledProcessError:
            print("[Git] pull --rebase 失败，尝试直接 push")
        subprocess.run(['git', 'push'], check=True, timeout=60)

        print(f"[Git] 提交成功: {commit_msg}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[Git错误] 提交失败: {e}")
        return False
    except Exception as e:
        print(f"[Git异常] {e}")
        return False


# ============================================================
# 运行日志管理
# ============================================================

def load_run_log():
    """加载历史运行日志"""
    log = []
    if os.path.exists(RUN_LOG_FILE):
        try:
            with open(RUN_LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        log.append(json.loads(line))
        except Exception:
            pass
    return log


def append_run_log(entry):
    """追加一条运行日志"""
    try:
        with open(RUN_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"[警告] 运行日志写入失败: {e}")


def analyze_and_fix(run_result):
    """
    运行后自分析 + 自动修复
    run_result: {'success': N, 'error': N, 'updated': N, 'total': N, 'errors': [...], 'updated_sites': [...]}
    """
    print("\n" + "=" * 60)
    print("[自检] 运行后分析")
    print("-" * 60)

    issues_found = []

    # 1. 检查失败站点
    if run_result['errors']:
        for err in run_result['errors']:
            url = err['url']
            msg = err['message']

            # 403 封锁 → 建议增加延迟
            if '403' in msg:
                issues_found.append({
                    'level': 'warn',
                    'site': url,
                    'issue': 'HTTP 403 被封锁',
                    'action': '已记录，建议该站点增加请求延迟或更换 User-Agent'
                })

            # 404 页面不存在 → 建议移除
            elif '404' in msg:
                issues_found.append({
                    'level': 'error',
                    'site': url,
                    'issue': 'HTTP 404 页面不存在',
                    'action': '建议从 MONITOR_SITES 中移除该站点'
                })

            # 页面正文为空 → JS 渲染问题
            elif '页面正文为空' in msg:
                issues_found.append({
                    'level': 'warn',
                    'site': url,
                    'issue': '页面正文为空（可能是JS渲染）',
                    'action': '该站点可能需要 Playwright 才能抓取，暂时保留观察'
                })

            # 超时
            elif '超时' in msg:
                issues_found.append({
                    'level': 'warn',
                    'site': url,
                    'issue': '请求超时',
                    'action': '网络问题，下轮重试'
                })

            # 连接失败
            elif '连接失败' in msg:
                issues_found.append({
                    'level': 'warn',
                    'site': url,
                    'issue': '连接失败',
                    'action': '站点可能已下线，连续3轮失败后将建议移除'
                })

    # 2. 检查失败率
    error_rate = run_result['error'] / run_result['total'] if run_result['total'] > 0 else 0
    if error_rate > 0.1:
        issues_found.append({
            'level': 'error',
            'site': '全局',
            'issue': f'失败率 {error_rate:.0%} 超过 10%',
            'action': '检查网络环境或 GitHub Actions 运行时'
        })

    # 3. 更新率异常检测（>80% 站点更新可能是哈希过于敏感）
    if run_result['total'] > 0:
        update_rate = run_result['updated'] / run_result['total']
        if update_rate > 0.8:
            issues_found.append({
                'level': 'info',
                'site': '全局',
                'issue': f'更新率 {update_rate:.0%} 异常高，可能是首次运行或哈希过于敏感',
                'action': '观察下轮结果，如持续高更新率可考虑过滤动态内容'
            })

    # 4. 检查历史趋势：连续失败的站点
    run_log = load_run_log()
    if len(run_log) >= 3:
        recent_errors = set()
        for log_entry in run_log[-3:]:
            for err in log_entry.get('errors', []):
                recent_errors.add(err['url'])

        for url in recent_errors:
            issues_found.append({
                'level': 'error',
                'site': url,
                'issue': '连续3轮巡检均失败',
                'action': '建议从 MONITOR_SITES 中移除'
            })

    # 打印分析报告
    if issues_found:
        print(f"\n[自检] 发现 {len(issues_found)} 个问题：\n")
        for i, issue in enumerate(issues_found, 1):
            level_icon = {'error': '❌', 'warn': '⚠️', 'info': '💡'}.get(issue['level'], '📋')
            print(f"  {i}. {level_icon} [{issue['site']}]\n     问题: {issue['issue']}\n     建议: {issue['action']}\n")
    else:
        print("\n  ✅ 本轮运行健康，无异常问题\n")

    return issues_found


# ============================================================
# 主流程
# ============================================================

def main():
    """主监控流程"""
    print("=" * 60)
    print("GitHub Actions 多站点更新监控系统")
    print("=" * 60)
    
    # 获取当前时间和轮次
    now = get_beijing_time()
    round_num = get_current_round()
    check_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"[启动] 北京时间: {check_time}")
    print(f"[启动] 当日第 {round_num} 轮巡检")
    print(f"[启动] 监控站点数: {len(MONITOR_SITES)}")
    print("-" * 60)
    
    # 加载历史哈希记录
    old_records = load_hash_records()
    print(f"[信息] 已加载哈希记录: {len(old_records)} 条")

    # 加载已通知过的条目URL（去重用）
    notified = load_notified_items()
    print(f"[信息] 已加载已通知条目: {len(notified)} 条")
    
    # 检查所有站点更新
    all_site_results = []  # 存储所有站点状态（含标题、摘要）
    new_records = old_records.copy()
    success_count = 0
    error_count = 0
    updated_count = 0

    for idx, url in enumerate(MONITOR_SITES, 1):
        print(f"\n[{idx}/{len(MONITOR_SITES)}] 检查: {url}")

        # 检查站点更新
        is_updated, new_hash, message, page_info = check_site_update(url, old_records)

        if is_updated is None:
            # 爬取失败
            print(f"[失败] {message}")
            error_count += 1
            all_site_results.append({
                'url': url,
                'title': url,
                'summary': '',
                'status': 'error',
                'message': message
            })
        else:
            # 更新哈希记录
            new_records[url] = new_hash
            success_count += 1

            if is_updated:
                print(f"[更新] ✅ {message}")
                updated_count += 1
                all_site_results.append({
                    'url': url,
                    'title': page_info.get('title', url) if page_info else url,
                    'summary': page_info.get('summary', '') if page_info else '',
                    'items': page_info.get('items', []) if page_info else [],
                    'status': 'updated',
                    'message': message
                })
            else:
                print(f"[正常] {message}")
                status = 'first' if url not in old_records else 'no_update'
                all_site_results.append({
                    'url': url,
                    'title': page_info.get('title', url) if page_info else url,
                    'summary': '',
                    'items': [],
                    'status': status,
                    'message': message
                })

        # 随机延迟，防止封禁
        delay = get_random_delay()
        time.sleep(delay)

    print("\n" + "=" * 60)
    print(f"[统计] 成功: {success_count} | 失败: {error_count}")
    print(f"[统计] 更新站点: {updated_count} 个")

    print("\n" + "-" * 60)
    print("[处理] 生成巡检报告邮件...")

    # 总是更新哈希文件
    save_hash_records(new_records)

    # 生成邮件内容（传入已通知条目用于去重）
    subject, html_body, text_body, new_urls = generate_email_html(round_num, all_site_results, check_time, notified)

    # 更新已通知条目：加入本轮所有站点的items URL（去重）
    for r in all_site_results:
        if r['status'] == 'updated':
            for item in r.get('items', []):
                item_url = item['url'] if isinstance(item, dict) else item
                notified.add(item_url)
    save_notified_items(notified)

    print(f"[信息] 本轮新通知条目: {len(new_urls)} 条")

    # 保存邮件备份
    backup_path = save_email_backup(round_num, html_body)

    # 保存 Dashboard 数据（供 GitHub Pages 读取）
    save_dashboard_data(round_num, all_site_results, check_time)

    # 发送邮件
    if SMTP_USER and SMTP_PASSWORD:
        success, error = send_email_smtp(subject, html_body, text_body)
        if not success:
            print(f"[警告] 邮件发送失败: {error}")
            print("[提示] 邮件已本地备份，可手动查看")
    else:
        print("[警告] 邮箱未配置，跳过邮件发送")
        print("[提示] 请在GitHub Secrets中配置 SMTP_USER 和 SMTP_PASSWORD")

    # Git提交
    git_commit_if_changed()

    # ===== 运行后自分析 =====
    errors_detail = [{'url': r['url'], 'message': r.get('message', '')} for r in all_site_results if r['status'] == 'error']
    updated_sites = [r['url'] for r in all_site_results if r['status'] == 'updated']

    # 记录本轮运行日志
    run_entry = {
        'round': round_num,
        'check_time': check_time,
        'total': len(all_site_results),
        'success': success_count,
        'error': error_count,
        'updated': updated_count,
        'new_items': len(new_urls),
        'errors': errors_detail,
        'updated_sites': updated_sites
    }
    append_run_log(run_entry)

    # 自分析 + 建议
    issues = analyze_and_fix({
        'success': success_count,
        'error': error_count,
        'updated': updated_count,
        'total': len(all_site_results),
        'errors': errors_detail,
        'updated_sites': updated_sites
    })

    print("\n" + "=" * 60)
    print("[完成] 本轮巡检结束")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[中断] 用户手动停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n[致命错误] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
