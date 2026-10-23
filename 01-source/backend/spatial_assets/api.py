from flask import Blueprint, jsonify, request, send_file

from project_store import ProjectMismatch

from .service import SpatialFrameConflictError, SpatialFrameNotFoundError, SpatialFrameService
from .validators import SpatialFrameValidationError


def register_spatial_asset_routes(app, project_store, asset_root=None):
    blueprint = Blueprint("spatial_asset_api", __name__)
    service = SpatialFrameService(project_store, asset_root)

    def execute(action, success_status=200):
        try:
            return jsonify(action()), success_status
        except SpatialFrameValidationError as exc:
            payload = {"error": exc.code, "message": str(exc)}
            if exc.fields:
                payload["fields"] = exc.fields
            return jsonify(payload), exc.status
        except SpatialFrameConflictError as exc:
            return jsonify({"error": "spatial_frame_revision_conflict", "message": str(exc)}), 409
        except SpatialFrameNotFoundError as exc:
            return jsonify({"error": "spatial_frame_not_found", "message": str(exc)}), 404
        except ProjectMismatch as exc:
            return jsonify({
                "error": "project changed",
                "expected": exc.expected,
                "actual": exc.actual,
            }), 409
        except (TypeError, ValueError) as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    @blueprint.post("/api/v2/spatial-frames/assets")
    def create_asset():
        return execute(lambda: service.create_image_frame(
            request.files.get("file"), request.form.to_dict(),
            request.form.get("expected_project_id"),
        ), 201)

    @blueprint.post("/api/v2/spatial-frames/cad-assets")
    def create_cad_asset():
        return execute(lambda: service.create_cad_frame(
            request.files.get("file"), request.form.to_dict(),
            request.form.get("expected_project_id"),
        ), 201)

    @blueprint.get("/api/v2/spatial-frames")
    def list_frames():
        return execute(lambda: service.list_frames(request.args.get("kind") or "image"))

    @blueprint.get("/api/v2/spatial-frames/<frame_id>")
    def get_frame(frame_id):
        return execute(lambda: service.get_frame(frame_id))

    @blueprint.get("/api/v2/spatial-frames/<frame_id>/image")
    def get_image(frame_id):
        try:
            path, image = service.image_file(frame_id)
            response = send_file(
                path,
                mimetype=image.get("mime_type") or "application/octet-stream",
                conditional=True,
                max_age=3600,
            )
            if image.get("sha256"):
                response.set_etag(image["sha256"])
            return response
        except SpatialFrameNotFoundError as exc:
            return jsonify({"error": "spatial_frame_not_found", "message": str(exc)}), 404

    @blueprint.get("/api/v2/spatial-frames/<frame_id>/source")
    def get_source(frame_id):
        try:
            path, cad = service.source_file(frame_id)
            response = send_file(
                path,
                mimetype=cad.get("mime_type") or "application/octet-stream",
                as_attachment=False,
                download_name=cad.get("original_name") or "drawing.dxf",
                conditional=True,
                max_age=3600,
            )
            if cad.get("sha256"):
                response.set_etag(cad["sha256"])
            return response
        except SpatialFrameNotFoundError as exc:
            return jsonify({"error": "spatial_frame_not_found", "message": str(exc)}), 404

    @blueprint.put("/api/v2/spatial-frames/<frame_id>/draft")
    def save_draft(frame_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.save_draft(
            frame_id, data, data.get("expected_project_id")
        ))

    @blueprint.post("/api/v2/spatial-frames/<frame_id>/publish")
    def publish(frame_id):
        data = request.get_json(silent=True) or {}
        return execute(lambda: service.publish(
            frame_id, data, data.get("expected_project_id")
        ))

    app.register_blueprint(blueprint)
