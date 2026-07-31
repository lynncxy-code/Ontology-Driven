import os
import sys
import tempfile
import unittest
from unittest import mock


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

import app as app_module  # noqa: E402
from project_store import ProjectStore  # noqa: E402


class BindingComponentApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Binding Components",
            object_types={"test.rotor": {"rid": "test.rotor", "name": "旋翼航空器"}},
            project_id="binding_components",
        )
        self.store_patch = mock.patch.object(app_module, "project_store", self.store)
        self.store_patch.start()
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.store_patch.stop()
        self.temp.cleanup()

    def test_delete_bound_component_preserves_running_instance(self):
        self.store.set_components({
            "cmp_image": {
                "id": "cmp_image",
                "object_type_rid": "test.rotor",
                "source_mode": "image",
                "source_label": "image:test-source",
                "bound_instance_id": "vehicle_01",
            }
        })
        self.store.spawn("vehicle_01", "test.rotor")

        response = self.client.delete("/api/v2/binding/components/cmp_image")

        self.assertEqual(200, response.status_code, response.get_json())
        self.assertEqual("vehicle_01", response.get_json()["bound_instance_id"])
        self.assertEqual({}, self.store.get_components())
        self.assertEqual(["vehicle_01"], [item["id"] for item in self.store.list_all()])

    def test_empty_image_save_clears_only_current_source(self):
        self.store.set_components({
            "cmp_image": {
                "id": "cmp_image",
                "source_mode": "image",
                "source_label": "image:test-source",
            },
            "cmp_cad": {
                "id": "cmp_cad",
                "source_mode": "dxf",
                "source_label": "hall.dxf",
            },
        })

        response = self.client.post("/api/v2/coord/save_components", json={
            "mode": "image",
            "source_label": "image:test-source",
            "transform_matrix": [[1, 0, 0], [0, 1, 0]],
            "items": [],
        })

        self.assertEqual(200, response.status_code, response.get_json())
        self.assertEqual(0, response.get_json()["source_saved"])
        self.assertEqual(1, response.get_json()["removed"])
        self.assertEqual(["cmp_cad"], list(self.store.get_components()))


if __name__ == "__main__":
    unittest.main()
