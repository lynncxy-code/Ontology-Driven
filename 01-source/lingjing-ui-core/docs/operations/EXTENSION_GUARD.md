## 🛑 EXTENSION_GUARD — Phase 1 扩展与升级护栏（b_system + ue5_overlay）

> **目的**：约束 Claude Code / AI 在 `b_system` 与 `ue5_overlay` 场景下的扩展行为，明确哪些情况必须询问人类、复审 Level，哪些扩展是直接禁止的。
> **范围**：主要适用于当前 Phase 1 的 `b_system` 与 `ue5_overlay` 场景，部分条款（如 scene 边界与 limited 模板使用）扩展适用于 `website` 与 `ai_assistant` 场景。

---

## 1. 何时必须停下来问人（stop & ask）

> 满足以下任一条件时，不得静默决策，必须在输出中明确提示“需要人工确认”，并给出当前判断与疑点。

### 1.1 Scene / Type / Mode 不明确
- 无法从需求中明确区分：
  - `b_system` vs `website`：既有运营后台元素，又强调营销转化时；
  - `b_system` vs `ue5_overlay`：既有后台指标，又要求三维视图与 world-marker 时；
- 无法从 `task_router.json` 与模板映射中确定唯一的：
  - `target_type`（system）；
  - `target_mode`（UE5）。

### 1.2 System 类型边界不清
- 需求同时满足多个类型特征：
  - 如“既像仪表盘，又要求完整工单列表 + 复杂筛选 + 详情浮层”；
- 当前候选任务中，`b_system_dashboard_overview` 与 `b_system_list` / `b_system_advanced_list` / `b_system_detail` 多个 id 均有较高匹配度，且无法通过简单关键词区分。
- 对于“任务清单 + 状态统计 + 异常提醒 + 少量筛选”这类生产管理任务：
  - 若未明确首屏主任务流到底是“看 KPI / 统计概览”还是“查表格列表并处理任务”，必须 stop&ask；
  - 至少补问两点：① 任务清单是否是页面主区主体；② 异常提醒是摘要卡片，还是独立待办 / 告警队列；
  - 未澄清前，不得静默默认回 `b_system_dashboard_overview`，也不得直接升级为 `b_system_advanced_list`。
- 推荐的澄清问题（b_system）：
  - dashboard vs list：
    - “首屏主视图是 KPI/图表为主，还是表格列表为主？”
    - “用户进入页面后，最常做的第一件事是看整体趋势，还是筛选并处理单条记录？”
  - list vs advanced_list：
    - “筛选条件是否需要长期占据左侧独立面板，并与表格并列展示？”
    - “筛选维度是否多到需要分组/折叠，而不是放在顶部一行 search-bar 内？”
  - detail vs dashboard / workspace：
    - “本页是否只关注单个实体的全链路信息，还是同时承载多个对象的整体运营视图？”
    - “顶部是否需要成组 KPI 网格（stats-grid / charts-grid），如果是，是否考虑拆出单独 dashboard？”



### 1.3 UE5 Mode / 驾驶舱边界不清
- 在以下模式之间摇摆不定：
  - Mode 2 vs Mode 3：需求同时强调右侧设备详情与左侧告警中心；
  - Mode 2/3 vs Mode 5：需求同时明确提出“双侧固定面板 + 底部 Dock”，但业务方对复杂度接受度不明；
  - Mode 2/3/5 vs 数字孪生驾驶舱：需求中出现“驾驶舱 / cockpit / control center”等字样，但同时又希望降低复杂度。
- 推荐的澄清问题（ue5_overlay）：
  - minimal vs Mode 1：
    - “是否明确需要顶部 HUD 展示全局 KPI 或快速操作？”
    - “页面的主要信息是 HUD + 面板，还是只在三维场景上做轻量标注？”
  - Mode 2 vs Mode 3：
    - “告警信息是用一个完整的告警中心面板来承载，还是只是详情面板里的一个区域？”
    - “用户主要流程是按设备/批次查看详情，还是在告警队列中逐条处理告警？”
  - Mode 3 vs 驾驶舱 / Mode 5：
    - “是否真的需要双侧固定面板 / 底部 Dock 等复杂布局元素？”
    - “业务方是否接受 cockpit 级复杂度，还是更希望保持轻量态势感知视图？”
