# LingJing Core 高风险文件与首批改造顺序清单

## 1. 文档目的

本文档用于指导 `lingjing-core` 在正式进入 `v3.1` 架构收敛阶段前，优先识别高风险文件，并按低风险、可回退、可验证的顺序推进首批改造。

本文档聚焦两件事：

1. 明确哪些文件是首轮迭代中的高风险点
2. 明确第一批改造的推荐顺序，避免一上来改动过深导致样式回归不可控

---

## 2. 使用原则

首批改造遵循以下原则：

- **先修基础，再动组件**
- **先统一 token，再拆分样式**
- **先修入口，再扩功能**
- **先保兼容，再做替换**
- **每完成一批都能通过现有 `examples` 验证**

本阶段目标不是新增大量组件，而是确保后续扩展建立在稳定基础上。

---

## 3. 风险等级定义

### P0：极高风险
满足以下任一条件：

- 影响多个场景入口
- 影响全局 token 或主题切换
- 已进入 `dist` 产物
- 容易导致整站大面积样式回退

### P1：高风险
满足以下任一条件：

- 被多个 demo / 文档依赖
- 与旧体系、新体系存在职责重叠
- 修改后易引发局部大范围回归

### P2：中风险
满足以下任一条件：

- 影响单一模块或单一组件类别
- 有替代方案或可局部回退
- 对整体结构影响较小

---

## 4. 首批高风险文件清单

## 4.1 P0：极高风险文件

### 1) `components/src/styles/variables.css`

**风险等级：P0**

**原因：**
- 承担全局设计令牌与主题变量定义
- 直接影响 light / dark 主题
- 当前已发现实现值与 `design-tokens.csv` 存在漂移
- 多个组件依赖该文件中的 token

**主要风险：**
- 修改后会影响按钮、卡片、表格、导航、反馈等几乎全部组件
- 若变量名调整不兼容，会直接导致 `dist` 中大量样式失效

**首轮处理建议：**
- 不直接大改原有变量命名
- 优先补齐缺失语义与 alias 映射
- 先做兼容，不做激进清理

---

### 2) `components/src/styles/index.css`

**风险等级：P0**

**原因：**
- 被文档误认为“完整公共入口”
- 当前导入内容并不完整
- 导入顺序与其他入口不完全一致

**主要风险：**
- 修改后可能影响文档示例、内部预览与维护逻辑
- 若直接重构而不处理口径，会继续制造入口认知混乱

**首轮处理建议：**
- 优先明确其定位：维护入口 / 聚合入口，而非对外推荐入口
- 补齐注释与说明
- 与场景入口统一导入规则

---

### 3) `components/src/styles/index-website.css`

**风险等级：P0**

**原因：**
- 对应网站场景正式产物
- 影响 `website` 类 demo 与最终 `dist`

**主要风险：**
- 导入顺序变更可能导致覆盖关系变化
- 若迁移组件后入口未同步，会出现样式缺失

**首轮处理建议：**
- 仅做导入顺序治理与缺失文件接入
- 暂不进行大规模场景样式重写

---

### 4) `components/src/styles/index-b-system.css`

**风险等级：P0**

**原因：**
- 对应 B 端场景正式产物
- 当前大量组件与中后台页面依赖该入口

**主要风险：**
- B 端页面组件密度高，局部问题更容易扩大
- 表格、表单、导航等高度依赖 token 和导入顺序

**首轮处理建议：**
- 优先确保表格、表单、导航、反馈链路稳定
- 所有新拆分组件必须在此入口逐项校验

---

### 5) `components/src/styles/index-presentation.css`

**风险等级：P0**

**原因：**
- 对应演示场景正式产物
- 属于当前已交付的标准入口之一

**主要风险：**
- 若入口维护时遗漏演示场景，容易形成“网站/B 端正常，演示页异常”的隐性问题

**首轮处理建议：**
- 将其纳入与其他入口同级的统一校验范围
- 每次入口变更后必须联动验证

---

### 6) `components/dist/lingjing-core-website.css`
### 7) `components/dist/lingjing-core-b-system.css`
### 8) `components/dist/lingjing-core-presentation.css`

