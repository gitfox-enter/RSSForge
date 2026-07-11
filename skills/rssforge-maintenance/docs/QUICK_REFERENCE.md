# RSSForge 维护系统 - 快速参考

## 🎯 核心使命

**保持 RSSForge feeds 健康、可访问、持续更新**

---

## 📊 当前状态

```
Health:    25% (12/48) ❌
Actions:   100% ✅
Monitor:   Active ✅
Auto-Fix:  Ready ✅
```

---

## 🔧 核心工具

### 1. 监控（每日 4 次）

```bash
python3 scripts/monitor_enhanced.py --pat $PAT
```

**检查**:
- ✅ Actions 状态
- ✅ Feed 健康度
- ✅ 链接可访问性
- ✅ 源站可用性

**输出**: `cron-logs/monitor_*.log`

---

### 2. 自动修复（每周日）

```bash
python3 scripts/auto_fix.py --pat $PAT
```

**修复**:
- feeds_meta.json URL 字段
- 缺失的 feed 文件
- 过期数据

**输出**: GitHub commit

---

### 3. 诊断（按需）

```bash
python3 scripts/diagnose_feeds.py --pat $PAT
```

**诊断**:
- 数据结构问题
- 配置缺失
- 爬取状态

**输出**: `/tmp/feed_diagnostic_results.json`

---

## ⏰ 定时任务

### Daily Quality Check

**时间**: 7:05, 12:05, 18:05, 23:05
**任务**: 监控脚本
**对齐**: GitHub Actions + 5 分钟

### Weekly Deep Maintenance

**时间**: 每周日 23:00
**任务**: 自动修复 + 深度检查
**输出**: weekly-report

---

## 🚨 报警条件

| 条件 | 严重度 | 动作 |
|------|--------|------|
| Actions 失败 > 1 | 🔴 高 | 立即调查 |
| Zero-count > 30 | 🔴 高 | 运行 auto-fix |
| Pages 下线 | 🔴 严重 | 立即修复 |
| 源站下线 > 3 | 🟡 中 | 标记死站点 |

---

## 🔗 关键链接

### RSS Feeds

**主页面**: `https://gitfox-enter.github.io/RSSForge/feeds/`

**示例**:
- 线报酷: `feeds/线报酷.xml`
- 汇发部: `feeds/汇发部.xml`

---

### 官方源站

1. **线报酷**: https://www.xianbao.co
2. **汇发部**: https://www.huifabu.com
3. **线报ICU**: https://www.xianbao.icu

---

## 🔄 恢复流程

### 平台失败

```bash
# 1. 克隆仓库
git clone https://github.com/gitfox-enter/RSSForge.git

# 2. 阅读指南
cat RECOVERY_GUIDE.md

# 3. 恢复监控
python3 scripts/monitor_enhanced.py --pat $PAT
```

---

### GitHub Pages 下线

1. 检查 Actions 部署状态
2. 验证 feeds/ 目录
3. 触发 Pages 重建
4. 验证可访问性

---

## ✅ 自动化权限

### 已授权

- ✅ 自动修复 feeds_meta.json
- ✅ 自动监控所有链接
- ✅ 自动清理死站点
- ✅ 自动添加新 RSS 源

### 需确认

- ⚠️ 大规模删除站点
- ⚠️ 修改 Parser 逻辑
- ⚠️ 性能优化变更

---

**快速参考** | 最后更新: 2026-07-11