- `ue5_overlay_digital_twin_cockpit` 的 `target_mode = "N/A"` 被命中时，必须提示“数字孪生驾驶舱仅在明确场景下启用”。


### 1.4 涉及跨业务域或跨场景混合
- 用户要求：
  - 在一个页面内同时承载多个业务域的工作台（例如“生产运营 + 市场运营 + 财务运营”全部混在一个 b_system 仪表盘）；
  - 在一个 UE5 Overlay 中同时做数字孪生驾驶舱 + 轻量监控视图 + 大量表格详情。 

### 1.5 需要使用 `limited` 模板或特殊角色模板
- 准备使用以下模板时：
  - `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html`（Mode 5，`use_scope: limited`）
  - `examples/ue5-overlay/digital_twin_overlay_dashboard.html`（数字孪生驾驶舱，`use_scope: limited`）
  - `examples/b-system/b-system-ai-assistant.html`（`scene = ai_assistant`，`page_type = assistant_workspace`，`grade = limited`）
- 或准备使用在 `TRUTH_SOURCES.md` / `skill_version.json` 中被说明为仅用于 UE5 引擎集成 / 性能测试或 world-marker 测试、不作为普通业务任务主模板且未进入 `task_router` 主链的模板（例如 `examples/ue5-overlay/ue5_overlay_engine_test.html`）。
- 对于 `examples/b-system/b-system-ai-assistant.html`，必须额外满足：
  - 仅在 `scene = ai_assistant` 的任务中使用，不得在 `scene = b_system` / `website` / `ue5_overlay` 中作为通用后台首页或工作台壳；
  - 不得仅因为“布局好看”或“已有任务卡片/日志样式”而复用在审批、录入、列表管理等固定流程页面；
  - 若需求本质是 `dashboard` / `workspace` / `list` / `detail`，且去掉助手模块后页面仍然完整成立，应优先回到 `b_system` 模板族；
  - 在判定是否可以使用该模板前，至少补问：
    - “本页面的主任务是通过对话让助手澄清、规划并执行多步任务，还是执行固定业务流程？”
    - “是否需要完整的对话区 + 任务/计划板 + 工具调用日志 + 结果回顾四块结构？”

### 1.6 新增多个关键模块可能导致 Level 升级
- 在现有模板基础上，计划新增 ≥ 2 个 “scene_coverage_matrix.yml.decision_matrix” 所定义的关键业务模块；
- 新模块涉及新的信息架构层级（例如新增完整工作流区域、多视图联动区域等）。

### 1.7 website 页型边界不清（landing / feature / pricing）
- 难以判断需求更接近以下哪一种：
  - 首页型场景（landing）：首屏以品牌叙事 + Hero + 1–2 个 CTA 为主，后续板块是典型“产品/方案 + 信誉背书”。
  - 功能/方案介绍页（feature）：以能力模块、方案详解为主，不强调“这是整个官网首页”。
  - 定价页（pricing）：以套餐/价格对比表为主，主要任务是选择方案并完成转化。
- 推荐的澄清问题（website）：
  - landing vs feature：
    - “这一页是否是官网首页？访问者进入站点默认首先看到的是这页吗？”
    - “首屏的主要任务是理解品牌/产品定位，还是详细对比功能模块？”
  - feature vs pricing：
    - “这一页的主要目的是讲清你能做什么，还是帮助用户直接选一个价格方案？”
    - “是否需要清晰的价格卡片/套餐对比表？如果是，是否应单独拆出定价页？”
- 若同时要求“首页 + 详细功能介绍 + 完整定价表 + 联系表单”全部塞在同一页，应视为信息架构过载，必须 stop&ask：
  - 是否需要拆分为 landing + feature/pricing 组合；
  - 是否有明确的首要转化目标（如预约演示/提交线索）。

