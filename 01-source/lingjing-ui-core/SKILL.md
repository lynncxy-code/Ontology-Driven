---
name: lingjing-ui-core
description: Official design system for Lingjing Aviation AI Agent. Enforces "Intelligent Aviation" visual style, prioritizing clean, smart, and ethereal aesthetics over heavy industrial effects.
license: MIT
compatibility: [Claude, GPT-4, Trae, Cursor, Windsurf]
metadata:
  version: 3.0.1
  updated: 2026-04-09
---

# LingJing Core - 面向航空 AI 场景的 UI Skill

> **技能定位**：将灵境设计规范内化为 AI 可理解、可执行的布局与组件调用逻辑。
> **核心逻辑**：场景识别 → Level 判定 → 模板/骨架选择 → 组件编排 → 质量校验。
> **主文档职责**：本文件只承担**全局规则入口 + 分流导航**；重场景布局细则、模板映射与食谱请按任务继续深读对应子文档。
> **当前版本**：v3.0.1（版本唯一真相源：本文件 frontmatter `metadata.version` 字段）
> **当前 Phase 1 优先场景**：`b_system` 与 `ue5_overlay`；`website` / `presentation` / `ai_assistant` 在本版中保持兼容可用，但不作为中间层建设主线。

---

## 使用技能包必读（5 条铁律）

> 拿到“遵循灵境 UI 规范”之类指令后，在写任何 HTML / JSX 前，必须先完成以下 5 步。

| # | 铁律 | 违反后果 |
|---|---|---|
| 1 | **先读真值源**：至少读取 `SKILL.md`、`scene_coverage_matrix.yml`、目标项目结构文件（如 `package.json` / `index.html`） | 场景、Level、落点判断漂移 |
| 2 | **先选模板/骨架再写页面**：B 端先看 `examples/b-system/b-system-complete.html`；UE5 必须先读 `docs/operations/ue5-overlay-layout-playbook.md` 末尾决策树，再选模式模板 | 框架骨架错误、页面同质化 |
| 3 | **框架层先行**：B 端先搭 `b-layout-sidebar > b-sidebar + b-main > b-header + b-content`；UE5 先搭 `ue5-overlay-root > ue5-overlay-viewport > ue5-overlay-safe-area` | `frame_shell_missing: ERROR` |
| 4 | **类名必须过注册表**：每个类名必须在 `data/class_registry.json` 中存在并可合法使用；禁止自造类名 | `unknown_classes: ERROR` |
| 5 | **交付前必须跑审计**：运行 `node scripts/skill-audit.js <html文件> --scene <b_system|ue5_overlay|website|presentation>`，FAIL 禁止交付 | 规范违规交付 |

**各场景 canonical 参考文件**：

| 场景 | 首选参考 | 说明 |
|---|---|---|
| `b_system` | `examples/b-system/b-system-complete.html` | B 端框架层主锚点 |
| `ue5_overlay` | 先读 `docs/operations/ue5-overlay-layout-playbook.md` | 先判 `layout_mode`，再选模式模板 |
| `website` | `examples/website/website-complete.html` | 官网首页 / 落地页起步模板 |
| `presentation` | `examples/presentation/presentation-product.html` | 演示汇报起步模板 |

**UE5 布局模式速记**（仅保留入口，不在主文档展开细则）：

| 模式 | 参考文件 | 何时必须继续深读 |
|---|---|---|
| Mode 1 | `examples/ue5-overlay/ue5_overlay_data_viz.html` | 监控大屏 / 单 HUD |
| Mode 2 | `examples/ue5-overlay/ue5_overlay_quality_tracking.html` | HUD + 侧边详情 |
| Mode 3 | `examples/ue5-overlay/ue5_overlay_dashboard.html` | HUD + 告警中心 |
| Mode 4 | `docs/operations/ue5-overlay-layout-playbook.md` 中骨架代码 | P1 告警叠加 |
| Mode 5 | `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html` | 双侧面板 + Dock |

---

## 0.0 核心执行规约 (Core Execution Protocol - 必须遵循)

### 0.0.1 强制任务清单 (Atomic Task Template)

> 在输出任何 HTML 前，必须先给出 PRE-GEN 声明；无法声明时，禁止写页面。

```text
[PRE-GEN]
scene       = <b_system|ue5_overlay|website|presentation>
layout_mode = <ue5_overlay 必填 1|2|3|4|5；其他场景填 n/a>
frame_shell = <必须保留的骨架类组合>
template    = <参考模板路径；若无直达模板写 none>
class_check = <已在 data/class_registry.json 确认所有待输出类名>
```

