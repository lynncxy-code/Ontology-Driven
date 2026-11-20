from uuid import uuid4

import pytest

from ue_project_binding import rebuild_index

URL = "/api/v2/runtime-editor/placements"
UE = "ACCEPT48_F10_LIBRARY"
HEADERS = {"X-OntoTwin-Project-Id": "p_test", "X-OntoTwin-UE-Project-Id": UE,
           "X-OntoTwin-UE-Scene-Id": "/Game/StandardScenes/Maps/Factory"}


@pytest.fixture
def placement(store):
    store.set_dataset({"bound_ue_project_id": UE})
    rebuild_index(store)
    return {"model": "models:AGV.glb", "label": "AGV.glb", "expected_project_id": "p_test",
            "position": {"x": -35, "y": 2.4, "z": 100}, "placement_id": str(uuid4())}


@pytest.mark.parametrize("key", ["models:AGV.glb", "/Game/StandardModels/Rack.Rack"])
def test_place_and_retry(client, store, placement, key):
    placement["model"] = key
    first = client.post(URL, headers=HEADERS, json=placement)
    assert first.status_code == 201, first.json
    iid = first.json["instance_id"]
    assert first.json["snapshot"]["objectTypeName"] == "场景陈设"
    interfaces = first.json["snapshot"]["interfaces"]
    assert interfaces["I3D_Representable"]["asset_id"] == key
    assert interfaces["I3D_Spatial"]["translation_x"] == -35
    repeat = client.post(URL, headers=HEADERS, json=placement)
    assert repeat.status_code == 200 and repeat.json["instance_id"] == iid
    placement["model"] = "models:other.glb"
    assert client.post(URL, headers=HEADERS, json=placement).status_code == 409
    persisted = store.read_project("p_test")
    assert list(persisted["instances"]) == [iid]
    assert not persisted["object_types"]["ontotwin.scene_object"].get("asset_id")


def test_legacy_scenery_name_in_catalog_instance_and_snapshot(client, store, placement):
    iid = client.post(URL, headers=HEADERS, json=placement).json["instance_id"]
    rid = "ontotwin.scene_object"

    def legacy_names(project):
        project["object_types"][rid]["name"] = "场景对象"
        instance = project["instances"][iid]
        instance.update(object_type_name="场景对象", hierarchy_path=["场景对象"], display_name="场景对象")
        instance["render_config"]["object_type_name"] = "场景对象"
        project["object_types"]["robot"] = {"rid": "robot", "name": "场景对象"}

    store.transact_project("p_test", legacy_names)
    catalog = client.get("/api/v2/ontology/types", headers=HEADERS).json
    names = {item["rid"]: item["name"] for item in catalog}
    assert names[rid] == "场景陈设" and names["robot"] == "场景对象"
    instance = client.get("/api/v2/instances", headers=HEADERS).json[0]
    assert instance["object_type_name"] == "场景陈设"
    assert instance["hierarchy_path"] == ["场景陈设"]
    assert instance["display_name"] == "场景对象"
    snapshot = client.get("/api/v2/state/snapshot", headers=HEADERS, query_string={"id": iid}).json
    assert snapshot["objectTypeName"] == "场景陈设" and snapshot["hierarchyPath"] == ["场景陈设"]


@pytest.mark.parametrize("patch", [{"model": "models:../x.glb"}, {"model": "models:D:/robot.glb"},
                                   {"position": {"x": 2}}, {"placement_id": "bad"}])
def test_invalid_never_creates_type_or_instance(client, store, placement, patch):
    response = client.post(URL, headers=HEADERS, json={**placement, **patch})
    assert response.status_code == 400
    assert "ontotwin.scene_object" not in store.read_project("p_test")["object_types"]
    assert not store.read_project("p_test")["instances"]


