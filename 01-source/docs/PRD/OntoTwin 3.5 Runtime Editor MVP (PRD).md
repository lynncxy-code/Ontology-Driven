# OntoTwin 3.5 Runtime Editor MVP (PRD)

> 状态：方案草案（grill-me 第二轮修订）
> 主线：OntoTwin Nexus / UE Runtime / OntoTwinSync 插件
> 日期：2026-07-07
> 目标版本：3.5 MVP

---

## 1. 背景与目标

当前实例运维与监控页面主要通过 OntoTwin 后端状态驱动 UE 中的 Actor 变化。对于“把设备靠墙”“微调工位朝向”“现场按真实画面校准位置”这类诉求，直接改 JSON 或表单字段不直观，也不符合三维编辑器的操作习惯。

Runtime Editor 的目标是在 **打包后的 UE exe 运行时** 提供一个轻量场景编辑入口，让用户在真实 UE runtime 场景里选中 OntoTwin 已接管的孪生实例，使用可交互 gizmo 进行平面拖拽、Yaw 旋转、靠墙吸附，并把当前 UE 运行时位置保存为 OntoTwin 后端的目标状态。

核心原则：

- UE runtime 负责真实三维交互和最终画面。
- OntoTwin 后端仍是实例空间状态的事实来源。
- MVP 只做最小闭环，不复刻 UE Editor。
- MVP 编辑的是 desired state：保存语义为“将当前 UE 运行时 Transform 写回为 OntoTwin 目标状态”。

---

## 2. 范围

### 2.1 本轮做

- 在现有 `ATwinSceneManager` 内集成 Runtime Edit Mode，不额外要求场景放置第二个 Manager。
- 默认启用 Runtime Editor，但保留 `bEnableRuntimeEditor` 开关以支持只读部署。
- 仅编辑由 `TwinSceneManager` 管理的 `ATwinInstance`。
- 快捷键进入/退出编辑模式；输入由 `TwinSceneManager` 轮询 `PlayerController` 并绑定 Actor 输入事件，MVP 不引入 Enhanced Input。
- 鼠标射线选中实例，选中后显示可交互 runtime gizmo。
- UMG 小面板展示选中实例、坐标、Yaw、dirty 状态、保存、取消、吸附开关和绑定状态。
- 支持世界 XY 平移、绕世界 Z 轴的本地中心 Yaw 旋转、保持当前 Z。
- 支持基础网格吸附和靠墙对齐。
- 保存时复用现有 `POST /api/v2/state/writeback`，并以后端返回的 `snapshot` 立即对齐本地 Actor。
- 编辑期间使用 `bLocalOverrideLock` 防止后端快照覆盖当前实例空间变换。
- 进入编辑模式时检查 UE 工程绑定状态；未绑定时允许 runtime 首次绑定当前 UE 工程到后端当前激活数据集。

### 2.2 本轮不做

- 不编辑未迁移、未被 OntoTwin 接管的历史 UE Actor。
- 不新增或删除实例。
- 不保存 `.umap`。
- 不打包 UE Editor 能力。
- 不做完整三轴 Transform Gizmo。
- 不做 Z 轴拖拽、Pitch/Roll、Scale 编辑。
- 不做多选、批量编辑、禁放区、完整避障。
- 不新增 ProjectStore 存储结构。
- 不引入后端多人编辑锁；多人冲突放到后续版本。
- 不在 Runtime Editor 中切换后端 active dataset；切换数据集仍由 OntoTwin Web 完成。
- 不展示 actual/desired 双态差异，不新增 runtime actual 上报通道。
- 不做多步 Undo/Redo；只支持取消恢复到本次编辑前。

---

## 3. 用户流程

1. 用户在 OntoTwin Web 激活目标数据集。
2. 用户启动打包 exe，场景正常由 `TwinSceneManager` 从 `/api/v2/state/snapshots` 拉取实例并生成 `ATwinInstance`。
3. 用户按 Runtime Editor 快捷键进入编辑模式。
4. `TwinSceneManager` 检查 `/api/v2/ue/binding_status`：
   - `matched`：允许保存。
   - `unbound`：UI 显示“绑定本 UE 工程到当前激活数据集”，用户确认后调用 `/api/v2/ue/bind_active_project`。
   - `mismatch`：允许本地预览，但禁止保存，并提示该数据集已绑定到其他 UE 工程。
