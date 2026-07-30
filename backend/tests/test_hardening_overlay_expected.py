import os
import sys
import tempfile
import unittest

from flask import Flask

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from overlay.api import register_overlay_routes
from project_store import ProjectStore


def _overlay_config():
    return {
        "enabled": True,
        "template_id": "title_metrics",
        "display_mode": "selected",
        "anchor": {"strategy": "bounds_top", "offset_cm": {"x": 0, "y": 0, "z": 20}},
        "slots": {
            "title": {
                "required": True,
                "binding": {"source": "instance", "path": "display_name"},
                "format": {"empty_text": "--"},
            }
        },
    }


class OverlayExpectedProjectTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Overlay Test",
            project_id="overlay_test",
            object_types={
                "machine": {
                    "rid": "machine",
                    "name": "Machine",
                    "injected_interfaces": ["I3D_Representable", "I3D_Overlay"],
                }
            },
        )
        app = Flask(__name__)
        register_overlay_routes(app, self.store)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_save_type_wrong_expected_project_returns_409(self):
        resp = self.client.put(
            "/api/v2/overlays/object-types/machine",
            json={
                "config": _overlay_config(),
                "expected_revision": 0,
                "expected_project_id": "p_other",
            },
        )
        self.assertEqual(409, resp.status_code)
        body = resp.get_json()
        self.assertEqual("project changed", body.get("error"))
        self.assertEqual("p_other", body.get("expected"))
        self.assertEqual("overlay_test", body.get("actual"))

    def test_save_type_correct_expected_project_succeeds(self):
        resp = self.client.put(
            "/api/v2/overlays/object-types/machine",
            json={
                "config": _overlay_config(),
                "expected_revision": 0,
                "expected_project_id": "overlay_test",
            },
        )
        self.assertEqual(200, resp.status_code)

    def test_save_type_without_expected_project_succeeds(self):
        resp = self.client.put(
            "/api/v2/overlays/object-types/machine",
            json={"config": _overlay_config(), "expected_revision": 0},
        )
        self.assertEqual(200, resp.status_code)


if __name__ == "__main__":
    unittest.main()
