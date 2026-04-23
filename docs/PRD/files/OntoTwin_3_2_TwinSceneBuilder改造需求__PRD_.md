# OntoTwin 3.2 TwinSceneBuilder 改造需求说明书（PRD）

| 字段 | 内容 |
|---|---|
| **文档版本** | v3.2-r1 |
| **日期** | 2026-04-17 |
| **状态** | 草稿（待审阅） |
| **模块代号** | TwinSceneBuilder |
| **归属** | UE 引擎侧（C++ / Blueprint / Python） |
| **父版本** | 2.5 TwinSceneBuilder |
| **依赖** | 3.0 USD 导出 API / 3.1 Scene 管理 API |

---

## 一、改造背景

### 1.1 原有能力（2.5）

TwinSceneBuilder 原本的数据流：

```
DXF 图纸 → Python (ezdxf, 本地) → JSON → UE (TwinSceneBuilder) → 场景生成
```

**能力**：
- 解析 DXF 中的墙、地板、柱子图层
- 生成 UE RuntimeMesh（墙/地板）和 HISM 实例（柱子）
- 纯前端算法驱动，不依赖中间层或后端

### 1.2 3.0 之后的变化

3.0 引入 Nexus Scene 概念 + USD 导出能力后，原有链路需要两个变化：

1. **DXF 解析从 UE 侧 Python 迁移到后端服务**（由 3.0 的 F3 承担）
2. **实例摆放从"硬编码 JSON"改为"Nexus Scene API 拉取"**

### 1.3 改造目标

让 TwinSceneBuilder 成为 Nexus Scene 的**视觉渲染端**：

```
                        ┌─ 结构（DXF 由后端解析） ─┐
Nexus Scene (3.1) ──────┤                          ├──→ 场景 JSON ──→ UE (TwinSceneBuilder)
                        └─ 实例（本体数据库） ─────┘                         ↓
                                                                    场景生成 + 可视化预览
                                                                            ↓
                                                                    (可选) 回写位置修改
```

同时 USD 导出**不经过 UE**，由后端统一生成（路径 Z 方案）。UE 仅作为：
- 视觉预览
- 美术调整
- 调整后回写到 Nexus
- 提供"导出 USD"入口按钮（按钮实际调用的是后端 API）

---

## 二、功能需求

### 2.1 功能清单

| 功能 ID | 功能名称 | 类型 | 优先级 |
|---|---|---|---|
| U1 | Scene 数据拉取组件（替代本地 JSON 源） | 新增 | P0 |
| U2 | 结构数据渲染（墙/地板/柱子） | 改造 | P0 |
| U3 | 实例资产加载（从资产库取 FBX） | 改造 | P0 |
| U4 | 本体追溯元数据挂载（Actor Tag） | 新增 | P0 |
| U5 | "加载场景"菜单 | 新增 | P0 |
| U6 | "导出 USD"编辑器按钮 | 新增 | P1 |
| U7 | 美术位置回写功能 | 新增 | P1 |
| U8 | 坐标系/单位转换 | 新增 | P0 |
| U9 | 资产缺失占位机制 | 新增 | P1 |

---

### 2.2 【U1】Scene 数据拉取组件

**新增类**：`UTwinSceneDataSource`（`UActorComponent` 子类）

**职责**：
- 从 Nexus 拉取 Scene 的完整数据（含结构 + 实例）
- 解析响应为 UE 可用的数据结构
- 缓存到本地，支持离线打开最后一次拉取的场景

**接口**：

