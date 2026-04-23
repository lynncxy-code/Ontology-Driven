# TECH_SPEC.md — 技术规格

> 本文档定义本项目的具体技术细节：数据结构、API 契约、代码骨架。
> Claude Code 按本文档生成代码。

---

## 一、后端数据模型（SQLite 表设计）

### 表 1：`lite_assets` — 资产库

```sql
CREATE TABLE lite_assets (
    file_number TEXT PRIMARY KEY,           -- 资产唯一编号，如 "SM_Std_Shelf_200"
    display_name TEXT NOT NULL,             -- 显示名，如 "标准货架 200"
    fbx_source_path TEXT NOT NULL,          -- FBX 文件绝对路径
    usd_cached_path TEXT,                   -- USD 缓存路径（首次转换后填写）
    usd_cache_hash TEXT,                    -- FBX 文件 hash，用于失效检查
    usd_cached_at TIMESTAMP,                -- 缓存时间
    bounding_box TEXT,                      -- JSON: {"x": 0.8, "y": 2.0, "z": 2.0}（米）
    mass_hint REAL,                         -- CAD 元数据里的默认质量（kg），可空
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 表 2：`lite_instances` — 实例

```sql
CREATE TABLE lite_instances (
    id TEXT PRIMARY KEY,                    -- "shelf_001"
    object_type_rid TEXT NOT NULL,          -- "ri.obj.shelf"
    file_number TEXT NOT NULL,              -- 关联 lite_assets
    display_name TEXT,
    
    -- I3D_Spatial（默认坐标）
    translation_x REAL DEFAULT 0,           -- 米
    translation_y REAL DEFAULT 0,
    translation_z REAL DEFAULT 0,
    rotation_x REAL DEFAULT 0,              -- 欧拉角，度
    rotation_y REAL DEFAULT 0,
    rotation_z REAL DEFAULT 0,
    scale_x REAL DEFAULT 1,
    scale_y REAL DEFAULT 1,
    scale_z REAL DEFAULT 1,
    
    -- I3D_PhysicsHint
    collision_type TEXT DEFAULT 'static',   -- static / dynamic / graspable
    mass REAL,                              -- kg，可空
    friction REAL DEFAULT 0.5,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_number) REFERENCES lite_assets(file_number)
);
```

### 表 3：`lite_scenes` — 场景

```sql
CREATE TABLE lite_scenes (
    id TEXT PRIMARY KEY,                    -- "warehouse_demo_01"
    display_name TEXT NOT NULL,
    description TEXT,
    
    -- 场景边界（米）
    bounds_x_min REAL NOT NULL,
    bounds_x_max REAL NOT NULL,
    bounds_y_min REAL NOT NULL,
    bounds_y_max REAL NOT NULL,
    bounds_z_min REAL NOT NULL,
    bounds_z_max REAL NOT NULL,
    
    up_axis TEXT DEFAULT 'Z',
    unit TEXT DEFAULT 'meter',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 表 4：`lite_scene_instances` — 场景-实例关联（多对多）

```sql
CREATE TABLE lite_scene_instances (
    scene_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    PRIMARY KEY (scene_id, instance_id),
    FOREIGN KEY (scene_id) REFERENCES lite_scenes(id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES lite_instances(id) ON DELETE CASCADE
);
```

### 表 5：`lite_exports` — 导出记录

```sql
CREATE TABLE lite_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_json TEXT,                       -- 导出报告 JSON
    FOREIGN KEY (scene_id) REFERENCES lite_scenes(id)
);
```

---

## 二、REST API 契约

### 前缀

所有新增 API 前缀：`/api/v3/lite/`

### 2.1 资产管理

#### GET `/api/v3/lite/assets`

**响应**：
```json
{
  "items": [
    {
      "file_number": "SM_Std_Shelf_200",
      "display_name": "标准货架 200",
      "fbx_source_path": "assets/fbx/SM_Std_Shelf_200.fbx",
      "usd_cached_path": "assets/usd_cache/SM_Std_Shelf_200.usd",
      "bounding_box": {"x": 0.8, "y": 2.0, "z": 2.0},
      "mass_hint": 50.0
    }
  ]
}
```

#### POST `/api/v3/lite/assets`

**请求体**：
```json
{
  "file_number": "SM_Std_Shelf_200",
  "display_name": "标准货架 200",
  "fbx_source_path": "assets/fbx/SM_Std_Shelf_200.fbx",
  "bounding_box": {"x": 0.8, "y": 2.0, "z": 2.0},
  "mass_hint": 50.0
}
```

#### POST `/api/v3/lite/assets/{file_number}/rebuild_usd`

触发单个资产重新转换 USD。

**响应**：
```json
{
  "usd_cached_path": "assets/usd_cache/SM_Std_Shelf_200.usd",
  "duration_ms": 3200
}
```

### 2.2 实例管理

#### GET `/api/v3/lite/instances`
#### POST `/api/v3/lite/instances`
#### GET `/api/v3/lite/instances/{id}`
#### PUT `/api/v3/lite/instances/{id}`
#### DELETE `/api/v3/lite/instances/{id}`

**Instance 响应示例**：
```json
{
  "id": "shelf_001",
  "object_type_rid": "ri.obj.shelf",
  "file_number": "SM_Std_Shelf_200",
  "display_name": "演示货架 1",
  "transform": {
    "translation": [1.5, 2.0, 0.0],
    "rotation": [0, 0, 90],
    "scale": [1, 1, 1]
  },
  "physics": {
    "collision_type": "static",
    "mass": 50.0,
    "friction": 0.6
  }
}
```

### 2.3 场景管理

#### GET `/api/v3/lite/scenes`

列出所有场景。

#### POST `/api/v3/lite/scenes`

创建场景。请求体：

```json
{
  "id": "warehouse_demo_01",
  "display_name": "仓库演示场景",
  "bounds": {
    "x": [-3, 3],
    "y": [-3, 3],
    "z": [0, 3]
  }
}
```

#### GET `/api/v3/lite/scenes/{id}`

获取场景详情（含关联的 instance_ids）。

#### POST `/api/v3/lite/scenes/{id}/instances`

添加实例到场景。

```json
{ "instance_ids": ["shelf_001", "shelf_002"] }
```

#### DELETE `/api/v3/lite/scenes/{id}/instances/{instance_id}`

### 2.4 导出 USD

#### POST `/api/v3/lite/scenes/{id}/export`

**请求体**：
```json
{
  "format": "usda",
  "include_physics": true
}
```

**响应（同步）**：
```json
{
  "success": true,
  "export_version": 3,
  "file_path": "exports/warehouse_demo_01_v3.usda",
  "download_url": "/api/v3/lite/exports/3/download",
  "stats": {
    "prim_count": 10,
    "warnings": []
  }
}
```

**同步执行**（不引入任务队列）。场景小，几秒完成。

#### GET `/api/v3/lite/exports/{id}/download`

直接返回 USD 文件。

### 2.5 UE 对接

#### GET `/api/v3/lite/scenes/{id}/ue_data`

UE 侧拉取场景数据。返回**米制坐标**，UE 端自己 × 100 转 cm。

```json
{
  "scene": {
    "id": "warehouse_demo_01",
    "unit": "meter",
    "up_axis": "Z"
  },
  "instances": [
    {
      "id": "shelf_001",
      "asset": {
        "file_number": "SM_Std_Shelf_200",
        "ue_asset_path": "/Game/Assets/Shelves/SM_Std_Shelf_200",
        "usd_path": "assets/usd_cache/SM_Std_Shelf_200.usd",
        "fallback_bounding_box": {"x": 0.8, "y": 2.0, "z": 2.0}
      },
      "transform": {
        "translation": [1.5, 2.0, 0.0],
        "rotation": [0, 0, 90],
        "scale": [1, 1, 1]
      },
      "ontology_metadata": {
        "instance_id": "shelf_001",
        "object_type_rid": "ri.obj.shelf",
        "collision_type": "static"
      }
    }
  ]
}
```

#### POST `/api/v3/lite/scenes/{id}/placements/update`

UE 回写位置。

```json
{
  "updates": [
    {
      "instance_id": "shelf_001",
      "translation": [1.8, 2.0, 0.0],
      "rotation": [0, 0, 90],
      "scale": [1, 1, 1]
    }
  ]
}
```

---

## 三、USD 导出器核心逻辑

### 3.1 文件：`backend/lite/services/usd_exporter.py`

**函数签名**：

```python
from pxr import Usd, UsdGeom, UsdPhysics, Gf
from pathlib import Path

def export_scene_to_usd(
    scene_id: str,
    output_path: str,
    format: str = "usda",
    include_physics: bool = True
) -> dict:
    """
    导出一个 Scene 为 USD 文件。
    
    Returns:
        {
            "success": bool,
            "file_path": str,
            "prim_count": int,
            "warnings": [...]
        }
    """
    pass
```

### 3.2 USD 结构模板

```
/World (Xform, Stage 默认 Prim)
 ├── customData: { ontology: { sourceScene, datasetId, exportVersion, exportTimestamp } }
 ├── upAxis = "Z", metersPerUnit = 1.0
 │
 ├── /World/Robot/
 │   └── franka_001 (Xform, references franka.usd)
 │       └── customData: { ontology: { instanceId, objectTypeRid, ... } }
 │
 ├── /World/Shelves/
 │   └── shelf_001 (Xform, references SM_Std_Shelf.usd)
 │       ├── customData: { ontology: {...} }
 │       ├── xformOp:translate = (1.5, 2.0, 0)
 │       ├── xformOp:rotateXYZ = (0, 0, 90)
 │       └── UsdPhysics.CollisionAPI
 │
 └── /World/Boxes/
     └── box_small_001 (Xform, references SM_Std_Box_Small.usd)
         ├── customData: { ontology: {...} }
         ├── xformOp:translate = (0.5, 0.3, 0.5)
         ├── UsdPhysics.CollisionAPI
         ├── UsdPhysics.RigidBodyAPI
         ├── UsdPhysics.MeshCollisionAPI (approximation=none)
         └── UsdPhysics.MassAPI (mass=0.3)
```

### 3.3 物理 Schema 应用规则

```python
def apply_physics_schema(prim, collision_type: str, mass: float = None, friction: float = 0.5):
    """根据 collision_type 应用不同的 USD Physics Schema。"""
    
    # 所有类型都需要 CollisionAPI
    UsdPhysics.CollisionAPI.Apply(prim)
    
    if collision_type == "static":
        # 静态物体只需要 CollisionAPI
        return
    
    # dynamic 和 graspable 都需要刚体 + 质量
    UsdPhysics.RigidBodyAPI.Apply(prim)
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    if mass is not None:
        mass_api.CreateMassAttr(mass)
    
    if collision_type == "graspable":
        # graspable 使用精确 mesh 碰撞
        mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
        mesh_collision.CreateApproximationAttr("none")
    elif collision_type == "dynamic":
        # dynamic 使用 convex hull（性能更好）
        mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
        mesh_collision.CreateApproximationAttr("convexHull")
```

### 3.4 customData 写入规范

```python
def write_ontology_metadata(prim, instance, scene, export_version: int):
    """在 Prim 上写入本体追溯信息。"""
    from datetime import datetime
    
    prim.SetCustomDataByKey("ontology", {
        "instanceId": instance.id,
        "objectTypeRid": instance.object_type_rid,
        "fileNumber": instance.file_number,
        "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_PhysicsHint"],
        "sourceScene": scene.id,
        "datasetId": "standard_practice",  # M0 硬编码
        "exportVersion": export_version,
        "exportTimestamp": datetime.utcnow().isoformat() + "Z"
    })
```

---

## 四、FBX → USD 转换

### 4.1 文件：`backend/lite/services/fbx_converter.py`

**M0 阶段简化实现**（手动准备 USD）：

```python
import hashlib
from pathlib import Path

def get_or_convert_usd(asset) -> str:
    """
    获取资产的 USD 路径。如果缓存有效则直接返回，否则触发转换。
    
    Returns:
        USD 文件的相对路径
    """
    fbx_path = Path(asset.fbx_source_path)
    if not fbx_path.exists():
        raise FileNotFoundError(f"FBX 源文件不存在: {fbx_path}")
    
    current_hash = _file_hash(fbx_path)
    
    # 缓存命中
    if (asset.usd_cache_hash == current_hash 
        and asset.usd_cached_path 
        and Path(asset.usd_cached_path).exists()):
        return asset.usd_cached_path
    
    # 缓存失效或未转换，触发转换
    usd_path = _convert_fbx_to_usd(fbx_path)
    
    # 更新资产记录
    asset.usd_cached_path = str(usd_path)
    asset.usd_cache_hash = current_hash
    # ... save to DB
    
    return str(usd_path)


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def _convert_fbx_to_usd(fbx_path: Path) -> Path:
    """
    FBX → USD 转换。
    
    M0 实现：如果对应 USD 文件已存在于 usd_cache/ 目录（用户手动转好），直接返回。
    M1 实现：调用 NVIDIA asset_converter 或 Blender 无头模式。
    """
    usd_path = Path("assets/usd_cache") / (fbx_path.stem + ".usd")
    if usd_path.exists():
        return usd_path
    raise NotImplementedError(
        "M0 阶段请手动把 FBX 转为 USD 放入 assets/usd_cache/。"
        "M1 实现自动转换。"
    )
```

---

## 五、前端页面规划

### 5.1 页面文件

```
frontend/scenes/
├── scenes.html          # 场景列表 + 简单管理（一个页面搞定）
└── scenes.js            # Vue 应用逻辑
```

### 5.2 scenes.html 结构

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>场景管理 - OntoTwin</title>
    <link rel="stylesheet" href="/static/common.css">
    <!-- CDN -->
    <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <style>
        /* 页面专属样式 */
    </style>
</head>
<body>
    <div id="app">
        <!-- 三个主要区域 -->
        <section id="scene-list">
            <!-- 场景列表 -->
        </section>
        
        <section id="scene-detail">
            <!-- 当前选中场景的详情：边界、实例列表、添加实例、导出按钮 -->
        </section>
        
        <section id="asset-library">
            <!-- 资产库侧边栏 -->
        </section>
    </div>
    
    <script src="scenes.js"></script>
</body>
</html>
```

### 5.3 交互流程

```
用户打开 /scenes
 → 看到场景列表（首次进入为空）
 → 点击"新建场景" → 填写名称和边界 → 创建
 → 点击某个场景 → 右侧展示详情
 → 详情页可以：
    - 添加实例（从资产库选）
    - 填写/修改实例坐标
    - 点击"导出 USD" → 下载文件
```

### 5.4 全局 API 调用封装

```javascript
// scenes.js 顶部
const API_BASE = '/api/v3/lite';

const api = {
    scenes: {
        list: () => axios.get(`${API_BASE}/scenes`),
        create: (data) => axios.post(`${API_BASE}/scenes`, data),
        get: (id) => axios.get(`${API_BASE}/scenes/${id}`),
        export: (id, opts) => axios.post(`${API_BASE}/scenes/${id}/export`, opts),
    },
    instances: {
        list: () => axios.get(`${API_BASE}/instances`),
        addToScene: (sceneId, ids) => 
            axios.post(`${API_BASE}/scenes/${sceneId}/instances`, { instance_ids: ids }),
    },
    assets: {
        list: () => axios.get(`${API_BASE}/assets`),
    }
};
```

---

## 六、路由注册

### `backend/lite/api/__init__.py`

```python
from flask import Blueprint

def register_lite_routes(app):
    """向 Flask app 注册本次新增的所有路由。"""
    from .scenes import bp as scenes_bp
    from .instances import bp as instances_bp
    from .assets import bp as assets_bp
    from .export import bp as export_bp
    
    app.register_blueprint(scenes_bp, url_prefix='/api/v3/lite/scenes')
    app.register_blueprint(instances_bp, url_prefix='/api/v3/lite/instances')
    app.register_blueprint(assets_bp, url_prefix='/api/v3/lite/assets')
    app.register_blueprint(export_bp, url_prefix='/api/v3/lite')
    
    # 前端静态文件
    @app.route('/scenes')
    def scenes_page():
        from flask import send_from_directory
        return send_from_directory('../frontend/scenes', 'scenes.html')
```

### `backend/app.py` 末尾（唯一修改）

```python
# 现有代码不变
# ...

# ============ OntoTwin Lite 模块（3.0 新增）============
try:
    from lite.api import register_lite_routes
    register_lite_routes(app)
    print("[Lite] 模块加载成功")
except Exception as e:
    print(f"[Lite] 模块加载失败: {e}")
```

---

## 七、错误处理约定

所有新增 API 统一错误响应格式：

```json
{
  "error": {
    "code": "validation_error",
    "message": "Scene id already exists",
    "details": {}
  }
}
```

**标准错误码**：
- `validation_error` (400)
- `not_found` (404)
- `conflict` (409)
- `internal_error` (500)

Flask 异常处理：

```python
@bp.errorhandler(ValueError)
def handle_value_error(e):
    return {"error": {"code": "validation_error", "message": str(e)}}, 400
```

---

## 八、依赖清单

### 后端新增依赖（需用户确认后加入 requirements.txt）

```txt
usd-core>=26.3         # Pixar OpenUSD Python SDK
SQLAlchemy>=2.0        # ORM（可选，用原生 sqlite3 也行）
```

### 前端 CDN（写在 HTML 里）

```html
<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>
```

---

## 九、目录结构最终形态

```
d:\tmp\digital_twin_aircraft\
├── backend/
│   ├── (现有文件，保持不变)
│   ├── app.py                  # ← 仅在末尾加 3 行
│   └── lite/                   # ← 新增
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── scenes.py
│       │   ├── instances.py
│       │   ├── assets.py
│       │   └── export.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── db.py          # SQLAlchemy engine/session
│       │   └── schemas.py     # 表定义
│       ├── services/
│       │   ├── __init__.py
│       │   ├── usd_exporter.py
│       │   ├── fbx_converter.py
│       │   └── scene_service.py
│       └── db/
│           └── lite.db        # (.gitignore)
│
├── frontend/
│   ├── (现有 HTML 文件，保持不变)
│   └── scenes/                 # ← 新增
│       ├── scenes.html
│       └── scenes.js
│
├── assets/                     # ← 新增
│   ├── fbx/                    # FBX 源文件
│   └── usd_cache/              # USD 缓存
│
├── exports/                    # ← 新增（存导出的 USD）
│
├── ue_project/                 # ← 新增（M2 创建）
│
├── docs/                       # ← 新增
│   ├── PROJECT_BRIEF.md
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── EXISTING_CODEBASE_MAP.md
│   ├── TECH_SPEC.md            # ← 本文件
│   ├── IMPLEMENTATION_PLAN.md
│   ├── TRAINING_BRIEF.md       # M2 创建
│   └── legacy/                 # 旧版本文档（参考用）
│       ├── 3.0_*.md
│       └── 2.x_*.md
│
└── CLAUDE.md                   # ← Claude Code 配置
```
