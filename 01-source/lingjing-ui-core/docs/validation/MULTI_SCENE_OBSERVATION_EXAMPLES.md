# MULTI_SCENE_OBSERVATION_EXAMPLES · Phase 1 多 scene observation 样本归档演示

> **文档目的**：演示跨 scene observation 协议在真实样本上的运行方式，跑通一条完整链路：
> **样本进入 → 统一字段记录 → 三档分类 → 回填去向 → 升级判断**。
>
> **适用范围**：当前仅覆盖 `b_system` / `ue5_overlay` / `website` / `ai_assistant` / `presentation` 五个核心 scene 的 Phase 1 样本；后续可在同一文档中持续追加 observation 记录。

---

## 1. observation 记录格式

> 本节给出统一记录字段，后文所有样本均按此格式归档。

- **样本 ID**：用于跨文档引用的稳定标识（优先复用已有 case/guard id，必要时新增 observation id）。
- **所属 scene / 关联 scene**：
  - `所属 scene`：当前任务预期落在哪个主 scene（b_system / ue5_overlay / website / ai_assistant / presentation）。
  - `关联 scene`：若样本本身是跨 scene 混合（例如 website + b_system），在此列出相关 scene，方便 Guard/路由检查。
- **输入描述**：需求原文的简化版，一句到数句即可。
- **当前预期 scene**：在当前真值源与 Guard 口径下，这条具体任务应该归入哪个 scene。
- **当前预期 page_type**：在该 scene 下的 page_type 预期，比如 `list` / `dashboard` / `overlay_dashboard` / `assistant_workspace` / `product_presentation` 等。
- **当前预期 template**：当前版本下预期使用的主模板（示例 HTML 路径）。
- **是否触发 stop&ask**：`是` / `否`，以及触发的大致 Guard 条款（如 `EXTENSION_GUARD §1.7`）。
- **命中的 Guard / 验证文档结论**：
  - 对应的 Guard 条款编号（如 `EXTENSION_GUARD §1.9`）；
  - 或对应验证文档中的小节（如 `WEBSITE_PHASE1_VALIDATION §3.4`）。
- **当前归类**：三档之一：
  - `已知稳定`：scene / page_type / template 组合在多轮样本中表现一致，Guard 行为稳定，不指向立即升级动作。
  - `观察中`：当前处理方案可接受，但明确存在“需继续积累样本”的 open 问题。
  - `接近触发预警`：当前仍视为 observation，但若类似样本继续出现，将需要触发更高一级动作（如 Guard 评估 / 模板族评估 / Phase 2 候选判断）。
- **是否需要回填到具体 scene 验证文档**：
  - `是`：应在对应 scene 的 `*_PHASE1_VALIDATION.md` 中补一条样本，或更新 Guard 回归样例；
  - `否`：仅作为跨 scene 观察样本存在于本文件即可。
- **是否足以触发升级动作**（当前时点）：分三类分别给出 `是/否`：
  - `Guard 评估`：是否需要重新评估或微调 Guard 条款；
  - `template / canonical 评估`：是否足以让某个模板族进入 canonical 候选评估；
  - `Phase 2 候选判断`：是否足以将某个局部纳入 Phase 2 试点候选。
- **简短说明**：对当前分类与后续动作的 2–4 句解释。

> 下文所有样本记录都遵循上述字段，必要时可在“简短说明”中补充跨 scene 视角的观察。 

---

## 2. 归档样本一览表

> 按“已知稳定 / 观察中 / 接近触发预警”三档，汇总本轮选取的 8 条样本。

| 样本 ID | 所属 scene | 关联 scene | 简要描述 | 当前归类 |
|---------|------------|------------|----------|----------|
| `baseline_b_system_list_top_filters` | b_system | — | 典型工单列表（list + 顶部筛选条），Phase 1 回归基线正例 | 已知稳定 |
| `baseline_ue5_overlay_minimal_no_hud` | ue5_overlay | — | 极简 Overlay（无 HUD，仅 world-marker），Phase 1 回归基线正例 | 已知稳定 |
| `website_case_landing_airline_cloud` | website | — | B2B SaaS 官网首页（landing），明确 homepage 诉求 | 已知稳定 |
| `ai_assistant_case_pure_workspace` | ai_assistant | b_system | 纯助手工作台（对话 + 计划 + 多工具调用 + 日志） | 已知稳定 |
| `website_case_w3_pricing_comparison_heavy` | website | — | 重度套餐矩阵 + FAQ 的 pricing 页，仍落在 homepage 壳 | 观察中 |
| `ai_assistant_case_dashboard_plus_assistant` | b_system | ai_assistant / ue5_overlay | dashboard + assistant 并置的混合场景 | 观察中 |
| `presentation_case_topic_deck_plus_site` | presentation / website | b_system（潜在） | 同一主题的分享 deck + 官网专题页双产物 | 观察中 |
| `presentation_case_work_report_template_misuse` | presentation | b_system | 试图将 `presentation-work-report.html` 当成通用工作汇报壳 | 接近触发预警 |

---

## 3. 逐条 observation 样本记录

### 3.1 `baseline_b_system_list_top_filters` — 普通工单列表（已知稳定）

- **样本 ID**：`baseline_b_system_list_top_filters`
- **所属 scene / 关联 scene**：
  - 所属：`b_system`
  - 关联：无
- **输入描述**：
  - “航空制造后台的工单列表页，需要按状态/优先级/负责人筛选工单，支持搜索工单号和批次号，表格中展示工单基础信息与当前状态。”
- **当前预期 scene**：`b_system`
- **当前预期 page_type**：`list`
- **当前预期 template**：`examples/b-system/b-system-task-list-top-filters.html`
- **是否触发 stop&ask**：
  - 否；需求语义清晰落在“列表页 + 顶部筛选条”的 standard list 模式。
