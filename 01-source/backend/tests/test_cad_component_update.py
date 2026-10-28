"""CAD reimport regressions; all data/files are isolated by the store fixture."""
import copy
import io

import pytest
from flask import Flask

from cad_component_update import CadUpdateError, save_cad_components
from coord_transform import apply_transform
from project_store import ProjectMismatch
from spatial_assets.api import register_spatial_asset_routes


def render(_):
    return {"ue_asset_path": "/Game/Tests/Pump"}


def item(x=100, equipment="pump-1"):
    return {"block_name": "PE16A", "cad_xy": [x, 200], "floor": 1,
            "rotation": 20, "attribs": {"EQUIP_ID": equipment} if equipment else {}}


@pytest.fixture
def cad(store):
    def seed(working):
        working["components"] = {}
        working["frames"] = [
            {"id": fid, "kind": "cad", "name": "同名图纸", "status": "published",
             "cad": {"original_name": "hall.dxf"}, "draft_revision": 0,
             "to_ue": {"matrix": [[0.1, 0, 10], [0, 0.1, 20], [0, 0, 1]]}}
            for fid in ("frame.cad.a", "frame.cad.b")]
    store.transact_active(seed)
    return store


def payload(**patch):
    return {"mode": "dxf", "frame_id": "frame.cad.a", "expected_project_id": "p_test",
            "source_label": "hall.dxf", "transform_matrix": [[1, 0, 0], [0, 1, 0]],
            "items": [item()], **patch}


def preview(store, data):
    return save_cad_components(store, {**data, "dry_run": True}, render)


def apply(store, data):
    review = preview(store, data)
    return save_cad_components(store, {**data, "preview_token": review["preview_token"]}, render)


def bound(store):
    apply(store, payload())
    cid = next(iter(store.get_components()))
    store.bind(cid, "P-001")
    store.mint_instances()
    store.update_raw_state("P-001", {"translation_x": 777, "translation_y": 888,
                                   "translation_z": 90, "rotation_z": 35, "custom": 42}, persist=True)
    return cid


def test_same_filename_and_geometry_are_isolated_by_frame(cad):
    apply(cad, payload())
    first = copy.deepcopy(cad.get_components())
    apply(cad, payload(frame_id="frame.cad.b"))
    assert len(cad.get_components()) == 2
    for cid, comp in first.items():
        assert cad.get_components()[cid] == comp
    apply(cad, payload())
    assert len(cad.get_components()) == 2


def test_moved_equipment_keeps_id_binding_pose_and_canonical_truth(cad):
    cid = bound(cad)
    before = cad.get_active_copy(with_render_parts=True)["instances"]
    data = payload(items=[item(3000)])
    review = preview(cad, data)
    assert review["rows"][0]["matched_by"] == "equipment_id"
    assert review["summary"]["position_changes"] == 1
    apply(cad, data)
    comp = cad.get_components()[cid]
    assert comp["bound_instance_id"] == "P-001"
    assert comp["source_xy"] == [3000, 200]
    assert comp["ue_xy"] == [777, 888]
    assert apply_transform(comp["to_ue_matrix"], comp["canonical_xy"]) == [777, 888]
    assert comp["canonical_z"] == 900
    assert cad.get_active_copy(with_render_parts=True)["instances"] == before
    assert apply(cad, data)["summary"]["matched"] == 1


def test_explicit_pose_update_preserves_other_instance_fields(cad):
    cid = bound(cad)
    apply(cad, payload(items=[item(3000)], apply_position_ids=[cid]))
    raw = cad.get_active_copy()["instances"]["P-001"]["raw_state"]
    assert [raw[k] for k in ("translation_x", "translation_y", "translation_z", "rotation_z")] == [310, 40, 90, 20]
    assert raw["custom"] == 42
    assert cad.get_components()[cid]["ue_xy"] == [310, 40]


def test_angle_wrap_and_same_floor_height_are_not_pose_changes(cad):
    bound(cad)
    cad.update_raw_state("P-001", {"translation_x": 20, "translation_y": 40,
                                  "translation_z": 90, "rotation_z": 380}, persist=True)
    assert preview(cad, payload())["summary"]["position_changes"] == 0


def test_float_noise_preserves_geometry_match(cad):
    apply(cad, payload(items=[item(equipment="")]))
    result = preview(cad, payload(items=[item(100 + 1e-9, "")]))
    assert result["rows"][0]["matched_by"] == "same_geometry"


def test_invalid_match_value_is_validation_error(cad):
    with pytest.raises(CadUpdateError) as caught:
        preview(cad, payload(matches={"0": []}))
    assert caught.value.code == "invalid_matches"


