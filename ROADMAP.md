# RSSForge 功能路线图 (v2.0)

> 此文件由 AI 维护，每周迭代开发时更新进度

## 第1周 (2026-07-10): 基础修复 + feeds_meta 过滤
**新功能**: feeds_meta.json 过滤零内容源（#131），OPML 只展示有内容的源
**Bug修复**: #105 parse_appinn_items 选择器永远取不到 href
**目标**: 让 OPML 和 feeds_meta 干净可信

## 第2周 (2026-07-17): 解析器批量修复
**新功能**: 修复 5-8 个零内容源的解析器（12345pro, 10000yun, yxssp, xianbaomi, wobangzhao 等有 HTML 但解析失败的源）
**Bug修复**: #122 is_junk() 使用 == 而非 in，#119 _fuzzy_dedupe_key 截断问题
**目标**: 活跃源从 7 个提升到 12+ 个

## 第3周 (2026-07-24): 前端体验升级
**新功能**: feeds/index.html 添加搜索框和源过滤功能
**Bug修复**: #102 index.html copyFeedLink 隐式 event，#101 pages.yml 未复制根级 HTML
**目标**: GitHub Pages 首页可搜索可过滤

## 第4周 (2026-07-31): 每日热门 Feed
**新功能**: 生成 daily_top.xml — 每日热门条目 feed（按来源数、关键词权重排序）
**Bug修复**: #116 _parse_response_html errors=ignore 导致中文截断，#104 datetime 无时区
**目标**: 用户可以订阅一个"精选" feed 而不用订阅全部

## 第5周 (2026-08-07): 订阅源健康度系统
**新功能**: 生成 health_report.json — 每个源的健康评分（成功率、条目数趋势、响应时间）
**Bug修复**: #120 robots.txt 缓存永不过期，#106 record_site_run O(n) 文件IO
**目标**: 可视化展示每个源的状态

## 第6周 (2026-08-14): API 接口
**新功能**: 添加 api.py — JSON API 接口 (/api/v1/items, /api/v1/sources, /api/v1/health)
**Bug修复**: #118 is_blacklisted 未解码 URL，#117 fast_check git push 重试逻辑
**目标**: 支持第三方应用集成

## 第7周 (2026-08-21): 每周摘要 Feed
**新功能**: 生成 weekly_summary.xml — 每周自动汇总各源精选条目
**Bug修复**: #127 分页 domain 过期，#126 三处致命运行时错误
**目标**: 低频用户只需订阅一个周报

## 第8周 (2026-08-28): OPML 分类分组
**新功能**: OPML 按分类分组（线报类、软件类、活动类），支持嵌套 outline
**Bug修复**: #103 opml_generator 删除文件副作用，#100 以下其他 Medium/Low
**目标**: OPML 更专业更好用

## 后续候选功能池
- PWA 离线访问（manifest.json + service worker）
- Telegram Bot 推送当日精选
- Webhook 通知（Discord/Telegram 新条目推送）
- 多语言支持（英文界面）
- 贡献指南和 Issue/PR 模板（#112）
- LICENSE 文件（#111）
- 每日数据质量报告（异常条目检测）
- RSS feed 内容全文提取（目前只有标题和链接）
- 支持认证/登录站点（带 cookie 的源）
- 自动发现 RSS 源（给一个网址，自动检测是否有 RSS）

## 进度记录
| 周次 | 日期 | 新功能 | Bug修复 | 活跃源数 | 总条目数 |
|------|------|--------|---------|----------|----------|
| - | 2026-07-04 (初始) | - | - | 7 | 11577 |
