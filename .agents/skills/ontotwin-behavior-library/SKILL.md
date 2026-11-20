---
name: ontotwin-behavior-library
description: 往 OntoTwin 工业行为库（UE 插件 OntoTwinIndustrialBehavior + 后台行为目录）补充动画、外观或特效的完整流程：判断能否进库、需求与参数、第三方素材入库、后台目录与 UE 插件三处代码、自测、网页和 UE 两半一起发布验收、存进 dev、同步到各项目 UE 工程。当新增/修改/改名行为库条目，或把别的工程里的动画和特效“沉淀”进行为库时使用。
---

# 工业行为库扩充操作手册

> 适用于：新增一个动画/外观/特效，修改已有条目的参数或效果，改条目显示名，把项目里做好的效果收进行为库。
> 总流程仍按 `AGENTS.md`（登记 → 自测 → 发布 → 产品验收 → 存进 dev → 收尾）。本手册只补充行为库特有的做法和已踩过的坑。
> 相关手册：后台 `ontotwin-backend`，测试 `ontotwin-testing`，UE 工程 `ue-super-steward`，打包和回退 `ontotwin-product-lifecycle`。

## 0. 心智模型

- **配置在网页，执行在 UE。** 产品在网页上按“类型 + 状态”给设备选行为、填参数；后台把当前状态解析成每个通道（channel）要放的行为；UE 插件收到后执行。
- **后台目录是“菜单”，UE 插件是“厨师”。** 两边用同一个行为编号对接，缺一边都不行：只改目录，网页能选、画面没反应；只改插件，能做但网页选不到。
- **四个通道，各有一个默认槽位（slot）**，同一台设备每个通道同一时刻只放一个行为：

| 通道 | 网页叫法 | 默认槽位 | 离开状态时退回 | 已有例子 |
|---|---|---|---|---|
| `animation` | 动画 | `motion` | `safe.idle` | 持续旋转、往复摆动 |
| `visual` | 外观／动态材质 | `status_indicator` | `safe.visible` | 状态外观·警告黄、目标高亮、皮带滚动 |
| `fx` | 特效 | `alarm` | `safe.none` | 告警闪烁、区域扫描 |
| `label` | 标签 | `label` | `safe.label` | 示例标签 |

（出处：`01-source/backend/presentation_routing.py` 的 `SAFE_FALLBACKS`）

## 1. 先判断能不能进库

四条都满足才进；不满足的，先和产品讨论方案，不要硬塞。

1. **作用在设备本身**，能用“某类型设备进入某状态”触发。两台设备之间的连线、全场景的天气这类效果不属于行为库（NEW-05 因此没收通信脉冲）。
2. **是通用能力**。只属于某个客户场景的内容放进那个项目的 UE 工程，不进平台插件；拿不准就问产品。
3. **参数能用下拉（`select`）或数字（`number`）表达**。网页配置页只按这两种类型自动生成控件（`01-source/frontend/ontology.html`）。要颜色盘、曲线、文本这类控件就得改前端，必须单独评估。
4. **能停干净**：离开状态、设备被移除时，能把模型恢复成原样，而且只清掉自己加上的东西。

## 2. 登记和需求

- 分配编号（`NEW-xx` 新增、`OPT-xx` 优化、`BUG-xx` 修复），先查台账和 git 记录避免重号，再在台账登记开工。
- 写 PRD（放 `01-source/docs/PRD/`），必须包含：
  - **效果**：长什么样，最好附源工程截图或录屏；
  - **参数表**：每个参数的名称、类型（下拉/数字）、范围、默认值；
  - **运行规则**：和谁互斥；进入和离开状态时怎么做；设定时长到期怎么办；同一状态数据重复推送时不重播；设备被移除时怎么做；插件缺失时退回什么样；
  - **验收清单**：照抄第 7 节，再补这个效果特有的项。
- 产品确认后再开工。新增依赖（例如 UE 自带的 Niagara 粒子插件）属于硬规矩，必须先得到产品同意。

## 3. 第三方素材入库

只在效果用到 UE 素材（材质、贴图、Niagara、材质参数集）时才需要这一步。

1. **只带用到的部分**。从效果的入口素材出发，沿引用关系找出完整的依赖链，只搬这条链上的素材，不带演示地图、示例模型和用不到的素材。
2. **用 UE 编辑器的“移动/迁移”功能搬**，放进 `Plugins/OntoTwinIndustrialBehavior/Content/Effects/`（材质类可放 `Content/Materials/`），让引用自动改到新位置。不要在资源管理器里直接复制 `.uasset` 文件。
3. **搬完检查**：所有素材都能在插件路径下单独加载；没有任何引用还指向源工程（例如 `/Game/...`、源工程的插件名）。
4. **大贴图降尺寸**：没有特殊理由时，4K 降到 1K。
5. **登记进打包清单**。插件在运行时按路径加载素材（`LoadObject`），打包工具看不出这些素材被用到，会漏带。NEW-05 的做法是在模块启动时挂 `FGameDelegates::GetModifyCookDelegate()`，把入口素材加进烹饪清单（cook，即打包前的素材转换）（见 `OntoTwinIndustrialBehaviorModule.cpp`），新素材照此登记入口即可，依赖会被自动带上。
6. 新增引擎插件依赖时，`.uplugin` 的 `Plugins` 和 `Build.cs` 的依赖模块两处都要加。

