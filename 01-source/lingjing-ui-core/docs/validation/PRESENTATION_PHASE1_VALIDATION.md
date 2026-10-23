# presentation · Phase 1 页型验证（deck / 演示文稿）

> **目的**：把 `scene = presentation` 从“有模板 / 有 UX spec / 有少量 router，但缺验证文档与边界治理”的兼容支持场景，推进为具备 **W1 级可治理能力** 的场景：
> - 写清演示文稿（deck）与官网 / BI 仪表盘 / 项目工作台之间的 **场景边界**；
> - 用少量高价值样本澄清“**同一主题的 deck + 官网专题页双产物**”在多 scene 下的分工；
> - 明确当前模板的 **分级与使用范围**，解释为什么现在还不能直接在真值源层标记 canonical，而只在文档层给出 **strong candidate / anti_pattern** 口径；
> - 给出面向 Guard 的 **文档级建议稿**，为后续 EXTENSION_GUARD patch 提供挂接素材，而不是在本轮直接修改 Guard。

---

## 1. 验证范围与前提

- **适用场景**：`scene = presentation`
- **当前主要 page_type（来自 template_router 摘要）**：
  - `page_type = product_presentation`
  - `page_type = business_report`
  - `page_type = planning_proposal`
- **当前模板与分级（来自 `data/template_router.json`）**：
  - `examples/presentation/presentation-product.html`
    - `scene = presentation`
    - `grade = candidate`
    - `use_scope = default`
    - `page_types = ["product_presentation"]`
    - `preferred_level = level_1`
  - `examples/presentation/presentation-business.html`
    - `scene = presentation`
    - `grade = candidate`
    - `use_scope = default`
    - `page_types = ["business_report"]`
    - `preferred_level = level_1`
  - `examples/presentation/presentation-planning.html`
    - `scene = presentation`
    - `grade = candidate`
    - `use_scope = default`
    - `page_types = ["planning_proposal"]`
    - `preferred_level = level_1`
  - `examples/presentation/presentation-work-report.html`
    - `scene = presentation`
    - `grade = anti_pattern`
    - `use_scope = forbidden`
    - `page_types = ["work_report"]`
    - `preferred_level = level_2`
  - `examples/presentation/presentation-minimal.html`
    - `scene = presentation`
    - `grade = anti_pattern`
    - `use_scope = forbidden`
    - `page_types = ["minimal_presentation"]`
    - `preferred_level = level_2`
- **当前 UX spec 引用**：
  - `lingjing-ux-core/examples/ux_spec_presentation_quarterly_review.yml`
    - `scene.id = presentation_quarterly_review`，名称：**季度经营汇报（HTML 演示文稿）**；
    - 主流程 `main_flow.id = presentation_storytelling`：开场 → 背景 → 亮点 → 决策 → Q&A → 总结；
    - 主要 pages：议程 / 指标页 / 决策页 / Q&A 页，对应章节导航、KPI 亮点、决策列表与问答互动。
- **当前真值源状态（TRUTH_SOURCES 摘要）**：
  - `TRUTH_SOURCES.md` 中将 `presentation` 标记为：
    - **“兼容支持”** 场景 —— 模板与样式可用；
    - 但 **不作为 Phase 1 深做主线**，中间层与 Guard 治理尚未完善。
- **本轮验证目标**：
  - 仅在文档层：
    - 梳理 presentation 与 website / b_system（必要时含 ai_assistant）的 **W1 级场景边界**；
    - 用少量样本标注当前模板的 **strong candidate / anti_pattern** 角色；
    - 给出 Guard 建议稿，作为后续 EXTENSION_GUARD patch 的蓝本；
  - **不做的事情**：
    - 不修改 `task_router.json` / `template_router.json` / `scene_coverage_matrix.yml`；
    - 不修改 `docs/EXTENSION_GUARD.md`；
    - 不改动 `examples/presentation/*.html` 或其分级、page_type / 样式 / 实现。

---

## 2. 现状摘要（W0 → W1 起步）

- **已具备的资产（W0 基础）**：
  - 模板层：
    - 3 个可用的 deck 模板：`presentation-product` / `presentation-business` / `presentation-planning`，在 `template_router` 中登记为 `grade = candidate`；
    - 2 个明确标记为 `grade = anti_pattern`, `use_scope = forbidden` 的模板：`presentation-work-report` / `presentation-minimal`；
  - UX 侧：
    - 有 `presentation_quarterly_review` 的 UX spec，清楚定义了季度经营汇报 deck 的章节结构与互动 flows；
  - 路由层：
    - `data/task_router.json` 中存在至少一条 `scene = "presentation"` 的任务（如 `presentation_product_story`），将“产品故事 deck”映射到 `product_presentation` / `business_report` 的组合；
  - 真值源层：
    - `TRUTH_SOURCES.md` 已记录 presentation 为“兼容支持”场景，有模板、有 UX、有少量 router，但**缺少验证文档与 Guard 治理**。
- **当前主要缺口**：
  - 未有专门的 `PRESENTATION_PHASE1_VALIDATION` 文档：
    - 没有系统整理“产品介绍 deck vs 官网落地页”“季度经营汇报 deck vs 日常 BI/dashboard”“项目规划 deck vs 项目执行工作台”等核心边界样本；
    - 对 `presentation-work-report` / `presentation-minimal` 仅在真值源中标注了 anti_pattern/forbidden，缺少“为什么不能作为主模板”的文字说明；
  - Guard 层缺失：
    - `EXTENSION_GUARD.md` 尚未引入 `scene = presentation` 的专向条款；
    - website / b_system 侧的 Guard 虽能部分拦截混合场景，但没有从 presentation 视角出发的 stop&ask 规则。
- **为什么现在适合进入 Phase 1 / W1**：
  - presentation 已具备“模板 + UX spec + router + 真值源”四件套，不再是单纯的 demo 模板集合；
  - website 与 ai_assistant 场景已跑通一轮 W1 治理 + Guard patch，形成可复用的 **样本驱动 / Guard 优先** 流程；
  - 在产品实践中，presentation 与 website / b_system 的混合诉求频繁出现，若不及早写清边界，很容易出现：
    - 官网页被强行“deck 化”；
    - BI 仪表盘被当作“可交付 deck”；
    - 项目工作台被退化成多页 deck，影响可操作性。

---

## 3. 任务样例一览（首批 W1 样本）

> 本表覆盖本轮必须写入的 5 类样本：
> - 产品介绍 deck vs 官网落地页（presentation vs website）；
> - 季度经营汇报 deck vs 日常 BI/dashboard（presentation vs b_system）；
> - 项目规划提案 deck vs 项目执行工作台（presentation vs b_system workspace）；
> - 同一主题的“分享 deck + 官网专题页”双产物（多 scene 协作）；
> - anti_pattern 误用样本（`presentation-work-report` / `presentation-minimal`）。

