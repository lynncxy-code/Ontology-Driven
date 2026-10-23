# MULTI_SCENE_OBSERVATION_CYCLE · Phase 1 多 scene observation 第一次正式周期运行说明

> **文档目的**：在已验证可运行的 observation 协议与样本归档演示基础上，给出一套**可持续执行的第一次 observation 周期运行方案**，把“机制”落成“工作流”。
>
> **目标**：明确在一个 observation 周期内——
> - 哪些新任务/新样本需要被记录；
> - 记录后如何分类、回填、计数与升级；
> - 周期节奏如何安排；
> - 周期结束时需要产出什么；
> - 以及第一次正式 observation 周期推荐如何启动。
>
> **适用范围**：当前覆盖 `b_system` / `ue5_overlay` / `website` / `ai_assistant` / `presentation` 五个 core scene 的 Phase 1 后续运行阶段；后续如扩展 scene，可复用同一工作流。

---

## 1. 观测周期的“输入范围”

> 这一节回答：**在 observation 周期内，哪些新任务/样本必须被记录，哪些可以选择性记录，哪些可以明确不记。**

### 1.1 必须记录的样本（强制纳入 observation）

满足以下任一条件的新任务/新样本，**必须**进入 `MULTI_SCENE_OBSERVATION_EXAMPLES.md` 或后续同类 observation 记录中：

- **跨 scene 边界 / 混合诉求**
  - 同一任务中，同时出现两个及以上 scene 的强信号：
    - 如 `dashboard + assistant`（`b_system` / `ue5_overlay` + `ai_assistant`）；
    - `deck + website` 双产物（`presentation` + `website`）；
    - `cockpit + website` / `cockpit + workspace` 等多 scene 组合。
  - 已有代表样本：`ai_assistant_case_dashboard_plus_assistant`、`presentation_case_topic_deck_plus_site`。

- **命中 stop&ask 的需求**（无论最终分类落在三档中的哪一档）
  - 任何由 `EXTENSION_GUARD` / scene Guard 触发 **stop&ask** 的任务：
    - 如 `landing vs pricing` 边界；
    - `presentation vs website` 互相吞噬；
    - `ai_assistant` 与 `b_system` 主任务不清晰等。
  - 理由：stop&ask 代表“规则 & 真值之间存在紧张点”，需要在 observation 中被长期追踪与计数。

- **命中 anti_pattern / limited 模板误用信号的需求**
  - 任何涉及：
    - 使用 `grade = anti_pattern` 模板（例如 `presentation-work-report.html`）；
    - 试图将 `limited` 模板当作主链 canonical 使用；
    - 将 anti_pattern 模式包装成“默认模板”或“通用壳”的诉求。
  - 典型代表：`presentation_case_work_report_template_misuse`。

- **现有“观察中”模式的典型延续样本**
  - 与已在 `MULTI_SCENE_OBSERVATION_EXAMPLES.md` 中标记为 `观察中` 的模式高度相似：
    - 重度 pricing 页仍落在 homepage 壳；
    - dashboard + assistant 并置；
    - deck + site 双产物等。
  - 要求：
    - 只要是 **结构上有增量信息** 的延续样本，就应记录；
    - 若仅是文案/配色变化，不带来结构/边界新信息，可归入“可选记录”。

- **可能影响 canonical / page_type / Guard 判断的新模式**
  - 任一样本在 scene 评审中被明确认为：“如果这种模式变多，可能需要：
    - 调整 canonical 模板族；
    - 调整 page_type 划分；
    - 调整关键 Guard 条款。”
  - 例如：
    - 新型组合 cockpit（如 `3D cockpit + 多 tab workspace + assistant` 的三合一场景）；
    - 与现有 canonical 壳在信息结构上有显著差异的高优先级任务。

- **对主链模板构成潜在风险的异常样本**
  - 如：
    - 强烈要求把 `anti_pattern` 模板纳入默认路由；
    - 要求用 `landing` 壳承载复杂 back-office 工作台；
    - 要求用 `ai_assistant` 壳替代 `b_system` cockpit 等。
  - 这些样本即便只有 1 次，也必须被记录，以便后续计数与复盘。