## 4. 改代码：固定三处

### 4.1 后台目录（网页的数据来源）

- 新行为放进**独立模块**，例如已有的 `01-source/backend/motion_behaviors.py`（基础运动）、`device_effects.py`（区域扫描、目标高亮）；不要往 `app.py` 里加。
- 在模块里给出每个条目：
  - `resource_id`：稳定编号，形如 `ot.industrial.xxx`、`ot.motion.xxx`，一经发布不再改；
  - `channel`、`slot`：按第 0 节的表填写；
  - `display_name`、`description`：给产品看的中文名称和说明；
  - `parameter_schema`：参数表，键名用英文，`label` 用中文；
  - `runtime_package`、`package_version`：说明需要哪个 UE 插件的哪个版本。
- 在 `presentation_catalog.py` 里把条目加进 `MOCK_PRESENTATION_RESOURCES`，并在 `validate_selection` 里接上参数校验。校验要拒绝：未知参数、超范围、非有限数（NaN）、布尔值冒充数字、不在选项里的下拉值。
- 目录内容变了就把 `CATALOG_VERSION` 加一，并更新 `catalog_payload` 里的 `runtime_note`，写清要求的 UE 插件版本。
- **改名只改 `display_name`，不改 `resource_id`**，旧配置才能照常生效（NEW-05 把三个旧高亮改名为“状态外观·…”就是这样做的）。
- 新增参数时，要给已保存、但没有这个参数的旧配置补上默认值（参考 `normalize_motion_params`）。默认值不能悄悄改变旧配置原来的效果；如果确实要变（例如 BUG-26 把旋转中心默认改成模型中心），要在 PRD 里写明，并经产品确认。
- 测试放 `01-source/backend/tests/`，至少覆盖：目录里能列出条目、合法参数能通过、各种非法参数被拒绝、按状态解析出正确的行为和参数、离开状态后退回 `safe.*`。

### 4.2 UE 插件（真正执行的地方）

插件目录：`01-source/ue_project/Plugins/OntoTwinIndustrialBehavior/`。

- **入口**：`OntoTwinIndustrialBehaviorModule.cpp` 的两个函数：
  - `SupportsPresentationRoute`：声明认领这个通道下的这个行为编号；
  - `ExecutePresentationRoute`：执行它。
  后台把 `resource_id` 映射成 UE 端的行为编号（`presentation_routing.py` 的 `_CATALOG_RESOURCE_BEHAVIOR_IDS`），两边编号要对得上。
- **效果写成独立组件**（参考 `DeviceEffectsComponent`、`BasicMotionComponent`），第一次执行时挂到设备上，不要把逻辑堆进模块入口。
- **必须做到：**
  - 同一通道换成别的行为、收到 `safe.*`、`EndPlay`（设备被移除）时都能停止，并恢复原样；
  - 只清除自己加上的东西，例如恢复覆盖材质（overlay）时，只在当前还是自己那份的情况下才恢复；
  - 接管通道时，先让同通道里原来的行为退出（参考 NEW-05 进入高亮前先让状态外观退回 `safe.visible`）；
  - 参数缺失时用默认值，参数非法时返回失败，不要猜；
  - **每次执行写一行日志**，格式和已有的保持一致：`[OT-Presentation] instance=… channel=… behavior=… applied=0/1`（动画用 `[OT-Motion]`）。NEW-05 的扫描和高亮漏了这一条，现场排查时无法确认到底执行没有。
- **不用自己处理重复推送**：同一状态数据重复推送时，`TwinInstance` 会比较“行为编号 + 参数”，没变化就不会再次调用执行函数。效果自己的计时（例如持续 8 秒）从第一次执行开始算。
- **模型的现实情况**：
  - OntoTwin 加载的 GLB 会合并成一个静态网格，轴心在模型文件的原点，不一定在模型中心（BUG-26 就是因此绕旁边的点画圈）；旋转类效果默认绕模型包围盒中心转；
  - 带骨骼的模型和静态模型是两类组件，只支持其中一类时要在 PRD 里写明；
  - 每个网格只有一个覆盖材质槽，外观类效果之间会互相顶替，所以同一时刻只显示一种。
- **全场景共享的资源**（例如扫描用的材质参数集，所有设备共用一份）同一时刻只能给一台设备用，要写清谁接管、结束后谁接上；用完把参数恢复成接管前的值。
- **自动测试**写在 `Private/*Tests.cpp`，路径统一用 `OntoTwin.Presentation.<名字>`，至少覆盖：执行成功、参数非法被拒、停止后恢复原样；有接管关系的要测接管和接续。