AI **必须**按以下顺序执行，严禁跳步：

1. **[分析] 对齐项目结构与业务需求**：读取调用方项目结构（如 `package.json` / `index.html` / 页面目录）与 PRD / `ux_spec`，先判断产物落点。
2. **[取证] 最小读探测**：读取 `scene_coverage_matrix.yml` 中对应场景的 `shell_consistency`、`machine_rules`、`audit_contract`，再读取 `1` 个最匹配的 canonical 模板。
   - `ue5_overlay` 必须先读 `docs/operations/ue5-overlay-layout-playbook.md` 决策树，确定 `layout_mode` 后再选模板；禁止直接默认读 `quality_tracking.html`。
   - `b_system` 至少读取 `examples/b-system/b-system-complete.html`；列表/详情/配置等页型再按需深读 playbook / map / recipes。
3. **[框架] 先搭框架层**：优先输出 `shell_consistency` 规定的外层骨架与容器，不得直接散装输出业务卡片。
4. **[资源] 接入官方资源**：复制单文件场景入口 CSS 与必要脚本到项目内；禁止自行生成一套“相似 CSS”替代官方资源。
5. **[生成] 按 Level 落地页面**：先判断 Level 1 / 2 / 3；若 PRD 模块无法被模板合理承载，必须升级到更高 Level，而不是为了“像模板”删需求。
6. **[校验] 完工自检**：执行 `5.0` 质量清单，并运行 `skill-audit.js`；FAIL 必须修复，WARN 需在摘要说明。

### 0.0.2 行为黑名单 (Negative Constraints)

- **严禁路径漂移**：默认禁止新建并行“验证子项目”；优先落在调用方现有项目结构内。
- **严禁口头复现**：未落盘文件前，禁止声称“已按规范完成”。
- **严禁样式污染**：禁止在 HTML 中用 `<style>` 定义布局/组件/场景样式；`style="..."` 中禁止硬编码颜色、间距、字号等值。如确需内联样式，必须全部用 CSS Token：
  ```html
  <!-- ❌ 硬编码 → 触发 inline_style_leak: WARN/ERROR -->
  <div style="padding: 16px; color: #0F172A; background: rgba(28,102,196,0.08);">

  <!-- ✅ Token 替换 → 合规 -->
  <div style="padding: var(--spacing-md); color: var(--theme-text-primary); background: var(--bg-card);">
  ```
  **常用 inline Token 速查**（完整表见 `docs/reference/css-token-reference.md`）：

  | 硬编码值（常见） | Token 替换 |
  |---|---|
  | `padding: 4px` / `8px` / `16px` / `24px` / `32px` | `var(--spacing-xs/sm/md/lg/xl)` |
  | `border-radius: 6px` / `8px` / `12px` | `var(--radius-sm/md/lg)` |
  | `color: #0F172A`（深色正文） | `var(--theme-text-primary)` |
  | `color: #64748B`（次级说明） | `var(--theme-text-secondary)` |
  | `background: #fff` / 深色卡片背景 | `var(--bg-card)` |
  | `background: rgba(28,102,196,0.08)` | `var(--bg-glass)` |
  | `border: 1px solid rgba(28,102,196,0.15)` | `var(--glass-border)` |
  | `color: #22C55E`（成功绿） | `var(--success-base)` |
  | `color: #F59E0B`（警告黄） | `var(--warning-base)` |
  | `color: #EF4444`（错误红） | `var(--error-base)` |
- **严禁命名自定义**：禁止输出 `.my-sidebar`、`.dashboard-container`、`.metric-card`、`.global-filter-bar` 等自造近似类；必须命中 `data/class_registry.json`。
- **严禁图表空转**：PRD 要求图表时，禁止只输出 `chart-placeholder` 占位；必须给出真实 ECharts DOM + 初始化逻辑。
- **严禁图表默认色盘漂移**：禁止裸 `echarts.init()` 与库默认配色；必须通过 `LingJingChart.init()` 并绑定灵境 Token 色板。违反此项触发 `bare_echarts_init: ERROR`。
  ```js
  // ❌ 触发 bare_echarts_init: ERROR
  const chart = echarts.init(document.getElementById('myChart'));

  // ✅ 正确写法
  const chart = LingJingChart.init(document.getElementById('myChart'), 'b_system');
  ```
