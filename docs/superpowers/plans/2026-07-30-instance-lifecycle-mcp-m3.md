# M3 实例生命周期 + 换模型 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 新增 9 工具（1 读 + 8 写），覆盖实例建/删/改位置/回写与换模型；并给 4 个生命周期写端点加**可选** `expected_project_id` 后端保护（加法式）。

**Architecture:** 首个碰 `backend/` 的里程碑。后端加法式改动：`project_store` 的 `spawn`/`remove`/`update_component` 加锁内 `expected_project_id` 校验（复用 M0 `ProjectMismatch`），`apply_writeback` 透传，4 端点读 body 透传并回 409；`project_store_pg` 仅 `remove` 需签名平价（spawn/update_component 继承）。换模型后端已就绪。MCP 侧直通式，client/errors 零改动。

**Tech Stack:** Python 3.10；后端 Flask + pytest（`store`/`client` fixture）；MCP `mcp`/`httpx` + pytest（fake client）。

## Global Constraints

- **后端改动加法式向后兼容**：`expected_project_id` 默认 `None` → 走旧路径，现有 backend 测试不回归。
- **锁内校验（TOCTOU 纪律）**：expected 比对必须在 `with self._lock:` 内比 `self._active_id`，复用 M0 `update_raw_state`（project_store.py:607）的写法：`if expected_project_id is not None and self._active_id != expected_project_id: raise ProjectMismatch(expected_project_id, self._active_id)`。
- **PG 平价（阻断）**：`project_store_pg` 只覆盖 `remove` → 必须同步其签名并透传；spawn/update_component 未覆盖，勿在 PG 重复实现。
- **MCP 侧**：直通式、`client`/`errors` 零改动（get/post_json/put_json/delete_json 已存在；M0+M2 错误映射已覆盖 M3 全部 409）。`expected_project_id: str = ""`（M0 式，非空才入 body）。URL `quote(x, safe='/')`。docstring 中文，写工具首句 `本操作会修改当前激活项目：...`，读工具 `只读：...`。
- **promote / clear_type_model_default 不加 expected**（类型级写）。
- 后端测试从 `backend/` 跑（`cd backend && python -m pytest`）；MCP 测试从 `mcp/` 跑。

---

### Task 1: 后端 —— 生命周期写加 `expected_project_id`（含 PG 平价）

**Files:**
- Modify: `backend/project_store.py`（`spawn`/`remove`/`update_component`）
- Modify: `backend/project_store_pg.py`（`remove` 签名平价）
- Modify: `backend/writeback.py`（`apply_writeback`）
- Modify: `backend/app.py`（`spawn_instance`/`delete_instance`/`instance_transform_put`/`writeback_state`）
- Test: `backend/tests/test_lifecycle_expected.py`

**Interfaces:**
- Consumes: 现有 `ProjectMismatch`（project_store.py，M0）、`store` / `client` fixtures（backend/tests/conftest.py）。
- Produces: `spawn(..., expected_project_id=None)`、`remove(instance_id, expected_project_id=None)`、`update_component(component_id, patch, expected_project_id=None)`、`apply_writeback(store, instance_id, transform, persist=True, expected_project_id=None)`；4 端点读 `expected_project_id` 并回 409 `{error:"project changed", expected, actual}`。

- [ ] **Step 1: 写失败测试** `backend/tests/test_lifecycle_expected.py`

```python
import pytest
from project_store import ProjectMismatch


def test_spawn_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch) as e:
        store.spawn("i-x", "PE16A", {"x": 0, "y": 0, "z": 0}, expected_project_id="p_other")
    assert e.value.expected == "p_other" and e.value.actual == "p_test"
    assert store.get_raw_state("i-x") is None  # 未写


def test_spawn_expected_match_ok(store):
    inst = store.spawn("i-ok", "PE16A", {"x": 1, "y": 2, "z": 0}, expected_project_id="p_test")
    assert inst is not None
    assert store.get_raw_state("i-ok") is not None


def test_spawn_expected_none_skips(store):
    inst = store.spawn("i-none", "PE16A")
    assert inst is not None


def test_remove_expected_mismatch_raises(store):
    store.spawn("i-del", "PE16A")
    with pytest.raises(ProjectMismatch):
        store.remove("i-del", expected_project_id="p_other")
    assert store.get_raw_state("i-del") is not None  # 未删


def test_remove_expected_match_ok(store):
    store.spawn("i-del2", "PE16A")
    store.remove("i-del2", expected_project_id="p_test")
    assert store.get_raw_state("i-del2") is None


def test_update_component_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch):
        store.update_component("c1", {"rotation": 90}, expected_project_id="p_other")


def test_update_component_expected_match_ok(store):
    assert store.update_component("c1", {"rotation": 45}, expected_project_id="p_test") is True


# ── 端点 409 契约（client fixture）──────────────────────────────
def test_delete_endpoint_expected_mismatch_409(client, store):
    store.spawn("DW-DEL", "PE16A")
    r = client.delete("/api/v2/instances/DW-DEL", json={"expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_writeback_endpoint_expected_mismatch_409(client, store):
    store.spawn("DW-WB", "PE16A")
    r = client.post("/api/v2/state/writeback", json={
        "instance_id": "DW-WB", "transform": {"tx": 0, "ty": 0, "tz": 0},
        "expected_project_id": "p_other"})
    assert r.status_code == 409
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && python -m pytest tests/test_lifecycle_expected.py -v`
Expected: FAIL（`spawn()`/`remove()`/`update_component()` 尚无 `expected_project_id` 参数 → TypeError；端点不读 expected → 非 409）

