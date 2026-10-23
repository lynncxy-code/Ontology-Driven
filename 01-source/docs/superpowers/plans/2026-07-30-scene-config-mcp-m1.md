# M1 场景配置 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 MCP 层新增 20 个工具（8 读 + 12 写），让 AI 可读写 Nexus 的信息面板 / 人物漫游 / 漫游路线三块配置。

**Architecture:** 纯 MCP 转译层，沿用 `register(mcp, client, registry)` + `_ot_tools` registry + FastMCP stdio。后端 `overlay/`、`scene_interaction/` 蓝图已具备 revision 乐观锁 + validator，**本计划不碰 `backend/`**。先补 client 的 PUT/DELETE 与 errors 的 422/409-revision/404-active 两处基座，再挂 overlay、scene 两个工具域，最后收口 skill 文档与冒烟。

**Tech Stack:** Python 3.10、`mcp`（FastMCP）、`httpx`；pytest（in-memory `MockTransport` + `create_connected_server_and_client_session`）。

## Global Constraints

- **后端零改动**：不修改 `backend/` 任何文件；仅动 `mcp/`。
- **无新依赖**：只用现有 `httpx`（`put` / `request`）；不改 `mcp/pyproject.toml` 依赖，不改 `backend/requirements.txt`。
- **纯加法**：现有 30 工具及其测试不得回归；新工具全部追加。
- **写工具 `expected_revision` 必填**（无默认值），强制先读后写；本域**不透传** `expected_project_id`（revision 已绑定当前激活项目的配置，兼作跨项目护栏）。
- **直通式**：工具不重塑后端响应，原样透传返回。
- **URL 路径参数编码**：一律 `quote(x, safe='/')`，与现有工具（`get_object_type` / `get_instance_state`）一致——转义 `#` 等特殊字符、保留 `/`。
- **注册惯例**：每域 `def register(mcp, client, registry):`，内定义 `@mcp.tool()`，结尾 `for f in (...): registry[f.__name__] = f`。
- **docstring 风格**：中文；写工具首句统一 `本操作会修改当前激活项目：...`；读工具首句 `只读：...`。
- **单测不起真 HTTP**：用 fake client 或 `httpx.MockTransport`。

---

### Task 1: client 加 `put_json` / `delete_json`

**Files:**
- Modify: `mcp/ontotwin_mcp/client.py`
- Test: `mcp/tests/test_client.py`

**Interfaces:**
- Consumes: 现有 `NexusClient._handle`、`map_transport_error`、`self.s.timeout_read`。
- Produces:
  - `NexusClient.put_json(operation: str, path: str, json: dict=None, timeout: float=None) -> dict|list|str`
  - `NexusClient.delete_json(operation: str, path: str, json: dict=None, timeout: float=None) -> dict|list|str`
  - 关键：DELETE 必须携带请求体，`httpx.Client.delete()` 不接受 body，改用 `self._c.request("DELETE", ...)`。

- [ ] **Step 1: 写失败测试**（追加到 `test_client.py` 末尾；文件顶部已 `import httpx, pytest`，新增 `import json`）

```python
import json  # 加到文件顶部已有 import 之后


def test_put_json_ok(make_client):
    def h(req):
        assert req.method == "PUT"
        assert req.url.path == "/api/v2/overlays/object-types/x"
        assert json.loads(req.content) == {"config": {}, "expected_revision": 3}
        return httpx.Response(200, json={"status": "ok"})
    c = make_client(h)
    assert c.put_json("save_overlay_type_config",
                      "/api/v2/overlays/object-types/x",
                      json={"config": {}, "expected_revision": 3}) == {"status": "ok"}


def test_delete_json_sends_body(make_client):
    seen = {}
    def h(req):
        seen["method"] = req.method
        seen["body"] = json.loads(req.content) if req.content else None
        return httpx.Response(200, json={"status": "ok"})
    c = make_client(h)
    c.delete_json("clear_overlay_instance_override",
                  "/api/v2/overlays/instances/i1", json={"expected_revision": 2})
    assert seen["method"] == "DELETE"
    assert seen["body"] == {"expected_revision": 2}


def test_put_json_default_timeout_falls_back(make_client):
    seen = {}
    def h(req):
        seen["timeout"] = req.extensions.get("timeout")
        return httpx.Response(200, json={"ok": True})
    c = make_client(h)
    c.put_json("op", "/x", json={"a": 1})
    assert seen["timeout"]["read"] == 30.0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_client.py -k "put_json or delete_json" -v`