### 1.8 ai_assistant vs b_system 场景边界（基础规则）
- 当需求中同时出现“助手/聊天”等字样与“审批 / 录入 / 编辑 / 工单 / 列表管理”等固定业务流程词汇时，必须 stop&ask，至少补问：
  - “本页面的主任务是通过对话让助手澄清、规划并执行多步任务，还是执行固定的业务流程？”
  - “如果移除助手/聊天模块，这个页面是否仍然完整成立？”
- 若补问后确认：
  - 去掉助手/聊天模块页面仍然成立，且用户主要通过按钮/表单/列表执行固定流程 → 应判为 `scene = b_system`，优先从 `b_system` 模板族（dashboard / workspace / list / detail）中选择；
  - 页面以自然语言对话作为主入口，包含“澄清 → 规划 → 执行 → 复核”的完整链路，并需要清晰展示任务/计划板、工具调用日志与结果回顾 → 才可优先判为 `scene = ai_assistant`，并考虑使用 `b-system-ai-assistant.html` 这类 limited 模板（需同时满足 §1.5 与 §3.4 的约束）。
- 当同一页面既包含 dashboard/workspace 视图，又包含助手模块时，必须 stop&ask：
  - “用户在该页最常做的第一件事，是浏览/操作列表或仪表盘，还是与助手对话并让其 orchestrate 后续操作？”
  - “若拆成‘后台页面 + 助手工作台两页’，业务方是否可以接受？”
- 在没有明确说明”对话 orchestrate”为主的情况下，若页面仍具备完整 dashboard/workspace 价值，应优先判为 `scene = b_system`（助手作为组件/浮层），而非将整页切换为 `ai_assistant`。

### 1.8.1 ai_assistant 命中后落地骨架约束（Composition Boundary）

> 一旦场景判定为 `scene = ai_assistant`，以下骨架与扩展边界必须强制执行。

**必须保留的框架骨架**（与 `b_system` 完全一致，不得替换）：

```
b-layout-sidebar > b-sidebar + b-main > b-header + b-content
```

- 不得将 `b-layout-sidebar / b-sidebar / b-main / b-header` 替换或省略；
- 助手工作台的所有功能区域，必须落在 `.b-content` 内部，而不是另起根容器。

**合法扩展出口**（仅限 `.b-content` 内部）：

| 扩展元素 | 官方类名 | 说明 |
|---|---|---|
| 对话消息流 | `.message-bubble` | 消息气泡，用于用户 / AI 对话 |
| 工具调用卡片 | `.tool-call-card` | 工具调用日志展示 |
| 任务状态卡片 | `.task-status-card` | 任务进度 / 执行状态 |
| 自定义扩展 | `.pj-b-ai-{component}` | 项目前缀类，仅限在 `.b-content` 内，样式值必须全用 CSS Token |

**禁止自造类名（典型反例）**：

以下类名在审计中触发 `unknown_classes: ERROR`，一律禁止出现：

- `.ai-workspace`、`.ai-chat-pane`、`.ai-sidebar`
- `.message-bubble-ai`、`.message-avatar-ai`、`.ai-message`
- `.action-btn-primary`、`.chat-container`、`.chat-input-area`
- 任何以 `.ai-*` 开头、且不在 `class_registry.json` 中的自造类

**`<style>` 块禁止规则**：

- 命中 `ai_assistant` 场景后，禁止写 `<style>` 块定义任何骨架类（`b-layout-sidebar`、`b-sidebar` 等）的样式；
- 禁止写 `<style>` 块为自造类名定义整页样式；
- 若需扩展视觉，必须通过项目 CSS 文件引入，而非内联 `<style>`。

**检查信号**（审计脚本同时覆盖）：

若生成的 `ai_assistant` 页面中出现以下情况，视为 Composition Boundary 被突破：

- `b-layout-sidebar / b-sidebar / b-main / b-header` 任一缺失 → `frame_shell_missing: ERROR`
- 存在 `<style>` 块定义布局或组件样式 → `style_tag_leak: ERROR`
- 存在 `class_registry.json` 中未收录的类名（`ai-workspace` 等）→ `unknown_classes: ERROR`

