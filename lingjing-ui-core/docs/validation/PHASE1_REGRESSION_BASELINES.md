# Phase 1 回归基线 — b_system + ue5_overlay

> **目的**：把当前已验证通过的主线边界沉淀为正式回归基线，方便在规则 / 模板调整后，一键重放审计，确认 Guard 行为未被破坏。
>
> **范围**：仅覆盖 Phase 1 深做场景：`b_system` 与 `ue5_overlay`，聚焦：
> - `b_system_list` 正反例
> - `b_system_advanced_list` 正反例
> - `b_system_detail` 正反例
> - `ue5_overlay_mode_1_single_hud` 正反例
> - `ue5_overlay_mode_2_hud_sidepanel` 正反例
> - `ue5_overlay_mode_3_hud_alert_center` 正反例
> - `ue5_overlay` 极简 Overlay 无 HUD 合法样例


---

## 1. 一键运行方式

- **npm script 入口**（位于 `package.json.scripts`）：
  - `"audit:phase1-regression"`: 一次性审计本文件列出的 13 个 HTML 样例。
- **在本地运行**：
  - 进入 `lingjing-ui-core` 目录：
    - `cd lingjing-ui-core`
  - 执行：
    - `npm run audit:phase1-regression`
- **行为说明**：
  - 对每个样例调用：`node scripts/skill-audit.js <file> --scene <scene> [--task <task_id>]`
  - 对“正例”样例，期望 **ERROR = 0**，整体 PASS；
  - 对“反例”样例，期望命中对应 Guard / ERROR 代码，整体 FAIL；
  - 所有样例都已在当前版本下实测通过（见第 9 节运行结果摘要）。


---

## 2. b_system_list 正反例

- **任务/类型**：
  - `scene = b_system`
  - `task_id = b_system_list`
  - `target_type = list`
  - `target_mode = N/A`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/b-system/b-system-task-list-top-filters.html` | `b_system` | `b_system_list` | `list` | `N/A` | **PASS**（ERROR = 0） | 无特定 Guard 命中，`b_system_list_left_filter_panel_forbidden` 未触发；整体审计通过。|
| `examples/b-system/b-system-list-with-left-filter-panel.html` | `b_system` | `b_system_list` | `list` | `N/A` | **ERROR**（FAIL） | `b_system_list_left_filter_panel_forbidden`：检测到左侧类似高级筛选面板结构，在 list 任务下视为误升为 advanced_list。|

> 用途：锁定“普通列表页 + 顶部筛选条”与“误长左侧高级筛选面板”的边界，确保 list Guard 工作正常。

---

## 3. b_system_advanced_list 正反例

- **任务/类型**：
  - `scene = b_system`
  - `task_id = b_system_advanced_list`
  - `target_type = advanced_list`
  - `target_mode = N/A`
- **审计调用建议**：
  - 必须带上 `--task b_system_advanced_list`，以便高级列表 Guard 生效：
    - `node scripts/skill-audit.js <file> --scene b_system --task b_system_advanced_list`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/b-system/b-system-advanced-list-with-left-filter-panel.html` | `b_system` | `b_system_advanced_list` | `advanced_list` | `N/A` | **PASS**（ERROR = 0） | 在 `--task b_system_advanced_list` 前提下，左侧高级筛选面板视为合法壳；`b_system_advanced_list_shell_missing` 未触发。|
| `examples/b-system/b-system-advanced-list-without-advanced-shell.html` | `b_system` | `b_system_advanced_list` | `advanced_list` | `N/A` | **ERROR**（FAIL） | `b_system_advanced_list_shell_missing`：任务 id = advanced_list，但页面未检测到典型高级筛选壳（advanced-data-table + filter-panel / advanced-data-table-side），建议降级为 list 或补齐壳结构。|

> 用途：确保“高级列表必须有壳 / 普通列表不应误升为高级壳”这条边界，在 task 语义生效时被稳定审计。

---

## 4. b_system_detail 正反例（Detail — 单实体详情页）

