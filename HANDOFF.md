# RSSForge 维护交接手册（HANDOFF）

> **最后维护者**：WorkBuddy（代表金军 / GitHub `gitfox-enter` 代为全权维护）
> **交接日期**：2026-07-26
> **项目状态**：质量守卫 + 全自主维护运行中，CI 全自动，无需人工值守
> **面向对象**：接手维护的另一位助手。Clone 本仓库即可完整接手。

---

## 0. 一句话接手

```
git clone <仓库> → pip install -r requirements.txt → 读本文 → 看 Issues/PR
```

CI 已全自动托管（爬取/体检/修复/部署）。你**只需要**：理解下方机制、偶尔处理质量守卫开的 Issue（加 parser）、以及在用户要求时改 `sites.yaml` 或频率。**不需要**手动跑爬取。

---

## 1. 项目概况（2026-07-26 实测）

| 项 | 值 |
|---|---|
| 项目 | RSSForge：GitHub Actions 驱动的 RSS 聚合器，部署在 GitHub Pages |
| Pages 地址 | `https://gitfox-enter.github.io/RSSForge` |
| 监控源数 | **22 个**（`sites.yaml`，15 high / 5 medium / 2 low） |
| 全库条目 | **24,322 条**（`items.json`，约 5.5 MB；另有 `items_latest.json` 镜像） |
| 输出 Feed | **22 个** `docs/feeds/*.xml` |
| OPML | `docs/opml.xml`（主）+ `opml.official.xml` / `opml.jsdelivr.xml` / `opml.ghfast.xml`（3 个 CDN 镜像） |
| 数据持久化 | **就地存仓库**（非外部 DB）。`items.json` / `items_latest.json` / `feeds_meta.json` 随 CI 持续提交 |
| 技术栈 | Python 3.11 + aiohttp/Playwright + feedgen + GitHub Pages + GitHub Actions |

> ⚠️ 数据在仓库内（5.5 MB 的 `items.json`）。改动库文件会产生较大 diff，**务必走下方的「ours 并发策略」**，不要随意重新格式化。

---

## 2. 目录与关键文件索引

| 文件 / 目录 | 作用 | 何时动 |
|---|---|---|
| `sites.yaml` | 全部源配置（url/name/tier/interval/fast_check/js_render） | 增删源、调频率时 |
| `common.py` | 共享工具（`slugify`、`is_junk` 标题级过滤等），约 38 KB | 极少改 |
| `crawler/` | 爬取引擎与 per-site parser | 加新源 parser 时 |
| `crawler/parsers/core.py` | **`PARSER_REGISTRY`**：域名 → parser 函数映射（约 39 个 host 已注册） | 注册新 parser 时 |
| `rss_feed.py` | 读 `items.json` → 生成 `docs/feeds/*.xml` | 极少改（守卫会调） |
| `opml_generator.py` | 生成主 `docs/opml.xml` | 极少改 |
| `generate_opml_mirrors.py` | 生成 3 个 CDN 镜像 OPML | 极少改 |
| `generate_feeds_index.py` | 生成 `docs/index.html` 订阅目录 | 极少改 |
| `health_check.py` | **一致性**体检（源↔feed↔OPML 孤儿核对），孤儿脚本未接 CI | 诊断一致性时手动跑 |
| `quality_check.py` | **内容级**体检器（守卫核心，见 §4） | 守卫调用，不手动改 |
| `quality_fix.py` | 内容垃圾自动修复器（守卫调用） | 守卫调用，不手动改 |
| `items.json` / `items_latest.json` | 全库条目（5.5 MB） | CI 自动改；手动改需谨慎 |
| `feeds_meta.json` | 每源条目计数（诊断用） | CI 自动改 |
| `docs/` | GitHub Pages 部署目录（`feeds/`、`opml*.xml`、`index.html`、`icons/`、`version.txt`） | CI 自动改 |
| `.github/workflows/` | 9 个 CI 工作流（见 §3） | 调频率/流程时 |

> 更通俗的英文新人文档见根目录 `ONBOARDING.md`（早期版，状态数字偏旧，以本手册为准）。

---

## 3. 自动化全景（CI 频率表，实测 cron）