- **命中的 Guard / 验证文档结论**：
  - 回归基线：`PHASE1_REGRESSION_BASELINES §2`（b_system_list 正例样本）。
  - Guard：应满足 `b_system_list_left_filter_panel_forbidden` 的“未命中”路径（没有左侧高级筛选壳）。
- **当前归类**：`已知稳定`
- **是否需要回填到具体 scene 验证文档**：
  - 否（已在 `PHASE1_REGRESSION_BASELINES` 与 `PHASE1_GENERATION_PLAYBACK §1.1` 中作为代表样本记录）。
- **是否足以触发升级动作**：
  - Guard 评估：否（已有 Guard 行为与样本完全对齐）。
  - template / canonical 评估：否（已在 `system-template-map` 中作为 list primary_example 出现）。
  - Phase 2 候选判断：否（只是 list 族的标准正例样本之一）。
- **简短说明**：
  - 此样本证明：在真实任务描述下，普通工单列表稳定落在 `b_system_list` + `b-system-task-list-top-filters`，且自动审计与 Guard 均 PASS。
  - 作为 observation 体系中的“绿色样本”，它主要用来确认后续规则调整不会破坏 list 主链，不承担新的升级动作触发职责。

---

### 3.2 `baseline_ue5_overlay_minimal_no_hud` — 极简 Overlay（无 HUD，已知稳定）

- **样本 ID**：`baseline_ue5_overlay_minimal_no_hud`
- **所属 scene / 关联 scene**：
  - 所属：`ue5_overlay`
  - 关联：无
- **输入描述**：
  - “仅需在三维场景上标注关键工位簇的极简视图，不需要 HUD、不需要告警中心，只保留 world-marker 与基础说明。”
- **当前预期 scene**：`ue5_overlay`
- **当前预期 page_type**：`overlay_dashboard`（子类型：`minimal_overlay`）
- **当前预期 template**：`examples/ue5-overlay/ue5_overlay_minimal_no_hud.html`
- **是否触发 stop&ask**：
  - 否；需求语义已经明确“无 HUD / 仅 world-marker”，可直接落在 minimal overlay。
- **命中的 Guard / 验证文档结论**：
  - 回归基线：`PHASE1_REGRESSION_BASELINES §8`；
  - 模板映射：`ue5-template-map §1.5 minimal overlay`；
  - Guard：仅命中 `shell_consistency.ue5_overlay`，不触发任何 Mode1/2/3/Dock 相关 ERROR（证明 HUD 已降级为可选模块）。
- **当前归类**：`已知稳定`
- **是否需要回填到具体 scene 验证文档**：
  - 否（已在 `PHASE1_REGRESSION_BASELINES` 与 `PHASE1_GENERATION_PLAYBACK §2.2` 中完整记录）。
- **是否足以触发升级动作**：
  - Guard 评估：否；此样本更多是已有 Guard 设计的正向锚点。
  - template / canonical 评估：否；minimal 仍标记为 candidate + limited use_scope，未来是否 canonical 需要更多业务样本。
  - Phase 2 候选判断：否；minimal 的 Phase 2 问题主要是“与 cockpit / workspace 的组合”，非本样本本身。
- **简短说明**：
  - 此样本验证了 Phase 1 的一个核心决策：HUD 在 `ue5_overlay` 场景中是“按需模块”而非必选骨架。
  - 作为 observation 框架里的“绿色样本”，它帮助确认未来规则调整不会误伤极简 Overlay 的合法性。

---

### 3.3 `website_case_landing_airline_cloud` — B2B 官网 landing（已知稳定）

- **样本 ID**：`website_case_landing_airline_cloud`
- **所属 scene / 关联 scene**：
  - 所属：`website`
  - 关联：`b_system`（潜在 cockpit/工作台场景，但本任务未涉及）
- **输入描述**：
  - “为‘灵境航空智能云’设计官网首页，说明产品定位、关键价值，并引导用户预约演示或下载白皮书。”
- **当前预期 scene**：`website`
- **当前预期 page_type**：`landing`
- **当前预期 template**：`examples/website/website-complete.html`
- **是否触发 stop&ask**：
  - 否；需求明确指定“官网首页”，未混入 dashboard 或 cockpit 语义。
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`WEBSITE_PHASE1_VALIDATION §3.1`；
  - Guard：隐含符合 `EXTENSION_GUARD §1.7` 对 landing 的判断（无 pricing/feature 歧义，无 website vs b_system 混合语义）。
- **当前归类**：`已知稳定`
- **是否需要回填到具体 scene 验证文档**：
  - 否（已在 `WEBSITE_PHASE1_VALIDATION` 中作为首批样本记录）。
- **是否足以触发升级动作**：
  - Guard 评估：否；样本证明现有 Guard 不会过度打断简单 landing 需求。
  - template / canonical 评估：部分是：它是 homepage canonical 壳稳定性的证据之一，但单个样本不足以独立触发 Phase 2。
  - Phase 2 候选判断：否；是否拆更多 website canonical 仍需综合其它 feature/pricing 样本。
- **简短说明**：
  - 此样本证明 `website-complete.html` 在典型 B2B landing 场景下表现稳定，无需额外模板或复杂 Guard。
  - 在 observation 体系中，它作为典型“纯 landing 正例”，主要用来检测未来规则/模板改动是否意外破坏 homepage 壳。

---

### 3.4 `ai_assistant_case_pure_workspace` — 纯助手工作台（已知稳定）

- **样本 ID**：`ai_assistant_case_pure_workspace`
- **所属 scene / 关联 scene**：
  - 所属：`ai_assistant`
  - 关联：`b_system`（通过工具调用后端 API）
- **输入描述**：
  - “做一个 AI 助手工作台，用户通过对话提出任务，助手先澄清需求，再规划子任务，并在同一页面里展示工具调用日志和结果。”
