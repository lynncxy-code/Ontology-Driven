# OntoTwin 3.5.1 Runtime Editor 交互优化 (PRD)

> 状态：开发完成，待 PIE 视觉与交互验收
> 主线：OntoTwin Nexus / UE Runtime / OntoTwinSync 插件
> 日期：2026-07-13
> 目标版本：3.5.1
> 前置版本：3.5 Runtime Editor MVP

---

## 1. 背景

3.5 已完成 Runtime Editor 的最小编辑闭环，但当前界面和 gizmo 仍带有明显的工程验证痕迹：

- 面板字号、信息密度和占屏面积失衡，长实例 ID 会挤压布局。
- `Binding: error`、`Dirty edit` 等内部状态直接暴露给用户，缺少可执行的下一步。
- 保存、取消、绑定和吸附控件缺少清晰层级，复选框没有对应标签。
- gizmo 的选择框、旋转环、朝向箭头和拖拽手柄尺寸过大，颜色和线宽缺少状态层级。
- gizmo 只有选中态，没有 hover、拖拽和吸附反馈，用户难以判断当前会执行移动还是旋转。
- 当前调试绘制方式容易让 gizmo 与场景中的灰色占位模型混淆。

3.5.1 的目标是把现有能力整理成可交付的产品交互，同时保持 3.5 的数据流、编辑边界和保存语义不变。

---

## 2. 产品目标

用户进入 Runtime Editor 后，应能在不阅读技术状态码的情况下完成以下任务：

1. 确认当前数据集是否允许本 UE 工程保存。
2. 识别当前选中的设备及其空间状态。
3. 明确区分 XY 移动和 Yaw 旋转手柄。
4. 在 hover、拖拽、吸附和保存过程中持续获得即时反馈。
5. 保存成功、保存失败或取消后，始终知道当前变更是否仍未提交。

设计原则：

- **工具化而非调试化**：隐藏内部状态码，界面只呈现用户任务和下一步操作。
- **克制的黑白灰**：面板以黑、白、灰构建层级；语义色只用于小面积状态点、提示和 gizmo。
- **稳定布局**：长 ID、状态变化和按钮 loading 不得改变面板宽度；高度可随内容安全扩展，不得裁切控件。
- **直接操控**：hover 先提示操作类型，按下后才进入拖拽；松开立即结束拖拽。
- **可逆**：保存失败保留本地未保存状态；取消恢复本次编辑前 Transform。
- **插件自包含**：安装 OntoTwinSync 插件即可获得该能力，不依赖宿主项目手工制作 UMG 或 gizmo 资产。

---

## 3. 范围

### 3.1 本轮做

- 重构 Runtime Editor C++ UMG 面板的视觉层级、尺寸、文案和控件状态。
- 将技术性的 Binding 状态转换成面向用户的“数据集访问状态”。
- 为绑定检查失败提供 `Retry`，为未绑定状态保留 `Bind active dataset`。
- 选中实例优先显示设备名称，实例 ID 截断显示并保留完整值供内部使用。
- 将 Transform 从单行文本改为固定的 2×2 数值区：X、Y、Z、Yaw。
- 为保存、取消、绑定、吸附提供明确的可用、禁用、loading 和结果反馈。
- 重做 gizmo 的尺寸、颜色、线宽和手柄比例，并增加世界 Z 轴移动。
- 增加 gizmo hover、active drag、吸附命中三类交互状态。
- gizmo 保持相对稳定的屏幕视觉尺寸，避免远近镜头下过大或过小。
- 扩大透明拾取区域，但不扩大可见图形，提高点击成功率。
- 用短时非阻塞 toast 显示保存、取消和错误结果。
- 保持纯 Runtime 实现，可用于 PIE 和打包 exe。

### 3.2 本轮不做

- 保留 3.5 的 XY 平移、Yaw 旋转、墙吸附和网格吸附规则；Z 从“保持不变”升级为显式手柄移动。
- 不新增 Pitch、Roll、Scale、多选、Undo/Redo。
- 不新增或修改后端接口、ProjectStore 字段和 JSON 存储结构。
- 不切换后端当前激活数据集。
- 不修改实例实际模型的加载和占位模型策略。
- 不制作需要用户在 UE Editor 中手工绑定的 Widget Blueprint。
- 不要求用户手工创建材质、图标、输入映射或关卡 Actor。
- 不引入完整设计系统、MVVM 框架或新的插件级子系统。

---

## 4. 归属与工程边界

