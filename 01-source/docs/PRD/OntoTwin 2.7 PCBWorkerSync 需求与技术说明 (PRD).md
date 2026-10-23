# PCBWorkerSyncComponent 产品需求与技术说明文档 (PRD)

## 1. 产品背景
在“数字孪生飞机 (Digital Twin Aircraft)”项目的 PCB 车间监控场景中，需要将后端传来的实时工人状态（位置、工作状态、工位）在 UE5 前端转化为三维空间内真实、直观的虚拟数字人表现。

**核心问题：**
早期版本受限于 UE5 动画蓝图 (AnimBP) 状态机复杂性、位置插值抖动、以及骨骼网格体不匹配（T-Pose 问题）等痛点。为解决这些问题，本项目演进了 `PCBWorkerSyncComponent`，采用了一种直接通过 C++ 控制动画序列树 (Animation Single Node)、绕开状态机的稳定方案。

---

## 2. 核心功能及使用场景
`PCBWorkerSyncComponent` 作为一个组件，挂载到表示工人的 `SkeletalMeshActor`（骨骼网格体对应的 Actor）上，承担以下职责：
1. **数据对接与中间层关系：**
   - 依赖并对接中间层 API (`/api/ue/snapshot` 和 `/api/ue/events`)。
   - 场景中 `APCBWorkerManager` 作为总控进行轮询，组件级实现 `ITwinEntitySync` 接口被动接收分发数据：
     - **快照更新：** `ApplySnapshot` 消费中间层 `snapshot.items` 的全量状态（坐标、状态、工位）。
     - **增量同步：** `ApplyPositionChanged` 响应中间层 `position_changed` 事件，进行空间平滑移动；`ApplyStateChanged` 响应事件驱动状态机切换。
     - **静态信息：** 人员的展示姓名等数据通过中间层的 `metadata.name` 等字段下发并供给前端渲染。
2. **三维空间同步（移动与朝向）：** 丝滑地控制工人在场景中从 A 点走到 B 点，并在到达工位后自动根据工位坐标调整物理朝向。
3. **骨骼动画自适应：** 诊断动画与模型骨架是否匹配，自动切换 待机(Idle)、行走(Walk)、工作(Working) 动画，规避原生的状态机死锁。
4. **悬浮信息展示：** 与 `UTwinLabelComponent` 联动，实时呈现头顶的“人员姓名 + 当前工位 + 工作状态”动态标签盘。

---

## 3. 详细逻辑与需求说明

### 3.1 空间位置与朝向同步逻辑
*   **初次快照（瞬移）：** 组件在接收到第一次快照时（`bFirstSnapshotReceived` == false），忽略常规插值逻辑，将模型瞬间移动到目标工位及其正确朝向。这是为了防止系统启动时工人从(0,0,0)跑到目标位置带来的违和感。
*   **日常运动插值：** 通过 `TickComponent` 使用 `FMath::VInterpConstantTo` 进行匀速位移，`MoveInterpSpeed` 默认可调（150cm/s）。如果移动过程中坐标发生更新而组件处在运动状态，则容错处理防抖。
*   **智能朝向修正：** 
    *   **行进中：** 模型会自动计算前进视角（减去90度的偏移补偿），基于 `RotationInterpSpeed` (默认 5.0) 平滑转向。
    *   **到达工位后：** 基于位置坐标 Y 的符号判断流水线侧：若目标 `Y > 0` 则朝向正方向（Yaw=0°），若目标 `Y < 0` 则朝向反面（Yaw=180°）。
    *(注：本期开发暂不实现动态朝向下发，维持上述坐标硬编码判断实现形式；计划未来将“到达工位后的朝向数据（Rotation）”由场景管理器统一规划并一并下发。)*

### 3.2 自主生命周期动画驱动逻辑 (V3 方案)
*   **强制动画模式：** `CachedMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode)`，这保证了状态完全由该 C++ 组件接管。
*   **防 T-Pose 校验：** `BeginPlay` 阶段将强制提取当前 `USkeletalMeshComponent` 的 `USkeleton` 并与三个预设动画的原生骨架对比，若不能兼用会在日志标红（提示在编辑器 Assign Skeleton）。
*   **状态优先级机：** 
    1.  检测到具备位移速度 (`bIsCurrentlyMoving == true`) -> **Walk 动画序列**。
    2.  检测到业务状态 (`WorkerStatus == "working"`) -> **Working 动画序列 (Cards_Anim)**。
    3.  默认托底兜底 -> **Idle 动画序列**。
    （注：为了避免动画每帧重入卡顿单帧死循环，通过引入 `EPCBAnimPhase` 记录枚举进行状态变更差分判断才触发切换）。

### 3.3 头顶 UI 信息跟随挂载
*   组件内置聚合实例化 `TwinLabelComponent`。
*   **渲染：** 将标签 `ZOffset` 偏移量定死为 200，并自动设置为公告板模式（`bBillboard = true`），使文本永久注视主摄。
*   **UI 数据：** 映射机制将 "working"、"idle" 等底层信号渲染为中文（"正常工作", "待机空闲"等）。自动将标签标题绑定为 `"[InstanceId] [姓名]"` 格式，其中姓名将直接从中间层 API 传出的 `metadata.name` 中无缝拉取解析，不再硬编码为“张明”。工位名称名称同样依据后端下发数据放入副标题中。

---

## 4. 可调配置与资产绑定说明
在 Editor 的 Details 板块中暴露了以下属性方便修改：
*   **身份：** `InstanceId` 必须填写。
*   **移动：** `MoveInterpSpeed` (默认 150cm/s), `RotationInterpSpeed` (默认 5 旋转插值/s)。
*   **动画资产（SoftObjectPointers）：** 自动绑定默认资产路径 (`/Game/ani/...`)，但在蓝图中可随意置换：
    *   `IdleAnimAsset`: 站立空闲
    *   `WalkAnimAsset`: 走路
    *   `WorkingAnimAsset`: 工作交互
*   **事件委托：** `OnStatusChanged`, `BP_OnWorkerStartMove`, `BP_OnWorkerArrived` 等以便给蓝图追加粒子特效。

---

## 5. 未来演进与优化方向
1. **统一动画管理表 (DataTable)：** 目前 C++ 里利用 `ConstructorHelpers` 硬编码了特定路径的动画序列。未来**不打算使用蓝图重载继承**，而是计划建立一套**标准的动画资产管理表 (DataTable 或 DataAsset)**，将人员模型模板相关的动画映射规则做统一配置化和数据驱动。
2. **场景管理器朝向下发：** 废弃目前写死的 `Y` 坐标正负判断方案，改为由中台接口下发或在场景数据配置表里指明各工位的精确旋转角度。
3. **后端网络抖动抗性：** 考虑应对频繁收到的短距离(如几厘米误差)位置更新，可在状态逻辑里增添适当的行动阈值半径以进行防抖降噪。
