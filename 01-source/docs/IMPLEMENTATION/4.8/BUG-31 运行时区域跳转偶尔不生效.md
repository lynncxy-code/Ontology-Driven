# BUG-31 运行时区域跳转偶尔不生效（4.8）

- 日期：2026-11-24 发现，2026-11-26 登记
- 状态：**待排查**，还没有对话接手（交接说明在桌面 `handoff_区域跳转排查.md`）
- 来源：4.7 场景演出 grill 讨论。产品决定关卡内跳到某个地方，用现有的「实例空间管理（区域）+ 运行时 Tab 面板跳转」，但反馈"有时候会不生效"
- 影响：UE 运行时 Tab 面板「空间」页签选区域后点「前往位置」
- 下游：4.7 把区域跳转定为关卡内跳转的正式方案，需要先修稳
- 改动范围（预计）：UE 插件为主，可能涉及后台

## 症状

在网页「实例」页的空间管理里建好区域（楼栋、楼层、房间、区域，实例绑在最底层的区域上）。UE 运行时按 Tab 打开面板，在「空间」页签选一个区域，点「前往位置」，应该只显示该区域的设备并对准镜头。**有时不生效**，具体复现条件未知。

## 线索（来自其他调查，需核实）

- 网页：`frontend/instance.html`（区域管理）。后台：`backend/zone_management/service.py`，`backend/web_interaction/validators.py`（`zone_catalog`、`zone_descendants`、`validate_zone_hierarchy`），`backend/web_interaction/runtime_projection.py`（UE 每秒查询一次 `/api/v2/web-interactions/runtime`）。
- UE：`OntoTwinWebInteractionComponent.cpp`（`OpenZone` 约 L381；显隐和取景约 L1240-1328），`TwinSceneManager.cpp`（`ApplySceneScope`、`FocusManagedInstances`/`FocusManagedBounds` 约 L1408-1503），`TwinGodViewPawn::FocusToTransform`，`OntoTwinRuntimeDockWidget`。
- 可能的原因：
  - 模型没加载完就取景，退回实例原点（L1424）；
  - 漫游中镜头正在切换时走另一条路径（约 L1467-1491）；
  - Dock 里已进入某个分区时会再按分区筛一遍（约 L1735）；
  - 配置要等每秒一次的查询拉到后才生效；
  - 区域里没有绑定实例，或者实例绑在了非最底层的区域上。
- 和 OPT-11（3.8.3 业务视图镜头取景校准）共用取景代码，修改时要互相协调。

## 待办

1. 只读排查，找出"不生效"的几种情况、各自的触发条件和证据（代码行号、UE 日志、后台数据）。
2. 给产品一份照着点的复现步骤，请产品提供不生效时的项目名、区域名、操作顺序和 UE 日志。
3. 给出修复方案并确认后，登记台账、建 `.worktrees/BUG-31` 草稿修改。

## 根因 / 修复

（排查和修复后补写）