- **严禁 Demo 修饰类泄漏**：业务页禁止直接使用 `*-demo-*` 或 `type=demo_only` 类。
- **严禁无 PRD 套词**：禁止不读需求就机械替换模板文案。
- **严禁表格溢出**：超宽表格必须放在 `data-table-container` 中，并具备横向滚动保护。
- **严禁命令滥用**：优先用读写文件工具；需要命令时保持单条命令，不拼接高风险操作。

### 0.0.3 类名真值校验与缺失组件处理 (Mandatory Fallback Protocol)

- **语义字段与类名字段分离**：`scene_coverage_matrix.yml.layout_shells` 中 `semantic_id` 只用于语义识别，`class_name` 才是可落地类名。
- **生成前真值校验**：输出前必须在 `data/class_registry.json` 或 `docs/reference/CLASS_NAME_REFERENCE.md` 中确认类名存在；仅 `canonical` 与 `utility` 可直接用于业务页。
- **alias 归一化**：若命中 `type=alias`，必须先转换为其 `canonical` 值后再写入 HTML。
- **生成后反向扫描**：交付前必须反扫 HTML 类名集合；存在 `alias`、`demo_only`、未知类时必须替换或删除。
- **缺失组件处理顺序**：
  1. 优先命中 `ux_spec.component_roles[*].lingjing_core_class`；
  2. 再用最接近的官方组件组合完成承载；
  3. 仍不足时进入 `3.0` 的 Level 3，并在摘要中明确说明“存在技能包未覆盖组件，需要业务项目扩展”。

### 0.0.4 框架层强一致性 (Frame-layer Consistency)

- **机器真值源**：框架层骨架与 DOM 约束，以 `scene_coverage_matrix.yml.shell_consistency` 为唯一机器真值源。
- **B 端强一致**：必须复用 `.b-layout-sidebar`、`.b-sidebar`、`.b-main`、`.b-header` 等官方框架类，不得重做一套侧边栏 / 顶栏。
- **网站强一致**：必须复用 `.website-nav` 体系作为顶部栏骨架，不得另起一套导航壳。
- **UE5 强一致**：必须复用 `.ue5-overlay-root`、`.ue5-overlay-viewport`、`.ue5-overlay-safe-area` 与 HUD / 面板体系；允许变化的是内容，不是骨架。

### 0.0.5 验证 / 验收模式 (Audit Mode)

当需求包含“验证 / 验收 / 复现 / 对标 / 跑通 / 检查技能包”时，必须：

- 若当前会话已有 `ux_spec`：以其 `pages / zones / component_roles` 为准进行 UI 落地。
- 若当前会话无 `ux_spec`：可直接按业务 PRD 映射，但摘要中需说明“本次未经 UX 技能包输出”。
- 必须展示“文件取证 + 资源落地 + 类名命中 + 审计结果”的证据链。
- 必须明确给出 audit 证据：`audit_command`、`audit-report.json` 路径、`delivery_gate`、`audit_exit_code`；缺一项都不能声称“已按技能包通过验收”。
- 必须输出 `scene_coverage_matrix.yml.decision_matrix.audit_contract.required_summary_fields` 要求的结构化摘要字段。
- 必须补充运行态字段：`runtime_icon_ready`、`runtime_chart_ready`、`runtime_table_scroll_ready`、`runtime_overlay_chain_ready`（不适用项标注 `N/A`）。


### 0.0.6 资源闭环与交付完整性硬约束 (Resource & Delivery Protocol)

**官方资产与依赖**：

- B 端 / Website Logo：`assets/logo-flat.png`
- UE5 HUD Logo：`.ue5-overlay-system-bar__brand-mark`（CSS 背景图形态，不额外叠加 `<img>`）
- UE5 默认背景图：`assets/ue5-bg-scene.png`
- 图标库：`scripts/lucide-umd-500.js`
- 图表库：`scripts/echarts.min.js` + `scripts/echarts-theme-lingjing.js`
- UE5 桥接：`components/dist/lingjing-core-ue5-bridge.js`（如环境支持）

**资源访问与复制原则**：

- 需要官方示例 / dist 资源时，优先从技能安装目录读取真实文件，而不是凭记忆重写。
- 大文件复制必须优先使用单条复制命令，不用 `read_file + write_to_file` 分段拼接重建。
- 若技能目录不可访问，必须在摘要中明确说明，不得声称“与技能包完全一致”。

**`resource_closure_ok` 判定**：以下三项全部满足才可标记为 `true`：

