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


def minimal_dxf():
    return b"0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n"


class SpatialAssetTestCase(unittest.TestCase):
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

    def test_upload_draft_publish_and_reload(self):
        created = self._create_frame()
        frame_id = created["id"]
        self.assertEqual("draft", created["status"])
        self.assertEqual(640, created["image"]["width_px"])
        self.assertNotIn("storage_name", created["image"])

        draft = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json={
                "expected_draft_revision": 0,
                "name": "一层底图",
                "floor": 1,
                "floor_id": "floor-1",
                "ue_level": "/Game/Maps/Main",
                "floor_reference_anchor_id": "a1",
                "anchors": self._anchors(),
            },
        )
        self.assertEqual(200, draft.status_code, draft.get_json())
        draft_frame = draft.get_json()["frame"]
        self.assertEqual(1, draft_frame["draft_revision"])
        self.assertEqual(20.0, draft_frame["floor_reference"]["ue_ground_z_cm"])
        self.assertIsNotNone(draft_frame["to_canonical"])

        published = self.client.post(
            f"/api/v2/spatial-frames/{frame_id}/publish",
            json={"expected_draft_revision": 1},
        )
        self.assertEqual(200, published.status_code, published.get_json())
        published_frame = published.get_json()["frame"]
        self.assertEqual("published", published_frame["status"])
        self.assertEqual(1, published_frame["calibration_revision"])
        self.assertTrue(published_frame["calibration_fingerprint"].startswith("sha256:"))

        floor = self.store.get_spatial_profile()["floor_table"][0]
        self.assertEqual(20.0, floor["ue_ground_z_cm"])
        self.assertEqual("/Game/Maps/Main", floor["ue_level"])

        image = self.client.get(f"/api/v2/spatial-frames/{frame_id}/image")
        self.assertEqual(200, image.status_code)
        self.assertEqual("image/png", image.mimetype)
        image.close()

        self.store.deactivate()
        self.assertTrue(self.store.activate("spatial_assets"))
        listing = self.client.get("/api/v2/spatial-frames")
        self.assertEqual(200, listing.status_code)
        self.assertEqual(frame_id, listing.get_json()["frames"][0]["id"])

    def test_publish_requires_ground_reference(self):
        frame = self._create_frame()
        frame_id = frame["id"]
        draft = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json={
                "expected_draft_revision": 0,
                "floor": 1,
                "floor_id": "floor-1",
                "ue_level": "/Game/Maps/Main",
                "anchors": self._anchors(),
            },
        )
        self.assertEqual(200, draft.status_code)
        response = self.client.post(
            f"/api/v2/spatial-frames/{frame_id}/publish",
            json={"expected_draft_revision": 1},
        )
        self.assertEqual(422, response.status_code)
        self.assertEqual("floor_reference_required", response.get_json()["error"])

    def test_publish_rejects_unconfigured_floor_without_creating_zero_height_row(self):
        frame = self._create_frame()
        frame_id = frame["id"]
        draft = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json={
                "expected_draft_revision": 0,
                "floor": 2,
                "floor_id": "floor-2",
                "ue_level": "/Game/Maps/Main",
                "floor_reference_anchor_id": "a1",
                "anchors": self._anchors(),
            },
        )
        self.assertEqual(200, draft.status_code, draft.get_json())

        response = self.client.post(
            f"/api/v2/spatial-frames/{frame_id}/publish",
            json={"expected_draft_revision": 1},
        )

        self.assertEqual(422, response.status_code, response.get_json())
        self.assertEqual("floor_not_configured", response.get_json()["error"])
        floors = self.store.get_spatial_profile()["floor_table"]
        self.assertFalse(any(item.get("floor") == 2 for item in floors))

    def test_publish_accepts_perspective_tolerance(self):
        frame = self._create_frame()
        anchors = self._anchors()
        anchors[3]["ue_world_cm"][0] += 160
        draft = self.client.put(
            f"/api/v2/spatial-frames/{frame['id']}/draft",
            json={
                "expected_draft_revision": 0,
                "floor": 1,
                "floor_id": "floor-1",
                "ue_level": "/Game/Maps/Main",
                "floor_reference_anchor_id": "a1",
                "anchors": anchors,
            },
        )
        self.assertEqual(200, draft.status_code, draft.get_json())
        metrics = draft.get_json()["frame"]["transform"]["metrics"]
        self.assertGreater(metrics["rmse_cm"], 20.0)
        self.assertLessEqual(metrics["rmse_cm"], 50.0)

        published = self.client.post(
            f"/api/v2/spatial-frames/{frame['id']}/publish",
            json={"expected_draft_revision": 1},
        )
        self.assertEqual(200, published.status_code, published.get_json())
        self.assertEqual("published", published.get_json()["frame"]["status"])

    def test_draft_rejects_non_raw_image_coordinates(self):
        frame = self._create_frame()
        anchors = self._anchors()
        anchors[0]["source_px"] = [10, -10]
        response = self.client.put(
            f"/api/v2/spatial-frames/{frame['id']}/draft",
            json={
                "expected_draft_revision": 0,
                "floor": 1,
                "floor_id": "floor-1",
                "ue_level": "/Game/Maps/Main",
                "anchors": anchors,
            },
        )
        self.assertEqual(422, response.status_code)
        self.assertEqual("anchor_source_out_of_bounds", response.get_json()["error"])

    def test_upload_rejects_unsupported_content(self):
        response = self.client.post(
            "/api/v2/spatial-frames/assets",
            data={"file": (io.BytesIO(b"not an image"), "fake.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(415, response.status_code)
        self.assertEqual("image_format_unsupported", response.get_json()["error"])

    def test_cad_upload_draft_publish_reload_and_source(self):
        created = self.client.post(
            "/api/v2/spatial-frames/cad-assets",
            data={
                "file": (io.BytesIO(minimal_dxf()), "plant.dxf"),
                "name": "厂房 CAD",
                "floor": "1",
                "floor_id": "floor-1",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(201, created.status_code, created.get_json())
        frame = created.get_json()["frame"]
        frame_id = frame["id"]
        self.assertEqual("cad", frame["kind"])
        self.assertEqual("draft", frame["status"])
        self.assertNotIn("storage_name", frame["cad"])

        anchors = [
            {"id": "c1", "source_xy_mm": [0, 0], "ue_world_cm": [10, 20]},
            {"id": "c2", "source_xy_mm": [1000, 0], "ue_world_cm": [110, 20]},
            {"id": "c3", "source_xy_mm": [0, 1000], "ue_world_cm": [10, 120]},
        ]
        draft = self.client.put(
            f"/api/v2/spatial-frames/{frame_id}/draft",
            json={
                "expected_draft_revision": 0,
                "name": "厂房 CAD",
                "floor": 1,
                "floor_id": "floor-1",
                "anchors": anchors,
                "canonical_origin": [100, 200],
                "display": {"rotation_deg": 90, "flip": False},
            },
        )
        self.assertEqual(200, draft.status_code, draft.get_json())
        draft_frame = draft.get_json()["frame"]
        self.assertEqual(1, draft_frame["draft_revision"])
        self.assertIsNotNone(draft_frame["to_ue"])
        self.assertEqual(-100.0, draft_frame["to_canonical"]["matrix"][0][2])

        published = self.client.post(
            f"/api/v2/spatial-frames/{frame_id}/publish",
            json={"expected_draft_revision": 1},
        )
        self.assertEqual(200, published.status_code, published.get_json())
        published_frame = published.get_json()["frame"]
        self.assertEqual("published", published_frame["status"])
        self.assertEqual(1, published_frame["calibration_revision"])
        self.assertTrue(published_frame["calibration_fingerprint"].startswith("sha256:"))

        profile = self.store.get_spatial_profile()
        self.assertEqual([100.0, 200.0], profile["canonical_origin"])
        self.assertAlmostEqual(20.0, profile["ue_transform"]["matrix"][0][2], places=4)
        self.assertAlmostEqual(40.0, profile["ue_transform"]["matrix"][1][2], places=4)

        source = self.client.get(f"/api/v2/spatial-frames/{frame_id}/source")
        self.assertEqual(200, source.status_code)
        self.assertEqual(minimal_dxf(), source.data)
        source.close()

        listing = self.client.get("/api/v2/spatial-frames?kind=cad")
        self.assertEqual(200, listing.status_code, listing.get_json())
        self.assertEqual(frame_id, listing.get_json()["frames"][0]["id"])

    def test_cad_publish_requires_three_non_collinear_anchors(self):
        created = self.client.post(
            "/api/v2/spatial-frames/cad-assets",
            data={"file": (io.BytesIO(minimal_dxf()), "plant.dxf")},
            content_type="multipart/form-data",
        ).get_json()["frame"]
        draft = self.client.put(
            f"/api/v2/spatial-frames/{created['id']}/draft",
            json={
                "expected_draft_revision": 0,
                "anchors": [
                    {"id": "c1", "source_xy_mm": [0, 0], "ue_world_cm": [0, 0]},
                    {"id": "c2", "source_xy_mm": [100, 0], "ue_world_cm": [10, 0]},
                ],
            },
        )
        self.assertEqual(200, draft.status_code, draft.get_json())
        published = self.client.post(
            f"/api/v2/spatial-frames/{created['id']}/publish",
            json={"expected_draft_revision": 1},
        )
        self.assertEqual(422, published.status_code, published.get_json())
        self.assertEqual("anchors_insufficient", published.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
