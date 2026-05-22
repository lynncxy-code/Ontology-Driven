# OntoTwin 3.0 USD 导出模块需求说明书（PRD）

| 字段 | 内容 |
|---|---|
| **文档版本** | v3.0-r1 |
| **日期** | 2026-04-17 |
| **状态** | 草稿（待审阅） |
| **模块代号** | UsdExporter |
| **归属** | 后端服务（Python） |
| **依赖** | 2.1 本体接口 / 2.2 Nexus 资产中台 / 3.1 Scene 管理 |

---

## 一、产品背景

### 1.1 目标
为 OntoTwin 本体驱动三维配置平台新增"USD 场景导出"能力，使本体定义的场景可以一键导出为 Pixar OpenUSD 格式，对接 Isaac Sim + Isaac Lab 具身智能训练流水线。

### 1.2 核心价值
- **数据复用**：本体库里定义的工厂/仓库场景直接转化为训练资产，避免重复建模
- **资产可溯源**：每个导出的 Prim 带本体元数据，训练侧可反查业务语义
- **训练就绪**：导出的 USD 文件开箱即用，Isaac Sim 加载后机器人可直接训练（抓取、导航等）

### 1.3 不做的事（Out of Scope）
- ❌ 不导出动态行为（工人动画、AGV 轨迹）
- ❌ 不做 USD → 本体 的反向导入（双向映射）
- ❌ 不做训练任务脚本（由训练侧同事负责）
- ❌ 不做 USD 文件的远程存储/分发（第一版仅支持下载到本地）

---

## 二、核心用户故事

### 2.1 用户故事 U1：场景一键导出
> 作为一名数字孪生平台的使用者，当我在 Nexus 前端完成场景配置后，我希望点击"导出 USD"按钮，就能下载一个可以直接在 Isaac Sim 中打开的 `.usda` 文件，不需要手动处理任何中间格式。

### 2.2 用户故事 U2：命令行批量导出
> 作为一名后端运维，我希望能通过命令行批量导出多个场景，方便 CI 流程集成。

### 2.3 用户故事 U3：UE 触发导出
> 作为一名美术设计师，当我在 UE 里预览场景、调整了物体位置并回写到 Nexus 后，我希望直接在 UE 编辑器里点个按钮就能把最新状态导出为 USD 给训练同事。

### 2.4 用户故事 U4：导出追溯
> 作为一名训练工程师，当我在 Isaac Sim 里看到一个 Prim 想知道它对应本体里的哪个实例时，我希望能从 Prim 的 metadata 里直接读到 `instanceId` 和 `objectTypeRid`。

---

## 三、功能需求

### 3.1 核心功能清单

| 功能 ID | 功能名称 | 优先级 |
|---|---|---|
| F1 | Scene → USD 转换引擎 | P0 |
| F2 | FBX → USD 缓存式转换服务 | P0 |
| F3 | DXF → USD 结构生成服务 | P0 |
| F4 | USD 导出 REST API | P0 |
| F5 | USD 导出命令行工具 | P1 |
| F6 | 导出任务异步处理与状态查询 | P1 |
| F7 | 导出报告（警告 / 冲突 / 缺失） | P1 |
| F8 | USD 分层导出（主文件 + 结构层 + 实例层） | P2（后续版本） |

---

### 3.2 【F1】Scene → USD 转换引擎

**3.2.1 输入**

- `scene_id`（必填）：要导出的场景 ID
- `options`：导出选项（见 §3.2.4）

**3.2.2 处理流程**

```
1. 查询 Scene 元数据（bounds / unit / up_axis / structure_dxf_path / placements）
2. 查询属于该 Scene 的所有 Instance（belongs_to_scenes 包含 scene_id）
3. 初始化 USD Stage，设置 metersPerUnit=1.0, upAxis=Z
4. 写入根 Prim /World 及其 customData
5. 若 Scene 有 structure_dxf_path：
     调用 F3（DXF→USD 结构生成），生成的 Prim 挂到 /World/Structure/
6. 遍历 Instance 列表：
     a. 根据 file_number 获取对应 USD 资产（调用 F2）
     b. 在 USD 里创建 Xform Prim，引用（References）该资产
     c. 应用 I3D_Spatial（translation / rotation / scale）
     d. 根据 I3D_PhysicsHint 应用物理 Schema
     e. 写入 customData（ontology 追溯信息）
7. 处理 Scene.placements（如有）：
     - StaticPlacement：覆盖对应 Instance 的默认坐标
     - ProceduralGroup：展开为 N 个 Prim，父 Prim 写入 proceduralRule customData
8. 生成导出报告（§3.2.5）
9. 保存 USD 文件到临时目录，返回下载链接
```

