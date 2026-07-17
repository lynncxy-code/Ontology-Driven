# 五大场景用户态测试复盘 · 2026-04

> **性质**：这是一份外部调用态测试的阶段性复盘，不是内部治理验证报告。  
> **测试目录**：`C:\Users\houyn\Desktop\双包测试-0406`  
> **测试目标**：通过真实调用结果，判断技能包在"场景判断、场景落地、实现约束、表达能力"上的真实稳定性。  
> **结论基准**：skill-audit.js 客观结果 + OpenClow 主观评估 + 人工代码核查。

---

## 一、总判断

| 层级 | 状态 |
|---|---|
| 场景理解层（scene 方向判断） | **基本成立** |
| 落地约束层（按规则稳定实现） | **仍不稳定** |
| 表达能力层（视觉质感、微交互） | **部分场景不足** |
| 执行链闭环层（audit 真正拦住问题） | **有明显缺口** |

**一句话总结**：技能包已建立场景方向判断能力，但按场景约束稳定落地的能力仍未收口。

---

## 二、五大场景 audit 客观结果

| 场景 | audit 结果 | ERROR 项 | WARN 项 |
|---|---|---|---|
| b_system (dashboard) | **FAIL** | `bare_echarts_init` ×2 | `inline_style_leak` ×6 |
| ue5_overlay | **FAIL** | `style_tag_leak` ×1（`<style>` 块重定义已有规范类） | `inline_style_leak` ×15、`project_scoped_classes` ×10 |
| ai_assistant | **FAIL** | `style_tag_leak` ×1、`frame_shell_missing` ×4、`unknown_classes` ×55+ | `inline_style_leak` ×35 |
| presentation | **FAIL** | `style_tag_leak` ×1、`unknown_classes` ×12+ | `inline_style_leak` ×6 |
| website | **FAIL** | `unknown_classes` ×1 | `inline_style_leak` ×15 |

> **5/5 场景全部 FAIL。** 没有一个场景通过 audit 闭环。

---

## 三、五大场景分场景结论

### 3.1 b_system

**判断**：场景方向正确，实现链条问题最集中。

**具体问题**：
- 图表接入链路被绕开：直接 `echarts.init()` 而不是通过 `LingJingChart.init()`，audit 报 `bare_echarts_init: ERROR`
- `inline_style` 含硬编码值（`padding: 16px`、`margin-bottom: 16px`、`border-bottom: 1px solid`），未使用 CSS Token
- 存在 `grid-cols-3` 等非注册类名出现于 DOM 中
- 框架层骨架 `b-layout-sidebar / b-sidebar / b-main / b-header` 存在（dashboard 页通过），但组合契约有潜在问题

**问题根源层**：实现纪律 / 组合契约

---

### 3.2 website

**判断**：场景方向基本稳定，表达力还不够。

**具体问题**：
- 出现 `website-cta-content`，audit 报 `unknown_classes: ERROR`；已对照 `components/dist/lingjing-core-website.css` 与 `data/class_registry.json` 核查，**确认为 AI 自造类名**，dist CSS 与 registry 均无此类名，属于 §0.0.2 命名自定义违规
- 大量 inline style 含硬编码布局值（`grid-template-columns`、`text-align`、`margin-top`）
- 页面结构方向对，但高级感 / 微交互（顶栏模糊、hover ripple）不稳定出现

**问题根源层**：AI 自造类名（命名自定义违规）+ 表达能力不足

---

### 3.3 ai_assistant

**判断**：当前不通过，问题最重。

**具体问题**：
- 完全缺失 b_system 框架层骨架（`b-layout-sidebar / b-sidebar / b-main / b-header` 全部 MISSING）
- 55+ 个未注册类名（`ai-workspace`、`ai-chat-pane`、`message-bubble-ai`、`message-avatar-ai`、`action-btn-primary` 等），整页自造类名体系
- 大块 `<style>` 标签定义整页样式（audit `style_tag_leak: ERROR`）
- 35 处 inline style

