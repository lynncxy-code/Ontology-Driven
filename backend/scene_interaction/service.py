import copy
import datetime
import threading
import time

from .catalog import ResourceCatalog
from .routes import (
    find_project_route,
    list_project_routes,
    normalize_route,
    public_route,
    route_review_state,
)
from .runtime_projection import RuntimeProjectionError, build_runtime_projection, calibration_state, prepare_spawn_for_save
from .validators import (
    SceneInteractionValidationError,
    default_roaming_config,
    project_route_provides_spawn,
    validate_roaming_config,
    validate_runtime_status,
)


class SceneInteractionNotFoundError(LookupError):
    pass


class SceneInteractionConflictError(RuntimeError):
    pass


class RuntimeStatusRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._by_project = {}

    def report(self, project_id, payload, ue_project):
        normalized = validate_runtime_status(payload)
        now = time.time()
        normalized["project_id"] = project_id
        normalized["ue_project_id"] = (ue_project or {}).get("id", "")
        normalized["ue_project_name"] = (ue_project or {}).get("name", "")
        normalized["last_seen_at"] = datetime.datetime.fromtimestamp(
            now, datetime.timezone.utc
        ).isoformat().replace("+00:00", "Z")
        normalized["online"] = True
        normalized["_seen_epoch"] = now
        with self._lock:
            self._by_project[project_id] = normalized
        return self.get(project_id)

    def get(self, project_id):
        with self._lock:
            value = copy.deepcopy(self._by_project.get(project_id))
        if not value:
            return None
        seen = value.pop("_seen_epoch", 0)
        value["online"] = (time.time() - seen) <= 6.0
        if not value["online"] and value.get("runtime_state") != "offline":
            value["reported_runtime_state"] = value.get("runtime_state")
            value["runtime_state"] = "offline"
        return value


_RUNTIME_STATUS = RuntimeStatusRegistry()


def get_runtime_status(project_id):
    """Read the latest ephemeral UE heartbeat for a project."""
    return _RUNTIME_STATUS.get(project_id) if project_id else None


