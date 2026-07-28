import os
import sys
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from realtime_channel import project_instance_realtime_channel
from scene_interaction.validators import SceneInteractionValidationError, validate_runtime_status


AGV_ID = "agv:agvfac000000001n01"


def runtime_status(active_source="websocket", targets=None, online=True):
    return {
        "online": online,
        "last_seen_at": "2026-07-17T00:00:00Z",
        "realtime_channel": {
            "enabled": True,
            "connection_state": "connected",
            "active_source": active_source,
            "last_frame_age_ms": 20,
            "frame_count": 12,
            "source_timestamp_ms": 1000,
            "target_count": len(targets or []),
            "applied_target_count": sum(1 for item in targets or [] if item.get("applied")),
            "targets": targets or [],
            "error": "",
        },
    }


class RealtimeChannelProjectionTests(unittest.TestCase):
    def test_non_websocket_instance_has_no_second_tag(self):
        self.assertIsNone(project_instance_realtime_channel("worker:01", None))

    def test_missing_ue_heartbeat_is_unknown(self):
        projected = project_instance_realtime_channel(AGV_ID, None)
        self.assertEqual("unknown", projected["state"])

    def test_fresh_applied_target_is_realtime(self):
        projected = project_instance_realtime_channel(AGV_ID, runtime_status(targets=[{
            "instance_id": AGV_ID,
            "state": "active",
            "applied": True,
        }]))
        self.assertEqual("realtime", projected["state"])

    def test_http_source_is_fallback(self):
        projected = project_instance_realtime_channel(
            AGV_ID, runtime_status(active_source="http_snapshot"),
        )
        self.assertEqual("http_fallback", projected["state"])

    def test_fresh_frame_without_applied_target_is_target_lost(self):
        projected = project_instance_realtime_channel(AGV_ID, runtime_status(targets=[]))
        self.assertEqual("target_lost", projected["state"])

    def test_runtime_validator_accepts_health_without_coordinates(self):
        normalized = validate_runtime_status({
            "runtime_state": "available",
            "realtime_channel": runtime_status()["realtime_channel"],
        })
        self.assertEqual("connected", normalized["realtime_channel"]["connection_state"])

    def test_runtime_validator_rejects_target_coordinates(self):
        payload = runtime_status(targets=[{
            "instance_id": AGV_ID,
            "state": "active",
            "applied": True,
            "x": 1,
        }])["realtime_channel"]
        with self.assertRaises(SceneInteractionValidationError):
            validate_runtime_status({
                "runtime_state": "available",
                "realtime_channel": payload,
            })


if __name__ == "__main__":
    unittest.main()
