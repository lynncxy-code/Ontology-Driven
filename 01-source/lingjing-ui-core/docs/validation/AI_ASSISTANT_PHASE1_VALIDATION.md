# ai_assistant · Phase 1 页型验证（assistant_workspace）

> **目的**：让 `scene = ai_assistant` 从"有模板 + 有 UX spec + 有 router，但缺验证与边界治理"的状态，进入具备 **W1 级可治理能力** 的起步状态：
> - 写清当前主模板 `b-system-ai-assistant.html` 在什么前提下可以/不可以使用；
> - 用少量高价值样本澄清 `ai_assistant` vs `b_system` 的场景边界；
> - 明确下一步应优先补 Guard 还是补样本，而不是直接扩 page_type 或新增模板。

---

## 1. 验证范围与前提

- **适用场景**：`scene = ai_assistant`
- **当前核心 page_type**：
  - `page_type = assistant_workspace`（唯一主类型，承接"多轮澄清 + 规划 + 工具执行"的助手工作台）。
- **当前主模板**：
  - `examples/b-system/b-system-ai-assistant.html`
- **当前分级与使用范围（根据 TRUTH_SOURCES 与 matrix 摘要）**：
  - `grade = limited`（有限模板，不作为通用后台壳使用）；
  - `use_scope = limited`（仅在明确识别为 `ai_assistant_workspace` 任务时才可使用）；
  - `scene_coverage_matrix.yml.scene_coverage.ai_assistant.candidate_templates[*]` 中登记为兼容支持场景；
  - 受 `EXTENSION_GUARD` 中"limited 模板误用"与 `b_system`/其它 scene 边界条款约束。
- **当前 UX spec 引用**：
  - `lingjing-ux-core/examples/ux_spec_ai_assistant_workspace.yml`
    - `scene.id = ai_assistant_workspace`，名称：**AI 助手工作台**；
    - 主要目标：`summary_zh: "多轮澄清+工具执行"`；
    - 核心 zones：
      - `chat` 对话区（澄清需求、反馈进度）；
      - `plan_board` 计划/子任务区（展示与调整子任务）；
      - `exec_log` 执行日志区（工具调用摘要与详情）；
      - `result_panel` 结果区（输出总结、复制/下载等）。
- **本轮验证目标**：
  - 只验证 **scene 边界** 与 **主模板承接能力**，并补齐 W1 级文档治理；
  - **不扩 page_type**、不新增模板、不修改 router / matrix / Guard / HTML 实现。

---

## 2. 现状摘要（W0 → W1 起步）

- **已具备的资产**：
  - 有明确的 `ai_assistant` 场景登记与 `b-system-ai-assistant.html` 模板示例（在 `scene_coverage_matrix.yml` / `data/template_router.json` 中可查）；
  - UX 侧有完整的 `ai_assistant_workspace` 规格文件，清楚定义了对话区、计划区、执行日志区、结果区的职责与交互；
  - `data/task_router.json` 中已有与助手相关的任务路由（例如面向"助手工作台/多步骤自动化"的任务）；
  - `TRUTH_SOURCES.md` 中明确：`ai_assistant` 场景当前在 v3.0.0 下为 **兼容支持**，模板为 **limited**，受 `EXTENSION_GUARD` 约束。
- **当前主要缺口**：
  - 缺少专门的 **验证文档** 来沉淀 `ai_assistant` vs `b_system`/其它场景的 **边界样本**；
  - `EXTENSION_GUARD` 中尚无针对 `ai_assistant` 的专向条款，limited 模板误用主要依赖通用 Guard 与人工理解；
  - 缺少对"dashboard + assistant 混合页""list/workspace + assistant 面板"等典型高歧义场景的书面共识。
- **为什么现在适合进入 Phase 1**：
  - 模板、UX spec 与 router 已经存在，且在 TRUTH_SOURCES 中有明确分级与场景说明——不再是"只存在一个 demo HTML"；
  - ai_assistant 与 b_system 在实际业务中已经频繁共现，若不及早写清边界，有限模板被当成"万能后台壳"的风险较高；
  - website Phase 1 已跑通一套可复用流程（样本驱动 + Guard 优先 + 谨慎分化模板），适合平移到 `ai_assistant` 场景作为 W1 起步方法。

---

## 3. 任务样例一览（首批 W1 验证样本）

> 本表列出首批 6 条高价值样本，后续可在本文件中继续扩充，但 W1 阶段优先围绕"ai_assistant vs b_system/其它 scene 边界"与"limited 模板误用"展开。

| id | 用例名 | 输入描述（概括） | 预期 scene / page_type / template | 是否应 stop&ask | 备注 |
|----|--------|------------------|-----------------------------------|------------------|------|
| `ai_assistant_case_pure_workspace` | 纯助手工作台 | 用户通过对话提出复杂任务，助手澄清→规划子任务→多次工具调用→在同页呈现执行日志与结果 | `scene = ai_assistant` / `page_type = assistant_workspace` / `template = b-system-ai-assistant.html` | 否（仅风险步骤需确认） | 典型正例：AI 主导的多步骤任务执行空间，应稳定落在 ai_assistant。 |
| `ai_assistant_case_pure_b_system_workspace` | 纯 b_system 工作台 | 运营人员在列表/表单界面处理审批、编辑实体，无 AI 规划或工具链路，仅有少量帮助文案 | `scene = b_system` / （list/detail/workspace，对应 system-template-map） / **禁止使用** `b-system-ai-assistant.html` | 是（如任务表述中提到"助手"/"聊天"但实际是固定流程） | 反例对照：不应因出现"助手"文案，就把纯后台工作台误判为 ai_assistant。 |
| `ai_assistant_case_dashboard_plus_assistant` | dashboard + assistant 混合 | KPI 仪表盘 / 待办列表与一个 AI 助手面板并置，同一页既要看指标也要让助手生成分析/脚本 | 主体：`scene = b_system`（dashboard/workspace） + 嵌入 `ai_assistant` 模块；整个页面 **不应整体切换为** ai_assistant | 是 | 典型混合场景：应通过 stop&ask 拆清"谁是主角"，防止 scene 误切。 |
| `ai_assistant_case_heavy_tool_calls` | 工具调用很重的助手界面 | 助手围绕单一目标多次调用外部工具（检索 / 运行脚本 / 写入系统），执行日志丰富且需要可追溯 | `scene = ai_assistant` / `page_type = assistant_workspace` / `template = b-system-ai-assistant.html` | 否（或仅在高风险操作前 stop&ask） | 强化 ai_assistant 对"多工具/可审计执行流"的承接能力。 |
| `ai_assistant_case_limited_template_misuse` | limited 模板误用倾向 | 想把 `b-system-ai-assistant.html` 当成通用后台页壳，承载列表/表单/导航等普通功能，无 AI 主导链路 | 实际应为 `scene = b_system`，对应 list/detail/workspace 模板；`b-system-ai-assistant.html` 视为 **误用** | 是 | 用于约束 limited 模板的使用范围，防止其演化为"万能管理后台"。 |
| `ai_assistant_case_assistant_plus_cockpit_overlay` | ai_assistant + cockpit/overlay 混合 | 希望在同一视图中既有 3D cockpit/overlay 视图，又有 AI 助手解释告警 / 生成剧本 | cockpit/overlay 部分：`scene = ue5_overlay` + `b_system`；助手部分：`scene = ai_assistant`（可作为旁路入口或弹窗） | 是 | 连接 ai_assistant 与 `b_system` / `ue5_overlay` 的三方边界，不应将整个 cockpit 页视为 ai_assistant。 |

---

## 4. 逐条任务验证记录

### 4.1 `ai_assistant_case_pure_workspace` — 纯 AI 助手工作台（正例）

- **输入任务描述**：
  - "做一个 AI 助手工作台，用户通过对话提出任务，助手会先澄清需求，再规划子任务，并在同一页面里展示工具调用日志和结果。"
- **预期判定**：
  - `scene = ai_assistant`；
  - `page_type = assistant_workspace`；
  - `template = examples/b-system/b-system-ai-assistant.html`；
  - 任务流匹配 UX spec 中 `assistant_request_to_delivery` 流（澄清 → 规划 → 执行 → 复核）。
- **应命中的结构要点**：
  - 页面包含清晰分区：对话区（澄清）、任务/计划区、执行日志区、结果区；
  - 工具调用日志可按卡片方式展示，并可展开详情（对应 `tool-call-card` 行为）；
  - 结果区支持"复制/下载/再次执行"等操作，而不是简单的一条最终回复。
- **是否需要 stop&ask**：
  - 一般不需要 scene 级 stop&ask —— 需求已明确指向"助手工作台"；
  - 仅在涉及高风险工具（写库、删除、批量变更）时，按 `EXTENSION_GUARD` 中通用高风险规则进行确认。
- **是否存在 b_system / ai_assistant 混淆**：
  - 否，页面的主角是 AI 助手本身；
  - 即使助手调用的是 b_system API，场景仍归属 `ai_assistant`，而非直接暴露 b_system 的 list/detail 界面。
