# LingJing Core 迭代计划（执行版）

> 说明：本文面向仓库维护与版本迭代，主要服务于设计系统内部演进；若用于 AI 在用户项目中生成页面，请优先参考仓库根目录 `SKILL.md`。

## 1. 文档目标


本文档作为 `lingjing-core` 当前阶段的迭代指引，统一说明项目的版本路线、模块级任务、周排期、验收标准与执行优先级。

目标不是把 `lingjing-core` 做成一个通用 UI 组件库，而是把它升级为：

- 面向航空 AI 场景的可落地 UI Skill
- 具备稳定 CSS 架构的可维护样式系统
- 具备复合组件与可视化能力的场景化组件体系
- 能被 AI 稳定调用的技能包

---

## 2. 当前判断

### 2.1 已有优势

- 已具备明确的“智能航空”视觉定位
- 已形成 `website / b-system / presentation` 三类输出
- 已有一定基础组件、模板和设计令牌基础
- 已启动分层重构，具备继续收敛的条件

### 2.2 当前主要问题

1. **CSS 结构仍不稳定**
   - `components.css` 职责过重
   - 存在重复定义与职责交叉
   - 入口文件导入逻辑不够统一

2. **主题 token 体系不统一**
   - `--theme-*`、`--brand-*`、`--bg-*`、`--text-*` 混用
   - 存在未定义变量进入产物的问题
   - `design-tokens.csv` 与真实实现有漂移

3. **组件能力不完整**
   - 基础组件有一定覆盖，但复合组件不够
   - AI 助手场景组件不足
   - 航空场景专属组件不足

4. **可视化能力偏弱**
   - 缺少完整图表主题体系
   - 缺少驾驶舱/运营看板类复合模块

5. **技能包使用逻辑仍偏文档说明式**
   - `SKILL.md` 还不够场景化
   - 文档、示例、产物口径不统一

---

## 3. 迭代总目标

将 `lingjing-core` 从“有航空风格的样式技能包”升级为“面向航空 AI 场景的 UI Skill + 可视化组件体系”。

### 核心目标

1. **结构稳定**：CSS 分层明确、变量统一、入口清晰
2. **组件完整**：基础组件 + 复合组件 + AI 组件 + 航空组件
3. **可视化可用**：具备图表容器、图表主题、驾驶舱风格模块
4. **AI 易调用**：技能文档能稳定指导页面生成与组件选择
5. **交付一致**：`docs`、`examples`、`preview`、`dist` 统一对外口径

### 总体迭代顺序

1. 架构治理
2. 组件扩容
3. 可视化增强
4. 技能智能化与质量体系

---

## 4. 版本路线图

## 4.1 v3.1 架构收敛版

### 目标
先把底层稳定住，避免后续继续叠加技术债。

### 范围

- CSS 结构重组
- token 统一
- 样式引用统一
- 修复已知变量与入口风险
- 文档推荐入口统一

### 版本输出

- 稳定的分层 CSS 结构
- 统一的入口文件体系
- token alias 兼容层
- 修正后的 `dist`
- 统一的文档引用策略

### 核心任务

1. 完成 CSS 分层迁移
2. 拆解 `components.css`
3. 建立 token alias 层
4. 清理未定义变量
5. 统一 `docs / examples / preview / dist` 口径

---

## 4.2 v3.2 组件增强版

### 目标
把组件能力从“基础展示”升级到“可支撑项目”。

### 范围

- 丰富基础组件类型
- 增加 B 端复合组件
- 增加 AI 助手组件
- 增加航空专属组件

### 版本输出

- 更完整的组件目录
- 每个组件具备标准示例
- 组件在 light/dark 下可稳定使用
- AI 与航空场景适配能力增强

---

## 4.3 v3.3 可视化版

### 目标
建立 `lingjing-core` 的差异化能力。

### 范围

- 可视化容器组件
- 图表主题体系
- 航空驾驶舱组件
- 数据面板与监控模板

### 版本输出

- 灵境主题图表 preset
- 航空场景可视化组件
- 至少 2 套可视化页面模板

---

## 4.4 v3.0 技能化与质量版

### 目标
让项目从“资源包”升级为“AI 真会用的技能包”。

### 范围

- `SKILL.md` 场景化重构
- 预览工具重构
- 自动化检查
- 视觉回归与发版流程

### 版本输出

- 新版 `SKILL.md`
- 场景化技能逻辑
- 稳定的 `preview-tool`
- 可复用的质量检查流程

---

## 5. 模块级任务清单

## 5.1 模块 A：CSS 架构治理

