# TEMPLATE_ASSET_REFERENCE_MAP · 模板资产盘点与 AI 参考价值分层

> **文档目的**：为 `lingjing-ui-core` 当前模板库建立一份面向 AI/skill 的“模板资产地图”，明确每个主要 HTML 模板在 **参考价值分层 / 规范风险 / 真值源挂接** 上的位置，避免 AI 把 demo / anti_pattern / limited 资产当成主链模板使用。
>
> **不做的事**：本轮不修改任何 router / matrix / Guard / HTML 模板，只在文档层完成 **资产盘点 + 参考标注**，为后续治理提供输入。

---

## 1. 面向 AI 的模板资产分层框架

> 本节定义五类“模板资产层级”，供后文统一标注。

- **A. 主参考资产（Primary Reference）**  
  - **定义**：AI 可以优先参考，并作为 **主链结构依据** 的模板。  
  - **典型特征**：
    - `grade = canonical`, `use_scope = default`；
    - 有明确 `scene / page_types`；
    - 已进入 `scene_coverage_matrix.yml` + `task_router.json` 主链；
    - 在 Phase 1 中被视为该 scene 的“绿色锚点”。

- **B. 次参考资产（Secondary Reference）**  
  - **定义**：AI **可以参考且可被选为主壳**，但不应当成“所有任务的默认壳”。  
  - **典型特征**：
    - `grade = candidate`, `use_scope = default`；
    - 结构有价值且已在 scene_coverage / router 中登记；
    - 可能是 Phase 2 的 potential canonical，或只在特定页型/场景下适用。

- **C. 局部参考资产（Partial / Layout Reference）**  
  - **定义**：适合作为 **局部 section / module / layout** 的参考，不建议整体套用为主模板。  
  - **典型特征**：
    - 结构/布局有参考价值，但 `use_scope = limited`；
    - 或信息密度/复杂度较高，更适合作为“模式草图”而非开箱主壳；
    - AI 在 Level 2 编排时可局部借鉴结构与模块组合，但应谨慎选为整页主壳。

- **D. 反例资产（Negative / Guard Reference）**  
  - **定义**：AI **不应作为正向参考** 的模板，但必须知道“不能如何使用”。  
  - **典型特征**：
    - `grade ∈ {demo, anti_pattern}`, `use_scope = forbidden`；
    - 或仅用于 engine test / component gallery / 占位；
    - 常被 EXTENSION_GUARD / 文档作为 **anti_pattern / demo only** 明确点名。

- **E. 悬空资产（Unanchored / Low-priority Reference）**  
  - **定义**：当前缺少清晰治理位置，不建议 AI 主动参考或路由到此模板。  
  - **典型特征**：
    - 不在 `scene_coverage_matrix.yml.scene_coverage.*.candidate_templates` 真值列表中；
    - 或不在 `data/template_router.json` / `data/task_router.json` 中出现；
    - 也未在 Phase 1 验证文档中承担代表样本角色。

> **规范风险字段**：后文每个模板还会标注 `规范风险 = 低 / 中 / 高`：
> - **低**：canonical 或结构稳定的 candidate，`risk_notes_zh` 为空或仅为提醒性质；
> - **中**：candidate 或 limited，存在一定使用前置条件，`risk_notes_zh` 有“使用场景限定/需清理”等提示；
> - **高**：demo / anti_pattern / forbidden，或 use_scope = limited 且 Guard 明确列为高风险误用源。

---

## 2. 按模板出资产地图

> 本节基于 `data/template_router.json` + `scene_coverage_matrix.yml.scene_coverage.*.candidate_templates` + `TRUTH_SOURCES.md` + 各 scene 验证文档，将当前对治理有意义的模板逐一标注。
>
> 字段说明：
> - **path**：模板文件路径；
> - **scene / page_types / grade / use_scope**：来自 template_router + matrix；
> - **引用情况**：是否被 `template_router` / `task_router` / `scene_coverage` / 验证文档 / Guard 提及；
> - **资产层级**：A/B/C/D/E；
> - **规范风险**：低 / 中 / 高；
> - **说明**：一句话解释分层与风险理由。

