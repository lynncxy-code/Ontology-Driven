"""
writeback.py —— UE→ontotwin 空间回写核心（FR-5，OntoTwin 3.4）
============================================================
把 UE 端调整后的空间变换（UE 世界坐标，单位 cm）落回真源。传输中立：
本模块只做业务逻辑，谁来调都行（编辑器回写端点 / 未来 runtime 拖拽回写），
不依赖 Flask / app.py。app.py 到时只需挂一个 POST 路由转调 apply_writeback()。

分类落点（见 grill 决策）：
  * 绑定 CAD 构件的实例：UE cm 逆变换回规范系 mm，写进构件 canonical_*（真源），
    同时把 raw_state 与构件 ue_* 更新为 UE 值——保持"真源+派生"一致，
    这样后续 _rederive_components 用规范系重算时不会把回写冲掉。
  * 自由实例（无构件，含迁移来的历史 actor）：raw_state 本身就是真源，直接写 UE cm。

坐标依赖 coord_transform：build_ue_matrix(规范mm→UE cm) 与其逆 invert_affine。
"""

import hashlib
import json
import math

from coord_transform import build_ue_matrix, invert_affine, apply_transform

# UE 空间数值字段（回写 payload 用；缺省值与实例 raw_state 约定一致）
_DEFAULTS = {
    "tx": 0.0, "ty": 0.0, "tz": 0.0,
    "rx": 0.0, "ry": 0.0, "rz": 0.0,
    "sx": 1.0, "sy": 1.0, "sz": 1.0,
}

_RAW_TRANSFORM_FIELDS = {
    "tx": "translation_x",
    "ty": "translation_y",
    "tz": "translation_z",
    "rx": "rotation_x",
    "ry": "rotation_y",
    "rz": "rotation_z",
    "sx": "scale_x",
    "sy": "scale_y",
    "sz": "scale_z",
}


def _f(transform, key):
    try:
        return float(transform.get(key, _DEFAULTS[key]))
    except (TypeError, ValueError):
        return _DEFAULTS[key]


def runtime_edit_state_hash(raw):
    """Stable optimistic-lock hash for fields writable by Runtime Editor."""
    raw = raw or {}
    state = {
        raw_key: float(raw.get(raw_key, _DEFAULTS[key]))
        for key, raw_key in _RAW_TRANSFORM_FIELDS.items()
    }
    state["is_loaded"] = bool(raw.get("is_loaded", True))
    state["runtime_spatial_editable"] = bool(raw.get("runtime_spatial_editable", True))
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_transform(transform):
    if not isinstance(transform, dict):
        return None, "transform must be an object"

    normalized = {}
    for key in _DEFAULTS:
        if key not in transform:
            return None, f"transform.{key} is required"
        try:
            value = float(transform[key])
        except (TypeError, ValueError):
            return None, f"transform.{key} must be numeric"
        if not math.isfinite(value):
            return None, f"transform.{key} must be finite"
        normalized[key] = value
    return normalized, None


def apply_writeback(store, instance_id, transform, persist=True, expected_project_id=None):
    """
    落库一次 UE 空间回写。

    Args:
        store: ProjectStore / ProjectStorePG（当前激活项目）
        instance_id: 目标实例 id
        transform: UE cm 变换 {tx,ty,tz, rx,ry,rz, sx,sy,sz}
                   （rx=Roll, ry=Pitch, rz=Yaw，与 UE 导出/ApplySpatial 约定一致）
        persist: 是否立即落盘

    Returns:
        (ok: bool, info: dict)
    """
    raw = store.get_raw_state(instance_id)
    if raw is None:
        return False, {"error": "instance not found", "instance_id": instance_id}

    tx, ty, tz = _f(transform, "tx"), _f(transform, "ty"), _f(transform, "tz")
    rx, ry, rz = _f(transform, "rx"), _f(transform, "ry"), _f(transform, "rz")
    sx, sy, sz = _f(transform, "sx"), _f(transform, "sy"), _f(transform, "sz")

    raw_patch = {
        "translation_x": tx, "translation_y": ty, "translation_z": tz,
        "rotation_x": rx, "rotation_y": ry, "rotation_z": rz,
        "scale_x": sx, "scale_y": sy, "scale_z": sz,
    }

    comp = store.get_component_by_instance(instance_id)

    # ── 自由实例：raw_state 即真源，直接写 ────────────────────────────────
    if comp is None:
        store.update_raw_state(instance_id, raw_patch, persist=persist,
                               expected_project_id=expected_project_id)
        return True, {"mode": "free", "instance_id": instance_id}

    # ── 绑定实例：回写到规范系真源，并同步派生 ─────────────────────────────
    profile = store.get_spatial_profile()
    m = build_ue_matrix(profile)
    inv = invert_affine(m)
    if inv is None:
        # 仿射退化（多半是 profile 未标定）→ 拒绝，避免写入垃圾规范坐标
        return False, {"error": "affine not invertible (profile uncalibrated?)",
                       "instance_id": instance_id}

    canon_xy = apply_transform(inv, [tx, ty])           # UE cm → 规范 mm
    ut = (profile or {}).get("ue_transform") or {}
    scale = float(ut.get("scale_to_cm", 0.1) or 0.1)
    canon_z = tz / scale if scale else 0.0              # ue_z = canon_z * scale 的逆

    # 下面两次写各自独立加锁（非单一事务）：若两次取锁之间激活项目被切换，
    # 第二次 update_raw_state 会在第一次已落盘后抛 ProjectMismatch（409）——
    # 一处窄窗口的部分写，符合既有多锁设计，且守卫仍会拒绝第二次写入。
    store.update_component(comp["id"], {
        "canonical_xy": [round(canon_xy[0], 3), round(canon_xy[1], 3)],
        "canonical_z": round(canon_z, 3),
        "rotation": rz,               # 构件旋转沿用 UE Yaw
        "ue_xy": [tx, ty],            # 同步派生，保持与真源一致
        "ue_z": tz,
    }, persist=persist, expected_project_id=expected_project_id)
    store.update_raw_state(instance_id, raw_patch, persist=persist,
                           expected_project_id=expected_project_id)
    return True, {
        "mode": "bound",
        "instance_id": instance_id,
        "component_id": comp["id"],
        "canonical_xy": [round(canon_xy[0], 3), round(canon_xy[1], 3)],
        "canonical_z": round(canon_z, 3),
    }


