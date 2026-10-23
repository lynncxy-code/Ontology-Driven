import copy
import datetime
import hashlib
import math
import time

from .schema import (
    DEFAULT_STATUS_APPEARANCE,
    INSTANCE_PATHS,
    OBJECT_TYPE_PATHS,
    STATUS_LEVELS,
    OverlayValidationError,
    default_overlay_values,
    normalize_full_config,
    validate_full_config,
    validate_override,
)
from .media import MediaPolicyError, MediaPolicyService


class OverlayNotFoundError(LookupError):
    pass


class OverlayConflictError(RuntimeError):
    pass


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_overlay_config(base, override):
    result = deep_merge(base, override)
    if (
        isinstance(override, dict)
        and "template_id" in override
        and override.get("template_id") != (base or {}).get("template_id")
        and "slots" in override
    ):
        result["slots"] = copy.deepcopy(override.get("slots") or {})
    return result


def _type_values_with_defaults(type_envelope):
    values = (type_envelope or {}).get("values") or default_overlay_values()
    return normalize_full_config(values)


def apply_merge_patch(target, patch):
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    result = copy.deepcopy(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = apply_merge_patch(result.get(key), value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _envelope(container, key):
    value = (container or {}).get(key)
    if not isinstance(value, dict):
        return {"revision": 0, "values": {}}
    return {
        "revision": int(value.get("revision") or 0),
        "values": copy.deepcopy(value.get("values") or {}),
    }


def _nested_value(root, path):
    value = root
    for segment in (path or "").split("."):
        if not isinstance(value, dict) or segment not in value:
            return None
        value = value[segment]
    return value


def _resolve_binding(binding, object_type, instance, raw_state):
    source = (binding or {}).get("source")
    if source == "literal":
        return (binding or {}).get("value")
    path = (binding or {}).get("path", "")
    roots = {
        "instance": instance or {},
        "object_type": object_type or {},
        "raw_state": raw_state or {},
    }
    return _nested_value(roots.get(source, {}), path)


def _is_missing(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _format_datetime(value, pattern):
    try:
        if isinstance(value, (int, float)):
            parsed = datetime.datetime.fromtimestamp(value)
        else:
            parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        fmt = pattern or "%Y-%m-%d %H:%M:%S"
        replacements = {
            "YYYY": "%Y", "MM": "%m", "DD": "%d",
            "HH": "%H", "mm": "%M", "ss": "%S",
        }
        if "%" not in fmt:
            for token, replacement in replacements.items():
                fmt = fmt.replace(token, replacement)
        return parsed.strftime(fmt)
    except (TypeError, ValueError, OverflowError):
        return str(value)


def _format_value(value, fmt):
    fmt = fmt or {}
    if _is_missing(value):
        return fmt.get("empty_text", "--"), True
    if fmt.get("datetime_format"):
        text = _format_datetime(value, fmt.get("datetime_format"))
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and fmt.get("precision") is not None:
        text = f"{value:.{fmt['precision']}f}"
    else:
        text = str(value)
    unit = str(fmt.get("unit") or "").strip()
    if unit:
        text = f"{text} {unit}"
    max_length = fmt.get("max_length")
    if isinstance(max_length, int) and len(text) > max_length:
        text = text[:max(1, max_length - 3)] + "..."
    return text, False


def _slot_state(missing, online):
    if not online:
        return "offline"
    return "empty" if missing else "ok"


def _finite_numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) else None


def _resolve_media_slot(slot, object_type, instance, raw_state, online,
                        media_policy_service=None, project_media_policy=None,
                        include_media_url=False):
    playback = copy.deepcopy((slot or {}).get("playback") or {})
    playback.setdefault("autoplay", True)
    playback.setdefault("muted", True)
    playback.setdefault("loop", False)
    result = {
        "available": False,
        "state": "offline" if not online else "empty",
        "kind": (slot or {}).get("kind", "auto"),
        "playback": playback,
        "playback_ref": str((instance or {}).get("id") or ""),
        "poster_state": "empty",
    }
    raw_url = _resolve_binding((slot or {}).get("url_binding"), object_type, instance, raw_state)
    if not isinstance(raw_url, str) or not raw_url.strip():
        result["error_code"] = "media_url_empty"
        return result
    result["source_revision"] = hashlib.sha256(raw_url.strip().encode("utf-8")).hexdigest()[:16]
    if media_policy_service is None:
        result["state"] = "blocked"
        result["error_code"] = "media_policy_unavailable"
        return result
    try:
        validated = media_policy_service.validate_url(
            raw_url,
            project_media_policy or {},
            purpose="video",
            requested_kind=(slot or {}).get("kind", "auto"),
        )
        result["available"] = True
        result["state"] = "offline" if not online else "ready"
        result["kind"] = validated["kind"]
        if validated["kind"] == "hls":
            result["playback"]["loop"] = False
        if include_media_url:
            result["preview_url"] = validated["url"]
    except MediaPolicyError as exc:
        result["state"] = "blocked"
        result["error_code"] = exc.code

    raw_poster = _resolve_binding((slot or {}).get("poster_binding"), object_type, instance, raw_state)
    if isinstance(raw_poster, str) and raw_poster.strip():
        try:
            validated_poster = media_policy_service.validate_url(
                raw_poster, project_media_policy or {}, purpose="poster"
            )
            result["poster_url"] = validated_poster["url"]
            result["poster_state"] = "ready"
        except MediaPolicyError as exc:
            result["poster_state"] = "blocked"
            result["poster_error_code"] = exc.code
    return result


def resolve_slots(config, object_type, instance, raw_state, online,
                  media_policy_service=None, project_media_policy=None,
                  include_media_url=False):
    slots = config.get("slots") or {}
    resolved = {}

    for slot_id in ("title", "subtitle", "body"):
        slot = slots.get(slot_id)
        if not isinstance(slot, dict):
            continue
        value = _resolve_binding(slot.get("binding"), object_type, instance, raw_state)
        display, missing = _format_value(value, slot.get("format"))
        if missing and not slot.get("required", False):
            continue
        resolved[slot_id] = {"display_value": display, "state": _slot_state(missing, online)}

    metrics = []
    for metric in slots.get("metrics") or []:
        if not isinstance(metric, dict):
            continue
        value = _resolve_binding(metric.get("binding"), object_type, instance, raw_state)
        display, missing = _format_value(value, metric.get("format"))
        if missing and not metric.get("required", False):
            continue
        resolved_metric = {
            "id": metric.get("id", ""),
            "label": metric.get("label", ""),
            "display_value": display,
            "state": _slot_state(missing, online),
            "emphasized": bool(metric.get("emphasized", False)),
        }
        numeric_value = _finite_numeric(value)
        if numeric_value is not None:
            resolved_metric["numeric_value"] = numeric_value
        metrics.append(resolved_metric)
    if metrics:
        resolved["metrics"] = metrics
        metrics_presentation = ((config.get("presentation") or {}).get("metrics") or {})
        if metrics_presentation.get("style") == "gauge":
            gauge = metrics_presentation.get("gauge") or {}
            resolved["metrics_visual"] = {
                "style": "gauge",
                "primary_metric_id": metrics_presentation.get("primary_metric_id", ""),
                "range": {
                    "min": gauge.get("min"),
                    "max": gauge.get("max"),
                    "clamp_visual": bool(gauge.get("clamp_visual")),
                },
            }

    status = slots.get("status")
    if isinstance(status, dict):
        detail = _resolve_binding(status.get("label_binding"), object_type, instance, raw_state)
        detail_display, detail_missing = _format_value(detail, status.get("format"))
        level = _resolve_binding(status.get("level_binding"), object_type, instance, raw_state)
        level = str(level or "unknown").lower()
        if level not in STATUS_LEVELS:
            level = "unknown"
        if not online:
            level = "offline"
        defaults = DEFAULT_STATUS_APPEARANCE[level]
        configured = ((status.get("appearance") or {}).get(level) or {})
        display = configured.get("label", defaults["label"])
        accent_token = configured.get("color", defaults["color"])
        if detail_missing or detail_display == display:
            detail_display = ""
        resolved["status"] = {
            "display_value": display,
            "detail_value": detail_display,
            "level": level,
            "accent_token": accent_token,
            "state": _slot_state(_is_missing(display), online),
        }
    media = slots.get("media")
    if isinstance(media, dict):
        resolved["media"] = _resolve_media_slot(
            media,
            object_type,
            instance,
            raw_state,
            online,
            media_policy_service,
            project_media_policy,
            include_media_url,
        )
    return resolved


def resolve_overlay_interface(object_type, instance, raw_state=None, online=None, config_override=None,
                              revision_override=None, media_policy_service=None,
                              project_media_policy=None, include_media_url=False):
    injected = object_type.get("injected_interfaces") or []
    if "I3D_Overlay" not in injected and config_override is None:
        return None

    type_env = _envelope(object_type.get("interface_configs"), "I3D_Overlay")
    render_config = instance.get("render_config") or {}
    override_env = _envelope(render_config.get("interface_overrides"), "I3D_Overlay")
    type_values = _type_values_with_defaults(type_env)
    config = (
        normalize_full_config(config_override)
        if config_override is not None
        else merge_overlay_config(type_values, override_env.get("values") or {})
    )
    validate_full_config(config)
    if online is None:
        online = (time.time() - float(instance.get("last_seen") or 0)) < 3.0
    revision = revision_override or f"t{type_env['revision']}-i{override_env['revision']}"
    return {
        "enabled": bool(config.get("enabled")),
        "config_revision": revision,
        "template_id": config.get("template_id"),
        "display_mode": config.get("display_mode"),
        "anchor": copy.deepcopy(config.get("anchor")),
        "presentation": copy.deepcopy(config.get("presentation")),
        "online": bool(online),
        "resolved_slots": resolve_slots(
            config,
            object_type,
            instance,
            raw_state or instance.get("raw_state") or {},
            bool(online),
            media_policy_service,
            project_media_policy,
            include_media_url,
        ),
    }


def _flatten_raw_fields(value, prefix="", depth=0):
    result = []
    if not isinstance(value, dict) or depth > 3:
        return result
    for key in sorted(value):
        child = value[key]
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(child, dict):
            result.extend(_flatten_raw_fields(child, path, depth + 1))
        elif not isinstance(child, list):
            result.append({"source": "raw_state", "path": path, "label": path, "value_type": type(child).__name__})
    return result


def build_field_catalog(object_type, instance):
    catalog = [
        {"source": "instance", "path": path, "label": path, "value_type": "metadata"}
        for path in sorted(INSTANCE_PATHS)
    ]
    catalog.extend({
        "source": "object_type", "path": path, "label": path, "value_type": "metadata"
    } for path in sorted(OBJECT_TYPE_PATHS))

    raw_paths = {item["path"]: item for item in _flatten_raw_fields((instance or {}).get("raw_state") or {})}
    for prop in object_type.get("properties") or []:
        path = prop.get("name")
        if path and path not in raw_paths:
            raw_paths[path] = {
                "source": "raw_state",
                "path": path,
                "label": prop.get("label") or path,
                "value_type": prop.get("type") or "unknown",
            }
    catalog.extend(raw_paths.values())
    return catalog


class OverlayService:
    def __init__(self, store, platform_media_policy=None):
        self.store = store
        self.media_policy = MediaPolicyService(store, platform_media_policy)

    def _project(self):
        project = self.store.get_active_copy()
        if not project:
            raise OverlayNotFoundError("当前没有激活项目")
        return project

    @staticmethod
    def _find_type(project, rid):
        object_type = (project.get("object_types") or {}).get(rid)
        if not object_type:
            raise OverlayNotFoundError("当前项目中不存在该类型")
        return object_type

    @staticmethod
    def _find_instance(project, instance_id):
        instance = (project.get("instances") or {}).get(instance_id)
        if not instance:
            raise OverlayNotFoundError("当前项目中不存在该实例")
        return instance

    @staticmethod
    def _ensure_attached(object_type):
        if "I3D_Overlay" not in (object_type.get("injected_interfaces") or []):
            raise OverlayValidationError([{"path": "I3D_Overlay", "message": "请先挂载顶部信息面板能力"}])

    def context(self, object_type_rid=None, instance_id=None):
        project = self._project()
        instance = None
        if instance_id:
            instance = self._find_instance(project, instance_id)
            actual_rid = instance.get("object_type_rid")
            if object_type_rid and actual_rid != object_type_rid:
                raise OverlayValidationError("实例不属于指定类型")
            object_type_rid = actual_rid
        if not object_type_rid:
            raise OverlayValidationError("object_type_rid 或 instance_id 至少提供一个")
        object_type = self._find_type(project, object_type_rid)

        instances = [
            rec for rec in (project.get("instances") or {}).values()
            if rec.get("object_type_rid") == object_type_rid
        ]
        instances.sort(key=lambda item: str(item.get("display_name") or item.get("id") or ""))
        if instance is None and instances:
            instance = instances[0]

        type_env = _envelope(object_type.get("interface_configs"), "I3D_Overlay")
        type_values = _type_values_with_defaults(type_env)
        override_env = _envelope(
            ((instance or {}).get("render_config") or {}).get("interface_overrides"),
            "I3D_Overlay",
        )
        effective = merge_overlay_config(type_values, override_env["values"])
        preview = None
        if instance:
            preview = resolve_overlay_interface(
                object_type, instance, config_override=effective,
                revision_override=f"preview-t{type_env['revision']}-i{override_env['revision']}",
                media_policy_service=self.media_policy,
                project_media_policy=project.get("media_policy") or {},
                include_media_url=True,
            )

        instance_items = []
        now = time.time()
        for rec in instances:
            env = _envelope((rec.get("render_config") or {}).get("interface_overrides"), "I3D_Overlay")
            instance_items.append({
                "id": rec.get("id"),
                "display_name": rec.get("display_name") or rec.get("id"),
                "online": (now - float(rec.get("last_seen") or 0)) < 3.0,
                "override_revision": env["revision"],
            })
        return {
            "schema_version": project.get("schema_version"),
            "object_type": {
                "rid": object_type_rid,
                "name": object_type.get("name") or object_type_rid,
                "capability_attached": "I3D_Overlay" in (object_type.get("injected_interfaces") or []),
            },
            "type_config": {"revision": type_env["revision"], "values": type_values},
            "instance_override": {
                "instance_id": (instance or {}).get("id"),
                "revision": override_env["revision"],
                "values": override_env["values"],
            },
            "effective_config": effective,
            "preview_instance": {
                "id": (instance or {}).get("id"),
                "display_name": (instance or {}).get("display_name") or (instance or {}).get("id"),
            } if instance else None,
            "preview": preview,
            "field_catalog": build_field_catalog(object_type, instance or {}),
            "instances": instance_items,
            "media_policy": self.media_policy.describe(project.get("media_policy") or {}),
        }

    def preview(self, object_type_rid, instance_id, config):
        validate_full_config(config)
        project = self._project()
        object_type = self._find_type(project, object_type_rid)
        instance = self._find_instance(project, instance_id) if instance_id else None
        if instance and instance.get("object_type_rid") != object_type_rid:
            raise OverlayValidationError("预览实例不属于该类型")
        if instance is None:
            instance = next((
                rec for rec in (project.get("instances") or {}).values()
                if rec.get("object_type_rid") == object_type_rid
            ), None)
        if instance is None:
            instance = {
                "id": "preview",
                "display_name": object_type.get("name") or object_type_rid,
                "object_type_rid": object_type_rid,
                "object_type_name": object_type.get("name") or object_type_rid,
                "last_seen": time.time(),
                "raw_state": {},
                "render_config": {},
            }
        return resolve_overlay_interface(
            object_type,
            instance,
            config_override=config,
            revision_override="preview",
            media_policy_service=self.media_policy,
            project_media_policy=project.get("media_policy") or {},
            include_media_url=True,
        )

    def resolve_instance_interface(self, object_type, instance, raw_state=None, online=None,
                                   project_media_policy=None):
        """3.5: allow caller to pass project_media_policy (for by-pid UE snapshots).
        默认从当前激活项目取（旧行为）。"""
        if project_media_policy is None:
            project = self._project()
            project_media_policy = project.get("media_policy") or {}
        return resolve_overlay_interface(
            object_type,
            instance,
            raw_state=raw_state,
            online=online,
            media_policy_service=self.media_policy,
            project_media_policy=project_media_policy or {},
        )

    def _validate_literal_media(self, config, project):
        media = ((config or {}).get("slots") or {}).get("media")
        if not isinstance(media, dict):
            return
        url_binding = media.get("url_binding") or {}
        if url_binding.get("source") == "literal":
            self.media_policy.validate_url(
                url_binding.get("value"),
                project.get("media_policy") or {},
                purpose="video",
                requested_kind=media.get("kind", "auto"),
            )
        poster_binding = media.get("poster_binding") or {}
        poster_value = poster_binding.get("value")
        if poster_binding.get("source") == "literal" and isinstance(poster_value, str) and poster_value.strip():
            self.media_policy.validate_url(
                poster_value,
                project.get("media_policy") or {},
                purpose="poster",
            )

    def get_media_policy(self):
        project = self._project()
        return self.media_policy.describe(project.get("media_policy") or {})

    def save_media_policy(self, values, expected_revision, expected_project_id=None):
        normalized = self.media_policy.validate_project_policy(values or {})

        def update(project):
            current = self.media_policy.validate_project_policy(project.get("media_policy") or {})
            if int(expected_revision) != current["revision"]:
                raise OverlayConflictError("项目媒体策略已被其他页面更新")
            normalized["revision"] = current["revision"] + 1
            project["media_policy"] = copy.deepcopy(normalized)
            return self.media_policy.describe(project["media_policy"])

        return self.store.transact_expected_active(expected_project_id, update)

    def resolve_media(self, instance_id):
        project = self._project()
        instance = self._find_instance(project, instance_id)
        object_type = self._find_type(project, instance.get("object_type_rid"))
        self._ensure_attached(object_type)
        type_env = _envelope(object_type.get("interface_configs"), "I3D_Overlay")
        override_env = _envelope(
            (instance.get("render_config") or {}).get("interface_overrides"), "I3D_Overlay"
        )
        config = merge_overlay_config(
            _type_values_with_defaults(type_env), override_env.get("values") or {}
        )
        validate_full_config(config)
        if not config.get("enabled"):
            raise MediaPolicyError("media_overlay_disabled", "该实例的视频面板未启用")
        media = (config.get("slots") or {}).get("media")
        if not isinstance(media, dict):
            raise MediaPolicyError("media_not_configured", "当前模板没有配置视频")
        raw_state = instance.get("raw_state") or {}
        raw_url = _resolve_binding(media.get("url_binding"), object_type, instance, raw_state)
        validated = self.media_policy.validate_url(
            raw_url,
            project.get("media_policy") or {},
            purpose="video",
            requested_kind=media.get("kind", "auto"),
        )
        playback = copy.deepcopy(media.get("playback") or {})
        playback.setdefault("autoplay", True)
        playback.setdefault("muted", True)
        playback.setdefault("loop", False)
        if validated["kind"] == "hls":
            playback["loop"] = False
        return {
            "instance_id": instance_id,
            "config_revision": f"t{type_env['revision']}-i{override_env['revision']}",
            "kind": validated["kind"],
            "url": validated["url"],
            "source_revision": hashlib.sha256(validated["url"].encode("utf-8")).hexdigest()[:16],
            "expires_at": None,
            "playback": playback,
            "retry": {"delays_seconds": [2, 5, 15], "max_attempts": 3},
        }

    def save_type(self, rid, config, expected_revision, expected_project_id=None):
        validate_full_config(config)
        normalized_config = normalize_full_config(config)

        def update(project):
            object_type = self._find_type(project, rid)
            self._ensure_attached(object_type)
            self._validate_literal_media(normalized_config, project)
            configs = object_type.setdefault("interface_configs", {})
            current = _envelope(configs, "I3D_Overlay")
            if int(expected_revision) != current["revision"]:
                raise OverlayConflictError("类型配置已被其他页面更新")
            envelope = {
                "revision": current["revision"] + 1,
                "values": copy.deepcopy(normalized_config),
            }
            configs["I3D_Overlay"] = envelope
            return copy.deepcopy(envelope)

        return self.store.transact_expected_active(expected_project_id, update)

    def save_instance(self, instance_id, values, expected_revision, expected_project_id=None):
        validate_override(values)

        def update(project):
            instance = self._find_instance(project, instance_id)
            object_type = self._find_type(project, instance.get("object_type_rid"))
            self._ensure_attached(object_type)
            type_env = _envelope(object_type.get("interface_configs"), "I3D_Overlay")
            resolved = merge_overlay_config(_type_values_with_defaults(type_env), values)
            validate_full_config(resolved)
            self._validate_literal_media(resolved, project)
            render_config = instance.setdefault("render_config", {})
            overrides = render_config.setdefault("interface_overrides", {})
            current = _envelope(overrides, "I3D_Overlay")
            if int(expected_revision) != current["revision"]:
                raise OverlayConflictError("实例覆盖已被其他页面更新")
            envelope = {"revision": current["revision"] + 1, "values": copy.deepcopy(values)}
            overrides["I3D_Overlay"] = envelope
            return copy.deepcopy(envelope)

        return self.store.transact_expected_active(expected_project_id, update)

    def clear_instance(self, instance_id, expected_revision, expected_project_id=None):
        return self.save_instance(instance_id, {}, expected_revision, expected_project_id)

    def batch_instances(self, object_type_rid, instance_ids, merge_patch, expected_revisions,
                        expected_project_id=None):
        if not isinstance(instance_ids, list) or not instance_ids or len(instance_ids) > 200:
            raise OverlayValidationError("批量实例数量必须为 1 至 200")
        if len(set(instance_ids)) != len(instance_ids):
            raise OverlayValidationError("批量实例不能重复")
        if not isinstance(merge_patch, dict):
            raise OverlayValidationError("merge_patch 必须是对象")
        expected_revisions = expected_revisions or {}

        def update(project):
            object_type = self._find_type(project, object_type_rid)
            self._ensure_attached(object_type)
            type_env = _envelope(object_type.get("interface_configs"), "I3D_Overlay")
            prepared = []
            for instance_id in instance_ids:
                instance = self._find_instance(project, instance_id)
                if instance.get("object_type_rid") != object_type_rid:
                    raise OverlayValidationError("批量目标必须属于同一类型")
                overrides = instance.setdefault("render_config", {}).setdefault("interface_overrides", {})
                current = _envelope(overrides, "I3D_Overlay")
                if instance_id not in expected_revisions or int(expected_revisions[instance_id]) != current["revision"]:
                    raise OverlayConflictError(f"实例 {instance_id} 的覆盖配置已更新")
                values = apply_merge_patch(current["values"], merge_patch)
                validate_override(values)
                resolved = merge_overlay_config(_type_values_with_defaults(type_env), values)
                validate_full_config(resolved)
                self._validate_literal_media(resolved, project)
                prepared.append((overrides, current, values, instance_id))

            result = []
            for overrides, current, values, instance_id in prepared:
                envelope = {"revision": current["revision"] + 1, "values": values}
                overrides["I3D_Overlay"] = envelope
                result.append({"instance_id": instance_id, "revision": envelope["revision"]})
            return result

        return self.store.transact_expected_active(expected_project_id, update)