### 1.2 可选记录的样本（视精力与信息增量决定）

满足以下条件的样本，可以 **视周期工作量与信息增量** 选择记录或不记录：

- **完全重复、无新增信息的“已知稳定”样本**
  - 与已有 `已知稳定` 样本在结构、交互、业务诉求上高度一致，仅是：
    - 文案品牌不同；
    - 颜色/插画更换；
    - 数据字段略微调整。
  - 若当前周期对该模式的稳定性已有足够信心，可不逐条记录，仅在周期小结中按“出现次数”做粗略统计。

- **已有大量同类记录的基础正例**
  - 如：常规 `landing`、常规 `list`、常规 `product_presentation` 等。
  - 当同一模式在 observation 文档中已出现多次且无边界新信息时，可不再增加单条记录，仅在小结中维护“计数”。

- **中低优先级、与主链无强耦合的边缘样本**
  - 对 scene/模板边界影响较小，仅影响个别二级模块、样式偏好等；
  - 若当期资源有限，可先不纳入 observation，后续若模式演化升级，再回溯补充代表样本即可。

### 1.3 明确不需要记录的样本

为避免 observation 被“所有样本都记”拖垮，以下类型**默认不进入 observation 记录**：

- 纯 UI 皮肤 / 主题切换诉求（色板/字体/边角圆润度等），不涉及结构与 scene/page_type 边界；
- 单纯文案润色、语言版本切换（中英、双语等），不改变信息架构；
- 仅在组件粒度做小调整的需求：
  - 如按钮文案、单个表格列增删、单个 form 项优化等；
- 已在 scene 验证文档中有充分覆盖，且本次样本未引入任何新 Guard 信号的普通正例。

> 简化口径：**只要新样本会“拉扯 scene 边界 / canonical 模板 / Guard 判定”，就应进入 observation；否则就可以只停留在各 scene 自身的验证/真值文档里。**

---

## 2. 观测周期内的标准动作链

> 这一节把 observation 周期内的操作流程，写成**可执行的标准动作链**，而不是松散建议。

整个动作链可抽象为：

> **新样本出现 → 判断是否需要记录 → 按协议记录 → 三档分类 → 决定回填 → 计数与聚类 → 判断是否升级 → 周期小结与落盘。**

### 2.1 步骤 0：判断“是否进入 observation”

1. 新任务/新样本出现时，先按第 1 节的规则进行快速判断：
   - 命中 **1.1 必须记录** 条件 → 进入 observation；
   - 命中 **1.2 可选记录** 条件 → 视当期精力决定；
   - 命中 **1.3 明确不记** 条件 → 不进入 observation，仅在 scene 层处理。
2. 一旦决定“进入 observation”，立即进入步骤 1。

### 2.2 步骤 1：按统一协议记录样本

1. 在 `MULTI_SCENE_OBSERVATION_EXAMPLES.md` 或后续拆分出的 observation 文档中新增一条记录：
   - 完整填写 `MULTI_SCENE_OBSERVATION_EXAMPLES.md §1` 中给出的统一字段：
     - 样本 ID
     - 所属 scene / 关联 scene
     - 输入描述
     - 当前预期 scene / page_type / template
     - 是否触发 stop&ask
     - 命中的 Guard / 验证文档结论
     - 当前归类（暂时可先给出“草案”分类）
     - 是否需要回填到具体 scene 验证文档
     - 是否足以触发升级动作（当前时点）
     - 简短说明
2. 对于首次出现的新模式：
   - 样本 ID 建议使用 `scene_case_<简短描述>` 或 `pattern_<模式名>_v1` 形式，便于后续聚类与计数。

### 2.3 步骤 2：进行三档分类

在记录字段后，对样本进行首次三档归类：

- **“已知稳定”**
  - 条件示例：
    - 已有多个类似样本稳定落在同一 scene/page_type/template；
    - Guard 未产生冲突或 stop&ask，仅作为轻量提醒；
    - 不指向任何立即的规则/模板升级动作；
  - 处理原则：
    - 记录为“绿色锚点”，用于未来监测是否被误杀或退化，不推升级。