| 工作流 | 触发（北京时间） | 职责 |
|---|---|---|
| `crawl.yml` | 每 **30 分**整 + 07:00/12:00/18:00/22:00 定点 | 全源爬取 → 增量更新 feed/OPML/index；含「停滞检测 + 内容质量体检」 |
| `fast_check.yml` | 每 **15 分**（:00/:15/:30/:45） | 高频快查，捕获活跃源新线报 |
| `freshness-watchdog.yml` | 每 **20 分** | 停滞源自愈（强制重爬 + 告警） |
| `quality-guard.yml` | **每小时 :17 分**（2026-07-22 由每6h升级） | **内容级体检 → 自动修复 → 开 Issue 闭环**（本手册核心） |
| `daily_summary.yml` | 每天 **22:00** | 日报汇总 |
| `blacklist-check.yml` | push `sites.yaml` 时 | 黑名单校验 |
| `test.yml` | push 时 | 单元测试 |
| `cleanup-history.yml` | 手动 | 清理历史 |
| `trigger-pages.yml` | 手动 | 触发 Pages 重建 |

> 所有定时流均支持 `workflow_dispatch`（Actions 页面手动 Run），调试时可直接触发。

---

## 4. 质量守卫机制（核心，ONBOARDING 未覆盖）

> 这是本项目的「质量防火墙」。把「检测预案」从 health_check 的**仅一致性**升级为**内容感知**。

### 4.1 三件套

| 组件 | 角色 |
|---|---|
| `quality_check.py` | 内容级体检：扫 feed 输出 + 扫 `items.json` 全库 + 一致性核对。退出码 `0`=干净，`1`=有垃圾/不一致 |
| `quality_fix.py` | 自动修复：删 TIER-1 垃圾 → 删受影响源陈旧 XML → 调 `rss_feed.py`/`opml_generator.py`/`generate_opml_mirrors.py`/`generate_feeds_index.py` 重生重建（**不负责 push**） |
| `quality-guard.yml` | 每小时触发：跑 check → 若 `exit 1` 则跑 fix + 提交推送 + 对无 parser 脏源开 Issue |

### 4.2 链路

```
每小时 :17 触发
  → quality_check.py
      ├─ 扫描 docs/feeds/*.xml（输出级，突破 feed 2000 条上限掩盖）
      ├─ 扫描 items.json 全库活跃源（防脏库被下次 crawl 写回 feed）
      └─ 一致性核对（源↔feed↔OPML↔索引）
  → 退出码 0（干净）：整轮跳过，零提交噪声
  → 退出码 1（有垃圾）：
      → quality_fix.py 自动清理 + 强制重生受影响 feed + 重建 OPML/index
      → 守卫流提交推送（数据文件 ours 策略，见 §6.2）
      → 对「无专用 parser 的复发脏源」开汇总 Issue（提示加 parser 根治）
```

### 4.3 TIER-1 垃圾规则（高查准：宁可漏报也不误删）

`quality_check.classify_junk(url, text)` 仅判定**明确垃圾**：

| 判定为垃圾（安全可自动清理） | 规则 |
|---|---|
| 空 URL | `not url.strip()` |
| 分类页 | path 含 `/category` |
| 论坛/系统页 | `/forum.php` `/plugin.php` `/portal.php` |
| 论坛板块列表 | `/forum-` |
| 导航页 | `/about(?|$|/)` |
| 广告标题 | `text.startswith("广告")` |

**明确不判垃圾（避免误删合法内容，务必牢记）**：

- **外站跳转链接**：`u.jd.com` / `m.tb.cn` / `s.click.taobao.com` 等是羊毛党站合法的京东/淘宝/商户跳转短链，删了会破坏 feed
- **根路径 `/`**：多为 feed 自身频道 `<link>` 或首页条目
- **`/group/topic/`**：豆瓣小组真实帖子（开心赚源）
- **`/docs`、`/tag/`** 等：部分站点用作真实文章路径

### 4.4 parserless（无 parser 脏源）判定

守卫对「有垃圾但无专用 parser」的源开 Issue，提示加 parser 才能根治复发。判定逻辑（`quality_check.py:registered_hosts` + parserless 比对）有两处易错点，已修复（见 §5 的 #137）：