| id | 类别 | 输入描述（概括） | 预期 scene / page_type / template | 判定要点 | 是否应 stop&ask |
|----|------|------------------|-----------------------------------|----------|------------------|
| `presentation_case_product_launch_deck` | 产品介绍 deck | 为新发布的 SaaS 产品设计一套发布会 deck，用于线下路演或线上直播演讲 | `scene = presentation` / `page_type = product_presentation` / `template = presentation-product.html` | 受众是听众 / 评审，会场使用；输出为一套按章节翻页的 deck，而非长期可访问的站点页 | 否（需求已明确说是“发布会 deck”） |
| `presentation_case_product_landing_page` | 官网落地页 | 为同一产品设计官网首页/落地页，面向外部访客长期在线访问 | `scene = website` / `page_type = landing` / `template = website-complete.html` | 面向长期访问，强调 SEO / 导航 / 链接，而不是单次演讲；不需要“翻页控制” | 是（需澄清是“演讲用 deck”还是“长期官网”） |
| `presentation_case_quarterly_review_deck` | 季度经营汇报 deck | 为季度经营评审会做一套经营汇报 deck，按“议程-指标-决策-Q&A”结构组织 | `scene = presentation` / `page_type = business_report`（W1 视角，对应 `presentation_quarterly_review`） / `template = presentation-business.html` | 输出是一场会议用的 deck；强调章节导航、时间受限展示；不承载日常监控 | 否 |
| `presentation_case_quarterly_kpi_dashboard` | 日常 BI/dashboard | 为经营团队设计日常运营 KPI 仪表盘，每天登录查看并 drill-down | `scene = b_system` / `page_type = dashboard` / `template = b-system-charts.html` 等 | 长期在线 / 支持 drill-down / 过滤 / 交互；不强调线性演示节奏 | 是（“季度经营视图”易被误听为季度汇报 deck，需要拆清是“演示”还是“日常监控”） |
| `presentation_case_project_planning_deck` | 项目规划提案 deck | 为重大项目立项会准备规划提案 deck，讲清背景、目标、里程碑与风险 | `scene = presentation` / `page_type = planning_proposal` / `template = presentation-planning.html` | 输出是一套提案 deck，用于一次或数次评审；不承担持续任务管理 | 否 |
| `presentation_case_project_execution_workspace` | 项目执行工作台 | 为同一项目设计执行工作台，管理任务、里程碑、风险与负责人 | `scene = b_system` / `page_type = workspace` / `template = b-system-production-plan.html` 等 | 长期在线 / 支持更新状态与协作；强调“可操作性”而非线性讲述 | 是（“项目规划界面”既可能是 deck 也可能是工作台） |
| `presentation_case_topic_deck_plus_site` | 同一主题 deck + 官网专题页 | 围绕同一产品发布，希望既有一套分享 deck，又有一个官网专题页 | **两条任务**：deck → `scene = presentation`；专题页 → `scene = website` | 同一主题可以拆为多 scene；不能用“万能 deck 页”或“万能官网页”一次性承载 | 是（典型多 scene 需求，必须拆任务，而不是单页膨胀） |
| `presentation_case_work_report_template_misuse` | anti_pattern 误用：work-report | 想将 `presentation-work-report.html` 当作所有内部周报/月报的通用壳，并以此作为 presentation 主模板 | 真值源已标记：`grade = anti_pattern`, `use_scope = forbidden`；不应被路由命中为主模板 | `work-report` 模板结构与 v3.0 口径不符，且与 b_system workspace / dashboard 角色高度重叠 | 是（需提醒：该模板是 anti_pattern，不能作为 canonical 候选） |
| `presentation_case_minimal_template_misuse` | anti_pattern 误用：minimal | 想在营销/经营场景中用 `presentation-minimal.html` 承载复杂 deck，只因“极简好看” | 真值源已标记：`grade = anti_pattern`, `use_scope = forbidden`；仅可作为样式参考，不进入路由 | minimal 模板缺少关键导航与结构骨架，无法承载严肃经营 / 产品汇报；易导致结构失控 | 是（需要明确禁止在业务 deck 中使用该壳） |

---

## 4. 逐条任务验证记录

### 4.1 `presentation_case_product_launch_deck` — 产品发布会 deck（presentation 正例）

- **输入任务描述**：
  - “为新一代云产品做一套发布会演示文稿，用于线下路演 / 线上直播演讲，包含封面、目录、产品亮点、架构与路线图等。”
- **预期判定**：
  - `scene = presentation`；
  - `page_type = product_presentation`；
  - 任务可对应 `presentation_product_story` 或类似任务 ID；
  - `template = examples/presentation/presentation-product.html`。
- **判定要点**：
  - 受众是一次或少数几次演讲的听众/评审，而非长期站点访客；
  - 信息组织强调线性“讲故事”节奏，而不是自由浏览：封面 → 议程 → 产品定位 → 能力 → 案例/路线图；
  - 需要键盘/遥控翻页控制，与 `presentation` 场景交互模式匹配；
  - 不需要搜索、全站导航、SEO 等典型 website 能力。
- **是否需要 stop&ask**：
  - 一般不需要：需求中已明确“演示文稿/演讲用 deck”；
  - 如果描述中出现“也希望这页长期对外展示”，则应转入 4.3/4.7 类型的多 scene 拆分讨论。
- **结论**：
  - 此类“发布会/路演 deck”是 `product_presentation` 的典型正例，应稳定路由到 `scene = presentation` + `presentation-product.html`，不应退化为 website 落地页。

---

### 4.2 `presentation_case_product_landing_page` — 同一产品的官网落地页（website 正例）

- **输入任务描述**：
  - “为同一个新产品设计官网首页 / 落地页，面向公共互联网访问，介绍产品价值并引导注册 / 预约演示。”
- **预期判定**：
  - `scene = website`；
  - `page_type = landing`；
  - 任务可对应 `website_landing_marketing`；
  - `template = examples/website/website-complete.html`。
- **判定要点**：
  - 访问形态是“长期在线、随时可访问”的站点页，而不是“按讲者节奏翻页”的 deck；
  - 强调导航、信息架构、SEO 与链接，而不是单次演讲的节奏控制；
  - 不需要键盘翻页控制，也不假定“一个屏幕一页”展示节奏；
  - 内容可以与 deck 共享，但表达形式不同：site 更适合模块化信息、可反复阅读与跳转。
