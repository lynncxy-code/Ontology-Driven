# OntoTwin MCP · M1–M4 转译层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在独立子目录 `mcp/` 构建一个本地 stdio 的 MCP server（Python + FastMCP），把 Nexus 的 `/api/v2` REST 包成 ~27 个动词工具 + 一套 skill，让 Claude Code / Cursor 能直接驱动 Nexus 的读/写/运维。

**Architecture:** 纯转译层，不 import 后端模块，只发 HTTP。分层：`config`（env）→ `client`（httpx + 错误映射 + multipart）→ `tools/*`（按域分组的工具，每个薄薄调 client）→ `server`（FastMCP 注册 + stdio 入口）。写工具透传 `expected_project_id`，映射后端 409；文件工具收本地 `file_path`，client 侧读文件组 multipart。

**Tech Stack:** Python 3.10、官方 `mcp` SDK（FastMCP）、httpx、pytest。

## Global Constraints

- **独立子项目**：全部代码在 `mcp/`，**不 import 后端任何模块**，只发 HTTP（copy from spec §2）。
- 依赖 `mcp` + `httpx` + `pytest` 只进 `mcp/pyproject.toml`，**不碰 `backend/requirements.txt`**（spec §12）。
- **FastMCP import 路径**：本计划按 `from mcp.server.fastmcp import FastMCP`、`@mcp.tool()`、`mcp.run()`（默认 stdio）书写。实现者在 Task 1 **pin `mcp` 版本后立即核对该 import 路径与装饰器 API**；若该版本 API 不同，以 pin 版本的官方用法为准并在 Task 1 报告记录，后续任务沿用。
- **工具面**：M1–M2 只注册 spec §3.2 的 27 个核心工具；§3.3 二期工具留 M4（只读部分）（spec §3.1–3.3）。
- **操作分级**（spec §3.1）：read / compute / stage-write / persist-write；写工具 description 首句写「本操作会修改当前激活项目」。
- **项目上下文**：写工具必带 `expected_project_id`；`get_active_project` 归一化返回 `{dataset_id, project_id, writable, kind}`（spec §5.4）。`create_empty_project` 固定传 `activate=false`（spec §3.2、§14.2）。
- **NEXUS_BASE_URL** 默认 `http://192.168.88.66:5000`；分级超时 env `NEXUS_TIMEOUT_CONNECT/_READ/_UPLOAD/_CADPARSE`；`NEXUS_ALLOWED_ROOTS`（spec §10）。
- **错误映射**（spec §6）：保留后端原始状态码 + 错误体 + operation，再分类；仅错误文本明确匹配「无激活项目」才给 activate 提示；Neo4j 503 如实说「语义图库暂不可达」不承诺「不影响主功能」。
- **文件工具**（spec §7）：收显式本地 `file_path`；client 读文件 → httpx multipart；路径规范化 + 存在 + 普通文件 + 落在 allowed roots 内 + 扩展名/大小校验；**本体 CSV 保留原始 basename**；multipart 的 `expected_project_id` 走 **form field**。首版不用 base64。
- **非幂等写超时后禁止自动重试**（create/save/mint/bind/override）；只读/计算可有限退避（spec §10）。
- 提交信息用中文 Conventional Commits。测试工作目录 `mcp/`。

---

## 文件结构

- Create `mcp/pyproject.toml` — 依赖 mcp/httpx/pytest；entry `python -m ontotwin_mcp`。
- Create `mcp/ontotwin_mcp/__init__.py`
- Create `mcp/ontotwin_mcp/config.py` — 读 env（base url / 分级超时 / allowed roots）。
- Create `mcp/ontotwin_mcp/errors.py` — `NexusError` + `map_response_error` + `map_transport_error`。
- Create `mcp/ontotwin_mcp/client.py` — `NexusClient`（httpx，get/post_json/post_multipart，接错误映射）。
- Create `mcp/ontotwin_mcp/files.py` — `resolve_upload(file_path)`：allowed roots / 存在 / 大小 / 扩展名 / 保留 basename。
- Create `mcp/ontotwin_mcp/tools/__init__.py` — `register_all(mcp, client)`。
- Create `mcp/ontotwin_mcp/tools/{project,ontology,cad,binding,runtime}.py` — 各域工具。
- Create `mcp/ontotwin_mcp/server.py` — FastMCP 实例 + `register_all` + `main()` stdio 入口。
- Create `mcp/skills/ontotwin-nexus/SKILL.md` — 编排 playbook。
- Create `mcp/README.md` — Claude Code / Cursor 注册 + 审批配置。
- Create `mcp/tests/{conftest,test_config,test_errors,test_client,test_tools_read,test_files,test_tools_write,test_stdio,test_smoke}.py`。

---

## Task 1: 子项目骨架 + config

**Files:**
- Create: `mcp/pyproject.toml`、`mcp/ontotwin_mcp/__init__.py`、`mcp/ontotwin_mcp/config.py`
- Test: `mcp/tests/test_config.py`、`mcp/tests/__init__.py`

