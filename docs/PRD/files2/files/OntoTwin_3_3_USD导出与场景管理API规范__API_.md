# OntoTwin 3.3 USD 导出与场景管理 API 规范（API）

| 字段 | 内容 |
|---|---|
| **文档版本** | v3.3-r1 |
| **日期** | 2026-04-17 |
| **状态** | 草稿（待审阅） |
| **归属** | 后端 REST API |
| **关联** | 3.0 USD 导出 / 3.1 Scene 管理 / 3.2 UE 改造 |

---

## 一、概述

本文档定义 OntoTwin 3.x 新增的所有 REST API 接口，作为前后端、UE 侧的对接契约。

### 1.1 基础约定

- **协议**：HTTPS（生产）/ HTTP（开发）
- **Base URL**：`/api/v3`
- **认证**：Bearer Token（`Authorization: Bearer <token>`）
- **Content-Type**：`application/json`（除文件上传 / 下载外）
- **字符编码**：UTF-8
- **时间格式**：ISO 8601 UTC（如 `2026-04-17T10:30:00Z`）
- **坐标单位**：米（m），Z-up，右手系

### 1.2 错误响应统一格式

```json
{
  "error": {
    "code": "validation_error",
    "message": "human readable error message",
    "details": {
      "field": "bounds.x",
      "reason": "x_max must be greater than x_min"
    }
  }
}
```

**标准错误码**：

| code | HTTP Status | 含义 |
|---|---|---|
| `validation_error` | 400 | 请求参数校验失败 |
| `not_found` | 404 | 资源不存在 |
| `conflict` | 409 | 资源冲突（如 ID 重复） |
| `forbidden` | 403 | 无权限 |
| `unauthorized` | 401 | 未登录或 Token 失效 |
| `internal_error` | 500 | 服务端错误 |
| `asset_missing` | 404 | 引用的资产不存在 |
| `job_failed` | 500 | 异步任务执行失败 |
| `stale_after_event_id` | 410 | 事件游标过期（2.6 专用，此处复用命名规范）|

---

## 二、Scene 管理接口

### 2.1 列出数据集下的场景

