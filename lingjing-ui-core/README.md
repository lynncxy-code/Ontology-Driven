# 🎯 LingJing Core - AI开发技能包

> **版本**: v3.0.0（版本唯一真相源：`SKILL.md` frontmatter `metadata.version` 字段）
> **更新日期**: 2026-03-27
> **定位**: 面向航空 AI 场景的 UI Skill + 可视化组件体系
> **核心理念**: 场景驱动，内容优先，AI 原生

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](./SKILL.md)
[![Design System](https://img.shields.io/badge/design-system-brightgreen.svg)](./components/src/styles/01-foundation/variables.css)
[![Components](https://img.shields.io/badge/components-24-orange.svg)](./docs/reference/CLASS_NAME_REFERENCE.md)

---

## 🚀 快速开始

### 对于AI工具

**建议先读取主入口文件**：**[SKILL.md](SKILL.md)**

用户可只用一句简单指令触发本技能（如：`遵循灵境UI规范，完成xxx页面`）；约束执行、自检与回退说明应由技能包内部默认完成，不要求用户额外补充规则。

当任务明确属于 `b_system` 或 `ue5_overlay` 主线时，请先读 `SKILL.md` 的 `0.0 / 0.1 / 1.1 / 3.0 / 5.0`，再按 `0.1 按任务阅读顺序` 继续深读 `TRUTH_SOURCES.md`、对应 playbook 与 template map，避免把所有子文档一次性全量读完。

**30 秒执行卡（建议优先命中）**：
- 先对齐调用方项目结构与技术栈；
- 必须接入现有灵境样式入口（如需新增，仅可在标准规则之上按规范扩展）；
- 若可访问文件，按已验证路径执行：先 Read `1` 个模板 + `1` 个样式入口，并同步读取 `scene_coverage_matrix.yml` 后再 Write 到目标文件；
- CSS 只复制 `1` 个场景入口文件即可，不要自行重建整套样式；
- 先完成 `chosen_level` 判定：`Level 1 模板轻调 / Level 2 组件编排 / Level 3 规范扩展`；
- 优先命中 `ux_spec.component_roles[*].lingjing_core_class`，并将历史别名归一化为 canonical 类名；
- B 端顶部栏 + 左侧菜单、网站顶部栏属于框架层，必须强一致；UE5 Overlay 场景中仅 `ue5-overlay-root` / `ue5-overlay-viewport` / `ue5-overlay-safe-area` 属于全局骨架，HUD 等模块按模式按需配置；
- 若命中“验证 / 验收 / 复现 / 对标 / 跑通 / 检查技能包”，必须转入“先 UX 后 UI”的验证链路，优先消费已落盘的 `ux_spec`；
- 仅在确认不可读时回退“描述驱动生成”，并注明失败原因；
- 输出附 3 - 5 行摘要（样式入口/关键类/取证/资源落地路径/`chosen_level`）。

- `SKILL.md` 是当前版本唯一主执行协议，`scene_coverage_matrix.yml` 是机器判定真相源；若与其他文档冲突，以这两者为准；
- 推荐阅读顺序：`0.0 核心执行规约 -> 0.1 按任务阅读顺序 -> 1.1 场景最小矩阵 -> 3.0 三级策略 -> 5.0 质量清单 -> scene_coverage_matrix.yml`；
- `examples/` 用于结构参考与仓库内验证，不是外部项目默认落点；
- 输出时建议附 3 - 5 行结构化摘要，至少包含 `scene_id / chosen_level / template_match_score / missing_key_modules_count / retained_frame_shell`。

```
用户："基于灵境规范开发XX管理系统"
  ↓
AI：读取 SKILL.md
  ↓
AI：先判断调用方项目结构与技术栈
  ↓
AI：用当前环境可用的方式查看最接近的模板、样式入口与 `scene_coverage_matrix.yml`
  ↓
AI：先判定本次采用 `Level 1 / Level 2 / Level 3`，并锁定必须保持强一致的框架层
  ↓
AI：接入现有灵境样式入口，再按“模板轻调 / 组件编排 / 规范扩展”生成或更新可直接接入项目的页面层成果
  ↓
AI：顺带说明样式入口、关键组件类、少量补充样式/脚本、`chosen_level`，以及本次是否实际查看过技能包文件
```

### 对于开发者

1. **阅读指南**：[SKILL.md](SKILL.md) 与 [docs/DOCS_STATUS_SUMMARY.md](docs/DOCS_STATUS_SUMMARY.md)
2. **查看示例**：[examples/](examples/) 目录（用于结构参考与仓库内验证）
3. **选择策略**：先按 `scene_coverage_matrix.yml` 判定 `Level 1 / Level 2 / Level 3`；高匹配模板走 Level 1，没有直达模板但组件可承载时走 Level 2，模板与组件都不足时再进入 Level 3
4. **开始开发**：优先复用组件类与设计系统变量；B 端顶部栏 + 左侧菜单、网站顶部栏必须保持强一致；UE5 Overlay 仅强制 `ue5-overlay-root` / `ue5-overlay-viewport` / `ue5-overlay-safe-area` 外层骨架，HUD 等模块按场景按需使用；若确有必要扩展，也尽量保持最小增量并与现有风格一致；若在独立项目中接入，先确认样式资源已落到项目内且引用路径可访问

---

## 📁 项目结构

```
lingjing-ui-core/
├── SKILL.md                           ← 当前版本的主执行协议
├── TRUTH_SOURCES.md                   ← 真值源与优先级总览
├── README.md                          ← 本文件
├── scene_coverage_matrix.yml          ← 场景/Level 机器真值源
├── docs/
│   ├── DOCS_STATUS_SUMMARY.md         ← 文档导航总入口
│   ├── REPO_STRUCTURE_GUIDE.md        ← 仓库结构与资产归属说明
│   ├── operations/                    ← 运行期/护栏/playbook/操作文档
│   ├── reference/                     ← 地图、索引、查表、实践参考
│   ├── validation/                    ← 回归/验证/观测留档与生成报告
│   └── archive/                       ← 历史过程稿与归档笔记
├── examples/                          ← 仓库内示例与结构参考，不作为外部项目默认落点
├── components/                        ← 样式与组件源码/产物
├── data/                              ← JSON/CSV 真值与索引数据
├── scripts/                           ← 当前保留的审计脚本 + 浏览器运行时依赖
├── assets/                            ← 品牌资源、UE5 背景图与已归档的根目录副本
└── tools/                             ← 预览与辅助工具
```

---

## 🎯 核心特性

### ✅ 场景驱动开发
- **网站场景**：企业官网、营销网站、产品展示
- **B端场景**：管理系统、SaaS后台、ERP、CRM

### ✅ 组件库
- 覆盖B端系统和网站的常用场景
- 响应式布局，自动适配桌面、平板、移动端
- 深浅主题一键切换

### ✅ JavaScript效果
- 主题切换
- 侧边栏折叠（B端）
- 卡片涟漪效果
- Lucide图标自动初始化

### ✅ 框架兼容
- 支持纯HTML模式
- 支持React/Vue/Vite等框架模式
- **无论用什么技术栈，样式只使用灵境规范的类名**

---

## 📖 文档说明

### 核心文档（v3.0.0）
- **[SKILL.md](SKILL.md)** - 当前版本的主执行协议（版本唯一真值源）
- **[TRUTH_SOURCES.md](TRUTH_SOURCES.md)** - 真值源总览（版本/场景/模板/类名的权威来源说明）
- **[docs/DOCS_STATUS_SUMMARY.md](docs/DOCS_STATUS_SUMMARY.md)** - 文档导航与版本状态一览
- **[docs/REPO_STRUCTURE_GUIDE.md](docs/REPO_STRUCTURE_GUIDE.md)** - 仓库结构、资产归属与降噪后的入口说明
- **[docs/operations/QUICKSTART_FOR_AGENT.md](docs/operations/QUICKSTART_FOR_AGENT.md)** - 面向 AI 工具的 5 分钟起步卡
- **[docs/operations/CLAUDE_CODE_START_HERE.md](docs/operations/CLAUDE_CODE_START_HERE.md)** - Claude Code 进入本仓库的首要入口

### 运行与规则主链（Phase 1 优先）
- **[docs/operations/ROUTING_DECISION_PROTOCOL.md](docs/operations/ROUTING_DECISION_PROTOCOL.md)** - 场景 → 模板 → Level 的决策协议
- **[docs/operations/EXTENSION_GUARD.md](docs/operations/EXTENSION_GUARD.md)** - stop&ask 与扩展护栏
- **[docs/operations/b-system-layout-playbook.md](docs/operations/b-system-layout-playbook.md)** - `b_system` 布局决策卡
- **[docs/operations/ue5-overlay-layout-playbook.md](docs/operations/ue5-overlay-layout-playbook.md)** - `ue5_overlay` 布局决策卡
- **[docs/reference/system-template-map.md](docs/reference/system-template-map.md)** - `b_system`：类型 → 模板 → Level → Shell → 常见误用
- **[docs/reference/ue5-template-map.md](docs/reference/ue5-template-map.md)** - `ue5_overlay`：布局模式 → 模板 → Level → Layer → 常见误用

> 当前 Phase 1 优先深做场景：`b_system` 与 `ue5_overlay`；`website` / `presentation` / `ai_assistant` 在本版中保持兼容可用，但不作为治理与中间层建设的主线场景。

### 参考与留档（按需阅读）
- **[examples/](examples/)** - 仓库内示例与结构参考
- **[docs/reference/CLASS_NAME_REFERENCE.md](docs/reference/CLASS_NAME_REFERENCE.md)** - 类名参考清单
- **[docs/reference/BEST_PRACTICES.md](docs/reference/BEST_PRACTICES.md)** - 常见问题与实践建议
- **[docs/reference/CODE_SNIPPETS.md](docs/reference/CODE_SNIPPETS.md)** - 代码片段库
- **[docs/validation/](docs/validation/)** - 回归/验证/观测留档
- **[docs/archive/](docs/archive/)** - 历史过程稿与归档文档

---

## 📄 许可证

MIT License

---

**最后提醒**：如果是实际项目接入，请先读 [SKILL.md](SKILL.md) 与 `scene_coverage_matrix.yml`；落地时宜先对齐调用方项目结构，再接入现有灵境样式入口并完成 `chosen_level` 判定；B 端顶部栏 + 左侧菜单、网站顶部栏必须保持框架层强一致；UE5 Overlay 仅强制外层骨架（`ue5-overlay-root` / `ue5-overlay-viewport` / `ue5-overlay-safe-area`），HUD 等模块按模式与需求选用。若需要补充结构参考，再按需查看 `examples/`、类名清单和最佳实践文档，并顺手确认样式入口、关键布局壳、模块骨架与核心组件类是否真实命中。 