**Interfaces:**
- Produces: `config.Settings`（`base_url`, `timeout_connect/read/upload/cadparse`, `allowed_roots: list[str]`）；`config.load() -> Settings` 从 env 读，带默认值。

- [ ] **Step 1: 写 pyproject.toml**

```toml
[project]
name = "ontotwin-mcp"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["mcp>=1.9,<2", "httpx>=0.27"]  # pin 1.x：FastMCP API 稳定（mcp 2.0.0 是大版本，API 可能变，Task 1 Step 2 核对）

[project.optional-dependencies]
dev = ["pytest>=8"]

[project.scripts]
ontotwin-mcp = "ontotwin_mcp.server:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: 核对 FastMCP import 路径**

Run: `cd mcp && pip install -e . && python -c "from mcp.server.fastmcp import FastMCP; print('ok', FastMCP)"`
Expected: 打印 ok。若 import 失败，查 pin 的 `mcp` 版本正确路径，记进报告并据此调整后续所有任务的 import。

- [ ] **Step 3: 写失败测试 test_config.py**

```python
import os
from ontotwin_mcp import config

def test_defaults(monkeypatch):
    for k in ("NEXUS_BASE_URL","NEXUS_TIMEOUT_READ","NEXUS_ALLOWED_ROOTS"):
        monkeypatch.delenv(k, raising=False)
    s = config.load()
    assert s.base_url == "http://192.168.88.66:5000"
    assert s.timeout_read == 30.0
    assert s.allowed_roots == []

def test_env_override(monkeypatch):
    monkeypatch.setenv("NEXUS_BASE_URL", "http://127.0.0.1:5000")
    monkeypatch.setenv("NEXUS_TIMEOUT_READ", "5")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", "/data;/tmp/up")
    s = config.load()
    assert s.base_url == "http://127.0.0.1:5000"
    assert s.timeout_read == 5.0
    assert s.allowed_roots == ["/data", "/tmp/up"]
```

- [ ] **Step 4: 跑，确认 FAIL**

Run: `cd mcp && python -m pytest tests/test_config.py -q`
Expected: FAIL（ModuleNotFoundError / config 未实现）。

- [ ] **Step 5: 实现 config.py**

```python
import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    base_url: str = "http://192.168.88.66:5000"
    timeout_connect: float = 5.0
    timeout_read: float = 30.0
    timeout_upload: float = 60.0
    timeout_cadparse: float = 120.0
    allowed_roots: list = field(default_factory=list)

def _f(name, default):
    v = os.environ.get(name)
    return float(v) if v else default

def load() -> Settings:
    roots = os.environ.get("NEXUS_ALLOWED_ROOTS", "")
    return Settings(
        base_url=os.environ.get("NEXUS_BASE_URL", "http://192.168.88.66:5000").rstrip("/"),
        timeout_connect=_f("NEXUS_TIMEOUT_CONNECT", 5.0),
        timeout_read=_f("NEXUS_TIMEOUT_READ", 30.0),
        timeout_upload=_f("NEXUS_TIMEOUT_UPLOAD", 60.0),
        timeout_cadparse=_f("NEXUS_TIMEOUT_CADPARSE", 120.0),
        allowed_roots=[p for p in roots.split(";") if p],
    )
```

- [ ] **Step 6: 跑通 + commit**

Run: `cd mcp && python -m pytest tests/test_config.py -q` → 2 passed
```bash
git add mcp/pyproject.toml mcp/ontotwin_mcp/__init__.py mcp/ontotwin_mcp/config.py mcp/tests/__init__.py mcp/tests/test_config.py
git commit -m "feat(mcp): 子项目骨架 + config（env 读取，分级超时/allowed roots）"
```

---

## Task 2: errors.py — 分级错误映射

**Files:**
- Create: `mcp/ontotwin_mcp/errors.py`
- Test: `mcp/tests/test_errors.py`

**Interfaces:**
- Produces:
  - `class NexusError(Exception)`：属性 `code, http_status, operation, backend_error, retryable`；`__str__` 给人读的中文。
  - `map_response_error(operation, status, body_text, parsed_json) -> NexusError`：按 spec §6 分级。
  - `map_transport_error(operation, exc) -> NexusError`：连接/超时类。

- [ ] **Step 1: 写失败测试**

```python
from ontotwin_mcp.errors import map_response_error, map_transport_error, NexusError
import httpx

def test_no_active_project_hint():
    e = map_response_error("save_components", 400, '{"error":"当前无激活项目，请先..."}', {"error":"当前无激活项目，请先..."})
    assert e.http_status == 400 and "activate_project" in str(e)

def test_generic_400_no_false_hint():
    e = map_response_error("upload_roster", 400, '{"error":"缺少必须的文件"}', {"error":"缺少必须的文件"})
    assert e.code == "NEXUS_VALIDATION_ERROR" and "activate_project" not in str(e)
    assert e.retryable is False

