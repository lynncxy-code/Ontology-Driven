"""Atomic writeback for assembly render-part relative transforms.

Preview edits to ``TwinRenderPart_*`` components are stored in the instance's
``render_config.render_parts``.  The mother actor transform is intentionally
handled by :mod:`writeback`; this module only patches child-part transforms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from project_store import ProjectMismatch


MAX_INSTANCES = 100
MAX_PARTS = 5000
TRANSFORM_FIELDS = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
DEFAULTS = {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0,
            "sx": 1.0, "sy": 1.0, "sz": 1.0}


@dataclass
class PartTransformWritebackError(Exception):
    code: str
    message: str
    status: int = 400
    details: dict | None = None

    def response(self):
        payload = {"error": self.code, "message": self.message}
        if self.details:
            payload.update(self.details)
        return payload


def _text(value):
    return str(value or "").strip()


def _identity(part):
    return (_text(part.get("asset_path")), _text(part.get("source_actor_guid")),
            _text(part.get("source_component_name")))


def _transform(value, field):
    if not isinstance(value, dict):
        raise PartTransformWritebackError("invalid_transform", f"{field} must be an object")
    result = {}
    for key in TRANSFORM_FIELDS:
        if key not in value:
            raise PartTransformWritebackError("invalid_transform", f"{field}.{key} is required")
        try:
            number = float(value[key])
        except (TypeError, ValueError):
            raise PartTransformWritebackError("invalid_transform", f"{field}.{key} must be numeric")
        if not math.isfinite(number):
            raise PartTransformWritebackError("invalid_transform", f"{field}.{key} must be finite")
        result[key] = number
    return result


def _current_transform(part):
    value = part.get("relative_transform") or part.get("transform")
    if not isinstance(value, dict):
        value = DEFAULTS
    return {key: float(value.get(key, DEFAULTS[key])) for key in TRANSFORM_FIELDS}


def _same(a, b, tolerance=0.01):
    return all(abs(float(a[key]) - float(b[key])) <= tolerance for key in TRANSFORM_FIELDS)


def _normalize(changes):
    if not isinstance(changes, list) or not changes:
        raise PartTransformWritebackError("changes_required", "changes must be a non-empty array")
    if len(changes) > MAX_INSTANCES:
        raise PartTransformWritebackError("too_many_instances", f"at most {MAX_INSTANCES} instances are allowed")
    normalized = []
    seen_instances = set()
    total = 0
    for index, change in enumerate(changes):
        if not isinstance(change, dict):
            raise PartTransformWritebackError("invalid_change", f"changes[{index}] must be an object")
        instance_id = _text(change.get("instance_id"))
        if not instance_id or instance_id in seen_instances:
            raise PartTransformWritebackError("invalid_instance_id", f"invalid or duplicate instance_id at changes[{index}]")
        seen_instances.add(instance_id)
        signature = _text(change.get("expected_assembly_signature"))
        if not signature:
            raise PartTransformWritebackError("assembly_signature_required", f"expected_assembly_signature is required for {instance_id}")
        parts = change.get("parts")
        if not isinstance(parts, list) or not parts:
            raise PartTransformWritebackError("parts_required", f"parts must be a non-empty array for {instance_id}")
        normalized_parts = []
        identities = set()
        for offset, part in enumerate(parts):
            if not isinstance(part, dict):
                raise PartTransformWritebackError("invalid_part", f"parts[{offset}] must be an object")
            try:
                part_index = int(part.get("part_index"))
            except (TypeError, ValueError):
                raise PartTransformWritebackError("invalid_part_index", f"parts[{offset}].part_index must be an integer")
            identity = _identity(part)
            if part_index < 0 or not identity[0] or identity in identities:
                raise PartTransformWritebackError("invalid_part_identity", f"invalid or duplicate part identity for {instance_id}")
            identities.add(identity)
            expected = _transform(part.get("expected_transform"), f"{instance_id}.parts[{offset}].expected_transform")
            desired = _transform(part.get("transform"), f"{instance_id}.parts[{offset}].transform")
            if _same(expected, desired):
                raise PartTransformWritebackError("unchanged_transform", f"part {part_index} did not change for {instance_id}")
            normalized_parts.append({"part_index": part_index, "asset_path": identity[0],
                "source_actor_guid": identity[1], "source_component_name": identity[2],
                "expected_transform": expected, "transform": desired})
        total += len(normalized_parts)
        if total > MAX_PARTS:
            raise PartTransformWritebackError("too_many_parts", f"at most {MAX_PARTS} changed parts are allowed")
        normalized.append({"instance_id": instance_id, "expected_assembly_signature": signature,
                           "parts": normalized_parts})
    return normalized, total


def _resolve(parts, change, owner):
    identity = (change["asset_path"], change["source_actor_guid"], change["source_component_name"])
    index = change["part_index"]
    if 0 <= index < len(parts) and isinstance(parts[index], dict) and _identity(parts[index]) == identity:
        return index
    matches = [i for i, part in enumerate(parts) if isinstance(part, dict) and _identity(part) == identity]
    if len(matches) != 1:
        raise PartTransformWritebackError("part_identity_conflict", f"part identity no longer resolves uniquely for {owner}", 409,
                                          {"instance_id": owner, "part_index": index, "match_count": len(matches)})
    return matches[0]


def _patch(config, change, owner):
    if _text(config.get("assembly_signature")) != change["expected_assembly_signature"]:
        raise PartTransformWritebackError("assembly_conflict", f"assembly changed after preview pull for {owner}", 409,
                                          {"instance_id": owner})
    parts = config.get("render_parts")
    if not isinstance(parts, list):
        raise PartTransformWritebackError("render_parts_missing", f"render_parts are unavailable for {owner}", 409,
                                          {"instance_id": owner})
    applied = []
    used = set()
    for item in change["parts"]:
        index = _resolve(parts, item, owner)
        if index in used:
            raise PartTransformWritebackError("duplicate_resolved_part", f"multiple changes resolved to part {index} for {owner}")
        used.add(index)
        current = _current_transform(parts[index])
        if not _same(current, item["expected_transform"]):
            raise PartTransformWritebackError("transform_conflict", f"part transform changed after preview pull for {owner} part {index}", 409,
                                              {"instance_id": owner, "part_index": index,
                                               "current_transform": current,
                                               "expected_transform": item["expected_transform"]})
        parts[index]["relative_transform"] = dict(item["transform"])
        parts[index].pop("transform", None)
        applied.append(index)
    return applied


def apply_part_transform_writeback(store, changes, expected_project_id=None):
    try:
        normalized, total = _normalize(changes)
    except PartTransformWritebackError as error:
        return False, error.response(), error.status

    def mutate(project):
        instances = project.get("instances") or {}
        components = project.get("components") or {}
        results = []
        component_count = 0
        for change in normalized:
            instance_id = change["instance_id"]
            instance = instances.get(instance_id)
            if not isinstance(instance, dict):
                raise PartTransformWritebackError("instance_not_found", f"instance not found: {instance_id}", 404,
                                                  {"instance_id": instance_id})
            config = instance.get("render_config")
            if not isinstance(config, dict):
                raise PartTransformWritebackError("render_config_missing", f"render config is unavailable for {instance_id}", 409)
            applied = _patch(config, change, instance_id)
            component_id = _text(instance.get("component_id"))
            component = components.get(component_id) if component_id else None
            synced = False
            if isinstance(component, dict) and isinstance(component.get("render_config"), dict) and component["render_config"].get("render_parts"):
                _patch(component["render_config"], change, f"component:{component_id}")
                component_count += 1
                synced = True
            results.append({"instance_id": instance_id, "part_indices": applied, "component_id": component_id, "component_synced": synced})
        return {"instance_ids": [item["instance_id"] for item in normalized], "instance_count": len(normalized),
                "part_count": total, "component_sync_count": component_count, "results": results}

    try:
        info = store.transact_expected_active(expected_project_id, mutate)
    except ProjectMismatch:
        raise
    except PartTransformWritebackError as error:
        return False, error.response(), error.status
    except RuntimeError as error:
        return False, {"error": "part_transform_writeback_failed", "message": str(error)}, 409
    except Exception as error:
        return False, {"error": "part_transform_writeback_persist_failed", "message": str(error)}, 500
    return True, info, 200