- **Guard / stop&ask 行为（文档级）**：
  - 当任务中同时出现“官网首页/落地页”与“演示文稿/演讲 deck”时，应补问：
    - “本次交付物是给用户长期访问的网站，还是给演讲人使用的一套 deck？”
    - “是否接受将 deck 与官网拆成两份产物？”
  - 若用户明确“这是官网首页”，则锁定 `scene = website`，deck 需求应另起任务（见 4.7）。
- **结论**：
  - 同一产品可以、也**应该**同时拥有 deck 与官网页——它们属于不同 scene；
  - presentation W1 的目标之一，是在文档层写清这一点，避免“用一个万能 deck 或万能官网承载一切”。

---

### 4.3 `presentation_case_quarterly_review_deck` — 季度经营汇报 deck（presentation 正例）

- **输入任务描述**：
  - “为季度经营评审会做一套经营汇报 deck，包含议程、关键指标亮点、风险与对策、决策事项和 Q&A。”
- **预期判定**：
  - `scene = presentation`；
  - `page_type = business_report`（W1 视角下对应 `presentation_quarterly_review`）;
  - 可落在 `template = examples/presentation/presentation-business.html`，并根据 UX spec 调整章节顺序与组件；
  - 与 `ux_spec_presentation_quarterly_review.yml` 中的 flows/pages 对齐。
- **判定要点**：
  - deck 用于季度评审会，有明确的“会议时间窗”，而非全天候监控；
  - 信息选取强调“**讲清故事与结论**”，而不是展示所有细节：
    - KPI 页突出少量核心指标和趋势；
    - 决策页列出关键决策项与责任人；
    - Q&A 页用于现场互动；
  - 需要章节导航与翻页控制，符合 presentation 场景交互模式；
  - 不承担“随时登录查看最新数据”的职责，数据多为截面/快照。
- **是否需要 stop&ask**：
  - 当 PRD 同时提到“季度经营视图”“日常 BI/dashboard”时，必须补问：
    - “本任务的主要产出是会议用 deck，还是日常运营 dashboard？”
  - 若输出目标明确定义为“季度经营汇报会 deck”，则落在 `scene = presentation`。
- **结论**：
  - 季度经营汇报 deck 是 `business_report` 的核心正例，应该由 `presentation-business.html` + `presentation_quarterly_review` UX 规格共同承接。

---

### 4.4 `presentation_case_quarterly_kpi_dashboard` — 日常 BI/dashboard（b_system 正例）

- **输入任务描述**：
  - “为经营团队设计一个季度经营看板，平时每天都要进去看实时/近实时的 KPI、告警、明细列表，用来追踪进度和发现问题。”
- **预期判定**：
  - `scene = b_system`；
  - `page_type = dashboard`（或 `overview`），由 `docs/system-template-map.md` 决定具体模板；
  - 典型模板可以是 `b-system-complete.html` / `b-system-charts.html` 等，而**不是**任何 presentation 模板。
- **判定要点**：
  - 使用频率高：每天/每周都要访问，而不是每季度开会时才使用；
  - 强调实时/近实时数据，需支持 drill-down、过滤、权限控制；
  - 核心任务是 **运营监控与操作**，而不是“在台上讲完一个故事”；
  - 不需要演讲用的线性翻页结构，反而需要支持多视图切换、交互操作。
- **Guard / stop&ask 行为（文档级）**：
  - 当需求描述中出现“季度经营视图/看板/驾驶舱”，应自动补问：
    - “这个界面是给人**日常登录使用**，还是只在季度会议上使用？”
    - “是否需要 drill-down 到明细、工单或初始化操作？”
  - 若答案偏向“日常登录 + 需要操作”，则应判定为 `scene = b_system` dashboard，而非 presentation。
- **结论**：
  - 季度视角并不自动意味着“deck”——只要产物是 **操作型看板**，就属于 `b_system`；
  - W1 边界中，必须清晰区分“**季度经营汇报 deck**”与“**季度经营 BI/dashboard**”。

---

### 4.5 `presentation_case_project_planning_deck` — 项目规划提案 deck（presentation 正例）

- **输入任务描述**：
  - “为某个重大项目立项评审会制作规划提案 deck，说明项目背景、目标、里程碑、风险与资源投入，目标是在评审会上获得立项决策。”
- **预期判定**：
  - `scene = presentation`；
  - `page_type = planning_proposal`；
  - `template = examples/presentation/presentation-planning.html`；
  - deck 用于一次或少数几次评审会议。
- **判定要点**：
  - 产出是 **决策前的演示材料**，用于讲清“做什么、为什么、怎么做”；
  - 不直接承载任务分配与执行进度追踪——那些属于执行阶段；
  - 结构上更接近“叙事 + 关键节点 + 风险与对策”，而非看板。
- **是否需要 stop&ask**：
  - 若需求表述中还提到“在同一界面管理任务进度/更新状态”，则应补问：
    - “这些任务管理能力是否需要作为日常工作台存在？是否接受将‘评审会 deck’与‘执行工作台’拆分？”
- **结论**：
  - 项目规划提案 deck 应落在 `presentation-planning.html`，并与后续 `b_system` 执行工作台分工（见 4.6）。

---

### 4.6 `presentation_case_project_execution_workspace` — 项目执行工作台（b_system 正例）

- **输入任务描述**：
  - “为同一个项目设计执行工作台，项目成员每天在上面更新任务状态、查看里程碑进度、处理风险与变更。”
- **预期判定**：
  - `scene = b_system`；
  - `page_type = workspace`；
  - 模板可选 `b-system-production-plan.html` 或其它典型 workspace 模板。
- **判定要点**：
  - 强调日常使用与可操作性：
    - 创建/更新任务；
    - 调整里程碑日期与负责人；
    - 管理风险与问题；
  - 页面是“工作工具”，不是“展示材料”；
  - 即使没有演讲人或听众，工作台仍然有价值。
- **Guard / stop&ask 行为（文档级）**：
  - 对“项目规划页”类需求，应补问：
    - “这个界面是给项目成员日常使用，还是给评审会一锤定音？”
    - “是否存在演讲人 + 听众的场景？”
  - 若偏向“日常协作/任务执行”，应归为 `b_system` workspace，而不是 presentation。
- **结论**：
  - 含有任务编辑 / 状态更新 / 权限控制的页面，应被视为 `b_system` 工作台，而非“可操作 deck”。

---

### 4.7 `presentation_case_topic_deck_plus_site` — 同一主题的 deck + 官网专题页（多 scene 协作）

- **输入任务描述**：
  - “围绕新一代产品发布，希望既有一套分享 deck，用于路演/发布会，也有一个官网专题页，用于会后长期对外展示。”
- **预期判定**：
  - 应拆分为两条任务：
    - 任务 A：`scene = presentation`，产出分享 deck；
    - 任务 B：`scene = website`，产出官网专题页（landing/feature）。