def test_409_project_changed():
    e = map_response_error("mint_instances", 409, '{"error":"project changed","expected":"a","actual":"b"}', {"error":"project changed","expected":"a","actual":"b"})
    assert e.http_status == 409 and "a" in str(e) and "b" in str(e)

def test_503_neo4j_no_overpromise():
    e = map_response_error("get_project_ontology_graph", 503, "graph down", None)
    assert "语义图库暂不可达" in str(e) and "不影响主功能" not in str(e)

def test_timeout_retryable_only_for_reads():
    e = map_transport_error("list_instances", httpx.ReadTimeout("t"))
    assert e.code == "NEXUS_TIMEOUT" and "NEXUS_BASE_URL" in str(e)
```

- [ ] **Step 2: 跑确认 FAIL** — Run: `cd mcp && python -m pytest tests/test_errors.py -q` → FAIL

- [ ] **Step 3: 实现 errors.py**

```python
import httpx

class NexusError(Exception):
    def __init__(self, code, http_status, operation, backend_error, retryable, hint=""):
        self.code, self.http_status, self.operation = code, http_status, operation
        self.backend_error, self.retryable, self.hint = backend_error, retryable, hint
        msg = f"[{code}] {operation}"
        if http_status: msg += f" (HTTP {http_status})"
        if backend_error: msg += f": {backend_error}"
        if hint: msg += f" — {hint}"
        super().__init__(msg)

def map_response_error(operation, status, body_text, parsed_json):
    berr = (parsed_json or {}).get("error") if isinstance(parsed_json, dict) else (body_text or "")[:300]
    if status == 400:
        if isinstance(berr, str) and "无激活项目" in berr:
            return NexusError("NEXUS_NO_ACTIVE_PROJECT", 400, operation, berr, False,
                              "请先用 activate_project 激活一个项目")
        return NexusError("NEXUS_VALIDATION_ERROR", 400, operation, berr, False)
    if status == 403:
        return NexusError("NEXUS_FORBIDDEN", 403, operation, berr, False, "项目/UE 绑定不匹配")
    if status == 404:
        return NexusError("NEXUS_NOT_FOUND", 404, operation, berr, False)
    if status == 409:
        exp = (parsed_json or {}).get("expected"); act = (parsed_json or {}).get("actual")
        return NexusError("NEXUS_PROJECT_CHANGED", 409, operation, berr, False,
                          f"当前激活项目已变（expected={exp} actual={act}），请重新确认后再写")
    if status == 413:
        return NexusError("NEXUS_TOO_LARGE", 413, operation, berr, False)
    if status == 503:
        return NexusError("NEXUS_DEGRADED", 503, operation, berr, True, "语义图库暂不可达")
    if 500 <= status < 600:
        return NexusError("NEXUS_BACKEND_ERROR", status, operation, berr, False)
    return NexusError("NEXUS_HTTP_ERROR", status, operation, berr, False)

def map_transport_error(operation, exc):
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
        return NexusError("NEXUS_UNREACHABLE", 0, operation, str(exc), False,
                          "Nexus 后端不可达，检查 NEXUS_BASE_URL")
    if isinstance(exc, httpx.TimeoutException):
        return NexusError("NEXUS_TIMEOUT", 0, operation, str(exc), True,
                          "请求超时，检查 NEXUS_BASE_URL 或后端负载")
    return NexusError("NEXUS_TRANSPORT_ERROR", 0, operation, str(exc), False)
```

- [ ] **Step 4: 跑通 + commit**

Run: `cd mcp && python -m pytest tests/test_errors.py -q` → 5 passed
```bash
git add mcp/ontotwin_mcp/errors.py mcp/tests/test_errors.py
git commit -m "feat(mcp): 分级错误映射（保留原状态+operation，无激活项目/409/503 精准区分）"
```

---

## Task 3: client.py — httpx 客户端 + 错误映射 + multipart

**Files:**
- Create: `mcp/ontotwin_mcp/client.py`
- Test: `mcp/tests/test_client.py`、`mcp/tests/conftest.py`

**Interfaces:**
- Consumes: `config.Settings`、`errors.*`。
- Produces: `NexusClient(settings)`，方法：
  - `get(operation, path, params=None) -> Any`
  - `post_json(operation, path, json=None, timeout=None) -> Any`
  - `post_multipart(operation, path, files, data=None) -> Any`（`files`: `[(field, filename, bytes)]`）
  非 2xx → 抛 `NexusError`（走 errors）；传输异常 → `map_transport_error`。

- [ ] **Step 1: 写 conftest（用 httpx MockTransport，不需真服务器）**

```python
import httpx, pytest
from ontotwin_mcp.config import Settings
from ontotwin_mcp.client import NexusClient

@pytest.fixture
def make_client():
    def _make(handler):
        s = Settings(base_url="http://test")
        c = NexusClient(s, transport=httpx.MockTransport(handler))
        return c
    return _make
