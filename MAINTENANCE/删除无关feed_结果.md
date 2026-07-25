# 删除 3 个与羊毛无关 feed — 结果

**时间**：2026-07-13 | **提交**：`0dc62a77` | **状态**：已推送，线上已生效

## 已删除的 feed

| feed 文件 | 源名称 | 原 sites.yaml 行 | 线上状态码 |
|---|---|---|---|
| `ReadHub-re-men.xml` | ReadHub 热门 | 行 35 | 404 ✅ |
| `hao-zhuan-wang.xml` | 好赚网 | 行 89 | 404 ✅ |
| `H6-xian-bao.xml` | H6线报 | 行 41 | 404 ✅ |

## 同步改动

- **`sites.yaml`**：已移除上述 3 个源配置（否则 CI 下次运行会重新生成它们，删除白做）。`sites` 总数 `27 → 24`。
- **`docs/index.html`**：重生成，目录页 feed 数 `27 → 24`。
- **4 个 OPML**（`opml.xml` / `opml.official.xml` / `opml.ghfast.xml` / `opml.jsdelivr.xml`）：重生成，均 `27 → 24` 个 `<outline>`。

## 线上验证（GitHub Pages 已重建）

| 校验项 | 结果 |
|---|---|
| 4 个 OPML outline 数 | 24 / 24 / 24 / 24 ✅ |
| 3 个已删 feed | 均 404 ✅ |
| 首页 index.html 列出 feed | 24 ✅ |

## 备注

- 备份保留在 `/root/.codebuddy/artifact/backup_del_20260719_073533/`（H6-xian-bao.xml、hao-zhuan-wang.xml、ReadHub-re-men.xml），需恢复可随时取用。
- `feeds_meta.json` / `items.json` 中无这 3 个源的历史键，无需清理增量缓存。
- CI 正常增量更新其余 feed，已通过 `merge -X ours` 合并、未受影响。