**风险等级：P0**

**原因：**
- 这是对外交付物
- 当前 `examples` 主要直接引用 `dist`
- 已发现未定义变量已进入产物

**主要风险：**
- 如果 `src` 修好了但 `dist` 未同步，对外依然是坏的
- 可能导致“源码看起来对，实际使用仍异常”

**首轮处理建议：**
- 每一批改动结束都必须重新核对 `dist`
- 将 `dist` 验证视为与源码验证同等优先级

---

## 4.2 P1：高风险文件

### 9) `components/src/styles/components.css`

**风险等级：P1（接近 P0）**

**原因：**
- 文件体量大、职责混杂
- 包含基础组件、导航、反馈、部分工具类等多类样式
- 与新拆分文件存在重复定义与职责交叉

**主要风险：**
- 贸然拆分很容易导致旧 demo 大面积回退
- 难以快速识别哪些选择器已被独立文件接管

**首轮处理建议：**
- 先标记职责边界，再逐块迁移
- 不要一次性大拆
- 迁移一类，验证一类

---

### 10) `components/src/styles/navigation-components.css`

**风险等级：P1**

**原因：**
- 与 `components.css` 中导航类定义重叠
- 使用了部分未统一语义变量

**主要风险：**
- 导航类组件极易受到覆盖顺序影响
- 拆分后可能出现 hover / active / dark 模式错乱

**首轮处理建议：**
- 先建立导航类的唯一归属
- 确认保留文件与兼容策略后再迁移

---

### 11) `components/src/styles/feedback-components.css`

**风险等级：P1**

**原因：**
- 与 `components.css`、`modal-dialog.css`、`toast.css` 相关职责交叉
- 同时存在两套反馈类 API 风格

**主要风险：**
- alert / toast / modal 命名与视觉逻辑容易分裂
- 若不先做统一规划，后续维护成本会继续上升

**首轮处理建议：**
- 先统一反馈组件命名策略
- 再合并 alert / toast / modal 相关结构

---

### 12) `components/src/styles/forms-b.css`

**风险等级：P1**

**原因：**
- B 端表单与表格密集使用
- 已发现使用未定义变量的情况

**主要风险：**
- 表格边框、文本层级、行高、状态样式易出回归
- 是 B 端场景最敏感的文件之一

**首轮处理建议：**
- 优先修复变量引用
- 暂不调整复杂布局与结构样式

---

### 13) `components/src/styles/theme-switcher.css`

**风险等级：P1**

**原因：**
- 直接关系到 light / dark 切换体验
- 已发现使用未定义变量并进入 `dist`

**主要风险：**
- 会导致主题切换器显示异常或 tooltip 异常
- 容易影响预览工具和示例页

**首轮处理建议：**
- 先修 token 引用
- 再检查位置层级、浮层背景、交互提示样式

---

### 14) `tools/preview-tool.html`

**风险等级：P1**

**原因：**
- 是当前最直接的人工验收入口之一
- 既依赖 `dist`，又写了大量内联 `<style>`
- 还依赖若干未定义变量

**主要风险：**
- 它可能掩盖真实问题，也可能制造额外问题
- 若不先治理，后续会成为错误的“验收基准”

**首轮处理建议：**
- 明确其角色：消费正式产物，而不是自己补一套变量体系
- 首轮先修依赖与变量问题，不做复杂功能扩展

---

### 15) `SKILL.md`

**风险等级：P1**

**原因：**
- 是 AI 使用技能包的核心入口
- 当前对入口说明与实际实现存在漂移

**主要风险：**
- 若不先修正文档，AI 仍会走错误入口或使用错误方式
- 会持续放大实现与使用之间的不一致

**首轮处理建议：**
- 首轮只修正入口口径与使用原则
- 深度场景化重构放到 `v3.0`

---

### 16) `README.md`

**风险等级：P1**

**原因：**
- 代表项目对外说明
- 当前结构说明与当前产物状态可能不完全一致

**主要风险：**
- 会导致使用者采用旧结构理解项目
- 影响后续协作与维护成本