**问题根源层**：命中场景后滑向整页 demo 化实现，composition boundary 完全没被钉住

---

### 3.4 ue5_overlay

**判断**：场景方向明显对了，执行纪律没有真正兜住。

**具体问题**：
- 框架层骨架存在（`ue5-overlay-root / topbar-hud / ue5-overlay-safe-area`），方向正确
- 但仍存在 `<style>` 块定义 `body` / `.ue5-overlay-root` / `.ue5-overlay-background` 等已有规范类（audit `style_tag_leak: ERROR`）
- 19 处 inline style（图标 `style="width:20px"`），audit 报 WARN
- `pj-ue5-*` 项目前缀类 10 个（WARN 级，规则允许，但需确认 token 合规）

**问题根源层**：执行纪律——规则存在但实现链没有真正拦住 style 污染

---

### 3.5 presentation

**判断**：方向正确型不通过。

**具体问题**：
- 框架骨架存在（`presentation-slide / slide-title`），方向对
- 但自定义了 `.slide-cover-title` 等类及对应 `<style>` 块（audit `style_tag_leak: ERROR`）
- 12+ 个未注册类名（`kpi-highlight__label` 等）
- 页面 composition / layout quality / rendering quality 不足，还未达到演示文稿应有交付质量

**问题根源层**：`<style>` 污染 + 未注册类名 + composition 质量

---

## 四、为什么当前不应继续修测试页面

1. **测试页面只是症状**，每修一处都会暴露新问题，是无限游戏
2. **问题不在单个页面**，而在技能包规则没有被执行链真正拦住——修完这个页面，下次生成同类页面还会重犯
3. **已达到盘面识别目的**：5场景 × audit 客观数据 × 分层问题定位，已经足够归并主线，继续 patch 是在消耗收益递减的边际工作
4. **碎片化 patch 会制造噪音**：散落的页面修改会干扰后续优化主线的清晰度

---

## 五、四条优化主线归并

### 主线 A：执行链闭环（P1）

**问题本质**：规则写了，audit 也识别了问题，但 audit 结果没有成为真正的交付卡点——AI 可以在 audit 报 ERROR 后继续交付，或在生成阶段直接绕过 audit 环节。

**涉及场景**：ue5_overlay（主）、ai_assistant（主）、b_system（次）

**方向**：
- 不是补更多规则，而是把 audit 结论接回执行链，让"audit FAIL = 禁止交付"成为真正的硬卡点
- 在 SKILL.md 和 QUICKSTART_FOR_AGENT 中，把"audit 必须在生成完成后、交付前强制跑"的位置和后果说得更具体、更不可绕过
- 区分两类问题：audit 没被触发（流程缺口）vs audit 触发了但结论被忽略（执行纪律缺口）

---

### 主线 B：组合契约 / 语义脑补（P2）

**问题本质**：AI 在找不到合适组件时，倾向于自造语义化类名（`mission-*`、`grid-cols-*`、`ai-workspace`），而不是走 Component Gap Protocol 的六步决策树。

**涉及场景**：b_system（主）、ai_assistant（主）

**方向**：
- 补清 `data/class_registry.json` 中缺失的高频合法类（如 `website-cta-content`）
- 在 Component Gap Protocol 中加入"禁止语义脑补类名"的具体反例列举
- DOM contract 说明：哪些类可以组合，哪些组合关系不成立

---

### 主线 C：Composition Boundary（P2）

**问题本质**：ai_assistant 和 ue5_overlay 命中场景后，容易滑向"整页自造 demo"——有骨架类，但主体内容全是自造类名 + `<style>`块。

**涉及场景**：ai_assistant（主）、ue5_overlay（次）