Expected: FAIL（`AttributeError: 'NexusClient' object has no attribute 'put_json'`）

- [ ] **Step 3: 实现两个方法**（加到 `NexusClient` 内，`post_multipart` 之后）

```python
    def put_json(self, operation, path, json=None, timeout=None):
        to = timeout if timeout is not None else self.s.timeout_read
        try:
            r = self._c.put(path, json=json or {}, timeout=to)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)

    def delete_json(self, operation, path, json=None, timeout=None):
        to = timeout if timeout is not None else self.s.timeout_read
        try:
            # httpx 的 delete() 不支持 body，用 request 显式带 json
            r = self._c.request("DELETE", path, json=json or {}, timeout=to)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)
```

- [ ] **Step 4: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_client.py -v`
Expected: PASS（含既有用例）

- [ ] **Step 5: 提交**

```bash
git add mcp/ontotwin_mcp/client.py mcp/tests/test_client.py
git commit -m "feat(mcp): NexusClient 加 put_json/delete_json（DELETE 带 body 走 request）"
```

---

### Task 2: errors 补 422 / 409-revision / 404-active

**Files:**
- Modify: `mcp/ontotwin_mcp/errors.py:24`（`map_response_error`）
- Test: `mcp/tests/test_errors.py`

**Interfaces:**
- Consumes: 现有 `map_response_error(operation, status, body_text, parsed_json)`、`NexusError`。
- Produces（新增/调整分支，加法式，不改既有分支语义与优先级）：
  - 404 + `error == "active_project_not_found"` → `NEXUS_NO_ACTIVE_PROJECT`；其余 404 仍 `NEXUS_NOT_FOUND`。
  - 409：既有「项目漂移」（带 expected/actual 或 `error=="project changed"`）**优先**；否则 `error` 以 `revision_conflict` 结尾 → `NEXUS_REVISION_CONFLICT`；再否则 `NEXUS_CONFLICT`。
  - 422 → `NEXUS_VALIDATION`，把 `fields`（`[{path,message}]`）汇进 hint。

- [ ] **Step 1: 写失败测试**（追加到 `test_errors.py` 末尾）

```python
def test_422_validation_carries_fields():
    e = map_response_error(
        "save_overlay_type_config", 422,
        '{"error":"overlay_validation_failed","fields":[{"path":"slots.status","message":"缺少绑定"}]}',
        {"error": "overlay_validation_failed",
         "fields": [{"path": "slots.status", "message": "缺少绑定"}]})
    assert e.code == "NEXUS_VALIDATION"
    assert e.http_status == 422
    assert "slots.status" in str(e)


def test_409_revision_conflict_distinct_from_project_changed():
    e = map_response_error(
        "save_roaming_config", 409,
        '{"error":"scene_interaction_revision_conflict"}',
        {"error": "scene_interaction_revision_conflict"})
    assert e.code == "NEXUS_REVISION_CONFLICT"
    assert e.http_status == 409


def test_409_project_changed_still_wins_over_revision():
    e = map_response_error(
        "save_roaming_config", 409,
        '{"error":"project changed","expected":"a","actual":"b"}',
        {"error": "project changed", "expected": "a", "actual": "b"})
    assert e.code == "NEXUS_PROJECT_CHANGED"


def test_404_active_project_not_found_maps_no_active():
    e = map_response_error(
        "get_roaming_config", 404,
        '{"error":"active_project_not_found"}', {"error": "active_project_not_found"})
    assert e.code == "NEXUS_NO_ACTIVE_PROJECT"


