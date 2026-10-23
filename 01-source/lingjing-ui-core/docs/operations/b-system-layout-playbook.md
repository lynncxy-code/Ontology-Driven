# B 端系统布局决策卡

> **适用场景**：`b_system`（B端管理系统/作业系统）
> **样式入口**：`lingjing-core-b-system.css`
> **依赖食谱**：`docs/reference/b-system-composition-recipes.md`

---

## 如何使用本文档

1. 确认页面类型（仪表盘 / 列表页 / 详情页 / 配置页）
2. 查找对应「布局模式」，复制骨架代码
3. 按「禁止做法」排查违规项
4. 运行 `node scripts/skill-audit.js <html> --scene b_system` 确认无 ERROR

---

## 布局模式 1 — 仪表盘 / 驾驶舱（Dashboard）

**典型需求**：指标概览 + 图表 + 日志/动态

```
┌─────────────────────────────────────────────────────────┐
│  b-header（面包屑 + 操作）                               │
├─────────────────────────────────────────────────────────┤
│  stats-grid（b-stat-card × 4）                          │
├─────────────────────────────────────────────────────────┤
│  charts-grid（b-chart-card × 2）                        │
├─────────────────────────────────────────────────────────┤
│  content-card（日志 / 状态时间线）                       │
└─────────────────────────────────────────────────────────┘
```

**骨架代码**：

```html
<main class="b-main">
  <header class="b-header">…</header>
  <div class="b-content">

    <!-- KPI 统计区 -->
    <div class="stats-grid">
      <div class="b-stat-card" data-color="blue">…</div>
      <div class="b-stat-card" data-color="green">…</div>
      <div class="b-stat-card" data-color="orange">…</div>
      <div class="b-stat-card" data-color="purple">…</div>
    </div>

    <!-- 图表区 -->
    <div class="charts-grid">
      <div class="b-chart-card">
        <div class="b-chart-header">…</div>
        <div class="b-chart-body">
          <!-- ECharts: <div id="chart-a" class="echarts-container"></div> -->
        </div>
      </div>
      <div class="b-chart-card">…</div>
    </div>

    <!-- 日志 / 时间线 -->
    <div class="content-card">
      <div class="card-header"><h3 class="card-title">操作日志</h3></div>
      <ul class="status-timeline">
        <li class="status-timeline-item completed">…</li>
      </ul>
    </div>

  </div>
</main>
```

**推荐 Level**：Level 1（模板直用）；仅当 KPI 指标超过 8 个或需要地图/3D 可视化时升 Level 2。

---

## 布局模式 2 — 列表管理页（List Page）

**典型需求**：搜索筛选 + 数据表格 + 分页

```
┌─────────────────────────────────────────────────────────┐
│  b-header                                               │
├─────────────────────────────────────────────────────────┤
│  content-card                                           │
│    ├── card-header（标题 + 新增按钮）                   │
│    ├── search-bar 或 filter-bar（见下方说明）            │
│    ├── data-table-container > table.data-table          │
│    └── pagination                                       │
└─────────────────────────────────────────────────────────┘
```

**骨架代码**：

```html
<div class="b-content">
  <div class="content-card">
    <div class="card-header">
      <h2 class="card-title">列表标题</h2>
      <button class="btn-primary"><i data-lucide="plus"></i><span>新增</span></button>
    </div>

    <!-- 筛选行选择规则：
         search-bar  → 字段即改即生效，无显式"应用/重置"按钮（1–4个字段）
         filter-bar  → 有显式"应用筛选"+"重置"按钮时使用（任意字段数）-->
    <div class="search-bar">
      <input type="text" class="search-input" placeholder="搜索…">
      <select class="filter-select"><option>全部状态</option></select>
    </div>
    <!-- 若需显式按钮，改用：
    <div class="filter-bar">
      <div class="filter-bar-main">
        <input type="text" class="search-input" placeholder="搜索…">
        <select class="filter-select"><option>全部状态</option></select>
      </div>
      <div class="filter-bar-extra">
        <button class="btn-outline">重置</button>
        <button class="btn-primary">应用筛选</button>
      </div>
    </div>
    -->

    <div class="data-table-container">
      <table class="data-table">
        <thead><tr><th>字段A</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr>
            <td>值</td>
            <td><span class="badge badge-success">正常</span></td>
            <td>
              <div class="action-buttons">
                <button class="btn-icon" title="查看"><i data-lucide="eye"></i></button>
                <button class="btn-icon" title="编辑"><i data-lucide="edit"></i></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pagination">…</div>
  </div>
</div>
```

