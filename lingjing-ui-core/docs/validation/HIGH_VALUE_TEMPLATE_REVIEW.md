# HIGH_VALUE_TEMPLATE_REVIEW · 第一批高价值模板定向规范审查

> **文档目的**：对首批“高价值 + 中高风险”的模板做一次 **文档级规范审查**，不改实现，只判断：
> - 结构骨架是否稳定、角色是否一致；
> - 有哪些明显会误导 AI 的非规范实现；
> - 哪些模板现在就可以相对安心地作为参考，哪些应先进入修复候选队列。
>
> **不做的事**：
> - 不修改任何 HTML 模板 / router / matrix / Guard；
> - 不给出实现层改动 diff，仅在文档中标注“风险点 + 建议动作”。

---

## 0. 审查范围与方法

- **审查范围（严格限制在第一批高价值模板）**：
  - `b_system`
    - `examples/b-system/b-system-production-plan.html`
    - `examples/b-system/b-system-saas.html`
  - `ue5_overlay`
    - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`
    - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`
  - `ai_assistant`
    - `examples/b-system/b-system-ai-assistant.html`
  - `presentation`
    - `examples/presentation/presentation-product.html`
    - `examples/presentation/presentation-business.html`
    - `examples/presentation/presentation-planning.html`

- **信息来源**：
  - `docs/TEMPLATE_ASSET_REFERENCE_MAP.md`：资产层级（A–E）、规范风险标记、真值源挂接；
  - 各模板 HTML：结构骨架、class 组织、注释与 demo/placeholder 密度；
  - Phase 1 验证文档 & EXTENSION_GUARD（在前序任务中已通读，当前仅作为语义参照）。

- **每个模板的审查维度**：
  - **A. 角色一致性**：角色定位 vs 实际结构；
  - **B. 骨架清晰度**：是否“一眼能看出是什么页型/模式”；
  - **C. 非规范内容污染**：placeholder / demo / deprecated class / 临时脚本；
  - **D. AI 参考风险**：AI 若当作主要参考，最容易被误导到哪里；
  - **E. 建议动作 + 审查结论等级**：
    - 结论等级：
      - `通过（低风险）`
      - `通过但建议整理（中风险）`
      - `高风险，后续应优先修复`
      - `定位需进一步澄清`

---

## 1. `b_system` 高价值模板

### 1.1 `examples/b-system/b-system-production-plan.html`

> **资产定位**：`scene = b_system`，`page_type = planning`，`grade = candidate / use_scope = default`，在资产地图中为 **B 次参考（中风险）**。

- **A. 角色一致性**
  - 资产地图将其定位为“生产排程/计划型页面 candidate 模板”，可作为 list/detail/dashboard 之间的 **planning/workspace 壳**。
  - HTML 实际结构：
    - 骨架为 `b-layout-sidebar` 标准后台壳；
    - 主内容部分是 **“高级数据表格 + 右侧筛选与详情 + 底部 Dock”** 的典型 planning 工作台布局；
    - 文案和 UI 元素（“战机生产控制台”“生产计划总览”“批次/状态筛选”等）与“生产计划工作台”语义高度一致。
  - **结论**：角色与 `scene/page_type` 定位整体一致，没有出现“名义 planning 实际只是普通 list/dashboard”的错位。

- **B. 骨架清晰度**
  - 左侧固定 sidebar，右侧 `b-main` 下是单列头部 + 单列内容，内容内部再分为：
    - 表格 + 顶部 filter-bar + 批量操作条；
    - 右侧 filter-panel + detail-panel + checklist-panel + comparison-card。
  - 以 AI 视角，“这是一个面向计划/排程的工作台页面”是容易识别的：
    - 有“批次 / 计划时间 / 人力负荷”等结构化字段；
    - 右侧 checklist 和 timeline 强化了“过程控制”语义。
  - **潜在问题**：
    - 结构在某些地方接近 `advanced_list + detail` 混合，AI 若只是看局部，很可能把它当成“升级版 list 页”而不是 planning/workspace；
    - 但整体导航文案和 meta 已在一定程度上纠偏。