```cpp
UCLASS(ClassGroup=(Twin), meta=(BlueprintSpawnableComponent))
class TWINSCENEBUILDER_API UTwinSceneDataSource : public UActorComponent
{
    GENERATED_BODY()

public:
    // 配置：Nexus 服务器地址与认证
    UPROPERTY(EditAnywhere, Category="Twin|Source")
    FString NexusBaseUrl = "http://localhost:5000";

    UPROPERTY(EditAnywhere, Category="Twin|Source")
    FString AuthToken;

    UPROPERTY(EditAnywhere, Category="Twin|Source")
    FString SceneId;

    // 主动拉取
    UFUNCTION(BlueprintCallable, Category="Twin|Source")
    void FetchSceneData();

    // 事件：数据拉取完成
    UPROPERTY(BlueprintAssignable)
    FOnSceneDataReady OnSceneDataReady;

    UPROPERTY(BlueprintAssignable)
    FOnSceneDataError OnSceneDataError;
};
```

**HTTP 请求**：`GET /api/v3/scenes/{scene_id}/ue_data`

**预期响应结构**：

```json
{
  "scene": {
    "id": "warehouse_demo_01",
    "display_name": "仓库演示场景",
    "up_axis": "Z",
    "unit": "meter",
    "bounds": {...}
  },
  "structure": {
    "type": "dxf_generated",
    "entities": [
      {
        "id": "wall_001",
        "layer": "1.21-墙体",
        "generate_type": "PROCEDURAL_WALL",
        "data": {
          "path": [[0,0],[1500,0],[1500,800]],
          "height": 4500,
          "thickness": 240
        }
      },
      {
        "id": "column_p1",
        "layer": "1.20-柱子",
        "generate_type": "INSTANCE",
        "data": {
          "mesh_id": "SM_Std_Column_500",
          "transform": { "loc": [0.5, 0.5, 0], "rot": [0,0,90], "scale":[1,1,1] }
        }
      }
    ]
  },
  "instances": [
    {
      "id": "shelf_001",
      "object_type_rid": "ri.obj.shelf",
      "asset": {
        "file_number": "SM_Std_Shelf_200",
        "ue_asset_path": "/Game/Assets/Shelves/SM_Std_Shelf_200",
        "fallback_bounding_box": {"x":0.8,"y":2.0,"z":2.0}
      },
      "transform": {
        "loc": [1.5, 2.0, 0.0],
        "rot": [0, 0, 90],
        "scale": [1, 1, 1]
      },
      "ontology_metadata": {
        "instance_id": "shelf_001",
        "object_type_rid": "ri.obj.shelf",
        "file_number": "SM_Std_Shelf_200",
        "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_PhysicsHint"],
        "collision_type": "static"
      }
    }
  ]
}
```

> [!NOTE]
> **坐标单位是米**。UE 侧必须做 × 100 的换算。详见 U8。

---

### 2.3 【U2】结构数据渲染（改造）

**保持 2.5 原有的 RMC/HISM 渲染能力**，但数据源改变：

| 来源 | 2.5 | 3.0 |
|---|---|---|
| `entities` 数组 | 本地 JSON 文件 | `UTwinSceneDataSource` 拉取后的内存数据 |
| 墙体/地板材质 | 本地资产引用 | 可选：从 Nexus 返回的参数动态实例化 |
| 图层映射 | 硬编码 | 保持硬编码（3.0 不动） |

**重要**：UE 不再需要 `ezdxf` 的 Python 脚本或任何 DXF 解析逻辑。2.5 里的这部分代码可以**整个删除**。

---

### 2.4 【U3】实例资产加载

**处理流程**：

```cpp
for (const FTwinInstanceData& InstanceData : SceneData.Instances)
{
    // 1. 解析资产路径
    FString UeAssetPath = InstanceData.Asset.UeAssetPath;
    
    // 2. 尝试加载
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *UeAssetPath);
    
    if (Mesh)
    {
        // 3a. 资产存在：Spawn Actor，应用 Transform
        AStaticMeshActor* Actor = SpawnInstanceActor(InstanceData, Mesh);
        AttachOntologyMetadata(Actor, InstanceData.OntologyMetadata);
    }
    else
    {
        // 3b. 资产缺失：生成占位 Cube（见 U9）
        SpawnPlaceholder(InstanceData);
    }
}
```

