# Cloudflare Worker 定时触发器

解决 GitHub Actions cron 调度延迟问题（实际延迟可达数小时）。

## 部署步骤

### 1. 安装 Wrangler CLI
```bash
npm install -g wrangler
```

### 2. 登录 Cloudflare
```bash
wrangler login
```

### 3. 设置 GitHub Token
需要一个有 `repo` 权限的 Personal Access Token：
```bash
wrangler secret put GITHUB_TOKEN
```

### 4. 部署
```bash
cd cloudflare-worker
wrangler deploy
```

### 5. 验证
部署成功后，访问 Worker URL 应返回健康检查信息。

## 触发策略

| 时间 | 触发的工作流 |
|------|------------|
| :00  | crawl.yml (全量爬取) |
| :15  | fast_check.yml (快速检查) |
| :30  | crawl.yml (全量爬取) |
| :45  | fast_check.yml (快速检查) |

## 手动触发

```bash
# 触发全量爬取
curl -X POST https://your-worker.workers.dev/trigger/crawl

# 触发快速检查
curl -X POST https://your-worker.workers.dev/trigger/fast_check
```

## 注意事项

- Worker 免费计划每天 10 万次请求，完全够用
- 如需调整频率，修改 wrangler.toml 中的 crons 配置
- 部署后可以关闭 GitHub Actions 的 cron 调度（保留 workflow_dispatch）
