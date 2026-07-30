import os
import sys
import tempfile
import unittest

from flask import Flask

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from scene_interaction.api import register_scene_interaction_routes
from project_store import ProjectStore


class SceneExpectedProjectTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Scene Test",
            project_id="scene_test",
        )
        app = Flask(__name__)
        register_scene_interaction_routes(app, self.store)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_save_roaming_wrong_expected_project_returns_409(self):
        resp = self.client.put(
            "/api/v2/scene-interactions/roaming",
            json={
                "config": {},
                "expected_revision": 0,
                "expected_project_id": "p_other",
            },
        )
        self.assertEqual(409, resp.status_code)
        body = resp.get_json()
        self.assertEqual("project changed", body.get("error"))
        self.assertEqual("p_other", body.get("expected"))
        self.assertEqual("scene_test", body.get("actual"))

    def test_save_roaming_without_expected_project_skips_guard(self):
        # No expected_project_id -> guard not triggered; may fail validation
        # but must NOT be a 409 project-changed response.
        resp = self.client.put(
            "/api/v2/scene-interactions/roaming",
            json={"config": {}, "expected_revision": 0},
        )
        self.assertNotEqual(409, resp.status_code)


if __name__ == "__main__":
    unittest.main()
