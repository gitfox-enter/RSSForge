#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 多站点更新监控系统
功能：爬取46个站点 → MD5比对检测更新 → 网易Claw邮件推送 → 本地备份归档
时间：每4小时执行一次（00:00, 04:00, 08:00, 12:00, 16:00, 20:00）
时区：Asia/Shanghai（北京时间）
"""

import os
import sys
import time
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import json
import subprocess

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
    "https://plink.anyfeeder.com/ign/cn",
    "https://plink.anyfeeder.com/3dm",
    "https://plink.anyfeeder.com/gamersky",
]

# 文件存储配置
HASH_RECORD_FILE = "hash_record.txt"
EMAIL_BACKUP_DIR = "email_backup"

# 网易Claw邮箱配置（从环境变量读取）
CLAW_AUTH_URL = os.getenv("CLAW_AUTH_URL", "t1/cDGJE7RNbeRsaZSWPDNfuU5FDNX")
CLAW_API_KEY = os.getenv("CLAWEMAIL_API_KEY", "")
CLAW_USER = os.getenv("CLAWEMAIL_USER", "")

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
# 爬虫核心逻辑
# ============================================================

def fetch_page_content(url):
    """
    爬取页面完整正文
    返回：(成功标志, 内容/错误信息)
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
        
        # 获取页面编码
        encoding = response.encoding or 'utf-8'
        if encoding.lower() in ['gb2312', 'gbk']:
            encoding = 'gbk'
        
        content = response.content.decode(encoding, errors='ignore')
        
        # 使用BeautifulSoup提取正文内容
        soup = BeautifulSoup(content, 'html.parser')
        
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
        
        return True, text
        
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
    返回：(是否更新, 新哈希值, 错误信息)
    """
    success, result = fetch_page_content(url)
    
    if not success:
        return None, None, result  # 爬取失败
    
    new_hash = calculate_md5(result)
    old_hash = old_records.get(url)
    
    if old_hash is None:
        # 首次监控，记录哈希但不视为更新
        return False, new_hash, "首次监控"
    elif old_hash != new_hash:
        # 检测到更新
        return True, new_hash, "内容已更新"
    else:
        # 无更新
        return False, new_hash, "无更新"


# ============================================================
# 邮件推送（网易Claw）
# ============================================================

def generate_email_html(round_num, updated_sites, check_time):
    """
    生成邮件HTML内容
    - 标题：【站点更新提醒】当日第N轮巡检 | 共M个网站更新
    - 正文：标准HTML格式，链接新窗口打开
    """
    # 邮件标题
    subject = f"【站点更新提醒】当日第{round_num}轮巡检 | 共{len(updated_sites)}个网站更新"
    
    # 邮件正文HTML
    body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f9f9f9;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .info-box {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .site-list {{
            background: white;
            border-radius: 5px;
            padding: 15px;
        }}
        .site-item {{
            padding: 10px;
            margin: 8px 0;
            background: #f0f4ff;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .site-item a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .site-item a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            padding: 15px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #e0e0e0;
            margin-top: 20px;
        }}
        .highlight {{
            color: #667eea;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0;">🔔 站点更新监控提醒</h2>
    </div>
    
    <div class="content">
        <div class="info-box">
            <p style="margin: 5px 0;">📅 当日第 <span class="highlight">{round_num}</span> 次全自动巡检</p>
            <p style="margin: 5px 0;">⏰ 巡检时间：<span class="highlight">{check_time}</span></p>
            <p style="margin: 5px 0;">📊 检测到 <span class="highlight">{len(updated_sites)}</span> 个网站内容更新</p>
        </div>
        
        <div class="site-list">
            <h3 style="margin-top: 0; color: #333;">更新站点列表</h3>
            <p>以下站点监测到内容更新，点击链接可直达原网页：</p>
"""
    
    # 添加每个更新站点
    for idx, site in enumerate(updated_sites, 1):
        body += f"""
            <div class="site-item">
                <strong>{idx}.</strong> <a href="{site}" target="_blank" rel="noopener noreferrer">{site}</a>
            </div>
"""
    
    body += """
        </div>
    </div>
    
    <div class="footer">
        <p style="margin: 5px 0;">🤖 自动化监控来源：GitHub Actions 站点巡检机器人</p>
        <p style="margin: 5px 0;">⏱ 每4小时自动巡检 | 零运维 | 稳定可靠</p>
    </div>
</body>
</html>
"""
    
    return subject, body


def send_claw_email(subject, html_body):
    """
    通过网易Claw发送邮件
    返回：(成功标志, 错误信息)
    """
    if not CLAW_API_KEY or not CLAW_USER:
        return False, "Claw邮箱密钥未配置"
    
    try:
        # Claw邮件API接口
        url = "https://api.claw.163.com/api/send"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CLAW_API_KEY}"
        }
        
        data = {
            "authUrl": CLAW_AUTH_URL,
            "to": CLAW_USER,
            "subject": subject,
            "html": html_body,
            "text": subject  # 纯文本备用
        }
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') or result.get('code') == 0:
                print(f"[邮件] 发送成功: {subject}")
                return True, None
            else:
                error = result.get('message', '未知错误')
                return False, f"API返回错误: {error}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
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
        
        # Git push
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
    
    # 检查所有站点更新
    updated_sites = []
    new_records = old_records.copy()
    success_count = 0
    error_count = 0
    
    for idx, url in enumerate(MONITOR_SITES, 1):
        print(f"\n[{idx}/{len(MONITOR_SITES)}] 检查: {url}")
        
        # 检查站点更新
        is_updated, new_hash, message = check_site_update(url, old_records)
        
        if is_updated is None:
            # 爬取失败
            print(f"[失败] {message}")
            error_count += 1
            continue
        
        # 更新哈希记录
        new_records[url] = new_hash
        success_count += 1
        
        if is_updated:
            # 检测到更新
            print(f"[更新] ✅ {message}")
            updated_sites.append(url)
        else:
            print(f"[正常] {message}")
        
        # 随机延迟，防止封禁
        delay = get_random_delay()
        time.sleep(delay)
    
    print("\n" + "=" * 60)
    print(f"[统计] 成功: {success_count} | 失败: {error_count}")
    print(f"[统计] 更新站点: {len(updated_sites)} 个")
    
    # 处理更新
    if updated_sites:
        print("\n" + "-" * 60)
        print("[处理] 检测到更新，开始处理...")
        
        # 1. 更新哈希文件
        save_hash_records(new_records)
        
        # 2. 生成邮件内容
        subject, html_body = generate_email_html(round_num, updated_sites, check_time)
        
        # 3. 保存邮件备份（无论发送成功与否）
        backup_path = save_email_backup(round_num, html_body)
        
        # 4. 发送邮件
        if CLAW_API_KEY and CLAW_USER:
            success, error = send_claw_email(subject, html_body)
            if not success:
                print(f"[警告] 邮件发送失败: {error}")
                print("[提示] 邮件已本地备份，可手动查看")
        else:
            print("[警告] Claw邮箱未配置，跳过邮件发送")
            print("[提示] 请在GitHub Secrets中配置 CLAWEMAIL_API_KEY 和 CLAWEMAIL_USER")
        
        # 5. Git提交（有哈希变更或新增邮件备份）
        git_commit_if_changed()
        
    else:
        print("\n[结果] 无更新，零输出、零提交、零打扰 ✓")
        
        # 即使无更新，也要保存首次监控的哈希
        if len(new_records) > len(old_records):
            save_hash_records(new_records)
            git_commit_if_changed()
    
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
