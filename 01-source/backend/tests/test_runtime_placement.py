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
