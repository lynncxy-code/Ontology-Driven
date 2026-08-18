"""Explicit route narration generation and project audio asset lifecycle."""

import copy
import datetime
import os

from .narration import VOICE_MODES, effective_voice_profile
from .narration_assets import NarrationAssetError, NarrationAssetStorage
from .tts import configured_provider
from .tts.base import TTSProviderError


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class NarrationGenerationError(RuntimeError):
    def __init__(self, code, message, status=422):
        self.code = code
        self.status = int(status)
        super().__init__(message)


class NarrationGenerationService:
    def __init__(self, store, provider=None, asset_root=None):
        self.store = store
        self.provider = provider or configured_provider()
        self.storage = NarrationAssetStorage(asset_root)

    def provider_status(self):
        status = copy.deepcopy(self.provider.readiness())
        status["voices"] = copy.deepcopy(self.provider.voice_catalog())
        return status

    @staticmethod
    def _route(project, route_id):
        for route in (project.get("scene_interactions") or {}).get("routes") or []:
            if isinstance(route, dict) and route.get("id") == route_id:
                return route
        return None

    @staticmethod
    def _expected(value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise NarrationGenerationError(
                "invalid_expected_revision", "expected_revision 必须是整数", 400
            ) from exc

    def _existing_asset(self, project, asset_id):
        metadata = ((project.get("scene_interactions") or {}).get("narration_assets") or {}).get(asset_id)
        if not isinstance(metadata, dict) or not self.storage.exists(project.get("id"), metadata):
            return None
        return copy.deepcopy(metadata)

    def generate(self, route_id, expected_revision, waypoint_ids=None, expected_project_id=None):
        project = self.store.get_active_copy()
        if not project:
            raise NarrationGenerationError("active_project_not_found", "当前没有激活项目", 404)
        expected = self._expected(expected_revision)
        scene = project.get("scene_interactions") or {}
        if int(scene.get("revision") or 0) != expected:
            raise NarrationGenerationError(
                "scene_interaction_revision_conflict", "路线配置已被修改，请刷新后重试", 409
            )
        route = self._route(project, route_id)
        if not route:
            raise NarrationGenerationError("route_not_found", "当前项目中找不到该漫游路线", 404)
        readiness = self.provider.readiness()
        if not readiness.get("ready"):
            raise NarrationGenerationError(
                "tts_provider_unconfigured", readiness.get("message") or "语音服务尚未配置", 422
            )
        selected = None
        if waypoint_ids:
            if not isinstance(waypoint_ids, list):
                raise NarrationGenerationError("invalid_waypoint_ids", "waypoint_ids 必须是数组", 400)
            selected = {str(item) for item in waypoint_ids if str(item)}

        profile = effective_voice_profile(
            scene.get("narration_defaults"), route.get("narration_profile")
        )
        work = []
        for waypoint in route.get("waypoints") or []:
            if selected is not None and waypoint.get("id") not in selected:
                continue
            narration = waypoint.get("narration")
            if not isinstance(narration, dict) or not narration.get("enabled"):
                continue
            if narration.get("mode") not in VOICE_MODES:
                continue
            for segment in narration.get("segments") or []:
                if not isinstance(segment, dict) or not segment.get("text"):
                    continue
                work.append({
                    "waypoint_id": waypoint.get("id"),
                    "content_digest": narration.get("content_digest"),
                    "segment_id": segment.get("segment_id"),
                    "segment_order": segment.get("order"),
                    "text": segment.get("text"),
                    "existing_asset_id": segment.get("audio_asset_id"),
                })
        if not work:
            return {
                "status": "ok",
                "project_id": project.get("id"),
                "revision": expected,
                "route_id": route_id,
                "total": 0,
                "reused": 0,
                "succeeded": 0,
                "failed": 0,
                "waypoints": [],
            }

        generated = {}
        generated_by_text = {}
        results = []
        created_files = []
        reused = succeeded = failed = 0
        for item in work:
            outcome = {key: item[key] for key in ("waypoint_id", "segment_id")}
            existing = self._existing_asset(project, item.get("existing_asset_id"))
            try:
                if existing:
                    metadata = existing
                    reused += 1
                    result_name = "reused"
                elif item["text"] in generated_by_text:
                    metadata = generated_by_text[item["text"]]
                    reused += 1
                    result_name = "reused"
                else:
                    wav = self.provider.synthesize(item["text"], profile)
                    metadata, path, created = self.storage.store_wav(project.get("id"), wav)
                    created_files.append((path, created))
                    generated_by_text[item["text"]] = metadata
                    succeeded += 1
                    result_name = "success"
                generated[(item["waypoint_id"], item["segment_id"])] = metadata
                outcome.update({
                    "result": result_name,
                    "asset_id": metadata["asset_id"],
                    "duration_sec": metadata["duration_sec"],
                })
            except (TTSProviderError, NarrationAssetError) as exc:
                failed += 1
                outcome.update({
                    "result": "failed",
                    "error": getattr(exc, "code", "tts_generation_failed"),
                    "message": str(exc),
                })
            results.append(outcome)

        project_id = project.get("id")
        completed_at = _utc_now()
        commit_result = {}

        def update(working):
            if working.get("id") != project_id:
                raise NarrationGenerationError("project_changed", "生成期间当前项目已切换", 409)
            target_scene = working.setdefault("scene_interactions", {})
            current_revision = int(target_scene.get("revision") or 0)
            if current_revision != expected:
                raise NarrationGenerationError(
                    "scene_interaction_revision_conflict", "生成期间路线配置已修改，结果未挂接", 409
                )
            target_route = self._route(working, route_id)
            if not target_route:
                raise NarrationGenerationError("route_not_found", "生成期间路线已删除", 409)
            assets = target_scene.setdefault("narration_assets", {})
            audit = target_scene.setdefault("narration_audit", [])
            waypoint_results = {}
            for waypoint in target_route.get("waypoints") or []:
                narration = waypoint.get("narration")
                if not isinstance(narration, dict):
                    continue
                matching_work = [
                    item for item in work
                    if item["waypoint_id"] == waypoint.get("id")
                    and item["content_digest"] == narration.get("content_digest")
                ]
                if not matching_work:
                    continue
                segment_failed = False
                for segment in narration.get("segments") or []:
                    key = (waypoint.get("id"), segment.get("segment_id"))
                    metadata = generated.get(key)
                    if metadata:
                        assets[metadata["asset_id"]] = copy.deepcopy(metadata)
                        segment.update({
                            "audio_asset_id": metadata["asset_id"],
                            "audio_sha256": metadata["sha256"],
                            "audio_duration_sec": metadata["duration_sec"],
                        })
                    elif any(item["segment_id"] == segment.get("segment_id") for item in matching_work):
                        segment.pop("audio_asset_id", None)
                        segment.pop("audio_sha256", None)
                        segment.pop("audio_duration_sec", None)
                        segment_failed = True
                has_all = bool(narration.get("segments")) and all(
                    segment.get("audio_asset_id") for segment in narration.get("segments") or []
                )
                narration["generation_state"] = "available" if has_all else "failed"
                narration["last_generation"] = {
                    "provider_id": self.provider.provider_id,
                    "requested_at": completed_at,
                    "completed_at": completed_at,
                    "result": "success" if has_all else "partial_failure" if segment_failed else "failed",
                    "operator": "local-editor",
                }
                waypoint_results[waypoint.get("id")] = narration["generation_state"]

            for item, outcome in zip(work, results):
                metadata = generated.get((item["waypoint_id"], item["segment_id"]))
                audit.append({
                    "route_id": route_id,
                    "waypoint_id": item["waypoint_id"],
                    "segment_id": item["segment_id"],
                    "text_digest": item["content_digest"],
                    "segmentation_version": "zh-punct-v1",
                    "voice_profile": copy.deepcopy(profile),
                    "provider_id": self.provider.provider_id,
                    "requested_at": completed_at,
                    "completed_at": completed_at,
                    "result": outcome["result"],
                    "error_code": outcome.get("error"),
                    "audio_asset_id": (metadata or {}).get("asset_id"),
                    "audio_sha256": (metadata or {}).get("sha256"),
                    "operator": "local-editor",
                })
            if len(audit) > 5000:
                del audit[:-5000]
            target_route["revision"] = int(target_route.get("revision") or 0) + 1
            target_route["updated_at"] = completed_at
            target_scene["revision"] = current_revision + 1
            commit_result.update({
                "revision": target_scene["revision"],
                "route_revision": target_route["revision"],
                "waypoints": waypoint_results,
            })

        try:
            self.store.transact_expected_active(expected_project_id, update)
        except Exception:
            for path, created in created_files:
                self.storage.remove_if_created(path, created)
            raise

        return {
            "status": "ok" if failed == 0 else "partial_failure",
            "project_id": project_id,
            "revision": commit_result["revision"],
            "route_revision": commit_result["route_revision"],
            "route_id": route_id,
            "total": len(work),
            "reused": reused,
            "succeeded": succeeded,
            "failed": failed,
            "waypoints": commit_result["waypoints"],
            "segments": results,
        }

    def asset_file(self, asset_id):
        project = self.store.get_active_copy()
        if not project:
            raise NarrationGenerationError("active_project_not_found", "当前没有激活项目", 404)
        metadata = ((project.get("scene_interactions") or {}).get("narration_assets") or {}).get(asset_id)
        if not isinstance(metadata, dict):
            raise NarrationGenerationError("narration_asset_not_found", "当前项目中找不到该解说音频", 404)
        path = self.storage.resolve(project.get("id"), metadata)
        if not os.path.isfile(path):
            raise NarrationGenerationError("narration_asset_missing", "解说音频文件缺失", 404)
        return path, copy.deepcopy(metadata)
