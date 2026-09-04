"""Shared safety gates for declarative UE instance replacement.

This module intentionally contains no storage or UE-specific I/O.  Migration
tools use it to validate an explicit replacement scope and to compare a
dry-run manifest immediately before an apply.  Keeping the gates here avoids
the test0316 workflow growing a second, weaker implementation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable, Iterable, Mapping


def sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def instance_ids_hash(ids: Iterable[str]) -> str:
    payload = "\n".join(sorted(str(value) for value in ids)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def values_hash(values: Iterable[str]) -> str:
    return instance_ids_hash(values)


def _required_unique(values: object, label: str) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        raise SystemExit(f"replacement {label} must be an explicit list")
    normalized = [str(value or "").strip() for value in values]
    if any(not value for value in normalized):
        raise SystemExit(f"replacement {label} contains an empty value")
    if len(set(normalized)) != len(normalized):
        raise SystemExit(f"replacement {label} must be unique")
    return normalized


def declared_scope(declaration: Mapping[str, object]) -> tuple[list[str], list[str]]:
    """Return explicit old instance IDs and source Actor GUIDs.

    ``source_container_guids`` is retained as a backwards-compatible alias
    for the first replacement manifest format.  New manifests should use
    ``source_actor_guids``.
    """

    if not isinstance(declaration, Mapping):
        raise SystemExit("replacement declaration is required")
    old_ids = _required_unique(declaration.get("old_instance_ids"), "old_instance_ids")
    source_guids = declaration.get("source_actor_guids")
    if source_guids is None:
        source_guids = declaration.get("source_container_guids")
    source_guids = _required_unique(source_guids, "source_actor_guids")
    return old_ids, source_guids


def validate_project_identity(
    payload: Mapping[str, object],
    project_id: str,
    *,
    bound_ue_project_id: str = "",
    bound_ue_project_name: str = "",
    require_ue_project_id: bool = True,
) -> None:
    """Reject a plan that is not explicitly for the active project/binding."""

    expected_project = str(payload.get("project_id") or "").strip()
    if not expected_project or expected_project != str(project_id).strip():
        raise SystemExit(f"project_id_mismatch:{expected_project}!={project_id}")
    expected_ue = str(payload.get("ue_project_id") or "").strip()
    bound_ue = str(bound_ue_project_id or "").strip()
    if require_ue_project_id and not expected_ue:
        raise SystemExit("ue_project_id is required for declarative replacement")
    if expected_ue and bound_ue and expected_ue != bound_ue:
        raise SystemExit(f"binding_mismatch:{bound_ue}!={expected_ue}")
    if require_ue_project_id and not bound_ue:
        raise SystemExit("active project has no bound ue_project_id")
    expected_name = str(payload.get("ue_project_name") or "").strip()
    bound_name = str(bound_ue_project_name or "").strip()
    if expected_name and bound_name and expected_name != bound_name:
        raise SystemExit(f"binding_name_mismatch:{bound_name}!={expected_name}")


def validate_input_consistency(
    payload: Mapping[str, object],
    type_specs: Mapping[str, Mapping[str, object]],
    *,
    actor_type_resolver: Callable[[Mapping[str, object]], str] | None = None,
    allow_unsupported: bool = False,
) -> tuple[list[Mapping[str, object]], list[str]]:
    """Validate actor GUIDs, type references and unsupported components."""

    actors = payload.get("actors")
    if not isinstance(actors, list) or not actors:
        raise SystemExit("replacement actors must be a non-empty list")
    if not isinstance(type_specs, Mapping) or not type_specs:
        raise SystemExit("replacement type_specs must be a non-empty mapping")
    guids: list[str] = []
    source_guids: list[str] = []
    for actor in actors:
        if not isinstance(actor, Mapping):
            raise SystemExit("replacement actors must contain objects")
        guid = str(actor.get("ext_guid") or "").strip()
        if not guid or guid in guids:
            raise SystemExit("replacement actor ext_guid must be present and unique")
        guids.append(guid)
        nested = actor.get("source_actor_guids") or [guid]
        if not isinstance(nested, (list, tuple, set)):
            nested = [nested]
        for value in nested:
            source = str(value or "").strip()
            if not source:
                raise SystemExit("replacement source_actor_guids contains an empty value")
            if source not in source_guids:
                source_guids.append(source)
        if actor.get("unsupported_components") and not allow_unsupported:
            raise SystemExit(f"replacement unsupported components: {guid}")
        if actor_type_resolver is not None:
            rid = str(actor_type_resolver(actor) or "").strip()
            if not rid or rid not in type_specs:
                raise SystemExit(f"replacement actor type is missing from type_specs:{guid}:{rid}")
    return actors, source_guids


def manifest_hashes(
    payload: Mapping[str, object],
    type_specs: Mapping[str, object],
    *,
    replaced_live_instance_ids: Iterable[str],
    final_instance_ids: Iterable[str],
    new_instance_ids: Iterable[str],
    final_instance_count: int,
    final_type_count: int,
) -> dict[str, object]:
    """Return deterministic digest/count fields shared by all replacement plans."""

    actors = payload.get("actors") or []
    new_ids = list(new_instance_ids)
    source_guids = []
    for actor in actors:
        if not isinstance(actor, Mapping):
            continue
        values = actor.get("source_actor_guids") or [actor.get("ext_guid")]
        if not isinstance(values, (list, tuple, set)):
            values = [values]
        source_guids.extend(str(value or "").strip() for value in values if str(value or "").strip())
    return {
        "input_digest": sha256_json(payload),
        "types_digest": sha256_json(type_specs),
        "source_actor_guids_hash": values_hash(source_guids),
        "replaced_live_instance_ids_hash": instance_ids_hash(replaced_live_instance_ids),
        "new_instance_ids_hash": instance_ids_hash(new_ids),
        "final_instance_ids_hash": instance_ids_hash(final_instance_ids),
        "new_instance_count": len(new_ids),
        "new_type_count": len(type_specs),
        "final_instance_count": int(final_instance_count),
        "final_type_count": int(final_type_count),
    }


def validate_declared_scope(
    declaration: Mapping[str, object],
    instances: Mapping[str, Mapping[str, object]],
    *,
    expected_source: str | None = "ue_migrated",
) -> tuple[list[str], list[str]]:
    """Validate that the replacement is limited to the declared records."""

    old_ids, source_guids = declared_scope(declaration)
    missing = [instance_id for instance_id in old_ids if instance_id not in instances]
    if missing:
        raise SystemExit(f"replacement old instances are missing: {missing}")
    wrong_source = []
    if expected_source is not None:
        wrong_source = [
            instance_id
            for instance_id in old_ids
            if str((instances[instance_id] or {}).get("source") or "") != expected_source
        ]
    if wrong_source:
        raise SystemExit(f"replacement old instances have unexpected source: {wrong_source}")
    actual_guids = [
        str((instances[instance_id] or {}).get("ext_guid") or "").strip()
        for instance_id in old_ids
    ]
    if any(not guid for guid in actual_guids):
        raise SystemExit("replacement old instances must all have ext_guid")
    if not set(actual_guids).issubset(set(source_guids)):
        raise SystemExit("replacement source_actor_guids do not include old instances")
    return old_ids, source_guids


def validate_apply_manifest(
    expected: Mapping[str, object],
    actual: Mapping[str, object],
    *,
    strict: bool = True,
) -> None:
    """Compare an apply plan with its approved dry-run manifest.

    Older test0316 manifests contain the four original fields; those remain
    accepted when ``strict=False`` so the checked-in fixtures can be replayed.
    New callers should keep the default strict gate.
    """

    legacy_keys = (
        "project_before_digest",
        "new_instance_ids_hash",
        "new_instance_count",
        "new_type_count",
    )
    strict_keys = legacy_keys + (
        "final_instance_ids_hash",
        "final_instance_count",
        "final_type_count",
        "replaced_live_instance_ids_hash",
        "source_actor_guids_hash",
        "input_digest",
        "types_digest",
    )
    keys = strict_keys if strict else legacy_keys
    for key in keys:
        if key not in expected:
            if strict:
                raise SystemExit(f"apply_gate_missing:{key}")
            continue
        if expected.get(key) != actual.get(key):
            raise SystemExit(f"apply_gate_mismatch:{key}:{actual.get(key)}!={expected.get(key)}")


def apply_declared_replacement(
    declaration: Mapping[str, object],
    instances: dict[str, dict],
    instance_mapping: Mapping[str, str],
    stats: dict[str, int],
    delete_actor_guids: list[str],
    *,
    expected_source: str | None = "ue_migrated",
) -> tuple[list[str], dict]:
    """Validate and stage an exact old-assembly/new-instance atomic swap."""

    old_ids, source_guids = validate_declared_scope(
        declaration, instances, expected_source=expected_source
    )
    expected_old = int(declaration.get("expected_old_instance_count") or 0)
    expected_new = int(declaration.get("expected_new_instance_count") or 0)
    expected_delete = int(declaration.get("expected_delete_actor_guid_count") or 0)
    if expected_old != len(old_ids):
        raise SystemExit("replacement expected_old_instance_count mismatch")
    if expected_new != len(instance_mapping):
        raise SystemExit(
            f"replacement expected {expected_new} migrated instances, got {len(instance_mapping)}"
        )
    new_ids = list(instance_mapping.values())
    if len(set(new_ids)) != expected_new:
        raise SystemExit("replacement generated duplicate instance IDs")
    expected_hash = str(declaration.get("new_instance_ids_hash") or "")
    if not expected_hash or expected_hash != instance_ids_hash(new_ids):
        raise SystemExit(
            f"replacement instance-ID hash mismatch: expected {expected_hash}, got {instance_ids_hash(new_ids)}"
        )
    if any(stats.get(key, 0) for key in ("blocked", "skipped", "legacy")):
        raise SystemExit("replacement refused because migration has blocked/skipped/legacy actors")
    if set(old_ids) & set(new_ids):
        raise SystemExit("replacement old and new instance IDs overlap")

    cleanup = list(delete_actor_guids)
    seen = set(cleanup)
    for guid in source_guids:
        if guid not in seen:
            seen.add(guid)
            cleanup.append(guid)
    if expected_delete != len(cleanup):
        raise SystemExit(
            f"replacement expected {expected_delete} cleanup GUIDs, got {len(cleanup)}"
        )
    for instance_id in old_ids:
        instances.pop(instance_id)
    stats["replaced"] = len(old_ids)
    return cleanup, {
        "applied": True,
        "old_instance_ids": old_ids,
        "old_instance_count": len(old_ids),
        "source_actor_guids": source_guids,
        "new_instance_count": len(new_ids),
        "new_instance_ids_hash": instance_ids_hash(new_ids),
        "delete_actor_guid_count": len(cleanup),
    }
