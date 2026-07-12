# RSSForge 质量审计 — 2026-07-12

## 目标
对 48 个 RSS 源做质量审计：死站移除、JS 渲染修复、域名迁移、非线报站点剔除。

## 处理结果

### 第一轮（死站清理）
- **移除 6 个死站**（feed 空/无法访问）：007羊毛党、51卡农、佛系软件、免恶魔、银软星球、小角落
- `huodong5.com` → `huodong8.com` 域名迁移
- `iehou.com` 添加 `js_render: true`（JS 渲染站）
- 结果：42 个 feed，index.html 58KB

### 第二轮（非线报站点清理）
- **移除 4 个站点**（38 个 feed，index.html 54KB）：
  - 我不找 (wobangzhao.com) — 密码破解资源论坛
  - 开心赚 (kxdao.net) — Discuz 论坛抓取到版块分类名，非线报
  - 新赚吧 (xzba.cc) — 游戏论坛，非线报
  - 万云积分 (10000yun.com) — VPN/影视聚合站，非线报

## 最终状态
- **38 个 feed**，全部为真实线报/软件类站点
- docs/index.html 54KB
- feeds_meta.json 已同步清理
- 所有变更已推送到 GitHub (commit: 52af0e6f)

## 保留站点的已知问题（未修复）
- 豆瓣小组、汇发部、羊毛王 等非线报类站点，保留但标注 low tier
- 部分 feed 的 pubDate 为爬取时间（非原始发布日），是爬虫元数据问题