```

- [ ] **Step 2: 写失败测试**

```python
import httpx
def test_get_ok(make_client):
    def h(req):
        assert req.url.path == "/api/v2/instances"
        return httpx.Response(200, json=[{"id":"i1"}])
    c = make_client(h)
    assert c.get("list_instances", "/api/v2/instances") == [{"id":"i1"}]

def test_post_json_409_maps(make_client):
    from ontotwin_mcp.errors import NexusError
    def h(req):
        return httpx.Response(409, json={"error":"project changed","expected":"a","actual":"b"})
    c = make_client(h)
    import pytest
    with pytest.raises(NexusError) as e:
        c.post_json("mint_instances", "/api/v2/binding/mint", json={"dry_run": False})
    assert e.value.http_status == 409

def test_multipart_sends_file(make_client):
    seen = {}
    def h(req):
        seen["ct"] = req.headers.get("content-type","")
        return httpx.Response(200, json={"status":"ok"})
    c = make_client(h)
    c.post_multipart("upload_roster", "/api/v2/binding/roster/upload",
                     files=[("file","roster.csv",b"x")], data={"expected_project_id":"p"})
    assert "multipart/form-data" in seen["ct"]

def test_connect_error_maps(make_client):
    from ontotwin_mcp.errors import NexusError
    def h(req): raise httpx.ConnectError("refused")
    c = make_client(h)
    import pytest
    with pytest.raises(NexusError) as e:
        c.get("list_projects", "/api/v2/ontology/datasets")
    assert e.value.code == "NEXUS_UNREACHABLE"
```

- [ ] **Step 3: 跑确认 FAIL**

- [ ] **Step 4: 实现 client.py**

```python
import httpx
from .errors import map_response_error, map_transport_error

class NexusClient:
    def __init__(self, settings, transport=None):
        self.s = settings
        self._c = httpx.Client(
            base_url=settings.base_url,
            timeout=httpx.Timeout(settings.timeout_read, connect=settings.timeout_connect),
            transport=transport,
        )

    def _handle(self, operation, resp):
        if resp.is_success:
            ct = resp.headers.get("content-type", "")
            return resp.json() if "application/json" in ct else resp.text
        try:
            parsed = resp.json()
        except Exception:
            parsed = None
        raise map_response_error(operation, resp.status_code, resp.text, parsed)

    def get(self, operation, path, params=None):
        try:
            r = self._c.get(path, params=params)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)

    def post_json(self, operation, path, json=None, timeout=None):
        try:
            r = self._c.post(path, json=json or {}, timeout=timeout)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)

    def post_multipart(self, operation, path, files, data=None):
        mp = [(field, (fname, content)) for (field, fname, content) in files]
        try:
            r = self._c.post(path, files=mp, data=data or {}, timeout=self.s.timeout_upload)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)
```

- [ ] **Step 5: 跑通 + commit** — `git commit -m "feat(mcp): httpx 客户端（get/post_json/multipart，接错误映射与分级超时）"`

---

## Task 4: files.py — 本地文件校验与读取

**Files:**
- Create: `mcp/ontotwin_mcp/files.py`
- Test: `mcp/tests/test_files.py`

**Interfaces:**
- Produces: `resolve_upload(file_path, settings, allowed_ext=None, max_bytes=50_000_000) -> (basename, bytes)`：规范化路径 → 校验存在/普通文件/在 allowed_roots 内/扩展名/大小 → 返回原始 basename + 内容。违规抛 `ValueError`（中文原因）。空 `allowed_roots` = 不限制（本地开发默认，但记录警告）。

- [ ] **Step 1: 写失败测试**

```python
import os, pytest
from ontotwin_mcp.files import resolve_upload
from ontotwin_mcp.config import Settings

def test_reads_and_keeps_basename(tmp_path):
    p = tmp_path / "objectdef.csv"; p.write_bytes("a".encode("utf-8-sig"))
    s = Settings(allowed_roots=[str(tmp_path)])
    name, content = resolve_upload(str(p), s, allowed_ext=[".csv"])
    assert name == "objectdef.csv" and content.startswith(b"\xef\xbb\xbf")

def test_outside_allowed_roots_rejected(tmp_path):
    p = tmp_path / "x.csv"; p.write_text("x")
    s = Settings(allowed_roots=["/nonexistent-root"])
    with pytest.raises(ValueError): resolve_upload(str(p), s, allowed_ext=[".csv"])

def test_bad_ext_rejected(tmp_path):
    p = tmp_path / "x.exe"; p.write_text("x")
    s = Settings(allowed_roots=[str(tmp_path)])
    with pytest.raises(ValueError): resolve_upload(str(p), s, allowed_ext=[".csv"])

def test_missing_file_rejected(tmp_path):
    s = Settings(allowed_roots=[str(tmp_path)])
    with pytest.raises(ValueError): resolve_upload(str(tmp_path / "nope.csv"), s, allowed_ext=[".csv"])
```

- [ ] **Step 2: 跑确认 FAIL**

- [ ] **Step 3: 实现 files.py**

```python
import os

