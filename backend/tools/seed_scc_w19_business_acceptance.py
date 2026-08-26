"""Seed a reversible SCC W19 ontology/zone/business acceptance scene.

This is a project-scoped fixture, not a generic demo generator. It adds:
- the five energy devices already authored in L_SCC_W9_Main;
- nine ArtStudio-backed logistics/production instances;
- one 1F floor containing only production, logistics, and energy areas;
- three cross-zone business views used by OntoTwin 3.8 acceptance.

Run inside the backend container so ProjectStore uses the PostgreSQL truth source:
    python -m tools.seed_scc_w19_business_acceptance
"""

import copy
import datetime as dt
import json
import argparse
import time

import artstudio_client
from project_store import ProjectStore, _default_raw_state, apply_instance_metadata
from web_interaction.validators import validate_config


PROJECT_ID = "ds_1785130727581"
BACKUP_PATH = "/app/tools/scc_w19_business_acceptance_backup.json"
RESULT_PATH = "/app/tools/scc_w19_business_acceptance_result.json"
UE_LEVEL = "/Game/SCC_W9/Art/Maps/L_SCC_W9_Main"
FIXTURE_PREFIX = "acceptance.scc_w19."


ZONES = {
    "scc_w19_building": {
        "name": "SCC W19 厂房",
        "level": "building",
        "parent_zone_id": None,
        "ue_level": UE_LEVEL,
        "streaming": {"building": "SCC W19"},
    },
    "scc_w19_1f": {
        "name": "1F",
        "level": "floor",
        "parent_zone_id": "scc_w19_building",
        "ue_level": UE_LEVEL,
        "streaming": {"floor": "1F"},
    },
    "scc_w19_1f_production": {
        "name": "生产区",
        "level": "area",
        "parent_zone_id": "scc_w19_1f",
        "ue_level": UE_LEVEL,
        "streaming": {"floor": "1F", "scope": "生产"},
    },
    "scc_w19_1f_logistics": {
        "name": "物流区",
        "level": "area",
        "parent_zone_id": "scc_w19_1f",
        "ue_level": UE_LEVEL,
        "streaming": {"floor": "1F", "scope": "物流"},
    },
    "scc_w19_1f_energy": {
        "name": "能源区",
        "level": "area",
        "parent_zone_id": "scc_w19_1f",
        "ue_level": UE_LEVEL,
        "streaming": {"floor": "1F", "scope": "能源"},
    },
}


