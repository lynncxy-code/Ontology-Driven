"""Flask routes for dataset package preflight, import and export."""

import io

from flask import Blueprint, jsonify, request, send_file, send_from_directory
from . import attachments

from .service import (
    DatasetPackageError,
    DatasetPackageService,
    MAX_PACKAGE_BYTES,
    PACKAGE_MIMETYPE,
)
from .delivery import DeliveryPackageService


def register_dataset_package_routes(
    app,
    project_store,
    dataset_lookup=None,
    dataset_names=None,
    on_import=None,
    asset_root=None,
):
    blueprint = Blueprint("dataset_package_api", __name__)
    service = DeliveryPackageService(
        project_store,
        dataset_lookup=dataset_lookup,
        dataset_names=dataset_names,
        on_import=on_import,
        asset_root=asset_root,
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
            data, filename, _ = service.export_package(dataset_id, data_only=request.args.get('data_only') == '1')
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
            data = uploaded_bytes()
            target = request.form.get('target_id')
            return jsonify(service.target_preview(data, target) if target else service.preflight(data))
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.post("/api/v2/ontology/dataset-packages/import")
    def import_package():
        try:
            result = service.import_delivery(
                uploaded_bytes(),
                request.form.get("target_name"),
                target_id=request.form.get('target_id') or None,
                expected=request.form.get('expected'),
                stopped=request.form.get('stopped') == 'true',
                origin=request.host_url.rstrip('/'),
            )
            return jsonify(result), 201
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.post('/api/v2/ontology/datasets/<dataset_id>/package-rollback')
    def rollback(dataset_id):
        try:
            return jsonify(service.rollback(dataset_id, (request.get_json(silent=True) or {}).get('stopped') is True))
        except DatasetPackageError as exc:
            return error_response(exc)

    @blueprint.post('/api/v2/ontology/datasets/<dataset_id>/package-bind')
    def bind_delivery(dataset_id):
        from ue_project_binding import bind_active_dataset, index_lookup, rebuild_index, _index_lock
        body = request.get_json(silent=True) or {}
        ue_id = str(body.get('ue_id') or '').strip()
        if dataset_id == 'demo':
            return error_response(DatasetPackageError('builtin_project', '内置项目不支持此操作', 400))
        if not ue_id or body.get('stopped') is not True:
            return error_response(DatasetPackageError('binding_confirmation_required', '请确认目标 UE 编号并停止运行', 409))
        with _index_lock:
            rebuild_index(project_store)
            previous = index_lookup(ue_id)
            for pid in {previous, dataset_id} - {None}:
                try:
                    service._require_offline(pid)
                except DatasetPackageError as exc:
                    return error_response(exc)
            if (previous or '') != str(body.get('expected_previous') or ''):
                return error_response(DatasetPackageError('binding_changed', 'UE 绑定已经变化，请刷新后重试', 409))
            ok, result = bind_active_dataset(project_store, ue_id, body.get('ue_name') or ue_id,
                                            force=body.get('replace') is True, target_project_id=dataset_id)
            if not ok:
                return jsonify(result), 409
            for pid in {previous, dataset_id} - {None}:
                project = project_store.read_project(pid)
                if project:
                    service._notify(project)
            return jsonify(result)

    @blueprint.get('/api/v2/project-assets/<project_id>/web/<path:filename>')
    def delivery_web(project_id, filename):
        if not project_store.read_project(project_id):
            return jsonify({'message': '项目不存在'}), 404
        try:
            root = attachments.project_dir(service.asset_root, project_id) / 'web'
            relative = attachments.safe_relative(filename)
            if not (root / relative).resolve().is_relative_to(root.resolve()):
                raise ValueError('资源路径越界')
            return send_from_directory(root, relative)
        except ValueError:
            return jsonify({'message': '资源路径无效'}), 400

    app.register_blueprint(blueprint)
    return service