- [ ] **Step 3: 改 `project_store.py` 三方法**（各自 `with self._lock:` 内最前面加锁内校验）

`spawn`（约 project_store.py:567）签名加 `expected_project_id=None`，锁内首行加校验：
```python
def spawn(self, instance_id, object_type_rid, initial_position=None,
          render_config=None, metadata=None, expected_project_id=None):
    with self._lock:
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        if not self._current:
            return None
        # …（其余不变）
```
`remove`（约 587）：
```python
def remove(self, instance_id, expected_project_id=None):
    with self._lock:
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        inst = self._inst().pop(instance_id, None)
        if inst is not None:
            self._save_current()
        return inst
```
`update_component`（约 782）：
```python
def update_component(self, component_id, patch, expected_project_id=None):
    with self._lock:
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        comp = self._comps().get(component_id)
        if not comp:
            return False
        comp.update(patch or {})
        self._save_current()
        return True
```

- [ ] **Step 4: 改 `project_store_pg.py` 的 `remove` 平价**（约 279）

```python
def remove(self, instance_id, expected_project_id=None):
    inst = super().remove(instance_id, expected_project_id=expected_project_id)
    if inst is not None and self._current:
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE instance SET deleted_at = now() WHERE project_id = %s AND id = %s",
                    (self._current["id"], instance_id),
                )
    return inst
```
（spawn/update_component 不在 PG 覆盖，勿改 PG。）

- [ ] **Step 5: 改 `writeback.py` 的 `apply_writeback` 透传 expected**（3 处 store 写调用）

签名加 `expected_project_id=None`；自由路径（约 66）、绑定路径的 `update_component`（约 83）与 `update_raw_state`（约 90）三处都加 `expected_project_id=expected_project_id`：
```python
def apply_writeback(store, instance_id, transform, persist=True, expected_project_id=None):
    # …
    if comp is None:
        store.update_raw_state(instance_id, raw_patch, persist=persist,
                               expected_project_id=expected_project_id)
        return True, {"mode": "free", "instance_id": instance_id}
    # …绑定路径：
    store.update_component(comp["id"], {…}, expected_project_id=expected_project_id)
    store.update_raw_state(instance_id, raw_patch, persist=persist,
                           expected_project_id=expected_project_id)
```

- [ ] **Step 6: 改 `app.py` 四端点读 expected + 捕获 ProjectMismatch**

`ProjectMismatch` 已在 app.py 使用（M0 handler），直接用。

`spawn_instance`（约 2137）：读 `expected_project_id = data.get("expected_project_id")`，`instance_store.spawn(..., expected_project_id=expected_project_id)`，外层 `try/except ProjectMismatch`。
`delete_instance`（约 2172）：现在不读 body，改为：
```python
def delete_instance(instance_id):
    expected = (request.get_json(silent=True) or {}).get("expected_project_id")
    try:
        removed = instance_store.remove(instance_id, expected_project_id=expected)
    except ProjectMismatch as e:
        return jsonify({"error": "project changed", "expected": e.expected, "actual": e.actual}), 409
    if removed:
        return jsonify({"status": "removed", "id": instance_id})
    return jsonify({"error": "Instance not found"}), 404
```
`instance_transform_put`（约 1150）：读 `expected = data.get("expected_project_id")`，把 `apply_writeback(project_store, instance_id, {...}, persist=True, expected_project_id=expected)`（自由路径）与 `project_store.update_component(comp["id"], patch, expected_project_id=expected)`（绑定路径）透传，整体 `try/except ProjectMismatch → 409`。
`writeback_state`（约 2467）：读 `expected = data.get("expected_project_id")`，`apply_writeback(instance_store, instance_id, transform, persist=True, expected_project_id=expected)`，`try/except ProjectMismatch → 409`。

