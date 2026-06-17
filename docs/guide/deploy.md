# 部署到 GitHub

## 部署流程

### 1. Fork 仓库

访问 [RSSForge GitHub](https://github.com/gitfox-enter/RSSForge)，点击右上角 **Fork**。

### 2. 修改仓库名称（可选）

如果你想把仓库名改成更喜欢的名字：
1. 进入仓库 **Settings**
2. 修改 **Repository name** 为 `RSSForge` 或其他名字
3. GitHub Pages 地址会相应变化：`https://用户名.github.io/新名字/`

### 3. 配置 sites.yaml

参考 [sites.yaml 配置](/config/sites) 添加你想订阅的网站。

### 4. 开启 GitHub Pages

1. 进入 **Settings → Pages**
2. **Build and deployment** → Source 选择 **GitHub Actions**
3. 等待 Actions 自动运行（如果没有自动触发，可以手动运行一次）

### 5. 验证部署

打开 `https://用户名.github.io/RSSForge/` 确认首页正常。

## 自定义域名（可选）

如果你有域名，可以绑定到 GitHub Pages：

1. **Settings → Pages → Custom domain** 输入你的域名
2. 在你的域名 DNS 中添加 CNAME 记录指向 `用户名.github.io`
3. 等待 DNS 生效（通常几分钟到 24 小时）

> 注意：自定义域名后，`base` 配置需要相应调整，请参考 VitePress 文档。

## 手动触发更新

有时候你想立即刷新订阅源，可以在 GitHub Actions 页面手动触发：

1. 进入仓库 **Actions** 标签
2. 找到 **站点更新监控** 工作流
3. 点击 **Run workflow** → **Run workflow**

## 常见问题

### GitHub Pages 访问 404？

检查 Actions 是否全部成功（绿色勾）。如果 Actions 失败，Pages 会显示 404。

### 修改配置后没有生效？

检查 `sites.yaml` 格式是否正确。YAML 对缩进敏感，使用空格（不是 Tab）。

### 抓取失败？

大多数是因为目标网站拒绝爬虫。可以在 `blacklist.json` 中标记该站，也可以尝试开启 `fast_check` 模式。