### 目标
解决 `components.css` 过大、职责交叉、入口不统一的问题。

### 建议目录结构

```text
components/src/styles/
├── 01-foundation/
├── 02-components/
├── 03-layouts/
├── 04-themes/
└── 05-entry/
```

### 任务

#### A1. 组件层迁移
将旧平铺文件中的以下内容迁入 `02-components/`：

- `buttons`
- `forms`
- `data-display`
- `feedback`
- `navigation`
- `containers`

#### A2. 布局层迁移
将以下内容迁入 `03-layouts/`：

- `grid`
- `bento-grid`
- `layout-shell`
- `responsive`

#### A3. 拆分 `components.css`
建议拆分顺序：

1. `button`
2. `navigation`
3. `feedback`
4. `data-display`
5. `container/surface`
6. `grid utility`

#### A4. 保留兼容层
旧类名先保留兼容映射，不立刻删除。

### 完成标准

- `components.css` 不再承担新增职责
- 新组件全部进入新目录
- 入口文件只负责组合
- 现有示例不因迁移而损坏

---

## 5.2 模块 B：Token 与主题治理

### 目标
统一色值、背景、边框、半径、阴影、层级等语义变量。

### 任务

#### B1. 确立 token 主源
- 以 `variables.css` 或新 `tokens.css` 为真实实现主源
- `data/design-tokens.csv` 作为规范镜像，建议与真实实现保持同步


#### B2. 建立 alias 层
统一兼容以下变量体系：

- `--theme-*`
- `--brand-*`
- `--bg-*`
- `--text-*`
- `--radius-*`
- `--z-*`

#### B3. 修复当前高风险未定义变量
优先处理：

- `--theme-border-light`
- `--theme-bg-secondary`
- `--theme-bg-tertiary`
- `--bg-card-dark`
- `--shadow-dialog`
- `--z-tooltip`
- `--color-background-dark`
- `--border-radius-sm`
- `--border-radius-md`
- `--border-radius-lg`

#### B4. 对齐 light/dark 语义值
重点覆盖：

- 背景
- 表面层
- 边框
- 文本色
- 状态色
- 浮层阴影
- 图表容器背景

### 完成标准

- 未定义变量为 `0`
- 所有关键语义均有 light/dark 对应值
- 新组件原则上不再引入新的私有 token 体系

- `design-tokens.csv` 与真实实现一致

---

## 5.3 模块 C：基础组件扩容

### 目标
让 `lingjing-core` 从“能展示”变成“能做应用”。

### 建议优先组件

#### C1. 交互基础
- `drawer`
- `popover`
- `dropdown-menu`
- `segmented-control`
- `accordion`
- `stepper`

#### C2. 状态类
- `empty-state`
- `skeleton`
- `loading-block`
- `status-badge-group`

#### C3. 搜索与筛选
- `filter-bar`
- `search-suggestion`

### 完成标准

- 每个组件有独立样式文件
- 每个组件有标准示例
- 每个组件支持 light/dark
- 不依赖内联样式

---

## 5.4 模块 D：B 端复合组件

### 目标
补齐管理后台高频模块。

### 建议优先组件

- `advanced-data-table`
- `table-toolbar`
- `filter-panel`
- `batch-action-bar`
- `detail-panel`
- `status-timeline`
- `checklist-panel`
- `comparison-card`

### 完成标准

- 能组合出完整列表页
- B 端 demo 至少新增或升级 1 页
- 所有模块支持 light/dark

---

## 5.5 模块 E：AI 助手组件

### 目标
形成 `lingjing-core` 的核心差异化能力。

### 建议优先组件

- `chat-layout`
- `message-bubble`
- `assistant-panel`
- `tool-call-card`
- `agent-thinking-block`
- `citation-chip`
- `task-status-card`
- `response-section`
- `action-toolbar`
- `multi-panel-workspace`

### 设计要求

- 符合“航空 AI 助手”定位
- 支持步骤、结果、状态、引用混排
- 视觉上更像专业工作台，不像社交聊天窗口

### 完成标准

- 至少形成 1 个 AI 工作台 demo
- 可与表格、卡片、状态模块组合使用
- 全部支持 light/dark

---

## 5.6 模块 F：航空专属组件

### 目标
建立项目的垂直领域护城河。

### 建议优先组件

- `flight-metric-card`
- `route-leg-card`
- `mission-status-board`
- `alert-center-panel`
- `aircraft-state-card`
- `safety-score-card`
- `telemetry-strip`
- `ops-console-panel`

### 设计要求

- 高信息密度但不压迫
- 具备仪表盘/监控中心气质
- 统一灵境品牌视觉语言

