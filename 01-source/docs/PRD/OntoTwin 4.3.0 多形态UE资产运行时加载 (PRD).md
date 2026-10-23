# OntoTwin 4.3.0 多形态 UE 资产运行时加载（PRD）

> 状态：已实现，待 UE 重启后运行验收  
> 日期：2026-08-18  
> 前置版本：OntoTwin 4.2 CAD 类型级 UE 资产选择与推荐  
> 适用范围：UE 编辑器、PIE、Development/Shipping 打包程序

## 1. 背景

OntoTwin 4.2 已把 CAD 类型与 UE 项目资产目录连接起来，支持对 StaticMesh、SkeletalMesh 和 Blueprint 进行推荐与人工确认。但当前 `ATwinInstance` 只有一个 `UStaticMeshComponent`，`/Game/...` 资产固定按 `UStaticMesh` 加载。结果是类型审核可以选中骨骼网格或 Actor Blueprint，运行时却只能显示占位 Cube。

4.3.0 负责补齐推荐闭环的最后一段：同一条 `asset_id / ue_asset_path` 数据契约能够在 UE 中正确实例化静态网格、骨骼网格或 Actor Blueprint，并继续复用现有实例生命周期、坐标同步、运行时编辑器和场景交互能力。

## 2. 目标

1. `ATwinInstance` 支持 StaticMesh、SkeletalMesh、Actor Blueprint 三种单资产表现。
2. 三种表现能够在同一个实例容器内热切换，不重建实例身份。
3. Blueprint 以子 Actor 运行，正常执行 Construction Script、BeginPlay、Tick、动画和特效。
4. SkeletalMesh 直接绑定时正确显示参考姿势、材质与 PhysicsAsset。
5. 三种表现统一支持坐标、显隐、加载/卸载、射线选择、聚焦、Runtime Gizmo 和顶部信息面板。
6. 编辑器、PIE 与打包后的 exe 行为一致；扫描目录具备明确的 Cook 覆盖检查。
7. 保留现有 `asset_id / ue_asset_path` 字符串契约，不修改 ProjectStore 或映射存储结构。

## 3. 非目标

- 不把 AnimSequence、AnimMontage、Animation Blueprint 作为独立类型资产绑定。
- 不为直接绑定的 SkeletalMesh 自动猜测或搜索动画。
- 不强制覆写 Actor Blueprint 内部的材质、动画状态机或业务逻辑。
- 不支持 Widget、ActorComponent、Level Blueprint、Pawn、Character、Controller 等非普通表现 Actor。
- 不改变 `assembly_v1` 的多 StaticMesh 部件协议。
- 不引入新的异步加载框架；4.3.0 延续当前本地烘焙资产的同步加载方式。

## 4. GrillMe 评审结论

| 决策 | 结论 |
|---|---|
| 版本边界 | 4.2 负责推荐和确认；4.3.0 负责运行时多形态实例化 |
| 运行环境 | 同时支持编辑器、PIE、Development/Shipping exe |
| Blueprint 宿主 | 保留 `ATwinInstance`，使用 `UChildActorComponent` 承载 Blueprint |
| Blueprint 范围 | 仅允许非抽象、非废弃的普通 `AActor` 生成类；拒绝 Pawn、Controller、LevelScriptActor 等 |
| Blueprint 生命周期 | 正常运行构造脚本、BeginPlay 和 Tick；内部逻辑由资产作者负责 |
| SkeletalMesh 动画 | 直接绑定只保证参考姿势；需要动画时绑定封装后的 Actor Blueprint |
| 热替换 | 保留实例 ID 和外层 Actor，只替换内部表现 |
| 可见性 | Representable 的 `is_visible=false` 卸载表现；Visual 的 `is_visible=false` 只隐藏 |
| Cook | 扫描目录必须进入 Cook；提供显式配置入口与运行时诊断，不把缺失留到打包后猜测 |
| 测试 | 不新增自动化测试；必须完成 C++ 编译和正式人工验收记录 |

## 5. 运行时架构

### 5.1 稳定容器

`ATwinSceneManager` 仍然只注册和管理 `ATwinInstance`。实例 ID、后端快照、场景树、运行时编辑状态、标签与信息面板都留在容器上。

`ATwinInstance` 内部增加三种互斥表现：

```text
ATwinInstance
├─ UStaticMeshComponent       StaticMesh / glTF / assembly_v1 基座
├─ USkeletalMeshComponent     直接绑定 SkeletalMesh
└─ UChildActorComponent       直接绑定 Actor Blueprint
```

任意时刻单资产模式只允许一种主表现处于激活状态。`assembly_v1` 继续使用现有动态 StaticMesh 部件数组。

### 5.2 资产识别

对于 `/Game/...` 和 `/Engine/...` 路径，加载器依次执行确定性识别：

1. 尝试加载 `UStaticMesh`；
2. 尝试加载 `USkeletalMesh`；
3. 把 Blueprint 对象路径规范化为生成类路径 `Package.Asset_C`，加载 `UClass` 并校验其是否为允许的 Actor 类；
4. 全部失败后显示占位 Cube，并记录每个失败阶段。

`artstudio:` 与本地 glb/gltf 继续走原有静态网格分支，不改变语义。

