# M5b 系统一 spatial 写 + coord 杂项 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 新增 7 工具（3 读 + 4 写）：系统一坐标规范剖面/坐标帧/帧标定/变换预览 + 场景导出 + 全局块-资产映射读写；并给 3 个 spatial 写加可选 `expected_project_id` 护栏。

**Architecture:** 纯直通式 + `register(mcp, client, registry)`。后端给 `project_store.set_spatial_profile`/`upsert_frame` 加锁内 expected 校验（复用 M0 `ProjectMismatch`），3 端点透传（frames POST 需从 body pop expected）。**PG 未覆盖这两个方法 → 无平价**。`save_block_asset_mapping`（全局文件）/`export`/`preview`（纯计算）不加护栏。client/errors 零改动。

**Tech Stack:** Python 3.10；后端 Flask + pytest（`store`/`client` fixture）；MCP `mcp`/`httpx` + pytest（fake client）。

## Global Constraints

- **后端改动加法式**：`set_spatial_profile`/`upsert_frame` 缺省 `expected_project_id=None` 走旧路径，现有后端测试不回归。不改 `project_store_pg`（未覆盖这两个方法）。
- **MCP 侧**：直通式、`client`/`errors` 零改动。`expected_project_id: str=""`（M0 式，非空入 body）。
- **命名区分**：系统一用 `spatial_profile`/`spatial_frame`（不带 reference），别与 M2 的 `reference_frame`（系统二 `/spatial-frames`）混。
- **护栏区分**：3 个 spatial 写加 expected；`save_block_asset_mapping`（全局文件）/`export_cad_scene`/`preview_spatial_transform`（纯计算）不加。
- **URL 路径参数**：仅 `calibrate_spatial_frame` 有 `<frame_id>` → `quote(safe='/')`；其余固定路径。
- **无新依赖**。纯加法，现有 84 工具及测试不回归。
- docstring 中文：写工具首句标注（`save_block_asset_mapping` 注明"修改全局文件、非项目数据"）；读/算工具 `只读/计算：...`。Passthrough。
- 后端测试从 `backend/` 跑；MCP 测试从 `mcp/` 跑。

---

### Task 1: 后端 —— spatial 写加 expected_project_id

**Files:**
- Modify: `backend/project_store.py`（`set_spatial_profile`、`upsert_frame`）
- Modify: `backend/app.py`（`spatial_profile_put`、`spatial_frames_post`、`spatial_frame_calibrate`）
- Test: `backend/tests/test_spatial_write_expected.py`

**Interfaces:**
- Consumes: 现有 `ProjectMismatch`；`store`/`client` fixtures。
- Produces: `set_spatial_profile(self, profile, expected_project_id=None)`、`upsert_frame(self, frame, expected_project_id=None)`（锁内校验）；3 端点读/剥离 expected 并透传，捕获 `ProjectMismatch` → 409。

- [ ] **Step 1: 写失败测试** `backend/tests/test_spatial_write_expected.py`

```python
import pytest
from project_store import ProjectMismatch


def test_set_spatial_profile_expected_mismatch(store):
    with pytest.raises(ProjectMismatch) as e:
        store.set_spatial_profile({"canonical_origin": [2, 2]}, expected_project_id="p_other")
    assert e.value.expected == "p_other" and e.value.actual == "p_test"


def test_set_spatial_profile_expected_match(store):
    store.set_spatial_profile({"canonical_origin": [3, 3]}, expected_project_id="p_test")
    assert store.get_spatial_profile().get("canonical_origin") == [3, 3]


def test_upsert_frame_expected_mismatch(store):
    with pytest.raises(ProjectMismatch):
        store.upsert_frame({"id": "f1", "kind": "custom"}, expected_project_id="p_other")


def test_upsert_frame_expected_match(store):
    store.upsert_frame({"id": "f-ok", "kind": "custom"}, expected_project_id="p_test")
    assert any(f.get("id") == "f-ok" for f in store.list_frames())


# ── 端点 409（client fixture）──────────────────────────────────
def test_profile_put_endpoint_409(client, store):
    r = client.put("/api/v2/spatial/profile",
                   json={"canonical_origin": [9, 9], "expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_frames_post_endpoint_409(client, store):
    r = client.post("/api/v2/spatial/frames",
                    json={"id": "fx", "kind": "custom", "expected_project_id": "p_other"})
    assert r.status_code == 409


def test_frames_post_does_not_leak_expected_into_frame(client, store):
    # 正常 upsert（match）后，帧数据不应残留 expected_project_id 字段
    client.post("/api/v2/spatial/frames",
                json={"id": "fclean", "kind": "custom", "expected_project_id": "p_test"})
    fr = next((f for f in store.list_frames() if f.get("id") == "fclean"), None)
    assert fr is not None
    assert "expected_project_id" not in fr
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && python -m pytest tests/test_spatial_write_expected.py -v`
Expected: FAIL（方法无 expected 参数 → TypeError；端点不读/剥离 expected → 非 409 / 帧残留 expected）