### 完成标准

- 有独立示例
- 有页面级组合示例
- 不依赖外部图表库也能表达核心信息

---

## 5.7 模块 G：可视化体系

### 目标
补齐数据表达与驾驶舱风格能力。

### G1. 纯 CSS/HTML 可视化容器
优先实现：

- `chart-card`
- `metric-trend`
- `progress-ring`
- `bar-strip`
- `timeline-strip`
- `signal-matrix`
- `status-heat-grid`

### G2. 图表主题适配层
输出：

- `chart-theme-light`
- `chart-theme-dark`
- 灵境色板 preset
- `tooltip / legend / axis / gridline` 规范

### G3. 航空专属可视化
优先实现：

- `telemetry-gauge-group`
- `route-progress-strip`
- `mission-readiness-radar`
- `ops-alert-heatmap`
- `flight-path-panel`

### 完成标准

- 至少 2 个页面级可视化 demo
- 图表主题与卡片体系一致
- light/dark 下保持视觉统一

---

## 5.8 模块 H：SKILL 与文档体系

### 目标
让 AI 更稳定地调用 `lingjing-core`。

### 任务

#### H1. 重写 `SKILL.md`
建议结构：

1. 定位说明
2. 使用原则
3. 场景判断
4. 入口选择
5. 布局策略
6. 组件推荐
7. 可视化推荐
8. 禁止事项
9. 生成模板

#### H2. 增加场景分类
至少支持：

- `website`
- `b-system`
- `presentation`
- `ai-assistant`
- `ops-console`

#### H3. 增加页面组合范式
建议补齐：

- 营销首页
- 后台列表页
- 指标仪表盘
- AI 助手工作台
- 航空任务详情页

#### H4. 统一文档口径
对外默认推荐 `dist` 或项目内可直接接入的样式入口；对内维护再补充 `src/styles` 的说明。


### 完成标准

- 技能逻辑从“文件说明式”升级为“场景决策式”
- 文档引用统一
- AI 输出稳定性提升

---

## 5.9 模块 I：预览工具与示例体系

### 目标
让项目可查阅、可预览、可回归验证。

### 任务

#### I1. 重构 `tools/preview-tool.html`
要求：

- 只依赖正式 `dist`
- 不依赖未定义变量
- 支持场景切换
- 支持 light/dark 切换
- 支持组件分类浏览
- 支持复制标准示例代码

#### I2. 重构 `examples/`
建议按场景分类：

- `website`
- `b-system`
- `presentation`
- `ai-assistant`
- `ops-console`
- `visualization`

#### I3. 每阶段至少新增 1 个综合示例
建议优先：

- `ai-assistant-workspace.html`
- `ops-dashboard.html`

### 完成标准

- `preview` 成为正式的组件验收入口
- 示例能覆盖新增组件
- 示例和文档口径一致

---

## 5.10 模块 J：质量保障

### 目标
防止后续继续发生样式漂移和隐性破坏。

### 任务

#### J1. 静态检查
至少包括：

- 未定义 CSS 变量检查
- 重复 selector 检查
- 入口完整性检查
- `src` 与 `dist` 漂移检查

#### J2. 视觉回归
对关键页面做截图基线：

- 主题：`light / dark`
- 断点：`375 / 768 / 1280 / 1440`

#### J3. Smoke Test
重点验证：

- 主题切换
- `modal`
- `toast`
- `tooltip`
- `dropdown`
- 表格
- 导航
- 图表容器

### 完成标准

- 每次发版前可快速验收
- 样式破坏可被及时发现
- 主题问题不再依赖纯人工排查

---

## 6. 六周执行排期

## 第 1 周：架构稳定周

### 本周目标
完成底层治理，确保后续开发建立在稳定基础上。

### 本周任务

- 完成 `02-components/` 迁移方案
- 完成 `03-layouts/` 迁移方案
- 建立 token alias 层
- 清理未定义变量
- 统一入口文件导入顺序
- 修复文档入口不一致问题

### 本周交付

- 可工作的新版样式目录
- 可消费的 `dist`
- 核心示例不破坏

---

## 第 2 周：基础组件增强周

### 本周目标
补齐基础交互组件。

### 本周任务

- `drawer`
- `popover`
- `dropdown-menu`
- `segmented-control`
- `accordion`
- `empty-state`
- `skeleton`

### 本周交付

- 组件样式文件
- 对应示例页
- `preview` 中可查看

---

## 第 3 周：B 端与 AI 组件周

### 本周目标
补齐管理后台与 AI 工作台高频模块。

### 本周任务

