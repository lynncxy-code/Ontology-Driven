# OntoTwin Nexus M5b —— 系统一 spatial 写 + coord 杂项 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图 M5 的后半（M5b），也是路线图最后一块。
> 前置：基础 30 + M1–M4 + M6 + M5a = 84 工具，均已交付 main（M3/M5a 后端已/待部署 88.66）。

## 修订记录

- **v1（2026-07-30）**：首版。用户定：3 个 spatial 写加 expected 护栏、mapping/export 不加（全局文件/纯计算）。沿用直通式 / 文档 A。

---

## 1. 目标与非目标

### 目标

补全 CAD/坐标标定的剩余面：系统一 spatial 写（规范剖面 / 坐标帧 / 帧标定 / 变换预览）+ coord 杂项（场景导出 / 块-资产全局映射读写）。

### 非目标

- **无后续里程碑**：M5b 完成即路线图收官。
- 不动已交付的 84 工具。

### 与系统二（M2）的区分

M2 做的是 `/api/v2/spatial-frames`（底图参考帧，`reference_frame` 命名）；M5b 做的是**系统一** `/api/v2/spatial/*`（坐标规范系：profile/frames/preview）。两套不同，命名上 M5b 用 `spatial_profile`/`spatial_frame`（不带 reference）。

---

## 2. 架构

- 直通式；`register(mcp, client, registry)`；文档 A。
- **并发护栏（只给隐式激活的项目写）**：`set_spatial_profile`/`upsert_spatial_frame`/`calibrate_spatial_frame` 写隐式当前激活项目 → 加可选 `expected_project_id`。`save_block_asset_mapping` 写**全局** `block_asset_mapping.json`（非项目数据）→ **不加**；`export_cad_scene`/`preview_spatial_transform` 纯计算 → 无。
- **后端改动**：`project_store.set_spatial_profile`/`upsert_frame` 加锁内 expected 校验（复用 M0 `ProjectMismatch`），3 个端点透传 + 捕获 → 409。**PG 未覆盖这两个方法 → 继承，无平价**。
- **client / errors 零改动**：get/post_json/put_json 已存在；400（无激活/校验）/409/5xx 映射已覆盖。

---

## 3. 工具清单（7 个：3 读 + 4 写）→ MCP 84→91

### 3.1 系统一 spatial

| 工具 | 方法 + 端点 | 类型 | 参数 |
|---|---|---|---|
| `set_spatial_profile` | PUT `/api/v2/spatial/profile` | 写（⚠️ 触发全场景重算 `_rederive_components`） | `profile:dict`, `expected_project_id=""` |
| `upsert_spatial_frame` | POST `/api/v2/spatial/frames` | 写（建/改坐标帧） | `frame:dict`, `expected_project_id=""` |
| `calibrate_spatial_frame` | POST `/api/v2/spatial/frames/<id>/calibrate` | 写（锚点拟合帧） | `frame_id`, `anchors:list`, `name=""`, `unit=""`, `expected_project_id=""` |
| `preview_spatial_transform` | POST `/api/v2/spatial/preview` | 读/算 | `points:list`, `floor=1`, `profile:Optional[dict]=None` |

### 3.2 coord 杂项

| 工具 | 方法 + 端点 | 类型 | 参数 |
|---|---|---|---|
| `export_cad_scene` | POST `/api/v2/coord/export` | 读/算 | `transform_matrix:list`, `entities:list`, `polylines:Optional[list]=None`, `wall_height=4500`, `wall_thickness=240` |
| `get_block_asset_mapping` | GET `/api/v2/coord/mapping` | 读 | — |
| `save_block_asset_mapping` | POST `/api/v2/coord/mapping` | 写（**全局**文件，无 expected） | `mapping:dict` |

### 请求体映射

- `set_spatial_profile` → body = `profile`（含 `ue_transform`/`floor_table`/`canonical_origin` 任意子集）+ 非空 `expected_project_id`。端点只读那几个 key + 旁读 `expected_project_id`，其余忽略。
- `upsert_spatial_frame` → body = `frame`（含 `id`）+ 非空 `expected_project_id`。**端点把整个 body 当 frame**，故后端需先 `pop` 出 `expected_project_id` 再 upsert（见 §4.2）。
- `calibrate_spatial_frame` → body `{anchors}` + 非空 `name`/`unit`/`expected_project_id`；path `<frame_id>` 用 `quote(safe='/')`。
- `preview_spatial_transform` → body `{points, floor}` + 非 None `profile`。
- `export_cad_scene` → body `{transform_matrix, entities, wall_height, wall_thickness}` + 非 None `polylines`。
- `save_block_asset_mapping` → body = `mapping`（dict 直接作请求体）。

---

## 4. 后端能力扩展（加法式）

### 4.1 project_store 两方法加锁内 expected 校验

`set_spatial_profile`（约 804）、`upsert_frame`（在 `list_frames` 附近）各自 `with self._lock:` 内最前面加（复用 M0/update_raw_state 写法）：
```python
if expected_project_id is not None and self._active_id != expected_project_id:
    raise ProjectMismatch(expected_project_id, self._active_id)
```
签名：`set_spatial_profile(self, profile, expected_project_id=None)`、`upsert_frame(self, frame, expected_project_id=None)`。**PG 未覆盖 → 继承，无平价。**

