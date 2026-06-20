# RSSForge 本地开发指南

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/gitfox-enter/RSSForge.git
cd RSSForge
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

核心依赖:
- `requests>=2.31.0` — HTTP 请求
- `aiohttp>=3.9.0` — 异步 HTTP
- `beautifulsoup4>=4.12.2` — HTML 解析
- `PyYAML>=6.0` — YAML 配置
- `pypinyin>=0.51.0` — 中文拼音转换
- `playwright>=1.40.0` — JS 渲染 (可选)
- `pytest-cov>=4.1.0` — 测试覆盖率 (可选)

### 3. 一键启动 (Docker Compose)

```bash
# 构建 & 启动开发环境
docker compose up -d

# 进入容器
docker compose exec rssforge bash

# 手动运行爬虫
python crawl.py

# 运行测试
python -m pytest test_crawler.py -v
```

> **注意**: Docker 方式主要用于模拟 CI 环境，本地开发通常直接用 pip 安装即可。

## 项目结构

```
RSSForge/
├── crawl.py              # 爬虫入口 (slim re-export)
├── fast_check.py         # 高频增量检查
├── common.py             # 共享模块 (日志/存储/黑名单/工具)
├── rss_feed.py           # RSS/Atom feed 生成器
├── opml_generator.py     # OPML 订阅包生成
├── alerter.py            # 告警 (GitHub Issue / 通知)
├── sites.yaml            # 站点配置 (Single Source of Truth)
├── adaptive_tiers.json   # 站点层级 (自动维护)
├── index.html            # 前端首页
├── health.html           # Feed 健康监控页
├── status.html           # 爬取状态页
├── redirect.html         # 外链跳转中转页
├── manifest.json         # PWA manifest
├── sw.js                 # Service Worker
├── crawler/
│   ├── engine.py         # 异步爬取引擎
│   ├── network.py        # 网络请求 (aiohttp + Playwright)
│   ├── storage.py        # 数据持久化 (items.json / notified)
│   ├── config.py         # 配置管理
│   └── parsers/          # 各站点解析器
├── feeds/                # 生成的 RSS feed 文件
├── docs/                 # VitePress 文档站
├── .github/workflows/    # GitHub Actions
└── test_crawler.py       # 测试套件
```

## 核心命令

```bash
# 完整爬取 (原 crawl.yml)
python crawl.py

# 增量快速检查 (原 fast_check.yml)
python fast_check.py

# 生成 RSS feed
python -c "from rss_feed import main; main()"

# 生成 OPML
python opml_generator.py

# 运行测试
python -m pytest test_crawler.py -v

# 带覆盖率
python -m pytest test_crawler.py --cov=crawler --cov=common -v
```

## 配置说明

### sites.yaml

所有站点配置的唯一来源。核心字段:

| 字段 | 说明 |
|------|------|
| `url` | 站点 URL |
| `name` | 显示名称 (会 slugify 生成 feed 文件名) |
| `tier` | high/medium/low — 决定爬取频率 |
| `interval` | 最小抓取间隔 (分钟) |
| `fast_check` | 是否参与高频检查 |
| `js_render` | 是否需要 Playwright 渲染 |
| `parser` | 自定义解析器名称 |
| `categories` | 子分类 (如 423down 的软件分类) |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SITE_URL_BASE` | 站点根 URL | `https://gitfox-enter.github.io/RSSForge/` |
| `PROXY_LIST` | 代理列表 (逗号分隔) | 无 |
| `GITHUB_TOKEN` | GitHub API Token | 无 (CI 自动注入) |

## 添加新站点

1. 编辑 `sites.yaml`，在合适分类下添加:
```yaml
  - url: "https://example.com/"
    max_pages: 3
    name: 示例站
    tier: medium
    interval: 60
```

2. 如果站点需要自定义解析，在 `crawler/parsers/` 中新建解析器。

3. 提交后 GitHub Actions 会自动开始爬取。

## 注意事项

- `test_crawler.py` 有 ~294 个测试，修改核心逻辑前先跑测试
- `common.py` 的 `slugify()` 将中文转为拼音用于文件名，确保站点名称唯一
- `dead_sites:` 区域的站点不会被爬取
- Service Worker 缓存版本在 `sw.js` 中，修改前端资源后需更新 `CACHE_NAME`