| 步骤 | 检查项 |
|---|---|
| Step 1 | 资源目标目录已就位 |
| Step 2 | 资源文件已成功复制到项目内 |
| Step 3 | HTML / CSS / JS 中引用路径与真实文件一致且可达 |

若任一步失败：`resource_closure_ok = false`，只能说明“资源闭环未完成，当前交付为结构草案或局部实现”。

**`delivery_scope` 判定**：

- `full`：`delivered_page_count >= planned_page_count` 且 `resource_closure_ok = true`
- `partial`：页面数未覆盖全部，但已覆盖核心高优页
- `prototype`：未覆盖核心页，或 `resource_closure_ok = false`

禁止在 `partial` / `prototype` 状态下声称“完整交付已完成”。

---

## 0.1 按任务阅读顺序（Progressive Loading）

> 目标：不是每次都全量读全仓，而是**先读主规则，再按场景深读**。

### 0.1.1 所有任务先读什么

1. `SKILL.md`：重点读 `0.0`、`1.1`、`3.0`、`5.0`
2. `scene_coverage_matrix.yml`：确认 `scene_id`、`shell_consistency`、`decision_matrix`
3. 调用方项目结构文件：如 `package.json`、`index.html`、路由 / 页面目录
4. 最接近的 canonical 模板：只读与当前任务强相关的那一张

### 0.1.2 `b_system` 任务如何继续深读

**默认顺序**：

`SKILL.md` → `scene_coverage_matrix.yml` → `docs/operations/b-system-layout-playbook.md` → `docs/reference/system-template-map.md`

**以下情况再继续读**：

- 涉及侧边栏折叠 / 主题切换 / 图表初始化 / 表格壳体时：`docs/reference/b-system-composition-recipes.md`
- 涉及类名或组合食谱查表时：`docs/reference/CLASS_NAME_REFERENCE.md`
- 涉及历史验证 / 回归时：`docs/validation/`

### 0.1.3 `ue5_overlay` 任务如何继续深读

**默认顺序**：

`SKILL.md` → `scene_coverage_matrix.yml` → `docs/operations/ue5-overlay-layout-playbook.md`（先走决策树）→ `docs/reference/ue5-template-map.md`

**以下情况再继续读**：

- 需要 Mode 1/2/3/5 的模板细节时：读取对应 `examples/ue5-overlay/*.html`
- 需要核对受限模板 / 反例 / observation 结果时：`docs/validation/`
- 需要类名 / Token / 资源路径查表时：`docs/reference/CLASS_NAME_REFERENCE.md`、`docs/reference/css-token-reference.md`

### 0.1.4 `website` / `presentation` / `ai_assistant` 任务如何轻读

这三类任务默认**不需要**先读全部 playbook。

**默认顺序**：

`SKILL.md` → `scene_coverage_matrix.yml` → `data/task_router.json` / `data/template_router.json` → 对应 `examples/` 模板

**以下情况再继续深读**：

- 需求包含“验证 / 对标 / 回归 / 复现”：再读 `docs/validation/` 中对应文档
- 需求触发场景混合、模板边界不清：再读 `docs/operations/EXTENSION_GUARD.md`
- 需求涉及资源归位 / 模板资产归属：再读 `docs/reference/TEMPLATE_ASSET_REFERENCE_MAP.md`

### 0.1.5 什么时候必须继续读 playbook / map / validation

- **必须读 playbook**：
  - `ue5_overlay`：总是先读 playbook 决策树
  - `b_system`：当页面类型不是“直接轻调 canonical 首页”时，应读 playbook
- **必须读 template map**：当需要判断 page_type / mode / fallback template / preferred level 时
- **必须读 validation**：当任务目标是验证、复现、验收、回归，或你需要确认某条规则是否已有实证留档时
- **不必默认读 validation**：普通页面生成任务无需先把所有验证文档读一遍

---

## 0.2 默认执行流程 (自然语言输入)

1. **识别场景与任务类型**：先判断是 `b_system`、`ue5_overlay`、`website`、`presentation` 还是 `ai_assistant`。
2. **执行 `0.0` 核心规约**：按原子步骤分析、取证、资源落地、生成与校验。
3. **协同 UX 链路**：若上下文中存在 `ux_spec`，优先以其 `pages / zones / component_roles` 为准。
4. **输出结构化摘要**：至少包含 `scene_id`、`chosen_level`、`template_match_score`、`missing_key_modules_count`、`retained_frame_shell` 与资源闭环状态。