- **判定要点**：
  - 两个产物共享主题与部分素材，但：
    - deck 更受控于“讲述顺序”“节奏”“演讲人视角”；
    - 官网专题页更受控于“信息架构”“SEO”“浏览路径”；
  - 若试图用一个 HTML 页面同时承担两者，将导致：
    - 对 deck 来说，导航与元素过多，演讲节奏容易被打断；
    - 对 site 来说，单页过长、结构僵化，不利于长期维护与扩展。
- **Guard / stop&ask 行为（文档级）**：
  - 当任务描述中同时包含“发布会 deck/演示文稿”和“官网专题页/落地页”时，应触发：
    - “是否接受将本需求拆分为：一套 deck + 一个专题页？”
    - “两个产物的受众与使用时长是否相同？”
  - 若用户接受拆分，则应在路由层明确分别走 presentation 与 website 链路，而不是寻找一个“万能模板”。
- **结论**：
  - **同一主题拥有多个 scene 是正常且健康的**：presentation 承接“场景化讲述”，website 承接“长期信息承载”。

---

### 4.8 `presentation_case_work_report_template_misuse` — 误用 `presentation-work-report.html` 作为主模板（anti_pattern）

- **输入任务描述**：
  - “想用 `presentation-work-report.html` 作为所有内部周报/月报的通用模板，未来大部分经营汇报/项目汇报都参考这个结构；也希望 AI 默认生成这种结构。”
- **真值源现状**：
  - `template_router` 中明确：
    - `path = examples/presentation/presentation-work-report.html`；
    - `grade = anti_pattern`；
    - `use_scope = forbidden`；
    - `page_types = ["work_report"]`；
  - 即：这是一个 **反例模板**，用于提醒“不要这样设计工作汇报页”，而不是推荐路径。
- **为什么不能当当前主模板**：
  - 结构问题：
    - 容易将长期、细碎的工作更新塞进大量类似页面，信息密度高但缺乏结构化聚合；
    - 与 `b_system` 中的 dashboard/workspace 职责重叠：很多“应在工作台完成的任务/状态更新”被搬到 deck 中，降低可操作性；
  - 治理问题：
    - 若把 anti_pattern 模板升级为“主流 work_report 壳”，等于将 v3.0 的治理口径反向拉回“万能汇报 deck”；
    - 与 `TRUTH_SOURCES.md` 中“presentation 仍为兼容支持场景”的定位冲突，容易造成真值源口径失衡。
- **W1 文档结论**：
  - 在 Phase 1 / W1 阶段，`presentation-work-report.html` 应继续保持 `grade = anti_pattern`, `use_scope = forbidden`：
    - 不能作为任何任务的 primary/secondary 模板候选；
    - 可以作为“反例截图”出现在文档中，但不能出现在路由与自动选择链路中；
  - 若未来希望支持“工作汇报 deck”，应基于真实项目样本重新设计新的模板，而不是复用该 anti_pattern。

---

### 4.9 `presentation_case_minimal_template_misuse` — 误用 `presentation-minimal.html` 承载复杂 deck（anti_pattern）

- **输入任务描述**：
  - “希望使用 `presentation-minimal.html` 作为所有产品发布会 / 经营汇报的通用壳，因为它极简好看；即便内容复杂、章节很多，也想统一用这一稿。”
- **真值源现状**：
  - `template_router` 中：
    - `path = examples/presentation/presentation-minimal.html`；
    - `grade = anti_pattern`；
    - `use_scope = forbidden`；
    - `page_types = ["minimal_presentation"]`；
- **为什么不能当当前主模板**：
  - 结构承载力不足：
    - minimal 模板缺乏稳定的章节导航、决策/行动区、图表/亮点区等骨架；
    - 无法为复杂经营汇报提供足够的“信息锚点”和“复盘结构”；
  - 审计与治理困难：
    - 若广泛使用 minimal 模板，审计难以判断何为“必要信息缺失”，因为所有内容都被压缩成极简形式；
    - 容易鼓励“为了好看牺牲信息质量”的设计倾向，与 Phase 1 治理目标相反。
- **W1 文档结论**：
  - `presentation-minimal.html` 仅可作为视觉/动画参考，不应作为任何正式业务 deck 的主壳；
  - 在 W1 期间，该模板继续作为 anti_pattern 反例存在，帮助强调“严肃业务 deck 需要结构化骨架”。

---

## 5. 阶段性结论（W1 视角）

### 5.1 presentation 场景当前具备的最小可治理能力

- 有 3 个 **结构明确的 candidate 模板**（product/business/planning），并在 `template_router` 中登记了 scene/page_type/use_scope；
- 有 2 个 **明确标记为 anti_pattern 的模板**（work-report/minimal），为治理提供反例锚点；
- 有针对季度经营汇报的 UX spec，提供章节/交互层面的真值源；
- 通过本文件首批样本，初步厘清了：
  - 产品 deck vs 官网落地页（4.1–4.2）；
  - 季度经营汇报 deck vs 日常 BI/dashboard（4.3–4.4）；
  - 项目规划 deck vs 项目执行工作台（4.5–4.6）；
  - 同一主题 deck + 官网专题双产物（4.7）；
  - anti_pattern 模板为何不能晋升为主模板（4.8–4.9）。

### 5.2 模板分级说明（W1 视角）

> 本小节回答三个问题：
> 1）哪些模板可视为 **strong candidate / potential canonical**；
> 2）哪些模板仅是普通 candidate；
> 3）哪些是 anti_pattern，以及为什么；同时说明为什么现在还不能在真值源层直接标记 canonical。

- **strong candidate / potential canonical（W1 文档视角）**：
  - `examples/presentation/presentation-product.html`
    - 作为产品发布 / 产品介绍 deck 的主壳，在结构上相对稳定：封面 → 议程 → 产品价值 → 能力/方案 → 路线图/CTA；
    - 搭配未来更多 product_presentation 样本，有机会晋级 canonical。
  - `examples/presentation/presentation-business.html`
    - 更适合经营/业务汇报类 deck，与 `presentation_quarterly_review` 流程自然契合；
    - 在“经营亮点 + 决策 + Q&A”结构下具有较强代表性，是 business_report 的潜在 canonical。
- **普通 candidate**：
  - `examples/presentation/presentation-planning.html`
    - 面向项目规划提案 deck，但目前真实样本相对较少，结构模式尚未充分验证；
    - 在 W1 视角下仍视为 candidate，暂不判断其是否能晋级 canonical。
- **anti_pattern（反例模板）**：
  - `examples/presentation/presentation-work-report.html`：
    - 已被标记 `grade = anti_pattern`, `use_scope = forbidden`；
    - 反映“将工作汇报长期任务塞进 deck 中”的错误倾向，应仅用于教育/对照。
  - `examples/presentation/presentation-minimal.html`：
    - 同样为 anti_pattern + forbidden；
    - 用于提醒“极简视觉不等于合格业务 deck”。
