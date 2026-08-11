"""
UE project binding helpers (OntoTwin 3.5)

一个数据项目（dataset/project）可以绑定到一个 UE 项目身份。UE 请求携带
X-OntoTwin-UE-Project-Id / X-OntoTwin-UE-Project-Name。

新模型（3.5）：
- 服务器维护 {ue_id -> pid} 内存索引（启动扫盘建、bind/unbind 时增删）
- 一个 UE-ID 只能绑到一个项目（互斥约束）
- UE 请求 → resolve_project_for_ue(store, request) → 得到它绑的 project_id →
  从那个项目读写，不再依赖 store._current；因此切换激活不影响老 UE
- Web 请求（无 UE-ID 头 + 浏览器 UA）→ 放行，继续走 _current

向后兼容：
- 保留 request_ue_project / active_dataset / bind_active_dataset /
  check_request_matches_active 名称与语义（旧调用方无需改动）
- bind_active_dataset 现在会做互斥检查（force=True 可强制迁移）
- check_request_matches_active 现在放行"绑到任意项目"的 UE 请求（不再要求匹配激活）
"""

import threading

UE_ID_HEADER = "X-OntoTwin-UE-Project-Id"
UE_NAME_HEADER = "X-OntoTwin-UE-Project-Name"


# ═══════════════════════════════════════════════════════════════
# 请求解析（不变）
# ═══════════════════════════════════════════════════════════════

def request_ue_project(request):
    data = request.get_json(silent=True) or {}
    return {
        "id": (request.headers.get(UE_ID_HEADER) or data.get("ue_project_id") or request.args.get("ue_project_id") or "").strip(),
        "name": (request.headers.get(UE_NAME_HEADER) or data.get("ue_project_name") or request.args.get("ue_project_name") or "").strip(),
    }


def is_browser_request(request):
    ua = request.headers.get("User-Agent", "")
    return "Mozilla" in ua or request.headers.get("X-OntoTwin-Client") == "Web"


# ═══════════════════════════════════════════════════════════════
# 项目侧读取（沿用旧函数：从 active 数据集读绑定信息）
# ═══════════════════════════════════════════════════════════════

def active_dataset(store):
    ds = store.get_active_dataset() if hasattr(store, "get_active_dataset") else None
    if isinstance(ds, dict):
        return ds
    active = store.get_active() if hasattr(store, "get_active") else None
    if isinstance(active, dict) and isinstance(active.get("dataset"), dict):
        return active["dataset"]
    return {}


def active_binding(store):
    ds = active_dataset(store)
    return {
        "id": (ds.get("bound_ue_project_id") or "").strip(),
        "name": (ds.get("bound_ue_project_name") or "").strip(),
    }


# ═══════════════════════════════════════════════════════════════
# UE-ID → project_id 索引（3.5 新增）
# ═══════════════════════════════════════════════════════════════

_index_lock = threading.RLock()
_ue_index = {}  # ue_id -> pid


def rebuild_index(store):
    """启动或大规模变更后调用：扫全部项目文件重建索引。"""
    new_index = {}
    if hasattr(store, "list_projects"):
        for meta in store.list_projects() or []:
            pid = meta.get("id") if isinstance(meta, dict) else None
            if not pid:
                continue
            proj = None
            if hasattr(store, "read_project"):
                try:
                    proj = store.read_project(pid)
                except Exception:
                    proj = None
            if not isinstance(proj, dict):
                continue
            ds = proj.get("dataset") or {}
            ue_id = (ds.get("bound_ue_project_id") or "").strip() if isinstance(ds, dict) else ""
            if ue_id:
                new_index[ue_id] = pid
    with _index_lock:
        _ue_index.clear()
        _ue_index.update(new_index)
    return dict(new_index)


def index_set(ue_id, pid):
    if not ue_id or not pid:
        return
    with _index_lock:
        _ue_index[str(ue_id)] = str(pid)


def index_unset(ue_id):
    if not ue_id:
        return
    with _index_lock:
        _ue_index.pop(str(ue_id), None)


def index_forget_project(pid):
    """删项目或清空绑定字段时调用：把指向该 pid 的所有 UE-ID 从索引删。"""
    if not pid:
        return
    with _index_lock:
        for ue_id in [k for k, v in _ue_index.items() if v == pid]:
            _ue_index.pop(ue_id, None)


def index_lookup(ue_id):
    if not ue_id:
        return None
    with _index_lock:
        return _ue_index.get(str(ue_id))


def index_snapshot():
    with _index_lock:
        return dict(_ue_index)


# ═══════════════════════════════════════════════════════════════
# Resolver：UE 请求 → 应该服务哪个项目
# ═══════════════════════════════════════════════════════════════

