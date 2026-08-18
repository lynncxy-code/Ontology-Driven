"""Automatic, atomic import for offline UE customer-edit change sets."""

from __future__ import annotations

import copy
import json
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from project_store import ProjectMismatch, _default_raw_state


SCHEMA = "ontotwin.customer_edit_changes.v2"
ADDED_TYPE_RID = "ontotwin.customer.added_model"
MODEL_CONFIG_FIELDS = {
    "asset_id", "ue_asset_path", "assembly_signature", "render_parts",
    "source_actor_guids", "unsupported_components", "model_override",
}


@dataclass
class CustomerEditError(Exception):
    code: str
    message: str
    details: dict | None = None

    def __str__(self):
        return self.message

    def response(self):
        result = {"error": self.code, "message": self.message}
        if self.details:
            result.update(self.details)
        return result


def load_change_document(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise CustomerEditError("invalid_document", "change document must be an object")
    return document


def _text(value):
    return str(value or "").strip()


def _number(value, field):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise CustomerEditError("invalid_number", f"{field} must be a number")
    if not math.isfinite(result):
        raise CustomerEditError("invalid_number", f"{field} must be finite")
    return result


def _transform(value, field):
    if not isinstance(value, dict):
        raise CustomerEditError("invalid_transform", f"{field} must be an object")
    return {
        key: _number(value.get(key, default), f"{field}.{key}")
        for key, default in (
            ("tx", 0.0), ("ty", 0.0), ("tz", 0.0),
            ("rx", 0.0), ("ry", 0.0), ("rz", 0.0),
            ("sx", 1.0), ("sy", 1.0), ("sz", 1.0),
        )
    }


def _render_config(value, field):
    if not isinstance(value, dict):
        raise CustomerEditError("invalid_render_config", f"{field} must be an object")
    config = copy.deepcopy(value)
    parts = config.get("render_parts")
    if not isinstance(parts, list) or not parts:
        raise CustomerEditError("render_parts_required", f"{field}.render_parts must be non-empty")
    for index, part in enumerate(parts):
        if not isinstance(part, dict) or not _text(part.get("asset_path")).startswith("/"):
            raise CustomerEditError("invalid_render_part", f"{field}.render_parts[{index}] is invalid")
        materials = part.get("material_paths")
        if not isinstance(materials, list) or any(
            not isinstance(path, str) or (path and not path.startswith("/")) for path in materials
        ):
            raise CustomerEditError("invalid_material_paths", f"{field}.render_parts[{index}] is invalid")
    signature = _text(config.get("assembly_signature"))
    if not signature:
        raise CustomerEditError("assembly_signature_required", f"{field}.assembly_signature is required")
    config["asset_id"] = _text(config.get("asset_id")) or _text(parts[0].get("asset_path"))
    config["ue_asset_path"] = _text(config.get("ue_asset_path")) or config["asset_id"]
    config["assembly_signature"] = signature
    config.pop("model_override", None)
    return config


def _normalize_material_parts(value, field):
    if value is None:
        return []
    if not isinstance(value, list):
        raise CustomerEditError("invalid_material_parts", f"{field} must be an array")
    result = []
    for index, part in enumerate(value):
        if not isinstance(part, dict):
            raise CustomerEditError("invalid_material_part", f"{field}[{index}] must be an object")
        try:
            part_index = int(part.get("part_index"))
        except (TypeError, ValueError):
            raise CustomerEditError("invalid_part_index", f"{field}[{index}].part_index is invalid")
        expected = part.get("expected_material_paths")
        desired = part.get("material_paths")
        if not isinstance(expected, list) or not isinstance(desired, list) or not desired:
            raise CustomerEditError("invalid_material_paths", f"{field}[{index}] is invalid")
        result.append({
            "part_index": part_index,
            "asset_path": _text(part.get("asset_path")),
            "source_actor_guid": _text(part.get("source_actor_guid")),
            "source_component_name": _text(part.get("source_component_name")),
            "expected_material_paths": list(expected),
            "material_paths": list(desired),
        })
    return result


def normalize_document(document):
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise CustomerEditError("unsupported_schema", f"expected schema {SCHEMA}")
    project_id = _text(document.get("project_id"))
    if not project_id:
        raise CustomerEditError("project_id_required", "project_id is required")
    operations = document.get("instance_operations") or []
    overrides = document.get("overrides") or []
    if not isinstance(operations, list) or len(operations) > 5000:
        raise CustomerEditError("invalid_operations", "instance_operations is invalid or too large")
    if not isinstance(overrides, list) or len(overrides) > 5000:
        raise CustomerEditError("invalid_overrides", "overrides is invalid or too large")

    normalized_operations = []
    operation_ids = set()
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise CustomerEditError("invalid_operation", f"instance_operations[{index}] must be an object")
        action = _text(operation.get("op")).lower()
        instance_id = _text(operation.get("instance_id"))
        if action not in {"replace", "delete", "create"} or not instance_id:
            raise CustomerEditError("invalid_operation", f"instance_operations[{index}] is invalid")
        if instance_id in operation_ids:
            raise CustomerEditError("duplicate_operation", f"duplicate operation for {instance_id}")
        operation_ids.add(instance_id)
        item = {"op": action, "instance_id": instance_id}
        if action in {"replace", "delete"}:
            item["expected_object_type_rid"] = _text(operation.get("expected_object_type_rid"))
            item["expected_assembly_signature"] = _text(operation.get("expected_assembly_signature"))
            if not item["expected_object_type_rid"] or not item["expected_assembly_signature"]:
                raise CustomerEditError("expected_state_required", f"{action} for {instance_id} lacks expected state")
        if action in {"replace", "create"}:
            item["transform"] = _transform(operation.get("transform"), f"{instance_id}.transform")
            item["render_config"] = _render_config(operation.get("render_config"), f"{instance_id}.render_config")
            item["display_name"] = _text(operation.get("display_name")) or instance_id
            item["object_type_rid"] = _text(operation.get("object_type_rid")) or ADDED_TYPE_RID
        normalized_operations.append(item)

    normalized_overrides = []
    override_ids = set()
    for index, override in enumerate(overrides):
        if not isinstance(override, dict):
            raise CustomerEditError("invalid_override", f"overrides[{index}] must be an object")
        instance_id = _text(override.get("instance_id"))
        if not instance_id or instance_id in override_ids:
            raise CustomerEditError("invalid_override", f"invalid or duplicate override for {instance_id}")
        if instance_id in operation_ids:
            raise CustomerEditError("operation_override_conflict", f"{instance_id} is both operation and override")
        override_ids.add(instance_id)
        item = {
            "instance_id": instance_id,
            "expected_assembly_signature": _text(override.get("expected_assembly_signature")),
            "material_parts": _normalize_material_parts(override.get("material_parts"), f"{instance_id}.material_parts"),
        }
        if "transform" in override:
            item["transform"] = _transform(override.get("transform"), f"{instance_id}.transform")
            item["expected_transform"] = _transform(override.get("expected_transform"), f"{instance_id}.expected_transform")
        if "transform" not in item and not item["material_parts"]:
            raise CustomerEditError("empty_override", f"override for {instance_id} has no changes")
        normalized_overrides.append(item)
    return {"project_id": project_id, "operations": normalized_operations, "overrides": normalized_overrides}


def _current_transform(instance):
    raw = instance.get("raw_state") or {}
    return {
        "tx": float(raw.get("translation_x", 0)), "ty": float(raw.get("translation_y", 0)),
        "tz": float(raw.get("translation_z", 0)), "rx": float(raw.get("rotation_x", 0)),
        "ry": float(raw.get("rotation_y", 0)), "rz": float(raw.get("rotation_z", 0)),
        "sx": float(raw.get("scale_x", 1)), "sy": float(raw.get("scale_y", 1)),
        "sz": float(raw.get("scale_z", 1)),
    }


def _assert_transform_matches(instance_id, expected, instance):
    current = _current_transform(instance)
    for key in expected:
        tolerance = 0.02 if key.startswith("t") else 0.001
        if abs(current[key] - expected[key]) > tolerance:
            raise CustomerEditError(
                "transform_conflict", f"spatial state changed after preview pull for {instance_id}",
                {"instance_id": instance_id, "expected_transform": expected, "current_transform": current},
            )


def _apply_transform(instance, transform):
    raw = instance.setdefault("raw_state", {})
    for short, full in (("tx", "translation_x"), ("ty", "translation_y"), ("tz", "translation_z"),
                        ("rx", "rotation_x"), ("ry", "rotation_y"), ("rz", "rotation_z"),
                        ("sx", "scale_x"), ("sy", "scale_y"), ("sz", "scale_z")):
        raw[full] = transform[short]


def _assert_expected_instance(operation, instance):
    instance_id = operation["instance_id"]
    if not isinstance(instance, dict):
        raise CustomerEditError("instance_not_found", f"instance not found: {instance_id}")
    actual_type = _text(instance.get("object_type_rid"))
    if actual_type != operation["expected_object_type_rid"]:
        raise CustomerEditError("object_type_conflict", f"object type changed for {instance_id}")
    actual_signature = _text((instance.get("render_config") or {}).get("assembly_signature"))
    if actual_signature != operation["expected_assembly_signature"]:
        raise CustomerEditError("assembly_conflict", f"model changed for {instance_id}")


def _merge_model_config(existing, replacement):
    merged = copy.deepcopy(existing) if isinstance(existing, dict) else {}
    for key in MODEL_CONFIG_FIELDS:
        merged.pop(key, None)
    merged.update(copy.deepcopy(replacement))
    merged.pop("model_override", None)
    return merged


def _part_identity(part):
    return (_text(part.get("asset_path")), _text(part.get("source_actor_guid")), _text(part.get("source_component_name")))


def _apply_material_parts(instance_id, render_config, changes):
    if not changes:
        return 0
    parts = render_config.get("render_parts") if isinstance(render_config, dict) else None
    if not isinstance(parts, list):
        raise CustomerEditError("render_parts_missing", f"render parts missing for {instance_id}")
    for change in changes:
        index = change["part_index"]
        identity = _part_identity(change)
        if not (0 <= index < len(parts) and _part_identity(parts[index]) == identity):
            matches = [i for i, part in enumerate(parts) if isinstance(part, dict) and _part_identity(part) == identity]
            if len(matches) != 1:
                raise CustomerEditError("part_identity_conflict", f"render part changed for {instance_id}")
            index = matches[0]
        current = list(parts[index].get("material_paths") or [])
        if current != change["expected_material_paths"]:
            raise CustomerEditError("material_conflict", f"material changed for {instance_id}")
        parts[index]["material_paths"] = list(change["material_paths"])
    return len(changes)


def _ensure_added_type(project):
    project.setdefault("object_types", {}).setdefault(ADDED_TYPE_RID, {
        "rid": ADDED_TYPE_RID, "name": "客户新增模型", "category": "客户编辑",
        "description": "由离线 UE 客户编辑包自动新增，待后续按业务语义归类。",
        "color": "#64748B", "properties": [],
        "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "asset_id": None, "mock_instances": [], "source": "customer_edit_auto",
    })


def mutate_project(project, normalized):
    if _text(project.get("id")) != normalized["project_id"]:
        raise CustomerEditError("project_mismatch", "active project does not match the customer snapshot")
    instances = project.setdefault("instances", {})
    components = project.setdefault("components", {})
    summary = {"replaced": 0, "deleted": 0, "created": 0, "overridden": 0,
               "material_parts": 0, "component_models_synced": 0, "component_bindings_cleared": 0}

    # Validate everything against the same working snapshot before mutation.
    for operation in normalized["operations"]:
        instance = instances.get(operation["instance_id"])
        if operation["op"] in {"replace", "delete"}:
            _assert_expected_instance(operation, instance)
        elif instance is not None:
            raise CustomerEditError("instance_already_exists", f"create target exists: {operation['instance_id']}")
    for override in normalized["overrides"]:
        instance = instances.get(override["instance_id"])
        if not isinstance(instance, dict):
            raise CustomerEditError("instance_not_found", f"instance not found: {override['instance_id']}")
        if "expected_transform" in override:
            _assert_transform_matches(override["instance_id"], override["expected_transform"], instance)
        expected_signature = override["expected_assembly_signature"]
        if expected_signature and _text((instance.get("render_config") or {}).get("assembly_signature")) != expected_signature:
            raise CustomerEditError("assembly_conflict", f"model changed for {override['instance_id']}")
        _apply_material_parts(override["instance_id"], copy.deepcopy(instance.get("render_config") or {}), override["material_parts"])

    for operation in normalized["operations"]:
        action, instance_id = operation["op"], operation["instance_id"]
        if action == "replace":
            instance = instances[instance_id]
            replacement = operation["render_config"]
            instance["render_config"] = _merge_model_config(instance.get("render_config"), replacement)
            _apply_transform(instance, operation["transform"])
            instance["raw_state"]["asset_id"] = replacement["asset_id"]
            instance["source_asset_path"] = replacement["asset_id"]
            instance["classification_key"] = f"assembly_signature:{replacement['assembly_signature']}"
            for component in components.values():
                if isinstance(component, dict) and component.get("bound_instance_id") == instance_id:
                    component["render_config"] = _merge_model_config(component.get("render_config"), replacement)
                    summary["component_models_synced"] += 1
            summary["replaced"] += 1
        elif action == "delete":
            instances.pop(instance_id)
            for component in components.values():
                if isinstance(component, dict) and component.get("bound_instance_id") == instance_id:
                    component["bound_instance_id"] = None
                    summary["component_bindings_cleared"] += 1
            project["instance_roster"] = [e for e in (project.get("instance_roster") or [])
                                          if not isinstance(e, dict) or e.get("instance_id") != instance_id]
            summary["deleted"] += 1
        else:
            _ensure_added_type(project)
            type_rid = operation["object_type_rid"]
            if type_rid not in project["object_types"]:
                type_rid = ADDED_TYPE_RID
            type_record = project["object_types"][type_rid]
            now = time.time()
            raw = _default_raw_state(type_rid, type_record.get("name"), None)
            instance = {
                "id": instance_id, "object_type_rid": type_rid,
                "object_type_name": type_record.get("name") or type_rid,
                "display_name": operation["display_name"], "hierarchy_path": ["客户新增模型"],
                "source_folder_path": "CustomerEditAuto",
                "source_asset_path": operation["render_config"]["asset_id"],
                "classification_status": "pending",
                "classification_key": f"assembly_signature:{operation['render_config']['assembly_signature']}",
                "render_config": copy.deepcopy(operation["render_config"]),
                "created_at": now, "last_seen": now, "status": "offline", "raw_state": raw,
            }
            _apply_transform(instance, operation["transform"])
            instance["raw_state"]["asset_id"] = operation["render_config"]["asset_id"]
            instances[instance_id] = instance
            project.setdefault("instance_roster", []).append({
                "instance_id": instance_id, "object_type_rid": type_rid,
                "name": operation["display_name"], "source": "customer_edit_auto",
            })
            summary["created"] += 1

    for override in normalized["overrides"]:
        instance = instances[override["instance_id"]]
        if "transform" in override:
            _apply_transform(instance, override["transform"])
        summary["material_parts"] += _apply_material_parts(
            override["instance_id"], instance.get("render_config") or {}, override["material_parts"]
        )
        for component in components.values():
            if (override["material_parts"] and isinstance(component, dict)
                    and component.get("bound_instance_id") == override["instance_id"]):
                _apply_material_parts(override["instance_id"], component.get("render_config") or {}, override["material_parts"])
        summary["overridden"] += 1
    return summary


def _write_backup(project, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(backup_dir, f"customer-edit-before-{project.get('id', 'project')}-{stamp}.json")
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(project, handle, ensure_ascii=False, indent=2, default=str)
    return path


def apply_customer_edit_changes(store, document, *, commit=False, backup_dir=None):
    normalized = normalize_document(document)
    project = store.get_active_copy()
    if not isinstance(project, dict):
        raise CustomerEditError("no_active_project", "no active project")
    summary = mutate_project(copy.deepcopy(project), normalized)
    result = {"mode": "commit" if commit else "dry-run", "project_id": normalized["project_id"],
              "summary": summary, "backup_path": None}
    if not commit:
        return result
    if not backup_dir:
        raise CustomerEditError("backup_dir_required", "backup_dir is required for commit")
    result["backup_path"] = _write_backup(project, backup_dir)
    try:
        result["summary"] = store.transact_expected_active(
            normalized["project_id"], lambda working: mutate_project(working, normalized)
        )
    except ProjectMismatch as error:
        raise CustomerEditError("project_mismatch", "active project changed before commit",
                                {"expected": error.expected, "actual": error.actual})
    return result