- **C. 非规范内容污染**
  - 内容主要是为场景定制的 demo 数据，并未出现大量 `TODO` / `占位文本` / 明确的“测试结构”；
  - JS 逻辑仅用于主题切换和 icon 渲染，没有大段与规范无关的实验脚本；
  - 未出现明显 `deprecated` class 或无前缀的临时类名（deprecated 更多在 CSS 层，HTML 本身看不出）。
  - **总体评价**：demo 色彩较强，但更多体现在具体文案，而非结构/类名层面，对 AI 结构参考影响有限。

- **D. AI 参考风险**
  - **场景风险**：低——整页都在强调“生产计划总览”，不太可能被 AI 误判为 dashboard/普通 list。
  - **page_type 风险**：中——结构与 `advanced_list` 接近，若没有 Phase 1 文档背书，AI 可能混淆“planning vs 高级列表”。
  - **结构风险**：中——AI 可能直接把这种“左表 + 右详情 + checklist + KPI 对比”模式推广到所有 list 场景，导致 planning/workspace 模式被过度泛化。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 在后续修复轮中：
      - 在模板注释或文档中更明确标注“**planning/workspace 模式仅在 PRD 明确要求时使用**”；
      - 适度将纯 demo 文案（战机场景）替换为更通用的工业/制造用语，减少“主题粘连”对 AI 迁移的影响；
      - 与 Phase 1 验证文档对齐，在骨架层强调“与 list/detail 的差异点”（例如 checklist/进度对比是 planning 专属）。
  - **规范审查结论等级**：`通过但建议整理（中风险）`
    - 可以继续作为 planning/workspace 的参考资产，但在进入更高权重前，建议先做一轮轻量结构/文案整理。

---

### 1.2 `examples/b-system/b-system-saas.html`

> **资产定位**：`scene = b_system`，`page_types = [saas_admin, operations_workspace]`，`grade = candidate / use_scope = default`，在资产地图中为 **B 次参考（中风险）**，偏 demo 化。

- **A. 角色一致性**
  - 资产地图定位为“通用 SaaS 后台/作业系统壳”，可承载 workspace/运营工作台类场景。
  - 实际 HTML：
    - 标题为“灵境SaaS”，侧栏菜单是典型 SaaS 模块（订阅管理 / 用户权限 / API 管理 / 数据分析 / 账单中心 / 系统设置）；
    - 主内容区是“工作台”式 dashboard：多块 b-stat-card、图表卡、订单表格、快捷操作等。
  - **结论**：角色基本与 `saas_admin / operations_workspace` 一致，是一个合理的 SaaS 控制台 demo。

- **B. 骨架清晰度**
  - 结构上是非常标准的 B 端门户/工作台：
    - sidebar + header + 多块统计卡片 + 图表行 + data table + 快捷操作。
  - 从 AI 视角，很容易被识别为“通用 b_system dashboard/workspace 壳”，**甚至比 `b-system-complete` 更像“常见 SaaS 后台首页”**，这既是优点也是风险。

- **C. 非规范内容污染**
  - 模板中含有大量用 `// 验证点` 标注的注释（深色主题、chart token、button 样式等），明确带有“验证/演示用”属性；
  - JS 部分有完整的 ECharts 配置、主题切换逻辑、console 日志等，逻辑复杂度远高于一般结构示例；
  - 零散出现的内联样式（如 `style="display: grid; ..."`）与 `*-enhanced` 类名，对规范本身影响不大，但会增加 AI 对“哪些是核心结构、哪些是项目级 embellishment”的识别难度。