- **结论**：
  - 此类"多轮澄清 + 多工具执行 + 单页可追溯"的工作台，是 `ai_assistant` 场景应优先承接的典型正例；
  - `b-system-ai-assistant.html` 可以作为该类任务的主壳使用，limited 约束主要用于防止它被误用到非助手场景，而非禁止其在助手场景中反复使用。

---

### 4.2 `ai_assistant_case_pure_b_system_workspace` — 纯 b_system 工作台（反例对照）

- **输入任务描述**：
  - "设计一个运营工作台页面，运营同学每天在这里查看订单列表、审批申请、编辑基础信息，可以有搜索筛选和批量操作。"
  - 文案中可能混入"智能助手提示""快捷说明"等字样，但无真实 AI 澄清/规划/工具执行链路。
- **预期判定**：
  - `scene = b_system`；
  - `page_type` 落在 `list` / `detail` / `workspace` 组合中，由 `docs/system-template-map.md` 决定；
  - **禁止** 选择 `examples/b-system/b-system-ai-assistant.html` 作为主壳；
  - 应命中典型 B 端模板（如 `b-system-task-list-top-filters.html` 等）而非助手壳。
- **Guard / stop&ask 行为（应有）**：
  - 若任务中出现"助手/聊天/智能建议"等字样，必须补问：
    - "页面的主任务是执行固定业务流程，还是让 AI 代为规划和执行一系列任务？"
    - "用户是否通过对话与页面交互，还是主要通过按钮/表格/表单操作？"
  - 若答案指向"固定业务流程 + 表格/表单交互"，应判定为 `b_system`，并禁止使用 ai_assistant limited 模板。
- **是否存在 b_system / ai_assistant 混淆**：
  - 高风险：业务文档可能会把普通提示/FAQ 文案称为"助手"，易被误判为 ai_assistant；
  - 本样本用于明确：**有"助手"文案 ≠ ai_assistant 场景** —— 决策应以交互模式与任务主导者为准。
- **结论**：
  - 纯后台工作台需求，无论文案是否提到"助手"，都应归入 `b_system`，并使用系统场景对应模板；
  - `b-system-ai-assistant.html` 在此类需求中属于明显误用，应由 Guard 阻止。

---

### 4.3 `ai_assistant_case_dashboard_plus_assistant` — KPI dashboard + 助手并置（混合场景）

- **输入任务描述**：
  - "做一个运营驾驶舱页面，左侧是 KPI 仪表盘和告警列表，右侧放一个 AI 助手窗口，可以让助手根据当前数据生成当日巡检重点和处理建议。"
- **预期判定**：
  - 页面主体是运营驾驶舱 → `scene = b_system`（或 `ue5_overlay` + `b_system` 组合，视具体 cockpit 模式而定）；
  - AI 助手仅作为 **辅助手段** 出现在一侧，负责生成建议和说明；
  - 整个页面 **不应被整体判成** `ai_assistant`，`b-system-ai-assistant.html` 不作为此页的主壳；
  - 更合理的结构是：在 b_system cockpit 模板中嵌入助手组件/浮层，或通过入口跳转到助手工作台。
- **应触发的 stop&ask**：
  - "这个页面的主要任务是看指标、处理告警，还是通过对话驱动任务？"
  - "用户是否需要在没有助手的情况下也能完成核心操作？"
  - 若回答为"驾驶舱本身是主角，助手只是辅助"，则锁定 `scene = b_system` / `ue5_overlay` 为主。
- **是否存在 b_system / ai_assistant 混淆**：
  - 是，该类需求容易被误认为"助手工作台"，实际上主任务是 dashboard 监控和操作；
  - 若错误切到 `ai_assistant` scene，会导致 cockpit 的结构约束被忽略。
- **结论**：
  - 对于"dashboard + assistant 并置"场景，应优先视为 **b_system or ue5_overlay 主场景 + 嵌入助手模块**；
  - ai_assistant 作为"工具使用者"，不自动成为整个页面的 scene；
  - 这类场景必须 stop&ask，而不是静默将整个页型切到 ai_assistant。

---

### 4.4 `ai_assistant_case_heavy_tool_calls` — 工具调用很重的助手界面（正例）

- **输入任务描述**：
  - "做一个 AI 助手界面，帮运维工程师排查集群故障：助手会先澄清范围，然后多次调用日志检索、配置校验、健康检查等工具，并在界面中展示每一步的调用状态和结果。"
- **预期判定**：
  - `scene = ai_assistant`；
  - `page_type = assistant_workspace`；
  - `template = examples/b-system/b-system-ai-assistant.html`；
  - UX 上高度依赖 `exec_log` 与 `result_panel` 区域，强调"可追溯执行流"。
- **应命中的结构要点**：
  - 工具调用日志以时间线或卡片形式展示，包含"工具名 / 参数摘要 / 结果摘要 / 状态（成功/失败/重试）"；
  - 失败时支持重试或回退到澄清阶段（与 UX spec 中的 edge_cases 与 tracking_requirements 对齐）；
  - 对话区与计划区需要在长执行链下仍保持可用，避免日志淹没主任务。
- **是否需要 stop&ask**：
  - 一般不需要 scene 级 stop&ask：需求明确强调"助手""多次工具调用"与"结果总结"；
  - 在个别极高风险操作前，应按照通用 Guard 进行二次确认，但不影响 scene 判定。
- **是否存在 b_system / ai_assistant 混淆**：
  - 不应：虽然助手调用了很多 b_system 工具，但界面是围绕"对话驱动 + 可追溯工具流"构建，而非展示业务实体列表或表单；
  - 若仅保留工具日志而无对话/规划，则需要重新评估是否仍是 ai_assistant 场景。
- **结论**：
  - "多工具调用 + 执行日志为一等公民"的场景，是 ai_assistant 的核心优势区域，应优先落在 `assistant_workspace` + `b-system-ai-assistant.html` 上；
  - 这进一步说明：ai_assistant 与 b_system 的边界 **不是"有没有工具调用"**，而是"谁在主导任务（AI vs 用户直驱 UI）"。

---

### 4.5 `ai_assistant_case_limited_template_misuse` — limited 模板误用场景（反例）

- **输入任务描述**：
  - "希望复用 `b-system-ai-assistant.html` 的布局来做一个通用管理后台首页，上面放导航、若干数据卡片和常用操作入口，不一定需要真正的 AI 对话和工具链路。"
- **预期判定**：
  - 该需求本质上是 `scene = b_system` 的仪表盘/门户页；
  - 页面主任务是"导航 + 入口聚合 + 数据概览"，而非"对话驱动的多步骤任务"；
  - 因此：
    - `b-system-ai-assistant.html` 应被视为 **limited 模板误用**；
    - 应改用 b_system 场景下的 dashboard/workspace 模板族。
- **应触发的 Guard / stop&ask**：
  - "是否存在真实的 AI 对话与多步骤规划/执行流？如果去掉'助手'文案，这个页面是否依然成立？"
  - "用户是否主要通过按钮/卡片进行固定操作，而不是与助手对话？"
  - 若回答为"只是想借用布局，看起来像有助手，但没有真正的 AI 任务流"，则必须阻止使用 limited 模板。
- **是否存在 b_system / ai_assistant 混淆**：
  - 是，本样本直接针对"把助手壳当作通用后台壳"的典型误用；
  - 若不加约束，`b-system-ai-assistant.html` 很快会演变成"万能管理后台"模板，削弱其作为 ai_assistant 真值源的意义。
- **结论**：
  - `b-system-ai-assistant.html` 虽然在文件路径上归属 `b-system` 目录，但在真值源中被标记为 `scene = ai_assistant`, `grade = limited`；
  - 在 W1 阶段，应把"limited 模板误用"视为高风险场景，并通过 Guard 文档明确禁止，将其重定向回标准 b_system 模板族。

---

### 4.6 `ai_assistant_case_assistant_plus_cockpit_overlay` — ai_assistant + cockpit/overlay 混合页

- **输入任务描述**：
  - "需要一个'数字孪生运维助手'界面，左侧是 3D cockpit/overlay 视图，展示设备状态和告警，右侧是 AI 助手对话，可以让助手解释告警原因、生成处理剧本并调用后台接口。"
- **预期判定**：
  - 3D cockpit/overlay 视图属于 `scene = ue5_overlay` + `b_system` 的组合（参见 `TRUTH_SOURCES.md` 与 `docs/ue5-template-map.md`）；
  - AI 助手部分属于 `scene = ai_assistant`；
  - 视业务决策，可以采用：
    - 方案 A：以 cockpit 视图为主（`ue5_overlay` + `b_system` 页），助手作为浮层/侧栏组件；
    - 方案 B：以助手工作台为主（`ai_assistant` 页），通过嵌入只读 cockpit 画面或跳转链接与后台视图协同；
  - 无论哪种方案，**都不应把整个 cockpit 页直接归为 ai_assistant scene**。
