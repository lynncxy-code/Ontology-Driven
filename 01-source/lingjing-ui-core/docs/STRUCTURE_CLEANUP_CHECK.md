# 仓库结构整理尾项检查（Phase 1 收口）

> 范围：仅确认 `lingjing-ui-core` 结构整理尾项与引用是否已闭合；不新增 scene/page_type/router，不改治理结论。

## 1. assets 与 legacy-root-copies

- `assets/logo-flat.png` / `assets/logo-reverse.png` / `assets/logo_3d.png` / `assets/ue5-bg-scene.png` 已作为正式品牌与场景资源使用；
- `assets/legacy-root-copies/` 仅保留历史根目录图片副本与取证记录，已在 `docs/REPO_STRUCTURE_GUIDE.md` 中标注为归档目录，不作为运行期资源引用目标。

## 2. components 文档归位

- 原 `components/玻璃效果组件使用指南.md` 已移动至 `docs/reference/玻璃效果组件使用指南.md`，统一作为参考层文档；
- 当前无其它“说明类文档”遗留在源码目录根部。

## 3. scripts 与 vendor

- `scripts/` 仍统一承载仓库工具脚本与浏览器运行时脚本 / vendor 依赖；
- vendor 文件（`lucide-umd-500.js`、`echarts.min.js`、`echarts-theme-lingjing.js`）保持在 `scripts/` 下，以兼容现有 `examples/` 与工具页的相对路径；
- 相关归属说明已在 `docs/REPO_STRUCTURE_GUIDE.md` 与 `scripts/README.md` 中明确，本轮不做物理拆分。

## 4. examples 边缘资产归属

- `examples/README.md` 已明确区分 canonical / limited / demo / draft / blacklist / anti_pattern；
- `design-system-overview.html`、`core-icon-library.html`、`*showcase*.html`、`aircraft-manufacturing-*.html` 等边缘资产已标注归属与使用边界；
- `examples/**/audit-report.json` 已归档到 `docs/validation/generated-reports/`，不再作为结构入口。

## 5. 主入口与活文档路径

- 主入口：`README.md` / `SKILL.md` / `TRUTH_SOURCES.md` / `docs/operations/QUICKSTART_FOR_AGENT.md`；
- 运行期文档：`docs/operations/*.md`、`docs/reference/*.md`、`docs/validation/*.md`；
- 历史归档：`docs/archive/`、`docs/archive/memory/`；
- UX/UI handoff 关键入口位于 `lingjing-ux-core/docs/UX_UI_ALIGNMENT_PLAN.md`、`UX_UI_CROSSWALK.md`、`UX_UI_HANDOFF_REGRESSION.md`。

> 结论：结构层尾项（assets/legacy-root-copies、components 说明文档、scripts/vendor、examples 边缘资产）已闭合；当前未发现新的坏链或明显归属错误。