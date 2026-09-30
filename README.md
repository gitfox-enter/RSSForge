# RSSForge（仅抓取模式）

抓取线报/羊毛/优惠站点，提取条目，存入 items.json / items_latest.json。

## 架构（2026-09-30 重构）

**只做「抓」**。发布与展示层已移除：

- ❌ RSS feed 生成（rss_feed.py / docs/feeds/）
- ❌ OPML 生成与镜像（opml_generator.py / docs/opml*.xml）
- ❌ GitHub Pages 静态展示站（docs/index.html / reader.html / icons / Pages 已停用）
- ❌ ima 知识库 URL 导入（ima_import_workflow.py —— ima 网址校验会过滤线报链接，方案改为消费端生成汇总文档上传）

数据产出（本仓库内）：
- `items.json` / `items_latest.json` — 全量/最新条目（url, text, source, time, category）
- `crawl_status.json` — 每轮抓取状态
- `run_log.jsonl` — 运行日志

## 消费方式

下游（QQ 机器人推送 / ima 汇总文档）由独立的消费端负责，不再由本仓库承载。

## 运行

GitHub Actions 每 30 分钟跑一次 `crawl.py`（可手动 workflow_dispatch 触发）。
