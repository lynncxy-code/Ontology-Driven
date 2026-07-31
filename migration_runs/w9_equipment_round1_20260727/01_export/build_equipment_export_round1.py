import csv
import hashlib
import json
from pathlib import Path


ROUND_ROOT = Path(r"D:\tmp\digital_twin_aircraft\migration_runs\w9_equipment_round1_20260727")
INVENTORY_PATH = Path(r"D:\tmp\digital_twin_aircraft\migration_runs\w9_round1_20260727\00_input\w9_scene_inventory_round1.json")
EXPORT_PATH = ROUND_ROOT / "01_export" / "ue_actors_export_round1.json"
CLASSIFICATION_PATH = ROUND_ROOT / "02_classification" / "ue_migration_classification_round1.csv"

ZONE_ID = "scc_w19_1f_ict"
PROJECT_ID = "ds_1785130727581"
UE_PROJECT_ID = "ueproj_SCC_W19"
UE_PROJECT_NAME = "SCC W19"


GROUPS = [
    {
        "label": "1号自动上板机",
        "rid": "scc_w19.auto_board_loader_l460",
        "type_name": "自动上板机_L460-SF-AGV",
        "hierarchy_path": "生产区/1F/ICT产线/产线_01/工位_01_自动上板",
        "primary": "732C27F24870223EF5E79888CF2AF036",
        "guids": ["732C27F24870223EF5E79888CF2AF036", "9BA8337B4CFF28F57196278F6B63DAA9"],
    },
    {
        "label": "2号机器人上下料单元",
        "rid": "scc_w19.robot_loading_unit",
        "type_name": "机器人上下料单元_W9",
        "hierarchy_path": "生产区/1F/ICT产线/产线_01/工位_02_机器人上下料",
        "primary": "8A44A1B44541CF99A2FB50A991E7CE6D",
        "guids": [
            "B5634B3B4D1DAE18DC8F7F9AF958ABF1",
            "D969E94D4C056228440843B9FD4D316E",
            "8A44A1B44541CF99A2FB50A991E7CE6D",
            "17C6207140433F27A11BA5992C09DDAE",
        ],
    },
    {
        "label": "3号ICT测试机",
        "rid": "scc_w19.ict_tester_tr5001e",
        "type_name": "ICT测试机_TR5001E",
        "hierarchy_path": "生产区/1F/ICT产线/产线_01/工位_03_ICT测试",
        "primary": "77B91DE442A171746AD29EA1F0CA5996",
        "guids": [
            "77B91DE442A171746AD29EA1F0CA5996",
            "9BFB8E944BCC698CCEF25E8400740CB8",
            "4AA836DB4910047749779993062F748D",
            "DEAAC224417004C134508A9F5B4A5BDF",
        ],
    },
    {
        "label": "4号自动分板机",
        "rid": "scc_w19.online_board_separator_er7000",
        "type_name": "在线分板机_ER-7000",
        "hierarchy_path": "生产区/1F/ICT产线/产线_01/工位_04_自动分板",
        "primary": "3DE531C644FE4163C0FC2DAD8A55FE8E",
        "guids": ["F7BB0CB94EE9129CE3546FBABD024D0F", "3DE531C644FE4163C0FC2DAD8A55FE8E"],
    },
    {
        "label": "5号机器人下料单元",
        "rid": "scc_w19.robot_unloading_unit",
        "type_name": "机器人下料单元_W9",
        "hierarchy_path": "生产区/1F/ICT产线/产线_01/工位_05_机器人下料",
        "primary": "663D2B5D44900F9251654788DE02278B",
        "guids": [
            "22D90A4241F30B61007B45B51272A122",
            "663D2B5D44900F9251654788DE02278B",
            "F3EEFD5847AA6AF24EB9EEBF219C5514",
            "67626B70476E269C819C5389F5628369",
            "B3AE11CE4DFE2968419F27815497E8A8",
            "3C0139F040C469AAD36898933E995ED2",
        ],
    },
    {
        "label": "2号ICT整线装配",
        "rid": "scc_w19.ict_line_assembly_sm_cit",
        "type_name": "ICT整线装配_SM_CIT",
        "hierarchy_path": "生产区/1F/ICT产线/产线_02/整线装配",
        "primary": "55DD159A434DCEE2B91ACE83EE64F145",
        "guids": ["55DD159A434DCEE2B91ACE83EE64F145"],
        "include_direct_children": True,
    },
]