- **应触发的 stop&ask**：
  - "主任务是盯 3D cockpit 并操作后台，还是通过对话驱动自动化处理？"
  - "用户是否需要在没有助手的情况下也能完成核心操作？"
  - "3D 视图是只读展示，还是包含复杂 HUD/操作面板？"
- **是否存在 b_system / ai_assistant / ue5_overlay 混淆**：
  - 是，这是三方场景的典型交叉点；
  - 若不通过 Guard 拆清主从关系，很容易出现"用 ai_assistant 壳承载复杂 cockpit UI"的错误。
- **结论**：
  - cockpit/overlay 与 ai_assistant 的关系应被视为"合作方"，而非"谁吞掉谁"：
  - cockpit/overlay 负责可视化与实时操作；
  - ai_assistant 负责解释、规划与调用自动化脚本；
  - 在 W1 阶段，应通过文档明确这类混合任务必须 stop&ask，按主任务拆分为 2–3 个协同页面，而非强行合为一个 scene。

---

## 5. 阶段性结论（W1 视角）

- **ai_assistant 场景当前具备的最小可治理能力**：
  - 有独立的 UX spec（`ai_assistant_workspace`），清晰界定了对话/计划/执行日志/结果四大区；
  - 有对应的 limited 模板 `b-system-ai-assistant.html` 作为起步壳，且在 TRUTH_SOURCES/matrix 中登记；
  - 通过本文件的 6 条样本，初步厘清了：
    - 典型 `assistant_workspace` 正例（4.1, 4.4）；
    - 纯 b_system 工作台与 dashboard 混合任务（4.2, 4.3）；
    - limited 模板误用与 cockpit 混合边界（4.5, 4.6）。
- **当前模板是否足以作为 assistant_workspace 的主承接壳**：
  - 对于"对话 + 计划 + 工具执行 + 结果回顾"的典型助手工作台，`b-system-ai-assistant.html` 在结构上是足够的；
  - 它能够承载：
    - 多轮对话与澄清区；
    - 子任务/计划面板；
    - 工具调用日志与错误重试；
    - 结果产物展示与再利用；
  - 在样本所覆盖的范围内，尚未出现"必须完全重写壳结构才能完成任务"的强证据。
- **当前 Guard 缺口（以文档形式记录，不修改 Guard 文件）**：
  - 缺少显式的 `ai_assistant` 章节，用于：
    - 明确"有工具调用 ≠ ai_assistant"，避免将所有工具驱动页面都归入助手场景；
    - 明确"有'助手/聊天'文案 ≠ ai_assistant"，避免纯 b_system 工作台被误判；
    - 约束 `b-system-ai-assistant.html` 的 limited 使用范围，禁止其成为通用后台壳。
  - 对"dashboard + assistant 并置""cockpit + assistant""list/workspace + assistant 侧栏"等混合任务，目前仅有 website/b_system/ue5_overlay 视角下的 Guard 条款，缺少 ai_assistant 视角的配套说明；
  - 对"助手仅做 FAQ/说明"的轻量场景，尚未明确应优先落在 b_system 页面内的说明模块，而非升级为 ai_assistant scene。

---

## 6. W1 级边界结论（ai_assistant vs b_system）

> 本节回答四个关键问题：
> 1）什么任务应优先判为 `ai_assistant`；
> 2）什么任务虽带"助手/聊天"，但本质上仍是 `b_system`；
> 3）什么混合任务应优先 stop&ask；
> 4）为什么 `b-system-ai-assistant.html` 虽然重要，但仍必须保持 `use_scope = limited`。

### 6.1 应优先判为 ai_assistant 的任务

- **核心特征**（满足多数即可）：
  - 任务以 **自然语言对话** 为主要入口，用户通过"说/写需求"而非点选固定流程开始；
  - 过程强调"**澄清 → 规划 → 执行 → 复核**"的闭环，而非一步到位的表单/操作；
  - 存在 **多次工具调用**，且每次调用需要被清晰记录、审计和回溯；
  - 助手需要根据中途反馈调整计划（增删子任务、改变顺序）；
  - 结果多为文稿/报告/代码片段/结构化输出，而非单一业务实体状态的变化。
- **典型例子**：
  - 故障排查助手（4.4）；
  - 文稿/方案自动生成助手；
  - "帮我梳理/拆解/排期"类多步骤规划任务；
  - 需要跨系统协调操作的自动化剧本（助手负责 orchestration）。

### 6.2 虽有"助手/聊天"元素，但本质仍是 b_system 的任务

- **核心特征**：
  - 页面主任务是 **执行预定义业务流程**：审批、录入、编辑、列表筛选、处理工单等；
  - 即使没有助手，用户仍可通过按钮/表单/列表完成全部核心操作；
  - 所谓"助手"仅提供：
    - 表单填写提示或校验说明；
    - 固定 FAQ/帮助文案；
    - 对当前页面数据的简单解释（例如"该状态表示… "），而不负责规划/执行任务流；
  - 无多轮澄清/多工具调用/计划看板等结构。
- **判定规则**：
  - 此类页面应始终归入 `scene = b_system`，在其中嵌入 **轻量助手组件**/帮助模块，而非切换 scene 为 `ai_assistant`；
  - 使用的模板应来自 `docs/system-template-map.md` 中的 list/detail/workspace 壳；
  - 若出现"仅为了使用助手壳而把工作台搬入 `b-system-ai-assistant.html`"的倾向，应视为误用（见 4.2, 4.5）。

### 6.3 混合任务（dashboard / cockpit / workspace + assistant）应如何处理

- **必须优先 stop&ask 的情况**：
  - 需求同时提到：
    - dashboard/cockpit/工作台 UI；
    - AI 助手用于解释数据、生成建议或触发操作；
  - 需求试图在 **同一页面、同一首屏** 完成监控/操作 + 对话/规划两种任务。
- **W1 建议的处理方式**：
  - **先判主场景，再决定助手以何种形式出现**：
    - 若主任务是盯盘/操作 → 主场景为 `b_system` / `ue5_overlay`，助手作为组件/浮层存在；
    - 若主任务是通过对话 orchestrate 一系列后台任务 → 主场景为 `ai_assistant`，dashboard 仅以嵌入视图或链接形式存在；
  - 对于多方都"很重要"且难以抉择的情况，应拆分为 2–3 个任务/页面，而非强行压缩为一页。

### 6.4 为什么 `b-system-ai-assistant.html` 必须保持 limited use_scope

- **原因 1：避免"万能后台壳"回潮**：
  - 若取消 limited 约束，该模板极易被用于各种后台首页/工作台，仅因其"看起来更现代"；
  - 这会模糊 `ai_assistant` 与 `b_system` 的边界，使审计与治理再次回到"看样式猜场景"的不稳定状态。
- **原因 2：保护 ai_assistant 的真值源质量**：
  - 作为 `assistant_workspace` 的主壳，它需要保持"对话 + 计划 + 执行日志 + 结果区"的稳定骨架；
  - 若混入大量不具备这些结构的使用场景，任何基于样本学习的代理都会误判"助手页可以是什么都行"。
- **原因 3：Phase 1 的复杂度控制**：
  - 当前 `ai_assistant` 仍处于 W1 初期，只完成了一轮边界与承接力验证；
  - 在 Guard 未完善、样本未充分的前提下放宽 use_scope，只会引入更多误用样本，反而难以治理。

---

## 7. 观察项与下一步建议（不越级推进）

### 7.1 当前仍在观察、暂不下硬结论的点

- **是否需要更多细分的助手页型**：
  - 当前仅存在 `assistant_workspace` 一种 page_type；
  - 未来是否需要区分"轻量问答助手页""多工具编排工作台""review/回顾页"等子类型，尚缺乏足够真实样本；
  - 在此之前，不建议新增 page_type。
- **助手与 cockpit/dashboard 深度融合的真实需求规模**：
  - 目前仅有少量"cockpit + assistant""dashboard + assistant"类设想样本；
  - 这些场景下的最佳结构（嵌入 vs 分页 vs 多 scene 组合）仍需通过真实项目验证；
  - 在证据不足时，应坚持"主场景优先 + 拆任务优先"的策略，而非创造新的复杂混合模板。

### 7.2 下一轮若继续推进，Guard vs 样本的优先级

- **优先建议：补 Guard 条款，再继续扩样本**：
  - 本文件已经为 `ai_assistant` 提供了首批高价值样本与 W1 边界结论；
  - 下一轮若继续推进，应优先在 `EXTENSION_GUARD.md` 中：
    - 增补 `ai_assistant` 专向条款，固化第 6 节中的边界判断；
    - 明确 limited 模板误用的禁止条件与 stop&ask 提示语；
    - 针对"dashboard + assistant""cockpit + assistant"给出标准拆分建议；
  - 在 Guard 初版落地后，再根据真实项目继续补充混合场景样本，用于验证 Guard 的有效性。

### 7.3 在什么证据不足的情况下，不应直接进入 W2 / 模板分化

