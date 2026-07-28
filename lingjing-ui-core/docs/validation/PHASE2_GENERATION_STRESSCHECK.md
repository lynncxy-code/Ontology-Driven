## PHASE2_GENERATION_STRESSCHECK — Phase 2 主线生成压测（b_system + ue5_overlay）

> **目的**：在 Phase 1 主线稳定的基础上，用更大样本的真实任务描述压测当前路由与模板主链，看在 20+ 条任务下是否仍然保持：正确路由、正确壳层选择、审计表现符合预期，以及是否存在明显模板收敛或边界漂移。

---

## 1. 样本设计与范围

- **总体样本数**：24 条（以现有 examples 为代表页）。
- **按场景划分**：
  - `b_system`：14 条
    - dashboard：3 条（含 aircraft-* 变体作为气质对照）
    - list：5 条（含带左侧筛选的越界样本）
    - advanced_list：2 条（正例 + 壳缺失反例）
    - detail：2 条（正例 + dashboard 气质过重对照）
    - 其它支持性：saas / sidebar / showcase 等 2 条
  - `ue5_overlay`：10 条
    - Mode 1：2 条（HUD 正例 + 无 HUD 反例）
    - minimal：1 条
    - Mode 2：2 条（正例 + 带 Dock 反例）
    - Mode 3：2 条（正例 + 壳过轻反例）
    - cockpit/Mode 5 相关：3 条（数字孪生驾驶舱 + sidepanel dock + engine_test/mock_bridge）

每条样本均绑定一个现有 HTML 文件，记录：任务描述、预期 scene/task/type/mode/level、实际模板壳与 `skill-audit.js` 审计结果。

---

## 2. b_system 样本概览（14 条）

> 代表性 examples：
> - `b-system-complete.html`
> - `b-system-task-list-top-filters.html`
> - `b-system-advanced-list-with-left-filter-panel.html`
> - `b-system-detail-order.html`
> - `b-system-production-plan.html`
> - `b-system-advanced-quality-list.html`
> - `b-system-list-with-left-filter-panel.html`
> - `b-system-advanced-list-without-advanced-shell.html`
> - `b-system-charts.html`
> - `b-system-saas.html`
> - `b-system-sidebar.html`
> - `b-system-showcase.html`

### 2.1 Dashboard 类（S1–S3）

- **S1 生产运营总览**
  - 任务描述：典型“产线任务 KPI + 工单分布 + 异常动态 + 重点待办”，图表与 KPI 为主。
  - 预期：scene=`b_system`，task≈`b_system_dashboard_overview`，type=`dashboard`，level=`level_1`。
  - 实际模板：`b-system-complete.html`，壳为 `b-layout-sidebar + stats-grid + charts-grid + content-card`。
  - 审计：PASS（exit=0）。

- **S2 航空运维驾驶台 / cockpit 风格总览**
  - 任务描述：更复杂的多模块运维 cockpit，总体仍为运营总览。
  - 预期：仍落在 dashboard 家族，后续可与 aircraft-* 页面结合用于 cockpit 研究。

- **S3 图表展厅型 dashboard**
  - 任务描述：图表为主、列表为辅的后台页。
  - 实际模板：`b-system-charts.html`，用作 dashboard 气质补充参考。

### 2.2 List 样本（S4–S8）

- **S4 工单列表（正例 list）**
  - 任务描述：工单列表页，顶部 search-bar + 状态/优先级/负责人筛选。
  - 预期：scene=`b_system`，task≈`b_system_list`，type=`list`，level=`level_1`。
  - 实际模板：`b-system-task-list-top-filters.html`（list 壳）。
  - 审计：PASS（exit=0）。

- **S5 质检工单轻量列表**
  - 任务描述：质检工单列表，筛选维度不多，不需要左侧筛选面板。
  - 预期：仍为 `list`。
  - 实际模板：`b-system-advanced-quality-list.html`，实质为 list 变体。
  - 审计：PASS（exit=0）。

- **S6 生产计划列表（含越界筛选结构）**
  - 任务描述：生产计划列表，部分需求希望“更灵活筛选”，但对左侧面板是否必要模糊。
  - 预期：理想路径是先 stop&ask 判定是否应升到 advanced_list。
  - 实际模板：`b-system-production-plan.html`，局部呈现类似高级筛选结构。
  - 审计：FAIL（exit=2），`b_system_list_left_filter_panel_forbidden`。

