# 🧭 system-template-map — B 端系统场景模板映射

> **场景**：`b_system`（B 端管理系统 / 作业系统）  
> **目的**：把“页面类型 → 模板 → Level → Shell → 常见误用”写成显式映射，
> 让 AI 与人类都能在系统场景下稳定走完 `Scene → Type → Template → Level → Guard` 主链。

---

## 0. 总览与真值源

- 样式入口：`components/dist/lingjing-core-b-system.css`
- 主要模板真值源：
  - `scene_coverage_matrix.yml.scene_coverage.b_system`
  - `skill_version.json.examples.canonical.b_system` / `.candidate.b_system`
- 参考模板：
  - canonical：
    - `examples/b-system/b-system-complete.html`
    - `examples/b-system/b-system-charts.html`
  - candidate：
    - `examples/b-system/b-system-production-plan.html`
    - `examples/b-system/b-system-saas.html`
    - `examples/b-system/b-system-task-list-top-filters.html`
    - `examples/b-system/b-system-advanced-list-with-left-filter-panel.html`
    - `examples/b-system/b-system-detail-order.html`
- 中间层索引：
  - `data/task_router.json`
  - `data/template_router.json`

> ⚠ **黑名单提醒**：
> - `examples/b-system/b-system-showcase.html`
> - `examples/b-system/b-system-sidebar.html`  
> 在 `scene_coverage_matrix.yml` 和 `skill_version.json` 中均标记为 `grade: demo / use_scope: forbidden`，**禁止作为业务模板或默认路由**。

---

## 1. 工作台 / 仪表盘（Dashboard / Overview）

- **type_name**：工作台 / 仪表盘
- **type_description**：
  - 首页总览页，突出 KPI、趋势和关键告警；
  - 通常由顶部导航 + KPI 区 + 图表区 + 最近活动/日志组成。
- **primary_example**：
  - `examples/b-system/b-system-complete.html`
- **fallback_examples**：
  - `examples/b-system/b-system-charts.html`（图表密集型仪表盘）
  - `examples/b-system/b-system-production-plan.html`（计划型仪表盘，candidate）
- **recommended_level**：
  - 默认：`level_1`（高匹配模板轻调）
  - 当需要新增 2+ 个关键模块或大改信息架构时：升级为 `level_2`
- **required_shell**：
  - 框架层：`b-layout-sidebar` + `b-sidebar` + `b-main` + `b-header`
  - 模块壳（参考 `scene_coverage_matrix.yml.module_shells.b_system`）：
    - `b_system_dashboard_shell`：`[b-layout-sidebar, b-header, content-card, stats-grid]`
- **key_modules**（典型组合）：
  - KPI 区：`stats-grid` + `b-stat-card`
  - 图表区：`charts-grid` + `b-chart-card`
  - 活动/日志：`content-card` + `status-timeline`
- **common_misuse**：
  - 使用 `b-system-showcase.html` 作为首页模板（组件展厅并非业务页）。
  - 在仪表盘里堆叠过多列表/表格，导致“首页变列表页”。
  - 不使用 `stats-grid / charts-grid`，而自造 `.dashboard-container` 等类。
- **human_confirmation_needed**：
  - 需由产品/业务确认：
    - 首页必须展示的 4–6 个 KPI 是哪些？
    - 哪些图表是“日常运营必看”，哪些属于次要分析？

---

## 2. 列表页（List Page）

- **type_name**：列表页
- **type_description**：
  - 包含搜索条件、数据表格、操作列和分页的标准列表；
  - 默认使用**表格上方的筛选区 / 顶部筛选条**承载筛选条件，而不是左侧固定筛选面板；
  - 可作为大部分资源管理/工单/记录的基础页型。
- **primary_example**：
  - `examples/b-system/b-system-task-list-top-filters.html`
- **fallback_examples**：
  - `examples/b-system/b-system-complete.html`（canonical，总览壳内的列表段落）
  - `examples/b-system/b-system-production-plan.html`（candidate）
- **recommended_level**：
  - 默认：`level_1`
  - 当字段极多（> 10 列）或需要复杂筛选/工具栏时：可考虑升为 `level_2`，**但仍优先保持列表页 + 顶部筛选条结构，仅在满足“高级筛选列表”条件时才切换为 advanced_list。**
