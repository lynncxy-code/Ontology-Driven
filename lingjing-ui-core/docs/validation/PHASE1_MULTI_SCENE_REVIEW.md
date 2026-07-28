# PHASE 1 · 多 scene 收官评估（b_system / ue5_overlay / website / ai_assistant / presentation）

> **目的**：站在跨 scene 总盘面上，对当前 Phase 1 的治理状态做一次统一评估，明确：
> - 各 scene 当前处于 W1 / Guard / observation 的哪一阶段；
> - Phase 1 在“方法层”到底解决了哪些问题；
> - 哪些问题仍是 observation 项、暂不进入 Phase 2 的原因；
> - 何时才算具备进入“模板族治理 / canonical 收敛 / page_type 深化”阶段的前置条件。

---

## 1. 场景状态矩阵（Phase 1 截止）

> 覆盖 `b_system` / `ue5_overlay` 主线场景，以及扩展场景 `website` / `ai_assistant` / `presentation`。

| scene | 当前阶段 / 状态 | 独立验证文档 | Guard 条款落点 | 模板治理成熟度（canonical / candidate / anti_pattern） | 主要风险 / 观察点 | 当前建议状态 |
|-------|-----------------|--------------|----------------|------------------------------------------------------|---------------------|---------------|
| `b_system` | Phase 1 主线闭环 + **长期 observation** | `docs/system-template-map.md`（类型映射）、`PHASE1_REGRESSION_BASELINES.md`、`PHASE1_GENERATION_PLAYBACK.md` | `EXTENSION_GUARD` §1.1–1.2、§3.3、§3.5–3.9 等 b_system 专向 Guard | list / advanced_list / detail 已有明确主模板族（task_router + template_router + matrix 对齐），壳与 Level 规则清晰；demo/limited/blacklist 由 `skill_version.json` + Guard 约束 | 仍标记为“基本稳定”而非“完全稳定”；复杂 workspace 组合 & 跨业务域 cockpit 型工作台在实践中仍会暴露新形态 | 作为 Phase 1 **主锚场景**进入 observation mode：优先用它校验新的 Guard / routing / audit 设计，暂不做更重级 canonical 收敛实验 |
| `ue5_overlay` | Phase 1 主线闭环 + **长期 observation** | `docs/ue5-template-map.md`、`PHASE1_REGRESSION_BASELINES.md`、`PHASE1_GENERATION_PLAYBACK.md` | `EXTENSION_GUARD` §1.3、§3.1–3.3、§3.7–3.10 等 | Mode 1 / 2 / 3 / minimal 的布局模式与壳结构已固化，并由 matrix + Guard 守护；minimal 从灰区样本升级为显式任务 id；demo/engine_test 有 blacklist/limited 约束 | cockpit 与普通 overlay 之间仍有演化空间；3D 视图与后台列表/工作台的组合在更多真实项目中可能暴露新需求 | 同样进入 observation mode，作为 `b_system` 的对位主线；后续复杂多 scene 混合（website + cockpit + assistant）都应先回到这一主线检视 |
| `website` | Phase 1 扩展场景：**W1–W3 完成 + 观察中** | `docs/WEBSITE_PHASE1_VALIDATION.md` | `EXTENSION_GUARD` §1.7（landing / feature / pricing 边界）、§1.1 部分 scene 边界；demo/limited 由 §3.3 约束 | homepage (`website-complete.html`) 作为 landing/pricing 的 canonical 壳；`website-feature-solution.html` 作为 feature 的 primary example；anti_pattern / demo 模板收口在 `examples/README.md` 与 matrix 中 | pricing 仍共用 homepage 壳，尚未形成独立 canonical 模板；blog/docs/portal 等页型未纳入本轮；website vs b_system / ue5_overlay 在更多行业样本下仍需观察 | 对 `landing/feature/pricing` 子集进入 observation mode：不扩新页型、不拆新模板，所有新需求优先按现有 3 页型 + Guard 跑一轮，积累证据后再考虑 Phase 2 |
| `ai_assistant` | 扩展场景：**W1 验证 + 最小 Guard patch 完成 + 初始 observation** | `docs/AI_ASSISTANT_PHASE1_VALIDATION.md` | `EXTENSION_GUARD` §1.5 / §1.8 / §3.4 + 新增 ai_assistant 限定条款（limited 模板、防误用、b_system vs ai_assistant 边界） | 仅有一个核心模板 `b-system-ai-assistant.html`，标记为 `scene = ai_assistant`, `grade = limited`；只承接 `assistant_workspace`，无 canonical 多模板族；anti_pattern 主要体现在“误用路径”而非独立模板 | cockpit + assistant + website 的三方混合边界仍主要靠验证文档中的协议说明；潜在助手子类型（轻量问答、review 页）缺样本支撑；Level 升级逻辑尚未进入 Guard | 在 limited 模板防误用与 b_system 边界 Guard 已落地的前提下，进入 **受控 observation mode**：继续累积真实混合样本，在文档层迭代规则，暂不拆 page_type、暂不扩模板族 |
| `presentation` | 扩展场景：**W1 验证 + 最小 Guard patch 刚完成（早期 observation）** | `docs/PRESENTATION_PHASE1_VALIDATION.md` | `EXTENSION_GUARD` 新增 §1.9（presentation vs website）、§1.10（presentation vs b_system） + §3.3 中 work-report/minimal anti_pattern 防误用 | 3 个 candidate 模板（product/business/planning）+ 2 个 anti_pattern 模板（work-report/minimal），文档层给出 strong candidate / anti_pattern 说明；真值源层仍标为 candidate / 兼容支持，未晋级 canonical | 样本数量相对 website/ai_assistant 更少；presentation vs website/b_system 边界刚写入 Guard，一些多 scene 组合（deck + cockpit + website + assistant）仍只在验证文档中记录；TRUTH_SOURCES 仍将其视为兼容支持场景 | 视为 **W1 + Guard 初步落地，刚切入 observation**：优先用现有样本做 Guard 回归，不建议马上升级为 canonical 模板族或扩 page_type，继续补真实 deck 样本与混合场景观察 |