- **当前预期 scene**：`ai_assistant`
- **当前预期 page_type**：`assistant_workspace`
- **当前预期 template**：`examples/b-system/b-system-ai-assistant.html`
- **是否触发 stop&ask**：
  - 否；需求已经包含“澄清 → 规划 → 多工具调用 → 执行日志 + 结果回顾”的完整助手链路。
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`AI_ASSISTANT_PHASE1_VALIDATION §4.1`；
  - Guard：符合 `EXTENSION_GUARD §1.8` 中“多轮澄清 + 计划 + 多工具调用的助手工作台”正例描述，以及 `§1.5` 对 limited 模板合规使用的下界（对话 + 计划板 + 工具日志 + 结果区齐备）。
- **当前归类**：`已知稳定`
- **是否需要回填到具体 scene 验证文档**：
  - 否（已记录为首批 W1 样本与 Guard 回归样本之一）。
- **是否足以触发升级动作**：
  - Guard 评估：否；当前 Guard 已明确该场景是 `ai_assistant` 正例。
  - template / canonical 评估：否；它证明 `b-system-ai-assistant.html` 在合规使用时是足够的，但 limited 是否晋级 canonical 仍需更多场景。
  - Phase 2 候选判断：否；Phase 2 的重点更多在“是否需要新增助手子类型/模板”，与本样本无直接驱动关系。
- **简短说明**：
  - 此样本是 `ai_assistant` 场景的“绿色锚点”：确认有限模板在纯助手工作台场景中的合规与稳定性。
  - 在 observation 中，它主要用于检测未来规则调整有没有误将此类需求降级回 `b_system` 或误判为 limited 模板误用。

---

### 3.5 `website_case_w3_pricing_comparison_heavy` — 重度套餐对比 pricing 页（观察中）

- **样本 ID**：`website_case_w3_pricing_comparison_heavy`
- **所属 scene / 关联 scene**：
  - 所属：`website`
  - 关联：无
- **输入描述**：
  - “做一页偏重对比的定价页面，需要 4 档套餐、详细功能矩阵、年付/月付切换和常见计费问题说明。”
- **当前预期 scene**：`website`
- **当前预期 page_type**：`pricing`
- **当前预期 template**：`examples/website/website-complete.html`（homepage 壳中的 pricing 区扩展）
- **是否触发 stop&ask**：
  - 是；按 `WEBSITE_PHASE1_VALIDATION §6.2` 与 `EXTENSION_GUARD §1.7`，需要澄清：“是否希望在此页完成价格/权益决策？是否需要独立 URL 和完整套餐矩阵？”
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`WEBSITE_PHASE1_VALIDATION §6.2`；
  - Guard：`EXTENSION_GUARD §1.7` 对 landing vs pricing 边界的 stop&ask ；Phase 1 结论为“在不拆新模板前，pricing 仍由 homepage 壳承接”。
- **当前归类**：`观察中`
- **是否需要回填到具体 scene 验证文档**：
  - 是：应继续作为 pricing 边界样本维护在 `WEBSITE_PHASE1_VALIDATION` 的后续 observation 小节中，用于跟踪未来是否仍坚持“不拆 pricing 模板”的策略。
- **是否足以触发升级动作**：
  - Guard 评估：否；现有 Guard 能稳定判定为 pricing，不需要立即调整。
  - template / canonical 评估：部分是；此类重度 pricing 样本是将来评估“是否需要独立 pricing 模板”的关键证据之一，但单样本不足以触发。
  - Phase 2 候选判断：否（需要连续出现更多结构显著偏离 homepage 壳的复杂 pricing 样本）。
- **简短说明**：
  - 此样本证明：在当前阶段，重度 pricing 页仍可由 `website-complete.html` 承载，因此“拆出独立 pricing 模板”暂不成立。
  - 但它同时是 future Phase 2 的观察点之一：若未来类似样本大量出现且 homepage 壳承载开始吃力，将推动 pricing 模板分化评估。

---

### 3.6 `ai_assistant_case_dashboard_plus_assistant` — dashboard + assistant 并置（观察中）

- **样本 ID**：`ai_assistant_case_dashboard_plus_assistant`
- **所属 scene / 关联 scene**：
  - 所属：`b_system`（主场景）
  - 关联：`ai_assistant`、`ue5_overlay`（若 cockpit 参与）
- **输入描述**：
  - “做一个运营驾驶舱页面，左侧是 KPI 仪表盘和告警列表，右侧放一个 AI 助手窗口，可以让助手根据当前数据生成当日巡检重点和处理建议。”
- **当前预期 scene**：`b_system` 或 `ue5_overlay`（根据 PRD 是否有 3D cockpit），助手作为模块/浮层。
- **当前预期 page_type**：`dashboard` / `overlay_dashboard`（主场景），助手不单独占 page_type。
- **当前预期 template**：
  - 仪表盘：`examples/b-system/b-system-complete.html` 或 `examples/ue5-overlay/ue5_overlay_dashboard.html`；
  - 助手：嵌入模块，而非单独选 `b-system-ai-assistant.html`。
- **是否触发 stop&ask**：
  - 是；按 `AI_ASSISTANT_PHASE1_VALIDATION §4.3` 与 `EXTENSION_GUARD §1.8`，必须补问“主任务是盯盘/操作，还是对话 orchestrate？”、“去掉助手后页面是否仍然成立？”。
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`AI_ASSISTANT_PHASE1_VALIDATION §4.3`、`§6.3`；
  - Guard（最小 patch 后）：`EXTENSION_GUARD §1.8` 中“dashboard + assistant 混合页主场景判断”的分支（以及 b_system / ue5_overlay 现有 cockpit/dashboard Guard）。