### 0.2.a UX → UI 协同流程（推荐）

1. 先由 `lingjing-ux-core` 产出结构化 `ux_spec`
2. 再由 UI 技能包读取 `route_path`、`lingjing_core_class`、`dev_handoff` 等字段完成落地

### 0.3 输出形态与技术栈对齐

AI 必须按以下优先级判断落点：**用户指定路径 > 现有页面目录 > 现有路由/布局目录 > 最小回退结构**。

| 识别信号 | 推荐输出形态 | 推荐落点 |
|---|---|---|
| `vue` 依赖、`App.vue`、`src/router` | `vue-sfc` | `src/views/`、`src/pages/` |
| `react` 依赖、`src/App.tsx`、`src/pages` | `react-jsx/tsx` | `src/pages/`、`src/components/` |
| `index.html`、`public/` | 多页面 `html` | `pages/`、`assets/` |
| 无明显前端结构 | 最小静态 Web 结构 | 根目录创建 `index.html` |

---

## 1.0 场景识别与深读入口

AI 在收到需求后，先判断所属场景，再选择更贴近该场景的样式入口与骨架。

| 场景识别 | 推荐样式入口 | 优先骨架 / 组件 | 说明 |
|---|---|---|---|
| `b_system` | `lingjing-core-b-system.css` | `.b-layout-sidebar`、`.b-sidebar`、`.b-main`、`.b-header`、`.content-card`、`.data-table-container` | 高信息密度、结构化、高效办公 |
| `ue5_overlay` | `lingjing-core-ue5-overlay.css` | `.ue5-overlay-root`、`.ue5-overlay-viewport`、`.ue5-overlay-safe-area`、`.topbar-hud`、`.detail-panel`、`.alert-center` | 视口叠加、HUD、低干扰玻璃感 |
| `ai_assistant` | `lingjing-core-b-system.css` | `.chat-layout`、`.message-bubble`、`.tool-call-card`、`.task-status-card` | 工作台 / 对话面板 |
| `website` | `lingjing-core-website.css` | `.website-nav`、`.website-hero`、`.feature-card`、`.website-cta-card` | 营销 / 门户 |
| `presentation` | `lingjing-core-presentation.css` | `.presentation-slide`、`.slide-title` | 演示 / 汇报 |

### 1.1 场景最小命中矩阵（用于快速验收）

| 场景 | 最小命中（布局 / 组件） |
|---|---|
| `b_system` | `.b-layout-sidebar` + `.b-sidebar` + `.b-main` + `.b-header` + `.content-card` |
| `ue5_overlay` | `.ue5-overlay-root` + `.ue5-overlay-viewport` + `.ue5-overlay-safe-area` + `.topbar-hud` |
| `ai_assistant` | `.chat-layout` + `.message-bubble` + `.tool-call-card` |
| `website` | `.website-nav` + `.website-hero` + `.website-cta-card` |
| `presentation` | `.presentation-slide` + `.slide-title` |

### 1.2 `ue5_overlay` 深读入口（入口 + 跳转）

> 主文档只保留 UE5 的关键原则；布局模式、禁止做法与骨架细节交给 playbook / template map。

- **触发条件**：当需求或 `ux_spec` 指向“UE5 Web Overlay / 数字孪生叠加层 / web_overlay_runtime / world_space_ui”时，进入本场景。
- **样式入口强制**：必须接入 `lingjing-core-ue5-overlay.css`；未接入前禁止声称“已按 UE 场景规范落地”。
- **结构骨架强制**：页面必须以 `.ue5-overlay-root` 为顶层，内部复用 `.ue5-overlay-background`、`.ue5-overlay-viewport`、`.ue5-overlay-safe-area` 等现有骨架类。
- **HUD / 面板约束**：必须复用 `.topbar-hud`、`.alert-center`、`.detail-panel`、`.layer-switcher` 等已有体系，不得自建一套 `.lj-overlay-*` 平替。
- **品牌与背景**：
  - 顶栏品牌使用 `.ue5-overlay-system-bar__brand-mark`，这是 UE5 的品牌形态；禁止额外叠加 `logo-flat.png`。
  - 默认背景图使用 `assets/ue5-bg-scene.png`；可被项目真实 UE 画面替换，但路径必须可达。