**资产加载策略**：
- 优先使用 Nexus 返回的 `ue_asset_path`（如 `/Game/Assets/Shelves/SM_Std_Shelf_200`）
- 如果路径为空，UE 侧发起一次资产导入请求（调用 Nexus API 下载 FBX 并做 UE 导入）—— **第一版简化为仅支持预导入好的资产**，FBX 动态导入不做

---

### 2.5 【U4】本体追溯元数据挂载

**目的**：让每个 Actor 都知道自己对应本体里哪个 Instance，便于回写和导出追溯。

**实现方式**：用 `UActorComponent` 挂载元数据，而不是 Actor Tag（Tag 是字符串，难以表达结构化数据）。

**新增组件**：`UTwinOntologyMetadataComponent`

```cpp
USTRUCT(BlueprintType)
struct FTwinOntologyMetadata
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FString InstanceId;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FString ObjectTypeRid;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FString FileNumber;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FString> Interfaces;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FString CollisionType;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FString SourceSceneId;
};

UCLASS(ClassGroup=(Twin), meta=(BlueprintSpawnableComponent))
class TWINSCENEBUILDER_API UTwinOntologyMetadataComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Twin|Ontology")
    FTwinOntologyMetadata Metadata;

    // 快速查询
    UFUNCTION(BlueprintPure, Category="Twin|Ontology")
    bool IsGraspable() const { return Metadata.CollisionType == "graspable"; }
};
```

**使用**：

```cpp
void USceneBuilder::AttachOntologyMetadata(AActor* Actor, const FTwinOntologyMetadata& Data)
{
    auto* Comp = NewObject<UTwinOntologyMetadataComponent>(Actor);
    Comp->Metadata = Data;
    Comp->RegisterComponent();
    Actor->AddInstanceComponent(Comp);
}
```

---

### 2.6 【U5】编辑器菜单：加载场景

在 UE 编辑器的菜单栏新增 **"OntoTwin"** 菜单：

```
OntoTwin
 ├── 加载场景...          ← 打开对话框选择 Scene
 ├── 刷新当前场景         ← 重新拉取并更新
 ├── ─────────────────
 ├── 导出 USD            ← U6
 ├── 回写位置修改         ← U7
 ├── ─────────────────
 └── 设置...             ← 配置 Nexus 地址与 Token
```

**"加载场景..." 对话框**：

```
┌─────────────────────────────────────────────┐
│ 加载 OntoTwin 场景                           │
├─────────────────────────────────────────────┤
│ 数据集：[标准实践（内置 Demo）▼]             │
│                                              │
│ 可用场景：                                    │
│   ◉ 仓库演示场景 (warehouse_demo_01)         │
│   ○ 训练场景 A   (training_a_01)             │
│   ○ 产线演示    (factory_test0316)           │
│                                              │
│ □ 加载前清空当前 Level                        │
│                                              │
│         [取消]    [加载]                      │
└─────────────────────────────────────────────┘
```

点击"加载"后：
1. 清空当前 Level（若勾选）
2. 创建 `ATwinSceneManager` Actor 到 Level 中
3. 设置 `UTwinSceneDataSource` 的 `SceneId`
4. 调用 `FetchSceneData()`
5. 拉取完成后依次生成结构 + 实例
6. 完成后弹出通知："场景已加载，共 X 个结构 + Y 个实例"

---

### 2.7 【U6】"导出 USD"编辑器按钮

> [!IMPORTANT]
> 这个按钮**不在 UE 侧实际执行 USD 导出**，而是调用后端 3.0 的导出 API。UE 侧只是一个入口。

**行为**：

