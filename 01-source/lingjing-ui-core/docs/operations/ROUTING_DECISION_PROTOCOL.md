## 🧩 ROUTING_DECISION_PROTOCOL — Phase 1 中间层决策协议（b_system + ue5_overlay）

> **目的**：把当前 Phase 1 的 `Scene → Task → Type/Mode → Template → Level → Guard` 主链写成一份可执行协议，供 Claude Code / AI 在 `b_system` 与 `ue5_overlay` 场景下稳定决策。
> **范围**：仅适用于 `b_system` 与 `ue5_overlay`；其他场景在 Phase 1 中只做兼容维护。

---

## 1. 主链步骤（必须按顺序执行）

1. **Step 1：判定 scene**
   - 依据：
     - 用户需求语义（后台系统 / UE5 叠加层 / 官网 / 幻灯片）；
     - `SKILL.md` 与 `TRUTH_SOURCES.md` 中的场景定义；
     - `scene_coverage_matrix.yml.scene_coverage` 中可用场景列表。
   - Phase 1 中，若需求同时满足以下任一条件，应优先判为：
     - `b_system`：后台管理系统 / 运营驾驶舱 / 工单 / 配置类场景；
     - `ue5_overlay`：UE5 Web Overlay / 数字孪生叠加层 + 三维视口 + world-marker + HUD。

2. **Step 2：命中 task_router（任务 → 场景）**
   - 读取 `data/task_router.json`：
     - 按 `scene` 过滤出 `b_system` 或 `ue5_overlay` 的任务条目；
     - 使用 `keywords_zh` 与需求语义匹配，选出最接近的 `id`。
  - Phase 1 重点任务示例：
    - `b_system_dashboard_overview`、`b_system_list`、`b_system_advanced_list`、`b_system_detail`；
    - `ue5_overlay_mode_1_single_hud`、`ue5_overlay_minimal_no_hud`、`ue5_overlay_mode_2_hud_sidepanel`、`ue5_overlay_mode_3_hud_alert_center`、`ue5_overlay_digital_twin_cockpit`。


3. **Step 3：从 task 读取 Type / Mode 元信息**
   - 对 `b_system`：
     - 从命中的任务条目读取 `target_type`，值与 `docs/system-template-map.md` 中的类型对应：
       - `"dashboard"` → 工作台 / 仪表盘
       - `"list"` → 列表页
       - `"advanced_list"` → 高级筛选列表
       - `"detail"` → 详情页
  - 对 `ue5_overlay`：
    - 从命中的任务条目读取 `layout_mode` 与 `target_mode`：
      - `"minimal"` → minimal overlay（无 HUD 极简骨架）
      - `1` → Mode 1 单 HUD
      - `2` → Mode 2 HUD + 右侧详情面板
      - `3` → Mode 3 HUD + 告警中心
      - `"N/A"` → 数字孪生驾驶舱（基于 Mode 2/3/5 的扩展场景，需结合 `docs/ue5-template-map.md` 与 Guard 协议谨慎处理）。


4. **Step 4：查模板映射（type/mode → template 族）**
   - 对 `b_system`：
     - 打开 `docs/system-template-map.md`，找到对应 `type_name` 段落：
       - 读取其中的 `primary_example`、`fallback_examples`；
       - 读取 `recommended_level`、`required_shell`、`key_modules`、`common_misuse`、`human_confirmation_needed`。
   - 对 `ue5_overlay`：
     - 打开 `docs/ue5-template-map.md`，找到对应 `mode_id` 段落：
       - 读取 `primary_example`、`fallback_examples`；
       - 读取 `recommended_level`、`required_shell`、`required_layers`、`common_misuse`、`human_confirmation_needed`。

5. **Step 5：通过 template_router 校验模板真值**
   - 读取 `data/template_router.json`：
     - 找到 `path` 等于上述 `primary_example` / `fallback_examples` 的条目；
     - 校验：
       - `scene` 是否与当前 scene 一致；
       - `grade` 是否为 `canonical` 或允许的 `candidate`；
       - `use_scope` 是否为 `default`，或在使用 `limited` 时已满足 Guard 条件；
       - 对 `ue5_overlay`：`layout_mode` 是否与当前 `target_mode` 一致。
   - 如果出现 `grade: demo / anti_pattern` 或 `use_scope: forbidden`，必须放弃该模板并触发 Guard 协议。