Runtime Editor 是 **OntoTwinSync 插件能力**，不是 `test0316` 项目功能。

唯一源码位置：

```text
ue_project/Plugins/OntoTwinSync/
```

职责边界：

| 位置 | 职责 | 3.5.1 是否修改 |
| :-- | :-- | :-- |
| `OntoTwinSync/Source/OntoTwinSync/` | Runtime Editor 正式实现 | 是 |
| `OntoTwinSync/Content/` | 插件可选通用资产 | 默认不新增 |
| `test0316/Plugins/OntoTwinSync/` | 本地验证时同步的插件副本 | 仅同步验证 |
| `test0316/Source/test0316/` | 宿主项目业务代码 | 否 |
| `test0316/Content/*.umap` | 宿主项目关卡 | 否 |

验收时可以把插件源码同步到 `test0316/Plugins/OntoTwinSync`，但不得在测试工程内形成独立分支实现。其他 UE 项目安装同一版本 OntoTwinSync 插件后，应获得相同 Runtime Editor。

---

## 5. 面板设计

### 5.1 布局

默认停靠左上角，距安全区左侧和顶部各 24 px。100% DPI 下外框宽 400 px、最小高度 306 px；允许随 UE DPI 缩放，高度由内容自适应，任何按钮不得溢出或被裁切。

```text
┌────────────────────────────────────────┐
│ Runtime Editor              Unsaved  × │
│                                        │
│ DEVICE                                 │
│ Forklift 04                            │
│ ue_94C56...4CC51                       │
│                                        │
│ X       -528.1    Y      -1604.0       │
│ Z          0.0    Yaw        0.0       │
│                                        │
│ DATASET ACCESS                         │
│ ● Ready                                │
│                                        │
│ □ Wall snap          □ Grid snap       │
│                                        │
│ [ Cancel ]              [ Save changes ]│
└────────────────────────────────────────┘
```

说明：

- `×` 代表关闭编辑模式的熟悉图形命令；hover 时显示 `Close editor` tooltip。
- 有未保存变更时，关闭操作遵循 3.5 规则：阻止退出，并在面板内提示先保存或取消。
- 面板不常驻显示快捷键说明，避免把产品界面做成调试帮助页。
- 无选中实例时保持相同外框，仅将设备区显示为 `No instance selected`，Transform 显示 `-`。

### 5.2 视觉 Token

面板视觉沿用 OntoTwin 极简黑白灰规范，在 C++ 中以局部常量集中定义，不新增全局主题系统：

| 用途 | 建议值 |
| :-- | :-- |
| 面板背景 | `rgba(20,20,20,0.92)` |
| 主文字 | `#F5F5F5` |
| 次文字 | `#A3A3A3` |
| 分隔线 | `rgba(255,255,255,0.10)` |
| hover 背景 | `rgba(255,255,255,0.08)` |
| 禁用透明度 | `0.40` |
| 圆角 | 6 px；只用于面板、按钮和 toast |
| 外边距 | 16 px |
| 区块间距 | 12 px |
| 控件间距 | 8 px |
| 标题字号 | 16 px / Semibold |
| 正文字号 | 13 px |
| 辅助字号 | 11 px |

面板不使用大面积红、绿、黄背景。成功、警告、错误只通过 6 px 状态点、短文本或 2 px toast 左边线表达。

### 5.3 信息层级

设备信息：

- 第一行优先使用实例 `DisplayName`；为空时使用类型名；再次为空时使用 `Twin instance`。
- 第二行显示截断实例 ID：前 8 位 + `...` + 后 5 位。
- 不允许长 ID 挤压按钮或撑宽面板。

空间信息：

- X、Y、Z、Yaw 使用固定宽度 2×2 网格。
- 数值保留 1 位小数；位置单位沿用 UE cm，不在每个值后重复显示单位。
- 本轮为只读展示，不增加文本框直接输入。

状态信息：

- 标题右侧只显示一个最高优先级状态：`Saving` > `Unsaved` > `Editing`。
- 未保存使用小面积警告色；保存中使用中性色并禁用所有编辑命令。
- 底部不常驻显示成功文本，成功和失败使用 toast。

### 5.4 数据集访问状态

用户界面不再直接显示 `Binding: error` 等内部值。