def test_binding_required(client, store, placement):
    for key in ["X-OntoTwin-UE-Scene-Id", "X-OntoTwin-UE-Project-Id"]:
        response = client.post(URL, headers={k: v for k, v in HEADERS.items() if k != key}, json=placement)
        assert response.status_code == 403
    assert client.post(URL, headers={**HEADERS, "X-OntoTwin-UE-Project-Id": "OTHER"}, json=placement).status_code == 403
    assert client.post(URL, headers=HEADERS, json={**placement, "expected_project_id": "other"}).status_code == 409
    assert not store.read_project("p_test")["instances"]


WEB = {"X-OntoTwin-Project-Id": "p_test", "X-OntoTwin-Session": "fixture-session"}


@pytest.fixture
def scenery_binding(client, store, placement):
    iid = client.post(URL, headers=HEADERS, json=placement).json["instance_id"]

    def seed(project):
        project["object_types"]["robot"] = {"rid": "robot", "name": "机器人",
                                            "injected_interfaces": ["I3D_Representable", "I3D_Spatial"]}
        project["instance_roster"] = [{"instance_id": "R-017", "type": "机器人", "name": "装配臂", "source": "import"}]
    store.transact_project("p_test", seed)
    return iid, f"/api/v2/instances/{iid}/business-number"


@pytest.mark.parametrize("mode,number", [("roster", "R-017"), ("new", "R-018")])
def test_browser_first_number(client, store, scenery_binding, mode, number):
    iid, endpoint = scenery_binding
    project = store.read_project("p_test")
    rec = project["instances"][iid]
    options = client.get(endpoint, headers=WEB).json
    assert options["types"] == [{"rid": "robot", "name": "机器人"}]
    assert [r["instance_id"] for r in options["roster"]] == ["R-017"]
    body = {"expected_project_id": "p_test", "instance_id": number, "mode": mode}
    if mode == "new":
        body["object_type_rid"] = "robot"
    assert client.post(endpoint, json=body, headers=WEB).json == {"instance_id": number}
    result = store.read_project("p_test")
    assert set(result["instances"]) == {number}
    bound = result["instances"][number]
    assert bound["object_type_rid"] == "robot" and bound["ext_guid"] == rec["ext_guid"]
    assert bound["raw_state"] == rec["raw_state"]
    assert bound["render_config"]["model_override"] == rec["render_config"]["model_override"]
    if mode == "roster":
        assert bound["display_name"] == "装配臂" and result["instance_roster"] == project["instance_roster"]
    else:
        assert bound["display_name"] == rec["display_name"]
        assert len([r for r in result["instance_roster"] if r["instance_id"] == number]) == 1
    assert client.post(endpoint, json=body, headers=WEB).status_code == 404
    assert client.post(endpoint.replace(iid, number), json=body, headers=WEB).status_code == 409


@pytest.mark.parametrize("case,code", [
    ("active", "already_placed"), ("trash", "in_trash"), ("component", "component_bound"),
    ("stale_roster", "roster_changed"), ("manual_roster", "on_roster"),
    ("invalid_type", "invalid_type"), ("project", "project_context_mismatch"),
])
def test_browser_binding_rejects_without_mutation(client, store, scenery_binding, placement, case, code):
    iid, endpoint = scenery_binding
    number = "R-019"
    body = {"expected_project_id": "p_test", "instance_id": number, "mode": "new", "object_type_rid": "robot"}
    if case in ("active", "trash"):
        response = client.post(URL, headers=HEADERS, json={**placement, "placement_id": str(uuid4()),
                               "instance_id": number, "object_type_rid": "robot"})
        assert response.status_code == 201
        if case == "trash":
            store.remove(number)
    elif case == "component":
        body["instance_id"] = "DW-001"
    elif case == "stale_roster":
        body["mode"] = "roster"
    elif case == "manual_roster":
        body["instance_id"] = "R-017"
    elif case == "invalid_type":
        body["object_type_rid"] = "ontotwin.scene_object"
    else:
        body["expected_project_id"] = "different"
    before = store.read_project("p_test")
    response = client.post(endpoint, headers=WEB, json=body)
    assert response.status_code in (400, 409) and response.json["error"] == code
    assert store.read_project("p_test") == before