- **“观察中”**
  - 条件示例：
    - 当前处理方案可接受，但明确存在 open 问题（如 pricing 是否需要独立模板）；
    - 或初次出现、但不立即构成风险的新模式；
    - 或多 scene 混合、目前采用保守处理方式，但未来可能需要专门模式治理；
  - 处理原则：
    - 在说明中写清“当前方案为何可接受”“若再出现 N 次将触发什么动作”。

- **“接近触发预警”**
  - 条件示例：
    - 已被 Guard 明确标为 anti_pattern 或 forbidden，但需求侧仍有强烈使用倾向；
    - 单个样本就已经对主链模板/scene 分工构成明显风险；
  - 处理原则：
    - 标注为“接近触发预警”；
    - 明确写出“一旦再出现几次，将启动何种正式评估”。

> 若首次分类存在犹豫，默认倾向于先标为 **“观察中”**，并在周期复盘时根据出现次数和影响范围再决定是否升级为“接近触发预警”。

### 2.4 步骤 3：决定是否回填 & 回填去向

针对每条 observation 样本，按以下顺序做判断：

1. **是否需要回填 scene 验证文档？**
   - 是，下列情况之一：
     - 对某个 scene 的边界判断具有代表性（如 pricing、dashboard + assistant、deck + site）；
     - 在该 scene 的 `*_PHASE1_VALIDATION.md` 中尚无类似样本，或已有小节但缺少该模式代表；
     - 将来很可能用作该 scene Phase 2 的真值源；
   - 否：
     - 已在回归基线/生成回放中充分出现；
     - 或只作为跨 scene 的“绿色锚点”，不打算在 scene 文档中重复堆叠。

2. **是否需要同步到 `PHASE1_MULTI_SCENE_REVIEW.md`？**
   - 是，下列情况之一：
     - 样本本身就是典型的多 scene 混合（如 deck + site、dashboard + assistant）；
     - 样本触发了跨 scene 的结构性 tension，需要在多 scene 视角下讨论；
   - 否：
     - 样本仅影响单一 scene 的局部边界，对多 scene 关系影响较小。

> 回填动作本身不需要“实时”完成，可以在周期内批量执行。但在 observation 记录中，必须明确写出“建议回填到哪些文档，以何种方式回填”。

### 2.5 步骤 4：计数与模式聚类

为避免“谁想升级就升级”的主观状态，需要对 observation 样本做**基本计数与模式聚类**：

1. **模式归类**
   - 将样本按“模式”聚类，而不是仅按“单条样本 ID”计数：
     - 如 `pricing_in_homepage_shell`、`dashboard_plus_assistant`、`deck_plus_site`、`work_report_anti_pattern_misuse` 等；
   - 每条样本记录中，在“简短说明”或增加辅助字段的方式，注明其所属模式。

2. **计数字段（可选轻量实现）**
   - 在文档中维护一个小表或注释：
     - 每个模式在本 observation 周期内：
       - 出现次数；
       - 涉及的 scene 列表；
       - 当前最高档位（已知稳定 / 观察中 / 接近预警）。
   - 实现方式可简化为：在周期小结中统一列一张模式表，而非在每条样本旁边实时维护计数。

### 2.6 步骤 5：判断是否进入升级评估队列

在周期内或周期结束时，针对每个“模式”而不是单条样本，判断是否需要进入某类正式评估：

- **Guard patch 评估队列**
  - 适用：
    - 模式已经被 Guard 覆盖，但仍频繁出现误用；
    - 或现有 Guard 提示不够清晰，观察中样本反复在相同歧义点卡住；
  - 结论类型：
    - 暂不升级（继续观察）；
    - 进入“文案增强”型 Guard patch 设计；
    - 进入“逻辑收紧/调整”型 Guard patch 设计。

- **template / canonical 评估队列**
  - 适用：
    - 某模式在现有 canonical 壳中承载明显吃力；
    - 或已经出现多种业务诉求，指向同一种新壳/新结构；
  - 结论类型：
    - 暂不升级（现有壳暂时足够）；
    - 纳入“候选模板/子模板”调研列表；
    - 推入下一个版本的模板族治理任务单中。

