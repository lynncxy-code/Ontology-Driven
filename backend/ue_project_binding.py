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
from contextlib import nullcontext

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


_TRUSTED_INTERNAL_CLIENTS = ("Web", "MCP")


def is_browser_request(request):
    """无 UE-ID 时判断是否是"内部可信客户端"（放行 web-bypass）。
    浏览器（UA 含 Mozilla）或 X-OntoTwin-Client 头为已知值（Web/MCP）都算。
    """
    ua = request.headers.get("User-Agent", "")
    client = (request.headers.get("X-OntoTwin-Client") or "").strip()
    return "Mozilla" in ua or client in _TRUSTED_INTERNAL_CLIENTS


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
    锁序：_index_lock（外）→ store._lock（内），全流程原子；
    重要节点做失败回滚，避免"清了旧但没写新"造成索引与真源不一致。
    """
    if not ue_project_id:
        return False, {"error": "ue_project_id is required"}

    store_lock = getattr(store, "_lock", None) or nullcontext()
    with _index_lock:
        with store_lock:
            # 在锁内重读激活态：避免另一线程正好切换激活导致我们写错项目
            active = store.get_active() if hasattr(store, "get_active") else None
            if not active:
                return False, {"error": "no active project"}
            active_pid = active.get("id")

            existing_pid = _ue_index.get(str(ue_project_id))
            if existing_pid and existing_pid != active_pid and not force:
                return False, {
                    "error": "ue_project_already_bound",
                    "message": f"该 UE 已绑到另一项目 {existing_pid}；先在那边解绑或加 force=1 迁移",
                    "bound_to": existing_pid,
                }

            # force 迁移：先快照旧项目绑定用于回滚；再清空旧项目绑定（失败则终止）
            old_snapshot = None
            if existing_pid and existing_pid != active_pid and force:
                try:
                    old_proj = store.read_project(existing_pid) if hasattr(store, "read_project") else None
                    if isinstance(old_proj, dict):
                        old_ds = old_proj.get("dataset") or {}
                        old_snapshot = (
                            existing_pid,
                            str(old_ds.get("bound_ue_project_id") or ""),
                            str(old_ds.get("bound_ue_project_name") or ""),
                        )
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
                # 新绑定写失败 → 尽力把旧绑定恢复回去，避免真源丢失
                if old_snapshot is not None:
                    try:
                        _restore_binding_on_project(store, *old_snapshot)
                    except Exception as re:
                        print(f"[ue_binding] 回滚旧项目绑定失败 pid={old_snapshot[0]}: {re}")
                return False, {"error": "write_binding_failed", "message": str(e)}

            # 落盘全部成功后才改内存索引，保证 DB/文件与索引一致
            if existing_pid and existing_pid != active_pid and force:
                for k in [k for k, v in _ue_index.items() if v == existing_pid]:
                    _ue_index.pop(k, None)
            _ue_index[str(ue_project_id)] = str(active_pid)

    return True, {"project_id": active_pid, "dataset": ds}


def _clear_binding_on_project(store, pid):
    """清空指定项目 dataset 的 bound_ue_project_id/name。
    失败一律抛错——bind_active_dataset 依赖此处的异常来做回滚决策。"""
    if not pid:
        raise ValueError("pid required")
    if not hasattr(store, "read_project") or not hasattr(store, "write_project"):
        raise RuntimeError("store lacks read_project/write_project")
    proj = store.read_project(pid)
    if not isinstance(proj, dict):
        raise ValueError(f"project not readable: {pid}")
    ds = proj.get("dataset") or {}
    ds = dict(ds) if isinstance(ds, dict) else {}
    ds["bound_ue_project_id"] = ""
    ds["bound_ue_project_name"] = ""
    proj["dataset"] = ds
    store.write_project(pid, proj)


def _restore_binding_on_project(store, pid, ue_id, ue_name):
    """回滚：把 pid 项目的 dataset 绑定重设为 (ue_id, ue_name)。best-effort。"""
    if not pid or not hasattr(store, "read_project") or not hasattr(store, "write_project"):
        return
    proj = store.read_project(pid)
    if not isinstance(proj, dict):
        return
    ds = proj.get("dataset") or {}
    ds = dict(ds) if isinstance(ds, dict) else {}
    ds["bound_ue_project_id"] = ue_id or ""
    ds["bound_ue_project_name"] = ue_name or ""
    proj["dataset"] = ds
    store.write_project(pid, proj)