1. `registered_hosts()` **不导入 `crawler` 模块**（Actions 轻量环境导入易失败返回空集 → 误判全部源 parserless）；改为**文本解析** `core.py` 的 `PARSER_REGISTRY` 键名，零导入。
2. parserless 比对**统一去 `www.` 前缀**（`sites.yaml` 用 `www.zuankeba.cn`，注册表用 `zuankeba.cn`）。

### 4.5 Issue 防重复

守卫开 Issue 前会按相同标题去重（`gh issue list --search`），不会每小时重复刷 Issue。

---

## 5. 历史修复记录（关键源质量史，备查）

| 源 | 问题 | 处理（提交） |
|---|---|---|
| 线报酷 / 专业线报 | fallback 误抓 `/category-*`、forum.php、外站引流 | 新增 `parse_ixbk_items` / `parse_zhuanyes_items`，注册 `news.ixbk.net`/`ixbk.net`/`zhuanyes.com`（含 www），清库 + 强制重生（提交 `bbfa6ee4`） |
| 超级线报 / 白菜哦 / 枫音 / 鸭先知 / APP喵 | fallback 残留（后三者已不在 sites.yaml，属死库噪音） | 清库 52 条（已备份 /tmp） |
| 赚客吧（zuankeba） | 既有 `parse_zuankeba_items`，曾被误报「无 parser」 | 修复 `registered_hosts` 文本解析 + www 归一化，关闭误报 Issue #137（提交 `0ed141bf`） |
| 网猴线报 | 改了 parser 却忘清库，CI 把脏库写回 feed 导致回潮 | 教训固化：改 parser **必须删陈旧 XML 强制重生**（quality_fix 已内置此步） |
| 开心赚（douban） | 误报 24 条「板块」（`/group\b` 规则误杀） | 规则收紧为排除 `/group/topic/`，真实帖子**非垃圾，未动** |
| iehou / cjx8 / xuankeba / ai-Q / xianbao 等 | 早期质量修复 + 清库 + 注册 parser | 已注册于 `core.py` |

> 详细结果见 `MAINTENANCE/` 目录归档文档。

---

## 6. 已知坑 / 必读注意事项（接手者最容易踩）

### 6.1 增量跳过 → 改 parser 必须删陈旧 XML
`rss_feed.py` 对未变化源跳过重生。改了 parser 后**必须删掉该源陈旧 XML** 才能强制重生，否则脏 feed 残留（网猴线报回潮教训）。`quality_fix.py` 已内置「删受影响源 XML → 重生」流程，手动改 parser 后请照做。

### 6.2 CI 并发冲突 → ours 策略
多个定时流（crawl/fast_check/guard）可能同时 push。提交策略（`quality-guard.yml` 已实现）：
- `git pull --no-rebase`（非 rebase）
- 冲突时 **数据文件**（`items.json` / `docs/feeds/*` / `docs/opml*.xml` / `docs/index.html` / `docs/icons/*`）`git checkout --ours`（保留本守卫已清理/生成版本）
- 其余文件 `git checkout --theirs`
- 用 `--force-with-lease` 推送（含 5 次重试）

手动提交时也建议 `git pull --no-rebase -X ours` 后再 push，避免吞掉他人数据。

### 6.3 外站链接 / 根路径 / douban 不删
见 §4.3「明确不判垃圾」。任何「自动清理」脚本都**不得**扩展这些为垃圾，否则破坏合法 feed。

### 6.4 registered_hosts 不导入 crawler
见 §4.4。新增 parser 后，若守卫误报「无 parser」，先确认 `core.py` 的 `PARSER_REGISTRY` 键名是否带 `www.` 与 `sites.yaml` 一致。

### 6.5 items.json 5.5 MB，改库谨慎
手动改 `items.json` 时只做最小必要改动，避免整体重新序列化产生巨型 diff 污染历史。

---

## 7. 自主模式授权（用户原话精神）

金军已明确授权**全自主维护**：

> 「提高定时任务检测预案的质量，以及维护这个项目的频率。发现问题后，你可以全部自己完成。我相信你不需要主动问我的意见，自己全部维护和修复，发现问题及时去修复。」

