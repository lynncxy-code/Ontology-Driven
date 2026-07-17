# ⚡ QUICKSTART_FOR_AGENT — 给 AI 的 5 分钟起步卡

> 适用对象：Claude Code / GPT / 其他支持文件访问的 AI 开发助手。
> 目标：在 **5 分钟内**，让你在 `lingjing-ui-core` 仓库里走上正确主线，而不是自己猜规则或随便翻 examples。

---

## 1. 当前阶段的“正确问题”

在这个仓库里，你**默认应该优先回答的问题**是：

- 在 B 端管理系统（`b_system`）和 UE5 Web Overlay（`ue5_overlay`）场景下，
- 如何根据 PRD 或用户自然语言需求，
- 在 **已有规范 + 模板 + 审计** 之间，稳定地选择：
  - 场景（scene）
  - 类型 / 布局模式（type / layout_mode）
  - 模板（template）
  - Level（1/2/3）
  - 审计与资源闭环（guard）

> **Phase 1 优先场景**：`b_system` + `ue5_overlay`。
> `website` / `presentation` / `ai_assistant` 只做兼容维护，不是当前深做主线。

---

## 2. 必读文件与推荐顺序

在输出任何 HTML / 代码前，先完成**基础必读**，再按场景继续深读：

### 2.1 基础必读（所有任务都要先读）

1. **`SKILL.md`**
   - 重点：`§0.0 核心执行规约`、`§0.1 按任务阅读顺序`、`§1.1 场景最小命中矩阵`、`§3.0 三级策略`、`§5.0 质量检查清单`。
2. **`TRUTH_SOURCES.md`**
   - 重点：哪些文件是版本、规则、模板、类名的真值源；哪些只是解释层。
3. **`scene_coverage_matrix.yml`**
   - 重点：
     - `decision_matrix`（Level 1/2/3 机器规则）
     - `shell_consistency.*`
     - `scene_coverage.*`

### 2.2 按场景继续深读（不要默认全量通读）

- **`b_system`**：
  - `docs/operations/b-system-layout-playbook.md`
  - `docs/reference/system-template-map.md`
  - 涉及侧边栏 / 主题 / 图表 / 表格时再读 `docs/reference/b-system-composition-recipes.md`
- **`ue5_overlay`**：
  - `docs/operations/ue5-overlay-layout-playbook.md`
  - `docs/reference/ue5-template-map.md`
  - 再按 `layout_mode` 读取对应 `examples/ue5-overlay/*.html`
- **`website` / `presentation` / `ai_assistant`**：
  - 先读 `data/task_router.json` / `data/template_router.json` 与对应模板
  - 只有在验证 / 回归 / 边界不清时，再读 `docs/validation/` 或 `docs/operations/EXTENSION_GUARD.md`

### 2.3 真值与索引补读

- `data/class_registry.json`
- `data/task_router.json`
- `data/template_router.json`

> 若时间有限：至少完成基础必读 1~3 步，再开始任何代码输出。未读取 `scene_coverage_matrix.yml` 就写 HTML = 违反 `SKILL.md §0.0`。

---

## 3. Phase 1 标准工作流（必须遵循）

以“生成/改造一个页面”为例，你应该按照下面的**原子步骤**执行：

1. **识别场景与类型**
   - 从用户指令 / PRD 抽取：
     - 是 B 端系统后台，还是 UE5 Overlay / 数字孪生大屏？
     - 属于哪类页面：仪表盘 / 列表 / 详情 / 高级筛选 / 配置 / Overlay 模式 1~5？
   - 若不确定，先在回复中给出 1–2 个候选场景与类型，请求用户澄清；不要自行假设。

2. **读取真值源与中间层**
   - 读取：`SKILL.md` → `scene_coverage_matrix.yml` → 对应场景的 playbook。
   - 对照 `scene_coverage_matrix.yml.scene_coverage.<scene>` 中的 `candidate_templates`、`module_shells` 与 `level_bias`，确认：
     - 有无高匹配模板（Level 1 候选）
     - 是否更适合走组件编排（Level 2）
   - 读取 `data/task_router.json` 和 `data/template_router.json`，用它们来 **验证** 你的判断，而不是推翻真值源。

3. **声明 PRE-GEN 信息（不得跳过）**

在写 HTML / JSX 前，先在回复里显式给出：

```text
[PRE-GEN]
scene       = <b_system|ue5_overlay>
page_type   = <dashboard|list|detail|planning|overlay_dashboard|quality_tracking...>
layout_mode = <1|2|3|4|5 或 n/a>
level       = <level_1|level_2|level_3>
template    = <参考模板路径或 "none"，必须与 matrix/router 一致>
frame_shell = <必须保留的骨架类组合，例如 b-layout-sidebar + b-sidebar + b-main + b-header>
class_check = <已在 data/class_registry.json 中校验所有计划输出的类名>
style_check = 本次 HTML 不含任何 <style> 块；图表若有，已规划使用 LingJingChart.init() 而非裸 echarts.init()
```