- **D. AI 参考风险**
  - **场景风险**：中——AI 可能在任何 b_system workspace 任务中默认选择该模板，而忽视 `b-system-complete` / list/detail 等更规范的主参考；
  - **page_type 风险**：中——作为 workspace 控制台没问题，但如果没有明确 PRD，就容易被用于纯列表或单模块页面；
  - **结构风险**：中偏高——过多 demo 内容与 chart 配置可能误导 AI 在其他场景中照搬细节，比如固定的 metric 名称/legend/颜色等。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 审查轮：
      - 在文档层进一步强调“**它是 demo/验证导向的 workspace 壳，不是所有 b_system 场景的默认模板**”；
      - 稍后修复轮中，考虑：
        - 分离 demo-only 脚本与结构；
        - 减少与具体业务（订单、用户姓名、价格等）强绑定的文案，使其更偏向结构型示例；
        - 明确与 `b-system-complete` 的分工关系（homepage vs SaaS workspace）。
  - **规范审查结论等级**：`通过但建议整理（中风险）`
    - 结构可用，但 demo/验证噪音较多，不适合在未清理前就作为高权重主参考，需要后续修复轮重点处理。

---

## 2. `ue5_overlay` 高价值模板

### 2.1 `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`

> **资产定位**：`scene = ue5_overlay`，`page_type = overlay_full_layout`，`grade = candidate / use_scope = limited`，资产地图为 **C 局部参考（高风险）**，对应布局模式 5（双侧面板 + 底 Dock）。

- **A. 角色一致性**
  - 注释与文档对齐：
    - 文件头部明确声明“布局模式 5：双侧面板 + 底部时间轴（数字孪生监控全布局）”，并引用 `docs/ue5-overlay-layout-playbook.md`；
    - 结构严格按照“左/右 pinned detail-panel + 底部 Dock 时间轴”的 cockpit 布局实现。
  - 场景语义（数字孪生总装监控）也与 Mode 5 预期高度一致。
  - **结论**：角色与 `scene/page_type/use_scope` 非常一致，没有出现“用 Mode 5 模板去模拟 Mode 1/2/3”的错位。

- **B. 骨架清晰度**
  - 从结构来看：
    - 顶部 `ue5-overlay-system-bar`，中部 safe-area grid，左/右 detail-panel，底部 timeline dock，外加 overlay world markers —— 完整表达了“full cockpit”模式；
    - JS 部分高度围绕时间轴与图表构建，整体交互层也符合数字孪生驾驶舱的预期复杂度。
  - 对 AI 而言，“这是一个 **数字孪生 cockpit 全布局**”极为清晰，但如果没有 `limited` 语义，很容易被误当成“更高级的通用 overlay 壳”。

- **C. 非规范内容污染**
  - JS 非常长，包含：
    - 自定义 timeline DOM 构造、日期计算、tooltip 行为等；
    - ECharts 配置；
    - 时间更新循环等。
  - 注释中大量使用 `[DEMO]` 标注演示状态（例如 critical banner 初始显示），并给出“生产环境请恢复 display:none”的说明 —— 对人类开发者很有帮助，但对 AI 来说，会增加“哪些是模板骨架，哪些只是 demo 展示”的辨识难度。

- **D. AI 参考风险**
  - **场景风险**：高——若 AI 在普通 overlay 任务中直接选用该模板，会把 cockpit 级复杂度强加给简单场景，违背 Mode 1/2/3 分层；
  - **结构风险**：高——AI 可能将“所有 overlay 都需要双侧面板 + timeline +复杂 detail-panel”的印象带入其他模式；
  - **page_type 风险**：中——由于 `page_type = overlay_full_layout`，若没有文档约束，AI 可能把它当作 overlay 的“终极 canonical”。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 短期（文档级）：
      - 在资产地图与 Guard 说明中进一步强调：该模板 **只作为 Mode 5 cockpit layout 草图**，AI 默认不得选用为主壳；
      - 强调“更多作为布局参考，而非完整 UI 参考”。
    - 中期（修复轮）：
      - 拆分“结构骨架 vs demo 数据/脚本”，将时间轴与告警示例尽量模块化，减轻 AI 理解负担；
      - 在结构上用更明显的 class/注释标注 cockpit 专属模块，强化 limited 边界表达。
  - **规范审查结论等级**：`高风险，后续应优先修复`
    - 结构本身是高价值资产，但 **对 AI 的误导潜力也很高**，应在第一批修复轮中重点处理。

---

### 2.2 `examples/ue5-overlay/digital_twin_overlay_dashboard.html`