### 2.1 `b_system` 模板资产

| path | scene | page_types | grade / use_scope | router / 真值引用 | 资产层级 | 规范风险 | 说明 |
|------|-------|------------|-------------------|-------------------|----------|----------|------|
| `examples/b-system/b-system-complete.html` | b_system | [dashboard, overview] | canonical / default | `template_router` / `scene_coverage` / `task_router.b_system_dashboard_overview` / `TRUTH_SOURCES` / `system-template-map` | **A 主参考** | **低** | B 端系统的 canonical 首页壳，Phase 1 中所有 dashboard/overview 的主锚点，审计与 Guard 完整覆盖，误用风险低。 |
| `examples/b-system/b-system-charts.html` | b_system | [dashboard] | canonical / default | `template_router` / `skill_version` / `SKILL.md §1.3` / `b-system-composition-recipes` | **A 主参考** | **中** | 图表密集型仪表盘 canonical 示例，作为 chart 接入与主题切换规范的主例，结构稳定但依赖较多脚本，生成时需严格遵守 chart 规范。 |
| `examples/b-system/b-system-task-list-top-filters.html` | b_system | [list] | candidate / default | `template_router` / `scene_coverage` / `task_router.b_system_list.primary` / `system-template-map §2` / WEBSITE_PHASE1 多处引用 | **A 主参考**（list 主锚） | **低** | 标准列表页 + 顶部筛选条，是 list 主链的绿色锚点，虽然标记为 candidate，但在 Phase 1 中被视作 list 族主参考资产。 |
| `examples/b-system/b-system-advanced-list-with-left-filter-panel.html` | b_system | [advanced_list] | candidate / default | `template_router` / `scene_coverage` / `task_router.b_system_advanced_list.primary` / `system-template-map §3` | **A 主参考**（advanced_list 主锚） | **中** | 高级筛选列表 canonical 壳，用于 PRD 明确要求左侧筛选面板时，Guard 对“普通 list 误升”为 advanced_list 有强约束，使用前需满足 must_keywords。 |
| `examples/b-system/b-system-detail-order.html` | b_system | [detail] | candidate / default | `template_router` / `scene_coverage` / `task_router.b_system_detail.primary` / `system-template-map §4` | **A 主参考**（detail 主锚） | **中** | 单实体详情页代表模板，系统 Guard 有“detail 误升 dashboard”条款；正常 detail 用途风险低，但混入 KPI 网格时需遵守 Guard 提示拆分页面。 |
| `examples/b-system/b-system-production-plan.html` | b_system | [planning] | candidate / default | `template_router` / `scene_coverage` / `task_router` 多个 fallback / `TRUTH_SOURCES` | **B 次参考** | **中** | 生产排程/计划型页面 candidate 模板，可作为 dashboard/list/detail 的 fallback 或 workspace 壳，`risk_notes_zh` 提醒含部分 deprecated 类，晋级前需审计。 |
| `examples/b-system/b-system-saas.html` | b_system | [saas_admin, operations_workspace] | candidate / default | `template_router` / `scene_coverage` / `task_router.b_system_dashboard_overview.fallback` | **B 次参考** | **中** | 通用 SaaS 后台/作业系统壳，适合 workspace/运营工作台类场景；`risk_notes_zh` 指出“表达偏演示/验证，不应作为所有 b_system 默认模板”，AI 使用时应基于任务特征慎选。 |
| `examples/b-system/b-system-showcase.html` | b_system | [component_gallery] | demo / forbidden | `template_router` / `scene_coverage` / `TRUTH_SOURCES` / `EXTENSION_GUARD §3.3` | **D 反例** | **高** | 组件展示页，仅供人工查阅，不得作为业务模板或 PRE-GEN template；AI 只能将其视作“反例/组件图鉴”，严禁路由到此。 |
| `examples/b-system/b-system-sidebar.html` | b_system | [component_gallery] | demo / forbidden | 同上 | **D 反例** | **高** | 侧边栏组件展厅，场景 coverage 明确标记 forbidden，AI 不得选为任何任务主模板，仅可人工参考侧边栏视觉。 |
| `examples/b-system/b-system-ai-assistant.html` | ai_assistant | [assistant_workspace] | canonical / limited | `template_router` / `scene_coverage.ai_assistant` / `task_router.ai_assistant_workspace.primary` / `AI_ASSISTANT_PHASE1_VALIDATION` / `EXTENSION_GUARD §1.5/§1.8/§3.4` | **B 次参考** | **高** | ai_assistant 场景唯一 workspace 主壳，对纯助手工作台非常重要，但 `use_scope = limited` 且 Guard 有严格误用条款：仅在“对话 + 计划板 + 工具日志 + 结果区”齐备的 assistant_workspace 中可作为主参考，其他场景视为误用。 |