统一 409 体：`jsonify({"error": "project changed", "expected": e.expected, "actual": e.actual}), 409`。

- [ ] **Step 7: 跑测试确认通过 + 全量后端不回归**

Run: `cd backend && python -m pytest tests/test_lifecycle_expected.py -v && python -m pytest tests/ -q`
Expected: PASS（新用例全过；既有后端测试不回归——缺省 expected 走旧路径）

- [ ] **Step 8: 提交**

```bash
git add backend/project_store.py backend/project_store_pg.py backend/writeback.py backend/app.py backend/tests/test_lifecycle_expected.py
git commit -m "feat(backend): 生命周期写加可选 expected_project_id（spawn/remove/update_component/writeback + 4 端点，PG remove 平价）"
```

---

### Task 2: lifecycle 域（4 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/lifecycle.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_lifecycle.py`

**Interfaces:**
- Consumes: `client.post_json/put_json/delete_json`。
- Produces：
  - `create_instance(instance_id, object_type_rid, initial_position=None, display_name="", expected_project_id="")` → POST `/api/v2/instances`
  - `delete_instance(instance_id, expected_project_id="")` → DELETE `/api/v2/instances/<id>`（delete_json，body 仅在 expected 非空时带）
  - `set_instance_transform(instance_id, transform, expected_project_id="")` → PUT `/api/v2/instances/<id>/transform`
  - `writeback_instance_transform(instance_id, transform, expected_project_id="")` → POST `/api/v2/state/writeback`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_lifecycle.py`

```python
"""lifecycle 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "removed"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_create_instance_body_minimal():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_instance")("i1", "rid.a")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/instances"
    assert body == {"instance_id": "i1", "object_type_rid": "rid.a"}


def test_create_instance_body_full():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_instance")("i1", "rid.a", initial_position={"x": 1, "y": 2, "z": 0},
                               display_name="货架A", expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"instance_id": "i1", "object_type_rid": "rid.a",
                    "initial_position": {"x": 1, "y": 2, "z": 0},
                    "display_name": "货架A", "expected_project_id": "p1"}


def test_delete_instance_delete_json_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_instance")("a#1", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/instances/a%231"
    assert body == {"expected_project_id": "p1"}


def test_delete_instance_no_expected_empty_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_instance")("i1")
    assert c.calls[-1][2] == {}


def test_set_instance_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_instance_transform")("i1", {"canonical_xy": [1, 2], "rotation": 90},
                                      expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/instances/i1/transform"
    assert body == {"canonical_xy": [1, 2], "rotation": 90, "expected_project_id": "p1"}


def test_writeback_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "writeback_instance_transform")("i1", {"tx": 1, "ty": 2, "tz": 3})
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/state/writeback"
    assert body == {"instance_id": "i1", "transform": {"tx": 1, "ty": 2, "tz": 3}}


def test_lifecycle_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"create_instance", "delete_instance", "set_instance_transform",
            "writeback_instance_transform"} <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_lifecycle.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/lifecycle.py`**

```python
"""lifecycle 域：实例生命周期写（建/删/改位置/回写）。