> 备注：`TRUTH_SOURCES.md` 当前仍将 `website` / `ai_assistant` / `presentation` 标为“兼容支持”，本表是在 Phase 1 迭代之后，对其实际治理状态的 **细化分层**（“兼容支持 + 已完成最小治理闭环 + 进入 observation”）。

---

## 2. Phase 1 跨 scene 已经解决的关键问题（方法层）

> 不按单 scene 复读，而是总结这一轮在“治理方法与机制”上已经收口的成果。

- **scene 边界从“口头约定”升级为“可执行协议 + Guard 条款”**：
  - b_system vs website / ue5_overlay / ai_assistant / presentation 的边界，已经通过 `EXTENSION_GUARD` + 各 scene 验证文档中的规则（触发条件 + 推荐补问 + 判定方向）固定下来；
  - website / ai_assistant / presentation 各自都有“场景 vs b_system/其它”的 stop&ask 条款，不再完全依赖人为记忆与临场判断。

- **验证文档路径在多 scene 上统一跑通**：
  - `WEBSITE_PHASE1_VALIDATION` / `AI_ASSISTANT_PHASE1_VALIDATION` / `PRESENTATION_PHASE1_VALIDATION` 形成三套结构相似的 W1 文档：
    - 清晰的“验证范围与前提 + 首批样本表 + 逐条验证记录 + W1 边界结论 + Guard 建议稿 + Guard 回归样本 + Guard readiness 判断”；
  - 这套“先文档、后 Guard、再 observation”的流程已经从 b_system / ue5_overlay 主线，推广到了 website / ai_assistant / presentation 三条扩展 scene。

- **Guard 的角色从“附属说明”升级为“防止万能场景/万能模板吞并”的制度化护栏**：
  - website：
    - §1.7 把 landing / feature / pricing 的边界写成 stop&ask 条款，实际阻止了“万能 homepage 吞 feature/pricing”的老问题；
  - ai_assistant：
    - 新增条款明确“有聊天框 ≠ ai_assistant”“仅为好看借壳 ≠ 合规使用 limited 模板”，防止 `b-system-ai-assistant.html` 退化为“万能后台壳”；
  - presentation：
    - §1.9 / §1.10 把“deck vs website / b_system”的典型混合诉求托管给 Guard，避免“万能 deck 页”或“万能工作台”继续膨胀。