```
用户点击"导出 USD"
  ↓
UE 侧弹窗提示：
  "即将导出场景 'warehouse_demo_01' 的最新状态。
   注意：UE 侧未回写的位置修改将不会包含在导出中。
   
   □ 先执行回写      ← 勾选后先调用 U7
   □ 重建资产缓存
   
   [取消]    [导出]"
  ↓
若勾选"先执行回写"：先调用 U7 流程
  ↓
调用 POST /api/v3/scenes/{scene_id}/export
  ↓
轮询 job 状态
  ↓
下载 USD 文件到用户指定路径（用 UE 原生文件对话框选择）
  ↓
完成提示
```

---

### 2.8 【U7】美术位置回写功能

**背景**：美术在 UE 里调整了一个货架的位置，希望这个修改同步回 Nexus，而不是只停留在本地 Level 里。

**回写范围**（见架构决策）：
- ✅ 位置（translation）
- ✅ 旋转（rotation）
- ✅ 缩放（scale）
- ❌ 新增 Instance
- ❌ 删除 Instance
- ❌ 资产替换

**触发方式**：

```
方式 A：主动触发
  OntoTwin 菜单 → 回写位置修改
    ↓
  扫描所有带 UTwinOntologyMetadataComponent 的 Actor
    ↓
  对比 Actor 当前 Transform 与 Metadata 里记录的原始 Transform
    ↓
  列出"已修改"的 Actor 列表，确认弹窗：
    "检测到 5 个实例位置已修改：
     - shelf_001:  (1.5, 2.0, 0) → (1.8, 2.0, 0)
     - box_003:    (3.0, 2.0, 1) → (3.2, 2.5, 1)
     ...
     
     是否回写到 Nexus？
     [取消]  [全部回写]"
    ↓
  调用 POST /api/v3/scenes/{scene_id}/placements/update

方式 B：被动提示（可选）
  监听 Actor 的位置变化，累计 N 秒无变化时，弹 toast 提示"检测到未回写的变更"
```

**回写 API 请求体**：

```json
{
  "updates": [
    {
      "instance_id": "shelf_001",
      "translation": [1.8, 2.0, 0.0],
      "rotation": [0, 0, 90],
      "scale": [1, 1, 1]
    },
    {
      "instance_id": "box_003",
      "translation": [3.2, 2.5, 1.0],
      "rotation": [0, 0, 0],
      "scale": [1, 1, 1]
    }
  ]
}
```

**后端行为**：
- 校验每个 Instance 归属当前 Scene
- 校验坐标在 Scene.bounds 内
- 批量更新 Instance.interfaces.I3D_Spatial
- 如果 Instance 属于多个 Scene：**默认修改默认坐标**；前端已在 3.1 §8.2 警告了这一点

---

### 2.9 【U8】坐标系与单位转换

**UE 默认**：cm + 左手系
**Nexus / USD 默认**：m + 右手系

**转换逻辑**：

```cpp
// Nexus → UE（加载时）
FVector NexusToUe(const FVector& NexusLoc)
{
    return FVector(
        NexusLoc.X * 100.0f,     // m → cm
       -NexusLoc.Y * 100.0f,     // Y 轴翻转（右手→左手）
        NexusLoc.Z * 100.0f
    );
}

FRotator NexusToUeRotation(const FVector& EulerXYZDeg)
{
    // UE 的 FRotator 是 Pitch-Yaw-Roll 顺序
    // 右手系 → 左手系时，绕 Y 和 Z 的角度取反
    return FRotator(
        EulerXYZDeg.Y,            // Pitch
       -EulerXYZDeg.Z,            // Yaw (取反)
       -EulerXYZDeg.X             // Roll (取反)
    );
}

// UE → Nexus（回写时）
FVector UeToNexus(const FVector& UeLoc)
{
    return FVector(
        UeLoc.X / 100.0f,
       -UeLoc.Y / 100.0f,
        UeLoc.Z / 100.0f
    );
}
```

> [!WARNING]
> 坐标系翻转是最容易出错的环节。强烈建议：
> - 写单元测试覆盖这两个函数
> - 第一次对接时，用一个简单场景（3 个货架在已知位置）做端到端验证
> - 在对话框里展示 Nexus 坐标和 UE 坐标两个值，便于肉眼 debug

