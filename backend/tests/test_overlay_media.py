import os
import sys
import tempfile
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from overlay.media import MediaPolicyError, MediaPolicyService
from overlay.service import OverlayService
from project_store import ProjectStore


def media_config(url="https://media.example.com/demo.mp4", kind="auto"):
    return {
        "enabled": True,
        "template_id": "title_video_body",
        "display_mode": "always",
        "anchor": {
            "strategy": "bounds_top",
            "offset_cm": {"x": 0, "y": 0, "z": 20},
        },
        "slots": {
            "title": {
                "required": True,
                "binding": {"source": "instance", "path": "display_name"},
                "format": {"empty_text": "--", "max_length": 80},
            },
            "media": {
                "required": True,
                "url_binding": {"source": "literal", "value": url},
                "poster_binding": {
                    "source": "literal",
                    "value": "https://images.example.com/demo.webp",
                },
                "kind": kind,
                "playback": {"autoplay": True, "muted": True, "loop": False},
            },
            "body": {
                "required": False,
                "binding": {"source": "literal", "value": "演示视频"},
                "format": {"empty_text": "--", "max_length": 300},
            },
        },
    }


class OverlayMediaTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Media Test",
            project_id="media_test",
            object_types={
                "machine": {
                    "rid": "machine",
                    "name": "设备",
                    "injected_interfaces": ["I3D_Representable", "I3D_Overlay"],
                    "interface_configs": {},
                }
            },
        )
        self.store.spawn("unit-1", "machine")
        self.platform_policy = {
            "allowed_hosts": [
                "media.example.com",
                "images.example.com",
                "*.streams.example.com",
                "10.20.1.15:8080",
            ],
            "http_exceptions": ["10.20.1.15:8080"],
        }
        self.service = OverlayService(self.store, self.platform_policy)

    def tearDown(self):
        self.temp.cleanup()

    def test_snapshot_hides_playback_url_and_lazy_resolve_returns_it(self):
        self.service.save_type("machine", media_config(), 0)
        project = self.store.get_active_copy()
        object_type = project["object_types"]["machine"]
        instance = project["instances"]["unit-1"]
        payload = self.service.resolve_instance_interface(object_type, instance, online=True)
        media = payload["resolved_slots"]["media"]
        self.assertTrue(media["available"])
        self.assertEqual("mp4", media["kind"])
        self.assertNotIn("preview_url", media)
        self.assertEqual("https://images.example.com/demo.webp", media["poster_url"])

        playback = self.service.resolve_media("unit-1")
        self.assertEqual("https://media.example.com/demo.mp4", playback["url"])
        self.assertEqual([2, 5, 15], playback["retry"]["delays_seconds"])

    def test_context_preview_may_return_targeted_url(self):
        preview = self.service.preview("machine", "unit-1", media_config())
        self.assertEqual(
            "https://media.example.com/demo.mp4",
            preview["resolved_slots"]["media"]["preview_url"],
        )

    def test_project_restriction_blocks_platform_host_not_selected_by_project(self):
        current = self.service.get_media_policy()["project"]
        self.service.save_media_policy({
            "mode": "restricted",
            "allowed_hosts": ["images.example.com"],
            "http_exceptions": [],
        }, current["revision"])
        with self.assertRaises(MediaPolicyError) as raised:
            self.service.save_type("machine", media_config(), 0)
        self.assertEqual("media_domain_not_allowed", raised.exception.code)

    def test_http_requires_explicit_platform_and_project_exception(self):
        policy = self.store.get_media_policy()
        result = self.service.media_policy.validate_url(
            "http://10.20.1.15:8080/live/camera.m3u8", policy, requested_kind="auto"
        )
        self.assertEqual("hls", result["kind"])
        with self.assertRaises(MediaPolicyError) as raised:
            self.service.media_policy.validate_url(
                "http://media.example.com/demo.mp4", policy, requested_kind="auto"
            )
        self.assertEqual("media_http_not_allowed", raised.exception.code)

    def test_wildcard_matches_subdomain_but_not_lookalike(self):
        policy_service = MediaPolicyService(self.store, self.platform_policy)
        policy = self.store.get_media_policy()
        self.assertEqual(
            "hls",
            policy_service.validate_url(
                "https://east.streams.example.com/live.m3u8", policy
            )["kind"],
        )
        with self.assertRaises(MediaPolicyError):
            policy_service.validate_url(
                "https://fake-streams.example.com/live.m3u8", policy
            )

    def test_empty_platform_allowlist_allows_any_https_source(self):
        policy_service = MediaPolicyService(self.store, {
            "allowed_hosts": [],
            "http_exceptions": [],
        })
        policy = self.store.get_media_policy()
        self.assertFalse(policy_service.describe(policy)["enforced"])
        result = policy_service.validate_url(
            "https://www.w3schools.com/html/mov_bbb.mp4", policy
        )
        self.assertEqual("mp4", result["kind"])

        with self.assertRaises(MediaPolicyError) as raised:
            policy_service.validate_url(
                "http://www.w3schools.com/html/mov_bbb.mp4", policy
            )
        self.assertEqual("media_http_not_allowed", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