- **anti_pattern / limited 模板从“标签”升级为“可执行约束”**：
  - b_system / ue5_overlay：
    - engine_test / demo_only / limited 模板已由 skill-audit + Guard 双重约束，不能进入主路由或被误认 canonical；
  - ai_assistant：
    - `b-system-ai-assistant.html` 的 limited use_scope 在 Guard 中有明确“允许/禁止/需 stop&ask”的条件，误用路径（后台首页借壳）有专门条款拦截；
  - presentation：
    - `presentation-work-report.html` / `presentation-minimal.html` 的 anti_pattern 定位不仅在 template_router 中打标签，还在 Guard 中写明了“误用语义信号 + 回退到哪些 candidate 模板”的具体策略。

- **observation mode 不再是“模糊状态”，而是有条件的轻量阶段**：
  - 对 b_system / ue5_overlay 主线：Phase 1 完成后，进入的是“有回归 runner + 审计脚本 + 模板/Guard 一致性检查”的 observation；
  - website / ai_assistant / presentation：
    - 先完成 W1 验证文档 + Guard 最小 patch + 文档级回归，然后才被允许进入“有限 scope 的 observation”，且每个 scene 都在自己的文档里写出了 Phase 2 准入条件；
  - 这意味着“观察期”本身也具有方法论：**以样本与 Guard 回归为主，不在此阶段扩模板/扩 page_type**。

- **“先 Guard / router 收口，再考虑模板族分化”的优先级得到跨 scene 一致确认**：
  - website 的 pricing、ai_assistant 的潜在子类型、presentation 的 canonical，都在各自文档中给出了“暂不拆模板/扩 page_type”的理由与触发条件；
  - Phase 1 没有再走“凭想象先扩模板，回头再补 Guard”的老路，而是坚持“**Guard 与路由先稳定起来，再用真实样本证明现有壳真的扛不住**”。

---

## 3. 仍未解决的问题与 observation 项（跨 scene）

> 这一节聚焦“现在知道有问题，但目前 **刻意** 只当 observation，而不是立刻进入 Phase 2 的点”。

### 3.1 canonical 仍不够“铁”的场景 / 模板族

- **b_system / ue5_overlay**：
  - 虽然已有清晰的 primary templates / candidate_templates，并通过回归与审计验证“基本稳定”，但 TRUTH_SOURCES 仍刻意不用“完全稳定/最终 canonical”的表述；
  - 登录态 cockpit、跨业务域 workspace、多类型模块拼接等复杂场景，还没有完全收敛到少数模板模式上。

- **website**：
  - `website-complete.html` 极大概率是 homepage canonical，但对于 pricing 是否要分化出独立 canonical 壳、feature 是否继续裂解子类，仍在观察；
  - blog / docs / portal / case-library 等页型暂未纳入本轮，canonical 讨论为时尚早。

- **ai_assistant**：
  - 只有一个 limited 模板 `b-system-ai-assistant.html`，还谈不上“模板族 canonical 收敛”；
  - 未来是否需要轻量问答页 / review 页等子类型，完全依赖后续样本。

- **presentation**：
  - 文档层给出了 `presentation-product` / `presentation-business` 的 **strong candidate / potential canonical** 判断，但真值源层仍标记为 candidate，且 `TRUTH_SOURCES` 中对该 scene 的定位仍是“兼容支持”；
  - 当前 deck 样本数量与生产实践尚不足以支撑 canonical 晋升。

### 3.2 page_type 仍是“文档级轮廓”的位置

- **website**：
  - `landing` / `feature` / `pricing` 虽已有 router 与 Guard 支撑，但更多细分 page_type（案例页、Docs、Portal 等）仍只在脑内/口头层面存在；
  - 是否需要正式进真值源，取决于后续真实任务是否形成稳定模式。

- **ai_assistant**：
  - 仅有 `assistant_workspace`，验证文档中提到的“轻量问答型助手页”“review/回顾页”等都明确标记为观察项；
  - 这些 page_type 目前只是概念层，不是真值源的一部分。

- **presentation**：
  - `product_presentation` / `business_report` / `planning_proposal` 在 router 与验证文档中有轮廓，但 page_type 族的深度（例如 training_deck、storytelling_deck）仍未知；
  - 未来是否要扩 page_type 要看真实 deck 的演化，而不是现在拍脑袋细分。

### 3.3 跨 scene 混合问题：只做了最小 Guard，不足以支撑 Phase 2

- **website + b_system / ue5_overlay / ai_assistant**：
  - 当前 Guard 足以阻止 website 静默吞 dashboard/workspace/cockpit/assistant，但对于大量“品牌 + 工作台/驾驶舱/助手”的混合需求，只给出了“拆任务优先”的通则；
  - 尚未形成一套“多 scene 组合模式”的稳定谱系（例如官网 + cockpit + assistant 三页组合的标准形态）。