> **资产定位**：`scene = ue5_overlay`，`page_type = digital_twin_dashboard`，`grade = candidate / use_scope = limited`，资产地图为 **C 局部参考（高风险）**，混合 `ue5_overlay + b_system` 元素。

- **A. 角色一致性**
  - 注释明确说明这是“数字孪生 + 运控面板混合模板”，左侧三维 Overlay，右侧运控数据面板；
  - HTML 中同时引入 `lingjing-core-ue5-overlay.css` 与 `lingjing-core-b-system.css`，结构上体现了 overlay 场景 + B 端面板混合；
  - 顶部 system-bar、HUD、alert-center、世界锚点、底部 dock 均符合 digital twin cockpit 预期。
  - **结论**：角色定位与实际结构高度一致。

- **B. 骨架清晰度**
  - 安全区中区为 overlay HUD + alert-center + marker，右侧是 b_system 风格 detail-panel；
  - 从任何一个切片看，都很容易理解：“左 3D 场景，右运控面板，底部 dock”，典型数字孪生混合 cockpit；
  - 对 AI 来说，**“这是个混合模板”** 是清晰的，但也因此会成为“混合模式”的强锚点。

- **C. 非规范内容污染**
  - demo 文案多为 C919 总装线场景，仍属“主题示例”，不构成严重 placeholder 污染；
  - 结构中存在若干 project 级 class（如 `flight-metric-card` / `mission-status-board`），但这部分已在组件层有规范，问题不大；
  - JS 仅负责 icon 渲染，没有像 Mode 5 一样的大体量脚本。

- **D. AI 参考风险**
  - **场景风险**：高——如果 AI 在普通 `ue5_overlay` 或普通 `b_system dashboard` 任务中选用此模板，会打乱 scene 边界；
  - **结构风险**：中偏高——AI 可能复制“左 3D + 右运控板”的模式到不需要数字孪生的场景；
  - **page_type 风险**：中——`digital_twin_dashboard` 本身属于少数场景，AI 误用其他 page_type 的可能性存在但可以靠 Guard 缓解。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 文档层：强调“**必须在 PRD 明确数字孪生 + 运控混合需求，且满足 limited 前置条件** 时，由人工确认后才可使用”；
    - 修复轮：
      - 考虑将右侧运控面板拆解为可复用 B 端组件示例，减少“混合模板”在 AI 眼中的黑盒感；
      - 在注释层进一步标明这是“**讨论用草图 / Phase 2 候选**”，而非 canonical。 
  - **规范审查结论等级**：`高风险，后续应优先修复`
    - 与 Mode 5 一样，是数字孪生治理中的关键资产，建议纳入首批修复队列。

---

## 3. `ai_assistant` 高价值模板

### 3.1 `examples/b-system/b-system-ai-assistant.html`

> **资产定位**：`scene = ai_assistant`，`page_type = assistant_workspace`，`grade = limited / use_scope = limited`（已在前一轮修复与 `skill_version.json` 对齐），资产地图为 **B 次参考 + 高风险**。

- **A. 角色一致性**
  - 注释说明其为“B 端 AI 工作台示例，布局：ai-workspace 双栏（左侧 AI 对话 / 右侧排产问题监控）”；
  - HTML：
    - 骨架仍是 `b-layout-sidebar`，但主内容内部非常明确地区分了：左侧 AI 对话 workspace + 右侧监控/问题列表 + chart + data table；
    - 与 Phase 1 验证文档中定义的 assistant_workspace 结构高度匹配。
  - **结论**：在“纯助手工作台 + 问题看板”的典型场景下，角色是高度一致的。

- **B. 骨架清晰度**
  - 侧栏导航 + header 表现的是排产系统的一个 workspace；
  - 核心是 `ai-workspace` 双栏布局：
    - 左栏完整模拟 AI 聊天流、tool-call-card、解决方案步骤；
    - 右栏将监控数据、表格、图表、问题列表组织成一个“问题工作台”。
  - 对 AI 来说，这明显是一种“**AI + 业务工作台融合的助手场景**”，而不是单纯 FAQ 页面。