- **upgrade_guard_rules（list → advanced_list）**：
  - 仅当 PRD 中明确出现以下语义之一时，才允许从 `list` 升级为 `advanced_list`：
    - “左侧筛选面板”“高级筛选侧栏”“复杂常驻筛选结构”等；
  - 仅出现“筛选 / 过滤 / 条件筛选”等模糊字样，或只是筛选条件数量较多，**不能单独作为升级 advanced_list 的理由**；
  - 若顶部 `search-bar` 可以容纳筛选条件，则必须优先保持 `list + 顶部筛选条`，并在需要高级筛选时再显式改为 advanced_list。

- **required_shell**：
  - 框架层：`b-layout-sidebar` + `b-sidebar` + `b-main` + `b-header`
  - 内容壳：
    - 外层：`content-card`
    - 搜索区：位于表格上方的 `search-bar` + `search-input` + `filter-select`
    - 表格壳：`data-table-container` + `table.data-table`
- **key_modules**：
  - 顶部操作：`card-header` + `card-title` + 右上角主操作按钮
  - 搜索框：`search-bar` + 输入框 + 筛选按钮
  - 数据表：`data-table-container > table.data-table`，带 `thead/tbody`
  - 分页：`pagination`（可为原生结构，但需有容器）
- **common_misuse**：
  - 直接把表格写在 `b-content` 下，未放入 `content-card`。
  - 表格列很多，却没有 `data-table-container`，导致横向溢出。
  - 自造 `.table-search` / `.table-actions` 等类名，而不用 `search-bar` / `action-buttons`。
  - **仅因为需求中出现“筛选”字样，就把普通列表页改造成左侧筛选面板布局（该布局属于高级筛选列表，而非所有 list 的默认形态）。**
- **human_confirmation_needed**：
  - 需确认：
    - 哪些筛选条件是“常用”，需要常驻在 `search-bar` 内？
    - 是否需要高级筛选侧栏（见下一节“高级筛选列表”）。


---

## 3. 高级筛选列表（Advanced List）

- **type_name**：高级筛选列表
- **type_description**：
  - 左侧为筛选面板，右侧为列表/表格；适用于条件复杂、需要多维组合筛选的场景；
  - **仅当筛选条件维度多、需要长期并列展示且不适合收纳在表格上方的顶部筛选条时，才启用高级筛选列表。左侧独立筛选面板是 advanced_list 的特征，而不是所有 list 的默认形态。**
- **primary_example**：
  - `examples/b-system/b-system-advanced-list-with-left-filter-panel.html`
- **fallback_examples**：
  - `examples/b-system/b-system-complete.html`（canonical，需按 `advanced-data-table` 壳重排）
  - `examples/b-system/b-system-production-plan.html`（candidate，适合作为表格区与操作区参考）
- **recommended_level**：
  - 默认：`level_2`（组件编排）
- **required_shell**：
  - 框架层：`b-layout-sidebar` + `b-sidebar` + `b-main` + `b-header`
  - 高级列表壳：
    - `advanced-data-table`
    - `advanced-data-table-side` + `filter-panel`
    - `advanced-data-table-main`
    - `table-toolbar` + `data-table-container` + `table.data-table`
- **key_modules**：
  - 筛选面板：`filter-panel`（header/body/footer）+ 表单控件
  - 工具栏：`table-toolbar`（统计信息 + 操作按钮）
  - 表格：`data-table-container > table.data-table`
- **common_misuse**：
  - 把筛选条件直接塞在表头上方的 `search-bar`，导致横向拥挤；明明适合 Advanced List 却继续沿用普通列表页结构。
  - 不使用 `advanced-data-table` 壳，散装布局左侧筛选与右侧表格，导致后续样式难以统一维护。
  - **仅因为 PRD 中提到“有筛选”，就直接采用左侧高级筛选面板布局，而没有证明普通列表页 + 顶部筛选区无法承载需求。**
- **human_confirmation_needed**：
  - 需确认：
    - 哪些筛选是“经常切换”的？是否需要固定面板？
    - 是否需要“保存筛选方案 / 快捷筛选卡片”等增值功能？


---

## 4. 详情页（Detail Page）

- **type_name**：详情页
- **type_description**：
  - 展示单个实体的完整信息，常包含基本信息、状态时间线、关联记录等；
  - 页面主任务流应围绕“一个清晰的主实体”展开，而不是多个实体的工作台化大杂烩。
- **primary_example**：
  - `examples/b-system/b-system-detail-order.html`