- **ai_assistant + b_system + ue5_overlay**：
  - cockpit + assistant + overlay 的复杂交集，目前主要通过 ai_assistant / ue5_overlay 验证文档中的协议说明来处理；
  - Guard 中只落地了最关键、最保守的一层（例如“cockpit 页整体不得切为 ai_assistant”），更细粒度的 orchestrate 场景仍需长期观察。

- **presentation + website / b_system / ai_assistant**：
  - 本轮 Guard patch 只落了 presentation vs website / b_system 的基础条款；
  - 对“官网 + deck + cockpit”“助手生成 deck + cockpit + website”这类多重组合，仅在 PRESENTATION 验证文档中做了方向性说明，没有进入 Guard 或模板决策层。

### 3.4 anti_pattern / candidate / canonical 分层仍在“收敛过程中”的点

- **b_system / ue5_overlay**：
  - demo / engine_test / anti_pattern 模板在主线场景中已有较清晰边界，但随着更多真实项目积累，可能暴露出新的 anti_pattern 模式需要追加；

- **website**：
  - `website-showcase.html` 这类组件展厅仍然是“demo/辅助”，未来是否会沉淀新的 anti_pattern（例如“极端视觉 homepage”）要看实践；

- **ai_assistant**：
  - 当前大部分“错误用法”还以行为路径（借壳 / 滥用 limited）形式出现，而不是独立的 anti_pattern 模板；

- **presentation**：
  - work-report / minimal 之外，未来在 deck 形态上可能出现新的 anti_pattern（例如“所有业务 deck 都只剩两页”等），需要 observation 期更多 deck 样本来发现。

### 3.5 “模板族太散但证据不足以集中治理”的风险

- 多个 scene 中都存在“目前模板族偏散，但还没有足够证据说明哪一两套壳值得晋升 canonical”的状态：
  - website 的 pricing；
  - ai_assistant 可能的轻量问答 / review 壳；
  - presentation 之外其他潜在 deck 类型；
- Phase 1 有意没有用“模板族碎片化”为由提前硬拉一个 canonical，而是把“集中治理”留给 Phase 2，并在各自文档里写明了触发条件。

---

## 4. 是否进入“模板族治理 / Phase 2”？— 当前判断

> 问题拆成两层：**1）是否建议“全面进入” Phase 2；2）是否有小范围可以尝试试点。**

### 4.1 全局结论：**不建议现在全面进入 Phase 2 模板族治理**

- **样本总量与覆盖面仍偏主线 + 部分扩展**：
  - b_system / ue5_overlay 虽有较丰富样本与回归基线，但 website / ai_assistant / presentation 仍主要集中在首轮高价值样本和少量混合场景；
  - 想要对“跨 scene 模板族”做系统收缩，目前样本密度不够。

- **Guard 与路由刚在扩展 scene 落地，仍需要 observation 期验证稳定性**：
  - website / ai_assistant 的 Guard patch 已通过文档级回归，但真正的“线上任务 + 收敛样本”还没跑够一轮；
  - presentation 的 Guard patch更是刚刚落地，贸然做 canonical 收敛会让未来调整成本变高。

- **TRUTH_SOURCES 明确写到“当前尚无标记为完全稳定的场景”**：
  - b_system / ue5_overlay 的 Type/Mode 组合被标注为“基本稳定”，这在本文语境中更接近“Phase 1 主线闭环 + Observation”，而非“可以随时锁死 canonical”；
  - 在这种前提下推动全局 Phase 2 容易僵死模板族，限制后续演化。

### 4.2 是否有局部已经“接近 Phase 2” 的区域？

在现有证据下，**可以标记出“相对成熟、未来适合优先评估 Phase 2 的候选区域”**，但仍建议暂时只作为“下一个阶段的优先备选”，而非立即启动：

- **b_system 的 list / advanced_list / detail 三类任务族**：
  - 优点：
    - 主模板族、shell、Guard、回归样本最齐全；
    - `system-template-map` 已经承担了半个“模板族治理文档”的角色；
  - 风险：
    - 真实项目中 workspace/portal 类页面的复杂度尚未完全展现，提前做 canonical 收缩可能压缩未来演化空间。