5. 用户点击某个设备实例，插件通过射线命中 `ATwinInstance` 并读取 `InstanceId`。
6. 插件记录该实例进入编辑前的 Transform 和行为动画状态，设置 `bLocalOverrideLock=true`，暂停该实例本地行为动画。
7. 选中实例旁生成 runtime gizmo：
   - 拖 XY 平面手柄：在当前 Z 高度水平平面内移动。
   - 拖 Yaw 旋转环：围绕 Actor Pivot 和世界 Z 轴旋转。
   - Bounds / footprint 框只做可视辅助和靠墙估算。
8. 用户拖拽或旋转后，面板显示“未保存”。dirty 状态存在时禁止切换到其他实例或退出编辑模式，必须先保存或取消。
9. 用户点击保存：
   - 插件把当前 Transform 组装成 `{tx,ty,tz, rx,ry,rz, sx,sy,sz}`。
   - 调用 `POST /api/v2/state/writeback`。
   - 成功后使用返回的 `snapshot` 立即应用最终后端确认 Transform，清除 dirty，解除锁。
10. 用户点击取消：
    - 实例恢复进入编辑模式前的 Transform。
    - 清除 dirty，解除锁。
    - 不写后端。

---

## 4. 技术方案

### 4.1 集成位置

MVP 直接集成到现有 `ATwinSceneManager`：

- 复用 `BackendBaseUrl`、`UEProjectId`、`UEProjectName`、`SceneId`。
- 复用 `InstanceRegistry` 查找当前受管实例。
- 复用 UE 工程 Header 组装逻辑。
- 避免用户在每个关卡里额外放置 `ATwinRuntimeEditorManager`。

可在后续版本把 Runtime Editor 拆成独立组件或 Actor，但 MVP 不拆。

新增/扩展职责：

```text
ATwinSceneManager
  - ToggleRuntimeEditMode()
  - CheckRuntimeBindingStatus()
  - BindCurrentRuntimeProject()
  - SelectTwinUnderCursor()
  - BeginEditInstance()
  - UpdateRuntimeGizmoDrag()
  - SaveRuntimeEdit()
  - CancelRuntimeEdit()
```

### 4.2 输入方案

MVP 不引入 Enhanced Input，也不要求项目改 Input Mapping Context。

`TwinSceneManager` 在 Tick 或轻量输入轮询中获取 `GetWorld()->GetFirstPlayerController()`，检测：

- `F8`：进入/退出 Runtime Edit Mode。
- 鼠标左键：选择 gizmo 手柄或实例。
- `Ctrl+S`：保存当前编辑。
- `Esc`：取消当前编辑。

规则：

- `bEnableRuntimeEditor=false` 时所有 Runtime Editor 输入无效。
- 保存中禁止继续选择、拖拽或退出编辑模式。
- 有 dirty 时禁止切换实例或退出编辑模式。

### 4.3 轮询与同步锁

Runtime Edit Mode 不暂停整个 `TwinSceneManager` 轮询。

规则：

- 普通运行时使用 `PollInterval`，默认 0.5 秒。
- 进入 Runtime Edit Mode 后使用 `EditModePollInterval`，默认 1.5 秒，用于降低拖拽期的 JSON 解析和快照应用压力。
- 当前编辑实例设置 `bLocalOverrideLock=true`，只锁空间变换。
- 其他实例继续响应后端快照。
- 当前实例的视觉/标签状态可以继续更新，但会暂停本地行为动画，避免动画 Tick 与 gizmo 拖拽叠加。

保存或取消后恢复普通轮询频率。

### 4.4 选择与高亮

选择流程：

```text
鼠标点击
  -> PlayerController DeprojectScreenPositionToWorld
  -> LineTraceByChannel
  -> 命中 Actor
  -> Cast<ATwinInstance>
  -> 若存在 InstanceId，则设为当前选中对象
```

高亮方式：

- MVP 优先使用材质 overlay 或 CustomDepth/Stencil。
- 若项目未配置后处理，高亮失败不影响编辑闭环。

### 4.5 Runtime Gizmo

MVP 必须包含可拾取、可拖拽的 runtime gizmo。Actor 本体点击只负责选中，不直接拖动 Actor。

Gizmo MVP 包含：

- XY 平面拖拽手柄：移动实例。
- Yaw 旋转环：旋转实例。
- 朝向箭头：显示对象本地 Forward。
- Bounds / footprint 辅助框：辅助靠墙和空间判断。

Gizmo 坐标规则：

- 平移使用 UE 世界 X/Y 轴。
- 旋转围绕 Actor Pivot 和世界 Z 轴。
- Actor Pivot / Actor Transform 是真实编辑中心。
- Bounds 中心不作为真实 Transform 中心，只用于可视辅助和靠墙距离估算。

