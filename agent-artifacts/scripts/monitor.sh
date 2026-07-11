#!/bin/bash
# RSSForge 运行质量监控脚本
# 用途：检查 GitHub Actions 运行状态、feeds 更新时间、异常检测

set -e

# 配置
REPO="gitfox-enter/RSSForge"
PAT=$(grep "GitHub PAT" /home/node/.openclaw/workspace/agent-606489db/AGENTS.md 2>/dev/null | grep -oP 'ghp_[a-zA-Z0-9]+' || echo "")
API_BASE="https://api.github.com/repos/$REPO"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 RSSForge 运行质量检查 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# 1. 检查 GitHub Actions 最新运行状态
echo ""
echo "📊 GitHub Actions 运行状态："
if [ -n "$PAT" ]; then
    RUNS=$(curl -s -H "Authorization: token $PAT" \
        "$API_BASE/actions/workflows/crawl.yml/runs?per_page=3" 2>/dev/null)

    if [ -n "$RUNS" ]; then
        echo "$RUNS" | grep -oP '"status":\s*"\K[^"]+' | head -3 | while read status; do
            echo "  - 状态: $status"
        done
        echo "$RUNS" | grep -oP '"conclusion":\s*"\K[^"]+' | head -3 | while read conclusion; do
            if [ "$conclusion" = "success" ]; then
                echo -e "  ${GREEN}✅ 结果: $conclusion${NC}"
            else
                echo -e "  ${RED}❌ 结果: $conclusion${NC}"
            fi
        done
        echo "$RUNS" | grep -oP '"created_at":\s*"\K[^"]+' | head -1 | while read time; do
            echo "  - 时间: $time"
        done
    else
        echo -e "  ${YELLOW}⚠️  无法获取运行记录${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  未找到 GitHub PAT${NC}"
fi

# 2. 检查 feeds_meta.json 更新时间
echo ""
echo "📡 Feeds 更新状态："
META_URL="https://raw.githubusercontent.com/$REPO/main/feeds_meta.json"
META_LOCAL="/tmp/feeds_meta_$(date +%Y%m%d).json"

if curl -s -o "$META_LOCAL" "$META_URL" 2>/dev/null; then
    # 获取文件最后修改时间（从 GitHub API）
    META_INFO=$(curl -s -H "Authorization: token $PAT" \
        "$API_BASE/contents/feeds_meta.json" 2>/dev/null)

    if [ -n "$META_INFO" ]; then
        UPDATED_AT=$(echo "$META_INFO" | grep -oP '"updated_at":\s*"\K[^"]+' || echo "未知")
        echo "  - 最后更新: $UPDATED_AT"

        # 检查是否超过 2 小时
        if [[ "$UPDATED_AT" != "未知" ]]; then
            UPDATED_TS=$(date -d "$UPDATED_AT" +%s 2>/dev/null || echo "0")
            NOW_TS=$(date +%s)
            DIFF=$((NOW_TS - UPDATED_TS))
            HOURS=$((DIFF / 3600))

            if [ $HOURS -gt 2 ]; then
                echo -e "  ${RED}⚠️  已超过 $HOURS 小时未更新${NC}"
            else
                echo -e "  ${GREEN}✅ 更新正常（${HOURS}小时前）${NC}"
            fi
        fi
    fi

    # 统计 feeds 数量
    TOTAL=$(grep -o '"count":' "$META_LOCAL" | wc -l)
    HEALTHY=$(grep -oP '"count":\s*\K[1-9][0-9]*' "$META_LOCAL" | wc -l)
    FAILED=$((TOTAL - HEALTHY))

    echo "  - 总站点数: $TOTAL"
    echo -e "  - ${GREEN}健康站点: $HEALTHY${NC}"
    if [ $FAILED -gt 0 ]; then
        echo -e "  - ${RED}疑似失效: $FAILED${NC}"
    fi
else
    echo -e "  ${RED}❌ 无法获取 feeds_meta.json${NC}"
fi

# 3. 检查最近的 commit
echo ""
echo "📝 最近提交："
if [ -n "$PAT" ]; then
    COMMITS=$(curl -s -H "Authorization: token $PAT" \
        "$API_BASE/commits?per_page=3" 2>/dev/null)

    if [ -n "$COMMITS" ]; then
        echo "$COMMITS" | grep -oP '"message":\s*"\K[^"]+' | head -3 | while read msg; do
            echo "  - $msg"
        done
    fi
fi

echo ""
echo "========================================"
echo "✅ 检查完成"
