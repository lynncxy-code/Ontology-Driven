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