- **world-marker 例外**：`.world-marker` 的 `top` / `left` 允许以内联 `style` 表达三维坐标；这是受控例外，不视为样式污染。
- **图表接入**：需要图表时，必须用 `LingJingChart.init()` + 本地 `echarts.min.js` / `echarts-theme-lingjing.js`；完整规则与模式差异见 playbook 与示例模板。
- **继续深读路径**：
  1. `docs/operations/ue5-overlay-layout-playbook.md`
  2. `docs/reference/ue5-template-map.md`
  3. 对应模式 `examples/ue5-overlay/*.html`

### 1.3 `b_system` 深读入口（入口 + 跳转）

> 主文档只保留 B 端的关键原则；主题切换、侧边栏折叠、图表 / 列表 / 详情细则交给 playbook / recipes / template map。

- **骨架强制**：页面应以 `.b-layout-sidebar` 包裹 `.b-sidebar` 与 `.b-main`，并显式保留 `.b-header`。
- **主题切换强制**：B 端页面必须具备主题切换能力；若用户指定“深色主题”，初始 `data-theme` 与回退值都必须是 `dark`。
- **侧边栏折叠强制**：`b-sidebar` 必须带 `id="sidebar"`，`b-sidebar-footer` 内必须有 `b-sidebar-toggle`，并实现展开 / 收起逻辑。
- **列表 / 筛选 / 表格边界**：
  - 顶部筛选行区分两种模式：
    - `search-bar`：1–4 个字段、自动过滤、**无显式"应用/重置"按钮**（字段改变即生效）
    - `filter-bar`：字段数不限，含显式 **"应用筛选"/"重置" 按钮**时使用；结构为 `filter-bar > filter-bar-main + filter-bar-extra`
  - `filter-panel` 仅用于 `advanced-data-table` 的右侧列
  - 数据表格必须写成 `div.data-table-container > table.data-table`
- **图表接入**：B 端图表必须通过 `LingJingChart.init()` 初始化，并根据 `data-theme` 动态选择 `b_system` / `b_system_dark`；禁止裸 `echarts.init()`。
- **品牌约束**：B 端侧边栏 / 网站品牌图统一使用 `assets/logo-flat.png`，不允许用 SVG 或 Lucide 图标占位。
- **继续深读路径**：
  1. `docs/operations/b-system-layout-playbook.md`
  2. `docs/reference/system-template-map.md`
  3. `docs/reference/b-system-composition-recipes.md`

### 1.4 `website` / `presentation` / `ai_assistant` 轻读策略

- **`website`**：默认先读主文档 + `scene_coverage_matrix.yml` + 对应模板；仅当进入验证 / 场景混合 / 资产归位问题时，再读 validation / asset map / guard。
- **`presentation`**：当前更适合作为 Level 2 / 3 的兼容场景处理；先读主文档、matrix 与模板，再按需查看 validation。
- **`ai_assistant`**：当前以兼容支持为主；优先复用 `.chat-layout`、`.message-bubble`、`.tool-call-card`、`.task-status-card`，不要把它扩写成新的主线规则系统。
- **统一原则**：这三类任务默认不需要先把 `b_system` / `ue5_overlay` 的 playbook 全量读完；只有命中场景混合、复杂验证或边界不清时再深读对应文档。

---

## 2.0 核心设计原则

### 2.1 内容驱动布局 (Content-Driven Layout)

- 布局应服务内容，而不是让内容去适应模板。
- 高匹配模板可直用；需求模块明显超出模板时，必须升级到 Level 2 / 3。
- B 端追求高信息密度与清晰操作流；UE5 追求低干扰、层级分离与视野保护。

### 2.2 视觉降噪与一致性

- 主结构避免硬编码样式；颜色、间距、字号优先使用 Token。
- 卡片 / 面板优先复用官方组件外壳，保持边框、阴影、描边、留白节奏一致。
- 项目级差异应主要落在信息架构、模块组合与内容优先级，而不是另起一套框架层视觉语言。

### 2.3 组件扩展梯度与 `pj-*` / candidate 边界

- **一级：内容扩展**：优先在官方组件内部补字段、说明、表单项、图表，不新增类名。
- **二级：修饰符扩展**：确需状态强化时，可在官方类上叠加项目修饰符；样式由调用方项目 CSS 提供。
- **三级：项目组件扩展**：只有当前两级都不足时，才使用 `.pj-{scene}-*` 项目前缀类，并嵌套在官方骨架 / 官方容器内。
- **审计三态**：`unknown → ERROR`，`candidate → WARN`，`canonical → PASS`。
- **`pj-*` 白名单边界**：
  - 允许：在官方容器内部创建项目级新模块
  - 禁止：用 `pj-*` 替换框架骨架（如 `.pj-sidebar`、`.pj-layout-sidebar`）
  - 项目类内部样式值必须全部引用 Token，禁止硬编码

