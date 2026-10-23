# M2 空间参考帧 + 分区管理 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 层新增 7 个工具（3 读 + 4 写），覆盖空间标定底图参考帧（spatial_assets）与实例分区（zone_management）。

**Architecture:** 纯 `mcp/` 转译层，沿用 M1 定式（`register(mcp, client, registry)` + `_ot_tools` + 直通式）。后端 `spatial_assets/`、`zone_management/` 蓝图已具备并发保护 + validator，**不碰 `backend/`**，**不改 `client.py`**（put/delete/multipart 均已存在）。仅补一处 errors 映射，再挂 spatial、zones 两个工具域，最后收口 skill 与冒烟。

**Tech Stack:** Python 3.10、`mcp`（FastMCP）、`httpx`；pytest（fake client + `create_connected_server_and_client_session`）。

## Global Constraints

- **后端零改动 + client 零改动**：只动 `mcp/`（errors.py、tools/、tests/、selfcheck.py、SKILL.md）。不改 `backend/`、不改 `client.py`。
- **无新依赖**。
- **纯加法**：现有 50 工具及测试不得回归。
- **命名划界**：底图参考帧工具一律 `reference_frame` 命名，避免与基础层 `list_spatial_frames`（`/api/v2/spatial/frames`，另一套坐标系）撞名。本域端点是 `/api/v2/spatial-frames`。
- **两种并发键，如实透传，均选填**：
  - 参考帧写：`expected_draft_revision`（放 payload；非 None 才放进 body，省略保持后端缺省）。
  - 分区写：`expected_project_id`（M0 式；非空才放进 body）。
- **直通式**：不重塑后端响应。docstring 中文；写工具首句 `本操作会修改当前激活项目：...`，读工具 `只读：...`。
- **URL 路径参数**：`quote(frame_id, safe='/')`，与现有工具一致。
- **单测不起真 HTTP**。

---

### Task 1: errors 补 409 `active_project_changed` → `NEXUS_PROJECT_CHANGED`

**Files:**
- Modify: `mcp/ontotwin_mcp/errors.py`（`map_response_error` 的 409 分支）
- Test: `mcp/tests/test_errors.py`

**Interfaces:**
- Consumes: 现有 `map_response_error`、`NexusError`。
- Produces: 409 且 `error == "active_project_changed"`（zones 激活项目漂移）→ `NEXUS_PROJECT_CHANGED`。加法式，不动既有优先级（仍在 `revision_conflict` 判定之前）。

- [ ] **Step 1: 写失败测试**（追加到 `test_errors.py` 末尾）

```python
def test_409_active_project_changed_maps_project_changed():
    e = map_response_error(
        "assign_zones", 409,
        '{"error":"active_project_changed"}', {"error": "active_project_changed"})
    assert e.code == "NEXUS_PROJECT_CHANGED"
    assert e.http_status == 409
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_errors.py -k active_project_changed -v`
Expected: FAIL（现在落到 `NEXUS_CONFLICT`）

- [ ] **Step 3: 改 409 分支的项目漂移判定**（把 `active_project_changed` 并入既有 or 条件）

把这一行：
```python
    if "expected" in pj or "actual" in pj or berr == "project changed":
```
改为：
```python
    if ("expected" in pj or "actual" in pj
            or berr == "project changed" or berr == "active_project_changed"):
```
（其余不变；`revision_conflict`、`NEXUS_CONFLICT` 分支保持原样、原顺序。）

- [ ] **Step 4: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_errors.py -v`
Expected: PASS（含既有 4 个 409 用例，尤其 `test_409_name_duplicated_is_conflict_not_project_changed` 仍为 `NEXUS_CONFLICT`、`test_409_non_dict_parsed_json_no_crash` 仍为 `NEXUS_CONFLICT`）

- [ ] **Step 5: 提交**

```bash
git add mcp/ontotwin_mcp/errors.py mcp/tests/test_errors.py
git commit -m "feat(mcp): errors 补 409 active_project_changed→PROJECT_CHANGED（zones 分区漂移）"
```

---

### Task 2: spatial 域（空间参考帧 5 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/spatial.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_spatial.py`