拖拽平面：

- 选中实例时记录 `EditPlaneZ = SelectedActor.Location.Z`。
- 拖 XY 手柄时，鼠标射线与 `Z = EditPlaneZ` 的水平平面求交。
- 拖动中只更新 X/Y，Z 保持不变。
- “贴地”不作为拖动中的实时行为；若需要，后续作为显式按钮加入。

### 4.6 靠墙吸附

MVP 的墙体来源为 UE runtime 场景中的 Actor 标签或碰撞通道。

默认规则：

- 墙体或结构 Actor 带 `OntoTwinWall` Tag 时参与吸附。
- 未带 Tag 的墙体不参与靠墙吸附，但自由 gizmo 拖拽仍可用。
- 吸附距离默认 100 cm，可在 `TwinSceneManager` 暴露为可配置属性。
- 设备接近墙体时：
  - 找到最近墙面或墙体碰撞面。
  - 使用墙面切线对齐设备 Yaw。
  - 使用墙面法线给设备中心点增加安全偏移。

本轮不保证复杂凹凸墙体、曲面墙、非标准碰撞体的完美吸附。

### 4.7 后端接口

复用现有保存接口：

```http
POST /api/v2/state/writeback
Content-Type: application/json
X-OntoTwin-UE-Project-Id: <ue_project_id>
X-OntoTwin-UE-Project-Name: <ue_project_name>

{
  "instance_id": "machine_01",
  "transform": {
    "tx": 1200.0,
    "ty": 300.0,
    "tz": 0.0,
    "rx": 0.0,
    "ry": 0.0,
    "rz": 90.0,
    "sx": 1.0,
    "sy": 1.0,
    "sz": 1.0
  }
}
```

约定：

- `rx=Roll`，`ry=Pitch`，`rz=Yaw`，与现有 `writeback.py` 和 `ApplySpatialFromSnapshot` 保持一致。
- 绑定 CAD 构件的实例由后端逆变换回规范系。
- 自由实例直接写 `raw_state`。
- 保存成功后以后端响应里的 `snapshot` 为准，立即对齐本地 Actor。
- 本轮不新增 runtime 专用保存接口。

绑定接口：

```http
GET /api/v2/ue/binding_status
POST /api/v2/ue/bind_active_project
```

绑定语义：

- 绑定目标永远是后端当前已激活数据集。
- Runtime Editor 不提供切换 active dataset 的能力。
- UI 必须提示用户“即将绑定到后端当前激活数据集”；后续建议 `binding_status` 返回 active dataset id/name，降低误绑风险。

---

## 5. 配置项

以下属性放在 `ATwinSceneManager`：

| 配置 | 默认值 | 说明 |
| :-- | :-- | :-- |
| `bEnableRuntimeEditor` | `true` | 默认启用 Runtime Editor；只读部署可关闭 |
| `ToggleEditKey` | `F8` | 进入/退出编辑模式；打包 exe 默认入口 |
| `AlternateToggleEditKey` | `F10` | 备用进入/退出编辑模式；PIE 中推荐使用，避免 F8 被 UE Editor Eject 吃掉 |
| `SaveKey` | `Ctrl+S` | 保存当前选中实例变更 |
| `CancelKey` | `Esc` | 取消当前编辑 |
| `EditModePollInterval` | `1.5` | 编辑模式下降低轮询频率 |
| `GridSnapSizeCm` | `50` | 网格吸附步长 |
| `WallSnapDistanceCm` | `100` | 靠墙吸附检测距离 |
| `WallTag` | `OntoTwinWall` | 墙体/结构识别标签 |
| `bEnableWallSnap` | `true` | 默认开启靠墙吸附 |
| `bEnableGridSnap` | `false` | 默认关闭网格吸附 |

---

## 6. 风险与约束

- 打包 exe 不能依赖 Editor API。所有 Runtime Editor 代码必须在非 Editor 构建可用。
- 靠墙吸附依赖 UE 场景里的墙体 Tag 或碰撞配置；项目没有配置时只能自由拖拽。
- 当前没有后端多人编辑锁；多个客户端同时编辑同一实例时以后提交者为准。
- 数据集绑定依赖后端当前 active dataset，用户需先在 OntoTwin Web 激活目标数据集。
- 如果后端不可达，保存失败但本地 Actor 已发生变化，必须保留 dirty 提示并允许重试或取消恢复。
- 如果 `ATwinInstance` 的网格没有可靠 Bounds，靠墙偏移只能使用 Actor Bounds 近似。
- 如果资产 Pivot 偏离真实设备中心，MVP 不做自动修正；后续通过资产治理或 `edit_pivot_offset` 解决。
- 本轮不处理项目特定约束，例如设备只能沿轨道移动、只能落在工位锚点。

