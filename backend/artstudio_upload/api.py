from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request

from .service import ArtStudioUploadError, ArtStudioUploadService


def _same_origin_request():
    origin = request.headers.get("Origin")
    if not origin:
        return True
    origin_parts = urlsplit(origin)
    host_parts = urlsplit(request.host_url)
    return (
        origin_parts.scheme.lower() == host_parts.scheme.lower()
        and origin_parts.netloc.lower() == host_parts.netloc.lower()
    )


def register_artstudio_upload_routes(
    app,
    artstudio_client,
    base_url,
    timeout=5,
    max_size_bytes=500 * 1024 * 1024,
):
    blueprint = Blueprint("artstudio_upload_api", __name__)
    service = ArtStudioUploadService(
        base_url,
        artstudio_client,
        timeout=timeout,
        max_size_bytes=max_size_bytes,
    )

    @blueprint.post("/api/v2/assets/uploads")
    def upload_asset():
        if not _same_origin_request():
            return jsonify({
                "error": "asset_upload_origin_rejected",
                "message": "请从当前 OntoTwin 页面上传模型。",
            }), 403
        try:
            result = service.upload(
                request.files.get("file"),
                request.form.get("name"),
                request.form.get("visibility", "public"),
                request.form.get("description", ""),
            )
            return jsonify(result), 201
        except ArtStudioUploadError as exc:
            return jsonify({
                "error": exc.code,
                "message": str(exc),
                "fields": exc.fields,
            }), exc.status

    app.register_blueprint(blueprint)
    return service