def guid_text(value):
    text = str(value or "").replace("-", "").upper()
    if len(text) != 32:
        raise ValueError(f"Invalid GUID: {value}")
    return f"{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def transform(actor):
    location = actor.get("location") or {}
    rotation = actor.get("rotation") or {}
    scale = actor.get("scale") or {}
    return {
        "tx": float(location.get("x", 0)),
        "ty": float(location.get("y", 0)),
        "tz": float(location.get("z", 0)),
        "rx": float(rotation.get("roll", 0)),
        "ry": float(rotation.get("pitch", 0)),
        "rz": float(rotation.get("yaw", 0)),
        "sx": float(scale.get("x", 1)),
        "sy": float(scale.get("y", 1)),
        "sz": float(scale.get("z", 1)),
    }


def relative_transform(actor, root):
    actor_tf = transform(actor)
    root_tf = transform(root)
    if any(abs(root_tf[key]) > 1e-4 for key in ("rx", "ry", "rz")):
        raise ValueError(f"Non-zero root rotation is not supported for {root['actor_label']}")
    return {
        "tx": actor_tf["tx"] - root_tf["tx"],
        "ty": actor_tf["ty"] - root_tf["ty"],
        "tz": actor_tf["tz"] - root_tf["tz"],
        "rx": actor_tf["rx"],
        "ry": actor_tf["ry"],
        "rz": actor_tf["rz"],
        "sx": actor_tf["sx"] / root_tf["sx"],
        "sy": actor_tf["sy"] / root_tf["sy"],
        "sz": actor_tf["sz"] / root_tf["sz"],
    }


def render_parts_for_actor(actor, root):
    parts = []
    for component in actor.get("components") or []:
        asset_path = component.get("static_mesh") or component.get("skeletal_mesh")
        if not asset_path:
            continue
        parts.append({
            "asset_path": asset_path,
            "source_actor_guid": guid_text(actor["actor_guid"]),
            "source_actor_label": actor.get("actor_label") or actor.get("actor_name"),
            "source_component_name": component.get("name") or "MeshComponent",
            "source_component_class": component.get("class_path") or "",
            "relative_transform": relative_transform(actor, root),
            "material_paths": [value for value in (component.get("materials") or []) if value],
            "visible": not bool(actor.get("hidden_in_game")),
            "hidden_in_game": bool(actor.get("hidden_in_game")),
            "cast_shadow": True,
            "collision_enabled": "QueryAndPhysics",
        })
    return parts


