# TEMPLATE_REPAIR_REGRESSION · 第一批高价值模板修复回归验证

> **文档目的**：对首批已完成“小范围模板修复执行轮”的 4 个模板做一次 **修复后回归验证**，仅在文档层评估：
> - 修复是否强化了模板本身的角色表达与自解释能力；
> - 修复是否实质性降低了 AI 误参考风险；
> - 模板本体与资产地图 / 审查文档的描述是否保持一致；
> - 是否需要、以及如何克制地规划第二批修复轮。
>
> **不做的事**：本轮不再修改任何 HTML 模板 / router / matrix / Guard，仅记录观察与判断，为后续是否扩轮提供依据。

---

## 0. 回归验证范围与对照基线

- **本轮回归对象（仅 4 个模板）**：
  - `examples/b-system/b-system-ai-assistant.html`
  - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`
  - `examples/presentation/presentation-business.html`

- **对照基线**：
  - 修复前的问题与风险，来源于：
    - `docs/HIGH_VALUE_TEMPLATE_REVIEW.md` 中的初始审查结论与“第一批修复候选清单”；
    - `docs/TEMPLATE_ASSET_REFERENCE_MAP.md` 中对这 4 个模板的资产层级 / 规范风险 / 说明；
  - 修复后的实际改动，来源于：
    - 对 4 个 HTML 模板中新增/增强的文件头注释、结构注释、aria-label 与少量文案调整；
    - 审查文档与资产地图中新增的“首批修复执行回写”与轻量状态说明。

---

## 1. `examples/b-system/b-system-ai-assistant.html` 回归验证

> **定位基线**：`scene = ai_assistant` / `page_type = assistant_workspace` / `grade = limited` / `use_scope = limited`，唯一的 ai_assistant workspace 主壳。

### 1.1 角色表达是否增强

- **修复前主要问题（来自审查文档）**：
  - 虽然在资产地图中被标记为 assistant_workspace，但 HTML 本身对 `scene/use_scope` 的表达较弱；
  - AI 容易将其视为“有 AI 的通用 b_system 工作台”，而不是“AI + 问题工作台”的 **limited workspace 场景**。
- **修复后模板现状（HTML）**：
  - 文件头明确写出：
    - `scene = ai_assistant / page_type = assistant_workspace / use_scope = limited`；
    - “仅在 PRD 明确需要「AI 对话 + 问题工作台」时作为主壳”；
    - “不用于普通 b_system dashboard / list / planning，也不用于轻量 FAQ/聊天助手”。
  - 主体 `ai-workspace` 容器上新增注释，清晰区分：
    - 左栏 = AI 对话流（assistant 主交互区，**必需模块**）；
    - 右栏 = 排产问题监控/KPI/表格（workspace 监控区，**可按 PRD 选配**）；
    - 并显式提示：“若只需要轻量问答型助手，请不要直接复用整个 workspace 壳”。
- **判断**：
  - 对 AI 而言，模板现在用自己的注释就讲清楚了“**我是 limited 的助手工作台壳**”，角色表达明显增强。

### 1.2 边界误导风险是否下降

- **修复前最担心的误导**：
  - AI 在任何“有助手”要求的任务里，直接选用该模板作为默认助手壳，包括 FAQ / 轻量问答 / 无右侧工作台的场景；
  - AI 把“左 chat + 右复杂 workspace”误认为所有助手场景的标准形态。
- **修复后缓解情况**：
  - 文件头用 `use_scope = limited` + 适用/不适用列表，把“只在 AI + 工作台场景使用”写死；
  - `ai-workspace` 注释中强调“左栏为必需、右栏可选”，提示轻量助手场景不应整页套用；
  - JS 顶部 `[DEMO NOTICE]` 注释将整段交互逻辑标明为“仅用于展示典型链路”，降低“照抄全部行为”的暗示。
- **残余风险**：
  - 模板仍然为唯一的 workspace 级助手样本，在没有更多变体出现前，AI 可能仍会倾向选它作为“高级助手形态”；
  - 右侧监控/图表/表格仍然非常丰富，如果 Guard 条件放松，仍存在“为好看借壳”的诱惑。
- **判断**：
  - 相比修复前，**误用为 FAQ/轻量助手的风险明显下降**，因为模板自己已经强烈明示“不适合”这些场景；
  - 但在所有 workspace 助手需求中，仍应通过 Guard/任务前置条件来约束，而不是提升为更广义的 canonical。

### 1.3 自解释能力与非规范噪音

- **自解释能力**：
  - 文件头 + 主壳注释 + demo 脚本说明共同构成了完整的“README in HTML”；
  - 对 AI 来说，仅通过阅读注释就能重建如下认知：
    - 这是 **assistant_workspace**，且 **limited**；
    - 左栏 = 对话壳，右栏 = 问题工作台，二者可以拆分；
    - 脚本 = demo-only，不是所有助手必备链路。
- **非规范噪音**：
  - 场景文案和 chart 配置仍然丰富，但被 `[DEMO NOTICE]` 与“示例问题/解决方案”语义包裹；
  - 内联样式主要是细节视觉/布局（如 sparkline 高度），未进一步放大，属于可接受范围。

### 1.4 当前状态判断

- **归类**：
  - **“风险明显下降，可继续作为当前 limited 参考资产”**：
    - 适合在满足“AI + 工作台”前置条件的 assistant_workspace 场景中被选为主参考；
    - 不宜无 Guard 地在所有助手任务中使用。

---

## 2. `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html` 回归验证

> **定位基线**：`scene = ue5_overlay` / `page_type = overlay_full_layout` / `grade = candidate` / `use_scope = limited`，Mode 5 双侧面板 + 底 Dock 的数字孪生 cockpit 布局草图，C 局部参考资产。

### 2.1 角色表达是否增强

- **修复前主要问题**：
  - 虽然在资产地图中被标为 Mode 5 cockpit layout，但 HTML 自身对“仅 cockpit 场景使用”“更多是 layout 草图”的提示不够强；
  - AI 很容易把它误解为“更高级的通用 overlay 壳”。
- **修复后模板现状**：
  - 文件头注释现在直接声明：
    - `scene = ue5_overlay / page_type = overlay_full_layout / use_scope = limited`；
    - “本模板是数字孪生驾驶舱 cockpit 布局草图，不应作为通用 overlay 场景默认壳”；
  - 安全区 `aria-label` 从普通“监控主界面”改为“数字孪生 Mode 5 驾驶舱主界面（limited，仅 cockpit 场景）”；
  - 底部 Dock 附注：“Mode 5 cockpit 专属模块，普通 overlay 场景一般不需要引入完整 Dock”。
- **判断**：
  - 模板在结构不变的前提下，用注释和 aria 明确地说出了“**我是 Mode 5 cockpit / limited / layout 草图**”，角色表达显著增强。

### 2.2 边界误导风险是否下降

- **修复前最担心的误导**：
  - AI 在任何 overlay 任务中，默认把 Mode 5 当成“终极壳”，忽略 Mode 1/2/3；
  - AI 在非数字孪生场景中也照搬“双侧面板 + Dock 时间轴”的重壳结构。
- **修复后缓解情况**：
  - 用 `use_scope = limited` + cockpit 关键字不断提醒“仅数字孪生驾驶舱场景使用”；
  - 时间轴脚本顶部 `[DEMO NOTICE]` 指明 TL_RANGE/TL_EVENTS 是示例项目数据，并强调应关注的是“单容器 + 绝对定位 + 百分比 left”这种布局模式，而非时间轴作为所有 overlay 的必需模块。
- **残余风险**：
  - 脚本仍然复杂，AI 若强行在别处复用，仍可能抬高作品复杂度；
  - 该模板在 C 层中仍然是最完整的 cockpit 草图之一，对“炫酷布局”的诱惑仍在，需要 Guard 从策略层面继续限制。
- **判断**：
  - **误将 Mode 5 视为通用 overlay 主壳的风险明显下降**，但模板依然应被视为“高级 layout 草图 + 人工确认使用”的资产，而不是扩权为更普适的参考。

### 2.3 自解释能力与非规范噪音

- **自解释能力**：
  - 文件头对 Mode 5 结构、grid 覆写方式、使用场景给出了相对详尽的文字说明；
  - 安全区、Dock、时间轴脚本都带有针对 cockpit/limited 的注释，AI 仅凭阅读即可理解其“层级”和“专用性”。
- **非规范噪音**：
  - 时间轴脚本和 demo 事件数据依然完整存在，但被标记为 Mode 5 示例；
  - critical banner 的 `[DEMO]` 注释保留，并强调生产环境应恢复 `display:none`，对 AI 是一个“告警组件可选”的提醒。

### 2.4 当前状态判断

- **归类**：
  - **“风险有所下降，但仍需后续修复”**：
    - 在“是否被误当通用壳”方面改善明显；
    - 在“脚本复杂度与 demo 数据体量”方面仍然偏重，适合在未来的更深层修复轮中继续做解耦和模块化。

---

## 3. `examples/ue5-overlay/digital_twin_overlay_dashboard.html` 回归验证

> **定位基线**：`scene = ue5_overlay` / `page_type = digital_twin_dashboard` / `grade = candidate` / `use_scope = limited`，数字孪生 + 运控面板混合 cockpit 模板，C 局部参考资产。

### 3.1 角色表达是否增强

- **修复前主要问题**：
  - 文档中已说明这是数字孪生 + 运控面板混合模板，但 HTML 注释对“limited + 混合角色”的表达略显简略；
  - AI 容易把它当作“更高级的 overlay 或 b_system dashboard”。
- **修复后模板现状**：
  - 文件头注释增加：
    - `scene = ue5_overlay / page_type = digital_twin_dashboard / use_scope = limited`；
    - “仅在 PRD 明确为『数字孪生驾驶舱 + 运控面板』混合场景时，由人工确认使用”；
    - 明写“不应用于普通 ue5_overlay 模式 1/2/3，也不应用于纯 b_system dashboard 场景”。
  - 安全区 `aria-label` 写为“数字孪生 + 运控 cockpit 安全区（limited，不作为通用 overlay 壳）”；
  - 底部 dock 的状态文案也加上“limited cockpit 示例，不作为通用 overlay 壳”。
- **判断**：
  - 模板现在用自己的文字不断强调“**我是数字孪生 + 运控 cockpit 混合模板，且 limited**”，角色表达比修复前清晰得多。

### 3.2 边界误导风险是否下降

- **修复前最担心的误导**：
  - AI 在普通 overlay 场景中使用此模板，导致 overlay 与 b_system 界面混合；
  - AI 在纯 b_system dashboard 场景中使用此模板，引入三维场景占位和 cockpit UI。
- **修复后缓解情况**：
  - 文件头/安全区/dock 中的“仅数字孪生 + 运控场景”“不作为通用 overlay 壳”等语句，把这两类误用路径直接否掉；
  - 右侧面板被明确称为“运控数据面板”，左侧 world marker 层也通过 aria 明示为“世界锚点示例”，AI 更容易把混合属性视为“示意/草图”。
- **残余风险**：
  - 作为少数 digital twin cockpit 模板之一，如果 Guard 不够严格，AI 在缺乏更合适模板时仍可能尝试引用其部分结构；
  - 混合 b_system 样式与 overlay HUD 的模式仍然需要通过文档与 Guard 约束使用频率。
- **判断**：
  - **误用为普通 overlay 或纯 b_system dashboard 的风险明显下降**；
  - 仍应保持其在 C 层、limited 的定位，并通过任务前置条件 +人工确认来控制使用。

### 3.3 自解释能力与非规范噪音

- **自解释能力**：
  - 文件头和 safe-area/dock 的 aria/文案已经足以让 AI 理解：
    - “左侧是三维 Overlay + 世界锚点 + HUD，右侧是 b_system 运控面板，整体为 cockpit 混合页”；
    - “这是 limited cockpit 示例，而非任何场景的默认壳”。
- **非规范噪音**：
  - JS 仅做 icon 渲染，没有额外 demo 逻辑，相比 Mode 5 噪音更低；
  - 文案依然以 C919 总装线为例，但未过度干扰结构理解，且未新增新的内联样式问题。

### 3.4 当前状态判断

- **归类**：
  - **“风险明显下降，可继续作为当前 C 局部参考资产”**：
    - 更适合作为“数字孪生 + 运控 cockpit 布局示意”和“组件组合参考”；
    - 不建议在短期内提升为更广义的主壳参考，也不应扩大 use_scope。

---

## 4. `examples/presentation/presentation-business.html` 回归验证

> **定位基线**：`scene = presentation` / `page_type = business_report` / `grade = candidate` / `use_scope = default`，经营/业务汇报 deck strong candidate，B 次参考。

### 4.1 角色表达是否增强

- **修复前主要问题**：
  - 文档指出其为 business_report deck，但模板本身对“适合/不适合哪些场景”的表达不明显；
  - AI 容易把它泛化为“任何 KPI 报告壳”，或误用为 dashboard/website。
- **修复后模板现状**：
  - 文件头注释现在明确说明：
    - 适用：阶段性经营汇报、QBR、管理层评审、以“封面 + 目录 + 指标回顾 + 分析 + 趋势 + 计划”为主线的 deck；
    - 不适用：日常运营 dashboard、drill-down 查询、登录型工作台、长期在线 website 专题页；
    - 并将自身定义为“business review / QBR deck 壳”。
  - 各 slide 前新增章节注释，例如：
    - “章节 01：关键指标回顾（KPI 回顾页，用于快速对齐业务成绩概览）”；
    - “章节 05：下一步计划（行动方向与关键目标，支撑决策与后续追踪）”；
    - 收尾页注释为“感谢 / Contact / 可选 Q&A 引导，不承载新的业务内容”。
- **判断**：
  - 模板现在在结构不变的前提下，清晰地对外表达：“我是 **经营汇报/QBR deck**，不是 dashboard 或网站”，角色表达显著增强。

### 4.2 边界误导风险是否下降

- **修复前最担心的误导**：
  - AI 将示例中的 KPI 结构和维度当成“所有 business report 的默认标准”；
  - AI 在需要 dashboard 或工作台时误选该 deck 作为壳。
- **修复后缓解情况**：
  - 文件头“不适用场景”列表直接否定了 dashboard / workbench / website 用途；
  - 经营数据页的“核心发现”卡片前增加注释，提醒下面是“示例业务内容”，实际项目应替换为本企业/行业的关键发现。
- **残余风险**：
  - 示例 KPI 与 bullet 仍明显偏向某类数字业务场景（活跃用户、用户增长、满意度等），AI 在缺少其他样本时，仍可能默认采用类似指标；
  - 其它内联样式仍然存在（本轮刻意只收敛“最显眼的一处”）。
- **判断**：
  - **被误用为 dashboard/website 的风险明显下降**；
  - 作为“所有 business_report 统一 KPI 模板”的风险有所缓解，但仍然存在，需要未来通过更多样本/规范进一步减弱。

### 4.3 自解释能力与非规范噪音

- **自解释能力**：
  - 文件头 + 每章注释，使得 AI 阅读结构即可重建“封面/目录/指标回顾/分析/市场对比/趋势/计划/收尾”的叙事框架；
  - 这对“识别 deck 类型”和“理解各章节角色”都明显有帮助。
- **非规范噪音**：
  - 最显眼的内联样式（经营数据页标题）已去除；
  - 仍有其他局部内联样式，但相对分散，本轮刻意不做大规模样式重构，以控制侵入度。

### 4.4 当前状态判断

- **归类**：
  - **“风险有所下降，但仍需后续修复”**：
    - 在“是不是 business deck / 不是 dashboard/website”这条边界上，表达已经足够清楚；
    - 但要想成为更强的 canonical 候选，仍需要在未来修复轮中统一样式与指标示例，使其对更多行业更中性。

---

## 5. 模板本体 vs 资产地图 vs 审查文档的一致性检查

### 5.1 一致性结论

- 对 4 个模板逐一校验后，当前状态为：
  - **模板本体** 中的文件头注释 / 结构注释 / aria / demo 提示，已经与：
    - `HIGH_VALUE_TEMPLATE_REVIEW.md §7.1/§8` 中对“首批修复候选 + 已执行修复”的描述；
    - `TEMPLATE_ASSET_REFERENCE_MAP.md` 相应表格行中的“资产层级 + 规范风险 + 说明”；
    - **保持一致**。
- 特别是：
  - `b-system-ai-assistant`、Mode 5、digital twin 三个模板在审查文档中被描述为“limited cockpit/assistant_workspace + 高风险，已在首批修复中强化注释与边界表达”，模板本身确实增加了对应的 limited/cockpit/DEMO 注释；
  - `presentation-business` 在审查文档的首批修复回写中被标记为“优先级 2 补位修复（增强角色注释 + 去除一处内联样式 + 标注示例内容）”，模板本身也准确反映了这些操作；
  - 资产地图中三条 overlay/assistant 资产与一条 presentation 资产的说明列，都已轻量补充“首批修复已在模板内部强化 xxx 注释/样式收敛”，与模板现状吻合。

### 5.2 轻微不一致与遗留点（本轮仅记录，不修复）

- **审查文档的风险等级仍保持“高风险 / 中风险”原标注**：
  - 即便经过小范围修复，`b-system-ai-assistant` 与两个 cockpit 模板在表格中仍标注为“高风险，后续应优先修复”；
  - 这与当前的现实相符：本轮主要做的是“边界表达 + 自解释”增强，而不是实质性降低结构复杂度或 demo 体量。
- **presentation deck 的“内联样式问题”在文档中仍以“多处”描述**：
  - 本轮只对 business deck 中最突出的一个内联标题做了收敛，但资产地图与审查文档仍将“内联样式较多”作为整个 deck 族的共性问题记录；
  - 这在语义上并不冲突：当前仍存在其它内联样式，因此可以保留原结论。

---

## 6. 本轮修复是否达成目标

### 6.1 AI 误参考风险的整体变化

- 对于本轮聚焦的 4 个高价值模板：
  - **b-system-ai-assistant**：
    - 现在更明确地声明了自己的 `scene/page_type/use_scope`，并在主壳注释中限制了使用场景；
    - 误被当作 FAQ/通用助手壳的风险明显下降。
  - **Mode 5 cockpit layout**（sidepanel + Dock）：
    - 通过 `limited`、cockpit 关键词和 Dock/时间轴脚本的 DEMO 声明，明显强化了“仅 Mode 5/数字孪生驾驶舱使用”的信号；
    - 误被当成“更高级的通用 overlay 壳”的风险下降。
  - **digital twin cockpit 混合模板**：
    - 通过文件头与 safe-area/dock 文案，把“数字孪生 + 运控 cockpit / limited”讲得很清楚；
    - 误用为普通 overlay 或纯 b_system dashboard 的风险下降。
  - **presentation-business deck**：
    - 文件头与章节注释清晰强调其为“business review / QBR deck”，并列出不适用的场景；
    - 误用为 dashboard/website 的风险下降，示例业务内容与骨架的边界也更清晰。

### 6.2 “试点 vs 第一阶段”的判断

- 从范围与深度上看：
  - 本轮对 4 个模板的修复 **刻意保持低侵入**，重点是“自解释 + 边界表达 + 少量内联/示例标注”；
  - 并未进入“大规模样式收敛”或“结构重构”层级。
- 因此更合理的定位是：
  - 本轮修复是一次 **“成功试点 + 第一阶段”**：
    - 证明了通过少量注释/aria/文案增强，可以显著收紧 AI 的使用边界；
    - 但尚未“完成”这几个模板的所有规范问题，只是把最关键的“误参考风险”往下压了一大块。

---

## 7. 是否建议开启第二批模板修复轮

### 7.1 是否建议立即开启

- **结论：暂不建议立即开启第二批模板修复轮。**

### 7.2 理由

- **本轮刚完成，值得先观察**：
  - 四个模板刚刚完成小范围修复，并在文档层完整回写；
  - 更合理的节奏是先等待一段 observation 周期，观察：
    - 这些模板在真实任务/AI 生成中的命中频率是否变化；
    - 误用/边界踩踏是否明显下降；
    - 是否出现新的“理解偏差”样本。
- **关键风险已从“红色”降到“黄色可控”**：
  - 对 limited cockpit/assistant 模板来说，最大的结构性误导来自“limited 边界不显性”与“模板不自己说话”，这一类问题已明显改善；
  - 当前更紧迫的问题转向“如何继续减轻 demo 噪音和样式债务”，这属于下一阶段、可以更从容规划的工作。
- **避免自然扩张范围**：
  - 审查文档中虽列出多处值得后续清理的模板（如 `b-system-production-plan`、其他 presentation deck），但在没有新的样本/压力之前，继续立即扩轮，容易把“小范围执行”滚成长期大项目。

### 7.3 若未来开启第二批，应考虑的范围（仅预告，不作为本轮决策）

> 注意：本小节属于“未来规划建议”，**不构成本轮的“立即行动结论”**。

- 若未来 observation 显示仍有较多误用或样式问题，可以考虑一轮 **“deep clean” 型修复**，范围可以控制在：
  - `b-system-production-plan.html`（进一步澄清 planning/workspace vs advanced_list 边界）；
  - `presentation-product.html` / `presentation-planning.html`（与 business deck 一起做更系统的样式收敛与示例内容中性化）。

---

## 8. 回归验证结论摘要

- **回归模板清单**：
  - 已对 `b-system-ai-assistant`、Mode 5 cockpit layout、digital twin cockpit 混合模板、`presentation-business` 共 4 个模板完成修复后回归验证。
- **风险变化**：
  - 四个模板在“角色表达”“边界自解释”“limited/适用场景显性化”方面均有清晰提升，**AI 将它们误读为更通用壳的风险整体下降**；
  - 非规范噪音在 demo/脚本/内联样式层做了有限收敛，已经不再是“第一优先级问题”，更适合在后续深度修复中统一处理。
- **文档与模板一致性**：
  - 模板本体与 `HIGH_VALUE_TEMPLATE_REVIEW.md` / `TEMPLATE_ASSET_REFERENCE_MAP.md` 的描述一致，审查文档中“首批修复执行回写”与资产地图中的轻量状态说明均已反映出本轮改动。
- **是否开启第二批修复轮**：
  - **暂不建议立即开启**，更合适的策略是在接下来一段 observation 周期中，重点观察这 4 个模板在真实任务中的命中与误用情况，再基于新样本决定第二批修复的范围与优先级。
