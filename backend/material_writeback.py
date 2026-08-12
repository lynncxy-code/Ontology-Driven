"""Atomic material-slot writeback for UE assembly preview edits.

The endpoint contract carries both the database baseline and the desired UE
material paths.  A write is accepted only while the active project, assembly
signature, part identity, and old material array still match.  Bound component
render configs are updated in the same project transaction so a later mint
cannot restore stale materials.
"""

from __future__ import annotations

from dataclasses import dataclass

from project_store import ProjectMismatch


MAX_INSTANCES = 100
MAX_PARTS = 5000
MAX_MATERIAL_SLOTS = 256
MAX_PATH_LENGTH = 1024


@dataclass
class MaterialWritebackError(Exception):
    code: str
    message: str
    status: int = 400
    details: dict | None = None

    def response(self):
        payload = {"error": self.code, "message": self.message}
        if self.details:
            payload.update(self.details)
        return payload


def _clean_text(value):
    return str(value or "").strip()


def _material_paths(value, field, *, allow_empty_array=False):
    if not isinstance(value, list):
        raise MaterialWritebackError("invalid_material_paths", f"{field} must be an array")
    if not value and not allow_empty_array:
        raise MaterialWritebackError("invalid_material_paths", f"{field} must not be empty")
    if len(value) > MAX_MATERIAL_SLOTS:
        raise MaterialWritebackError(
            "too_many_material_slots",
            f"{field} contains more than {MAX_MATERIAL_SLOTS} slots",
        )

    result = []
    for index, raw_path in enumerate(value):
        if not isinstance(raw_path, str):
            raise MaterialWritebackError(
                "invalid_material_path", f"{field}[{index}] must be a string"
            )
        path = raw_path.strip()
        if len(path) > MAX_PATH_LENGTH or any(ord(char) < 32 for char in path):
            raise MaterialWritebackError(
                "invalid_material_path", f"{field}[{index}] is not a valid UE object path"
            )
        if path and not path.startswith("/"):
            raise MaterialWritebackError(
                "invalid_material_path", f"{field}[{index}] must start with '/'"
            )
        result.append(path)
    return result


def _part_identity(part):
    return (
        _clean_text(part.get("asset_path")),
        _clean_text(part.get("source_actor_guid")),
        _clean_text(part.get("source_component_name")),
    )


def _normalize_changes(changes):
    if not isinstance(changes, list) or not changes:
        raise MaterialWritebackError(
            "changes_required", "changes must be a non-empty array"
        )
    if len(changes) > MAX_INSTANCES:
        raise MaterialWritebackError(
            "too_many_instances", f"at most {MAX_INSTANCES} instances are allowed"
        )

    normalized = []
    seen_instances = set()
    total_parts = 0
    for instance_index, change in enumerate(changes):
        if not isinstance(change, dict):
            raise MaterialWritebackError(
                "invalid_change", f"changes[{instance_index}] must be an object"
            )
        instance_id = _clean_text(change.get("instance_id"))
        if not instance_id:
            raise MaterialWritebackError(
                "instance_id_required", f"changes[{instance_index}].instance_id is required"
            )
        if instance_id in seen_instances:
            raise MaterialWritebackError(
                "duplicate_instance", f"duplicate instance_id: {instance_id}"
            )
        seen_instances.add(instance_id)

        assembly_signature = _clean_text(change.get("expected_assembly_signature"))
        if not assembly_signature:
            raise MaterialWritebackError(
                "assembly_signature_required",
                f"expected_assembly_signature is required for {instance_id}",
            )
        parts = change.get("parts")
        if not isinstance(parts, list) or not parts:
            raise MaterialWritebackError(
                "parts_required", f"parts must be a non-empty array for {instance_id}"
            )

        normalized_parts = []
        seen_identities = set()
        for part_offset, part in enumerate(parts):
            if not isinstance(part, dict):
                raise MaterialWritebackError(
                    "invalid_part",
                    f"parts[{part_offset}] must be an object for {instance_id}",
                )
            try:
                part_index = int(part.get("part_index"))
            except (TypeError, ValueError):
                raise MaterialWritebackError(
                    "invalid_part_index",
                    f"parts[{part_offset}].part_index must be an integer for {instance_id}",
                )
            if part_index < 0:
                raise MaterialWritebackError(
                    "invalid_part_index",
                    f"parts[{part_offset}].part_index must be non-negative for {instance_id}",
                )

            identity = _part_identity(part)
            if not identity[0]:
                raise MaterialWritebackError(
                    "asset_path_required",
                    f"parts[{part_offset}].asset_path is required for {instance_id}",
                )
            if identity in seen_identities:
                raise MaterialWritebackError(
                    "duplicate_part", f"duplicate part identity for {instance_id}: {identity!r}"
                )
            seen_identities.add(identity)

            expected_paths = _material_paths(
                part.get("expected_material_paths"),
                f"{instance_id}.parts[{part_offset}].expected_material_paths",
                allow_empty_array=True,
            )
            material_paths = _material_paths(
                part.get("material_paths"),
                f"{instance_id}.parts[{part_offset}].material_paths",
            )
            if material_paths == expected_paths:
                raise MaterialWritebackError(
                    "unchanged_material_paths",
                    f"material paths did not change for {instance_id} part {part_index}",
                )
            normalized_parts.append({
                "part_index": part_index,
                "asset_path": identity[0],
                "source_actor_guid": identity[1],
                "source_component_name": identity[2],
                "expected_material_paths": expected_paths,
                "material_paths": material_paths,
            })

        total_parts += len(normalized_parts)
        if total_parts > MAX_PARTS:
            raise MaterialWritebackError(
                "too_many_parts", f"at most {MAX_PARTS} changed parts are allowed"
            )
        normalized.append({
            "instance_id": instance_id,
            "expected_assembly_signature": assembly_signature,
            "parts": normalized_parts,
        })
    return normalized, total_parts