- **S7 带左侧筛选的列表（反例）**
  - 任务描述：需求直接要求左侧筛选栏，但未澄清是否长期并列展示大量条件。
  - 实际模板：`b-system-list-with-left-filter-panel.html`。
  - 审计：FAIL（exit=2），`b_system_list_left_filter_panel_forbidden`。

- **S8 SaaS/Sidebar/Showcase 类**
  - 任务描述：SaaS 后台、sidebar 结构演示、组件 showcase，用于补充视图与壳示例。
  - 实际模板：`b-system-saas.html` / `b-system-sidebar.html` / `b-system-showcase.html`，不进入主线 routing。

### 2.3 advanced_list 样本（S9–S10）

- **S9 高级质检列表（正例 advanced_list）**
  - 任务描述：质检工单高级列表，需左侧长期多维筛选 + 右侧大表格。
  - 预期：scene=`b_system`，task=`b_system_advanced_list`，type=`advanced_list`，level≈`level_2`。
  - 实际模板：`b-system-advanced-list-with-left-filter-panel.html`。
  - 审计：PASS（exit=0）。

- **S10 advanced_list 壳缺失（反例）**
  - 任务描述：任务被标为 advanced_list，但页面仍是普通列表，没有 filter-panel/advanced-data-table 壳。
  - 实际模板：`b-system-advanced-list-without-advanced-shell.html`。
  - 审计：FAIL（exit=2），`b_system_advanced_list_shell_missing`。

### 2.4 detail 样本（S11–S12）

- **S11 工单详情（正例 detail）**
  - 任务描述：单工单详情页，展示基本信息、状态时间线、质检记录与关联工序。
  - 预期：scene=`b_system`，task=`b_system_detail`，type=`detail`。
  - 实际模板：`b-system-detail-order.html`。
  - 审计：PASS（exit=0）。

- **S12 带 dashboard 气质的详情变体**
  - 任务描述：在详情顶部堆叠大量 KPI 与趋势图，整体气质更像 dashboard。
  - 实际模板：`b-system-detail-with-dashboard-kpi.html`（对照用）。
  - 审计：预期 FAIL（detail 类型混入 dashboard 壳）。

> **b_system 小结**：在 14 条样本中，list/advanced_list/detail/dashboard 已经各有代表壳；普通列表未回退到 `b-system-complete`，advanced_list 与 detail 在壳结构与主视图重心上与 dashboard 拉开差距。越界样本（list+左侧筛选、advanced_list 无壳、detail 混入 KPI 网格）均被 Guard 拦截，说明主线在更大样本下保持了预期的稳定性和分化能力。

---

## 3. ue5_overlay 样本概览（10 条）

> 代表性 examples：
> - `ue5_overlay_data_viz.html`
> - `ue5_overlay_data_viz_no_hud.html`
> - `ue5_overlay_minimal_no_hud.html`
> - `ue5_overlay_quality_tracking.html`
> - `ue5_overlay_quality_tracking_mode2_with_dock.html`
> - `ue5_overlay_dashboard.html`
> - `ue5_overlay_dashboard_mode3_too_light.html`
> - `digital_twin_overlay_dashboard.html`
> - `ue5_overlay_sidepanel_dock_layout.html`
> - `ue5_overlay_engine_test.html` / `ue5_overlay_mock_bridge.html`

### 3.1 Mode 1 / minimal（U1–U3）

- **U1 设备运行监控（Mode 1 正例）**
  - 预期：scene=`ue5_overlay`，task=`ue5_overlay_mode_1_single_hud`，layout_mode/target_mode=`1`。
  - 模板：`ue5_overlay_data_viz.html`。
  - 审计：PASS（exit=0）。

- **U2 Mode 1 无 HUD（反例）**
  - 预期：若仍标记 Mode 1，应 FAIL 并建议改用 minimal。
  - 模板：`ue5_overlay_data_viz_no_hud.html`。
  - 审计：FAIL（exit=2），`ue5_mode1_hud_missing`。

- **U3 极简 world-marker 视图（minimal 正例）**
  - 预期：scene=`ue5_overlay`，task=`ue5_overlay_minimal_no_hud`，layout_mode/target_mode=`"minimal"`。
  - 模板：`ue5_overlay_minimal_no_hud.html`。
  - 审计：PASS（exit=0）。

### 3.2 Mode 2（U4–U5）

- **U4 质量追踪 Overlay（Mode 2 正例）**
  - 模板：`ue5_overlay_quality_tracking.html`（HUD + 右侧 detail-panel）。
  - 审计：PASS（exit=0）。