---

### 2.10 【U9】资产缺失占位机制

**触发条件**：
- Nexus 返回的 `ue_asset_path` 在 UE 项目中不存在
- FBX 文件损坏无法加载
- 网络异常无法拉取

**占位策略**：

```cpp
void USceneBuilder::SpawnPlaceholder(const FTwinInstanceData& Data)
{
    // 1. 根据 fallback_bounding_box 生成对应尺寸的 Cube
    FVector BoxSize = Data.Asset.FallbackBoundingBox * 100.0f;  // m → cm
    
    // 2. Spawn 一个带醒目颜色（品红色）的 StaticMeshActor
    AStaticMeshActor* Placeholder = ...;
    ApplyMagentaMaterial(Placeholder);
    
    // 3. 挂 OntologyMetadata（保证后续回写仍然可用）
    AttachOntologyMetadata(Placeholder, Data.OntologyMetadata);
    
    // 4. 日志输出并在 Outliner 里打标记
    UE_LOG(LogTwin, Warning, 
        TEXT("Asset missing for instance %s, using placeholder. Expected: %s"),
        *Data.Id, *Data.Asset.UeAssetPath);
    
    Placeholder->Tags.Add("TwinPlaceholder");
}
```

**设计理念**：占位优于崩溃。场景不完整但可视化仍在，美术可以先调整其他物体，缺失的资产事后补充。

---

## 三、UE 端类结构总览

```
ATwinSceneManager (AActor)
  ├── UTwinSceneDataSource         ← U1 数据拉取
  ├── UTwinStructureBuilder         ← U2 结构生成（2.5 复用）
  ├── UTwinInstanceSpawner          ← U3 实例生成
  └── UTwinWritebackCollector       ← U7 回写收集

Spawned Actors in Level:
  AStaticMeshActor (Wall/Floor via RMC)
  AStaticMeshActor (Shelf/Box, UE Asset)
    └── UTwinOntologyMetadataComponent    ← U4 元数据

Editor Modules:
  FTwinEditorMenu               ← U5/U6 菜单
  FTwinExportCommand            ← U6 导出调用
  FTwinWritebackCommand         ← U7 回写调用
```

---

## 四、工作流示例

### 4.1 典型工作流：美术调整并导出

```
1. 打开 UE → OntoTwin 菜单 → 加载场景
2. 选择 "warehouse_demo_01" → 点击加载
3. 等待场景生成（结构 + 实例）
4. 美术拖动几个货架到理想位置
5. OntoTwin 菜单 → 回写位置修改
   - 确认变更清单
   - 点击回写
6. OntoTwin 菜单 → 导出 USD
   - 勾选"先执行回写"（如未操作第 5 步）
   - 点击导出
7. 选择保存路径，等待后端生成
8. 得到 .usda 文件，交给训练侧同事
```

### 4.2 典型工作流：首次场景预览

```
1. 产品团队在 Nexus 前端新建场景，上传 DXF，批量添加实例配坐标
2. 美术在 UE 里打开 OntoTwin 菜单 → 加载场景
3. 查看生成效果
4. 如有问题：
   - 视觉问题（材质、贴图）→ 在 UE 里调整资产，不触发回写
   - 位置问题 → 在 UE 里调整位置 → 回写
   - 资产缺失（占位 Cube）→ 联系资产库管理员补资产
5. 最后一次刷新场景验证
```

---

## 五、非功能需求

### 5.1 性能

| 指标 | 要求 |
|---|---|
| 加载场景（100 Instance） | ≤ 10s |
| 加载场景（1000 Instance） | ≤ 60s |
| 回写 100 个位置变更 | ≤ 5s |
| 单个资产加载 | ≤ 500ms |

### 5.2 离线能力

