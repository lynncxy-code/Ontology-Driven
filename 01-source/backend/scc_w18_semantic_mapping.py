"""SCC W18 business-ontology to CAD-type mapping view.

The business ontology remains the stable graph backbone. CAD-derived types are
kept as a separate catalogue and are only projected into the graph when a user
selects a confirmed mapping.
"""

from __future__ import annotations

import copy
import re
from typing import Any


DATASET_ID = "ds_1786957368669"
BUSINESS_CATEGORY = "PCB业务对象"
EQUIPMENT_ID = "equipment"
EQUIPMENT_SEMANTIC_RID = "ri.obj.413a3b7d-7f54-5a38-8d0c-8538c8314c41"
LEGACY_EQUIPMENT_INTERFACE_RID = "ri.iface.02baa12b-3ae6-5b13-9fdf-a1b49fbc2ee5"
DEFAULT_SCOPE = {
    "id": "w18_3f",
    "building": "W18",
    "floor": "3F",
    "label": "W18 三楼",
    "source_batch": "W18_3F_OntoTwin_clean.dxf",
}

INTERFACE_RIDS = [
    "ri.iface.6df2b90b-4fce-59e1-85cf-1ae618adc04a",
    "ri.iface.b6853938-5de6-5b2d-a761-4f495d61ddda",
    "ri.iface.4c79e494-eae7-5fd5-8049-fe8ab1a5e6b4",
]

CONFIRMED_GROUPS = [
    {
        "id": "transport",
        "name": "搬运输送",
        "reason": "名称包含皮带线或出料输送特征",
        "types": ["3米 皮带线", "800皮带线", "冷包出料皮带", "加宽皮带线", "皮带4"],
    },
    {
        "id": "solder",
        "name": "阻焊 / 曝光",
        "reason": "名称包含阻焊、DI 或曝光工艺标识",
        "types": ["阻焊DI1", "阻焊DI2", "阻焊手动曝光机", "阻焊前处理", "阻焊前处理新", "网版曝光机"],
    },
    {
        "id": "develop",
        "name": "显影",
        "reason": "名称包含显影工序或配套烘箱特征",
        "types": ["显影1阻焊", "显影2阻焊", "显影烘箱", "网版显影机"],
    },
    {
        "id": "print",
        "name": "丝印 / 字符",
        "reason": "名称包含丝印、字符打印或字符烘烤标识",
        "types": ["丝印机连线", "手动丝印机新", "单机字符", "字符打印", "字符烘箱"],
    },
    {
        "id": "ink",
        "name": "网版 / 油墨",
        "reason": "名称包含网版或油墨存储处理特征",
        "types": ["网版架", "油墨库", "油墨震荡机", "涂布烘箱网版"],
    },
    {
        "id": "inspection",
        "name": "检验 / AOI",
        "reason": "名称包含 AVI、AOI、CCD 或检孔检测特征",
        "types": ["AVI新设备", "CCD检修站", "CCD铣床", "ccd复查机", "成检AVI", "翘曲检孔机", "背钻AOI新", "AOI喷砂收"],
    },
    {
        "id": "thermal",
        "name": "热处理 / 清洗",
        "reason": "名称包含固化、UV、喷砂或酸洗处理特征",
        "types": ["uv机", "后固化新", "喷砂酸洗", "阻焊后AVI喷砂"],
    },
]

