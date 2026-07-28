# 🌌 ue5-template-map — UE5 Overlay 场景模板映射

> **场景**：`ue5_overlay`（UE5 Web Overlay / 数字孪生叠加层）  
> **目的**：将 `layout_mode`（`minimal` / 1 / 2 / 3 / 4 / 5）与模板、Level、Shell/Layer、常见误用显式映射，
> 让 AI 与人类在 UE5 场景下可以稳定完成 `Scene → Mode → Template → Level → Guard`。

---

## 0. 总览与真值源

- 样式入口：`components/dist/lingjing-core-ue5-overlay.css`
- 主要模板真值源：
  - `scene_coverage_matrix.yml.scene_coverage.ue5_overlay`
  - `skill_version.json.examples.canonical.ue5_overlay` / `.candidate.ue5_overlay`
- 参考模板：
  - canonical：
    - 模式 1：`examples/ue5-overlay/ue5_overlay_data_viz.html`
    - 模式 2：`examples/ue5-overlay/ue5_overlay_quality_tracking.html`
    - 模式 3：`examples/ue5-overlay/ue5_overlay_dashboard.html`
    - Engine 测试：`examples/ue5-overlay/ue5_overlay_engine_test.html`（仅用于 UE5 引擎桥接 / 性能与世界标记测试，**Phase 1 不作为任务路由主链模板**）
  - candidate：
    - minimal：`examples/ue5-overlay/ue5_overlay_minimal_no_hud.html`
    - 模式 5：`examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`
    - 数字孪生混合：`examples/ue5-overlay/digital_twin_overlay_dashboard.html`
- 参考 Playbook：
  - `docs/operations/ue5-overlay-layout-playbook.md`

> ⚠ **黑名单提醒**：
> - `examples/ue5-overlay/ue5_overlay_mock_bridge.html`  
> 在 `scene_coverage_matrix.yml` 中标记为 `grade: anti_pattern / use_scope: forbidden`，仅用于反面案例说明，**禁止作为 canonical 或默认路由**。

---

## 1. Mode 1 — 单 HUD（Single HUD）

- **mode_id**：1
- **mode_name**：单 HUD 监控大屏
- **applicable_when**：
  - 顶部需要展示少量全局 KPI 和状态；
  - 下方主要是三维场景本身，辅以少量 world-marker；
  - 无侧边详情面板，交互较轻。
- **primary_example**：
  - `examples/ue5-overlay/ue5_overlay_data_viz.html`
- **fallback_examples**：
  - 暂无（可按 Playbook 骨架结合业务定制）。
- **recommended_level**：
  - 默认：`level_1`（模板直用 + 轻调文案/指标）。
- **required_shell**：
  - 根骨架：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`
  - HUD：`topbar-hud`（无 `--with-sidepanel` 修饰）
- **required_layers**（参考 Playbook）：
  - `ue5-overlay-layer--ambient` — 环境装饰
  - `ue5-overlay-layer--marker` — world-marker 图层
  - `ue5-overlay-layer--hud` — HUD 顶部信息
- **common_misuse**：
  - 将 Mode 2/3 的复杂面板硬塞进 Mode 1 布局，导致 HUD 与面板挤占视野。
  - 不使用 `ue5-overlay-safe-area`，而在视口中随意绝对定位内容。
- **human_confirmation_needed**：
  - 需确认：
    - 哪些 KPI 必须出现在 HUD（通常不超过 3–5 个）；
    - world-marker 的数量与重要程度（避免信息过载）。

---

## 1.5 补充：minimal overlay — 极简无 HUD

- **mode_id**：`minimal`
- **mode_name**：极简 Overlay（无 HUD）
- **applicable_when**：
  - 只需要 `world-marker` 与基础安全区骨架；
  - 不需要 HUD、告警中心或持续展开的详情面板；
  - 需求重点是三维场景上的轻量状态标注，而不是总览看板。
- **primary_example**：
  - `examples/ue5-overlay/ue5_overlay_minimal_no_hud.html`
- **fallback_examples**：
  - 暂无；若开始需要顶部 KPI / HUD，应回到 Mode 1。
- **recommended_level**：
  - 默认：`level_1`
- **required_shell**：
  - 根骨架：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`
  - 标注层：`ue5-overlay-layer--marker` + `world-marker`（推荐至少 1 个）
- **required_layers**：
  - `ue5-overlay-layer--marker`
- **common_misuse**：
  - 明明要求“无 HUD”，却沿用 Mode 1 的 `topbar-hud`。
  - 在极简路径中继续塞入 `alert-center` / `detail-panel`，导致实际更接近 Mode 2/3。
- **human_confirmation_needed**：
  - 需确认：
    - `world-marker` 是否就是主要交互入口？
    - 是否后续仍需要补充 HUD 或固定详情面板？

---

## 2. Mode 2 — HUD + 侧边详情面板（HUD + Side Detail）


- **mode_id**：2
- **mode_name**：HUD + 右侧详情面板
- **applicable_when**：
  - 需要在查看三维场景的同时，持续关注某个对象的详情；
  - 右侧面板用于展示选中对象的属性、历史、操作入口。
