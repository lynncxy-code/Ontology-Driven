# 📚 LingJing Core 文档导航与版本状态一览

> 目的：帮助 AI 工具和开发者快速区分「当前活入口 / 运行期文档 / 验证留档 / 历史归档」，避免默认搜索直接落到旧稿或低频材料。
> 当前主版本：v3.0.0 (Stable)

---

## 1. 首读入口

优先按下面顺序读取：

1. `../SKILL.md` — 主执行协议
2. `../TRUTH_SOURCES.md` — 真值源与优先级总览
3. `../scene_coverage_matrix.yml` — 场景 / Level 机器真值源
4. `operations/QUICKSTART_FOR_AGENT.md` — AI 快速起步卡
5. `operations/CLAUDE_CODE_START_HERE.md` — 仓库内执行入口
6. `REPO_STRUCTURE_GUIDE.md` — 仓库结构与资产归属说明

> 若只是想知道“文档现在怎么分层”，先看 `REPO_STRUCTURE_GUIDE.md`；若想直接进入运行主线，先看 `operations/`。

---

## 2. `docs/` 分层说明

### 2.1 `operations/` — 当前活文档 / 运行期主链

这里放仍会直接影响执行路径、观察周期或发版动作的文档：

- `operations/QUICKSTART_FOR_AGENT.md`
- `operations/CLAUDE_CODE_START_HERE.md`
- `operations/ROUTING_DECISION_PROTOCOL.md`
- `operations/EXTENSION_GUARD.md`
- `operations/b-system-layout-playbook.md`
- `operations/ue5-overlay-layout-playbook.md`
- `operations/NEXT_STAGE_OPERATION_PLAN.md`
- `operations/MULTI_SCENE_OBSERVATION_CYCLE.md`
- `operations/PRE_RELEASE_CHECKLIST.md`
- `operations/ITERATION_GUIDE.md`
- `operations/HIGH_RISK_FILES_AND_PHASE1_ORDER.md`

### 2.2 `reference/` — 地图 / 索引 / 查表 / 实践参考

这里放需要按需查阅、但不是默认首读的说明层：

- `reference/system-template-map.md`
- `reference/ue5-template-map.md`
- `reference/CLASS_NAME_REFERENCE.md`
- `reference/b-system-composition-recipes.md`
- `reference/TEMPLATE_ASSET_REFERENCE_MAP.md`
- `reference/CODE_SNIPPETS.md`
- `reference/css-token-reference.md`
- `reference/BEST_PRACTICES.md`

### 2.3 `validation/` — 回归 / 验证 / 运行期留档

这里放验证证据，而不是规则本身：

- `validation/PHASE1_REGRESSION_BASELINES.md`
- `validation/PHASE1_VALIDATION_REPORT.md`
- `validation/PHASE1_USABILITY_VALIDATION.md`
- `validation/PHASE1_GENERATION_PLAYBACK.md`
- `validation/PHASE2_GENERATION_STRESSCHECK.md`
- `validation/TEMPLATE_REPAIR_REGRESSION.md`
- `validation/HIGH_VALUE_TEMPLATE_REVIEW.md`
- `validation/MULTI_SCENE_OBSERVATION_EXAMPLES.md`
- `validation/RELEASE_READINESS_SUMMARY.md`
- `validation/generated-reports/*.json`

### 2.4 `archive/` — 历史过程稿 / 旧版本留档

这里的文档保留追溯价值，但不代表当前主版本默认口径：

- `archive/COMPONENT_CATALOG.md`
- `archive/INTERACTIONS.md`
- `archive/WORKFLOW_GUIDE.md`
- `archive/COMPONENT_USAGE_ANALYSIS.md`
- `archive/RATIONALITY_ANALYSIS.md`
- `archive/OPTIMIZATION_PLAN.md`
- `archive/V3.0_IMPLEMENTATION_SUMMARY.md`
- `archive/PRESENTATION_GUIDE.md`
- `archive/STABILITY_STATUS.md`
- `archive/memory/`

---

## 3. 当前主线阅读建议

### 3.1 做规则判断 / 模板决策
`../SKILL.md` → `../TRUTH_SOURCES.md` → `../scene_coverage_matrix.yml` → `operations/ROUTING_DECISION_PROTOCOL.md` → 对应 playbook / template map

### 3.2 做运行期 observation / 运维节奏判断
`operations/NEXT_STAGE_OPERATION_PLAN.md` → `operations/MULTI_SCENE_OBSERVATION_CYCLE.md` → `validation/`

### 3.3 查类名 / 模板 / 资产归属
`reference/CLASS_NAME_REFERENCE.md` → `reference/system-template-map.md` / `reference/ue5-template-map.md` → `../examples/README.md`

### 3.4 做 UX/UI handoff 对齐
`lingjing-ux-core/README.md` → `lingjing-ux-core/docs/UX_UI_ALIGNMENT_PLAN.md` → `lingjing-ux-core/docs/UX_UI_CROSSWALK.md` → `lingjing-ux-core/docs/UX_UI_HANDOFF_REGRESSION.md`

### 3.5 查历史背景
仅在需要追溯时进入 `archive/`


---

## 4. 使用提醒

- `archive/` 中的文档可以引用，但不应作为默认执行入口。
- `validation/` 中的文档提供证据，不单独覆盖真值源。
- 若文档口径冲突，仍以 `../SKILL.md` + `../scene_coverage_matrix.yml` 为准。
- 如果你需要仓库目录级导航，而不是文档级导航，请转到 `REPO_STRUCTURE_GUIDE.md`。