- **Phase 2 候选队列**
  - 适用：
    - 模式已经跨多个 scene 反复出现；
    - 涉及多条主链（如 cockpit + workspace + assistant 的组合）；
  - 结论类型：
    - 暂不升级；
    - 标记为 Phase 2 候选主题，在未来大版本规划中评估优先级。

> 关键点：**升级判断永远针对“模式”，而不是针对“单条样本”。** observation 记录的作用是为模式提供证据与计数，而不直接代表“必须立刻改 Guard / 改模板”。

---

## 3. 观测周期的运行节奏

> 这一节回答：**是按“样本触发”即时记录，还是按“每周/每批次”整理，以及何时复盘/升级。**

### 3.1 日常节奏：样本触发 + 轻量实时记录

- **T0：样本出现时**
  - 完成：
    - 步骤 0：判断是否进入 observation；
    - 步骤 1：填写最小字段版本（样本 ID、scene/page_type/template、Guard 命中情况、初步分类）。
  - 目标：
    - 确保信息不过夜、不丢失；
    - 先有“草稿记录”，细化说明可在当周集中补齐。

### 3.2 周节奏：每周一次 observation 小整理

- **建议频率**：
  - 每周一次（如周五），耗时 30–60 分钟。

- **每周要做的事**：
  - 补齐本周新增样本的记录字段与说明；
  - 重新审视本周新增样本的三档分类（必要时上调/下调档位）；
  - 初步做模式聚类：
    - 将相似样本聚合为模式；
    - 记下每个模式在本周的出现次数与涉及 scene；
  - 标记“需要回填”的样本清单：
    - 记下对应 scene 文档 / `PHASE1_MULTI_SCENE_REVIEW.md` 的待更新列表，但暂不一定当周就更新。  

### 3.3 月节奏：每 1 个 observation 周期的正式小结

- **建议周期长度**：
  - 第一次 observation 周期建议为 **4 周**（约 1 个月）。

- **周期结束时**（详见第 5 节）：
  - 在 observation 文档中新增本周期小结段落；
  - 将需回填的样本批量同步到：
    - 各 `*_PHASE1_VALIDATION.md` scene 文档；
    - 必要时，更新 `PHASE1_MULTI_SCENE_REVIEW.md` 中的多 scene 观察章节；
  - 对各模式的计数与影响进行评估，决定是否有模式需要进入 Guard/template/Phase 2 的正式评估队列。

### 3.4 何时更新 `PHASE1_MULTI_SCENE_REVIEW.md`

- **不建议频繁更新**，以免文档膨胀：
  - 默认在每个 observation 周期结束时，根据本周期的模式变化情况更新一次；
  - 如发生“跨 scene 结构性事件”（例如某模式在 2–3 个 scene 爆发，且已触发 Guard/模板讨论），可以在周期中途追加一次补充说明。

### 3.5 何时值得发起升级讨论

- **Guard / template / Phase 2 升级讨论**，原则上只在以下两个时间点集中发起：
  - 周期结束小结时：
    - 汇总计数与模式影响，一次性讨论是否需要把某些模式推入评估队列；
  - 出现“重大单次事件”时：
    - 某个样本单次就对主链模板或核心场景边界造成严重冲击（例如大量生产任务被误导到 anti_pattern 壳），可在周期中途直接拉起临时讨论。

> 节奏总结：**即时记、每周理、每月评**。日常以轻量记录为主，升级相关决策尽量集中在周期小结时进行，避免 observation 变成“随时翻案”。

---

## 4. 计数与升级阈值的最小规则

> 这一节定义一套跨 scene 视角下的**最小计数/阈值规则**，避免“看到 1 个样本就升级，也避免永远停在观察中”。

### 4.1 从“观察中”升级为“接近触发预警”

一个模式（而非单条样本）满足以下任一组合条件时，应从“观察中”升级为“接近触发预警”：

- **条件组合 A：同一 scene 内高频出现**
  - 在连续 **1 个 observation 周期** 内：
    - 同一模式在同一 scene 中出现 **≥ 3 条** 有意义差异的样本；
    - 且这些样本在说明中都指出了“现有方案只是勉强可接受”或“明显有结构压力”。

