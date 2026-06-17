# 快速开始

三步让你的 RSSForge 跑起来。

## 第一步：Fork 仓库

点击 GitHub 右上角 **Fork**，将仓库复制到你的账号下。

```
https://github.com/gitfox-enter/RSSForge  →  你的 Fork
```

## 第二步：修改 sites.yaml

在仓库根目录找到 `sites.yaml`，按格式添加你想订阅的网站：

```yaml
sites:
  - url: "https://news.ixbk.fun/"
    name: 线报酷          # 显示名称
    tier: high            # high/mid/low，影响抓取频率
    interval: 15          # 抓取间隔（分钟）
    fast_check: true     # 是否启用快速检查模式
    max_pages: 3         # 首次回填抓取历史页数（可选）
```

每个字段的含义：

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `url` | ✅ | 目标网站地址 | `https://example.com/` |
| `name` | ✅ | 显示名称 | `示例网站` |
| `tier` | - | 等级（影响优先级） | `high` / `mid` / `low` |
| `interval` | - | 抓取间隔（分钟） | `30` |
| `fast_check` | - | 快速检查模式（只检测变化，不解析内容） | `true` / `false` |
| `max_pages` | - | 首次回填时抓取的历史页数（默认 1） | `5` |

## 第三步：开启 GitHub Pages

1. 进入仓库 **Settings → Pages**
2. Source 选择 **GitHub Actions**
3. Actions 会自动触发第一次运行

等待 1-2 分钟，打开你的 GitHub Pages 地址：

```
https://你的用户名.github.io/RSSForge/
```

就能看到订阅源列表了。

## 订阅第一个 RSS

在首页找到你想订阅的网站，点击 **订阅** 按钮获取 feed 地址，粘贴到 RSS 阅读器即可。

推荐使用 [Folo](https://folo.io)（AI RSS 阅读器，支持 RSSForge），也可以用 Inoreader、Reeder、NetNewsWire 等。

## 下一步

- [配置更新频率](/config/schedule) — 调整站点的抓取间隔
- [开启历史回填](/config/pagination) — 首次订阅时拉取历史内容
- [OPML 批量订阅](/feeds/opml) — 一次订阅全部站点