### 1.9 presentation vs website 场景边界（基础规则）
- 当需求中同时出现：
  - 演示类词汇（如“演示文稿 / 演讲 / 路演 / 发布会 / 分享会”等）；
  - 站点类词汇（如“官网首页 / 落地页 / 专题页 / SEO / 长期在线 / 站点导航”等）；
  时，必须 stop&ask，至少补问：
  - “本次交付物的第一优先是会议/路演上的演讲 deck，还是用户长期访问的官网/专题页？”
  - “是否需要章节化线性叙事与翻页控制，还是需要站点导航 / SEO / 自由浏览？”
  - “是否接受将 deck 与官网专题页拆成两条任务，分别在 presentation 与 website 场景中治理？”
- 推荐判定方向：
  - 若回答偏向“用于会议/路演/评审，强调线性讲述 + 翻页控制” → 当前任务应优先判为 `scene = presentation`，对应产品/方案类 deck；官网/专题页需求另起 `scene = website` 任务；
  - 若回答偏向“长期在线访问，强调站点导航 / SEO / 多入口浏览” → 当前任务应判为 `scene = website`（landing/feature），演讲 deck 需求另起 `scene = presentation` 任务。
- 不应静默决策的原因：
  - “产品发布 / 方案介绍”类需求极易被误解为“只做一页既当 deck 又当官网”的万能页；
  - 若不 stop&ask，将难以在后续按 scene 治理模板与信息架构。

### 1.10 presentation vs b_system 场景边界（基础规则）
- 当需求中同时出现：
  - 汇报类词汇（如“经营汇报 / 季度经营视图 / QBR / 向管理层展示 / 项目汇报 / 立项评审”等）；
  - 操作类词汇（如“KPI 看板 / 日常登录 / drill-down / 实时查询 / 编辑 / 任务执行 / 工作台”等）；
  时，必须 stop&ask，至少补问：
  - “本次交付的核心是评审会/汇报会使用的一次性或阶段性 deck，还是团队日常操作的 dashboard / workspace？”
  - “是否需要在页面中进行实时查询、明细 drill-down、编辑状态或处理任务？”
- 推荐判定方向：
  - 若回答偏向“一次性/阶段性汇报 + 预先组织好的结论讲述，不在该界面执行操作” → 当前任务应判为 `scene = presentation`，对应 business_report / planning_proposal 等 deck；如确有日常工作台需求，应另起 `scene = b_system` 任务承接 dashboard/workspace；
  - 若回答偏向“日常登录使用 + 实时操作 / drill-down / 编辑 / 执行”为主 → 当前任务应判为 `scene = b_system`（dashboard / workspace），如另有会议 deck 需求，再派生 `scene = presentation` 任务。
- 不应静默决策的原因：
  - 若静默用一个页面兼任“汇报 deck + 工作台/看板”，会造成交互模式与信息架构混杂，难以在模板与审计层确保质量；
  - 也会削弱 `b_system` 与 `presentation` 在真值源中的分工，使后续治理成本显著升高。

---


## 2. 何时必须复审 Level（review Level）


> 以下情况不直接强制禁止，但必须重新评估当前 Level 是否合理，并在输出中说明理由。

### 2.1 b_system：从单模块扩展到多模块组合
- 原本选定 `level_1`，且仅在仪表盘中微调 KPI / 卡片内容；
- 后续 PRD 要求：
  - 新增完整的高级筛选区域（接近 `advanced_list`）；
  - 新增完整的详情区域（接近 `detail`）；
  - 新增新的工作流或审批轨迹模块；
- 若这些新增模块无法通过简单卡片重用实现，而需要明显重排布局，则应考虑从 `level_1` 升至 `level_2`。

### 2.2 b_system：需要多模板关键结构拼接
- 为了满足需求，计划在同一页面中同时引入：
  - `b-system-complete` 与 `b-system-production-plan` 等多模板的关键结构，而不仅是局部卡片参考；
- 此时应评估：
  - 当前页面是否仍属于“模板轻调”（Level 1）；
  - 还是已经进入“组件与规则编排”（Level 2）。