**推荐 Level**：Level 1；列超过 8 列或需要左侧筛选面板时改用 Recipe 8（advanced-data-table）→ Level 2。

---

## 布局模式 3 — 列表 + 高级筛选（Advanced List）

**典型需求**：左侧筛选面板 + 右侧表格 + 工具栏

```
┌──────────┬──────────────────────────────────────────────┐
│  filter  │  table-toolbar（统计 + 导出 + 新增）         │
│  panel   ├──────────────────────────────────────────────┤
│  (side)  │  data-table-container > table.data-table     │
│          ├──────────────────────────────────────────────┤
│          │  pagination                                  │
└──────────┴──────────────────────────────────────────────┘
```

**骨架代码**：

```html
<div class="advanced-data-table">
  <div class="advanced-data-table-side">
    <div class="filter-panel">
      <div class="filter-panel-header">
        <span class="filter-panel-title">筛选条件</span>
      </div>
      <div class="filter-panel-body">
        <div class="form-group">
          <label class="form-label">状态</label>
          <div class="form-select-wrapper">
            <select class="form-select"><option>全部</option></select>
          </div>
        </div>
      </div>
      <div class="filter-panel-footer">
        <button class="btn-primary btn-sm">应用</button>
        <button class="btn-outline btn-sm">重置</button>
      </div>
    </div>
  </div>

  <div class="advanced-data-table-main">
    <div class="table-toolbar">
      <div class="table-toolbar-meta">共 128 条</div>
      <div class="table-toolbar-actions">
        <button class="btn-outline btn-sm"><i data-lucide="download"></i> 导出</button>
        <button class="btn-primary btn-sm"><i data-lucide="plus"></i> 新增</button>
      </div>
    </div>
    <div class="data-table-container">
      <table class="data-table">…</table>
    </div>
  </div>
</div>
```

**推荐 Level**：Level 2。

---

## 布局模式 4 — 详情页（Detail Page）

**典型需求**：基本信息卡片 + 操作历史 + 关联数据

```
┌─────────────────────────────────────────────────────────┐
│  b-header（面包屑：列表 / 详情名称）                    │
├───────────────────────┬─────────────────────────────────┤
│  content-card         │  content-card                   │
│  （基本信息 + 表单）  │  （状态时间线 / 相关记录）      │
└───────────────────────┴─────────────────────────────────┘
```

**骨架代码**：

```html
<div class="b-content">
  <!-- 两列布局：左侧信息区 + 右侧历史区 -->
  <div class="grid-cols-2 gap-lg">

    <!-- 左：基本信息 -->
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">基本信息</h3>
        <button class="btn-outline btn-sm"><i data-lucide="edit"></i> 编辑</button>
      </div>
      <div class="form-group"><label class="form-label">名称</label><p>值</p></div>
      <div class="form-group"><label class="form-label">状态</label>
        <span class="badge badge-success">正常</span>
      </div>
    </div>

    <!-- 右：操作历史 -->
    <div class="content-card">
      <div class="card-header"><h3 class="card-title">操作历史</h3></div>
      <ul class="status-timeline">
        <li class="status-timeline-item completed">
          <div class="status-timeline-dot"></div>
          <div class="status-timeline-content">
            <span class="status-timeline-title">创建记录</span>
            <span class="status-timeline-time">2024-01-15 09:00</span>
          </div>
        </li>
      </ul>
    </div>

  </div>

  <!-- 下方关联数据表格（可选） -->
  <div class="content-card">
    <div class="card-header"><h3 class="card-title">关联记录</h3></div>
    <div class="data-table-container">
      <table class="data-table">…</table>
    </div>
  </div>
</div>
```

**推荐 Level**：Level 1~2；详情字段超过 20 个时，拆分为 Tab 标签页（项目级扩展，Level 3）。

---

## 布局模式 5 — 配置页（Settings Page）

**典型需求**：左侧分类导航 + 右侧表单区域

```
┌──────────────┬──────────────────────────────────────────┐
│  settings-   │  content-card（表单区块 1）              │
│  nav         ├──────────────────────────────────────────┤
│  （侧边列表） │  content-card（表单区块 2）              │
└──────────────┴──────────────────────────────────────────┘
```