def _find_part(render_parts, change, owner):
    requested_index = change["part_index"]
    identity = _part_identity(change)
    if 0 <= requested_index < len(render_parts):
        candidate = render_parts[requested_index]
        if isinstance(candidate, dict) and _part_identity(candidate) == identity:
            return requested_index

    matches = [
        index
        for index, part in enumerate(render_parts)
        if isinstance(part, dict) and _part_identity(part) == identity
    ]
    if len(matches) != 1:
        raise MaterialWritebackError(
            "part_identity_conflict",
            f"part identity no longer resolves uniquely for {owner}",
            status=409,
            details={
                "instance_id": owner,
                "part_index": requested_index,
                "asset_path": change["asset_path"],
                "match_count": len(matches),
            },
        )
    return matches[0]


def _patch_render_config(config, instance_change, owner):
    expected_signature = instance_change["expected_assembly_signature"]
    current_signature = _clean_text(config.get("assembly_signature"))
    if current_signature != expected_signature:
        raise MaterialWritebackError(
            "assembly_conflict",
            f"assembly changed after preview pull for {owner}",
            status=409,
            details={
                "instance_id": instance_change["instance_id"],
                "expected_assembly_signature": expected_signature,
                "current_assembly_signature": current_signature,
            },
        )
    render_parts = config.get("render_parts")
    if not isinstance(render_parts, list):
        raise MaterialWritebackError(
            "render_parts_missing",
            f"render_parts are unavailable for {owner}",
            status=409,
            details={"instance_id": instance_change["instance_id"]},
        )

    applied = []
    used_indices = set()
    for part_change in instance_change["parts"]:
        part_index = _find_part(render_parts, part_change, owner)
        if part_index in used_indices:
            raise MaterialWritebackError(
                "duplicate_resolved_part",
                f"multiple changes resolved to part {part_index} for {owner}",
            )
        used_indices.add(part_index)
        part = render_parts[part_index]
        current_paths = [str(path or "") for path in (part.get("material_paths") or [])]
        expected_paths = part_change["expected_material_paths"]
        if current_paths != expected_paths:
            raise MaterialWritebackError(
                "material_conflict",
                f"material paths changed after preview pull for {owner} part {part_index}",
                status=409,
                details={
                    "instance_id": instance_change["instance_id"],
                    "part_index": part_index,
                    "asset_path": part_change["asset_path"],
                    "expected_material_paths": expected_paths,
                    "current_material_paths": current_paths,
                },
            )
        part["material_paths"] = list(part_change["material_paths"])
        applied.append(part_index)
    return applied


def apply_material_writeback(store, changes, expected_project_id=None):
    """Apply one editor-preview material session as a single project transaction."""
    try:
        normalized, total_parts = _normalize_changes(changes)
    except MaterialWritebackError as error:
        return False, error.response(), error.status

    def mutate(project):
        instances = project.get("instances") or {}
        components = project.get("components") or {}
        results = []
        component_sync_count = 0
        for instance_change in normalized:
            instance_id = instance_change["instance_id"]
            instance = instances.get(instance_id)
            if not isinstance(instance, dict):
                raise MaterialWritebackError(
                    "instance_not_found",
                    f"instance not found: {instance_id}",
                    status=404,
                    details={"instance_id": instance_id},
                )
            config = instance.get("render_config")
            if not isinstance(config, dict):
                raise MaterialWritebackError(
                    "render_config_missing",
                    f"render config is unavailable for {instance_id}",
                    status=409,
                    details={"instance_id": instance_id},
                )
            applied_parts = _patch_render_config(config, instance_change, instance_id)

            component_id = _clean_text(instance.get("component_id"))
            component_synced = False
            component = components.get(component_id) if component_id else None
            if isinstance(component, dict):
                component_config = component.get("render_config")
                if isinstance(component_config, dict) and component_config.get("render_parts"):
                    _patch_render_config(
                        component_config,
                        instance_change,
                        f"component:{component_id}",
                    )
                    component_synced = True
                    component_sync_count += 1
            results.append({
                "instance_id": instance_id,
                "part_indices": applied_parts,
                "component_id": component_id,
                "component_synced": component_synced,
            })
        return {
            "instance_ids": [change["instance_id"] for change in normalized],
            "instance_count": len(normalized),
            "part_count": total_parts,
            "component_sync_count": component_sync_count,
            "results": results,
        }

    try:
        info = store.transact_expected_active(expected_project_id, mutate)
    except ProjectMismatch:
        raise
    except MaterialWritebackError as error:
        return False, error.response(), error.status
    except RuntimeError as error:
        return False, {"error": "material_writeback_failed", "message": str(error)}, 409
    except Exception as error:
        return False, {"error": "material_writeback_persist_failed", "message": str(error)}, 500
    return True, info, 200
