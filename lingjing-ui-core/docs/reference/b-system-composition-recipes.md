# B 端系统高频组合食谱

> **适用场景**：`b_system`（B端管理系统/作业系统）
> **样式入口**：`lingjing-core-b-system.css`
> **canonical 参考文件**：`examples/b-system/b-system-complete.html`
> **真值来源**：`data/class_registry.json`（所有类名均为 `type: canonical`，可直接落地）

---

## 使用规则

1. **食谱 = 最小可用 DOM 骨架**，按需组合，不强制全用。
2. **禁止重命名**：类名必须与本文件一致，不得用 `.my-header`、`.custom-sidebar` 替代。
3. **扩展方式**：在官方类容器内加内容，或叠加项目修饰符类（如 `b-stat-card--warning`），项目修饰符样式由调用方项目 CSS 提供。
4. 食谱通过 `skill-audit.js` 检验，若输出 FAIL 必须先修复类名再声称完成。

---

## Recipe 1 — 页面顶部栏（Header）

适用于：所有 B 端页面的固定顶部区域。**框架层，必须强一致，禁止自建替代。**

```html
<header class="b-header">
  <!-- 左侧：面包屑 -->
  <div class="b-header-left">
    <nav class="b-breadcrumb">
      <div class="b-breadcrumb-item">
        <a href="#" class="b-breadcrumb-link">首页</a>
        <span class="b-breadcrumb-separator">/</span>
      </div>
      <div class="b-breadcrumb-item">
        <span class="b-breadcrumb-current">当前页面</span>
      </div>
    </nav>
  </div>

  <!-- 右侧：功能按钮 -->
  <div class="b-header-right">
    <!-- 主题切换（可选） -->
    <button class="btn-icon" onclick="window.Lingjing.toggleTheme()" title="切换主题">
      <i data-lucide="moon" class="icon-light"></i>
      <i data-lucide="sun" class="icon-dark hidden"></i>
    </button>
    <!-- 通知（可选） -->
    <button class="btn-icon" title="通知">
      <i data-lucide="bell"></i>
    </button>
    <!-- 用户菜单（可选） -->
    <button class="btn-icon" title="用户菜单">
      <i data-lucide="user"></i>
    </button>
  </div>
</header>
```

**注意**：
- `icon-light` / `icon-dark`：主题切换图标对类，由 `window.Lingjing.toggleTheme()` 控制显隐
- 隐藏用 `hidden` utility 类（禁止 `style="display:none"`）

---

## Recipe 2 — 左侧导航栏（Sidebar）

适用于：所有 B 端页面的左侧固定导航。**框架层，必须强一致。**

> ⚠️ **强制要求**：B 端页面侧边栏**必须**实现展开/收起功能，不允许生成无法折叠的固定侧边栏。详见 `SKILL.md §1.3 b_system 深读入口`。

```html
<div class="b-layout-sidebar">
  <aside class="b-sidebar" id="sidebar">
    <!-- 品牌区 -->
    <div class="b-sidebar-header">
      <div class="b-sidebar-logo">
        <img src="assets/logo-flat.png" alt="灵境" height="32">
      </div>
      <span class="b-sidebar-brand">系统名称</span>
    </div>

    <!-- 导航区 -->
    <nav class="b-sidebar-nav b-scrollable">
      <ul class="b-sidebar-nav-list">
        <!-- 激活态：加 active 类；每项必须加 title 属性供收起时 tooltip 显示 -->
        <li class="b-sidebar-nav-item">
          <a href="#" class="b-sidebar-nav-link active" title="仪表盘">
            <span class="b-sidebar-nav-icon"><i data-lucide="layout-dashboard"></i></span>
            <span class="b-sidebar-nav-text">仪表盘</span>
          </a>
        </li>
        <li class="b-sidebar-nav-item">
          <a href="#" class="b-sidebar-nav-link" title="数据管理">
            <span class="b-sidebar-nav-icon"><i data-lucide="database"></i></span>
            <span class="b-sidebar-nav-text">数据管理</span>
          </a>
        </li>
        <!-- 分割线 -->
        <li><hr class="divider"></li>
        <!-- 更多导航项… -->
      </ul>
    </nav>

    <!-- 必须：收起/展开按钮（不得省略） -->
    <div class="b-sidebar-footer">
      <button class="b-sidebar-toggle" id="sidebarToggle" onclick="toggleSidebarCollapse()" title="收起侧边栏">
        <span class="b-sidebar-toggle-icon"><i data-lucide="chevrons-left" id="sidebarToggleIcon"></i></span>
        <span class="b-sidebar-toggle-text">收起</span>
      </button>
    </div>
  </aside>

  <!-- 移动端遮罩 -->
  <div class="b-sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

  <!-- 主内容区 -->
  <main class="b-main">
    <header class="b-header">…</header>
    <div class="b-content">
      <!-- 页面正文 -->
    </div>
  </main>
</div>
```