- **为什么现在还不能在真值源层直接定 canonical**：
  - `TRUTH_SOURCES.md` 仍将 presentation 定位为“兼容支持”，不属于 Phase 1 深做主线；
  - 真实项目中，presentation 的使用规模与模式尚未达到 website / b_system 那样的稳定程度：
    - 产品发布 / 经营汇报 / 规划提案各自的样本数量有限；
    - 不同行业对 deck 结构的差异可能较大；
  - 在缺乏充分样本支持的前提下，过早将 product/business 标记为 canonical 可能导致：
    - 后续调整付出更高迁移成本；
    - 真值源与实际使用模式脱节；
  - 因此，在 W1 阶段，**canonical 仍停留在“候选”状态，由本验证文档提供非强制性的“strong candidate / potential canonical”判断。**

### 5.3 Guard 与路由的准备度（W1 结论）

- 从文档与样本角度看，presentation 已经具备：
  - 可被 Guard 引用的场景边界描述（第 6 节）；
  - 明确的 anti_pattern 模板与误用场景说明（4.8–4.9）；
  - 对典型任务提供了 scene/page_type/template 的预期组合（第 3–4 节）；
- 但考虑到当前 TRUTH_SOURCES 定位与 Phase 1 主线优先级，本轮仍然：
  - 只在本文件中给出 Guard 建议稿（第 7 节），
  - **不直接修改** `EXTENSION_GUARD.md` 或 router/matrix；
  - 将 presentation 视为“已具备 W1 级文档治理基础，可以在 observation mode 中继续积累样本”的场景。

---

## 6. W1 级边界结论

> 本节从 W1 视角，明确 presentation 的核心边界：
> - presentation vs website；
> - presentation vs b_system；
> - 如有必要，补充 presentation vs ai_assistant 的轻量说明。

### 6.1 presentation vs website

- **应优先判为 presentation 的典型特征**：
  - 产物是“**一次或少数几次演讲用的 deck**”，而不是“长期在线的页面/站点”；
  - 有明确的“演讲人 + 听众”角色设定，强调讲述节奏与演讲场景（会议室/路演/直播）；
  - 页面结构以“封面/议程/章节/结尾”等 slide 为单位，强调线性顺序与翻页控制；
  - 不依赖 SEO / 站点导航 / 搜索等能力，通常通过链接/附件/分享直接打开。
- **应优先判为 website 的典型特征**：
  - 产物是“**长期在线的公共页面**”，面向多次访问、多种入口；
  - 强调站点内导航、链接、SEO、响应式布局等；
  - 信息结构允许用户自由浏览，非必须沿单一路径阅读；
  - 即使没有演讲人存在，页面仍然完全有价值。
- **W1 边界结论**：
  - 若同一业务诉求同时需要 deck 与官网页，应拆分为 `scene = presentation` 与 `scene = website` 两条任务（见 4.7），而不是寻找“既像 deck 又像官网的万能页”；
  - 对存在歧义的需求，应通过 Guard 提示“交付物是 deck 还是 site”，优先澄清 scene，再讨论 page_type/template。

### 6.2 presentation vs b_system

- **应优先判为 presentation 的典型特征**：
  - 产物只在少数会议/路演中使用，用完之后主要用于回溯与记录，而不是日常操作；
  - 不支持实时数据操作或状态变更，仅展示数据快照与结论；
  - 不包含复杂的交互控件（表单、可编辑表格、操作按钮等），观众主要通过听看获取信息。
- **应优先判为 b_system 的典型特征**：
  - 产物是“**日常工作工具**”：频繁登录、执行操作、变更状态、创建/编辑实体；
  - 强调权限控制、数据一致性、错误处理与审计；
  - 页面即使没有“演讲”情境，也必须完整且可用；
  - 内容随时间持续更新，而非一次性准备好后在会议上集中展示。
- **W1 边界结论**：
  - 任何承载真实“任务执行 / 状态更新 / 列表操作”的界面，应归为 `b_system`（dashboard/list/workspace），而非“可操作 deck”；
  - “季度经营汇报 deck”与“季度经营 dashboard”必须拆分（4.3 vs 4.4），不能通过一个 hybrid 页同时满足；
  - “项目规划提案 deck”与“项目执行工作台”同理（4.5 vs 4.6）。

### 6.3 presentation vs ai_assistant（轻量说明）

- **与 ai_assistant 的关系**：
  - ai_assistant 更关注“对话 + 规划 + 工具执行 + 结果回顾”的多轮任务执行；
  - presentation 更关注“演讲叙事 + 章节结构 + 可视化展示”，输出为 deck；
- **典型协作模式**：
  - ai_assistant 可作为“**内容生产工具**”，帮助准备 deck 文案、结构草稿或图表脚本；
  - 最终交付层 surface 仍是 `scene = presentation` 的 HTML deck；
- **W1 边界结论**：
  - 当需求重点是“帮我准备一套 deck，并输出为 HTML/PPT 等形式”，即便中途使用 AI 辅助，最终 scene 仍应为 `presentation`；
  - 当需求重点是“通过对话持续迭代与执行任务，偶尔生成 deck 作为中间/附属产物”，则主场景可能是 `ai_assistant`，deck 仅为结果的一部分；
  - 在 W1 阶段，presentation 与 ai_assistant 边界暂以“谁是最终交付 surface”作为简化判断，不在本轮细拆更复杂组合场景。

---

## 7. Guard 建议稿（准 EXTENSION_GUARD 条文）

> 本节将第 3–6 节的 W1 边界结论整理为面向 `EXTENSION_GUARD.md` 的“准 Guard 条文”，**仅在本文件中生效**，为后续 Guard patch 提供文案参考。本轮不修改 Guard 文件，也不改 router/matrix/html。
>
> 约定：每条规则尽量包含四个要素：**触发条件 / 推荐补问 / 推荐判定方向 / 不应静默决策的原因**。

### 7.1 A 组：presentation vs website

> 回答“产品介绍 / 方案介绍 / 营销主题”究竟落在 website 还是 presentation。