6. **Step 6：用 scene_coverage_matrix 判 Level**
   - 依据：
     - `scene_coverage_matrix.yml.decision_matrix` 的 Level 1/2/3 机器规则；
     - `scene_coverage_matrix.yml.scene_coverage.<scene>.candidate_templates` 中的 `preferred_level` 与 `suited_for`；
     - `docs/system-template-map.md` / `docs/ue5-template-map.md` 中的 `recommended_level` 与选中模板对需求的覆盖度；
   - 判定原则（简化版）：
     - 若存在高匹配 canonical 模板，且只需轻调 KPI/文案/字段 → 倾向 `level_1`；
     - 若需在现有组件/shell 内大幅编排模块（列表/详情/告警中心/复杂面板） → 倾向 `level_2`；
     - 若新增多个关键业务模块且信息架构明显超出现有模板/组件 → 倾向 `level_3`（但仍需保持 shell 一致）。

7. **Step 7：输出 PRE-GEN 声明**
   - 在写任何 HTML / 结构代码前，输出一段 PRE-GEN，明确：
     - 当前决策的 `scene` / `page_type` / `layout_mode`；
     - 选中的 `template`（具体路径）与 `level`；
     - 拟保留的 `frame_shell`；
     - class 与审计的来源 `class_check`。

8. **Step 8：进入审计 / Guard**
   - 编排或改造页面后：
     - 必须运行 `scripts/skill-audit.js <file> --scene <scene>`；
     - 按 `scene_coverage_matrix.yml.decision_matrix.audit_contract.required_summary_fields` 输出审计摘要；
     - 若触发 `frame_shell_missing` / `unknown_classes` / `demo_modifier_leak` / `broken_resource_refs` 等 ERROR，必须先修复再交付；
   - 若过程中发现涉及 Mode/Level 升级、使用 limited 模板或数字孪生驾驶舱，应按 `docs/EXTENSION_GUARD.md` 的规则停下询问人类或拒绝扩展。

---

## 2. PRE-GEN 字段来源表（b_system + ue5_overlay）

> **目标**：明确 PRE-GEN 每个字段从哪一份真值源读取，减少 AI 的自由发挥空间。

- **`scene`**
  - 来源：
    - 用户需求语义 + `SKILL.md` 场景章节 + `TRUTH_SOURCES.md` 场景说明；
    - `scene_coverage_matrix.yml.scene_coverage` 中存在的 scene 列表。
- **`page_type`**（仅 `b_system`）
  - 来源：
    - `data/task_router.json.tasks[*].page_types`；
    - `data/task_router.json.tasks[*].target_type` 与 `docs/system-template-map.md` 中对应 `type_name` 的映射。
- **`layout_mode`**（仅 `ue5_overlay`）
  - 来源：
    - `data/task_router.json.tasks[*].layout_mode`；
    - `data/task_router.json.tasks[*].target_mode` 与 `docs/ue5-template-map.md` 中 `mode_id` 的映射。
- **`template`**
  - 初始候选来源：
    - `data/task_router.json.tasks[*].primary_templates` / `fallback_templates`；
    - 对应类型/模式在 `docs/system-template-map.md` / `docs/ue5-template-map.md` 的 `primary_example` / `fallback_examples` 字段。
  - 最终确认：
    - 用 `data/template_router.json.templates[*]` 校验 `scene` / `grade` / `use_scope` / `layout_mode`（UE5），仅在通过时方可写入 PRE-GEN。
- **`level`**
  - 来源：
    - `scene_coverage_matrix.yml.decision_matrix` 中的 Level 规则；
    - `scene_coverage_matrix.yml.scene_coverage.<scene>.candidate_templates[*].preferred_level`；
    - `docs/system-template-map.md` / `docs/ue5-template-map.md` 中的 `recommended_level` 与当前需求的匹配度。
  - 判定过程：
    - 先根据模板匹配度与模块覆盖度评估 Level 1 是否充分；
    - 若出现多模板编排或新增多个关键模块，再考虑 Level 2/3，并触发 `EXTENSION_GUARD` 中的复审规则。