- **不应触发 W2 / 模板分化的典型情况**：
  - 仅凭个别想象中的复杂助手界面，就主观认为需要新的助手模板；
  - 真实项目中尚未出现稳定、高频、结构显著不同的助手页型模式；
  - 当前助手工作台模板（在合理布局调整后）仍然可以承载主要需求，没有出现严重的承载困难；
  - Guard 尚未覆盖 `ai_assistant` 场景的关键边界问题，样本也尚未充分回归。
- **进入 W2 的前置信号（示意）**：
  - 在多项目中反复出现"仅需要轻量问答，无需执行日志/计划板"的 stable 模式；
  - 或者出现"多用户协同/多会话管理/复杂回溯"等明显超出当前模板结构的典型模式；
  - 审计中频繁出现"模板结构被严重改造""关键 zone 丢失"等信号，表明现有壳已不适于承载所有助手需求。

### 7.4 当前是否建议维持单一 page_type：assistant_workspace

- **结论**：
  - 在 W1 阶段，**建议维持单一 `page_type = assistant_workspace`**：
    - 便于所有助手相关样本在同一类型下积累，形成稳定结构共识；
    - 避免过早将"问答式助手""多工具助手""review 页"等概念拆散，导致 router 与审计复杂度上升；
    - 为后续基于真实样本的 W2 分化保留空间。
  - 任何"想新增助手子类型/新模板"的诉求，应先回到本文件：
    - 检查是否可以通过现有模板 + 布局调整承载；
    - 若不能，再按"样本驱动 + 审计信号"的方式，正式立项评估。

---

## 8. Guard 建议稿（准 EXTENSION_GUARD 条文）

> 本节将前文边界结论整理为面向 `EXTENSION_GUARD.md` 的"准 Guard 条文"，方便后续直接迁移。在真正改 Guard 之前，这些条款仅作为文档级协议，不具备执行力。

### 8.1 ai_assistant vs b_system

- **规则 A1：带"助手/聊天"字样但主任务为固定业务流程**
  - **触发条件**：
    - 设计请求或任务描述中同时出现：
      - "助手/智能助手/聊天"等字样；
      - 以及"审批/录入/编辑/列表/工单/批量操作"等固定业务流程关键词。
  - **推荐补问**：
    - Q1：`"页面的主任务是执行固定业务流程（审批/录入/处理工单），还是让 AI 代为规划和执行一系列任务？"`
    - Q2：`"如果移除对话/助手模块，当前页面是否仍然可以完成核心工作？"`
  - **推荐判定方向**：
    - 若答案偏向"固定流程 + 按钮/表单/列表即可完成"，则：
      - `scene = b_system`；
      - `page_type ∈ {list, detail, workspace}`（参考 `docs/system-template-map.md`）；
      - **禁止** 使用 `b-system-ai-assistant.html` 作为主壳。
  - **不应静默决策的原因**：
    - 业务文档经常把普通提示/说明叫做"助手"，若不 stop&ask，极易将纯后台页面误判为 `ai_assistant`，破坏场景边界与模板真值。

- **规则 A2：有多轮澄清 + 计划 + 多工具调用的助手工作台**
  - **触发条件**：
    - 任务描述中包含下列要素中的多数：
      - 用户通过自然语言对话发起需求；
      - 助手需要"澄清/追问/确认范围"；
      - 页面上存在"任务/子任务列表/计划板"等结构；
      - 助手会调用多个不同工具，并需要展示调用日志与状态；
      - 结果以报告/方案/脚本/总结为主，而非单一实体状态变更。
  - **推荐补问**：
    - Q1：`"用户是主要通过对话来驱动整个任务，还是主要依赖按钮/表单？"`
    - Q2：`"是否需要在页面中清晰看到每次工具调用的历史与结果？"`
  - **推荐判定方向**：
    - 若对话 + 计划 + 多工具调用 + 结果回顾是核心体验，则：
      - `scene = ai_assistant`；
      - `page_type = assistant_workspace`；
      - `template = b-system-ai-assistant.html`（limited 模板，见 C 组规则）。
  - **不应静默决策的原因**：
    - 该场景与"带说明文案的 b_system 工作台"在表象上可能相似，需要通过补问确认是否存在完整的助手任务流。

- **规则 A3：dashboard / workspace + assistant 混合页的主场景判断**
  - **触发条件**：
    - 同一页面需求中同时包含：
      - dashboard/cockpit/工作台视图（KPI、告警、列表等）；
      - AI 助手模块，用于解释数据或生成建议。
  - **推荐补问**：
    - Q1：`"这个页面在没有 AI 助手的情况下，是否仍然需要存在？核心价值是什么？"`
    - Q2：`"用户更依赖仪表盘/列表本身，还是主要通过与助手对话来完成任务？"`
  - **推荐判定方向**：
    - 若主任务是"盯盘/操作后台"，则：
      - `scene = b_system`（或与 `ue5_overlay` 组合，视 cockpit 类型而定）；
      - 助手模块作为组件/浮层/侧栏存在；
      - 页面整体 **不得** 改为 `scene = ai_assistant`。
    - 若主任务是"通过对话 orchestrate 多个后台步骤"，则：
      - `scene = ai_assistant`；
      - dashboard/列表仅作为嵌入视图或跳转入口存在。
  - **不应静默决策的原因**：
    - 若静默按"谁看起来更酷"选择 scene，很容易把 cockpit/dashboard 场景错误吸入 ai_assistant，导致系统模板与壳约束失效。

### 8.2 ai_assistant vs ue5_overlay

- **规则 B1：3D cockpit/overlay + 助手的三方边界**
  - **触发条件**：
    - 需求中出现 "3D cockpit / overlay / 数字孪生视图" 与 "AI 助手解释告警/生成剧本/触发操作" 同时存在。
  - **推荐补问**：
    - Q1：`"主视图是否为 3D cockpit/overlay，包含复杂 HUD/控制面板？"`
    - Q2：`"用户主要是在 3D 视图中操作，还是通过对话让助手代为执行？"`
    - Q3：`"是否需要在没有助手的情况下，也提供完整的 cockpit 操作能力？"`
  - **推荐判定方向**：
    - 若 cockpit/overlay 是主视图，且需要独立操作能力，则：
      - 主场景：`scene = ue5_overlay` + `b_system`（参见 `ue5-template-map` 与 system-template-map）；
      - 助手：`scene = ai_assistant`，以浮层/侧栏/弹窗方式嵌入或通过入口跳转；
      - 整个页面 **不得** 直接标记为 `scene = ai_assistant`。
    - 若对话 orchestrate 明显成为主线（例如 cockpit 只是只读画面或辅助上下文），则可以考虑：
      - 主场景：`scene = ai_assistant`；
      - 3D 视图作为嵌入视图/预览，不承担完整 cockpit 职责。
  - **不应静默决策的原因**：
    - `ue5_overlay` 场景对 HUD/层级/操作模式有严格约束，若静默切到 `ai_assistant` 会绕开这些约束，导致 cockpit 类页面失控。

- **规则 B2：官网/营销 + cockpit + 助手的多 scene 拆分**
  - **触发条件**：
    - 需求中同时出现 website 式营销叙事、3D cockpit 交互视图以及 AI 助手模块。
  - **推荐补问**：
    - Q1：`"是否希望同一个页面同时承担对外营销介绍 + 实时 cockpit 操作 + 对话式助手？"`
    - Q2：`"是否接受拆分为官网页 + cockpit 工作台 + 助手工作台三个页面，通过导航/入口串联？"`
  - **推荐判定方向**：
    - 高度混合的需求应被拆分为：
      - `scene = website`：营销/方案介绍页；
      - `scene = ue5_overlay` + `b_system`：实际 cockpit/运维界面；
      - `scene = ai_assistant`：助手工作台（可链接到 cockpit/后台操作）。
  - **不应静默决策的原因**：
    - 若不拆分，极易出现"万能 cockpit/官网/助手页"，任何 Guard 都难以有效约束结构与职责。

### 8.3 limited 模板误用防护（`b-system-ai-assistant.html`）

- **规则 C1：仅为"好看"而想借用助手壳**
  - **触发条件**：
    - 需求描述类似："想用助手布局做一个后台首页/运营看板，但暂时不需要真正的 AI 对话或多步骤执行。"
  - **推荐补问**：
    - Q1：`"如果去掉助手/对话区，这个页面是否仍然完整、合理？"`
    - Q2：`"是否存在多轮澄清 + 任务规划 + 多次工具调用 + 执行结果回顾？"`
  - **推荐判定方向**：
    - 若答案为"去掉助手照样成立""没有完整助手任务流"，则：
      - `scene = b_system`；
      - 选择 list/detail/workspace/dashboard 模板族；
      - 将"使用 `b-system-ai-assistant.html`"标记为 **limited 模板误用**，给出替代模板建议。
  - **不应静默决策的原因**：
    - 静默接受会直接把 limited 模板演化为"万能后台壳"，从根本上破坏 ai_assistant 真值源。

