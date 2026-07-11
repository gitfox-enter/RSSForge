# Task Summary — RSS 时间显示与发表时间不匹配

- **时间标签**: 2026-07-10
- **目标**: 解决 RSS 内容「显示时间 ≠ 文章发表时间」的问题，以上海/北京时间(Asia/Shanghai, UTC+8)为准。

## 根因分析
RSS 2.0 `<pubDate>` 与 Atom `<published>/<updated>` 都表示**绝对 UTC 时刻**（带时区），
不是本地时间。不匹配来自：
1. 展示用 `date.toString()/toLocaleString()` 用了**服务器本地时区**而非北京时间（常见差 8 小时）。
2. 解析前剥离 `GMT/+0000` 时区后缀，把 UTC 时刻误当上海本地时刻。
3. 排序/比较用格式化字符串而非绝对毫秒数。

## 解决方案
在 `/home/node/.openclaw/workspace/agent-606489db/rss-time-fix/` 下：
- `rss-time.cjs`：规范化模块
  - `parseRssTime(raw)`：保留原始时区解析为绝对 Date（失败返回 null）
  - `formatShanghai(input, opts)`：用 `Intl.DateTimeFormat('zh-CN', {timeZone:'Asia/Shanghai'})` 展示
  - `toShanghaiISO(input)`：输出带 `+08:00` 的 ISO 字符串用于统一存储
  - `compareByInstant(a,b)`：按 UTC 毫秒排序/比较
- `rss-time.test.cjs`：6 项测试，全部通过（node --test）。
- `README.md`：根因、修复原则、套用方式。

## 验证
`node --test rss-time.cjs` → 6 passed, 0 failed。
复现反例：同一时刻 `15:30 UTC` 用错误做法(UTC 时区展示)得到 `15:30`，正确做法(上海)得到 `23:30`。

## 结论
显示与发表时间不匹配是**时区处理 bug**，不是数据问题。统一“解析保留时区 + 展示指定 Asia/Shanghai +
比较用绝对毫秒”即可彻底解决。已交付可用模块与测试。
