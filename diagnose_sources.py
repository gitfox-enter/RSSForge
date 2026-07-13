#!/usr/bin/env python3
"""Diagnose zero-content RSS sources."""
import os
import urllib.request, re, json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='replace')

sources = [
    ('51卡农', 'https://www.51kanong.com/'),
    ('新赚吧', 'https://xzba.cc/'),
    ('线报迷', 'https://xianbaomi.com/'),
    ('果核剥壳', 'https://www.ghxi.com/'),
    ('小角落', 'https://yangmao.19970709.xyz/'),
    ('小众软件', 'https://www.appinn.com/'),
    ('薅羊毛', 'https://www.ymxianbao.cn/'),
    ('Line资讯', 'https://www.linejia.com/'),
    ('万站云', 'https://www.10000yun.com/'),
    ('Free App', 'https://free.apprcn.com/'),
    ('每日APP', 'https://www.daydayzhuan.com/'),
    ('007情报站', 'https://www.007ymd.com/'),
    ('帮果网', 'https://www.haodanku.com/'),
    ('好东西', 'https://m.hybase.com/'),
    ('活动屋', 'https://www.huodong5.com/'),
    ('羊毛档', 'https://www.yangmaodang.club/'),
    ('羊毛说说', 'https://www.yxssp.com/'),
    ('APP推荐', 'https://www.apprcn.com/'),
    ('哆来咪', 'https://www.12345pro.com/'),
    ('白采网', 'https://www.baicaio.com/'),
    ('423down', 'https://www.423down.com/'),
    ('wycad', 'https://www.wycad.com/'),
    ('ThoseFree', 'https://www.thosefree.com/'),
    ('LSAPK', 'https://www.lsapk.com/'),
    ('涨姿势', 'https://www.wobangzhao.com/'),
]

results = []
for name, url in sources:
    result = {'name': name, 'url': url, 'status': 'unknown', 'size': 0, 'reason': ''}
    try:
        content = fetch(url)
        result['size'] = len(content)
        
        if len(content) < 3000:
            result['status'] = 'SMALL_RESPONSE'
            result['reason'] = 'small_response'
        elif 'setTimeout("reload()"' in content:
            result['status'] = 'JS_REDIRECT'
            result['reason'] = 'js_redirect'
        elif 'window.location' in content:
            result['status'] = 'JS_REDIRECT'
            result['reason'] = 'js_redirect'
        elif 'nginx' in content.lower() or '502' in content:
            result['status'] = 'SERVER_ERROR'
            result['reason'] = 'server_error'
        elif 'id="app"' in content or 'id="root"' in content:
            result['status'] = 'SPA'
            result['reason'] = 'spa'
        elif '登录' in content[:5000] and len(content) < 20000:
            result['status'] = 'LOGIN_REQUIRED'
            result['reason'] = 'login_required'
        else:
            links = re.findall(r'href=["\']([^"\']*\.html)["\']', content)
            links = [l for l in links if len(l) > 20]
            result['status'] = 'HTML_OK'
            result['reason'] = f'{len(content)}b,{len(links)}links'
            result['article_count'] = len(links)
    except urllib.error.HTTPError as e:
        result['status'] = f'HTTP_{e.code}'
        result['reason'] = f'http_{e.code}'
    except Exception as e:
        result['status'] = 'ERROR'
        result['reason'] = str(type(e).__name__)
    results.append(result)

# 输出到仓库根目录（原脚本写死到已废弃的 openclaw 外部路径，会导致写入失败）
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagnose_results.json')
with open(out_path, 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

for r in results:
    print(f"{r['name']}: [{r['status']}] {r['reason']}")
