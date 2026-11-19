"""OPT-03: the legacy I3D_Visual projection after the type page dropped its card."""


def _snapshot(interfaces, raw):
    import app as app_module

    project = {
        "object_types": {"T": {"rid": "T", "name": "设备", "injected_interfaces": interfaces}},
        "instances": {"one": {"object_type_rid": "T", "display_name": "A-01", "raw_state": raw}},
    }
    return app_module._build_snapshot("one", app_module._project_snapshot_context(project))


def test_model_type_gets_visibility_without_visual_capability(client):
    snap = _snapshot(["I3D_Representable"], {"is_visible": False})
    assert snap["interfaces"]["I3D_Visual"]["is_visible"] is False
    assert snap["interfaces"]["I3D_Visual"]["ui_label_content"] == ""


def test_old_test_material_is_no_longer_sent(client):
    snap = _snapshot(["I3D_Representable", "I3D_Visual"], {"material_variant": "gray"})
    assert snap["interfaces"]["I3D_Visual"]["material_variant"] == "normal"


def test_type_without_model_or_visual_still_gets_no_visual(client):
    snap = _snapshot(["I3D_Behavioral"], {})
    assert "I3D_Visual" not in snap["interfaces"]