def resolve_upload(file_path, settings, allowed_ext=None, max_bytes=50_000_000):
    real = os.path.realpath(os.path.abspath(file_path))
    if not os.path.exists(real) or not os.path.isfile(real):
        raise ValueError(f"文件不存在或非普通文件: {file_path}")
    if settings.allowed_roots:
        ok = any(os.path.commonpath([real, os.path.realpath(r)]) == os.path.realpath(r)
                 for r in settings.allowed_roots)
        if not ok:
            raise ValueError(f"路径不在允许目录内（NEXUS_ALLOWED_ROOTS）: {file_path}")
    base = os.path.basename(real)
    if allowed_ext and os.path.splitext(base)[1].lower() not in allowed_ext:
        raise ValueError(f"不支持的扩展名: {base}（允许 {allowed_ext}）")
    size = os.path.getsize(real)
    if size > max_bytes:
        raise ValueError(f"文件过大: {size} > {max_bytes}")
    with open(real, "rb") as f:
        return base, f.read()
```

- [ ] **Step 4: 跑通 + commit** — `git commit -m "feat(mcp): 本地文件校验读取（allowed roots/扩展名/大小/保留 basename）"`

---

## Task 5: 读工具（project/ontology/runtime）+ server 装配 + stdio 入口

**Files:**
- Create: `mcp/ontotwin_mcp/tools/__init__.py`、`tools/project.py`、`tools/ontology.py`、`tools/runtime.py`、`mcp/ontotwin_mcp/server.py`
- Test: `mcp/tests/test_tools_read.py`

**Interfaces:**
- Consumes: `NexusClient`。
- Produces: `tools.<domain>.register(mcp, client)`；`tools.register_all(mcp, client)`；`server.build_server(client=None) -> FastMCP`；`server.main()`。
- `get_active_project` 归一化：`{dataset_id, dataset_name, project_id, writable, kind}`；仅 `is_active=true` 且非 demo 且 project 存在 → `writable=true`。

- [ ] **Step 1: 写失败测试（用 fake client，不起真 MCP）**

```python
from ontotwin_mcp.server import build_server

class FakeClient:
    def __init__(self, routes): self.routes = routes; self.calls = []
    def get(self, op, path, params=None): self.calls.append((op,path,params)); return self.routes[path]
    def post_json(self, op, path, json=None, timeout=None): self.calls.append((op,path,json)); return self.routes[path]

def _tool(mcp, name):
    # FastMCP 暴露已注册工具的方式以 pin 版本为准；实现者在此封装一个按名取 callable 的辅助
    return mcp._tool_callable(name)   # 见 Step 3 说明

def test_get_active_project_normalizes_demo():
    c = FakeClient({"/api/v2/ontology/datasets": [{"id":"demo","name":"D","is_active":True}]})
    mcp = build_server(c)
    res = _tool(mcp, "get_active_project")()
    assert res["kind"] == "demo" and res["writable"] is False and res["project_id"] is None

def test_get_active_project_writable():
    c = FakeClient({"/api/v2/ontology/datasets":[{"id":"p1","name":"厂","is_active":True}]})
    mcp = build_server(c)
    res = _tool(mcp, "get_active_project")()
    assert res["writable"] is True and res["project_id"] == "p1"

def test_list_instances_calls_endpoint():
    c = FakeClient({"/api/v2/instances":[{"id":"i1"}]})
    mcp = build_server(c)
    assert _tool(mcp, "list_instances")() == [{"id":"i1"}]
```

- [ ] **Step 2: 跑确认 FAIL**

- [ ] **Step 3: 实现**

`tools/project.py`（示范一个域，其余同构）：

```python
def register(mcp, client):
    @mcp.tool()
    def list_projects() -> list:
        """列出所有项目（数据集），含 is_active 标记。只读。"""
        return client.get("list_projects", "/api/v2/ontology/datasets")

    @mcp.tool()
    def get_active_project() -> dict:
        """返回当前激活项目的归一化视图 {dataset_id,dataset_name,project_id,writable,kind}。只读。
        writable=true 仅当激活的是真实项目（非内置 demo）。写工具前应先调它确认 writable。"""
        rows = client.get("get_active_project", "/api/v2/ontology/datasets")
        active = next((r for r in rows if r.get("is_active")), None)
        if not active:
            return {"dataset_id": None, "dataset_name": None, "project_id": None, "writable": False, "kind": "none"}
        is_demo = active.get("id") == "demo"
        return {"dataset_id": active.get("id"), "dataset_name": active.get("name"),
                "project_id": None if is_demo else active.get("id"),
                "writable": not is_demo, "kind": "demo" if is_demo else "project"}

    @mcp.tool()
    def activate_project(dataset_id: str, expected_current: str = "") -> dict:
        """激活指定数据集（改全局激活态，高危）。激活已有项目为只读，不覆盖其类型能力配置。"""
        return client.post_json("activate_project", "/api/v2/ontology/datasets/activate",
                                json={"dataset_id": dataset_id})

    @mcp.tool()
    def create_empty_project(name: str) -> dict:
        """新建空数据集（类型库需另经 import→publish→activate 填充）。固定不切换激活态。"""
        return client.post_json("create_empty_project", "/api/v2/ontology/datasets",
                                json={"name": name, "activate": False})