### 2.2 `website` 模板资产

| path | scene | page_types | grade / use_scope | router / 真值引用 | 资产层级 | 规范风险 | 说明 |
|------|-------|------------|-------------------|-------------------|----------|----------|------|
| `examples/website/website-complete.html` | website | [landing, pricing] | canonical / default | `template_router` / `scene_coverage.website` / `task_router.website_landing_marketing.primary` / `task_router.website_pricing_page.primary` / `WEBSITE_PHASE1_VALIDATION` / `TRUTH_SOURCES` | **A 主参考** | **中** | website Phase 1 的 canonical homepage 壳，承载 landing 与当前阶段所有 pricing；Guard 文档对 landing/feature/pricing 边界有清晰 stop&ask；模板本身稳定，但在复杂 pricing 场景中需按 Level 2 编排扩展模块。 |
| `examples/website/website-feature-solution.html` | website | [feature] | candidate / default | `template_router` / `scene_coverage.website` / `task_router.website_feature_highlight.primary` / `WEBSITE_PHASE1_VALIDATION` | **A 主参考**（feature 主锚） | **中** | 解决方案/能力介绍页主壳，已在多条 feature 样本中稳定命中，是 feature 页型的 primary example；结构稳定，但仍标记 candidate，后续晋级需更多项目审计。 |
| `examples/website/website-showcase.html` | website | [component_gallery] | demo / forbidden | `template_router` / `scene_coverage.website` / `TRUTH_SOURCES` / `EXTENSION_GUARD §3.3` | **D 反例** | **高** | 官网组件展厅 demo，不得作为业务页模板或默认路由，AI 仅可视作组件视觉参考；任何路由到本模板的行为都视为误用。 |

### 2.3 `ue5_overlay` 模板资产

