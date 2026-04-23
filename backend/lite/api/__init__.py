"""向 Flask app 注册所有 lite 模块路由。

每个 URL 路径只用一条 add_url_rule，与现有 @app.route 行为完全一致。
"""


def register_lite_routes(app):
    from .assets import assets_collection, asset_item, rebuild_usd
    from .instances import instances_collection, instance_item
    from .scenes import (scenes_collection, scene_detail, scene_ue_data,
                         scene_instances, scene_instance_remove,
                         scene_placements_update)
    from .export import scene_export, export_download

    # 一个 URL 路径 → 一条规则，methods 列表包含所有支持的 HTTP 方法
    app.add_url_rule("/api/v3/lite/assets",
                     endpoint="lite_assets_collection",
                     view_func=assets_collection,
                     methods=["GET", "POST"])

    app.add_url_rule("/api/v3/lite/assets/<file_number>",
                     endpoint="lite_asset_item",
                     view_func=asset_item,
                     methods=["DELETE"])

    app.add_url_rule("/api/v3/lite/assets/<file_number>/rebuild_usd",
                     endpoint="lite_asset_rebuild",
                     view_func=rebuild_usd,
                     methods=["POST"])

    app.add_url_rule("/api/v3/lite/instances",
                     endpoint="lite_instances_collection",
                     view_func=instances_collection,
                     methods=["GET", "POST"])

    app.add_url_rule("/api/v3/lite/instances/<instance_id>",
                     endpoint="lite_instance_item",
                     view_func=instance_item,
                     methods=["GET", "PUT", "DELETE"])

    app.add_url_rule("/api/v3/lite/scenes",
                     endpoint="lite_scenes_collection",
                     view_func=scenes_collection,
                     methods=["GET", "POST"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>",
                     endpoint="lite_scene_detail",
                     view_func=scene_detail,
                     methods=["GET"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>/ue_data",
                     endpoint="lite_scene_ue_data",
                     view_func=scene_ue_data,
                     methods=["GET"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>/instances",
                     endpoint="lite_scene_instances",
                     view_func=scene_instances,
                     methods=["POST"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>/placements/update",
                     endpoint="lite_scene_placements_update",
                     view_func=scene_placements_update,
                     methods=["POST"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>/instances/<instance_id>",
                     endpoint="lite_scene_instance_remove",
                     view_func=scene_instance_remove,
                     methods=["DELETE"])

    app.add_url_rule("/api/v3/lite/scenes/<scene_id>/export",
                     endpoint="lite_scene_export",
                     view_func=scene_export,
                     methods=["POST"])

    app.add_url_rule("/api/v3/lite/exports/<int:export_id>/download",
                     endpoint="lite_export_download",
                     view_func=export_download,
                     methods=["GET"])

    # 场景管理前端页面（M1-8）
    @app.route("/scenes")
    def scenes_page():
        from flask import send_from_directory
        import os
        scenes_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../frontend/scenes")
        )
        return send_from_directory(scenes_dir, "scenes.html")

    print("[Lite] 路由注册完成")
