from flask import Blueprint, jsonify, request

from .service import RepresentationContainerError, RepresentationContainerService


def register_representation_container_routes(
    app,
    project_store,
    on_object_types_changed=None,
):
    blueprint = Blueprint("representation_container_api", __name__)
    service = RepresentationContainerService(
        project_store,
        on_object_types_changed=on_object_types_changed,
    )

    def error_response(exc):
        return jsonify({
            "error": exc.code,
            "message": str(exc),
            "fields": exc.fields,
        }), exc.status

    @blueprint.get("/api/v2/object-types/<object_type_rid>/representation-container")
    def get_type_container(object_type_rid):
        try:
            return jsonify(service.summary(object_type_rid))
        except RepresentationContainerError as exc:
            return error_response(exc)

    @blueprint.put("/api/v2/object-types/<object_type_rid>/representation-container")
    def put_type_container(object_type_rid):
        try:
            return jsonify(service.save(
                object_type_rid,
                request.get_json(silent=True) or {},
            ))
        except RepresentationContainerError as exc:
            return error_response(exc)

    @blueprint.delete("/api/v2/object-types/<object_type_rid>/representation-container")
    def delete_type_container(object_type_rid):
        try:
            return jsonify(service.clear(
                object_type_rid,
                request.get_json(silent=True) or {},
            ))
        except RepresentationContainerError as exc:
            return error_response(exc)

    @blueprint.post("/api/v2/object-types/representation-container/batch")
    def batch_type_container():
        try:
            return jsonify(service.apply_batch(request.get_json(silent=True) or {}))
        except RepresentationContainerError as exc:
            return error_response(exc)

    app.register_blueprint(blueprint)
    return service