- **primary_example**：
  - `examples/ue5-overlay/ue5_overlay_quality_tracking.html`
- **fallback_examples**：
  - 可参考 Mode 1 + Playbook 中 Mode 2 骨架组合。
- **recommended_level**：
  - 默认：`level_1`；
  - 当右侧面板结构极复杂（多个子面板/子标签）时，可视为 `level_2`。
- **required_shell**：
  - 根骨架：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`
  - HUD：`topbar-hud topbar-hud--with-sidepanel`
  - 详情面板：`detail-panel`
- **required_layers**：
  - HUD：`ue5-overlay-layer--hud`
  - Marker：`ue5-overlay-layer--marker`
  - Detail：`ue5-overlay-layer--detail`
- **模块配置偏好（HUD / alert-center / detail-panel / world-marker）**：
  - HUD：默认推荐使用 `topbar-hud--with-sidepanel` 变体，为右侧 detail-panel 让出空间；仅当 PRD 明确说明“无需顶部 HUD，仅右侧详情”时才考虑弱化 HUD。
  - detail-panel：默认存在且为单侧；若 PRD 需要左右双侧固定面板，应考虑 Mode 5，而不是在 Mode 2 中堆叠多个 pinned 面板。
  - world-marker：推荐，用于与右侧详情面板联动高亮当前对象；完全没有 world-marker 时，场景更接近普通 B 端大屏。
  - alert-center：可在 HUD 或 detail-panel 中以少量告警卡片呈现；若需要完整告警中心列表，应优先考虑 Mode 3。
- **common_misuse**：
  - 未使用 `topbar-hud--with-sidepanel` 修饰，导致 HUD 与面板布局冲突。
  - 将多个完全不同功能塞入一个 detail-panel，缺乏分区与子卡片结构。
- **human_confirmation_needed**：
  - 需确认：
    - 右侧详情面板需要承载哪些信息块？
    - 是否允许在操作过程中更换当前 focus 的对象？

---

## 3. Mode 3 — HUD + 告警中心（HUD + Alert Center）

- **mode_id**：3
- **mode_name**：HUD + 告警中心总览
- **applicable_when**：
  - 强调实时告警列表与告警处理流程；
  - 通常左侧或下方为告警列表，右侧/中央为三维视图与 world-marker。
- **primary_example**：
  - `examples/ue5-overlay/ue5_overlay_dashboard.html`
- **fallback_examples**：
  - 可结合 Mode 1 HUD + `alert-center` 卡片结构自行编排。
- **recommended_level**：
  - 默认：`level_1`；
  - 当告警列表与多种视图联动、逻辑复杂时：`level_2`。
- **required_shell**：
  - 根骨架：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`
  - HUD：`topbar-hud`
  - 告警中心：`alert-center`
- **required_layers**：
  - HUD：`ue5-overlay-layer--hud`
  - Marker：`ue5-overlay-layer--marker`
  - Detail / Alert：`ue5-overlay-layer--detail`
- **模块配置偏好（HUD / alert-center / detail-panel / world-marker）**：
  - alert-center：Mode 3 的核心模块，理论上必须出现；缺失时将触发壳过轻 Guard 并建议降级为 Mode 2（参见 scene_coverage_matrix.yml 与 EXTENSION_GUARD）。
  - HUD：默认推荐保留，用于承载全局态势与告警摘要；在极端“告警工作台”场景下可以弱化 HUD 文案，但不建议完全移除。
  - world-marker：推荐，用于将高优先级告警映射到三维场景；如 PRD 将告警完全限制在列表中，可在 world-marker 上仅保留关键节点。
  - detail-panel：可选；建议用于承载当前选中告警或设备详情；若不出现，则应确保 alert-center 列表本身具备足够的详情能力。
- **common_misuse**：
  - 仅在 HUD 中显示告警计数，而没有独立的 `alert-center` 面板，导致告警无法被有效浏览和筛选。
  - 把 alert-center 做成普通列表样式，未使用规范的类名与分区结构。
- **human_confirmation_needed**：
  - 需确认：
    - 告警优先级/分组规则（按设备、区域、级别等）。
    - 是否需要告警详情与三维对象的联动高亮逻辑。

---

## 4. Mode 4 — 紧急告警叠加（Critical Banner Overlay）

- **mode_id**：4
- **mode_name**：紧急横幅叠加
- **applicable_when**：
  - 在既有 Mode 1/2/3 布局上，叠加全局紧急告警（P1/P0）；
  - 不作为单独母模板，而是某种“叠加模式”。
- **primary_example**：
  - 无独立 HTML 文件；参考 `docs/operations/ue5-overlay-layout-playbook.md` 中的 Mode 4 骨架代码。
- **fallback_examples**：
  - 在 Mode 1/2/3 页面基础上，叠加 `ue5-critical-banner` 与相关内容。
- **recommended_level**：
  - 通常仍保持原页面 Level（1 或 2），但逻辑复杂度往往提升。