```

`tools/ontology.py` 读部分：`get_import_staging_graph`(GET /ontology/custom_graph)、`get_project_ontology_graph`(GET /ontology/datasets/{id}/graph，参数 dataset_id 可选→缺省用 get_active 的 dataset_id)、`list_object_types`(GET /ontology/types)、`get_object_type`(GET /ontology/types/{rid})。
`tools/runtime.py` 读部分：`list_instances`(GET /instances)、`get_instance_state`(GET /instances/{id})、`get_instance_snapshot`(GET /state/snapshot?id=)、`get_state_snapshots`(GET /state/snapshots?zone=)、`get_spatial_profile`(GET /spatial/profile)、`list_components`(GET /binding/components)、`list_roster`(GET /binding/roster)。

`server.py`：

```python
from mcp.server.fastmcp import FastMCP
from . import config
from .client import NexusClient
from .tools import register_all

def build_server(client=None) -> FastMCP:
    mcp = FastMCP("ontotwin")
    if client is None:
        client = NexusClient(config.load())
    register_all(mcp, client)
    return mcp

def main():
    build_server().run()   # 默认 stdio

if __name__ == "__main__":
    main()
```

`tools/__init__.py`：`register_all(mcp, client)` 依次调各域 `register`。

**关于 `_tool_callable`**：FastMCP 未必公开「按名取已注册工具 callable」的 API。实现者在 `tools/__init__.py` 或测试辅助里维护一个 `{name: func}` 注册表（各 `register` 把裸函数也存进 `mcp._registry` 或返回），供单测直接调裸函数（绕过 MCP 协议层）。若 pin 版本的 FastMCP 有官方内省 API 则用官方的。此决定在 Task 5 报告记录，后续写工具测试沿用。

- [ ] **Step 4: 跑通 + commit** — `git commit -m "feat(mcp): 读工具（project/ontology/runtime）+ FastMCP 装配 + stdio 入口"`

---

## Task 6: 本体写链工具（import→publish→activate）+ CAD 工具

**Files:**
- Modify: `mcp/ontotwin_mcp/tools/ontology.py`；Create `mcp/ontotwin_mcp/tools/cad.py`
- Test: `mcp/tests/test_tools_write.py`

**Interfaces:**
- Produces：`import_ontology_csv(file_paths: list[str])`、`publish_ontology_dataset(name)`、`parse_cad_dxf(file_path, wall_height=0, wall_thickness=0)`、`calibrate_coordinates(anchors)`、`save_components(payload, expected_project_id)`。

- [ ] **Step 1: 写失败测试**

```python
def test_import_csv_multipart_basenames(monkeypatch, tmp_path):
    from ontotwin_mcp.server import build_server
    files=[]
    class C:
        def post_multipart(self, op, path, files_, data=None):
            files.extend(files_); return {"status":"ok"}
        def get(self,*a,**k): return []
        def post_json(self,*a,**k): return {}
    for n in ("objectdef.csv","linkdef.csv"):
        (tmp_path/n).write_bytes(b"x")
    import os; monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", str(tmp_path))
    mcp = build_server(C())
    _tool(mcp,"import_ontology_csv")([str(tmp_path/"objectdef.csv"), str(tmp_path/"linkdef.csv")])
    assert {f[0] for f in files} == {"objectdef.csv","linkdef.csv"}  # 保留 basename 作 field/filename

def test_save_components_passes_expected(monkeypatch):
    sent={}
    class C:
        def post_json(self, op, path, json=None, timeout=None): sent.update(json or {}); return {"status":"ok"}
        def get(self,*a,**k): return []
    from ontotwin_mcp.server import build_server
    mcp = build_server(C())
    _tool(mcp,"save_components")({"components":[]}, expected_project_id="p1")
    assert sent.get("expected_project_id") == "p1"
