from flask import Blueprint, jsonify, request

from ue_project_binding import request_ue_project

from .service import AssetCatalogError, UEAssetCatalogService


def register_ue_asset_catalog_routes(app, project_store, catalog_root=None):
    blueprint = Blueprint("ue_asset_catalog_api", __name__)
    service = UEAssetCatalogService(project_store, catalog_root)

    def execute(action, success_status=200):
        try:
            return jsonify(action()), success_status
        except AssetCatalogError as exc:
            return jsonify({"error": exc.code, "message": str(exc)}), exc.status
        except (TypeError, ValueError) as exc:
            return jsonify({"error": "invalid_request", "message": str(exc)}), 400

    @blueprint.post("/api/v2/ue/assets/catalog")
    def replace_catalog():
        payload = request.get_json(silent=True) or {}
        ue = request_ue_project(request)
        return execute(lambda: service.replace_catalog(payload, ue), 201)

    @blueprint.get("/api/v2/ue/assets/catalog")
    def get_catalog():
        return execute(lambda: service.get_catalog(request.args.get("ue_project_id")))

    @blueprint.post("/api/v2/ue/assets/recommend")
    def recommend_assets():
        payload = request.get_json(silent=True) or {}
        return execute(lambda: service.recommend(payload))

    @blueprint.post("/api/v2/ue/assets/confirmations")
    def remember_confirmations():
        payload = request.get_json(silent=True) or {}
        return execute(lambda: service.remember_confirmations(payload))

    app.register_blueprint(blueprint)
    return service