- **当前归类**：`观察中`
- **是否需要回填到具体 scene 验证文档**：
  - 是：应在 `AI_ASSISTANT_PHASE1_VALIDATION` 和未来的 multi-scene 观测记录中持续追加类似样本，用于评估“混合场景是否需要更细的 Guard 条款或中间层模式”。
- **是否足以触发升级动作**：
  - Guard 评估：部分是；当类似“dashboard + assistant” 样本积累到一定数量时，可能需要从“简单主场景判断”升级为更细粒度的模式（例如标准 sidecar 模式）。
  - template / canonical 评估：否；当前更多是中间层/Guard 问题，而非模板壳问题。
  - Phase 2 候选判断：否；作为混合场景，尚缺足够样本支持做模板族级 Phase 2 治理。
- **简短说明**：
  - 此样本是 `b_system` / `ue5_overlay` / `ai_assistant` 三方交汇的典型案例，现有 Guard 能给出“主场景 = dashboard/overlay + 助手组件”的保守答案。
  - 未来若这类样本在真实项目中大量出现，可能需要在 observation 文档基础上，将其升级为专门的“dashboard + assistant pattern”治理对象。

---

### 3.7 `presentation_case_topic_deck_plus_site` — 同一主题 deck + 官网专题页（观察中）

- **样本 ID**：`presentation_case_topic_deck_plus_site`
- **所属 scene / 关联 scene**：
  - 所属：`presentation` 与 `website`（本样本天然是两条任务）
  - 关联：`b_system`（如后续 cockpit/工作台延伸）
- **输入描述**：
  - “围绕新一代产品发布，希望既有一套分享 deck，用于路演/发布会，也有一个官网专题页，用于会后长期对外展示。”
- **当前预期 scene**：
  - 任务 A：`scene = presentation`（分享 deck）；
  - 任务 B：`scene = website`（官网专题页）。
- **当前预期 page_type**：
  - 任务 A：`product_presentation`；
  - 任务 B：`landing` 或 `feature`（视专题页定位而定）。
- **当前预期 template**：
  - 任务 A：`examples/presentation/presentation-product.html`；
  - 任务 B：`examples/website/website-complete.html` 或 `examples/website/website-feature-solution.html`。
- **是否触发 stop&ask**：
  - 是；按照 `PRESENTATION_PHASE1_VALIDATION §4.7` 与 Guard 建议 P1，需要补问“是否接受拆分为 deck + site 两条任务”“两个产物的受众与使用时长是否相同”。
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`PRESENTATION_PHASE1_VALIDATION §4.7`、`§8.4`；
  - Guard：`EXTENSION_GUARD §1.9`（presentation vs website）在当前最小 patch 中的逻辑，与本样本高度一致。
- **当前归类**：`观察中`
- **是否需要回填到具体 scene 验证文档**：
  - 是：
    - `PRESENTATION_PHASE1_VALIDATION`：继续作为“deck + site 双产物”典型样本；
    - `WEBSITE_PHASE1_VALIDATION`：后续可在多 scene 章节中引用该样本，确认 website 不吞 deck。
- **是否足以触发升级动作**：
  - Guard 评估：否；现有 `§1.9` 条款已明确推荐拆任务策略。
  - template / canonical 评估：否；当前关键问题是 scene 拆分，不是模板壳。
  - Phase 2 候选判断：否；多 scene 组合模式未来可能单独进入一个“组合模式治理”轨道，但本样本本身仍偏少。
- **简短说明**：
  - 此样本验证了“同一主题拥有多个 scene 是健康的”，Guard 能推动从“万能页”回到“deck + site 两条任务”。
  - 在 observation 中，它是 future multi-scene 模式治理的关键证据，但目前还不足以触发更重级模板治理。

---

### 3.8 `presentation_case_work_report_template_misuse` — 误用 work-report anti_pattern（接近触发预警）

- **样本 ID**：`presentation_case_work_report_template_misuse`
- **所属 scene / 关联 scene**：
  - 所属：`presentation`
  - 关联：`b_system`（长期工作台/工作汇报场景）
- **输入描述**：
  - “想用 `presentation-work-report.html` 作为所有内部周报/月报的通用模板，未来大部分经营汇报/项目汇报都参考这个结构，也希望 AI 默认生成这种工作汇报结构。”
- **当前预期 scene**：
  - 汇报 deck 部分：`scene = presentation`（但不使用 work-report 壳，应回到 `presentation-business` / `presentation-planning`）；
  - 日常进展管理：`scene = b_system`（工作台/dashboard）。
- **当前预期 page_type**：
  - deck：`business_report` 或 `planning_proposal`；
  - 工作台：`workspace` / `dashboard`。
- **当前预期 template**：
  - deck：`examples/presentation/presentation-business.html` / `examples/presentation/presentation-planning.html`；
  - 工作台：`examples/b-system/b-system-production-plan.html` 等；
  - `examples/presentation/presentation-work-report.html` 维持 `grade = anti_pattern`, `use_scope = forbidden`，不得进入路由。
- **是否触发 stop&ask**：
  - 是；根据 Guard 建议 P5（现已在 `EXTENSION_GUARD §3.3` 的 expansion 中体现），当检测到“所有周报/月报/工作汇报都统一用 work-report 壳”等语义时，必须 stop&ask 并提示这是 anti_pattern。
- **命中的 Guard / 验证文档结论**：
  - 验证文档：`PRESENTATION_PHASE1_VALIDATION §4.8`、`§7.3 P5`；
  - Guard：`EXTENSION_GUARD §3.3` 中针对 `presentation-work-report.html` 的 anti_pattern 说明与推荐回退路径（本轮 patch 已落地）。
- **当前归类**：`接近触发预警`
- **是否需要回填到具体 scene 验证文档**：
  - 是：继续作为 presentation 文档中的 anti_pattern 主样本；若真实项目中频繁出现类似诉求，应在该文档中新增“观测计数”与处理记录小节。