高危写：并发多写带 expected_project_id（M0 式，选填，非空才入 body）；
遇 NEXUS_PROJECT_CHANGED 说明项目被切走，重新确认后再写。
"""
from typing import Optional
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def create_instance(instance_id: str, object_type_rid: str,
                        initial_position: Optional[dict] = None,
                        display_name: str = "", expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：投产一个新实例。

        前提：object_type_rid 必须已注入三维接口（否则后端 400）；实例 id 重复后端 409。
        """
        body = {"instance_id": instance_id, "object_type_rid": object_type_rid}
        if initial_position is not None:
            body["initial_position"] = initial_position
        if display_name:
            body["display_name"] = display_name
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("create_instance", "/api/v2/instances", json=body)

    @mcp.tool()
    def delete_instance(instance_id: str, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：销毁一个实例（不可逆）。"""
        body = {}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.delete_json(
            "delete_instance",
            f"/api/v2/instances/{quote(instance_id, safe='/')}", json=body)

    @mcp.tool()
    def set_instance_transform(instance_id: str, transform: dict,
                               expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：微调实例位置（规范坐标）。

        transform: {canonical_xy:[x,y], canonical_z, rotation, floor} 的任意子集。
        """
        body = dict(transform)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "set_instance_transform",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/transform", json=body)

    @mcp.tool()
    def writeback_instance_transform(instance_id: str, transform: dict,
                                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：把 UE 端空间变换回写真源（UE cm）。

        transform: {tx,ty,tz,rx,ry,rz,sx,sy,sz}。
        """
        body = {"instance_id": instance_id, "transform": transform}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "writeback_instance_transform", "/api/v2/state/writeback", json=body)

    for f in (create_instance, delete_instance, set_instance_transform,
              writeback_instance_transform):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；追加 `lifecycle`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_lifecycle.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/lifecycle.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_lifecycle.py
git commit -m "feat(mcp): lifecycle 域 4 工具（建/删/改位置/回写，expected_project_id 透传）"
```

---

### Task 3: model_binding 域（5 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/model_binding.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_model_binding.py`

**Interfaces:**
- Consumes: `client.get/post_json/put_json/delete_json`。
- Produces：
  - `get_model_binding(instance_id)` → GET `/api/v2/instances/<id>/model-binding`
  - `set_model_binding(instance_id, selection, expected_project_id="")` → PUT `/api/v2/instances/<id>/model-binding`
  - `clear_model_binding(instance_id, expected_project_id="")` → DELETE `/api/v2/instances/<id>/model-binding`
  - `clear_type_model_default(object_type_rid)` → DELETE `/api/v2/object-types/<rid>/model-binding`
  - `promote_model_binding(object_type_rid, source_asset_path)` → POST `/api/v2/object-types/<rid>/model-binding/promote`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_model_binding.py`

```python
"""model_binding 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_model_binding_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_model_binding")("i1")
    assert c.calls[-1] == ("get", "/api/v2/instances/i1/model-binding", None)


def test_set_model_binding_body_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_model_binding")("i1", {"asset_id": "m2"}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/instances/i1/model-binding"
    assert body == {"asset_id": "m2", "expected_project_id": "p1"}


def test_clear_model_binding_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_model_binding")("i1", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/instances/i1/model-binding"
    assert body == {"expected_project_id": "p1"}


def test_clear_type_model_default_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_type_model_default")("rid.a")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/object-types/rid.a/model-binding"


def test_promote_model_binding_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "promote_model_binding")("rid.a", "assets/high.glb")
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/object-types/rid.a/model-binding/promote"
    assert body == {"source_asset_path": "assets/high.glb"}


def test_model_binding_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_model_binding", "set_model_binding", "clear_model_binding",
            "clear_type_model_default", "promote_model_binding"} <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_model_binding.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/model_binding.py`**

```python
"""model_binding 域：实例换模型 + 类型默认模型。

save/clear 透传 expected_project_id（后端已自带锁内校验）；
promote/clear_type 是类型级写，无 expected（与其它类型级配置写口径一致）。
"""
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def get_model_binding(instance_id: str) -> dict:
        """只读：实例的模型绑定现状（当前模型、可选迁移模型、能力状态）。"""
        return client.get(
            "get_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding")

    @mcp.tool()
    def set_model_binding(instance_id: str, selection: dict,
                          expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：给实例换模型。

        selection 结构以 get_model_binding 返回为准；expected_project_id 非空时透传做并发校验。
        """
        body = dict(selection)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "set_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding", json=body)

    @mcp.tool()
    def clear_model_binding(instance_id: str, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：清除实例模型覆盖，恢复类型默认模型。"""
        body = {}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.delete_json(
            "clear_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding", json=body)

    @mcp.tool()
    def clear_type_model_default(object_type_rid: str) -> dict:
        """本操作会修改当前激活项目：清除类型的默认模型（类型级）。"""
        return client.delete_json(
            "clear_type_model_default",
            f"/api/v2/object-types/{quote(object_type_rid, safe='/')}/model-binding")

    @mcp.tool()
    def promote_model_binding(object_type_rid: str, source_asset_path: str) -> dict:
        """本操作会修改当前激活项目：把某个迁移模型提升为类型默认模型（类型级）。"""
        return client.post_json(
            "promote_model_binding",
            f"/api/v2/object-types/{quote(object_type_rid, safe='/')}/model-binding/promote",
            json={"source_asset_path": source_asset_path})

    for f in (get_model_binding, set_model_binding, clear_model_binding,
              clear_type_model_default, promote_model_binding):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；lifecycle 已在，追加 `model_binding`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle, model_binding)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle, model_binding):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/model_binding.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_model_binding.py