TYPE_SPECS = {
    "scc_w19.energy.solar_array": {
        "name": "屋顶光伏阵列",
        "category": "能源设备",
        "description": "厂房分布式光伏发电单元。",
        "properties": [
            {"rid": "rated_power_kw", "name": "rated_power_kw", "label": "额定功率", "type": "FLOAT", "description": "额定发电功率，kW"},
            {"rid": "daily_generation_kwh", "name": "daily_generation_kwh", "label": "当日发电量", "type": "FLOAT", "description": "当日累计发电量，kWh"},
        ],
    },
    "scc_w19.energy.wind_turbine": {
        "name": "厂区风力发电机",
        "category": "能源设备",
        "description": "室外分布式风力发电设备。",
        "properties": [
            {"rid": "rated_power_kw", "name": "rated_power_kw", "label": "额定功率", "type": "FLOAT", "description": "额定发电功率，kW"},
            {"rid": "wind_speed_mps", "name": "wind_speed_mps", "label": "实时风速", "type": "FLOAT", "description": "实时风速，m/s"},
        ],
    },
    "scc_w19.energy.bess": {
        "name": "储能电池柜",
        "category": "能源设备",
        "description": "用于削峰填谷和应急保供的储能单元。",
        "properties": [
            {"rid": "capacity_kwh", "name": "capacity_kwh", "label": "额定容量", "type": "FLOAT", "description": "储能容量，kWh"},
            {"rid": "soc_percent", "name": "soc_percent", "label": "荷电状态", "type": "FLOAT", "description": "当前 SOC，%"},
        ],
    },
    "scc_w19.energy.diesel_generator": {
        "name": "柴油应急发电机",
        "category": "能源设备",
        "description": "市电失电时保障关键产线的备用发电设备。",
        "properties": [
            {"rid": "rated_power_kw", "name": "rated_power_kw", "label": "额定功率", "type": "FLOAT", "description": "额定输出功率，kW"},
            {"rid": "fuel_level_percent", "name": "fuel_level_percent", "label": "燃油液位", "type": "FLOAT", "description": "燃油余量，%"},
        ],
    },
    "scc_w19.energy.cooling_pump": {
        "name": "能源站循环油泵",
        "category": "能源设备",
        "description": "为能源站设备提供冷却油循环。",
        "properties": [
            {"rid": "flow_m3h", "name": "flow_m3h", "label": "实时流量", "type": "FLOAT", "description": "循环流量，m³/h"},
            {"rid": "outlet_pressure_mpa", "name": "outlet_pressure_mpa", "label": "出口压力", "type": "FLOAT", "description": "出口压力，MPa"},
        ],
    },
    "scc_w19.logistics.conveyor": {
        "name": "工业输送机",
        "category": "物流设备",
        "description": "跨工序输送物料的低模验收设备。",
        "properties": [{"rid": "throughput_pph", "name": "throughput_pph", "label": "输送节拍", "type": "FLOAT", "description": "件/小时"}],
        "artstudio_id": "340387089050767360",
    },
    "scc_w19.logistics.forklift": {
        "name": "工业叉车",
        "category": "物流设备",
        "description": "负责区域内托盘转运。",
        "properties": [{"rid": "load_capacity_kg", "name": "load_capacity_kg", "label": "额定载荷", "type": "FLOAT", "description": "kg"}],
        "artstudio_id": "340386428988952576",
    },
    "scc_w19.logistics.agv": {
        "name": "AGV 搬运车",
        "category": "物流设备",
        "description": "负责跨分区物料配送。",
        "properties": [{"rid": "battery_level", "name": "battery_level", "label": "电量", "type": "FLOAT", "description": "%"}],
        "artstudio_id": "337856526880346112",
    },
    "scc_w19.logistics.pallet": {
        "name": "智能物料托盘",
        "category": "物流设备",
        "description": "用于重点物料追踪的智能托盘。",
        "properties": [{"rid": "payload_kg", "name": "payload_kg", "label": "当前载荷", "type": "FLOAT", "description": "kg"}],
        "artstudio_id": "340387420023296000",
    },
    "scc_w19.logistics.container": {
        "name": "工业周转箱",
        "category": "物流设备",
        "description": "用于暂存待装配部件的工业周转箱。",
        "properties": [{"rid": "fill_percent", "name": "fill_percent", "label": "装载率", "type": "FLOAT", "description": "%"}],
        "artstudio_id": "340388069762928640",
    },
}