- **C. 非规范内容污染**
  - 内容高度场景化（CNC-03 / HYD-01 / AGV-07 等），但这些都服务于“问题工作台”叙事；
  - JS 部分：
    - 完整模拟了“问 AI → tool 调用 → AI 回复 → 任务状态更新”的交互链路；
    - 多处硬编码文本、日志、chart 配置等，偏 demo 化；
  - 没有明显 deprecated 类，但 `pj-b-ai-*` 系列类名是典型项目级定制，容易与通用规范混在一起让 AI 误判“所有助手都长这样”。

- **D. AI 参考风险**
  - **场景风险**：高——如果 AI 在 FAQ/轻量问答/仅摘要型助手场景中直接用该模板，会过度引入右侧监控与复杂 chart，违背 limited 边界；
  - **结构风险**：高——AI 很可能将“左 AI chat + 右复杂 workspace”视为所有助手的默认形态；
  - **page_type 风险**：中——`assistant_workspace` 本来就是带 workspace 特征的助手场景，但其他助手类型（纯问答、回顾型等）若被错误映射到此模板，就会出现严重失配。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 文档层（立即可做）：
      - 在资产地图和 Guard 说明中，加强“**这是 limited 工作台壳，仅在 PRD 明确需要‘AI + 工作台’时使用**”的表达；
      - 在 Phase 1 验证文档中，将其明确作为“W1: AI workspace”代表样本，与其它轻量助手形态区分开来。
    - 修复轮（建议优先）：
      - 将核心骨架（ai-workspace 双栏）与 demo 级“排产问题监控”逻辑适度解耦：例如收敛 JS 复杂度、将 demo 数据收拢；
      - 在结构注释中显式标记“最小必需模块”，帮助 AI 分辨哪些是 workspace 壳，哪些是可选模块。
  - **规范审查结论等级**：`高风险，后续应优先修复`
    - 这是 ai_assistant 场景的唯一 workspace 壳，对 AI 参考极其关键，同时具有高误用风险，**应当进入首批修复执行候选**。

---

## 4. `presentation` 高价值模板

> 三个模板共性：`grade = candidate / use_scope = default`，资产地图中为 **B 次参考 / strong candidate（中风险）**。

### 4.1 `examples/presentation/presentation-product.html`

- **A. 角色一致性**
  - 标题与结构均围绕“产品展示 / 产品介绍”：cover + TOC + core advantages + product overview + features + architecture + use cases + closing。
  - 与 `page_type = product_presentation` 定位完全一致。

- **B. 骨架清晰度**
  - 典型 deck 结构：封面 / 目录 / 多 slide 内容块 / 结束页；
  - 每一页都围绕一个主题（核心优势、产品简介、核心功能、技术架构、应用场景等），组织成卡片或三列布局；
  - 对 AI 而言，**“这是一套完整产品 deck 壳”** 非常清晰。

- **C. 非规范内容污染**
  - 存在较多 **内联样式**（`style="..."`），特别是在字体大小、颜色、布局细节上，降低了 class 驱动的一致性；
  - 文案全部是“灵境AI智能体”示例，对结构理解影响不大，但不利于 AI 学习“可重命名”的 slot；
  - JS 仅是通用 `presentation-template.js` + icon 渲染，没有额外实验脚本。

- **D. AI 参考风险**
  - **结构风险**：中——AI 可能把演示中使用的行文顺序（cover → 产品优势 → 产品简介 → 功能 → 架构 → 场景）视作所有 product deck 的唯一正确结构；
  - **规范风险**：中——内联样式会让 AI 误以为“直接写 style 就可以”，削弱 class/token 的规范地位。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 修复轮中：
      - 尽量把内联样式收敛为 class 或 CSS token；
      - 将换行/间距等表达提升到组件/类层级，减少模板内的样式碎片；
      - 在文档中标明“这是强 candidate，但仍在样式/结构上待整理”。
  - **规范审查结论等级**：`通过但建议整理（中风险)`
    - 结构适合作为 AI 参考，但样式规范性不足，建议在进入 canonical 讨论前先做一次规范清理。

---

### 4.2 `examples/presentation/presentation-business.html`