- **规则 P1（A 组）：产品/方案需求同时出现“演示文稿/演讲”与“官网/落地页”**
  - **触发条件**：
    - 设计请求中同时出现两类关键词：
      - 演示类：`“演示文稿”`、`“演讲”`、`“路演”`、`“发布会”`、`“分享会”` 等；
      - 站点类：`“官网首页”`、`“落地页”`、`“专题页”`、`“长期在线”`、`“站点导航/SEO”` 等。
  - **推荐补问**：
    - Q1：`"本次交付物的**第一优先**是会议/路演上的演讲 deck，还是用户长期访问的官网/专题页？"`
    - Q2：`"是否接受将 deck 与官网专题页拆成两条任务，分别在 presentation 与 website 场景中治理？"`
    - Q3：`"是否需要章节化的线性叙事（封面/目录/章节/结尾 + 翻页），还是需要站点导航/SEO/自由浏览？"`
  - **推荐判定方向**：
    - 若回答偏向“用于会议/路演/评审”“需要线性讲述 + 翻页控制”，则：
      - 当前任务建议落在 `scene = presentation`；
      - 官网/专题页需求另起 `scene = website` 任务承接。
    - 若回答偏向“长期在线浏览”“需要站点导航/SEO/多入口访问”，则：
      - 当前任务锁定 `scene = website`（landing/feature）；
      - 演讲 deck 需求另起 `scene = presentation` 任务。
  - **不应静默决策的原因**：
    - “产品发布/方案介绍”极易被误解为“只需要一页既能当 deck 又能当官网”；
    - 若不 stop&ask，容易出现用单一 HTML 同时承担“会场讲述 + 长期站点”的万能页，导致后续很难按 scene 治理。

- **规则 P2（A 组）：只提“产品/方案介绍页”，未明确是否用于演讲**
  - **触发条件**：
    - 需求描述类似“做一个产品介绍页面/解决方案介绍页/专题页”，但：
      - 未提“演示文稿/演讲/路演”等；
      - 未明确“是否仅在会场使用”。
  - **推荐补问**：
    - Q1：`"这个页面是给访客随时在网站上访问，还是仅在会议上由演讲人翻页讲解？"`
    - Q2：`"是否需要网站导航、SEO、跳转到其他页面？"`
  - **推荐判定方向**：
    - 若“随时访问 + 需要导航/SEO”为主，则：
      - 判定为 `scene = website`（landing/feature），不进入 presentation；
    - 只有当业务明确“这是给演讲人用的 deck，按章节线性讲述，不需要网站导航”时，才：
      - 建议进入 `scene = presentation`。
  - **不应静默决策的原因**：
    - 不少“产品介绍”需求本质是官网内容，若静默切到 presentation，会把站点能力（导航/SEO）丢掉；
    - 反之，若静默认为所有介绍页都是 website，真正需要线性叙事的 deck 会失去专门模板支撑。

### 7.2 B 组：presentation vs b_system

> 回答“经营分析 / QBR / 项目汇报”究竟是演示 deck 还是 dashboard/workspace。

- **规则 P3（B 组）：同时出现“经营视图/看板/任务列表”与“汇报/QBR/展示给上级”**
  - **触发条件**：
    - 需求中包含：
      - 数据/任务类词汇：`“季度经营视图”`、`“运营看板”`、`“KPI 仪表盘”`、`“项目任务列表”` 等；
      - 汇报类词汇：`“季度经营汇报”`、`“QBR”`、`“经营评审会”`、`“向管理层汇报”` 等。
  - **推荐补问**：
    - Q1：`"这个界面是给团队**日常登录使用**，还是主要在季度/年度评审会上，由演讲人按顺序讲解？"`
    - Q2：`"是否需要在界面内直接编辑数据、更新状态、处理工单/任务？"`
    - Q3：`"是否需要 drill-down 到明细、工单或其他操作页面？"`
  - **推荐判定方向**：
    - 若回答偏向“日常登录 + drill-down + 编辑/处理任务”，则：
      - 主场景应为 `scene = b_system`（dashboard/list/workspace）；
      - 若额外需要会议 deck，则另起 `scene = presentation` 任务承接季度汇报 deck；
    - 若回答偏向“只在评审会上使用，主要讲结果和决策，不做实时操作”，则：
      - 当前任务可落在 `scene = presentation`，对应 quarterly/business_report deck。
  - **不应静默决策的原因**：
    - “季度经营视图/经营看板”极易被误判为“就是季度汇报 deck”；
    - 若静默判定为 presentation，会让真正需要持续监控和操作的场景缺失 b_system 能力；
    - 若静默判定为 b_system，又会让经营汇报 deck 失去演示结构的真值源。

- **规则 P4（B 组）：项目规划相关需求（规划 deck vs 执行工作台）**
  - **触发条件**：
    - 需求描述中包含“项目规划/里程碑/风险/资源/项目汇报”等关键词，且：
      - 既提到“立项/阶段性评审/汇报会”等会议场景；
      - 又提到“日常更新任务/查看进度/处理风险”等操作场景。
  - **推荐补问**：
    - Q1：`"本次交付的核心是立项/阶段性评审用的一次性规划 deck，还是日常执行工作台？"`
    - Q2：`"是否需要在页面上直接创建/编辑任务、调整里程碑和负责人？"`
  - **推荐判定方向**：
    - 若核心是“一次性决策/评审材料”，且不需要日常编辑，则：
      - 当前任务判定为 `scene = presentation`，使用 `planning_proposal` 类模板；
      - 后续执行工作台另起 `scene = b_system` 任务；
    - 若核心是“日常协作/任务执行”（频繁登录更新状态），则：
      - 当前任务判定为 `scene = b_system` workspace；
      - 若另有汇报需求，再派生 presentation deck 任务。
  - **不应静默决策的原因**：
    - “项目规划页”经常被混用为既是汇报材料又是日常工作台；
    - 若不通过 stop&ask 拆清，会出现“用 deck 壳承载工作台”或“用 workspace 承载汇报会”的混用，后续极难治理。

### 7.3 C 组：anti_pattern 模板误用防护

> 回答 `presentation-work-report.html` / `presentation-minimal.html` 在什么语义信号下属于误用，应如何回退到 candidate 模板。

- **规则 P5（C 组）：将 `presentation-work-report.html` 视为“通用工作汇报模板”**
  - **触发条件**：
    - 任务描述中出现以下语义信号之一：
      - “希望所有周报/月报/工作汇报都基于 `presentation-work-report.html` 模板”；
      - “以后经营汇报、项目汇报统一用这一个 work-report 壳”；
      - “希望 AI 默认生成这种工作汇报结构”。
  - **推荐补问**：
    - Q1：`"这些周报/月报中是否包含大量需要在日常工作台中维护的任务/KPI/工单？"`
    - Q2：`"是否期望通过 deck 长期承载细碎进展，而不是在 b_system workspace 中管理？"`
  - **推荐判定方向**：
    - 若回答包含“长期、细碎进展”“需要频繁更新”，则：
      - 明确提示：`presentation-work-report.html` 在真值源中为 `grade = anti_pattern`, `use_scope = forbidden`；
      - 建议拆分为：
        - 汇报 deck → 使用 `presentation-business.html` 或 `presentation-planning.html`，聚焦结论与关键节点；
        - 日常进展 → 回到 `scene = b_system`（dashboard/workspace），用系统模板承载任务/指标管理；
    - 仅在极少数“单次总结性汇报”（例如年度复盘）且不涉及后续工作台管理时，可将该 anti_pattern 作为负面参考，而非主模板。
  - **不应静默决策的原因**：
    - 若静默接受，将反例模板升级为“通用工作汇报壳”，会把本应落在 b_system 的长期任务全部拉入 deck，直接违背 Phase 1 的 scene 治理目标；
    - 也会与 `TRUTH_SOURCES.md` 中“presentation 仍为兼容支持场景”的定位冲突。

