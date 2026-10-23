# OntoTwin 2.9.1 CAD 实体批量入实例库需求说明书 (PRD)

> **文档定位：** 把 PRD 2.9 工作台解析出的 CAD 实体（含 UE 坐标），批量投入 PRD 2.3 的实例运维监控中心（InstanceStore）。
>
> **开发顺序：** 本模块（2.9.1）**依赖 2.9.2 先完成**。2.9.1 创建实例时需要 ObjectType 已存在且**所在数据集已激活**。

---

## 1. 产品背景

PRD 2.9 工作台目前的产出是 **JSON / CSV 文件**，需要人工导入下游系统。但项目内部其实已有一个完整的 **实例运维监控中心**（`InstanceStore` + `instance.html`），存放着所有"活着"的数字孪生实例，并提供 spawn / monitor / override 能力。

把"CAD 坐标"和"实例库"打通，就能实现完整闭环：

```
DXF 上传 → 类型审核（2.9.2）→ 坐标标定（2.9） → 实体投入实例库（2.9.1） → UE 看到 / 监控
```

2.9.1 解决"最后一公里"——让坐标标定的结果直接变成可监控、可干预的实例。

### 1.1 与 PRD 2.3.1（数据集批量投产）的关系

PRD 2.3.1 的核心论断是：**"批量投产的本质，不是批量创造实例，而是批量为已知实例分配场景坐标"**——它假设实例 ID 来自 MES/SAP 等外部系统，已通过 `POST /api/v2/instances` 提前注册，用户只是补坐标。

**2.9.1 与 2.3.1 是互补关系，不是替代：**

| 维度 | PRD 2.3.1（数据集批量投产） | PRD 2.9.1（CAD 批量入实例） |
| :--- | :--- | :--- |
| 实例 ID 来源 | MES/SAP 已注册 | 从 CAD 的 `EQUIP_ID` 来，或自动生成 |
| 坐标来源 | 用户手填 | CAD 仿射变换得到 |
| 操作方向 | 先有 ID，配坐标 | ID + 坐标一起来 |
| 适用前提 | 实例已存在 | 实例可能不存在 |

两者共享同一个 `InstanceStore`。2.9.1 必须处理"实例已被 2.3.1/MES 注册"的边界场景，详见第 7 节冲突处理。

---

## 2. 核心功能概览

| 功能模块 | 说明 |
| :--- | :--- |
| **类型自动绑定** | INSERT 的 block_name 直接对应 ObjectType.rid（2.9.2 已保证一致） |
| **激活数据集校验** | 三态校验：在激活集 / 在未激活集 / 完全没有，分别处理 |
| **实例 ID 推导** | 优先用 `attribs.EQUIP_ID`；缺失则自动生成 `<rid>-<hash6>` |
| **坐标自动注入** | 把 UE_X/UE_Y 注入 `translation_x/y`，UE_Z=0，`rotation_z = CAD rotation` |
| **批量预览与确认** | 弹窗展示即将创建/更新/冲突的实例列表，让用户最终确认 |
| **冲突处理** | 同 instanceId 已存在时三选一：更新坐标 / 跳过 / 新建副本 |
| **MES 已注册兼容** | 若实例已被 2.3.1/MES 注册但无坐标，默认走"补充坐标"路径 |
| **图片模式支持** | 图片模式 marker 已带 type 与 UE 坐标，复用同一后端接口 |

---

## 3. 系统架构

### 3.1 技术栈

延续 2.9 / 2.9.2 的栈，不引入新依赖。

### 3.2 文件清单

| 文件路径 | 职责 |
| :--- | :--- |
| `backend/app.py` | 新增 `/api/v2/coord/spawn_instances` 路由（1 个） |
| `backend/mapping_store.py` | 复用现有 `InstanceStore.spawn()` / `update()` 方法，**不改写** |
| `frontend/coord_workbench.html` | CAD 模式 Step5 导出面板新增"投入实例库"按钮；图片模式 `importToInstanceLib()` 函数补全实现 |

### 3.3 API 路由

