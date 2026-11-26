# BUG-30 未绑定关卡卡在加载画面（4.8）

- 日期：2026-11-25 发现，2026-11-26 登记
- 状态：**待排查**，还没有对话接手（交接说明在桌面 `handoff_未绑定关卡可运行.md`）
- 来源：4.7 场景演出 grill 讨论关卡切换时，产品指出进入未绑定的关卡会卡在加载画面，而且已经在用的项目里也会出现"没绑定数据集，关卡就彻底进不去"
- 影响：所有用 OntoTwinSync 插件、但当前地图没在网页上绑定数据集的 UE 程序
- 下游：4.7 NEW-14 关卡切换依赖本条（未绑定的关卡要能进入）
- 改动范围（预计）：UE 插件 `OntoTwinSync`

## 症状

UE 程序启动或进入一张未绑定数据集的地图后，画面一直被加载画面盖着，显示"正在连接 OntoTwin 并等待当前项目的模型数据。"，不会结束，也没有"未绑定"的提示。

## 已知现状（需接手的人核实）

文件：`01-source/ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/Private/TwinSceneManager.cpp`

- BeginPlay（约 L285-297）先 `EnsureModelLoadingWidget()`，在最上层（层级 2000）加加载画面，然后 `CheckInitialBindingStatus()`。注释写的是 "An unbound level stays blocked until the user binds it in the web console."，**说明"未绑定就挡住"是当初有意的设计**，要查清来历（git log、PRD、台账）并告诉产品。
- `CheckInitialBindingStatus` 的 `unbound` 分支：只把 `RuntimeStatusMessage` 设成"关卡尚未绑定，请在网页数据集卡片中选择关卡绑定"（只在 F10 面板里显示），然后按 5 秒起、最长 60 秒的间隔反复重查（`ScheduleBindingStatusCheck`）。加载画面不会关闭。
- 加载画面只有在首批模型数据到达（`CompleteInitialModelBaseline`，`bInitialModelBaselineReady = true`）后才关闭。展示方案（`TwinSceneManagerDisplaySchemes.cpp` L136、L273）、运行时编辑自测等也以它为前提。
- 漫游配置来自 `/api/v2/scene-interactions/runtime`（`TwinInteractionManagerComponent.cpp` 约 L584、L816-858）。未绑定时很可能返回 `blocked_reason`，导致 F7 漫游不可用。待核实。
- 后台没启动或连不上时，很可能也卡在同一个画面。待评估。

## 期望（产品要求）

- 关卡本身不依赖数据集的功能照常可用：自由镜头、上帝视角、Tab 面板、关卡切换（NEW-14）、全局灯光的"关卡原样"（NEW-15）。F7 漫游是否可用，排查后和产品确认。
- 依赖数据集的功能（设备实例、业务视图、保存编辑等）可以不可用，但要用不挡画面的方式明确提示"该关卡尚未绑定数据集"。
- 在网页上绑定后自动接上（保留现有的定时重查）。
- 已绑定关卡现有的加载流程（加载进度、失败自动重试）不受影响。

## 待办

1. 只读排查，列出未绑定（以及后台连不上）时被挡住的功能和挡住它们的代码。
2. 和产品确认未绑定时哪些功能要能用、提示怎么显示。
3. 给出修改方案并确认后，登记台账、建 `.worktrees/BUG-30` 草稿修改。只改 UE 插件的话，5501 不适用，用打包程序或录屏验收。

## 根因 / 修复

（排查和修复后补写）