```

- [ ] **Step 2–4: FAIL → 实现 → 通过**

`import_ontology_csv`：对每个 path 调 `files.resolve_upload(path, settings, allowed_ext=[".csv"])` 得 `(basename, content)`；后端按 filename 识别 6 表，故 **field 名与 filename 都用 basename**：`client.post_multipart("import_ontology_csv","/api/v2/ontology/import_csv", files=[(base, base, content) for ...])`。
`publish_ontology_dataset(name)` → post_json `/ontology/publish {name}`。
`parse_cad_dxf(file_path,...)` → resolve_upload allowed_ext=[".dxf"]，post_multipart `/cad/parse` files=[("file","x.dxf",content)] data={"wall_height","wall_thickness"}，超时用 `timeout_cadparse`（post_multipart 里对该 operation 用 cadparse 超时——实现者在 client.post_multipart 加可选 timeout 参数）。
`calibrate_coordinates(anchors)` → post_json `/coord/calibrate {anchors}`（compute，无 expected）。
`save_components(payload, expected_project_id)` → post_json `/coord/save_components {**payload, expected_project_id}`（persist-write）。写工具 description 首句写「本操作会修改当前激活项目」。

- [ ] **Step 5: commit** — `git commit -m "feat(mcp): 本体写链（import→publish→activate）+ CAD 工具（multipart/expected）"`

---

## Task 7: 绑定链工具 + 运行态写工具

**Files:**
- Modify: `mcp/ontotwin_mcp/tools/binding.py`（新建）、`tools/runtime.py`
- Test: `mcp/tests/test_tools_write.py`（追加）

**Interfaces:**
- Produces：`upload_roster(file_path, expected_project_id)`、`automatch_bindings()`、`bind_instance(component_id, instance_id, expected_project_id)`、`bind_instances_batch(pairs, expected_project_id)`、`unbind_instance(component_id, expected_project_id)`、`mint_instances(dry_run=False, expected_project_id="")`、`set_instance_state(instance_id, patch, expected_project_id)`。

- [ ] **Step 1: 写失败测试**

```python
def test_upload_roster_expected_as_form_field():
    seen={}
    class C:
        def post_multipart(self, op, path, files, data=None): seen["data"]=data; return {"status":"ok"}
        def get(self,*a,**k): return []
    from ontotwin_mcp.server import build_server
    import os; os.environ["NEXUS_ALLOWED_ROOTS"]=""   # 本测试用 monkeypatch resolve_upload 更稳，见实现说明
    # 实现者：用 monkeypatch 替换 files.resolve_upload 返回 ("roster.csv", b"x")
    ...

def test_mint_dry_run_passthrough():
    sent={}
    class C:
        def post_json(self, op, path, json=None, timeout=None): sent.update(json or {}); return {"minted":0,"to_create":["a"],"to_update":[]}
        def get(self,*a,**k): return []
    from ontotwin_mcp.server import build_server
    mcp = build_server(C())
    r = _tool(mcp,"mint_instances")(dry_run=True, expected_project_id="p1")
    assert sent == {"dry_run": True, "expected_project_id": "p1"} and r["to_create"]==["a"]
```

- [ ] **Step 2–4: FAIL → 实现 → 通过**

- `upload_roster(file_path, expected_project_id)`：resolve_upload allowed_ext=[".csv"]；post_multipart `/binding/roster/upload` files=[("file","roster.csv",content)] **data={"expected_project_id": expected_project_id}**（form field，spec §14.2）。
- `automatch_bindings()` → post_json `/binding/automatch`（compute，只出建议）。
- `bind_instance(...)`/`unbind_instance(...)` → post_json，body 含 `expected_project_id`。
- `bind_instances_batch(pairs, expected_project_id)` → post_json `/binding/bind_batch {pairs, expected_project_id}`，透传返回 `{bound, failed}`。
- `mint_instances(dry_run, expected_project_id)` → post_json `/binding/mint {dry_run, expected_project_id}`（省略空 expected：仅当非空才放进 body）。
- `set_instance_state(instance_id, patch, expected_project_id)` → post_json `/state/override {instance_id, patch, expected_project_id}`。
- 所有 persist-write description 首句「本操作会修改当前激活项目」。空 `expected_project_id` 时不放进 body（保持后端「缺省=旧行为」）。

- [ ] **Step 5: commit** — `git commit -m "feat(mcp): 绑定链 + 运行态写工具（expected 透传、mint dry_run、bind_batch）"`

---

## Task 8: MCP stdio 协议测试 + 只读集成冒烟（真部署，env 开关）

**Files:**
- Test: `mcp/tests/test_stdio.py`、`mcp/tests/test_smoke.py`

**Interfaces:**
- Consumes: 完整 server。

- [ ] **Step 1: 写 stdio 协议测试**

用官方 mcp client（或子进程 + JSON-RPC over stdio）走 `initialize` → `tools/list` → 断言 27 个工具都在、名字/描述正确 → 挑一个只读工具 `tools/call`（后端用 MockTransport 注入 NexusClient，或指向一个 Flask test-client 起的临时端口）。**实现者按 pin 的 mcp SDK 的测试工具/`ClientSession` 写**；若 SDK 提供 in-memory 传输则用它，否则起子进程。

```python
# 骨架（具体 API 以 pin 版本为准）
import pytest
@pytest.mark.asyncio
async def test_tools_list_has_all(mcp_stdio_session):
    tools = await mcp_stdio_session.list_tools()
    names = {t.name for t in tools.tools}
    assert {"get_active_project","mint_instances","save_components","list_instances"} <= names
    assert len(names) >= 27
```

- [ ] **Step 2: 写只读冒烟（默认 skip，env `NEXUS_SMOKE=1` + 可达 88.66 才跑）**

```python
import os, pytest
pytestmark = pytest.mark.skipif(os.environ.get("NEXUS_SMOKE") != "1", reason="需 NEXUS_SMOKE=1 + 可达后端")