```http
GET /api/v3/datasets/{dataset_id}/scenes
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `q` | string | 否 | 按名称模糊搜索 |
| `sort_by` | string | 否 | `updated_at` (默认) / `name` / `instance_count` |
| `order` | string | 否 | `desc` (默认) / `asc` |
| `limit` | int | 否 | 默认 50 |
| `offset` | int | 否 | 默认 0 |

**响应 200**：

```json
{
  "total": 3,
  "items": [
    {
      "id": "warehouse_demo_01",
      "dataset_id": "standard_practice",
      "display_name": "仓库演示场景",
      "description": null,
      "bounds": {
        "x": [-30, 30],
        "y": [-20, 20],
        "z": [0, 5]
      },
      "up_axis": "Z",
      "unit": "meter",
      "structure_dxf_path": "/datasets/standard_practice/dxf/warehouse.dxf",
      "structure_dxf_uploaded_at": "2026-04-10T08:00:00Z",
      "created_at": "2026-04-10T08:00:00Z",
      "updated_at": "2026-04-15T14:30:00Z",
      "stats": {
        "instance_count": 35,
        "static_count": 23,
        "dynamic_count": 8,
        "graspable_count": 4
      },
      "latest_export": {
        "version": 3,
        "exported_at": "2026-04-15T14:30:00Z",
        "file_size_bytes": 251680
      }
    }
  ]
}
```

---

### 2.2 创建场景

```http
POST /api/v3/datasets/{dataset_id}/scenes
Content-Type: application/json
```

**请求体**：

```json
{
  "id": "warehouse_demo_01",
  "display_name": "仓库演示场景",
  "description": "演示用的标准仓库布局",
  "bounds": {
    "x": [-30, 30],
    "y": [-20, 20],
    "z": [0, 5]
  }
}
```

**校验规则**：
- `id` 只能包含 `[a-zA-Z0-9_-]`，长度 ≤ 64
- `id` 在同一 dataset 下唯一
- `display_name` 非空，长度 ≤ 256
- `bounds` 的每个轴 max > min
- `up_axis` 默认 `"Z"`（当前版本不允许其他值）
- `unit` 默认 `"meter"`（当前版本不允许其他值）

**响应 201**：返回创建的 Scene 对象（同 §2.1 的 item 结构）

**错误**：
- 400 `validation_error` — 字段校验失败
- 409 `conflict` — ID 已存在

---

### 2.3 获取场景详情

```http
GET /api/v3/scenes/{scene_id}
```

**响应 200**：

```json
{
  "id": "warehouse_demo_01",
  "dataset_id": "standard_practice",
  "display_name": "仓库演示场景",
  "description": null,
  "bounds": { "x": [-30, 30], "y": [-20, 20], "z": [0, 5] },
  "up_axis": "Z",
  "unit": "meter",
  "structure_dxf_path": "/datasets/standard_practice/dxf/warehouse.dxf",
  "placements": [],
  "created_at": "2026-04-10T08:00:00Z",
  "updated_at": "2026-04-15T14:30:00Z",
  "stats": {
    "instance_count": 35,
    "static_count": 23,
    "dynamic_count": 8,
    "graspable_count": 4
  },
  "latest_export": { ... },
  "recent_exports_count": 3
}
```

---

### 2.4 更新场景基本信息

```http
PUT /api/v3/scenes/{scene_id}
Content-Type: application/json
```

**请求体**（部分更新，所有字段可选）：

```json
{
  "display_name": "新名称",
  "description": "新描述",
  "bounds": { ... }
}
```

**不可修改**：`id`、`dataset_id`、`up_axis`、`unit`

**响应 200**：返回更新后的 Scene 对象

---

### 2.5 删除场景

```http
DELETE /api/v3/scenes/{scene_id}
```

**行为**：
- 删除 Scene 记录
- 从所有归属该 Scene 的 Instance 的 `belongs_to_scenes` 中移除该 ID
- 不删除 Instance 本身
- 不删除导出历史文件（保留供审计）

**响应 204**：No Content

---

### 2.6 添加 Instance 到场景

```http
POST /api/v3/scenes/{scene_id}/instances
Content-Type: application/json
```

**请求体**：

```json
{
  "instance_ids": ["shelf_001", "shelf_002", "box_001"]
}
```

**行为**：
- 对每个 Instance，将 `scene_id` 添加到其 `belongs_to_scenes`（如果不存在）
- 已经归属的 Instance 被忽略（幂等）

**响应 200**：

```json
{
  "added": ["shelf_001", "shelf_002"],
  "already_existed": ["box_001"],
  "not_found": []
}
```

---

### 2.7 从场景移除 Instance

```http
DELETE /api/v3/scenes/{scene_id}/instances/{instance_id}
```

**行为**：从 Instance 的 `belongs_to_scenes` 中移除该 scene_id。Instance 本身不删除。

**响应 204**：No Content

---

### 2.8 列出场景下的实例

```http
GET /api/v3/scenes/{scene_id}/instances
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `object_type_rid` | string | 否 | 按类型过滤 |
| `collision_type` | string | 否 | `static` / `dynamic` / `graspable` |
| `limit` | int | 否 | 默认 100 |
| `offset` | int | 否 | 默认 0 |

**响应 200**：

```json
{
  "total": 35,
  "items": [
    {
      "id": "shelf_001",
      "object_type_rid": "ri.obj.shelf",
      "interfaces": {
        "I3D_Representable": {
          "file_number": "SM_Std_Shelf_200",
          "lod_strategy": "level_2",
          "is_visible": true
        },
        "I3D_Spatial": {
          "translation": [1.5, 2.0, 0.0],
          "rotation": [0, 0, 90],
          "scale": [1, 1, 1]
        },
        "I3D_PhysicsHint": {
          "collision_type": "static",
          "mass": 50.0,
          "friction": 0.6
        }
      },
      "belongs_to_scenes": ["warehouse_demo_01"]
    }
  ]
}
```

---

### 2.9 上传 DXF 结构文件

```http
POST /api/v3/scenes/{scene_id}/structure/dxf
Content-Type: multipart/form-data
```

**请求字段**：
- `file`：DXF 文件（二进制）

