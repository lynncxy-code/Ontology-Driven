# OntoTwin 3.0 架构变更说明（Architecture Changelog）

| 字段 | 内容 |
|---|---|
| **文档版本** | v3.0-r1 |
| **日期** | 2026-04-17 |
| **状态** | 草稿（待审阅） |
| **适用范围** | OntoTwin 2.1 / 2.2 / 2.3 / 2.3.1 / 2.5 的增量修订 |
| **变更触发** | 新增"USD 导出与具身训练对接"能力（3.0 系列） |

---

## 一、变更总览

3.0 系列新增"USD 场景导出"能力，用于对接 Isaac Sim + Isaac Lab 具身训练。由此引发对 2.x 系列本体数据模型、API 契约、UE 端组件的若干修订。本文档集中说明**变更点**，3.0 新增模块的完整需求见配套的 3.x 开发文档。

### 1.1 变更原则

- **不破坏 2.x 现有功能**：UE 实时渲染链路、中间层轮询、数字人/AGV 同步均保持兼容
- **数据模型向前兼容**：新增字段允许为空，旧实例数据无需强制迁移
- **导出能力独立成模块**：USD 导出走独立 API，不污染 2.6 轮询接口

### 1.2 受影响的 2.x 模块

| 2.x 模块 | 变更程度 | 说明 |
|---|---|---|
| 2.1 DigitalTwinSync（本体接口） | **中** | 新增 `I3D_PhysicsHint` 接口；坐标系语义标准化 |
| 2.2 Nexus 资产中台 | **中** | 新增 Scene 概念；资产库字段扩展 |
| 2.3 数据集管理 | **小** | Dataset 下挂 Scene 节点 |
| 2.3.1 批量投产 | **小** | 不改；新增按 Scene 筛选能力 |
| 2.5 TwinSceneBuilder | **大** | 数据源从 DXF-only 改为 DXF+Nexus 混合 |
| 2.6 中间层轮询接口 | **无** | 完全兼容，不修改 |
| 2.7 PCBWorkerSync | **无** | 与 USD 导出链路无关 |
| 2.8 AGVPatrol | **无** | 与 USD 导出链路无关 |

---

## 二、【重大变更】本体数据模型修订

### 2.1 新增 Scene 概念

**原状态（2.x）**：本体结构为 `Dataset → Ontology(ObjectType) → Instance`，实例直接飘在数据集下。

**新结构（3.0）**：

```
Dataset
 ├── Ontology（ObjectType 定义）
 ├── Instances（实例资产池）
 └── Scenes（场景组织层，新增）
      └── 每个 Scene 聚合一批 Instance，定义空间边界与结构
```

**Scene 的定位**：
- 一个可导出的三维空间组织单元
- 对应 USD 文件中的一个 Stage
- 对应 UE 中的一个 Level
- 对应 Isaac Sim 中的一个训练环境

**Scene 数据结构**：

```python
Scene {
    id: str                          # "warehouse_demo_01"
    dataset_id: str                  # 所属数据集
    display_name: str                # "仓库演示场景"
    
    # 空间定义
    bounds: {
        x: [float, float],           # 单位：米
        y: [float, float],
        z: [float, float]
    }
    up_axis: str = "Z"               # 固定为 Z-up
    unit: str = "meter"              # 固定为米
    
    # 结构数据源（2.5 DXF 链路复用）
    structure_dxf_path: str | None   # 可选，指向 DXF 文件
    
    # 摆放规则（第一版可选，大部分场景不用）
    placements: list[Placement]      # 见 §2.3
    
    # 导出记录
    exports: list[ExportRecord]
}
```

### 2.2 Instance 数据结构修订

**新增字段**：