### 5.3 Blueprint 子 Actor

- 使用 `UChildActorComponent` 创建和销毁子 Actor，避免外部 Actor 泄漏。
- 子 Actor 相对容器使用 Identity Transform；Blueprint 组件自身的默认相对变换保持不变。
- 子 Actor 的 Owner/AttachParent 可以向上解析到 `ATwinInstance`，现有射线交互链继续生效。
- 聚焦和 Runtime Gizmo 包围盒必须显式合并子 Actor 的 PrimitiveComponent bounds。
- `I3D_Visual.is_visible` 同步到子 Actor；Representable 卸载时清空 ChildActorClass。

### 5.4 SkeletalMesh

- 新增 `USkeletalMeshComponent`，默认隐藏且不占用主表现。
- 设置 SkeletalMesh 后使用参考姿势；UE 自带的材质和 PhysicsAsset 正常生效。
- 继续忽略 Pawn 碰撞通道，保留 Visibility 射线选择。
- 原始材质缓存与恢复改为针对当前激活的 MeshComponent，兼容 StaticMesh 与 SkeletalMesh。

### 5.5 热切换

当快照中的 `asset_id` 变化时：

1. 停止并清理旧单资产表现；
2. 保留 `ATwinInstance`、实例 ID、Actor Transform、运行时编辑状态和信息面板；
3. 加载新表现；
4. 重新应用当前加载状态和视觉显隐；
5. 加载失败时显示占位 Cube，但保留原始 `AssetPath` 便于后续修复后重载。

## 6. 资产目录契约

UE 目录同步在现有字段之外补充：

```json
{
  "asset_kind": "Blueprint",
  "generated_class_path": "/Game/Art/.../BP_LY.BP_LY_C",
  "runtime_loadable": true,
  "runtime_reason": "Actor Blueprint"
}
```

- StaticMesh、SkeletalMesh 默认 `runtime_loadable=true`。
- Blueprint 只有生成类通过 Actor 白名单校验时才为 true。
- Blueprint 类别不合格或生成类不可解析时仍可在目录中展示，但不可确认绑定，并显示原因。
- 后端不再仅依据 `asset_kind=Blueprint` 判断支持状态，而是读取 UE 上报的 `runtime_loadable`。

## 7. Cook 与打包

运行时按字符串加载的资产没有硬引用，Cooker 不会自动发现。正式版本要求：

- `AssetRoots` 中的 `/Game/...` 扫描目录加入 `DirectoriesToAlwaysCook`；
- 插件提供编辑器按钮“配置扫描目录用于打包”，只在用户显式操作时修改宿主项目配置；
- 目录同步时检查 Cook 覆盖，缺失时输出明确告警；
- 当前 `DigitalFactoryBase_SCC` 项目加入 `/Game/Art`；
- 打包验收必须至少覆盖一个 Actor Blueprint 与一个 SkeletalMesh。

## 8. 兼容性

- StaticMesh、glTF、ArtStudio 和 `assembly_v1` 保持现有行为。
- 不增加后端存储字段，不迁移历史项目数据。
- 旧资产目录没有 `runtime_loadable` 时：StaticMesh/SkeletalMesh 可按类型兼容；Blueprint 保持“需重新同步目录”状态，避免误放行无效蓝图。
- 4.2 的推荐和人工确认逻辑继续保留；运行时支持状态由新的目录元数据驱动。

## 9. 诊断与失败回退

日志至少包含：实例 ID、输入路径、推断资产类型、规范化对象/生成类路径、失败阶段和回退结果。

失败场景包括：

- 路径不存在或资产未 Cook；
- Blueprint 生成类路径无效；
- Blueprint 不是允许的 Actor 类；
- SkeletalMesh 加载失败；
- ChildActor 创建失败。

所有失败均不得导致崩溃；容器保留并显示占位 Cube。

## 10. 验收标准

1. 同一类型分别绑定 StaticMesh、SkeletalMesh、Actor Blueprint，PIE 中均正确出现。
2. 水幕喷淋绑定 `BP_LY` 后 Blueprint 自身动画/特效正常运行。
3. 直接绑定“淋雨” SkeletalMesh 时正确显示参考姿势，不显示 Cube。
4. 三种类型之间热切换后实例 ID、位置、缩放和信息面板不丢失。
5. Blueprint 子组件可被射线选中，并正确解析为所属 TwinInstance。
6. 聚焦、Runtime Gizmo 和顶部信息面板使用真实表现包围盒。
7. Representable 卸载后 Blueprint 不再 Tick；重新加载时可重新创建。
8. 未 Cook 的路径输出明确诊断并回退 Cube，不崩溃。
9. 打包 exe 中 Blueprint 与 SkeletalMesh 均可加载。
10. 既有 StaticMesh、glTF、ArtStudio 与 assembly_v1 行为无回归。

## 11. 后续版本

- 异步 StreamableManager 加载与大资产首屏性能治理。
- Blueprint 可选的 OntoTwin 表现接口，用于接收业务参数和行为事件。
- SkeletalMesh + AnimClass/AnimationAsset 的显式组合配置。
- 组合 Actor/Prefab 的独立资产协议。