ENERGY_INSTANCES = [
    {
        "id": "ue_accept_energy_solar_01", "type": "scc_w19.energy.solar_array",
        "name": "屋顶光伏阵列 01", "zone": "scc_w19_1f_energy",
        "folder": "能源管理区/太阳能板", "source_asset": "/Game/SCC_W9/Art/EnergyManagement/solar_panel/solar_panel/StaticMeshes/solar_panel.solar_panel",
        "position": (7400.0, -7600.0, -412.741), "scale": (1.21011, 1.21011, 1.21011),
        "values": {"rated_power_kw": 120.0, "daily_generation_kwh": 486.2, "operating_mode": "grid_connected", "health_score": 96},
    },
    {
        "id": "ue_accept_energy_wind_01", "type": "scc_w19.energy.wind_turbine",
        "name": "厂区风力发电机 01", "zone": "scc_w19_1f_energy",
        "folder": "能源管理区/风力发电机", "source_asset": "/Game/SCC_W9/Art/EnergyManagement/wind_turbine/wind_turbine/StaticMeshes/windturbine_tall.windturbine_tall",
        "position": (7900.0, -7600.0, 20.0), "scale": (1.627126, 1.627126, 1.627126),
        "render_parts": [
            {"asset_path": "/Game/SCC_W9/Art/EnergyManagement/wind_turbine/wind_turbine/StaticMeshes/windturbine_tall.windturbine_tall", "relative_transform": {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1}},
            {"asset_path": "/Game/SCC_W9/Art/EnergyManagement/wind_turbine/wind_turbine/StaticMeshes/windturbine_tall_fan.windturbine_tall_fan", "relative_transform": {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1}},
        ],
        "values": {"rated_power_kw": 80.0, "wind_speed_mps": 6.8, "operating_mode": "automatic", "health_score": 91},
    },
    {
        "id": "ue_accept_energy_bess_01", "type": "scc_w19.energy.bess",
        "name": "储能电池柜 BESS-01", "zone": "scc_w19_1f_energy",
        "folder": "能源管理区/储能电池", "source_asset": "/Game/SCC_W9/Art/EnergyManagement/energy_battery/energy_battery/StaticMeshes/energy_battery.energy_battery",
        "position": (8400.0, -7600.0, 145.726), "scale": (0.69325, 0.69325, 0.69325),
        "values": {"capacity_kwh": 500.0, "soc_percent": 76.0, "operating_mode": "peak_shaving", "health_score": 94},
    },
    {
        "id": "ue_accept_energy_generator_01", "type": "scc_w19.energy.diesel_generator",
        "name": "柴油应急发电机 DG-01", "zone": "scc_w19_1f_energy",
        "folder": "能源管理区/应急发电机", "source_asset": "/Game/SCC_W9/Art/EnergyManagement/power_generator/power_generator/StaticMeshes/power_generator.power_generator",
        "position": (8900.0, -7600.0, 38.33), "scale": (1.578223, 1.578223, 1.578223),
        "values": {"rated_power_kw": 320.0, "fuel_level_percent": 82.0, "operating_mode": "standby", "health_score": 88},
    },
    {
        "id": "ue_accept_energy_pump_01", "type": "scc_w19.energy.cooling_pump",
        "name": "能源站循环油泵 P-01", "zone": "scc_w19_1f_energy",
        "folder": "能源管理区/石油抽油机", "source_asset": "/Game/SCC_W9/Art/EnergyManagement/oil_pump/oil_pump/StaticMeshes/Box001.Box001",
        "position": (9400.0, -7600.0, 20.684), "scale": (0.000008529567, 0.000008529567, 0.000008529567),
        "render_parts": [
            {"asset_path": f"/Game/SCC_W9/Art/EnergyManagement/oil_pump/oil_pump/StaticMeshes/{name}.{name}", "relative_transform": {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1}}
            for name in ([f"Box{index:03d}" for index in range(1, 12)] + [f"Cylinder{index:03d}" for index in range(1, 6)])
        ],
        "values": {"flow_m3h": 38.5, "outlet_pressure_mpa": 0.62, "operating_mode": "duty", "health_score": 79},
    },
]