- **A. 角色一致性**
  - 明确以“年度经营分析报告”为主题，目录、内容页围绕 KPI 回顾、经营数据、市场分析、趋势与洞察、下一步计划展开；
  - 与 `page_type = business_report` 精确对齐。

- **B. 骨架清晰度**
  - 结构类似 product deck，但内容更偏分析/报告：
    - KPI 卡片 + timeline + 对比表格 +趋势/洞察 + 下一步计划；
  - 对 AI 而言，是一个非常清晰的 business_report 壳，适合作为结构参考。

- **C. 非规范内容污染**
  - 同样存在较多内联样式，控制字体/颜色/间距；
  - 文案是场景化示例，不是占位符；
  - JS 仅为通用模板脚本与 icon 渲染，规范风险主要在样式层。

- **D. AI 参考风险**
  - **结构风险**：中——AI 可能将示例中使用的 KPIs 与分析维度当成“默认经营报告维度”；
  - **规范风险**：中——与 product 模板相同，内联样式会削弱 class/token 规范。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 与 product 模板一起，在修复轮中统一做样式收敛；
    - 在文档中强化其作为“strong candidate”的地位，但同时明确“**不代表所有经营报告必须采用完全相同的指标与结构**”。
  - **规范审查结论等级**：`通过但建议整理（中风险)`

---

### 4.3 `examples/presentation/presentation-planning.html`

- **A. 角色一致性**
  - 主题为“项目规划模板”，结构包含：项目背景与目标、总体 Roadmap、分阶段计划、资源需求、风险评估等；
  - 与 `page_type = planning_proposal` 对齐良好。

- **B. 骨架清晰度**
  - 结构上是较为完整的规划提案 deck：cover → 背景与目标 → Roadmap → 分阶段计划 → 资源需求 → 风险评估 → 收尾；
  - AI 很容易识别其为“项目规划提案 deck”。

- **C. 非规范内容污染**
  - 内联样式与前两个 presentation 模板类似；
  - **额外问题**：头部脚本引入 `https://unpkg.com/lucide@latest`，没有统一使用本地 `lucide-umd-500.js`，与其它模板不一致；
  - 这会让 AI 误判“在 deck 模板里可以随意用 CDN script”，与 skill 规范（使用本地脚本、可控版本）有偏差。

- **D. AI 参考风险**
  - **结构风险**：中——合乎规划提案预期；
  - **实现层风险**：中偏高——CDN 方式与其它模板不一致，可能对“如何引入资源”的规范产生误导。

- **E. 建议动作 + 审查结论等级**
  - **建议动作**：
    - 修复轮中优先：
      - 将 lucide 依赖统一到本地脚本，与其它 deck 模板对齐；
      - 收敛内联样式，使其更符合组件/类驱动的规范；
    - 文档层中，将此问题作为“实现层规范风险”的典型示例标注出来。
  - **规范审查结论等级**：`通过但建议整理（中风险)`

---

## 5. 各模板规范审查结论等级汇总

| 模板路径 | scene / page_type | 资产层级（参考地图） | 本轮规范审查结论等级 |
|----------|-------------------|------------------------|------------------------|
| `examples/b-system/b-system-production-plan.html` | b_system / planning | B 次参考 | **通过但建议整理（中风险）** |
| `examples/b-system/b-system-saas.html` | b_system / saas_admin, operations_workspace | B 次参考 | **通过但建议整理（中风险）** |
| `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html` | ue5_overlay / overlay_full_layout | C 局部参考（limited） | **高风险，后续应优先修复** |
| `examples/ue5-overlay/digital_twin_overlay_dashboard.html` | ue5_overlay / digital_twin_dashboard | C 局部参考（limited） | **高风险，后续应优先修复** |
| `examples/b-system/b-system-ai-assistant.html` | ai_assistant / assistant_workspace | B 次参考（limited） | **高风险，后续应优先修复** |
| `examples/presentation/presentation-product.html` | presentation / product_presentation | B 次参考（strong candidate） | **通过但建议整理（中风险）** |
| `examples/presentation/presentation-business.html` | presentation / business_report | B 次参考（strong candidate） | **通过但建议整理（中风险）** |
| `examples/presentation/presentation-planning.html` | presentation / planning_proposal | B 次参考 | **通过但建议整理（中风险）** |

