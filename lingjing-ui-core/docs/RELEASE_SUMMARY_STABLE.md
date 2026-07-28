# Lingjing UI Core v3.0.0 · Release Summary (Stable)

> 目的：给出当前 v3.0.0 的稳定版发版口径，说明本版核心能力、稳定边界、明确不做项与已知限制。仅总结已落盘事实，不预支后续规划。

---

## 1. 本版核心能力概览

### 1.1 UI 能力

- 已提供覆盖 `b_system` / `ue5_overlay` / `website` / `presentation` / `ai_assistant` 的样式入口与组件体系；
- 已沉淀 canonical 模板与 limited 模板，用于典型 B 端后台、UE5 Web Overlay 大屏、网站着陆页与演示文稿；
- 已通过 `data/class_registry.json`、`scene_coverage_matrix.yml`、`task_router.json`、`template_router.json` 建立起“类名 → 结构 → 模板 → 场景”的真值链路；
- 已提供 `scripts/skill-audit.js` 与 `docs/validation/` 作为 UI 侧的审计与回归基础设施。

### 1.2 UX/UI 对齐与 handoff

- `lingjing-ux-core` 已提供结构化 `ux_spec` 输出与典型场景样本；
- `docs/UX_UI_ALIGNMENT_PLAN.md`、`docs/UX_UI_CROSSWALK.md`、`docs/UX_UI_HANDOFF_REGRESSION.md` 已完成第一批最小对齐与回归验证；
- 当前状态：UX → UI handoff 在 `b_system` / `website` / `ai_assistant` / `ue5_overlay` 的主链上已“可用且可解释”，仍保留部分 archetype 处于“部分对齐”。

### 1.3 当前运行模式

- UI 侧已进入 `Run-Phase1-ops`：以既有规则与模板为主，辅以观察与轻量修复；
- 默认通过 `SKILL.md §0.0 / §0.1 / §1.1 / §3.0 / §5.0` 驱动执行，通过 `scene_coverage_matrix.yml` 与 router 决定模板落点；
- 运行期观测与回归主要通过 `docs/operations/NEXT_STAGE_OPERATION_PLAN.md` 与 `docs/operations/MULTI_SCENE_OBSERVATION_CYCLE.md` 协调，由 `docs/validation/` 留底。

---

## 2. 当前稳定边界

### 2.1 已较稳定的 scene / archetype / page_type

- `b_system`
  - `list / advanced_list / detail / dashboard`：已具备 canonical 模板、scene matrix、router 与 Guard，多轮回归已跑通；
  - 对应 archetype 如 `supply_chain_monitoring`、典型审批/工单场景，可通过 crosswalk + router 进入稳定落点；
- `ue5_overlay`
  - `overlay_dashboard` Mode 1/2/3 + minimal：已具备清晰的 layout_mode 与 shell 约束，配有正反例与审计规则；
  - 典型 UE5 工厂 overlay scene 可稳定命中 `ue5_overlay` authority，并以 `overlay_dashboard` 为默认落点；
- `website`
  - `website_marketing_landing` archetype 对应的 landing page：可直接 handoff 到 `website-complete.html` 作为 canonical 模板；
- `ai_assistant`
  - `ai_assistant_workspace`：已明确独立 scene 与 `assistant_workspace` page_type，模板落点为 limited 的 `b-system-ai-assistant.html`；
- `presentation`
  - `presentation_quarterly_review`：已可以通过 crosswalk 映射到 presentation/business_report 方向，但仍处于部分对齐（见 Known Limits）。

### 2.2 仍属 partial / limited / candidate 的部分

- `website` 中除 landing 以外的 feature / pricing 组合：当前仍以兼容支持为主，缺少完整中间层；
- `presentation` 中除季度经营汇报以外的 product_presentation / planning_proposal：目前仍视为部分对齐与 Level 2/3 自构场景；
- `ai_assistant` 除 canonical workspace 外的变体：仍需人工判断与 stop&ask，不视为完全稳定；
- 部分 `b_system` archetype 在 dashboard 与 workspace 之间仍需结合页面骨架做人工判定。

---

## 3. 当前明确不做什么（v3.0.0 范围内）

> 以下“不做”指的是在当前 v3.0.0 稳定版范围内，不会主动推进的结构性工作；后续如需升级，应通过新的版本规划单独立项。

- 不开启第二批模板修复：
  - 当前模板修复集中在 Phase 1 任务范围内，后续如需扩充将通过新的 repair 迭代执行；
- 不开启第二批 UX/UI 最小对齐：
  - 现有 crosswalk 与 handoff 已能支撑关键场景，剩余“部分对齐”交由 observation 与轻量回填处理；
- 不启动全面 Phase 2：
  - 当前运行模式仍是 `Run-Phase1-ops`，不主动扩张 scene/page_type/router 的覆盖面；
- 不新增新的 scene：
  - `scene_coverage_matrix.yml` 中现有 scene 视为本版范围；新增 scene 需要新的规划与验证周期。

---

## 4. 已知限制（概要）

> 详尽的边界说明见 `docs/KNOWN_LIMITS.md`；此处仅给出概要，方便快速评估风险。

- Page_type 分流仍需人工兜底的场景：
  - `presentation` 中 business_report / product_presentation / planning_proposal 的边界；
  - `b_system` 中 dashboard vs operations_workspace 在部分 archetype 上仍需 stop&ask；
- Archetype 仍为部分对齐的情况：
  - `presentation_quarterly_review` 已可用，但 deck 结构转换仍有复杂度；
  - 部分 B 端运控场景在“二维运控 vs 三维 overlay”之间仍需人工判断；
- Examples 仅为局部 / 特殊用途资产的情况：
  - `design-system-overview.html`、`core-icon-library.html`、各类 `*showcase*.html`、`aircraft-manufacturing-*.html` 仅作为 demo / reference / draft 使用；
  - `ue5_overlay_engine_test.html` 仅限 UE5 引擎桥接 / 性能 / world-marker 测试，不进入默认模板主链；
- UX/UI handoff 仍在观察期的点：
  - crosswalk 对部分 archetype 的 page_type 划分仍标记为“部分对齐”，需要结合 observation 与回归报告使用。

---

## 5. 一句话总结

本版 v3.0.0 已可作为 **“以 b_system 与 ue5_overlay 为主线、其他场景兼容可用”** 的稳定 UI 技能包版本：核心规则与模板已成型，UX/UI handoff 在关键场景上可用，已知限制和“不做”的边界也都明确落档。