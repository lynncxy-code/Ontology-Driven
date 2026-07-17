# 🚦 CLAUDE_CODE_START_HERE — 进入 lingjing-ui-core 的第一站

> 面向：在本仓库内执行代码生成/修改的 Claude Code / 其他代理。
> 目的：让你在 **第一次进入仓库** 时，就命中当前 Phase 1 的主线，而不是在规则与模板之间“自由跳跃”。

---

## 1. 当前 Phase 1 主线（只记这条）

- **优先场景**：
  - `b_system` — B 端管理系统 / 作业系统
  - `ue5_overlay` — UE5 Web Overlay / 数字孪生叠加层
- **优先目标**：
  - 建立清晰的：`Scene → Type/Mode → Template → Level → Guard` 中间层主链；
  - 让你在实现 UI 时，不再直接从 `SKILL.md` 跳到 `examples/*.html`，而是先经过机器可读中间层。
- **当前阶段暂不深做**：
  - `website` / `presentation` / `ai_assistant` 仅做兼容维护，不是当前需要“打磨到极致”的场景。

---

## 2. 进入仓库后的第一件事：确认你在什么“模式”下工作

进入仓库时，先判断自己是在哪种模式下执行：

- **模式 A：在 lingjing-ui-core 仓库内做验证/整理**
  - 典型任务：
    - 审计/修复 `examples/b-system/*.html` 或 `examples/ue5-overlay/*.html`
    - 更新中间层配置与文档
- **模式 B：在外部业务项目中接入 lingjing-ui-core**
  - 典型任务：
    - 在某个 `src/pages/**` 或 `pages/**` 下落地 B 端页面或 UE5 Overlay 页面

> 无论是哪种模式，你都必须先完成下文的“文件读取顺序”，再开始任何代码写入。

---

## 3. 必读文件顺序（Phase 1 专用）

按顺序读取，至少完成 1~3 才能写代码：

1. `SKILL.md`
   - 重点：
     - `§0.0 核心执行规约`
     - `0.0.2 行为黑名单`
     - canonical 参考文件表（尤其是 b_system / ue5_overlay 行）
2. `TRUTH_SOURCES.md`
   - 重点：
     - 谁是版本真值源（`SKILL.md` frontmatter）
     - `scene_coverage_matrix.yml` / `skill_version.json` / `class_registry.json` 等的职责与优先级
     - Phase 1 只深做 `b_system` + `ue5_overlay`
3. `scene_coverage_matrix.yml`
   - 重点：
     - `decision_matrix`（Level 1/2/3 的机器规则）
     - `shell_consistency.b_system` / `shell_consistency.ue5_overlay`
     - `scene_coverage.b_system` / `scene_coverage.ue5_overlay`
4. 针对目标场景的 Playbook
   - 若场景为 `b_system`：`docs/operations/b-system-layout-playbook.md`
   - 若场景为 `ue5_overlay`：`docs/operations/ue5-overlay-layout-playbook.md`
5. 中间层与类名真值源
   - `data/task_router.json`
   - `data/template_router.json`
   - `data/class_registry.json`
6. Phase 1 专项映射文档（如已存在）
   - `docs/reference/system-template-map.md`
   - `docs/reference/ue5-template-map.md`

---

## 4. 针对 Claude Code 的标准执行步骤

当用户在本仓库中发出“帮我改/生成一个页面”的请求时，你应该：

1. **解析用户意图**
   - 判断：
     - 场景：`b_system` 还是 `ue5_overlay`？
     - 页面类型或布局模式：仪表盘 / 列表 / 详情 / 高级筛选 / 配置 / Overlay 模式 1/2/3/5？
   - 若不确定，先用简短问题确认，而不要武断选一个。

2. **取证而不是猜测**
   - 使用工具函数读取上文列出的文件；
   - 尤其要确认：
     - 期望 Level（1/2/3）
     - 是否有现成模板可以轻调（Level 1）
     - 是否更适合按组件重编排（Level 2）

3. **在回复中显式给出 PRE-GEN 声明**

```text
[PRE-GEN]
scene       = <b_system|ue5_overlay>
page_type   = <dashboard|list|detail|advanced_list|settings|overlay_dashboard|quality_tracking...>
layout_mode = <1|2|3|4|5 或 n/a>
level       = <level_1|level_2|level_3>
template    = <examples/... 或 none>
frame_shell = <强制骨架类组合>
class_check = <已用 class_registry.json 校验>
```

> **约束**：若你无法可靠填入上述任意一项，必须先补充取证（多读文件 / 多与用户确认），禁止直接写 HTML。

4. **仅在合适的目录写入代码**

- 在本仓库内：
  - 仅修改用户或任务单明确列出的文件；
  - 除非用户要求，否则不要新建子项目或大规模复制 dist 资源。
- 在外部业务项目中：
  - 落点优先：`src/pages/**`、`src/views/**`、`pages/**`、`app/**` 等项目既有页面目录；
  - 优先复制官方 CSS/JS 到项目，再写 `<link>` / `import`，并确保路径可达。

5. **运行审计并据此修复**

- 在生成/修改 HTML 后，必须运行：
  - `node scripts/skill-audit.js <html-file> --scene b_system|ue5_overlay`
- 若 `audit-report.json.pass = false`（存在 ERROR）：
  - 禁止声称“已完成落地”；
  - 必须根据 `fail_items` 修复，再次运行审计。
- 在最终摘要中，至少给出：
  - `scene_id`
  - `chosen_level`
  - `retained_frame_shell`
  - `resource_closure_ok`
  - 是否存在 WARN，以及如何处理。

---

## 5. 当前禁止事项（Claude Code 视角）

在 Phase 1 中，以下行为被视为明显偏离主线：

- **继续深挖 presentation / website / ai_assistant**
  - 不要主动扩展这些场景的 router 条目或模板映射；
  - 仅在用户明确要求时，做最小必要修改。
- **在未更新真值源的前提下，只改解释层**
  - 严禁只改 README / 某个 md 说明，却不更新 `scene_coverage_matrix.yml` / `skill_version.json`。
- **绕过中间层，直接在 examples 上“自由发挥”**
  - 不得在不看 matrix/router 的情况下随便选 `examples/*.html` 当模板；
  - 不得在未运行审计的情况下，复制/修改 UE5 或 B 端模板后就声称“已按规范落地”。

只要你按本文件和 `QUICKSTART_FOR_AGENT.md` 的顺序行事，在 Phase 1 中就会稳稳踩在“规则 → 中间层 → 模板 → 审计”这条主链上，而不会回到“看见 examples 就想直接改”的老路。