TEST_INSTANCES = [
    ("ue_accept_smt_conveyor_01", "scc_w19.logistics.conveyor", "SMT 上料输送机 CV-01", "scc_w19_1f_production", (9900, -7600, 20), (1.0, 1.0, 1.0), {"throughput_pph": 820, "health_score": 93}),
    ("ue_accept_smt_agv_01", "scc_w19.logistics.agv", "SMT 配料 AGV-01", "scc_w19_1f_production", (10400, -7600, 20), (1.2, 1.2, 1.2), {"battery_level": 67, "speed": 1.1, "health_score": 86}),
    ("ue_accept_smt_pallet_01", "scc_w19.logistics.pallet", "SMT 锡膏物料托盘 PL-01", "scc_w19_1f_production", (10900, -7600, 20), (1.5, 1.5, 1.5), {"payload_kg": 180, "health_score": 98}),
    ("ue_accept_logistics_forklift_01", "scc_w19.logistics.forklift", "物流叉车 FL-01", "scc_w19_1f_logistics", (11400, -7600, 20), (1.3, 1.3, 1.3), {"load_capacity_kg": 2500, "health_score": 82}),
    ("ue_accept_logistics_agv_02", "scc_w19.logistics.agv", "跨区配送 AGV-02", "scc_w19_1f_logistics", (11900, -7600, 20), (1.2, 1.2, 1.2), {"battery_level": 42, "speed": 0.8, "health_score": 73}),
    ("ue_accept_logistics_container_01", "scc_w19.logistics.container", "待装配周转箱 CT-01", "scc_w19_1f_logistics", (12400, -7600, 20), (1.4, 1.4, 1.4), {"fill_percent": 64, "health_score": 95}),
    ("ue_accept_assembly_conveyor_02", "scc_w19.logistics.conveyor", "总装下线输送机 CV-02", "scc_w19_1f_production", (12900, -7600, 20), (1.0, 1.0, 1.0), {"throughput_pph": 520, "health_score": 89}),
    ("ue_accept_assembly_agv_03", "scc_w19.logistics.agv", "总装配送 AGV-03", "scc_w19_1f_production", (13400, -7600, 20), (1.2, 1.2, 1.2), {"battery_level": 88, "speed": 1.3, "health_score": 97}),
    ("ue_accept_unzoned_pallet_99", "scc_w19.logistics.pallet", "临时待定物料托盘 PL-99", "scc_w19_1f_logistics", (13800, -7600, 20), (1.5, 1.5, 1.5), {"payload_kg": 95, "health_score": 90}),
]


def stable_artstudio_id(asset_id):
    detail = artstudio_client.fetch_detail(asset_id)
    if not detail or not artstudio_client.pick_glb_file(detail):
        raise RuntimeError(f"ArtStudio asset is unavailable or has no GLB: {asset_id}")
    return artstudio_client.make_stable_id(asset_id, detail["version"])


def type_record(rid, spec):
    asset_id = spec.get("artstudio_id")
    stable_id = stable_artstudio_id(asset_id) if asset_id else ""
    return {
        "rid": rid,
        "name": spec["name"],
        "category": spec["category"],
        "description": spec["description"],
        "color": "#6f6f6f",
        "properties": copy.deepcopy(spec.get("properties") or []),
        "injected_interfaces": ["I3D_Representable", "I3D_Overlay", "I3D_Spatial"],
        "interface_configs": {},
        "asset_id": asset_id or None,
        "ue_asset_path": stable_id,
        "mock_instances": [],
        "source": "acceptance_fixture",
        "lifecycle_status": "EXPERIMENTAL",
        "graph_rid": rid,
        "classification_key": FIXTURE_PREFIX + rid,
    }


def raw_state(type_rid, type_name, position, scale, values, asset_path=""):
    raw = _default_raw_state(type_rid, type_name, {"x": position[0], "y": position[1], "z": position[2]})
    raw["scale_x"], raw["scale_y"], raw["scale_z"] = scale
    raw.update(values or {})
    if asset_path:
        raw["asset_id"] = asset_path
    return raw


