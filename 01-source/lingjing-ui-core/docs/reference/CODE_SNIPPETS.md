# 📝 LingJing Core - 代码片段库

> **面向**: AI开发工具、前端开发者
> **用途**: 快速复制粘贴常用布局和组件代码
> **更新**: 2026-02-12

---

## 🧭 使用前说明

- 若当前任务是实际项目落地，应先读取 `scene_coverage_matrix.yml`，再按“**Level 1 模板轻调 → Level 2 组件编排 → Level 3 规范扩展**”选择实现路径。
- 本文档中的片段与完整页面更适合作为**结构参考**；交付到调用方项目时，仍应结合 `SKILL.md` 的场景判断、页面目标与目录约定完成适配。
- 若页面将落到独立项目中，更稳妥的做法是先把灵境样式资源放入调用方项目自己的样式目录，再回写 `<link>` / `import` 路径，并从生成文件的实际位置检查样式是否可达。

## 📋 目录


- [B端系统布局](#-b端系统布局)
  - [侧边栏布局（标准）](#1-侧边栏布局标准)
  - [顶部导航布局](#2-顶部导航布局)
- [表单和筛选](#-表单和筛选)
  - [搜索筛选栏](#1-搜索筛选栏)
  - [表单输入组](#2-表单输入组)
- [表格组件](#-表格组件)
  - [基础数据表格](#1-基础数据表格)
  - [带分页表格](#2-带分页表格)
- [卡片布局](#-卡片布局)
  - [统计卡片网格](#1-统计卡片网格)
  - [内容卡片](#2-内容卡片)
- [按钮组合](#-按钮组合)
  - [操作按钮组](#1-操作按钮组)
  - [表单操作区](#2-表单操作区)
- [完整页面模板](#-完整页面模板)
  - [用户管理页面](#1-用户管理页面)
  - [数据看板页面](#2-数据看板页面)

---

## 🏗️ B端系统布局

### 1. 侧边栏布局（标准）

**适用场景**: 管理后台、B端系统主布局

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B端系统</title>
    <!-- 此示例使用 dist 单文件 CSS 作为演示入口 -->
    <link rel="stylesheet" href="../components/dist/lingjing-core-b-system.css">

    <script src="https://unpkg.com/lucide@latest"></script>

</head>
<body>
    <div class="b-layout-sidebar">
        <!-- 侧边栏 -->
        <aside class="b-sidebar">
            <!-- 品牌区 -->
            <div class="b-sidebar-header">
                <span class="b-sidebar-logo">灵境Core</span>
                <span class="b-sidebar-version">v1.7.0</span>
            </div>

            <!-- 导航菜单 -->
            <nav class="b-sidebar-nav">
                <a href="#" class="b-sidebar-nav-link active">
                    <i data-lucide="home"></i>
                    <span class="b-sidebar-nav-text">首页</span>
                </a>
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="users"></i>
                    <span class="b-sidebar-nav-text">用户管理</span>
                </a>
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="settings"></i>
                    <span class="b-sidebar-nav-text">系统设置</span>
                </a>
            </nav>

            <!-- 底部折叠按钮 -->
            <div class="b-sidebar-footer">
                <button class="b-sidebar-toggle" onclick="toggleSidebarCollapse()">
                    <span class="b-sidebar-toggle-icon">
                        <i data-lucide="chevrons-left"></i>
                    </span>
                    <span class="b-sidebar-toggle-text">收起</span>
                </button>
            </div>
        </aside>

        <!-- 移动端遮罩层 -->
        <div class="b-sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

        <!-- 主内容区 -->
        <main class="b-main">
            <!-- 顶部标题栏 -->
            <header class="b-header">
                <div>
                    <h1 class="page-title">页面标题</h1>
                    <p class="page-subtitle">页面描述信息</p>
                </div>

                <!-- 顶部操作区 - Header中不包含收起侧边栏按钮，该功能已在侧边栏底部提供 -->
                <div style="display: flex; gap: var(--spacing-md); align-items: center;">
                    <button class="btn-icon" onclick="toggleTheme()">
                        <i data-lucide="moon" id="themeIcon"></i>
                    </button>
                    <div class="user-avatar">
                        <i data-lucide="user"></i>
                    </div>
                </div>
            </header>

            <!-- 内容区域 -->
            <div class="b-content">
                <!-- 页面内容 -->
            </div>
        </main>
    </div>

    <script>
        // 初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // 主题切换
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);

            const icon = document.getElementById('themeIcon');
            icon.setAttribute('data-lucide', newTheme === 'light' ? 'moon' : 'sun');
            lucide.createIcons();
        }

        // 侧边栏折叠（桌面端）
        function toggleSidebarCollapse() {
            const sidebar = document.querySelector('.b-sidebar');
            sidebar.classList.toggle('collapsed');
        }

        // 侧边栏切换（移动端）
        function toggleSidebar() {
            const sidebar = document.querySelector('.b-sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
    </script>
</body>
</html>
```

### 2. 顶部导航布局

**适用场景**: 简单后台、单页面应用

```html
<div class="b-layout-topbar">
    <nav class="b-topbar">
        <div class="b-topbar-brand">
            <span class="b-topbar-logo">Logo</span>
        </div>
        <div class="b-topbar-nav">
            <a href="#" class="b-topbar-nav-link active">首页</a>
            <a href="#" class="b-topbar-nav-link">用户</a>
            <a href="#" class="b-topbar-nav-link">设置</a>
        </div>
        <div class="b-topbar-actions">
            <button class="btn-icon" onclick="toggleTheme()">
                <i data-lucide="moon"></i>
            </button>
        </div>
    </nav>
    <main class="b-main">
        <!-- 内容 -->
    </main>
</div>
```

---

## 📝 表单和筛选

### 1. 搜索筛选栏

**适用场景**: 数据列表页、表格页

```html
<div class="search-bar">
    <input type="text" class="search-input" placeholder="搜索用户名称、邮箱...">
    <select class="filter-select">
        <option>全部状态</option>
        <option>已激活</option>
        <option>待审核</option>
        <option>已禁用</option>
    </select>
    <button class="btn-outline">
        <i data-lucide="filter"></i>
        <span>筛选</span>
    </button>
    <button class="btn-primary">
        <i data-lucide="plus"></i>
        <span>添加用户</span>
    </button>
</div>
```

### 2. 表单输入组

**适用场景**: 编辑表单、设置页面

```html
<div class="content-card">
    <h3>基本信息</h3>

    <div class="form-group">
        <label class="form-label">用户名</label>
        <input type="text" class="search-input" placeholder="请输入用户名">
    </div>

    <div class="form-group">
        <label class="form-label">邮箱</label>
        <input type="email" class="search-input" placeholder="请输入邮箱">
    </div>

    <div class="form-group">
        <label class="form-label">状态</label>
        <select class="filter-select">
            <option>已激活</option>
            <option>待审核</option>
            <option>已禁用</option>
        </select>
    </div>

    <div class="action-buttons">
        <button class="btn-primary">
            <i data-lucide="check"></i>
            <span>保存</span>
        </button>
        <button class="btn-text">
            <span>取消</span>
        </button>
    </div>
</div>
```

---

## 📊 表格组件

> 若当前页面来自 B 端列表页、审批待办页、工单看板页或主从详情页，优先使用 `.advanced-data-table`、`.table-toolbar`、`.filter-panel` 等复合组件；本节的 `.data-table` 更适合作为轻量内嵌表格。

### 1. 基础数据表格

**适用场景**: 用户列表、订单列表、任何数据展示


```html
<table class="data-table">
    <thead>
        <tr>
            <th>用户名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>张三</td>
            <td>zhangsan@example.com</td>
            <td><span class="badge success">已激活</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" title="编辑">
                        <i data-lucide="edit"></i>
                    </button>
                    <button class="btn-icon" title="删除">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>
        <tr>
            <td>李四</td>
            <td>lisi@example.com</td>
            <td><span class="badge pending">待审核</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" title="编辑">
                        <i data-lucide="edit"></i>
                    </button>
                    <button class="btn-icon" title="删除">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>
        <tr>
            <td>王五</td>
            <td>wangwu@example.com</td>
            <td><span class="badge danger">已禁用</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" title="编辑">
                        <i data-lucide="edit"></i>
                    </button>
                    <button class="btn-icon" title="删除">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>
    </tbody>
</table>
```

### 2. 带分页表格

**适用场景**: 大量数据分页展示

```html
<div class="content-card">
    <table class="data-table">
        <!-- 表格内容同上 -->
    </table>

    <!-- 分页 -->
    <div class="pagination">
        <button class="pagination-btn" disabled>
            <i data-lucide="chevron-left"></i>
        </button>
        <button class="pagination-btn active">1</button>
        <button class="pagination-btn">2</button>
        <button class="pagination-btn">3</button>
        <span class="pagination-ellipsis">...</span>
        <button class="pagination-btn">10</button>
        <button class="pagination-btn">
            <i data-lucide="chevron-right"></i>
        </button>
    </div>
</div>
```

---

## 🎴 卡片布局

### 1. 统计卡片网格

**适用场景**: 数据看板、首页概览

```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: var(--spacing-lg);">
    <div class="b-stat-card">
        <div class="b-stat-label">总用户数</div>
        <div class="b-stat-value">1,234</div>
        <div class="b-stat-trend positive">
            <i data-lucide="trending-up"></i>
            <span>+12.5%</span>
        </div>
    </div>

    <div class="b-stat-card">
        <div class="b-stat-label">活跃用户</div>
        <div class="b-stat-value">856</div>
        <div class="b-stat-trend positive">
            <i data-lucide="trending-up"></i>
            <span>+8.2%</span>
        </div>
    </div>

    <div class="b-stat-card">
        <div class="b-stat-label">待审核</div>
        <div class="b-stat-value">23</div>
        <div class="b-stat-trend negative">
            <i data-lucide="trending-down"></i>
            <span>-3.1%</span>
        </div>
    </div>

    <div class="b-stat-card">
        <div class="b-stat-label">已禁用</div>
        <div class="b-stat-value">12</div>
        <div class="b-stat-trend neutral">
            <i data-lucide="minus"></i>
            <span>0.0%</span>
        </div>
    </div>
</div>
```

### 2. 内容卡片

**适用场景**: 包裹内容、表单、图表

```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-lg);">
    <div class="content-card">
        <h3>最近活动</h3>
        <ul style="list-style: none; padding: 0;">
            <li style="padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--theme-border-light);">
                用户张三登录了系统
            </li>
            <li style="padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--theme-border-light);">
                用户李四更新了资料
            </li>
            <li style="padding: var(--spacing-sm) 0;">
                管理员添加了新用户
            </li>
        </ul>
    </div>

    <div class="content-card">
        <h3>系统状态</h3>
        <div style="display: flex; flex-direction: column; gap: var(--spacing-md);">
            <div style="display: flex; justify-content: space-between;">
                <span>CPU使用率</span>
                <span class="badge success">正常</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>内存使用率</span>
                <span class="badge warning">警告</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>磁盘空间</span>
                <span class="badge success">正常</span>
            </div>
        </div>
    </div>
</div>
```

---

## 🔘 按钮组合

### 1. 操作按钮组

**适用场景**: 表格操作列、卡片操作区

```html
<div class="action-buttons">
    <button class="btn-icon" title="编辑">
        <i data-lucide="edit"></i>
    </button>
    <button class="btn-icon" title="删除">
        <i data-lucide="trash-2"></i>
    </button>
    <button class="btn-icon" title="更多">
        <i data-lucide="more-horizontal"></i>
    </button>
</div>
```

### 2. 表单操作区

**适用场景**: 表单底部、对话框底部

```html
<div class="action-buttons">
    <button class="btn-primary">
        <i data-lucide="check"></i>
        <span>确认</span>
    </button>
    <button class="btn-outline">
        <i data-lucide="save"></i>
        <span>保存草稿</span>
    </button>
    <button class="btn-text">
        <span>取消</span>
    </button>
</div>
```

---

## 📄 完整页面模板

### 1. 用户管理页面

**完整的用户管理页面，包含搜索、筛选、表格、分页**

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户管理 - LingJing Core</title>
    <!-- 此示例使用 dist 单文件 CSS 作为演示入口 -->
    <link rel="stylesheet" href="../components/dist/lingjing-core-b-system.css">
    <script src="https://unpkg.com/lucide@latest"></script>

</head>
<body>
    <div class="b-layout-sidebar">
        <aside class="b-sidebar">
            <div class="b-sidebar-header">
                <span class="b-sidebar-logo">灵境Core</span>
                <span class="b-sidebar-version">v1.7.0</span>
            </div>
            <nav class="b-sidebar-nav">
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="home"></i>
                    <span class="b-sidebar-nav-text">首页</span>
                </a>
                <a href="#" class="b-sidebar-nav-link active">
                    <i data-lucide="users"></i>
                    <span class="b-sidebar-nav-text">用户管理</span>
                </a>
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="settings"></i>
                    <span class="b-sidebar-nav-text">系统设置</span>
                </a>
            </nav>
            <div class="b-sidebar-footer">
                <button class="b-sidebar-toggle" onclick="toggleSidebarCollapse()">
                    <span class="b-sidebar-toggle-icon">
                        <i data-lucide="chevrons-left"></i>
                    </span>
                    <span class="b-sidebar-toggle-text">收起</span>
                </button>
            </div>
        </aside>

        <div class="b-sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

        <main class="b-main">
            <header class="b-header">
                <div>
                    <h1 class="page-title">用户管理</h1>
                    <p class="page-subtitle">管理系统用户和权限</p>
                </div>
                <div style="display: flex; gap: var(--spacing-md); align-items: center;">
                    <!-- Header中不包含收起侧边栏按钮，该功能已在侧边栏底部提供 -->
                    <button class="btn-icon" onclick="toggleTheme()">
                        <i data-lucide="moon" id="themeIcon"></i>
                    </button>
                    <div class="user-avatar">
                        <i data-lucide="user"></i>
                    </div>
                </div>
            </header>

            <div class="b-content">
                <!-- 搜索筛选栏 -->
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="搜索用户名称、邮箱...">
                    <select class="filter-select">
                        <option>全部状态</option>
                        <option>已激活</option>
                        <option>待审核</option>
                        <option>已禁用</option>
                    </select>
                    <button class="btn-outline">
                        <i data-lucide="filter"></i>
                        <span>筛选</span>
                    </button>
                    <button class="btn-primary">
                        <i data-lucide="plus"></i>
                        <span>添加用户</span>
                    </button>
                </div>

                <!-- 数据表格 -->
                <div class="content-card">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>用户名</th>
                                <th>邮箱</th>
                                <th>状态</th>
                                <th>注册时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>张三</td>
                                <td>zhangsan@example.com</td>
                                <td><span class="badge success">已激活</span></td>
                                <td>2026-01-15</td>
                                <td>
                                    <div class="action-buttons">
                                        <button class="btn-icon" title="编辑">
                                            <i data-lucide="edit"></i>
                                        </button>
                                        <button class="btn-icon" title="删除">
                                            <i data-lucide="trash-2"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td>李四</td>
                                <td>lisi@example.com</td>
                                <td><span class="badge pending">待审核</span></td>
                                <td>2026-02-01</td>
                                <td>
                                    <div class="action-buttons">
                                        <button class="btn-icon" title="编辑">
                                            <i data-lucide="edit"></i>
                                        </button>
                                        <button class="btn-icon" title="删除">
                                            <i data-lucide="trash-2"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td>王五</td>
                                <td>wangwu@example.com</td>
                                <td><span class="badge danger">已禁用</span></td>
                                <td>2025-12-20</td>
                                <td>
                                    <div class="action-buttons">
                                        <button class="btn-icon" title="编辑">
                                            <i data-lucide="edit"></i>
                                        </button>
                                        <button class="btn-icon" title="删除">
                                            <i data-lucide="trash-2"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 分页 -->
                    <div class="pagination">
                        <button class="pagination-btn" disabled>
                            <i data-lucide="chevron-left"></i>
                        </button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">3</button>
                        <button class="pagination-btn">
                            <i data-lucide="chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);

            const icon = document.getElementById('themeIcon');
            icon.setAttribute('data-lucide', newTheme === 'light' ? 'moon' : 'sun');
            lucide.createIcons();
        }

        function toggleSidebarCollapse() {
            const sidebar = document.querySelector('.b-sidebar');
            sidebar.classList.toggle('collapsed');
        }

        function toggleSidebar() {
            const sidebar = document.querySelector('.b-sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
    </script>
</body>
</html>
```

### 2. 数据看板页面

**数据看板，包含统计卡片、图表、活动列表**

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据看板 - LingJing Core</title>
    <!-- 此示例使用调用方项目内的单文件 CSS 路径作为示意 -->
    <link rel="stylesheet" href="./styles/lingjing/lingjing-core-b-system.css">
    <script src="https://unpkg.com/lucide@latest"></script>

</head>
<body>
    <div class="b-layout-sidebar">
        <aside class="b-sidebar">
            <div class="b-sidebar-header">
                <span class="b-sidebar-logo">灵境Core</span>
                <span class="b-sidebar-version">v1.7.0</span>
            </div>
            <nav class="b-sidebar-nav">
                <a href="#" class="b-sidebar-nav-link active">
                    <i data-lucide="home"></i>
                    <span class="b-sidebar-nav-text">数据看板</span>
                </a>
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="users"></i>
                    <span class="b-sidebar-nav-text">用户管理</span>
                </a>
                <a href="#" class="b-sidebar-nav-link">
                    <i data-lucide="settings"></i>
                    <span class="b-sidebar-nav-text">系统设置</span>
                </a>
            </nav>
        </aside>

        <main class="b-main">
            <header class="b-header">
                <div>
                    <h1 class="page-title">数据看板</h1>
                    <p class="page-subtitle">实时数据概览</p>
                </div>
                <button class="btn-icon" onclick="toggleTheme()">
                    <i data-lucide="moon" id="themeIcon"></i>
                </button>
            </header>

            <div class="b-content">
                <!-- 统计卡片 -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: var(--spacing-lg); margin-bottom: var(--spacing-xl);">
                    <div class="b-stat-card">
                        <div class="b-stat-label">总用户数</div>
                        <div class="b-stat-value">1,234</div>
                        <div class="b-stat-trend positive">
                            <i data-lucide="trending-up"></i>
                            <span>+12.5%</span>
                        </div>
                    </div>
                    <div class="b-stat-card">
                        <div class="b-stat-label">活跃用户</div>
                        <div class="b-stat-value">856</div>
                        <div class="b-stat-trend positive">
                            <i data-lucide="trending-up"></i>
                            <span>+8.2%</span>
                        </div>
                    </div>
                    <div class="b-stat-card">
                        <div class="b-stat-label">待审核</div>
                        <div class="b-stat-value">23</div>
                        <div class="b-stat-trend negative">
                            <i data-lucide="trending-down"></i>
                            <span>-3.1%</span>
                        </div>
                    </div>
                    <div class="b-stat-card">
                        <div class="b-stat-label">已禁用</div>
                        <div class="b-stat-value">12</div>
                        <div class="b-stat-trend neutral">
                            <i data-lucide="minus"></i>
                            <span>0.0%</span>
                        </div>
                    </div>
                </div>

                <!-- 内容卡片 -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-lg);">
                    <div class="content-card">
                        <h3>最近活动</h3>
                        <ul style="list-style: none; padding: 0; margin: 0;">
                            <li style="padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--theme-border-light);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span>用户张三登录了系统</span>
                                    <span style="font-size: var(--font-size-xs); color: var(--text-secondary);">刚刚</span>
                                </div>
                            </li>
                            <li style="padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--theme-border-light);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span>用户李四更新了资料</span>
                                    <span style="font-size: var(--font-size-xs); color: var(--text-secondary);">5分钟前</span>
                                </div>
                            </li>
                            <li style="padding: var(--spacing-sm) 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span>管理员添加了新用户</span>
                                    <span style="font-size: var(--font-size-xs); color: var(--text-secondary);">10分钟前</span>
                                </div>
                            </li>
                        </ul>
                    </div>

                    <div class="content-card">
                        <h3>系统状态</h3>
                        <div style="display: flex; flex-direction: column; gap: var(--spacing-md);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>CPU使用率</span>
                                <span class="badge success">45%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>内存使用率</span>
                                <span class="badge warning">78%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>磁盘空间</span>
                                <span class="badge success">32%</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>网络流量</span>
                                <span class="badge success">正常</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);

            const icon = document.getElementById('themeIcon');
            icon.setAttribute('data-lucide', newTheme === 'light' ? 'moon' : 'sun');
            lucide.createIcons();
        }
    </script>
</body>
</html>
```

---

## 🎯 使用建议

### 1. 快速开始

1. 先判断当前更适合复用完整模板、组合片段，还是依据规范补生成缺失结构
2. 选择与目标页面最接近的代码片段或完整页面骨架
3. 若用于独立项目，先把样式资源放入项目内，再回写引用路径
4. 根据需求调整内容，尽量保持核心 HTML 结构与 class 名称稳定
5. 在生成文件的实际位置检查样式与图标入口是否可访问


### 2. 组合使用

可以组合多个片段创建完整页面：

```html
<!-- 布局容器 -->
<div class="b-layout-sidebar">
    <!-- 侧边栏片段 -->
    <aside class="b-sidebar">...</aside>

    <!-- 主内容 -->
    <main class="b-main">
        <div class="b-content">
            <!-- 搜索筛选片段 -->
            <div class="search-bar">...</div>

            <!-- 表格片段 -->
            <div class="content-card">
                <table class="data-table">...</table>
            </div>
        </div>
    </main>
</div>
```

### 3. 响应式检查

所有片段都已适配响应式，无需额外处理：
- 桌面端(>768px): 正常布局
- 平板端(≤768px): 自适应调整
- 移动端(≤480px): 垂直堆叠

---

## 📌 相关文档

- [COMPONENT_CATALOG.md](COMPONENT_CATALOG.md) - 组件目录

---

**更新日志**:
- 2026-02-12: 初始版本，包含常用布局和完整页面模板