- **是否足以触发升级动作**：
  - Guard 评估：已触发（本轮 Guard patch 已将其写入 §3.3）；若后续仍频繁出现，可能需要再收紧提示语或在 router 层增加更强硬保护（例如禁止任何自动选择）。
  - template / canonical 评估：部分是；高频误用会促使我们考虑是否需要专门的“work_report candidate 模板”来替代该 anti_pattern，但前提是出现“正向、合理的工作汇报 deck 模式”。
  - Phase 2 候选判断：否；目前更多是“需要更强 Guard”，未到模板族治理阶段。
- **简短说明**：
  - 当前单条样本已足以 justify 把 `presentation-work-report.html` 明确写入 Guard anti_pattern 条款，这是 Phase 1 已完成的动作。
  - 在 observation 体系中，该样本被标为“接近触发预警”：
    - 如果未来真实需求还频繁要求“统一用 work-report 壳”
    - 则说明现有模板/scene 分工在“工作汇报”方向仍不清晰，可能需要：
      - 更强的 Guard 提示；
      - 或单独立项设计新的 work_report candidate 模板，并重新评估 presentation vs b_system 的分工。

---

## 4. 回填路径与升级分流示意

> 这一节从“样本 → 文档/机制”的视角，说明 observation 文档如何作为样本总入口与分流器，而非替代各 scene 文档。

- **只需留在本 observation 文档中的样本**：
  - `baseline_b_system_list_top_filters`、`baseline_ue5_overlay_minimal_no_hud`：
    - 已在 `PHASE1_REGRESSION_BASELINES` / `PHASE1_GENERATION_PLAYBACK` 中作为正式基线样本存在；
    - 在本文件中主要作为跨 scene “绿色锚点”，不需要额外回填。

- **需同步回填 / 对齐到具体 scene 验证文档的样本**：
  - `website_case_w3_pricing_comparison_heavy`：
    - 继续留在 `WEBSITE_PHASE1_VALIDATION` 的 pricing 边界章节；
    - 后续若新增类似样本，可在该文档中新建“pricing 观测样本”小节，记录数量、模板承载压力与 Guard 表现。
  - `ai_assistant_case_dashboard_plus_assistant`：
    - 持续在 `AI_ASSISTANT_PHASE1_VALIDATION` 的混合场景章节补充；
    - 同时在未来若有“跨 scene 组合模式”文档（例如 `MULTI_SCENE_COMBO_PATTERNS.md`），可作为 dashboard + assistant pattern 的首批观测样本。
  - `presentation_case_topic_deck_plus_site`：
    - 已在 `PRESENTATION_PHASE1_VALIDATION` 中记录，应继续在那里维护 deck + site 双产物的样本列表；
    - 未来若 `WEBSITE_PHASE1_VALIDATION` 增设“多 scene 协作”小节，也可在 website 侧引用该样本，确保两边文档对齐。
  - `presentation_case_work_report_template_misuse`：
    - 持续作为 presentation 文档中的 anti_pattern 主例，用于统计“误用倾向”的频率；
    - 若未来 Guard 文本进一步收紧，也应在 `PHASE1_MULTI_SCENE_REVIEW` 或后续 Guard 总结中更新其处理策略。

- **潜在触发更高一级动作时的去向示例**：
  - 当 `website_case_w3_pricing_comparison_heavy` 这类样本在真实项目中累积到一定规模时：
    - 由本 observation 文档汇总其计数与共性；
    - 再回填到 `WEBSITE_PHASE1_VALIDATION` 的“pricing Phase 2 准入条件”小节；
    - 最终推动“是否立项 pricing 模板分化评估”的决策。
  - 当 `ai_assistant_case_dashboard_plus_assistant` 这类混合样本变成常态时：
    - 由本文收集“dashboard + assistant”模式的多条样本；
    - 在 `AI_ASSISTANT_PHASE1_VALIDATION` 与 `PHASE1_MULTI_SCENE_REVIEW` 中共同标记为“多 scene 组合治理候选”；
    - 为后续“多 scene 组合模式治理”任务单提供真值源。
  - 当 `presentation_case_work_report_template_misuse` 频繁出现时：
    - 由本文件统计其出现频率与当前 Guard 处理情况（是否仍有绕过或误用）；
    - 再和 `PRESENTATION_PHASE1_VALIDATION` 中的 anti_pattern 小节联动，决定是仅加强 Guard 文案，还是启动“work_report candidate 模板”设计评估。

> 换句话说：**本 observation 文档负责“见人、见事、见链路”——记录样本、场景判断与潜在升级路线；具体规则与模板的收敛仍发生在各自的 scene 验证文档与 Guard 文件中。**

---

## 5. 三档分类机制的验证小结

- **“已知稳定”档**：
  - 对应的样本在多个文档与回归基线中都已有记录（例如 `baseline_b_system_list_top_filters`、`baseline_ue5_overlay_minimal_no_hud`、`website_case_landing_airline_cloud`、`ai_assistant_case_pure_workspace`）。
  - observation 记录主要用来监控“未来规则调整是否破坏现有稳定性”，不主动推进任何升级动作。

- **“观察中”档**：
  - 用于承载“现有方案可接受，但未来可能演化为 Phase 2 驱动因素”的样本，例如重度 pricing 页、dashboard + assistant 混合、deck + site 双产物。
  - 这类样本在文档中会显式写明：
    - 当前 Guard 与模板选择为何仍可接受；
    - 未来何种演化（数量增加、结构压力上升）会促使其升级为 Guard/模板评估的触发器。