### 4.2 三端点透传 + 捕获 ProjectMismatch → 409

- `spatial_profile_put`（约 1001）：`expected = data.get("expected_project_id")`；`set_spatial_profile(profile, expected_project_id=expected)`；`try/except ProjectMismatch → 409`（校验先于 `_rederive_components`，命中则不重算）。
- `spatial_frames_post`（约 1028）：**先** `frame = request.json or {}; expected = frame.pop("expected_project_id", None)`（把 expected 从 frame 剥离，避免污染帧数据）→ `upsert_frame(frame, expected_project_id=expected)`；`try/except → 409`。
- `spatial_frame_calibrate`（约 1039）：`expected = data.get("expected_project_id")`（端点单独 build frame，不 spread data）→ `upsert_frame(frame, expected_project_id=expected)`；`try/except → 409`。

统一 409 体：`{"error":"project changed","expected":e.expected,"actual":e.actual}`。缺省 expected=None 走旧路径、行为不变。

### 4.3 后端测试

`backend/tests/` 加：`set_spatial_profile`/`upsert_frame` 方法级 expected 命中/漏（用 `store` fixture，`ProjectMismatch`）；3 端点带错 expected → 409（用 `client` fixture）。**不改既有行为**。

---

## 5. 错误映射 / client

**零改动**。已覆盖：400「当前无激活项目」→ `NEXUS_NO_ACTIVE_PROJECT`（M0）；calibrate 锚点不足 400 → `NEXUS_VALIDATION_ERROR`；`ProjectMismatch` 409 → `NEXUS_PROJECT_CHANGED`（M0）。client 用 get/post_json/put_json（均已存在）。

---

## 6. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「坐标规范系 / 场景导出」段：

- **规范剖面**：`get_spatial_profile()`（基础层）看当前 → `set_spatial_profile(profile, expected_project_id=…)` 改（⚠️ **会触发全场景重算**，高危，带 expected）。
- **坐标帧**：`upsert_spatial_frame(frame, expected_project_id=…)` 建/改；`calibrate_spatial_frame(frame_id, anchors, expected_project_id=…)` 用锚点拟合；`preview_spatial_transform(points, floor)` 预览规范→UE。
- **场景导出 / 映射**：`export_cad_scene(transform_matrix, entities, polylines)` 出 UE 场景 JSON；`get_block_asset_mapping()` / `save_block_asset_mapping(mapping)` 读写**全局**块→资产映射（非项目数据、无 expected）。
- 金规：spatial 写带 `expected_project_id`（从 `get_active_project` 取）；profile PUT 会全场重算，改前想清楚。
- 触发示例：「把规范原点设成 (1,1)」「用这几组锚点标定 world 帧」「导出当前 CAD 场景 JSON」。

---

## 7. Repo 布局

```
backend/project_store.py       # set_spatial_profile / upsert_frame + expected（锁内）
backend/app.py                 # 3 端点透传 expected + 捕获 ProjectMismatch
backend/tests/                 # 方法级 + 端点 409 测试
mcp/ontotwin_mcp/tools/
  spatial_write.py             # 新增：7 个工具
  __init__.py                  # register_all 追加 spatial_write
```
client/errors/project_store_pg **不改**。

---

## 8. 测试策略

- **后端**：方法级 expected + 端点 409（§4.3）。
- **MCP 协议**：stdio 列表新增 7 工具；`call_tool` 挑 `get_block_asset_mapping` 走一遍。
- **MCP 单元（fake client）**：每工具断言 URL/方法/请求体；重点 `set_spatial_profile`/`upsert_spatial_frame` 的 expected 透传/省略（frame 合并 expected）、`calibrate` 的 path 编码、`save_block_asset_mapping` 的 dict 直传。
- **只读冒烟**：`get_block_asset_mapping` 可无参、稳定 → 纳入 `selfcheck.py`。
- **写路径**：spatial 写只对一次性抛弃项目验证，不碰生产库。

---

## 9. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · 后端 | set_spatial_profile/upsert_frame + expected + 3 端点 + 后端测试 | ✅ |
| B · spatial_write | 7 个工具 + register + 单测 | ✅ |
| C · skill+冒烟 | SKILL.md 段 + selfcheck 1 读工具 + stdio 协议测试 | ✅ |

A 前置；B、C 收口。

---

## 10. 依赖与兼容

- **无新依赖**、**client/errors/PG 零改动**。后端 project_store 2 方法 + app.py 3 端点加法式改动。
- 纯加法，现有 84 工具与测试不回归。MCP 工具总数 **84 → 91**。
- **需部署**：project_store.py + app.py 两文件 scp + restart（像 M3/M5a；改生产前确认）。

---

## 11. 风险科普

- **profile PUT 的放大效应**：改规范剖面会 `_rederive_components` 全场重算所有实例坐标——一次写、全场动。这类"高扇出写"最该有并发护栏(`expected_project_id`)：避免"以为在改 A 项目、实则 A 已被切走、把 B 项目全场坐标推乱"。
- **护栏边界的一般准则（本轮再次印证）**：写隐式当前激活项目 → 加 expected；写全局文件（`block_asset_mapping.json`）或纯计算（export/preview）→ 不加。判断依据始终是"目标是不是隐式的当前项目态"。