def instance_record(instance_id, type_rid, display_name, zone_id, position, scale, values, object_types, source_asset="", render_parts=None, source_folder=""):
    now = time.time()
    type_name = object_types[type_rid]["name"]
    render_config = {
        "injected_interfaces": list(object_types[type_rid]["injected_interfaces"]),
        "asset_id": source_asset or object_types[type_rid].get("asset_id") or "",
        "ue_asset_path": source_asset or object_types[type_rid].get("ue_asset_path") or "",
        "object_type_name": type_name,
    }
    if render_parts:
        render_config["render_parts"] = copy.deepcopy(render_parts)
        render_config["assembly_signature"] = FIXTURE_PREFIX + instance_id
        render_config["source_actor_guids"] = []
    record = {
        "id": instance_id,
        "object_type_rid": type_rid,
        "object_type_name": type_name,
        "display_name": display_name,
        "hierarchy_path": ["SCC W19", ZONES[zone_id]["name"] if zone_id else "待分区", display_name],
        "source_folder_path": source_folder,
        "source_asset_path": source_asset or object_types[type_rid].get("ue_asset_path") or "",
        "classification_status": "confirmed",
        "classification_key": FIXTURE_PREFIX + type_rid,
        "source": "acceptance_fixture",
        "render_config": render_config,
        "created_at": now,
        "last_seen": now,
        "status": "online",
        "raw_state": raw_state(type_rid, type_name, position, scale, values, source_asset),
    }
    if zone_id:
        record["zone_id"] = zone_id
    apply_instance_metadata(record)
    record["raw_state"]["ui_label_content"] = display_name
    return record


def ensure_graph_nodes(project, object_types):
    dataset = project.get("dataset") or {}
    graph = dataset.setdefault("graph_data", {"nodes": [], "links": [], "categories": []})
    nodes = graph.setdefault("nodes", [])
    fixture_rids = set(TYPE_SPECS)
    nodes[:] = [node for node in nodes if node.get("rid") not in fixture_rids and node.get("id") not in fixture_rids]
    for rid in TYPE_SPECS:
        object_type = object_types[rid]
        nodes.append({
            "id": rid, "rid": rid, "name": object_type["name"],
            "display_name": object_type["name"], "category": object_type["category"],
            "description": object_type["description"],
            "injected_interfaces": object_type["injected_interfaces"],
            "color": object_type["color"], "properties": object_type["properties"],
            "lifecycle_status": object_type["lifecycle_status"],
        })
    categories = graph.setdefault("categories", [])
    existing = {item.get("name") for item in categories if isinstance(item, dict)}
    for name in ("能源设备", "物流设备"):
        if name not in existing:
            categories.append({"name": name})
    dataset["node_count"] = len(nodes)
    dataset["link_count"] = len(graph.get("links") or [])


