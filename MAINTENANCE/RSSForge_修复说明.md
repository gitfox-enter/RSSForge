# RSSForge feed 条目数修复说明

> 针对问题：「部分 rss 条目数量不满 1000 就被清理了，导致数量一直都是几十个」

## 一、根因（关键澄清）

**真正的清理原因不是 1000 阈值。** `rss_feed.py` 里的 `MAX_FEED_ITEMS=1000` 只是「每个 feed 最多保留最近 N 条」的**截断上限**，不是「低于 1000 就删」的阈值——这个常量从未删过任何条目。

真正的根因在 `crawler/storage.py` 的 `merge_items_into_db()`：

> 它用 **7 天（time 字段）/ 3 天（first_seen_at）** 的时间窗口清理全量库。

后果：每个源在数据库里只保留最近几天的条目，单源长期只有「几十个」，feed 自然喂不满。线上还叠加了一个更糟的情况——CI 用**旧代码**跑了一次，把 16 个历史 feed 直接删掉，只留下约 10 个用 7 天窗口生成的小 feed。

## 二、已修复内容（已提交并推送）

| 文件 | 改动 | 作用 |
|------|------|------|
| `crawler/storage.py` | 留存窗口 7天→**60天**、3天→**30天** | 防止未来再次被砍小，feed 计数不再跌回几十 |
| `rss_feed.py` | `MAX_FEED_ITEMS` 1000→**2000**（两处） | 大源（汇发部/线报酷）能真正填满 |
| `rss_feed.py` | 无数据的源**不再删除**其 feed 文件 | 某源在抓取窗口内没数据时，feed 不被误清空 |
| `rss_feed.py` | **禁用**「删除不在 SOURCE_NAME_MAP 的 feed」逻辑 | 杜绝 CI 把 16 个历史 feed 清掉 |
| 全量 feed | 清空 `feeds_meta.json` 哈希缓存，用当前 **16,921 条**大库强制重生成 | 立即让线上计数涨上来 |
| 16 个历史 feed | 从备份恢复（CI 旧代码曾删除） | 订阅不被打断 |
| 首页索引 / OPML | 跟随重生成 | 目录页与订阅文件同步 |

提交记录：`644bf1fe`（根因修复）→ 合并 CI 最新数据 → `861afd7e`（恢复历史 feed + 重生成并推送）。
**下一次 CI 跑的就是修复后的代码**，不会再删历史 feed、留存窗口已是 60 天。

## 三、当前线上 feed 计数（已验证）

| feed | 条目数 | 说明 |
|------|-------:|------|
| 汇发部 (hui-fa-bu) | **2000** | 2000 封顶 |
| 线报酷 (xian-bao-ku) | **2000** | 2000 封顶 |
| 线报ICU (xian-bao-ICU) | 976 | |
| 专业线报 (zhuan-ye-xian-bao) | 634 | |
| 白菜哦 (bai-cai-o) | 503 | |
| 赚客吧 (zhuan-ke-ba) | 296 | |
| 超级线报 (chao-ji-xian-bao) | 180 | |
| 爱Q社区 (ai-Q-she-qu) | 166 | |
| 线报网 (xian-bao-wang) | 89 | |
| 网猴线报 (wang-hou-xian-bao) | 33 | |
| 16 个历史 feed | 保留 | 订阅不断，目录页可见 |

## 四、OPML 列全 feed 问题（已修复）

原来 `generate_opml_mirrors.py` 只读 `feeds_meta.json`（仅 10 个数据源），且最后把
`opml.xml` 覆盖成 10 条，导致 OPML 与首页（26 个）不一致。

**已修复**：让镜像脚本复用 `opml_generator._load_feeds()` 枚举 `docs/feeds/*.xml` 全部 feed，
4 个 OPML（official / ghfast / jsdelivr / 主）现均列 **27 个**（含历史 feed + 新增 yang-mao-xian-bao）。
提交 `72cb424c` → 合并 → `bbdc3ecb`。线上已验证：3 个 OPML 均 27 个。

## 五、验证方式

线上直连 GitHub Pages（部署后实拉）：
```
opml.xml / opml.ghfast.xml / opml.jsdelivr.xml  -> 各 27 个
xian-bao-ku.xml -> 2000 条
hui-fa-bu.xml   -> 2000 条
xian-bao-ICU.xml -> 982 条
zhuan-ye-xian-bao.xml -> 635 条
```