**3.2.3 USD 输出结构规范**

```usda
#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
    customLayerData = {
        dictionary ontology = {
            string sourceScene = "warehouse_demo_01"
            string datasetId = "standard_practice"
            int exportVersion = 3
            string exportTimestamp = "2026-04-17T10:30:00Z"
        }
    }
)

def Xform "World"
{
    def Xform "Structure"      # DXF 生成的结构
    {
        def Mesh "wall_001" { ... }
        def Mesh "floor_001" { ... }
    }
    
    def Xform "Shelves"         # 货架组
    {
        def Xform "shelf_001" (
            references = @./assets/SM_Std_Shelf.usd@
        )
        {
            customData = {
                dictionary ontology = {
                    string instanceId = "shelf_001"
                    string objectTypeRid = "ri.obj.shelf"
                    string fileNumber = "SM_Std_Shelf_200"
                    string[] interfaces = ["I3D_Representable", "I3D_Spatial", "I3D_PhysicsHint"]
                }
            }
            double3 xformOp:translate = (1.5, 2.0, 0)
            float3 xformOp:rotateXYZ = (0, 0, 90)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
            
            # 物理 Schema（根据 collision_type 动态应用）
            rel physics:collision:simulationOwner
        }
    }
    
    def Xform "Boxes"           # 可抓取物体组
    {
        def Xform "box_001" ( ... )
        {
            # graspable 类型：mesh 精确碰撞 + RigidBody + Mass
        }
    }
}
```

**3.2.4 导出选项（Options）**

```python
class ExportOptions:
    format: str = "usda"                 # "usda" (ASCII) 或 "usdc" (binary)
    include_physics: bool = True         # 是否写入物理 Schema
    include_procedural_rules: bool = True # 是否把生成规则写入 customData
    bundle_assets: bool = False          # 是否把引用的资产打包进 .usdz
    output_filename: str | None = None   # 自定义文件名
```

**3.2.5 导出报告**

每次导出生成结构化报告，包含：

```json
{
    "scene_id": "warehouse_demo_01",
    "export_version": 3,
    "exported_at": "2026-04-17T10:30:00Z",
    "file_path": "/tmp/exports/warehouse_demo_01_v3.usda",
    "file_size_bytes": 245678,
    "stats": {
        "prim_count": 42,
        "instance_count": 35,
        "structure_prim_count": 7,
        "physics_applied_count": 12
    },
    "warnings": [
        {
            "level": "warning",
            "instance_id": "box_005",
            "message": "collision_type=graspable but no mass_hint in asset metadata, using default 0.5kg"
        }
    ],
    "errors": []
}
```

---

### 3.3 【F2】FBX → USD 缓存式转换服务

**3.3.1 功能定位**

将资产库中的 FBX 模型按需转换为 USD 格式，首次转换后缓存供后续复用。

**3.3.2 转换工具选型**

**优先方案**：NVIDIA `asset_converter`（Omniverse 自带，支持批量）
**备选方案**：Blender 无头模式（`blender -b -P convert.py`）

> 团队需在正式开发前做一次技术选型评估：Omniverse 依赖较重，Blender 较轻但材质转换可能有损。

**3.3.3 转换流程**

```
输入：file_number (资产库编号)
1. 查询资产记录，获取 fbx_source_path
2. 检查 usd_cached_path 是否存在，且 usd_cache_hash == hash(fbx_source_path)
   - 命中缓存：直接返回 usd_cached_path
   - 未命中：进入转换
3. 调用转换工具：fbx_source_path → usd_cached_path
4. 转换完成后：
   - 更新资产记录：usd_cached_path, usd_cache_hash, usd_cached_at
   - 若 collision_type == graspable：验证 mesh 精度（面数、封闭性）
5. 返回 usd_cached_path
```

