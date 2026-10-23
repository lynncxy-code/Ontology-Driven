"""Idempotently add/configure OntoTwin's representation host on the SCC Machine BP.

Run only after OntoTwinSync 4.4 has compiled and Unreal Editor is closed:
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<this file> -unattended -nop4 -nosplash -nullrhi
"""

import json

import unreal


BLUEPRINT_PATH = "/Game/SCC/Program/Function/Machine/BP_Item_base_SCC_Machine"
HOST_VARIABLE_NAME = "OntoTwinRepresentationHost"
TARGET_VARIABLE_NAME = "StaticMesh"
SLOT_NAME = "primary"


def _data_for_handle(handle):
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)


def _object_for_handle(handle, blueprint):
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(
        _data_for_handle(handle), blueprint
    )


def _variable_name(handle):
    return str(
        unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(
            _data_for_handle(handle)
        )
    )


def _find_host(handles, blueprint):
    for handle in handles:
        candidate = _object_for_handle(handle, blueprint)
        if isinstance(candidate, unreal.TwinRepresentationHostComponent):
            return handle, candidate
    return None, None


def _require_static_mesh_target(handles, blueprint):
    for handle in handles:
        candidate = _object_for_handle(handle, blueprint)
        if (
            isinstance(candidate, unreal.StaticMeshComponent)
            and _variable_name(handle) == TARGET_VARIABLE_NAME
        ):
            return candidate
    raise RuntimeError(
        f"{BLUEPRINT_PATH} 缺少名为 {TARGET_VARIABLE_NAME} 的 StaticMeshComponent"
    )


def _configure_host(host):
    host.set_editor_property("slot_name", unreal.Name(SLOT_NAME))
    host.set_editor_property(
        "target_component_name_fallback", unreal.Name(TARGET_VARIABLE_NAME)
    )

    # FComponentReference resolves a Blueprint component through its SCS variable name.
    component_reference = host.get_editor_property("target_static_mesh_component")
    component_reference.set_editor_property(
        "component_property", unreal.Name(TARGET_VARIABLE_NAME)
    )
    host.set_editor_property("target_static_mesh_component", component_reference)


def main():
    blueprint = unreal.EditorAssetLibrary.load_asset(BLUEPRINT_PATH)
    if not isinstance(blueprint, unreal.Blueprint):
        raise RuntimeError(f"无法加载 Actor Blueprint: {BLUEPRINT_PATH}")

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    if subsystem is None:
        raise RuntimeError("SubobjectDataSubsystem 不可用")

    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    if not handles:
        raise RuntimeError(f"无法读取 Blueprint 组件树: {BLUEPRINT_PATH}")
    _require_static_mesh_target(handles, blueprint)

    host_handle, host = _find_host(handles, blueprint)
    created = False
    if host is None:
        params = unreal.AddNewSubobjectParams(
            parent_handle=handles[0],
            new_class=unreal.TwinRepresentationHostComponent,
            blueprint_context=blueprint,
        )
        host_handle, fail_reason = subsystem.add_new_subobject(params=params)
        if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(host_handle):
            raise RuntimeError(f"添加 OntoTwin HostComponent 失败: {fail_reason}")
        if not subsystem.rename_subobject(
            host_handle, unreal.Text(HOST_VARIABLE_NAME)
        ):
            raise RuntimeError("已添加 HostComponent，但组件重命名失败")
        host = _object_for_handle(host_handle, blueprint)
        if not isinstance(host, unreal.TwinRepresentationHostComponent):
            raise RuntimeError("新建组件不是 TwinRepresentationHostComponent")
        created = True

    _configure_host(host)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    if not unreal.EditorAssetLibrary.save_loaded_asset(
        blueprint, only_if_is_dirty=False
    ):
        raise RuntimeError(f"保存 Blueprint 失败: {BLUEPRINT_PATH}")

    # Re-gather after compile/save so the result is also an executable verification.
    verified_handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    _, verified_host = _find_host(verified_handles, blueprint)
    _require_static_mesh_target(verified_handles, blueprint)
    if verified_host is None:
        raise RuntimeError("保存后未找到 OntoTwin HostComponent")
    if str(verified_host.get_editor_property("slot_name")) != SLOT_NAME:
        raise RuntimeError("保存后 HostComponent 槽位不是 primary")

    result = {
        "status": "ok",
        "blueprint": BLUEPRINT_PATH,
        "host_component": HOST_VARIABLE_NAME,
        "slot": SLOT_NAME,
        "target": TARGET_VARIABLE_NAME,
        "created": created,
    }
    unreal.log(f"ONTOTWIN_BP_CONTAINER_RESULT={json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
