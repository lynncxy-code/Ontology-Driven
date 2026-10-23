import copy

from part_transform_writeback import apply_part_transform_writeback


def _transform(rz=0):
    return {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": rz,
            "sx": 1, "sy": 1, "sz": 1}


def test_part_rotation_is_persisted_and_component_synced(store):
    config = {
        "assembly_signature": "sig-58",
        "render_parts": [{
            "asset_path": "/Game/Part.Part",
            "source_actor_guid": "actor-58",
            "source_component_name": "TwinRenderPart_0",
            "relative_transform": _transform(),
        }],
    }

    def seed(project):
        project["instances"]["part-58"] = {
            "id": "part-58", "component_id": "c58", "render_config": copy.deepcopy(config),
            "raw_state": {}, "object_type_rid": "x", "object_type_name": "组合展品",
        }
        project["components"]["c58"] = {"id": "c58", "render_config": copy.deepcopy(config)}

    store.transact_active(seed)
    ok, info, status = apply_part_transform_writeback(store, [{
        "instance_id": "part-58", "expected_assembly_signature": "sig-58", "parts": [{
            "part_index": 0, "asset_path": "/Game/Part.Part",
            "source_actor_guid": "actor-58", "source_component_name": "TwinRenderPart_0",
            "expected_transform": _transform(), "transform": _transform(90),
        }],
    }])

    assert ok and status == 200
    assert info["part_count"] == 1
    assert store.get_render_config("part-58")["render_parts"][0]["relative_transform"]["rz"] == 90
    assert store._current["components"]["c58"]["render_config"]["render_parts"][0]["relative_transform"]["rz"] == 90


def test_part_transform_conflict_is_rejected(store):
    config = {
        "assembly_signature": "sig-58",
        "render_parts": [{"asset_path": "/Game/Part.Part", "source_actor_guid": "a",
                           "source_component_name": "p", "relative_transform": _transform(15)}],
    }

    def seed(project):
        project["instances"]["part-58"] = {"id": "part-58", "render_config": config,
                                             "raw_state": {}, "object_type_rid": "x", "object_type_name": "x"}

    store.transact_active(seed)
    ok, info, status = apply_part_transform_writeback(store, [{
        "instance_id": "part-58", "expected_assembly_signature": "sig-58", "parts": [{
            "part_index": 0, "asset_path": "/Game/Part.Part", "source_actor_guid": "a",
            "source_component_name": "p", "expected_transform": _transform(),
            "transform": _transform(45),
        }],
    }])
    assert not ok and status == 409 and info["error"] == "transform_conflict"