**Interfaces:**
- Consumes: `client.get/post_json/put_json/post_multipart`；`files.resolve_upload(file_path, settings, allowed_ext=[...]) -> (basename, content)`；`config.load()`。
- Produces（工具名 → 端点）：
  - `create_reference_frame(file_path, floor=1, floor_id="", ue_level="", name="")` → POST `/api/v2/spatial-frames/assets`（multipart，file 字段名 `file`，form 只放非空项 + `floor` 恒传 `str(floor)`）
  - `list_reference_frames()` → GET `/api/v2/spatial-frames`
  - `get_reference_frame(frame_id)` → GET `/api/v2/spatial-frames/<id>`
  - `save_reference_frame_draft(frame_id, draft, expected_draft_revision=None)` → PUT `/api/v2/spatial-frames/<id>/draft`，body=`draft`（+ 非 None 的 `expected_draft_revision`）
  - `publish_reference_frame(frame_id, payload=None, expected_draft_revision=None)` → POST `/api/v2/spatial-frames/<id>/publish`，body=`payload or {}`（+ 非 None 的 `expected_draft_revision`）

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_spatial.py`

```python
"""spatial（空间参考帧）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"ok": True}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"ok": True}

    def post_multipart(self, op, path, files, data=None, timeout=None):
        self.calls.append(("multipart", path, list(files), data)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_create_reference_frame_multipart(monkeypatch):
    monkeypatch.setattr(
        "ontotwin_mcp.tools.spatial.resolve_upload",
        lambda p, s, allowed_ext=None: ("plan.png", b"img"))
    c = C(); mcp = build_server(c)
    _t(mcp, "create_reference_frame")("whatever.png", floor=2, floor_id="F2", name="一楼底图")
    method, path, files, data = c.calls[-1]
    assert method == "multipart"
    assert path == "/api/v2/spatial-frames/assets"
    assert files[0] == ("file", "plan.png", b"img")
    assert data == {"floor": "2", "floor_id": "F2", "name": "一楼底图"}
    assert "ue_level" not in data  # 空项不放入


def test_list_reference_frames_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_reference_frames")()
    assert c.calls[-1] == ("get", "/api/v2/spatial-frames", None)


def test_get_reference_frame_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_reference_frame")("frame#1")
    assert c.calls[-1] == ("get", "/api/v2/spatial-frames/frame%231", None)


def test_save_reference_frame_draft_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": [1]}, expected_draft_revision=3)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/spatial-frames/f1/draft"
    assert body == {"anchors": [1], "expected_draft_revision": 3}


def test_save_reference_frame_draft_omits_none_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": []})
    method, path, body = c.calls[-1]
    assert body == {"anchors": []}
    assert "expected_draft_revision" not in body


def test_publish_reference_frame_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1", expected_draft_revision=5)
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/spatial-frames/f1/publish"
    assert body == {"expected_draft_revision": 5}


def test_publish_reference_frame_empty_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1")
    assert c.calls[-1][2] == {}


def test_spatial_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "create_reference_frame", "list_reference_frames", "get_reference_frame",
        "save_reference_frame_draft", "publish_reference_frame",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_spatial.py -v`
Expected: FAIL（工具未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/spatial.py`**

```python
"""spatial 域：空间标定底图参考帧读写（spatial_assets，/api/v2/spatial-frames）。

注意：与基础层 list_spatial_frames（/api/v2/spatial/frames，坐标规范系）不是一回事。
本域是底图参考帧（带 draft_revision 乐观锁），故一律用 reference_frame 命名划清界限。

