#!/bin/bash
# RSSForge 自动检查脚本
# 用途: 平台重启后快速恢复上下文

WORKSPACE="/home/node/.openclaw/workspace/agent-606489db"

echo "=== RSSForge 维护系统启动检查 ==="
echo ""

# 检查核心信息文件
if [ -f "$WORKSPACE/RSSFORGE_CORE.md" ]; then
    echo "✅ 核心信息文件存在"
    echo "   - 项目仓库: https://github.com/gitfox-enter/rssforge"
    echo "   - 我的角色: RSSForge 全栈运维 Agent"
else
    echo "❌ 核心信息文件不存在，需要重建"
fi

# 检查最新日志
LATEST_LOG=$(ls -t $WORKSPACE/memory/*.md 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "✅ 最新日志: $LATEST_LOG"
    echo "   内容预览:"
    head -10 "$LATEST_LOG" | sed 's/^/   /'
else
    echo "⚠️  没有找到日志文件"
fi

# 检查 feeds_meta.json
if [ -f "$WORKSPACE/rssforge-maintain/feeds_meta.json" ]; then
    echo "✅ feeds_meta.json 存在"
    HEALTHY=$(jq '[.[] | select(.count > 0)] | length' $WORKSPACE/rssforge-maintain/feeds_meta.json 2>/dev/null || echo "?")
    TOTAL=$(jq 'keys | length' $WORKSPACE/rssforge-maintain/feeds_meta.json 2>/dev/null || echo "?")
    echo "   - 健康站点: $HEALTHY / $TOTAL"
else
    echo "❌ feeds_meta.json 不存在"
fi

echo ""
echo "=== 下一步行动 ==="
echo "1. 读取 RSSFORGE_CORE.md 了解项目背景"
echo "2. 读取最新日志了解最近工作"
echo "3. 决定本次需要执行的任务"
echo ""
echo "如需执行每周任务，请说: '执行每周日深夜任务'"