**骨架代码**：

```html
<div class="b-content">
  <div class="grid-master-detail">
    <!-- 左侧：设置分类 -->
    <nav class="content-card">
      <ul class="b-sidebar-nav-list">
        <li class="b-sidebar-nav-item">
          <a href="#general" class="b-sidebar-nav-link active">
            <span class="b-sidebar-nav-icon"><i data-lucide="settings"></i></span>
            <span class="b-sidebar-nav-text">通用设置</span>
          </a>
        </li>
        <li class="b-sidebar-nav-item">
          <a href="#security" class="b-sidebar-nav-link">
            <span class="b-sidebar-nav-icon"><i data-lucide="shield"></i></span>
            <span class="b-sidebar-nav-text">安全设置</span>
          </a>
        </li>
      </ul>
    </nav>

    <!-- 右侧：表单区块 -->
    <div>
      <div class="content-card" id="general">
        <div class="card-header"><h3 class="card-title">通用设置</h3></div>
        <div class="form-group">
          <label class="form-label">系统名称</label>
          <input type="text" class="form-input" value="灵境Core">
        </div>
        <div class="form-group">
          <label class="form-label">自动保存</label>
          <label class="form-switch">
            <input type="checkbox" checked>
            <span class="form-switch-track"></span>
          </label>
        </div>
        <div>
          <button class="btn-primary">保存</button>
          <button class="btn-outline">取消</button>
        </div>
      </div>
    </div>
  </div>
</div>
```

**推荐 Level**：Level 2；设置项极多时升 Level 3，引入 Tab 分页（项目前缀类）。

---

## 通用禁止做法

| 类型 | 禁止行为 | 正确替代 |
|------|---------|---------|
| 骨架替换 | 用 `.custom-sidebar` / `.my-nav` 替代 `b-sidebar` | 必须用 `b-layout-sidebar > b-sidebar + b-main` |
| **错误根元素** | `<div class="b-layout">` 或 `<div class="b-body">` | `b-layout` / `b-body` 在库中**无任何样式定义**，导致高度链断裂（`chat-messages`、`b-content` 的 `height:100%` 全部失效）；正确根元素见下方说明 |
| 内联样式 | `style="width:300px; margin-top:20px"` | 用 `w-xl`、`mt-lg` 等 utility 类 |
| 裸表格 | `<table class="data-table">` 无容器 | 必须 `<div class="data-table-container"><table…>` |
| 废弃类 | `nav-sidebar` / `card-glass` / `header-top` | 见 `class_registry.json` 的 `deprecated.use_instead` |
| alias 类 | `activity-timeline` 直接写入 HTML | 归一化为 `status-timeline` |
| demo_only 类 | `demo-info-card` / `world-marker--demo-a` | 改用 `content-card` / 业务语义修饰符 |

### 根元素选择规则

| 布局类型 | 正确根元素 | 库定义 |
|---------|-----------|-------|
| 顶部导航栏，无侧边栏 | `b-layout-topbar` | `display:flex; flex-direction:column; height:100vh; overflow:hidden` |
| 左侧导航栏 | `b-layout-sidebar` | `display:flex; height:100vh; overflow:hidden` |

**错误示例（`b-layout` 无效）：**
```html
<!-- ❌ b-layout / b-body 不存在，height 链断裂 -->
<div class="b-layout">
  <header class="b-topbar">…</header>
  <div class="b-body">
    <main class="b-content" style="height:100%">…</main>
  </div>
</div>
```

**正确示例：**
```html
<!-- ✅ b-layout-topbar 提供 height:100vh + flex-direction:column -->
<div class="b-layout-topbar">
  <header class="b-topbar">…</header>
  <main class="b-content" style="padding:0; overflow:hidden; min-height:0;">
    …
  </main>
</div>
```

---

## 快速决策树

```
新 B 端页面需求
│
├─ 有多个指标 + 图表？
│   └─ 布局模式 1（仪表盘）
│
├─ 主体是数据列表？
│   ├─ 筛选条件 ≤ 3 个 → 布局模式 2（简单列表）
│   └─ 筛选条件 > 3 个 → 布局模式 3（高级列表）
│
├─ 主体是单条记录详情？
│   └─ 布局模式 4（详情页）
│
└─ 主体是系统配置表单？
    └─ 布局模式 5（配置页）
```