class SceneInteractionService:
    def __init__(self, store, catalog=None, runtime_status=None):
        self.store = store
        self.catalog = catalog or ResourceCatalog()
        self.runtime_status = runtime_status or _RUNTIME_STATUS

    def _project(self):
        project = self.store.get_active_copy()
        if not project:
            raise SceneInteractionNotFoundError("当前没有激活项目")
        return project

    @staticmethod
    def _scene(project):
        value = project.get("scene_interactions")
        if not isinstance(value, dict):
            return {"revision": 0, "roaming": default_roaming_config(), "routes": []}
        return value

    def catalog_snapshot(self):
        return self.catalog.snapshot()

    def get_roaming(self):
        project = self._project()
        scene = self._scene(project)
        config = copy.deepcopy(scene.get("roaming") or default_roaming_config())
        calibration = calibration_state(project, config.get("spawn"))
        return {
            "project_id": project.get("id"),
            "schema_version": project.get("schema_version"),
            "revision": int(scene.get("revision") or 0),
            "catalog_version": self.catalog.version,
            "config": config,
            "calibration_state": calibration,
            "calibration_context": self._calibration_context(project, config),
            "project_routes": list_project_routes(project, include_waypoints=False),
            "runtime_status": self.runtime_status.get(project.get("id")),
        }

    @staticmethod
    def _calibration_context(project, config):
        frames = []
        for frame in project.get("frames") or []:
            if (
                frame.get("kind") != "image"
                or frame.get("status") != "published"
                or not frame.get("image")
            ):
                continue
            to_ue = frame.get("to_ue")
            if isinstance(to_ue, dict):
                to_ue = to_ue.get("matrix")
            if not to_ue:
                continue
            frames.append({
                "id": frame.get("id"),
                "name": frame.get("name") or frame.get("id"),
                "floor": frame.get("floor") or 1,
                "unit": frame.get("unit") or "px",
                "to_ue_matrix": copy.deepcopy(to_ue),
                "source_label": frame.get("source_label"),
                "image_url": frame.get("image_url") or (
                    f"/api/v2/spatial-frames/{frame.get('id')}/image"
                    if frame.get("kind") == "image" and frame.get("image") else None
                ),
                "status": frame.get("status"),
                "calibration_revision": frame.get("calibration_revision"),
                "calibration_fingerprint": frame.get("calibration_fingerprint"),
                "floor_reference": copy.deepcopy(frame.get("floor_reference")),
            })
        return {
            "selected_frame_id": ((config.get("spawn") or {}).get("frame_id")),
            "frames": frames,
            "spatial_profile": copy.deepcopy(project.get("spatial_profile") or {}),
        }

    def save_roaming(self, config, expected_revision, expected_project_id=None):
        project = self._project()
        try:
            expected = int(expected_revision)
        except (TypeError, ValueError) as exc:
            raise SceneInteractionValidationError([{
                "path": "expected_revision", "message": "必须是整数",
            }]) from exc
        prepared = copy.deepcopy(config)
        project_routes = list_project_routes(project, include_waypoints=False)
        route_owns_spawn = project_route_provides_spawn(prepared, project_routes)
        if isinstance(prepared, dict) and isinstance(prepared.get("spawn"), dict):
            try:
                prepared["spawn"] = prepare_spawn_for_save(project, prepared["spawn"])
            except RuntimeProjectionError as exc:
                if route_owns_spawn:
                    prepared.pop("spawn", None)
                else:
                    raise SceneInteractionValidationError([{
                        "path": "spawn", "message": str(exc), "code": exc.code,
                    }]) from exc
        normalized = validate_roaming_config(
            prepared,
            self.catalog,
            project_routes,
        )
        project_id = project.get("id")

        def update(working):
            if working.get("id") != project_id:
                raise SceneInteractionConflictError("保存期间当前激活项目已切换")
            scene = working.setdefault("scene_interactions", {
                "revision": 0, "roaming": default_roaming_config(), "routes": [],
            })
            current = int(scene.get("revision") or 0)
            if current != expected:
                raise SceneInteractionConflictError(
                    f"scene interaction revision conflict: expected {expected}, current {current}"
                )
            scene["roaming"] = copy.deepcopy(normalized)
            scene["revision"] = current + 1
            return scene["revision"]

        revision = self.store.transact_expected_active(expected_project_id, update)
        return {
            "status": "ok",
            "project_id": project_id,
            "revision": revision,
            "catalog_version": self.catalog.version,
            "config": normalized,
            "calibration_state": calibration_state(
                self.store.get_active_copy(), normalized.get("spawn")
            ),
        }

    @staticmethod
    def _expected_revision(value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise SceneInteractionValidationError([{
                "path": "expected_revision", "message": "必须是整数",
            }]) from exc

    def get_routes(self):
        project = self._project()
        scene = self._scene(project)
        roaming = scene.get("roaming") or {}
        return {
            "project_id": project.get("id"),
            "revision": int(scene.get("revision") or 0),
            "default_route_id": ((roaming.get("route") or {}).get("route_id") or ""),
            "routes": list_project_routes(project, include_waypoints=False),
        }

    def get_route(self, route_id):
        project = self._project()
        route = find_project_route(project, route_id)
        if not route:
            raise SceneInteractionNotFoundError("当前项目中找不到该漫游路线")
        return {
            "project_id": project.get("id"),
            "revision": int(self._scene(project).get("revision") or 0),
            "route": public_route(project, route, include_waypoints=True),
        }

    def create_route(self, payload, expected_revision, expected_project_id=None):
        project = self._project()
        expected = self._expected_revision(expected_revision)
        project_id = project.get("id")
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise SceneInteractionConflictError("保存期间当前激活项目已切换")
            scene = working.setdefault("scene_interactions", {
                "revision": 0, "roaming": default_roaming_config(), "routes": [],
            })
            current_revision = int(scene.get("revision") or 0)
            if current_revision != expected:
                raise SceneInteractionConflictError(
                    f"scene interaction revision conflict: expected {expected}, current {current_revision}"
                )
            route = normalize_route(working, payload)
            scene.setdefault("routes", []).append(copy.deepcopy(route))
            scene["revision"] = current_revision + 1
            result.update({"route": route, "revision": scene["revision"]})

        self.store.transact_expected_active(expected_project_id, update)
        return {
            "status": "ok",
            "project_id": project_id,
            "revision": result["revision"],
            "route": public_route(self.store.get_active_copy(), result["route"], True),
        }

    def update_route(self, route_id, payload, expected_revision, expected_project_id=None):
        project = self._project()
        expected = self._expected_revision(expected_revision)
        project_id = project.get("id")
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise SceneInteractionConflictError("保存期间当前激活项目已切换")
            scene = working.setdefault("scene_interactions", {
                "revision": 0, "roaming": default_roaming_config(), "routes": [],
            })
            current_revision = int(scene.get("revision") or 0)
            if current_revision != expected:
                raise SceneInteractionConflictError(
                    f"scene interaction revision conflict: expected {expected}, current {current_revision}"
                )
            routes = scene.setdefault("routes", [])
            for index, current in enumerate(routes):
                if current.get("id") != route_id:
                    continue
                route = normalize_route(working, payload, current=current)
                routes[index] = copy.deepcopy(route)
                scene["revision"] = current_revision + 1
                result.update({"route": route, "revision": scene["revision"]})
                return
            raise SceneInteractionNotFoundError("当前项目中找不到该漫游路线")

        self.store.transact_expected_active(expected_project_id, update)
        return {
            "status": "ok",
            "project_id": project_id,
            "revision": result["revision"],
            "route": public_route(self.store.get_active_copy(), result["route"], True),
        }

    def review_route(self, route_id, expected_revision, expected_project_id=None):
        project = self._project()
        current = find_project_route(project, route_id)
        if not current:
            raise SceneInteractionNotFoundError("当前项目中找不到该漫游路线")
        return self.update_route(route_id, current, expected_revision, expected_project_id)

    def delete_route(self, route_id, expected_revision, expected_project_id=None):
        project = self._project()
        expected = self._expected_revision(expected_revision)
        project_id = project.get("id")
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise SceneInteractionConflictError("删除期间当前激活项目已切换")
            scene = working.setdefault("scene_interactions", {
                "revision": 0, "roaming": default_roaming_config(), "routes": [],
            })
            current_revision = int(scene.get("revision") or 0)
            if current_revision != expected:
                raise SceneInteractionConflictError(
                    f"scene interaction revision conflict: expected {expected}, current {current_revision}"
                )
            default_id = (((scene.get("roaming") or {}).get("route") or {}).get("route_id"))
            if default_id == route_id:
                raise SceneInteractionConflictError("该路线正在作为默认路线，请先更换默认路线")
            routes = scene.setdefault("routes", [])
            next_routes = [item for item in routes if item.get("id") != route_id]
            if len(next_routes) == len(routes):
                raise SceneInteractionNotFoundError("当前项目中找不到该漫游路线")
            scene["routes"] = next_routes
            scene["revision"] = current_revision + 1
            result["revision"] = scene["revision"]

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "project_id": project_id, "revision": result["revision"]}

    def set_default_route(self, route_id, expected_revision, expected_project_id=None):
        project = self._project()
        expected = self._expected_revision(expected_revision)
        project_id = project.get("id")
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise SceneInteractionConflictError("保存期间当前激活项目已切换")
            scene = working.setdefault("scene_interactions", {
                "revision": 0, "roaming": default_roaming_config(), "routes": [],
            })
            current_revision = int(scene.get("revision") or 0)
            if current_revision != expected:
                raise SceneInteractionConflictError(
                    f"scene interaction revision conflict: expected {expected}, current {current_revision}"
                )
            route = next((item for item in scene.get("routes") or [] if item.get("id") == route_id), None)
            if not route:
                raise SceneInteractionNotFoundError("当前项目中找不到该漫游路线")
            if route_review_state(working, route) != "ready" or not route.get("enabled", True):
                raise SceneInteractionValidationError([{
                    "path": "route_id", "message": "只有已就绪且已启用的路线可以设为默认",
                }])
            roaming = scene.setdefault("roaming", default_roaming_config())
            route_config = roaming.setdefault("route", {})
            route_config.update({
                "enabled": True,
                "route_id": route_id,
                "auto_start": route_config.get("auto_start", True),
                "completion_mode": "loop" if route.get("loop") else "stop",
                "takeover_enabled": route_config.get("takeover_enabled", True),
            })
            scene["revision"] = current_revision + 1
            result["revision"] = scene["revision"]

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "project_id": project_id, "revision": result["revision"], "route_id": route_id}

    def runtime_projection(self, binding):
        project = self._project()
        scene = self._scene(project)
        revision = int(scene.get("revision") or 0)
        config = copy.deepcopy(scene.get("roaming") or default_roaming_config())
        projection = build_runtime_projection(project, config, self.catalog, revision)
        return {
            "project_id": project.get("id"),
            "revision": revision,
            "catalog_version": self.catalog.version,
            "binding": copy.deepcopy(binding),
            **projection,
            "last_client_status": self.runtime_status.get(project.get("id")),
        }

    def report_runtime(self, payload, ue_project):
        project = self._project()
        return {
            "status": "ok",
            "runtime_status": self.runtime_status.report(project.get("id"), payload, ue_project),
        }
