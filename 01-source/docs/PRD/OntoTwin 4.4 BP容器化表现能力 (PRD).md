# OntoTwin 4.4 BP 容器化表现能力（PRD）

| 项目 | 内容 |
|---|---|
| PRD 编号 | `PRD-OT-4.4-001` |
| 状态 | 已确认，进入实施 |
| 目标版本 | OntoTwinSync 4.4.0 |
| 当前基线 | OntoTwinSync 4.3.0 |
| 确认日期 | 2026-08-20 |

## 1. 目标

让一个 OntoTwin 实例同时拥有两层 UE 表现：

1. `ATwinInstance` 继续作为孪生父 Actor，负责实例 ID、后端快照、空间变换、加载/显隐、选择与生命周期。
2. 项目 Blueprint 作为容器子 Actor，负责项目既有的组件、碰撞、高亮、动画和交互。
3. 具体设备资产继续由 `asset_id` 指定，并注入容器 Blueprint 的目标表现槽位。

SCC 首个落地目标：

```text
ATwinInstance(ZJCXJ001)
└── BP_Item_base_SCC_Machine_C
    ├── StaticMesh = 对应 XJCG 型号的具体 Static Mesh
    ├── BPC_Highlight
    └── 项目原有设备逻辑
```

本能力解决“实例生成后使用哪个项目 BP 容器运行”。它不负责判断 93 台 Main 缺口该绑定到哪个 CAD 点，也不自动修复设备清单和资产型号之间的错误映射。

## 2. 当前 4.3.0 已有能力

现有代码已经具备以下基础：

- `ATwinInstance` 内已有 `UChildActorComponent`。
- `asset_id` 指向普通 Actor Blueprint 时，能规范化 `_C` 路径并生成子 Actor。
- 子 Actor 使用单位相对变换，会继承父实例的世界变换。
- `I3D_Visual.is_visible` 已同步到子 Actor。
- 包围盒计算已包含 Blueprint 子 Actor。
- 鼠标射线命中子 Actor 后，场景选择逻辑会沿 Attach Parent / Owner 回溯到 `ATwinInstance`。
- 资产热替换、直接 Static Mesh、Skeletal Mesh、运行时 glTF 和 `assembly_v1` 已有各自加载路径。

当前缺口：一个实例只有 `asset_id` 这一条主资产路径。若它指向 BP，插件不知道 BP 内应该显示哪个具体设备模型；若它指向具体模型，插件又不会生成项目 BP 容器。

## 3. 建议的数据协议

在 `I3D_Representable` 保留 `asset_id` 原语义，并增加容器字段：

```json
{
  "I3D_Representable": {
    "asset_id": "/Game/SCC/Art/.../SM_XJCG169.SM_XJCG169",
    "file_number": "XJCG169",
    "container_blueprint_id": "/Game/SCC/Program/Function/Machine/BP_Item_base_SCC_Machine.BP_Item_base_SCC_Machine",
    "container_slot": "primary",
    "is_visible": true
  }
}
```

字段语义：

| 字段 | 语义 | 是否必填 |
|---|---|---|
| `asset_id` | 注入容器的具体表现资产；无容器时仍是直接加载资产 | 是 |
| `container_blueprint_id` | 需要生成的普通 Actor Blueprint | 否 |
| `container_slot` | 容器内的逻辑槽位，默认 `primary` | 否 |
| `is_visible` | 运行时加载状态 | 是 |

兼容规则：

- 没有 `container_blueprint_id`：完全沿用 4.3 直接资产加载路径。
- 有 `container_blueprint_id`：进入 BP 容器模式，`asset_id` 不再占用父 Actor 的 `TwinMesh`，而是注入子 Actor。
- `render_parts` 与 BP 容器模式在首版互斥；若同时出现，后端校验拒绝，避免不明确的优先级。
- 容器路径非法、类不可生成或注入失败时显示明确占位物并输出结构化错误，不静默显示错误型号。

## 4. 建议的容器适配方式

不建议让 `ATwinInstance` 永久依赖组件名 `StaticMesh`。建议插件新增一个宿主适配组件：

```text
UTwinRepresentationHostComponent
```

项目 BP 只需一次性添加该组件，并在详情面板配置：

```text
SlotName = primary
TargetStaticMeshComponent = StaticMesh
```

运行时流程：

```text
ATwinInstance 创建容器 BP
→ 查找 UTwinRepresentationHostComponent
→ 按 container_slot 找到目标槽位
→ 加载 asset_id 指定的具体 Static Mesh
→ HostComponent 注入目标组件
→ 回传成功/错误结果
```

这样 C++ 不依赖美术命名；组件重命名后，BP 内的组件引用仍可维护。为了支持项目自定义逻辑，可同时预留 Blueprint 事件：

- `OnTwinRepresentationConfigured`
- `OnTwinVisualStateChanged`
- `OnTwinBehaviorStateChanged`
- `OnTwinRepresentationCleared`

不建议首版使用“找第一个 StaticMeshComponent”作为兜底，因为 `BP_Item_base_SCC_Machine` 同时包含 `StaticMesh`、`StaticMesh1` 和 `SkeletalMesh`，自动猜测可能把型号写入错误组件。

## 5. 后端配置与继承

建议把 `container_blueprint_id` 作为 ObjectType 的表现配置，而不是写死在 UE 插件中：

- 同一设备类型的所有实例默认使用同一个容器。
- SCC 可以批量把设备 ObjectType 设置为 `BP_Item_base_SCC_Machine`。
- 其他项目或非设备类型保持空值，不受 SCC 路径污染。
- 项目迁移时，该配置随实例的 `render_config` 冻结副本一起保存。

建议的解析优先级：