EQUIPMENT_NODE = {
    "id": EQUIPMENT_ID,
    "rid": EQUIPMENT_ID,
    "semantic_rid": EQUIPMENT_SEMANTIC_RID,
    "api_name": "equipment",
    "name": "设备",
    "display_name": "设备",
    "category": BUSINESS_CATEGORY,
    "symbolSize": 46,
    "description": "生产设备。作为业务本体类型承接工序、工位、区域、网板、告警、操作员和换网记录；CAD 类型通过独立映射关联。",
    "lifecycle_status": "ACTIVE",
    "interfaces": INTERFACE_RIDS,
    "primary_keys": ["code"],
    "properties": [
        {"name": "id", "label": "ID", "type": "string", "semantic_rid": "ri.prop.d98674c1-1bd5-531d-b0be-03c7cc5a1378", "shared_property_rid": "ri.shprop.27e64435-fead-5093-91c2-72950dea1f1f"},
        {"name": "created_at", "label": "创建时间", "type": "datetime", "semantic_rid": "ri.prop.65dd9452-fedf-5044-8e02-56b29ed9268a", "shared_property_rid": "ri.shprop.7d04c13c-7a8a-5106-b7ba-ab3b21b5712b"},
        {"name": "code", "label": "设备编号", "type": "string", "semantic_rid": "ri.prop.79b9a817-648b-5e35-b46b-6a19268fbd4f", "shared_property_rid": "ri.shprop.b7d37e46-38ea-5419-b55b-830018430be8"},
        {"name": "name", "label": "设备名称", "type": "string", "semantic_rid": "ri.prop.b4b252cb-0c4e-5118-b052-e36b6409189d", "shared_property_rid": "ri.shprop.eb95d2ea-8738-5090-ab22-21a772f9de28"},
        {"name": "status", "label": "运行状态", "type": "string", "semantic_rid": "ri.prop.2b85b535-0f91-5c90-bff5-c4c65da525ff", "shared_property_rid": "ri.shprop.f13e331f-c275-5213-8492-2933baa942e8"},
        {"name": "oee", "label": "OEE", "type": "number", "semantic_rid": "ri.prop.27ecb927-97bc-59f3-9449-101e15953e50"},
    ],
}

EQUIPMENT_LINKS = [
    {"source": "station", "target": EQUIPMENT_ID, "label": "工位包含设备", "name": "工位包含设备", "api_name": "station_has_equipment", "rid": "ri.link.80efe74e-67e5-58b7-812f-a445fa34b19b", "semantic_rid": "ri.link.80efe74e-67e5-58b7-812f-a445fa34b19b", "cardinality": "ONE_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": "zone", "target": EQUIPMENT_ID, "label": "区域包含设备", "name": "区域包含设备", "api_name": "zone_contains_equipment", "rid": "ri.link.ca7de2f9-93c9-503f-a352-c18575dc7758", "semantic_rid": "ri.link.ca7de2f9-93c9-503f-a352-c18575dc7758", "cardinality": "ONE_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": "process", "target": EQUIPMENT_ID, "label": "工序使用设备", "name": "工序使用设备", "api_name": "process_uses_equipment", "rid": "ri.link.b5986874-6794-57fc-afee-3776c64170e7", "semantic_rid": "ri.link.b5986874-6794-57fc-afee-3776c64170e7", "cardinality": "MANY_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": EQUIPMENT_ID, "target": "screen_plate", "label": "设备适配网板", "name": "设备适配网板", "api_name": "equipment_accepts_screen_plate", "rid": "ri.link.b0ec91ab-2a84-5bec-ae40-a371fe43c412", "semantic_rid": "ri.link.b0ec91ab-2a84-5bec-ae40-a371fe43c412", "cardinality": "ONE_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": EQUIPMENT_ID, "target": "alert", "label": "设备产生告警", "name": "设备产生告警", "api_name": "equipment_has_alert", "rid": "ri.link.0ecf7674-bc8a-536d-87a6-ec699763fdda", "semantic_rid": "ri.link.0ecf7674-bc8a-536d-87a6-ec699763fdda", "cardinality": "ONE_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": "operator", "target": EQUIPMENT_ID, "label": "操作员负责设备", "name": "操作员负责设备", "api_name": "operator_handles_equipment", "rid": "ri.link.96a58a27-a578-5823-bc8f-3eadc2e516c5", "semantic_rid": "ri.link.96a58a27-a578-5823-bc8f-3eadc2e516c5", "cardinality": "MANY_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
    {"source": EQUIPMENT_ID, "target": "net_change", "label": "设备包含换网记录", "name": "设备包含换网记录", "api_name": "equipment_has_net_change", "rid": "ri.link.28366607-9b64-5d9f-a516-909f68ebd5f3", "semantic_rid": "ri.link.28366607-9b64-5d9f-a516-909f68ebd5f3", "cardinality": "ONE_TO_MANY", "lifecycle_status": "ACTIVE", "projection_scope": "object_to_object_only"},
]


def _pending_reason(name: str) -> str:
    if re.search(r"桌|衣柜|鞋柜|水盆", name):
        return "更可能是家具或设施，缺少生产设备语义"
    if re.search(r"弯头|球阀|三通|直通|异径|螺丝|支架", name):
        return "更可能是构件或部件，需要确认是否为独立资产"
    if re.fullmatch(r"[0-9\W_]+", name):
        return "名称只有数字或符号，无法判断业务类型"
    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return "缩写或编码缺少业务说明，需要人工核对"
    return "名称像设备，但缺少明确工艺证据或粒度需要确认"


def _node_name(node: dict[str, Any]) -> str:
    return str(node.get("name") or node.get("display_name") or node.get("id") or "").strip()


def _floor_label(floor: str) -> str:
    match = re.fullmatch(r"(\d+)F", floor.upper())
    if not match:
        return floor
    number = int(match.group(1))
    chinese = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}
    return f"{chinese.get(number, number)}楼"


