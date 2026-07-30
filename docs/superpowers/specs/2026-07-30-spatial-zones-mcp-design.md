# OntoTwin Nexus M2 —— 空间参考帧 + 分区管理 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图第二个子项目（M2）。路线图 M1–M6。
> 前置：`2026-07-29-ontotwin-mcp-design.md`（基础 30 工具）、`2026-07-30-scene-config-mcp-design.md`（M1，20 工具，已交付 main）。

## 修订记录

- **v1（2026-07-30）**：首版。沿用 M1 定式（直通式 / 显式并发 / 文档 A）。范围与三处取舍已在 brainstorm 与用户敲定。

---

## 1. 目标与非目标

### 目标

把 Nexus 的**空间标定底图帧**与**实例分区**开放给 MCP：

- **空间参考帧**（`backend/spatial_assets/`，`/api/v2/spatial-frames`）：上传底图 → 存草稿 → 发布，带 `draft_revision` 乐观锁。漫游/场景标定用的就是它。
- **分区管理**（`backend/zone_management/`，`/api/v2/zones`）：读分区汇总、批量给实例指派分区。

### 非目标（本轮不做）

- **后端零改动**：两个蓝图已具备并发保护 + validator，纯 MCP 转译层，不碰 `backend/`。
- **不做系统一 `/api/v2/spatial/*`（app.py）的写**：`profile` PUT（会触发全场景重算 `_rederive_components`）、`/spatial/frames` POST、`/spatial/frames/<id>/calibrate`、`/spatial/preview` 是**坐标规范系**（from/to_canonical 矩阵），与底图参考帧是两套东西，且 profile-PUT 重副作用需谨慎——挪到 **M5（CAD/坐标标定链）**。基础层已暴露其两个读（`get_spatial_profile`、`list_spatial_frames`）。
- **不做 `GET /spatial-frames/<id>/image`**：返回二进制底图（`send_file`），AI 用不上原图字节，YAGNI 砍掉。
- **不做 M3–M6**。

### 与既有工具的命名区分（重要）

基础层已有 `list_spatial_frames` → `/api/v2/spatial/frames`（系统一，坐标帧）。M2 的底图帧是**另一套**（`/api/v2/spatial-frames`，系统二）。为避免撞名/歧义，M2 底图帧工具**一律用 `reference_frame` 命名**，docstring 称「空间标定底图帧」。

---

## 2. 架构

- **同构于 M1**：`register(mcp, client, registry)` + `_ot_tools` registry；直通式；文档 A；后端零改动。
- **两种并发模型（分别透传，不强求统一）**：
  - **参考帧写**：`expected_draft_revision`（放在 payload 里，后端 `save_draft`/`publish` 读取）。**选填**——省略即后端缺省（首存/强写）；非空时作乐观并发校验。读工具（`get_reference_frame`）返回里带 `draft_revision`。
  - **分区写**：`expected_project_id`（M0 式，放在 payload 里）。**选填**——非空时作乐观并发校验；为空则不放进 body，保持后端缺省。（`zone_management` 用的是项目级 `expected_project_id`，不是帧 revision。）
- **client 无需改动**：`post_multipart` / `put_json` / `post_json` / `get` 均已存在（M1 已加 `put_json`/`delete_json`）。M2 不新增 client 方法。

---

## 3. 工具清单（7 个：3 读 + 4 写）

### 3.1 操作分级

| 级别 | 工具 | 审批 |
|---|---|---|
| read-only | `list_reference_frames`, `get_reference_frame`, `get_zones` | 可默认自动 |
| config-write（项目级持久化） | `create_reference_frame`, `save_reference_frame_draft`, `publish_reference_frame`, `assign_zones` | 高危，默认需人工审批 |

### 3.2 空间参考帧（spatial_assets，5 个）

| 工具 | 方法 + 端点 | 级别 | 参数 | 请求 |
|---|---|---|---|---|
| `create_reference_frame` | POST `/spatial-frames/assets`（multipart） | 写 | `file_path`, `floor=1`, `floor_id=""`, `ue_level=""`, `name=""` | file 字段名 `file`；form: `floor`/`floor_id`/`ue_level`/`name`（仅非空/非默认放入） |
| `list_reference_frames` | GET `/spatial-frames` | 读 | — | `{project_id, frames:[...]}` |
| `get_reference_frame` | GET `/spatial-frames/<id>` | 读 | `frame_id` | `{...frame, draft_revision, calibration_revision}` |
| `save_reference_frame_draft` | PUT `/spatial-frames/<id>/draft` | 写 | `frame_id`, `draft:dict`, `expected_draft_revision=None` | body = `draft`，`expected_draft_revision` 非 None 时合并进 body |
| `publish_reference_frame` | POST `/spatial-frames/<id>/publish` | 写 | `frame_id`, `payload:dict=None`, `expected_draft_revision=None` | body = `payload or {}`，`expected_draft_revision` 非 None 时合并 |

**上传细节**（`create_reference_frame`）：
- 复用基础层 `files.resolve_upload`，`allowed_ext=[".png",".jpg",".jpeg",".webp"]`，保留 basename 作 filename。
- form data 只放**非空/非默认**项：`floor`（默认 1 时也传，后端 `positive_int` 有默认；为简化统一传 `str(floor)`），`floor_id`/`ue_level`/`name` 仅非空时放入。
- 走 `post_multipart`，超时用 `timeout_upload`。

**并发键处理**（`save_reference_frame_draft` / `publish_reference_frame`）：
```python
body = dict(draft)                    # 或 payload or {}
if expected_draft_revision is not None:
    body["expected_draft_revision"] = expected_draft_revision
```
（省略即不放进 body，保持后端缺省行为，与基础层 expected 透传铁律一致。）