- **规则 C2：轻量 FAQ/说明型"助手"组件**
  - **触发条件**：
    - 页面仅需要一个 FAQ/说明/帮助提示模块，可能被命名为"助手气泡""小助手"等；
    - 无对话历史、任务规划、工具日志等结构需求。
  - **推荐补问**：
    - Q1：`"这个'助手'是否需要记忆多轮对话和任务历史？"`
    - Q2：`"是否需要在页面中展示工具调用日志和执行结果？"`
  - **推荐判定方向**：
    - 若只是静态说明或少量建议：
      - 仍归属 `scene = b_system`（或其他主场景）；
      - 使用普通提示/帮助组件，不进入 `ai_assistant` 场景；
      - 不使用 `b-system-ai-assistant.html`。
  - **不应静默决策的原因**：
    - 静默按"只要有聊天泡泡就是 ai_assistant"，会将大量轻量帮助用例误吸入助手场景，造成样本污染。

- **规则 C3：对话 + 工具日志 + 计划板齐备时才允许使用 limited 模板**
  - **触发条件**：
    - 同时满足：
      - 需要对话区；
      - 需要任务/计划板或子任务列表；
      - 需要工具调用日志与执行结果区。
  - **推荐补问**：
    - Q1：`"是否明确需要一个区域专门展示每次工具调用的历史和状态？"`
    - Q2：`"是否需要在界面中看到任务/子任务的结构化列表？"`
  - **推荐判定方向**：
    - 若回答为"是"，且整体任务流符合 6.1 所述特征，则：
      - 可以使用 `b-system-ai-assistant.html` 作为 `assistant_workspace` 主壳；
      - 同时标记本次使用为 **limited 模板的合规使用**。
  - **不应静默决策的原因**：
    - 需要明确合规使用的下界，避免 Guard 只会"禁止"，却没有正例锚点可供审计复核。

---

## 9. Guard 回归样本（补充）

> 本节补充 5 条专门用于验证第 8 节 Guard 建议是否足够的样本，重点覆盖：
> - 带聊天框但本质仍是 `b_system` 的页面；
> - 典型 `ai_assistant` 主工作台；
> - cockpit/overlay + assistant 混合场景；
> - limited 模板误用；
> - dashboard + assistant 并置但主任务不是对话 orchestrate。

### 9.1 `guard_case_bsystem_with_chatbox` — 含聊天框的审批工作台

- **输入描述**：
  - "设计一个审批工作台页面，主体是待审批列表和详情面板，右下角有一个小聊天框，运营可以在里面向'审批助手'咨询规则解释，但不会通过聊天触发真实审批操作。"
- **预期 scene / page_type / template**：
  - `scene = b_system`；
  - `page_type = list + detail` 或 `workspace`（按 system-template-map 选择）；
  - **禁止** 使用 `b-system-ai-assistant.html`。
- **是否应 stop&ask**：
  - 是，应命中规则 A1 / C2：
    - 补问"如果去掉聊天框，这个页面是否仍然成立？"等。
- **对应 Guard 建议命中情况**：
  - 命中 A1（带助手文案但主任务为固定业务流程）；
  - 命中 C2（轻量 FAQ/说明型助手组件）。
- **结论**：
  - Guard 应将该页面稳定判为 `b_system`，只在后台模板内嵌入说明型"助手气泡"，不进入 `ai_assistant` 场景，也不使用 limited 助手壳。

---

### 9.2 `guard_case_pure_ai_workspace_minimal_ui` — 界面极简但任务流完备的助手工作台

- **输入描述**：
  - "做一个极简 AI 助手工作台界面，只有对话区和一个侧边栏，侧边栏展示当前子任务列表和最近几次工具调用记录，不需要复杂导航或仪表盘。"
- **预期 scene / page_type / template**：
  - `scene = ai_assistant`；
  - `page_type = assistant_workspace`；
  - `template = b-system-ai-assistant.html`（或其精简变体）。
- **是否应 stop&ask**：
  - 建议进行一次轻量确认（规则 A2/C3）：
    - 确认是否存在完整的对话 + 任务规划 + 工具日志链路。
- **对应 Guard 建议命中情况**：
  - 命中 A2（多轮澄清 + 计划 + 多工具调用的助手工作台）；
  - 命中 C3（合规使用 limited 模板）。
- **结论**：
  - 即使 UI 极简，只要任务流符合 `assistant_workspace` 特征，Guard 应允许使用 `ai_assistant` 场景与 limited 助手模板，不应因为"没有仪表盘"而错误下沉到 `b_system`。

---

### 9.3 `guard_case_cockpit_with_assistant_sidecar` — cockpit 主视图 + 助手侧栏

- **输入描述**：
  - "做一个设备监控 cockpit 页面，中间是 3D 设备视图和实时告警列表，右侧有一个助手侧栏，可以根据当前选中的告警给出解释和处理建议。"
- **预期 scene / page_type / template**：
  - 主体：`scene = ue5_overlay` + `b_system`（按 ue5-template-map/system-template-map 决定具体模板）；
  - 助手：`scene = ai_assistant`，以组件/浮层形式存在；
  - 整页 **不得** 设为 `scene = ai_assistant`。
- **是否应 stop&ask**：
  - 必须，命中规则 B1/A3：
    - 补问 cockpit 是否需要在无助手时仍完整工作；
    - 确认主任务是盯盘/操作，还是对话 orchestrate。
- **对应 Guard 建议命中情况**：
  - 命中 B1（三方边界）；
  - 命中 A3（dashboard/workspace + assistant 混合页的主场景判断）。
- **结论**：
  - Guard 应将该页面稳定归为 `ue5_overlay` + `b_system` 主场景，助手仅作为附属解释层存在，避免 cockpit 被错误划入 `ai_assistant`。

---

### 9.4 `guard_case_assistant_shell_misuse_admin_home` — 误用助手壳的后台首页

- **输入描述**：
  - "做一个后台首页，顶部是导航条，中间是几个统计卡片和快捷入口，没有对话需求，只是想复用 `b-system-ai-assistant.html` 的布局让页面显得更现代。"
- **预期 scene / page_type / template**：
  - `scene = b_system`；
  - `page_type = dashboard` 或 `workspace`；
  - **不得** 使用 `b-system-ai-assistant.html`。
- **是否应 stop&ask**：
  - 必须，命中规则 C1：
    - 补问"去掉助手后页面是否仍然成立""是否存在多轮澄清 + 任务规划 + 工具日志"等。
- **对应 Guard 建议命中情况**：
  - 命中 C1（仅为"好看"而想借用助手壳）。
- **结论**：
  - Guard 应明确给出"limited 模板误用"提示，并推荐改用 `b_system` dashboard 模板，防止助手壳被当作通用后台页壳。

---

### 9.5 `guard_case_dashboard_with_assistant_insights` — dashboard 主场景 + 助手洞察

- **输入描述**：
  - "做一个运营 dashboard，核心是关键 KPI 图表和告警列表，页面中有一个'AI 洞察'面板，用于总结当前周期的重点问题和建议。"
- **预期 scene / page_type / template**：
  - `scene = b_system`；
  - `page_type = dashboard`；
  - 使用系统场景 dashboard 模板，AI 洞察面板作为模块嵌入；
  - 无需使用 `b-system-ai-assistant.html`，也不视为 `scene = ai_assistant`。
- **是否应 stop&ask**：
  - 应命中规则 A3/C2：
    - 补问主任务是什么、是否需要完整助手任务流。
- **对应 Guard 建议命中情况**：
  - 命中 A3（dashboard + assistant 混合）；
  - 命中 C2（轻量说明型助手组件）。
- **结论**：
  - Guard 应确保该类"dashboard + 洞察"页面稳定落在 `b_system` 场景，避免被"AI 洞察"文案错误升级为 `ai_assistant`。

---

## 10. Guard 落地准备度判断

- **当前已具备的 Guard 设计基础**：
  - 有 website Phase 1 的 Guard 经验作为参照（scene 优先、混合诉求拆任务、样本驱动）；
  - `ai_assistant` 侧已经通过第 4–6 节样本与边界结论，明确了：
    - 典型助手工作台 vs 纯后台工作台；
    - dashboard / cockpit + assistant 混合场景的主从关系；
    - limited 模板的合规使用与误用场景；
  - 第 8 节给出了结构化的"触发条件 + 推荐补问 + 推荐判定方向 + 不应静默决策的原因"，可以较直接迁移到 `EXTENSION_GUARD.md`。
- **仍在观察但不阻碍 Guard 初版落地的点**：
  - 助手与 cockpit/dashboard 深度融合的真实规模仍有限，后续可能需要在更多样本基础上微调 B 组规则；
  - 是否需要为"轻量问答助手页""review/回顾页"等未来潜在子类型预留更细粒度条款，目前样本不足，以通用规则覆盖即可。