### 4.3 前端

一般不用改：网页会按 `parameter_schema` 自动生成下拉框和数字输入框。只有第 1 节第 3 条那种新控件才需要改前端，改前先读 `ontotwin-ui`。

## 5. 自测

```bash
cd 01-source/backend; python -m pytest -q
```

- 后台：先跑新加的测试文件，再跑全量。
- UE：在隔离的宿主工程里编译插件，再无界面跑自动测试：
  ```bash
  UnrealEditor-Cmd.exe <宿主>.uproject -ExecCmds="Automation RunTests OntoTwin.Presentation; Quit" -unattended -nullrhi -nosplash -NoSound -abslog=<日志路径>
  ```
  宿主工程放在路径短的位置（例如 `D:\tmp_ue\<编号>host`），Windows 路径过长会导致编译失败；收尾时删掉。
  如果别的工程正开着编辑器、开启了实时编码（Live Coding），编译会被拦下，加 `-NoHotReloadFromIDE` 绕开，不要去关别人的编辑器。
  启动时出现的两行 `LogAutomationTest: Error: Condition failed` 是引擎自带的噪音，不算失败；以 `Test Completed. Result={成功}` 为准。
- 结果写进台账备注。

## 6. 发布和验收：网页和 UE 两半一起发

- **后台**按 `AGENTS.md` 的 5501 规则发布（或按产品指定的临时环境，例如 5503）。
- **同时更新连这个环境的 UE 程序**：
  - 先查清是哪一个：看后台访问日志里出现的 `ue_project_id`，再对照各 UE 工程 `Config/DefaultGame.ini` 里的 `BackendBaseUrl` 和 `UEProjectId`；
  - 把新插件装进去重新编译；需要打包程序时，用打包后的程序验收，因为编辑器里正常不代表打包后素材齐全。
  - BUG-26 只发了后台、没换 UE 插件，结果网页上能看到新选项，画面没有变化。
- **实测前准备好**：
  - 一份测试用的类型配置，先备份原配置；保存走网页同一个接口 `PUT /api/v2/ontology/types/<类型>/behavior-config`，不要用旧接口 `presentation-profile`，那个只改到三份副本中的一份；
  - 用状态名区分各测试项（例如“巡检蓝”“阻断”），避免用 `normal`、`idle` 这类会被当成同义词互相匹配的状态；
  - **一个能看到测试设备的固定机位**。没有机位就拍不到效果（NEW-05 的高亮因此没测成）；
  - 切换状态用调试接口 `POST /api/v2/state/override`，测之前记下设备原来的状态值。
- **5501 上是真实业务数据**：在 5501 上改配置、切状态前，必须得到产品明确同意；能用临时环境就用临时环境。
- **测完恢复原样**：配置要核对三处副本都和原来一致（类型的 `presentation_profile`、`interface_configs.I3D_Behavioral`、`interface_configs.I3D_Presentation`），设备状态改回原值，关掉自己开的程序。
- 告诉产品版本号、这一版包含哪几条修改、去哪里看、怎么看。

## 7. 验收清单（每个新效果都过一遍）

1. 网页上能选到这一条，参数控件、范围和默认值都和 PRD 一致；非法值保存时会被拦下。
2. 设备进入状态时开始播放，离开状态时停止，并恢复原样。
3. 在状态之间来回切换时，效果跟着正确切换，没有残留。
4. 设定的时长到期后自动消失；同一状态数据重复推送时不重播。
5. 同通道互斥正确；有共享资源的，接管和接续正确，配色不串。
6. 设备被移除后不留残留。
7. 打包后的程序里素材齐全，日志里没有素材缺失报错。
8. 禁用插件后，场景照常同步，这个行为退回静态安全表现。
9. 记录帧率基线（例如 200 台设备、20 台同时播放）。
10. 日志里能查到每次执行记录。

**验收结论只按产品的明确表态记录。** 几个 AI 同时干活时，产品在一个对话里说“通过”，只对那个对话里说的那一条有效，不要套用到别的编号上。

## 8. 存进 dev，同步到各项目 UE 工程

- 产品明确验收通过后，才把这一条存进 dev，再收尾：删草稿文件夹、分支、宿主工程和临时文件。推送云端前单独问产品。
- **同步到各项目 UE 工程**（例如 0bay 的 `D:\0bay\OfficeShell`），只在产品要求时做：
  1. 对比项目里的行为库插件和 dev 的差异，确认项目没有自己改过这个插件；有的话先问产品；
  2. 备份要被替换的文件和旧插件程序（`Binaries` 下的 DLL）；
  3. 只替换行为库插件，不动项目里的其他插件（例如 OntoTwinSync 在项目里常有专属修改）；
  4. 重新编译这个项目的编辑器，在项目里跑 `OntoTwin.Presentation` 自动测试；
  5. 在台账里记下改了哪个工程、哪几个文件、备份放在哪里；产品验收后删除备份。