| 路由 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/api/v2/coord/spawn_instances` | POST | 接收实体列表，批量创建/更新实例。支持 `commit` 参数做 dry-run/真正写入二阶段 |
| `/api/v2/instances`（现有） | — | 不改动；2.9.1 在后端内部调用 `InstanceStore.spawn()` / `update()`，不走前端 spawn 接口 |

---

## 4. 工作流

### 4.1 CAD 模式工作流

```
① 上传 DXF
   ↓
② 类型审核（2.9.2 已建 ObjectType，已发布并激活/合并到数据集）
   ↓
③ 锚点标定（拿到变换矩阵）
   ↓
④ 实体管理（勾选要导出哪些）
   ↓
⑤ 导出面板：
   ├─ [导出 JSON]      （PRD 2.9 已有）
   ├─ [下载 CSV]       （PRD 2.9 已有）
   └─ [投入实例库]      （2.9.1 新增） ★
```

### 4.2 投入实例库的两阶段流程

```
[点击投入实例库]
   ↓
前端 POST /spawn_instances?commit=false   ← dry-run
   ↓
后端逐条处理：
  1. 三态校验 block_name 对应的 ObjectType
  2. 推导 instance_id
  3. 应用仿射变换得到 UE 坐标
  4. 检测与 InstanceStore 现有实例的冲突
   ↓
返回预览：{ to_create, to_update_coord_only, conflicts, errors, warnings }
   ↓
前端弹窗展示 → 用户选冲突策略 → 确认
   ↓
前端 POST /spawn_instances?commit=true   ← 真写入
   ↓
后端调用 InstanceStore.spawn() / update()
   ↓
返回最终摘要 → 前端提示"完成 + 前往实例运维中心"
```

### 4.3 图片模式工作流

图片模式 Step2 已有"导入至实例库"按钮（当前是 `alert('即将对接')`），本次实现：

```
① 上传图片 + 像素锚点标定
   ↓
② 手动标注设备（每个 marker 已选 type、填名称/ID）
   ↓