**顶层骨架结构**：`div.b-layout-sidebar > aside.b-sidebar + main.b-main`
**内容容器**：`main.b-main > header.b-header + div.b-content`

**侧边栏展开/收起 JS（必须包含，直接照抄）**：

```javascript
// ── 侧边栏收起/展开 ───────────────────────────
var sidebarCollapsed = false;

function toggleSidebarCollapse() {
  sidebarCollapsed = !sidebarCollapsed;
  var sidebar = document.getElementById('sidebar');
  var icon = document.getElementById('sidebarToggleIcon');
  var toggleBtn = document.getElementById('sidebarToggle');

  if (sidebarCollapsed) {
    sidebar.classList.add('collapsed');       // ⚠️ 注意：是 'collapsed'，不是 'b-sidebar--collapsed'
    icon.setAttribute('data-lucide', 'chevrons-right');
    toggleBtn.title = '展开侧边栏';
  } else {
    sidebar.classList.remove('collapsed');
    icon.setAttribute('data-lucide', 'chevrons-left');
    toggleBtn.title = '收起侧边栏';
  }
  lucide.createIcons();
  if (typeof LingJingChart !== 'undefined') {
    setTimeout(function() { LingJingChart.resizeAll(); }, 300);
  }
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed ? '1' : '0');
}

// ── DOMContentLoaded 中加入（恢复上次状态） ────
// if (localStorage.getItem('sidebarCollapsed') === '1') { toggleSidebarCollapse(); }
```

---

## Recipe 3 — KPI 统计卡片组（Stats Grid）

适用于：仪表盘、概览页的指标展示区。

```html
<!-- 默认 4 列，可叠加 grid-cols-2 改为 2 列 -->
<div class="stats-grid">
  <!-- data-color 可选: blue / green / orange / purple / red / cyan -->
  <div class="b-stat-card" data-color="blue">
    <div class="b-stat-header">
      <span class="b-stat-label">指标名称</span>
      <i data-lucide="users" class="b-stat-icon"></i>
    </div>
    <div class="b-stat-value">12,847</div>
    <div class="b-stat-change positive">
      <!-- positive / negative / neutral -->
      <i data-lucide="trending-up"></i>
      <span>+18.2% 较上月</span>
    </div>
  </div>
  <!-- 重复 b-stat-card 块 -->
</div>
```

**说明**：
- `data-color` 属性驱动左侧色条，无需额外类
- `b-stat-change` 状态类：`positive`（绿色）/ `negative`（红色）/ `neutral`（灰色）
- 在窄空间（如抽屉）叠加 `grid-cols-2` 强制两列

---

## Recipe 4 — 图表卡片（Chart Card）

适用于：Dashboard 的图表展示区，含占位图（ECharts 未集成时）与实际图表挂载点。

```html
<div class="charts-grid">
  <div class="b-chart-card">
    <div class="b-chart-header">
      <div>
        <h3 class="b-chart-title">图表标题</h3>
        <p class="b-chart-subtitle">副标题 / 时间范围</p>
      </div>
      <div>
        <button class="btn-text">
          <i data-lucide="download"></i>
          <span>导出</span>
        </button>
      </div>
    </div>
    <div class="b-chart-body">
      <!-- 占位图（无 ECharts 时使用） -->
      <div class="chart-placeholder">
        <i data-lucide="trending-up" width="48" height="48" class="opacity-30"></i>
      </div>
      <!-- 有 ECharts 时替换为：<div id="chart-xxx" class="echarts-container"></div> -->
    </div>
    <!-- 可选底部说明 -->
    <!-- <div class="b-chart-footer">…</div> -->
  </div>
</div>
```

**禁止**：`chart-placeholder` 仅用于开发占位。PRD 要求图表时必须输出 ECharts DOM + 初始化脚本，不得以占位图代替（见 `SKILL.md §0.0.2 严禁图表空转`）。

---

## Recipe 5 — 内容卡片（Content Card）

适用于：信息展示、表单包装、说明区块等通用容器。

```html
<div class="content-card">
  <div class="card-header">
    <h3 class="card-title">
      <i data-lucide="info"></i>
      卡片标题
    </h3>
    <!-- 右侧操作按钮（可选） -->
    <button class="btn-primary">
      <i data-lucide="plus"></i>
      <span>新增</span>
    </button>
  </div>

  <!-- 卡片正文内容直接置于 content-card 内，无需 card-body 包装层 -->
  <p class="text-secondary">说明文本</p>

  <!-- 底部操作区（可选） -->
  <!-- 直接在 content-card 末尾写按钮区 -->
</div>
```

**注意**：`card-body` 类不存在，内容直接放在 `content-card` 中。

---

## Recipe 6 — 搜索筛选区（Search Bar）

