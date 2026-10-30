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

2026-10 连接稳定性修订：
- 索引只读 list_projects() 元数据重建；未命中时节流懒重建（自愈：后端先于
  PG 就绪启动、离线工具/导入直接改库后，不必重启 backend）
- 未绑定的 UE 请求在错误体里带 binding_state="unbound"（错误码仍是
  ue_project_mismatch，兼容旧插件）
- 绑定不再静默抢占：目标项目已绑其他 UE-ID 时返回 project_already_bound，
  需要 force 才覆盖
- bind 支持 target_project_id：UE 可按上次成功绑定的项目重绑，不依赖激活态
"""

import datetime
import os
import threading
import time
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
        "scene_id": (request.headers.get("X-OntoTwin-UE-Scene-Id") or data.get("scene_id") or request.args.get("scene_id") or request.args.get("scene") or "").strip(),
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
# 同一 UE-ID 出现在多个项目上的冲突（ue_id -> [pid...]），供诊断接口展示。
_ue_conflicts = {}
# 懒重建节流：索引未命中时最多每 _LAZY_REBUILD_INTERVAL 秒回源重建一次。
_LAZY_REBUILD_INTERVAL = 5.0
_last_rebuild = {"at": 0.0, "ok": False, "error": "", "attempted_at": 0.0}

# UE 身份发现是临时状态，不写入项目数据。它只用于网页提供“最近发现的 UE”
# 选择项；真正的项目绑定仍由显式确认操作持久化。请求停止一段时间后自动过期。
_DISCOVERY_TTL_SECONDS = 10 * 60
_DISCOVERY_MAX_ENTRIES = 256
_discovered_lock = threading.RLock()
_discovered_ue = {}  # ue_id -> {name, context, last_seen_epoch}


def observe_ue_project(request):
    """记录一次带 UE 身份的请求，供网页显示最近发现的工程。"""
    incoming = request_ue_project(request)
    ue_id = incoming.get("id") or ""
    if not ue_id:
        return None
    now = time.time()
    context = (request.headers.get("X-OntoTwin-UE-Context") or "").strip().lower()
    with _discovered_lock:
        for stale_id, value in list(_discovered_ue.items()):
            if now - value['last_seen_epoch'] > _DISCOVERY_TTL_SECONDS:
                _discovered_ue.pop(stale_id, None)
        previous = _discovered_ue.get(ue_id) or {}
        if ue_id not in _discovered_ue and len(_discovered_ue) >= _DISCOVERY_MAX_ENTRIES:
            oldest = min(_discovered_ue, key=lambda key: _discovered_ue[key]['last_seen_epoch'])
            _discovered_ue.pop(oldest)
        _discovered_ue[ue_id] = {
            "ue_project_id": ue_id,
            "ue_project_name": incoming.get("name") or ue_id,
            "scene_id": (incoming.get("scene_id") or "").strip(),
            "context": context or previous.get('context') or "unknown",
            "last_seen_epoch": now,
        }
    return ue_id


def ue_scene_online(ue_id, scene_key, max_age_seconds=30):
    """UE 工程最近一次心跳上报的场景是否正好是 scene_key（即该关卡当前在线）。

    一个 UE 工程可以绑定多个关卡（每个关卡对应一个数据集）；工程在线不代表
    所有关卡在线，只有 UE 当前打开的那张地图才算在线。
    """
    if not ue_id or not scene_key:
        return False
    with _discovered_lock:
        record = _discovered_ue.get(ue_id)
        if record is None:
            return False
        last_seen = record.get("last_seen_epoch") or 0
        current_scene = (record.get("scene_id") or "").strip()
    if time.time() - last_seen > max_age_seconds:
        return False
    return current_scene == (scene_key or "").strip()


def discovered_ue_projects(store, max_age_seconds=_DISCOVERY_TTL_SECONDS):
    """Return recent UE identities plus their current persistent binding."""
    now = time.time()
    with _discovered_lock:
        for ue_id, value in list(_discovered_ue.items()):
            if now - float(value.get("last_seen_epoch") or 0) > max_age_seconds:
                _discovered_ue.pop(ue_id, None)
        discovered = [dict(value) for value in _discovered_ue.values()]

    # The index is rebuilt on startup and after binding changes. A throttled
    # refresh here also makes the picker correct when another process changed
    # the persistent project store.
    try_rebuild_index(store)
    projects = {}
    try:
        projects = {
            str(meta.get("id")): meta
            for meta in (store.list_projects() or [])
            if isinstance(meta, dict) and meta.get("id")
        }
    except Exception:
        projects = {}

    result = []
    for value in discovered:
        ue_id = value["ue_project_id"]
        pid = index_lookup(ue_id)
        if pid and str(pid) not in projects:
            pid = None
        meta = projects.get(str(pid)) if pid else None
        seen = float(value.get("last_seen_epoch") or now)
        result.append({
            "ue_project_id": ue_id,
            "ue_project_name": value.get("ue_project_name") or ue_id,
            "scene_id": value.get("scene_id") or "",
            "context": value.get("context") or "unknown",
            "last_seen_at": datetime.datetime.fromtimestamp(
                seen, datetime.timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "last_seen_seconds": max(0, int(now - seen)),
            "online": now - seen <= 10,
            "binding_state": "bound" if pid else "unbound",
            "project_id": str(pid) if pid else "",
            "project_name": (meta or {}).get("name") or "",
            "is_active": bool(pid and hasattr(store, "get_active_id") and pid == store.get_active_id()),
        })
    result.sort(key=lambda item: (not item["online"], item["last_seen_seconds"], item["ue_project_name"].casefold()))
    return result


def _binding_id_from_meta(store, meta):
    """优先用 list_projects() 自带的绑定字段；旧/自定义 store 没有时再读整份项目。"""
    if "bound_ue_project_id" in meta:
        return str(meta.get("bound_ue_project_id") or "").strip()
    if not hasattr(store, "read_project"):
        return ""
    proj = store.read_project(meta.get("id"))
    ds = (proj or {}).get("dataset") if isinstance(proj, dict) else None
    return str((ds or {}).get("bound_ue_project_id") or "").strip() if isinstance(ds, dict) else ""


def rebuild_index(store):
    """启动或大规模变更后调用：从持久层重建 UE-ID→pid 索引。

    只读 list_projects() 的元数据（PG 一条 SQL / JSON 逐文件），不再逐项目
    read_project 重组全部实例，因此可以放在请求路径上做懒重建。
    list_projects() 抛错（例如 PG 尚未就绪）时向上抛出，且不清空现有索引。
    同一 UE-ID 绑在多个项目上时：优先激活项目，否则取 id 字典序最小者，
    并把冲突记入 _ue_conflicts（诊断接口可见）。
    """
    metas = store.list_projects() if hasattr(store, "list_projects") else []
    active_id = store.get_active_id() if hasattr(store, "get_active_id") else None
    seen = {}
    for meta in metas or []:
        pid = meta.get("id") if isinstance(meta, dict) else None
        if not pid:
            continue
        try:
            ue_id = _binding_id_from_meta(store, meta)
        except Exception:
            ue_id = ""
        if ue_id:
            seen.setdefault(ue_id, []).append(str(pid))

    new_index, conflicts = {}, {}
    for ue_id, pids in seen.items():
        pids = sorted(set(pids))
        if len(pids) > 1:
            conflicts[ue_id] = pids
        new_index[ue_id] = active_id if active_id in pids else pids[0]

    with _index_lock:
        _ue_index.clear()
        _ue_index.update(new_index)
        _ue_conflicts.clear()
        _ue_conflicts.update(conflicts)
        now = time.monotonic()
        _last_rebuild.update(at=now, attempted_at=now, ok=True, error="")
    if conflicts:
        print(f"[ue_binding] 同一 UE-ID 绑定到多个项目（已按激活/字典序取一个）：{conflicts}")
    return dict(new_index)


def try_rebuild_index(store, force=False):
    """节流 + 吞异常的重建入口，供请求路径调用。返回是否成功执行了重建。"""
    with _index_lock:
        now = time.monotonic()
        if not force and now - _last_rebuild["attempted_at"] < _LAZY_REBUILD_INTERVAL:
            return False
        _last_rebuild["attempted_at"] = now
    try:
        rebuild_index(store)
        return True
    except Exception as exc:
        with _index_lock:
            _last_rebuild.update(ok=False, error=str(exc))
        print(f"[ue_binding] 索引重建失败: {exc}")
        return False


def index_state():
    """诊断用：索引规模、冲突与最近一次重建结果。"""
    with _index_lock:
        return {
            "size": len(_ue_index),
            "conflicts": {k: list(v) for k, v in _ue_conflicts.items()},
            "last_rebuild_ok": bool(_last_rebuild["ok"]),
            "last_rebuild_error": _last_rebuild["error"],
            "seconds_since_rebuild": (
                round(time.monotonic() - _last_rebuild["at"], 1) if _last_rebuild["at"] else None
            ),
        }


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


def lookup_with_heal(store, ue_id):
    """索引查找；未命中时节流回源重建一次再查（索引自愈）。"""
    pid = index_lookup(ue_id)
    if pid is None and ue_id and store is not None:
        if try_rebuild_index(store):
            pid = index_lookup(ue_id)
    return pid


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
    # Every UE request is also a lightweight discovery heartbeat. This keeps
    # the web picker useful without introducing a second registration protocol.
    observe_ue_project(request)
    ue_id = incoming.get("id") or ""

    # 4.8 explicit context.  The Flask request guard has already checked the
    # scene-level binding (or browser membership); keeping the resolver aware
    # of the same header lets all legacy handlers use their existing code path
    # without looking at process-global active state.
    explicit_pid = (
        request.headers.get("X-OntoTwin-Project-Id")
        or request.args.get("project_id")
        or (request.get_json(silent=True) or {}).get("project_id")
        or ""
    ).strip()
    if explicit_pid and ue_id and getattr(request, "path", "") != "/api/v2/ue/binding_status":
        return explicit_pid, True, {
            "mode": "explicit",
            "binding_state": "bound",
            "project_id": explicit_pid,
            "request_ue_project_id": ue_id,
            "request_ue_project_name": incoming.get("name"),
            "scene_id": incoming.get("scene_id") or "",
        }

    # Scene-level binding is authoritative for 4.8.  It is queried directly so
    # a UE project with two levels can resolve two different projects even
    # though the legacy dataset field can store only one UE id.
    scene_id = incoming.get("scene_id") or ""
    pg_mode = os.environ.get("ONTOTWIN_STORE", "json").lower() == "pg"
    if ue_id and scene_id:
        try:
            from db import pg
            with pg.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT b.project_id FROM project_scene_binding b
                            JOIN ue_project u ON u.ue_project_id=b.ue_project_id
                            JOIN ue_scene s ON s.scene_id=b.scene_id
                           WHERE (u.ue_project_id=%s OR u.stable_key=%s)
                             AND (s.scene_id=%s OR s.stable_key=%s)
                             AND b.status='active'""",
                        (ue_id, ue_id, scene_id, scene_id),
                    )
                    row = cur.fetchone()
            if row:
                return str(row[0]), True, {
                    # 兼容旧 UE 插件：它只认 "matched" / "unbound"；场景级绑定
                    # 的额外信息已由 binding_state / scene_id / project_id 表达。
                    "mode": "matched",
                    "binding_state": "bound",
                    "project_id": str(row[0]),
                    "request_ue_project_id": ue_id,
                    "request_ue_project_name": incoming.get("name"),
                    "scene_id": scene_id,
                }
        except Exception:
            if pg_mode:
                return None, False, {"error": "binding_storage_unavailable", "message": "无法核对关卡绑定，已停止读取数据"}

    if pg_mode and ue_id:
        return None, False, {"binding_state": "unbound", "message": "该关卡未绑定，请在网页数据集卡片中选择关卡绑定", "scene_id": scene_id}

    if not ue_id:
        if is_browser_request(request):
            return None, True, {"mode": "web-bypass"}
        return None, False, {
            "error": "ue_project_required",
            "message": "UE 请求缺少 X-OntoTwin-UE-Project-Id 头",
        }

    pid = lookup_with_heal(store, ue_id)
    if pid is None:
        # 错误码保留旧名 ue_project_mismatch 以兼容 UE 插件里的硬编码
        # （TwinSceneManager.cpp 里根据此码走"save disabled"专属提示）；
        # binding_state 让新插件/诊断区分"未绑定"和真正的冲突。
        return None, False, {
            "error": "ue_project_mismatch",
            "binding_state": "unbound",
            "message": (
                f"UE 工程 {ue_id} 尚未绑定到任何 OntoTwin 项目；"
                "请在 Web UI 激活目标项目后，在 UE 中执行“绑定当前UE工程到激活数据集”"
            ),
            "request_ue_project_id": ue_id,
            "request_ue_project_name": incoming.get("name"),
        }

    return pid, True, {
        "mode": "matched",
        "binding_state": "bound",
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
    注意：写入当前激活项目的接口还必须再用 check_request_can_write_active 校验。
    """
    pid, ok, info = resolve_project_for_ue(store, request)
    return bool(ok), dict(info)


def check_request_can_write_active(store, request):
    """写接口专用：UE 请求必须绑定到"当前激活项目"才能写。

    写路径直接操作激活项目的内存 store；若 UE 绑的是另一个项目而照样放行，
    迁移出的副本与源项目共享实例 ID 时会把改动写进错误的项目。
    返回 (ok, info, http_status)。
    """
    pid, ok, info = resolve_project_for_ue(store, request)
    if not ok:
        return False, dict(info), 403
    active_id = store.get_active_id() if hasattr(store, "get_active_id") else None
    if pid is not None and pid != active_id:
        return False, {
            "error": "ue_project_not_active",
            "message": "UE 所绑项目非当前激活项目；只有激活项目可写入。请在 Web UI 激活后重试。",
            "ue_project_id": pid,
            "active_project_id": active_id,
        }, 409
    return True, dict(info), 200


def binding_status(store, request):
    """/api/v2/ue/binding_status 的响应体与状态码。

    - 已绑定：200 mode=matched（与旧版一致），附 is_active/can_write
    - 未绑定：200 mode=unbound（旧插件据此启用 F10“绑定”按钮）
    - 缺 UE-ID 等真正错误：403
    """
    incoming = request_ue_project(request)
    pid, ok, info = resolve_project_for_ue(store, request)
    active_id = store.get_active_id() if hasattr(store, "get_active_id") else None
    body = {"request": incoming, "active_project_id": active_id, **info}
    if ok:
        if pid is not None:
            body["is_active"] = pid == active_id
            body["can_write"] = (bool(incoming.get("scene_id")) if os.environ.get("ONTOTWIN_STORE", "json").lower() == "pg" else pid == active_id)
        body["status"] = "ok"
        return body, 200
    if info.get("binding_state") == "unbound":
        body.update(status="ok", mode="unbound", can_write=False)
        body.pop("error", None)
        return body, 200
    body["status"] = "error"
    return body, 403


# ═══════════════════════════════════════════════════════════════
# 绑定：加互斥约束 + 联动索引
# ═══════════════════════════════════════════════════════════════

def bind_active_dataset(store, ue_project_id, ue_project_name, force=False, target_project_id=None):
    """把当前激活项目（或显式 target_project_id）绑到指定 UE-ID。
    互斥：同一 UE-ID 只能绑一个项目；已绑他处需 force=True 才能迁移。
    防抢占：目标项目已绑另一个 UE-ID 时同样需要 force=True 才能覆盖。
    锁序：_index_lock（外）→ store._lock（内），全流程原子；
    重要节点做失败回滚，避免"清了旧但没写新"造成索引与真源不一致。
    """
    if not ue_project_id:
        return False, {"error": "ue_project_id is required"}

    # 索引可能落后于持久层（PG 晚于 backend 就绪、独立维护/迁移进程、离线改库）。
    # 未命中时判定互斥前先从持久层重建；失败也继续，由下方真源字段兜底。
    if index_lookup(ue_project_id) is None:
        try:
            rebuild_index(store)
        except Exception as exc:
            print(f"[ue_binding] bind 前索引重建失败: {exc}")

    store_lock = getattr(store, "_lock", None) or nullcontext()
    with _index_lock:
        with store_lock:
            # 在锁内重读激活态：避免另一线程正好切换激活导致我们写错项目
            if target_project_id:
                active = store.read_project(target_project_id) if hasattr(store, "read_project") else None
                if not active:
                    return False, {
                        "error": "target_project_not_found",
                        "message": f"目标项目不存在: {target_project_id}",
                        "target_project_id": target_project_id,
                    }
            else:
                active = store.get_active() if hasattr(store, "get_active") else None
            if not active:
                return False, {"error": "no active project",
                               "message": "Web UI 当前没有激活的项目（或激活的是内置 Demo）；请先激活目标项目"}
            active_pid = active.get("id")

            existing_pid = _ue_index.get(str(ue_project_id))
            if existing_pid and existing_pid != active_pid and not force:
                return False, {
                    "error": "ue_project_already_bound",
                    "message": f"该 UE 已绑到另一项目 {existing_pid}；先在那边解绑或加 force=1 迁移",
                    "bound_to": existing_pid,
                }

            ds = active.get("dataset") if target_project_id else active_dataset(store)
            current_ue = str((ds or {}).get("bound_ue_project_id") or "").strip() if isinstance(ds, dict) else ""
            if current_ue and current_ue != str(ue_project_id) and not force:
                return False, {
                    "error": "project_already_bound",
                    "message": (
                        f"项目 {active_pid} 已绑定 UE 工程 {current_ue}；"
                        "如确认要改绑到当前 UE 工程，请显式强制绑定（force=1）"
                    ),
                    "project_id": active_pid,
                    "bound_ue_project_id": current_ue,
                    "bound_ue_project_name": str((ds or {}).get("bound_ue_project_name") or ""),
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
                if target_project_id:
                    active = dict(active)
                    active["dataset"] = ds
                    store.write_project(target_project_id, active)
                elif hasattr(store, "set_dataset"):
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
            for k in [k for k, v in _ue_index.items() if v == str(active_pid) and k != str(ue_project_id)]:
                _ue_index.pop(k, None)
            _ue_index[str(ue_project_id)] = str(active_pid)
            _ue_conflicts.pop(str(ue_project_id), None)

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