---

## 6. 跨模板共性问题

> 本节只总结在“高价值 + 中高风险”模板中重复出现的模式，方便后续考虑是否做统一治理。

- **共性问题 1：内联样式与类驱动规范混用**
  - 主要出现在三个 `presentation` 模板中，也在 `b-system-saas` 中有少量体现：
    - 使用 `style="..."` 调整字体大小、颜色、间距、grid 布局等；
    - 与组件/类名（如 `presentation-glass-card`、`b-stat-card`）共同存在，削弱了“通过类/变量控制视觉”的规范性。
  - **风险**：
    - AI 容易学习到“直接用 style 就行”，在生成新页面时忽略现有 class/token 系统；
    - 后续统一主题/暗色模式时，这些内联样式难以被自动收敛。

- **共性问题 2：demo/场景文案强绑定，削弱通用 slot 表达**
  - 所有高价值模板都使用了很具体的场景叙事（战机生产、C919 总装线、SaaS 订单、具体 KPI 数字等）；
  - 对人类理解结构有帮助，但对 AI 来说，**容易把这些文案当成“字段名/模块名”固定下来**。
  - **风险**：
    - 生成非制造业场景时仍保留“战机/总装线”等用语；
    - 对“哪些是业务字段、哪些是结构标签”辨识度下降。

- **共性问题 3：limited/candidate 模板的“边界表达”在实现层仍不够显性**
  - 在资产地图与 Guard 中，`b-system-ai-assistant`、Mode 5、digital twin 等模板已经清晰标注了 `use_scope = limited`；
  - 但在 **HTML 自身的注释/结构** 中，这种“limited 边界”表达仍偏向“温和解释”，而不是硬性提示：
    - 例如 Mode 5 中仅在注释中说明“[DEMO] 横幅已激活，生产环境请隐藏”，没有更强的“仅数字孪生 cockpit 使用”的提醒；
    - ai-assistant 模板中也没有在结构上突出“这是 workspace，不适用于轻量问答型助手”。

- **共性问题 4：资源引入方式存在少量不一致**
  - 大多数模板使用本地脚本（`../../scripts/lucide-umd-500.js` / `echarts.min.js` / `echarts-theme-lingjing.js`）；
  - `presentation-planning.html` 使用了 `https://unpkg.com/lucide@latest`，破坏了资源引入方式的一致性；
  - 对 AI 而言，这种不一致会放松“使用本地受控资源”的隐性规范。

---

## 7. 第一批修复候选清单

> 本节只给出“下一步值得投入实现层修复/整理”的模板列表，不代表所有问题都要在一轮内解决。

### 7.1 最值得进入下一轮修复的模板（高价值 + 高风险）

- **优先级 1（强烈建议在首个修复执行轮处理）**
  - `examples/b-system/b-system-ai-assistant.html`
    - ai_assistant 场景唯一 workspace 壳，对 AI 行为影响极大；
    - 目前 `use_scope = limited`，但在结构和脚本上仍偏 demo 化，误用风险高；
    - 建议：首轮修复聚焦“骨架清晰化 + demo 逻辑收敛 + limited 边界加强”。
  - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`
    - Mode 5 cockpit 布局草图，是数字孪生治理的核心资产之一；
    - JS 复杂且 demo 注释繁多，极易被 AI 误判为“终极 overlay 壳”；
    - 建议：首轮在结构/注释层做一次精简与边界强化。
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`
    - digital twin 混合模板，对“overlay + b_system”边界有强示范作用；
    - 建议：与 Mode 5 一起，统一梳理数字孪生 cockpit 模式。