def test_browser_binding_requires_session_and_edit_access(client, scenery_binding, monkeypatch):
    import app as backend
    _, endpoint = scenery_binding
    assert client.post(endpoint, headers=HEADERS, json={}).status_code == 401
    monkeypatch.setattr(backend, "legacy_project_role", lambda pid, minimum="view": "none" if minimum == "edit" else "viewer")
    assert client.get(endpoint, headers=WEB).status_code == 200
    assert client.post(endpoint, headers=WEB, json={}).status_code == 403


def test_scenery_names_trash_and_purge(client, store, placement):
    def place(**fields):
        response = client.post(URL, headers=HEADERS, json={**placement, "label": "货架",
                               "placement_id": str(uuid4()), **fields})
        assert response.status_code == 201, response.json
        iid = response.json["instance_id"]
        return iid, store.read_project("p_test")["instances"][iid]["display_name"]

    first, name = place()
    assert name == "货架 01"
    store.remove(first)
    second, name = place()
    assert name == "货架 02"
    store.remove(second)
    store.purge_trash()
    new_id, name = place()
    assert name == "货架 01" and new_id != first
    duplicate, name = place(display_name="货架 01")
    assert name == "货架 01" and duplicate != new_id
    assert not store.get_roster()


def test_business_placement_roster_retry_and_conflicts(client, store, placement):
    def setup(project):
        project["object_types"]["robot"] = {"rid": "robot", "name": "机器人",
                                            "injected_interfaces": ["I3D_Representable", "I3D_Spatial"]}
        project["instance_roster"] = [{"instance_id": "R-017", "type": "机器人", "name": "装配臂"}]
    store.transact_project("p_test", setup)
    data = {**placement, "instance_id": "R-017"}
    assert client.post(URL, headers=HEADERS, json=data).status_code == 201
    assert client.post(URL, headers=HEADERS, json=data).status_code == 200
    rec = store.read_project("p_test")["instances"]["R-017"]
    assert (rec["display_name"], rec["object_type_rid"]) == ("装配臂", "robot")
    other = {**data, "placement_id": str(uuid4())}
    assert client.post(URL, headers=HEADERS, json=other).json["error"] == "already_placed"
    store.remove("R-017")
    assert client.post(URL, headers=HEADERS, json=other).json["error"] == "in_trash"
    new = {**other, "instance_id": "R-018", "object_type_rid": "robot", "display_name": "二号臂"}
    assert client.post(URL, headers=HEADERS, json=new).status_code == 201
    assert [row["instance_id"] for row in store.get_roster()] == ["R-017", "R-018"]


def test_scene_delete_restore_and_identity(client, store, placement):
    iid = client.post(URL, headers=HEADERS, json=placement).json["instance_id"]
    def edit(action, **fields):
        return client.post("/api/v2/runtime-editor/objects/" + action, headers=HEADERS,
                           json={"expected_project_id":"p_test", "ids":[iid], **fields})
    assert edit("delete").status_code == 200
    assert iid not in store.read_project("p_test")["instances"]
    assert edit("delete").status_code == 200
    assert edit("restore").status_code == 200
    assert edit("restore").status_code == 200
    assert iid in store.read_project("p_test")["instances"]
    assert edit("identity", display_name="新名称").status_code == 200
    store.transact_project("p_test", lambda p:p["object_types"].update(
        robot={"rid":"robot", "name":"机器人", "injected_interfaces":["I3D_Representable","I3D_Spatial"]}))
    assert edit("identity", instance_id="R-020",object_type_rid="robot",display_name="新名称").status_code == 200
    project = store.read_project("p_test")
    assert list(project["instances"]) == ["R-020"]
    assert not store.list_trash()
    assert project["instance_roster"][0]["instance_id"] == "R-020"
    iid = "R-020"
    store.transact_project("p_test",lambda p:p["instances"][iid].update(zone_id="zone"))
    assert edit("identity",instance_id="R-021",display_name="新名称").json["error"] == "identifier_locked"
    assert edit("delete").json["error"] == "confirmation_required"
    assert edit("delete",confirm_business=True).status_code == 200
    assert edit("restore").status_code == 200
    assert store.read_project("p_test")["instances"][iid]["zone_id"] == "zone"