- 拉取过的 Scene 数据缓存到本地 `Saved/TwinCache/`
- 网络断开时，可加载最后一次缓存数据（提示"当前为离线模式"）
- 回写功能在离线时禁用

### 5.3 日志

- 每次加载/回写操作详细日志
- 日志级别：Verbose（详细）、Log（常规）、Warning（占位/缺失）、Error（失败）
- 日志文件：`Saved/Logs/OntoTwin.log`

---

## 六、验收标准

| 场景 | 通过条件 |
|---|---|
| 从 UE 菜单加载场景 | 场景正确生成，墙/货架位置与 Nexus 配置一致 |
| 坐标系转换正确 | 已知位置的货架在 UE 里的可视化位置正确 |
| 资产缺失时的占位 | 品红色 Cube 出现在正确位置，Outliner 标记 |
| 美术调整位置 → 回写 | Nexus 数据库里对应 Instance 坐标已更新 |
| UE 按钮触发 USD 导出 | 调用后端 API，下载到指定路径的 USD 文件 |
| 离线加载 | 网络断开时能加载最后一次缓存 |
| 大场景性能 | 1000 实例加载不崩溃，UI 不卡死（用 async spawn） |
| 元数据挂载 | 每个 Actor 都有 UTwinOntologyMetadataComponent，可在 Details 面板查看 |

---

## 七、范围外（Out of Scope）

- ❌ UE 侧 DXF 解析（迁移到后端）
- ❌ UE 侧 FBX 动态导入（第一版要求预导入）
- ❌ UE 侧 USD 导出（调用后端 API，不自己导）
- ❌ UE 与 Nexus 的实时双向同步（非 2.6 场景）
- ❌ 多人协同编辑
- ❌ Undo/Redo 回写变更栈
- ❌ 材质编辑器集成
- ❌ 资产替换功能

---

## 八、开发注意事项

### 8.1 插件化

建议把本模块打包为 UE 插件 `TwinSceneBuilder.uplugin`，便于：
- 在多个 UE 项目间复用
- 版本迭代独立
- 不污染项目主干代码

### 8.2 和 2.7/2.8 组件的关系

`PCBWorkerSyncComponent` (2.7) 和 `AGVPatrolComponent` (2.8) 与本模块**互相独立**：
- 2.7/2.8 负责运行态动态同步（工人/AGV 在跑）
- 3.2 负责设计态静态场景搭建与导出

在同一个 UE 项目里，三个模块可以共存，但不直接交互。

### 8.3 配置存储

Nexus 地址、Token 等配置存在：
- 项目级别：`Config/DefaultOntoTwin.ini`
- 用户级别：`Saved/Config/Windows/OntoTwin.ini`

用户级别优先于项目级别。敏感信息（Token）只存用户级别。

### 8.4 团队协作

在多人开发时：
- Scene 数据是服务端权威，不要把 Level .umap 作为场景真相源
- Level .umap 可以提交 Git（作为视觉快照），但"加载场景"按钮是随时可用的
- 出现冲突时以 Nexus 为准

---

## 九、迁移策略（从 2.5 到 3.2）

### 9.1 保留的代码

- 墙/地板 RMC 挤压算法
- 柱子 HISM 放置逻辑
- World Aligned Material 相关
- `TwinSceneManager` / `TwinInstance` 主体框架

### 9.2 删除的代码

- `ezdxf` 相关的 UE 侧 Python 脚本
- DXF 解析逻辑（由后端承担）
- 本地 JSON 文件读取逻辑（由 API 拉取替换）

### 9.3 新增的代码

- `UTwinSceneDataSource`
- `UTwinOntologyMetadataComponent`
- `UTwinWritebackCollector`
- 编辑器菜单扩展模块
- 坐标转换工具类

### 9.4 迁移时机

建议在 3.0 后端 API 完成并自测通过后，再开始 UE 侧的改造。避免 UE 和后端互相等待。
