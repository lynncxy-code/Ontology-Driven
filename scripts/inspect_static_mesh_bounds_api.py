import json
from pathlib import Path

import unreal


def main():
    asset_path = (
        "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/"
        "Shape1622259920.Shape1622259920"
    )
    mesh = unreal.load_asset(asset_path)
    if not mesh:
        raise RuntimeError("Could not load " + asset_path)
    result = {
        "mesh_methods": [name for name in dir(mesh) if "bound" in name.lower()],
        "unreal_names": [name for name in dir(unreal) if "StaticMesh" in name],
    }
    for name in result["mesh_methods"]:
        try:
            value = getattr(mesh, name)
            if callable(value):
                value = value()
            result.setdefault("values", {})[name] = str(value)
            result.setdefault("value_types", {})[name] = type(value).__name__
            result.setdefault("value_members", {})[name] = [
                member for member in dir(value) if member in {"min", "max", "origin", "box_extent", "sphere_radius"}
            ]
        except Exception as error:
            result.setdefault("errors", {})[name] = str(error)
    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "static_mesh_bounds_api.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin mesh bounds API wrote " + str(output))


if __name__ == "__main__":
    main()
