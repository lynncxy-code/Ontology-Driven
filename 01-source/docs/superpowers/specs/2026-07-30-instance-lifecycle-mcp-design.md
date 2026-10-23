# OntoTwin Nexus M3 —— 实例生命周期 + 换模型 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图第三个子项目（M3）。路线图 M1–M6。
> 前置：基础 30 工具、M1（场景配置 20）、M2（空间/分区 7）均已交付 main（共 57 工具）。

## 修订记录

- **v1（2026-07-30）**：首版。用户选「加后端保护」（生命周期写加 `expected_project_id`）+ promote/clear_type 走 B（类型级不加）。沿用直通式 / 文档 A。

---

## 1. 目标与非目标

### 目标

把实例生命周期与换模型开放给 MCP：

- **实例生命周期**：建实例、删实例、改位置（transform）、空间回写（writeback）。
- **换模型（model-binding）**：读/存/清实例模型绑定、清类型默认、提升迁移模型为默认（promote）。

### 非目标

- **不做 M4–M6**（本体深编辑、CAD 交互标定、floor_pulse）。
- **系统一 `/spatial/*` 写**仍归 M5。
- promote / clear_type_model_default **不加** `expected_project_id`（类型级写，风险低，与 M1/M2 的类型级配置写口径一致）。

### 与 M0–M2 的关系

- **首个碰后端的 MCP 里程碑**（M1/M2 均零后端改动）。后端改动为**加法式、向后兼容**：给 4 个生命周期写加**可选** `expected_project_id`（锁内校验），空缺即保持旧行为。
- 换模型后端**已就绪**（save/clear 自带 `expected_project_id` + `ActiveProjectChangedError`）。
- **错误映射零改动**：`ProjectMismatch`→409 带 expected/actual→`NEXUS_PROJECT_CHANGED`（M0）；`active_project_changed`→`NEXUS_PROJECT_CHANGED`（M2 补丁已覆盖）。

---

## 2. 架构

- 直通式；`register(mcp, client, registry)`；文档 A。
- **并发**：生命周期写用 `expected_project_id`（M0 式，选填，非空才入 body）；换模型 save/clear 同样透传 `expected_project_id`。
- **client 零改动**（get/post_json/put_json/delete_json 均已存在）。
- **errors 零改动**（M0+M2 已覆盖全部 M3 的 409 语义）。

---

## 3. 工具清单（9 个：1 读 + 8 写）→ MCP 57→66

### 3.1 实例生命周期（`tools/lifecycle.py`，4 写）

| 工具 | 方法 + 端点 | 参数 | 请求体 |
|---|---|---|---|
| `create_instance` | POST `/api/v2/instances` | `instance_id`, `object_type_rid`, `initial_position:dict=None`, `display_name=""`, `expected_project_id=""` | `{instance_id, object_type_rid, initial_position}`（+ 非空 `display_name`/`expected_project_id`） |
| `delete_instance` | DELETE `/api/v2/instances/<id>` | `instance_id`, `expected_project_id=""` | 非空 `expected_project_id` 时 body `{expected_project_id}`，否则空 body（delete_json） |
| `set_instance_transform` | PUT `/api/v2/instances/<id>/transform` | `instance_id`, `transform:dict`, `expected_project_id=""` | body = `transform`（`canonical_xy`/`canonical_z`/`rotation`/`floor`）+ 非空 `expected_project_id` |
| `writeback_instance_transform` | POST `/api/v2/state/writeback` | `instance_id`, `transform:dict`, `expected_project_id=""` | `{instance_id, transform}` + 非空 `expected_project_id` |

- `initial_position` 缺省 `{"x":0,"y":0,"z":0}` 由后端处理；工具仅在非 None 时放入。
- `transform`（set_instance_transform）是规范坐标微调：`canonical_xy:[x,y]` / `canonical_z:float` / `rotation:float` / `floor:int`，直通透传。
- `transform`（writeback）是 UE cm 变换：`{tx,ty,tz,rx,ry,rz,sx,sy,sz}`，直通透传。

### 3.2 换模型（`tools/model_binding.py`，1 读 + 4 写）