- **fallback_examples**：
  - `examples/b-system/b-system-complete.html`（canonical，适合作为框架层与卡片参考）
  - `examples/b-system/b-system-production-plan.html`（candidate，可借用局部表格与状态区）
- **recommended_level**：
  - 默认：`level_1`
  - 当字段极多（> 20）或需要 Tab 标签页/复杂布局时：`level_2`，甚至 `level_3`（信息架构明显扩展）。
- **required_shell**：
  - 框架层：`b-layout-sidebar` + `b-sidebar` + `b-main` + `b-header`
  - 内容壳：
    - `b-content`
    - 组合：`grid-cols-2` + 多个 `content-card`
- **key_modules**：
  - 基本信息卡：`content-card` + `card-header` + `form-group` + `form-label` + 文本/Badge
  - 操作历史：`content-card` + `status-timeline`
  - 关联数据：`content-card` + `data-table-container` + `table.data-table`
- **upgrade_guard_rules（detail → dashboard / workspace）**：
  - 当 PRD 要求在详情页顶部添加大量 KPI 总览（stats-grid / charts-grid），并突出“整体运营情况”时，应优先考虑使用 dashboard + detail 的组合方案，而不是把详情页升级成半个工作台。
  - 当同一页面内需要并列展示多个独立主任务流（例如多个工单的处理状态 + 跨部门任务看板）时，说明已经超出单详情页范畴，应 stop&ask 并评估是否需要新的 dashboard/workspace 类型。
- **common_misuse**：
  - 把详情页做成单列长表单，缺乏分组与视觉层次。
  - 把所有历史记录直接放在表格里，而不用 `status-timeline` 表达关键节点。
  - 在详情页顶部堆叠 `stats-grid` / `charts-grid` 等仪表盘壳，使页面更像首页工作台而不是“单实体详情”。
- **human_confirmation_needed**：
  - 需确认：
    - 哪些字段是“第一屏必须看到”的？
    - 是否需要将部分字段折叠到高级信息区或二级页？
    - 当 PRD 同时强调“单工单详情”与“整体运营 KPI 总览”时，是否需要拆分为 dashboard + detail 两类页面？


---

## 5. 配置页（Settings Page）

- **type_name**：配置页（Settings）
- **type_description**：
  - 左侧为配置项分类导航，右侧为表单与配置项；常用于系统设置/个人偏好等。
- **primary_example**：
  - `docs/operations/b-system-layout-playbook.md` 中的“布局模式 5 — 配置页（Settings Page）”。
- **fallback_examples**：
  - 当前无 canonical 具体 HTML 文件，可参考 `b-system-complete` 中的表单卡片结构进行组合。
- **recommended_level**：
  - 默认：`level_2`（组件编排），因为配置页往往需要项目级扩展。
- **required_shell**：
  - 框架层：`b-layout-sidebar` + `b-sidebar` + `b-main` + `b-header`
  - 配置壳：
    - 左侧：`settings-nav` / `settings-nav-item`
    - 右侧：`content-card` + 表单控件
- **key_modules**：
  - 分类导航：垂直菜单形式，当前选中项高亮
  - 表单区块：分组标题 + `form-group` 列表
  - 提交区：主按钮 + 次按钮
- **common_misuse**：
  - 把配置页当普通列表页做，仅提供表格而没有清晰的分类结构。
  - 过度使用自定义类名，导致样式无法复用。
- **human_confirmation_needed**：
  - 需确认：
    - 设置项是否需要分组/分 Tab？
    - 哪些配置对安全/合规敏感，需要额外确认或提示？

---

## 6. 补充：与中间层和审计的关系

- 当你在 `data/task_router.json` 中新增/调整与 `b_system` 相关的任务时，应：
  1. 先在本文件中找到对应 `type_name`，确保 type → template → level → shell 的映射清晰；
  2. 再将这些信息同步到 `scene_coverage_matrix.yml.scene_coverage.b_system` 与 `skill_version.json`；
  3. 最后才更新 `task_router` / `template_router`。
- 在为系统场景生成页面后：
  - 必须运行 `scripts/skill-audit.js <file> --scene b_system`；
  - 若出现 `frame_shell_missing` / `unknown_classes` / `table_overflow_missing_container` 等 ERROR，说明你偏离了本映射或真值源，需要先修复再交付。

通过本文件，你可以把“这是什么类型的系统页面？应该用哪张模板？应该走哪个 Level？壳是什么？人类要拍板什么？”这些问题说清楚，而不再只是“凭感觉选一个 examples 文件”。