- **规则 P6（C 组）：试图用 `presentation-minimal.html` 承载复杂经营/产品 deck**
  - **触发条件**：
    - 需求中出现以下语义信号之一：
      - “希望所有复杂 deck 都采用极简模板 `presentation-minimal.html`”；
      - “不想要那么多结构化区块，只要一页一大段极简内容”；
      - “哪怕是 QBR/产品发布会，也想统一用 minimal 壳”。
  - **推荐补问**：
    - Q1：`"该 deck 是否包含多个章节（议程/指标/决策/风险等），需要明确的章节导航和信息锚点？"`
    - Q2：`"是否需要在会后通过 deck 回溯决策与行动项，而不仅仅是‘看过一眼就算’？"`
  - **推荐判定方向**：
    - 若 deck 为复杂经营/产品场景（多章节、多决策、多指标）：
      - 明确提示：`presentation-minimal.html` 为 anti_pattern + forbidden，仅供视觉/动画参考；
      - 推荐使用：
        - 产品发布/介绍 → `presentation-product.html`；
        - 经营/QBR 汇报 → `presentation-business.html`；
        - 项目规划提案 → `presentation-planning.html`；
      - 极简视觉诉求可通过上述模板的样式/模块编排实现，而不是退回 minimal 反例壳。
  - **不应静默决策的原因**：
    - 若静默允许 minimal 壳承载复杂 deck，会让“章节导航/决策区/亮点区”等关键骨架消失，审计难以判断信息是否缺失；
    - 也会把“为了好看牺牲信息质量”的模式固化为默认选项，直接削弱治理效果。

---

## 8. Guard 回归样本（presentation 专向）

> 本节补充 5 条专门用于验证第 7 节 Guard 建议是否足够的样本，重点覆盖：
> - 产品发布 deck vs 官网落地页；
> - 季度经营汇报 deck vs 日常 KPI dashboard；
> - 项目规划 deck vs 项目执行工作台；
> - 同一主题 deck + 网站双产物；
> - anti_pattern 模板误用（work-report/minimal）。

### 8.1 `guard_case_product_deck_vs_landing` — 发布会 deck vs 官网首页

- **输入描述**：
  - “为‘灵境智能云’做一次发布会演示文稿，用于线下发布会演讲；同时 PRD 里顺带提到‘也需要官网首页介绍产品’。”
- **预期 scene / page_type / template**：
  - 当前任务：
    - 若以发布会 deck 为主：`scene = presentation` / `page_type = product_presentation` / `template = presentation-product.html`；
  - 官网需求：
    - 需另起任务：`scene = website` / `page_type = landing` / `template = website-complete.html`。
- **是否应 stop&ask**：
  - 是，应命中 **规则 P1（A 组）**：
    - 自动补问“第一优先是 deck 还是官网”“是否接受拆分为 deck + 官网任务”。
- **对应 Guard 建议命中情况**：
  - 命中 P1 的触发条件（同时出现演讲与官网）；
  - 通过补问，将需求拆分为 presentation + website 两条任务。
- **结论**：
  - Guard 建议应确保不会产生“既当 deck 又当官网”的万能页，而是明确拆分 scene，并为每个 scene 选择合适模板。

---

### 8.2 `guard_case_quarterly_deck_vs_dashboard` — 季度经营汇报 deck vs 日常 KPI dashboard

- **输入描述**：
  - “希望有一个‘季度经营视图’，既能在 QBR 上做汇报，又能让经营团队平时每天登录查看实时 KPI 和告警，并 drill-down 到明细。”
- **预期 scene / page_type / template**：
  - QBR 汇报 deck：`scene = presentation` / `page_type = business_report` / `template = presentation-business.html`；
  - 日常 KPI dashboard：`scene = b_system` / `page_type = dashboard` / `template = b-system-charts.html` 或同类模板。
- **是否应 stop&ask**：
  - 必须，应命中 **规则 P3（B 组）**：
    - 补问“日常登录 vs 只在评审会使用”“是否需要编辑/处理任务、drill-down”。
- **对应 Guard 建议命中情况**：
  - 若用户确认“既要日常使用又要 QBR 汇报”，Guard 建议会：
    - 将日常部分稳定判为 `b_system` dashboard；
    - 建议另起 presentation QBR deck 任务，而不是用一个 hybrid 页面承载两者。
- **结论**：
  - 本样本验证 P3 足以区分“QBR deck”与“日常 BI/dashboard”，并引导拆分为 presentation + b_system 两套产物。

---

### 8.3 `guard_case_planning_deck_vs_workspace` — 项目规划 deck vs 执行工作台

- **输入描述**：
  - “为新项目做一个‘统一规划页面’，既要在立项会上展示背景/目标/里程碑/风险，又希望团队后续每天在同一页面更新任务状态和进度。”
- **预期 scene / page_type / template**：
  - 立项会规划 deck：`scene = presentation` / `page_type = planning_proposal` / `template = presentation-planning.html`；
  - 执行阶段工作台：`scene = b_system` / `page_type = workspace` / `template = b-system-production-plan.html` 等。
- **是否应 stop&ask**：
  - 必须，应命中 **规则 P4（B 组）**：
    - 补问“本次交付核心是评审 deck 还是日常工作台”“是否需要在界面内编辑任务/更新进度”。
- **对应 Guard 建议命中情况**：
  - 若用户承认“需要日常执行工作台”：
    - Guard 建议会引导将执行部分拆出为 `b_system` 任务；
    - 当前任务仅保留立项会 deck 的职责，落在 presentation。
- **结论**：
  - 本样本验证 P4 能有效阻止“用一个 deck 页面同时做工作台”，迫使项目规划场景拆为“决策前 deck + 执行工作台”两条链路。

---

### 8.4 `guard_case_topic_deck_plus_site` — 同一主题的 deck + 官网专题页

- **输入描述**：
  - “围绕‘工业数字孪生平台’，希望有一套分享 deck 用于路演，同时做一个官网专题页，方便会后长期对外展示。”