- **任务/类型**：
  - `scene = b_system`
  - `task_id = b_system_detail`
  - `target_type = detail`
  - `target_mode = N/A`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/b-system/b-system-detail-order.html` | `b_system` | `b_system_detail` | `detail` | `N/A` | **PASS**（ERROR = 0） | 标准单工单详情页：使用 `b-layout-sidebar + b-main + b-header + b-content` 框架壳，核心区域由基本信息卡 + 状态时间线 + 关联记录表格组成；未出现 `stats-grid` / `charts-grid` 等仪表盘壳，`b_system_detail_dashboard_shell_forbidden` 未触发。|
| `examples/b-system/b-system-detail-with-dashboard-kpi.html` | `b_system` | `b_system_detail` | `detail` | `N/A` | **ERROR**（FAIL） | `b_system_detail_dashboard_shell_forbidden`：在详情页顶部检测到 `stats-grid` KPI 网格，属于 Dashboard 壳误混入详情页，建议拆分为 dashboard + detail 或调整任务类型。|

> 用途：锁定“单实体详情页”与“混入仪表盘 KPI 壳的工作台化详情页”之间的边界，防止在 `b_system_detail` 任务下无意识堆叠 Dashboard 结构。

---

## 5. ue5_overlay_mode_2 正反例（Mode 2 — HUD + 单侧详情）

- **任务/模式**：
  - `scene = ue5_overlay`
  - `task_id = ue5_overlay_mode_2_hud_sidepanel`
  - `target_type = overlay_dashboard`
  - `target_mode = 2`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/ue5-overlay/ue5_overlay_quality_tracking.html` | `ue5_overlay` | `ue5_overlay_mode_2_hud_sidepanel` | `overlay_dashboard` | `2` | **PASS**（ERROR = 0） | Mode 2 Guard 全部通过：`ue5_mode2_dock_or_double_panel_forbidden` 未触发；页面为 HUD + 单侧 detail-panel + world-marker，无 Dock / 双侧固定面板。|
| `examples/ue5-overlay/ue5_overlay_quality_tracking_mode2_with_dock.html` | `ue5_overlay` | `ue5_overlay_mode_2_hud_sidepanel` | `overlay_dashboard` | `2` | **ERROR**（FAIL） | `ue5_mode2_dock_or_double_panel_forbidden`（ERROR）：在 Mode 2 场景下检测到 Dock 结构（`ue5-overlay-bottom-dock`），建议改用 Mode 5；同时存在 `project_scoped_classes`（WARN）用于 pj-* 时间轴类。|

> 用途：锁定 Mode 2 与 Mode 5 之间的 Dock 边界，防止普通质量追踪场景被误升级为驾驶舱级 Dock 布局。

---

## 6. ue5_overlay_mode_3 正反例（Mode 3 — HUD + 告警中心）

- **任务/模式**：
  - `scene = ue5_overlay`
  - `task_id = ue5_overlay_mode_3_hud_alert_center`
  - `target_type = overlay_dashboard`
  - `target_mode = 3`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/ue5-overlay/ue5_overlay_dashboard.html` | `ue5_overlay` | `ue5_overlay_mode_3_hud_alert_center` | `overlay_dashboard` | `3` | **PASS**（ERROR = 0） | Mode 3 Guard 通过：检测到完整 `alert-center` 壳，`ue5_mode3_shell_invalid` 未触发；页面为 HUD + 告警中心 + world-marker，无 Dock/双侧固定面板。|
| `examples/ue5-overlay/ue5_overlay_dashboard_mode3_too_light.html` | `ue5_overlay` | `ue5_overlay_mode_3_hud_alert_center` | `overlay_dashboard` | `3` | **ERROR**（FAIL） | `ue5_mode3_shell_invalid`：layout_mode = 3 但未检测到 `alert-center` 告警中心壳，被视为 Mode 3 壳过轻，建议降级为 Mode 2 或补齐告警中心。|

> 用途：锁定 Mode 3 的“告警中心必须存在”边界，防止简单 HUD + 告警计数伪装成告警中心工作台。

---

## 7. ue5_overlay_mode_1 正反例（Mode 1 — 单 HUD 监控大屏）


- **任务/模式**：
  - `scene = ue5_overlay`
  - `task_id = ue5_overlay_mode_1_single_hud`
  - `target_type = overlay_dashboard`
  - `target_mode = 1`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/ue5-overlay/ue5_overlay_data_viz.html` | `ue5_overlay` | `ue5_overlay_mode_1_single_hud` | `overlay_dashboard` | `1` | **PASS**（ERROR = 0） | 单 HUD 模板：包含 `topbar-hud`、安全区骨架与数据可视化面板；未触发 `ue5_mode1_hud_missing`，Mode 1 Guard 通过。|
| `examples/ue5-overlay/ue5_overlay_data_viz_no_hud.html` | `ue5_overlay` | `ue5_overlay_mode_1_single_hud` | `overlay_dashboard` | `1` | **ERROR**（FAIL） | `ue5_mode1_hud_missing`：layout_mode = 1 的页面中未检测到 `topbar-hud`，更接近 minimal overlay，建议改用极简模板或补齐 HUD。|

> 用途：锁定“单 HUD 监控大屏”与“误把极简无 HUD 场景标成 Mode 1”的边界，确保当 layout_mode=1 却没有 HUD 时可以被机器发现并提示改用 minimal overlay。

---

## 8. ue5_overlay 极简 Overlay（minimal_no_hud）合法样例