**后端行为**：
1. 保存文件到 `/datasets/{dataset_id}/dxf/{scene_id}.dxf`
2. 用 `ezdxf` 做一次校验解析，确认图层规范正确
3. 更新 Scene 的 `structure_dxf_path` 和 `structure_dxf_uploaded_at`

**响应 200**：

```json
{
  "path": "/datasets/standard_practice/dxf/warehouse_demo_01.dxf",
  "uploaded_at": "2026-04-17T10:30:00Z",
  "parsed_summary": {
    "walls": 12,
    "floors": 3,
    "columns": 8
  }
}
```

**错误 400**（DXF 解析失败）：

```json
{
  "error": {
    "code": "validation_error",
    "message": "DXF file parsing failed",
    "details": {
      "reason": "Required layer '1.21-墙体' not found",
      "found_layers": ["0", "Defpoints", "layer_a"]
    }
  }
}
```

---

### 2.10 删除 DXF 关联

```http
DELETE /api/v3/scenes/{scene_id}/structure/dxf
```

**响应 204**：No Content

---

## 三、USD 导出接口

### 3.1 触发场景导出

```http
POST /api/v3/scenes/{scene_id}/export
Content-Type: application/json
```

**请求体**：

```json
{
  "format": "usda",
  "include_physics": true,
  "include_procedural_rules": true,
  "bundle_assets": false,
  "rebuild_asset_cache": false,
  "output_filename": null
}
```

**所有字段可选**，默认值见 3.0 文档 §3.2.4。

**响应 202**（异步任务已创建）：

```json
{
  "job_id": "export_01HW4TZ5X8",
  "status": "queued",
  "scene_id": "warehouse_demo_01",
  "created_at": "2026-04-17T10:30:00Z",
  "polling_url": "/api/v3/export/jobs/export_01HW4TZ5X8"
}
```

**预校验错误 400**：

```json
{
  "error": {
    "code": "validation_error",
    "message": "Scene validation failed. Fix issues before export.",
    "details": {
      "errors": [
        { "type": "empty_scene", "message": "Scene has no instances" }
      ]
    }
  }
}
```

> 注：预校验失败时直接返回 400，不创建 job。

---

### 3.2 查询导出任务状态

```http
GET /api/v3/export/jobs/{job_id}
```

**响应 200**：

```json
{
  "job_id": "export_01HW4TZ5X8",
  "scene_id": "warehouse_demo_01",
  "status": "running",
  "progress": {
    "stage": "converting_assets",
    "current": 8,
    "total": 15,
    "stage_description": "正在转换资产（8/15）"
  },
  "created_at": "2026-04-17T10:30:00Z",
  "started_at": "2026-04-17T10:30:01Z",
  "completed_at": null,
  "result": null,
  "error": null
}
```

**status 状态机**：`queued` → `running` → `success` / `failed` / `cancelled`

**stage 枚举值**：
- `validating` — 预校验
- `converting_assets` — 转换 FBX → USD
- `generating_structure` — 解析 DXF 生成结构
- `composing_scene` — 组装主 USD
- `writing_file` — 写入文件

**完成后响应（status=success）**：

```json
{
  "job_id": "export_01HW4TZ5X8",
  "scene_id": "warehouse_demo_01",
  "status": "success",
  "progress": { "stage": "done", "current": 15, "total": 15 },
  "created_at": "2026-04-17T10:30:00Z",
  "started_at": "2026-04-17T10:30:01Z",
  "completed_at": "2026-04-17T10:30:18Z",
  "result": {
    "export_version": 4,
    "file_path": "/tmp/exports/warehouse_demo_01_v4.usda",
    "file_size_bytes": 251680,
    "download_url": "/api/v3/export/jobs/export_01HW4TZ5X8/download",
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
        "code": "missing_mass_hint",
        "message": "collision_type=graspable but no mass_hint, using default 0.5kg"
      }
    ],
    "errors": []
  },
  "error": null
}
```

**失败响应（status=failed）**：

```json
{
  "status": "failed",
  "error": {
    "code": "asset_missing",
    "message": "FBX file not found for SM_Std_Shelf_200",
    "stage": "converting_assets"
  }
}
```

---