适用于：数据列表页的搜索 + 快速筛选行。

```html
<div class="search-bar">
  <input type="text" class="search-input" placeholder="搜索…">
  <select class="filter-select">
    <option>全部状态</option>
    <option>已激活</option>
    <option>已禁用</option>
  </select>
  <button class="btn-outline">
    <i data-lucide="filter"></i>
    <span>筛选</span>
  </button>
</div>
```

需要高级筛选面板时，在卡片内叠加 `filter-panel`：

```html
<div class="filter-panel">
  <div class="filter-panel-header">
    <span class="filter-panel-title">筛选条件</span>
  </div>
  <div class="filter-panel-body">
    <!-- filter-bar 行 -->
    <div class="filter-bar">
      <div class="filter-bar-main">
        <!-- 多个 filter-select / form-input 等 -->
      </div>
      <div class="filter-bar-extra">
        <button class="btn-primary btn-sm">搜索</button>
        <button class="btn-outline btn-sm">重置</button>
      </div>
    </div>
  </div>
</div>
```

---

## Recipe 7 — 数据表格（Data Table）

适用于：列表页标准数据表格，含搜索、操作列和状态徽章。

```html
<div class="content-card">
  <div class="card-header">
    <h2 class="card-title">列表标题</h2>
    <button class="btn-primary">
      <i data-lucide="plus"></i>
      <span>新增</span>
    </button>
  </div>

  <!-- Recipe 6 搜索筛选区 -->
  <div class="search-bar">…</div>

  <!-- 必须包裹在 data-table-container 中，禁止裸 table.data-table -->
  <div class="data-table-container">
    <table class="data-table">
      <thead>
        <tr>
          <th>字段A</th>
          <th>字段B</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>值A</td>
          <td>值B</td>
          <td>
            <!-- 状态徽章: badge-success / badge-warning / badge-error / badge-info -->
            <span class="badge badge-success">正常</span>
          </td>
          <td>
            <div class="action-buttons">
              <button class="btn-icon" title="查看"><i data-lucide="eye"></i></button>
              <button class="btn-icon" title="编辑"><i data-lucide="edit"></i></button>
              <button class="btn-icon" title="删除"><i data-lucide="trash-2"></i></button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div><!-- /data-table-container -->

  <!-- 分页（可选） -->
  <div class="pagination">…</div>
</div>
```

**必须**：`table.data-table` 必须包裹在 `div.data-table-container` 内（skill-audit 会检查，缺失则 FAIL）。

---

## Recipe 8 — 高级数据表格（Advanced Data Table）

适用于：带侧边筛选面板的复杂列表页（`b_system` 专用）。

```html
<div class="advanced-data-table">
  <!-- 左侧筛选面板 -->
  <div class="advanced-data-table-side">
    <div class="filter-panel">
      <div class="filter-panel-header">
        <span class="filter-panel-title">筛选</span>
      </div>
      <div class="filter-panel-body">
        <!-- 筛选项 -->
      </div>
      <div class="filter-panel-footer">
        <button class="btn-primary btn-sm">应用</button>
        <button class="btn-outline btn-sm">清除</button>
      </div>
    </div>
  </div>

  <!-- 右侧主表格区 -->
  <div class="advanced-data-table-main">
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <div class="table-toolbar-meta">
        <span class="text-secondary">共 128 条记录</span>
      </div>
      <div class="table-toolbar-actions">
        <button class="btn-outline btn-sm"><i data-lucide="download"></i> 导出</button>
        <button class="btn-primary btn-sm"><i data-lucide="plus"></i> 新增</button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="data-table-container">
      <table class="data-table">…</table>
    </div>
  </div>
</div>
```

---

## Recipe 9 — 状态时间线（Status Timeline）

适用于：操作日志、流程节点、审批记录等时序展示。

> ⚠️ `activity-timeline` 是 `status-timeline` 的 **alias（别名）**，落地时必须使用 `status-timeline`。
> 验证：`data/class_registry.json` 中 `activity-timeline.type === "alias"`

```html
<ul class="status-timeline">
  <li class="status-timeline-item completed">
    <div class="status-timeline-dot"></div>
    <div class="status-timeline-content">
      <span class="status-timeline-title">已创建</span>
      <span class="status-timeline-time">2024-01-15 09:00</span>
    </div>
  </li>
  <li class="status-timeline-item completed">
    <div class="status-timeline-dot"></div>
    <div class="status-timeline-content">
      <span class="status-timeline-title">审核通过</span>
      <span class="status-timeline-time">2024-01-16 14:30</span>
    </div>
  </li>
  <li class="status-timeline-item">
    <!-- 未完成项：不加 completed 类 -->
    <div class="status-timeline-dot"></div>
    <div class="status-timeline-content">
      <span class="status-timeline-title">待执行</span>
      <span class="status-timeline-time">预计 2024-01-20</span>
    </div>
  </li>
</ul>
```