---

## 7. 验收标准

### 7.1 PIE 验收

- 能进入和退出 Runtime Edit Mode。
- 能点击选中 `ATwinInstance`。
- 能看到并拖拽可交互 runtime gizmo。
- 选中后实例空间变换不会被后端轮询覆盖。
- 编辑模式下整体轮询降频，但其他实例仍可更新。
- 能通过 gizmo 执行世界 XY 平移和 Yaw 旋转。
- 拖拽时 Z 保持选中时高度。
- 点击取消后恢复编辑前 Transform。
- 点击保存后后端实例 `raw_state` 更新，本地 Actor 按返回 snapshot 对齐。

### 7.2 打包 exe 验收

- 打包构建不因 `GEditor`、`CallInEditor`、`UnrealEd` 依赖失败。
- Runtime Editor 默认可用，也可通过 `bEnableRuntimeEditor=false` 关闭。
- UMG 面板可显示选中实例、dirty 状态、绑定状态和保存结果。
- 未绑定数据集可在 runtime 内绑定当前 UE 工程到当前激活数据集。
- 已绑定但 UE 工程不匹配时禁止保存。
- 保存请求可携带 UE 工程绑定 Header。
- 后端不可达时不崩溃，并提示保存失败。

### 7.3 场景验收

- 带 `OntoTwinWall` Tag 的墙体参与靠墙吸附。
- 未带 Tag 的墙体不参与靠墙吸附。
- 无墙体配置时 gizmo 自由拖拽仍可用。
- dirty 未处理时禁止切换选中实例和退出编辑模式。
- 保存后重启 exe 或刷新后端快照，设备保持新位置。

---

## 8. MVP 之后

后续版本按优先级考虑：

1. 后端编辑锁 API，支持 Web/UE 多端冲突控制。
2. Blueprint 接口 `IOntoTwinEditable` / `IOntoTwinSnapSurface`，降低项目适配成本。
3. 独立 `ATwinRuntimeEditorManager` 或 ActorComponent 拆分。
4. 轨道、锚点、禁放区、碰撞避让等项目约束。
5. 显式贴地按钮、Z 轴移动、Local/World 坐标模式切换。
6. 多选、批量移动、复制、删除。
7. Undo/Redo 命令栈。
8. actual/desired 双态监控与 runtime actual 上报通道。
9. 3D/2D 双视图联动。
10. Pixel Streaming 作为远程真实画面入口。

---

## 9. Grill-me 决策记录

### 第一轮

1. MVP 不支持未迁移历史 Actor；历史 Actor 先走 FR-6 迁移流程。
2. 保存失败不自动回滚，保持 dirty，允许重试或取消。
3. 靠墙吸附 MVP 不依赖后端 layout，先用 UE Tag/碰撞通道。
4. MVP 不允许编辑 Scale。
5. 不保存 `.umap`，所有变更写回 OntoTwin 后端。

### 第二轮

1. MVP 集成进 `ATwinSceneManager`，不新增独立 Manager。
2. 输入使用 Manager 轮询并绑定 Actor 输入事件，不引入 Enhanced Input。
3. 编辑模式不暂停全局轮询，但降低轮询频率；当前实例只锁 spatial。
4. MVP 必须有可交互 gizmo；Actor 本体点击只负责选中。
5. Gizmo 使用世界 XY 平移，绕世界 Z 轴做 Yaw 旋转。
6. 拖拽平面使用选中实例当前 Z，高度保持不变。
7. Actor Pivot 是真实编辑中心，Bounds 只做辅助。
8. 编辑期间暂停选中实例本地行为动画，视觉/标签可继续更新。
9. 保存不做二次确认，依靠 dirty、保存结果和取消恢复。
10. dirty 未处理前禁止切换实例或退出编辑模式。
11. Runtime Editor 默认开启，但可配置关闭。
12. 未绑定数据集允许 runtime 首次绑定；已绑定不匹配则禁止保存。
13. Runtime Editor 只绑定/编辑当前 active dataset，不提供切换数据集。
14. 保存成功后以后端返回 snapshot 为准立即对齐本地 Actor。
15. MVP 不做 actual/desired 双态监控。
16. MVP 只做 Cancel，不做多步 Undo/Redo。