即：守卫每小時自检，发现 TIER-1 垃圾自动清理重生，发现无 parser 复发脏源开 Issue 提示，**不需主动征求用户意见**。涉及 `sites.yaml` 源增删、频率调整等结构性变更时，仍建议事后告知或按用户新指令执行。

---

## 8. 接手操作指南（新助手动作清单）

### 8.1 本地环境
```bash
git clone <仓库> RSSForge && cd RSSForge
pip install -r requirements.txt        # Python 3.11
```

### 8.2 手动体检 / 修复（调试用）
```bash
python3 quality_check.py               # 内容级体检，看 stdout 报告 + quality_report.json
python3 quality_fix.py                 # 仅在有垃圾时跑；会改 items.json + 重生 feed
python3 health_check.py                # 仅一致性体检（孤儿脚本，未接 CI）
```

### 8.3 常用 gh 命令
```bash
export GH_TOKEN=<你的 PAT 或 GITHUB_TOKEN>
gh repo view gitfox-enter/RSSForge
gh run list -R gitfox-enter/RSSForge --workflow=quality-guard.yml --limit 5
gh workflow run quality-guard.yml -R gitfox-enter/RSSForge          # 手动触发守卫
gh issue list -R gitfox-enter/RSSForge --state open
gh issue close 137 -R gitfox-enter/RSSForge -c "原因说明"
```

### 8.4 提交策略（防并发冲突）
```bash
git add <具体文件>                      # 不要 git add -A
git commit -m "feat/fix: 说明"
git pull --no-rebase -X ours origin main
git push origin main --force-with-lease
```

### 8.5 部署
push 到 `main` 即触发 Pages 重建（`crawl.yml` 等会提交 `docs/`）。无需额外部署步骤。

---

## 9. 凭据与安全（重要）

| 场景 | 凭据 |
|---|---|
| **GitHub Actions 内** | 用 `secrets.GITHUB_TOKEN`（仓库自动提供，`permissions: contents: write, issues: write`）。**勿改**。 |
| **本地 push** | 本机 git remote 已配置 **classic PAT**（`ghp_...`，scope: `repo`）。复用同一环境即可直接 `git push`。 |

⚠️ **安全提醒**：
1. **切勿把 PAT 明文写进仓库或公开文档**——GitHub 会自动检测并撤销泄露的 token。
2. 当前本机 `git remote -v` 的 HTTPS URL **已内含明文 PAT**。Clone 到新环境会带上该凭据，存在扩散风险。建议接手者改用 **SSH** 或 `git config --global credential.helper store`，并向金军索取独立 PAT。
3. PAT 若失效：向 **金军（gitfox-enter）** 索取新的 classic PAT（scope: `repo`）。

---

## 10. 交接检查清单（Checklist）

- [ ] `git clone` 成功，`pip install -r requirements.txt` 通过
- [ ] 本地跑通 `python3 quality_check.py`，理解 TIER-1 规则与 §4.3「不删清单」
- [ ] 理解质量守卫三件套与每小时链路（§4）
- [ ] 配好 PAT / SSH 凭据（§9），能 `git push`
- [ ] 在 Actions 页面确认 `quality-guard.yml` 最近一次运行 success
- [ ] 读过 `MAINTENANCE/` 下历史修复文档
- [ ] 记住 §6 五个已知坑

---

## 11. 历史维护文档索引（`MAINTENANCE/`）

| 文件 | 内容 |
|---|---|
| `MAINTENANCE/RSSForge_维护总结_2026-07-19.md` | 全权维护首轮总览：状态、CI 频率、质量守卫、TIER-1 规则、误报修复 #137、自主模式声明 |
| `MAINTENANCE/RSSForge_修复说明.md` | 质量修复说明 |
| `MAINTENANCE/羊毛党_源更新说明.md` | 羊毛党类源更新说明 |
| `MAINTENANCE/删除优惠线报_结果.md` | 删除「优惠线报」源结果 |
| `MAINTENANCE/删除我不找_结果.md` | 删除「我不找」源结果 |
| `MAINTENANCE/删除无关feed_结果.md` | 删除无关 feed 结果 |
| `MAINTENANCE/删除网猴线报_结果.md` | 删除「网猴线报」源结果（回潮教训来源） |

> 根目录 `ONBOARDING.md` 为英文新人文档（早期状态，数字偏旧），可作补充参考。