- **优先级 2（高价值 + 中风险，适合作为同一修复轮的并行对象）**
  - `examples/b-system/b-system-production-plan.html`
    - 规划/workspace 候选，结构健康，但与 advanced_list/list 的边界尚可强化；
  - `examples/b-system/b-system-saas.html`
    - 通用 SaaS workspace demo，需在“验证 vs 通用模板”之间做更清晰的定位；
  - `examples/presentation/presentation-{product,business,planning}.html`
    - deck strong candidates，需要统一收敛样式、对齐资源引入方式，降低规范噪音。

### 7.2 暂不建议优先处理的模板（当前只需保持现状）

> 注意：下列模板并不“规范正确到无需关注”，而是 **在当前阶段投入产出比不高**，可以在更后续的治理轮次中再处理。

- 所有明确的 **反例 / demo-only** 模板（已在资产地图中标为 D 层）：
  - `b-system-showcase.html`、`b-system-sidebar.html`、`website-showcase.html`、`ue5_overlay_mock_bridge.html`、`presentation-work-report.html`、`presentation-minimal.html`；
  - 本轮已确认其“反例角色”清晰且有 Guard 约束，只需持续保证不被 router/AI 使用即可。
- `ue5_overlay_engine_test.html` 等 testing-only 资产：
  - 只要在文档层标明“测试/engine-only”，并保持不进入 router/matrix 主链，暂不需要做结构/样式层治理。

### 7.3 是否建议启动“小范围模板修复执行轮”

- **建议**：
  - 基于本轮审查，**建议开启一个“高价值有限模板的小范围修复执行轮”**，只覆盖 3–5 个模板：
    - 优先 3 个：`b-system-ai-assistant.html`、`ue5_overlay_sidepanel_dock_layout.html`、`digital_twin_overlay_dashboard.html`；
    - 视资源情况，可以再加 1–2 个 deck 模板（优先 `presentation-business.html`）或 `b-system-production-plan.html`。
  - 修复轮目标：
    - 不做大重构，优先完成：
      - 骨架/注释层“limited/candidate 边界”强化；
      - demo 内容与结构的适度解耦（尤其是脚本）；
      - 样式收敛（移除关键内联样式，提升 class/token 一致性）。

> **一句话判断**：当前审查结果足以为一个“小范围模板修复执行轮”提供明确对象和优先级，且修复范围可以控制在 3–5 个对 AI 行为影响最大的模板之内。

---

## 8. 首批修复执行回写（2026-04）

- **本轮实际处理的模板**：
  - `examples/b-system/b-system-ai-assistant.html`（ai_assistant / assistant_workspace）
  - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`（ue5_overlay / overlay_full_layout, Mode 5）
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`（ue5_overlay / digital_twin_dashboard）
  - `examples/presentation/presentation-business.html`（presentation / business_report deck，优先级 2 补位修复）
- **处理方式（实现层）**：
  - 对前三个 limited cockpit / assistant 模板：仅在 HTML 内增加/强化注释、aria-label 与少量文案，明确 `use_scope = limited`、cockpit/digital_twin 角色以及 demo-only 脚本的边界；
  - 对 `presentation-business`：增强文件头与各章节 slide 的角色注释，去除一处明显的标题内联样式，并在关键要点处标明“示例业务内容”，降低业务文案对骨架识别的干扰；
  - 全部改动均未修改任何 scene / page_type / use_scope / grade 配置，也未对结构骨架做重构级改动。
- **AI 参考风险变化**：
  - 对前三个模板，AI 在读取模板本身时更容易理解「这是 limited cockpit / assistant_workspace 草图」而非通用壳，误把限用模板当作默认主壳的风险降低；
  - 对 `presentation-business`，AI 更容易一眼识别其为 business review / QBR deck，而非 dashboard/website，且示例内容与结构被明确区分；
  - demo 脚本和样例数据被标明为示例用途，有助于 AI 将“结构模式”与“场景叙事内容”分离。
- **保留到后续的工作**：
  - ai-assistant workspace 与 Mode 5 / digital twin 模板仍然保留原有的复杂交互与场景文案，后续如需进一步降噪或抽象组件，需要单独的结构/脚本级治理轮；
  - presentation-business 仍然有较强的场景化指标与文案，仅做了轻量收敛，未来如需升级为 canonical，需要更系统的样式与内容规范整理。