- [ ] **Step 3: 改 `project_store.py` 两方法**（READ 实际代码；`with self._lock:` 内最前面加锁内校验）

`set_spatial_profile`（约 804）：
```python
def set_spatial_profile(self, profile, expected_project_id=None):
    with self._lock:
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        if self._current:
            self._current["spatial_profile"] = profile or _default_spatial_profile()
            self._save_current()
```
`upsert_frame`（在 `list_frames` 附近；READ 其实际实现后仅加签名参数 + 锁内校验，其余逻辑不变）：
```python
def upsert_frame(self, frame, expected_project_id=None):
    with self._lock:
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        # …原有 upsert 逻辑不变…
```

- [ ] **Step 4: 改 `app.py` 三端点**（READ 实际函数）

- `spatial_profile_put`（约 1001）：解析处加 `expected = data.get("expected_project_id")`；把 `project_store.set_spatial_profile(profile)` 改为 `set_spatial_profile(profile, expected_project_id=expected)`；用 `try/except ProjectMismatch as e: return jsonify({"error":"project changed","expected":e.expected,"actual":e.actual}), 409` 包住 set + `_rederive_components()`（校验命中则不重算）。
- `spatial_frames_post`（约 1028）：`frame = request.json or {}` 之后**立即** `expected = frame.pop("expected_project_id", None)`（把 expected 从帧数据剥离）；`upsert_frame(frame, expected_project_id=expected)`；`try/except ProjectMismatch → 409`。
- `spatial_frame_calibrate`（约 1039）：加 `expected = data.get("expected_project_id")`（端点单独 build frame，不 spread data，故不会污染）；`upsert_frame(frame, expected_project_id=expected)`；`try/except ProjectMismatch → 409`。

`ProjectMismatch` 已在 app.py import。缺省 expected=None 走旧路径、行为不变。

- [ ] **Step 5: 跑测试确认通过 + 全量后端不回归**

Run: `cd backend && python -m pytest tests/test_spatial_write_expected.py -v && python -m pytest tests/ -q`
Expected: PASS（新用例过；既有后端测试不回归。注：全量约 8–9 分钟，FOREGROUND 跑、勿后台）

- [ ] **Step 6: 提交**

```bash
git add backend/project_store.py backend/app.py backend/tests/test_spatial_write_expected.py
git commit -m "feat(backend): spatial 写加可选 expected_project_id（set_spatial_profile/upsert_frame + 3 端点，frames POST 剥离 expected）"
```

---

### Task 2: spatial_write 域（7 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/spatial_write.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_spatial_write.py`

**Interfaces:**
- Consumes: `client.get/post_json/put_json`。
- Produces（工具名 → 端点）：见 spec §3。

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_spatial_write.py`

```python
"""spatial_write 工具单测（fake client）。"""
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


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_set_spatial_profile_body_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_spatial_profile")({"canonical_origin": [1, 1]}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put" and path == "/api/v2/spatial/profile"
    assert body == {"canonical_origin": [1, 1], "expected_project_id": "p1"}


def test_set_spatial_profile_omits_empty_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_spatial_profile")({"canonical_origin": [1, 1]})
    assert c.calls[-1][2] == {"canonical_origin": [1, 1]}


def test_upsert_spatial_frame_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "upsert_spatial_frame")({"id": "f1", "kind": "custom"}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/spatial/frames"
    assert body == {"id": "f1", "kind": "custom", "expected_project_id": "p1"}


def test_calibrate_spatial_frame_encoded_path_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "calibrate_spatial_frame")("f#1", [{"src": [0, 0], "dst": [1, 1]}],
                                       name="世界", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/spatial/frames/f%231/calibrate"
    assert body == {"anchors": [{"src": [0, 0], "dst": [1, 1]}],
                    "name": "世界", "expected_project_id": "p1"}


def test_preview_spatial_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_spatial_transform")([[1, 2], [3, 4]], floor=2)
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/spatial/preview"
    assert body == {"points": [[1, 2], [3, 4]], "floor": 2}
    assert "profile" not in body


def test_export_cad_scene_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "export_cad_scene")([[1, 0, 0], [0, 1, 0]], [{"id": "e1"}])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/export"
    assert body == {"transform_matrix": [[1, 0, 0], [0, 1, 0]], "entities": [{"id": "e1"}],
                    "wall_height": 4500, "wall_thickness": 240}
    assert "polylines" not in body


def test_get_block_asset_mapping_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_block_asset_mapping")()
    assert c.calls[-1] == ("get", "/api/v2/coord/mapping", None)