### 2.3 ue5_overlay：从 Mode 1/2/3 升级到 Mode 5 或 驾驶舱
- 当需求从：
  - 单 HUD 或 HUD + 右侧详情（Mode 1/2）
  - 升级为“双侧固定面板 + 底 Dock”（典型 Mode 5）；
- 或从普通监控/质量追踪场景升级为明确的“数字孪生驾驶舱”：
  - 必须重新评估 Level 是否应从 `level_1` 升至 `level_2` 甚至 `level_3`；
  - 并在 PRE-GEN 与后续说明中，明确这种升级的原因与对复杂度的影响。

### 2.4 审计结果提示关键结构变化
- `skill-audit.js` 的审计摘要中出现：
  - `template_match_score` 明显降低；
  - `missing_key_modules_count` 增加；
- 此时应复检当前 Level 判定是否与 matrix 中的规则仍然相符。

---

## 3. 何时禁止自动扩展（forbid auto extension）

> 以下行为在 Phase 1 中直接视为违规，应在输出中明确拒绝，并说明原因。

### 3.1 将 Mode 5 视为通用默认模板
- 在未得到明确业务指令与人工确认的前提下：
  - 不得将 `Mode 5`（双侧面板 + 底 Dock）用作任意 UE5 Overlay 的默认模式；
  - 不得在普通质量监控/态势感知场景中默认选用 `ue5_overlay_sidepanel_dock_layout`。

### 3.2 将 engine_test 拉入任务主链
- 不得：
  - 为 `examples/ue5-overlay/ue5_overlay_engine_test.html` 新增任务路由项；
  - 在普通业务需求（例如质量追踪、态势感知）中，将 engine_test 当作主模板使用；
- engine_test 仅可用于：
  - UE5 引擎集成测试；
  - world-marker 与桥接链路测试；
  - 不通过 `task_router` 主链进入。

### 3.3 使用 demo / forbidden 模板作为默认路由
- 所有在 `scene_coverage_matrix.yml` / `template_router.json` 中标记为：
  - `grade: demo` 或 `grade: anti_pattern`；
  - `use_scope: forbidden`；
- 一律不得作为：
  - `task_router.json` 中的 primary_templates / fallback_templates；
  - PRE-GEN 中的 `template` 字段值。
- 对于 `scene = presentation`，以下两个 anti_pattern 模板需额外注意：
  - `examples/presentation/presentation-work-report.html`
    - 典型误用语义信号包括：
      - “希望所有周报/月报/工作汇报都统一用 `presentation-work-report.html` 壳”；
      - “以后经营汇报、项目汇报默认使用这一套 work-report 模板”；
      - “希望 AI 默认生成这种工作汇报结构”。
    - 一旦检测到上述语义，应视为误用场景，必须 stop&ask，并明确提示：
      - 该模板在真值源中为 `grade = anti_pattern`, `use_scope = forbidden`，不能作为当前或未来的通用 work_report 壳；
      - 推荐回退路径：
        - 汇报 deck → 选择 `presentation-business.html` 或 `presentation-planning.html` 等 candidate 模板，聚焦关键结论与节点；
        - 日常任务/进展 → 回到 `scene = b_system` 的 dashboard / workspace 模板族管理，而不是长期堆在 deck 中。
  - `examples/presentation/presentation-minimal.html`
    - 典型误用语义信号包括：
      - “希望所有产品发布会/QBR deck 统一使用极简 `presentation-minimal.html` 壳”；
      - “复杂经营/产品 deck 也只要一页极简内容，不需要完整结构”；
    - 一旦检测到上述语义，应视为误用场景，必须 stop&ask，并明确提示：
      - 该模板在真值源中为 `grade = anti_pattern`, `use_scope = forbidden`，仅可作为视觉/动画参考，不得直接承接正式业务 deck；
      - 推荐回退路径：
        - 产品发布/方案介绍 deck → 使用 `presentation-product.html`；
        - 经营/QBR 汇报 deck → 使用 `presentation-business.html`；
        - 项目规划提案 deck → 使用 `presentation-planning.html`；
      - 如有强烈极简视觉诉求，应在上述 candidate 模板基础上通过样式与模块编排实现，而不是退回 minimal 反例壳。