def test_placement_options_and_retry_after_id_change(client, store, placement):
    iid = client.post(URL,headers=HEADERS,json=placement).json["instance_id"]
    response = client.get("/api/v2/runtime-editor/placement-options",headers=HEADERS,
                          query_string={"expected_project_id":"p_test","selected_id":iid})
    assert response.status_code == 200 and response.json["identity"]["scenery"]
    retry = client.post(URL,headers=HEADERS,json={**placement,"instance_id":"another"})
    assert retry.status_code == 200 and retry.json["instance_id"] == iid
    assert len(store.read_project("p_test")["instances"]) == 1


@pytest.fixture(params=["configured", "heartbeat"])
def external_data_instance(request, client, store, placement, monkeypatch):
    import scene_interaction.service as runtime_service
    registry = runtime_service.RuntimeStatusRegistry()
    monkeypatch.setattr(runtime_service, "_RUNTIME_STATUS", registry)
    iid = "agv:agvfac000000001n01" if request.param == "configured" else "ACCEPT48_EXTERNAL_01"
    store.transact_project("p_test", lambda p: p["object_types"].update(
        robot={"rid": "robot", "name": "机器人", "injected_interfaces": ["I3D_Representable", "I3D_Spatial"]}))
    response = client.post(URL, headers=HEADERS, json={
        **placement, "instance_id": iid, "object_type_rid": "robot", "display_name": "外部数据设备"})
    assert response.status_code == 201, response.json
    if request.param == "heartbeat":
        registry.report("p_test", {"runtime_state": "available", "realtime_channel": {
            "enabled": True, "connection_state": "connected", "active_source": "websocket",
            "targets": [{"instance_id": iid, "state": "active", "applied": True}]}}, {})
    return iid


def test_external_data_locks_identity(client, store, external_data_instance):
    iid = external_data_instance
    options = client.get("/api/v2/runtime-editor/placement-options", headers=HEADERS,
                         query_string={"expected_project_id": "p_test", "selected_id": iid})
    assert options.json["identity"]["reasons"] == ["正在接收外部实时数据"]
    before = store.read_project("p_test")
    response = client.post("/api/v2/runtime-editor/objects/identity", headers=HEADERS,
                           json={"expected_project_id": "p_test", "ids": [iid], "instance_id": "ACCEPT48_RENAMED"})
    assert response.status_code == 409
    assert response.json["error"] == "identifier_locked"
    assert response.json["message"] == "正在接收外部实时数据"
    assert store.read_project("p_test") == before


def test_external_data_delete_confirmation_and_restore(client, store, external_data_instance):
    iid = external_data_instance
    body = {"expected_project_id": "p_test", "ids": [iid]}
    expected = ["外部实时数据（外部系统按此编号推送）。删除后外部推送将对不上。"]
    inspect = client.post("/api/v2/runtime-editor/objects/inspect", headers=HEADERS, json=body)
    assert inspect.json["objects"][0]["reasons"] == expected
    rejected = client.post("/api/v2/runtime-editor/objects/delete", headers=HEADERS, json=body)
    assert rejected.status_code == 409 and rejected.json["error"] == "confirmation_required"
    assert rejected.json["objects"][0]["reasons"] == expected
    assert iid in store.read_project("p_test")["instances"]
    deleted = client.post("/api/v2/runtime-editor/objects/delete", headers=HEADERS,
                          json={**body, "confirm_business": True})
    assert deleted.status_code == 200
    assert iid not in store.read_project("p_test")["instances"]
    assert any(row["instance_id"] == iid for row in store.get_roster())
    assert client.post("/api/v2/runtime-editor/objects/restore", headers=HEADERS, json=body).status_code == 200
    assert iid in store.read_project("p_test")["instances"]


