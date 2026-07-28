from flask import Blueprint, jsonify, request

from ue_project_binding import check_request_matches_active, request_ue_project

from .catalog import CatalogValidationError, ResourceCatalog
from .runtime_projection import RuntimeProjectionError
from .service import SceneInteractionConflictError, SceneInteractionNotFoundError, SceneInteractionService
from .validators import SceneInteractionValidationError


class SceneInteractionForbiddenError(PermissionError):
    def __init__(self, payload):
        self.payload = payload
        super().__init__(payload.get("message") or payload.get("error") or "forbidden")


def register_scene_interaction_routes(app, project_store, catalog_path=None):
    blueprint = Blueprint("scene_interaction_api", __name__)
    service = SceneInteractionService(project_store, ResourceCatalog(catalog_path))

    def execute(action, success_status=200):
        try:
            return jsonify(action()), success_status
        except SceneInteractionForbiddenError as exc:
            return jsonify(exc.payload), 403
        except SceneInteractionValidationError as exc:
            return jsonify({"error": "roaming_validation_failed", "fields": exc.errors}), 422
        except SceneInteractionConflictError as exc:
            return jsonify({"error": "scene_interaction_revision_conflict", "message": str(exc)}), 409
        except SceneInteractionNotFoundError as exc:
            return jsonify({"error": "active_project_not_found", "message": str(exc)}), 404
        except CatalogValidationError as exc:
            return jsonify({"error": "catalog_resource_not_found", "message": str(exc)}), 404
        except RuntimeProjectionError as exc:
            return jsonify({"error": exc.code, "message": str(exc)}), 422
        except (TypeError, ValueError) as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    def runtime_binding(require_ue_identity=False):
        ue = request_ue_project(request)
        context = (request.headers.get("X-OntoTwin-UE-Context") or "").strip().lower()
        is_ue_request = bool(ue.get("id") or context)
        if not is_ue_request and not require_ue_identity:
            return {"mode": "web-inspection"}, ue
        if require_ue_identity and not ue.get("id"):
            raise SceneInteractionForbiddenError({
                "error": "ue_project_required",
                "message": "UE 运行心跳必须携带 UE 工程身份",
            })
        ok, info = check_request_matches_active(project_store, request)
        if not ok:
            raise SceneInteractionForbiddenError(info)
        if info.get("mode") == "unbound" and context == "packaged":
            raise SceneInteractionForbiddenError({
                "error": "ue_project_unbound",
                "message": "打包运行时只允许访问已绑定的当前项目",
                "request_ue_project_id": ue.get("id"),
            })
        if info.get("mode") == "unbound":
            info = {**info, "mode": "unbound_dev", "warning": "当前项目尚未绑定 UE 工程"}
        return info, ue

    @blueprint.get("/api/v2/scene-interactions/catalog")
    def get_catalog():
        return execute(service.catalog_snapshot)

    @blueprint.get("/api/v2/scene-interactions/roaming")
    def get_roaming():
        return execute(service.get_roaming)

    @blueprint.put("/api/v2/scene-interactions/roaming")
    def save_roaming():
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.save_roaming(
            data.get("config"), data.get("expected_revision"),
        ))

    @blueprint.get("/api/v2/scene-interactions/routes")
    def get_routes():
        return execute(service.get_routes)

    @blueprint.post("/api/v2/scene-interactions/routes")
    def create_route():
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.create_route(
            data.get("route"), data.get("expected_revision"),
        ), success_status=201)

    @blueprint.get("/api/v2/scene-interactions/routes/<route_id>")
    def get_route(route_id):
        return execute(lambda: service.get_route(route_id))

    @blueprint.put("/api/v2/scene-interactions/routes/<route_id>")
    def update_route(route_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.update_route(
            route_id, data.get("route"), data.get("expected_revision"),
        ))

    @blueprint.delete("/api/v2/scene-interactions/routes/<route_id>")
    def delete_route(route_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.delete_route(
            route_id, data.get("expected_revision"),
        ))

    @blueprint.post("/api/v2/scene-interactions/routes/<route_id>/review")
    def review_route(route_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.review_route(
            route_id, data.get("expected_revision"),
        ))

    @blueprint.post("/api/v2/scene-interactions/routes/<route_id>/default")
    def set_default_route(route_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.set_default_route(
            route_id, data.get("expected_revision"),
        ))

    @blueprint.get("/api/v2/scene-interactions/runtime")
    def get_runtime():
        def action():
            binding, _ = runtime_binding(require_ue_identity=False)
            return service.runtime_projection(binding)
        return execute(action)

    @blueprint.post("/api/v2/scene-interactions/runtime")
    def report_runtime():
        data = request.get_json(silent=True) or {}
        def action():
            _, ue = runtime_binding(require_ue_identity=True)
            return service.report_runtime(data, ue)
        return execute(action)

    app.register_blueprint(blueprint)