[导入至实例库] → 复用同一后端接口
```

调用时把 marker 的 `type` 当成 `block_name`，校验流程与 CAD 模式完全一致（因为 marker 的 type 下拉框来源就是 `/api/v2/ontology/types`，所以必然在当前激活的 `_object_types` 中）。

---

## 5. 三态校验规则（核心）

后端处理每条 INSERT 时，按以下顺序校验：

| 校验项 | 三种结果 | 处理 |
| :--- | :--- | :--- |
| block_name 对应的 ObjectType 在 `_object_types` 中（即在当前激活数据集中） | ✅ 通过 | 继续后续处理 |
| 不在 `_object_types`，但在某个**未激活**数据集中 | ⚠️ 需切换 | 该条 error，提示"该类型存在于数据集 X，请在语义图谱总览先激活该数据集" |
| 任何数据集中都没有该 rid | ❌ 缺失 | 该条 error，提示"请先在 2.9.2 中创建该类型" |

**实现要点**：后端在校验时**扫描所有 `_datasets`**，能精确告诉用户该 rid 在哪里能找到，避免用户盲目排查。

### 5.1 校验返回示例

```json
{
  "errors": [
    {
      "block_name": "AGV",
      "reason": "type_not_in_active_dataset",
      "found_in_datasets": [
        {"id": "ds_user_02", "name": "我的工厂工作集"}
      ],
      "hint": "该类型存在于数据集'我的工厂工作集'，请先激活该数据集"
    },
    {
      "block_name": "UNKNOWN_BLOCK",
      "reason": "type_not_found",
      "found_in_datasets": [],
      "hint": "请先在 2.9.2 中创建该类型"
    }
  ]
}
```

---

## 6. 字段映射规则

| InstanceStore 字段 | 来源 |
| :--- | :--- |
| `instance_id` | `attribs.EQUIP_ID` → 若空则 `<rid>-<6位hash>` |
| `object_type_rid` | INSERT 的 `block_name`（CAD 模式）/ marker 的 `type`（图片模式） |
| `translation_x` | 仿射变换后的 UE_X（cm） |
| `translation_y` | 仿射变换后的 UE_Y（cm） |
| `translation_z` | 固定 `0`（2D 标定） |
| `rotation_z` | INSERT 的 `rotation`（度）；图片模式固定 `0` |
| `rotation_x/y`, `scale_*` | 取 `INTERFACES` 表中 `I3D_Spatial` 的默认值 |
| `is_visible` | `true` |
| `source` | 字符串：`cad:<文件名>` 或 `image:<文件名>` |
| `created_at` | 服务端当前时间 |

---

## 7. 冲突处理策略

`instance_id` 与 `InstanceStore` 中已有实例匹配时，按以下规则分类：

### 7.1 四种场景

| 场景 | 后端归类 | UI 显示 | 默认动作 | 用户可改 |
| :--- | :--- | :--- | :--- | :--- |
| 同 ID 实例存在且**已有非零坐标** | `conflicts` | 🟡 黄色冲突 | 按用户选的批策略 | ✅ |
| 同 ID 实例存在但**坐标全为 0**（推测来自 2.3.1/MES 注册但未部署） | `to_update_coord_only` | 🔵 蓝色"补充坐标" | 自动写入（不视为冲突） | ❌（透明） |
| 同 ID 实例存在且 `object_type_rid` 不一致 | `errors` | 🔴 红色错误 | 跳过，不写入 | ❌ |
| 同 ID 不存在 | `to_create` | 🟢 绿色新建 | 直接创建 | ❌ |

### 7.2 冲突的三种批策略（针对场景 1）

| 策略 | 说明 |
| :--- | :--- |
| **更新坐标** | 仅覆盖 `translation_*` / `rotation_z` 字段，其他字段保留（推荐，符合"重新标定"场景） |
| **跳过** | 完全不动现有实例 |
| **新建副本** | `instance_id` 自动加后缀 `-2`、`-3`，作为新实例创建（用于复制场景） |

前端弹窗按批次让用户选一次，本批次内统一执行。

---

## 8. 请求/响应数据格式

### 8.1 `POST /api/v2/coord/spawn_instances?commit=false`（dry-run）

请求：

```json
{
  "source_label": "新块.dxf",
  "mode": "dxf",
  "transform_matrix": [[a,b,tx],[c,d,ty]],
  "items": [
    {
      "block_name": "SDT-0200-甲-3",
      "cad_xy": [12450.5, -8700.2],
      "rotation": 90.0,
      "attribs": {"EQUIP_ID": "EQ-001", "MODEL": "甲型"}
    },
    {
      "block_name": "AGV",
      "cad_xy": [3000, 2000],
      "rotation": 0,
      "attribs": {"EQUIP_ID": "AGV-007"}
    }
  ],
  "conflict_strategy": "update_coord"
}
```

### 8.2 响应

```json
{
  "summary": {
    "total": 2,
    "to_create": 1,
    "to_update_coord_only": 0,
    "conflicts": 0,
    "errors": 1,
    "warnings": 0
  },
  "to_create": [
    {
      "instance_id": "EQ-001",
      "object_type_rid": "SDT-0200-甲-3",
      "translation_x": 1245.05, "translation_y": -870.02, "translation_z": 0,
      "rotation_z": 90.0
    }
  ],
  "to_update_coord_only": [],
  "conflicts": [],
  "errors": [
    {
      "block_name": "AGV",
      "reason": "type_not_in_active_dataset",
      "found_in_datasets": [{"id": "ds_user_02", "name": "我的工厂工作集"}],
      "hint": "该类型存在于数据集'我的工厂工作集'，请先激活该数据集"
    }
  ],
  "warnings": []
}
```

### 8.3 commit 阶段

`commit=true` 时用同样的 payload 触发真正写入；响应结构相同，但所有列表反映实际写入结果（带 `instance_id` 写入后的最终值）。

---

## 9. UI 设计：投入实例库弹窗

```
┌──────────────────────────────────────────────────────┐
│ 即将投入 InstanceStore                                │
├──────────────────────────────────────────────────────┤
│  🟢 新建: 8    🔵 补充坐标: 3    🟡 冲突: 2    🔴 错误: 1 │
│                                                       │
│  [展开详情 ▼]                                          │
│    🟢 EQ-001  SDT-0200-甲-3   (1245, -870)  新建      │
│    🔵 AGV-007 AGV              (300, 200)  补充坐标   │
│         （MES 已注册，原坐标(0,0,0)）                  │
│    🟡 EQ-002  SDT-0200-甲-3   (1830, -870)  冲突     │
│         （现有坐标(800, 200)）                         │
│    🔴 UNKNOWN_BLK              —            错误     │
│         （ObjectType 不存在，请先 2.9.2）              │
│                                                       │
│  冲突处理策略（仅作用于🟡冲突项）：                     │
│    (◉) 更新坐标   ( ) 跳过   ( ) 新建副本             │
│                                                       │
│  [取消]                          [确认投入]            │
└──────────────────────────────────────────────────────┘
```

确认后跳转提示：

```
✓ 已成功投入 11 个实例（新建 8、补充坐标 3）
跳过 2 个冲突项，1 个错误项未处理
[前往实例运维中心查看 →]   /instance
```

---

## 10. 错误与边界

| 场景 | 处理 |
| :--- | :--- |
| `block_name` 找不到对应 ObjectType | 该条 `errors`，按 5.1 区分"未激活"或"完全没有" |
| `transform_matrix` 缺失（未标定就点投入） | 整批 400 报错，前端按钮在未标定时禁用即可避免 |
| `cad_xy` 含非法值（NaN/字符串） | 该条 `errors`，列出原因 |
| 同批次内 `instance_id` 重复 | 自动加 `-2/-3` 后缀，标记为"批内重名已自动重命名"，列入 `warnings` |
| ObjectType 的 `asset_id` 为空（`ready=false`） | 仍允许创建实例，但响应 `warnings` 中标注"asset_id 缺失，UE 不会渲染" |
| 同 ID 但 `object_type_rid` 不一致 | 该条 `errors`，"实例 ID 已被其他类型占用" |

---

## 11. 与其他模块的关系

| 模块 | 关系 |
| :--- | :--- |
| **PRD 2.9 坐标标定工作台** | 在导出面板新增按钮；复用变换矩阵 |
| **PRD 2.9.2 本体类型自动建库** | **上游依赖**：必须先建好 ObjectType 且数据集已激活 |
| **PRD 2.3 实例运维监控中心** | 实例写入后立刻在 `instance.html` 可见、可监控、可干预 |
| **PRD 2.3.1 数据集批量投产** | **互补关系**：2.3.1 处理"有 ID 无坐标"（来自 MES），2.9.1 处理"ID + 坐标同时来自 CAD"。同 `instance_id` 时 2.9.1 自动走"补充坐标"路径，不创建副本 |
| **PRD 2.1 DigitalTwinSync** | 实例创建后由现有同步机制自动推送到 UE 端 |
| **语义图谱总览** | 2.9.1 校验失败时，引导用户到该页面激活相应数据集 |

---

## 12. 已知限制与约束

1. **不支持 POLYLINE 实体**：墙体/地面走程序化生成（PRD 2.5 TwinSceneBuilder），不入实例库。
2. **2D 限制**：Z 坐标固定为 0，不支持 CAD 的 3D 高程信息。
3. **rotation 单轴**：CAD 平面图旋转都是绕 Z 轴，X/Y 旋转固定为 0。
4. **不做反向同步**：实例库里的坐标变更不会回写到 DXF 文件。
5. **不持久化**：实例存在 `InstanceStore` 内存中，服务重启丢失（与现有体系一致）。
6. **跨数据集校验只读不切换**：2.9.1 发现 ObjectType 在未激活数据集时只提示，不自动激活——避免静默切换激活数据集导致其他实例引用悬空。

---

## 13. 未来演进路线

1. **支持复用现有实例**：投入时如果某 instance_id 已在场景中，可选"链接"而非"新建"。
2. **批次撤销**：每次批量投入生成一个 batch_id，提供"撤销整批"操作。
3. **AGV 路径线投入**：识别 AGV 线路图层的 POLYLINE，自动建一个 AGVRoute 实例（衔接 PRD 2.8）。
4. **3D 高程**：从图层名（如 `F2-生产设备`）或属性中提取楼层信息，自动设置 Z 坐标。
5. **UE 实时反馈**：投入后等待 UE 侧 ACK，UI 显示"已在 UE 中可见"状态。
6. **一键激活并投入**：2.9.1 检测到类型在未激活数据集时，提供"立即激活并继续"按钮（含副作用警告）。
