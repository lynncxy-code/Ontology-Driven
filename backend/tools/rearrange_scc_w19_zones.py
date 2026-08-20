"""Rearrange SCC W19 acceptance instances into separated zone clusters.

The command is intentionally project-scoped and reversible. It preserves every
instance's rotation, scale and Z coordinate, and only changes its X/Y position.

Run inside the backend container:
    python -m tools.rearrange_scc_w19_zones
    python -m tools.rearrange_scc_w19_zones --dry-run
    python -m tools.rearrange_scc_w19_zones --restore /app/tools/<backup>.json
"""

import argparse
import datetime as dt
import json
from pathlib import Path

from project_store import ProjectStore
from writeback import apply_batch_writeback, runtime_edit_state_hash


PROJECT_ID = "ds_1785130727581"
BACKUP_DIR = Path("/app/tools")
RESULT_PATH = BACKUP_DIR / "scc_w19_zone_layout_result.json"

# UE world coordinates in centimetres. Members of one Zone remain visually
# grouped; neighbouring Zone centres are roughly 30--60 metres apart.
TARGET_XY = {
    # 1F ICT equipment area: two rows, with extra room for composite machines.
    "ue_732C27F2-4870-223E-F5E7-9888CF2AF036": (0.0, -3350.0),
    "ue_8A44A1B4-4541-CF99-A2FB-50A991E7CE6D": (1500.0, -3350.0),
    "ue_77B91DE4-42A1-7174-6AD2-9EA1F0CA5996": (3000.0, -3350.0),
    "ue_3DE531C6-44FE-4163-C0FC-2DAD8A55FE8E": (0.0, -2200.0),
    "ue_663D2B5D-4490-0F92-5165-4788DE02278B": (1500.0, -2200.0),
    "ue_55DD159A-434D-CEE2-B91A-CE83EE64F145": (3300.0, -2200.0),

    # 1F SMT production area.
    "ue_accept_smt_conveyor_01": (5200.0, -3200.0),
    "ue_accept_smt_agv_01": (6100.0, -3200.0),
    "ue_accept_smt_pallet_01": (7000.0, -3200.0),

    # 1F logistics staging area.
    "ue_accept_logistics_forklift_01": (8400.0, -3200.0),
    "ue_accept_logistics_agv_02": (9300.0, -3200.0),
    "ue_accept_logistics_container_01": (10200.0, -3200.0),

    # 1F energy room.
    "ue_accept_energy_generator_01": (5100.0, 800.0),
    "ue_accept_energy_bess_01": (6200.0, 800.0),
    "ue_accept_energy_pump_01": (7300.0, 800.0),

    # 2F assembly area. Existing Z=420 cm is preserved.
    "ue_accept_assembly_conveyor_02": (8700.0, 800.0),
    "ue_accept_assembly_agv_03": (9900.0, 800.0),

    # Outdoor renewable-energy area.
    "ue_accept_energy_solar_01": (-7000.0, -3000.0),
    "ue_accept_energy_wind_01": (-4500.0, -3000.0),

    # Deliberately unassigned acceptance instance: isolated holding area.
    "ue_accept_unzoned_pallet_99": (0.0, 1000.0),
}


TRANSFORM_FIELDS = {
    "tx": "translation_x",
    "ty": "translation_y",
    "tz": "translation_z",
    "rx": "rotation_x",
    "ry": "rotation_y",
    "rz": "rotation_z",
    "sx": "scale_x",
    "sy": "scale_y",
    "sz": "scale_z",
}


def _number(raw, field, default):
    try:
        return float(raw.get(field, default))
    except (TypeError, ValueError):
        return float(default)


def _transform_from_raw(raw, target_xy=None):
    defaults = {
        "tx": 0.0, "ty": 0.0, "tz": 0.0,
        "rx": 0.0, "ry": 0.0, "rz": 0.0,
        "sx": 1.0, "sy": 1.0, "sz": 1.0,
    }
    transform = {
        key: _number(raw, raw_field, defaults[key])
        for key, raw_field in TRANSFORM_FIELDS.items()
    }
    if target_xy is not None:
        transform["tx"], transform["ty"] = target_xy
    return transform


def _changes(project, restore_transforms=None):
    instances = project.get("instances") or {}
    expected_ids = set(TARGET_XY)
    missing = sorted(expected_ids - set(instances))
    if missing:
        raise RuntimeError("Layout instances are missing: " + ", ".join(missing))

    changes = []
    for instance_id in sorted(expected_ids):
        raw = instances[instance_id].get("raw_state") or {}
        if restore_transforms is None:
            transform = _transform_from_raw(raw, TARGET_XY[instance_id])
        else:
            if instance_id not in restore_transforms:
                raise RuntimeError(f"Backup is missing instance: {instance_id}")
            transform = restore_transforms[instance_id]
        changes.append({
            "instance_id": instance_id,
            "expected_state_hash": runtime_edit_state_hash(raw),
            "transform": transform,
            "is_loaded": bool(raw.get("is_loaded", True)),
        })
    return changes


def _backup(project):
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"scc_w19_zone_layout_backup_{stamp}.json"
    payload = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_id": PROJECT_ID,
        "transforms": {
            instance_id: _transform_from_raw(
                (project["instances"][instance_id].get("raw_state") or {}))
            for instance_id in sorted(TARGET_XY)
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(dry_run=False, restore_path=None):
    store = ProjectStore()
    if store.get_active_id() != PROJECT_ID:
        raise RuntimeError(
            f"Active project must be {PROJECT_ID}, got {store.get_active_id()}"
        )
    project = store.get_active_copy()
    if not project:
        raise RuntimeError("Active project is unavailable")

    restore_transforms = None
    mode = "apply"
    if restore_path:
        backup = json.loads(Path(restore_path).read_text(encoding="utf-8"))
        if backup.get("project_id") != PROJECT_ID:
            raise RuntimeError("Backup belongs to another project")
        restore_transforms = backup.get("transforms") or {}
        mode = "restore"

    changes = _changes(project, restore_transforms)
    preview = {
        "mode": mode,
        "project_id": PROJECT_ID,
        "count": len(changes),
        "targets": [
            {
                "instance_id": change["instance_id"],
                "zone_id": project["instances"][change["instance_id"]].get("zone_id"),
                "from": _transform_from_raw(
                    project["instances"][change["instance_id"]].get("raw_state") or {}
                ),
                "to": change["transform"],
            }
            for change in changes
        ],
    }
    if dry_run:
        preview["dry_run"] = True
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    backup_path = _backup(project)
    ok, info, status = apply_batch_writeback(store, changes, max_changes=100)
    if not ok:
        raise RuntimeError(f"Batch writeback failed ({status}): {info}")

    preview.update({
        "status": "ok",
        "backup": str(backup_path),
        "updated_count": info["count"],
    })
    RESULT_PATH.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": "ok",
        "mode": mode,
        "updated_count": info["count"],
        "backup": str(backup_path),
        "result": str(RESULT_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", dest="restore_path")
    args = parser.parse_args()
    main(dry_run=args.dry_run, restore_path=args.restore_path)