---

## 3.0 场景-模板应用顺序与三级策略

### 3.0.a Level 判定矩阵（执行前必须回答）

- 先读取 `scene_coverage_matrix.yml.decision_matrix.*.machine_rules`，至少回答：
  1. `template_match_score` 是否足够高，且主任务流 / 导航骨架 / 信息架构一致？若是，进入 **Level 1**。
  2. 若不适合 Level 1，现有组件与模块骨架是否仍可覆盖主模块比例？若是，进入 **Level 2**。
  3. 若存在新业务域、关键信息模块明显缺失，或 `missing_key_modules_count` 达到阈值，进入 **Level 3**。
- 摘要必须写明：`scene_id`、`chosen_level`、`template_match_score`、`missing_key_modules_count`、`retained_frame_shell`。
- 对齐技能包 / 对标示例，只代表**框架层必须强一致**，不等于主体内容必须停留在 Level 1。

### 3.0.b 模块骨架层（Module Shell Layer）

- 除整页模板外，还必须把 `scene_coverage_matrix.yml.scene_coverage[*].module_shells[*]` 当作二级骨架资产使用。
- 常见模块骨架包括：
  - `b_system_dashboard_shell`
  - `b_system_list_detail_shell`
  - `website_landing_shell`
  - `ue5_overlay_shell`
  - `ai_workspace_shell`
  - `presentation_story_shell`
- 当整页模板不合适时，应先复用模块骨架，再补组件组合；模块骨架也无法承载时，才进入 Level 3。

### 3.0.c 组件缺口处理协议（Component Gap Protocol）

当没有任何现有组件 / 模板能完整覆盖业务需求时，按以下顺序执行：

#### Step 1 — 锁定框架层（必须保持不变）

- B 端保留 `b-layout-sidebar` / `b-sidebar` / `b-main` / `b-header`
- UE5 保留 `ue5-overlay-root` / `ue5-overlay-viewport` / `ue5-overlay-safe-area`
- Website 保留 `website-nav` 体系

#### Step 2 — 选用安全容器承载新增内容

优先从现有容器中选择最接近的父节点，例如：

- `content-card`
- `detail-panel__body`
- `detail-panel__section`
- `alert-center__list`
- `data-table-container`
- `form-section` / `form-group`
- `website-section`

#### Step 3 — 在容器内优先填入已有原子类

优先复用：

- `badge-*`
- `status-dot-*`
- `data-trend-*`
- `detail-panel__list-row`
- `detail-panel__metric`
- `data-table`
- `advanced-data-table`
- `chart-placeholder`（仅作图表容器，不作交付占位）

#### Step 4 — 自定义 DOM 只允许使用 CSS Token，禁止硬编码任何值

```html
<!-- ✅ 正确：仅使用 Token -->
<div style="background: var(--bg-card); border: var(--glass-border);
            border-radius: var(--radius-md); padding: var(--spacing-md);
            color: var(--theme-text-primary);">
  自定义内容
</div>

<!-- ❌ 错误：硬编码颜色 / 间距 / 圆角 -->
<div style="background: #fff; border: 1px solid rgba(28,102,196,0.15);
            border-radius: 8px; padding: 16px; color: #0F172A;">
  自定义内容
</div>
```

完整 Token 见 `docs/reference/css-token-reference.md` 与本文件 `4.0`。

#### Step 5 — 项目前缀类仅作最后手段

- 格式：`.pj-{scene}-{component}`，如 `.pj-b-system-kanban-card`
- 不得替换场景骨架
- 交付摘要中应说明这是项目扩展而非技能包原生组件

#### Step 6 — 运行 Audit，修复所有 ERROR

```bash
node scripts/skill-audit.js <html文件> --scene <场景id>
```

有 ERROR 必须修复后再交付；WARN 需在摘要中说明原因与处理方式。

---

## 4.0 Token 与资源速查

> 本节只保留主入口级速记；完整变量表与示例见 `docs/reference/css-token-reference.md`。

### 4.1 官方资产与依赖速记

