# Task Summary — 全文 RSS 阅读器（rss-fulltext）

- **时间标签**: 2026-07-10
- **目标**: 解决「RSS 只有标题、总要跳原网页」的体验问题，自动抓取并提取每篇文章正文，
  发布时间按上海/北京时间展示，正文后保留「查看原文」跳转。

## 交付物（/home/node/.openclaw/workspace/agent-606489db/rss-fulltext/）
- `rss-fulltext.cjs`：核心库
  - `parseFeed(xml)`：容错解析 RSS 2.0 / Atom（标题/链接/pubDate/content）。
  - `extractArticle(html, url)`：轻量 Readability 正文提取（去导航/footer/噪音，
    按段落长度+链接密度过滤，兜底取最大文本块；标题取 og:title>h1>title）。
  - `fetchText(url)`：带 UA + 超时的 HTTP 抓取（Node 全局 fetch）。
  - `getFullTextFeed(feedUrl, opts)`：编排——解析 feed → 逐篇抓取/提取 →
    复用已带 `<content:encoded>` 的全文 → 统一北京时间 → 保留 link。
- `rss-read.cjs`：命令行阅读器（`node rss-read.cjs <feedUrl> [--limit N] [--no-body]`）。
- `rss-fulltext.test.cjs`：5 项离线单测（mock feed + mock HTML），全部通过。
- `README.md`：用法、库接入、UI 接入方式、提取策略、注意事项。

## 关键设计
- 零第三方依赖，纯 Node.js（>=18）。
- 复用 `../rss-time-fix/rss-time.cjs` 的 `formatShanghai` / `toShanghaiISO`，确保时间按 Asia/Shanghai 展示。
- 提取失败时不产生空白破页：`it.hasBody=false` + `it.extractError`，仍保留「查看原文」链接。
- UI 接入建议：先渲染提取正文，底部放「🔗 查看原文 👉 link」按钮，实现「先看全文、按需跳原站」。

## 验证
- `node --test rss-fulltext.test.cjs` → 5 passed, 0 failed。
- 修复了 Atom `<link href rel="alternate"/>` 自闭合标签解析失败的问题（原先要求 `</link>` 闭合）。
- 实时联调未做：本沙箱无外网（fetch failed），但离线条目已验证解析与提取逻辑正确；
  在有网络的环境运行 `rss-read.cjs <真实feedUrl>` 即可拉取真实全文。

## 结论
已交付可用的全文 RSS 阅读器：列表/详情直接展示正文，不再强制跳原网页；
正文后仍保留原文链接供按需跳转。代码、测试、说明均已就绪。