| 工具 | 方法 + 端点 | 参数 | 请求体 |
|---|---|---|---|
| `get_model_binding` | GET `/api/v2/instances/<id>/model-binding` | `instance_id` | — |
| `set_model_binding` | PUT `/api/v2/instances/<id>/model-binding` | `instance_id`, `selection:dict`, `expected_project_id=""` | body = `selection` + 非空 `expected_project_id` |
| `clear_model_binding` | DELETE `/api/v2/instances/<id>/model-binding` | `instance_id`, `expected_project_id=""` | 非空 `expected_project_id` 时 body `{expected_project_id}` |
| `clear_type_model_default` | DELETE `/api/v2/object-types/<rid>/model-binding` | `object_type_rid` | — |
| `promote_model_binding` | POST `/api/v2/object-types/<rid>/model-binding/promote` | `object_type_rid`, `source_asset_path` | `{source_asset_path}` |

- `selection`（set_model_binding）结构以 `get_model_binding` 返回 + 后端 `_validate_selection` 为准（换哪个模型），直通透传。
- URL 路径参数一律 `quote(x, safe='/')`。

---

## 4. 后端能力扩展（加法式，向后兼容）

### 4.0 双实现签名平价（阻断，勿漏）

`project_store_pg` 策略是「**只覆盖 IO 原语**，内存逻辑继承复用」。据此：
- `spawn`、`update_component` PG **未覆盖** → 改 base 即可，PG 自动继承，**无需平价**。
- `remove` PG **有覆盖**（`project_store_pg.py:279`，`super().remove()` + PG 软删）→ **必须同步改 PG 的 `remove` 签名并透传**，照 `mint_instances`（`project_store_pg.py:297`）的样板：
  ```python
  def remove(self, instance_id, expected_project_id=None):
      inst = super().remove(instance_id, expected_project_id=expected_project_id)
      ...  # PG 软删逻辑不变
  ```

### 4.1 project_store 三个方法加可选 `expected_project_id`（锁内校验）

复用 M0 已有的 `ProjectMismatch` 与「锁内比对」模式（`update_raw_state`，`project_store.py:607`）：

```python
# spawn / remove / update_component 各自 with self._lock: 内，最前面加：
if expected_project_id is not None and self._active_id != expected_project_id:
    raise ProjectMismatch(expected_project_id, self._active_id)
```

- `spawn(self, instance_id, object_type_rid, initial_position=None, render_config=None, metadata=None, expected_project_id=None)`
- `remove(self, instance_id, expected_project_id=None)`
- `update_component(self, component_id, patch, expected_project_id=None)`

### 4.2 apply_writeback 透传 expected

`writeback.apply_writeback(store, instance_id, transform, persist=True, expected_project_id=None)`：
- 自由实例：`store.update_raw_state(instance_id, raw_patch, persist=persist, expected_project_id=expected_project_id)`（update_raw_state 已有 expected，锁内校验）。
- 绑定实例：写构件真源处透传到 `store.update_component(..., expected_project_id=expected_project_id)`。

### 4.3 四个端点读 body 的 expected 并透传 + 捕获 ProjectMismatch

`spawn_instance` / `delete_instance` / `instance_transform_put` / `writeback_state`：
- 读 `expected_project_id = (request.json or {}).get("expected_project_id")`（`delete_instance` 现在不读 body，需开始读；DELETE 带 body Flask 支持）。
- 透传到对应 store 调用。
- `try: ... except ProjectMismatch as e: return jsonify({"error":"project changed","expected":e.expected,"actual":e.actual}), 409`（与 M0 端点一致）。

### 4.4 后端测试

- `spawn`/`remove`/`update_component` 的 expected 命中/不命中（`ProjectMismatch`）单测；PG `remove` 签名平价（可 mock）；apply_writeback 透传 expected 的单测；4 端点 409 契约测试。加进 `backend/tests/`。**不改既有行为**：缺省 `expected_project_id`（None）时全部走旧路径。

---

## 5. 错误映射

**零改动**。M3 的所有 409 已被覆盖：
- 生命周期写并发漂移：`ProjectMismatch` → 端点回 409 `{error:"project changed", expected, actual}` → `NEXUS_PROJECT_CHANGED`（M0 映射）。
- 换模型并发漂移：`ActiveProjectChangedError`（code `active_project_changed`, 409）→ `NEXUS_PROJECT_CHANGED`（M2 补丁）。
- spawn 重名 409（"实例 ID 已存在"）/ 能力未启用 409（`representable_capability_required`）→ `NEXUS_CONFLICT`（透传 error 文本，可接受）。
- 换模型 422（validator，带 fields）→ `NEXUS_VALIDATION`（M1）。