```python
Instance {
    # ... 原有字段 ...
    
    # 新增字段 1：Scene 归属（多对多）
    belongs_to_scenes: list[str]     # Scene ID 列表
    
    # 新增字段 2：物理提示（新接口，见 §3.2）
    interfaces: {
        # ... 原有 I3D_Representable / I3D_Spatial / I3D_Rotatable 等 ...
        
        I3D_PhysicsHint: {            # 新增
            collision_type: str       # "static" | "dynamic" | "graspable"
            mass: float               # kg，可选
            friction: float           # 摩擦系数，可选
        }
    }
}
```

**设计要点**：
- `belongs_to_scenes` 采用**多对多**关系：一个 Instance 可以被多个 Scene 复用（如同一个货架出现在"仓库演示"和"训练场景"中）
- Instance 自带 `I3D_Spatial` 的默认坐标（与 2.1 保持兼容），不同 Scene 加载时使用该默认坐标
- 需要同一 Instance 在同一 Scene 里多次摆放（如 5 个相同货架），通过 Scene 的 `placements` 字段表达

### 2.3 Scene 的 Placement 字段

`placements` 是一个可选的特殊摆放规则列表。如果为空，则使用每个 Instance 的默认坐标（`I3D_Spatial`）。

**两种 Placement 类型**：

```python
# 类型 A：静态单点摆放（覆盖 Instance 默认坐标）
StaticPlacement {
    type: "static"
    instance_id: str                  # 必填
    translation: [float, float, float]
    rotation: [float, float, float]   # 欧拉角，度
    scale: [float, float, float]
}

# 类型 B：程序化摆放组（复制同一模板多次）
ProceduralGroup {
    type: "procedural_group"
    pattern: str                      # "linear_repeat" | "grid" | "random_in_region"
    template_instance_id: str         # 以哪个 Instance 为模板
    count: int                        # 生成数量
    
    # pattern=linear_repeat 时的参数
    start_translation: [float, float, float]
    step: [float, float, float]
    rotation: [float, float, float]
    
    # 为未来域随机化预留（第一版不启用）
    randomization: {
        enabled: bool = false
        translation_jitter: [float, float, float]
        rotation_jitter: float
    }
}
```

> [!IMPORTANT]
> 第一版实现中，Placement 字段**可选**，多数场景可以不用（直接用 Instance 的默认坐标）。为未来"程序化场景 + 域随机化"保留数据结构。

---

## 三、【接口扩展】I3D 能力接口新增

### 3.1 原有接口清单（2.1 已定义）

| 接口 RID | 用途 | 状态 |
|---|---|---|
| `I3D_Representable` | 资产渲染基础（file_number / lod_strategy / is_visible） | 保留 |
| `I3D_Movable` | 位移（translation_x/y/z） | 保留 |
| `I3D_Rotatable` | 旋转（rotation_p/y/r） | 保留 |
| `I3D_Animatable` | 动画状态 | 保留（USD 导出不使用） |

> **注**：2.1 中 `I3D_Movable` 和 `I3D_Rotatable` 在 3.0 里可合并表达为 `I3D_Spatial`（便于前端 UI 统一），但底层字段保持一致，不做数据迁移。

### 3.2 新增接口：`I3D_PhysicsHint`

**用途**：为 USD 导出和 Isaac Sim 训练提供物理属性提示。

**字段定义**：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `collision_type` | enum | 是 | `static` / `dynamic` / `graspable` |
| `mass` | float | 否 | 单位 kg，仅 `dynamic` 和 `graspable` 需要 |
| `friction` | float | 否 | 0~1，默认 0.5 |

**collision_type 语义**：

| 值 | 含义 | Isaac Sim 对应 Schema | 典型物体 |
|---|---|---|---|
| `static` | 不动，仅作障碍物 | `CollisionAPI` 单独应用 | 墙、地板、柱子、固定货架 |
| `dynamic` | 受重力可推动 | `CollisionAPI + RigidBodyAPI + MassAPI`，convex hull 碰撞 | 可倾倒的桶、散落物 |
| `graspable` | 可被机器人抓取 | `CollisionAPI + RigidBodyAPI + MassAPI`，**mesh 精确碰撞** | 待抓取的零件、箱子 |

