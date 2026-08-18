from flask import Blueprint, jsonify, request

from ue_project_binding import check_request_matches_active, request_ue_project

from .service import WebInteractionConflictError, WebInteractionNotFoundError, WebInteractionService


class WebInteractionForbiddenError(PermissionError):
    def __init__(self, payload):
        self.payload = payload
        super().__init__(payload.get("message") or payload.get("error") or "forbidden")


def register_web_interaction_routes(app, project_store):
    blueprint = Blueprint("web_interaction_api", __name__)
    service = WebInteractionService(project_store)

    def execute(action):
        try:
            return jsonify(action())
        except WebInteractionForbiddenError as exc:
            return jsonify(exc.payload), 403
        except WebInteractionConflictError as exc:
            return jsonify({"error": "web_interaction_revision_conflict", "message": str(exc)}), 409
        except WebInteractionNotFoundError as exc:
            return jsonify({"error": "active_project_not_found", "message": str(exc)}), 404
        except (TypeError, ValueError) as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    def runtime_binding(require_ue_identity=False):
        ue = request_ue_project(request)
        context = (request.headers.get("X-OntoTwin-UE-Context") or "").strip().lower()
        is_ue = bool(ue.get("id") or context)
        if not is_ue and not require_ue_identity:
            return {"mode": "web-inspection"}, ue
        if require_ue_identity and not ue.get("id"):
            raise WebInteractionForbiddenError({"error": "ue_project_required", "message": "UE 运行事件必须携带 UE 工程身份"})
        ok, info = check_request_matches_active(project_store, request)
        if not ok:
            raise WebInteractionForbiddenError(info)
        if info.get("mode") == "unbound" and context == "packaged":
            raise WebInteractionForbiddenError({"error": "ue_project_unbound", "message": "打包运行时只允许访问已绑定的当前项目"})
        return info, ue

    @blueprint.get("/api/v2/web-interactions")
    def get_config():
        return execute(service.get)

    @blueprint.put("/api/v2/web-interactions/draft")
    def save_draft():
        return execute(lambda: service.save_draft(request.get_json(silent=True) or {}))

    @blueprint.post("/api/v2/web-interactions/validate")
    def validate():
        return execute(lambda: service.validate(request.get_json(silent=True) or {}))

    @blueprint.post("/api/v2/web-interactions/resolve-preview")
    def resolve_preview():
        return execute(lambda: service.resolve_preview(request.get_json(silent=True) or {}))

    @blueprint.post("/api/v2/web-interactions/publish")
    def publish():
        return execute(lambda: service.publish(request.get_json(silent=True) or {}))

    @blueprint.post("/api/v2/web-interactions/apply")
    def apply():
        return execute(lambda: service.apply(request.get_json(silent=True) or {}))

    @blueprint.post("/api/v2/web-interactions/rollback")
    def rollback():
        return execute(lambda: service.rollback(request.get_json(silent=True) or {}))

    @blueprint.get("/api/v2/web-interactions/runtime")
    def runtime():
        def action():
            binding, _ = runtime_binding(False)
            return service.runtime(request.args.get("known_revision"), binding)
        return execute(action)

    @blueprint.post("/api/v2/web-interactions/runtime-events")
    def runtime_events():
        def action():
            _, ue = runtime_binding(True)
            return service.runtime_event(request.get_json(silent=True) or {}, ue)
        return execute(action)

    app.register_blueprint(blueprint)
    return service