def test_heartbeat_attachment_uses_bound_project_and_latest_report(client, store, placement, monkeypatch):
    import scene_interaction.service as runtime_service
    registry = runtime_service.RuntimeStatusRegistry()
    monkeypatch.setattr(runtime_service, "_RUNTIME_STATUS", registry)
    iid = client.post(URL, headers=HEADERS, json=placement).json["instance_id"]
    store.transact_project("p_test", lambda p: p.update(web_interactions={
        "draft": {"bindings": [{"scope": {"instance_id": iid}}]}}))
    heartbeat = {"runtime_state": "available", "realtime_channel": {
        "enabled": True, "connection_state": "connected", "active_source": "websocket",
        "targets": [{"instance_id": iid, "state": "active", "applied": True}]}}
    registry.report("other_project", heartbeat, {})
    query = {"expected_project_id": "p_test", "selected_id": iid}
    def reasons():
        return client.get("/api/v2/runtime-editor/placement-options", headers=HEADERS,
                          query_string=query).json["identity"]["reasons"]
    assert reasons() == []
    registry.report("p_test", heartbeat, {})
    assert reasons() == ["正在接收外部实时数据"]
    heartbeat["realtime_channel"]["targets"] = []
    registry.report("p_test", heartbeat, {})
    assert reasons() == []
    assert client.post("/api/v2/runtime-editor/objects/identity", headers=HEADERS,
                       json={"expected_project_id": "p_test", "ids": [iid], "display_name": "更名布景"}).status_code == 200


@pytest.fixture
def identity_instance(client, store, placement):
    store.transact_project("p_test", lambda p: p["object_types"].update(
        robot={"rid": "robot", "name": "机器人",
               "injected_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Overlay"]}))
    iid = "ACCEPT48_ID_OLD"
    response = client.post(URL, headers=HEADERS, json={
        **placement, "instance_id": iid, "object_type_rid": "robot", "display_name": "编号测试"})
    assert response.status_code == 201, response.json
    return iid


def rename_identity(client, iid, destination="ACCEPT48_ID_NEW", **fields):
    return client.post("/api/v2/runtime-editor/objects/identity", headers=HEADERS, json={
        "expected_project_id": "p_test", "ids": [iid], "instance_id": destination, **fields})


@pytest.mark.parametrize("version", ["draft", "published", "previous_published"])
def test_inherited_panel_and_derived_view_do_not_lock_id(client, store, identity_instance, version):
    from web_interaction.validators import business_view_members
    iid = identity_instance
    view = {"id": "automatic", "rule_groups": [{"object_type_rids": ["robot"]}]}
    def setup(project):
        project["web_interactions"] = {version: {"business_views": [view]}}
        project["object_types"]["robot"]["interface_overrides"] = {
            "I3D_Overlay": {"values": {"title": "继承面板"}}}
    store.transact_project("p_test", setup)
    options = client.get("/api/v2/runtime-editor/placement-options", headers=HEADERS,
                         query_string={"expected_project_id": "p_test", "selected_id": iid})
    assert options.json["identity"]["reasons"] == []
    assert iid in business_view_members(store.read_project("p_test"), view)
    before = store.read_project("p_test")["instances"][iid]
    response = rename_identity(client, iid)
    assert response.status_code == 200, response.json
    project = store.read_project("p_test")
    assert "ACCEPT48_ID_NEW" in business_view_members(project, view)
    rec = project["instances"]["ACCEPT48_ID_NEW"]
    assert rec["raw_state"] == before["raw_state"]
    assert rec["render_config"]["model_override"] == before["render_config"]["model_override"]
    assert project["web_interactions"][version]["business_views"] == [view]


