import unittest

from backend.tools.ue_replacement import (
    apply_declared_replacement,
    instance_ids_hash,
    manifest_hashes,
    validate_apply_manifest,
    validate_declared_scope,
    validate_input_consistency,
    validate_project_identity,
)


class DeclarativeReplacementTests(unittest.TestCase):
    def test_scope_requires_explicit_ids_and_source_guids(self):
        instances = {
            "old-a": {"source": "ue_migrated", "ext_guid": "GUID-A"},
            "manual": {"source": "manual", "ext_guid": "GUID-M"},
        }
        old, guids = validate_declared_scope(
            {"old_instance_ids": ["old-a"], "source_actor_guids": ["GUID-A"]},
            instances,
        )
        self.assertEqual(old, ["old-a"])
        self.assertEqual(guids, ["GUID-A"])
        with self.assertRaises(SystemExit):
            validate_declared_scope({"old_instance_ids": ["old-a"]}, instances)
        with self.assertRaises(SystemExit):
            validate_declared_scope(
                {"old_instance_ids": ["manual"], "source_actor_guids": ["GUID-M"]},
                instances,
            )

    def test_project_identity_and_input_consistency_are_explicit(self):
        payload = {
            "project_id": "ds-a",
            "ue_project_id": "ueproj-a",
            "ue_project_name": "Demo",
            "actors": [{"ext_guid": "GUID-A", "type_rid": "ot-a"}],
        }
        validate_project_identity(
            payload,
            "ds-a",
            bound_ue_project_id="ueproj-a",
            bound_ue_project_name="Demo",
        )
        actors, guids = validate_input_consistency(
            payload,
            {"ot-a": {"name": "Type A"}},
            actor_type_resolver=lambda actor: actor["type_rid"],
        )
        self.assertEqual(len(actors), 1)
        self.assertEqual(guids, ["GUID-A"])
        bad = dict(payload, project_id="ds-other")
        with self.assertRaises(SystemExit):
            validate_project_identity(
                bad,
                "ds-a",
                bound_ue_project_id="ueproj-a",
                bound_ue_project_name="Demo",
            )

    def test_apply_requires_manifest_fields_and_exact_scope(self):
        instances = {
            "old-a": {"source": "ue_migrated", "ext_guid": "GUID-A"},
            "manual": {"source": "manual", "ext_guid": "GUID-M"},
            "new-a": {"source": "ue_migrated", "ext_guid": "NEW-A"},
        }
        stats = {"blocked": 0, "skipped": 0, "legacy": 0, "replaced": 0}
        cleanup, result = apply_declared_replacement(
            {
                "old_instance_ids": ["old-a"],
                "source_actor_guids": ["GUID-A"],
                "expected_old_instance_count": 1,
                "expected_new_instance_count": 1,
                "new_instance_ids_hash": instance_ids_hash(["new-a"]),
                "expected_delete_actor_guid_count": 1,
            },
            instances,
            {"GUID-NEW": "new-a"},
            stats,
            [],
        )
        self.assertEqual(cleanup, ["GUID-A"])
        self.assertNotIn("old-a", instances)
        self.assertEqual(result["old_instance_count"], 1)
        self.assertEqual(stats["replaced"], 1)

    def test_manifest_hashes_and_strict_apply_gate(self):
        payload = {"project_id": "ds-a", "actors": [{"ext_guid": "GUID-A"}]}
        hashes = manifest_hashes(
            payload,
            {"ot-a": {"name": "Type A"}},
            replaced_live_instance_ids=["old-a"],
            final_instance_ids=["manual", "new-a"],
            new_instance_ids=["new-a"],
            final_instance_count=2,
            final_type_count=1,
        )
        expected = {
            "project_before_digest": "sha256:before",
            **hashes,
        }
        validate_apply_manifest(expected, expected)
        with self.assertRaises(SystemExit):
            validate_apply_manifest(expected, {**expected, "input_digest": "sha256:changed"})


if __name__ == "__main__":
    unittest.main()