| path | scene | page_types | grade / use_scope | router / 真值引用 | 资产层级 | 规范风险 | 说明 |
|------|-------|------------|-------------------|-------------------|----------|----------|------|
| `examples/ue5-overlay/ue5_overlay_data_viz.html` | ue5_overlay | [overlay_dashboard, data_viz] | canonical / default | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_mode_1_single_hud.primary` / `ue5-template-map Mode 1` / `TRUTH_SOURCES` | **A 主参考** | **低** | Mode 1 单 HUD 监控大屏 canonical 模板，是 UE5 主线最重要的参考之一，已形成完整 Playbook 与 Guard，风险主要在模块取舍而非模板本身。 |
| `examples/ue5-overlay/ue5_overlay_minimal_no_hud.html` | ue5_overlay | [overlay_dashboard, minimal_overlay] | candidate / default | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_minimal_no_hud.primary` / `ue5-template-map minimal` | **B 次参考** | **中** | 极简 Overlay 模板，用于“无 HUD、仅 world-marker”的场景；`risk_notes_zh` 明确要求：一旦 PRD 需要 HUD/KPI/告警中心，应回退至 Mode 1/2/3，因此 AI 只能在“明确 minimal”任务中选它。 |
| `examples/ue5-overlay/ue5_overlay_quality_tracking.html` | ue5_overlay | [overlay_dashboard, quality_tracking] | canonical / default | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_mode_2_hud_sidepanel.primary` / `ue5-template-map Mode 2` | **A 主参考** | **中** | Mode 2 HUD + 右侧质量详情面板 canonical 模板，是质量追踪场景主锚；适合作为主参考，但需遵守“不升级为 Dock / 双侧面板”的 Guard 条款。 |
| `examples/ue5-overlay/ue5_overlay_dashboard.html` | ue5_overlay | [overlay_dashboard] | canonical / default | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_mode_3_hud_alert_center.primary` / `ue5-template-map Mode 3` | **A 主参考** | **中** | Mode 3 HUD + 告警中心 canonical 模板，Alert Center 壳是必备模块；适合 AI 作为告警总览主壳参考，但必须保证 `alert-center` 存在，避免壳过轻或误升 Mode 5。 |
| `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html` | ue5_overlay | [overlay_full_layout] | candidate / limited | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_digital_twin_cockpit.fallback` / `ue5-template-map Mode 5` / `EXTENSION_GUARD §1.5 / §3.1 / §3.4` | **C 局部参考** | **高** | Mode 5 双侧面板 + 底 Dock 草图模板，`use_scope = limited`，仅在**明确数字孪生驾驶舱**场景下由人工确认使用；AI 应主要将其视为 layout 参考，不得把它当作所有 Overlay 的默认壳；首批修复在文件头、安全区与时间轴脚本中强化了 cockpit/limited 注释与 demo-only 标记。 |
| `examples/ue5-overlay/digital_twin_overlay_dashboard.html` | ue5_overlay | [digital_twin_dashboard] | candidate / limited | `template_router` / `scene_coverage.ue5_overlay` / `task_router.ue5_overlay_digital_twin_cockpit.primary` / `ue5-template-map §6` / `EXTENSION_GUARD §1.5 / §3.1` | **C 局部参考** | **高** | 数字孪生驾驶舱候选模板，混合 `ue5_overlay + b_system` 元素，`use_scope = limited`；适合作为数字孪生 cockpit 的示意与 layout 参考，AI 不应在普通 overlay 任务中默认选择；首批修复通过注释/aria/底部 dock 文案强调其为数字孪生 + 运控 cockpit 混合模板，而非通用 overlay 或通用 b_system dashboard。 |
| `examples/ue5-overlay/ue5_overlay_mock_bridge.html` | ue5_overlay | [placeholder] | anti_pattern / forbidden | `template_router` / `scene_coverage.ue5_overlay` / `TRUTH_SOURCES` / `EXTENSION_GUARD §3.2/§3.3` | **D 反例** | **高** | bridge 占位示例，明确标记为 anti_pattern + forbidden，仅用于反例说明或 engine bridge 测试；AI 必须视其为“不要用”的模板，不得作为任何任务主壳。 |
| `examples/ue5-overlay/ue5_overlay_engine_test.html` | ue5_overlay | —（未进入 page_type / router 主链） | 未登记 / special-purpose | `TRUTH_SOURCES` / `EXTENSION_GUARD`（未进入 `template_router` / `task_router` / `scene_coverage.ue5_overlay.candidate_templates`） | **C 局部参考**（special-purpose local reference） | **中** | UE5 overlay 场景下的可视化图表 / engine test / 工程演示参考页，价值在于局部图层、渲染联调与工程示例，不是纯反例或 forbidden 页面；但它不应作为通用 overlay page shell，也不进入 router 主链或默认模板推荐。 |

### 2.4 `ai_assistant` 与 `presentation` 模板资产

| path | scene | page_types | grade / use_scope | router / 真值引用 | 资产层级 | 规范风险 | 说明 |
|------|-------|------------|-------------------|-------------------|----------|----------|------|
| `examples/b-system/b-system-ai-assistant.html` | ai_assistant | [assistant_workspace] | canonical / limited | 见上表 b_system 区 | **B 次参考** | **高** | ai_assistant 工作台的唯一主壳，对助手场景是主参考；但因 `use_scope = limited` 且 Guard 有严格误用防护，AI 使用时必须满足“多轮澄清 + 计划板 + 工具日志 + 结果区”四块结构。 |
| `examples/presentation/presentation-product.html` | presentation | [product_presentation] | candidate / default | `template_router` / `scene_coverage.presentation` / `task_router.presentation_product_story.primary` / `PRESENTATION_PHASE1_VALIDATION` | **B 次参考**（strong candidate） | **中** | 产品发布/产品介绍 deck 的主壳，在 Phase 1 文档中被视为 strong candidate / potential canonical，但真实项目样本仍有限，暂不升为 A。 |
| `examples/presentation/presentation-business.html` | presentation | [business_report] | candidate / default | 同上 | **B 次参考**（strong candidate） | **中** | 季度经营/业务汇报 deck 主壳，与 `presentation_quarterly_review` UX spec 配合良好，是 business_report 方向的强 candidate；本轮补位修复已在模板内部增强 business_review/QBR 角色注释并收敛一处标题内联样式，使其更适合作为经营汇报 deck 的结构参考。 |
| `examples/presentation/presentation-planning.html` | presentation | [planning_proposal] | candidate / default | `template_router` / `scene_coverage.presentation` / `task_router.presentation_product_story.fallback` / `PRESENTATION_PHASE1_VALIDATION` | **B 次参考** | **中** | 项目规划提案 deck 模板，结构合理，但样本与使用频次相对较少，暂作为次参考资产，后续视项目使用情况决定晋级。 |
| `examples/presentation/presentation-work-report.html` | presentation | [work_report] | anti_pattern / forbidden | `template_router` / `scene_coverage.presentation` / `TRUTH_SOURCES` / `PRESENTATION_PHASE1_VALIDATION` / `EXTENSION_GUARD §3.3` | **D 反例** | **高** | 已被明确定义为工作汇报 anti_pattern 模板，仅用于反例说明；AI 必须避开，不得作为“通用 work_report 壳”，相关需求应回退到 business/planning deck + b_system workspace 组合。 |
| `examples/presentation/presentation-minimal.html` | presentation | [minimal_presentation] | anti_pattern / forbidden | 同上 | **D 反例** | **高** | 极简演示反例模板，缺少结构化骨架与导航，仅供视觉参考；任何“用 minimal 承载复杂产品/经营 deck”的需求都应被 Guard 阻止，推荐回退到 product/business/planning candidate 模板。 |

---

## 3. 按 scene 的资产摘要

> 本节从每个 scene 视角给出“主参考 / 次参考 / 反例 / 悬空资产”的简要概览。

### 3.1 `b_system` 场景

- **主参考资产（A）**：
  - `b-system-complete.html`（dashboard/overview 主壳）；
  - `b-system-charts.html`（图表密集仪表盘）；
  - `b-system-task-list-top-filters.html`（list 主链）；
  - `b-system-advanced-list-with-left-filter-panel.html`（advanced_list 主链）；
  - `b-system-detail-order.html`（detail 主链）。
- **次参考资产（B）**：
  - `b-system-production-plan.html`（planning / workspace 候选模板）；
  - `b-system-saas.html`（泛 SaaS 后台 / operations workspace 候选壳）；
  - `b-system-ai-assistant.html`（在 ai_assistant 场景下使用的 limited 工作台壳）。
- **反例资产（D）**：
  - `b-system-showcase.html`、`b-system-sidebar.html` → 组件展厅 demo，仅用于人工浏览，不得作为业务模板。  
- **悬空资产（E）**：
  - 无在 template_router / scene_coverage 中登记但未定位的 b_system 模板；其它零散 examples 若存在，可视为 **局部参考/低优先级 demo**，当前不进入 AI 主路由。
- **最值得观察的资产类型**：
  - `b-system-production-plan` / `b-system-saas` 等 planning/workspace 类 candidate：结构有价值，但 risk_notes 提示需清理 deprecated 类和演示性内容；中长期可能进入规范审查与 canonical 评估队列。

### 3.2 `website` 场景

- **主参考资产（A）**：
  - `website-complete.html`（landing + pricing 主壳）；
  - `website-feature-solution.html`（feature 主壳）。
- **次参考资产（B）**：
  - 暂无额外 B 级模板——website 当前模板族刻意保持收敛，核心结构集中在上述两张模板上。  
- **反例资产（D）**：
  - `website-showcase.html` → 组件/品牌展示 demo，不得用作业务页。  
- **悬空资产（E）**：
  - 无在真值源中登记但未说明职责的 website 模板。  
- **观察重点**：
  - `website-complete` 承载 pricing 的压力（重度 pricing 页是否挤压 homepage 壳）；
  - 未来是否需要从 `website-complete` 中拆出独立 pricing 模板，取决于 observation 文档中的样本计数与结构压力。

### 3.3 `ue5_overlay` 场景

- **主参考资产（A）**：
  - `ue5_overlay_data_viz.html`（Mode 1 单 HUD）；
  - `ue5_overlay_quality_tracking.html`（Mode 2 HUD + 单侧详情面板）；
  - `ue5_overlay_dashboard.html`（Mode 3 HUD + 告警中心）。
- **次参考 / 局部参考资产（B/C）**：
  - `ue5_overlay_minimal_no_hud.html` → **B 次参考**，极简 overlay；
  - `ue5_overlay_sidepanel_dock_layout.html` / `digital_twin_overlay_dashboard.html` → **C 局部参考**，仅在 layout_mode=5 / 数字孪生 cockpit 场景作为 layout 参考，`use_scope = limited`，规范风险高。  
- **反例资产（D）**：
  - `ue5_overlay_mock_bridge.html` → anti_pattern 占位页，明确禁止进入业务路由。  
- **局部参考资产（C，special-purpose）**：
  - `ue5_overlay_engine_test.html` → UE5 可视化 / engine test / 工程演示参考页；不进入真值模板主链，也不作为默认模板推荐，但可作为局部图层、渲染联调与工程示例参考。  
- **观察重点**：
  - minimal / Mode 5 / digital twin 类型的使用频率与边界：目前都通过 `limited` + Guard 控制，只允许在明确场景下按规则使用，后续可能进入 Phase 2 canonical/规范审查队列。

### 3.4 `ai_assistant` 场景

- **主参考资产（A）**：
  - 无额外 canonical 模板——当前唯一模板 `b-system-ai-assistant.html` 已在上文标注为 **B 次参考 + limited**。  
- **次参考资产（B）**：
  - `b-system-ai-assistant.html`：assistant_workspace 主壳，受 `use_scope = limited` 与 `EXTENSION_GUARD §1.5/§1.8/§3.4` 严格约束。  
- **反例 / 悬空资产（D/E）**：
  - 无单独 ai_assistant demo/anti_pattern 模板；风险更多来自 **误用 limited 模板**，而非模板本身。  
- **观察重点**：
  - “纯助手工作台” vs “带聊天的 b_system 工作台” vs “dashboard/cockpit + assistant 混合页”的边界样本；
  - 若 future 出现更多稳定的助手子类型（轻量问答/回顾页等），可能触发模板族与 page_type 进一步分化。

### 3.5 `presentation` 场景

- **主/次参考资产（B）**：
  - `presentation-product.html`（产品发布/介绍 deck strong candidate）；
  - `presentation-business.html` (经营/业务汇报 deck strong candidate)；
  - `presentation-planning.html`（项目规划提案 deck candidate）。
- **反例资产（D）**：
  - `presentation-work-report.html`（工作汇报 anti_pattern）；
  - `presentation-minimal.html`（极简演示 anti_pattern）。
- **悬空资产（E）**：
  - 无在真值源中登记但未被文档定位的 presentation 模板。  
- **观察重点**：
  - product/business/planning 三类 deck 在真实项目中的使用规模与结构稳定性，决定是否有资格从 B 晋级为 canonical；
  - anti_pattern 模板的误用频率，将驱动 Guard 文案/约束是否需要进一步收紧。

---

## 4. 规范风险标记与后续审查候选

> 本节从“规范风险”视角抽取一批资产，标记出 **最值得后续规范审查 / 定位澄清 / 暂不处理** 的模板。

### 4.1 最值得优先做规范审查的资产（高价值 + 中/高风险）

- **b_system**：
  - `b-system-production-plan.html`（planning）  
    - **风险**：`risk_notes_zh` 明确含 deprecated 类与占位内容；
    - **价值**：承载项目/生产计划类 workspace，后续极可能成为 workspace canonical 候选。  
  - `b-system-saas.html`（saas_admin / operations_workspace）  
    - **风险**：表达偏 demo/验证，容易被误当成“万能后台壳”；
    - **价值**：对通用 SaaS 后台/作业系统场景帮助很大，是 b_system 侧 workspace 模式的重要候选。  

- **ue5_overlay**：
  - `ue5_overlay_sidepanel_dock_layout.html`（Mode 5 layout）  
    - **风险**：`use_scope = limited`，结构复杂，若使用口径模糊，容易被误当“通用 overlay 壳”；
    - **价值**：定义数字孪生 cockpit 布局的核心草图，对后续 cockpit 治理至关重要。  
  - `digital_twin_overlay_dashboard.html`（digital twin cockpit）  
    - **风险**：limited，混合 b_system 元素，场景边界与 b_system/website 关系复杂；
    - **价值**：真实数字孪生驾驶舱样式与交互最直接的参考资产之一。  

- **ai_assistant**：
  - `b-system-ai-assistant.html`（assistant_workspace）  
    - **风险**：`use_scope = limited`，Guard 明确将“为好看借壳”“FAQ/洞察型助手”视为误用，规范风险高；
    - **价值**：所有助手工作台的主壳，样本与 Guard 都围绕它展开，是 ai_assistant 场景的关键真值资产。  

- **presentation**：
  - `presentation-product.html` / `presentation-business.html` / `presentation-planning.html`  
    - **风险**：仍为 candidate，且 `risk_notes_zh` 提示需清理 placeholder / inline style；
    - **价值**：未来很可能成为 deck 方向的 canonical 模板族，值得专门做规范审查与清理。

### 4.2 最值得后续做定位澄清的“悬空/边缘”资产

- **`ue5_overlay_engine_test.html`（engine test / 可视化联调专用）**  
  - 现状：已从“身份不清”的悬空状态归档为 **C 局部参考资产（special-purpose local reference）**；仍不进入 `template_router` / `task_router` / `scene_coverage` 主链。  
  - 价值：
    - 适合作为 UE5 overlay 场景下的局部可视化图表、渲染联调、engine bridge 演示与工程示例参考；
    - 不属于 demo/anti_pattern/forbidden，也不是纯无效页面。  
  - 限制：
    - 不得作为通用 overlay page shell，不得进入默认模板推荐；
    - AI 若误把它当作业务页主壳，会绕开 overlay shell/Mode 等约束，因此只能作为人工确认后的局部参考。  

- **`b-system-production-plan.html` / `b-system-saas.html`**  
  - 虽已为 candidate，但在“规划 workspace vs 通用后台壳”之间的角色仍略显模糊；
  - 后续需要通过 observation 样本与规范审查，澄清它们是：
    - 真正的 workspace canonical 候选，还是仅用于局部结构参考（C 层资产）。

- **presentation strong candidates**  
  - product/business/planning 三个 deck 模板的最终定位（canonical vs 长期 candidate）需要更多业务项目样本支撑，属于“高潜力但暂不轻易升级”的资产。

### 4.3 当前不值得花精力处理的资产（明确反例 / 低优先级草稿）

- **反例资产（已被 Guard/真值源明确标记）**：
  - `b-system-showcase.html`、`b-system-sidebar.html`、`website-showcase.html`；
  - `ue5_overlay_mock_bridge.html`；
  - `presentation-work-report.html`、`presentation-minimal.html`。  
  - 这些模板的角色已经非常清晰：**仅作为 demo/anti_pattern 反例，AI 不得使用**，不需要在短期内做额外治理，只需保证 Guard 和 router 不放松约束。

- **engine test / component gallery 等专用页面**：
  - 除了在文档中标明“Testing-only / Gallery-only”，当前不需要对其做更深的结构治理或规范优化。

---

## 5. 面向 AI/skill 的使用建议（模板参考优先级）

> 以下规则是给 AI/skill 的 **默认参考顺序**，在没有显式 override 的情况下应遵守。

- **（1）默认只在 A 层资产中选择主壳**  
  - 生成新页面时，AI 应优先根据 `scene` + `page_type` + `task_router` 从 **A 主参考资产** 中选择主模板：
    - `b-system-complete / b-system-charts / b-system-task-list-top-filters / b-system-advanced-list-with-left-filter-panel / b-system-detail-order`；
    - `website-complete / website-feature-solution`；
    - `ue5_overlay_data_viz / ue5_overlay_quality_tracking / ue5_overlay_dashboard`；
  - 除非明确需要特殊场景（planning / workspace / cockpit 等），否则不应跨入 B/C 层模板作为主壳。

- **（2）在明确场景与前置条件满足时，可以下探到 B 层资产作为主壳**  
  - 当 `task_router` 或 PRD 明确指向 planning / workspace / assistant_workspace / presentation deck 等场景，并且满足相应前置条件时：
    - 可选用 `b-system-production-plan` / `b-system-saas` / `b-system-ai-assistant`；
    - 可选用 `website-feature-solution`（既是 A 也可视为强 B）、presentation 的 product/business/planning deck；
    - 可选用 `ue5_overlay_minimal_no_hud`（在 PRD 明确 minimal 的情况下）。  
  - 使用 B 层资产前，应总是检查其 `risk_notes_zh` 与本映射表中的 **规范风险**，必要时在摘要中说明原因。

- **（3）仅在极少数、经过人工确认的高级场景中才可参考 C 层资产**  
  - C 层资产（例如 `ue5_overlay_sidepanel_dock_layout`、`digital_twin_overlay_dashboard`）应主要用于：
    - layout / module 壳的局部参考；
    - 作为 Phase 2 治理的讨论基础；
  - AI 默认不得在常规任务中选用 C 层模板作为 primary template，除非：
    - PRD 明确为“数字孪生驾驶舱 / Mode 5 full layout”等；
    - 并在 PRE-GEN / 摘要中记录“已人工确认使用 limited cockpit 模板”的证据。

- **（4）D 层反例资产只用于“不要怎么做”的 Guard 参考，严禁作为生成目标**  
  - 对任何 `grade ∈ {demo, anti_pattern}` 或 `use_scope = forbidden` 的模板：  
    - AI 可以在说明/对比中引用其结构作为反例；
    - 但 PRE-GEN 的 `template` 字段、`task_router` 的 primary/fallback、Level 判定等位置都 **不得指向 D 层资产**。

- **（5）E 层悬空资产在当前阶段视为“禁止自动选用”，仅供人工测试或参考**  
  - 对仍未完成正式归档的 engine test / gallery-only 等 E 层资产，AI 在自动决策时应一律视为不可选模板；
  - 如确需在验证项目中使用，应由人类显式指定路径并承担评估责任，AI 不做主动推荐。

> **一句话使用规则**：
> 
> **AI 在默认情况下必须先从 A 层主参考资产中按 `scene + page_type + task_router` 选模板，仅在 PRD 明确且满足前置条件时才可下探到 B 层或局部借用 C 层布局；像 `ue5_overlay_engine_test.html` 这类 special-purpose 的 C 层资产只能作为局部工程参考，不得进入主模板主链或默认推荐，任何命中 D 层反例或仍处于 E 层悬空状态的选择都应被视为误用并立即回退。**