def build():
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    actors = inventory.get("actors") or []
    by_guid = {str(actor.get("actor_guid") or "").replace("-", "").upper(): actor for actor in actors}
    by_path = {actor.get("actor_path"): actor for actor in actors}
    export_actors = []
    classification_rows = []

    for group in GROUPS:
        primary = by_guid[group["primary"]]
        selected = [by_guid[value] for value in group["guids"]]
        if group.get("include_direct_children"):
            selected.extend(actor for actor in actors if actor.get("attach_parent_path") == primary.get("actor_path"))

        source_guids = [guid_text(actor["actor_guid"]) for actor in selected]
        parts = [part for actor in selected for part in render_parts_for_actor(actor, primary)]
        if not parts:
            raise ValueError(f"No render parts for {group['label']}")
        if any(min(part["relative_transform"][key] for key in ("sx", "sy", "sz")) < 0 for part in parts):
            raise ValueError(f"Negative scale found in {group['label']}")

        signature_input = [
            {"asset_path": part["asset_path"], "relative_transform": part["relative_transform"]}
            for part in parts
        ]
        signature = hashlib.md5(
            json.dumps(signature_input, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        static_assets = [part["asset_path"] for part in parts if "StaticMesh" in part["source_component_class"]]
        skeletal_assets = [part["asset_path"] for part in parts if "SkeletalMesh" in part["source_component_class"]]
        first_asset = parts[0]["asset_path"]
        source_records = []
        for actor in selected:
            parent = by_path.get(actor.get("attach_parent_path"))
            source_records.append({
                "guid": guid_text(actor["actor_guid"]),
                "actor_label": actor.get("actor_label"),
                "actor_name": actor.get("actor_name"),
                "folder_path": actor.get("folder_path") or "None",
                "parent_guid": guid_text(parent["actor_guid"]) if parent else "",
                "actor_class_path": actor.get("actor_class_path") or "",
                "has_mirrored_scale": bool(actor.get("has_negative_scale")),
            })

        export_actors.append({
            "ext_guid": guid_text(primary["actor_guid"]),
            "name": group["label"],
            "actor_label": group["label"],
            "actor_name": primary.get("actor_name"),
            "source_folder_path": "设备迁移/1F/ICT产线",
            "actor_class": "LogicalEquipmentAssembly",
            "actor_class_path": primary.get("actor_class_path") or "",
            "transform": transform(primary),
            "assembly_signature": signature,
            "source_actor_guids": source_guids,
            "source_actors": source_records,
            "render_parts": parts,
            "unsupported_components": [],
            "migration_warnings": [],
            "mesh_asset": first_asset,
            "static_mesh_asset": static_assets[0] if static_assets else "",
            "static_mesh_assets": static_assets,
            "skeletal_mesh_asset": skeletal_assets[0] if skeletal_assets else "",
            "skeletal_mesh_assets": skeletal_assets,
            "component_audit": {
                "source_actor_count": len(selected),
                "descendant_actor_count": max(0, len(selected) - 1),
                "render_part_count": len(parts),
                "unsupported_component_count": 0,
                "static_mesh_components": len(static_assets),
                "skeletal_mesh_components": len(skeletal_assets),
            },
        })
        classification_rows.append({
            "group_key": f"assembly_signature:{signature}",
            "count": 1,
            "sample_actor_labels": group["label"],
            "source_folder_path": "设备迁移/1F/ICT产线",
            "asset_path": first_asset,
            "actor_class_path": primary.get("actor_class_path") or "",
            "assembly_signature": signature,
            "render_part_count": len(parts),
            "total_render_part_count": len(parts),
            "source_actor_count": len(selected),
            "unsupported_component_count": 0,
            "unsupported_component_types": "",
            "risk_flags": "composite_assembly" + ("|skeletal_mesh" if skeletal_assets else ""),
            "suggested_object_type_rid": group["rid"],
            "suggested_object_type_name": group["type_name"],
            "hierarchy_path": group["hierarchy_path"],
            "classification_status": "confirmed",
            "action": "create_experimental",
            "notes": "Gate A/B approved by user; equipment only; zone_id=" + ZONE_ID,
        })

    payload = {
        "schema_version": "assembly_v1",
        "project_id": PROJECT_ID,
        "zone_id": ZONE_ID,
        "ue_project_id": UE_PROJECT_ID,
        "ue_project_name": UE_PROJECT_NAME,
        "source_map": "/Game/SCC_W9/Art/Maps/L_SCC_W9_Main",
        "actors": export_actors,
    }
    EXPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    fieldnames = list(classification_rows[0].keys())
    with CLASSIFICATION_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classification_rows)
    print(json.dumps({
        "export": str(EXPORT_PATH),
        "classification": str(CLASSIFICATION_PATH),
        "instance_count": len(export_actors),
        "render_part_count": sum(len(actor["render_parts"]) for actor in export_actors),
        "source_actor_guid_count": len({guid for actor in export_actors for guid in actor["source_actor_guids"]}),
    }, ensure_ascii=False))


if __name__ == "__main__":
    build()
