import io
import os
import sys
import tempfile
import unittest

from flask import Flask

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import ProjectStore
from spatial_assets.api import register_spatial_asset_routes


def minimal_png(width=640, height=480):
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + int(width).to_bytes(4, "big")
        + int(height).to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


class SpatialAssetsHardeningTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Spatial Assets",
            project_id="spatial_assets",
            dataset={
                "id": "spatial_assets",
                "name": "Spatial Assets",
                "bound_ue_project_id": "ue-project-a",
            },
        )
        app = Flask(__name__)
        register_spatial_asset_routes(
            app, self.store, os.path.join(self.temp.name, "project_assets")
        )
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def _create_frame(self):
        response = self.client.post(
            "/api/v2/spatial-frames/assets",
            data={
                "file": (io.BytesIO(minimal_png()), "floor.png"),
                "name": "一层底图",
                "floor": "1",
                "floor_id": "floor-1",
                "ue_level": "/Game/Maps/Main",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(201, response.status_code, response.get_json())
        return response.get_json()["frame"]

    @staticmethod
    def _anchors():
        return [
            {"id": "a1", "source_px": [10, 10], "ue_world_cm": [100, 100, 20]},
            {"id": "a2", "source_px": [110, 10], "ue_world_cm": [200, 100, 20]},
            {"id": "a3", "source_px": [10, 110], "ue_world_cm": [100, 200, 20]},
            {"id": "a4", "source_px": [110, 110], "ue_world_cm": [200, 200, 20]},
        ]

    def _draft_body(self, **overrides):
        body = {
            "expected_draft_revision": 0,
            "floor": 1,
            "floor_id": "floor-1",
            "ue_level": "/Game/Maps/Main",
            "floor_reference_anchor_id": "a1",
            "anchors": self._anchors(),
        }
        body.update(overrides)
        return body

    def test_draft_wrong_expected_project_returns_409(self):
        frame_id = self._create_frame()["id"]
        resp = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json=self._draft_body(expected_project_id="p_other"),
        )
        self.assertEqual(409, resp.status_code, resp.get_json())
        body = resp.get_json()
        self.assertEqual("project changed", body.get("error"))
        self.assertEqual("p_other", body.get("expected"))
        self.assertEqual("spatial_assets", body.get("actual"))

    def test_draft_correct_expected_project_succeeds(self):
        frame_id = self._create_frame()["id"]
        resp = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json=self._draft_body(expected_project_id="spatial_assets"),
        )
        self.assertEqual(200, resp.status_code, resp.get_json())

    def test_draft_without_expected_project_succeeds(self):
        frame_id = self._create_frame()["id"]
        resp = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json=self._draft_body(),
        )
        self.assertEqual(200, resp.status_code, resp.get_json())

    def test_draft_does_not_persist_expected_project_id(self):
        frame_id = self._create_frame()["id"]
        resp = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json=self._draft_body(expected_project_id="spatial_assets"),
        )
        self.assertEqual(200, resp.status_code, resp.get_json())
        self.assertNotIn("expected_project_id", resp.get_json()["frame"])
        stored = self.store.get_active_copy()
        frame = next(f for f in stored["frames"] if f["id"] == frame_id)
        self.assertNotIn("expected_project_id", frame)


if __name__ == "__main__":
    unittest.main()
