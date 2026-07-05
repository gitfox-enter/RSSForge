# RSSForge 接手指南

> 给完全不了解代码的人看的。用大白话讲清楚这个项目是什么、怎么运作、怎么改。

---

## 一句话总结

RSSForge 是一个**自动帮你把网站内容变成 RSS 订阅源**的工具，跑在 GitHub 上，**一分钱不用花**。

## 项目在做什么？（打个比方）

想象你关注了 47 个论坛/网站，每天手动去逛太累了。RSSForge 就是雇了个机器人：
1. 每 30 分钟自动去这些网站看看有没有新内容
2. 把新内容整理成标准的 RSS 格式
3. 发布到一个网页上，你的 RSS 阅读器可以订阅

## 核心概念（只有 5 个）

| 概念 | 是什么 | 对应文件 | 你需要关心的 |
|------|--------|----------|-------------|
| **站点配置** | 要监控哪些网站 | `sites.yaml` | 最常改的文件。加站、删站都在这里 |
| **爬虫引擎** | 怎么去网站抓内容 | `crawler/engine.py` | 一般不用改，除非抓取失败 |
| **解析器** | 怎么读懂网页内容 | `crawler/parsers/*.py` | 新加站点时可能需要写解析器 |
| **Feed 生成** | 把内容变成 RSS 文件 | `rss_feed.py` | 一般不用改 |
| **自动化流程** | 定时运行以上步骤 | `.github/workflows/*.yml` | 调整运行频率时改 |

## 文件地图

```
RSSForge/
├── sites.yaml                 ← 【最重要】所有站点配置
├── common.py                  ← 公共工具函数
├── crawl.py                   ← 入口：运行爬虫
├── rss_feed.py                ← 入口：生成 RSS 文件
├── opml_generator.py          ← 入口：生成 OPML（批量订阅文件）
├── generate_feeds_index.py    ← 入口：生成首页
├── crawler/
│   ├── engine.py              ← 爬虫主引擎（异步抓取）
│   ├── config.py              ← 读取 sites.yaml 的配置
│   ├── parsers/               ← 各网站的解析器
│   │   ├── core.py            ← 解析器注册表（域名→函数）
│   │   ├── deal_sites.py      ← 线报/羊毛站解析
│   │   ├── software_sites.py  ← 软件站解析
│   │   └── rss_parsers.py     ← RSS 源直接解析
│   └── ...
├── docs/                      ← GitHub Pages 部署目录
│   ├── index.html             ← 首页
│   ├── feeds/*.xml            ← 各站点的 RSS 文件
│   ├── opml.xml               ← 批量订阅文件
│   └── icons/                 ← 网站图标
└── .github/workflows/         ← GitHub Actions 自动化
    ├── crawl.yml              ← 每 30 分钟完整抓取
    ├── fast_check.yml         ← 每 30 分钟增量检查
    └── daily_summary.yml      ← 每天 22 点总结
```

## 自动化流程怎么跑的？

```
GitHub Actions 定时触发（每 30 分钟）
    ↓
运行 crawl.py → 访问各网站 → 抓取新内容 → 存到 items.json
    ↓
运行 rss_feed.py → 读取 items.json → 生成 docs/feeds/*.xml
    ↓
运行 opml_generator.py → 生成 docs/opml.xml
    ↓
运行 generate_feeds_index.py → 生成 docs/index.html
    ↓
git push → GitHub Pages 更新 → 你的 RSS 阅读器收到新内容
```

## 你日常会做的事

### 1. 添加新站点（最常见）

编辑 `sites.yaml`，在 `sites:` 列表末尾加：

```yaml
  - url: "https://example.com/"
    name: 示例站点
    tier: medium        # high=15-30分钟, medium=1-2小时, low=4-12小时
    interval: 60        # 最小抓取间隔（分钟）
    max_pages: 5        # 最大翻页数
    fast_check: true    # 是否参与快速检查
```

如果这个网站有自带的 RSS 地址，加上 `rss_feed: "https://example.com/feed/"` 就行，不需要写解析器。

如果没有 RSS，需要在 `crawler/parsers/` 下写一个解析函数，然后在 `crawler/parsers/core.py` 的 `PARSER_REGISTRY` 里注册。

### 2. 删除失效站点

在 `sites.yaml` 中找到那个站点，删除对应条目。同时在 `dead_sites:` 下添加记录：

```yaml
dead_sites:
  "https://example.com/":
    reason: "站点关闭"
    confirmed_at: "2026-07-05"
```

### 3. 查看运行状况

- GitHub 仓库的 **Actions** 页面 → 看每次运行的日志
- `docs/crawl_status.json` → 各站点最后一次抓取状态
- `feeds_meta.json` → 各站点条目数量

### 4. 手动触发一次抓取

在 GitHub 仓库页面 → Actions → 选 "站点更新监控" → Run workflow

## sites.yaml 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `url` | 是 | 网站地址 |
| `name` | 是 | 显示名称（中文） |
| `tier` | 否 | 优先级：high/medium/low，默认 medium |
| `interval` | 否 | 最小抓取间隔（分钟），默认 30 |
| `max_pages` | 否 | 最大翻页数，默认 5 |
| `fast_check` | 否 | 是否参与快速检查，默认 false |
| `js_render` | 否 | 是否需要 Playwright 渲染 JS，默认 false |
| `rss_feed` | 否 | 网站自带的 RSS 地址（有就不需要写解析器） |
| `parser` | 否 | 自定义解析器标识 |

## 常见问题

**Q: 为什么有些站点没有内容？**
A: 可能是网站反爬、解析器失效、或网站本身没更新。查看 Actions 日志中的错误信息。

**Q: 怎么增加抓取频率？**
A: 修改 `sites.yaml` 中该站点的 `tier` 改为 `high`，`interval` 改小（如 15）。

**Q: 怎么知道哪些站点是活跃的？**
A: 看 `feeds_meta.json` 中各站点的 `count` 字段。count > 0 说明有内容。

**Q: 我改了代码怎么生效？**
A: Push 到 GitHub 的 main 分支即可。下次 Actions 运行时会自动使用新代码。

## 技术栈一览

- **语言**：Python 3.11
- **爬虫**：aiohttp（异步HTTP）+ Playwright（JS渲染）
- **RSS**：Atom 格式（XML）
- **部署**：GitHub Pages（免费静态托管）
- **自动化**：GitHub Actions（免费 CI/CD）
- **数据存储**：JSON 文件（items.json, feeds_meta.json 等）

## 当前状态（2026-07-05）

- 配置站点：48 个
- 有内容的站点：7 个（线报酷、汇发部、线报ICU、专业线报、爱Q社区、超级线报、线报网）
- 总条目：11,914 条
- 自动运行：每 30 分钟一次
