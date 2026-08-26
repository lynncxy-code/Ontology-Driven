import unittest
import uuid

from flask import Flask

from external_data_control import (
    REALTIME_STREAM_CONTROL,
    RealtimeStreamControlRegistry,
    build_active_realtime_status,
    realtime_control_for_heartbeat,
    register_external_data_control_routes,
)


class FakeProjectStore:
    def __init__(self, project=None):
        self.project = project
        self.runtime_settings = {}

    def get_active_copy(self):
        return dict(self.project) if self.project else None

    def get_runtime_setting(self, key):
        return self.runtime_settings.get(key)

    def set_runtime_setting(self, key, value):
        self.runtime_settings[key] = dict(value)


class ExternalDataControlTests(unittest.TestCase):
    def setUp(self):
        self.database_id = f"test_{uuid.uuid4().hex}"
        self.project = {
            "id": self.database_id,
            "name": "测试 Database",
            "bound_ue_project_id": "ueproj_Test",
            "bound_ue_project_name": "Test",
        }
        self.runtime = {
            "online": True,
            "ue_project_id": "ueproj_Test",
            "ue_project_name": "Test",
            "last_seen_at": "2026-08-21T10:00:00Z",
            "realtime_channel": {
                "enabled": True,
                "stream_id": "metaverse.targets.primary",
                "owner": "MetaverseClient",
                "url": "ws://10.191.12.40:8080/ws/targets",
                "connection_state": "connected",
                "active_source": "websocket",
                "last_frame_age_ms": 120,
                "frame_count": 99,
                "target_count": 57,
                "applied_target_count": 52,
                "error": "",
            },
        }

    def make_client(self, project=True):
        app = Flask(__name__)
        store = FakeProjectStore(self.project if project else None)
        register_external_data_control_routes(app, store, lambda _database_id: self.runtime)
        return app.test_client()

    def test_status_uses_ue_heartbeat_as_actual_state(self):
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        self.assertEqual(self.database_id, status["database"]["id"])
        self.assertTrue(status["websocket"]["reported_enabled"])
        self.assertEqual("connected", status["websocket"]["connection_state"])
        self.assertEqual("metaverse.targets.primary", status["websocket"]["stream_id"])
        self.assertEqual("MetaverseClient", status["websocket"]["owner"])
        self.assertEqual(
            "ws://10.191.12.40:8080/ws/targets", status["websocket"]["url"]
        )
        self.assertFalse(status["http_snapshot"]["affected_by_switch"])

    def test_toggle_is_isolated_by_database_and_exposed_to_heartbeat(self):
        response = self.make_client().put(
            "/api/v2/external-data/realtime",
            json={"enabled": False, "expected_database_id": self.database_id},
        )
        self.assertEqual(200, response.status_code)
        payload = response.get_json()
        self.assertFalse(payload["websocket"]["desired_enabled"])
        self.assertFalse(payload["websocket"]["in_sync"])
        command = realtime_control_for_heartbeat(self.database_id)
        self.assertFalse(command["enabled"])
        key = f"external_data.realtime_stream.{self.database_id}"
        persisted = REALTIME_STREAM_CONTROL._project_store.runtime_settings[key]
        self.assertFalse(persisted["enabled"])

    def test_persisted_command_is_restored_after_registry_restart(self):
        store = FakeProjectStore(self.project)
        first = RealtimeStreamControlRegistry()
        first.configure_project_store(store)
        saved = first.set_enabled(self.database_id, False)

        restored = RealtimeStreamControlRegistry()
        restored.configure_project_store(store)
        self.assertEqual(saved, restored.get_command(self.database_id))

    def test_offline_ue_does_not_expose_stale_targets_as_current(self):
        self.runtime["online"] = False
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        self.assertEqual("none", status["websocket"]["active_source"])
        self.assertEqual(0, status["websocket"]["target_count"])
        self.assertEqual(0, status["websocket"]["applied_target_count"])
        self.assertIsNone(status["websocket"]["last_frame_age_ms"])

    def test_stale_page_cannot_control_new_active_database(self):
        response = self.make_client().put(
            "/api/v2/external-data/realtime",
            json={"enabled": False, "expected_database_id": "old_database"},
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("active_database_changed", response.get_json()["error"])
        self.assertIsNone(REALTIME_STREAM_CONTROL.get_command(self.database_id))

    def test_missing_active_database_is_reported(self):
        response = self.make_client(project=False).get("/api/v2/external-data/realtime")
        self.assertEqual(404, response.status_code)
        self.assertEqual("active_database_not_found", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
