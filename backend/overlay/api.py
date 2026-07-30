from flask import Blueprint, jsonify, request

from project_store import ProjectMismatch

from .schema import OverlayValidationError, clone_templates
from .media import MediaPolicyError
from .service import OverlayConflictError, OverlayNotFoundError, OverlayService


def register_overlay_routes(app, project_store, on_object_types_changed=None, platform_media_policy=None):
    blueprint = Blueprint("overlay_api", __name__)
    service = OverlayService(project_store, platform_media_policy)

    def execute(action, success_status=200):
        try:
            return jsonify(action()), success_status
        except OverlayValidationError as exc:
            return jsonify({"error": "overlay_validation_failed", "fields": exc.errors}), 422
        except OverlayNotFoundError as exc:
            return jsonify({"error": "overlay_target_not_found", "message": str(exc)}), 404
        except OverlayConflictError as exc:
            return jsonify({"error": "overlay_revision_conflict", "message": str(exc)}), 409
        except ProjectMismatch as exc:
            return jsonify({
                "error": "project changed",
                "expected": exc.expected,
                "actual": exc.actual,
            }), 409
        except MediaPolicyError as exc:
            return jsonify({
                "error": exc.code,
                "message": str(exc),
                "fields": [{"path": exc.path, "message": str(exc)}],
            }), 422
        except (TypeError, ValueError) as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    @blueprint.get("/api/v2/overlays/templates")
    def get_templates():
        return jsonify({"templates": clone_templates()})

    @blueprint.get("/api/v2/overlays/context")
    def get_context():
        return execute(lambda: service.context(
            object_type_rid=request.args.get("object_type_rid"),
            instance_id=request.args.get("instance_id"),
        ))

    @blueprint.post("/api/v2/overlays/preview")
    def preview_overlay():
        data = request.get_json(silent=True) or {}
        return execute(lambda: {
            "preview": service.preview(
                data.get("object_type_rid"), data.get("instance_id"), data.get("config")
            )
        })

    @blueprint.put("/api/v2/overlays/object-types/<path:object_type_rid>")
    def save_type_overlay(object_type_rid):
        data = request.get_json(silent=True) or {}

        def action():
            envelope = service.save_type(
                object_type_rid,
                data.get("config"),
                data.get("expected_revision", 0),
                data.get("expected_project_id"),
            )
            if on_object_types_changed:
                on_object_types_changed()
            return {"status": "ok", "config": envelope}

        return execute(action)

    @blueprint.put("/api/v2/overlays/instances/<path:instance_id>")
    def save_instance_overlay(instance_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: {
            "status": "ok",
            "override": service.save_instance(
                instance_id,
                data.get("override") or {},
                data.get("expected_revision", 0),
                data.get("expected_project_id"),
            ),
        })

    @blueprint.delete("/api/v2/overlays/instances/<path:instance_id>")
    def clear_instance_overlay(instance_id):
        data = request.get_json(silent=True) or {}
        expected = request.args.get("expected_revision", data.get("expected_revision", 0))
        return execute(lambda: {
            "status": "ok",
            "override": service.clear_instance(
                instance_id, expected, data.get("expected_project_id")
            ),
        })

    @blueprint.post("/api/v2/overlays/instances/batch")
    def batch_instance_overlays():
        data = request.get_json(silent=True) or {}
        return execute(lambda: {
            "status": "ok",
            "instances": service.batch_instances(
                data.get("object_type_rid"),
                data.get("instance_ids"),
                data.get("merge_patch") or {},
                data.get("expected_revisions") or {},
                data.get("expected_project_id"),
            ),
        })

    @blueprint.get("/api/v2/overlays/media/policy")
    def get_media_policy():
        return execute(service.get_media_policy)

    @blueprint.put("/api/v2/overlays/media/policy")
    def save_media_policy():
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.save_media_policy(
            data.get("policy") or {},
            data.get("expected_revision", 0),
            data.get("expected_project_id"),
        ))

    @blueprint.post("/api/v2/overlays/media/resolve")
    def resolve_media():
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.resolve_media(data.get("instance_id")))

    app.register_blueprint(blueprint)
    return service
