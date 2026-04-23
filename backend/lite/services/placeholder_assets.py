"""生成 M0 占位资产 USD（简单 Cube，按实际尺寸缩放）。

M0 阶段不做 FBX 转换，用这些 Cube 验证导出器和 Isaac Sim 加载流程。
M1 之后替换为真实 FBX → USD 转换产物。
"""
from pathlib import Path
from pxr import Usd, UsdGeom, Gf


# file_number → (display_name, size_xyz_in_meters)
PLACEHOLDER_ASSETS = {
    "franka":     ("Franka 机械臂（占位）",  (0.3, 0.3, 1.2)),
    "shelf":      ("标准货架（占位）",        (0.8, 0.4, 2.0)),
    "box_large":  ("大箱子 30cm（占位）",     (0.3, 0.3, 0.3)),
    "box_medium": ("中箱子 20cm（占位）",     (0.2, 0.2, 0.2)),
    "box_small":  ("小箱子 10cm（占位）",     (0.1, 0.1, 0.1)),
}


def create_placeholder_asset(name: str, size: tuple, output_path: str):
    """生成一个以 Cube 为几何体的占位资产 USD。

    size 为 (x, y, z) 米制尺寸，通过 scaleOp 驱动，cube 自身 size=1。
    """
    stage = Usd.Stage.CreateNew(str(output_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    xform = UsdGeom.Xform.Define(stage, f"/{name}")
    stage.SetDefaultPrim(xform.GetPrim())

    # 根 prim 不加 xformOps，保持干净，让引用方可以自由叠加 translate/rotate/scale
    xform.GetPrim().SetCustomDataByKey("placeholder", True)
    xform.GetPrim().SetCustomDataByKey("intendedSize_m", f"{size[0]},{size[1]},{size[2]}")

    # scale 放在子层级，不污染根 prim 的 xformOpOrder
    geo = UsdGeom.Xform.Define(stage, f"/{name}/geo")
    geo.AddScaleOp().Set(Gf.Vec3f(*size))

    cube = UsdGeom.Cube.Define(stage, f"/{name}/geo/mesh")
    cube.CreateSizeAttr(1.0)

    stage.Save()
    return str(output_path)


def generate_all(usd_cache_dir: Path) -> dict:
    """生成所有占位资产到 usd_cache_dir，返回 {file_number: path} 映射。"""
    usd_cache_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for file_number, (_, size) in PLACEHOLDER_ASSETS.items():
        out = usd_cache_dir / f"{file_number}.usd"
        create_placeholder_asset(file_number, size, out)
        results[file_number] = str(out)
        print(f"  [生成] {out.name}  size={size}")
    return results


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    cache_dir = project_root / "assets" / "usd_cache"
    print(f"生成占位资产 → {cache_dir}")
    generate_all(cache_dir)
    print("完成。")
