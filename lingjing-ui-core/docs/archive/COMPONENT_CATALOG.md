# 📦 LingJing Core - 组件目录

> **面向**: AI开发工具、前端开发者
> **用途**: 快速查找和使用现成组件
> **版本**: v2.7.1
> **更新**: 2026-02-23
> **文档状态**: 历史文档（待迁移至 v3.0 口径）

---

## 🧭 使用组件前的建议

- 在实际项目中，应先读取 `scene_coverage_matrix.yml`，再按“**Level 1 模板轻调 → Level 2 组件编排 → Level 3 规范扩展**”决定页面实现方式；组件目录更适合作为二级拼装和局部补充参考。
- 若页面已经有高匹配模板，优先沿用模板骨架和布局节奏，再从本文查找缺失组件；若没有直达模板，再按场景规则组织布局并调用标准组件。
- 若页面将落到独立项目中，更稳妥的做法是先把样式与脚本资源放入调用方项目，再回写 `<link>` / `<script>` / `import` 路径，并从生成文件的实际位置检查资源是否可达。

## 📋 组件分类索引


- [交互效果](#-交互效果) - 涟漪、悬停描边 **[NEW]**
- [按钮组件](#-按钮组件) - 5种按钮类型
- [表单组件](#-表单组件) - 输入框、选择器、搜索栏
- [表格组件](#-表格组件) - 数据表格、斑马纹样式
- [布局组件](#-布局组件) - B端系统布局、导航栏
- [卡片组件](#-卡片组件) - 内容卡片、统计卡片
- [导航组件](#-导航组件) - 面包屑、分页
- [状态组件](#-状态组件) - 徽章、标签
- [反馈组件](#-反馈组件) - 空状态提示

---

## 🎭 交互效果

> **完整文档**: [INTERACTIONS.md](./INTERACTIONS.md)

### 1. 卡片涟漪效果

**用途**: 鼠标进入卡片时的蓝色波纹扩散动画

**使用**:
```html
<!-- 以下路径示意调用方项目内的脚本落点 -->
<script src="./scripts/lingjing/interactions.js"></script>

<!-- 使用标准卡片类即可 -->
<div class="card-glass">
    <h3>卡片标题</h3>

    <p>鼠标进入会显示涟漪效果</p>
</div>
```

**特点**:
- 🎯 从鼠标位置开始扩散
- ⏱️ 持续 0.6 秒
- 🎨 自动适配深浅色主题
- ⚡ 需引入 `interactions.js`

**支持的卡片类**:
- `.card-glass` ✅
- `.glass-card` ✅
- `.glass-flowing` ✅
- `.glass-frosted` ✅
- `.glass-colored` ✅

---

### 2. 卡片悬停描边

**用途**: 鼠标悬停时自动显示蓝色描边高亮

**使用**:
```html
<!-- 无需 JS，使用标准卡片类即可 -->
<div class="card-glass">
    <h3>鼠标悬停试试</h3>
    <p>会自动显示蓝色描边</p>
</div>
```

**特点**:
- 🔵 蓝色描边高亮 (`--glass-border-hover`)
- ⬆️ 向上浮起 `translateY(-4px)`
- ✨ 增强阴影 + 蓝色光晕
- ✅ 无需 JS，自动生效

**视觉效果**:
- 浅色模式：蓝色描边 `rgba(0, 102, 204, 0.3)`
- 深色模式：亮蓝描边 `rgba(0, 132, 255, 0.4)`

---

### 3. 按钮光泽效果

**用途**: 按钮悬停时从左到右的光泽扫过动画

**使用**:
```html
<button class="btn-primary">
    <i data-lucide="check"></i>
    <span>确认</span>
</button>
```

**特点**:
- ✨ 光泽从左扫到右
- 🎨 半透明白色光泽
- ✅ 无需 JS，自动生效

---

### 快速开始

**完整集成**:
```html
<!DOCTYPE html>
<html>
<head>
  <!-- 以下路径示意调用方项目内的资源落点 -->
  <link rel="stylesheet" href="./styles/lingjing/lingjing-core-b-system.css">
</head>
<body>

  <!-- 你的卡片 -->
  <div class="card-glass">
    <h3>标题</h3>
    <p>内容</p>
  </div>

  <!-- 引入交互脚本（涟漪效果） -->
  <script src="./scripts/lingjing/interactions.js"></script>
</body>
</html>
```


**详细文档**: 查看 [INTERACTIONS.md](./INTERACTIONS.md) 了解完整用法和自定义选项。

---

## 🔘 按钮组件

### 1. 主按钮 (.btn-primary)

**用途**: 主要操作（提交、确认、保存）

**代码**:
```html
<button class="btn-primary">
    <i data-lucide="check"></i>
    <span>确认</span>
</button>
```

**特点**:
- 蓝色实心背景
- 白色文字
- 悬停时变为青色
- 图标自动16x16px

---

### 2. 轮廓按钮 (.btn-outline)

**用途**: 次要操作（筛选、取消、编辑）

**代码**:
```html
<button class="btn-outline">
    <i data-lucide="filter"></i>
    <span>筛选</span>
</button>
```

**特点**:
- 透明背景 + 蓝色边框
- 蓝色文字
- 悬停时填充蓝色背景

---

### 3. 幽灵按钮 (.btn-ghost)

**用途**: 最轻量操作（工具栏按钮）

**代码**:
```html
<button class="btn-ghost">
    <i data-lucide="x"></i>
    <span>清空</span>
</button>
```

**特点**:
- 完全透明
- 蓝色文字
- 悬停时浅蓝色背景

---

### 4. 文本按钮 (.btn-text)

**用途**: 超轻量操作（链接式按钮）

**代码**:
```html
<button class="btn-text">
    <span>查看详情</span>
</button>
```

**特点**:
- 无边框无背景
- 只有文字
- 悬停时浅蓝色背景

---

### 5. 图标按钮 (.btn-icon)

**用途**: 只有图标的小按钮（编辑、删除、更多）

**代码**:
```html
<button class="btn-icon">
    <i data-lucide="edit"></i>
</button>
```

**特点**:
- 32x32px 正方形
- 有边框
- 图标16x16px
- 悬停时边框变蓝

---

### 按钮组合使用

```html
<!-- 操作按钮组 -->
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

---

## 📝 表单组件

### 1. 搜索输入框 (.search-input)

**用途**: 搜索数据、筛选内容

**代码**:
```html
<input type="text" class="search-input" placeholder="搜索用户名称、邮箱...">
```

**特点**:
- 玻璃拟态效果
- Focus时蓝色边框 + 阴影环
- Hover时半透明蓝色边框
- 自动响应式宽度

---

### 2. 筛选下拉框 (.filter-select)

**用途**: 筛选数据、选择状态

**代码**:
```html
<select class="filter-select">
    <option>全部状态</option>
    <option>已激活</option>
    <option>待审核</option>
    <option>已禁用</option>
</select>
```

**特点**:
- 与搜索框样式统一
- 自定义下拉箭头
- 自动宽度适应内容

---

### 3. 搜索栏容器 (.search-bar)

**用途**: 组合搜索、筛选、操作按钮

**代码**:
```html
<div class="search-bar">
    <input type="text" class="search-input" placeholder="搜索...">
    <select class="filter-select">
        <option>全部状态</option>
    </select>
    <button class="btn-outline">
        <i data-lucide="filter"></i>
        <span>筛选</span>
    </button>
</div>
```

**特点**:
- 自动flex布局
- 桌面端横向排列
- 平板端自然换行
- 移动端(<480px)垂直堆叠

---

## 📊 表格组件

> 对于 B 端列表页、审批待办页、工单看板页、主从详情页，优先使用 `.advanced-data-table`、`.table-toolbar`、`.filter-panel` 等复合组件；`.data-table` 更适合作为轻量内嵌表格。

### 1. 数据表格 (.data-table)


**用途**: 展示列表数据、用户列表、订单列表

**完整代码**:
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
                    <button class="btn-icon">
                        <i data-lucide="edit"></i>
                    </button>
                    <button class="btn-icon">
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
                    <button class="btn-icon">
                        <i data-lucide="edit"></i>
                    </button>
                    <button class="btn-icon">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>
    </tbody>
</table>
```

**特点**:
- ✅ 斑马纹设计（偶数行浅蓝色背景）
- ✅ 悬停高亮（浅蓝色 + 阴影）
- ✅ 深浅主题统一
- ✅ 响应式字体和间距

---

## 🏗️ 布局组件

### 1. B端侧边栏布局 (.b-layout-sidebar)

**用途**: 管理后台、B端系统主布局

**完整代码**:
```html
<div class="b-layout-sidebar">
    <!-- 侧边栏 -->
    <aside class="b-sidebar">
        <!-- 品牌区 -->
        <div class="b-sidebar-header">
            <span class="b-sidebar-logo">灵境Core</span>
            <span class="b-sidebar-version">v1.8.1</span>
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
```

**特点**:
- 侧边栏固定260px，可折叠至80px
- 移动端(<768px)侧边栏自动抽屉式
- 主内容区自动填充剩余空间
- 响应式断点: 768px

---

### 2. B端导航菜单 - API选择指南

**重要**: B端系统**推荐使用完整版API** (`.b-sidebar-nav-link`)，简化版仅用于原型开发和快速迭代。

#### 完整版API（推荐B端系统使用）

**用途**: 规范化的B端系统导航菜单

**完整代码**:
```html
<!-- 侧边栏完整结构 -->
<aside class="b-sidebar">
  <!-- 品牌区（Header） -->
  <div class="b-sidebar-header">
    <div class="lingjing-logo">
      <i data-lucide="zap"></i>
    </div>
    <span class="b-sidebar-brand">灵境Core</span>
  </div>

  <!-- 导航菜单（完整版API） -->
  <nav class="b-sidebar-nav">
    <ul class="b-sidebar-nav-list">
      <li class="b-sidebar-nav-item">
        <a href="#" class="b-sidebar-nav-link active">
          <span class="b-sidebar-nav-icon">
            <i data-lucide="home"></i>
          </span>
          <span class="b-sidebar-nav-text">首页</span>
        </a>
      </li>
      <li class="b-sidebar-nav-item">
        <a href="#" class="b-sidebar-nav-link">
          <span class="b-sidebar-nav-icon">
            <i data-lucide="users"></i>
          </span>
          <span class="b-sidebar-nav-text">用户管理</span>
        </a>
      </li>
      <li class="b-sidebar-nav-item">
        <a href="#" class="b-sidebar-nav-link">
          <span class="b-sidebar-nav-icon">
            <i data-lucide="settings"></i>
          </span>
          <span class="b-sidebar-nav-text">系统设置</span>
        </a>
      </li>
    </ul>
  </nav>

  <!-- 底部折叠按钮（Footer） -->
  <div class="b-sidebar-footer">
    <button class="b-sidebar-toggle" onclick="toggleSidebarCollapse()">
      <span class="b-sidebar-toggle-icon">
        <i data-lucide="chevrons-left"></i>
      </span>
      <span class="b-sidebar-toggle-text">收起</span>
    </button>
  </div>
</aside>
```

#### 简化版API（仅用于原型开发）

**用途**: 快速原型和简单项目

**代码**:
```html
<!-- 简化版 - 仅用于快速原型 -->
<nav class="b-sidebar-nav">
  <a href="#" class="b-sidebar-item active">
    <i data-lucide="home"></i>
    <span>首页</span>
  </a>
  <a href="#" class="b-sidebar-item">
    <i data-lucide="users"></i>
    <span>用户管理</span>
  </a>
</nav>
```

**交互效果**（简化版独有）:
- ✨ **悬停右移**：鼠标悬停时菜单项向右移动 4px
- 🎯 **激活指示条**：激活菜单项左侧显示蓝青渐变指示条
- 🌈 **渐变背景**：激活状态使用渐变背景 + 内阴影
- 🔍 **图标缩放**：悬停/激活时图标放大 1.1x/1.15x + 光晕
- 📜 **自定义滚动条**：蓝色细滚动条（4px 宽度）
- 🌗 **深浅主题适配**：自动适配深色模式

**对比**:

| 特性 | 完整版 `.b-sidebar-nav-link` | 简化版 `.b-sidebar-item` |
|------|------------------------------|--------------------------|
| **适用场景** | **B端系统（推荐）** | 快速原型开发 |
| HTML 结构 | 3 层嵌套（ul > li > a） | 2 层嵌套（nav > a） |
| 类名长度 | 19 字符 | 14 字符 (-26%) |
| 子元素 | `.b-sidebar-nav-icon` + `.b-sidebar-nav-text` | 直接 `<i>` + `<span>` |
| 高级交互 | 基础悬停/激活 | 右移、指示条、图标缩放等 |
| 语义化 | ✅ 更规范 | ⚠️ 较简单 |
| 可维护性 | ✅ 易扩展 | ⚠️ 结构扁平 |

**使用建议**:
- ✅ **B端系统 / 新项目**: 优先使用完整版 `.b-sidebar-nav-link`（更规范、易维护、与当前 B 端导航壳一致）
- ✅ **快速原型**: 可使用简化版 `.b-sidebar-item`，但更适合作为低保真或临时结构
- ✅ **旧项目**: 若已采用 `.b-sidebar-nav-link`，继续沿用即可


---

## 🎴 卡片组件

### 1. 内容卡片 (.content-card)

**用途**: 包裹内容、表单、图表

**代码**:
```html
<div class="content-card">
    <h3>卡片标题</h3>
    <p>卡片内容...</p>
</div>
```

**特点**:
- 玻璃拟态效果
- 自动圆角和内边距
- 深浅主题自适应

---

### 2. 统计卡片 (.b-stat-card)

**用途**: KPI数据、统计指标

**代码**:
```html
<div class="b-stat-card">
    <div class="b-stat-label">总用户数</div>
    <div class="b-stat-value">1,234</div>
    <div class="b-stat-trend positive">
        <i data-lucide="trending-up"></i>
        <span>+12.5%</span>
    </div>
</div>
```

**特点**:
- 左侧3px彩色条
- 支持趋势指示器
- 自动响应式布局

---

## 🧭 导航组件

### 1. 面包屑 (.b-breadcrumb)

**用途**: 页面导航路径

**代码**:
```html
<nav class="b-breadcrumb" aria-label="面包屑导航">
    <span class="b-breadcrumb-item"><a href="#" class="b-breadcrumb-link">首页</a></span>
    <span class="b-breadcrumb-separator">/</span>
    <span class="b-breadcrumb-item"><a href="#" class="b-breadcrumb-link">用户管理</a></span>
    <span class="b-breadcrumb-separator">/</span>
    <span class="b-breadcrumb-current">用户列表</span>
</nav>
```


---

### 2. 分页 (.pagination)

**用途**: 数据分页导航

**代码**:
```html
<div class="pagination">
    <button class="pagination-btn">
        <i data-lucide="chevron-left"></i>
    </button>
    <button class="pagination-btn active">1</button>
    <button class="pagination-btn">2</button>
    <button class="pagination-btn">3</button>
    <button class="pagination-btn">
        <i data-lucide="chevron-right"></i>
    </button>
</div>
```

---

## 🏷️ 状态组件

### 1. 徽章 (.badge)

**用途**: 状态标签（成功、警告、错误）

**代码**:
```html
<span class="badge success">已激活</span>
<span class="badge pending">待审核</span>
<span class="badge danger">已禁用</span>
<span class="badge warning">待处理</span>
```

**类型**:
- `.badge.success` - 绿色（成功、已激活）
- `.badge.pending` - 橙色（待审核、处理中）
- `.badge.danger` - 红色（错误、已禁用）
- `.badge.warning` - 黄色（警告、注意）

---

### 2. 卡片标签 (.card-label)

**用途**: 卡片顶部小标签

**代码**:
```html
<div class="content-card">
    <span class="card-label">NEW</span>
    <h3>卡片标题</h3>
</div>
```

---

## 💬 反馈组件

### 1. 空状态 (.empty-state)

**用途**: 无数据提示

**代码**:
```html
<div class="empty-state">
    <div class="empty-state-icon">
        <i data-lucide="inbox"></i>
    </div>
    <div class="empty-state-title">暂无数据</div>
    <div class="empty-state-description">
        当前列表没有数据，请尝试添加新内容
    </div>
    <button class="btn-primary">
        <i data-lucide="plus"></i>
        <span>添加数据</span>
    </button>
</div>
```

---

## 🎯 完整页面示例

### B端系统 - 用户管理页面

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
            <!-- 侧边栏内容 -->
        </aside>

        <main class="b-main">
            <header class="b-header">
                <h1 class="page-title">用户管理</h1>
            </header>

            <div class="b-content">
                <!-- 搜索筛选栏 -->
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="搜索用户...">
                    <select class="filter-select">
                        <option>全部状态</option>
                        <option>已激活</option>
                        <option>待审核</option>
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
                                        <button class="btn-icon">
                                            <i data-lucide="edit"></i>
                                        </button>
                                        <button class="btn-icon">
                                            <i data-lucide="trash-2"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 分页 -->
                    <div class="pagination">
                        <button class="pagination-btn">
                            <i data-lucide="chevron-left"></i>
                        </button>
                        <button class="pagination-btn active">1</button>
                        <button class="pagination-btn">2</button>
                        <button class="pagination-btn">
                            <i data-lucide="chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // 初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    </script>
</body>
</html>
```

---

## 📚 相关文档

- [INTERACTIONS.md](INTERACTIONS.md) - **交互效果完整指南** ⭐
- [CODE_SNIPPETS.md](CODE_SNIPPETS.md) - 代码片段库
- [examples/b-system-complete.html](../examples/b-system-complete.html) - B 端结构参考示例


---

**更新日志**:
- 2026-02-13:
  - 新增交互效果章节，添加涟漪和悬停效果说明
  - **增强B端导航菜单**：添加简化版 API (.b-sidebar-item)
  - **导航菜单高级交互**：悬停右移、激活指示条、渐变背景、图标缩放、自定义滚动条
  - **Bento Grid 简化版**：添加 bento-* 简化类名（如 .bento-item, .bento-lg）
  - 类名优化：减少26%长度，提升开发效率
- 2026-02-12: 初始版本，包含所有核心组件