- **`frame_shell`**
  - 来源：
    - `scene_coverage_matrix.yml.shell_consistency.<scene>.mandatory_classes` 与 `required_dom_chains`；
    - `scene_coverage_matrix.yml.shell_consistency.<scene>.layout_shells`（如 `stats-grid`、`ue5-overlay-safe-area` 等）；
    - `docs/system-template-map.md` / `docs/ue5-template-map.md` 中的 `required_shell` 描述。
  - PRE-GEN 中应至少列出：
    - 场景骨架：
      - `b_system`：`b-layout-sidebar + b-sidebar + b-main + b-header` 等；
      - `ue5_overlay`：`ue5-overlay-root + ue5-overlay-viewport + ue5-overlay-safe-area` 为固定骨架，`topbar-hud / detail-panel / alert-center / world-marker` 按命中的任务路径增减。

- **`class_check`**
  - 来源：
    - `TRUTH_SOURCES.md` 中对类名真值源的说明；
    - `skill_version.json.data.class_registry` 条目；
    - `data/class_registry.json` 本身；
    - `scripts/skill-audit.js` 使用说明。
  - PRE-GEN 中建议写为：
    - `data/class_registry.json` + `scripts/skill-audit.js <file> --scene <scene>`，并隐含遵守 `scene_coverage_matrix.yml.shell_consistency.<scene>.machine_enforcement` 中的规则。

---

## 3. 极简示例（system / UE5 各一条）

> 以下仅演示协议如何被调用，不展示具体 HTML 结构。

### 3.1 示例：b_system — 生产运营总览页（Dashboard）

- **输入需求（摘要）**：
  - “航空制造管理后台的生产运营总览页，包含产线任务 KPI、生产进度趋势、工单分布、异常/告警动态、重点待办。”
- **按协议走主链**：
  1. 判定 `scene = b_system`；
  2. 在 `task_router.json` 命中 `id = b_system_dashboard_overview`；
  3. 读取 `target_type = "dashboard"`；
  4. 在 `docs/system-template-map.md` 中找到“工作台 / 仪表盘”段落，读取 `primary_example = examples/b-system/b-system-complete.html` 等；
  5. 在 `template_router.json` 中校验该模板 `scene = b_system` 且 `grade = canonical`、`use_scope = default`；
  6. 结合 `scene_coverage_matrix.yml` 与模板映射，判定本次可采用 `level_1`；
  7. 输出 PRE-GEN：
     - `scene = b_system`
     - `page_type = dashboard`
     - `layout_mode = n/a`
     - `level = level_1`
     - `template = examples/b-system/b-system-complete.html`
     - `frame_shell = b-layout-sidebar + b-sidebar + b-main + b-header + b-content`
     - `class_check = data/class_registry.json + skill-audit.js --scene b_system`
  8. 之后才进入页面编排与审计。

### 3.2 示例：ue5_overlay — 设备质量追踪 Overlay（Mode 2）

- **输入需求（摘要）**：
  - “数字孪生设备质量追踪场景，需要顶部质量 KPI、右侧设备详情/质检/异常、三维场景与 world-marker、HUD 快速定位异常设备。”
- **按协议走主链**：
  1. 判定 `scene = ue5_overlay`；
  2. 在 `task_router.json` 命中 `id = ue5_overlay_mode_2_hud_sidepanel`；
  3. 读取 `layout_mode = 2` 与 `target_mode = 2`；
  4. 在 `docs/ue5-template-map.md` 中找到 `mode_id = 2` 段落，读取 `primary_example = examples/ue5-overlay/ue5_overlay_quality_tracking.html`；
  5. 在 `template_router.json` 中校验该模板 `scene = ue5_overlay`、`layout_mode = 2`、`grade = canonical`、`use_scope = default`；
  6. 结合 `scene_coverage_matrix.yml` 与模板映射，判定本次可采用 `level_1`；
  7. 输出 PRE-GEN：
     - `scene = ue5_overlay`
     - `page_type = overlay_dashboard`
     - `layout_mode = 2`
     - `level = level_1`
     - `template = examples/ue5-overlay/ue5_overlay_quality_tracking.html`
     - `frame_shell = ue5-overlay-root + ue5-overlay-viewport + ue5-overlay-safe-area + topbar-hud topbar-hud--with-sidepanel + detail-panel`
     - `class_check = data/class_registry.json + skill-audit.js --scene ue5_overlay`
  8. 如有升级为双侧面板 + Dock 的诉求，应先参考 `docs/EXTENSION_GUARD.md` 再决定是否切换 Mode 5 / Level 2/3。