### 3.4 未经确认使用 limited 模板作为通用解法
- 对以下模板：
  - `ue5_overlay_sidepanel_dock_layout.html`、`digital_twin_overlay_dashboard.html`、`b-system-ai-assistant.html` 等 `use_scope: limited` 的模板；
  - 在 `TRUTH_SOURCES.md` / `skill_version.json` 中被说明为仅用于 UE5 引擎集成 / 性能测试或 world-marker 测试、不进入 `task_router` 主链的模板（例如 `ue5_overlay_engine_test.html`）；
- 不得：
  - 在普通场景中直接使用作为主链模板；
  - 将其标记为新的任务路由 primary_template。

### 3.5 在 shell 与 class 真值之外自建骨架
- 对于 `b_system`：
  - 禁止替换 `b-layout-sidebar + b-sidebar + b-main + b-header` 框架壳；
- 对于 `ue5_overlay`：
  - 禁止替换 `ue5-overlay-root + ue5-overlay-viewport + ue5-overlay-safe-area` 外层骨架；`topbar-hud` 属于按需配置的 HUD 模块，而非强制框架层；
- 禁止：

  - 在上述框架层之外另起一套自定义根容器（如 `custom-overlay-root`、`my-dashboard-layout`）作为主要骨架。

### 3.6 普通列表误升为高级筛选列表
- 禁止仅因需求文案中出现“筛选”“过滤”等字样，就将普通列表页自动升级为 `advanced_list`：
  - 若筛选需求仍可由表格上方的筛选区 / 顶部筛选条承载，应优先保持 `list + top filter bar` 结构；
  - 只有当 PRD 明确要求“左侧独立筛选面板 / 多维复杂筛选 / 持续并列展示筛选条件”时，才可以考虑切换为 `advanced_list`，并按 `ROUTING_DECISION_PROTOCOL` 复查类型与 Level 判定。
- 当 PRE-GEN / 中间层已判定 `target_type = list` 时：
  - 若生成 HTML 中出现左侧 `filter-panel` / `advanced-data-table-side` 等高级筛选面板结构，应视为**违反本 Guard**，并由审计脚本给出 ERROR；
  - 在 Phase 1 中，除显式任务 id 为 `b_system_advanced_list` 外，默认禁止自动生成左侧筛选面板。
- 当 PRE-GEN / 中间层已判定 `target_type = advanced_list` 时：
  - 若生成 HTML 中未检测到 `advanced-data-table` + `filter-panel` / `advanced-data-table-side` 等典型高级筛选列表壳，应视为**advanced_list 壳缺失或类型判定错误**，由审计脚本给出 ERROR，建议降级为普通 list 或补齐左侧高级筛选面板结构。


### 3.7 Mode 2 误升为 Mode 3 / Mode 5
- 对于 `ue5_overlay_mode_2_hud_sidepanel`：
  - 默认布局为 HUD + 单侧质量/设备详情面板 + world-marker，不含告警中心面板、底部 Dock 或双侧固定面板；
  - 若 PRD 未明确出现“告警中心 / 告警列表 / 底部 Dock / 驾驶舱 / control center”等语义，不得从 Mode 2 升级为 Mode 3/5。
- 当 PRE-GEN / 中间层已判定 `target_mode = 2` 时：
  - 若生成 HTML 中出现 `.ue5-overlay-bottom-dock` / `.ue5-overlay-dock` 等 Dock 结构，或同时存在 `pj-ue5-layout-left` + `pj-ue5-layout-right` 这类双侧固定面板标记，应视为**布局升级跑偏**，由审计脚本给出 ERROR；
  - 如业务确需 Dock 或双侧固定面板，应改用 `layout_mode = 5` 候选模板，并在 PRE-GEN 中明确升级原因，由人工确认。

### 3.8 Mode 3 壳过轻 / 壳过重
- 对于 `ue5_overlay_mode_3_hud_alert_center`：
  - Mode 3 必须具备完整告警中心面板（`alert-center`），同时避免升级为驾驶舱级别布局；