> 如果你无法填完整上面任意一项，禁止继续写 HTML，而应先补充取证步骤（多读文件 / 多问问题）。  
> `style_check` 必须为肯定句；若计划使用 `<style>` 块，必须在此说明具体原因并引用允许例外的规则条款，否则视为违规。

4. **框架层先行 + 资源落地**
   - 先输出 B 端或 UE5 的框架层骨架：
     - B 端：`b-layout-sidebar > b-sidebar + b-main > b-header + b-content`。
     - UE5：`ue5-overlay-root > ue5-overlay-viewport > ue5-overlay-safe-area` + `topbar-hud` + 对应布局模式的面板类。
   - 确保引用了正确的样式入口和脚本（在目标项目中可达）：
     - `components/dist/lingjing-core-b-system.css` 或 `lingjing-core-ue5-overlay.css`
     - `scripts/lucide-umd-500.js`（图标）
     - `scripts/echarts.min.js` + `scripts/echarts-theme-lingjing.js`（如有图表）

5. **根据 Level 选择生成策略**
   - **Level 1**：高匹配模板轻调
     - 复制模板框架，仅调整文案、字段、顺序、显隐；禁止改动框架层骨架。
   - **Level 2**：组件与规则编排
     - 以 `module_shells` + canonical 组件类为基座，按 PRD 的模块组合页面；
     - 允许重排主内容区，但不得推翻 shell 与关键组件组合方式。
   - **Level 3**：规范指导下的场景扩展
     - 在保留场景框架层的前提下，说明哪些信息架构/模块是对规范的扩展。

6. **运行审计并输出摘要（硬卡点）**
   - 必须运行：
     - `node scripts/skill-audit.js <html-file> --scene b_system|ue5_overlay`
   - **audit FAIL（exit=2）时，禁止在回复中出现任何”已完成””已生成””可以使用”等交付性结论；必须先修复所有 ERROR，重跑 audit 直到 exit=0，才允许给出交付摘要。**
   - 验证 / 验收任务里，不能只口头说”跑过 audit”；必须在回复里带出：
     - `audit_command`
     - `audit-report.json` 路径
     - `delivery_gate`
     - `audit_exit_code`
     - `blocking_error_checks`（若为空写 `[]`）
   - 在回复末尾给出 3–5 行结构化摘要，至少包含：
     - `scene_id`
     - `chosen_level`
     - `template_match_score`（如未实际对比模板，可给出估计并说明依据）
     - `missing_key_modules_count`
     - `retained_frame_shell`
     - `resource_closure_ok`


---

## 4. 行为黑名单（只列当前阶段最关键的）

以下行为在 Phase 1 一律视为错误路径：

- **跳过真值源**
  - 未读取 `SKILL.md` / `scene_coverage_matrix.yml` 就开始写 HTML。
  - 完全不参考 `b-system-layout-playbook.md` / `ue5-overlay-layout-playbook.md` 就构建复杂布局。
- **绕过框架层**
  - 在 B 端页面中不用 `b-layout-sidebar` / `b-sidebar` / `b-main` / `b-header`，而自造 `.dashboard-container` 等类。
  - 在 UE5 页面中不用 `ue5-overlay-root` / `ue5-overlay-safe-area` / `topbar-hud`，而自造 `.overlay-root-custom`。
- **类名与样式违规**
  - 使用 `data/class_registry.json` 中不存在的类名（unknown）。
  - 使用 `type=demo_only` 的类或 `*-demo-*` 修饰类。
  - 在 HTML 中写 `<style>` 定义布局/组件样式，或使用带硬编码值的 `style="..."`（token-only 例外除外）。
- **绕过审计与资源闭环**
  - 不运行 `scripts/skill-audit.js` 就声称“已按规范完成”。
  - 引用不存在或 CDN-only 的 CSS/JS 资源，却声称“资源已闭环”。

---

## 5. Phase 1 特别提醒

- 在这轮里，**不要把精力放在 website / presentation / ai_assistant 的路由细节扩写上**：
  - 可以使用它们已有的模板与路由作兼容输出；
  - 但当前所有“中间层建设”与“模板映射”优先服务 `b_system` 与 `ue5_overlay`。
- 当你需要更细致的映射关系时：
  - 系统场景 → 参考 `docs/reference/system-template-map.md`
  - UE5 场景 → 参考 `docs/reference/ue5-template-map.md`

只要你按上面的顺序读文件、声明 PRE-GEN 信息、遵守黑名单，并在每次生成后跑审计并写明摘要，就已经在 Phase 1 上走在了“正确主线”上。