**首轮处理建议：**
- 首轮只修结构说明与入口说明
- 不在本轮扩写过多未来能力描述

---

## 4.3 P2：中风险文件

### 17) `components/src/styles/modal-dialog.css`
### 18) `components/src/styles/toast.css`
### 19) `components/src/styles/tooltip.css`
### 20) `components/src/styles/dropdown-menu.css`
### 21) `components/src/styles/grid-system.css`
### 22) `components/src/styles/bento-grid.css`
### 23) `components/src/styles/data-display.css`
### 24) `components/src/styles/advanced-components.css`

**风险等级：P2**

**原因：**
- 影响特定组件或特定场景
- 有些存在入口未接入、语义变量混乱或与其他文件职责交叉的问题

**首轮处理建议：**
- 纳入专项校验
- 在 P0/P1 文件稳定后再逐个纳入重构节奏

---

## 5. 首批改造总策略

首批改造不追求“大重构一次完成”，而采用以下节奏：

### 阶段 1：先修“真源”
优先处理 token、入口、产物同步问题。

### 阶段 2：再修“重复职责”
优先解决 `components.css` 与拆分文件之间的重叠关系。

### 阶段 3：最后修“使用口径”
统一 `README`、`SKILL.md`、`preview-tool` 的对外说明与使用方式。

---

## 6. 首批改造推荐顺序

以下顺序按“风险控制优先”设计，建议严格执行。

## Step 1：锁定基线与验证入口

### 处理对象
- `examples/*.html`
- `tools/preview-tool.html`
- `components/dist/*.css`

### 要做的事
- 记录当前核心 demo 的可展示状态
- 固定一版视觉基线截图
- 明确后续主要验收页

### 目标
确保后续每一批改动都有对照参考。

---

## Step 2：处理全局 token 真源

### 处理对象
- `components/src/styles/variables.css`
- 未来新增的 token alias 层文件
- `data/design-tokens.csv`

### 要做的事
- 梳理当前 token 实际定义与实际使用
- 补齐高风险缺失变量
- 建立 alias 映射，而不是立即删除旧语义
- 标记设计规范漂移项

### 目标
让变量系统先“可用且不炸”，再谈进一步收敛。

### 不建议此时做的事
- 大范围重命名现有 token
- 一次性清空旧 token
- 一步到位重写整套主题系统

---

## Step 3：统一入口文件导入秩序

### 处理对象
- `components/src/styles/index.css`
- `components/src/styles/index-website.css`
- `components/src/styles/index-b-system.css`
- `components/src/styles/index-presentation.css`

### 要做的事
- 统一导入层级顺序
- 明确哪些是基础层、组件层、布局层、主题层、场景层
- 明确 `index.css` 是维护入口还是公共入口
- 补齐遗漏或冗余接入

### 目标
确保覆盖关系可预测。

### 验收重点
- 同类组件在不同入口下展示一致
- 无“某入口有样式、另一入口没样式”的情况

---

## Step 4：修复主题切换与关键变量消费点

### 处理对象
- `components/src/styles/theme-switcher.css`
- `components/src/styles/forms-b.css`
- `components/src/styles/modal-dialog.css`
- `components/src/styles/toast.css`
- `components/src/styles/navigation-components.css`
- `components/src/styles/feedback-components.css`

### 要做的事
- 先修未定义变量引用
- 再检查 dark 模式下背景、边框、阴影、文本是否可用
- 对关键浮层组件做重点验证

### 目标
先消除现有“明显会坏”的问题。

---

## Step 5：拆解 `components.css` 的职责边界

### 处理对象
- `components/src/styles/components.css`
- 对应的新组件层文件

### 推荐拆分顺序
1. `button`
2. `navigation`
3. `feedback`
4. `data-display`
5. `surface/container`
6. `grid utility`

### 要做的事
- 先建立职责表
- 一类一类迁移
- 每迁移一类都立即在 `website / b-system / presentation` 验证
- 旧选择器先保兼容

### 目标
在不破坏现有 demo 的前提下，把“大杂烩文件”逐步拆小。

---

## Step 6：统一文档与使用口径

