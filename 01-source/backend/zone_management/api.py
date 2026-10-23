from flask import Blueprint, jsonify, request

from .service import (
    ZoneManagementConflictError,
    ZoneManagementError,
    ZoneManagementService,
)


def register_zone_management_routes(app, project_store):
    blueprint = Blueprint("zone_management_api", __name__)
    service = ZoneManagementService(project_store)

    @blueprint.get("/api/v2/zones")
    def get_zones():
        try:
            return jsonify(service.summary())
        except ZoneManagementError as exc:
            status = 404 if exc.code == "active_project_not_found" else 422
            return jsonify({"error": exc.code, "message": str(exc), "fields": exc.fields}), status

    @blueprint.put("/api/v2/zones/assignments")
    def assign_zone():
        try:
            return jsonify(service.assign(request.get_json(silent=True) or {}))
        except ZoneManagementConflictError as exc:
            return jsonify({"error": "active_project_changed", "message": str(exc)}), 409
        except ZoneManagementError as exc:
            status = 404 if exc.code == "active_project_not_found" else 422
            return jsonify({"error": exc.code, "message": str(exc), "fields": exc.fields}), status

    @blueprint.put("/api/v2/zones/catalog")
    def save_zone_catalog():
        try:
            return jsonify(service.save_catalog(request.get_json(silent=True) or {}))
        except ZoneManagementConflictError as exc:
            return jsonify({"error": "active_project_changed", "message": str(exc)}), 409
        except ZoneManagementError as exc:
            status = 404 if exc.code == "active_project_not_found" else 422
            return jsonify({"error": exc.code, "message": str(exc), "fields": exc.fields}), status

    app.register_blueprint(blueprint)
    return service
