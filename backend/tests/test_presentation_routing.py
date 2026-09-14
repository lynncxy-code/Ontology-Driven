import os
import sys
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from presentation_routing import (
    build_presentation,
    normalize_industrial,
    profile_fingerprint,
    profile_from_object_type,
    resolve_presentation,
)


class PresentationRoutingTestCase(unittest.TestCase):
    def test_normalizes_state_modifiers_and_actions(self):
        intent = normalize_industrial(
            {
                "status": "running",
                "battery_level": 12,
                "maintenance_mode": True,
                "presentation_actions": [
                    {"id": "industrial.start_pulse", "event_id": "evt-1"}
                ],
                "state_revision": 7,
            },
            "agv-1",
        )
        self.assertEqual("industrial.machine.running", intent["primary_state"]["id"])
        self.assertEqual(7, intent["presentation_revision"])
        self.assertEqual("evt-1", intent["actions"][0]["event_id"])
        self.assertEqual(
            {"industrial.low_battery", "industrial.maintenance"},
            {item["id"] for item in intent["modifiers"]},
        )

    def test_project_route_wins_per_channel_and_platform_fills_other_channels(self):
        result = build_presentation(
            "crane-1",
            {"status": "running"},
            {
                "version": "1.0",
                "channels": {
                    "animation": {
                        "slot": "motion",
                        "states": {
                            "industrial.machine.running": {
                                "behavior_id": "project.crane.running",
                                "slot": "motion",
                            }
                        },
                    }
                },
            },
        )
        self.assertEqual("project", result["resolution"]["channels"]["animation"]["source"])
        self.assertEqual("project.crane.running", result["resolution"]["channels"]["animation"]["behavior_id"])
        self.assertEqual("safe_fallback", result["resolution"]["channels"]["label"]["source"])
        self.assertEqual("safe_fallback", result["resolution"]["channels"]["fx"]["source"])

    def test_modifier_conflict_is_deterministic(self):
        intent = normalize_industrial({"status": "fault", "battery_level": 10}, "machine")
        result = resolve_presentation(intent)
        self.assertEqual("industrial.visual.critical", result["channels"]["visual"]["behavior_id"])
        self.assertEqual(
            ["industrial.critical", "industrial.low_battery"],
            [item["id"] for item in intent["modifiers"]],
        )

    def test_profile_fingerprint_changes_when_profile_changes(self):
        first = {"channels": {"animation": {"behavior_id": "project.a"}}}
        second = {"channels": {"animation": {"behavior_id": "project.b"}}}
        self.assertNotEqual(profile_fingerprint(first), profile_fingerprint(second))

    def test_modifier_channel_scope_is_respected(self):
        intent = normalize_industrial({"status": "warning", "battery_level": 10}, "machine")
        result = resolve_presentation(intent)
        self.assertEqual([], result["channels"]["animation"]["modifier_ids"])
        self.assertIn("industrial.warning", result["channels"]["visual"]["modifier_ids"])
        self.assertIn("industrial.low_battery", result["channels"]["fx"]["modifier_ids"])

    def test_same_input_produces_stable_wire_payload(self):
        first = build_presentation("machine-1", {"status": "running"})
        second = build_presentation("machine-1", {"status": "running"})
        self.assertEqual(first, second)

    def test_user_selectable_safe_fallback_disables_platform_library(self):
        result = build_presentation(
            "machine-1",
            {"status": "fault", "battery_level": 10},
            {"version": "1.0", "normalization_profile": "industrial.v1", "behavior_library": "safe_fallback"},
        )
        self.assertTrue(all(
            channel["source"] == "safe_fallback"
            for channel in result["resolution"]["channels"].values()
        ))

    def test_profile_reads_existing_interface_config_extension_point(self):
        profile = {"version": "1.0", "channels": {"visual": {"behavior_id": "project.warn"}}}
        self.assertEqual(
            profile,
            profile_from_object_type({"interface_configs": {"I3D_Presentation": {"presentation_profile": profile}}}),
        )


if __name__ == "__main__":
    unittest.main()