def resolve_project_for_ue(store, request):
    """
    返回 (pid, ok, info)：
      pid=None,  ok=True  → Web 请求（无 UE-ID + 浏览器 UA），调用方走 _current
      pid="<id>", ok=True → UE 请求，服务该项目
      pid=None,  ok=False → 拒绝，info 含 error/message
    """
    incoming = request_ue_project(request)
    ue_id = incoming.get("id") or ""

    if not ue_id:
        if is_browser_request(request):
            return None, True, {"mode": "web-bypass"}
        return None, False, {
            "error": "ue_project_required",
            "message": "UE 请求缺少 X-OntoTwin-UE-Project-Id 头",
        }

    pid = index_lookup(ue_id)
    if pid is None:
        # 错误码保留旧名 ue_project_mismatch 以兼容 UE 插件里的硬编码
        # （TwinSceneManager.cpp 里根据此码走"save disabled"专属提示）
        return None, False, {
            "error": "ue_project_mismatch",
            "message": "该 UE 未绑定到任何项目；请在 Web UI 激活目标项目后在 UE 中执行绑定",
            "request_ue_project_id": ue_id,
            "request_ue_project_name": incoming.get("name"),
        }

    return pid, True, {
        "mode": "matched",
        "project_id": pid,
        "request_ue_project_id": ue_id,
        "request_ue_project_name": incoming.get("name"),
    }


# ═══════════════════════════════════════════════════════════════
# 兼容：旧鉴权入口（新语义 = 绑到任意项目即放行）
# ═══════════════════════════════════════════════════════════════

def check_request_matches_active(store, request):
    """
    3.5 起新语义：只要 UE 已绑到"某个"项目就放行（Web 请求也放行）。
    切激活不再影响老 UE。返回 (ok, info)。info 里带 project_id 供调用方按需路由。
    """
    pid, ok, info = resolve_project_for_ue(store, request)
    return bool(ok), dict(info)


# ═══════════════════════════════════════════════════════════════
# 绑定：加互斥约束 + 联动索引
# ═══════════════════════════════════════════════════════════════

def bind_active_dataset(store, ue_project_id, ue_project_name, force=False):
    """把当前激活项目绑到指定 UE-ID。
    互斥：同一 UE-ID 只能绑一个项目；已绑他处需 force=True 才能迁移。
    整个流程持 _index_lock：检查/清旧/写新/更新索引原子。
    """
    if not ue_project_id:
        return False, {"error": "ue_project_id is required"}
    active = store.get_active() if hasattr(store, "get_active") else None
    if not active:
        return False, {"error": "no active project"}
    active_pid = active.get("id")

    with _index_lock:
        existing_pid = _ue_index.get(str(ue_project_id))
        if existing_pid and existing_pid != active_pid and not force:
            return False, {
                "error": "ue_project_already_bound",
                "message": f"该 UE 已绑到另一项目 {existing_pid}；先在那边解绑或加 force=1 迁移",
                "bound_to": existing_pid,
            }

        # 若强制迁移：先清旧项目的 dataset 绑定字段；异常则中止不动索引
        if existing_pid and existing_pid != active_pid and force:
            try:
                _clear_binding_on_project(store, existing_pid)
            except Exception as e:
                return False, {
                    "error": "clear_previous_binding_failed",
                    "message": f"清理旧项目 {existing_pid} 的绑定失败：{e}",
                    "bound_to": existing_pid,
                }

        ds = active_dataset(store)
        if not ds:
            ds = {
                "id": active.get("id"),
                "name": active.get("name"),
                "created_at": active.get("created_at"),
                "node_count": len(active.get("object_types") or {}),
                "link_count": 0,
                "graph_data": {"nodes": [], "links": [], "categories": []},
            }
        ds = dict(ds)
        ds["bound_ue_project_id"] = ue_project_id
        ds["bound_ue_project_name"] = ue_project_name or ue_project_id
        try:
            if hasattr(store, "set_dataset"):
                store.set_dataset(ds)
            else:
                active["dataset"] = ds
        except Exception as e:
            return False, {"error": "write_binding_failed", "message": str(e)}

        # 所有落盘成功后再改内存索引，保证 DB/文件与索引一致
        if existing_pid and existing_pid != active_pid and force:
            _ue_index.pop(existing_pid, None)   # 冗余清理（防止 pid==ue_id 的极端命名）
            for k in [k for k, v in _ue_index.items() if v == existing_pid]:
                _ue_index.pop(k, None)
        _ue_index[str(ue_project_id)] = str(active_pid)

    return True, {"project_id": active_pid, "dataset": ds}


def _clear_binding_on_project(store, pid):
    """把某项目 dataset 的 bound_ue_project_id/name 清空（force 迁移时用）。"""
    if not pid or not hasattr(store, "read_project") or not hasattr(store, "write_project"):
        return
    try:
        proj = store.read_project(pid)
    except Exception:
        proj = None
    if not isinstance(proj, dict):
        return
    ds = proj.get("dataset") or {}
    if not isinstance(ds, dict):
        return
    ds = dict(ds)
    ds["bound_ue_project_id"] = ""
    ds["bound_ue_project_name"] = ""
    proj["dataset"] = ds
    try:
        store.write_project(pid, proj)
    except Exception as e:
        print(f"[ue_binding] 清理项目 {pid} 绑定失败: {e}")