- **场景属性**：
  - `scene = ue5_overlay`
  - `task_id = ue5_overlay_minimal_no_hud`
  - `target_type = overlay_dashboard`
  - `target_mode = minimal`

| 文件路径 | scene | task_id | target_type | target_mode | 预期结果 | 命中的 Guard / audit 项 |
|----------|-------|---------|-------------|-------------|----------|--------------------------|
| `examples/ue5-overlay/ue5_overlay_minimal_no_hud.html` | `ue5_overlay` | `ue5_overlay_minimal_no_hud` | `overlay_dashboard` | `minimal` | **PASS**（ERROR = 0） | 仅依赖 `shell_consistency.ue5_overlay`：骨架 `ue5-overlay-root + ue5-overlay-viewport + ue5-overlay-safe-area` 完整，未触发任何 Mode 1 / Mode 2 / Mode 3 / Dock 相关 Guard；证明 HUD 已从“强制框架”降级为“按需模块”，且 minimal overlay 场景在无 HUD 情况下也是合法的。|

> 用途：作为 HUD 可选性的正向锚点，验证在仅有骨架 + world-marker 的极简 Overlay 场景下，审计仍然允许通过。

---

## 9. 实际运行结果摘要（本轮验证）


本轮在仓库根目录下通过以下命令直接调用审计脚本（与 npm script 内部行为等价），覆盖本文件列出的全部 13 个样例：

- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-task-list-top-filters.html --scene b_system`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-list-with-left-filter-panel.html --scene b_system`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-advanced-list-with-left-filter-panel.html --scene b_system --task b_system_advanced_list`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-advanced-list-without-advanced-shell.html --scene b_system --task b_system_advanced_list`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-detail-order.html --scene b_system --task b_system_detail`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/b-system/b-system-detail-with-dashboard-kpi.html --scene b_system --task b_system_detail`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_quality_tracking.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_quality_tracking_mode2_with_dock.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_dashboard.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_dashboard_mode3_too_light.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_data_viz.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_data_viz_no_hud.html --scene ue5_overlay`
- `node lingjing-ui-core/scripts/skill-audit.js lingjing-ui-core/examples/ue5-overlay/ue5_overlay_minimal_no_hud.html --scene ue5_overlay`

**汇总结果（与上表预期完全一致）：**

- **b_system_list**：
  - `b-system-task-list-top-filters.html` → `ERROR: 0, exit=0`（PASS）
  - `b-system-list-with-left-filter-panel.html` → 命中 `b_system_list_left_filter_panel_forbidden`（ERROR 1, exit=2）
- **b_system_advanced_list**（带 `--task b_system_advanced_list`）：
  - `b-system-advanced-list-with-left-filter-panel.html` → `ERROR: 0, exit=0`（PASS）
  - `b-system-advanced-list-without-advanced-shell.html` → 命中 `b_system_advanced_list_shell_missing`（ERROR 1, exit=2）
- **b_system_detail**（带 `--task b_system_detail`）：
  - `b-system-detail-order.html` → `ERROR: 0, exit=0`（PASS）
  - `b-system-detail-with-dashboard-kpi.html` → 命中 `b_system_detail_dashboard_shell_forbidden`（ERROR 1, exit=2）
- **ue5_overlay_mode_2_hud_sidepanel**：
  - `ue5_overlay_quality_tracking.html` → `ERROR: 0, exit=0`（PASS）
  - `ue5_overlay_quality_tracking_mode2_with_dock.html` → 命中 `ue5_mode2_dock_or_double_panel_forbidden`（并伴随 `project_scoped_classes` WARN，exit=2）
- **ue5_overlay_mode_3_hud_alert_center**：
  - `ue5_overlay_dashboard.html` → `ERROR: 0, exit=0`（PASS）
  - `ue5_overlay_dashboard_mode3_too_light.html` → 命中 `ue5_mode3_shell_invalid`（ERROR 1, exit=2）
- **ue5_overlay_mode_1_single_hud**：
  - `ue5_overlay_data_viz.html` → `ERROR: 0, exit=0`（PASS）
  - `ue5_overlay_data_viz_no_hud.html` → 命中 `ue5_mode1_hud_missing`（ERROR 1, exit=2）
- **ue5_overlay 极简 Overlay**：
  - `ue5_overlay_minimal_no_hud.html` → `ERROR: 0, exit=0`（PASS）

> 因此，可以将本文件列出的 13 个样例视为 Phase 1 的**正式真值回归基线**：只要未来规则/模板变更后 `npm run audit:phase1-regression` 的行为仍与上述预期一致，就可以认为 b_system 的 list / advanced_list / detail 以及 UE5 Mode 1 / Mode 2 / Mode 3 / minimal overlay 的关键边界未被破坏。