| 内部状态 | 用户文案 | 状态点 | 操作 |
| :-- | :-- | :-- | :-- |
| `checking` | `Checking access` | 灰 | 按钮 loading，禁止保存 |
| `matched` | `Ready` | 绿 | 无额外操作 |
| `unbound` | `Not bound` | 黄 | `Bind active dataset` |
| `ue_project_mismatch` | `Bound to another UE project` | 红 | 禁止保存 |
| `error` / `unknown` | `Unable to verify` | 红 | `Retry` |

`Binding` 的业务含义仍是“后端当前激活数据集与 UEProjectId 的归属关系”，但该技术解释不常驻占用面板。3.5.1 不新增数据集名称接口；后端未返回名称时不伪造或猜测数据集信息。

### 5.5 控件

按钮层级：

- `Save changes`：唯一主按钮，黑白高对比；仅在有 dirty、访问状态为 `matched` 且未保存中时可用。
- `Cancel`：次按钮；仅在有 dirty 时可用，执行后恢复本次编辑基线。
- `Retry` / `Bind active dataset`：按数据集访问状态出现在状态区，不与保存按钮争夺主操作层级。
- `Close editor`：标题栏图形命令；dirty 时不直接关闭。

吸附开关：

- 使用带文字标签的 checkbox/toggle，不再显示两个无标签原生方框。
- `Wall snap` 默认开启，`Grid snap` 默认关闭，与 3.5 配置一致。
- 切换后立即生效，不弹确认框。

### 5.6 Toast

toast 位于面板右侧上方或视口右上安全区，持续 2.5 秒，不阻断编辑：

| 事件 | 文案 |
| :-- | :-- |
| 保存成功 | `Changes saved` |
| 取消成功 | `Changes reverted` |
| 保存失败 | `Save failed. Changes are still local.` |
| 绑定检查失败 | `Access check failed` |
| dirty 时尝试退出/换选 | `Save or cancel the current change first` |

保存失败后 Actor 保持当前位置、dirty 保持，用户可重试保存或取消。

---

## 6. Gizmo 设计

### 6.1 组成

3.5.1 继续保留 3.5 的四个语义部件，但重新定义视觉权重：

| 部件 | 用途 | 默认视觉 |
| :-- | :-- | :-- |
| Selection corners | 表示当前选择范围 | 地面四个冷灰色短角标，不参与拖拽 |
| Move XY handle | 平面移动 | 实例 Bounds 顶部的深青绿色四向手柄 |
| Move Z handle | 垂直移动 | 与 XY 同处实例顶部的世界 Z 轴工程蓝箭头 |
| Rotate Yaw ring | 绕世界 Z 轴旋转 | 实例 Bounds 中高位置的深橙色细环 + 小圆形抓手 |

不再使用大面积实心平板、过粗整圆、独立 Forward 箭头、大球形抓手或完整矩形 footprint。

### 6.2 颜色

场景 gizmo 允许使用少量功能色，但颜色必须与操作语义绑定：

| 语义 | 默认 | Hover | Dragging |
| :-- | :-- | :-- | :-- |
| Move XY | `#006F78` | `#00939E` | `#00BAC7` |
| Move Z | `#2652C4` | `#306FE0` | `#4E8DFF` |
| Rotate Yaw | `#B85B00` | `#DC7400` | `#FF971F` |
| Selection | `#A8B3BC` | 不变 | 不变 |
| Snap hit | `#66B58A` | - | 短时显示 |

同一时刻只有当前 hover 或 dragging 部件增强亮度和线宽，其他部件降低视觉权重。

### 6.3 尺寸与镜头适配

- gizmo 的 XY 与 Z 移动手柄根据实例 Bounds 放在模型顶部，避免被实心模型遮挡或难以拾取。
- Rotate Yaw 环根据实例 Bounds 放在模型中高位置；变换计算仍作用于目标 Actor Transform。
- 三类轴线使用同一基础线宽；hover 放大 10%，dragging 放大 20%。
- 可见尺寸按相机距离和视口高度换算，目标屏幕直径约 120 px。
- 屏幕直径限制在 96–144 px，避免贴近镜头时占满画面，远离时无法拾取。
- Rotate ring 半径约为 gizmo 可见尺寸的 45%。
- Move XY 可见手柄约 48–56 px，透明拾取区约 64 px。
- Move Z 箭头目标屏幕高度约 64–80 px。
- Rotate 抓手可见直径约 10 px。
- Selection corners 根据实例 Bounds 绘制，但独立于 gizmo 的屏幕尺寸，不用于计算 Actor Pivot。

拾取体与可见图形分离：

- Move XY 拾取区最小约 44×44 px。
- Rotate ring 拾取带最小宽度约 14 px。
- 拾取体透明且不渲染，不产生阴影，不出现在主渲染 Pass。