def test_missing_filtered_and_other_sources_are_retained(cad):
    apply(cad, payload(items=[item(), item(1000, "pump-2")]))
    apply(cad, payload(frame_id="frame.cad.b"))
    old = copy.deepcopy(cad.get_components())
    review = preview(cad, payload(items=[]))
    assert review["summary"]["retained_missing"] == 2
    apply(cad, payload(items=[]))
    assert cad.get_components() == old


def test_moved_without_identity_requires_manual_match_no_proximity(cad):
    apply(cad, payload(items=[item(equipment="")]))
    cid = next(iter(cad.get_components()))
    data = payload(items=[item(100.001, "")])
    review = preview(cad, data)
    assert review["unresolved"] == [0]
    before = cad.get_active_copy(with_render_parts=True)
    with pytest.raises(CadUpdateError, match="对应关系"):
        apply(cad, data)
    assert cad.get_active_copy(with_render_parts=True) == before
    apply(cad, {**data, "matches": {"0": cid}})
    assert list(cad.get_components()) == [cid]


def test_duplicate_geometry_requires_explicit_new_and_stays_ambiguous(cad):
    data = payload(items=[item(equipment=""), item(equipment="")])
    assert preview(cad, data)["unresolved"] == [0, 1]
    apply(cad, {**data, "matches": {"0": "new", "1": "new"}})
    assert len(cad.get_components()) == 2
    assert preview(cad, data)["unresolved"] == [0, 1]


def test_explicit_new_at_existing_geometry_does_not_overwrite(cad):
    apply(cad, payload())
    original = copy.deepcopy(cad.get_components())
    apply(cad, payload(matches={"0": "new"}))
    assert len(cad.get_components()) == 2
    for cid, comp in original.items():
        assert cad.get_components()[cid] == comp


def test_manual_matches_reject_cross_frame_and_duplicate_targets(cad):
    apply(cad, payload())
    cid = next(iter(cad.get_components()))
    with pytest.raises(CadUpdateError, match="不在本底图"):
        preview(cad, payload(frame_id="frame.cad.b", matches={"0": cid}))
    with pytest.raises(CadUpdateError, match="重复选择"):
        preview(cad, payload(items=[item(), item(900, "other")], matches={"0": cid, "1": cid}))


@pytest.mark.parametrize("change", ["pose", "binding", "frame", "project"])
def test_stale_preview_never_overwrites_newer_state(cad, change):
    cid = bound(cad)
    data = payload(items=[item(2000)])
    review = preview(cad, data)
    if change == "pose":
        cad.update_raw_state("P-001", {"translation_x": 999}, persist=True)
    elif change == "binding":
        cad.bind(cid, "P-002")
    elif change == "frame":
        cad.transact_active(lambda w: w["frames"][0].update(draft_revision=1))
    else:
        cad.create_project("其他项目", project_id="other")
    before = cad.get_active_copy(with_render_parts=True)
    with pytest.raises((CadUpdateError, ProjectMismatch)):
        save_cad_components(cad, {**data, "preview_token": review["preview_token"]}, render)
    assert cad.get_active_copy(with_render_parts=True) == before


def test_preview_cancel_and_validation_are_read_only(cad, monkeypatch):
    bound(cad)
    before = cad.get_active_copy(with_render_parts=True)
    monkeypatch.setattr(cad, "_save_current", lambda: pytest.fail("preview must not save"))
    preview(cad, payload(items=[item(2000)]))
    with pytest.raises(CadUpdateError):
        apply(cad, payload(items=[item(), {**item(), "cad_xy": [float("nan"), 0]}]))
    assert cad.get_active_copy(with_render_parts=True) == before


def test_disk_failure_rolls_back_component_and_instance_together(cad, monkeypatch):
    cid = bound(cad)
    before = cad.get_active_copy(with_render_parts=True)
    def fail():
        raise OSError("disk unavailable")
    monkeypatch.setattr(cad, "_save_current", fail)
    with pytest.raises(OSError):
        apply(cad, payload(items=[item(5000)], apply_position_ids=[cid]))
    assert cad.get_active_copy(with_render_parts=True) == before


def test_http_preview_guard_and_success(client, store):
    data = payload(frame_id=None)
    store.set_components({})
    review = client.post("/api/v2/coord/save_components", json={**data, "dry_run": True})
    assert review.status_code == 200
    assert not store.get_components()
    result = client.post("/api/v2/coord/save_components", json={
        **data, "preview_token": review.json["preview_token"]})
    assert result.status_code == 200, result.json
    stale = client.post("/api/v2/coord/save_components", json={
        **data, "preview_token": review.json["preview_token"]})
    assert stale.status_code == 409
    assert stale.json["error"] == "preview_stale"