- **判断**：
  - 从 W1 治理角度看，**当前 ai_assistant 的边界规则已经足够成熟，可以进入下一步：在不改实现的前提下，起草并评审 `EXTENSION_GUARD.md` 中的 ai_assistant 章节修改方案。**
  - Guard 落地时应注意：
    - 先按本文件第 8 节条款写出 Guard 文本草案；
    - 再用本文件第 3、4、9 节的样本做一轮小规模回归，确认 Guard 能正确触发与判定；
    - 保持 limited 模板约束不放松，直至未来 W2 分化有充分样本支撑。

> **W1 总结（一句话）**：在不修改实现的前提下，`ai_assistant` 通过首版验证文档、6 条核心边界样本和一组 Guard 建议 + 回归样本，已经从"兼容支持"升级为具备 **可治理 W1 起步能力** 的场景 —— 边界协议已清晰到可以进入 Guard 文本落地阶段，但在真正改动 `EXTENSION_GUARD.md` 前，仍建议以本文件作为唯一的 ai_assistant 边界真值源进行人工复核与迭代。

---

## 11. EXTENSION_GUARD patch 方案（ai_assistant 挂接建议）

> 本节在不直接修改 `EXTENSION_GUARD.md` 的前提下，给出 ai_assistant 相关条款的挂接方案、拟新增条目清单、最小改动策略与回归检查清单，作为 Guard 执行轮的设计蓝本。

### 11.1 EXTENSION_GUARD 现状结构与挂接点

- **当前整体结构（摘要）**：
  - `§1 何时必须停下来问人（stop & ask）`
    - `§1.1 Scene / Type / Mode 不明确`（含 `b_system` vs `website`、`b_system` vs `ue5_overlay`）；
    - `§1.2 System 类型边界不清`（list vs dashboard vs detail 等）；
    - `§1.3 UE5 Mode / 驾驶舱边界不清`；
    - `§1.4 跨业务域或跨场景混合`；
    - `§1.5 需要使用 limited 模板或特殊角色模板`（已提到 `b-system-ai-assistant.html` 作为"非当前主线场景的 limited 模板"）；
    - `§1.6 新增多个关键模块可能导致 Level 升级`；
    - `§1.7 website 页型边界不清（landing / feature / pricing）`。
  - `§2 何时必须复审 Level（review Level）`
    - 仅覆盖 `b_system` 与 `ue5_overlay` 的 Level 升级情形。
  - `§3 何时禁止自动扩展（forbid auto extension）`
    - `§3.1–3.3`：Mode 5 / engine_test / demo 模板等；
    - `§3.4 未经确认使用 limited 模板作为通用解法`（已经列出 `b-system-ai-assistant.html` 这类 limited 模板，但暂未细化 ai_assistant 规则）；
    - `§3.5–3.10`：b_system 壳、ue5 overlay 各 Mode 壳的限制与误用。
- **现有与 ai_assistant 强相关的节点**：
  - `§1.5`：首次点名 `examples/b-system/b-system-ai-assistant.html`，但只从"limited 模板"角度约束；
  - `§1.1`、`§1.4`：已经有 scene 边界类 stop&ask（主要是 b_system vs website / ue5_overlay），未来可在此处挂上 ai_assistant 的分支；
  - `§3.4`：限定 limited 模板不能作为通用解法，是 ai_assistant limited 防误用的天然挂接点。
- **推荐挂接方式（保持结构最小扰动）**：
  - 保持 `EXTENSION_GUARD` 的三大章节结构不变，只做"**在现有骨架下追加 ai_assistant 分支**"：
    - 在 `§1` 中新增一个小节 `§1.8 ai_assistant 场景相关 stop&ask`，承接本文件 `§8.1 + §8.2` 的规则 A1–A3、B1–B2；
    - 在 `§1.5` 的 limited 模板列表中，保留 `b-system-ai-assistant.html`，并补一句"其使用需遵守 §1.8 / §3.11 中的 ai_assistant 专向条款"；
    - 在 `§3` 底部新增 `§3.11 ai_assistant limited 模板误用`，承接规则 C1–C3 的"禁止误用"部分；
    - `§2` 先暂不引入 ai_assistant 的 Level 升级条款，待未来出现更明显的模板承载压力再评估。
  - 这种挂接方式的优点：
    - 不改动现有 b_system / ue5_overlay 条目顺序，仅在末尾追加 ai_assistant 分支；
    - limited 模板相关规则仍然集中在 `§1.5 + §3.4 + §3.11`，便于后续审计与维护；
    - scene 边界类 stop&ask（website / ai_assistant / b_system / ue5_overlay）被统一放在 `§1` 下，足够一致。

### 11.2 拟新增 Guard 条目清单与推荐位置

> 下面按"拟新增条目 → 对应 Guard 章节位置 → 引用本文件中哪个规则组"给出 patch plan。

- **条目 1：ai_assistant 场景 stop&ask 总则**
  - **位置**：`EXTENSION_GUARD §1` 下新增小节 `§1.8 ai_assistant 场景相关 stop&ask`。
  - **内容来源**：本文件 `§8.1` 规则 A1–A3。
  - **条目结构建议**：
    - `§1.8.1 带"助手/聊天"字样但主任务为固定业务流程`（A1）；
    - `§1.8.2 多轮澄清 + 计划 + 多工具调用的助手工作台`（A2）；
    - `§1.8.3 dashboard / cockpit + assistant 混合页主场景判断`（A3）。
  - **wording 调整建议**：
    - 延续现有 Guard 行文风格，统一使用"不得静默决策，应补问……""推荐判定为 scene = ……"的句式；
    - 在条文中显式引用 `task_router` / `system-template-map`，与原有 b_system 条款保持一致口径。

- **条目 2：ai_assistant vs ue5_overlay 三方边界**
  - **位置**：可作为 `§1.8` 的子条目，或在 `§1.3 UE5 Mode / 驾驶舱边界不清` 内新增"ai_assistant 参与时的补充说明"。推荐方案：
    - 在 `§1.8` 中新增：
      - `§1.8.4 3D cockpit/overlay + 助手的三方边界`（B1）；
      - `§1.8.5 官网 + cockpit + 助手的多 scene 拆分`（B2），并在文中交叉引用 `§1.7 website 页型边界不清`。
  - **内容来源**：本文件 `§8.2` 规则 B1、B2。
  - **wording 调整建议**：
    - 保持与 `§1.3` 一致的 Mode / cockpit 术语；
    - 在 B2 中强调"应拆分为 website + ue5_overlay + ai_assistant 三个 scene"，并提醒按各自 scene 的 Guard 执行 stop&ask。

- **条目 3：limited 模板误用防护（ai_assistant 专向）**
  - **位置**：
    - 在 `§1.5` 中，保留原有 limited 模板列表，将 `b-system-ai-assistant.html` 的说明改为：
      - "`examples/b-system/b-system-ai-assistant.html`（`scene = ai_assistant`, `grade = limited`，使用前需遵守 §1.8 / §3.11）"；
    - 在 `§3.4 未经确认使用 limited 模板作为通用解法` 后，新增 `§3.11 ai_assistant limited 模板误用`：
      - 集中说明"仅为好看借壳""FAQ/说明型助手组件""合规使用的下界"等内容。
  - **内容来源**：本文件 `§8.3` 规则 C1–C3。
  - **条目结构建议**：
    - 在 `§3.11` 内部使用与 3.7/3.8 类似结构：
      - 概述：`b-system-ai-assistant.html` 在 `scene = ai_assistant` 中为 limited；
      - 禁止情形：
        - 需求主任务为后台首页/工作台，去掉助手仍完全成立；
        - "助手"仅为 FAQ/说明/提示，不存在多轮对话 + 计划 + 工具日志；
      - 允许情形（引用 C3）：
        - 同时有对话区 + 计划板 + 工具日志 + 结果区，且符合 `assistant_workspace` 流程。

- **条目 4：scope 文案微调**
  - **位置**：`EXTENSION_GUARD` 文件开头 `> 范围` 说明（当前为"仅适用于 Phase 1 的 b_system 与 ue5_overlay 场景"）。
  - **建议改动**：
    - 调整为类似：
      - "范围：当前 Phase 1 **主要**适用于 `b_system` 与 `ue5_overlay` 场景；其中部分条款（如 §1.1、§1.5、§1.7、§1.8、§3.4、§3.11）同时作为 website / ai_assistant 等兼容场景的扩展 Guard 使用。"
  - **目的**：
    - 在不改变"主线仍是 b_system + ue5_overlay"的前提下，将 ai_assistant 条款定位为"扩展护栏"，避免结构性冲突。

### 11.3 最小改动优先的落地策略

> 为避免一次性向 Guard 注入过多新条文，建议分两步推进：**先落最关键、最稳的条目**，其余保留在本验证文档中继续迭代。