def test_404_other_still_not_found():
    e = map_response_error(
        "get_route", 404,
        '{"error":"overlay_target_not_found"}', {"error": "overlay_target_not_found"})
    assert e.code == "NEXUS_NOT_FOUND"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_errors.py -k "422 or revision or active or other_still" -v`
Expected: FAIL（422 落到 `NEXUS_HTTP_ERROR`；revision 落到 `NEXUS_CONFLICT`；active 落到 `NEXUS_NOT_FOUND`）

- [ ] **Step 3: 改 `map_response_error`**（替换 404 分支、409 分支，并在 413 分支之前插入 422 分支）

```python
    if status == 404:
        if berr == "active_project_not_found":
            return NexusError("NEXUS_NO_ACTIVE_PROJECT", 404, operation, berr, False,
                              "请先用 activate_project 激活一个项目")
        return NexusError("NEXUS_NOT_FOUND", 404, operation, berr, False)
    if status == 409:
        # 「激活项目并发漂移」优先：带 expected/actual 或 error=="project changed"
        if "expected" in pj or "actual" in pj or berr == "project changed":
            exp = pj.get("expected"); act = pj.get("actual")
            return NexusError("NEXUS_PROJECT_CHANGED", 409, operation, berr, False,
                              f"当前激活项目已变（expected={exp} actual={act}），请重新确认后再写")
        # 配置乐观锁冲突：overlay_/scene_interaction_revision_conflict
        if isinstance(berr, str) and berr.endswith("revision_conflict"):
            return NexusError("NEXUS_REVISION_CONFLICT", 409, operation, berr, False,
                              "配置已被他处修改，请重新 GET 拿最新 revision 后重写")
        return NexusError("NEXUS_CONFLICT", 409, operation, berr, False,
                          "后端返回冲突（非激活项目漂移），请检查上述 error")
    if status == 422:
        fields = pj.get("fields") if isinstance(pj.get("fields"), list) else []
        hint = "；".join(
            f"{f.get('path')}: {f.get('message')}" for f in fields if isinstance(f, dict)
        )[:300] or "配置结构校验失败"
        return NexusError("NEXUS_VALIDATION", 422, operation, berr, False, hint)
```

- [ ] **Step 4: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_errors.py -v`
Expected: PASS（含既有 409/404/400/503 用例，尤其 `test_409_non_dict_parsed_json_no_crash` 仍为 `NEXUS_CONFLICT`）

- [ ] **Step 5: 提交**

```bash
git add mcp/ontotwin_mcp/errors.py mcp/tests/test_errors.py
git commit -m "feat(mcp): errors 补 422→VALIDATION、409-revision→REVISION_CONFLICT、404-active→NO_ACTIVE_PROJECT"
```

---

### Task 3: overlay 域（信息面板 10 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/overlay.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_overlay.py`