**校验规则**：
- 当 `collision_type = graspable` 时，后端必须验证对应资产的 USD 文件存在 mesh 级碰撞几何，否则抓取训练会失败
- `mass` 缺省时，后端从资产库的元数据（若有）读取；仍缺失时给予默认值（dynamic: 1.0 kg，graspable: 0.5 kg）并在导出报告中警告

---

## 四、【扩展】模型资产库字段修订

### 4.1 原状态（2.1 / 2.2）

```
资产记录 {
    file_number: str             # 唯一识别码
    fbx_source_path: str         # FBX 源文件路径
    lod_level: enum              # 源/一级/二级优化区
    bounding_box: dict
}
```

### 4.2 3.0 修订

新增字段：

```
资产记录 {
    # ... 原有字段 ...
    
    # 新增：USD 缓存
    usd_cached_path: str | None   # 转换后的 USD 路径（缓存命中时）
    usd_cache_hash: str | None    # 对应 FBX 的 hash，用于失效检查
    usd_cached_at: datetime | None
    
    # 新增：物理代理模型
    physics_proxy_path: str | None  # 专用碰撞低模（可选，graspable 场景用）
    
    # 新增：元数据扩展
    meta: {
        mass_hint: float | None      # 来自 CAD 的默认质量
        material_hint: str | None    # 表面材质类型
    }
}
```

**FBX → USD 转换策略**：**缓存式惰性转换**
- 首次需要时转换（通过 NVIDIA `asset_converter` 或 Blender 无头模式）
- 转换后写入 `usd_cached_path` 和 `usd_cache_hash`
- FBX 若被更新（hash 不匹配），自动触发重转

---

## 五、【集成】TwinSceneBuilder 数据源变更（2.5 修订）

### 5.1 原状态（2.5）

```
DXF → Python (ezdxf) → JSON → UE (TwinSceneBuilder) → 场景生成
```

单数据源：DXF 图纸。

### 5.2 3.0 修订

```
                  ┌─→ DXF 解析 (Python ezdxf) ─→ structure_usd.usda
Scene (Nexus) ────┤
                  └─→ Instance 查询 ────────────→ instances_usd.usda
                                                         │
                                           合并 ─────────┘
                                             ↓
                                    warehouse.usda (主导出)
                                             ↓
                                  ┌──────────┴──────────┐
                                  ↓                     ↓
                              UE (预览)            Isaac Sim (训练)
```

**核心变化**：
- `TwinSceneBuilder` 在 UE 侧**仍保留**，但数据源从"本地 DXF JSON"改为"Nexus Scene JSON API"
- USD 导出**不经过 UE**，由 Python 后端统一生成（路径 Z 方案）
- UE 只作为"视觉预览 + 美术调整 + 回写"的前端

### 5.3 UE 端 TwinSceneBuilder 对应职责调整

| 职责 | 2.5 状态 | 3.0 状态 |
|---|---|---|
| DXF → JSON 解析 | Python 侧完成 | **迁移至后端**（不再由 UE 侧 Python 执行） |
| JSON → UE 场景生成 | ✅ | ✅（数据源从本地 JSON 改为 API 拉取） |
| 墙/地板/柱子 RuntimeMesh 构建 | ✅ | ✅ |
| 资产实例摆放 | ✅ | ✅（数据源改为 Nexus Scene API） |
| 美术位置调整 | 本地保存 | **回写到 Nexus**（新增功能） |
| USD 导出 | 无 | **调用后端 API，不自导**（新增入口按钮） |

---

## 六、【新增】坐标系与单位标准化

### 6.1 标准规范