- **条件组合 B：跨多个 scene 出现**
  - 在一个周期内：
    - 同一模式在 **≥ 2 个 scene** 内被观测到；
    - 且至少一个 scene 的样本被标为“中/高风险”。
  - 示例：
    - `dashboard + assistant` 模式从 `b_system` 扩展到 `ue5_overlay`、`website` 等。

- **条件组合 C：单次事件对主链构成重大风险**
  - 某个样本虽然是首次出现，但已经：
    - 明显冲击主链 canonical 模板的使用边界；
    - 或试图绕过/推翻现有 Guard 条款（例如强行要求启用 anti_pattern 模板作为默认）；
  - 此类样本可以直接标为“接近触发预警”，而无需等待多次计数。

### 4.2 从“接近触发预警”进入正式评估

模式一旦进入“接近触发预警”，需要进一步判断是否进入正式评估（Guard / template / Phase 2）：

- **Guard 正式评估触发条件（示例）**
  - 在连续 **2 个 observation 周期** 内：
    - 某 anti_pattern / 误用模式（如 work_report 误用）出现 **≥ 3 次**；
    - 或每个周期至少出现 1 次，且都来自真实高优先级业务需求；
  - 或：
    - 该模式导致多次 stop&ask，严重影响交互体验。

- **template / canonical 评估触发条件（示例）**
  - 某种页面结构：
    - 在 **≥ 2 个 scene** 内以略微变体出现；
    - 且在现有 canonical 壳中实现明显吃力（需要大量 patch/说明才能勉强落下）；
  - 或：
    - 同一 scene 中、该结构在一个周期内出现 **≥ 5 次**，且被多位评审标注为“结构偏离 canonical 壳”。

- **Phase 2 候选触发条件（示例）**
  - 某模式符合以下 3 个条件中的至少 2 个：
    - 涉及 **多 scene 组合**（≥ 2）且与核心任务强相关；
    - 影响到 **多个主链模板族** 的边界；
    - 已在 **2 个及以上 observation 周期** 内持续出现，且在周期小结中被多次提及。

### 4.3 比“次数”更重要的因素

在判断是否升级时，以下因素优先级 **高于纯次数**：

- **是否影响主链模板**
  - 例如：landing/homepage canonical、b_system 列表/工作台主链、ai_assistant 工作台、ue5 cockpit 等。

- **是否影响 scene 边界判断**
  - 是否会让用户/系统对“这是 website 还是 b_system / presentation / ai_assistant”产生根本性混淆。

- **是否已被 Guard 明确覆盖但仍高频出现**
  - Guard 已清晰写明禁止或警告，但 observation 显示需求侧仍频繁提出同类诉求，意味着：
    - Guard 文案/交互需要调整；或
    - scene/template 分工本身需要重新审视。

- **是否开始出现在多个 scene 中**
  - 同一模式在多个 scene 中出现，往往代表这是“结构性问题”，不再是局部偶发事件。

> 归纳：**次数提供“量”，上述因素提供“质”。升级决策必须同时看“量”和“质”，不能只凭一次灵感，也不能只看次数累积。**

---

## 5. 观测周期结束时的产出物

> 这一节定义：**每个 observation 周期结束时，至少要落地哪些文档与结论。**

### 5.1 observation 周期小结

- 在 `MULTI_SCENE_OBSERVATION_EXAMPLES.md` 末尾或单独小节中，增加：
  - `## Observation 周期 YYYY-MM-DD ~ YYYY-MM-DD 小结`：
    - 本周期新增样本总数；
    - 按三档分类的样本数量（已知稳定 / 观察中 / 接近预警）；
    - 按“模式”聚类后的概要表：
      - 模式名
      - 出现次数
      - 涉及 scene
      - 当前档位
      - 拟采取的后续动作（继续观察 / 候选 Guard 评估 / 候选模板评估 / Phase 2 候选）。

### 5.2 新归档样本清单

- 在同一小结中，给出本周期新增样本的清单：
  - 每条样本列出：
    - 样本 ID
    - scene / page_type / template 概要
    - 三档分类
    - 所属模式
    - 是否需要回填及回填目标文档。

### 5.3 scene 文档更新列表