- **第一批（建议优先落地的最小改动）**：
  - **优先 1：limited 模板误用防护**
    - 在 `§1.5` 中补充对 `b-system-ai-assistant.html` 的说明，并显式指向"需要遵守 ai_assistant 专向条款"；
    - 在 `§3.4` 中增加一条针对 `b-system-ai-assistant.html` 的说明：
      - 明确其不得作为通用后台模板使用；
      - 仅当场景满足"对话 + 计划板 + 工具日志 + 结果区"四块时才可用；
    - 在 `§3.11` 新增"ai_assistant limited 模板误用"条，固化规则 C1/C2 的禁止情形。
  - **优先 2：ai_assistant vs b_system 的场景 stop&ask**
    - 在 `§1` 中新增 `§1.8`，但首轮只包含 A1、A2 两条：
      - A1：带"助手/聊天"字样但主任务为固定业务流程 → 判 `b_system`；
      - A2：多轮澄清 + 计划 + 多工具调用的助手工作台 → 判 `ai_assistant`；
    - A3（dashboard + assistant 混合）可先只在条文中简要提醒"需综合参考 cockpit / dashboard 规则"，详细内容继续留在本验证文档中。

- **第二批（可稍后再落地的条目）**：
  - `§1.8` 中更细致的混合场景处理（A3 的完整展开）；
  - `§1.8` 中 B1/B2 的 ue5_overlay + ai_assistant 三方边界说明；
  - 对 cockpit + assistant + website 三方混合的拆分建议（B2），可以等更多真实样本后再补充进 Guard。

- **暂不落地的条目（继续留在验证文档即可）**：
  - 任何涉及未来潜在助手子类型（如"轻量问答助手页""review 页"）的推演条款；
  - 与 ai_assistant Level 升级直接相关的内容（目前样本还不足以支持在 `§2` 中新增 Level 复审条款）。

### 11.4 Guard 落地后的回归检查清单

> 若下一轮正式修改 `EXTENSION_GUARD.md`，至少应基于本文件样本执行以下回归检查：

- **场景 1：纯 ai_assistant 工作台**
  - 样本：`ai_assistant_case_pure_workspace`、`ai_assistant_case_heavy_tool_calls`、`guard_case_pure_ai_workspace_minimal_ui`。
  - **预期行为**：
    - 不触发"scene 边界不清"的 stop&ask（除高风险操作外）；
    - Guard 不应将其降级为 `b_system`；
    - 使用 `b-system-ai-assistant.html` 不会被误判为 limited 模板误用。
  - **不应出现**：
    - 仅因没有仪表盘/复杂导航就被判为 `b_system`；
    - 仅因使用 limited 模板就强制 stop&ask 阻止。

- **场景 2：纯 b_system 工作台但带聊天框**
  - 样本：`ai_assistant_case_pure_b_system_workspace`、`guard_case_bsystem_with_chatbox`。
  - **预期行为**：
    - 命中 `§1.8`（A1） / `§3.11`（C1/C2） 的 stop&ask；
    - 在补问后稳定判定为 `scene = b_system`，使用系统模板，不使用助手壳；
    - Guard 明确标记"助手"只是说明/FAQ，不构成 ai_assistant 场景。
  - **不应出现**：
    - 仅因存在聊天框/"助手"字样就直接判定为 `ai_assistant`；
    - 在没有完整助手任务流时允许使用 `b-system-ai-assistant.html`。

- **场景 3：dashboard + assistant 混合**
  - 样本：`ai_assistant_case_dashboard_plus_assistant`、`guard_case_dashboard_with_assistant_insights`。
  - **预期行为**：
    - 命中 `§1.8.3` stop&ask，补问"无助手时是否仍需存在""主任务是盯盘还是对话 orchestrate"；
    - 多数情况下判定为 `scene = b_system`，助手只是模块/洞察面板；
    - 若业务明确要求"助手 orchestrate 多步骤任务"，才允许判为 `scene = ai_assistant`，并将 dashboard 退为嵌入视图/入口。
  - **不应出现**：
    - 无 stop&ask 情况下直接把 dashboard 页切到 `ai_assistant`；
    - 忽略 `b_system` 模板壳约束。

- **场景 4：cockpit + assistant**
  - 样本：`ai_assistant_case_assistant_plus_cockpit_overlay`、`guard_case_cockpit_with_assistant_sidecar`。
  - **预期行为**：
    - 命中 B1/A3 分支，明确 cockpit 属于 `ue5_overlay` + `b_system`；
    - 默认情况下：
      - 整页 `scene = ue5_overlay` + `b_system`；
      - 助手为 sidecar/浮层组件；
    - 只有在非常明确的"助手工作台为主、cockpit 只读"描述下，才允许考虑 `scene = ai_assistant` 方案。
  - **不应出现**：
    - 直接将 cockpit 页标记为 `scene = ai_assistant`；
    - 使用 `b-system-ai-assistant.html` 作为 cockpit 页主壳。

- **场景 5：limited 模板误用**
  - 样本：`ai_assistant_case_limited_template_misuse`、`guard_case_assistant_shell_misuse_admin_home`。
  - **预期行为**：
    - 命中 `§1.5` + `§3.4` + `§3.11`；
    - Guard 明确给出"limited 模板误用"的提示，建议改用 b_system dashboard/workspace 模板；
    - 不允许在无助手任务流的情况下使用 `b-system-ai-assistant.html`。
  - **不应出现**：
    - 把"为了好看借壳"的场景视为 ai_assistant 合规使用；
    - 缺乏任何 warning/ERROR 信号。

- **场景 6：说明型 AI 洞察面板**
  - 样本：`guard_case_dashboard_with_assistant_insights`。
  - **预期行为**：
    - 命中 `§1.8`（A3）/`§3.11`（C2） 的 stop&ask；
    - 仍判定为 `scene = b_system` 的 dashboard，AI 洞察为模块；
    - Guard 不鼓励把这种"洞察说明"升级为 ai_assistant 场景。
  - **不应出现**：
    - 仅因"AI 洞察"三个字就判定为 `ai_assistant`；
    - 将 `b-system-ai-assistant.html` 用于这类 dashboard。

### 11.5 是否进入 Guard 执行轮（结论）

- **挂接合理性**：
  - ai_assistant 条款可以在不打乱 `EXTENSION_GUARD` 主结构的前提下，通过新增 `§1.8` / `§3.11` 和少量交叉引用完成挂接；
  - b_system / ue5_overlay 现有条款只需轻微补充对 `b-system-ai-assistant.html` 的说明，不需要重构。
- **样本与规则成熟度**：
  - 本文件第 3/4/9 节提供的 11 条样本，已覆盖"纯助手工作台、纯后台工作台 + 聊天框、dashboard + assistant、cockpit + assistant、limited 模板误用、说明型 AI 洞察"等关键情形；
  - 第 8 节 Guard 建议稿已经按 Guard 语气给出了 A/B/C 三组规则，可直接转化为条文。
- **建议**：
  - 从风险与收益平衡角度，**建议下一轮进入 Guard 执行轮，采用"最小改动优先"的策略**：
    - 首先落地 limited 模板防误用相关条款（`§1.5` 补充说明 + `§3.4` 补充 + 新增 `§3.11`）；
    - 同时新增 `§1.8` 的 A1/A2 两条（b_system vs ai_assistant 基础边界）；
    - A3/B1/B2 等更复杂混合场景规则可作为第二轮扩展，在更多真实样本出现后补充。

> **Guard patch plan 总结（一句话）**：在不改动实现与 router 的前提下，ai_assistant 的 Guard 条款可以通过"新增 `§1.8` + `§3.11` 并轻量补充 `§1.5`/`§3.4`"的方式安全挂接进 `EXTENSION_GUARD.md`，建议下一轮按"limited 模板防误用 + 基础场景边界优先"的最小改动策略正式进入 Guard 执行落地。

---

## 12. Guard 回归验证结果（ai_assistant Phase 1）

> 本节基于已落地的 `EXTENSION_GUARD.md` 最小 Guard patch，回归验证第 3/4 节首批样本与第 9 节 Guard 回归样本，评估 limited 模板防误用与 `ai_assistant` vs `b_system` 基础场景边界在实际样本上的表现，并判断是否具备进入 observation mode 的条件。

### 12.1 回归范围与整体结论

- **回归范围**：
  - Guard 条款：`EXTENSION_GUARD §1.5`（limited 模板）、`§1.8`（ai_assistant vs b_system 场景边界）、`§3.4`（limited 模板禁止通用化）；
  - 样本集合：
    - 第 3/4 节的 6 条核心样本；
    - 第 9 节的 5 条 Guard 回归样本。
- **整体结论**：
  - `b-system-ai-assistant.html` 的 limited 防误用现在对"为好看借壳""说明型助手组件"等高风险场景有了明确拦截路径；
  - `ai_assistant` vs `b_system` 的基础 stop&ask 与第 6 节边界结论在所有相关样本上保持一致，未发现逻辑冲突；
  - 对纯助手工作台样本，新的 Guard 条款未出现"误伤"行为；
  - cockpit / website 等更复杂混合场景仍主要由本验证文档提供协议说明，Guard 目前只做轻量提示，符合本轮"最小 patch"预期。

