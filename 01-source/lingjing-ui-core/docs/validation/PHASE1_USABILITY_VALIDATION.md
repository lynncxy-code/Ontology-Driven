# Phase 1 真实任务可用度验证

> 验证日期：2026-04-05  
> 验证范围：仅覆盖 `b_system` 与 `ue5_overlay` 的 Phase 1 主线；不扩新 `scene` / 新 `mode` / 新治理面。  
> 验证定位：本轮不以“页面是否好看”为核心，而以“真实任务是否能命中正确结构路径”作为判断标准。

---

## 1. 目的

本轮验证的目标不是继续扩边界，而是确认当前 Phase 1 主线是否已经具备以下能力：

1. **稳定性**  
   自然语言任务能否稳定命中正确的 `scene / type / mode / level`。
2. **灵活性**  
   同一 `scene` 内不同任务是否能真正分化为不同结构，而不是无脑回到同一套页面。
3. **边界有效性**  
   `list / advanced_list / detail` 与 `mode1 / minimal / mode2 / mode3` 是否已能被真实任务描述拉开。

---

## 2. 验证方法

### 2.1 方法说明

- 采用 9 条贴近真实需求的自然语言任务描述作为验证集。
- 对每条任务同时记录：
  - 预期 `scene / task_id / target_type / target_mode`
  - 预期 `preferred_level`
  - 预期模板/壳方向
  - 当前技能包下的实际命中结果
  - 是否存在歧义、是否容易收敛到单一模板
- 本轮**不调用外部 AI 生成整页 HTML**；
  实际命中结果基于当前仓库已经固化的：
  - `TRUTH_SOURCES.md`
  - `scene_coverage_matrix.yml`
  - `data/task_router.json`
  - `docs/system-template-map.md`
  - `docs/ue5-template-map.md`
  - `docs/EXTENSION_GUARD.md`
  - `docs/PHASE1_REGRESSION_BASELINES.md`
  - `docs/PHASE1_VALIDATION_REPORT.md`

### 2.2 判定口径

- **稳定命中**：任务描述可以较自然地落到唯一主路径，且与回归基线一致。
- **灵活分化**：不同任务不仅 `task_id / mode` 不同，推荐壳结构也明显不同。
- **单模板收敛**：虽然类型判定正确，但实际 primary template 长期收敛到同一文件，说明灵活性更多靠壳与 Guard，而不是模板层本身。
- **需 stop & ask**：当任务同时命中多个高相似路径，且现有规则已明确要求人工确认时，视为“边界已被识别，但仍需人工拍板”。

---

## 3. 任务验证表