def test_save_block_asset_mapping_dict_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_block_asset_mapping")({"BLK-1": "assets/a.glb"})
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/coord/mapping"
    assert body == {"BLK-1": "assets/a.glb"}


def test_spatial_write_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "set_spatial_profile", "upsert_spatial_frame", "calibrate_spatial_frame",
        "preview_spatial_transform", "export_cad_scene", "get_block_asset_mapping",
        "save_block_asset_mapping",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_spatial_write.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/spatial_write.py`**

```python
"""spatial_write 域：系统一坐标规范系写 + coord 杂项。

注意：系统一 /api/v2/spatial/*（坐标规范系），与 M2 的系统二
/api/v2/spatial-frames（底图参考帧，reference_frame 命名）不是一回事。
set_spatial_profile/upsert_spatial_frame/calibrate_spatial_frame 写隐式激活项目 → 带 expected_project_id；
save_block_asset_mapping 写全局文件、export/preview 纯计算 → 无 expected。
"""
from typing import Optional
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def set_spatial_profile(profile: dict, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：设置坐标规范剖面（会触发全场景重算）。

        profile 含 ue_transform/floor_table/canonical_origin 任意子集。高危写，带 expected_project_id。
        """
        body = dict(profile)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json("set_spatial_profile", "/api/v2/spatial/profile", json=body)

    @mcp.tool()
    def upsert_spatial_frame(frame: dict, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：建/改一个坐标帧（frame 需含 id）。"""
        body = dict(frame)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("upsert_spatial_frame", "/api/v2/spatial/frames", json=body)

    @mcp.tool()
    def calibrate_spatial_frame(frame_id: str, anchors: list, name: str = "",
                                unit: str = "", expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：用锚点拟合标定指定坐标帧。"""
        body = {"anchors": anchors}
        if name:
            body["name"] = name
        if unit:
            body["unit"] = unit
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "calibrate_spatial_frame",
            f"/api/v2/spatial/frames/{quote(frame_id, safe='/')}/calibrate", json=body)

    @mcp.tool()
    def preview_spatial_transform(points: list, floor: int = 1,
                                  profile: Optional[dict] = None) -> dict:
        """计算：给一批规范坐标，返回派生 UE 坐标（可传 profile 覆盖，不落库）。"""
        body = {"points": points, "floor": floor}
        if profile is not None:
            body["profile"] = profile
        return client.post_json(
            "preview_spatial_transform", "/api/v2/spatial/preview", json=body)

    @mcp.tool()
    def export_cad_scene(transform_matrix: list, entities: list,
                         polylines: Optional[list] = None,
                         wall_height: int = 4500, wall_thickness: int = 240) -> dict:
        """计算：把 CAD 实体经变换矩阵导出为 UE 场景 JSON（不落库）。"""
        body = {"transform_matrix": transform_matrix, "entities": entities,
                "wall_height": wall_height, "wall_thickness": wall_thickness}
        if polylines is not None:
            body["polylines"] = polylines
        return client.post_json("export_cad_scene", "/api/v2/coord/export", json=body)

    @mcp.tool()
    def get_block_asset_mapping() -> dict:
        """只读：全局块名→资产路径映射。"""
        return client.get("get_block_asset_mapping", "/api/v2/coord/mapping")

    @mcp.tool()
    def save_block_asset_mapping(mapping: dict) -> dict:
        """本操作会修改全局块→资产映射文件（非项目数据、无 expected）：合并保存传入的 dict。"""
        return client.post_json(
            "save_block_asset_mapping", "/api/v2/coord/mapping", json=mapping)

    for f in (set_spatial_profile, upsert_spatial_frame, calibrate_spatial_frame,
              preview_spatial_transform, export_cad_scene, get_block_asset_mapping,
              save_block_asset_mapping):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；追加 `spatial_write`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle, model_binding,
               ontology_edit, floor_pulse, cad_calibration, spatial_write)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle, model_binding,
                ontology_edit, floor_pulse, cad_calibration, spatial_write):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_spatial_write.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/spatial_write.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_spatial_write.py
git commit -m "feat(mcp): spatial_write 域 7 工具（系统一 spatial 写+coord 杂项，3 写带 expected）"
```

---

### Task 3: 协议冒烟 + selfcheck + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/selfcheck.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

**Interfaces:**
- Consumes: Task 2 注册的工具。
- Produces：协议层验证 7 新工具可 list/call；selfcheck 补 1 读工具；skill 增「坐标规范系 / 场景导出」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_spatial_write_tools_listed_and_callable():
    """M5b 系统一 spatial 写 7 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/coord/mapping": {"BLK-1": "assets/a.glb"}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("get_block_asset_mapping", {})

    new_tools = {
        "set_spatial_profile", "upsert_spatial_frame", "calibrate_spatial_frame",
        "preview_spatial_transform", "export_cad_scene", "get_block_asset_mapping",
        "save_block_asset_mapping",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 91, f"工具总数应 ≥91（84+7），实际 {len(names)}"
    assert res.isError is False
```

- [ ] **Step 2: 跑测试确认（Task 2 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k spatial_write -v`
Expected: PASS（7 工具已注册；回归守卫）

- [ ] **Step 3: selfcheck 补 1 个只读冒烟工具**（`mcp/selfcheck.py`）

工具列表尾部追加 `get_block_asset_mapping`（现共 21 个），并把 print 的「20 个」改为「21 个」：

```python
for t in [
    "get_active_project", "list_projects", "list_object_types",
    "get_import_staging_graph", "list_instances", "get_state_snapshots",
    "list_components", "list_roster", "get_spatial_profile", "get_ue_binding_status",
    "list_overlay_templates", "get_overlay_media_policy", "get_scene_catalog",
    "get_roaming_config", "list_routes", "list_reference_frames", "get_zones",
    "list_interface_defs", "list_property_defs", "list_transform_types",
    "get_block_asset_mapping",
]:
    run(t)
```
```python
print(f"=== OntoTwin MCP 基础只读链路冒烟检查 · 21 个代表性只读工具（后端 {BASE}）===")
```
（顶部 docstring 的「20 个」措辞可一并改为「21 个」，非必须。）

> 注：`get_import_staging_graph` 在后端 `_custom_graph_data` 为空时会返回 404（预期，非回归）——本轮不动它。

- [ ] **Step 4: skill 增「坐标规范系 / 场景导出」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「CAD 一键成模（交互标定链）」段之后追加（文档 A）：

````markdown
## 坐标规范系 / 场景导出（系统一 spatial）

> 这是系统一 `/spatial/*`（坐标规范系），别与 M2 的系统二底图参考帧（`reference_frame`）混。

- **规范剖面**：`get_spatial_profile()` 看当前 → `set_spatial_profile(profile, expected_project_id=…)` 改（⚠️ **会触发全场景重算**，高危；`profile` 含 `canonical_origin`/`floor_table`/`ue_transform` 子集）。
- **坐标帧**：`upsert_spatial_frame({"id":..., "kind":"custom", ...}, expected_project_id=…)` 建/改；`calibrate_spatial_frame(frame_id, anchors, expected_project_id=…)` 用锚点拟合；`preview_spatial_transform(points, floor)` 预览规范→UE（不落库）。
- **导出 / 映射**：`export_cad_scene(transform_matrix, entities, polylines)` 出 UE 场景 JSON；`get_block_asset_mapping()` / `save_block_asset_mapping({块名:资产路径})` 读写**全局**映射（非项目数据、无 expected）。

**金规**：spatial 写带 `expected_project_id`（从 `get_active_project` 取）；`set_spatial_profile` 会全场重算，改前想清楚。

**触发示例**
- 「把规范原点设成 (1,1)」
- 「用这几组锚点标定 world 帧」
- 「导出当前 CAD 场景 JSON」
````

- [ ] **Step 5: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 6: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/selfcheck.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): 系统一 spatial 写协议冒烟 + selfcheck 补读工具 + skill playbook"
```

---

## 交付后（人工，需确认）

- **部署后端到 88.66**：`project_store.py` + `app.py` 两文件 scp（paramiko）+ `docker compose restart backend`；可与 M5a 的 app.py 一并部署（M5a app.py 尚未部署）。部署前与用户确认。见 memory `deploy-88-66-method`。
- 重打发行包：`mcp/build-dist.ps1`。
- 真机只读冒烟：`python selfcheck.py`，确认 `get_block_asset_mapping` 对 88.66 `[OK]`。
- **至此 M5 收官（M5a+M5b），路线图 M1–M6 全部交付，MCP 达 91 工具。**

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 7 工具 ↔ Task 2；§4 后端 ↔ Task 1；§6 skill ↔ Task 3 Step 4；client/errors/PG 零改动（无对应任务）。
- **类型一致**：`expected_project_id: str=""`（3 spatial 写，非空入 body）；`save_block_asset_mapping` 无 expected；`profile`/`polylines: Optional[...]=None`。
- **占位符扫描**：无 TBD；每 code step 含完整代码或精确改法。
- **护栏区分**：3 spatial 写加 expected、mapping/export/preview 不加——贯穿 spec 与 plan。
- **命名无冲突**：7 个新名与现有 84 工具无交集（`spatial_profile`/`spatial_frame` ≠ M2 `reference_frame`；`get_spatial_profile` 是基础层已有、本轮复用不新增）。
- **frames POST 剥离 expected**：Task 1 Step 4 明确 `frame.pop("expected_project_id", None)`，Task 1 Step 1 有 `test_frames_post_does_not_leak_expected_into_frame` 守住。
