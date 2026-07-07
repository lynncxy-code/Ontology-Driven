"""
UE project binding helpers (OntoTwin 3.4)

A dataset/project may be bound to one UE project identity. UE requests carry
X-OntoTwin-UE-Project-Id / X-OntoTwin-UE-Project-Name. If the active dataset is
bound, UE-facing state APIs reject mismatched identities. Browser-originated
Nexus pages are allowed to read state for operations and debugging.
"""

UE_ID_HEADER = "X-OntoTwin-UE-Project-Id"
UE_NAME_HEADER = "X-OntoTwin-UE-Project-Name"


def request_ue_project(request):
    data = request.get_json(silent=True) or {}
    return {
        "id": (request.headers.get(UE_ID_HEADER) or data.get("ue_project_id") or request.args.get("ue_project_id") or "").strip(),
        "name": (request.headers.get(UE_NAME_HEADER) or data.get("ue_project_name") or request.args.get("ue_project_name") or "").strip(),
    }


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


def bind_active_dataset(store, ue_project_id, ue_project_name):
    if not ue_project_id:
        return False, {"error": "ue_project_id is required"}
    active = store.get_active() if hasattr(store, "get_active") else None
    if not active:
        return False, {"error": "no active project"}
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
    if hasattr(store, "set_dataset"):
        store.set_dataset(ds)
    else:
        active["dataset"] = ds
    return True, {"project_id": active.get("id"), "dataset": ds}


def is_browser_request(request):
    ua = request.headers.get("User-Agent", "")
    return "Mozilla" in ua or request.headers.get("X-OntoTwin-Client") == "Web"


def check_request_matches_active(store, request):
    bound = active_binding(store)
    if not bound["id"]:
        return True, {"mode": "unbound"}
    incoming = request_ue_project(request)
    # Nexus web pages use the same read APIs for operations/debugging. They do
    # not send a UE project id, so they may read. Once a UE id is present, even
    # from a browser-like client, it must match.
    if not incoming["id"] and is_browser_request(request):
        return True, {"mode": "web-bypass", "bound": bound}
    if not incoming["id"]:
        return False, {
            "error": "ue_project_required",
            "message": "???????? UE ?????????? UE ?????",
            "bound_ue_project_id": bound["id"],
            "bound_ue_project_name": bound["name"],
        }
    if incoming["id"] != bound["id"]:
        return False, {
            "error": "ue_project_mismatch",
            "message": "?? UE ??????????",
            "bound_ue_project_id": bound["id"],
            "bound_ue_project_name": bound["name"],
            "request_ue_project_id": incoming["id"],
            "request_ue_project_name": incoming["name"],
        }
    return True, {"mode": "matched", "bound": bound, "request": incoming}