### 3.3 下载导出文件

```http
GET /api/v3/export/jobs/{job_id}/download
```

**响应 200**：
- `Content-Type: text/plain` (usda) 或 `application/octet-stream` (usdc)
- `Content-Disposition: attachment; filename="warehouse_demo_01_v4.usda"`
- Body：文件二进制

**错误 404**：Job 未完成或已过期（Job 保留 24 小时后清理）

---

### 3.4 取消导出任务

```http
POST /api/v3/export/jobs/{job_id}/cancel
```

**响应 200**：

```json
{
  "job_id": "export_01HW4TZ5X8",
  "status": "cancelled"
}
```

**行为**：只能取消 `queued` 或 `running` 状态的任务。

---

### 3.5 获取场景导出历史

```http
GET /api/v3/scenes/{scene_id}/exports
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 默认 20 |
| `offset` | int | 否 | 默认 0 |

**响应 200**：

```json
{
  "total": 4,
  "items": [
    {
      "version": 4,
      "exported_at": "2026-04-17T10:30:18Z",
      "file_size_bytes": 251680,
      "file_hash": "sha256:...",
      "file_available": true,
      "download_url": "/api/v3/scenes/warehouse_demo_01/exports/4/download",
      "report_summary": {
        "instance_count": 35,
        "warning_count": 2,
        "error_count": 0
      }
    }
  ]
}
```

---

### 3.6 下载历史导出文件

```http
GET /api/v3/scenes/{scene_id}/exports/{version}/download
```

**响应**：同 §3.3。

**错误 404**：版本不存在或文件已过期（默认保留最近 10 个版本）

---

### 3.7 获取导出报告

```http
GET /api/v3/scenes/{scene_id}/exports/{version}/report
```

**响应 200**：完整的导出报告（JSON，同 3.0 文档 §3.2.5）

---

### 3.8 场景预校验

```http
POST /api/v3/scenes/{scene_id}/validate
```

**响应 200**：

```json
{
  "is_valid": false,
  "errors": [
    {
      "type": "out_of_bounds",
      "instance_id": "box_003",
      "message": "Instance translation [35.0, 0, 0] exceeds scene x bound [-30, 30]"
    }
  ],
  "warnings": [
    {
      "type": "missing_mass_hint",
      "instance_id": "box_005",
      "message": "graspable object lacks mass, will use default 0.5kg"
    }
  ]
}
```

---

## 四、UE 对接接口（3.2 专用）

### 4.1 拉取场景的 UE 加载数据

```http
GET /api/v3/scenes/{scene_id}/ue_data
```

**响应 200**：

```json
{
  "scene": {
    "id": "warehouse_demo_01",
    "display_name": "仓库演示场景",
    "up_axis": "Z",
    "unit": "meter",
    "bounds": { ... }
  },
  "structure": {
    "type": "dxf_generated",
    "entities": [
      {
        "id": "wall_001",
        "layer": "1.21-墙体",
        "generate_type": "PROCEDURAL_WALL",
        "data": {
          "path": [[0, 0], [15, 0], [15, 8]],
          "height": 4.5,
          "thickness": 0.24,
          "material_params": { "color": "#C0C0C0" }
        }
      },
      {
        "id": "column_p1",
        "layer": "1.20-柱子",
        "generate_type": "INSTANCE",
        "data": {
          "mesh_id": "SM_Std_Column_500",
          "transform": {
            "loc": [0.5, 0.5, 0],
            "rot": [0, 0, 90],
            "scale": [1, 1, 1]
          }
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
        "fallback_bounding_box": { "x": 0.8, "y": 2.0, "z": 2.0 }
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
        "collision_type": "static",
        "source_scene_id": "warehouse_demo_01"
      }
    }
  ]
}
```

**坐标单位**：米（m），UE 侧需 × 100 转为 cm。

---

### 4.2 批量回写位置变更

```http
POST /api/v3/scenes/{scene_id}/placements/update
Content-Type: application/json
```

**请求体**：

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
  ],
  "write_mode": "default_coordinates"
}
```

**`write_mode` 枚举**：
- `default_coordinates`（默认）：写入 Instance 的 `I3D_Spatial`，影响所有归属 Scene
- `scene_placement`：仅为当前 Scene 创建 StaticPlacement 覆盖（不影响其他 Scene）

**响应 200**：

```json
{
  "success_count": 2,
  "failed": [],
  "updated_instances": ["shelf_001", "box_003"],
  "warnings": [
    {
      "instance_id": "shelf_001",
      "message": "shelf_001 belongs to 2 scenes; updating default coordinates will affect all scenes"
    }
  ]
}
```

**校验规则**：
- 每个 `instance_id` 必须归属当前 `scene_id`（否则 404）
- 每个 `translation` 必须在 Scene.bounds 内（否则 400）

---

## 五、资产库接口（3.0 新增）

### 5.1 查询资产详情

```http
GET /api/v3/assets/{file_number}
```

**响应 200**：

```json
{
  "file_number": "SM_Std_Shelf_200",
  "display_name": "标准货架 200",
  "fbx_source_path": "/assets/fbx/SM_Std_Shelf_200.fbx",
  "lod_strategy": "level_2",
  "usd_cached_path": "/assets/usd_cache/SM_Std_Shelf_200.usd",
  "usd_cache_hash": "sha256:abc123...",
  "usd_cached_at": "2026-04-15T08:00:00Z",
  "physics_proxy_path": null,
  "bounding_box": { "x": 0.8, "y": 2.0, "z": 2.0 },
  "meta": {
    "mass_hint": 50.0,
    "material_hint": "metal"
  }
}
```

---

### 5.2 触发单个资产 USD 重建

```http
POST /api/v3/assets/{file_number}/usd/rebuild
```

**响应 202**：

```json
{
  "job_id": "asset_rebuild_01HW...",
  "status": "queued",
  "polling_url": "/api/v3/asset/jobs/asset_rebuild_01HW..."
}
```

---

### 5.3 批量预转资产

```http
POST /api/v3/assets/usd/batch_build
Content-Type: application/json
```

**请求体**：

```json
{
  "file_numbers": ["SM_xxx1", "SM_xxx2"],
  "force_rebuild": false
}
```

或（全部资产）：

```json
{
  "file_numbers": null,
  "force_rebuild": false
}
```

**响应 202**：

```json
{
  "job_id": "asset_batch_01HW...",
  "total_assets": 87,
  "polling_url": "/api/v3/asset/jobs/asset_batch_01HW..."
}
```

---

## 六、命令行工具对接

3.0 提供的 CLI 工具 `ontotwin-export` 基于本 API 规范包装。配置方式：

```bash
# 设置服务器地址和 token
export ONTOTWIN_API_URL="https://nexus.internal/api/v3"
export ONTOTWIN_API_TOKEN="xxxxxx"

# 导出单个场景
ontotwin-export --scene warehouse_demo_01 --output ./warehouse.usda

# 等价于：
curl -H "Authorization: Bearer $ONTOTWIN_API_TOKEN" \
     -X POST \
     $ONTOTWIN_API_URL/scenes/warehouse_demo_01/export \
     -d '{"format":"usda"}' \
  | jq -r '.job_id' \
  | xargs -I {} poll_and_download ...
```

---

## 七、接口版本演进策略

- **向后兼容**：同一 `v3` 下字段只增不删
- **破坏性变更**：启用新版本号（`v4`），两版本并存至少 6 个月
- **弃用标记**：通过响应头 `Deprecation: true` 和 `Sunset: <date>` 告知客户端

---

## 八、附录：JSON Schema 定义

为方便客户端生成类型代码，所有核心数据结构的 JSON Schema 放在：

```
https://ontotwin.internal/schemas/v3/scene.schema.json
https://ontotwin.internal/schemas/v3/instance.schema.json
https://ontotwin.internal/schemas/v3/export-options.schema.json
https://ontotwin.internal/schemas/v3/export-report.schema.json
https://ontotwin.internal/schemas/v3/placement.schema.json
https://ontotwin.internal/schemas/v3/ue-scene-data.schema.json
```

建议的代码生成工具：
- TypeScript：`json-schema-to-typescript`
- Python：`datamodel-code-generator`
- UE/C++：人工维护 USTRUCT 对应