def test_smoke_readonly():
    from ontotwin_mcp.config import load
    from ontotwin_mcp.client import NexusClient
    c = NexusClient(load())
    assert isinstance(c.get("list_instances", "/api/v2/instances"), list)
```

- [ ] **Step 3: 跑（协议测试必过；冒烟默认 skip）+ commit** — `git commit -m "test(mcp): stdio 协议测试 + 只读集成冒烟（env 开关）"`

---

## Task 9: skill 文件 + README

**Files:**
- Create: `mcp/skills/ontotwin-nexus/SKILL.md`、`mcp/README.md`

**Interfaces:** 无代码接口；交付文档。

- [ ] **Step 1: 写 SKILL.md**（含 frontmatter description + 四段流水线心智图 + §8 三个范例 + 黄金铁律：写前先 get_active_project 且 writable、写工具必带 expected_project_id、术语链、mint 先 dry_run。内容照 spec §4、§8 落地）

- [ ] **Step 2: 写 README.md**：
  - Claude Code 注册：`claude mcp add ontotwin -- python -m ontotwin_mcp`（附 env 示例 `NEXUS_BASE_URL`/`NEXUS_ALLOWED_ROOTS`）。
  - Cursor：`~/.cursor/mcp.json` 片段。
  - 审批配置：**分别记录** Claude Code / Cursor 如何对 persist-write 工具要求人工审批（spec §5.3——写清「兼容客户端可提供审批体验，非协议保证」，并给各自实测的开关位置）。
  - Skill 安装：`ontotwin-nexus/` 拷进 `~/.claude/skills/`。

- [ ] **Step 3: commit** — `git commit -m "docs(mcp): ontotwin-nexus skill 编排 playbook + Claude Code/Cursor 注册与审批 README"`

---

## Task 10: Claude Code 端到端联调 + 二期只读工具 + 交付

**Files:**
- Modify: `tools/runtime.py`/新建 `tools/phase2.py`（二期只读）
- Test: `mcp/tests/test_tools_read.py`（追加二期）
- Create: `mcp/CHANGELOG.md` 或在 README 加「已知边界」

**Interfaces:**
- Produces（二期只读，spec §3.3）：`get_instance_transform(instance_id)`、`get_ue_binding_status()`、`list_spatial_frames()`。（写类二期工具 `promote_model_binding`/transform PUT/spatial 写**不在本轮**。）

- [ ] **Step 1: 加二期只读工具 + 测试**（同 Task 5 读工具模式：GET `/instances/{id}/transform`、`/ue/binding_status`、`/spatial/frames`）
- [ ] **Step 2: Claude Code 端到端**：在本机 `claude mcp add` 注册指向 88.66，人工走 spec §8 例 1（只读查询）与例 3（运维改状态，观察写前 get_active_project + 审批）。把实测结果记进 README「验证记录」。**此步为人工验收，不是自动测试**——在报告描述实际命中的工具序列与结果。
- [ ] **Step 3: 全量 `cd mcp && python -m pytest -q` 通过 + commit** — `git commit -m "feat(mcp): 二期只读工具 + 交付（Claude Code 端到端验证记录）"`

---

## Self-Review（作者自查）

**1. Spec 覆盖：** §2 架构→Task 5 server；§3.1 分级→各写工具 description；§3.2 27 工具→Task 5（读）/6/7（写）逐项；§3.3 二期只读→Task 10；§5.4 get_active_project 归一化→Task 5；§6 错误映射→Task 2；§7 文件参数/allowed roots/basename/form-field expected→Task 4/6/7；§8 范例→Task 9 skill；§9 repo 布局→文件结构；§10 配置/分级超时/非幂等不重试→Task 1/3；§12 依赖隔离→Task 1；create_empty_project activate=false→Task 5。M0 的 expected/dry_run 由后端提供，MCP 仅透传（Task 6/7）。
**2. 占位符扫描：** 无 TBD。两处**显式标注依存 pin 版本 FastMCP API**（`_tool_callable` 内省、stdio 测试传输）——给了确定的回退方案（自建 name→func 注册表 / 子进程），非占位。文件/错误/client/config/读写工具均有真实代码与测试。
**3. 类型一致：** `NexusClient.get/post_json/post_multipart`、`NexusError(code,http_status,operation,backend_error,retryable,hint)`、`resolve_upload(file_path,settings,allowed_ext,max_bytes)->(basename,bytes)`、`get_active_project()->{dataset_id,dataset_name,project_id,writable,kind}`、`mint_instances(dry_run,expected_project_id)` 跨任务签名一致。

> 依赖前置：本计划假定 M0 后端分支（dry_run/expected_project_id/bind_batch/save_component_bundle/roster form-field）已合并并部署到 `NEXUS_BASE_URL` 指向的后端；否则写工具的 dry_run/expected/409 行为在真后端上不成立（只读工具不受影响）。**执行本计划前确认 M0 已上线到目标后端。**