- **“接近触发预警”档**：
  - 对应已经通过 Guard patch 明确禁止，但在需求侧仍可能反复被提出的模式，例如 `presentation_case_work_report_template_misuse`。
  - 这档样本说明：
    - 当前 Guard 已有正式条文防止误用；
    - 但在 observation 期内仍需关注此类需求的出现频率，如果成为高频，将推动更高一级的结构调整或模板设计。

- **分类模糊最容易出现在两类场景**：
  1. **复杂多 scene 混合**（如 dashboard + assistant + cockpit + website）：
     - 同一需求包含多重场景信号，很容易在“观察中”与“接近预警”之间摇摆；
     - 目前通过在说明中显式写清“当前为什么仍仅观察”与“未来的触发动作”来对冲模糊。
  2. **边界尚未完全固化的 page_type / 模板族**（如 pricing）：
     - 既有 evidence 支持当前做法，又有潜在演化方向；
     - 这里倾向于保守地归为“观察中”，并在 scene 验证文档中写出 Phase 2 准入条件。

- **轻量机制修正建议**：
  - 在 observation 记录中显式增加两个辅助字段（已经在本轮隐含使用）：
    - “**当前方案是否可接受（Y/N）**”：避免把明显已不可接受的情况仍标为“观察中”；
    - “**若再出现 N 次将触发什么动作**”：把模糊的“接近预警”具体化为“再出现 3 次则需要 Guard 评估”等轻量规则。
  - 本轮示例中的 `presentation_case_work_report_template_misuse` 已以文字方式体现这一思路，后续可以在模板中显式加入这两个字段。

---

## 6. 机制可用性判断：observation 是否已可投入日常使用？

- **字段设计层面**：
  - 当前字段集合已经能够完整描述一条样本在多 scene 体系中的位置（scene / page_type / template）、Guard 命中情况与潜在升级路线；
  - 缺口主要在“统计层/计数层”，更适合在未来增加简单的计数字段或外部表格工具，而无需调整本文件结构。

- **分类标准层面**：
  - “已知稳定 / 观察中 / 接近触发预警”三档分类在本轮样本上可以落地，并能清晰表达当前处置态度与后续可能动作；
  - 真正模糊的样本主要集中在复杂多 scene 混合方向，已通过“说明未来触发条件”的方式做了轻量对冲。

- **回填规则与升级触发层面**：
  - 每条样本都已经明确“是否需要回填到哪份 scene 文档”“未来在何种条件下可能触发 Guard / 模板 / Phase 2 评估”，证明“记录 → 分类 → 回填 → 升级判断”链路是可跑通的；
  - 当前阶段最大的问题不是机制本身，而是后续如何持续维护和统计 observation 样本，这部分可以通过简单流程补充，而无需立刻改文档结构。

> **结论（一句话）**：在当前规模和复杂度下，现有的 observation 机制（统一记录字段 + 三档分类 + 回填/升级分流）已经足以支撑后续日常治理，下一步更重要的是坚持使用、持续累积样本，而不是立即再做一轮机制重构。

---

## 7. Observation 周期 2026-04-01 ~ 2026-04-06 小结（第 1 周期 · 首轮执行）

> 本小结视为 **第一次正式 observation 周期** 的结束汇报。由于 Phase 1 收官后暂未引入新的真实业务样本，本周期以 **对既有 8 条样本的模式级整理与验证** 为主；所有样本均来自前置 Phase 1 文档与演示，未新增全新样本，相关结论仍具代表性。

### 7.1 本周期概览

- **周期时间**（逻辑窗口）：`2026-04-01 ~ 2026-04-06`
- **本周期纳入样本总数**：8 条
  - 其中：
    - 历史样本复用：8 条（全部来自前期 Phase 1 验证与本文件第 3 章记录）；
    - 本周期新增样本：0 条（无新业务/需求输入）。
- **按三档分类统计**：
  - 已知稳定：4 条
  - 观察中：3 条
  - 接近触发预警：1 条
- **本周期整体结论简述**：
  - 在“样本量有限、无新增样本”的前提下，observation 周期机制在文档层面可以完整跑通：
    - 样本被统一字段记录；
    - 可以按模式聚类；
    - 能给出“继续 observation 而非立即升级”的可解释结论；
  - 当前尚未达到任何模式的升级阈值，本周期所有模式均选择“继续 observation”。

### 7.2 本周期纳入样本清单

> 下表仅重申本周期视为 observation 对象的 8 条样本，并标注其 **当前分类、所属模式、是否需回填、是否触发升级判断**。全部为历史样本复用。

| 样本 ID | 所属 scene | 当前分类 | 所属模式 | 是否需回填 | 是否触发升级判断 |
|---------|------------|----------|----------|------------|------------------|
| `baseline_b_system_list_top_filters` | b_system | 已知稳定 | `canonical_b_system_list` | 否（已在基线与回放文档中） | 否 |
| `baseline_ue5_overlay_minimal_no_hud` | ue5_overlay | 已知稳定 | `canonical_ue5_minimal_overlay` | 否（已在基线与模板映射中） | 否 |
| `website_case_landing_airline_cloud` | website | 已知稳定 | `canonical_website_landing` | 否（已在 WEBSITE 验证文档中） | 否 |
| `ai_assistant_case_pure_workspace` | ai_assistant | 已知稳定 | `canonical_ai_assistant_workspace` | 否（已在 AI_ASSISTANT 验证文档中） | 否 |
| `website_case_w3_pricing_comparison_heavy` | website | 观察中 | `pricing_in_homepage_shell` | 是（继续维护在 WEBSITE 验证文档 pricing 小节） | 否（继续观察） |
| `ai_assistant_case_dashboard_plus_assistant` | b_system / ai_assistant / ue5_overlay | 观察中 | `dashboard_plus_assistant` | 是（AI_ASSISTANT 验证文档混合场景章节） | 否（继续观察） |
| `presentation_case_topic_deck_plus_site` | presentation / website | 观察中 | `deck_plus_site_dual_output` | 是（PRESENTATION 验证文档；website 侧可引用） | 否（继续观察） |
| `presentation_case_work_report_template_misuse` | presentation / b_system | 接近触发预警 | `anti_pattern_work_report_misuse` | 是（PRESENTATION 验证文档 anti_pattern 主样本） | Guard 已升级；本周期无新增样本，继续 observation |