| 项 | 值 | 备注 |
|---|---|---|
| 单位 | meter（米） | 本体数据库内存储均用米 |
| 上轴 | Z-up | 与 USD / Isaac Sim / Omniverse 一致 |
| 坐标系 | 右手系 | X 前、Y 左、Z 上 |
| 旋转表达 | 欧拉角（度） | 存储格式：`[rx, ry, rz]` |

### 6.2 UE 端单位换算

UE 默认是 cm + 左手系。在 UE 侧做加载时的转换，而非在本体或导出侧：

| 数据流向 | 转换 |
|---|---|
| Nexus → UE | 米 × 100 = cm；Y 轴翻转 |
| UE → Nexus（回写） | cm ÷ 100 = 米；Y 轴翻转 |
| Nexus → USD 导出 | 直接使用米，不换算 |

**UE 的 USD 导入/导出设置**：
- `Meters Per Unit` = 0.01（表示 UE 的 1 单位 = 0.01 米）
- UE 会自动处理坐标系翻转

### 6.3 历史数据迁移

2.x 若已有数据以 cm 为单位存储，提供一次性迁移脚本：

```bash
python migrate_2_to_3.py --dataset=standard_practice --unit-from=cm --unit-to=m
```

脚本会遍历所有 Instance 的 `I3D_Spatial.translation`，除以 100。

---

## 七、【新增】customData 追溯标准

所有 3.0 导出的 USD 文件，在每个 Prim 上按以下规范写入 `customData`（嵌套 dict 形式）：

```python
prim.SetCustomDataByKey("ontology", {
    "instanceId": "shelf_001",
    "objectTypeRid": "ri.obj.shelf",
    "fileNumber": "SM_Std_Shelf_200",
    "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_PhysicsHint"],
    "sourceScene": "warehouse_demo_01",
    "datasetId": "standard_practice",
    "exportVersion": 3,
    "exportTimestamp": "2026-04-17T10:30:00Z"
})
```

**用途**：
- **追溯**：训练侧可以根据 Prim 反查本体实例
- **回写**：UE 导出前读取该 customData，保证身份一致
- **诊断**：导出报告可根据该字段生成 Prim 级别的数据血缘

---

## 八、【不变】2.6 中间层接口保持兼容

2.6 的 `/api/ue/snapshot` 和 `/api/ue/events` 完全不修改。这两个接口服务于**运行态工人/AGV 同步**，与 USD 导出的**静态训练场景**在数据流向、时效性、用途上完全正交。

**关键边界**：
- USD 导出：**设计态 + 静态**（描述场景长什么样）
- 2.6 轮询：**运行态 + 动态**（描述场景里有谁在动）

两者可以独立演进，互不影响。

---

## 九、变更影响总结与迁移清单

### 9.1 破坏性变更（Breaking Changes）

**无破坏性变更**。所有 3.0 新增字段在 2.x 数据上均为可选或默认值兼容。

### 9.2 建议的迁移动作

| 动作 | 必须性 | 备注 |
|---|---|---|
| 为历史 Instance 补充 `belongs_to_scenes` 字段 | 建议 | 不补的话不会出现在任何 Scene 的导出中 |
| 为需要物理训练的 Instance 添加 `I3D_PhysicsHint` | 视需要 | 不加则默认按 `static` 处理 |
| 坐标单位从 cm 统一为米 | 必须 | 使用迁移脚本 |
| FBX 资产批量预转为 USD | 可选 | 提前转好可提升首次导出速度 |

### 9.3 文档阅读顺序建议

对已经熟悉 2.x 的团队成员：

1. 先读本文档（了解变更全貌）
2. 再读 `3.0_USD导出模块需求说明书 (PRD)`（后端 USD 导出模块）
3. 再读 `3.1_Nexus场景管理需求说明书 (PRD)`（前后端 Scene 管理）
4. 再读 `3.2_TwinSceneBuilder改造需求 (PRD)`（UE 端改造）
5. 最后读 `3.3_USD导出API规范 (API)`（接口契约）