| 类型 | 路径 / 规则 | 说明 |
|---|---|---|
| B 端 / Website Logo | `assets/logo-flat.png` | 浅色 / 深色统一同一文件 |
| UE5 HUD 品牌 | `.ue5-overlay-system-bar__brand-mark` | CSS 背景图形态，不额外叠加 `<img>` |
| UE5 默认背景图 | `assets/ue5-bg-scene.png` | 可替换为项目真实场景图 |
| 图标库 | `scripts/lucide-umd-500.js` | 页面加载后调用 `lucide.createIcons()` |
| 图表库 | `scripts/echarts.min.js` + `scripts/echarts-theme-lingjing.js` | 图表必须本地优先 |
| UE5 桥接 | `components/dist/lingjing-core-ue5-bridge.js` | 环境允许时优先复用 |

### 4.2 常用 Token 速记

| 类别 | Token | 用途 |
|---|---|---|
| 背景 | `--bg-base` / `--bg-card` / `--bg-glass` | 页面 / 卡片 / 浮层背景 |
| 文字 | `--theme-text-primary` / `--theme-text-secondary` | 标题 / 正文 / 次级说明 |
| 品牌 | `--theme-primary` / `--theme-secondary` / `--theme-accent` | 主按钮 / 高亮 / 成功态 |
| 状态 | `--success-base` / `--warning-base` / `--error-base` / `--info-base` | 状态语义色 |
| 边框 | `--glass-border` | 容器边框 |
| 间距 | `--spacing-xs/sm/md/lg/xl` | 4 / 8 / 16 / 24 / 32 px |
| 圆角 | `--radius-sm/md/lg` | 6 / 8 / 12 px |

### 4.3 按钮与品牌速记

- 按钮文案建议 ≤ 6 个汉字，优先“动词 + 宾语”。
- `btn-icon` 只放图标，必须带 `aria-label` 与 `title`。
- B 端与 Website 品牌区统一使用 `logo-flat.png`，禁止用 SVG / Lucide 图标冒充品牌。
- UE5 顶栏品牌使用 `.ue5-overlay-system-bar__brand-mark`，不要把 B 端 Logo 直接塞进 HUD。

---

## 5.0 质量检查清单 (AI 自检)

进入最终输出前，至少确认以下关键项：

- [ ] 已读取 `SKILL.md`、`scene_coverage_matrix.yml`、调用方项目结构文件
- [ ] 已完成 PRE-GEN 声明
- [ ] 已明确 `scene_id` 与 `chosen_level`
- [ ] 已命中当前场景最小骨架（见 `1.1`）
- [ ] 类名已完成生成前 / 生成后双校验
- [ ] 未把 `semantic_id` / `id` 直接写入 HTML class
- [ ] 框架层严格复用官方骨架，而非自建平替
- [ ] 表格、图表、侧栏、HUD 等关键区块有真实可运行结构，而非占位
- [ ] 图表通过 `LingJingChart.init()` 初始化，并绑定灵境色板
- [ ] 资源路径可达，`resource_closure_ok` 判定真实可信
- [ ] 对 Level 1 / 2 / 3 的选择有明确证据，而不是主观猜测
- [ ] 若为 Level 2 / 3，已说明项目级差异点，不是纯模板换词
- [ ] 已运行 `skill-audit.js`，并根据 PASS / WARN / FAIL 给出真实结论
- [ ] 摘要已包含 `scene_id`、`chosen_level`、`template_match_score`、`missing_key_modules_count`、`retained_frame_shell`

---

## 6.0 文档分流导航

### 当前活入口 / 运行主链

- `TRUTH_SOURCES.md`
- `scene_coverage_matrix.yml`
- `docs/operations/QUICKSTART_FOR_AGENT.md`
- `docs/operations/CLAUDE_CODE_START_HERE.md`
- `docs/operations/b-system-layout-playbook.md`
- `docs/operations/ue5-overlay-layout-playbook.md`
- `docs/operations/EXTENSION_GUARD.md`

### 参考层（按需深读）

- `docs/reference/system-template-map.md`
- `docs/reference/ue5-template-map.md`
- `docs/reference/b-system-composition-recipes.md`
- `docs/reference/CLASS_NAME_REFERENCE.md`
- `docs/reference/css-token-reference.md`
- `docs/reference/TEMPLATE_ASSET_REFERENCE_MAP.md`

### 验证 / 留档层（不要默认全量读取）

- `docs/validation/`
- `docs/validation/generated-reports/`

### 历史归档层（可追溯，不是首读入口）

- `docs/archive/`
- `docs/archive/memory/`