> 备注：本周期“是否需回填”的判断与第 4 章一致，此处仅重申，未新增新的回填需求。

### 7.3 模式聚类与计数表

> 本节按“模式”而非散点样本整理本周期 observation 结果。由于本周期无新增样本，每个模式的计数均为 1，但仍给出档位与未来触发动作的说明，作为后续多周期对比的基线。

| 模式名 | 模式说明 | 本周期出现次数 | 涉及 scene | 当前档位 | 当前是否仍可接受 | 若再出现的潜在动作 |
|--------|----------|----------------|------------|----------|------------------|----------------------|
| `canonical_b_system_list` | 标准 b_system 工单列表 + 顶部筛选条 | 1 | b_system | 已知稳定 | 是：现有模板与 Guard 表现稳定 | 继续作为绿色锚点；若未来被误杀或被迫改壳，则触发 Guard 回归检查 |
| `canonical_ue5_minimal_overlay` | 极简 UE5 Overlay，仅 world-marker 无 HUD | 1 | ue5_overlay | 已知稳定 | 是：HUD 已成功降级为可选模块 | 继续作为绿色锚点；若 future patch 误将 HUD 视为强依赖，则需回滚/修正 Guard 或模板映射 |
| `canonical_website_landing` | B2B 官网 landing，homepage canonical 壳 | 1 | website | 已知稳定 | 是：homepage 壳在典型 landing 场景下健康 | 若 future landing 样本在 homepage 壳下出现不合理限制，需评估 homepage canonical 是否被过度约束 |
| `canonical_ai_assistant_workspace` | 纯助手工作台（对话 + 计划 + 多工具 + 日志） | 1 | ai_assistant / b_system（工具） | 已知稳定 | 是：limited 模板在合规使用时稳定 | 若 future 纯助手场景频繁需要绕路（如退回 b_system 壳），则评估 ai_assistant 模板族的完整性 |
| `pricing_in_homepage_shell` | 重度套餐对比 pricing 页仍承载在 homepage 壳中 | 1 | website | 观察中 | 暂可接受：当前证据不足以 justify 新 pricing 壳 | 当该模式在真实项目中累计 ≥3 条、且 homepage 壳明显吃力时，进入 template/canonical 评估队列（考虑 pricing 子模板） |
| `dashboard_plus_assistant` | dashboard/cockpit 与 AI 助手并置的混合页 | 1 | b_system / ue5_overlay / ai_assistant | 观察中 | 暂可接受：主场景仍清晰为 dashboard/overlay，助手为组件 | 若该模式在 ≥2 个 scene 中各出现 ≥2 条，且 stop&ask 高频，则进入 Guard 评估与“组合模式治理”候选（例如 sidecar pattern） |
| `deck_plus_site_dual_output` | 同一主题下的 deck + 官网专题页双产物 | 1 | presentation / website / b_system（潜在） | 观察中 | 是：当前 Guard 已指导拆分 deck 与 site 两条任务 | 若 deck+site 组合在多个产品/场景中重复出现，则进入多 scene 组合模式治理候选，可能需要单独模式文档 |
| `anti_pattern_work_report_misuse` | 试图将 work-report anti_pattern 壳用作通用周报模板 | 1 | presentation / b_system | 接近触发预警 | 需求侧意图不可接受，但当前 Guard patch 已明确禁止且可拦截 | 若未来两个周期内该模式 ≥3 次出现在真实需求里，则进入 Guard 文案增强或新 work_report candidate 模板评估队列 |

> 当前周期主要价值在于：为后续“跨周期计数与趋势判断”建立一套模式与档位的基线，后续周期可以直接在此表基础上累加计数与调整档位。

### 7.4 各模式升级判断

> 依据 `MULTI_SCENE_OBSERVATION_CYCLE.md §4` 的计数与阈值规则，并结合本周期“无新增样本”的事实，对每个模式给出升级判断：

- **`canonical_*` 四个模式（list / minimal_overlay / landing / assistant_workspace）**：
  - **结论**：继续 observation；暂不进入任何升级评估队列。
  - **理由**：
    - 仅作为主链绿色锚点，当前没有“被 Guard 误杀或结构承载吃力”的信号；
    - 不需要做 Guard 或模板层面的主动动作，只需在未来 patch 时确保不被破坏。

- **`pricing_in_homepage_shell` 模式**：
  - **结论**：继续 observation；暂不进入 template/canonical 评估队列。
  - **理由**：
    - 本周期仅有 1 条历史样本，没有新的真实任务复现该模式；
    - homepage 壳当前仍可承载该结构，未出现实际项目中“承载明显吃力”的证据；
    - 升级为独立 pricing 壳的论据不足，继续按照“累计 ≥3 条同类样本并观察结构压力”的阈值执行。

- **`dashboard_plus_assistant` 模式**：
  - **结论**：继续 observation；暂不进入 Guard 评估或组合模式治理队列。
  - **理由**：
    - 目前仅有 1 条典型样本，且 Phase 1 已给出合理的主场景判断（dashboard/overlay 为主，助手为组件）；
    - 未出现该模式在多个 scene 爆发或 stop&ask 频繁打断的情形；
    - 在计数与跨 scene 覆盖上均未达到“接近触发预警 → 正式评估”的阈值。

