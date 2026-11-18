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