git commit -m "feat(mcp): model_binding 域 5 工具（换模型/类型默认/promote）"
```

---

### Task 4: 协议冒烟 + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

（selfcheck 不改：M3 新只读工具 `get_model_binding` 需实例 id，无法无参冒烟。）

**Interfaces:**
- Consumes: Task 2/3 注册的工具。
- Produces：协议层验证 9 新工具可 list/call；skill 增「实例生命周期 / 换模型」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_lifecycle_model_binding_tools_listed_and_callable():
    """M3 生命周期/换模型 9 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/instances/i1/model-binding": {"instance_id": "i1"}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("get_model_binding", {"instance_id": "i1"})

    new_tools = {
        "create_instance", "delete_instance", "set_instance_transform",
        "writeback_instance_transform", "get_model_binding", "set_model_binding",
        "clear_model_binding", "clear_type_model_default", "promote_model_binding",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 66, f"工具总数应 ≥66（57+9），实际 {len(names)}"
    assert res.isError is False
```

> `FakeClient.get(op, path, params=None)` 返回 `routes.get(path, [])`，本测试 routes 命中 `/model-binding` 路径，call_tool 不报错即可。

- [ ] **Step 2: 跑测试确认（Task 2/3 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k lifecycle_model_binding -v`
Expected: PASS（9 工具已注册；回归守卫）

- [ ] **Step 3: skill 增「实例生命周期 / 换模型」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「空间参考帧 / 分区」段之后追加（文档 A）：

````markdown
## 实例生命周期 / 换模型

这些是**高危写**（尤其 delete 不可逆）。并发多写带 `expected_project_id`（从 `get_active_project` 的 `project_id` 取）；遇 `NEXUS_PROJECT_CHANGED` 说明激活项目被切走，重新确认后再写。

**建 / 删实例**
- `create_instance(instance_id, object_type_rid, initial_position={"x":..,"y":..,"z":..})`。前提：类型已注入三维接口（否则 400），id 不得重复（否则 409）。
- `delete_instance(instance_id, expected_project_id=…)`。

**改位置**
- `set_instance_transform(instance_id, {"canonical_xy":[x,y], "canonical_z":z, "rotation":deg, "floor":n})` — 规范坐标微调。
- `writeback_instance_transform(instance_id, {"tx":..,"ty":..,"tz":..,"rx":..,"ry":..,"rz":..,"sx":..,"sy":..,"sz":..})` — UE cm 回写。

**换模型**
- `get_model_binding(instance_id)` 看现状 → `set_model_binding(instance_id, selection, expected_project_id=…)` 换模型 → `clear_model_binding(instance_id)` 恢复类型默认。
- 类型级：`clear_type_model_default(rid)`、`promote_model_binding(rid, source_asset_path)`（把迁移模型提为默认，source_asset_path 必须属于该类型历史实例模型）。

**触发示例**
- 「在当前项目建一个货架实例 shelf-A3，放在规范坐标 (1200, 800)」
- 「把 shelf-A3 挪到 (1500, 900)」
- 「给 shelf-A3 换成高精模型」/「把 shelf-A3 恢复成类型默认模型」
````

- [ ] **Step 4: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 5: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): 生命周期/换模型协议冒烟 + skill playbook"
```

---

## 交付后（人工，需确认）

- **部署后端到 88.66**（首次碰 backend）：`project_store.py`/`project_store_pg.py`/`writeback.py`/`app.py` 四文件 scp + `docker compose restart backend`，像 M0 那样；部署前与用户确认。
- 重打发行包：`mcp/build-dist.ps1`。
- 真机写验证：建实例→改位置→换模型→删实例→带错 expected 验 409，只对一次性抛弃数据集，不碰生产库。

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 9 工具 ↔ Task 2（lifecycle 4）+ Task 3（model_binding 5）；§4 后端扩展 ↔ Task 1（含 PG remove 平价 §4.0、锁内校验 §4.1、apply_writeback §4.2、端点 §4.3、后端测试 §4.4）；§6 skill ↔ Task 4；errors/client 零改动（无对应任务，符合 spec §5/§2）。
- **类型一致**：`expected_project_id: str=""`（M0 式，非空入 body）贯穿；DELETE 工具用 delete_json；`initial_position: Optional[dict]=None`。
- **占位符扫描**：无 TBD；每 code step 含完整代码或精确到行号的改法。
- **PG 平价**：仅 `remove`（Task 1 Step 4）；spawn/update_component 明确「勿改 PG」。
- **锁内 TOCTOU**：三方法校验均在 `with self._lock:` 内，复用 M0 写法。
