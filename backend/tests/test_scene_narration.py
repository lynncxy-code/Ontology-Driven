import io
import os
import sys
import tempfile
import unittest
import wave
import struct

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import ProjectStore
from scene_interaction.narration import (
    DEFAULT_NARRATION_SETTINGS,
    effective_voice_profile,
    normalize_waypoint_narration,
    split_text,
)
from scene_interaction.narration_assets import NarrationAssetStorage, inspect_wav
from scene_interaction.narration_service import NarrationGenerationService
from scene_interaction.api import register_scene_interaction_routes
from scene_interaction.service import SceneInteractionService
from scene_interaction.tts.base import TTSProvider


def wav_bytes(seconds=0.5, sample_rate=16000):
    target = io.BytesIO()
    with wave.open(target, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return target.getvalue()


class FakeProvider(TTSProvider):
    provider_id = "fake.standard"

    def __init__(self):
        self.calls = []

    def readiness(self):
        return {
            "provider_id": self.provider_id,
            "configured": True,
            "ready": True,
            "message": "ready",
        }

    def voice_catalog(self):
        return [{
            "voice_id": "fake-voice",
            "display_name": "测试音色",
            "voice_type": "测试女声",
            "scenario": "自动化测试",
            "language": "zh-CN",
        }]

    def synthesize(self, text, voice_profile):
        self.calls.append((text, dict(voice_profile)))
        return wav_bytes()


class NarrationContractTests(unittest.TestCase):
    def test_split_text_is_bounded_and_preserves_content(self):
        source = "第一段很短。" + ("没有强标点的内容" * 50) + "！结束。"
        segments = split_text(source)
        self.assertGreater(len(segments), 2)
        self.assertTrue(all(0 < len(item) <= 280 for item in segments))
        self.assertEqual(source, "".join(segments))

    def test_manual_break_is_applied_before_automatic_split(self):
        source = "甲乙丙丁戊己庚辛"
        self.assertEqual(["甲乙丙丁", "戊己庚辛"], split_text(source, [4]))

    def test_voice_change_invalidates_old_audio(self):
        errors = []
        first_profile = effective_voice_profile(DEFAULT_NARRATION_SETTINGS, {})
        first = normalize_waypoint_narration({
            "enabled": True,
            "mode": "voice",
            "text": "欢迎来到总装区域。",
        }, None, first_profile, errors, "waypoints[0].narration")
        self.assertFalse(errors)
        first["segments"][0].update({
            "audio_asset_id": "narration_old",
            "audio_sha256": "old",
            "audio_duration_sec": 1.0,
        })
        first["generation_state"] = "available"

        second_profile = effective_voice_profile(
            DEFAULT_NARRATION_SETTINGS, {"voice_id": "new-voice"}
        )
        second = normalize_waypoint_narration({
            "enabled": True,
            "mode": "voice",
            "text": "欢迎来到总装区域。",
        }, first, second_profile, errors, "waypoints[0].narration")
        self.assertNotIn("audio_asset_id", second["segments"][0])
        self.assertEqual("pending", second["generation_state"])

    def test_recorded_upload_survives_single_segment_subtitle_edit(self):
        errors = []
        profile = effective_voice_profile(DEFAULT_NARRATION_SETTINGS, {})
        first = normalize_waypoint_narration({
            "enabled": True,
            "mode": "voice",
            "text": "原始字幕。",
        }, None, profile, errors, "waypoints[0].narration")
        first["segments"][0].update({
            "audio_asset_id": "narration_recorded",
            "audio_sha256": "recorded-sha",
            "audio_duration_sec": 46.621,
        })
        first["generation_state"] = "available"
        first["last_generation"] = {
            "provider_id": "uploaded.recorded",
            "result": "success",
        }

        second = normalize_waypoint_narration({
            "enabled": True,
            "mode": "voice",
            "text": "修改后的字幕。",
        }, first, profile, errors, "waypoints[0].narration")

        self.assertFalse(errors)
        self.assertEqual("修改后的字幕。", second["segments"][0]["text"])
        self.assertEqual("narration_recorded", second["segments"][0]["audio_asset_id"])
        self.assertEqual("recorded-sha", second["segments"][0]["audio_sha256"])
        self.assertEqual(46.621, second["segments"][0]["audio_duration_sec"])
        self.assertEqual("available", second["generation_state"])
        self.assertEqual("uploaded.recorded", second["last_generation"]["provider_id"])


class NarrationAssetTests(unittest.TestCase):
    def test_store_and_resolve_wav_by_content(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = NarrationAssetStorage(directory)
            metadata, path, created = storage.store_wav("project-a", wav_bytes())
            self.assertTrue(created)
            self.assertTrue(os.path.isfile(path))
            self.assertEqual(16000, metadata["sample_rate"])
            self.assertEqual(path, storage.resolve("project-a", metadata))
            duplicate, duplicate_path, duplicate_created = storage.store_wav("project-a", wav_bytes())
            self.assertEqual(metadata["asset_id"], duplicate["asset_id"])
            self.assertEqual(path, duplicate_path)
            self.assertFalse(duplicate_created)

    def test_rejects_non_wav(self):
        with self.assertRaises(Exception):
            inspect_wav(b"not audio")

    def test_duration_uses_available_pcm_when_streaming_header_is_oversized(self):
        data = bytearray(wav_bytes(seconds=0.5))
        data_offset = data.index(b"data")
        struct.pack_into("<I", data, data_offset + 4, 16000 * 2)
        inspected = inspect_wav(bytes(data))
        self.assertAlmostEqual(0.5, inspected["duration_sec"], places=2)


class NarrationGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project("Narration", project_id="narration-project")
        profile = effective_voice_profile(DEFAULT_NARRATION_SETTINGS, {})
        errors = []
        narration = normalize_waypoint_narration({
            "enabled": True,
            "mode": "subtitle_voice",
            "text": "第一段。第二段。",
        }, None, profile, errors, "waypoints[0].narration")
        self.assertFalse(errors)

        def seed(project):
            scene = project.setdefault("scene_interactions", {})
            scene.update({
                "revision": 0,
                "narration_defaults": dict(DEFAULT_NARRATION_SETTINGS),
                "narration_assets": {},
                "narration_audit": [],
                "routes": [{
                    "id": "route-a",
                    "revision": 1,
                    "narration_profile": {"inherit_project": True},
                    "waypoints": [{"id": "wp-1", "narration": narration}],
                }],
            })
        self.store.transact_active(seed)
        self.provider = FakeProvider()
        self.service = NarrationGenerationService(
            self.store,
            provider=self.provider,
            asset_root=os.path.join(self.temp.name, "assets"),
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_generate_attaches_assets_and_increments_once(self):
        result = self.service.generate("route-a", 0)
        self.assertEqual("ok", result["status"])
        self.assertEqual(1, result["revision"])
        self.assertGreaterEqual(result["succeeded"], 1)
        project = self.store.get_active_copy()
        scene = project["scene_interactions"]
        narration = scene["routes"][0]["waypoints"][0]["narration"]
        self.assertEqual("available", narration["generation_state"])
        self.assertTrue(all(item.get("audio_asset_id") for item in narration["segments"]))
        self.assertEqual(len(narration["segments"]), len(scene["narration_assets"]))
        self.assertEqual(len(narration["segments"]), len(scene["narration_audit"]))

    def test_provider_status_includes_voice_catalog(self):
        status = self.service.provider_status()
        self.assertTrue(status["ready"])
        self.assertEqual("fake-voice", status["voices"][0]["voice_id"])

    def test_second_generation_reuses_existing_assets(self):
        first = self.service.generate("route-a", 0)
        second = self.service.generate("route-a", first["revision"])
        self.assertEqual(0, second["succeeded"])
        self.assertEqual(first["total"], second["reused"])

    def test_narration_asset_download_reads_ue_bound_inactive_project(self):
        self.service.generate("route-a", 0)
        asset_id = next(iter(
            self.store.get_active_copy()["scene_interactions"]["narration_assets"]
        ))
        project_a_id = self.store.get_active_id()
        self.store.set_dataset({
            "id": project_a_id,
            "name": "Narration",
            "graph_data": {"nodes": [], "links": [], "categories": []},
            "bound_ue_project_id": "ue-narration-a",
            "bound_ue_project_name": "UE Narration A",
        })
        self.store.create_project(
            "Other Active",
            project_id="narration-other",
            dataset={
                "id": "narration-other",
                "name": "Other Active",
                "graph_data": {"nodes": [], "links": [], "categories": []},
            },
        )

        import ue_project_binding as binding_index
        binding_index._ue_index.clear()
        binding_index.rebuild_index(self.store)
        app = Flask(__name__)
        register_scene_interaction_routes(
            app,
            self.store,
            narration_asset_root=os.path.join(self.temp.name, "assets"),
        )
        response = app.test_client().get(
            f"/api/v2/scene-interactions/narration-assets/{asset_id}",
            headers={
                "X-OntoTwin-UE-Project-Id": "ue-narration-a",
                "X-OntoTwin-UE-Project-Name": "UE Narration A",
                "X-OntoTwin-UE-Context": "editor",
            },
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("audio/wav", response.mimetype)
        self.assertEqual("narration-other", self.store.get_active_id())
        response.close()
        binding_index._ue_index.clear()

    def test_project_default_voice_change_invalidates_inherited_audio(self):
        generated = self.service.generate("route-a", 0)
        scene_service = SceneInteractionService(
            self.store,
            narration_provider=self.provider,
            narration_asset_root=os.path.join(self.temp.name, "assets"),
        )
        defaults = dict(DEFAULT_NARRATION_SETTINGS)
        defaults["voice_id"] = "xiaogang"
        result = scene_service.save_narration_defaults(
            defaults, generated["revision"], "narration-project"
        )
        self.assertEqual(generated["revision"] + 1, result["revision"])
        narration = self.store.get_active_copy()["scene_interactions"]["routes"][0]["waypoints"][0]["narration"]
        self.assertEqual("pending", narration["generation_state"])
        self.assertTrue(all(not item.get("audio_asset_id") for item in narration["segments"]))


if __name__ == "__main__":
    unittest.main()
