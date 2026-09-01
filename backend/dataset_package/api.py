"""Flask routes for dataset package preflight, import and export."""

import io

from flask import Blueprint, jsonify, request, send_file

from .service import (
    DatasetPackageError,
    DatasetPackageService,
    MAX_PACKAGE_BYTES,
    PACKAGE_MIMETYPE,
)


def register_dataset_package_routes(
    app,
    project_store,
    dataset_lookup=None,
    dataset_names=None,
    on_import=None,
):
    blueprint = Blueprint("dataset_package_api", __name__)
    service = DatasetPackageService(
        project_store,
        dataset_lookup=dataset_lookup,
        dataset_names=dataset_names,
        on_import=on_import,
    )

    def error_response(exc):
        payload = {"error": exc.code, "message": str(exc)}
        if exc.details is not None:
            payload["details"] = exc.details
        return jsonify(payload), exc.status

    def uploaded_bytes():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            raise DatasetPackageError("package_missing", "请选择 OntoTwin 数据集包")
        data = upload.stream.read(MAX_PACKAGE_BYTES + 1)
        if len(data) > MAX_PACKAGE_BYTES:
            raise DatasetPackageError("package_too_large", "数据集包超过 64 MB 限制", 413)
        return data

    @blueprint.get("/api/v2/ontology/datasets/<dataset_id>/package-summary")
    def export_summary(dataset_id):
        try:
            return jsonify(service.export_summary(dataset_id))
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.get("/api/v2/ontology/datasets/<dataset_id>/package")
    def export_package(dataset_id):
        try:
            data, filename, _ = service.export_package(dataset_id)
            return send_file(
                io.BytesIO(data),
                mimetype=PACKAGE_MIMETYPE,
                as_attachment=True,
                download_name=filename,
                max_age=0,
            )
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.post("/api/v2/ontology/dataset-packages/preflight")
    def preflight():
        try:
            return jsonify(service.preflight(uploaded_bytes()))
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.post("/api/v2/ontology/dataset-packages/import")
    def import_package():
        try:
            result = service.import_package(
                uploaded_bytes(),
                request.form.get("target_name"),
            )
            return jsonify(result), 201
        except DatasetPackageError as exc:
            return error_response(exc)

    app.register_blueprint(blueprint)
    return service
