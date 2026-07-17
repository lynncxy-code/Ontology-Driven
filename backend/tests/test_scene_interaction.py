import os
import sys
import tempfile
import unittest
import copy

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scene_interaction.api import register_scene_interaction_routes
from scene_interaction.catalog import ResourceCatalog
from scene_interaction.service import RuntimeStatusRegistry, SceneInteractionService
from project_store import ProjectStore


def roaming_config():
    return {
        "enabled": True,
        "auto_enter": True,
        "character_id": "character.observer.base",
        "allowed_skin_ids": ["skin.observer.gray", "skin.observer.green"],
        "default_skin_id": "skin.observer.gray",
        "spawn": {
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        },
        "camera": {
            "default_mode": "near_follow",
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
        self.assertEqual("2026.07.3", catalog["catalog_version"])
        self.assertEqual(1, len(catalog["characters"]))
        self.assertGreaterEqual(len(catalog["skins"]), 2)
        self.assertEqual(1, len(catalog["spawn_anchors"]))
        self.assertEqual(1, len(catalog["routes"]))
        self.assertEqual(1, len(catalog["god_cameras"]))

    def test_save_anchor_does_not_require_calibration(self):
        saved = self.service.save_roaming(roaming_config(), 0)
        self.assertEqual({
            "mode": "ue_anchor",
            "anchor_id": "spawn.character.default",
        }, saved["config"]["spawn"])
        self.assertEqual("not_required", saved["calibration_state"]["state"])

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

    def test_runtime_projection_contains_ue_anchor(self):
        self.service.save_roaming(roaming_config(), 0)
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

    def test_http_binding_policy_and_heartbeat(self):
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
            "degraded_features": [],
            "error": None,
        })
        self.assertEqual(200, heartbeat.status_code)
        self.assertTrue(heartbeat.get_json()["runtime_status"]["online"])

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
        self.assertEqual("ue_project_unbound", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
