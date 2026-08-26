from scc_w18_semantic_mapping import (
    BUSINESS_CATEGORY,
    CONFIRMED_GROUPS,
    DATASET_ID,
    EQUIPMENT_ID,
    EQUIPMENT_LINKS,
    build_mapping_view,
    decorate_graph,
    ensure_equipment_semantics,
)


def _sample_graph():
    confirmed = [name for group in CONFIRMED_GROUPS for name in group["types"]]
    nodes = [
        {"id": "process", "name": "工序", "category": BUSINESS_CATEGORY},
        {"id": "station", "name": "工位", "category": BUSINESS_CATEGORY},
        {"id": "zone", "name": "区域", "category": BUSINESS_CATEGORY},
        {"id": "screen_plate", "name": "网板", "category": BUSINESS_CATEGORY},
        {"id": "alert", "name": "告警", "category": BUSINESS_CATEGORY},
        {"id": "operator", "name": "操作员", "category": BUSINESS_CATEGORY},
        {"id": "net_change", "name": "换网记录", "category": BUSINESS_CATEGORY},
    ]
    nodes.extend({"id": name, "name": name, "category": "一期生产设备"} for name in confirmed)
    nodes.extend(
        {"id": f"待审{i}", "name": f"待审{i}", "category": "一期生产设备"}
        for i in range(99)
    )
    return {"nodes": nodes, "links": [], "categories": [{"name": BUSINESS_CATEGORY}]}


def test_mapping_view_separates_confirmed_and_pending_cad_types():
    view = build_mapping_view(_sample_graph())
    assert view["confirmed_count"] == 36
    assert view["pending_count"] == 99
    assert view["cad_total"] == 135
    assert sum(group["count"] for group in view["groups"]) == 36
    assert view["scopes"] == [{
        "id": "w18_3f",
        "building": "W18",
        "floor": "3F",
        "label": "W18 三楼",
        "cad_total": 135,
        "confirmed_count": 36,
        "pending_count": 99,
    }]
    assert all(item["scope_id"] == "w18_3f" for group in view["groups"] for item in group["types"])


def test_mapping_view_discovers_future_floor_from_source_name():
    graph = _sample_graph()
    graph["nodes"].append({
        "id": "future_4f",
        "name": "四楼待判断设备",
        "category": "四楼生产设备",
        "source": "W18_4F_OntoTwin_clean.dxf",
    })
    view = build_mapping_view(graph)
    scopes = {item["id"]: item for item in view["scopes"]}
    assert scopes["w18_4f"]["label"] == "W18 四楼"
    assert scopes["w18_4f"]["pending_count"] == 1


def test_decorate_graph_only_enables_scc_w18():
    graph = _sample_graph()
    assert decorate_graph("another_dataset", graph) is graph
    decorated = decorate_graph(DATASET_ID, graph)
    assert decorated is not graph
    assert decorated["mapping_view"]["equipment_id"] == EQUIPMENT_ID


def test_equipment_semantics_migration_is_idempotent():
    dataset = {"graph_data": _sample_graph()}
    object_types = {}
    first = ensure_equipment_semantics(dataset, object_types)
    second = ensure_equipment_semantics(dataset, object_types)

    assert first["nodes_added"] == 1
    assert first["links_added"] == len(EQUIPMENT_LINKS)
    assert second["nodes_added"] == 0
    assert second["links_added"] == 0
    assert sum(node["id"] == EQUIPMENT_ID for node in dataset["graph_data"]["nodes"]) == 1
    assert sum(link["rid"] in {item["rid"] for item in EQUIPMENT_LINKS}
               for link in dataset["graph_data"]["links"]) == len(EQUIPMENT_LINKS)
    assert object_types[EQUIPMENT_ID]["name"] == "设备"
