#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本：使用163邮箱SMTP发送邮件
"""

import os
import sys
import time
import hashlib
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# 测试站点
TEST_SITES = [
    "https://www.baidu.com",
    "https://www.github.com",
    "https://www.python.org",
]

# 163邮箱SMTP配置
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "")  # mrjin2004@163.com
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # 授权码
EMAIL_TO = os.getenv("SMTP_USER", "")  # 发送到自己

def get_beijing_time():
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz)

def get_random_ua():
    import random
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ])

def calculate_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fetch_page_content(url):
    """爬取页面内容"""
    headers = {
        'User-Agent': get_random_ua(),
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    try:
        print(f"[爬取] {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        
        return True, text
        
    except Exception as e:
        return False, str(e)

def send_email_smtp(subject, html_body):
    """使用163邮箱SMTP发送邮件"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[错误] 邮箱配置缺失")
        return False, "邮箱未配置"
    
    try:
        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = SMTP_USER
        message['To'] = EMAIL_TO
        message['Subject'] = subject
        
        # 添加HTML正文
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        print(f"[邮件] 正在发送到: {EMAIL_TO}")
        print(f"[邮件] 主题: {subject}")
        
        # 连接SMTP服务器并发送
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, message.as_string())
        
        print("[邮件] ✓ 发送成功！")
        return True, None
        
    except smtplib.SMTPAuthenticationError:
        return False, "邮箱认证失败（检查授权码）"
    except smtplib.SMTPException as e:
        return False, f"SMTP错误: {e}"
    except Exception as e:
        return False, f"发送异常: {e}"

def generate_email_html(updated_sites, check_time):
    """生成邮件HTML"""
    subject = f"【站点更新提醒】测试邮件 - 共{len(updated_sites)}个网站"
    
    body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .info-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        .site-list {{
            margin-top: 20px;
        }}
        .site-item {{
            padding: 15px;
            margin: 10px 0;
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
            padding: 20px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #e0e0e0;
        }}
        .highlight {{
            color: #667eea;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🔔 站点更新监控提醒</h2>
        </div>
        
        <div class="content">
            <div class="info-box">
                <p style="margin: 10px 0;">📅 发送时间：<span class="highlight">{check_time}</span></p>
                <p style="margin: 10px 0;">📊 检测到 <span class="highlight">{len(updated_sites)}</span> 个网站内容更新</p>
                <p style="margin: 10px 0;">✉️ 这是一封测试邮件</p>
            </div>
            
            <div class="site-list">
                <h3 style="margin-top: 0; color: #333;">更新站点列表</h3>
                <p>以下站点监测到内容更新，点击链接可直达原网页：</p>
"""
    
    for idx, site in enumerate(updated_sites, 1):
        body += f"""
                <div class="site-item">
                    <strong>{idx}.</strong> <a href="{site}" target="_blank">{site}</a>
                </div>
"""
    
    body += """
            </div>
        </div>
        
        <div class="footer">
            <p style="margin: 5px 0;">🤖 自动化监控来源：GitHub Actions 站点巡检机器人</p>
            <p style="margin: 5px 0;">⏱ 每4小时自动巡检 | 零运维 | 稳定可靠</p>
            <p style="margin: 5px 0; color: #667eea;">✉️ 163邮箱推送服务</p>
        </div>
    </div>
</body>
</html>
"""
    
    return subject, body

def main():
    print("=" * 60)
    print("测试邮件发送 (163 SMTP)")
    print("=" * 60)
    
    now = get_beijing_time()
    check_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"时间: {check_time}")
    print(f"邮箱: {SMTP_USER}")
    print(f"站点数: {len(TEST_SITES)}")
    print()
    
    # 爬取站点
    updated_sites = []
    for url in TEST_SITES:
        success, result = fetch_page_content(url)
        if success:
            print(f"[成功] 内容长度: {len(result)}")
            updated_sites.append(url)
        else:
            print(f"[失败] {result}")
        time.sleep(0.5)
    
    print()
    print("=" * 60)
    
    # 发送邮件
    if SMTP_USER and SMTP_PASSWORD:
        subject, html_body = generate_email_html(updated_sites, check_time)
        
        # 保存HTML备份
        os.makedirs("email_backup", exist_ok=True)
        backup_file = f"email_backup/test_{now.strftime('%Y%m%d_%H%M%S')}.html"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(html_body)
        print(f"[备份] {backup_file}")
        
        # 发送邮件
        success, error = send_email_smtp(subject, html_body)
        if success:
            print("\n" + "=" * 60)
            print("✅ 邮件发送成功！")
            print("=" * 60)
            print(f"\n📧 请检查邮箱: {EMAIL_TO}")
            print("   (包括垃圾邮件文件夹)")
        else:
            print(f"\n✗ 邮件发送失败: {error}")
    else:
        print("\n[错误] 请配置环境变量:")
        print("  export SMTP_USER='mrjin2004@163.com'")
        print("  export SMTP_PASSWORD='your-auth-code'")

if __name__ == "__main__":
    main()
