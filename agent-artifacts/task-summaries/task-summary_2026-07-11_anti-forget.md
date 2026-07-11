# Task Summary - RSSForge 抗遗忘系统

## 目标
设计一个不会被平台重启影响的维护计划，确保 RSSForge 项目维护工作的连续性

## 解决方案

### 1. 核心信息持久化
创建 `RSSFORGE_CORE.md`，包含：
- 项目仓库地址和 GitHub PAT
- 我的角色和使命
- 维护任务清单
- 已完成的工作
- 健康指标

### 2. 日志系统
创建 `memory/YYYY-MM-DD.md`，记录：
- 每日工作内容
- 技术决策
- 遇到的问题
- 下一步计划

### 3. 自动检查脚本
`rssforge-maintain/check.sh`:
- 检查核心文件是否存在
- 显示最新日志预览
- 提示下一步行动

### 4. 定时提醒
每周日 23:00 自动提醒执行维护任务

## 文件结构
```
/home/node/.openclaw/workspace/agent-606489db/
├── RSSFORGE_CORE.md          # 核心信息（永久）
├── AGENTS.md                 # 已更新，包含 RSSForge 维护说明
├── memory/
│   └── 2026-07-11.md         # 今日日志
├── rssforge-maintain/
│   ├── check.sh              # 自动检查脚本
│   ├── feeds_meta.json       # feed 元数据
│   └── weekly-report_2026-07-11.md  # 周报
└── task-summary_2026-07-11_rssforge-weekly.md
```

## 恢复流程

### 平台重启后
1. 用户说"你还记得你的任务吗？"
2. 我读取 `RSSFORGE_CORE.md` 恢复上下文
3. 我读取 `memory/YYYY-MM-DD.md` 了解最近工作
4. 我继续执行未完成的任务

### 每周自动
- 周日 23:00 自动提醒
- 我读取核心信息
- 执行维护任务

## 关键改进
- ✅ 不依赖会话内存
- ✅ 所有信息写入文件
- ✅ 有自动检查脚本
- ✅ 有定时提醒机制
- ✅ 有清晰的恢复流程

## 下次启动指令
如果平台再次重启，直接说：
- "你还记得你的任务吗？"
- 或 "执行检查脚本"

我会自动读取文件恢复上下文。
