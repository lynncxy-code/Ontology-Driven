import os
import sys
import tempfile
import unittest
import copy

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from scene_interaction.api import register_scene_interaction_routes
from scene_interaction.catalog import ResourceCatalog
from scene_interaction.service import RuntimeStatusRegistry, SceneInteractionService
from project_store import ProjectStore


def roaming_config():
    return {
        "enabled": True,
        "auto_enter": True,
        "minimap": {"enabled": False},
        "character_id": "character.observer.base",
        "allowed_skin_ids": ["skin.observer.gray", "skin.observer.green"],
        "default_skin_id": "skin.observer.gray",
        "spawn": {
            "mode": "image",
            "frame_id": "frame_image",
            "source_px": {"x": 100.0, "y": 200.0},
            "yaw_deg": 0.0,
            "z_hint_mm": None,
        },
        "camera": {
            "default_mode": "near_follow",
            "first_person": {"eye_height_cm": 165, "fov_deg": 85, "look_sensitivity": 1},
            "near_follow": {"distance_cm": 120, "height_cm": 35, "look_sensitivity": 1},
            "god": {"camera_id": "camera.god.default", "move_speed_cm_s": 1800, "look_sensitivity": 1},
        },
        "movement": {
            "walk_speed_cm_s": 250,
            "sprint_speed_cm_s": 500,
            "auto_route_speed_cm_s": 180,
            "jump_height_cm": 80,
        },
        "route": {
            "enabled": True,
            "route_id": "route.test.default",
            "auto_start": True,
            "completion_mode": "stop",
            "takeover_enabled": True,
        },
    }


def image_roaming_config():
    config = copy.deepcopy(roaming_config())
    config["spawn"] = {
        "mode": "image",
        "frame_id": "frame_image",
        "source_px": {"x": 100.0, "y": 200.0},
        "yaw_deg": 90.0,
        "z_hint_mm": None,
    }
    return config


def project_route_payload():
    return {
        "name": "一层默认参观路线",
        "enabled": True,
        "frame_id": "frame_image",
        "loop": False,
        "speed_cm_s": 150,
        "waypoints": [
            {"id": "wp-1", "source_px": [100.0, 200.0]},
            {"id": "wp-2", "source_px": [300.0, 200.0]},
        ],
    }