并发：写用 expected_draft_revision（选填，放 payload；非 None 才透传，省略保持后端缺省）。
"""
from typing import Optional
from urllib.parse import quote

from .. import config
from ..files import resolve_upload

_FRAMES = "/api/v2/spatial-frames"


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def create_reference_frame(file_path: str, floor: int = 1, floor_id: str = "",
                               ue_level: str = "", name: str = "") -> dict:
        """本操作会修改当前激活项目：上传一张底图作空间标定参考帧（multipart）。

        file_path 指向本地图片（png/jpg/jpeg/webp）；floor/floor_id/ue_level/name 为可选元数据。
        """
        base, content = resolve_upload(
            file_path, settings, allowed_ext=[".png", ".jpg", ".jpeg", ".webp"])
        data = {"floor": str(floor)}
        if floor_id:
            data["floor_id"] = floor_id
        if ue_level:
            data["ue_level"] = ue_level
        if name:
            data["name"] = name
        return client.post_multipart(
            "create_reference_frame", f"{_FRAMES}/assets",
            [("file", base, content)], data=data)

    @mcp.tool()
    def list_reference_frames() -> dict:
        """只读：列出当前项目的空间标定底图参考帧。"""
        return client.get("list_reference_frames", _FRAMES)

    @mcp.tool()
    def get_reference_frame(frame_id: str) -> dict:
        """只读：单张底图参考帧（含 draft_revision / calibration_revision）。"""
        return client.get("get_reference_frame", f"{_FRAMES}/{quote(frame_id, safe='/')}")

    @mcp.tool()
    def save_reference_frame_draft(frame_id: str, draft: dict,
                                   expected_draft_revision: Optional[int] = None) -> dict:
        """本操作会修改当前激活项目：保存底图参考帧草稿（锚点/楼层参照等）。

        draft 结构以 get_reference_frame 返回为准。expected_draft_revision 非 None 时作
        乐观并发校验（取自 get_reference_frame 的 draft_revision）；省略保持后端缺省。
        """
        body = dict(draft)
        if expected_draft_revision is not None:
            body["expected_draft_revision"] = expected_draft_revision
        return client.put_json(
            "save_reference_frame_draft",
            f"{_FRAMES}/{quote(frame_id, safe='/')}/draft", json=body)

    @mcp.tool()
    def publish_reference_frame(frame_id: str, payload: Optional[dict] = None,
                                expected_draft_revision: Optional[int] = None) -> dict:
        """本操作会修改当前激活项目：发布底图参考帧（把草稿标定固化为生效标定）。

        expected_draft_revision 非 None 时作乐观并发校验；省略保持后端缺省。
        """
        body = dict(payload) if payload else {}
        if expected_draft_revision is not None:
            body["expected_draft_revision"] = expected_draft_revision
        return client.post_json(
            "publish_reference_frame",
            f"{_FRAMES}/{quote(frame_id, safe='/')}/publish", json=body)

    for f in (create_reference_frame, list_reference_frames, get_reference_frame,
              save_reference_frame_draft, publish_reference_frame):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`mcp/ontotwin_mcp/tools/__init__.py`）

```python
from . import project, ontology, runtime, cad, binding, phase2, overlay, scene, spatial


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2, overlay, scene, spatial):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_spatial.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/spatial.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_spatial.py
git commit -m "feat(mcp): spatial 域 5 工具（空间标定底图参考帧读写，reference_frame 命名划界）"
```

---

### Task 3: zones 域（分区 2 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/zones.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_zones.py`

**Interfaces:**
- Consumes: `client.get/put_json`。
- Produces：
  - `get_zones()` → GET `/api/v2/zones`
  - `assign_zones(instance_ids, zone_id="", expected_project_id="")` → PUT `/api/v2/zones/assignments`，body `{instance_ids, zone_id:(zone_id or None)}` + 非空 `expected_project_id`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_zones.py`

```python
"""zones（分区）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"zones": []}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"ok": True}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_zones_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_zones")()
    assert c.calls[-1] == ("get", "/api/v2/zones", None)