def configure_web(project, all_instance_ids):
    web = project.setdefault("web_interactions", {})
    current_revision = int(web.get("revision") or 0)
    draft = copy.deepcopy(web.get("published") or web.get("draft") or {})
    pages = draft.setdefault("pages", [])
    views = draft.setdefault("business_views", [])
    bindings = draft.setdefault("bindings", [])

    energy_page = next((page for page in pages if page.get("page_id") == "page.energy-overview"), None)
    if energy_page:
        energy_page.setdefault("param_mapping", {})["business_view_id"] = "business_view_id"
        energy_page.setdefault("scope_effects", {})["business_view"] = "web_and_scene"
    building_page = next((page for page in pages if page.get("page_id") == "page.s3-building"), None)
    if building_page:
        building_page.setdefault("param_mapping", {})["business_view_id"] = "business_view_id"
        building_page.setdefault("scope_effects", {})["business_view"] = "web_and_scene"
    event_page = next((page for page in pages if page.get("page_id") == "page.event-workbench"), None)
    if event_page:
        event_page.setdefault("param_mapping", {})["business_view_id"] = "business_view_id"
        event_page.setdefault("scope_effects", {})["business_view"] = "web_and_scene"
    workstation = next((page for page in pages if page.get("page_id") == "page.s5-workstation"), None)
    if workstation:
        workstation.setdefault("scope_effects", {})["instance"] = "web_only"
    zone_page = next((page for page in pages if page.get("page_id") == "page.s4-zone"), None)
    if zone_page:
        zone_page.setdefault("scope_effects", {})["zone"] = "web_and_scene"

    managed_zone_bindings = {
        "bind.zone.ict", "bind.zone.production", "bind.zone.logistics", "bind.zone.energy",
    }
    bindings[:] = [item for item in bindings if item.get("binding_id") not in managed_zone_bindings]
    for suffix, zone_id, name in (
        ("production", "scc_w19_1f_production", "生产区总览"),
        ("logistics", "scc_w19_1f_logistics", "物流区总览"),
        ("energy", "scc_w19_1f_energy", "能源区总览"),
    ):
        bindings.append({
            "binding_id": f"bind.zone.{suffix}",
            "name": name,
            "enabled": True,
            "trigger": "zone_activated",
            "activation_mode": "explicit",
            "effect": "open_web",
            "page_id": "page.s4-zone",
            "scope": {"zone_id": zone_id},
        })

    business_specs = [
        {
            "business_view_id": "energy", "name": "能源管理",
            "description": "同一楼层能源区内的光伏、风电、储能、备用电源与循环泵。",
            "enabled": True,
            "rule_groups": [{"zone_ids": ["scc_w19_1f_energy"], "object_type_rids": [], "instance_ids": []}],
            "exclude_instance_ids": [],
        },
        {
            "business_view_id": "mobile_equipment_maintenance", "name": "移动设备运维",
            "description": "跨 SMT、物流和总装区域的 AGV 与叉车统一运维。",
            "enabled": True,
            "rule_groups": [{"zone_ids": [], "object_type_rids": ["scc_w19.logistics.agv", "scc_w19.logistics.forklift"], "instance_ids": []}],
            "exclude_instance_ids": [],
        },
        {
            "business_view_id": "critical_inspection", "name": "重点设备巡检",
            "description": "跨分区指定高风险设备，并演示排除检修中设备。",
            "enabled": True,
            "rule_groups": [{
                "zone_ids": [], "object_type_rids": [],
                "instance_ids": [
                    "ue_accept_energy_generator_01", "ue_accept_energy_pump_01",
                    "ue_accept_logistics_forklift_01", "ue_accept_logistics_agv_02",
                    "ue_77B91DE4-42A1-7174-6AD2-9EA1F0CA5996",
                ],
            }],
            "exclude_instance_ids": ["ue_accept_logistics_agv_02"],
        },
    ]
    managed_view_ids = {item["business_view_id"] for item in business_specs}
    views[:] = [item for item in views if item.get("business_view_id") not in managed_view_ids] + business_specs

    energy_binding = next((item for item in bindings if item.get("binding_id") == "bind.business.energy"), None)
    if not energy_binding:
        energy_binding = {"binding_id": "bind.business.energy"}
        bindings.append(energy_binding)
    energy_binding.update({
        "name": "能源管理总览", "enabled": True,
        "trigger": "business_view_activated", "activation_mode": "explicit",
        "effect": "open_web", "page_id": "page.energy-overview",
        "scope": {"business_view_id": "energy"},
    })

    mobile_binding = next((item for item in bindings if item.get("binding_id") == "bind.business.mobile-maintenance"), None)
    if not mobile_binding:
        mobile_binding = {"binding_id": "bind.business.mobile-maintenance"}
        bindings.append(mobile_binding)
    mobile_binding.update({
        "name": "移动设备运维总览", "enabled": True,
        "trigger": "business_view_activated", "activation_mode": "explicit",
        "effect": "open_web", "page_id": "page.s3-building",
        "scope": {"business_view_id": "mobile_equipment_maintenance"},
    })

    critical_binding = next((item for item in bindings if item.get("binding_id") == "bind.business.critical-inspection"), None)
    if not critical_binding:
        critical_binding = {"binding_id": "bind.business.critical-inspection"}
        bindings.append(critical_binding)
    critical_binding.update({
        "name": "重点设备巡检台账", "enabled": True,
        "trigger": "business_view_activated", "activation_mode": "explicit",
        "effect": "open_web", "page_id": "page.event-workbench",
        "scope": {"business_view_id": "critical_inspection"},
    })

    draft["base_revision"] = current_revision + 1
    draft.setdefault("web_policy", {"allowed_hosts": ["localhost"]})
    web["previous_published"] = copy.deepcopy(web.get("published"))
    published = copy.deepcopy(draft)
    published.pop("base_revision", None)
    web["published"] = published
    web["draft"] = draft
    web["revision"] = current_revision + 1
    web["schema_version"] = int(web.get("schema_version") or 1)


