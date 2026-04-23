"""USD 导出器：把场景 dict 导出为 .usda 文件。

M0 阶段：不依赖数据库，接受硬编码 dict，生成符合 Isaac Sim 要求的 USD。
坐标系：厘米 + Z-up + 右手系（metersPerUnit=0.01，与 UE 导出资产单位一致）。
DB 中坐标存储为米，写入 USD 时自动 ×100 转换为厘米。
"""
import os
from pathlib import Path
from datetime import datetime, timezone

from pxr import Usd, UsdGeom, UsdPhysics, Gf


# object_type_rid → USD 分组名（见 TECH_SPEC 3.2）
_GROUP_MAP = {
    "ri.obj.robot": "Robots",
    "ri.obj.shelf": "Shelves",
    "ri.obj.box": "Boxes",
}


def export_scene_to_usd(
    scene_data: dict,
    output_path: str,
    export_version: int = 1,
    include_physics: bool = True,
) -> dict:
    """导出一个 Scene 为 USD 文件。

    scene_data 结构见 IMPLEMENTATION_PLAN M0-2。
    返回 {success, file_path, prim_count, warnings}。
    """
    warnings: list[str] = []
    out_abs = str(Path(output_path).resolve())
    Path(out_abs).parent.mkdir(parents=True, exist_ok=True)

    stage = Usd.Stage.CreateNew(out_abs)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # 场景级 customData
    world.GetPrim().SetCustomDataByKey("ontology", {
        "sourceScene": scene_data["id"],
        "datasetId": scene_data.get("dataset_id", "standard_practice"),
        "exportVersion": export_version,
        "exportTimestamp": _utc_now_iso(),
    })

    prim_count = 1  # /World
    for inst in scene_data.get("instances", []):
        group_path = _ensure_group(stage, inst["object_type_rid"])
        if group_path not in _ensure_group._cache.get(id(stage), set()):
            prim_count += 1
            _ensure_group._cache.setdefault(id(stage), set()).add(group_path)

        inst_path = f"{group_path}/{inst['id']}"
        # Xform 负责坐标变换；资产引用放子 prim，让引用的类型（Mesh/Xform）自决
        inst_xform = UsdGeom.Xform.Define(stage, inst_path)
        prim = inst_xform.GetPrim()
        prim_count += 1

        asset_ref = _resolve_asset_ref(inst["file_number"], out_abs, warnings)
        if asset_ref:
            asset_prim = stage.DefinePrim(f"{inst_path}/asset")
            asset_prim.GetReferences().AddReference(asset_ref)

        _apply_transform(inst_xform, inst)

        if include_physics:
            _apply_physics_schema(
                prim,
                collision_type=inst.get("collision_type", "static"),
                mass=inst.get("mass"),
                friction=inst.get("friction", 0.5),
                warnings=warnings,
            )


        _write_ontology_metadata(prim, inst, scene_data, export_version)

    stage.Save()
    # 清缓存避免多次调用串扰
    _ensure_group._cache.pop(id(stage), None)

    return {
        "success": True,
        "file_path": out_abs,
        "prim_count": prim_count,
        "warnings": warnings,
    }


# ── 内部辅助 ─────────────────────────────────────────────────────

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _ensure_group(stage: Usd.Stage, object_type_rid: str) -> str:
    """根据 object_type_rid 获取/创建分组 Xform，返回分组路径。"""
    group = _GROUP_MAP.get(object_type_rid, "Misc")
    path = f"/World/{group}"
    if not stage.GetPrimAtPath(path):
        UsdGeom.Xform.Define(stage, path)
    return path

_ensure_group._cache = {}  # 简易缓存，用于计数新建的分组


def _resolve_asset_ref(file_number: str, output_abs: str, warnings: list) -> str:
    """返回资产 USD 相对于 output 目录的路径，用于 USD 引用。

    资产缺失时仍写入引用并在 warnings 里记录，便于后续补齐。
    """
    # 以项目根（output 所在的 exports/ 的父目录）为基准查找
    project_root = Path(output_abs).resolve().parent.parent
    # 优先找 .usda（UE 导出格式），其次 .usd（占位资产格式）
    asset_abs = None
    for ext in (".usda", ".usd"):
        candidate = (project_root / "assets" / "usd_cache" / f"{file_number}{ext}").resolve()
        if candidate.exists():
            asset_abs = candidate
            break
    if asset_abs is None:
        asset_abs = (project_root / "assets" / "usd_cache" / f"{file_number}.usd").resolve()
        warnings.append(f"asset USD missing: {asset_abs}")
    rel = os.path.relpath(str(asset_abs), start=str(Path(output_abs).parent))
    return rel.replace("\\", "/")


def _apply_transform(xformable: UsdGeom.Xform, inst: dict):
    t = inst.get("translation", [0, 0, 0])
    r = inst.get("rotation", [0, 0, 0])
    s = inst.get("scale", [1, 1, 1])
    # DB 单位为米，USD 场景单位为厘米（metersPerUnit=0.01），乘以 100 转换
    xformable.AddTranslateOp().Set(Gf.Vec3d(float(t[0])*100, float(t[1])*100, float(t[2])*100))
    xformable.AddRotateXYZOp().Set(Gf.Vec3f(float(r[0]), float(r[1]), float(r[2])))
    xformable.AddScaleOp().Set(Gf.Vec3f(float(s[0]), float(s[1]), float(s[2])))


def _apply_physics_schema(prim, collision_type: str, mass, friction: float, warnings: list):
    """按 ADR-006 三分法应用 USD Physics Schema。"""
    UsdPhysics.CollisionAPI.Apply(prim)
    if collision_type == "static":
        return

    if collision_type not in ("dynamic", "graspable"):
        warnings.append(f"unknown collision_type: {collision_type} (instance will be static)")
        return

    UsdPhysics.RigidBodyAPI.Apply(prim)
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    if mass is not None:
        mass_api.CreateMassAttr(float(mass))

    mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
    approx = "none" if collision_type == "graspable" else "convexHull"
    mesh_collision.CreateApproximationAttr(approx)

    # friction 需要 PhysicsMaterial 绑定，M0 先写入 customData 留档
    prim.SetCustomDataByKey("physics:frictionHint", float(friction))


def _write_ontology_metadata(prim, inst: dict, scene_data: dict, export_version: int):
    """写入 ADR-011 规定的 customData.ontology 追溯信息。"""
    prim.SetCustomDataByKey("ontology", {
        "instanceId": inst["id"],
        "objectTypeRid": inst["object_type_rid"],
        "fileNumber": inst["file_number"],
        "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_PhysicsHint"],
        "sourceScene": scene_data["id"],
        "datasetId": scene_data.get("dataset_id", "standard_practice"),
        "exportVersion": export_version,
        "exportTimestamp": _utc_now_iso(),
    })