**3.3.4 缓存失效规则**

- FBX 源文件 hash 变化时触发重转
- 资产记录里 `lod_strategy` 字段变化时触发重转（可能换了精度）
- 手动 API 触发强制重转：`POST /api/v3/assets/{file_number}/usd/rebuild`

**3.3.5 批量预转 API（运维用）**

```
POST /api/v3/assets/usd/batch_build
Body: {
    file_numbers: ["SM_xxx1", "SM_xxx2", ...] 或 null（null 表示全部）
    force_rebuild: bool = false
}
Returns: { job_id }
```

---

### 3.4 【F3】DXF → USD 结构生成服务

**3.4.1 功能定位**

复用 2.5 TwinSceneBuilder 原有的 `ezdxf` 解析逻辑，把 DXF 图纸转换为 USD 中的结构性几何（墙、地板、柱子）。**这部分逻辑从 UE 侧 Python 迁移到后端服务中。**

**3.4.2 处理流程**

```
输入：dxf_file_path
1. 使用 ezdxf 加载 DXF 文件
2. 遍历 entities，按图层名过滤：
   - "1.20-柱子" → 提取 Block 实体，作为 INSTANCE 类型
   - "1.21-墙体" → 提取 Polyline，作为 PROCEDURAL_WALL
   - "4.10-地坪" → 提取 Closed Polyline，作为 PROCEDURAL_FLOOR
3. 对墙体：根据路径 + 高度 + 厚度生成挤压 Mesh
4. 对地坪：根据闭合轮廓生成面片 Mesh
5. 对柱子：引用预设 USD 模型，设置 Transform
6. 所有结构 Prim 挂到 /World/Structure/ 下
7. 为所有结构 Prim 应用 CollisionAPI（static 类型）
```

**3.4.3 输出约定**

- 墙体：`/World/Structure/walls/wall_<index>`
- 地板：`/World/Structure/floors/floor_<index>`
- 柱子：`/World/Structure/columns/column_<index>`
- 材质：使用 `UsdPreviewSurface`，颜色来自 JSON 配置

---

### 3.5 【F4】USD 导出 REST API

详见 `3.3_USD导出API规范 (API)` 文档。核心接口概述：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v3/scenes/{scene_id}/export` | 触发导出，返回 job_id |
| GET | `/api/v3/export/jobs/{job_id}` | 查询导出状态与报告 |
| GET | `/api/v3/export/jobs/{job_id}/download` | 下载 USD 文件 |
| GET | `/api/v3/scenes/{scene_id}/exports` | 获取导出历史 |

---

### 3.6 【F5】命令行工具

**3.6.1 基本用法**

```bash
# 单场景导出
ontotwin-export --scene warehouse_demo_01 --output ./warehouse.usda

# 批量导出
ontotwin-export --dataset standard_practice --all-scenes --output-dir ./exports/

# 指定格式
ontotwin-export --scene warehouse_demo_01 --format usdc

# 强制重建资产 USD 缓存
ontotwin-export --scene warehouse_demo_01 --rebuild-assets
```

**3.6.2 实现方式**

Python 脚本包装 REST API 客户端，内置认证逻辑（从环境变量读取 token）。

```
安装：pip install ontotwin-cli
依赖：只依赖 requests，不直接依赖 pxr（通过调用服务端实现）
```

---

### 3.7 【F6】导出任务异步处理

**3.7.1 异步化的必要性**

大型场景（1000+ Prim）导出可能耗时 10+ 秒，需异步处理避免 HTTP 超时。

**3.7.2 任务状态机**

```
QUEUED → RUNNING → SUCCESS
                  ↘ FAILED
         ↘ CANCELLED