- 当 PRE-GEN / 中间层已判定 `target_mode = 3` 或任务 id 为 `ue5_overlay_mode_3_hud_alert_center` 时：
  - 若生成 HTML 中未检测到 `alert-center` 相关壳结构，应视为**Mode 3 壳过轻**，由审计脚本给出 ERROR，建议降级为 Mode 2（质量追踪）或补齐告警中心面板；
  - 若生成 HTML 中检测到 `.ue5-overlay-bottom-dock` / `.ue5-overlay-dock` 等 Dock 结构，或同时存在 `pj-ue5-layout-left` + `pj-ue5-layout-right` 这类双侧固定面板标记，应视为**Mode 3 壳过重**，由审计脚本给出 ERROR，建议改用 `layout_mode = 5` 候选模板并由人工确认。

### 3.9 b_system 详情页误升级为仪表盘 / 工作台
- 对于 `b_system_detail`：
  - 详情页用于展示单个实体的完整信息（基本信息 + 状态时间线 + 关联记录），主任务流应围绕该实体展开；
  - 可以包含少量关联列表/表格，但不应在同一视图中承载多个独立主任务流或整体运营工作台。
- 当 PRE-GEN / 中间层已判定 `target_type = detail` 或任务 id 为 `b_system_detail` 时：
  - 如页面中检测到 `stats-grid` / `charts-grid` 等 KPI 网格壳，应视为在详情页中混入了 Dashboard 壳；
  - 若 PRD 同时强调“运营总览 / 多业务域工作台 / KPI 总览”等语义，应优先评估拆分为 dashboard + detail，而不是在 detail 中堆叠仪表盘模块。
- 审计脚本行为（由 `skill-audit.js` 实现）：
  - 在 `scene = b_system` 且 `task = b_system_detail` 时，检查 HTML 中是否出现 `stats-grid` 或 `charts-grid`；
  - 若检测到上述类名，则触发 `b_system_detail_dashboard_shell_forbidden`，给出 ERROR，并提示“详情页不应使用仪表盘壳，建议拆分为 dashboard + detail 或调整任务类型”。