- `advanced-data-table`
- `table-toolbar`
- `filter-panel`
- `detail-panel`
- `chat-layout`
- `message-bubble`
- `tool-call-card`
- `task-status-card`

### 本周交付

- B 端列表页 demo
- AI 工作台 demo 初版

---

## 第 4 周：航空专属组件周

### 本周目标
形成灵境的场景辨识度。

### 本周任务

- `flight-metric-card`
- `route-leg-card`
- `mission-status-board`
- `alert-center-panel`
- `telemetry-strip`
- `safety-score-card`

### 本周交付

- 航空任务页 demo
- 运营状态页 demo

---

## 第 5 周：可视化周

### 本周目标
补齐驾驶舱与图表能力。

### 本周任务

- `chart-card`
- `metric-trend`
- `progress-ring`
- `timeline-strip`
- 图表 `light/dark` preset
- `telemetry-gauge-group`
- `ops-alert-heatmap`

### 本周交付

- 1 个运营驾驶舱 demo
- 1 个指标监控 demo

---

## 第 6 周：技能与发布周

### 本周目标
完成项目的技能化整理与发版准备。

### 本周任务

- 重写 `SKILL.md`
- 重构 `preview-tool`
- 统一 `README / docs`
- 完成静态检查
- 完成视觉回归
- 准备稳定版发布

### 本周交付

- `v3.0` 稳定版
- 完整示例与文档
- 可持续维护的结构体系

---

## 7. 优先级管理

## P0：建议优先完成


- token 统一
- 未定义变量修复
- `components.css` 拆分
- 入口统一
- 文档口径统一

## P1：本轮核心价值

- 基础组件扩容
- B 端复合组件
- AI 助手组件
- 预览工具升级

## P2：建立差异化能力

- 航空专属组件
- 可视化主题
- 驾驶舱模板

## P3：长期能力建设

- 技能推理逻辑
- 自动化质量检查
- 视觉回归体系
- 页面组合模板库

---

## 8. 每阶段验收标准

## 8.1 v3.1 验收

- 未定义变量数量为 `0`
- 新旧入口关系清晰
- `examples` 无明显样式回退
- 文档统一推荐 `dist`

## 8.2 v3.2 验收

- 新增组件可独立展示
- 复合组件可拼装页面
- AI 与 B 端场景能力明显增强

## 8.3 v3.3 验收

- 图表容器与图表主题一致
- 至少具备 2 个驾驶舱/监控类页面
- 可视化符合灵境航空风格

## 8.4 v3.0 验收

- `SKILL.md` 可按场景指导生成
- `preview-tool` 可作为正式验收工具
- 发布前检查流程可重复执行

---

## 9. 推荐执行顺序

### 第一批立即启动

1. 完成 `v3.1`
2. 开始 `v3.2` 中的基础增强组件
3. 搭建 `preview-tool` 基础升级版

### 第二批跟进

1. B 端复合组件
2. AI 助手组件
3. 文档结构升级

### 第三批推进

1. 航空专属组件
2. 可视化组件
3. 驾驶舱模板

---

## 10. 项目管理建议

建议将任务拆分为 5 个主看板：

- 架构治理
- 组件扩容
- 航空场景
- 可视化体系
- 文档与质量

每个任务统一记录：

- 目标
- 输入文件
- 输出文件
- 依赖关系
- 验收方式

---

## 11. 结论

`lingjing-core` 下一阶段的关键，不是继续零散补样式，而是围绕“航空 AI 场景”完成三件事：

1. **先稳架构**
2. **再补复合组件**
3. **最后强化可视化驾驶舱能力**

只有这样，`lingjing-core` 才能真正从“有风格的技能包”进化为“可持续演进的航空 AI UI 能力底座”。

### 当前执行进度（v3.0.0，截止 2026-03-20）

- **总体版本**: 已完成迭代计划中的“第 6 周：技能与发布周”，形成 `v3.0.0 (Stable)` 稳定版。
- **本轮关键交付**:
  - 重写并场景化 `SKILL.md`，支持按场景进行样式入口与组件决策。
  - 重构 `tools/preview-tool.html`，作为正式的组件预览与验收入口。
  - 扩展 `scripts/component-generator.js`，支持航空/可视化等高级组件的生成。
  - 在样式与文档层面执行发版前的静态检查与视觉基线梳理。
- **文档口径**: `README.md` / `SKILL.md` / `ITERATION_GUIDE.md` 已统一到 v3.0 口径，早期围绕 v2.7.x / v3.0.0 的分析文档已全部标注为“历史文档”，仅作为背景参考。