---

## 6. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「实例生命周期 / 换模型」段：

- **建实例**：`create_instance(instance_id, object_type_rid, initial_position=…)`。前提：类型已注入三维接口（否则 400），实例 id 不得重复（否则 409）。并发多写带 `expected_project_id`（从 `get_active_project` 取）。
- **改位置**：`set_instance_transform(instance_id, {canonical_xy, canonical_z, rotation, floor})`（规范坐标微调）；`writeback_instance_transform(instance_id, {tx..sz})`（UE cm 回写）。
- **换模型**：`get_model_binding` → `set_model_binding(instance_id, selection, expected_project_id)`；`clear_model_binding` 恢复类型默认。
- 金规：这些是**高危写**，写前带 `expected_project_id`；遇 `NEXUS_PROJECT_CHANGED` 说明项目被切走，重新确认激活项目后再写。
- 触发示例：「在当前项目建一个货架实例 shelf-A3」「把 shelf-A3 挪到规范坐标 (1200, 800)」「给 shelf-A3 换成高精模型」。

---

## 7. Repo 布局

```
backend/                              # 加法式改动（首次碰后端）
  project_store.py                    # spawn/remove/update_component + expected（锁内）
  project_store_pg.py                 # remove 签名平价（透传）
  writeback.py                        # apply_writeback + expected 透传
  app.py                              # 4 端点读 expected + 捕获 ProjectMismatch
  tests/                              # 后端单测/契约测试
mcp/ontotwin_mcp/tools/
  lifecycle.py                        # 4 生命周期工具
  model_binding.py                    # 5 换模型工具
  __init__.py                         # register_all 追加 lifecycle, model_binding
```

client.py、errors.py **零改动**。

---

## 8. 测试策略

- **后端**：见 §4.4（expected 命中/漏、PG 平价、端点 409）。
- **MCP 协议**：stdio 列表新增 9 工具；`call_tool` 挑 `get_model_binding` 走一遍。
- **MCP 单元（fake client）**：每工具断言 URL/方法/请求体；重点 `expected_project_id` 透传/省略、DELETE 带 body（delete_json）、transform/selection 直通。
- **只读冒烟**（88.66）：`get_model_binding` 需要实例 id，暂不入 selfcheck（无实例）；本轮 selfcheck 不加（M3 无「可无参只读」新工具）。
- **写路径**：只对一次性抛弃数据集验证（建实例→改位置→换模型→删实例→带错 expected 验 409），不碰生产库。

---

## 9. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · 后端 | spawn/remove/update_component/apply_writeback + 4 端点 + PG remove 平价 + 后端测试 | ✅ |
| B · lifecycle | 4 个生命周期工具 + register + 单测 | ✅ |
| C · model_binding | 5 个换模型工具 + register + 单测 | ✅ |
| D · skill+协议 | SKILL.md 段 + stdio 协议测试 | ✅ |

A 是前置（B/C 的写工具依赖后端 expected 生效才有意义，但 B/C 的 MCP 单测用 fake client、不依赖真后端，可与 A 并行；真机写验证需 A 部署）。B、C 互不依赖；D 收口。

---

## 10. 依赖与兼容

- **无新依赖**。**client/errors 零改动**。
- 后端改动**加法式向后兼容**：缺省 `expected_project_id` 时行为不变；现有 backend 测试与 50→57 MCP 工具不回归。
- **PG 平价**是唯一「阻断」项（`remove`）——漏了会导致 PG 后端 `remove` 调用签名不匹配。

---

## 11. 风险科普

- **首次碰后端的 TOCTOU 纪律**：expected 校验必须在**存储层锁内**（`with self._lock:` 内比对 `self._active_id`），不能在端点层「先查激活项目再写」——那之间项目可能被切，等于没护栏。这正是 M0 把 `expected_project_id` 下沉到 project_store 方法内的原因，M3 沿用。
- **PG 平价易漏**：`project_store_pg` 只覆盖了 `remove`（不是 spawn/update_component），所以平价面很小——但正因为只有一个，容易在改 base 时忘了它。Task A 的后端测试要显式覆盖 PG `remove` 的新签名。
- **删实例是不可逆写**：`delete_instance` + `expected_project_id` 是最该带护栏的操作；skill 明确要求写前带 expected。
