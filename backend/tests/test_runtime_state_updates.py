import os
import sys
import tempfile
import time
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from project_store import ProjectStore
from snapshot_delta import _collect_instance_tokens


class RuntimeStateUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            projects_dir=os.path.join(self.tempdir.name, "projects"),
            active_file=os.path.join(self.tempdir.name, "active.json"),
        )
        self.store.create_project("hotfix", project_id="p-hotfix")
        self.store.spawn("one", "type-a", initial_position={})
        self.object_types = {
            "type-a": {"injected_interfaces": ["I3D_Spatial"]}
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def test_empty_patch_does_not_refresh_or_dirty_instance(self):
        before = self.store.get_instance_metadata("one")
        self.store._dirty = False

        self.assertTrue(self.store.update_raw_state("one", {}, persist=False))

        after = self.store.get_instance_metadata("one")
        self.assertEqual(before["last_seen"], after["last_seen"])
        self.assertFalse(self.store._dirty)

    def test_real_patch_replaces_raw_state_change_token(self):
        _, before = _collect_instance_tokens(
            self.store, None, self.object_types
        )

        self.assertTrue(self.store.update_raw_state(
            "one", {"translation_x": 25.0}, persist=False
        ))
        _, after = _collect_instance_tokens(
            self.store, None, self.object_types
        )

        self.assertNotEqual(before["one"], after["one"])

    def test_heartbeat_timestamp_alone_does_not_churn_online_token(self):
        _, before = _collect_instance_tokens(
            self.store, None, self.object_types
        )

        with self.store._lock:
            self.store._current["instances"]["one"]["last_seen"] = time.time()
        _, after = _collect_instance_tokens(
            self.store, None, self.object_types
        )

        self.assertEqual(before["one"], after["one"])

    def test_single_metadata_lookup_does_not_call_list_all(self):
        self.store.list_all = lambda: (_ for _ in ()).throw(
            AssertionError("list_all must not be used for a single lookup")
        )

        self.assertEqual(
            "type-a",
            self.store.get_instance_metadata("one")["object_type_rid"],
        )

    def test_explicit_heartbeat_refreshes_liveness_without_dirtying(self):
        with self.store._lock:
            self.store._current["instances"]["one"]["last_seen"] = 0.0
        self.store._dirty = False

        self.store.touch("one")

        after = self.store.get_instance_metadata("one")
        self.assertLess(time.time() - after["last_seen"], 1.0)
        self.assertFalse(self.store._dirty)


if __name__ == "__main__":
    unittest.main()
