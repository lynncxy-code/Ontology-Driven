"""Release identity shown to people: the account menu, the Nexus badge and UE.

One platform version number covers web, backend and UE plugins (see
.agents/skills/ontotwin-product-lifecycle/references/release-versioning.md).

* ``GET /release-info.json`` (public): which version is running and when it
  was built, already worded for display.
* UE plugins report their installed version in ``X-OntoTwin-Plugin-Release``;
  the backend remembers the last report per UE project and level, in memory.
* ``GET /api/v4.8/release/ue-plugins`` (signed in): the UE projects bound to
  projects the current account may view in its current organization, each
  with the plugin version it last reported and whether it matches.
"""
import os
import re
import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

PLUGIN_RELEASE_HEADER = "X-OntoTwin-Plugin-Release"
UE_ID_HEADER = "X-OntoTwin-UE-Project-Id"
UE_SCENE_HEADER = "X-OntoTwin-UE-Scene-Id"
_MAX_ENTRIES = 512
_MAX_AGE_SECONDS = 7 * 24 * 3600

_CANDIDATE = re.compile(r"^rc\.(\d+)$")
_FORMAL = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d+)(?:\.(\d+))?$")

_reports = {}
_lock = threading.Lock()


def running_release():
    return os.environ.get("ONTOTWIN_RELEASE_ID", "").strip() or "dev"


def describe(release):
    """Turn a release id into the words people see."""
    release = (release or "").strip()
    match = _CANDIDATE.match(release)
    if match:
        return {"kind": "candidate", "label": "候选 " + match.group(1), "display": "OntoTwin 候选 {} · 验收版".format(match.group(1))}
    if _FORMAL.match(release):
        return {"kind": "formal", "label": release, "display": "OntoTwin {} · 正式版".format(release)}
    if not release or release in ("dev", "4.8-dev"):
        return {"kind": "dev", "label": "开发版", "display": "OntoTwin 开发版"}
    return {"kind": "legacy", "label": release, "display": "OntoTwin " + release}


def remember_plugin_report(ue_project, scene, release, now=None):
    if not ue_project:
        return
    key = (ue_project.strip(), (scene or "").strip())
    with _lock:
        _reports[key] = {"release": (release or "").strip()[:64], "seen": now if now is not None else time.time()}
        if len(_reports) > _MAX_ENTRIES:
            for old in sorted(_reports, key=lambda k: _reports[k]["seen"])[: len(_reports) - _MAX_ENTRIES]:
                _reports.pop(old, None)


def plugin_report(ue_project, scene, now=None):
    now = now if now is not None else time.time()
    with _lock:
        item = _reports.get(((ue_project or "").strip(), (scene or "").strip()))
        if item and now - item["seen"] <= _MAX_AGE_SECONDS:
            return dict(item)
    return None


def plugin_rows(bindings, backend_release, now=None):
    """bindings: dicts with ue_project_key, scene_key, ue_project_name, scene_name.

    Only UE projects that reported recently are listed; a plugin too old to
    report its version is listed as not matching.
    """
    rows, seen = [], set()
    for b in bindings:
        key = (b["ue_project_key"], b["scene_key"])
        if key in seen:
            continue
        seen.add(key)
        report = plugin_report(*key, now=now)
        if not report:
            continue
        release = report["release"]
        rows.append({
            "ue_project_name": b.get("ue_project_name") or b["ue_project_key"],
            "scene_name": b.get("scene_name") or b["scene_key"],
            "plugin_release": release,
            "plugin_label": describe(release)["label"] if release else "",
            "status": "same" if release and release == backend_release else ("unknown" if not release else "different"),
            "last_seen_at": datetime.fromtimestamp(report["seen"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    rows.sort(key=lambda r: (r["status"] == "same", r["ue_project_name"], r["scene_name"]))
    return rows


def _visible_bindings(cur, session, project_allowed):
    cur.execute(
        """SELECT b.project_id, u.stable_key, s.stable_key, u.display_name,
                  COALESCE(NULLIF(s.display_name,''), NULLIF(s.level_path,''), s.stable_key)
             FROM project_scene_binding b
             JOIN ue_project u ON u.ue_project_id=b.ue_project_id
             JOIN ue_scene s ON s.scene_id=b.scene_id
            WHERE b.organization_id=%s AND b.status='active'""",
        (session["organization_id"],))
    rows, allowed = [], {}
    for project_id, ue_key, scene_key, ue_name, scene_name in cur.fetchall():
        if project_id not in allowed:
            allowed[project_id] = bool(project_allowed(cur, session["user_id"], project_id))
        if allowed[project_id]:
            rows.append({"ue_project_key": ue_key, "scene_key": scene_key, "ue_project_name": ue_name, "scene_name": scene_name})
    return rows


def register_release_info_routes(app):
    import tenant_api
    from db import pg

    blueprint = Blueprint("release_info", __name__)

    @blueprint.before_app_request
    def _record_plugin_report():
        ue_project = request.headers.get(UE_ID_HEADER)
        if ue_project:
            remember_plugin_report(ue_project, request.headers.get(UE_SCENE_HEADER), request.headers.get(PLUGIN_RELEASE_HEADER))

    @blueprint.get("/release-info.json")
    def release_info():
        release = running_release()
        info = describe(release)
        return jsonify({
            "version": release,
            "backend": release,          # kept for older readers
            "kind": info["kind"],
            "label": info["label"],
            "display": info["display"],
            "updated_at": os.environ.get("ONTOTWIN_RELEASE_BUILT_AT", ""),
            "time_zone": "UTC",
        })

    @blueprint.get("/api/v4.8/release/ue-plugins")
    @tenant_api._api
    def ue_plugins():
        tenant_api._require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant_api._load_session(cur)
                if not session.get("organization_id"):
                    raise tenant_api.ApiError(400, "请先选择组织", "context_required")
                bindings = _visible_bindings(cur, session, lambda c, u, p: tenant_api._project_allowed(c, u, p, "view"))
        release = running_release()
        return jsonify({"backend_release": release, "items": plugin_rows(bindings, release)})

    app.register_blueprint(blueprint)
