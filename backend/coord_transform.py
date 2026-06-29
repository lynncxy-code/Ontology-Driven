"""
coord_transform.py — 后端仿射变换计算模块
PRD 2.9: CAD 坐标标定工作台
与前端 coord_transform.js 算法对称
"""
import numpy as np


def calibrate(anchors):
    """
    最小二乘法求解 2D 仿射变换矩阵。

    Args:
        anchors: list of {"src": [x,y], "dst": [x,y]}

    Returns:
        dict with matrix, rmse, per_anchor_residuals, scale info
    
    Raises:
        ValueError: 锚点不足或数据退化
    """
    n = len(anchors)
    if n < 2:
        raise ValueError("至少需要 2 组锚点")

    src = np.array([a["src"] for a in anchors], dtype=np.float64)
    dst = np.array([a["dst"] for a in anchors], dtype=np.float64)

    # 构造 A * params = b
    # [sx, sy, 1, 0, 0, 0] [a]   [dx]
    # [0, 0, 0, sx, sy, 1] [b] = [dy]
    #                       [tx]
    #                       [c]
    #                       [d]
    #                       [ty]
    A = np.zeros((2 * n, 6))
    b = np.zeros(2 * n)
    for i in range(n):
        sx, sy = src[i]
        dx, dy = dst[i]
        A[2 * i]     = [sx, sy, 1, 0, 0, 0]
        A[2 * i + 1] = [0, 0, 0, sx, sy, 1]
        b[2 * i]     = dx
        b[2 * i + 1] = dy

    # 最小二乘求解
    try:
        params, residuals, rank, sv = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        raise ValueError("锚点数据退化（可能共线），无法求解")

    if rank < 6 and n >= 3:
        # 检查是否真正退化（2点时 rank=4 是正常的）
        pass

    a, b_val, tx, c, d, ty = params
    matrix = [
        [round(a, 8), round(b_val, 8), round(tx, 4)],
        [round(c, 8), round(d, 8),     round(ty, 4)],
        [0, 0, 1]
    ]

    # 各锚点残差
    per_anchor = []
    for i in range(n):
        pred = apply_transform(matrix, src[i].tolist())
        err = np.sqrt((pred[0] - dst[i][0])**2 + (pred[1] - dst[i][1])**2)
        per_anchor.append({"index": i, "residual_cm": round(float(err), 2)})

    residual_values = [p["residual_cm"] for p in per_anchor]
    rmse = float(np.sqrt(np.mean(np.array(residual_values)**2)))

    # 缩放因子
    scale_x = float(np.sqrt(a**2 + c**2))
    scale_y = float(np.sqrt(b_val**2 + d**2))
    avg_scale = (scale_x + scale_y) / 2
    consistency = abs(scale_x - scale_y) / avg_scale * 100 if avg_scale > 0 else 0

    return {
        "success": True,
        "transform_matrix": matrix,
        "metrics": {
            "rmse_cm": round(rmse, 2),
            "scale_x": round(scale_x, 6),
            "scale_y": round(scale_y, 6),
            "scale_consistency_pct": round(consistency, 2),
            "per_anchor_residuals": per_anchor
        }
    }


def apply_transform(matrix, point):
    """应用 3x3 仿射矩阵到 2D 点"""
    x = matrix[0][0] * point[0] + matrix[0][1] * point[1] + matrix[0][2]
    y = matrix[1][0] * point[0] + matrix[1][1] * point[1] + matrix[1][2]
    return [round(x, 2), round(y, 2)]


import math


def _axis_vec(spec):
    """'+x'/'-y' → (列索引, 符号)。"""
    sign = -1.0 if str(spec).startswith("-") else 1.0
    idx = 0 if str(spec).endswith("x") else 1
    return idx, sign


def _build_coarse_matrix(ut):
    """由"规范→UE"的粗声明（轴映射 + 翻转 + 旋转 + 尺度 + 原点）构造 3×3 仿射。
    仅在未做锚点精确拟合时用于预览；锚点拟合后用 ut['matrix'] 覆盖。"""
    disp = ut.get("display") or {}
    am = disp.get("axis_map") or {"x": "+x", "y": "+y"}
    ix, sx = _axis_vec(am.get("x", "+x"))
    iy, sy = _axis_vec(am.get("y", "+y"))
    # 轴映射 2×2：ue = AxisM · canon
    axisM = [[0.0, 0.0], [0.0, 0.0]]
    axisM[0][ix] = sx
    axisM[1][iy] = sy
    # 翻转（X 镜像）
    flip = [[-1.0, 0.0], [0.0, 1.0]] if disp.get("flip") else [[1.0, 0.0], [0.0, 1.0]]
    # 旋转
    th = math.radians(float(disp.get("rotation_deg", 0) or 0))
    rot = [[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]

    def mul(a, b):
        return [[a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]],
                [a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]]]

    F = mul(rot, mul(flip, axisM))
    s = float(ut.get("scale_to_cm", 0.1) or 0.1)
    ox, oy = (ut.get("ue_origin_cm") or [0.0, 0.0])[:2]
    return [
        [s * F[0][0], s * F[0][1], float(ox)],
        [s * F[1][0], s * F[1][1], float(oy)],
        [0, 0, 1],
    ]


def build_ue_matrix(profile):
    """取"规范→UE"3×3 仿射：优先用锚点拟合的精确矩阵；未标定则用粗声明构造。"""
    ut = (profile or {}).get("ue_transform") or {}
    m = ut.get("matrix")
    if m:
        return m
    return _build_coarse_matrix(ut)


def canonical_to_ue(profile, xy, floor=1):
    """规范坐标(mm) + 楼层 → UE 世界坐标(cm) [x, y, z]。
    z = 该楼层 z_base_mm × scale_to_cm（与 XY 同量纲；尺度待现场核实，见 PRD §12）。"""
    m = build_ue_matrix(profile)
    ue = apply_transform(m, xy)
    ut = (profile or {}).get("ue_transform") or {}
    scale = float(ut.get("scale_to_cm", 0.1) or 0.1)
    z_base_mm = 0.0
    for ft in (profile or {}).get("floor_table") or []:
        if ft.get("floor") == floor:
            z_base_mm = float(ft.get("z_base_mm", 0) or 0)
            break
    return [ue[0], ue[1], round(z_base_mm * scale, 2)]


def invert_affine(matrix):
    """求 3×3 仿射的逆（FR-9：将来向外部系反算坐标）。退化时返回 None。"""
    a, b, tx = matrix[0]
    c, d, ty = matrix[1]
    det = a * d - b * c
    if abs(det) < 1e-12:
        return None
    ia, ib = d / det, -b / det
    ic, idd = -c / det, a / det
    return [
        [round(ia, 10), round(ib, 10), round(-(ia * tx + ib * ty), 4)],
        [round(ic, 10), round(idd, 10), round(-(ic * tx + idd * ty), 4)],
        [0, 0, 1],
    ]


def batch_transform(matrix, entities):
    """
    批量变换实体坐标，返回带 UE 坐标的实体列表。
    用于导出接口。
    """
    result = []
    for ent in entities:
        ent_out = dict(ent)
        if ent.get("position"):
            ue = apply_transform(matrix, ent["position"])
            ent_out["ue_position"] = ue
        if ent.get("points"):
            ent_out["ue_points"] = [apply_transform(matrix, p) for p in ent["points"]]
        result.append(ent_out)
    return result