def _node_scope(node: dict[str, Any]) -> dict[str, str]:
    source = str(node.get("source") or node.get("source_batch") or DEFAULT_SCOPE["source_batch"])
    nested_scope = node.get("scope") if isinstance(node.get("scope"), dict) else {}
    building = str(node.get("building") or nested_scope.get("building") or "").strip()
    floor = str(node.get("floor") or nested_scope.get("floor") or "").strip().upper()
    source_match = re.search(r"(?P<building>[A-Za-z]+\d+)[_\-\s]+(?P<floor>\d+F)", source, re.IGNORECASE)
    if source_match:
        building = building or source_match.group("building").upper()
        floor = floor or source_match.group("floor").upper()
    building = building or DEFAULT_SCOPE["building"]
    floor = floor or DEFAULT_SCOPE["floor"]
    return {
        "id": f"{building}_{floor}".lower(),
        "building": building,
        "floor": floor,
        "label": f"{building} {_floor_label(floor)}",
        "source_batch": source,
    }


def _mapping_item(node: dict[str, Any], name: str, reason: str) -> dict[str, Any]:
    scope = _node_scope(node)
    return {
        "id": node.get("id") or name,
        "name": name,
        "category": node.get("category") or "未分类",
        "reason": reason,
        "source": scope["source_batch"],
        "scope_id": scope["id"],
        "scope_label": scope["label"],
        "building": scope["building"],
        "floor": scope["floor"],
    }