### 12.2 按样本分组的 Guard 表现

#### 12.2.1 纯 ai_assistant 正例

- **覆盖样本**：
  - `ai_assistant_case_pure_workspace`；
  - `ai_assistant_case_heavy_tool_calls`；
  - `guard_case_pure_ai_workspace_minimal_ui`。
- **Guard 行为与预期对齐情况**：
  - 这些样本均满足"对话入口 + 澄清/规划 + 多工具调用 + 执行日志 + 结果回顾"的 `assistant_workspace` 特征：
    - 在 `EXTENSION_GUARD §1.8` 中会命中"多轮澄清 + 计划 + 多工具调用的助手工作台"的正例描述；
    - 在 `§1.5` 中使用 `b-system-ai-assistant.html` 时，能够满足"对话区 + 任务/计划板 + 工具调用日志 + 结果回顾四块结构"的要求；
    - 不会触发 `§3.4` 所禁止的"limited 模板通用化"行为。
  - 因此：
    - Guard 不会把这类场景误拉回 `scene = b_system`；
    - 也不会对合法的助手工作台使用 limited 模板给出误报。

#### 12.2.2 纯 b_system 反例

- **覆盖样本**：
  - `ai_assistant_case_pure_b_system_workspace`；
  - `guard_case_bsystem_with_chatbox`；
  - `guard_case_dashboard_with_assistant_insights`；
  - FAQ/帮助型"小助手"相关描述（对应 8.3 C2）。
- **Guard 行为与预期对齐情况**：
  - 这些样本都会触发 `§1.8` 中"带助手/聊天字样 + 固定业务流程词汇"的 stop&ask：
    - 补问"去掉助手是否仍成立""主任务是对话 orchestrate 还是固定流程"；
    - 根据样本设定，答案均指向"去掉助手页面仍成立 + 固定流程为主"。
  - 判定结果：
    - Guard 会将其稳定归为 `scene = b_system`；
    - `§1.5`/`§3.4`/limited 相关条款禁止在这些场景中使用 `b-system-ai-assistant.html`；
    - 对 FAQ/洞察面板这类说明型"助手"，Guard 会按照 C2 逻辑，将其视为模块而非场景切换理由。
  - 与验证文档结论的吻合点：
    - 完全符合第 6.2 节"虽有助手元素但本质仍是 b_system"的判定；
    - "有聊天框 ≠ ai_assistant""有 AI 洞察文案 ≠ ai_assistant"这类结论，已经通过 Guard 条文固化。

#### 12.2.3 混合场景（dashboard / cockpit + assistant）

- **覆盖样本**：
  - dashboard + assistant：`ai_assistant_case_dashboard_plus_assistant`、`guard_case_dashboard_with_assistant_insights`；
  - cockpit + assistant：`ai_assistant_case_assistant_plus_cockpit_overlay`、`guard_case_cockpit_with_assistant_sidecar`。
- **Guard 当前表现**：
  - 对于 dashboard + assistant：
    - 会命中 `§1.8` 中关于"同页包含 dashboard/workspace 视图 + 助手模块"的 stop&ask；
    - 在"去掉助手仍具备完整 dashboard/workspace 价值"的情况下，优先判定为 `scene = b_system`，助手为模块/浮层；
    - 只有当 PRD 明确以"对话 orchestrate 多步骤任务"为主线时，才有机会切到 `scene = ai_assistant`。
  - 对于 cockpit + assistant：
    - 虽然 `AI_ASSISTANT_PHASE1_VALIDATION` 第 8 节提供了 B1/B2 条文草案，但本轮 Guard 最小 patch 仅实现了轻量提示：
      - cockpit 类混合场景仍主要由 `§1.3`（UE5 Mode 边界）与 `§1.4`（跨场景混合）触发 stop&ask；
      - 并通过文案引导"先判主场景为 `ue5_overlay` + `b_system`，助手为 sidecar"，而非强制规则化所有三方组合。
- **与预期结论的关系**：
  - dashboard + assistant 的最小保守判定，已经实现"先判主场景 + 避免整页切 ai_assistant"；
  - cockpit + assistant 仍处于"保守处理"阶段：
    - Guard 能提醒"需要人工确认 cockpit 是否主场景"；
    - 但更细的三方拆分策略仍留在验证文档中，待更多真实案例后再考虑进入 Guard。

### 12.3 本轮 Guard 已覆盖 / 仍待后续的边界

- **本轮已经 Guard 化的边界**：
  - **limited 模板防误用**：
    - `b-system-ai-assistant.html` 被限定为 `scene = ai_assistant, page_type = assistant_workspace, grade = limited`；
    - 明确禁止"为好看借壳""在纯后台首页/工作台中使用助手壳"；
    - 说明型 FAQ/洞察型"助手"被明确排除在助手壳使用范围之外。
  - **ai_assistant vs b_system 基础 stop&ask**：
    - 带"助手/聊天"文案但主任务为固定流程 → 通过 `§1.8` 回退到 `b_system`；
    - 满足"对话 + 澄清/规划 + 多工具调用 + 日志 + 结果回顾"的完整助手链路 → 通过 `§1.8` 判为 `ai_assistant`；
    - dashboard/workspace + assistant 混合 → 强制 stop&ask，默认优先保留 `b_system` 主场景。
  - **最关键误用风险**：
    - "把助手壳当通用后台壳"的误用路径已被 `§1.5 + §3.4` 阻断；
    - "看到聊天框/AI 洞察就判 ai_assistant"的误判路径被 `§1.8` 的补问机制抑制。

- **仍待后续 Guard 化的边界（继续在本验证文档中维护）**：
  - **ai_assistant vs ue5_overlay 的复杂三方边界**：
    - cockpit + assistant 的角色划分，仍主要依赖第 8.2 节文档条款与人工判断；
    - 未在本轮 Guard patch 中全面条文化，只以 UE5 Mode 边界条款 + 跨场景混合提示进行保守处理。
  - **website + assistant + cockpit 等多 scene 组合**：
    - 目前仍建议拆分为 website / ue5_overlay + b_system / ai_assistant 三页；
    - 具体 Guard 行为仍停留在"提醒拆分 + stop&ask"，尚未写入细节规则。
  - **潜在 ai_assistant 子类型（轻量问答、review 等）与 Level 升级**：
    - 缺乏稳定样本，本轮不进入 EXTENSION_GUARD，继续在本文件中作为观察项记录。

### 12.4 是否进入 observation mode（ai_assistant）

- **前置条件检查**：
  - 已具备：
    - 完整的 W1 验证文档（范围/样本/边界结论/Guard 建议）；
    - 覆盖关键风险路径的最小 Guard patch（limited 防误用 + 基础场景 stop&ask）；
    - 一组明确可用于回归的样本清单（第 3/4/9 节）。
  - 尚在观察但不阻碍 observation mode 的点：
    - cockpit / website 等复杂三方混合尚未完全规则化，但已被 Guard 标记为必须 stop&ask 的高复杂度场景；
    - ai_assistant 子类型与 Level 的更细治理留待后续样本驱动。
- **判断**：
  - 在当前状态下，**ai_assistant 已具备与 website Phase 1 类似的 observation mode 前置条件**：
    - 关键误用路径已有 Guard 正式约束；
    - 其它复杂场景已在本文件中被显式标记为"需人工判定/待后续规则化"。
  - 建议的 observation mode 做法：
    - 新增/调整与 ai_assistant 相关任务时，优先对照本文件与 `EXTENSION_GUARD` 条款进行人工复核；
    - 将未来在真实项目中出现的边界争议，持续回填到本文件的样本与观察项章节中，而不是立刻扩写 Guard。

### 12.5 是否可以准备下一个 scene（例如 presentation）

- **当前 ai_assistant 治理状态小结**：
  - W1 级验证文档 + 样本集已完备到可支撑 Guard 条文化；
  - 最小 Guard patch 已落地并通过本轮文档级回归验证；
  - 残余风险集中在复杂三方混合与未来子类型，已被明确标记为 observation 阶段议题。
- **切换下一个 scene 的触发判断**：
  - 若后续一段时间内：
    - 新增的 ai_assistant 相关任务在本 Guard 框架下未出现系统性误判；
    - cockpit/website 等复杂混合问题可以通过 stop&ask + 文档协议得到可接受处理；
  - 则可以认为 ai_assistant 已进入稳定的 observation mode，**可以开始规划下一个 scene（如 presentation）的 Phase 1 W1 工作**。
  - 若在 observation 期内暴露出大量新的越界模式（尤其是 cockpit + assistant 方向），则应优先回到本文件，先补样本和 Guard 草案，再考虑切换新场景。

> **Phase 1 总结（当前轮）**：在完成最小 Guard patch 并通过现有样本回归验证后，`ai_assistant` 已从"可治理 W1 起步"进一步进入"具备 Guard 支撑的 observation mode"阶段 —— 后续工作重心可以逐步从规则补强转向真实项目观测与其他 scene（如 presentation）的 Phase 1 建设筹备。