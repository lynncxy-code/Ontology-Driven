# Lingjing UI Core v3.0.0 · Known Limits

> 目的：列出当前 v3.0.0 版本下已知的能力边界与限制，避免在未稳定的区域误导 AI 或使用方。本文件是风险说明，不是新规划。

---

## 1. scene / page_type 级别的已知限制

### 1.1 `b_system`

- Dashboard vs Operations Workspace：
  - 部分运控 / 战情室类 archetype（如 `ops_console_control_tower`）在 dashboard 与 operations_workspace 之间仍存在灰区；
  - 当前 router 与 Guard 能给出推荐落点，但在“强交互作业区”显著放大时，仍需要 stop&ask 与人工判断；
- 多页业务流场景：
  - 涉及多步骤审批、复杂业务闭环时，现有 canonical 示例更偏单页入口（dashboard 或 detail），未覆盖完整 multi-step flow 的所有页面形态。

### 1.2 `ue5_overlay`

- Overlay Dashboard 的细分变体：
  - `overlay_dashboard` 的 Mode 1/2/3 + minimal 已相对稳定，但 `digital_twin_dashboard` / `overlay_full_layout` 与 minimal overlay 的边界仍需结合结构信号与观察样本；
  - world-marker 重度使用场景在“信息层 vs 交互主界面”之间仍属灰区，需要结合 UE 侧画面与业务语义共同判断；
- cockpit 类场景：
  - 部分 cockpit / control center 需求在 `b_system` 与 `ue5_overlay` 之间仍存在 authority 歧义，需通过 UX spec 与 crosswalk 协同判断。

### 1.3 `website`

- Feature / Pricing 页面：
  - 当前 canonical 主要覆盖 marketing landing，feature 与 pricing 场景仍处于兼容支持状态；
  - 对于以复杂价格表或功能矩阵为主的页面，AI 需结合业务需求与 UX spec 做结构设计，不可完全依赖现有模板。

### 1.4 `presentation`

- 非经营汇报类 deck：
  - `presentation_quarterly_review` 已有相对稳定的 handoff 路径，但 product_presentation / planning_proposal 仍缺少完整 canonical；
  - 当前建议仍以 Level 2/3 自构为主，并通过审计脚本校验基本规范，而非依赖固定模板。

### 1.5 `ai_assistant`

- 非 workspace 类场景：
  - 当前仅 `ai_assistant_workspace` archetype 在 crosswalk 中被明确为 `ai_assistant / assistant_workspace`；
  - 其他提示泛用型助手、轻量工具栏等场景仍视为“部分对齐”，需要结合业务上下文与 UX spec 具体判断。

---

## 2. 模板与 examples 的已知限制

- Demo / showcase 模板：
  - `design-system-overview.html`、`core-icon-library.html`、各类 `*showcase*.html` 仅供人工查阅与 demo 使用；
  - 它们可能包含实验性样式或脚本，不保证在业务场景下直接复用；
- Draft / 待观察模板：
  - `b-system/aircraft-manufacturing-*.html`、部分 presentation 模板仍标记为 draft；
  - 这些模板保留追溯与探索价值，但不应作为 router 的默认落点；
- Limited / test-only 模板：
  - `ue5_overlay_engine_test.html` 仅用于 UE5 引擎 / 桥接 / 性能测试，不应作为业务模板；
- 资源引用不完全统一：
  - 少数历史模板中存在使用 CDN 脚本（如早期 presentation 模板使用 `https://unpkg.com/lucide@latest`）的记录；
  - 当前规范要求一律使用本地 `scripts/lucide-umd-500.js` / `echarts.min.js` / `echarts-theme-lingjing.js`，旧模板应被视为反例而非新规范。

---

## 3. UX/UI handoff 的已知限制

- Crosswalk 仍有“部分对齐”条目：
  - 某些 archetype 在 `docs/UX_UI_CROSSWALK.md` 中明确标记为部分对齐，依赖 stop&ask 与 observation 支撑；
- Legacy 命名与路径噪音：
  - 个别 UX flows / examples 仍使用旧命名（如 `ops_alert_to_action`）或旧路径前缀，对 UI 侧判断会产生噪音；
  - 当前已通过 handoff regression 与 observation 记录这些噪音来源，但尚未全部清理；
- UX spec 的 page_type 间接表达：
  - 目前仍主要通过 `pages + zones + component_roles` 间接表达 page_type，缺少正式字段；
  - 对于复杂场景，UI 侧仍需结合骨架与组件角色做判断，而不仅仅依赖单一字段。

---

## 4. 使用建议

- 在上述“已知限制”覆盖的场景中，AI 工具应：
  - 优先读取 `TRUTH_SOURCES.md` 与 `docs/UX_UI_CROSSWALK.md` 中的相关说明；
  - 在存在明显歧义时主动触发 stop&ask，而不是强行按某一模板落地；
  - 在输出摘要中标注“命中 Known Limits 范围”，简要说明风险点与人工兜底建议；
- 维护者在后续版本中，如需缩小这些限制范围，应通过新的治理/修复迭代单独立项，而不是在当前稳定版中悄然扩建。