class SceneInteractionTestCase(unittest.TestCase):
    def setUp(self):
        # 3.5：UE-ID 索引是模块级全局，测试间会串；每次清空+按本测试的 store 重建
        import ue_project_binding as _ub
        _ub._ue_index.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Scene Interaction",
            project_id=f"scene_{id(self)}",
            dataset={
                "id": f"scene_{id(self)}",
                "name": "Scene Interaction",
                "bound_ue_project_id": "ue-project-a",
                "bound_ue_project_name": "UE Project A",
            },
        )
        self.store.upsert_frame({
            "id": "frame_image",
            "name": "图片平面图",
            "kind": "image",
            "unit": "px",
            "floor": 1,
            "floor_id": "floor-1",
            "status": "published",
            "ue_level": "/Game/Maps/Main",
            "bound_ue_project_id": "ue-project-a",
            "image": {"width_px": 640, "height_px": 480, "sha256": "test"},
            "calibration_revision": 1,
            "calibration_fingerprint": "sha256:published-frame",
            "floor_reference": {"canonical_z_base_mm": 0, "ue_ground_z_cm": 20},
            "to_ue": {
                "method": "anchor",
                "matrix": [[0.2, 0, 0], [0, 0.2, 0], [0, 0, 1]],
            },
            "to_canonical": {
                "method": "anchor",
                "matrix": [[2, 0, 0], [0, 2, 0], [0, 0, 1]],
            },
        })
        profile = self.store.get_spatial_profile()
        profile["floor_table"][0]["ue_ground_z_cm"] = 20.0
        profile["floor_table"][0]["ue_level"] = "/Game/Maps/Main"
        self.store.set_spatial_profile(profile)
        self.catalog = ResourceCatalog()
        self.service = SceneInteractionService(
            self.store, self.catalog, RuntimeStatusRegistry(),
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_catalog_has_mvp_resources(self):
        catalog = self.service.catalog_snapshot()
        self.assertEqual("2026.07.9", catalog["catalog_version"])
        self.assertEqual(7, len(catalog["characters"]))
        self.assertGreaterEqual(len(catalog["skins"]), 8)
        self.assertEqual(1, len(catalog["spawn_anchors"]))
        self.assertEqual(1, len(catalog["routes"]))
        self.assertEqual(1, len(catalog["god_cameras"]))

    def test_renderpeople_catalog_contract(self):
        catalog = self.service.catalog_snapshot()
        characters = {item["id"]: item for item in catalog["characters"]}
        skins = {item["id"]: item for item in catalog["skins"]}
        names = ("Carla", "Claudia", "Eric", "Manuel", "Nathan", "Sophia")
        for name in names:
            key = name.lower()
            character_id = f"character.renderpeople.{key}"
            skin_id = f"skin.renderpeople.{key}.default"
            character = characters[character_id]
            skin = skins[skin_id]
            self.assertEqual(
                f"TwinCharacter:RenderPeople{name}",
                character["ue_primary_asset_id"],
            )
            self.assertEqual(character_id, skin["character_id"])
            self.assertEqual(
                f"TwinSkin:RenderPeople{name}Default",
                skin["ue_primary_asset_id"],
            )
            self.assertEqual(character["skeleton_id"], skin["skeleton_id"])

    def test_renderpeople_character_uses_only_its_own_skin(self):
        config = roaming_config()
        config["character_id"] = "character.renderpeople.carla"
        config["allowed_skin_ids"] = ["skin.renderpeople.carla.default"]
        config["default_skin_id"] = "skin.renderpeople.carla.default"
        saved = self.service.save_roaming(config, 0)
        self.assertEqual("character.renderpeople.carla", saved["config"]["character_id"])
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual(
            "TwinCharacter:RenderPeopleCarla",
            runtime["resources"]["character"]["ue_primary_asset_id"],
        )

        invalid = roaming_config()
        invalid["character_id"] = "character.renderpeople.carla"
        invalid["allowed_skin_ids"] = ["skin.renderpeople.nathan.default"]
        invalid["default_skin_id"] = "skin.renderpeople.nathan.default"
        with self.assertRaises(Exception) as mismatch:
            self.service.save_roaming(invalid, saved["revision"])
        paths = [item["path"] for item in mismatch.exception.errors]
        self.assertIn("allowed_skin_ids[0]", paths)
        self.assertIn("default_skin_id", paths)

    def test_save_converts_source_pixels_to_canonical_mm(self):
        saved = self.service.save_roaming(image_roaming_config(), 0)
        self.assertEqual(1, saved["revision"])
        spawn = saved["config"]["spawn"]
        # Default canonical->UE scale is 0.1. frame px->UE scale is 0.2.
        self.assertEqual({"x": 200.0, "y": 400.0}, spawn["canonical_position_mm"])
        self.assertTrue(spawn["calibration_fingerprint"].startswith("sha256:"))

    def test_revision_conflict_is_atomic(self):
        self.service.save_roaming(roaming_config(), 0)
        with self.assertRaises(Exception):
            self.service.save_roaming(roaming_config(), 0)
        self.assertEqual(1, self.store.get_scene_interactions()["revision"])

    def test_first_person_camera_is_normalized_and_projected(self):
        config = roaming_config()
        config["camera"]["default_mode"] = "first_person"
        config["camera"]["first_person"] = {
            "eye_height_cm": 172,
            "fov_deg": 92,
            "look_sensitivity": 1.4,
        }
        saved = self.service.save_roaming(config, 0)
        self.assertEqual("first_person", saved["config"]["camera"]["default_mode"])
        self.assertEqual(172, saved["config"]["camera"]["first_person"]["eye_height_cm"])
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual(92, runtime["config"]["camera"]["first_person"]["fov_deg"])

    def test_legacy_camera_receives_first_person_defaults(self):
        config = roaming_config()
        config["camera"].pop("first_person")
        saved = self.service.save_roaming(config, 0)
        self.assertEqual({
            "eye_height_cm": 165,
            "fov_deg": 85,
            "look_sensitivity": 1,
        }, saved["config"]["camera"]["first_person"])

    def test_legacy_camera_defaults_to_god_view(self):
        config = roaming_config()
        config["camera"].pop("default_mode")
        saved = self.service.save_roaming(config, 0)
        self.assertEqual("god", saved["config"]["camera"]["default_mode"])

    def test_first_person_camera_range_is_validated(self):
        config = roaming_config()
        config["camera"]["first_person"]["fov_deg"] = 120
        with self.assertRaises(Exception) as invalid:
            self.service.save_roaming(config, 0)
        self.assertIn(
            "camera.first_person.fov_deg",
            [item["path"] for item in invalid.exception.errors],
        )

    def test_minimap_defaults_off_and_projects_when_enabled(self):
        legacy = roaming_config()
        legacy.pop("minimap")
        saved = self.service.save_roaming(legacy, 0)
        self.assertEqual({"enabled": False}, saved["config"]["minimap"])

        enabled = copy.deepcopy(saved["config"])
        enabled["minimap"]["enabled"] = True
        saved = self.service.save_roaming(enabled, saved["revision"])
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual({"enabled": True}, saved["config"]["minimap"])
        self.assertEqual({"enabled": True}, runtime["config"]["minimap"])

    def test_minimap_rejects_non_boolean_enabled(self):
        config = roaming_config()
        config["minimap"] = {"enabled": "yes"}
        with self.assertRaises(Exception) as invalid:
            self.service.save_roaming(config, 0)
        self.assertIn(
            "minimap.enabled",
            [item["path"] for item in invalid.exception.errors],
        )

    def test_legacy_stored_roaming_is_read_with_minimap_default(self):
        legacy = roaming_config()
        legacy.pop("minimap")

        def inject_legacy(working):
            scene = working.setdefault("scene_interactions", {})
            scene["revision"] = 1
            scene["roaming"] = copy.deepcopy(legacy)

        self.store.transact_active(inject_legacy)
        self.assertEqual(
            {"enabled": False},
            self.service.get_roaming()["config"]["minimap"],
        )
        self.assertEqual(
            {"enabled": False},
            self.service.runtime_projection({"mode": "matched"})["config"]["minimap"],
        )

    def test_runtime_projection_contains_ue_anchor(self):
        legacy = roaming_config()
        legacy["spawn"] = {
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        }
        legacy["route"] = {
            "enabled": False,
            "route_id": "",
            "auto_start": False,
            "completion_mode": "stop",
            "takeover_enabled": True,
        }

        def inject_legacy(working):
            scene = working.setdefault("scene_interactions", {})
            scene["revision"] = 1
            scene["roaming"] = copy.deepcopy(legacy)

        self.store.transact_active(inject_legacy)
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual(1, runtime["revision"])
        self.assertTrue(runtime["config"]["enabled"])
        self.assertEqual({
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        }, runtime["config"]["spawn_ue"])
        self.assertEqual(
            "spawn.character.default",
            runtime["resources"]["spawn_anchor"]["ue_spawn_id"],
        )
        self.assertNotIn("spawn", runtime["config"])
        self.assertTrue(runtime["runtime_token"].startswith("sha256:"))

    def test_legacy_image_runtime_projection_contains_coordinates(self):
        self.service.save_roaming(image_roaming_config(), 0)
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual("coordinates", runtime["config"]["spawn_ue"]["mode"])
        self.assertEqual(20.0, runtime["config"]["spawn_ue"]["x_cm"])
        self.assertEqual(40.0, runtime["config"]["spawn_ue"]["y_cm"])

    def test_runtime_token_is_scoped_to_project(self):
        first = self.service.runtime_projection({"mode": "test"})["runtime_token"]
        cloned = self.store.get_active_copy()
        cloned["id"] = "another_project"
        from scene_interaction.runtime_projection import build_runtime_projection
        second = build_runtime_projection(
            cloned,
            cloned["scene_interactions"]["roaming"],
            self.service.catalog,
            cloned["scene_interactions"]["revision"],
        )["runtime_token"]
        self.assertNotEqual(first, second)

    def test_project_route_crud_default_and_runtime_projection(self):
        created = self.service.create_route(project_route_payload(), 0)
        route = created["route"]
        self.assertEqual("ready", route["review_state"])
        self.assertEqual([200.0, 400.0, 0.0], route["waypoints"][0]["canonical_position_mm"])
        self.assertEqual(1, route["revision"])

        defaulted = self.service.set_default_route(route["id"], created["revision"])
        config = roaming_config()
        config["route"]["route_id"] = route["id"]
        saved = self.service.save_roaming(config, defaulted["revision"])
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual(route["id"], runtime["runtime_route"]["route_id"])
        self.assertEqual(20.0, runtime["runtime_route"]["floor_ground_z_hint_cm"])
        self.assertEqual([20.0, 40.0, 20.0], runtime["runtime_route"]["waypoints_ue_cm"][0])
        self.assertEqual("project_route", runtime["resources"]["route"]["kind"])
        self.assertEqual(saved["revision"], runtime["revision"])

    def test_runtime_projection_lists_all_enabled_ready_routes(self):
        first = self.service.create_route(project_route_payload(), 0)
        second_payload = project_route_payload()
        second_payload["name"] = "东进西出"
        second_payload["waypoints"] = [
            {"id": "wp-3", "source_px": [120.0, 220.0]},
            {"id": "wp-4", "source_px": [340.0, 220.0]},
        ]
        second = self.service.create_route(second_payload, first["revision"])
        defaulted = self.service.set_default_route(
            first["route"]["id"], second["revision"],
        )
        config = roaming_config()
        config["route"]["route_id"] = first["route"]["id"]
        self.service.save_roaming(config, defaulted["revision"])

        runtime = self.service.runtime_projection({"mode": "matched"})
        routes = runtime["available_routes"]
        self.assertEqual(2, len(routes))
        self.assertEqual(
            {first["route"]["id"], second["route"]["id"]},
            {item["route_id"] for item in routes},
        )
        self.assertEqual(
            [first["route"]["id"]],
            [item["route_id"] for item in routes if item["is_default"]],
        )
        self.assertEqual(
            "东进西出",
            next(item["display_name"] for item in routes
                 if item["route_id"] == second["route"]["id"]),
        )
        self.assertTrue(all(len(item["waypoints_ue_cm"]) >= 2 for item in routes))

    def test_ready_project_route_supplies_spawn_without_manual_point(self):
        created = self.service.create_route(project_route_payload(), 0)
        route = created["route"]
        config = roaming_config()
        config.pop("spawn")
        config["route"].update({
            "route_id": route["id"],
            "auto_start": False,
        })

        saved = self.service.save_roaming(config, created["revision"])
        self.assertNotIn("spawn", saved["config"])
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertTrue(runtime["config"]["enabled"])
        self.assertEqual("not_required", runtime["calibration"]["state"])
        self.assertEqual({
            "mode": "coordinates",
            "source": "route_start",
            "route_id": route["id"],
            "x_cm": 20.0,
            "y_cm": 40.0,
            "trace_origin_z_cm": 1020.0,
            "yaw_deg": 0.0,
            "z_hint_cm": 20.0,
            "floor": 1,
        }, runtime["config"]["spawn_ue"])
        self.assertFalse(runtime["config"]["route"]["auto_start"])

    def test_ready_project_route_drops_invalid_optional_spawn_drafts(self):
        created = self.service.create_route(project_route_payload(), 0)
        config = roaming_config()
        config["route"]["route_id"] = created["route"]["id"]
        config["spawn"] = {
            "mode": "ue_anchor",
            "anchor_id": "spawn.anchor.no-longer-installed",
        }
        saved = self.service.save_roaming(config, created["revision"])
        self.assertNotIn("spawn", saved["config"])

        config["spawn"] = {
            "mode": "image",
            "frame_id": "frame_draft_not_published",
            "source_px": {"x": 10.0, "y": 20.0},
        }
        saved = self.service.save_roaming(config, saved["revision"])
        self.assertNotIn("spawn", saved["config"])

        config["spawn"] = {
            "mode": "image",
            "frame_id": "frame_image",
            "yaw_deg": 45.0,
        }
        saved = self.service.save_roaming(config, saved["revision"])
        self.assertNotIn("spawn", saved["config"])

    def test_ready_project_route_preserves_valid_manual_spawn_for_reuse(self):
        created = self.service.create_route(project_route_payload(), 0)
        config = roaming_config()
        config["route"]["route_id"] = created["route"]["id"]
        saved = self.service.save_roaming(config, created["revision"])
        self.assertEqual("image", saved["config"]["spawn"]["mode"])
        self.assertEqual(
            {"x": 100.0, "y": 200.0},
            saved["config"]["spawn"]["source_px"],
        )
        self.assertEqual(
            {"x": 200.0, "y": 400.0},
            saved["config"]["spawn"]["canonical_position_mm"],
        )
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertEqual("route_start", runtime["config"]["spawn_ue"]["source"])

    def test_no_project_route_requires_image_spawn_for_new_save(self):
        config = roaming_config()
        config.pop("spawn")
        config["route"].update({"enabled": False, "route_id": ""})
        with self.assertRaises(Exception) as missing:
            self.service.save_roaming(config, 0)
        self.assertIn("spawn", [item["path"] for item in missing.exception.errors])

        config["spawn"] = {
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        }
        with self.assertRaises(Exception) as legacy_anchor:
            self.service.save_roaming(config, 0)
        self.assertIn("spawn.mode", [item["path"] for item in legacy_anchor.exception.errors])

        config["spawn"] = {
            "mode": "image",
            "frame_id": "frame_image",
            "yaw_deg": 0.0,
        }
        with self.assertRaises(Exception) as partial_image:
            self.service.save_roaming(config, 0)
        self.assertIn(
            "spawn.source_px",
            [item["path"] for item in partial_image.exception.errors],
        )

    def test_enabled_route_with_empty_selection_is_invalid_not_manual(self):
        config = roaming_config()
        config["route"].update({"enabled": True, "route_id": ""})
        with self.assertRaises(Exception) as incomplete_route:
            self.service.save_roaming(config, 0)
        self.assertIn(
            "route.route_id",
            [item["path"] for item in incomplete_route.exception.errors],
        )

    def test_disabled_selected_project_route_blocks_manual_spawn_fallback(self):
        created = self.service.create_route(project_route_payload(), 0)
        config = roaming_config()
        config["route"]["route_id"] = created["route"]["id"]
        self.service.save_roaming(config, created["revision"])

        def disable_route(working):
            working["scene_interactions"]["routes"][0]["enabled"] = False

        self.store.transact_active(disable_route)
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertFalse(runtime["config"]["enabled"])
        self.assertEqual("default_route_invalid", runtime["blocked_reason"])
        self.assertNotIn("spawn_ue", runtime["config"])

    def test_route_needing_review_blocks_legacy_anchor_fallback(self):
        created = self.service.create_route(project_route_payload(), 0)
        config = roaming_config()
        config["spawn"] = {
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        }
        config["route"]["route_id"] = created["route"]["id"]
        self.service.save_roaming(config, created["revision"])

        def change_calibration(working):
            working["frames"][0]["calibration_fingerprint"] = "sha256:changed"

        self.store.transact_active(change_calibration)
        runtime = self.service.runtime_projection({"mode": "matched"})
        self.assertFalse(runtime["config"]["enabled"])
        self.assertEqual("default_route_needs_review", runtime["blocked_reason"])
        self.assertIsNone(runtime["runtime_route"])
        self.assertFalse(runtime["resources"]["route"]["runtime_ready"])
        self.assertNotIn("spawn_ue", runtime["config"])

    def test_route_requires_published_frame_and_two_points(self):
        payload = project_route_payload()
        payload["waypoints"] = payload["waypoints"][:1]
        with self.assertRaises(Exception):
            self.service.create_route(payload, 0)
        self.assertEqual(0, self.store.get_scene_interactions()["revision"])

    def test_route_http_endpoints(self):
        app = Flask(__name__)
        register_scene_interaction_routes(app, self.store)
        client = app.test_client()
        created = client.post("/api/v2/scene-interactions/routes", json={
            "expected_revision": 0,
            "route": project_route_payload(),
        })
        self.assertEqual(201, created.status_code, created.get_json())
        route_id = created.get_json()["route"]["id"]
        detail = client.get(f"/api/v2/scene-interactions/routes/{route_id}")
        self.assertEqual(200, detail.status_code)
        self.assertEqual(2, len(detail.get_json()["route"]["waypoints"]))
        defaulted = client.post(
            f"/api/v2/scene-interactions/routes/{route_id}/default",
            json={"expected_revision": 1},
        )
        self.assertEqual(200, defaulted.status_code)
        blocked_delete = client.delete(
            f"/api/v2/scene-interactions/routes/{route_id}",
            json={"expected_revision": 2},
        )
        self.assertEqual(409, blocked_delete.status_code)

    def test_calibration_change_marks_route_for_review(self):
        created = self.service.create_route(project_route_payload(), 0)
        route_id = created["route"]["id"]
        project = self.store.get_active_copy()
        project["frames"][0]["calibration_fingerprint"] = "sha256:changed"
        self.store.transact_active(lambda working: working.update({"frames": project["frames"]}))
        detail = self.service.get_route(route_id)
        self.assertEqual("needs_review", detail["route"]["review_state"])

    def test_project_coordinate_change_marks_route_for_review(self):
        created = self.service.create_route(project_route_payload(), 0)
        route_id = created["route"]["id"]
        profile = self.store.get_spatial_profile()
        profile["ue_transform"]["matrix"] = [
            [0.1, 0.0, 100.0],
            [0.0, 0.1, -50.0],
            [0.0, 0.0, 1.0],
        ]
        self.store.set_spatial_profile(profile)
        detail = self.service.get_route(route_id)
        self.assertEqual("needs_review", detail["route"]["review_state"])

    def test_calibration_change_blocks_runtime_until_review(self):
        self.service.save_roaming(image_roaming_config(), 0)
        before = self.service.runtime_projection({"mode": "matched"})
        self.store.upsert_frame({
            "id": "frame_image",
            "name": "图片平面图",
            "kind": "image",
            "unit": "px",
            "floor": 1,
            "to_ue": {
                "method": "anchor",
                "matrix": [[0.25, 0, 0], [0, 0.25, 0], [0, 0, 1]],
            },
        })
        after = self.service.runtime_projection({"mode": "matched"})
        self.assertNotEqual(before["runtime_token"], after["runtime_token"])
        self.assertFalse(after["config"]["enabled"])
        self.assertEqual("calibration_needs_review", after["blocked_reason"])
        self.assertEqual("needs_review", after["calibration"]["state"])

    def test_runtime_status_rejects_character_position(self):
        with self.assertRaises(Exception):
            self.service.report_runtime({
                "runtime_state": "manual",
                "applied_revision": 1,
                "position": {"x": 1, "y": 2, "z": 3},
            }, {"id": "ue-project-a", "name": "UE Project A"})

    def test_runtime_status_validates_minimap_state(self):
        status = self.service.report_runtime({
            "runtime_state": "manual",
            "applied_revision": 1,
            "minimap_state": "anchor_missing",
            "degraded_features": ["minimap_anchor_missing"],
        }, {"id": "ue-project-a", "name": "UE Project A"})
        self.assertEqual(
            "anchor_missing",
            status["runtime_status"]["minimap_state"],
        )

        with self.assertRaises(Exception) as invalid:
            self.service.report_runtime({
                "runtime_state": "manual",
                "applied_revision": 1,
                "minimap_state": "broken",
            }, {"id": "ue-project-a", "name": "UE Project A"})
        self.assertIn(
            "minimap_state",
            [item["path"] for item in invalid.exception.errors],
        )

    def test_http_binding_policy_and_heartbeat(self):
        # 3.5：UE 请求走 UE-ID→pid 索引；测试需先扫盘建索引（正式服由启动流程负责）
        import ue_project_binding as _ub
        _ub._ue_index.clear()
        _ub.rebuild_index(self.store)

        app = Flask(__name__)
        register_scene_interaction_routes(app, self.store)
        client = app.test_client()

        save = client.put("/api/v2/scene-interactions/roaming", json={
            "expected_revision": 0,
            "config": roaming_config(),
        })
        self.assertEqual(200, save.status_code)

        mismatch = client.get("/api/v2/scene-interactions/runtime", headers={
            "X-OntoTwin-UE-Project-Id": "ue-project-b",
            "X-OntoTwin-UE-Context": "packaged",
        })
        self.assertEqual(403, mismatch.status_code)
        # 3.5：错误码保 ue_project_mismatch 以兼容 UE 插件硬编码
        self.assertEqual("ue_project_mismatch", mismatch.get_json()["error"])

        matched_headers = {
            "X-OntoTwin-UE-Project-Id": "ue-project-a",
            "X-OntoTwin-UE-Project-Name": "UE Project A",
            "X-OntoTwin-UE-Context": "packaged",
        }
        runtime = client.get("/api/v2/scene-interactions/runtime", headers=matched_headers)
        self.assertEqual(200, runtime.status_code)
        self.assertEqual("matched", runtime.get_json()["binding"]["mode"])

        heartbeat = client.post("/api/v2/scene-interactions/runtime", headers=matched_headers, json={
            "applied_revision": 1,
            "pending_revision": None,
            "catalog_version": "2026.07.3",
            "runtime_state": "auto_route",
            "camera_mode": "near_follow",
            "route_state": "following",
            "active_skin_id": "skin.observer.gray",
            "minimap_state": "ready",
            "degraded_features": [],
            "error": None,
        })
        self.assertEqual(200, heartbeat.status_code)
        self.assertTrue(heartbeat.get_json()["runtime_status"]["online"])
        self.assertEqual("ready", heartbeat.get_json()["runtime_status"]["minimap_state"])

    def test_packaged_runtime_rejects_unbound_project(self):
        dataset = self.store.get_active_dataset().copy()
        dataset.pop("bound_ue_project_id", None)
        dataset.pop("bound_ue_project_name", None)
        self.store.set_dataset(dataset)
        app = Flask(__name__)
        register_scene_interaction_routes(app, self.store)
        response = app.test_client().get("/api/v2/scene-interactions/runtime", headers={
            "X-OntoTwin-UE-Project-Id": "ue-project-a",
            "X-OntoTwin-UE-Context": "packaged",
        })
        self.assertEqual(403, response.status_code)
        # 3.5：错误码统一走 ue_project_mismatch（兼容 UE 插件；覆盖旧的 unbound 语义）
        self.assertEqual("ue_project_mismatch", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