- **预期 scene / page_type / template**：
  - 分享 deck：`scene = presentation` / `page_type = product_presentation` / `template = presentation-product.html`；
  - 官网专题页：`scene = website` / `page_type = landing` 或 `feature` / `template = website-complete.html` 或 `website-feature-solution.html`。
- **是否应 stop&ask**：
  - 是，应命中 **规则 P1（A 组）**：
    - 补问“第一优先交付物是什么”“是否接受拆为 deck + site 两条任务”。
- **对应 Guard 建议命中情况**：
  - Guard 建议应：
    - 确认 deck → presentation、site → website 的双 scene 分工；
    - 避免尝试用一个页面同时满足“演讲 + 长期站点”双目标。
- **结论**：
  - 本样本验证 P1 在“deck + 网站双产物”场景下仍然稳定工作，不会把两条需求压缩成一个混合页。

---

### 8.5 `guard_case_anti_pattern_templates` — anti_pattern 模板误用（work-report/minimal）

- **输入描述**：
  - 场景 A：“希望所有内部周报/月报、项目周会都统一用 `presentation-work-report.html` 模板。”
  - 场景 B：“希望所有产品发布会/QBR deck 统一用极简 `presentation-minimal.html` 模板，看起来更干净。”
- **预期 scene / page_type / template**：
  - 场景 A：
    - 汇报 deck → 应使用 `presentation-business.html` 或 `presentation-planning.html`，视内容选择 business_report / planning_proposal；
    - 日常任务管理 → 应回到 `scene = b_system` workspace/dashboard；
    - `presentation-work-report.html` 维持 `grade = anti_pattern`, `use_scope = forbidden`；
  - 场景 B：
    - 产品发布/经营 deck → 应分别使用 `presentation-product.html` / `presentation-business.html`；
    - `presentation-minimal.html` 仅作视觉参考，不进入路由。
- **是否应 stop&ask**：
  - 必须：
    - 场景 A 命中 **规则 P5（C 组）**；
    - 场景 B 命中 **规则 P6（C 组）**。
- **对应 Guard 建议命中情况**：
  - P5：通过语义信号识别“想把 work-report 壳升级为通用 work_report 模板”，并强制拆分为 presentation deck + b_system workspace；
  - P6：通过语义信号识别“想用 minimal 壳承载复杂 deck”，并引导回 product/business/planning candidate 模板。
- **结论**：
  - 本样本验证 C 组规则足以阻止两类高风险 anti_pattern 误用，避免反例模板被当成“当前主模板”。

---

## 9. Guard 落地准备度判断（presentation）

### 9.1 当前 Guard 建议的成熟度

- **规则维度**：
  - A 组（P1–P2）已覆盖“产品/方案/营销类需求”在 presentation vs website 之间的主要歧义模式，并明确判断依据：
    - 是否用于会议/路演/评审；
    - 是否需要章节化线性叙事与翻页控制；
    - 是否需要网站导航/SEO/长期在线浏览。
  - B 组（P3–P4）已覆盖“经营分析/QBR/项目规划”在 presentation vs b_system 之间的典型混合场景：
    - 将“日常操作 + drill-down + 编辑任务”的需求稳定拉回 b_system；
    - 将“一次性决策/评审 deck”稳定归入 presentation。
  - C 组（P5–P6）将 `presentation-work-report.html` / `presentation-minimal.html` 的误用语义信号写成可执行规则：
    - 明确这两个模板在真值源中的 anti_pattern/forbidden 定位；
    - 给出推荐回退路径（对应的 candidate 模板与 b_system 工作台）。

- **样本维度**：
  - 第 3–4 节提供了 9 条 presentation W1 样本，覆盖正反例与 anti_pattern；
  - 第 8 节新增 5 条专门面向 Guard 的回归样本，对应逐条命中 P1–P6；
  - 这些样本共同验证：
    - 关键误判路径（deck vs site、deck vs dashboard/workspace、anti_pattern 误用）均有对应 Guard 建议；
    - 在正例场景下，Guard 建议不会阻止合法的 deck 使用 candidate 模板。

### 9.2 仍在观察、暂不 Guard 化的灰区

- **更复杂的多 scene 组合**：
  - 如“官网 + cockpit + deck”“dashboard + 快速演示视图 + 分享 deck”等三方混合，目前仅在文档中通过示意拆分处理；
  - 暂未在 EXTENSION_GUARD 级别详尽条文化，后续需要更多真实项目样本支撑。
- **presentation 与 ai_assistant 的深度协作场景**：
  - 例如“由助手自动生成/更新 deck，并在助手工作台中预览/讲解”，目前仅通过第 6.3 节的简化口径处理；
  - 尚未形成足够多的真实例子支撑 Guard 条文级规则。

### 9.3 是否建议进入 Guard 执行轮（修改 EXTENSION_GUARD.md）

- **判断**：
  - 就 Phase 1 / W1 范围而言，围绕 presentation 的三大核心问题：
    - presentation vs website；
    - presentation vs b_system；
    - anti_pattern 模板误用防护；
    - 已有相对成熟的规则组（P1–P6）和覆盖这些规则的回归样本（第 3–4 节 + 第 8 节）；
  - 与 website / ai_assistant 先前的 Guard 执行轮对比，presentation 侧已具备类似级别的“样本 + 规则 + 回归”基础；
  - 因此，从治理收益与风险平衡角度看：
    - **已具备进入下一步 Guard 执行轮（在 `EXTENSION_GUARD.md` 中追加小范围条文）的前置条件**，前提是：
      - 严格限定首批 Guard 改动在 P1–P6 所覆盖的基本边界与 anti_pattern 防护范围内；
      - 将本文作为设计蓝本，在 Guard 落地后再用第 8 节样本做一次小规模回归验证。

- **建议（仍停留在文档层）**：
  - 当前轮次只在 `PRESENTATION_PHASE1_VALIDATION.md` 中完成 Guard 建议稿与回归样本；
  - 下一轮若要修改 `EXTENSION_GUARD.md`，可按以下优先级推进：
    1. 落地 A 组（P1–P2）：presentation vs website 的 stop&ask 条款；
    2. 落地 B 组（P3–P4）：presentation vs b_system 的“汇报 vs dashboard/workspace”条款；
    3. 落地 C 组（P5–P6）：明确标注 `presentation-work-report.html` / `presentation-minimal.html` 为 anti_pattern，并给出误用防护条款。

> **Guard readiness 总结（一句话）**：在仅修改验证文档、不触碰 Guard/路由/模板的前提下，presentation 已通过本轮规则提炼与回归样本补强，具备进入下一步“在 `EXTENSION_GUARD.md` 中落地小范围 Guard 条款”的成熟度，但本文件仍是当前唯一的 presentation Guard 真值源，实际 Guard 修改应在下一轮单独执行。