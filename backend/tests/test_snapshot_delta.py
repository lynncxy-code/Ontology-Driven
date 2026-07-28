import copy
import os
import sys
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from snapshot_delta import SCHEMA_VERSION, SnapshotDeltaService


def full_snapshot(instance_id, x=0.0, overlay="ready", render_parts=None):
    return {
        "instanceId": instance_id,
        "displayName": instance_id,
        "timestamp": 123.0,
        "raw_state": {"translation_x": x},
        "interfaces": {
            "I3D_Representable": {
                "asset_id": f"/Game/{instance_id}",
                "is_visible": True,
                "render_parts": render_parts or [{"asset_path": f"/Game/{instance_id}_part"}],
            },
            "I3D_Spatial": {
                "translation_x": x,
                "translation_y": 0.0,
                "translation_z": 0.0,
                "rotation_x": 0.0,
                "rotation_y": 0.0,
                "rotation_z": 0.0,
                "scale_x": 1.0,
                "scale_y": 1.0,
                "scale_z": 1.0,
            },
            "I3D_Overlay": {"resolved_slots": {"body": {"display_value": overlay}}},
        },
    }


class SnapshotDeltaServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.service = SnapshotDeltaService(max_history=2)
        self.snapshots = {"one": full_snapshot("one")}
        self.tokens = {"one": (1, True)}

    def build(self, instance_id):
        value = self.snapshots.get(instance_id)
        return copy.deepcopy(value) if value is not None else None

    def poll(self, cursor=None):
        return self.service.poll(
            project_id="project",
            scope_id="project\x1f",
            cursor=cursor,
            tokens=self.tokens,
            build_snapshot=self.build,
        )

    def test_first_poll_returns_reset_full_baseline(self):
        result = self.poll()
        self.assertEqual(SCHEMA_VERSION, result["schemaVersion"])
        self.assertEqual("reset", result["mode"])
        self.assertEqual("missing_cursor", result["resetReason"])
        self.assertEqual(["one"], [item["instanceId"] for item in result["upserts"]])

    def test_unchanged_poll_returns_empty_delta(self):
        baseline = self.poll()
        result = self.poll(baseline["cursor"])
        self.assertEqual("delta", result["mode"])
        self.assertEqual([], result["upserts"])
        self.assertEqual([], result["deletedIds"])

    def test_spatial_change_does_not_repeat_render_parts_or_overlay(self):
        baseline = self.poll()
        self.snapshots["one"] = full_snapshot("one", x=25.0)
        self.tokens["one"] = (2, True)

        result = self.poll(baseline["cursor"])

        self.assertEqual("delta", result["mode"])
        self.assertEqual(1, len(result["upserts"]))
        patch = result["upserts"][0]
        self.assertEqual({"I3D_Spatial"}, set(patch["interfaces"]))
        self.assertNotIn("raw_state", patch)
        self.assertNotIn("timestamp", patch)

    def test_overlay_change_does_not_repeat_spatial_or_render_parts(self):
        baseline = self.poll()
        self.snapshots["one"] = full_snapshot("one", overlay="alarm")
        self.tokens["one"] = (2, True)

        result = self.poll(baseline["cursor"])

        patch = result["upserts"][0]
        self.assertEqual({"I3D_Overlay"}, set(patch["interfaces"]))

    def test_delete_is_explicit(self):
        baseline = self.poll()
        self.snapshots.pop("one")
        self.tokens.pop("one")

        result = self.poll(baseline["cursor"])

        self.assertEqual([], result["upserts"])
        self.assertEqual(["one"], result["deletedIds"])

    def test_new_instance_is_full_snapshot(self):
        baseline = self.poll()
        self.snapshots["two"] = full_snapshot("two")
        self.tokens["two"] = (1, True)

        result = self.poll(baseline["cursor"])

        created = next(item for item in result["upserts"] if item["instanceId"] == "two")
        self.assertIn("I3D_Representable", created["interfaces"])
        self.assertIn("render_parts", created["interfaces"]["I3D_Representable"])

    def test_multiple_revisions_merge_interfaces_for_lagging_client(self):
        baseline = self.poll()
        self.snapshots["one"] = full_snapshot("one", x=10.0)
        self.tokens["one"] = (2, True)
        first = self.poll(baseline["cursor"])
        self.snapshots["one"] = full_snapshot("one", x=10.0, overlay="alarm")
        self.tokens["one"] = (3, True)
        self.poll(first["cursor"])

        result = self.poll(baseline["cursor"])

        patch = result["upserts"][0]
        self.assertEqual({"I3D_Spatial", "I3D_Overlay"}, set(patch["interfaces"]))

    def test_expired_history_returns_reset(self):
        baseline = self.poll()
        cursor = baseline["cursor"]
        for revision in range(2, 5):
            self.snapshots["one"] = full_snapshot("one", x=float(revision))
            self.tokens["one"] = (revision, True)
            latest = self.poll(cursor)
            cursor = latest["cursor"]

        result = self.poll(baseline["cursor"])
        self.assertEqual("reset", result["mode"])
        self.assertEqual("history_expired", result["resetReason"])

    def test_removed_interface_rotates_stream_and_returns_reset(self):
        baseline = self.poll()
        changed = full_snapshot("one")
        changed["interfaces"].pop("I3D_Overlay")
        self.snapshots["one"] = changed
        self.tokens["one"] = (2, True)

        result = self.poll(baseline["cursor"])

        self.assertEqual("reset", result["mode"])
        self.assertEqual("structural_change", result["resetReason"])
        self.assertNotEqual(baseline["streamId"], result["streamId"])

    def test_project_switch_discards_previous_stream(self):
        baseline = self.poll()
        result = self.service.poll(
            project_id="other",
            scope_id="other\x1f",
            cursor=baseline["cursor"],
            tokens={},
            build_snapshot=self.build,
        )
        self.assertEqual("reset", result["mode"])
        self.assertEqual("stream_mismatch", result["resetReason"])


if __name__ == "__main__":
    unittest.main()
