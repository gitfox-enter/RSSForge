# ClearReader — 极简 RSS 阅读器

## 核心理念

**"少即是多"** —— 不追求功能堆砌，追求阅读体验的极致干净。

现有 RSS 阅读器的通病：界面臃肿、颜色混乱、信息密度过高、主题切换只是简单反色。

ClearReader 要做到：
- 界面干净到"感觉不到界面存在"
- 主题不只是反色，是真正的设计语言
- 集众家之长：Feedly 的信息架构 + Reeder 的阅读体验 + Instapaper 的专注感

---

## 设计语言

### 主题系统（三套完整主题）

**Light（默认）**
- 背景：#FAFAFA
- 卡片：#FFFFFF
- 主色调：#0A84FF（苹果蓝，舒适护眼）
- 文字主色：#1D1D1F
- 文字次色：#6E6E73
- 分割线：#E5E5EA
- 悬停/选中：#F2F2F7

**Dark（深夜专注）**
- 背景：#000000（纯黑，省电 OLED）
- 卡片：#1C1C1E
- 主色调：#0A84FF
- 文字主色：#F5F5F7
- 文字次色：#8E8E93
- 分割线：#38383A
- 悬停/选中：#2C2C2E

**Sepia（阅读友好）**
- 背景：#F4ECD8（羊皮纸质感）
- 卡片：#FBF7EE
- 主色调：#C17A3A（暖琥珀色）
- 文字主色：#3D2B1F
- 文字次色：#7A6555
- 分割线：#D9CCB0
- 悬停/选中：#EDE5D0

### 字体
- 界面字体：system-ui, -apple-system, sans-serif
- 阅读字体（可切换）：Georgia / system-ui / 苹方-简 / Noto Serif SC
- 英文默认：Georgia（经典阅读感）
- 中文默认：system-ui（系统默认，干净）

### 布局

**桌面（>768px）**：三栏
```
[侧边栏 200px] | [文章列表 320px] | [阅读区 flex-1, max-width: 720px 居中]
```

**平板（768px）**：两栏
```
[侧边栏图标模式 56px] | [文章列表 + 阅读 区]
```

**手机（<768px）**：单栏 + 底部 Tab 切换
```
[列表视图] ←→ [阅读视图]（滑动切换）
```

---

## 功能模块

### 1. 订阅源管理
- 添加 RSS/Atom URL，自动检测并解析
- 按「全部 / 分类 / 收藏 / 已读」分组
- 分类管理（增删改）
- OPML 导入/导出
- 内置推荐源（BBC News, TechCrunch, 少数派等）

### 2. 文章列表
- 按时间倒序，每源显示最新 N 条
- 每条显示：标题 + 来源 + 时间 + 摘要（截断 100 字）
- 未读标记（左侧蓝点）
- 已读自动变灰（可配置）
- 搜索过滤（标题/内容）
- 滑动标记已读/未读

### 3. 阅读视图
- 文章标题、来源、时间、作者
- 正文内容（支持 HTML 渲染）
- 字体大小调节（小/中/大）
- 阅读宽度调节（窄/中/宽）
- 一键收藏/书签
- 原文链接（外部打开）
- 分享（复制链接）
- 标记已读/未读

### 4. 主题切换
- 顶部工具栏一键切换：Light 🌙 / Dark 🌑 / Sepia 📜
- 自动跟随系统（可选）
- 记忆偏好（localStorage）

### 5. 工具面板
- 订阅源列表管理
- 分类编辑
- 存储使用量显示
- OPML 导入/导出
- 代理服务器配置

---

## 技术方案

### 架构
- 单 HTML 文件（便于部署到 GitHub Pages）
- 纯原生 JavaScript（无框架依赖）
- CSS 自定义属性（CSS Variables）实现主题切换
- localStorage 存储订阅数据
- CORS 代理（同 feedforge，api.allorigins.win）

### 数据模型
```javascript
// 订阅源
feeds = {
  'https://example.com/rss': {
    url: 'https://example.com/rss',
    title: 'Example',
    site: 'https://example.com',
    category: 'Tech',
    items: [...],
    lastFetch: 1234567890
  }
}

// 书签
bookmarks = [{ title, link, date, feedTitle, feedUrl }]

// 收藏的源
favorites = ['url1', 'url2']

// 设置
settings = {
  theme: 'light' | 'dark' | 'sepia' | 'system',
  fontSize: 'small' | 'medium' | 'large',
  readingWidth: 'narrow' | 'medium' | 'wide',
  autoRead: true  // 阅读后自动标记已读
}
```

### 代理配置
沿用 feedforge 的 CORS_PROXIES 方案，支持用户自定义代理。

---

## UI 组件清单

### Toolbar（顶部）
- 左：菜单图标（侧边栏开关）
- 中：当前视图标题
- 右：主题切换 | 设置图标

### Sidebar（侧边栏）
- 搜索框（全局搜索）
- 导航项：全部 / 未读 / 收藏 / 书签
- 分类列表（可折叠）
- 订阅源列表（带未读数）
- 底部：添加源 / 设置

### Article List（文章列表）
- 每条 ArticleCard：
  - 左侧：未读蓝点
  - 标题（最多2行）
  - 摘要（最多3行）
  - 底部：来源名 + 时间
- 底部：加载更多 / 下拉刷新

### Reader（阅读区）
- 文章头部（标题、来源、时间、作者）
- 操作栏（收藏、分享、原文、已读状态）
- 正文（居中显示，可选宽度）
- 底部：相关推荐

### Theme Switcher
- 三个按钮，图标 + 文字
- 当前激活态高亮

---

## PWA 支持

- manifest.json（name: ClearReader, theme_color: 跟随主题）
- 可添加到主屏幕
- 离线缓存核心文件

---

## 待完成

- [ ] 界面重构（当前 feedforge 基础上改）
- [ ] 三主题完整实现
- [ ] 响应式布局
- [ ] 阅读区优化
- [ ] PWA 配置
- [ ] 测试部署