def test_assign_zones_body_zone_and_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "assign_zones")(["i1", "i2"], zone_id="A区", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/zones/assignments"
    assert body == {"instance_ids": ["i1", "i2"], "zone_id": "A区", "expected_project_id": "p1"}


def test_assign_zones_empty_zone_becomes_none():
    c = C(); mcp = build_server(c)
    _t(mcp, "assign_zones")(["i1"])
    method, path, body = c.calls[-1]
    assert body == {"instance_ids": ["i1"], "zone_id": None}
    assert "expected_project_id" not in body


def test_zones_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_zones", "assign_zones"} <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_zones.py -v`
Expected: FAIL（工具未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/zones.py`**

```python
"""zones 域：实例分区读写（zone_management）。

并发：assign 用 expected_project_id（M0 式，选填，非空才透传）。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def get_zones() -> dict:
        """只读：当前项目的分区汇总（各 zone 及实例数）。"""
        return client.get("get_zones", "/api/v2/zones")

    @mcp.tool()
    def assign_zones(instance_ids: list, zone_id: str = "",
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：批量给实例指派分区。

        zone_id 传空串表示解除分区。expected_project_id 非空时作乐观并发校验；
        为空则不放进 body，保持后端缺省行为。
        """
        body = {"instance_ids": instance_ids, "zone_id": (zone_id or None)}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json("assign_zones", "/api/v2/zones/assignments", json=body)

    for f in (get_zones, assign_zones):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`mcp/ontotwin_mcp/tools/__init__.py`；spatial 已在，追加 zones）

```python
from . import project, ontology, runtime, cad, binding, phase2, overlay, scene, spatial, zones


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2, overlay, scene, spatial, zones):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全部既有 + 新增）

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/zones.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_zones.py
git commit -m "feat(mcp): zones 域 2 工具（实例分区读写，expected_project_id 透传）"
```

---

### Task 4: 协议冒烟 + selfcheck + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/selfcheck.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

**Interfaces:**
- Consumes: Task 2/3 注册的工具。
- Produces：协议层验证 7 新工具可 list/call；selfcheck 读工具补 2 个；skill 增「空间参考帧 / 分区」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_spatial_zones_tools_listed_and_callable():
    """M2 空间/分区 7 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/spatial-frames": {"project_id": "p1", "frames": []}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("list_reference_frames", {})

    new_tools = {
        "create_reference_frame", "list_reference_frames", "get_reference_frame",
        "save_reference_frame_draft", "publish_reference_frame",
        "get_zones", "assign_zones",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 57, f"工具总数应 ≥57（50+7），实际 {len(names)}"
    assert res.isError is False
```

- [ ] **Step 2: 跑测试确认（若 Task 2/3 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k spatial_zones -v`
Expected: PASS（7 工具已由 Task 2/3 注册；本测试是回归守卫）

- [ ] **Step 3: selfcheck 补 2 个只读冒烟工具**（`mcp/selfcheck.py`）

把工具列表尾部追加 `list_reference_frames`, `get_zones`（现共 17 个），并把首行 print 的「15 个」改为「17 个」：

```python
for t in [
    "get_active_project", "list_projects", "list_object_types",
    "get_import_staging_graph", "list_instances", "get_state_snapshots",
    "list_components", "list_roster", "get_spatial_profile", "get_ue_binding_status",
    "list_overlay_templates", "get_overlay_media_policy", "get_scene_catalog",
    "get_roaming_config", "list_routes", "list_reference_frames", "get_zones",
]:
    run(t)
```
```python
print(f"=== OntoTwin MCP 基础只读链路冒烟检查 · 17 个代表性只读工具（后端 {BASE}）===")
```
（顶部 docstring 的「15 个」措辞可一并改为「17 个」，非必须。）

- [ ] **Step 4: skill 增「空间参考帧 / 分区」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「场景配置」段之后追加下面整段（文档 A：导航速查 + 依赖活配置）：

````markdown
## 空间参考帧 / 分区

**空间标定底图参考帧**（`reference_frame`，别与坐标系的 `list_spatial_frames` 混淆）
- playbook：`create_reference_frame(底图路径, floor=…)` → `get_reference_frame(frame_id)` 拿 `draft_revision` → 改 `draft`（锚点/楼层参照）→ `save_reference_frame_draft(frame_id, draft, expected_draft_revision)` → `publish_reference_frame(frame_id, expected_draft_revision=…)`。
- 金规：写前先 `get_reference_frame` 拿 `draft_revision`；遇 `NEXUS_REVISION_CONFLICT` 重读重写；`draft` 结构以读到的活帧为准。

**实例分区**（zones）
- `get_zones()` 看各分区实例数 → `assign_zones(instance_ids, zone_id)` 批量指派；`zone_id` 传空串=解除分区。
- 并发多写时带 `expected_project_id`（从 `get_active_project` 的 `project_id` 取）。

**触发示例**
- 「上传这张一楼底图作空间参考帧，楼层填 1」
- 「把这批实例划到 A 区」 / 「解除这些实例的分区」
````

- [ ] **Step 5: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 6: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/selfcheck.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): 空间/分区协议冒烟 + selfcheck 补读工具 + skill 空间参考帧/分区 playbook"
```

---

## 交付后（人工，可选）

- 重打发行包：`mcp/build-dist.ps1`。
- 真机只读冒烟：`python selfcheck.py`，确认 `list_reference_frames`/`get_zones` 对 88.66 `[OK]`。
- 写路径只对一次性抛弃数据集验证，不碰生产库。

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 7 工具 ↔ Task 2（spatial 5）+ Task 3（zones 2）；§4 errors 补丁 ↔ Task 1；§5 skill 文档 A ↔ Task 4 Step 4；§7 测试三层 ↔ Task 2–4。client 零改动、后端零改动均体现（无对应任务）。
- **类型一致**：`expected_draft_revision: Optional[int]=None`（参考帧写）、`expected_project_id: str=""`（分区写）贯穿 spec 与 plan 一致；`zone_id` 空→None 一致。
- **占位符扫描**：无 TBD；每 code step 均含完整代码。
- **命名划界**：全用 `reference_frame`，不与基础层 `list_spatial_frames` 冲突（新工具名集合与现有 50 工具无交集）。
- **既有惯例**：URL `quote(safe='/')`；registry 尾注册；multipart 用 `resolve_upload` + `post_multipart`（对齐 `upload_roster`/`parse_cad_dxf`）；expected 透传铁律（非空/非 None 才放 body）。
