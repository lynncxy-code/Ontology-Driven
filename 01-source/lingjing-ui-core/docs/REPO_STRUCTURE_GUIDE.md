# REPO_STRUCTURE_GUIDE · 仓库结构导航说明

> 目标：让 AI 与维护者一进入仓库，就能快速区分“当前活入口 / 运行期文档 / 验证留档 / 历史归档 / 边缘资产”。

## 1. 根目录主入口

根目录现在只保留高频入口与机器真值源：

- `SKILL.md`：主执行协议
- `TRUTH_SOURCES.md`：真值源与优先级总览
- `README.md`：项目总览与快速开始
- `scene_coverage_matrix.yml`：场景 / Level 机器真值源
- `skill_version.json`：模板与资源分级索引
- `package.json`：脚本入口

其余高频目录：

- `docs/`：文档总入口与分层目录
- `examples/`：示例模板与演示资产
- `components/`：样式源码与 dist 产物
- `data/`：router / registry / 索引数据
- `scripts/`：审计脚本与运行时脚本
- `tools/`：预览工具
- `assets/`：品牌资源与已归档的根目录重复副本

## 2. `docs/` 新分层

### `docs/DOCS_STATUS_SUMMARY.md`
文档导航总入口。先看这里，再决定进入哪个子层。

### `docs/operations/`
当前仍在运行或会直接影响操作路径的文档：

- quickstart / first-read / playbook / guard / protocol
- 运行期总控与 observation cycle
- pre-release checklist

适用问题：
- 现在该按什么顺序读？
- 当前运行期主线是什么？
- stop&ask / guard / playbook 在哪里？

### `docs/reference/`
查表、地图、食谱、类名索引、最佳实践等参考层。

适用问题：
- 某个 page_type / template 应该看哪张地图？
- 某类名或组合食谱在哪里查？
- 某个实践建议是否已有沉淀？

### `docs/validation/`
验证、回归、复盘、observation 样例与归档后的生成报告。

- 正式 validation / regression / stresscheck
- observation 示例
- `generated-reports/`：从 `examples/**/audit-report.json` 归档过来的 JSON 报告

适用问题：
- 某场景是否验证过？
- 关键回归样本在哪？
- 之前的 audit 输出放在哪里？

### `docs/archive/`
历史过程稿、旧版本说明、归档笔记。

适用问题：
- 需要追溯旧版本思路时去哪里看？
- 某份历史分析是否仍保留？

默认原则：**archive 可查，但不应成为首读入口。**

## 3. `examples/` 的归属规则

`examples/` 仍按场景组织，但默认只把 canonical / registered limited 模板视为主链参考。

### 当前主链有效模板
- `examples/b-system/*.html` 中已登记 canonical
- `examples/ue5-overlay/*.html` 中已登记 canonical
- `examples/website/website-complete.html`

### 局部参考 / 特殊用途资产
- `examples/design-system/design-system-overview.html`：设计系统展示页
- `examples/shared/core-icon-library.html`：工具页
- `*showcase*.html`：demo / showroom

### 待观察资产
- `examples/b-system/aircraft-manufacturing-*.html`
- `examples/presentation/presentation-*.html`（当前仍按 draft 看待）

### 生成产物
- `examples/**/audit-report.json` 不再作为正式 examples 资产长期暴露
- 当前已归档到 `docs/validation/generated-reports/`
- 未来新生成的同名文件默认忽略，不作为结构导航入口

## 4. `assets/`、`scripts/`、vendor 与图片资源

### `assets/`
- `assets/logo-flat.png`、`assets/logo-reverse.png`：正式品牌资源
- `assets/logo_3d.png`：UE5 HUD 品牌资源
- `assets/ue5-bg-scene.png`：UE5 / 数字孪生默认背景图
- `assets/legacy-root-copies/`：根目录历史重复副本归档（仅保留历史副本与取证记录，不作为运行期资源引用目标）

本轮已完成 UE5 图片资源收口，并同步修复示例与样式引用路径。

### `scripts/`
`scripts/` 当前保留两类文件：

1. 仓库工具脚本
   - `skill-audit.js`
   - `run-phase1-regression.js`
   - `build-css.js`
   - `build-registry.js`
   - `show-task-router.js`
   - `show-template-router.js`

2. 浏览器运行时脚本 / vendor 依赖
   - `lucide-umd-500.js`
   - `echarts.min.js`
   - `echarts-theme-lingjing.js`
   - 其他被示例或工具页直接引用的运行时代码

> 为保持 `examples/` 与 `tools/preview-tool.html` 的现有相对路径不变，本轮**不把 vendor 文件物理迁出 `scripts/`**；仅在导航层明确其归属，避免把它们误当成仓库治理文档或 CLI 入口。

## 5. `memory/` 与归档笔记

原 `memory/` 目录已收口到：

- `docs/archive/memory/`

这类内容仅保留追溯价值，不再作为一级根目录入口。

## 6. 推荐阅读路径

### AI / 新维护者首读
`README.md` → `TRUTH_SOURCES.md` → `docs/DOCS_STATUS_SUMMARY.md` → `docs/operations/QUICKSTART_FOR_AGENT.md`

### 做运行期治理 / observation
`docs/operations/NEXT_STAGE_OPERATION_PLAN.md` → `docs/operations/MULTI_SCENE_OBSERVATION_CYCLE.md` → `docs/validation/`

### 查模板 / 类名 / 食谱
`docs/reference/` + `examples/README.md`

### 查历史背景
`docs/archive/`
