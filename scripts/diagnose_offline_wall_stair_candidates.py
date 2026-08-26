import json
import math
from pathlib import Path

import unreal


CHANGE_ROOT = Path(
    r"D:\ZHHZ\ZHHZ-Offline-Changes-20260821-113527"
    r"\ZHHZ-Offline-Changes-20260821-113527"
)
BACKUP_PROJECT = Path(
    r"D:\ZHHZ\Backups\OfflineMerge-20260821-113527\Database"
    r"\customer-edit-before-ds_1784694647848-20260821T043713Z.json"
)


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def map_package(path):
    value = str(path).replace("\\", "/")
    if value.lower().startswith("content/") and value.lower().endswith(".umap"):
        return "/Game/" + value[8:-5]
    return ""


def vector_dict(vector):
    return {
        "x": round(float(vector.x), 4),
        "y": round(float(vector.y), 4),
        "z": round(float(vector.z), 4),
    }


def distance(vector, transform):
    return math.sqrt(
        (float(vector.x) - float(transform.get("tx", 0.0))) ** 2
        + (float(vector.y) - float(transform.get("ty", 0.0))) ** 2
        + (float(vector.z) - float(transform.get("tz", 0.0))) ** 2
    )


def actor_assets(actor):
    values = []
    try:
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
    except Exception:
        components = []
    for component in components:
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        if mesh:
            values.append(mesh.get_path_name())
    return sorted(set(values))


def main():
    changes = load_json(CHANGE_ROOT / "customer-overrides.json")
    report = load_json(CHANGE_ROOT / "return-report.json")
    backup = load_json(BACKUP_PROJECT)

    targets = []
    for operation in changes.get("instance_operations") or []:
        if operation.get("op") not in {"delete", "replace"}:
            continue
        original = backup["instances"].get(operation.get("instance_id")) or {}
        old_render = original.get("render_config") or {}
        new_render = operation.get("render_config") or {}
        old_parts = old_render.get("render_parts") or []
        new_parts = new_render.get("render_parts") or []
        old_assets = sorted(
            set(
                str(part.get("asset_path") or "")
                for part in old_parts
                if part.get("asset_path")
            )
        )
        new_assets = sorted(
            set(
                str(part.get("asset_path") or "")
                for part in new_parts
                if part.get("asset_path")
            )
        )
        old_labels = sorted(
            set(
                str(part.get("source_actor_label") or "")
                for part in old_parts
                if part.get("source_actor_label")
            )
        )
        new_labels = sorted(
            set(
                str(part.get("source_actor_label") or "")
                for part in new_parts
                if part.get("source_actor_label")
            )
        )
        name = str(operation.get("display_name") or "")
        is_wall = name.startswith("GW")
        is_stair_change = any("LTypeStair" in value for value in new_assets + new_labels)
        if not (is_wall or is_stair_change):
            continue
        targets.append(
            {
                "instance_id": operation.get("instance_id"),
                "display_name": name,
                "operation": operation.get("op"),
                "old_transform": operation.get("expected_transform") or {},
                "new_transform": operation.get("transform") or {},
                "old_assets": old_assets,
                "new_assets": new_assets,
                "old_labels": old_labels,
                "new_labels": new_labels,
            }
        )

    maps = []
    for value in (report.get("changed_files") or []) + (report.get("added_files") or []):
        item = map_package(value)
        if item and item not in maps:
            maps.append(item)

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    result = {"target_count": len(targets), "maps": []}
    for item in maps:
        if not unreal.EditorLoadingAndSavingUtils.load_map(item):
            raise RuntimeError("Could not load " + item)
        actors = []
        for actor in subsystem.get_all_level_actors():
            try:
                location = actor.get_actor_location()
                label = actor.get_actor_label()
            except Exception:
                continue
            actors.append(
                {
                    "label": label,
                    "class": actor.get_class().get_path_name(),
                    "location_obj": location,
                    "location": vector_dict(location),
                    "assets": actor_assets(actor),
                }
            )

        map_result = {"map": item, "actor_count": len(actors), "targets": []}
        for target in targets:
            candidates = []
            old_assets = set(target["old_assets"])
            new_assets = set(target["new_assets"])
            old_labels = set(target["old_labels"])
            new_labels = set(target["new_labels"])
            for actor in actors:
                actor_asset_set = set(actor["assets"])
                old_distance = distance(actor["location_obj"], target["old_transform"])
                new_distance = distance(actor["location_obj"], target["new_transform"])
                old_asset_hit = bool(old_assets.intersection(actor_asset_set))
                new_asset_hit = bool(new_assets.intersection(actor_asset_set))
                old_label_hit = actor["label"] in old_labels
                new_label_hit = actor["label"] in new_labels
                near_old = old_distance <= 750.0
                near_new = new_distance <= 750.0
                if not (old_asset_hit or new_asset_hit or old_label_hit or new_label_hit or near_old or near_new):
                    continue
                candidates.append(
                    {
                        "label": actor["label"],
                        "class": actor["class"],
                        "location": actor["location"],
                        "old_distance_cm": round(old_distance, 3),
                        "new_distance_cm": round(new_distance, 3),
                        "old_asset_hit": old_asset_hit,
                        "new_asset_hit": new_asset_hit,
                        "old_label_hit": old_label_hit,
                        "new_label_hit": new_label_hit,
                        "assets": actor["assets"],
                    }
                )
            candidates.sort(
                key=lambda value: (
                    not value["old_asset_hit"],
                    not value["new_asset_hit"],
                    not value["old_label_hit"],
                    not value["new_label_hit"],
                    min(value["old_distance_cm"], value["new_distance_cm"]),
                )
            )
            asset_or_label = [
                value
                for value in candidates
                if value["old_asset_hit"]
                or value["new_asset_hit"]
                or value["old_label_hit"]
                or value["new_label_hit"]
            ]
            nearest = sorted(
                candidates,
                key=lambda value: min(value["old_distance_cm"], value["new_distance_cm"]),
            )[:20]
            selected = []
            seen = set()
            for value in asset_or_label + nearest:
                key = (value["label"], tuple(sorted(value["assets"])), tuple(value["location"].values()))
                if key in seen:
                    continue
                seen.add(key)
                selected.append(value)
                if len(selected) >= 80:
                    break
            map_result["targets"].append(
                {
                    **target,
                    "old_asset_hits": sum(value["old_asset_hit"] for value in candidates),
                    "new_asset_hits": sum(value["new_asset_hit"] for value in candidates),
                    "old_label_hits": sum(value["old_label_hit"] for value in candidates),
                    "new_label_hits": sum(value["new_label_hit"] for value in candidates),
                    "candidates": selected,
                }
            )
        result["maps"].append(map_result)
        unreal.log("OntoTwin wall/stair diagnostic {} actors={}".format(item, len(actors)))

    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "offline_wall_stair_candidates.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin wall/stair diagnostic wrote " + str(output))


if __name__ == "__main__":
    main()