def apply_batch_writeback(store, changes, max_changes=100):
    """Atomically apply one Runtime Editor session with optimistic locking."""
    if not isinstance(changes, list) or not changes:
        return False, {"error": "changes_required", "message": "changes must be a non-empty array"}, 400
    if len(changes) > max_changes:
        return False, {
            "error": "too_many_changes",
            "message": f"at most {max_changes} changes are allowed",
            "limit": max_changes,
        }, 400

    def mutate():
        prepared = []
        seen = set()
        conflicts = []

        for index, change in enumerate(changes):
            if not isinstance(change, dict):
                return False, {
                    "error": "invalid_change",
                    "message": f"changes[{index}] must be an object",
                }

            instance_id = str(change.get("instance_id") or "").strip()
            if not instance_id:
                return False, {
                    "error": "instance_id_required",
                    "message": f"changes[{index}].instance_id is required",
                }
            if instance_id in seen:
                return False, {
                    "error": "duplicate_instance",
                    "message": f"duplicate instance_id: {instance_id}",
                    "instance_id": instance_id,
                }
            seen.add(instance_id)

            raw = store.get_raw_state(instance_id)
            if raw is None:
                return False, {
                    "error": "instance_not_found",
                    "message": f"instance not found: {instance_id}",
                    "instance_id": instance_id,
                }
            if not bool(raw.get("runtime_spatial_editable", True)):
                return False, {
                    "error": "runtime_spatial_edit_disabled",
                    "message": f"runtime spatial editing is disabled: {instance_id}",
                    "instance_id": instance_id,
                }

            expected_hash = str(change.get("expected_state_hash") or "").strip()
            current_hash = runtime_edit_state_hash(raw)
            if not expected_hash or expected_hash != current_hash:
                conflicts.append({
                    "instance_id": instance_id,
                    "expected_state_hash": expected_hash,
                    "current_state_hash": current_hash,
                })
                continue

            transform, error = _normalize_transform(change.get("transform"))
            if error:
                return False, {
                    "error": "invalid_transform",
                    "message": error,
                    "instance_id": instance_id,
                }

            is_loaded = change.get("is_loaded", raw.get("is_loaded", True))
            if not isinstance(is_loaded, bool):
                return False, {
                    "error": "invalid_is_loaded",
                    "message": "is_loaded must be boolean",
                    "instance_id": instance_id,
                }
            prepared.append((instance_id, transform, is_loaded))

        if conflicts:
            return False, {
                "error": "runtime_edit_conflict",
                "message": "one or more instances changed after editing began",
                "conflicts": conflicts,
            }

        results = []
        for instance_id, transform, is_loaded in prepared:
            ok, info = apply_writeback(store, instance_id, transform, persist=False)
            if not ok:
                return False, {"error": "writeback_failed", **info}
            if not store.update_raw_state(instance_id, {"is_loaded": is_loaded}, persist=False):
                return False, {
                    "error": "instance_not_found",
                    "instance_id": instance_id,
                }
            results.append(info)

        return True, {"results": results, "count": len(results)}

    try:
        ok, info = store.run_atomic_update(mutate)
    except Exception as exc:
        return False, {
            "error": "batch_persist_failed",
            "message": str(exc),
        }, 500

    if not ok:
        status = 409 if info.get("error") == "runtime_edit_conflict" else 400
        if info.get("error") == "instance_not_found":
            status = 404
        if info.get("error") == "runtime_spatial_edit_disabled":
            status = 403
        return False, info, status
    return True, info, 200