---

## Recipe 10 — 抽屉（Drawer）

适用于：详情查看、二级表单、侧边设置面板。

```html
<!-- 触发按钮（放在 content-card 内） -->
<button class="btn-primary" id="openDrawerRight">打开抽屉</button>

<!-- 抽屉主体（放在 body 末尾或 b-content 内） -->
<!-- 方向类: drawer-right（默认右侧）或 drawer-left -->
<div class="drawer-overlay drawer-right" id="drawerRight" aria-hidden="true">
  <div class="drawer-container" role="dialog" aria-modal="true">
    <div class="drawer-header">
      <h3 class="drawer-title">抽屉标题</h3>
      <button class="drawer-close" type="button" data-drawer-close="drawerRight" aria-label="关闭">
        <i data-lucide="x"></i>
      </button>
    </div>
    <div class="drawer-body">
      <!-- 内容：可嵌套 form-group、content-card 等 -->
    </div>
    <div class="drawer-footer">
      <button class="btn-outline">取消</button>
      <button class="btn-primary">确认</button>
    </div>
  </div>
</div>
```

---

## Recipe 11 — 模态框（Modal）

适用于：确认操作、新建表单、二次确认等。

```html
<!-- 触发按钮 -->
<button class="btn-primary" id="openModal">打开弹窗</button>

<!-- 模态框（放在 body 末尾） -->
<!-- 尺寸类: modal-small / modal-medium / modal-large / modal-fullscreen -->
<div class="modal-overlay" id="modal" aria-hidden="true">
  <div class="modal-container modal-medium" role="dialog" aria-modal="true">
    <div class="modal-header">
      <h3 class="modal-title">弹窗标题</h3>
      <button class="modal-close" type="button" aria-label="关闭">
        <i data-lucide="x"></i>
      </button>
    </div>
    <div class="modal-body">
      <!-- 内容 -->
    </div>
    <div class="modal-footer">
      <button class="btn-outline">取消</button>
      <button class="btn-primary">确认</button>
    </div>
  </div>
</div>
```

危险确认变体（叠加语义类）：
```html
<div class="modal-container modal-small modal-danger">…</div>
```

---

## Recipe 12 — 表单组（Form Group）

适用于：新建/编辑表单，支持输入、选择、开关、文本域。

```html
<!-- 标准文本输入 -->
<div class="form-group">
  <label class="form-label">字段名称</label>
  <input type="text" class="form-input" placeholder="请输入…">
</div>

<!-- 下拉选择 -->
<div class="form-group">
  <label class="form-label">状态</label>
  <div class="form-select-wrapper">
    <select class="form-select">
      <option>全部</option>
      <option>激活</option>
    </select>
  </div>
</div>

<!-- 开关 -->
<div class="form-group">
  <label class="form-label">启用功能</label>
  <label class="form-switch">
    <input type="checkbox">
    <span class="form-switch-track"></span>
  </label>
</div>

<!-- 文本域 -->
<div class="form-group">
  <label class="form-label">备注</label>
  <div class="form-textarea-wrapper">
    <textarea class="form-textarea" rows="4" placeholder="请输入备注…"></textarea>
    <span class="form-textarea-counter">0/500</span>
  </div>
</div>
```

---

## 扩展路径（Level 3）

当以下业务组件技能包未覆盖时，按 `SKILL.md §2.3` 三级扩展梯度处理：

| 业务组件 | 推荐扩展方式 |
|---------|------------|
| **权限树/组织树** | 嵌套在 `advanced-data-table-side` 或 `content-card` 内，用项目类 `.pj-permission-tree`；不得替换 `b-sidebar` |
| **用户信息头像区** | 放在 `b-sidebar-footer` 或 `b-header-right`，用 `btn-icon` 触发弹出；头像使用 `<figure>` 标签 |
| **步骤条/向导** | 嵌套在 `content-card` 内，用项目类 `.pj-b-stepper`；样式由项目 CSS 提供 |
| **看板/拖拽列** | 在 `b-content` 内实现，用项目类 `.pj-b-kanban`；禁止替换 `b-main` 骨架 |
| **折叠展开面板** | 用 `content-card` 作包装，`<details>/<summary>` 或 JS 控制折叠；不需要新组件类 |

---

## 快速检验清单

生成 B 端页面后，运行 `node scripts/skill-audit.js <html文件> --scene b_system`，确认：

- `frame_shell_missing: []`（b-layout-sidebar / b-sidebar / b-main / b-header 均存在）
- `unknown_classes: []`（无未收录类名）
- `table_overflow_missing_container: []`（所有 `table.data-table` 均有 `data-table-container`）
- `demo_only_classes: []`（无 demo_only 类泄漏）
- `delivery_gate: PASS`
