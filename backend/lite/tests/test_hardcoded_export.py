"""M0 验证脚本：生成占位资产 → 导出 USD → 打印结构摘要。

从项目根运行：
    python backend/lite/tests/test_hardcoded_export.py

验证清单（M0）：
  ✓ 无报错
  ✓ exports/hardcoded_demo.usda 生成，size > 0
  ✓ 肉眼看 USD 文本结构合理
  ✓ 发给训练同事，Isaac Sim 能加载
"""
import sys
from pathlib import Path

# 把 backend/ 加入 path，使 lite 包可导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from lite.services.placeholder_assets import generate_all
from lite.services.usd_exporter import export_scene_to_usd


SCENE_DATA = {
    "id": "hardcoded_demo",
    "display_name": "M0 硬编码演示场景",
    "dataset_id": "standard_practice",
    "bounds": {"x": [-3, 3], "y": [-3, 3], "z": [0, 3]},
    "instances": [
        {
            "id": "franka_001",
            "object_type_rid": "ri.obj.robot",
            "file_number": "franka",
            "translation": [0, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision_type": "static",
        },
        {
            "id": "shelf_001",
            "object_type_rid": "ri.obj.shelf",
            "file_number": "shelf",
            "translation": [1.5, 0, 0],
            "rotation": [0, 0, 90],
            "scale": [1, 1, 1],
            "collision_type": "static",
        },
        {
            "id": "shelf_002",
            "object_type_rid": "ri.obj.shelf",
            "file_number": "shelf",
            "translation": [-1.5, 0, 0],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision_type": "static",
        },
        {
            "id": "box_large_001",
            "object_type_rid": "ri.obj.box",
            "file_number": "box_large",
            "translation": [-0.5, 0.5, 0.15],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision_type": "graspable",
            "mass": 2.0,
            "friction": 0.5,
        },
        {
            "id": "box_medium_001",
            "object_type_rid": "ri.obj.box",
            "file_number": "box_medium",
            "translation": [0, 0.5, 0.10],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision_type": "graspable",
            "mass": 0.8,
            "friction": 0.5,
        },
        {
            "id": "box_small_001",
            "object_type_rid": "ri.obj.box",
            "file_number": "box_small",
            "translation": [0.5, 0.5, 0.05],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision_type": "graspable",
            "mass": 0.3,
            "friction": 0.6,
        },
    ],
}


def main():
    print("=" * 55)
    print("M0 硬编码导出验证")
    print("=" * 55)

    # Step 1：生成占位资产
    cache_dir = PROJECT_ROOT / "assets" / "usd_cache"
    print(f"\n[Step 1] 生成占位资产 → {cache_dir}")
    generate_all(cache_dir)

    # Step 2：导出场景
    output = PROJECT_ROOT / "exports" / "hardcoded_demo.usda"
    print(f"\n[Step 2] 导出场景 → {output}")
    result = export_scene_to_usd(SCENE_DATA, str(output), export_version=1)

    # Step 3：验证
    print(f"\n[Step 3] 验证结果")
    assert result["success"], f"导出失败: {result}"
    out_path = Path(result["file_path"])
    assert out_path.exists(), f"文件不存在: {out_path}"
    size_kb = out_path.stat().st_size / 1024
    assert size_kb > 0, "文件大小为 0"

    print(f"  ✓ 文件存在: {out_path.name}")
    print(f"  ✓ 文件大小: {size_kb:.1f} KB")
    print(f"  ✓ Prim 数量: {result['prim_count']}")

    if result["warnings"]:
        print(f"\n  ⚠ Warnings ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"    - {w}")
    else:
        print(f"  ✓ 无警告")

    # Step 4：打印 USD 文本前 50 行，肉眼检查结构
    print(f"\n[Step 4] USD 文件前 50 行：")
    print("-" * 55)
    lines = out_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines[:50], 1):
        print(f"  {i:3d}  {line}")
    if len(lines) > 50:
        print(f"  ... （共 {len(lines)} 行）")

    print("\n" + "=" * 55)
    print("M0 本地验证通过。请把以下文件发给训练同事：")
    print(f"  {output}")
    print(f"  {cache_dir}/*.usd（所有占位资产）")
    print("=" * 55)


if __name__ == "__main__":
    main()
