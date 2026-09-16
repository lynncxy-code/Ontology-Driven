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

    def test_v2_wrapper_and_summary_keep_legacy_projection(self):
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        self.assertEqual("external_realtime_v2", status["schema_version"])
        self.assertEqual(1, len(status["streams"]))
        stream = status["streams"][0]
        self.assertEqual(status["websocket"]["stream_id"], stream["stream_id"])
        self.assertEqual("partial", stream["execution_state"])
        self.assertEqual(5, stream["unapplied_target_count"])
        self.assertEqual(1, status["summary"]["stream_count"])
        self.assertEqual(1, status["summary"]["connected_stream_count"])
        self.assertEqual(57, status["summary"]["total_target_count"])
        self.assertEqual(52, status["summary"]["total_applied_target_count"])
        self.assertEqual(5, status["summary"]["total_unapplied_target_count"])

    def test_received_but_zero_applied_is_never_healthy(self):
        self.runtime["realtime_channel"].update({
            "target_count": 25,
            "applied_target_count": 0,
            "last_frame_age_ms": 100,
        })
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        stream = status["streams"][0]
        self.assertEqual("none_applied", stream["execution_state"])
        self.assertEqual(25, stream["unapplied_target_count"])
        self.assertFalse(stream["healthy"])
        self.assertEqual(0, status["summary"]["healthy_stream_count"])
        self.assertEqual(1, status["summary"]["attention_stream_count"])

    def test_full_application_is_ready_when_control_is_in_sync(self):
        store = FakeProjectStore(self.project)
        REALTIME_STREAM_CONTROL.configure_project_store(store)
        REALTIME_STREAM_CONTROL.set_enabled(self.database_id, True)
        self.runtime["realtime_channel"].update({
            "target_count": 25,
            "applied_target_count": 25,
            "last_frame_age_ms": 100,
        })
        status = build_active_realtime_status(store, lambda _database_id: self.runtime)
        stream = status["streams"][0]
        self.assertEqual("in_sync", stream["control_state"])
        self.assertEqual("ready", stream["execution_state"])
        self.assertEqual("healthy", stream["health_state"])
        self.assertTrue(stream["healthy"])
        self.assertEqual(1, status["summary"]["healthy_stream_count"])

    def test_partial_application_is_reported(self):
        self.runtime["realtime_channel"].update({
            "target_count": 10,
            "applied_target_count": 3,
            "last_frame_age_ms": 100,
        })
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        stream = status["streams"][0]
        self.assertEqual("partial", stream["execution_state"])
        self.assertEqual(7, stream["unapplied_target_count"])

    def test_no_frame_and_expired_frame_are_not_reported_as_ready(self):
        channel = self.runtime["realtime_channel"]
        channel.update({"frame_count": 0, "last_frame_age_ms": None})
        no_frame = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )["streams"][0]
        self.assertEqual("no_frame", no_frame["frame_state"])
        self.assertEqual("waiting", no_frame["execution_state"])
        self.assertFalse(no_frame["healthy"])

        channel.update({"frame_count": 1, "last_frame_age_ms": 5001})
        stale = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )["streams"][0]
        self.assertEqual("stale", stale["frame_state"])
        self.assertEqual("waiting", stale["execution_state"])
        self.assertFalse(stale["healthy"])

    def test_missing_execution_counter_is_unknown_not_fabricated(self):
        channel = self.runtime["realtime_channel"]
        channel.pop("applied_target_count", None)
        channel["target_count"] = 25
        channel["last_frame_age_ms"] = 100
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        stream = status["streams"][0]
        self.assertIsNone(stream["applied_target_count"])
        self.assertIsNone(stream["unapplied_target_count"])
        self.assertEqual("unknown", stream["execution_state"])
        self.assertFalse(stream["healthy"])
        # The compatibility projection retains the old numeric shape.
        self.assertEqual(0, status["websocket"]["applied_target_count"])

    def test_provider_categories_reasons_and_diagnostics_are_normalized(self):
        self.runtime["realtime_channel"].update({
            "categories": [
                {
                    "category_id": "person",
                    "label": "人员",
                    "lifecycle": "transient_dynamic",
                    "handler_id": "metaverse.people",
                    "target_count": 20,
                    "applied_count": 20,
                    "reasons": [],
                },
                {
                    "category_id": "agv",
                    "label": "AGV",
                    "target_count": 5,
                    "applied_count": 0,
                    "reasons": [{
                        "code": "instance_missing",
                        "count": 5,
                        "message": "尚未找到对应的正式实例",
                    }],
                },
            ],
            "unapplied_reasons": {
                "instance_missing": 5,
            },
            "diagnostics": {"provider_version": "1.2.3"},
        })
        stream = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )["streams"][0]
        self.assertEqual(2, len(stream["categories"]))
        self.assertEqual("agv", stream["categories"][1]["category_id"])
        self.assertEqual(5, stream["categories"][1]["reasons"][0]["count"])
        self.assertEqual("instance_missing", stream["unapplied_reasons"][0]["code"])
        self.assertEqual("1.2.3", stream["diagnostics"]["provider_version"])

    def test_multiple_reported_channels_are_wrapped_and_aggregated(self):
        primary = dict(self.runtime["realtime_channel"])
        secondary = dict(primary)
        secondary.update({
            "stream_id": "devices.secondary",
            "owner": "DeviceProvider",
            "target_count": 2,
            "applied_target_count": 2,
        })
        self.runtime["realtime_channels"] = [primary, secondary]
        self.runtime.pop("realtime_channel")
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        self.assertEqual(2, status["summary"]["stream_count"])
        self.assertEqual(59, status["summary"]["total_target_count"])
        self.assertEqual(54, status["summary"]["total_applied_target_count"])
        self.assertEqual("metaverse.targets.primary", status["websocket"]["stream_id"])

    def test_optional_stream_id_must_name_a_reported_stream(self):
        client = self.make_client()
        response = client.put(
            "/api/v2/external-data/realtime",
            json={
                "stream_id": "not.registered",
                "enabled": False,
                "expected_database_id": self.database_id,
            },
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("unknown_stream", response.get_json()["error"])

        response = client.put(
            "/api/v2/external-data/realtime",
            json={
                "stream_id": "metaverse.targets.primary",
                "enabled": False,
                "expected_database_id": self.database_id,
            },
        )
        self.assertEqual(200, response.status_code)

    def test_secondary_stream_is_observable_but_not_silently_toggled(self):
        primary = dict(self.runtime["realtime_channel"])
        secondary = dict(primary)
        secondary.update({"stream_id": "devices.secondary", "owner": "DeviceProvider"})
        self.runtime["realtime_channels"] = [primary, secondary]
        self.runtime.pop("realtime_channel")

        response = self.make_client().put(
            "/api/v2/external-data/realtime",
            json={
                "stream_id": "devices.secondary",
                "enabled": False,
                "expected_database_id": self.database_id,
            },
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("stream_not_controllable", response.get_json()["error"])
        status = build_active_realtime_status(
            FakeProjectStore(self.project), lambda _database_id: self.runtime
        )
        self.assertTrue(status["streams"][0]["control_supported"])
        self.assertFalse(status["streams"][1]["control_supported"])
        self.assertEqual("observe_only", status["streams"][1]["control_scope"])

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