```

**3.7.3 任务存储**

建议使用 Redis 存储任务状态，TTL = 24 小时（超过自动清理）。

---

### 3.8 【F7】导出报告

每次导出必须生成报告，报告内容见 §3.2.5，通过以下途径呈现：

- Nexus 前端"导出历史"页面展示
- API 返回 JSON
- 导出 USD 文件的同目录下生成 `.export_report.json`

**警告示例**：

| 警告类型 | 触发条件 |
|---|---|
| `missing_mass_hint` | Instance 的 collision_type 要求 mass 但本体里没填 |
| `asset_fbx_not_found` | 资产记录指向的 FBX 文件不存在 |
| `procedural_rule_disabled` | 场景有 procedural_group 但 randomization.enabled=false |
| `bounds_violation` | 某实例坐标超出 Scene.bounds 范围 |
| `physics_proxy_missing` | graspable 类型但无 physics_proxy_path，将使用全 mesh（性能差） |

---

## 四、非功能需求

### 4.1 性能指标

| 指标 | 要求 |
|---|---|
| 中型场景导出（100 Prim）| ≤ 5 秒 |
| 大型场景导出（1000 Prim）| ≤ 30 秒 |
| FBX → USD 首次转换（单文件）| ≤ 10 秒 |
| 缓存命中时资产查询 | ≤ 100ms |

### 4.2 可靠性

- **原子性**：导出中途失败不应产生半成品 USD 文件（写临时文件，成功后原子 rename）
- **幂等性**：同一 scene_id + 同一时间点的状态，多次导出结果应完全一致（不含 exportTimestamp 差异）
- **降级**：FBX 转换服务不可用时，退化为直接输出占位 Cube，导出报告中警告

### 4.3 可维护性

- **USD 规范版本**：基于 OpenUSD 1.0 Core Spec（AOUSD 2025 发布版）
- **依赖管理**：`pxr` 库版本锁定（建议 24.x LTS）
- **日志**：每次导出的完整日志保留 7 天

---

## 五、技术实现要点

### 5.1 Python 环境

```
核心依赖：
- usd-core (Pixar 官方 PyPI 包，包含 pxr)
- ezdxf (DXF 解析)
- fastapi (REST API)
- celery + redis (异步任务，可选)

工具依赖：
- NVIDIA asset_converter 或 Blender 4.x
```

### 5.2 关键代码骨架

```python
# 核心导出器
from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf

class SceneUsdExporter:
    def __init__(self, scene_id: str, options: ExportOptions):
        self.scene = self._load_scene(scene_id)
        self.options = options
        self.stage = None
        self.report = ExportReport(scene_id=scene_id)
    
    def export(self, output_path: str):
        self._init_stage(output_path)
        self._write_layer_metadata()
        self._export_structure()      # F3
        self._export_instances()      # 核心循环
        self._apply_placements()      # 特殊摆放
        self.stage.Save()
        return self.report
    
    def _init_stage(self, output_path):
        self.stage = Usd.Stage.CreateNew(output_path)
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1.0)
        UsdGeom.Xform.Define(self.stage, "/World")
        self.stage.SetDefaultPrim(self.stage.GetPrimAtPath("/World"))
    
    def _write_layer_metadata(self):
        layer = self.stage.GetRootLayer()
        layer.customLayerData = {
            "ontology": {
                "sourceScene": self.scene.id,
                "datasetId": self.scene.dataset_id,
                "exportVersion": self._next_version(),
                "exportTimestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    
    def _export_instances(self):
        for instance in self.scene.get_instances():
            prim = self._create_instance_prim(instance)
            self._apply_transform(prim, instance)
            self._apply_physics(prim, instance)
            self._write_ontology_metadata(prim, instance)
    
    def _create_instance_prim(self, instance):
        prim_path = f"/World/{self._category_name(instance)}/{instance.id}"
        prim = UsdGeom.Xform.Define(self.stage, prim_path).GetPrim()
        
        usd_asset_path = self.asset_service.get_usd_path(instance.file_number)
        prim.GetReferences().AddReference(usd_asset_path)
        return prim
    
    def _apply_physics(self, prim, instance):
        hint = instance.interfaces.get("I3D_PhysicsHint")
        if not hint:
            return
        
        UsdPhysics.CollisionAPI.Apply(prim)
        
        if hint.collision_type in ("dynamic", "graspable"):
            UsdPhysics.RigidBodyAPI.Apply(prim)
            mass_api = UsdPhysics.MassAPI.Apply(prim)
            mass_api.CreateMassAttr(hint.mass or self._default_mass(hint))
            
            if hint.collision_type == "graspable":
                # 使用 mesh 级精确碰撞
                mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
                mesh_collision.CreateApproximationAttr("none")
    
    def _write_ontology_metadata(self, prim, instance):
        prim.SetCustomDataByKey("ontology", {
            "instanceId": instance.id,
            "objectTypeRid": instance.object_type_rid,
            "fileNumber": instance.file_number,
            "interfaces": list(instance.interfaces.keys()),
            "sourceScene": self.scene.id,
            "datasetId": self.scene.dataset_id,
            "exportVersion": self._export_version,
            "exportTimestamp": self._timestamp
        })
```

### 5.3 常见踩坑提示

团队若首次接触 OpenUSD，请注意以下问题：

1. **Layer vs Stage**：Stage 由多个 Layer 叠加组成，编辑时要明确作用在哪一层
2. **Prim Path 不能有空格、括号、中文**：命名规范要提前约定
3. **customData 是字典套字典**：用 `SetCustomDataByKey` 而非直接 `customData[key] = ...`
4. **物理 Schema 必须用 Apply() 方法添加**：不是直接 setattr
5. **References vs Payloads**：References 立即加载，Payloads 延迟加载；第一版用 References 即可
6. **保存后不要直接修改 usda 文本**：会破坏二进制一致性，始终用 API 修改

---

## 六、验收标准

| 场景 | 通过条件 |
|---|---|
| 导出一个含 10 个实例的简单仓库场景 | 生成的 usda 能在 `usdview` 中打开，看到所有物体 |
| 导出含 DXF 结构的场景 | 墙/地板/柱子能正确生成，带碰撞体 |
| 导出 graspable 物体 | 含 MassAPI 和 mesh 精确碰撞 |
| customData 追溯 | 用 `usdview` 查看任一 Prim，能看到完整的 ontology metadata |
| FBX 缓存命中 | 连续 2 次导出同场景，第 2 次耗时 ≤ 第 1 次的 50% |
| 命令行导出 | `ontotwin-export --scene xxx` 能正确生成文件 |
| 并发导出 | 同时触发 5 个场景导出，均能成功完成 |
| 错误场景：Instance 引用的 FBX 不存在 | 导出不崩溃，报告中标记错误，该 Instance 用占位 Cube 代替 |
| 错误场景：Scene 下无任何 Instance | 正常生成空场景 USD（仅有 /World） |

---

## 七、范围外（Out of Scope）

- ❌ USD 分层导出（主文件 + SubLayers），规划在 3.1+ 版本
- ❌ USDZ 打包（把资产压缩进单个文件），规划在 3.2+ 版本
- ❌ Omniverse Nucleus 远程分发，规划在 4.x
- ❌ 增量导出（只导出变化的 Prim），规划在 4.x
- ❌ 训练任务脚本生成（Isaac Lab env_cfg），由训练侧同事负责
- ❌ USD → 本体的反向导入，不在 3.0 路线图内

---

## 八、依赖与风险

### 8.1 外部依赖

| 依赖 | 版本 | 风险 |
|---|---|---|
| Pixar OpenUSD (usd-core) | 24.x | 低（稳定） |
| NVIDIA asset_converter | 最新 | 中（闭源，API 可能变动） |
| Blender (备选) | 4.x | 低 |
| ezdxf | 1.x | 低（2.5 已验证） |

### 8.2 关键风险

| 风险 | 级别 | 缓解措施 |
|---|---|---|
| 团队首次接触 pxr，学习成本 | 中 | 正式开发前 2-3 天的 spike，写一个 "hello cube" 端到端跑通 |
| FBX 转 USD 的材质损失 | 中 | 第一版允许材质精度降级，后期若需要可手写 MDL 映射 |
| graspable 资产的碰撞几何质量 | 高 | 要求美术提供专门的 physics_proxy；自动检测面数不合格触发警告 |
| Isaac Sim 加载时的 Schema 兼容性 | 中 | 开发中频繁在 Isaac Sim 侧验证，不要等全部开发完才联调 |