@pytest.mark.parametrize("version", ["draft", "published", "previous_published"])
@pytest.mark.parametrize("reference", ["include", "exclude", "group_exclude"])
def test_explicit_view_references_still_lock_id(client, store, identity_instance, version, reference):
    iid = identity_instance
    # A non-matching type must not hide an explicit ID dependency.
    group = {"object_type_rids": ["non_matching_type"]}
    view = {"rule_groups": [group]}
    if reference == "include":
        group["instance_ids"] = [iid]
    elif reference == "group_exclude":
        group["exclude_instance_ids"] = [iid]
    else:
        view["exclude_instance_ids"] = [iid]
    store.transact_project("p_test", lambda p: p.update(
        web_interactions={version: {"business_views": [view]}}))
    before = store.read_project("p_test")
    response = rename_identity(client, iid)
    assert response.status_code == 409 and response.json["error"] == "identifier_locked"
    assert "业务视图" in response.json["message"]
    assert store.read_project("p_test") == before


@pytest.mark.parametrize("attachment,reason", [
    ("panel", "已配置信息面板"), ("zone", "已设置业务分区"), ("component", "已绑定构件")])
def test_instance_attachments_still_lock_id(client, store, identity_instance, attachment, reason):
    iid = identity_instance
    def setup(project):
        rec = project["instances"][iid]
        if attachment == "panel":
            rec["render_config"]["interface_overrides"] = {"I3D_Overlay": {"values": {"title": "实例面板"}}}
        elif attachment == "zone":
            rec["zone_id"] = "ACCEPT48_ZONE"
        else:
            project["components"]["ACCEPT48_COMPONENT"] = {"bound_instance_id": iid}
    store.transact_project("p_test", setup)
    before = store.read_project("p_test")
    response = rename_identity(client, iid)
    assert response.status_code == 409 and response.json["message"] == reason
    assert store.read_project("p_test") == before


@pytest.mark.parametrize("source", ["runtime_editor", "manual", "import", "legacy_unknown", None])
@pytest.mark.parametrize("existing_target", [False, True])
def test_rename_preserves_planned_and_unknown_roster_entries(client, store, identity_instance, source, existing_target):
    iid, destination = identity_instance, "ACCEPT48_ID_NEW"
    original = {"instance_id": iid, "type": "机器人", "name": "原计划名称", "note": "保留原清单资料"}
    if source is not None:
        original["source"] = source
    target = {"instance_id": destination, "type": "机器人", "name": "目标计划", "source": "manual"}
    unrelated = {"instance_id": "ACCEPT48_OTHER", "type": "机器人", "name": "其他计划"}
    store.transact_project("p_test", lambda p: p.update(
        instance_roster=[original, unrelated] + ([target] if existing_target else [])))
    response = rename_identity(client, iid, destination)
    assert response.status_code == 200, response.json
    project = store.read_project("p_test")
    assert iid not in project["instances"] and destination in project["instances"]
    rows = {row["instance_id"]: row for row in project["instance_roster"]}
    if source == "runtime_editor":
        assert iid not in rows
    else:
        assert rows[iid] == original
    assert rows[unrelated["instance_id"]] == unrelated
    if existing_target:
        assert rows[destination] == target
    assert len(project["instance_roster"]) == len(rows)
    options = client.get("/api/v2/runtime-editor/placement-options", headers=HEADERS,
                         query_string={"expected_project_id": "p_test", "model": "models:AGV.glb"})
    available = {row["instance_id"] for row in options.json["roster"]}
    assert (iid in available) == (source != "runtime_editor")
    assert destination not in available


@pytest.mark.parametrize("conflict", ["active", "trash"])
def test_failed_rename_preserves_original_roster(client, store, identity_instance, placement, conflict):
    iid, destination = identity_instance, "ACCEPT48_ID_TAKEN"
    other = client.post(URL, headers=HEADERS, json={**placement, "placement_id": str(uuid4()),
                        "instance_id": destination, "object_type_rid": "robot"})
    assert other.status_code == 201
    if conflict == "trash":
        store.remove(destination)
    before = store.read_project("p_test")
    response = rename_identity(client, iid, destination)
    assert response.status_code == 409
    assert response.json["error"] == ("already_placed" if conflict == "active" else "in_trash")
    assert store.read_project("p_test") == before
