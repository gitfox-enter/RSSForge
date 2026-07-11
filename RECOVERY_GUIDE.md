# 🚨 Agent 紧急复活指南

> 如果 QClaw 平台挂掉，使用此指南恢复 Agent 工作

## 📍 关键位置

### GitHub 仓库（最重要）
**主仓库**: https://github.com/gitfox-enter/RSSForge

**工作手册**: https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/README.md

**工作成果**: https://github.com/gitfox-enter/RSSForge/blob/main/agent-artifacts/README.md

### 本地文件（备用）
**核心信息**: `/home/node/.openclaw/workspace/agent-606489db/RSSFORGE_CORE.md`

**工作日志**: `/home/node/.openclaw/workspace/agent-606489db/memory/2026-07-11.md`

---

## 🔧 复活步骤

### 方案 1: 使用 GitHub 恢复（推荐）

1. **访问工作手册**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/README.md
   ```

2. **读取关键信息**
   - 我的身份和使命
   - 当前状态（健康/失效站点）
   - 工作流程
   - 决策记录

3. **检查 Issues 列表**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/issues/ISSUES.md
   ```

4. **读取最新日志**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/logs/
   ```

5. **恢复定时任务**
   - 运行质量监控: 每天 7:05, 12:05, 18:05, 23:05
   - 每周维护: 每周日 23:00

---

### 方案 2: 使用本地文件恢复

1. **读取核心信息**
   ```bash
   cat /home/node/.openclaw/workspace/agent-606489db/RSSFORGE_CORE.md
   ```

2. **读取工作日志**
   ```bash
   cat /home/node/.openclaw/workspace/agent-606489db/memory/2026-07-11.md
   ```

3. **读取 PAT**
   ```bash
   grep "GitHub PAT" /home/node/.openclaw/workspace/agent-606489db/AGENTS.md
   ```

4. **克隆仓库**
   ```bash
   git clone https://github.com/gitfox-enter/RSSForge.git
   cd RSSForge
   ```

---

### 方案 3: 使用工作成果恢复

1. **访问工作成果索引**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/agent-artifacts/README.md
   ```

2. **查看任务总结**
   ```
   https://github.com/gitfox-enter/RSSForge/tree/main/agent-artifacts/task-summaries
   ```

3. **下载监控脚本**
   ```
   https://github.com/gitfox-enter/RSSForge/blob/main/agent-artifacts/scripts/monitor.sh
   ```

---

## 🔑 关键凭证

### GitHub PAT
**存储位置**: `/home/node/.openclaw/workspace/agent-606489db/AGENTS.md`

**权限**: 仓库读写权限

**用途**:
- 提交代码修改
- 访问 GitHub API
- 检查 Actions 运行状态

**注意**: 不要提交到公开仓库！

---

## 📊 当前项目状态

### 健康站点 (12/48)
- 线报酷 (7609)、汇发部 (7376) - 高频核心源
- 线报ICU (1013)、专栏吧 (524) - 稳定更新
- 其他 8 个站点保持更新

### 疑似失效站点 (36/48)
- 高频 (13): 线报迷、小角落、ReadHub、羊毛系列等
- 中频 (10): 好赚网、活动5、IT之家等
- 低频 (13): 软件下载类、资讯类

### 监控系统
- ✅ 运行质量监控: 每天 4 次
- ✅ 每周深度维护: 每周日 23:00
- ✅ 监控脚本: monitor.sh

---

## 🎯 立即执行的任务

### 高优先级
1. **验证 36 个疑似失效站点**
   - 抽查 HTTP 状态
   - 区分域名失效/解析失败/正常
   - 记录结果到 Issues

2. **清理确认失效的站点**
   - 从 sites.yaml 移除
   - 更新 README.md
   - commit + push

### 中优先级
1. **全文抓取功能实现**
   - 修改 engine.py
   - 配置 sites.yaml
   - 测试验证

---

## 📞 联系信息

**维护者**: Agent-606489db

**用户 ID**: u:1158536988

**项目仓库**: https://github.com/gitfox-enter/RSSForge

---

## 🔍 验证恢复成功

执行以下命令验证系统正常：

```bash
# 1. 检查 GitHub Actions 状态
curl -H "Authorization: token YOUR_PAT" \
  https://api.github.com/repos/gitfox-enter/RSSForge/actions/workflows/crawl.yml/runs?per_page=1

# 2. 检查 feeds_meta.json
curl https://raw.githubusercontent.com/gitfox-enter/RSSForge/main/feeds_meta.json

# 3. 运行监控脚本
bash monitor.sh
```

---

## 📝 记住

**所有工作内容都在 GitHub 仓库中**：
- `agent-maintenance/` - 维护手册（第一人称）
- `agent-artifacts/` - 工作成果（客观记录）
- `feeds_meta.json` - Feed 元数据
- `sites.yaml` - 站点配置

**只要 GitHub 还在，我就能恢复工作！**

---

**最后更新**: 2026-07-11 16:10
**文档版本**: 1.0
