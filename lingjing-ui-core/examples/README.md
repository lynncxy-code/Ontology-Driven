# examples/ 目录说明

本目录按**场景 + 工具目录**组织：核心场景包括 `b_system` / `ue5_overlay` / `website` / `presentation`，并包含 `shared`、`design-system` 等通用目录；每个场景文件夹内根据真值源混放 canonical / candidate / demo / limited / blacklist / anti_pattern 模板，具体分级以 `scene_coverage_matrix.yml` 与 `skill_version.json` 为准。

**AI 生成页面时，默认只允许以“可作为默认路由目标的 canonical 模板”作为结构参考。**

- **true-canonical（默认路由模板）**：在 `scene_coverage_matrix.yml` 与 `skill_version.json` 中标记为 canonical，且允许作为 task_router 的 primary/fallback 模板；适合作为 AI 在对应场景下的默认结构参考与落点。
- **limited / test 模板**：仅在登记场景/任务下使用（例如 `ai_assistant` 工作台、UE5 引擎性能测试）；不得当作通用主链模板或默认结构参考。
- **demo / blacklist / anti_pattern**：只能用于人工查阅或反例说明，**禁止作为业务模板或自动路由目标**。

> 具体分级与是否允许默认路由，以 `scene_coverage_matrix.yml` 与 `skill_version.json` 为准；本 README 仅作导航与索引，不单独作为真值源。

## 目录结构

```
examples/
├── b-system/              # B 端管理系统 / 作业后台
│   ├── b-system-complete.html                         ★ canonical — B 端完整参考页
│   ├── b-system-charts.html                           ★ canonical — B 端图表（折/柱/环/表）
│   ├── b-system-task-list-top-filters.html            candidate — 列表页（顶部筛选条 + 数据表格）
│   ├── b-system-advanced-list-with-left-filter-panel.html  candidate — 高级筛选列表（左侧面板 + 右侧表格）
│   ├── b-system-detail-order.html                     candidate — 工单详情（基本信息 + 时间线 + 关联记录）
│   ├── b-system-production-plan.html                  candidate — 计划管理 / 生产排程
│   ├── b-system-saas.html                             candidate — SaaS 后台 / 通用作业系统
│   ├── b-system-showcase.html                         demo — 组件展示工具
│   ├── b-system-sidebar.html                          demo — 侧边栏组件展示
│   └── aircraft-manufacturing-*.html                  draft / 待观察 — 行业草稿，不进入当前主链
│
├── ue5-overlay/           # UE5 Web Overlay / 数字孪生叠加层
│   ├── ue5_overlay_quality_tracking.html  ★ canonical — 质量追踪看板（Mode 2）
│   ├── ue5_overlay_data_viz.html          ★ canonical — 数据可视化监控大屏（Mode 1 单 HUD）
│   ├── ue5_overlay_engine_test.html       limited/test — 发动机台架测试监控（仅限 UE5 引擎/桥接测试）
│   ├── ue5_overlay_mock_bridge.html       demo — 占位页，仅供桥接/结构草图参考；禁止作为业务模板
│   └── ue5_overlay_dashboard.html         ★ canonical — HUD + 告警中心总览（Mode 3）
│
├── website/               # 营销 / 企业门户网站
│   ├── website-showcase.html             demo — 组件展示工具
│   ├── website-feature-solution.html     candidate — 功能 / 方案介绍页起步模板
│   └── website-complete.html             ★ canonical — 官网首页 / 营销落地页起步模板
│
├── presentation/          # 专业演示 / 汇报幻灯片
│   └── presentation-*.html               draft — 待审计通过（共 5 个）
│
├── design-system/         # 设计系统展示页（非业务模板）
│   └── design-system-overview.html       reference/demo — 设计系统概览，不进入任务主链
│
├── shared/                # 跨场景通用工具
│   └── core-icon-library.html            demo/tool — 图标库查阅工具
│
└── styles/                # 保留目录（当前无额外样式文件）
                        # 注：业务/draft/canonical 模板的项目级 CSS 应与 HTML 同目录
                        #     (如 b-system/pj-b-system-ai.css)，禁止放在本目录
```

## 分级规则

| 分级 | 典型来源 | 审计/使用状态 | AI 使用规则 |
|------|----------|---------------|-------------|
| canonical | `skill_version.json.examples.canonical` / matrix 中 `grade: canonical` | 通过审计的主力模板 | ✅ 可作为结构参考与业务交付落点，调用前应读取对应文件与审计报告取证 |
| candidate | `skill_version.json.examples.candidate` / matrix 中 `grade: candidate` | 候选模板，可能带 TODO 或风险备注 | ⚠️ 可作为结构参考；业务落地前应先改造并通过 `skill-audit.js`，再晋级为 canonical |
| demo | `skill_version.json.examples.demo` | 组件/样式展厅，仅用于人工查阅 | 🔧 仅限内部展示与开发预览；**禁止作为业务交付模板或自动路由目标** |
| limited | `skill_version.json.examples.limited` | 场景限定模板（如 `ai_assistant`、数字孪生 cockpit） | ⚠️ 仅在登记场景/任务下使用；禁止泛化为通用模板 |
| blacklist | `skill_version.json.examples.blacklist` | 黑名单模板，审计脚本一旦命中即 ERROR | ⛔ 禁止作为结构参考或业务交付目标；仅可在文档中当作反例说明 |
| anti_pattern | `scene_coverage_matrix.yml` / `data/template_router.json` 中 `grade: anti_pattern` | 反例模板，通常同时归入 blacklist | ⛔ 仅用于说明“不要这么做”，不得作为生成或修复的目标模板 |