### 6.4 交互状态

```text
Idle selected
  -> cursor hits Move XY     -> Hover move
  -> cursor hits Move Z      -> Hover Z
  -> cursor hits Rotate Yaw  -> Hover rotate

Hover + left press
  -> capture pointer
  -> Dragging XY / Dragging Z / Dragging rotate
  -> update Transform and dirty state

Dragging + left release
  -> release pointer
  -> return to Hover or Idle selected
```

状态反馈：

- Hover move：只增强 Move XY，面板短状态显示 `Move XY`。
- Hover Z：只增强 Z 轴箭头，面板短状态显示 `Move Z`。
- Hover rotate：只增强 Rotate ring，面板短状态显示 `Rotate Yaw`。
- Dragging：对应部件加亮、线宽增加约 25%，面板显示 `Moving XY`、`Moving Z` 或 `Rotating Yaw`。
- Wall snap 命中：墙面接触点或 gizmo 边缘短时显示绿色提示，面板显示 `Wall snap`。
- Grid snap 生效：只显示 `Grid snap` 短状态，不持续绘制大网格。

### 6.5 输入与冲突规则

- UI hover/click 不得穿透到场景选择。
- Gizmo hover 每帧最多执行一次鼠标射线，不新增场景全量遍历。
- 按下 gizmo 后捕获本次拖拽，鼠标移出手柄仍继续拖动，直到左键释放。
- 拖拽期间禁止切换实例，保存和退出操作禁用。
- `Esc` 优先级：正在拖拽时先结束本次拖拽；存在 dirty 时恢复编辑基线；无 dirty 时清除选择或退出编辑模式。
- 鼠标释放后必须清除 dragging 状态，避免镜头恢复时 Actor 继续跟随。
- Runtime Editor 不改宿主项目输入映射；继续由 `TwinSceneManager` 读取现有快捷键配置。

---

## 7. 技术实现约束

### 7.1 实现方式

- 面板继续由 `UOntoTwinRuntimeEditorPanel` 使用 C++ `WidgetTree` 构建。
- 不要求创建或绑定 Widget Blueprint。
- gizmo 继续由 `AOntoTwinRuntimeGizmo` 管理，视觉组件与透明拾取组件分离。
- 优先复用 Engine 内置基础网格和运行时动态材质；3.5.1 不要求用户制作插件资产。
- 不依赖 `GEditor`、`UnrealEd`、`CallInEditor` 或仅 Editor 可用的 Style 资源。
- 不引入新的第三方依赖。
- 样式常量局部集中在 Runtime Editor 模块文件内，不为一次优化建设全局主题框架。

### 7.2 预计修改文件

正式修改只发生在插件源码：

```text
ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/
├── Public/OntoTwinRuntimeEditorPanel.h
├── Private/OntoTwinRuntimeEditorPanel.cpp
├── Public/OntoTwinRuntimeGizmo.h
├── Private/OntoTwinRuntimeGizmo.cpp
├── Public/TwinSceneManager.h
└── Private/TwinSceneManager.cpp
```

职责：

- `OntoTwinRuntimeEditorPanel`：布局、字体、按钮、toggle、状态点、toast 和 UI 状态刷新。
- `OntoTwinRuntimeGizmo`：可见几何、颜色、屏幕尺寸适配、hover/drag/snap 表现。
- `TwinSceneManager`：hover 射线、拖拽状态机、可展示 ViewModel 文案、Retry 入口和 toast 事件。

只有在编译需要新增 Engine 自带模块时才修改 `OntoTwinSync.Build.cs`；若现有 UMG、Slate、Engine 能力足够则不改。

### 7.3 状态接口建议

不引入完整 MVVM，仅增加足够的明确状态：

```text
EOntoTwinRuntimeGizmoPart HoverPart
EOntoTwinRuntimeGizmoPart ActivePart
EOntoTwinRuntimeSnapState SnapState

RetryRuntimeBindingStatus()
GetRuntimeEditorDisplayName()
GetRuntimeEditorInstanceIdText()
GetRuntimeEditorAccessState()
GetRuntimeEditorInteractionText()
ShowRuntimeEditorToast(Message, Type)
```

具体函数名可在实现时按现有命名调整，但不得继续依赖拼接整行调试文本来驱动布局。

---

## 8. 验收标准

### 8.1 面板

