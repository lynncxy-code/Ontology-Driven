# scripts/ 目录说明

> 目的：说明 `scripts/` 当前存放的脚本类型，避免把浏览器运行时依赖、审计脚本与构建脚本混为一谈。

## 1. 当前分类

### A. 仓库工具脚本

- `skill-audit.js` — HTML 审计入口
- `run-phase1-regression.js` — Phase 1 回归批量执行
- `build-css.js` — 构建 dist CSS
- `build-registry.js` — 从 dist CSS 重建 `data/class_registry.json`
- `show-task-router.js` — 查看 `data/task_router.json`
- `show-template-router.js` — 查看 `data/template_router.json`

### B. 浏览器运行时 / vendor 依赖

- `lucide-umd-500.js` — 图标运行时
- `echarts.min.js` — ECharts 运行时
- `echarts-theme-lingjing.js` — ECharts 灵境主题注册
- `presentation-template.js` — presentation 示例页脚本
- `component-generator.js` — 预览工具/示例用运行时代码

### C. 历史/低频模板脚本

- `interactions-template.js`
- `b-interactions-template.js`

这两份仍保留以便追溯，但不属于当前 Phase 1 主线入口。

## 2. 为什么 vendor 仍在 `scripts/`

本轮没有把 `lucide-umd-500.js`、`echarts.min.js` 等文件物理迁到 `vendors/`，原因是：

- `examples/` 与 `tools/preview-tool.html` 仍直接使用 `../scripts/...` 或 `../../scripts/...` 相对路径；
- 本轮目标是**降噪与归属澄清**，不是修改 HTML / CSS 运行路径。

因此当前策略是：

- 在导航层明确 `scripts/` 内的不同角色；
- 保持现有相对路径兼容；
- 等未来如需统一 vendor 目录，再与模板路径改造一起处理。

## 3. 高频命令

```bash
npm run audit
npm run audit:phase1-regression
npm run build:css
npm run show:task-router
npm run show:template-router
```

## 4. 相关文档

- [`../README.md`](../README.md) — 项目总览
- [`../TRUTH_SOURCES.md`](../TRUTH_SOURCES.md) — 真值源与优先级
- [`../docs/DOCS_STATUS_SUMMARY.md`](../docs/DOCS_STATUS_SUMMARY.md) — 文档导航入口
- [`../docs/reference/CLASS_NAME_REFERENCE.md`](../docs/reference/CLASS_NAME_REFERENCE.md) — 类名索引
- [`../docs/REPO_STRUCTURE_GUIDE.md`](../docs/REPO_STRUCTURE_GUIDE.md) — 仓库结构与资产归属说明