### 类名治理模型（class 级别）

模板中使用的 CSS 类名由 `data/class_registry.json` 管理：

| 状态 | 审计结果 | 说明 |
|:---|:---|:---|
| `unknown`（不在 registry） | **ERROR** — 阻断交付 | 必须修复：改用 canonical/utility 类，或按 `pj-*` 规范声明项目级类 |
| `canonical` / `utility` | PASS | 可直接出现在业务交付页面 |
| `alias` | **WARN** — 需归一化 | 生成前或交付前必须替换为其 `canonical` 字段指向的类名 |
| `demo_only` | **ERROR**（在业务页面中） | 仅允许出现在 demo 示例；业务交付页出现时视为违规 |
| `deprecated` | **WARN** — 建议迁移 | 仍可被识别，但应优先改用 `use_instead` 中推荐的替代类 |

> 更完整的类名治理规则见 `TRUTH_SOURCES.md §2.2` 与 `SKILL.md` 中的类名规范章节。

### 项目级 CSS 规范

- **co-located 原则**：模板需要项目级 CSS 时，必须与 HTML 放在同一目录，不得放入 `examples/styles/`
- **命名**：`pj-{scene}-{purpose}.css`，如 `pj-b-system-ai.css`、`pj-ue5-sidepanel-dock.css`
- **内容**：B 类（页面独有布局）用 `pj-*` 类名；A 类（candidate 组件样式）用裸类名（registry 已登记）

## 边缘资产与生成产物归属

- `b-system/aircraft-manufacturing-*.html`
  - **归属**：`draft / 待观察资产`
  - **说明**：保留追溯价值，但当前不视为主链模板，不进入默认路由判断。
- `design-system/design-system-overview.html`
  - **归属**：`reference / demo`
  - **说明**：用于设计系统展示，不作为业务页面模板。
- `shared/core-icon-library.html`、各场景 `*showcase*.html`
  - **归属**：`demo / tool`
  - **说明**：仅供人工查阅与本地预览，禁止作为业务交付模板。
- `examples/**/audit-report.json`
  - **归属**：`generated output`
  - **说明**：已归档到 `docs/validation/generated-reports/`；未来运行 `skill-audit.js` 产生的同名文件默认不作为正式仓库资产。

## ★ 默认路由 canonical / 受限模板索引

| 文件 | 场景 | 分级 / 使用范围 | 说明 |
|------|------|-----------------|------|
| `b-system/b-system-complete.html` | `b_system` | `canonical / default` | B 端管理系统完整参考（布局、导航、表单、表格） |
| `b-system/b-system-charts.html` | `b_system` | `canonical / default` | B 端图表标准示例（折线 + 柱状 + 环形 + 数据表） |
| `b-system/b-system-task-list-top-filters.html` | `b_system` | `candidate / default` | 列表页：顶部筛选条 + 数据表格（工单 / 台账 / 记录列表） |
| `b-system/b-system-advanced-list-with-left-filter-panel.html` | `b_system` | `candidate / default` | 高级筛选列表：左侧筛选面板 + 右侧表格（仅 PRD 明确要求常驻侧栏时） |
| `b-system/b-system-detail-order.html` | `b_system` | `candidate / default` | 工单详情：基本信息 + 状态时间线 + 关联记录 |
| `b-system/b-system-production-plan.html` | `b_system` | `candidate / default` | 计划管理 / 生产排程（晋级前需通过审计） |
| `b-system/b-system-saas.html` | `b_system` | `candidate / default` | SaaS 后台 / 通用作业系统（不作为所有 b_system 默认模板） |
| `b-system/b-system-ai-assistant.html` | `ai_assistant` | `limited / registered-scene` | B 端 AI 工作台（仅限 `ai_assistant` 场景；含 `pj-b-ai-*` 项目级扩展，不作为普通 `b_system` 默认模板） |
| `ue5-overlay/ue5_overlay_quality_tracking.html` | `ue5_overlay` | `canonical / default` | UE5 质量追踪看板（Mode 2：HUD + 右侧详情面板） |
| `ue5-overlay/ue5_overlay_data_viz.html` | `ue5_overlay` | `canonical / default` | UE5 数据可视化监控大屏（Mode 1：单 HUD，无侧面板） |
| `ue5-overlay/ue5_overlay_dashboard.html` | `ue5_overlay` | `canonical / default` | UE5 HUD + 告警中心总览（Mode 3） |
| `ue5-overlay/ue5_overlay_engine_test.html` | `ue5_overlay` | `limited / test-only` | UE5 台架测试监控（仅限 UE5 引擎桥接 / 性能 / world-marker 测试，不进入任务主链，也不作为普通默认模板） |
| `website/website-complete.html` | `website` | `canonical / default` | 官网首页 / 营销落地页起步模板（已通过审计，可作为网站场景 canonical） |

> 上表中仅 `canonical / default` 行可被理解为“默认路由可落点模板”；`limited` 行必须在真值源明确登记的场景 / 任务下才可使用。
>
> **演示场景**尚无 canonical 文件；AI 在 presentation 场景使用 Level 2/3 自行构建，
> 通过 `node scripts/skill-audit.js` 审计后可提交为该场景首个 canonical。

## 新增 canonical 文件的流程

1. 生成 HTML，运行 `node scripts/skill-audit.js <file> --scene <scene>` 审计
2. 确认 `delivery_gate: PASS`（无 ERROR 项）
3. 将文件移入对应场景文件夹（如 `examples/b-system/`），确认 CSS/script 路径为 `../../`
4. 在本 README 索引表和 `skill_version.json` 中登记
