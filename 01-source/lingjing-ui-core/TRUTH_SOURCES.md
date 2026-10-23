# 🔍 TRUTH_SOURCES.md — 真值源总览

> **目的**：明确 lingjing-ui-core v3.0.0 下，哪些文件是“机器与 AI 必须信”的真值源，哪些只是解释层；避免规则—模板—实现之间再次出现断层与口径冲突。

---

## 1. 版本与协议真值源

- **主版本真值源（唯一）**
  - `SKILL.md` frontmatter `metadata.version`
  - 当前值：`3.0.0`
- **版本从属文件（必须与主真值源保持一致，不再单独作为权威）**
  - `README.md` 顶部版本行与版本徽章
  - `package.json.version`
  - `skill_version.json.version`
  - `docs/DOCS_STATUS_SUMMARY.md` 中的“当前主版本”说明
- **执行协议真值源（优先级）**
  - 1️⃣ `SKILL.md §0.0 核心执行规约` — 所有场景通用的执行协议与行为黑名单
  - 2️⃣ `scene_coverage_matrix.yml` — 各场景的机器判定矩阵（Level、shell、一致性约束）
  - 3️⃣ `docs/operations/b-system-layout-playbook.md` — b_system 场景布局决策卡
  - 4️⃣ `docs/operations/ue5-overlay-layout-playbook.md` — ue5_overlay 场景布局决策卡

> **规则**：若 `SKILL.md` 与其他文档描述冲突，以 `SKILL.md` + `scene_coverage_matrix.yml` 为准；playbook 属于对特定场景的“展开解释”，不得反向覆盖主协议。

---

## 2. 场景 / 模板 / 类名真值源

### 2.1 场景与模板分级

- **主机读真值源**
  - `scene_coverage_matrix.yml.scene_coverage.*.candidate_templates[*]`
    - 字段：`path / grade / use_scope / page_types / layout_mode / preferred_level / suited_for / risk_notes_zh`
  - `skill_version.json.examples.*`（canonical / candidate / demo / blacklist / limited；`anti_pattern` 等反例分级来自 `scene_coverage_matrix.yml` 与 `data/template_router.json`）
- **快速索引层（供工具与代理按路径反查，不是独立真值源）**
  - `data/template_router.json`
    - 作用：按 `path` 查询 `scene / grade / use_scope / page_types / preferred_level`
    - 说明：当与 `scene_coverage_matrix.yml` / `skill_version.json` 冲突时，以后者为准
