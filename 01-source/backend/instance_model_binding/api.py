from flask import Blueprint, jsonify, request

from .service import InstanceModelBindingError, InstanceModelBindingService


def register_instance_model_binding_routes(
    app,
    project_store,
    asset_catalog,
    artstudio_client,
    on_object_types_changed=None,
):
    blueprint = Blueprint("instance_model_binding_api", __name__)
    service = InstanceModelBindingService(
        project_store,
        asset_catalog,
        artstudio_client,
        on_object_types_changed,
    )

    def error_response(exc):
        return jsonify({
            "error": exc.code,
            "message": str(exc),
            "fields": exc.fields,
        }), exc.status

    @blueprint.get("/api/v2/instances/<instance_id>/model-binding")
    def get_model_binding(instance_id):
        try:
            return jsonify(service.summary(instance_id))
        except InstanceModelBindingError as exc:
            return error_response(exc)

    @blueprint.put("/api/v2/instances/<instance_id>/model-binding")
    def put_model_binding(instance_id):
        try:
            return jsonify(service.save(instance_id, request.get_json(silent=True) or {}))
        except InstanceModelBindingError as exc:
            return error_response(exc)

    @blueprint.delete("/api/v2/instances/<instance_id>/model-binding")
    def delete_model_binding(instance_id):
        try:
            return jsonify(service.clear(instance_id, request.get_json(silent=True) or {}))
        except InstanceModelBindingError as exc:
            return error_response(exc)

    @blueprint.delete("/api/v2/object-types/<object_type_rid>/model-binding")
    def delete_type_model_binding(object_type_rid):
        try:
            return jsonify(service.clear_type_default(object_type_rid))
        except InstanceModelBindingError as exc:
            return error_response(exc)

    app.register_blueprint(blueprint)
    return service