| 任务ID | 任务描述 | 预期 scene/type/mode | 实际命中 | 是否一致 | 是否存在单模板收敛 | 备注 |
|------|----------|----------------------|----------|----------|--------------------|------|
| `BS-01` | 做一个生产任务列表页，页面主区是数据表格，顶部提供状态、日期、责任人筛选，不要左侧常驻筛选侧栏。 | `scene=b_system`；`task_id=b_system_list`；`type=list`；`mode=N/A`；`preferred_level=level_1`；模板/壳方向：`b-system-complete.html` + `content-card` + 顶部 `search-bar` + `data-table-container`。 | 命中 `b_system_list`；`type=list`；`preferred_level=level_1`；仍会优先参考 `b-system-complete.html`，但结构上会保持“顶部筛选条 + 表格”，不会升为左侧筛选。 | 是 | 中 | 任务文本显式排除了左侧常驻筛选侧栏，当前边界稳定。 |
| `BS-02` | 做一个设备台账高级列表页，筛选维度较多，需要常驻的侧栏筛选区与右侧表格并列展示。 | `scene=b_system`；`task_id=b_system_advanced_list`；`type=advanced_list`；`mode=N/A`；`preferred_level=level_2`；模板/壳方向：`advanced-data-table` + `advanced-data-table-side/filter-panel` + `advanced-data-table-main`。 | 命中 `b_system_advanced_list`；`type=advanced_list`；`preferred_level=level_2`；模板层仍优先 `b-system-complete.html` / `b-system-production-plan.html`，但壳层会切到 `advanced-data-table`。 | 是 | 中高 | 当前可以稳定命中 advanced_list，不会退回普通 list；但模板层仍明显依赖 `b-system-complete.html`。 |
| `BS-03` | 做一个工单详情页，展示工单基本信息、状态时间线、关联记录表格，不要做成运营总览工作台。 | `scene=b_system`；`task_id=b_system_detail`；`type=detail`；`mode=N/A`；`preferred_level=level_1`；模板/壳方向：`grid-cols-2` + 多个 `content-card` + `status-timeline` + 关联表格。 | 命中 `b_system_detail`；`type=detail`；`preferred_level=level_1`；主模板仍倾向 `b-system-complete.html`，但 Guard 会排斥 `stats-grid/charts-grid` 仪表盘壳。 | 是 | 中高 | “不要做成运营总览工作台”能有效把它从 dashboard 拉回 detail。 |
| `BS-04` | 做一个生产管理页面，需要看任务清单、状态统计、少量筛选和异常提醒。 | 故意歧义；预期 `dashboard` 与 `list` 都可能被激活，应记录当前倾向，并判断是否需要 `stop&ask`。 | 当前更倾向 `b_system_dashboard_overview`；`type=dashboard`；`preferred_level=level_1`；会优先参考 `b-system-complete.html` 的总览壳，但**按 Guard 应提示人工确认**。 | 是（按预期暴露歧义） | 高 | “任务清单 + 状态统计 + 异常提醒”同时命中多类型特征；这类任务不应静默决策。 |
| `UE-01` | 做一个 UE5 运行监控大屏，需要顶部 HUD 和核心数据可视化，不要侧面板和告警中心。 | `scene=ue5_overlay`；`task_id=ue5_overlay_mode_1_single_hud`；`type=overlay_dashboard`；`mode=1`；`preferred_level=level_1`；模板/壳方向：`ue5_overlay_data_viz.html` + `topbar-hud`。 | 命中 `ue5_overlay_mode_1_single_hud`；`mode=1`；`preferred_level=level_1`；优先参考 `ue5_overlay_data_viz.html`。 | 是 | 低 | “不要侧面板和告警中心”使其与 Mode 2/3 明确分离。 |
| `UE-02` | 做一个极简 UE5 overlay，只保留 world-marker 和基础安全区骨架，不需要 HUD。 | `scene=ue5_overlay`；`type=overlay_dashboard`；`mode=N/A（minimal）`；预期为轻量路径；模板/壳方向：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area` + `world-marker`。 | 会被理解为合法的 minimal overlay 路径；`scene=ue5_overlay`、`type=overlay_dashboard`、`mode=N/A`；可参考 `ue5_overlay_minimal_no_hud.html` 作为回归锚点，但**当前 `task_router` 没有显式 minimal 任务项**。 | 部分一致 | 低 | minimal 边界已合法且稳定，但任务级路由记录仍不够显式。 |
| `UE-03` | 做一个 UE5 质量追踪界面，需要顶部 HUD、右侧详情面板、world-marker 联动，不需要告警中心。 | `scene=ue5_overlay`；`task_id=ue5_overlay_mode_2_hud_sidepanel`；`type=overlay_dashboard`；`mode=2`；`preferred_level=level_1`；模板/壳方向：`ue5_overlay_quality_tracking.html` + `topbar-hud--with-sidepanel` + `detail-panel`。 | 命中 `ue5_overlay_mode_2_hud_sidepanel`；`mode=2`；`preferred_level=level_1`；优先参考 `ue5_overlay_quality_tracking.html`。 | 是 | 低 | “不需要告警中心”能有效阻止其误升为 Mode 3。 |
| `UE-04` | 做一个 UE5 告警监控总览，需要 HUD、告警中心、world-marker，突出告警处置。 | `scene=ue5_overlay`；`task_id=ue5_overlay_mode_3_hud_alert_center`；`type=overlay_dashboard`；`mode=3`；`preferred_level=level_1`；模板/壳方向：`ue5_overlay_dashboard.html` + `alert-center`。 | 命中 `ue5_overlay_mode_3_hud_alert_center`；`mode=3`；`preferred_level=level_1`；优先参考 `ue5_overlay_dashboard.html`。 | 是 | 低 | “告警中心 / 告警处置”是当前 Mode 3 最稳定的语义锚点。 |
| `UE-05` | 做一个数字孪生运行监控界面，既要异常信息，也要设备状态和空间标注。 | 故意歧义；预期记录当前更偏 `Mode 2` 还是 `Mode 3`，并评估是否需要 `stop&ask`。 | 当前更倾向 `ue5_overlay_mode_2_hud_sidepanel`；`mode=2`；`preferred_level=level_1`；优先参考 `ue5_overlay_quality_tracking.html`，因为“异常信息”本身不足以升级为完整 `alert-center`。 | 是（按预期观察边界） | 低 | 当前规则对 `Mode 2 vs Mode 3` 的倾向已较清楚；若业务明确要结构化告警列表，再升级为 Mode 3。 |

---

## 4. 总结结论

### 4.1 稳定性判断

**整体结论：比上一阶段更稳定。**

- `b_system`
  - `list / advanced_list / detail` 的边界现在已经可以通过自然语言任务较稳定拉开；
  - 尤其是：
    - “顶部筛选，不要左侧侧栏”会稳定留在 `list`；
    - “常驻侧栏筛选 + 右侧表格”会稳定进入 `advanced_list`；
    - “单实体详情 + 时间线 + 关联记录，不要运营总览”会稳定进入 `detail`。
- `ue5_overlay`
  - `mode1 / mode2 / mode3 / minimal` 的边界比此前清楚；
  - `topbar-hud`、`detail-panel`、`alert-center`、`world-marker` 已形成较明确的模式锚点；
  - `minimal overlay` 也已经被回归与 Guard 明确承认是“无 HUD 也合法”的路径。

### 4.2 灵活性判断

**结论：已具备初步灵活分化能力，但分化强度在两个主线场景中不均衡。**

- `ue5_overlay`：灵活性较好。  
  Mode 1 / 2 / 3 的 primary template 与壳结构都明显不同，分化是真实存在的。
- `b_system`：结构分化已建立，但模板层灵活性仍偏弱。  
  `list / advanced_list / detail / dashboard` 的**类型判定与 Guard** 已能拉开，
  但 `task_router` 的 primary template 仍明显收敛到 `b-system-complete.html`，说明当前 `b_system` 的分化更多依赖：
  - `target_type`
  - `required_shell`
  - Guard / 审计
  而不是由不同 primary template 自然承载。

### 4.3 边界有效性判断

#### `b_system`

- `list vs advanced_list`：**可靠**  
  当前明确要求“左侧独立/常驻筛选面板”时，才会进入 `advanced_list`；仅有“筛选条件多”不会自动升级。
- `detail vs dashboard`：**基本可靠**  
  当任务强调单实体详情且排除运营总览时，能够稳定落到 `detail`；但一旦需求同时出现清单、统计、告警，仍需 `stop&ask`。

#### `ue5_overlay`

- `mode1 vs minimal`：**基本可靠**  
  当前已经能识别“无 HUD 的合法 minimal overlay”；
  但由于 minimal 尚未成为显式任务路由项，透明度略弱于 Mode 1/2/3。
- `mode2 vs mode3`：**基本可靠**  
  当前“右侧详情 + world-marker”会更偏 Mode 2；
  只有明确提出“告警中心 / 告警列表 / 告警处置主线”时，才会稳定进入 Mode 3。

### 4.4 是否存在明显单模板收敛

**存在，但主要集中在 `b_system`。**

- 不存在“全仓任务都无脑回一张模板”的问题；
- 但 `b_system` 的 `dashboard / list / advanced_list / detail` 目前 primary template 大多仍指向 `b-system-complete.html`；
- 因此，当前可以说：
  - **类型边界比之前清楚了**；
  - **结构分化比之前真实了**；
  - 但 **模板层仍有明显的单模板收敛残留**。

---

## 5. 后续建议（仅列最小修补项）

1. **为 minimal overlay 增加显式任务路由记录**  
   在后续最小修补中，可考虑补充一个显式的 minimal overlay 路由项（或等价任务说明），把 `preferred_level`、示例锚点与适用语义写清楚，减少“合法但未显式登记”的灰区。

2. **降低 `b_system` 的 primary template 收敛**  
   不需要新增大规模 examples；可直接考虑把已有正例样例接入路由：
   - `b_system_list` → `b-system-task-list-top-filters.html`
   - `b_system_advanced_list` → `b-system-advanced-list-with-left-filter-panel.html`
   - `b_system_detail` → `b-system-detail-order.html`
   这样能让 `b_system` 的“类型分化”在模板层也更可见。

3. **补一条更窄的模糊任务 stop&ask 口径**  
   对于同时出现“任务清单 + 状态统计 + 异常提醒”的系统任务，可在后续最小修补中增加更直接的澄清提示，减少 `dashboard` 与 `list/workspace` 之间的静默漂移。

---

## 6. 最终结论

当前 Phase 1 主线已经**初步证明“更稳定”**：

- `list / advanced_list / detail` 可以被真实任务稳定拉开；
- `mode1 / minimal / mode2 / mode3` 也已具备较清楚的边界；
- `ue5_overlay` 已展示出较好的模板与壳分化能力；
- `b_system` 虽然仍存在明显的 `b-system-complete.html` 收敛，但其类型与结构边界已经不再是“单模板一张脸”。

**一句话结论：当前 Phase 1 主线已初步证明“稳定且开始具备灵活性”，但 `b_system` 模板层收敛与 minimal overlay 显式路由缺位，仍是下一轮最值得做的最小修补点。**