### 3.3 分区管理（zone_management，2 个）

| 工具 | 方法 + 端点 | 级别 | 参数 | 请求 |
|---|---|---|---|---|
| `get_zones` | GET `/zones` | 读 | — | `{zones:[{id, instance_count}], ...}` |
| `assign_zones` | PUT `/zones/assignments` | 写 | `instance_ids:list`, `zone_id="", expected_project_id=""` | body `{instance_ids, zone_id, expected_project_id?}` |

**`assign_zones` body 处理**：
```python
body = {"instance_ids": instance_ids, "zone_id": (zone_id or None)}
if expected_project_id:
    body["expected_project_id"] = expected_project_id
```
- `zone_id` 传空串→ `None`（后端 `_normalize_zone_id` 视 None/空为「解除分区」）。
- `expected_project_id` 非空才放入（M0 铁律）。

---

## 4. 错误映射（`errors.py`）一处小补丁

M1 的映射已覆盖 M2 绝大部分：
- 参考帧 409 `spatial_frame_revision_conflict` → 已被 `endswith("revision_conflict")` → `NEXUS_REVISION_CONFLICT` ✓
- 404 `spatial_frame_not_found` → `NEXUS_NOT_FOUND` ✓
- 422（validator，带 `fields`）→ `NEXUS_VALIDATION` ✓
- 404 `active_project_not_found`（zones/参考帧）→ `NEXUS_NO_ACTIVE_PROJECT` ✓

**唯一缺口**：zones 的 409 `active_project_changed`（激活项目漂移）现在会掉进泛化 `NEXUS_CONFLICT`。它本质等同 M0 的项目漂移，应映 `NEXUS_PROJECT_CHANGED`。在既有 409「项目漂移」判定里补一个 or 分支：

```python
if "expected" in pj or "actual" in pj or berr == "project changed" or berr == "active_project_changed":
    ...  # NEXUS_PROJECT_CHANGED
```

（放在 `revision_conflict` 判定之前，保持既有优先级。不影响 M1 已有用例。）

---

## 5. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「空间参考帧 / 分区」段：

- **参考帧 playbook**：`create_reference_frame`（传底图）→ `get_reference_frame` 拿 `draft_revision` → 改 `draft`（锚点等）→ `save_reference_frame_draft(frame_id, draft, expected_draft_revision)` → `publish_reference_frame`。遇 `NEXUS_REVISION_CONFLICT` 重读重写。
- **分区 playbook**：`get_zones` 看现状 → `assign_zones(instance_ids, zone_id)` 批量指派；`zone_id` 传空=解除分区；并发多写时带 `expected_project_id`（从 `get_active_project` 的 `project_id` 取）。
- 速查（A，不复述全字段）：参考帧结构以 `get_reference_frame` 返回为准（`anchors`/`floor_reference`/`to_ue`/`to_canonical` 等）；分区就是给实例打 `zone_id` 标签。
- 触发示例：「上传这张一楼底图作空间参考帧」「把这批实例划到 A 区」「解除这些实例的分区」。

---

## 6. Repo 布局

```
mcp/ontotwin_mcp/
  errors.py          # + 409 active_project_changed → PROJECT_CHANGED
  tools/
    spatial.py       # 新增：5 个参考帧工具
    zones.py         # 新增：2 个分区工具
    __init__.py      # register_all 追加 spatial, zones
```
沿用 `register(mcp, client, registry)` + registry 尾注册。**client.py 不改**。

---

## 7. 测试策略

- **协议**：stdio 列表新增 7 工具全可见；`call_tool` 挑 `list_reference_frames` 走一遍。
- **单元（fake client）**：每工具断言 URL/方法/请求体；重点覆盖 `create_reference_frame` 的 multipart（file 字段名 `file`、form data 非空项）、`save_reference_frame_draft`/`publish_reference_frame` 的 `expected_draft_revision` 透传/省略、`assign_zones` 的 `zone_id` 空→None + `expected_project_id` 透传/省略；errors 新增 `active_project_changed`→`PROJECT_CHANGED`。
- **只读冒烟**（88.66）：`list_reference_frames`、`get_zones` 纳入 `selfcheck.py`。
- **写路径**：只对隔离/一次性数据集验证，不碰生产库。

---

## 8. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · errors | 409 `active_project_changed` → `PROJECT_CHANGED` + 单测 | ✅ |
| B · spatial | 5 个参考帧工具 + register + 单测 | ✅ |
| C · zones | 2 个分区工具 + register + 单测 | ✅ |
| D · skill+冒烟 | SKILL.md 段 + selfcheck 2 读工具 + stdio 协议测试 | ✅ |

A 是 errors 前置（B/C 的错误映射依赖它，但 B/C 本身可先写）；B、C 互不依赖；D 收口。

---

## 9. 依赖与兼容

- **无新依赖**、**后端零改动**、**client 零改动**。纯加法，现有 50 工具与测试不回归。
- MCP 工具总数 **50 → 57**。
- 无 PG 平价问题（不动后端）。

---

## 10. 风险科普

- **两套 spatial 易混**：系统一（`/spatial/*`，坐标规范系，重算副作用）vs 系统二（`/spatial-frames`，底图参考帧，revision 锁）。M2 只做系统二 + 分区；命名用 `reference_frame` 划清界限，避免 AI 或维护者把两者当一回事。
- **两种并发键并存**：参考帧用 `expected_draft_revision`（帧级），分区用 `expected_project_id`（项目级）。这不是不一致，是后端两个子系统各自的粒度——直通式如实透传即可，skill 里点明各自从哪读。
