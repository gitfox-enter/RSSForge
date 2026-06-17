# sites.yaml 站点配置

`sites.yaml` 是 RSSForge 的核心配置文件，定义你想订阅的所有站点。

## 文件位置

仓库根目录：`sites.yaml`

## 完整字段说明

```yaml
sites:
  - url: "https://example.com/"
    name: 示例网站
    tier: high
    interval: 15
    fast_check: true
    max_pages: 3
    enabled: true
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | string | **必填** | 目标网站的完整 URL，必须以 `http://` 或 `https://` 开头 |
| `name` | string | **必填** | 站点显示名称，会显示在首页和 feed 标题中 |
| `tier` | string | `high` | 优先级等级，影响 Actions 调度顺序：`high` / `mid` / `low` |
| `interval` | int | `30` | 抓取间隔（分钟），实际间隔还会受 `fast_check` 和夜间权重影响 |
| `fast_check` | bool | `false` | 开启后只检测页面哈希变化，不解析内容（节省资源） |
| `max_pages` | int | `1` | 首次回填时抓取的历史页数，超过 1 会启用分页抓取 |
| `enabled` | bool | `true` | 是否启用，设为 `false` 则跳过该站点 |

## 配置示例

### 基础配置

```yaml
sites:
  - url: "https://news.ixbk.fun/"
    name: 线报酷
```

### 高频更新站点

```yaml
sites:
  - url: "https://www.zhuanyes.com/xianbao/"
    name: 专业线报
    tier: high
    interval: 15
```

### 需要历史回填的站点

```yaml
sites:
  - url: "https://www.douban.com/group/711811/"
    name: 豆瓣小组
    max_pages: 5        # 首次抓取5页历史内容
    interval: 60
```

### 只做变更检测（不解析内容）

```yaml
sites:
  - url: "https://status.example.com/"
    name: 服务状态页
    fast_check: true    # 只检测是否有变化，不提取具体内容
```

## 分类组织

建议按站点类型分类组织，用注释分隔：

```yaml
sites:
  # ============================================================
  # 综合线报站（更新频繁，15~30 分钟）
  # ============================================================
  - url: "https://news.ixbk.fun/"
    name: 线报酷
    tier: high
    interval: 15

  - url: "https://xianbao.icu/"
    name: 线报ICU
    tier: high
    interval: 15

  # ============================================================
  # 软件资源站（更新较慢，1~2 小时）
  # ============================================================
  - url: "https://www.423down.com/"
    name: 423down
    tier: mid
    interval: 60
```

## 注意事项

- **URL 必须唯一**：两个站点不能有完全相同的 URL
- **YAML 缩进**：使用空格缩进（2 个空格），不要使用 Tab
- **长 URL 建议加注释**：方便后续维护
- **定期清理**：不用的站点设为 `enabled: false`，不要直接删除（保留配置历史）