- **website 的 landing / feature 子族**：
  - 优点：
    - homepage canonical (`website-complete.html`) 与 feature primary example (`website-feature-solution.html`) 在多轮样本中表现稳定；
  - 风险：
    - pricing 与未来 blog/docs/portal 仍在观察；
    - 过早定义“官网模板族”的 canonical 可能妨碍后续在更多行业形态上的探索。

> 综合来看：**这些区域更适合作为后续 Phase 2 的优先候选，而不是立刻进入 Phase 2**。当前更合理的做法，是先通过跨 scene 的 observation 机制，把这些候选区域的真实使用证据继续堆厚。

---

## 5. 下一阶段主线建议

> 假设当前阶段目标是“Phase 1 收官，而不是直接 Phase 2 起步”，下面给出更保守、可执行的下一阶段主线建议。

### 5.1 情况 A：整体不进入 Phase 2（推荐路径）

**推荐将下一阶段主线设定为：跨 scene 的 observation 机制固化 + canonical 候选观察，而非立即晋级。**

- **主线 1：建立统一的 multi-scene observation 机制**：
  - 为 b_system / ue5_overlay / website / ai_assistant / presentation 建立统一的“新任务登记与回填”流程：
    - 每个新任务记录：scene / page_type / template / 是否命中 Guard / 是否出现人为 override；
    - 当出现越界或高歧义时，要求回填到对应 scene 的验证文档（样本章节）。

- **主线 2：在文档层维护 canonical 候选 watchlist**：
  - 在各 scene 的验证文档或新增的小节中，维护一份“canonical 候选模板清单”，记录：
    - 当前候选模板；
    - 最近 N 个真实任务中命中次数 / 遭拒次数；
    - 与其它模板相比的优势/不足；
  - 只要还停留在文档层，就不改真值源中的 canonical 字段。

- **主线 3：扩展回归与生成回放，但不过度扩模板族**：
  - 适度将 website / ai_assistant / presentation 的关键样本纳入 `PHASE1_REGRESSION_BASELINES` 或新建的 multi-scene 回归文件；
  - 对典型多 scene 组合（官网 + dashboard + assistant / deck + website + workspace）做极少数“生成回放”样本，用来验证现有 Guard 是否足够，而不是用来 justify 新模板。

### 5.2 情况 B：若需要局部 Phase 2 试点（保守建议）

若后续确实需要挑一块做 Phase 2 试点，我建议：

- **仅考虑 b_system 的 list / advanced_list / detail 模板族** 作为第一优先：
  - 理由：
    - 该区域的任务密度最高，回归/审计/生成样本最丰富，canonical 候选已经在实践中反复被验证；
    - 对其它 scene 的依赖较少，局部调整风险相对可控；
  - 限定范围：
    - Phase 2 试点只处理现有 list / advanced_list / detail 模板族的 canonical/anti_pattern 收敛与 Level 深化；
    - 不扩新 scene、不触碰 website / ai_assistant / presentation 的 canonical 判断；
    - 不借机重写 EXTENSION_GUARD 结构，仅根据试点结果微调 b_system 局部条款。

> 即便如此，**不建议在当前这个轮次马上启动试点**，而是先用一段 observation 期确认多 scene Guard 与路由足够稳定，再单独立项处理。

---

## 6. “何时才算可以进入更重治理（Phase 2）”的触发清单

> 从多 scene 视角抽象出一组 **跨场景通用的 Phase 2 触发条件**，避免靠主观感觉切阶段。

### 6.1 样本与使用模式视角

- **触发条件 1：多个 scene 中，canonical 候选在真实任务中反复胜出**：
  - 某个模板（或模板小族）在对应 scene 内的任务中被稳定命中，且替代方案极少；
  - 在回归与生成回放中，该模板一再表现出较好的承载力与少量 patch 即可适配；
  - 相比之下，其它 candidate 模板长期处于“几乎不用”或“仅 demo”状态。

- **触发条件 2：anti_pattern / limited / demo 分层在实践中足够稳定**：
  - 被标为 anti_pattern / limited / demo 的模板，在真实任务中基本只作为反例/测试存在，很少出现合规使用需求；
  - Guard 与 audit 已能稳定阻止它们进入主路由，不存在反复绕过约束的情况。