- **required_shell**：
  - 在已有模式的 `ue5-overlay-safe-area` 内追加：`ue5-critical-banner` 元素。
- **required_layers**：
  - Critical：`ue5-overlay-layer--critical`
- **common_misuse**：
  - 将 Mode 4 当作单独 layout_mode 使用，没有任何基础 HUD/面板结构。
  - 叠加横幅时覆盖 HUD 的全部交互区域，导致用户无法操作。
- **human_confirmation_needed**：
  - 需确认：
    - 紧急横幅需要承载哪些信息（标题、影响范围、操作按钮等）；
    - 触发/解除的条件与流程。

---

## 5. Mode 5 — 双侧面板 + 底部 Dock（Full Layout with Dock）

- **mode_id**：5
- **mode_name**：双侧固定面板 + 底部 Dock
- **applicable_when**：
  - 需要同时展示大量侧边信息（如左侧工艺流、右侧设备详情），并在底部展示时间轴或多视图 Dock；
  - 典型是“复杂数字孪生控制台”场景。
- **primary_example**：
  - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`（candidate + use_scope: limited）
- **fallback_examples**：
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`（digital twin 专用，混合 b_system 元素，仅在明确数字孪生驾驶舱需求下使用）。
- **recommended_level**：
  - 默认：`level_2`，很多情况下甚至趋向 `level_3`（信息架构明显扩展）。
- **required_shell**：
  - 根骨架：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`
  - 左右面板：`detail-panel`（左） + `detail-panel`（右，常带 `--pinned` 修饰）
  - 底部 Dock：`ue5-overlay-bottom-dock`
- **required_layers**：
  - HUD：`ue5-overlay-layer--hud`（如有）
  - 左/右面板：`ue5-overlay-layer--detail`
  - Dock：可视为 detail 或单独分层，需在样式中保持 z-index 合理。
- **模块配置偏好（HUD / alert-center / detail-panel / world-marker）**：
  - detail-panel：默认左右各有一个 pinned detail-panel；如需要在左右继续堆叠多层 pinned 面板，应首先复查信息架构是否过重。
  - world-marker：推荐高密度使用，用于在中央三维场景中投射 cockpit 的关键状态；完全没有 world-marker 的 cockpit 通常是不合理的。
  - HUD：可按项目取舍；对于信息极度密集的驾驶舱，可以弱化顶部 HUD，仅保留系统栏与关键状态指示，避免过度压缩三维视口高度。
  - alert-center：可选；当 cockpit 以告警为主线时，推荐保留结构化 alert-center（独立面板或嵌入右侧 detail-panel）；当以工艺流或多视图联动为主时，可将告警收敛在右侧 detail-panel 内。
- **common_misuse**：
  - 在非数字孪生/极复杂场景下滥用 Mode 5，导致界面过重、学习成本过高。
  - 忽略 `use_scope: limited`，将 Mode 5 当作所有 UE5 页面的默认模板。
- **human_confirmation_needed**：
  - 需确认：
    - 左右面板中哪些信息是“长期驻留”的，哪些可以缩减为弹窗/临时视图；
    - 底部 Dock 承载的是时间轴、视图切换还是其他功能？其优先级如何？

---

## 6. 数字孪生驾驶舱（Digital Twin Cockpit，特殊说明）

- **mode_id**：N/A（可基于 Mode 2/3/5 扩展）
- **mode_name**：数字孪生驾驶舱
- **applicable_when**：
  - 明确需求为“数字孪生控制台 / 驾驶舱”，需要同时呈现三维状态、业务 KPI 与多视图联动。
- **primary_example**：
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`（`use_scope: limited`）
- **fallback_examples**：
  - 具体依赖上文 Mode 2/3/5 的组合。
- **recommended_level**：
  - 至少 `level_2`，复杂项目通常 `level_3`。
- **common_misuse**：
  - 在一般 UE5 HUD 场景中直接使用数字孪生驾驶舱模板，导致信息架构完全不匹配。

---

## 7. 与中间层和审计的关系

- 当你在 `data/task_router.json` 中新增/调整与 `ue5_overlay` 相关的任务时，应：
  1. 先在本文件中确定对应 `mode_id` 与 `primary_example`；
  2. 再将映射关系同步进 `scene_coverage_matrix.yml.scene_coverage.ue5_overlay` 与 `skill_version.json`；
  3. 最后更新 `task_router` / `template_router`，并适配 `docs/operations/ue5-overlay-layout-playbook.md`。
- 在为 UE5 场景生成页面后：
  - 必须运行：`scripts/skill-audit.js <file> --scene ue5_overlay`；
  - 若出现 `frame_shell_missing` / `unknown_classes` / `demo_modifier_leak` / `broken_resource_refs` 等 ERROR，说明你偏离了本映射或真值源。

通过本文件，你可以在 UE5 Overlay 场景下，把“需求对应哪种 layout_mode？应该选哪张模板？推荐的 Level 是多少？有哪些常见误用需要避免？哪些点必须让人类拍板？”这些关键问题一次性说清楚，而不是在模板和 Playbook 之间来回猜测。