- 1280×720、1920×1080、2560×1440 三种视口下，面板不超出安全区、不遮挡自身控件。
- 默认 100% DPI 下宽度约 400 px、最小高度约 306 px；内容增加时允许向下扩展且不得裁切。
- 长实例 ID 不撑宽面板，按钮文字不截断。
- 界面不出现原始值 `error`、`unknown`、`dirty`、`ue_project_mismatch`。
- Wall snap 和 Grid snap 都有可点击标签及明确开关状态。
- matched、unbound、mismatch、error、checking 五种访问状态均有正确文案和按钮行为。
- 保存中按钮禁用并显示进行中状态；成功、失败、取消均有非阻塞反馈。
- 无选中实例、已选中未修改、已选中 dirty 三种状态布局稳定。

### 8.2 Gizmo

- 选中实例后不再出现大面积灰色方块、灰色锥体或棋盘格 gizmo 占位物。
- Move XY、Move Z 与 Rotate Yaw 在默认、hover、dragging 三态下可视觉区分。
- Move XY 使用明显的青蓝色四向手柄；Move Z 使用世界 Z 轴蓝色箭头。
- 旧白色 Forward 箭头已移除，选中范围只绘制四个短角标，不再绘制完整矩形。
- 旋转环、箭头和抓手不会覆盖大部分设备或占据大块视口。
- 相机远近变化时 gizmo 视觉尺寸保持可操作，目标屏幕直径维持在 96–144 px。
- 可见图形不投射阴影；透明拾取体不进入主渲染 Pass。
- 鼠标按下、移动、释放形成完整拖拽生命周期，不发生松开后继续移动。
- hover 射线不影响现有后端轮询和其他实例状态更新。

### 8.3 功能回归

- F8/F10 进入与退出 Runtime Editor 行为保持可用。
- XY 平移保持拖拽开始时高度；Z 手柄只修改 Z；Yaw 环只修改 Yaw。Z 移动不触发墙吸附或 XY 网格吸附。
- dirty 期间仍不会被后端轮询覆盖。
- Save 仍复用 `/api/v2/state/writeback`，Cancel 仍恢复基线。
- Wall snap、Grid snap 的默认值和计算规则不变。
- PIE 和打包 exe 均不依赖 Editor API。
- 将同一 OntoTwinSync 插件装入非 `test0316` UE 项目后，Runtime Editor 仍能由 `TwinSceneManager` 启用。

### 8.4 视觉验收材料

实现完成后至少提供以下截图用于确认：

1. 1920×1080：未选择实例。
2. 1920×1080：已选中、无 dirty。
3. 1920×1080：Move XY hover。
4. 1920×1080：Move Z dragging。
5. 1920×1080：Rotate Yaw dragging。
6. 1920×1080：dirty + 保存可用。
7. 1280×720：完整面板与 gizmo 同屏。
8. 绑定检查失败：`Unable to verify` + `Retry`。

---

## 9. 实施顺序

1. 面板结构与视觉 Token：先解决尺寸、字体、信息分组和长文本约束。
2. 数据集访问状态：补齐用户文案、Retry、按钮状态和错误反馈。
3. Gizmo 视觉：分离可见组件与拾取体，收敛尺寸和颜色。
4. Gizmo 状态机：增加 hover、dragging、snap feedback。
5. Toast 与输入冲突：补齐保存、取消、失败和 dirty 拦截反馈。
6. 在 `test0316` 同步插件副本进行 PIE、打包和多分辨率截图验收。

每一步通过后再进入下一步，避免视觉重构与拖拽逻辑同时变化造成难以定位的回归。

---

## 10. 需要确认的设计结论

本 PRD 默认采用以下结论作为 3.5.1 开发基线：

1. Runtime Editor 永久归属 OntoTwinSync 插件，`test0316` 仅是验证宿主。
2. 采用纯 C++ UMG，不要求用户手工制作 Widget Blueprint。
3. 采用插件自包含的 runtime gizmo，不要求用户手工制作材质或模型。
4. 面板保持英文短文案，避免当前 UE 默认字体缺少中文 glyph；中文本地化不进入 3.5.1。
5. 面板默认左上角、宽 400 px、最小高度 306 px，保持稳定宽度并允许高度自适应。
6. 黑白灰作为面板主视觉；蓝色表示移动、琥珀色表示旋转、绿色只表示吸附成功。
7. Save changes 是唯一主操作；保存失败保留 dirty 和本地 Transform。
8. 3.5.1 不碰后端与存储，只优化 UE Runtime 交互层。
