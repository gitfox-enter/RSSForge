#!/usr/bin/env python3
"""Create GitHub issues for RSSForge known problems."""
import os
import urllib.request
import json

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
if not GITHUB_TOKEN:
    raise SystemExit('ERROR: GITHUB_TOKEN environment variable not set')
REPO = 'gitfox-enter/RSSForge'

def create_issue(title, body, labels):
    data = json.dumps({
        'title': title,
        'body': body,
        'labels': labels
    }).encode()
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/issues',
        data=data,
        headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'RSSForge-AI-Agent'
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

# Issue 1: 31个零内容源
body1 = """## 问题描述

当前 RSSForge 配置了 38 个订阅源，但其中 **31 个**持续产出 0 条内容。

**正常运行的 7 个源：**
- 线报酷 (5472 条)
- 汇发部 (4197 条)
- 线报ICU (775 条)
- 专业线报 (465 条)
- 爱Q社区 (225 条)
- 超级线报 (135 条)
- 线报网 (89 条)

## 已确认的失败原因

| 源 | URL | 失败原因 |
|----|-----|---------|
| 51卡农 | www.51kanong.com | JS 重定向（953字节），需 Playwright |
| 新赚吧 | xzba.cc | SSL 握手失败 |
| 豆瓣小组 | www.douban.com | HTTP 404（群组已失效）|
| Line资讯 | www.linejia.com | Connection refused |
| 羊毛派 | www.ymxianbao.cn | Connection refused |
| FoxIRJ | www.foxirj.com | SSL 证书过期 |
| 007情报站 | 007ymd.com | DNS 解析失败 |

## 修复优先级

| 优先级 | 行动 |
|--------|------|
| P0 | 51卡农加入 JS_RENDER_SITES |
| P0 | 果核剥壳(ghxi)加入 JS_RENDER_SITES |
| P1 | SSL问题源调试 |
| P2 | 已下线站点从 sites.yaml 移除 |

*自动生成 via RSSForge AI Agent | 2026-07-04*
"""
r1 = create_issue('[P0] 31个订阅源持续零内容产出', body1, ['bug', 'high-priority'])
print(f'Issue #1 created: #{r1["number"]} {r1["html_url"]}')

# Issue 2: feeds_meta 写入零内容源
body2 = """## 问题描述

`feeds_meta.json` 当前写入全部 38 个源，包括 31 个零内容源。

`_generate_feeds_meta()` 函数文档声称"仅包含有数据的站点"，但代码实际遍历 `SOURCE_NAME_MAP`（38个）并全部写入，缺少 `if items_count == 0: continue` 过滤。

## 修复方案

在 `rss_feed.py` 的 `_generate_feeds_meta()` 中添加：

```python
if items_count == 0:
    continue
```

仅写入有内容的源，使 feeds_meta.json 和 feeds/ 目录保持一致。

*自动生成 via RSSForge AI Agent | 2026-07-04*
"""
r2 = create_issue('[P1] feeds_meta.json 应过滤零内容源', body2, ['bug', 'enhancement'])
print(f'Issue #2 created: #{r2["number"]} {r2["html_url"]}')

# Issue 3: 每周维护任务
body3 = """## 功能需求

为 RSSForge 建立**每周自动维护机制**，确保项目长期健康运行。

### 维护内容

1. **订阅源健康检查**
   - 确认有内容的源仍正常产出
   - 排查零内容源的失败原因（网络/解析器/站点关闭）
   - 评估是否需要移除已失效源

2. **新订阅源发现**
   - 搜索"线报"、"羊毛"、"薅羊毛"类网站最新动态
   - 测试新站点可用性（网络可达 + HTML结构可解析）
   - 评估内容质量后决定是否加入 sites.yaml

3. **数据质量报告**
   - 汇总本周各源新增条目数量
   - 发现异常的源（突然停更、内容异常）标记排查

### 实施方式

- 每周五 18:00 (北京时间) 自动触发
- AI Agent 执行维护检查并输出报告
- 如有新源或重大变化，通过 Issue 记录

*自动生成 via RSSForge AI Agent | 2026-07-04*
"""
r3 = create_issue('[enhancement] 建立每周订阅源维护机制', body3, ['enhancement'])
print(f'Issue #3 created: #{r3["number"]} {r3["html_url"]}')