def build_mapping_view(graph: dict[str, Any]) -> dict[str, Any]:
    """Build UI metadata from the project graph without changing stored nodes."""
    nodes = graph.get("nodes") or []
    nodes_by_name: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        name = _node_name(node)
        if name:
            nodes_by_name.setdefault(name, []).append(node)
    confirmed_names = [name for group in CONFIRMED_GROUPS for name in group["types"]]
    confirmed_node_ids: set[str] = set()
    for name in confirmed_names:
        for node in nodes_by_name.get(name, []):
            scope_id = _node_scope(node)["id"]
            if scope_id == DEFAULT_SCOPE["id"] or node.get("mapping_status") == "confirmed":
                confirmed_node_ids.add(str(node.get("id") or name))
    cad_nodes = [node for node in nodes if node.get("category") != BUSINESS_CATEGORY]
    pending = []
    for node in cad_nodes:
        name = _node_name(node)
        if not name or str(node.get("id") or name) in confirmed_node_ids:
            continue
        pending.append(_mapping_item(node, name, _pending_reason(name)))
    pending.sort(key=lambda item: item["name"].casefold())

    groups = []
    for group in CONFIRMED_GROUPS:
        types = []
        for name in group["types"]:
            for node in nodes_by_name.get(name, []):
                if str(node.get("id") or name) in confirmed_node_ids:
                    types.append(_mapping_item(node, name, group["reason"]))
        groups.append({**group, "types": types, "count": len(types)})

    confirmed_count = sum(group["count"] for group in groups)
    pending_keys = {(item["scope_id"], str(item["id"])) for item in pending}
    scope_index: dict[str, dict[str, Any]] = {}
    for item in [*pending, *(item for group in groups for item in group["types"])]:
        scope = scope_index.setdefault(item["scope_id"], {
            "id": item["scope_id"],
            "building": item["building"],
            "floor": item["floor"],
            "label": item["scope_label"],
            "cad_total": 0,
            "confirmed_count": 0,
            "pending_count": 0,
        })
        scope["cad_total"] += 1
        if (item["scope_id"], str(item["id"])) in pending_keys:
            scope["pending_count"] += 1
        else:
            scope["confirmed_count"] += 1
    scopes = sorted(scope_index.values(), key=lambda item: (item["building"], item["floor"]))
    return {
        "enabled": True,
        "dataset_id": DATASET_ID,
        "scope": {"building": "W18", "floor": "3F", "source_batch": "W18_3F_OntoTwin_clean.dxf"},
        "scopes": scopes,
        "business_category": BUSINESS_CATEGORY,
        "equipment_id": EQUIPMENT_ID,
        "confirmed_count": confirmed_count,
        "pending_count": len(pending),
        "cad_total": len(cad_nodes),
        "groups": groups,
        "pending": pending,
    }


def decorate_graph(dataset_id: str, graph: dict[str, Any]) -> dict[str, Any]:
    if dataset_id != DATASET_ID or not isinstance(graph, dict):
        return graph
    response = copy.deepcopy(graph)
    response["mapping_view"] = build_mapping_view(response)
    return response


def ensure_equipment_semantics(dataset: dict[str, Any], object_types: dict[str, Any]) -> dict[str, int]:
    """Idempotently restore Equipment and its seven business relations."""
    graph = dataset.setdefault("graph_data", {"nodes": [], "links": [], "categories": []})
    nodes = graph.setdefault("nodes", [])
    links = graph.setdefault("links", [])
    categories = graph.setdefault("categories", [])

    nodes_before = len(nodes)
    links_before = len(links)
    node_index = {str(node.get("id")): index for index, node in enumerate(nodes)}
    if EQUIPMENT_ID in node_index:
        nodes[node_index[EQUIPMENT_ID]] = copy.deepcopy(EQUIPMENT_NODE)
    else:
        nodes.append(copy.deepcopy(EQUIPMENT_NODE))

    link_rids = {str(link.get("rid")) for link in links}
    for link in EQUIPMENT_LINKS:
        if link["rid"] not in link_rids:
            links.append(copy.deepcopy(link))
            link_rids.add(link["rid"])

    category_names = {item.get("name") if isinstance(item, dict) else item for item in categories}
    if BUSINESS_CATEGORY not in category_names:
        categories.append({"name": BUSINESS_CATEGORY})

    object_types[EQUIPMENT_ID] = {
        "rid": EQUIPMENT_ID,
        "semantic_rid": EQUIPMENT_SEMANTIC_RID,
        "name": "设备",
        "category": BUSINESS_CATEGORY,
        "description": EQUIPMENT_NODE["description"],
        "color": "#1a1a1a",
        "properties": copy.deepcopy(EQUIPMENT_NODE["properties"]),
        "injected_interfaces": copy.deepcopy(INTERFACE_RIDS),
        "source": "business_ontology:scc_w18_pcb",
    }
    dataset["node_count"] = len(nodes)
    dataset["link_count"] = len(links)
    return {
        "nodes_added": len(nodes) - nodes_before,
        "links_added": len(links) - links_before,
        "node_count": len(nodes),
        "link_count": len(links),
    }
