# OntoTwin UE 启动固定镜头默认 Pawn 隐藏补丁（PRD）

## 1. 问题

宿主关卡未指定自定义 GameMode 时，UE 原生 `GameModeBase` 会自动生成一个 `ADefaultPawn`。该 Pawn 自带 `/Engine/EngineMeshes/Sphere` 灰色球体。OntoTwin 启动后把玩家视角切换到 `camera.startup.default` 固定镜头，原生 Pawn 仍停留在 PlayerStart，因此会被固定镜头看到，通常表现为地面上的灰色半球。

该球体不是 OntoTwin 相机锚点，也不是人物漫游角色。

## 2. 修复规则

启动固定镜头成功生效后：

1. 读取当前 PlayerController 占有的 Pawn。
2. 仅当 Pawn 的实际类**精确等于** UE 原生 `ADefaultPawn` 时执行处理；不匹配其子类。
3. 对该原生 Pawn 调用 `SetActorHiddenInGame(true)` 并关闭 Actor 碰撞。
4. 不销毁 Pawn，不修改 GameMode，不修改关卡资产。
5. 自定义 Pawn、OntoTwin 运行时编辑摄像机、人物漫游角色和上帝视角 Pawn 均不得受影响。

## 3. 兼容性

- 固定镜头仍由 `TwinGodViewAnchor` 提供。
- F8 运行时编辑仍按需生成并占有 `TwinRuntimeEditorCameraPawn`。
- 人物漫游仍按需生成并占有 `TwinRoamingCharacter`。
- 退出临时模式后即使重新占有原生 Pawn，它仍保持不可见，避免灰球再次出现。
- 不改变项目存储、后端接口或 UE 关卡文件。

## 4. 验收标准

1. 使用原生 `GameModeBase` 启动时，固定镜头画面中不再出现灰色球体。
2. 日志出现一次原生 DefaultPawn 隐藏记录。
3. 自定义 Pawn 不会被自动隐藏。
4. F8 摄像机、人物漫游、固定镜头恢复均正常。
5. Editor Development 与 Game Shipping 目标编译通过。
