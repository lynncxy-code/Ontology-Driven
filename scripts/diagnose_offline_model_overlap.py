import json
import math
import re
from pathlib import Path

import unreal


CHANGE_FILE = Path(
    r"D:\ZHHZ\ZHHZ-Offline-Changes-20260821-113527"
    r"\ZHHZ-Offline-Changes-20260821-113527\customer-overrides.json"
)
LEVEL_PACKAGE = "/Game/AVIC_Show/Art/Maps/L_AS_Arch"


def norm_guid(value):
    if value is None:
        return ""
    if hasattr(value, "to_string"):
        value = value.to_string()
    text = str(value).upper()
    match = re.search(
        r"([0-9A-F]{8})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{12})",
        text,
    )
    if match:
        return "".join(match.groups())
    words = re.findall(r"(?<![0-9A-F])[0-9A-F]{8}(?![0-9A-F])", text)
    if len(words) >= 4:
        return "".join(words[-4:])
    return ""


def get_guid(actor):
    getter = getattr(actor, "get_actor_guid", None)
    if callable(getter):
        value = norm_guid(getter())
        if value:
            return value
    return ""


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


def vector(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False, True)
    low = [float(origin.x - extent.x), float(origin.y - extent.y), float(origin.z - extent.z)]
    high = [float(origin.x + extent.x), float(origin.y + extent.y), float(origin.z + extent.z)]
    return {
        "origin": vector(origin),
        "extent": vector(extent),
        "low": low,
        "high": high,
    }


def transformed_mesh_bounds(mesh, transform):
    local = mesh.get_bounding_box()
    xs = [float(local.min.x), float(local.max.x)]
    ys = [float(local.min.y), float(local.max.y)]
    zs = [float(local.min.z), float(local.max.z)]
    roll = math.radians(float(transform.get("rx", 0.0)))
    pitch = math.radians(float(transform.get("ry", 0.0)))
    yaw = math.radians(float(transform.get("rz", 0.0)))
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    sx = float(transform.get("sx", 1.0))
    sy_scale = float(transform.get("sy", 1.0))
    sz = float(transform.get("sz", 1.0))
    tx = float(transform.get("tx", 0.0))
    ty = float(transform.get("ty", 0.0))
    tz = float(transform.get("tz", 0.0))
    points = []
    for x in xs:
        for y in ys:
            for z in zs:
                x0, y0, z0 = x * sx, y * sy_scale, z * sz
                x1, y1, z1 = x0, y0 * cr - z0 * sr, y0 * sr + z0 * cr
                x2, y2, z2 = x1 * cp + z1 * sp, y1, -x1 * sp + z1 * cp
                x3, y3 = x2 * cy - y2 * sy, x2 * sy + y2 * cy
                points.append([x3 + tx, y3 + ty, z2 + tz])
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    origin = [(low[axis] + high[axis]) * 0.5 for axis in range(3)]
    extent = [(high[axis] - low[axis]) * 0.5 for axis in range(3)]
    return {
        "origin": [round(value, 4) for value in origin],
        "extent": [round(value, 4) for value in extent],
        "low": low,
        "high": high,
    }


def volume(item):
    return max(0.0, item["high"][0] - item["low"][0]) * max(
        0.0, item["high"][1] - item["low"][1]
    ) * max(0.0, item["high"][2] - item["low"][2])


def intersection(a, b):
    sizes = [
        max(0.0, min(a["high"][axis], b["high"][axis]) - max(a["low"][axis], b["low"][axis]))
        for axis in range(3)
    ]
    return sizes[0] * sizes[1] * sizes[2]


def aabb_gap(a, b):
    gaps = []
    for axis in range(3):
        if a["high"][axis] < b["low"][axis]:
            gaps.append(b["low"][axis] - a["high"][axis])
        elif b["high"][axis] < a["low"][axis]:
            gaps.append(a["low"][axis] - b["high"][axis])
        else:
            gaps.append(0.0)
    return math.sqrt(sum(value * value for value in gaps))