- **任务路由层**
  - `data/task_router.json`
    - 作用：将“任务关键词/ID → scene + page_types + preferred_level + primary/fallback_templates`
    - 说明：用于减轻 AI 从长文中猜模板的负担，但不单独决定模板等级与使用范围

### 2.2 类名与结构

- **类名真值源**
  - `data/class_registry.json`
    - 字段：`classes[*].type`（canonical / utility / alias / deprecated / demo_only）
    - 规则：
      - 仅 `canonical` 与 `utility` 可直接出现在业务交付页
      - `alias` 必须在生成前归一化为其 `canonical` 字段值
      - `demo_only` 仅限 `examples/demo`，业务交付页禁止出现
  - `docs/reference/CLASS_NAME_REFERENCE.md`
    - 解释层：帮助人类理解类名分组与用法，不是机器权威来源

- **结构与 shell 真值源**
  - `scene_coverage_matrix.yml.shell_consistency.*`
    - 定义各场景的强制骨架类与 DOM 形态
  - `scene_coverage_matrix.yml.scene_coverage.*.module_shells[*]`
    - 定义可复用的模块壳（如 `b_system_dashboard_shell`、`ue5_overlay_shell`）

> **规则**：结构是否合法 = 类名存在 + DOM 形态满足 `shell_consistency` / `module_shells`；仅其一通过不算合规。

---

## 3. 审计与中间层真值源

- **审计脚本**
  - `scripts/skill-audit.js`
    - 负责：
      - 类名真值校验（unknown / alias / demo_only / candidate / pj-*）
      - `<style>` 污染与内联 `style` 高风险检查
      - demo 修饰类泄漏 / 表格溢出 / B 端框架层缺失
      - 资源引用可达性（CSS/JS 本地路径）
      - **模板分级策略**：结合 `skill_version.json` / `scene_coverage_matrix.yml` 判断 `blacklist / demo / limited scene mismatch`
- **中间层配置**
  - `data/task_router.json` — 任务 → 场景 → 模板的轻量路由
  - `data/template_router.json` — 模板 → 场景 / 等级 / 使用范围索引

> **规则**：
> - 审计结论 (`audit-report.json`) 中关于 `template_grade / template_categories / template_scene_from_registry` 字段，来自 `skill_version.json` + `scene_coverage_matrix.yml`，不能手改覆盖。
> - `task_router` / `template_router` 是中间层索引与决策辅助，**不是**“第四套真值源”。当它们与 matrix / skill_version 冲突时，以后者为准，router 需要被修复。

---

## 4. 文档层与解释层

以下文件用于解释与导航，**不得单独作为机器真值源**：

- `README.md` — 项目总览与快速开始
- `docs/DOCS_STATUS_SUMMARY.md`、`docs/REPO_STRUCTURE_GUIDE.md` — 文档导航与仓库结构入口
- `docs/operations/ITERATION_GUIDE.md`、`docs/operations/HIGH_RISK_FILES_AND_PHASE1_ORDER.md` — 整体迭代说明与高风险文件清单
- `examples/README.md` — examples 分级规则、边缘资产归属与生成产物说明
- 其他历史分析与经验文档（`docs/archive/COMPONENT_CATALOG.md` / `docs/archive/WORKFLOW_GUIDE.md` / `docs/archive/OPTIMIZATION_PLAN.md` 等）

> **使用建议**：
> - AI 工具在执行 UI 生成时，**必须**先读取：`SKILL.md` → `scene_coverage_matrix.yml`；随后按 `SKILL.md §0.1 按任务阅读顺序`，再继续深读对应场景的 playbook / template map / validation，而不是默认全量读取全部子文档。
> - 人类维护者在修改规则或模板分级时，必须先更新真值源（`SKILL.md` / `scene_coverage_matrix.yml` / `skill_version.json`），再更新 README / 导航文档；不得只改解释层。

---

## 5. Phase 1 特别说明（b_system + ue5_overlay）

- **当前 Phase 1 优先深做场景**：
  - `b_system` — B 端管理系统 / 作业系统
  - `ue5_overlay` — UE5 Web Overlay / 数字孪生叠加层
- **配套专项映射文档**：
  - `docs/reference/system-template-map.md` — 系统场景：类型 → 模板 → Level → Shell → 常见误用
  - `docs/reference/ue5-template-map.md` — UE5 场景：布局模式 → 模板 → Level → Shell/Layer → 常见误用
- **其他场景（当前阶段定位）**：
  - `website` / `presentation` / `ai_assistant`：在 v3.0.0 下保持兼容可用，但**不作为 Phase 1 深做主线**；router 与模板治理只做必要修正，不做扩写。

> 若你是 AI 工具：当用户没有特别指定场景时，在“系统 / 数字孪生 / UE5 大屏 / 管理后台”等需求下，应优先进入 `b_system` 或 `ue5_overlay`，并结合上述真值源与专项映射文档完成决策；不要在当前阶段主动把任务导向 website / presentation 作为主策略。

---

## 6. Phase 1 稳定度状态表（v3.0.0）

> **说明**：本表用于标记当前阶段 "场景 × 类型/Mode" 的稳定度，仅覆盖 `b_system` 与 `ue5_overlay` 主线；其他场景仍按“兼容支持”处理。

| 场景 | 类型 / Mode | 代表任务 / 模板 | 稳定度 | 说明 |
|------|-------------|-----------------|--------|------|
| `b_system` | `list` | `b_system_list` / `b-system-task-list-top-filters.html` | 基本稳定 | 已有 router + matrix + system-template-map + 专向 Guard + 正反例回归；list vs 左侧高级筛选边界由 `b_system_list_left_filter_panel_forbidden` 守护。 |
| `b_system` | `advanced_list` | `b_system_advanced_list` / `b-system-advanced-list-with-left-filter-panel.html` | 基本稳定 | 已有 router + matrix + system-template-map + 专向 Guard + 正反例回归；advanced_list 壳缺失由 `b_system_advanced_list_shell_missing` 守护。 |
| `b_system` | `detail` | `b_system_detail` / `b-system-detail-order.html` | 基本稳定 | 已有 router + matrix + system-template-map + 专向 Guard + 正反例回归；详情页混入 Dashboard 壳由 `b_system_detail_dashboard_shell_forbidden` 守护。 |
| `ue5_overlay` | `overlay_dashboard` / Mode 1 | `ue5_overlay_mode_1_single_hud` / `ue5_overlay_data_viz.html` | 基本稳定 | layout_mode=1 且缺失 HUD 时由 `ue5_mode1_hud_missing` 守护；Mode1 vs minimal overlay 边界已通过正反例回归锁定。 |
| `ue5_overlay` | `overlay_dashboard` / Mode 2 | `ue5_overlay_mode_2_hud_sidepanel` / `ue5_overlay_quality_tracking.html` | 基本稳定 | Mode2 vs Mode5 的 Dock / 双侧面板边界由 `ue5_mode2_dock_or_double_panel_forbidden` 守护，配有正反例。 |
| `ue5_overlay` | `overlay_dashboard` / Mode 3 | `ue5_overlay_mode_3_hud_alert_center` / `ue5_overlay_dashboard.html` | 基本稳定 | Mode3 必须具备 `alert-center` 壳，壳过轻/过重由 `ue5_mode3_shell_invalid` Guard 与正反例回归保障。 |
| `ue5_overlay` | `overlay_dashboard` / minimal | `ue5_overlay_minimal_no_hud` / `ue5_overlay_minimal_no_hud.html` | 基本稳定 | 已进入显式任务路由与回归基线：无 HUD、仅骨架 + world-marker 在审计中合法通过。 |
| `website` | `N/A` | `website-complete.html` | 兼容支持 | 模板与样式已可用，但当前 Phase 1 不围绕 website 构建路由与 Guard；仅做兼容维护。 |
| `presentation` | `N/A` | `presentation-*.html` | 兼容支持 | 演示场景仍以 Level 2/3 自行构建为主；暂无完整中间层与 Guard 治理。 |
| `ai_assistant` | `N/A` | `b-system-ai-assistant.html` | 兼容支持 | 作为 limited 模板存在，受 `EXTENSION_GUARD` 约束；当前阶段不作为主线治理对象。 |

> 当前版本尚未将任何场景标记为“完全稳定（已稳定）”；对于上表中的“基本稳定”组合，应视为 Phase 1 的主线约束与回归锚点。