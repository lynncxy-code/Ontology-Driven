# Lingjing UI Core v3.0.0 · Release Readiness Check

> 目的：在不做大规模测试的前提下，对当前仓库进行一次面向稳定发版的最小 readiness walk-through。仅检查“是否可以说接近稳定发版”，不重开治理主线。

---

## A. 结构层检查

- [x] 仓库结构整理已闭合：
  - `assets/`、`scripts/`、`docs/`、`examples/`、`tools/` 等顶层目录职责清晰，见 `docs/REPO_STRUCTURE_GUIDE.md`；
  - `assets/legacy-root-copies/` 仅保留历史根目录副本与取证记录，不再作为运行期资源引用目标；
  - 原 `components/玻璃效果组件使用指南.md` 已归位到 `docs/reference/玻璃效果组件使用指南.md`；
- [x] 根目录与 docs 分层清晰：
  - 根目录集中放置主协议 (`SKILL.md`)、真值源 (`scene_coverage_matrix.yml`)、版本说明 (`TRUTH_SOURCES.md`)、项目总览 (`README.md`)；
  - `docs/` 下分为 `operations/`（运行期）、`reference/`（参考层）、`validation/`（验证留档）、`archive/`（历史过程稿），结构稳定；
- [x] archive / active / operations / reference / validation 定位清楚：
  - `docs/DOCS_STATUS_SUMMARY.md` 与 `docs/REPO_STRUCTURE_GUIDE.md` 已给出分层说明与首读入口；
  - 运行主链集中在 `operations/` + 真值源，archive 仅作追溯，不再作为默认入口。

## B. 入口层检查

- [x] README / QUICKSTART / TRUTH_SOURCES / SKILL.md 入口一致：
  - 均指向 `SKILL.md` → `TRUTH_SOURCES.md` → `scene_coverage_matrix.yml` 作为规则与决策起点；
  - `SKILL.md §0.1` 与 `operations/QUICKSTART_FOR_AGENT.md` 共同定义“按任务阅读顺序”，避免默认全量通读；
- [x] UX/UI handoff 入口一致：
  - `docs/DOCS_STATUS_SUMMARY.md` 在“3.4 做 UX/UI handoff 对齐”中指向 `lingjing-ux-core/docs/UX_UI_ALIGNMENT_PLAN.md`、`UX_UI_CROSSWALK.md`、`UX_UI_HANDOFF_REGRESSION.md`；
  - `lingjing-ux-core/README.md` 也将这三份文档作为 handoff 关键入口；
- [x] 无明显坏链 / 错链：
  - 已修正早期路径变更（如 b-system 食谱、UE5 playbook、css-token reference 等）导致的旧路径；
  - 当前导航中引用的主要文档和示例文件均存在，skill-audit.js 中的章节引用已改为稳定锚点（`SKILL.md §0.0.2`、`§1.2`、`§1.3`）。

## C. 能力层检查

- [x] UI 侧运行期文档一致：
  - `SKILL.md`、`TRUTH_SOURCES.md`、`scene_coverage_matrix.yml`、`skill_version.json`、`data/*.json` 相互引用关系一致；
  - `docs/operations/` 与 `docs/reference/` 中的运行期说明与地图文档，以上述真值源为依据，不单独形成第二套规则；
- [x] UX/UI crosswalk 与 regression 一致：
  - `lingjing-ux-core/docs/UX_UI_CROSSWALK.md` 与 `UX_UI_HANDOFF_REGRESSION.md` 已确认第一批最小对齐在关键场景上“已对齐”或“部分对齐”；
  - `UX_UI_ALIGNMENT_PLAN.md` 标注了早期 gap 盘点仅作为基线说明，当前执行结果以 crosswalk + handoff regression 为准；
- [x] 已知限制已写清：
  - `docs/RELEASE_SUMMARY_STABLE.md` 概要说明了当前稳定边界与“不做”的范围；
  - `docs/KNOWN_LIMITS.md` 列出了 scene/page_type、模板/examples、UX/UI handoff 的具体已知限制与使用建议；
- [x] 当前默认运行模式已写清：
  - 在多个文档中明确当前处于 `Run-Phase1-ops`，以现有规则与模板为主，不主动扩建 scene/page_type/router；
  - 后续升级将通过新的 iteration / operation plan 立项，不混入本版。

## D. 风险层检查

- [x] 本轮收口没有引入新的结构性错误：
  - 结构调整主要为 assets 归档说明、文档归位与路径修正，未改动 scene/router/Guard 逻辑；
  - 新增的 `STRUCTURE_CLEANUP_CHECK`、`SKILL_ENTRY_REGRESSION`、`RELEASE_SUMMARY_STABLE`、`KNOWN_LIMITS`、本文件均为说明层，不改变真值源；
- [x] 当前没有必须立即继续扩张的未闭合主线：
  - 第二批模板修复、第二批 UX/UI 最小对齐、Phase 2 扩展与新增 scene 均明确标记为“当前版本不做”；
  - 剩余问题集中在 Known Limits 所列的“部分对齐”与灰区场景，可通过 observation 与轻量回填逐步收窄，不影响本版作为稳定起点使用。

---

## E. 一句话结论

在当前收口状态下，`lingjing-ui-core v3.0.0` 可以被视为一版 **结构干净、入口清晰、能力与边界均有说明、适合作为后续迭代基础的稳定版**；后续改动应通过新版本或新迭代来承载，而不是在本版中继续扩建。