**Interfaces:**
- Consumes: `client.get/post_json/put_json/delete_json`（Task 1 产出）。
- Produces（工具名 → 端点）：
  - `list_overlay_templates()` → GET `/api/v2/overlays/templates`
  - `get_overlay_context(object_type_rid="", instance_id="")` → GET `/api/v2/overlays/context`（params 仅放非空项）
  - `preview_overlay(object_type_rid="", instance_id="", config=None)` → POST `/api/v2/overlays/preview`
  - `get_overlay_media_policy()` → GET `/api/v2/overlays/media/policy`
  - `enable_info_panel(object_type_rid)` → POST `/api/v2/ontology/inject`，body `{object_type_rid, interfaces:["I3D_Representable","I3D_Overlay"]}`
  - `save_overlay_type_config(object_type_rid, config, expected_revision)` → PUT `/api/v2/overlays/object-types/<rid>`，body `{config, expected_revision}`
  - `save_overlay_instance_override(instance_id, override, expected_revision)` → PUT `/api/v2/overlays/instances/<id>`，body `{override, expected_revision}`
  - `clear_overlay_instance_override(instance_id, expected_revision)` → DELETE `/api/v2/overlays/instances/<id>`，body `{expected_revision}`
  - `batch_overlay_instance_override(object_type_rid, instance_ids, merge_patch, expected_revisions)` → POST `/api/v2/overlays/instances/batch`
  - `save_overlay_media_policy(policy, expected_revision)` → PUT `/api/v2/overlays/media/policy`，body `{policy, expected_revision}`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_overlay.py`

```python
"""overlay 工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"ok": True}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}

    def post_multipart(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_overlay_context_only_nonempty_params():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_overlay_context")(object_type_rid="rid.a")
    assert c.calls[-1] == ("get", "/api/v2/overlays/context", {"object_type_rid": "rid.a"})


def test_enable_info_panel_injects_two_interfaces():
    c = C(); mcp = build_server(c)
    _t(mcp, "enable_info_panel")("rid.a")
    method, path, body = c.calls[-1]
    assert path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable", "I3D_Overlay"]}


def test_save_overlay_type_config_put_body_and_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("a#b", {"slots": {}}, 4)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/overlays/object-types/a%23b"
    assert body == {"config": {"slots": {}}, "expected_revision": 4}


def test_clear_overlay_instance_override_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_overlay_instance_override")("i1", 2)
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/overlays/instances/i1"
    assert body == {"expected_revision": 2}


def test_batch_overlay_instance_override_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "batch_overlay_instance_override")(
        "rid.a", ["i1", "i2"], {"slots": {}}, {"i1": 1, "i2": 3})
    method, path, body = c.calls[-1]
    assert path == "/api/v2/overlays/instances/batch"
    assert body == {"object_type_rid": "rid.a", "instance_ids": ["i1", "i2"],
                    "merge_patch": {"slots": {}}, "expected_revisions": {"i1": 1, "i2": 3}}


def test_overlay_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "list_overlay_templates", "get_overlay_context", "preview_overlay",
        "get_overlay_media_policy", "enable_info_panel", "save_overlay_type_config",
        "save_overlay_instance_override", "clear_overlay_instance_override",
        "batch_overlay_instance_override", "save_overlay_media_policy",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_overlay.py -v`
Expected: FAIL（`KeyError` / 工具未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/overlay.py`**

```python
"""overlay 域：信息面板配置读写。

读（read-only）：模板 / 上下文 / 预览 / 媒体策略。
写（config-write，项目级持久化，expected_revision 必填）：启用面板能力、存类型配置、
存/清实例覆盖、批量覆盖、存媒体策略。