- **U5 Mode 2 + Dock（反例）**
  - 模板：`ue5_overlay_quality_tracking_mode2_with_dock.html`。
  - 审计：FAIL（exit=2），`ue5_mode2_dock_or_double_panel_forbidden`。

### 3.3 Mode 3 / cockpit（U6–U8）

- **U6 告警中心态势感知（Mode 3 正例）**
  - 模板：`ue5_overlay_dashboard.html`（HUD + alert-center）。
  - 审计：PASS（exit=0）。

- **U7 Mode 3 壳过轻（反例）**
  - 模板：`ue5_overlay_dashboard_mode3_too_light.html`。
  - 审计：FAIL（exit=2），`ue5_mode3_shell_invalid`（缺失 alert-center 壳）。

- **U8 数字孪生驾驶舱（cockpit/Mode 5 相关）**
  - 模板：`digital_twin_overlay_dashboard.html`（限制使用场景）。
  - 审计：PASS（exit=0）。

### 3.4 Mode 5 / 引擎相关（U9–U10）

- **U9 sidepanel dock layout**
  - 模板：`ue5_overlay_sidepanel_dock_layout.html`（示范性 Mode 5 壳）。

- **U10 engine test / mock bridge**
  - 模板：`ue5_overlay_engine_test.html`、`ue5_overlay_mock_bridge.html`（仅用于引擎/桥接测试，不进入主线 routing）。

> **ue5_overlay 小结**：在 10 条样本中，Mode 1 / minimal / Mode 2 / Mode 3 各自拥有代表壳，反例（Mode 1 无 HUD、Mode 2 + Dock、Mode 3 壳过轻）全部被 Guard 拦截；cockpit/Mode 5 相关模板被限制在 limited/测试范围内，没有静默吞并普通 Mode 任务。

---

## 4. 压测阶段结论

- **更大样本下的稳定性**：
  - 24 条样本中，所有 PASS/FAIL 与错误类型均符合当前 Type/Mode/Guard 设计；未出现“规则层预期与审计输出严重不符”的情况。
  - `skill-audit.js` 在 list/advanced_list/detail/dashboard、Mode 1/minimal/Mode 2/Mode 3 相关的关键场景上表现稳定，未出现异常退出或资源问题。

- **更大样本下的灵活性与模板收敛**：
  - `b_system`：list / advanced_list / detail / dashboard 四类任务在样本中分别落在不同模板壳上，普通列表不再统一回到 `b-system-complete`，advanced_list 与 detail 与 dashboard 在结构和视觉重心上区分明显。
  - `ue5_overlay`：Mode 1 / minimal / Mode 2 / Mode 3 在 HUD、world-marker、alert-center、detail-panel、Dock 的组合上各不相同，反例则通过 Guard 提示升级/降级或切换路径。
  - 剩余的模板收敛主要集中在：
    - dashboard 仍以 `b-system-complete` 族为 canonical；
    - cockpit/Mode 5 相关场景集中在 `digital_twin_overlay_dashboard` 与 `ue5_overlay_sidepanel_dock_layout`，被 limited 策略保护，不回流到普通 Mode。

- **脆弱边界与后续优化点**：
  - `b_system`：
    - dashboard vs list：当需求同时提到“KPI 总览 + 任务清单”时，仍需要借助 stop&ask 澄清“首屏主视图”和“第一操作行为”；否则容易把本应是 list 的任务做成 dashboard，或反之。
    - list vs advanced_list：是否真的需要“左侧常驻筛选面板 + 多维条件并列展示”仍是关键判断点，当前 Guard 能拦截越界，但上游 ask 仍有优化空间。
    - detail vs dashboard/workspace：在需求中习惯性“给详情页加几块 KPI”的倾向依旧存在，需要通过问法与 Guard 共同防止详情页被 dashboard 气质吞没。
  - `ue5_overlay`：
    - minimal vs Mode 1：HUD 是否必要是关键决策点，当前模式依赖此判断，后续可以继续压 real tasks 看 minimal 是否被充分使用。
    - Mode 2 vs Mode 3 vs cockpit/Mode 5：当告警、双侧面板、底 Dock 同时出现时，Mode 边界容易模糊，需要更精炼的 stop&ask 将其拉开。

> 总体判断：在 20+ 样本的压测下，当前主线在生成层面仍保持了“稳定 + 结构分化”的特征；b_system 与 ue5_overlay 在关键边界上的脆弱性主要体现在表达模糊的真实需求上，而不是模板或 Guard 本身失控。