```text
实例表现覆盖
> 当前 ObjectType 实时配置
> 实例创建时冻结的 render_config
> 无容器（兼容 4.3 直接表现）
```

后端快照构建必须原样传递 `container_blueprint_id` 与 `container_slot`。类型资产热更新时：

- 只有 `asset_id` 改变：复用原子 Actor，仅替换目标 Mesh。
- `container_blueprint_id` 改变：销毁旧子 Actor，创建新容器并重新注入。
- 取消容器字段：销毁子 Actor，回到直接资产模式。

## 6. UE 运行时状态机

建议新增独立状态，而不是继续把“容器 BP”和“具体 Mesh”压进现有单个 `AssetPath`：

```text
None
DirectStaticMesh
DirectSkeletalMesh
DirectBlueprintActor（兼容旧语义）
RuntimeGltf
Assembly
ContainerBlueprint
```

容器模式至少缓存：

- 当前 `container_blueprint_id`
- 当前 `container_slot`
- 当前注入 `asset_id`
- 当前 HostComponent 弱引用
- 最近一次配置结果与错误码

关键生命周期：

1. Manager 从首个快照同时解析 `asset_id` 和容器字段，避免先显示裸 Mesh 再切换 BP 的一帧闪烁。
2. 父 Actor 是唯一空间变换源；子 Actor 始终保持单位相对变换。
3. `I3D_Representable.is_visible=false` 按现有语义卸载表现；重新加载时重建子 Actor 并注入。
4. `I3D_Visual.is_visible` 只隐藏，不卸载。
5. 子 Actor 命中继续回溯到父实例，沿用现有选择链路。
6. 清理或热切换时必须清除 Host 引用、子 Actor 和父级占位表现，不能同时残留两套模型。

## 7. 状态、碰撞和性能边界

首版建议：

- 保留子 BP 自己的碰撞与 Tick 配置，不由插件全局强制关闭。
- 父 `ATwinInstance` 继续负责位置、旋转、缩放；子 BP 不写世界变换。
- 插件只保证可见性、选择归属和具体 Mesh 注入。
- 材质变体、报警状态、动画与 FX 通过 Host 的可选 Blueprint 事件转发；未实现事件时不影响基础显示。
- 对约 300 台设备做 PIE 性能采样后，再决定是否增加“空闲时禁用子 BP Tick”的显式选项。

## 8. 计划修改范围

### UE 插件

- 新增 `UTwinRepresentationHostComponent` 与槽位配置结构。
- 扩展 `ATwinInstance`：容器加载、注入、热替换、清理、状态转发和错误状态。
- 扩展 `ATwinSceneManager`：首快照解析容器字段并传给实例初始化。
- 增加自动化测试：旧快照兼容、容器成功注入、错误槽位、资产热替换、容器热替换、显隐、选择回溯。
- 更新插件 README 与版本号。

### 后端

- ObjectType / `render_config` 保存容器字段。
- `I3D_Representable` 快照下发容器字段。
- 增加 `render_parts` 与容器模式互斥校验。
- 保持旧项目数据可读，不要求迁移。

### 前端

- 类型级资产配置中增加“容器 Blueprint”与“槽位”。
- 实例页显示最终生效的容器来源。
- 提供按设备类型批量应用 SCC Machine 容器的操作，避免逐类型填写。

### SCC Blueprint 资产

- 给 `BP_Item_base_SCC_Machine` 添加 `UTwinRepresentationHostComponent`。
- 把 `primary` 槽位指向现有 `StaticMesh` 组件。
- 验证 `StaticMesh1`、`SkeletalMesh`、`BPC_Highlight` 的原行为没有被破坏。

## 9. 分阶段验收

### A. 协议与兼容

- 旧快照不含容器字段时，显示结果与 4.3.0 一致。
- SCC 设备快照能同时看到具体 `asset_id` 与容器 BP 路径。

### B. 单实例功能

- `ZJCXJ001` 只生成一个 `ATwinInstance` 和一个 Machine 子 BP。
- 子 BP 的 `StaticMesh` 等于目标 XJCG 资产。
- 位置、旋转、缩放与原直接 Mesh 模式一致，无双重偏移。
- 切换型号时不重建父实例；切换容器时只重建子 Actor。
- 加载/显隐、点击选择、包围盒和 Runtime Editor 操作正常。

### C. SCC 批量回归

- 在测试关卡 PIE 中抽检不同设备型号与镜像缩放实例。
- 对约 300 台设备记录 Actor 数、帧时间、内存与日志错误。
- 与 Main 的设备外观和变换做自动对比。

### D. 最终业务验收

- 设备“是否出现、型号是否正确、点位是否正确”仍按 Main 对标清单验收。
- BP 容器能力通过后，再处理尚未绑定或错绑的 93 台业务缺口；两项工作分别统计，避免把能力缺陷与数据缺口混在一起。

## 10. 已确认的实施决策

1. 首轮完成 UE 插件、后端、前端和 SCC Machine BP 的完整闭环。
2. `BP_Item_base_SCC_Machine` 一次性添加插件 `UTwinRepresentationHostComponent`；不使用“第一个 StaticMesh”猜测。
3. 容器按 ObjectType 管理并支持批量应用；首版不提供单实例容器覆盖。
4. 首版只支持单 Static Mesh 注入，并与 `render_parts` 互斥。
5. 首版保证模型注入、空间变换、加载/显隐、选择与热替换；状态事件只建立转发契约，不在本轮定义项目业务映射。
6. 子 BP 保留自身 Tick 与碰撞配置，插件不做全局强制关闭。
7. 只修改 4.3.0 活动主线，不同步修改 `SCC2/scc2` 旧副本。