### 3.10 Mode 1 与 minimal overlay 边界（单 HUD vs 极简无 HUD）
- 对于 `ue5_overlay_mode_1_single_hud`：
  - Mode 1 适用于需要在顶部展示少量全局 KPI、下方主要为三维视图与 world-marker 的轻量监控场景；
  - 典型结构为：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area` + `topbar-hud`，通常不包含完整 `detail-panel` / `alert-center` 面板。
- 对于 minimal overlay（如 `ue5_overlay_minimal_no_hud.html`）：
  - 用于仅需世界标注 + 轻量说明的极简叠加场景；
  - 结构通常为：`ue5-overlay-root` + `ue5-overlay-viewport` + `ue5-overlay-safe-area` + 少量 `world-marker`，**不包含 topbar-hud / alert-center / detail-panel / Dock**。
- 当 PRE-GEN / 中间层已判定 `target_mode = 1` 或任务 id 为 `ue5_overlay_mode_1_single_hud` 时：
  - 若生成 HTML 中未检测到 `topbar-hud` 类，说明页面实际更接近 minimal overlay，应触发审计 ERROR，并建议改用极简模板或补齐 HUD；
  - 若 PRD 明确仅需“无 HUD、仅 world-marker 标注”的视图，不应继续使用 Mode 1，而是选择 minimal overlay 路径。
- 审计脚本行为（由 `skill-audit.js` 实现）：
  - 通过文件路径推断 layout_mode，当 `layout_mode = 1` 时检查是否存在 `topbar-hud`；
  - 若未检测到，则触发 `ue5_mode1_hud_missing`（ERROR），提示“单 HUD 模式未检测到 HUD，建议改用 minimal overlay 或补齐 HUD”。

### 3.11 ai_assistant 场景命中后禁止整页自造 demo

- **问题模式**：AI 命中 `scene = ai_assistant` 后，倾向于生成一套完全自造的类名体系（`ai-workspace`、`ai-chat-pane`、`message-bubble-ai` 等），并用 `<style>` 块定义整页样式，彻底绕开官方框架层与组件体系。
- **本质**：Composition Boundary 被突破——有骨架类 intent（”要做助手页”），但实现时整页变成未受约束的 demo。
- **直接禁止**：
  - 禁止用自造类名（如 `.ai-workspace`）作为 ai_assistant 页面的根容器或主布局容器；
  - 禁止用 `<style>` 块为自造类名构建整页视觉体系（等同于 `style_tag_leak: ERROR`）；
  - 禁止省略 `b-layout-sidebar / b-sidebar / b-main / b-header` 骨架（等同于 `frame_shell_missing: ERROR`）；
  - 禁止在页面中混入 50 个以上未注册类名（达到此量级，说明整页已自造，而非规范扩展）。
- **正确路径**（见 §1.8.1）：
  1. 保留 `b-layout-sidebar + b-sidebar + b-main + b-header` 框架层；
  2. 在 `.b-content` 内用 `.message-bubble` / `.tool-call-card` / `.task-status-card` 承载对话功能；
  3. 项目级新增组件使用 `.pj-b-ai-{component}` 前缀，样式在项目 CSS 中定义（不含 `<style>` 块），且值全部引用 CSS Token；
  4. 运行 audit，修复所有 `frame_shell_missing`、`style_tag_leak`、`unknown_classes` ERROR 后方可交付。
- **审计脚本行为**：`ai_assistant` 场景已在 `skill-audit.js` 的 `detectSceneFromDom` 中优先识别（先于 `b_system`）；`frame_shell_missing` 检查对 `ai_assistant` 与 `b_system` 使用相同骨架规则，确保框架层不会因场景切换而被绕过。

### 3.12 ue5_overlay 场景禁止用 `<style>` 块重定义官方规范类

- **问题模式**：AI 在生成 UE5 Overlay 页面时，虽然使用了官方骨架类（`.ue5-overlay-root`、`.ue5-overlay-background`、`body` 等），却同时在 `<style>` 块中对这些类重新定义或覆写样式，导致 `style_tag_leak: ERROR`。
- **本质**：官方规范类的视觉定义已在 `lingjing-core-ue5-overlay.css` 中完整给出；在 HTML 内再写 `<style>` 是对”骨架不可侵入”原则的直接违反。

**直接禁止**：

- 禁止在 `<style>` 块中重定义以下类（或其子类）的任何属性：
  - `body`、`.ue5-overlay-root`、`.ue5-overlay-background`、`.ue5-overlay-viewport`
  - `.ue5-overlay-safe-area`、`.topbar-hud`、`.detail-panel`、`.alert-center`
  - `.layer-switcher`、`.world-marker`（world-marker 位置坐标用 `style=””` 内联属性，不是 `<style>` 块）
- 禁止为自造类名（如 `.my-ue5-panel`）写 `<style>` 块替换上述规范类的布局角色

**合法扩展路径**：

1. **内容扩展**：在 `.detail-panel__body` / `.detail-panel__section` / `.alert-center__list` 等官方容器内部补充字段，不需要新类名
2. **项目前缀扩展**：新增视觉模块使用 `.pj-ue5-{component}` 前缀类，样式在项目 CSS 文件中定义，**不在 HTML 内写 `<style>` 块**，值全部引用 CSS Token
3. **world-marker 位置**：唯一受控例外——`.world-marker` 的 `top` / `left` / `transform` 允许以 `style=””` 内联属性表达三维坐标，不视为污染

**审计脚本行为**：

- `skill-audit.js` 的 `style_tag_leak` 检查对 `ue5_overlay` 场景有效；
- 若 HTML 中存在任何 `<style>` 块，不论内容是否重定义官方类，均触发 `style_tag_leak: ERROR`；
- 修复方式：删除 `<style>` 块，将需要的项目样式移入项目 CSS 文件，或改用 Token 内联属性。

---

通过本 Guard 协议，Phase 1 的 `b_system` 与 `ue5_overlay` 中间层可以在不增加复杂 schema 的前提下，明确哪些扩展可以放心自动决策，哪些升级必须停下与人类确认，哪些行为则需要直接拒绝，从而减少 Claude Code / AI 在关键决策上的”自由脑补空间”。
