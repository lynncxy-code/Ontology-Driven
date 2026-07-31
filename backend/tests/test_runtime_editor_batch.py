import os
import sys
import tempfile
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from project_store import ProjectStore
from writeback import apply_batch_writeback, runtime_edit_state_hash


def transform(x, y=0.0, z=0.0, yaw=0.0):
    return {
        "tx": x, "ty": y, "tz": z,
        "rx": 0.0, "ry": 0.0, "rz": yaw,
        "sx": 1.0, "sy": 1.0, "sz": 1.0,
    }


class RuntimeEditorBatchTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.projects_dir = os.path.join(self.temp.name, "projects")
        self.active_file = os.path.join(self.temp.name, "active.json")
        self.store = ProjectStore(self.projects_dir, self.active_file)
        self.store.create_project(
            "Runtime Editor",
            project_id="runtime_editor",
            object_types={"ot:test": {"name": "Test Device"}},
        )
        self.store.spawn("a", "ot:test", {"x": 0, "y": 0, "z": 0})
        self.store.spawn("b", "ot:test", {"x": 10, "y": 0, "z": 0})

    def tearDown(self):
        self.temp.cleanup()

    def change(self, instance_id, x, is_loaded=True):
        raw = self.store.get_raw_state(instance_id)
        return {
            "instance_id": instance_id,
            "expected_state_hash": runtime_edit_state_hash(raw),
            "transform": transform(x),
            "is_loaded": is_loaded,
        }

    def test_batch_saves_all_changes_once(self):
        ok, info, status = apply_batch_writeback(self.store, [
            self.change("a", 100.0),
            self.change("b", 200.0, is_loaded=False),
        ])

        self.assertTrue(ok)
        self.assertEqual(200, status)
        self.assertEqual(2, info["count"])
        self.assertEqual(100.0, self.store.get_raw_state("a")["translation_x"])
        self.assertEqual(200.0, self.store.get_raw_state("b")["translation_x"])
        self.assertFalse(self.store.get_raw_state("b")["is_loaded"])

        reloaded = ProjectStore(self.projects_dir, self.active_file)
        self.assertEqual(100.0, reloaded.get_raw_state("a")["translation_x"])
        self.assertFalse(reloaded.get_raw_state("b")["is_loaded"])

    def test_conflict_rolls_back_entire_batch(self):
        first = self.change("a", 100.0)
        second = self.change("b", 200.0)
        self.store.update_raw_state("b", {"translation_x": 99.0}, persist=True)

        ok, info, status = apply_batch_writeback(self.store, [first, second])

        self.assertFalse(ok)
        self.assertEqual(409, status)
        self.assertEqual("runtime_edit_conflict", info["error"])
        self.assertEqual(0.0, self.store.get_raw_state("a")["translation_x"])
        self.assertEqual(99.0, self.store.get_raw_state("b")["translation_x"])

    def test_disabled_instance_rejects_entire_batch(self):
        first = self.change("a", 100.0)
        self.store.update_raw_state(
            "b", {"runtime_spatial_editable": False}, persist=True)
        second = self.change("b", 200.0)

        ok, info, status = apply_batch_writeback(self.store, [first, second])

        self.assertFalse(ok)
        self.assertEqual(403, status)
        self.assertEqual("runtime_spatial_edit_disabled", info["error"])
        self.assertEqual(0.0, self.store.get_raw_state("a")["translation_x"])

    def test_batch_limit_is_enforced_before_mutation(self):
        ok, info, status = apply_batch_writeback(
            self.store, [self.change("a", 1.0), self.change("b", 2.0)], max_changes=1)

        self.assertFalse(ok)
        self.assertEqual(400, status)
        self.assertEqual("too_many_changes", info["error"])


if __name__ == "__main__":
    unittest.main()
