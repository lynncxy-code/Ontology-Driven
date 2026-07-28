# Phase 1 正式验证报告

> 验证日期：2026-04-05  
> 验证范围：`b_system` 与 `ue5_overlay` 的 Phase 1 主线，不扩新 scene / 新 mode / 新治理面。

---

## 1. 验证目的

基于当前已固化的正式回归入口 `npm run audit:phase1-regression`，对 Phase 1 主线的 13 个回归样例进行一次完整正式验证，确认：

- 回归 runner 可完整执行全部样例，不会因反例非 0 退出码中断；
- `b_system_list` / `b_system_advanced_list` / `b_system_detail` 的正反例边界稳定；
- `ue5_overlay` 的 Mode 1 / Mode 2 / Mode 3 / minimal overlay 的正反例边界稳定；
- 当前仓库可作为 Phase 1 阶段成果进入正式验收。

---

## 2. 正式验证入口与实际执行命令

- **仓库正式入口**：`npm run audit:phase1-regression`
- **本次实际执行命令**：
  - `node c:/Users/houyn/Desktop/UI规范skill迭代/lingjing-ui-core/scripts/run-phase1-regression.js`
- **等价关系说明**：
  - `package.json` 中的 `audit:phase1-regression` 已指向 `scripts/run-phase1-regression.js`；
  - 因此，本次实际执行与仓库正式入口等价。

---

## 3. 验证样例与实际结果

| ID | 样例文件 | 预期 | 实际 | exit code | 是否一致 | 备注 |
|----|----------|------|------|-----------|----------|------|
| `b_system_list:top_filters` | `examples/b-system/b-system-task-list-top-filters.html` | PASS | PASS | `0` | 是 | 标准 list 正例 |
| `b_system_list:left_filter_panel` | `examples/b-system/b-system-list-with-left-filter-panel.html` | FAIL | FAIL | `2` | 是 | 命中 `b_system_list_left_filter_panel_forbidden` |
| `b_system_advanced_list:with_shell` | `examples/b-system/b-system-advanced-list-with-left-filter-panel.html` | PASS | PASS | `0` | 是 | 标准 advanced_list 正例 |
| `b_system_advanced_list:without_shell` | `examples/b-system/b-system-advanced-list-without-advanced-shell.html` | FAIL | FAIL | `2` | 是 | 命中 `b_system_advanced_list_shell_missing` |
| `b_system_detail:order` | `examples/b-system/b-system-detail-order.html` | PASS | PASS | `0` | 是 | 标准 detail 正例 |
| `b_system_detail:with_dashboard_kpi` | `examples/b-system/b-system-detail-with-dashboard-kpi.html` | FAIL | FAIL | `2` | 是 | 命中 `b_system_detail_dashboard_shell_forbidden` |
| `ue5_overlay_mode2:quality_tracking` | `examples/ue5-overlay/ue5_overlay_quality_tracking.html` | PASS | PASS | `0` | 是 | Mode 2 正例 |
| `ue5_overlay_mode2:with_dock` | `examples/ue5-overlay/ue5_overlay_quality_tracking_mode2_with_dock.html` | FAIL | FAIL | `2` | 是 | 命中 `ue5_mode2_dock_or_double_panel_forbidden` |
| `ue5_overlay_mode3:dashboard` | `examples/ue5-overlay/ue5_overlay_dashboard.html` | PASS | PASS | `0` | 是 | Mode 3 正例 |
| `ue5_overlay_mode3:too_light` | `examples/ue5-overlay/ue5_overlay_dashboard_mode3_too_light.html` | FAIL | FAIL | `2` | 是 | 命中 `ue5_mode3_shell_invalid` |
| `ue5_overlay_mode1:data_viz` | `examples/ue5-overlay/ue5_overlay_data_viz.html` | PASS | PASS | `0` | 是 | Mode 1 正例 |
| `ue5_overlay_mode1:data_viz_no_hud` | `examples/ue5-overlay/ue5_overlay_data_viz_no_hud.html` | FAIL | FAIL | `2` | 是 | 命中 `ue5_mode1_hud_missing` |
| `ue5_overlay_minimal:no_hud` | `examples/ue5-overlay/ue5_overlay_minimal_no_hud.html` | PASS | PASS | `0` | 是 | minimal overlay 正例 |

**汇总：**

- 总样例数：`13`
- 预期 PASS：`7`
- 预期 FAIL：`6`
- 与预期一致：`13 / 13`
- runner 整体退出码：`0`

---

## 4. 稳定度结论

结合本次正式验证结果与 `TRUTH_SOURCES.md §6`：

- `b_system`
  - `list`：基本稳定
  - `advanced_list`：基本稳定
  - `detail`：基本稳定
- `ue5_overlay`
  - Mode 1：基本稳定
  - Mode 2：基本稳定
  - Mode 3：基本稳定
  - minimal overlay：基本稳定

当前版本尚未将上述主线组合提升为“已稳定”，但已经具备：

- 真值源与解释层基本对齐；
- 回归入口可一键完整重放；
- 正反例 Guard 可被稳定触发；
- 阶段验收所需的验证闭环已形成。

---

## 5. 阶段验收判断

**结论：可以。**

以当前仓库状态，Phase 1 主线成果已经满足“正式验证通过”的要求，可作为本阶段成果进入验收；后续若进入发版准备，应继续以：

- `docs/PHASE1_REGRESSION_BASELINES.md`
- `docs/PHASE1_VALIDATION_REPORT.md`
- `TRUTH_SOURCES.md §6`

作为回归、验证与稳定度判断的正式依据。