**方向**：
- 补清楚命中场景后哪些结构必须复用、哪些允许扩展、扩展出口在哪里
- `ai_assistant` 需要明确 workspace 落地边界：`b-layout-sidebar` 骨架必须保留，主内容区才是可扩展区域
- 在 QUICKSTART_FOR_AGENT 或 EXTENSION_GUARD 中加入"命中场景后的最小复用清单"

---

### 主线 D：表达能力观察（P3，暂不动）

**问题本质**：website 微交互（顶栏模糊、hover ripple）和 presentation 排版布局质量不稳定。

**涉及场景**：website、presentation

**方向**：
- 继续 observation，积累更多样本，不立即大修
- 当样本足够多（≥3轮测试），再判断是否需要补 CSS 组件或模板

---

## 六、建议执行顺序

| 优先级 | 主线 | 理由 |
|---|---|---|
| P1 | **主线 A：执行链闭环** | 5/5 场景都有 `<style>` 污染，这是最普遍的断层，修一处收益最大 |
| P2 | **主线 B：组合契约** | b_system 是最重要的主线场景，图表接入和类名问题直接影响交付质量 |
| P2 | **主线 C：Composition Boundary** | ai_assistant 完全 demo 化，需要钉住落地边界 |
| P3 | **主线 D：表达能力** | 只观察，不修 |

**先不做**：
- 继续修测试目录中的任何页面
- 新增新的测试场景
- 扩张模板数量

---

## 七、对前期已做优化的判断

**已有价值、继续保留**：
- 真值源三层架构（SKILL.md → matrix → class_registry）
- task_router / template_router 中间层（减少模板猜测）
- 13个回归基线 + regression runner（主线结构有回归保护）
- QUICKSTART_FOR_AGENT 的 PRE-GEN 信息声明卡点
- Component Gap Protocol 六步决策树框架

**仍不足的地方**：
- PRE-GEN 声明存在，但没有被真正作为硬卡点执行（AI 可以填完就继续写 `<style>`）
- audit 作为交付前必须项写进了规则，但执行中仍被绕开
- Composition Boundary 在 ai_assistant 场景下没有被真正锁定
- `bare_echarts_init` 等 audit 检查存在，但图表接入的正确路径（`LingJingChart.init()`）没有被足够强调

**结论**：前期优化是必要的，但还不充分——规则层已经建立，执行链还没有真正闭合。

---

## 八、本轮测试的边界说明

- 本轮测试为首轮用户态测试，样本量为每场景 1 个主页面
- B端场景测试包含 4 个子页面（dashboard / workorders / exceptions / resources），其余场景各 1 个
- 测试结论基于当前样本，后续需要第二轮、第三轮积累才能对"表达能力"类问题做定量判断
- `website-cta-content` 未注册类名可能是 class_registry 漏收，需确认后酌情补录

---

## 九、下一轮只做什么 / 不做什么

### 只做

- **主线 A**：把 audit 结论接回交付卡点——在 SKILL.md / QUICKSTART_FOR_AGENT 中明确"audit FAIL = 禁止继续交付"，区分"audit 未触发"与"触发了但被忽略"两类缺口，分别收口
- **主线 B**：补 ai_assistant 的 composition boundary——明确命中场景后哪些骨架必须保留、哪些是合法扩展出口、哪些类名属于禁止自造
- **主线 B**：~~确认 `website-cta-content` 的类名状态~~（已核查：确认为 AI 自造类名，dist CSS / registry 均无，已在 §3.2 定性标注）✅
- **主线 B**：补图表接入正确路径的代码示例（`LingJingChart.init()` vs 直接 `echarts.init()`）

### 不做

- 不继续修 `双包测试-0406` 中的任何测试页面
- 不新增测试场景或新模板
- 不重写 `scene_coverage_matrix.yml` 的结构
- 不扩大 `docs/` 文档数量
- 不对 website / presentation 的表达能力问题做主动修改（继续 observation）
- 不在本轮结论尚未收口前开启第二轮用户态测试