def test_replace_source_keeps_frame_bindings_and_requires_republish(cad, tmp_path):
    bound(cad)
    app = Flask(__name__)
    register_spatial_asset_routes(app, cad, str(tmp_path))
    client = app.test_client()
    def upload(**patch):
        return client.post("/api/v2/spatial-frames/cad-assets", data={
            "file": (io.BytesIO(b"0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n"), "new.dxf"),
            "expected_project_id": "p_test", "update_frame_id": "frame.cad.a",
            "expected_draft_revision": "0", **patch})
    before = cad.get_active_copy(with_render_parts=True)
    result = upload()
    assert result.status_code == 201, result.json
    frame = result.json["frame"]
    assert frame["id"] == "frame.cad.a"
    assert frame["draft_revision"] == 1
    assert frame["status"] == "draft"
    after = cad.get_active_copy(with_render_parts=True)
    assert after["components"] == before["components"]
    assert after["instances"] == before["instances"]
    assert after["frames"][1] == before["frames"][1]
    assert upload().status_code == 409
    assert upload(expected_project_id="other").status_code == 409
    with pytest.raises(CadUpdateError, match="发布"):
        preview(cad, payload())


def test_upload_replace_publish_then_reimport_keeps_original_identity(cad, tmp_path):
    app = Flask(__name__)
    register_spatial_asset_routes(app, cad, str(tmp_path))
    client = app.test_client()
    def upload(**patch):
        response = client.post("/api/v2/spatial-frames/cad-assets", data={
            "file": (io.BytesIO(b"0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n"), "hall.dxf"),
            "expected_project_id": "p_test", **patch})
        assert response.status_code == 201, response.json
        return response.json["frame"]
    frame = upload()
    fid = frame["id"]
    draft = client.put(f"/api/v2/spatial-frames/{fid}/draft", json={
        "expected_project_id": "p_test", "expected_draft_revision": 0,
        "floor": 1, "floor_id": "floor-1", "canonical_origin": [100, 200],
        "anchors": [
            {"id": "a", "source_xy_mm": [0, 0], "ue_world_cm": [0, 0]},
            {"id": "b", "source_xy_mm": [1000, 0], "ue_world_cm": [100, 0]},
            {"id": "c", "source_xy_mm": [0, 1000], "ue_world_cm": [0, 100]},
        ]})
    assert draft.status_code == 200, draft.json
    def publish(revision):
        response = client.post(f"/api/v2/spatial-frames/{fid}/publish", json={
            "expected_project_id": "p_test", "expected_draft_revision": revision})
        assert response.status_code == 200, response.json
    publish(1)
    data = payload(frame_id=fid)
    apply(cad, data)
    cid = next(iter(cad.get_components()))
    cad.bind(cid, "P-001")
    cad.mint_instances()
    cad.update_raw_state("P-001", {"translation_x": 999}, persist=True)
    before = cad.get_active_copy(with_render_parts=True)
    replacement = upload(update_frame_id=fid, expected_draft_revision="1")
    assert replacement["anchors"] == draft.json["frame"]["anchors"]
    assert len(cad.get_active_copy()["frames"]) == len(before["frames"])
    publish(2)
    assert cad.get_active_copy(with_render_parts=True)["instances"] == before["instances"]
    apply(cad, {**data, "items": [item(5000)]})
    assert next(iter(cad.get_components())) == cid
    assert cad.get_components()[cid]["bound_instance_id"] == "P-001"
    assert cad.get_active_copy()["instances"]["P-001"]["raw_state"]["translation_x"] == 999


def test_rotation_is_transformed_with_matrix_yaw(cad):
    """BUG-07：构件朝向随标定矩阵的线性部分换算为 UE Yaw（20° + 90° 旋转 = 110°）。"""
    cad.transact_active(lambda w: w["frames"][0].update(
        {"to_ue": {"matrix": [[0, -1, 10], [1, 0, 20], [0, 0, 1]]}}))
    apply(cad, payload())
    comp = next(iter(cad.get_components().values()))
    assert round(comp["rotation"], 1) == 110.0


def test_identity_matrix_preserves_rotation(cad):
    """BUG-07：无旋转/镜像的矩阵下朝向保持不变。"""
    apply(cad, payload())
    comp = next(iter(cad.get_components().values()))
    assert comp["rotation"] == 20.0


def test_frame_components_endpoint_echoes_saved_components(cad, tmp_path):
    """BUG-09：/components 接口按 frame_id 回显已保存构件。"""
    app = Flask(__name__)
    register_spatial_asset_routes(app, cad, str(tmp_path))
    client = app.test_client()
    apply(cad, payload())
    resp = client.get("/api/v2/spatial-frames/frame.cad.a/components")
    assert resp.status_code == 200
    assert resp.json["frame_id"] == "frame.cad.a"
    assert len(resp.json["components"]) == 1
    assert resp.json["components"][0]["object_type_rid"] == "PE16A"
    assert resp.json["components"][0]["source_mode"] == "dxf"
