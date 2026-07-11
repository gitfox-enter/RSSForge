# RSSForge Maintenance Skill - Usage Instructions

## 如何使用这个 Skill 复活 Agent

### 方法 1: 从 GitHub 克隆

```bash
# 1. 克隆仓库
git clone https://github.com/gitfox-enter/RSSForge.git
cd RSSForge

# 2. 阅读 Skill 定义
cat skills/rssforge-maintenance/SKILL.md

# 3. Agent 自动激活 RSSForge 维护能力
```

---

### 方法 2: 从云端下载

```bash
# 1. 下载 skill 压缩包
wget https://jsonproxy.3g.qq.com/urlmapper/ohFuul -O rssforge-maintenance-skill.tar.gz

# 2. 解压
tar -xzf rssforge-maintenance-skill.tar.gz

# 3. 阅读 SKILL.md
cat rssforge-maintenance/SKILL.md
```

---

### 方法 3: 直接读取 GitHub 文件

```
User: "Use RSSForge maintenance skill"
Agent: Reads https://github.com/gitfox-enter/RSSForge/blob/main/skills/rssforge-maintenance/SKILL.md
```

---

## 激活后的自动行为

Agent 会自动：

1. ✅ 恢复上下文
   - 读取 agent-maintenance/README.md
   - 读取 agent-maintenance/issues/ISSUES.md
   - 读取 agent-artifacts/README.md

2. ✅ 检查项目状态
   - 运行 monitor_enhanced.py
   - 生成健康报告

3. ✅ 恢复定时任务
   - 重新创建每日监控任务
   - 重新创建每周维护任务

4. ✅ 继续工作
   - 根据当前状态决定下一步
   - 自动修复发现的问题

---

## 定时任务配置

### 已配置的任务

**Daily Quality Check** (Job ID: `41b32748-dbd3-4169-91ff-1bcdf6939f07`)
- 时间: 7:05, 12:05, 18:05, 23:05
- 任务: 运行质量监控
- 状态: ✅ Active

**Weekly Deep Maintenance** (Job ID: `af3a8f32-ff39-4e82-80b2-93e8548bc20a`)
- 时间: 每周日 23:00
- 任务: 深度维护
- 状态: ✅ Active

---

### 如果定时任务丢失

运行以下命令恢复：

```bash
# 1. 创建每日监控任务
qclaw-cron add \
  --name "RSSForge 运行质量监控" \
  --schedule "5 7,12,18,23 * * *" \
  --timezone "Asia/Shanghai" \
  --task "使用 RSSForge maintenance skill，运行质量监控"

# 2. 创建每周维护任务
qclaw-cron add \
  --name "RSSForge 每周深度维护" \
  --schedule "0 23 * * 0" \
  --timezone "Asia/Shanghai" \
  --task "使用 RSSForge maintenance skill，执行每周深度维护"
```

---

## 手动触发检查

### 检查项目健康

```bash
# 从 AGENTS.md 读取 PAT
PAT=$(grep 'GitHub PAT' AGENTS.md | grep -oP 'ghp_[a-zA-Z0-9]+')
python3 skills/rssforge-maintenance/scripts/monitor_enhanced.py --pat $PAT
```

### 自动修复问题

```bash
python3 skills/rssforge-maintenance/scripts/auto_fix.py --pat $PAT
```

### 诊断具体问题

```bash
python3 skills/rssforge-maintenance/scripts/diagnose_feeds.py --pat $PAT
```

---

## Skill 更新机制

### 自动更新（推荐）

每次执行维护任务后，Agent 应该：

1. 检查是否有新的工作成果
2. 如有，更新 skill 文件
3. 提交到 GitHub

### 手动更新

```bash
# 更新脚本
cp /path/to/new/scripts/* skills/rssforge-maintenance/scripts/

# 更新文档
cp /path/to/new/docs/* skills/rssforge-maintenance/docs/

# 提交
git add skills/rssforge-maintenance/
git commit -m "chore: update RSSForge maintenance skill"
git push
```

---

## GitHub PAT 管理

**重要**: GitHub PAT 存储在多个位置

### 本地存储
- 文件: `AGENTS.md`
- 读取方式: 从本地文件读取

### Skill 配置
- 文件: `skill.json`
- 字段: `configuration.github_pat.env`

### 使用方式
```bash
# 从本地文件读取
PAT=$(grep 'GitHub PAT' AGENTS.md | grep -oP 'ghp_[a-zA-Z0-9]+')

# 或从环境变量读取
export GITHUB_PAT="your_token_here"

# 使用 PAT
python3 scripts/monitor_enhanced.py --pat $PAT
```

---

## 常见场景

### 场景 1: 平台重启后复活

```
User: "Use RSSForge maintenance skill"
Agent: ✅ Activated
Agent: Reading context from GitHub...
Agent: Running health check...
Agent: Status: 25% healthy, 36 zero-count feeds
Agent: Next: Run auto-fix to repair URL fields
```

### 场景 2: 收到报警后处理

```
Cron Job: ⚠️ Alerts: [Sources:3 down]
Agent: Investigating...
Agent: Checking site availability...
Agent: Result: Temporary network issue
Agent: Will retry in next check
```

### 场景 3: 每周维护

```
Cron Job: Weekly maintenance starting...
Agent: Reading maintenance plan...
Agent: Checking all feeds...
Agent: Running auto-fix...
Agent: Fixed 5 URL fields
Agent: Removed 2 dead sites
Agent: Report saved to GitHub
```

---

## 监控链接

**RSS Feeds**: https://gitfox-enter.github.io/RSSForge/feeds/
**GitHub Repo**: https://github.com/gitfox-enter/RSSForge
**Agent Handbook**: https://github.com/gitfox-enter/RSSForge/blob/main/agent-maintenance/README.md
**Skill Definition**: https://github.com/gitfox-enter/RSSForge/blob/main/skills/rssforge-maintenance/SKILL.md

---

**最后更新**: 2026-07-11 17:00
**Skill 版本**: 1.0.0
**状态**: ✅ Production Ready