def transform_summary(actor):
    transform = actor.get_actor_transform()
    location = transform.translation
    rotation = transform.rotation.rotator()
    scale = transform.scale3d
    return {
        "tx": round(float(location.x), 4),
        "ty": round(float(location.y), 4),
        "tz": round(float(location.z), 4),
        "rx": round(float(rotation.roll), 4),
        "ry": round(float(rotation.pitch), 4),
        "rz": round(float(rotation.yaw), 4),
        "sx": round(float(scale.x), 6),
        "sy": round(float(scale.y), 6),
        "sz": round(float(scale.z), 6),
    }


def main():
    with CHANGE_FILE.open("r", encoding="utf-8-sig") as handle:
        changes = json.load(handle)
    targets = []
    for operation in changes.get("instance_operations") or []:
        render = operation.get("render_config") or {}
        asset_path = str(render.get("ue_asset_path") or render.get("asset_id") or "")
        is_wall = str(operation.get("display_name") or "").startswith("GW")
        is_stair = asset_path.endswith("/LTypeStair013.LTypeStair013")
        if operation.get("op") != "replace" or not (is_wall or is_stair):
            continue
        targets.append((operation, asset_path))

    if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
        raise RuntimeError("Could not load " + LEVEL_PACKAGE)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    current = []
    for actor in subsystem.get_all_level_actors():
        assets = actor_assets(actor)
        if not assets:
            continue
        try:
            current.append(
                {
                    "actor": actor,
                    "guid": get_guid(actor),
                    "label": actor.get_actor_label(),
                    "class": actor.get_class().get_path_name(),
                    "assets": assets,
                    "transform": transform_summary(actor),
                    "bounds": bounds(actor),
                }
            )
        except Exception as error:
            unreal.log_warning("Could not inspect overlap actor: {}".format(error))

    result = {"level": LEVEL_PACKAGE, "target_count": len(targets), "targets": []}
    for operation, asset_path in targets:
            mesh = unreal.load_asset(asset_path)
            if not mesh:
                raise RuntimeError("Could not load target mesh " + asset_path)
            transform = operation.get("transform") or {}
            probe_bounds = transformed_mesh_bounds(mesh, transform)
            probe_volume = volume(probe_bounds)
            candidates = []
            for item in current:
                item_bounds = item["bounds"]
                hit_volume = intersection(probe_bounds, item_bounds)
                item_volume = volume(item_bounds)
                gap = aabb_gap(probe_bounds, item_bounds)
                if gap > 250.0:
                    continue
                denominator = min(probe_volume, item_volume)
                overlap_ratio = hit_volume / denominator if denominator > 0.0001 else 0.0
                candidates.append(
                    {
                        "guid": item["guid"],
                        "label": item["label"],
                        "class": item["class"],
                        "assets": item["assets"],
                        "transform": item["transform"],
                        "bounds": item_bounds,
                        "aabb_gap_cm": round(gap, 4),
                        "intersection_volume": round(hit_volume, 4),
                        "overlap_of_smaller": round(overlap_ratio, 6),
                        "volume_ratio": round(
                            min(probe_volume, item_volume) / max(probe_volume, item_volume), 6
                        )
                        if max(probe_volume, item_volume) > 0.0001
                        else 0.0,
                    }
                )
            candidates.sort(
                key=lambda value: (
                    value["aabb_gap_cm"] > 0.0,
                    -value["overlap_of_smaller"],
                    -value["volume_ratio"],
                    value["aabb_gap_cm"],
                )
            )
            result["targets"].append(
                {
                    "instance_id": operation.get("instance_id"),
                    "display_name": operation.get("display_name"),
                    "asset_path": asset_path,
                    "transform": transform,
                    "probe_bounds": probe_bounds,
                    "probe_volume": probe_volume,
                    "candidate_count": len(candidates),
                    "candidates": candidates[:100],
                }
            )

    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "offline_model_overlap_diagnostic.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin overlap diagnostic wrote " + str(output))


if __name__ == "__main__":
    main()