- **触发条件 3：page_type 新增需求呈现出连续、稳定模式**：
  - 新的 page_type（例如 website 的某种案例页、ai_assistant 的轻量问答页、presentation 的 training deck）在多项目中反复出现；
  - 需求描述、信息架构、交互路径高度相似，已经形成“肉眼可见的模式”；
  - 现有 page_type / template 需要多次大改才能勉强承载。

### 6.2 Guard 与 scene 边界视角

- **触发条件 4：现有 Guard 在复杂混合场景下出现系统性不足**：
  - 多个 scene 的 observation 记录中，频繁出现同一类混合场景（如“官网 + cockpit + assistant”“deck + workspace + cockpit”）难以通过现有 Guard 处理；
  - 业务与设计方面也给出反馈：现有 Guard 提示不足以帮他们拆清场景/任务。

- **触发条件 5：跨 scene 混合页面从“例外”变为“常态”**：
  - 大量真实项目都要求“官网 + cockpit”“官网 + 工作台”“cockpit + assistant”“deck + website + workspace”等组合；
  - 在这种情况下，仅靠“拆任务 + 现有 Guard 提醒”已经明显不够，需要考虑更系统的“多 scene 组合模式”和桥接层治理。

### 6.3 真值源与实现视角

- **触发条件 6：scene / page_type / template 的真值源长期稳定，无频繁回退**：
  - `scene_coverage_matrix.yml` / `skill_version.json` / router 中关于某 scene 的配置在多个版本间保持高度一致，仅有小修补；
  - 不再出现“频繁变更 primary_template / preferred_level / use_scope”的情况。

- **触发条件 7：审计结果长期提示结构性问题**：
  - audit 与 regression 中反复暴露出某类结构问题（例如 pricing 被 homepage 壳压扁、某类 cockpit 反复触发“壳过重/壳过轻”警告）；
  - 且这些问题无法通过简单模板 patch / Guard 调整解决，指向“模板族本身设计需要升级”。

### 6.4 组织与流程视角

- **触发条件 8：团队对当前 Phase 1 结果的共识度高**：
  - 设计 / 前端 / AI 中间层对现有 scene 边界、Guard 行为和模板分工有较强共识，不再大量争论“到底是不是这个 scene”；
  - Phase 1 的文档（各 scene 验证文档 + EXTENSION_GUARD + template-map）在日常工作中被实际使用，而不是停留在仓库角落。

- **触发条件 9：有明确业务驱动需要更重治理**：
  - 例如某个模板族成为多个产品线的共用壳，任何结构升级都会影响大量业务；
  - 在这种情况下，用更重的 Phase 2 治理（canonical 收敛 / Level 深化 / 更强审计）来换取中长期稳定性是有明确 ROI 的。

> 当上述多类触发条件在某个局部（例如 b_system list/detail 模板族、website landing/feature 子族）上集中出现时，再单独为该局部立项 Phase 2 更重治理；在此之前，当前“Phase 1 + observation” 结构已经足够支撑安全扩展与风险可控演化。

---

## 7. 收尾结论（Phase 1 多 scene 总盘）

- **修改文件清单**：
  - 新增：`docs/PHASE1_MULTI_SCENE_REVIEW.md`（本文件），作为跨 scene 的 Phase 1 收官评估文档；
  - 未修改任何 router / matrix / Guard / HTML 模板 / 样式或实现。
- **每个核心 scene 当前状态**：
  - `b_system` / `ue5_overlay`：Phase 1 主线闭环，进入长期 observation mode，是后续多 scene 决策的主锚；
  - `website`：landing/feature/pricing 子集完成 W1–W3 与 Guard 落地，进入有限 scope 的 observation mode；
  - `ai_assistant`：W1 + 最小 Guard patch 完成，limited 模板与场景边界可控，进入初始 observation；
  - `presentation`：W1 + 最小 Guard patch 刚落地，处于 W1 与 observation 之间的早期阶段，需要更多 deck 样本支撑。
- **是否建议现在进入更重模板族治理 / Phase 2**：
  - **不建议全面进入**；只建议将 b_system list/detail 模板族、website landing/feature 视为未来 Phase 2 的优先候选区域，在后续 observation 期专门关注它们的证据积累；
- **一句话总结**：
  - Phase 1 在多 scene 上的“最小治理闭环”（验证文档 + 边界样本 + Guard 最小落地）已经跑通，本轮可以视为 **Phase 1 收官 + 进入跨 scene 观察期** 的合适节点，后续重治理应谨慎、按触发清单逐块推进，而不是一次性全面升级。