### 处理对象
- `SKILL.md`
- `README.md`
- `docs/*`
- `tools/preview-tool.html`

### 要做的事
- 对外统一推荐 `dist`
- 对内维护再说明 `src/styles`
- 删除或修正错误入口示例
- 修正文档中与官方规范冲突的样式示例

### 目标
避免继续制造“文档指导错误”。

---

## Step 7：核对 `dist` 与正式示例

### 处理对象
- `components/dist/*.css`
- `examples/*.html`

### 要做的事
- 对照源码变更核查 `dist`
- 检查 demo 是否真实引用最新正式产物
- 验证 light / dark 与关键场景页

### 目标
保证交付物可真实使用，而不是只停留在源码层面“理论正确”。

---

## 7. 不建议的首轮改造顺序

以下做法在首轮不推荐：

### 不建议 1：先大规模新增组件
原因：基础不稳时新增组件，只会把问题扩散到更多文件。

### 不建议 2：先重写 `SKILL.md`
原因：如果底层入口、变量、结构还没稳定，技能文档会再次很快过时。

### 不建议 3：先大改 `preview-tool`
原因：若核心 `dist` 仍不稳定，先做预览工具功能重构价值不高。

### 不建议 4：直接删除旧类名或旧文件
原因：当前项目依赖链复杂，删除会带来不可控回归。

### 不建议 5：先推进复杂可视化模块
原因：可视化建立在稳定的 token、surface、card、theme 之上，不应倒序进行。

---

## 8. 首轮文件处理批次建议

## 批次 A：必须先动

- `components/src/styles/variables.css`
- `components/src/styles/index.css`
- `components/src/styles/index-website.css`
- `components/src/styles/index-b-system.css`
- `components/src/styles/index-presentation.css`
- token alias 层文件（新增）

**目标：** 先把全局基础打稳。

---

## 批次 B：紧接着处理

- `components/src/styles/theme-switcher.css`
- `components/src/styles/forms-b.css`
- `components/src/styles/navigation-components.css`
- `components/src/styles/feedback-components.css`
- `components/src/styles/modal-dialog.css`
- `components/src/styles/toast.css`

**目标：** 先消除当前可见故障点。

---

## 批次 C：随后推进

- `components/src/styles/components.css`
- `components/src/styles/data-display.css`
- `components/src/styles/advanced-components.css`
- `components/src/styles/grid-system.css`
- `components/src/styles/bento-grid.css`

**目标：** 做职责拆解与结构收敛。

---

## 批次 D：最后对齐说明层

- `SKILL.md`
- `README.md`
- `docs/*`
- `tools/preview-tool.html`

**目标：** 统一对外口径与维护说明。

---

## 9. 每批次改造的最低验收要求

每完成一个批次，至少执行以下检查：

### 视觉检查
- `website-complete.html`
- `b-system-complete.html`
- `presentation-product.html`
- `preview-tool.html`

### 主题检查
- light
- dark

### 核心模块检查
- button
- card
- table
- navigation
- modal
- toast
- tooltip
- theme-switcher

### 结构检查
- 是否存在未定义变量
- 是否存在入口遗漏
- 是否出现 `dist` 未同步
- 是否出现重复定义继续扩大

---

## 10. 首轮完成标准

当以下条件同时满足，可视为首轮准备完成，可以进入后续组件扩容阶段：

1. token 真源与 alias 关系已建立
2. 高风险未定义变量已清理
3. 四类入口文件导入逻辑已统一
4. `dist` 与 `src` 一致
5. 核心 demo 在 light / dark 下可稳定展示
6. `README`、`SKILL.md`、`docs` 不再继续推荐错误入口
7. `components.css` 已明确进入“逐步拆解、不再继续扩写”的状态

---

## 11. 结论

`lingjing-core` 的首轮改造，正确顺序不是“先做新东西”，而是：

1. **先稳 token**
2. **再稳入口**
3. **再修关键故障点**
4. **再拆 `components.css`**
5. **最后统一文档口径**

只有按这个顺序推进，后续的组件扩容、AI 场景组件和可视化体系建设，才不会建立在不稳定的基础上。