- **`deck_plus_site_dual_output` 模式**：
  - **结论**：继续 observation；暂不进入模板或 Phase 2 候选队列。
  - **理由**：
    - 当前仅有 1 条典型样本，但 Guard 已给出明确拆分策略（deck + site 两条任务）；
    - 尚未见到该模式在大量产品/主题上重复出现，也未对现有模板壳造成明显结构压力；
    - 更适合作为“多 scene 组合模式候选”，在未来多个周期内累积证据后再讨论治理。

- **`anti_pattern_work_report_misuse` 模式**：
  - **结论**：继续 observation；不新增 Guard 或模板评估动作。
  - **理由**：
    - Phase 1 已完成 Guard patch，将 `presentation-work-report.html` 明确标为 anti_pattern 并禁止路由使用；
    - 本周期没有新增真实需求再次提出“统一用 work-report 壳”的诉求，说明现有 Guard 在当前规模下足以应对；
    - 按阈值规则，需要在后续 1–2 个周期内观察该模式是否以 ≥3 次的频率再次出现，再决定是否进入 Guard 文案增强或新 work_report candidate 模板评估队列。

> **整体升级结论**：
> - 本周期内 **没有任何模式进入 Guard / template / Phase 2 正式评估队列**，全部模式结论均为“继续 observation”；
> - 原因不是“忘记升级”，而是：样本完全来自历史演示，无新增业务信号，距离计数与影响范围的最小升级门槛仍有明显差距。

### 7.5 回填动作清单

> 结合第 4 章与本周期样本情况，判断是否需要对各 scene 文档做新的回填或更新。

- **`WEBSITE_PHASE1_VALIDATION.md`**：
  - 本周期未新增任何与 website 相关的新样本，仅复用：
    - `website_case_landing_airline_cloud`（landing 正例）；
    - `website_case_w3_pricing_comparison_heavy`（pricing_in_homepage_shell）。
  - 二者均已在 WEBSITE 验证文档中有明确记录与结论。
  - **结论**：本周期暂无需要回填的 WEBSITE 文档更新。

- **`AI_ASSISTANT_PHASE1_VALIDATION.md`**：
  - 本周期未新增 ai_assistant 或 dashboard+assistant 新样本，仅复用：
    - `ai_assistant_case_pure_workspace`；
    - `ai_assistant_case_dashboard_plus_assistant`。
  - 两个样本均已在 AI_ASSISTANT 验证文档中记录为 W1 / 混合场景代表。
  - **结论**：本周期暂无需要回填的 AI_ASSISTANT 文档更新。

- **`PRESENTATION_PHASE1_VALIDATION.md`**：
  - 本周期未新增 presentation 样本，仅复用：
    - `presentation_case_topic_deck_plus_site`；
    - `presentation_case_work_report_template_misuse`。
  - 两者均作为 deck+site 双产物与 work_report anti_pattern 的主样本存在于 PRESENTATION 验证文档中。
  - **结论**：本周期暂无需要回填的 PRESENTATION 文档更新。

- **`PHASE1_MULTI_SCENE_REVIEW.md`**：
  - 本周期仅对既有多 scene 模式做整理，没有观察到新的、多 scene 结构性风险或模式；
  - **结论**：本周期不更新 `PHASE1_MULTI_SCENE_REVIEW.md`，保持 Phase 1 收官评估结果不变。

> **总回填结论**：
> - **本周期暂无任何新的 scene 文档或总评审文档回填动作**；
> - 原因是：仅复用历史样本进行模式级整理，并未发现需要以“新增样本形式”回写到 scene 文档或多 scene 评审的增量信息。

### 7.6 周期小结与下一周期关注点

- **三档分类在真实周期中的表现**：
  - 即便在“样本全为历史”的情况下，三档分类仍能稳定表达每个模式的当前状态：
    - 已知稳定：作为主链绿色锚点；
    - 观察中：承载潜在 Phase 2 候选与边界 tension；
    - 接近触发预警：聚焦 anti_pattern 与结构性风险。
  - 在本周期没有出现需要调整三档定义或新增档位的情况。

- **最值得持续观察的模式**：
  - `pricing_in_homepage_shell`：未来真实项目中重度 pricing 页的样本数量与结构压力；
  - `dashboard_plus_assistant`：在 b_system / ue5_overlay / website 等多 scene 中是否出现更多变体；
  - `deck_plus_site_dual_output`：是否在多个产品/主题中重复出现，演化为常规组合模式；
  - `anti_pattern_work_report_misuse`：在 Guard patch 后是否仍高频出现，暴露 Guard 文案或 scene 分工问题。

- **是否出现新的结构性风险**：
  - 本周期未引入新的真实样本，因此未识别出新的结构性风险；
  - 现有 4 个非 canonical 模式在 Phase 1 中已被充分识别并通过最小 Guard/策略加以处理，目前风险状态可控。

- **observation 机制在真实使用中是否需要轻量修正**：
  - 在“文档驱动”的首个周期中，机制本身无需调整；
  - 未来需要补充的是：
    - 在周期小结中持续维护“模式计数表”；
    - 在 observation 记录中显式使用“当前方案是否可接受 / 再出现 N 次触发何种动作”两个辅助字段，以减轻主观判断负担。

- **下一周期建议重点盯的模式与行动**：
  - 继续使用本周期的模式表与档位作为基线；
  - 在真实业务接入后，优先记录：
    - 所有命中 stop&ask 的样本；
    - 所有跨 scene 混合样本；
    - 所有涉及 anti_pattern / limited 模板误用或合理扩展的样本；
  - 在此基础上：
    - 尤其关注 `pricing_in_homepage_shell`、`dashboard_plus_assistant`、`deck_plus_site_dual_output`、`anti_pattern_work_report_misuse` 的计数与跨 scene 分布；
    - 仅在达到既定阈值且出现真实结构压力时，才将模式推入 Guard / template / Phase 2 正式评估队列。