并发：写前先用 get_overlay_context 拿 revision，改结构后带 expected_revision 写回；
遇 NEXUS_REVISION_CONFLICT 重新读后重写。revision 绑定当前激活项目的这份配置，
项目切走则旧 revision 必对不上 → 409，故本域无需再透传 expected_project_id。
"""
from typing import Optional
from urllib.parse import quote

INFO_PANEL_INTERFACES = ["I3D_Representable", "I3D_Overlay"]


def register(mcp, client, registry):

    @mcp.tool()
    def list_overlay_templates() -> dict:
        """只读：列出可用的信息面板模板。"""
        return client.get("list_overlay_templates", "/api/v2/overlays/templates")

    @mcp.tool()
    def get_overlay_context(object_type_rid: str = "", instance_id: str = "") -> dict:
        """只读：读取信息面板配置上下文。

        返回含 type_config.revision / instance_override.revision /
        instances[].override_revision / media_policy.revision。写面板前先调它拿
        revision 与当前活配置，照结构改后再 save_*。
        """
        params = {}
        if object_type_rid:
            params["object_type_rid"] = object_type_rid
        if instance_id:
            params["instance_id"] = instance_id
        return client.get("get_overlay_context", "/api/v2/overlays/context", params=params)

    @mcp.tool()
    def preview_overlay(object_type_rid: str = "", instance_id: str = "",
                        config: Optional[dict] = None) -> dict:
        """只读（纯计算）：按给定 config 预览面板解析结果，不落库。config 省略时用已存配置。"""
        body = {"object_type_rid": object_type_rid or None,
                "instance_id": instance_id or None, "config": config}
        return client.post_json("preview_overlay", "/api/v2/overlays/preview", json=body)

    @mcp.tool()
    def get_overlay_media_policy() -> dict:
        """只读：读取媒体域名策略（含 revision）。"""
        return client.get("get_overlay_media_policy", "/api/v2/overlays/media/policy")

    @mcp.tool()
    def enable_info_panel(object_type_rid: str) -> dict:
        """本操作会修改当前激活项目：给类型注入信息面板能力（I3D_Representable+I3D_Overlay）。

        类型首次配置面板前调用；幂等（重复注入同一组接口无副作用）。
        """
        return client.post_json(
            "enable_info_panel", "/api/v2/ontology/inject",
            json={"object_type_rid": object_type_rid, "interfaces": INFO_PANEL_INTERFACES})

    @mcp.tool()
    def save_overlay_type_config(object_type_rid: str, config: dict,
                                 expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存类型级信息面板配置。

        expected_revision 取自 get_overlay_context 的 type_config.revision；
        冲突返回 NEXUS_REVISION_CONFLICT，重读后再写。
        """
        return client.put_json(
            "save_overlay_type_config",
            f"/api/v2/overlays/object-types/{quote(object_type_rid, safe='/')}",
            json={"config": config, "expected_revision": expected_revision})

    @mcp.tool()
    def save_overlay_instance_override(instance_id: str, override: dict,
                                       expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存实例级面板覆盖。

        expected_revision 取自 get_overlay_context 的 instance_override.revision。
        """
        return client.put_json(
            "save_overlay_instance_override",
            f"/api/v2/overlays/instances/{quote(instance_id, safe='/')}",
            json={"override": override, "expected_revision": expected_revision})

    @mcp.tool()
    def clear_overlay_instance_override(instance_id: str, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：清除实例覆盖，恢复继承类型配置。"""
        return client.delete_json(
            "clear_overlay_instance_override",
            f"/api/v2/overlays/instances/{quote(instance_id, safe='/')}",
            json={"expected_revision": expected_revision})

    @mcp.tool()
    def batch_overlay_instance_override(object_type_rid: str, instance_ids: list,
                                        merge_patch: dict, expected_revisions: dict) -> dict:
        """本操作会修改当前激活项目：给一批实例合并同一份覆盖补丁。

        expected_revisions 为 {instance_id: revision} 映射，逐实例乐观并发校验。
        """
        return client.post_json(
            "batch_overlay_instance_override", "/api/v2/overlays/instances/batch",
            json={"object_type_rid": object_type_rid, "instance_ids": instance_ids,
                  "merge_patch": merge_patch, "expected_revisions": expected_revisions})

    @mcp.tool()
    def save_overlay_media_policy(policy: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存媒体域名策略。"""
        return client.put_json(
            "save_overlay_media_policy", "/api/v2/overlays/media/policy",
            json={"policy": policy, "expected_revision": expected_revision})

    for f in (list_overlay_templates, get_overlay_context, preview_overlay,
              get_overlay_media_policy, enable_info_panel, save_overlay_type_config,
              save_overlay_instance_override, clear_overlay_instance_override,
              batch_overlay_instance_override, save_overlay_media_policy):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`mcp/ontotwin_mcp/tools/__init__.py`）

```python
from . import project, ontology, runtime, cad, binding, phase2, overlay


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2, overlay):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_overlay.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/overlay.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_overlay.py
git commit -m "feat(mcp): overlay 域 10 工具（信息面板读写，直通式+显式 revision）"
```

---

### Task 4: scene 域（人物漫游 + 漫游路线 10 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/scene.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_scene.py`

**Interfaces:**
- Consumes: `client.get/post_json/put_json/delete_json`。
- Produces（工具名 → 端点）：
  - `get_scene_catalog()` → GET `/api/v2/scene-interactions/catalog`
  - `get_roaming_config()` → GET `/api/v2/scene-interactions/roaming`
  - `list_routes()` → GET `/api/v2/scene-interactions/routes`
  - `get_route(route_id)` → GET `/api/v2/scene-interactions/routes/<id>`
  - `save_roaming_config(config, expected_revision)` → PUT `/api/v2/scene-interactions/roaming`，body `{config, expected_revision}`
  - `create_route(route, expected_revision)` → POST `/api/v2/scene-interactions/routes`，body `{route, expected_revision}`
  - `update_route(route_id, route, expected_revision)` → PUT `.../routes/<id>`，body `{route, expected_revision}`
  - `delete_route(route_id, expected_revision)` → DELETE `.../routes/<id>`，body `{expected_revision}`
  - `review_route(route_id, expected_revision)` → POST `.../routes/<id>/review`，body `{expected_revision}`
  - `set_default_route(route_id, expected_revision)` → POST `.../routes/<id>/default`，body `{expected_revision}`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_scene.py`

```python
"""scene 工具单测（fake client，不起真 HTTP）。"""
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

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"ok": True}

    def post_multipart(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_route_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_route")("r#1")
    assert c.calls[-1] == ("get", "/api/v2/scene-interactions/routes/r%231", None)


def test_save_roaming_config_put_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_roaming_config")({"spawn": {}}, 7)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/scene-interactions/roaming"
    assert body == {"config": {"spawn": {}}, "expected_revision": 7}


def test_create_route_post_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_route")({"name": "巡检"}, 2)
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/scene-interactions/routes"
    assert body == {"route": {"name": "巡检"}, "expected_revision": 2}


def test_update_route_put_encoded_path_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "update_route")("r1", {"name": "x"}, 3)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/scene-interactions/routes/r1"
    assert body == {"route": {"name": "x"}, "expected_revision": 3}


def test_delete_route_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_route")("r1", 5)
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/scene-interactions/routes/r1"
    assert body == {"expected_revision": 5}


def test_set_default_route_post_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_default_route")("r1", 4)
    method, path, body = c.calls[-1]
    assert path == "/api/v2/scene-interactions/routes/r1/default"
    assert body == {"expected_revision": 4}


def test_scene_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "get_scene_catalog", "get_roaming_config", "list_routes", "get_route",
        "save_roaming_config", "create_route", "update_route", "delete_route",
        "review_route", "set_default_route",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_scene.py -v`
Expected: FAIL（工具未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/scene.py`**

```python
"""scene 域：人物漫游 + 漫游路线读写。

读（read-only）：catalog / roaming / routes / route。
写（config-write，项目级持久化，expected_revision 必填）：save_roaming、
路线增删改 / 评审 / 设默认。

并发：写前先 get_roaming_config / list_routes / get_route 拿 revision，带
expected_revision 写回；遇 NEXUS_REVISION_CONFLICT 重读后重写。
"""
from urllib.parse import quote

_ROUTES = "/api/v2/scene-interactions/routes"


def register(mcp, client, registry):

    @mcp.tool()
    def get_scene_catalog() -> dict:
        """只读：场景交互资源目录（可用帧 / 路线等）。"""
        return client.get("get_scene_catalog", "/api/v2/scene-interactions/catalog")

    @mcp.tool()
    def get_roaming_config() -> dict:
        """只读：人物漫游配置（含 revision、runtime_status、calibration_state、catalog_version）。"""
        return client.get("get_roaming_config", "/api/v2/scene-interactions/roaming")

    @mcp.tool()
    def list_routes() -> dict:
        """只读：漫游路线列表（含 default_route_id）。"""
        return client.get("list_routes", _ROUTES)

    @mcp.tool()
    def get_route(route_id: str) -> dict:
        """只读：单条漫游路线（含 revision）。"""
        return client.get("get_route", f"{_ROUTES}/{quote(route_id, safe='/')}")

    @mcp.tool()
    def save_roaming_config(config: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存人物漫游配置。

        expected_revision 取自 get_roaming_config 的 revision。
        """
        return client.put_json(
            "save_roaming_config", "/api/v2/scene-interactions/roaming",
            json={"config": config, "expected_revision": expected_revision})

    @mcp.tool()
    def create_route(route: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：新建一条漫游路线。

        expected_revision 为路线集合版本，取自 list_routes / get_roaming_config。
        """
        return client.post_json(
            "create_route", _ROUTES,
            json={"route": route, "expected_revision": expected_revision})

    @mcp.tool()
    def update_route(route_id: str, route: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：更新指定漫游路线。"""
        return client.put_json(
            "update_route", f"{_ROUTES}/{quote(route_id, safe='/')}",
            json={"route": route, "expected_revision": expected_revision})

    @mcp.tool()
    def delete_route(route_id: str, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：删除指定漫游路线。"""
        return client.delete_json(
            "delete_route", f"{_ROUTES}/{quote(route_id, safe='/')}",
            json={"expected_revision": expected_revision})

    @mcp.tool()
    def review_route(route_id: str, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：标记路线为已评审。"""
        return client.post_json(
            "review_route", f"{_ROUTES}/{quote(route_id, safe='/')}/review",
            json={"expected_revision": expected_revision})

    @mcp.tool()
    def set_default_route(route_id: str, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：设为人物漫游默认路线。"""
        return client.post_json(
            "set_default_route", f"{_ROUTES}/{quote(route_id, safe='/')}/default",
            json={"expected_revision": expected_revision})

    for f in (get_scene_catalog, get_roaming_config, list_routes, get_route,
              save_roaming_config, create_route, update_route, delete_route,
              review_route, set_default_route):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`mcp/ontotwin_mcp/tools/__init__.py`）

```python
from . import project, ontology, runtime, cad, binding, phase2, overlay, scene


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2, overlay, scene):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全部既有 + 新增用例）

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/scene.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_scene.py
git commit -m "feat(mcp): scene 域 10 工具（人物漫游+漫游路线读写，直通式+显式 revision）"
```

---

### Task 5: 协议冒烟 + selfcheck + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/selfcheck.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

**Interfaces:**
- Consumes: Task 3/4 注册的工具。
- Produces：协议层验证 20 新工具可 list/call；selfcheck 读工具冒烟补 5 个；skill 增「场景配置」段（文档粒度 A）。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_scene_config_tools_listed_and_callable():
    """场景配置 20 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/overlays/templates": {"templates": []}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("list_overlay_templates", {})

    new_tools = {
        "list_overlay_templates", "get_overlay_context", "preview_overlay",
        "get_overlay_media_policy", "enable_info_panel", "save_overlay_type_config",
        "save_overlay_instance_override", "clear_overlay_instance_override",
        "batch_overlay_instance_override", "save_overlay_media_policy",
        "get_scene_catalog", "get_roaming_config", "list_routes", "get_route",
        "save_roaming_config", "create_route", "update_route", "delete_route",
        "review_route", "set_default_route",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 50, f"工具总数应 ≥50（30+20），实际 {len(names)}"
    assert res.isError is False
```

> 注：`FakeClient` 当前只有 get/post_json/post_multipart。若本测试触发的读工具够用则无需改；本测试只调 `list_overlay_templates`（走 get），不需要 put/delete。保持 FakeClient 不动。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k scene_config -v`
Expected: FAIL（工具数不足 / 缺工具——若 Task 3/4 已完成则此步应直接 PASS，那样跳到 Step 3）

- [ ] **Step 3: selfcheck 补 5 个只读冒烟工具**（`mcp/selfcheck.py` 的工具列表尾部追加）

把列表改为（新增最后一行 5 个场景配置只读工具）：

```python
for t in [
    "get_active_project", "list_projects", "list_object_types",
    "get_import_staging_graph", "list_instances", "get_state_snapshots",
    "list_components", "list_roster", "get_spatial_profile", "get_ue_binding_status",
    "list_overlay_templates", "get_overlay_context", "get_scene_catalog",
    "get_roaming_config", "list_routes",
]:
    run(t)
```

同时把首行说明的「10 个」改为「15 个」：

```python
print(f"=== OntoTwin MCP 基础只读链路冒烟检查 · 15 个代表性只读工具（后端 {BASE}）===")
```

（文件顶部 docstring 里的「10 个」措辞可一并改为「15 个」，非必须。）

- [ ] **Step 4: skill 增「场景配置」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在既有「运行态运维」类小节之后追加下面整段（文档粒度 A：导航速查 + 依赖活配置，不复述全字段）：

````markdown
## 场景配置（信息面板 / 人物漫游 / 漫游路线）

三块配置都走「读活配置 → 改 → 带 revision 写回」，后端 validator 兜底。

**金规**
1. **写前必先读**：`get_overlay_context` / `get_roaming_config` / `get_route` 返回里带 revision，写工具的 `expected_revision` 必填，取自刚读到的值。
2. **遇 `NEXUS_REVISION_CONFLICT`**：配置被他处改过 → 重新读 → 合并意图 → 重写。
3. **config 结构以读到的活配置为准**，不臆造字段；结构非法后端返回 `NEXUS_VALIDATION`，按 `fields` 里的 path/message 纠正。
4. **类型首次配面板**先 `enable_info_panel(object_type_rid)` 注入能力，再 `save_overlay_type_config`。

**信息面板 config 速查**（详细字段以 `get_overlay_context` 返回为准）
- 槽位 slots：`body`（正文）/`status`（状态灯+文案）/`media`（视频）/`metrics`（指标）。
- 绑定源 4 种：`literal`（固定值）/`instance`（实例信息）/`object_type`（类型信息）/`raw_state`（实时数据，如 `status`/`capacity`）。
- 状态分级配色：`slots.status.appearance[level] = {label, color}`，level 取 `statusLevelOptions`。

**典型流程**
- 改某类型面板的状态配色：`enable_info_panel(rid)` →（若已启用可跳过）`get_overlay_context(object_type_rid=rid)` → 改 `config.slots.status.appearance` → `save_overlay_type_config(rid, config, expected_revision)`。
- 批量给一批实例覆盖标签：`get_overlay_context(object_type_rid=rid)` 拿各实例 `override_revision` → `batch_overlay_instance_override(rid, ids, merge_patch, expected_revisions)`。
- 新建漫游路线并设默认：`list_routes()` 拿集合 revision → `create_route(route, expected_revision)` → `set_default_route(new_id, expected_revision)`。

**触发示例**
- 「把货架类型信息面板的『缺货』状态配成红色」
- 「给这批 AGV 实例的面板标题统一改成设备编号」
- 「新建一条从入口到 A 区的巡检漫游路线，并设为默认」
````

- [ ] **Step 5: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 6: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/selfcheck.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): 场景配置协议冒烟 + selfcheck 补读工具 + skill 场景配置 playbook"
```

---

## 交付后（人工，可选）

- 重打发行包：`mcp/build-dist.ps1`（把 20 新工具与 skill 更新打进 `D:\ontotwin-mcp.zip`）。
- 真部署只读冒烟：装好包后 `python selfcheck.py`，确认新增 5 个只读工具对 88.66 后端 `[OK]`。
- 写路径只对一次性抛弃数据集验证，不碰生产库。

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 20 工具 ↔ Task 3（overlay 10）+ Task 4（scene 10）；§4 client ↔ Task 1；§5 errors ↔ Task 2；§7 skill 文档 A ↔ Task 5 Step 4；§9 测试三层（协议/单元/冒烟）↔ Task 3–5 测试。
- **类型一致**：所有写工具 `expected_revision: int` 必填、无默认；`config`/`override`/`route`/`policy`/`merge_patch`/`expected_revisions` 类型贯穿 spec 与 plan 一致。
- **占位符扫描**：无 TBD；每个 code step 均含完整代码。
- **与既有惯例一致**：URL 编码统一 `quote(safe='/')`（对齐 `test_*_url_encodes_special_chars`）；registry 尾注册；fake-client 单测范式沿用 `test_tools_write.py`。