- 整理一份“需要回填/已回填的 scene 文档更新列表”：
  - 每个 scene 下：
    - 需要更新的 `*_PHASE1_VALIDATION.md` 小节；
    - 对应样本 ID 列表；
    - 更新状态（已完成/下周期处理）。

- 如有必要，同步列出对 `PHASE1_MULTI_SCENE_REVIEW.md` 的更新点：
  - 新增/修订了哪些多 scene 模式的描述；
  - 哪些模式被提升为多 scene 重点观察对象。

### 5.4 “是否触发升级评估”的结论

- 在小结中明确给出本周期的升级结论：
  - 对每个模式，注明：
    - 是否进入 Guard 评估队列；
    - 是否进入 template/canonical 评估队列；
    - 是否进入 Phase 2 候选队列；
    - 或继续观察，并简单写明“继续观察”的理由。

- 如本周期 **没有任何模式触发升级评估**：
  - 需要显式写出：
    - “本周期未触发新的 Guard/template/Phase 2 正式评估，原因是：当前样本规模/影响范围尚不足以 justify 升级，建议继续 observation。”

> 这样，即便“没有升级动作”，也有一个清晰的“此轮观测没有升级”的书面结论，避免状态长期模糊。

---

## 6. 第一次正式 observation 周期的推荐执行方式

> 最后一节给出一个**可以立即执行的第一次 observation 周期方案**，基于当前已有样本与多 scene 评审结论。

### 6.1 推荐周期参数

- **周期长度**：4 周；
- **记录节奏**：
  - 样本发生时即时做最小记录；
  - 每周一次集中整理与补全；
  - 周期末做正式小结与升级判断。

### 6.2 第一次周期优先关注的 scene

- **website**：
  - 重点关注 `landing vs pricing` 边界与重度 pricing 模式（如 `website_case_w3_pricing_comparison_heavy` 的后续样本）；

- **ai_assistant + b_system / ue5_overlay**：
  - 重点关注 `dashboard + assistant`、`cockpit + assistant` 等混合场景；

- **presentation + website**：
  - 重点关注 `deck + site` 双产物诉求的变体；

- **presentation + b_system**：
  - 持续观察 `work_report` 方向的 anti_pattern 诉求，统计误用频次。

### 6.3 第一次周期优先关注的样本类型

- **所有命中 stop&ask 的样本**：
  - 尤其是：`EXTENSION_GUARD §1.7`（landing vs pricing）、`§1.8`（ai_assistant vs b_system）、`§1.9`（presentation vs website）、`§3.3`（work_report anti_pattern）相关。

- **所有跨 scene 混合样本**：
  - 包含至少 2 个 scene 强信号的任务，无论最终如何拆分，都应记录。

- **所有涉及 anti_pattern / limited 模板的诉求**：
  - 记录误用或潜在合理新模式，为后续决策提供证据。

### 6.4 第一次 observation 周期的目标

- **首要目标：验证机制在日常使用中的稳定性**
  - 验证“即时记录 + 每周整理 + 周期小结”的节奏是否顺手；
  - 验证三档分类与回填决策在真实工作量下是否可执行。

- **次要目标：稳住扩展 scene 与模板边界**
  - 利用 observation 记录，持续确认：
    - Phase 1 已确定的 scene 边界是否在新任务中保持稳定；
    - canonical/limited/anti_pattern 模板的使用范围是否被遵守。

- **逐步目标：为 Phase 2 候选积累证据，而不是立即立项**
  - 本周期内，以“积累模式证据与计数”为主；
  - 即便发现潜在 Phase 2 主题，也优先标记为候选，而非立即发起大规模治理。

---

## 7. 一句话总结：第一次正式 observation 周期应如何启动？

> **建议：立即以 4 周为一个 observation 周期，在日常中对所有命中 stop&ask / 跨 scene / anti_pattern/limited 模板相关的新样本进行轻量即时记录，每周集中整理与聚类，在周期结束时围绕 website pricing、dashboard+assistant、deck+site 以及 work_report 误用等关键模式，做一次“记录→分类→回填→是否升级”的小结决策，在不断验证节奏可行性的同时稳住现有 scene 与模板边界。**
