# GitHub Actions 多站点更新监控系统

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions%20Ready-brightgreen.svg)](https://github.com/features/actions)

> 🤖 **零运维 · 稳定可靠 · 自动备份 · 即时通知**
> 
> 基于 GitHub Actions + 网易Claw邮箱的46站全自动更新监控系统，每4小时自动巡检，检测到更新立即邮件推送。

---

## ✨ 核心特性

- ✅ **全自动化**：每4小时自动执行（00:00, 04:00, 08:00, 12:00, 16:00, 20:00）
- ✅ **精准检测**：MD5哈希比对，不漏报不误报
- ✅ **即时通知**：网易Claw邮箱推送，HTML邮件支持链接跳转
- ✅ **完整备份**：每次邮件本地存档，GitHub自动提交
- ✅ **零打扰**：无更新零输出、零提交、零邮件
- ✅ **高容错**：单站失败不影响整体，完整日志记录
- ✅ **易维护**：代码注释齐全，增删站点只需编辑列表

---

## 📦 项目结构

```
.
├── crawl.py                    # 主程序（爬虫+比对+邮件+备份）
├── requirements.txt            # Python依赖
├── hash_record.txt            # 哈希记录文件（自动生成）
├── email_backup/              # 邮件备份目录（自动生成）
│   └── 20260603_第1轮_站点更新邮件备份.html
├── .github/
│   └── workflows/
│       └── crawl.yml          # GitHub Actions工作流
└── README.md                  # 本文档
```

---

## 🚀 快速部署

### 第一步：Fork本仓库

点击右上角 **Fork** 按钮，将仓库复制到您的账号下。

### 第二步：获取网易Claw邮箱密钥

#### 方法一：命令行获取（推荐）

```bash
# 使用您的auth-url替换下面的值
npx "@clawemail/claw-setup@latest" --auth-url "t1/cDGJE7RNbeRsaZSWPDNfuU5FDNX"
```

执行后会返回：
```json
{
  "apiKey": "sk-xxxxxxxxxxxxxxxx",
  "user": "your@email.com"
}
```

#### 方法二：网页获取

1. 访问：https://claw.163.com/skills-hub/skills/claw-email-setup
2. 登录网易邮箱账号
3. 完成授权后获取 `API Key` 和 `User Email`

### 第三步：配置GitHub Secrets

进入您Fork的仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下3个密钥：

| Secret名称 | 值 | 说明 |
|-----------|-----|------|
| `CLAW_AUTH_URL` | `t1/cDGJE7RNbeRsaZSWPDNfuU5FDNX` | Claw授权URL（固定值） |
| `CLAWEMAIL_API_KEY` | `sk-xxxxxxxx` | 从第二步获取的API Key |
| `CLAWEMAIL_USER` | `your@email.com` | 接收通知的邮箱地址 |

### 第四步：启用GitHub Actions

1. 进入仓库的 **Actions** 标签页
2. 如果提示需要启用，点击 **I understand my workflows, go ahead and enable them**
3. 选择 **站点更新监控** 工作流
4. 点击 **Enable workflow**

### 第五步：测试运行

点击 **Run workflow** → **Run workflow** 手动触发一次测试。

查看运行日志，确认：
- ✅ 爬虫正常执行
- ✅ 首次运行记录所有站点哈希
- ✅ 邮件发送成功（如已配置）

---

## ⚙️ 自定义配置

### 增删监控站点

编辑 `crawl.py` 文件中的 `MONITOR_SITES` 列表：

```python
MONITOR_SITES = [
    "https://example1.com/",
    "https://example2.com/",
    # 添加新站点...
    # 删除不需要的站点...
]
```

提交后，下次运行自动生效。

### 修改执行频率

编辑 `.github/workflows/crawl.yml` 中的 `schedule` 配置：

```yaml
on:
  schedule:
    - cron: '0 */4 * * *'  # 每4小时执行一次
```

常用Cron表达式：

| 表达式 | 含义 |
|--------|------|
| `0 */4 * * *` | 每4小时（00:00, 04:00, 08:00...） |
| `0 */2 * * *` | 每2小时 |
| `0 8,12,18 * * *` | 每天8点、12点、18点 |
| `0 9 * * *` | 每天早上9点 |

### 修改请求超时时间

编辑 `crawl.py` 中的配置：

```python
REQUEST_TIMEOUT = 15  # 单个站点超时时间（秒）
REQUEST_DELAY_MIN = 0.5  # 请求间隔最小值（秒）
REQUEST_DELAY_MAX = 1.5  # 请求间隔最大值（秒）
```

---

## 📊 运行日志示例

```
============================================================
GitHub Actions 多站点更新监控系统
============================================================
[启动] 北京时间: 2026-06-03 12:00:15
[启动] 当日第 4 轮巡检
[启动] 监控站点数: 46
------------------------------------------------------------
[信息] 已加载哈希记录: 46 条

[1/46] 检查: https://xianbaomi.com/
[正常] 无更新

[2/46] 检查: http://www.0818tuan.com/
[更新] ✅ 内容已更新

...

============================================================
[统计] 成功: 44 | 失败: 2
[统计] 更新站点: 3 个

------------------------------------------------------------
[处理] 检测到更新，开始处理...
[信息] 哈希文件已更新: hash_record.txt
[备份] 邮件已保存: email_backup/20260603_第4轮_站点更新邮件备份.html
[邮件] 发送成功: 【站点更新提醒】当日第4轮巡检 | 共3个网站更新
[Git] 提交成功: 站点更新检测 - 2026-06-03 12:05:32
============================================================
```

---

## 🔧 故障排查

### 问题1：邮件发送失败

**原因**：
- Secrets未配置或配置错误
- Claw邮箱配额用尽
- 网络连接问题

**解决**：
1. 检查GitHub Secrets是否正确
2. 访问Claw控制台查看配额：https://claw.163.com
3. 查看邮件备份：`email_backup/` 目录

### 问题2：所有站点都显示"首次监控"

**原因**：首次运行正常现象

**解决**：第二次运行时会正常比对更新

### 问题3：部分站点爬取失败

**原因**：
- 目标站点无法访问
- 被反爬机制拦截
- 超时

**解决**：
- 检查目标站点是否可正常访问
- 适当增加 `REQUEST_TIMEOUT` 值
- 检查日志中的具体错误信息

### 问题4：GitHub Actions未自动执行

**原因**：
- 工作流未启用
- 仓库超过60天未活动（GitHub会禁用定时任务）

**解决**：
1. 检查Actions标签页是否启用工作流
2. 定期提交代码保持仓库活跃

---

## 📋 邮件模板预览

```
主题：【站点更新提醒】当日第4轮巡检 | 共3个网站更新

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 站点更新监控提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 当日第 4 次全自动巡检
⏰ 巡检时间：2026-06-03 12:00:15
📊 检测到 3 个网站内容更新

更新站点列表：
1. http://www.0818tuan.com/
2. https://www.yxssp.com/
3. https://www.ithome.com/zt/xijiayi

━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 自动化监控来源：GitHub Actions 站点巡检机器人
⏱ 每4小时自动巡检 | 零运维 | 稳定可靠
```

---

## 🛡️ 安全说明

- 所有敏感信息（API Key、邮箱）存储在GitHub Secrets中，不会暴露在代码中
- 哈希记录文件仅包含URL和MD5值，不包含页面内容
- 邮件备份仅保存在您的仓库中，不会泄露给第三方

---

## 📝 常见问题

**Q: 可以监控需要登录的网站吗？**
A: 暂不支持，仅适用于公开访问的网站

**Q: 哈希比对是否会误判？**
A: MD5比对正文内容，广告、时间戳等动态内容可能触发更新。如频繁误报，可考虑过滤特定内容

**Q: 邮件会发送到Gmail/QQ邮箱吗？**
A: 不会。Claw邮箱只能发送到配置的网易邮箱（@163.com/@126.com等）

**Q: 如何查看历史更新？**
A: 查看 `email_backup/` 目录下的HTML文件，或查看Git提交记录

---

## 📜 更新日志

### v1.0.0 (2026-06-03)
- ✅ 初始版本发布
- ✅ 支持46个站点监控
- ✅ MD5哈希比对检测
- ✅ 网易Claw邮件推送
- ✅ 本地备份归档
- ✅ GitHub Actions自动化

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

[MIT License](LICENSE)

---

## 📞 支持

如有问题，请提交 [Issue](../../issues)