def main(dry_run=False):
    store = ProjectStore()
    if store.get_active_id() != PROJECT_ID:
        raise RuntimeError(f"Active project must be {PROJECT_ID}, got {store.get_active_id()}")
    project = store.get_active_copy()
    if not project:
        raise RuntimeError("Active project is unavailable")

    fixture_ids = {item["id"] for item in ENERGY_INSTANCES} | {item[0] for item in TEST_INSTANCES}
    existing_fixture_ids = [iid for iid in project.get("instances", {}) if iid.startswith("ue_accept_")]
    if existing_fixture_ids:
        raise RuntimeError("Acceptance fixture already exists: " + ", ".join(sorted(existing_fixture_ids)))

    backup = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_id": PROJECT_ID,
        "object_types": {rid: copy.deepcopy(project.get("object_types", {}).get(rid)) for rid in TYPE_SPECS},
        "zones": copy.deepcopy(project.get("zones") or {}),
        "web_interactions": copy.deepcopy(project.get("web_interactions") or {}),
        "instances": {iid: copy.deepcopy(project.get("instances", {}).get(iid)) for iid in fixture_ids},
    }
    object_types = project.setdefault("object_types", {})
    for rid, spec in TYPE_SPECS.items():
        object_types[rid] = type_record(rid, spec)
    ensure_graph_nodes(project, object_types)

    project["zones"] = copy.deepcopy(ZONES)
    # Keep the six original ICT devices and assign them to the shared production area.
    for record in (project.get("instances") or {}).values():
        if record.get("object_type_rid", "").startswith("scc_w19.") and not record.get("id", "").startswith("ue_accept_"):
            record["zone_id"] = "scc_w19_1f_production"

    instances = project.setdefault("instances", {})
    for spec in ENERGY_INSTANCES:
        instances[spec["id"]] = instance_record(
            spec["id"], spec["type"], spec["name"], spec["zone"],
            spec["position"], spec["scale"], spec["values"], object_types,
            source_asset=spec["source_asset"], render_parts=spec.get("render_parts"),
            source_folder=spec["folder"],
        )
    for instance_id, type_rid, name, zone_id, position, scale, values in TEST_INSTANCES:
        instances[instance_id] = instance_record(
            instance_id, type_rid, name, zone_id, position, scale, values,
            object_types,
        )

    configure_web(project, fixture_ids)
    validation = validate_config(project, project["web_interactions"]["published"])
    if not validation.get("valid"):
        raise RuntimeError("Web interaction validation failed: " + json.dumps(validation, ensure_ascii=False))

    result = {
        "project_id": PROJECT_ID,
        "zones": ZONES,
        "fixture_instance_ids": sorted(fixture_ids),
        "expected_counts": {
            "all": len(project["instances"]),
            "energy": 5,
            "mobile_equipment_maintenance": 4,
            "critical_inspection": 4,
            "unzoned": 0,
        },
        "artstudio_type_defaults": {
            rid: object_types[rid].get("ue_asset_path")
            for rid, spec in TYPE_SPECS.items() if spec.get("artstudio_id")
        },
        "web_validation": validation,
        "backup": BACKUP_PATH,
    }
    if dry_run:
        result["mode"] = "dry-run"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    with open(BACKUP_PATH, "w", encoding="utf-8") as handle:
        json.dump(backup, handle, ensure_ascii=False, indent=2, default=str)
    store.write_project(PROJECT_ID, project)
    with open(RESULT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
