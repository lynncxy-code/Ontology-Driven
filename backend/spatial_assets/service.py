import copy
import datetime
import hashlib
import json
import os
import uuid

from coord_transform import build_ue_matrix, calibrate as coord_calibrate, invert_affine

from .storage import SpatialAssetStorage
from .validators import (
    SpatialFrameValidationError,
    clean_name,
    ensure_non_collinear,
    finite_number,
    normalize_cad_anchors,
    normalize_anchors,
    positive_int,
)


IMAGE_CALIBRATION_PUBLISH_RMSE_CM = 50.0
IMAGE_CALIBRATION_PUBLISH_MAX_RESIDUAL_CM = 75.0
CAD_CALIBRATION_PUBLISH_RMSE_CM = 200.0


class SpatialFrameNotFoundError(LookupError):
    pass


class SpatialFrameConflictError(RuntimeError):
    pass


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _find_frame(project, frame_id):
    for frame in project.get("frames") or []:
        if isinstance(frame, dict) and frame.get("id") == frame_id:
            return frame
    return None


def _find_floor(project, floor, floor_id):
    profile = project.get("spatial_profile") or {}
    for item in profile.get("floor_table") or []:
        if not isinstance(item, dict):
            continue
        if item.get("floor_id") == floor_id or item.get("floor") == floor:
            return item
    return None


def _multiply_affine(left, right):
    return [
        [
            sum(float(left[row][k]) * float(right[k][column]) for k in range(3))
            for column in range(3)
        ]
        for row in range(3)
    ]


class SpatialFrameService:
    def __init__(self, store, asset_root=None):
        self.store = store
        self.storage = SpatialAssetStorage(asset_root)

    def _project(self):
        project = self.store.get_active_copy()
        if not project:
            raise SpatialFrameNotFoundError("当前无激活项目")
        return project

    @staticmethod
    def _public_frame(frame):
        value = copy.deepcopy(frame)
        if value.get("kind") == "image" and isinstance(value.get("image"), dict):
            value["image_url"] = f"/api/v2/spatial-frames/{value.get('id')}/image"
        image = value.get("image")
        if isinstance(image, dict):
            image.pop("storage_name", None)
        cad = value.get("cad")
        if isinstance(cad, dict):
            cad.pop("storage_name", None)
            value["source_url"] = f"/api/v2/spatial-frames/{value.get('id')}/source"
        return value

    def list_frames(self, kind="image"):
        project = self._project()
        if kind not in ("image", "cad", "all"):
            raise SpatialFrameValidationError("frame_kind_invalid", "kind 仅支持 image、cad 或 all", status=400)
        frames = [
            self._public_frame(frame) for frame in project.get("frames") or []
            if isinstance(frame, dict)
            and frame.get("kind") in ("image", "cad")
            and (kind == "all" or frame.get("kind") == kind)
            and isinstance(frame.get("image") if frame.get("kind") == "image" else frame.get("cad"), dict)
        ]
        return {"project_id": project.get("id"), "frames": frames}

    def get_frame(self, frame_id):
        project = self._project()
        frame = _find_frame(project, frame_id)
        source = frame.get("image") if frame and frame.get("kind") == "image" else frame.get("cad") if frame else None
        if not frame or frame.get("kind") not in ("image", "cad") or not isinstance(source, dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
        return self._public_frame(frame)

    def create_image_frame(self, file_storage, fields, expected_project_id=None):
        project = self._project()
        if file_storage is None:
            raise SpatialFrameValidationError("image_required", "请选择图片文件", status=400)
        data = file_storage.stream.read(20 * 1024 * 1024 + 1)
        image, path, created = self.storage.store_image(
            project.get("id"), data, file_storage.filename or ""
        )
        floor = positive_int(fields.get("floor"), "floor", 1)
        floor_id = str(fields.get("floor_id") or f"floor-{floor}").strip()
        ue_level = str(fields.get("ue_level") or "").strip()
        frame_id = "frame.image." + uuid.uuid4().hex[:16]
        now = _utc_now()
        dataset = project.get("dataset") or {}
        frame = {
            "id": frame_id,
            "name": clean_name(fields.get("name"), image.get("original_name") or "图片空间底图"),
            "kind": "image",
            "unit": "px",
            "status": "draft",
            "floor": floor,
            "floor_id": floor_id,
            "bound_ue_project_id": str(dataset.get("bound_ue_project_id") or ""),
            "ue_level": ue_level,
            "image": image,
            "anchors": [],
            "floor_reference": None,
            "to_ue": None,
            "to_canonical": None,
            "calibration_revision": 0,
            "draft_revision": 0,
            "calibration_fingerprint": "",
            "created_at": now,
            "updated_at": now,
        }

        def update(working):
            working.setdefault("frames", []).append(copy.deepcopy(frame))

        try:
            self.store.transact_expected_active(expected_project_id, update)
        except Exception:
            self.storage.remove_if_created(path, created)
            raise
        return {"status": "ok", "frame": self._public_frame(frame)}

    def create_cad_frame(self, file_storage, fields, expected_project_id=None):
        project = self._project()
        if file_storage is None:
            raise SpatialFrameValidationError("cad_required", "请选择 DXF 文件", status=400)
        cad, path, created = self.storage.store_cad_stream(
            project.get("id"), file_storage.stream, file_storage.filename or ""
        )
        floor = positive_int(fields.get("floor"), "floor", 1)
        floor_id = str(fields.get("floor_id") or f"floor-{floor}").strip()
        ue_level = str(fields.get("ue_level") or "").strip()
        frame_id = "frame.cad." + uuid.uuid4().hex[:16]
        now = _utc_now()
        dataset = project.get("dataset") or {}
        profile = project.get("spatial_profile") or {}
        frame = {
            "id": frame_id,
            "name": clean_name(fields.get("name"), cad.get("original_name") or "CAD 空间底图"),
            "kind": "cad",
            "unit": "mm",
            "status": "draft",
            "floor": floor,
            "floor_id": floor_id,
            "bound_ue_project_id": str(dataset.get("bound_ue_project_id") or ""),
            "ue_level": ue_level,
            "cad": cad,
            "anchors": [],
            "to_ue": None,
            "to_canonical": None,
            "transform": None,
            "display": copy.deepcopy(((profile.get("ue_transform") or {}).get("display") or {})),
            "canonical_origin": copy.deepcopy((profile.get("canonical_origin") or [0.0, 0.0])[:2]),
            "calibration_revision": 0,
            "draft_revision": 0,
            "calibration_fingerprint": "",
            "created_at": now,
            "updated_at": now,
        }

        def update(working):
            working.setdefault("frames", []).append(copy.deepcopy(frame))

        try:
            self.store.transact_expected_active(expected_project_id, update)
        except Exception:
            self.storage.remove_if_created(path, created)
            raise
        return {"status": "ok", "frame": self._public_frame(frame)}

    def save_draft(self, frame_id, payload, expected_project_id=None):
        if not isinstance(payload, dict):
            raise SpatialFrameValidationError("invalid_request", "请求体必须是对象", status=400)
        project = self._project()
        current = _find_frame(project, frame_id)
        if current and current.get("kind") == "cad" and isinstance(current.get("cad"), dict):
            return self._save_cad_draft(project, current, payload, expected_project_id)
        if not current or current.get("kind") != "image" or not isinstance(current.get("image"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
        configured_floor = _find_floor(project, current.get("floor"), current.get("floor_id"))
        if configured_floor is None:
            raise SpatialFrameValidationError(
                "floor_not_configured", "发布前请先保存该楼层的空间配置"
            )
        finite_number(configured_floor.get("z_base_mm"), "floor.z_base_mm")
        expected = payload.get("expected_draft_revision")
        if expected is not None:
            try:
                expected = int(expected)
            except (TypeError, ValueError) as exc:
                raise SpatialFrameValidationError("draft_revision_invalid", "expected_draft_revision 必须是整数") from exc
            if expected != int(current.get("draft_revision") or 0):
                raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")

        anchors = normalize_anchors(payload.get("anchors") or [])
        image = current.get("image") or {}
        image_width = float(image.get("width_px") or 0)
        image_height = float(image.get("height_px") or 0)
        out_of_bounds = []
        for index, anchor in enumerate(anchors):
            x, y = anchor["source_px"]
            if x < 0 or y < 0 or (image_width and x > image_width) or (image_height and y > image_height):
                out_of_bounds.append({
                    "path": f"anchors[{index}].source_px",
                    "message": "图片锚点必须位于原始图片范围内",
                })
        if out_of_bounds:
            raise SpatialFrameValidationError(
                "anchor_source_out_of_bounds",
                "图片锚点超出原始图片范围",
                fields=out_of_bounds,
            )
        floor = positive_int(payload.get("floor", current.get("floor")), "floor", 1)
        floor_id = str(payload.get("floor_id") or current.get("floor_id") or f"floor-{floor}").strip()
        ue_level = str(payload.get("ue_level") if "ue_level" in payload else current.get("ue_level") or "").strip()
        reference_id = str(payload.get("floor_reference_anchor_id") or "").strip()
        reference = next((item for item in anchors if item["id"] == reference_id), None)
        if reference_id and not reference:
            raise SpatialFrameValidationError("floor_reference_invalid", "地面基准必须引用当前标定锚点")

        to_ue = None
        to_canonical = None
        metrics = None
        if len(anchors) >= 3:
            ensure_non_collinear(anchors)
            calibrated = coord_calibrate([
                {"src": item["source_px"], "dst": item["ue_world_cm"][:2]}
                for item in anchors
            ])
            to_ue = calibrated["transform_matrix"]
            metrics = calibrated.get("metrics") or {}
            ue_to_canonical = invert_affine(build_ue_matrix(project.get("spatial_profile") or {}))
            if ue_to_canonical is None:
                raise SpatialFrameValidationError(
                    "canonical_matrix_singular", "项目规范坐标到 UE 的矩阵不可逆"
                )
            to_canonical = _multiply_affine(ue_to_canonical, to_ue)

        now = _utc_now()
        updated = copy.deepcopy(current)
        updated.update({
            "name": clean_name(payload.get("name"), current.get("name") or "图片空间底图"),
            "status": "draft",
            "floor": floor,
            "floor_id": floor_id,
            "ue_level": ue_level,
            "anchors": anchors,
            "floor_reference": ({
                "canonical_z_base_mm": self._floor_z_base(project, floor, floor_id),
                "ue_ground_z_cm": reference["ue_world_cm"][2],
                "captured_from_anchor_id": reference["id"],
            } if reference else None),
            "to_ue": ({"method": "anchor", "matrix": to_ue} if to_ue else None),
            "to_canonical": ({"method": "anchor", "matrix": to_canonical} if to_canonical else None),
            "transform": ({
                "type": "affine_2d",
                "source": "image_px",
                "target": "canonical_mm",
                "matrix": to_canonical,
                "metrics": metrics,
            } if to_canonical else None),
            "draft_revision": int(current.get("draft_revision") or 0) + 1,
            "updated_at": now,
        })

        def update(working):
            frames = working.setdefault("frames", [])
            for index, frame in enumerate(frames):
                if frame.get("id") == frame_id:
                    actual = int(frame.get("draft_revision") or 0)
                    if expected is not None and actual != expected:
                        raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
                    frames[index] = copy.deepcopy(updated)
                    return
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "frame": self._public_frame(updated)}

    def _save_cad_draft(self, project, current, payload, expected_project_id=None):
        expected = payload.get("expected_draft_revision")
        if expected is not None:
            try:
                expected = int(expected)
            except (TypeError, ValueError) as exc:
                raise SpatialFrameValidationError(
                    "draft_revision_invalid", "expected_draft_revision 必须是整数"
                ) from exc
            if expected != int(current.get("draft_revision") or 0):
                raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")

        anchors = normalize_cad_anchors(payload.get("anchors") or [])
        floor = positive_int(payload.get("floor", current.get("floor")), "floor", 1)
        floor_id = str(payload.get("floor_id") or current.get("floor_id") or f"floor-{floor}").strip()
        ue_level = str(payload.get("ue_level") if "ue_level" in payload else current.get("ue_level") or "").strip()
        origin_value = payload.get("canonical_origin", current.get("canonical_origin") or [0.0, 0.0])
        if not isinstance(origin_value, (list, tuple)) or len(origin_value) != 2:
            raise SpatialFrameValidationError("canonical_origin_invalid", "规范原点必须是二维坐标")
        origin = [
            finite_number(origin_value[0], "canonical_origin[0]"),
            finite_number(origin_value[1], "canonical_origin[1]"),
        ]
        display_value = payload.get("display", current.get("display") or {})
        display = copy.deepcopy(display_value if isinstance(display_value, dict) else {})

        to_ue = None
        to_canonical = None
        metrics = None
        if len(anchors) >= 3:
            ensure_non_collinear(anchors, "source_xy_mm")
            calibrated = coord_calibrate([
                {"src": item["source_xy_mm"], "dst": item["ue_world_cm"][:2]}
                for item in anchors
            ])
            to_ue = calibrated["transform_matrix"]
            metrics = calibrated.get("metrics") or {}
            to_canonical = [
                [1.0, 0.0, -origin[0]],
                [0.0, 1.0, -origin[1]],
                [0.0, 0.0, 1.0],
            ]

        now = _utc_now()
        updated = copy.deepcopy(current)
        updated.update({
            "name": clean_name(payload.get("name"), current.get("name") or "CAD 空间底图"),
            "status": "draft",
            "floor": floor,
            "floor_id": floor_id,
            "ue_level": ue_level,
            "anchors": anchors,
            "to_ue": ({"method": "anchor", "matrix": to_ue} if to_ue else None),
            "to_canonical": ({"method": "origin", "matrix": to_canonical} if to_canonical else None),
            "transform": ({
                "type": "affine_2d",
                "source": "cad_mm",
                "target": "canonical_mm",
                "matrix": to_canonical,
                "metrics": metrics,
            } if to_canonical else None),
            "display": display,
            "canonical_origin": origin,
            "draft_revision": int(current.get("draft_revision") or 0) + 1,
            "updated_at": now,
        })

        def update(working):
            frames = working.setdefault("frames", [])
            for index, frame in enumerate(frames):
                if frame.get("id") == current.get("id"):
                    actual = int(frame.get("draft_revision") or 0)
                    if expected is not None and actual != expected:
                        raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
                    frames[index] = copy.deepcopy(updated)
                    return
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "frame": self._public_frame(updated)}

    @staticmethod
    def _floor_z_base(project, floor, floor_id):
        profile = project.get("spatial_profile") or {}
        for item in profile.get("floor_table") or []:
            if not isinstance(item, dict):
                continue
            if item.get("floor_id") == floor_id or item.get("floor") == floor:
                return float(item.get("z_base_mm") or 0.0)
        return 0.0

    def publish(self, frame_id, payload, expected_project_id=None):
        payload = payload if isinstance(payload, dict) else {}
        project = self._project()
        current = _find_frame(project, frame_id)
        if current and current.get("kind") == "cad" and isinstance(current.get("cad"), dict):
            return self._publish_cad(project, current, payload, expected_project_id)
        if not current or current.get("kind") != "image" or not isinstance(current.get("image"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
        expected = payload.get("expected_draft_revision")
        if expected is not None and int(expected) != int(current.get("draft_revision") or 0):
            raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
        anchors = current.get("anchors") or []
        ensure_non_collinear(anchors)
        if not current.get("to_ue") or not current.get("to_canonical"):
            raise SpatialFrameValidationError("frame_not_calibrated", "请先保存有效的标定草稿")
        reference = current.get("floor_reference")
        if not isinstance(reference, dict) or reference.get("ue_ground_z_cm") is None:
            raise SpatialFrameValidationError("floor_reference_required", "发布前必须选择一个楼层地面基准点")
        metrics = ((current.get("transform") or {}).get("metrics") or {})
        rmse = finite_number(metrics.get("rmse_cm"), "metrics.rmse_cm", 0)
        residuals = metrics.get("per_anchor_residuals") or []
        max_residual = max(
            [finite_number(item.get("residual_cm"), "metrics.per_anchor_residuals", 0) for item in residuals]
            or [rmse]
        )
        if (
            rmse > IMAGE_CALIBRATION_PUBLISH_RMSE_CM
            or max_residual > IMAGE_CALIBRATION_PUBLISH_MAX_RESIDUAL_CM
        ):
            raise SpatialFrameValidationError(
                "calibration_residual_too_high",
                f"标定误差超过发布门槛（RMSE {rmse:.2f} cm，最大 {max_residual:.2f} cm）",
            )
        if not current.get("ue_level"):
            raise SpatialFrameValidationError("ue_level_required", "发布前必须填写绑定的 UE Level")

        fingerprint_material = {
            "image_sha256": (current.get("image") or {}).get("sha256"),
            "anchors": anchors,
            "to_canonical": current.get("to_canonical"),
            "floor": current.get("floor"),
            "floor_id": current.get("floor_id"),
            "floor_reference": reference,
            "bound_ue_project_id": current.get("bound_ue_project_id"),
            "ue_level": current.get("ue_level"),
        }
        serialized = json.dumps(fingerprint_material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fingerprint = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        published = copy.deepcopy(current)
        published.update({
            "status": "published",
            "calibration_revision": int(current.get("calibration_revision") or 0) + 1,
            "calibration_fingerprint": fingerprint,
            "published_at": _utc_now(),
            "updated_at": _utc_now(),
        })

        def update(working):
            frames = working.setdefault("frames", [])
            for index, frame in enumerate(frames):
                if frame.get("id") == frame_id:
                    actual = int(frame.get("draft_revision") or 0)
                    if expected is not None and actual != int(expected):
                        raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
                    frames[index] = copy.deepcopy(published)
                    break
            else:
                raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
            profile = working.setdefault("spatial_profile", {})
            floors = profile.setdefault("floor_table", [])
            target = None
            for item in floors:
                if item.get("floor_id") == published.get("floor_id") or item.get("floor") == published.get("floor"):
                    target = item
                    break
            if target is None:
                raise SpatialFrameValidationError(
                    "floor_not_configured", "发布前请先保存该楼层的空间配置"
                )
            target["floor_id"] = published.get("floor_id")
            target["ue_ground_z_cm"] = reference.get("ue_ground_z_cm")
            target["ue_level"] = published.get("ue_level")

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "frame": self._public_frame(published)}

    def _publish_cad(self, project, current, payload, expected_project_id=None):
        expected = payload.get("expected_draft_revision")
        if expected is not None and int(expected) != int(current.get("draft_revision") or 0):
            raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
        configured_floor = _find_floor(project, current.get("floor"), current.get("floor_id"))
        if configured_floor is None:
            raise SpatialFrameValidationError(
                "floor_not_configured", "发布前请先保存该楼层的空间配置"
            )
        finite_number(configured_floor.get("z_base_mm"), "floor.z_base_mm")
        anchors = current.get("anchors") or []
        ensure_non_collinear(anchors, "source_xy_mm")
        if not current.get("to_ue") or not current.get("to_canonical"):
            raise SpatialFrameValidationError("frame_not_calibrated", "请先保存有效的标定草稿")
        source_to_ue = (current.get("to_ue") or {}).get("matrix")
        if not source_to_ue or invert_affine(source_to_ue) is None:
            raise SpatialFrameValidationError("calibration_matrix_singular", "标定矩阵不可逆，请重新选择锚点")
        metrics = ((current.get("transform") or {}).get("metrics") or {})
        rmse = finite_number(metrics.get("rmse_cm"), "metrics.rmse_cm", 0)
        if rmse >= CAD_CALIBRATION_PUBLISH_RMSE_CM:
            raise SpatialFrameValidationError(
                "calibration_residual_too_high",
                f"标定误差超过发布门槛（RMSE {rmse:.2f} cm）",
            )

        fingerprint_material = {
            "cad_sha256": (current.get("cad") or {}).get("sha256"),
            "anchors": anchors,
            "to_ue": current.get("to_ue"),
            "to_canonical": current.get("to_canonical"),
            "canonical_origin": current.get("canonical_origin"),
            "display": current.get("display"),
            "floor": current.get("floor"),
            "floor_id": current.get("floor_id"),
            "bound_ue_project_id": current.get("bound_ue_project_id"),
            "ue_level": current.get("ue_level"),
        }
        serialized = json.dumps(fingerprint_material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fingerprint = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        published = copy.deepcopy(current)
        published.update({
            "status": "published",
            "calibration_revision": int(current.get("calibration_revision") or 0) + 1,
            "calibration_fingerprint": fingerprint,
            "published_at": _utc_now(),
            "updated_at": _utc_now(),
        })
        origin = (published.get("canonical_origin") or [0.0, 0.0])[:2]
        a, b, tx = source_to_ue[0]
        c, d, ty = source_to_ue[1]
        canonical_to_ue = [
            [a, b, a * float(origin[0]) + b * float(origin[1]) + tx],
            [c, d, c * float(origin[0]) + d * float(origin[1]) + ty],
            [0.0, 0.0, 1.0],
        ]

        def update(working):
            frames = working.setdefault("frames", [])
            for index, frame in enumerate(frames):
                if frame.get("id") == current.get("id"):
                    actual = int(frame.get("draft_revision") or 0)
                    if expected is not None and actual != int(expected):
                        raise SpatialFrameConflictError("空间底图草稿已被更新，请刷新后继续")
                    frames[index] = copy.deepcopy(published)
                    break
            else:
                raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")

            profile = working.setdefault("spatial_profile", {})
            profile["canonical_origin"] = copy.deepcopy(origin)
            ue_transform = profile.setdefault("ue_transform", {})
            ue_transform["matrix"] = canonical_to_ue
            ue_transform["display"] = copy.deepcopy(published.get("display") or {})
            floors = profile.setdefault("floor_table", [])
            target = next((item for item in floors if item.get("floor_id") == published.get("floor_id")
                           or item.get("floor") == published.get("floor")), None)
            if target is None:
                raise SpatialFrameValidationError(
                    "floor_not_configured", "发布前请先保存该楼层的空间配置"
                )
            target["floor_id"] = published.get("floor_id")
            if published.get("ue_level"):
                target["ue_level"] = published.get("ue_level")

        self.store.transact_expected_active(expected_project_id, update)
        return {"status": "ok", "frame": self._public_frame(published)}

    def image_file(self, frame_id):
        project = self._project()
        frame = _find_frame(project, frame_id)
        if not frame or frame.get("kind") != "image" or not isinstance(frame.get("image"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
        image = frame.get("image") or {}
        path = self.storage.resolve_image(project.get("id"), image)
        if not os.path.isfile(path):
            raise SpatialFrameNotFoundError("空间底图文件已丢失")
        return path, image

    def source_file(self, frame_id):
        project = self._project()
        frame = _find_frame(project, frame_id)
        if not frame or frame.get("kind") != "cad" or not isinstance(frame.get("cad"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该 CAD 空间底图")
        cad = frame.get("cad") or {}
        path = self.storage.resolve_cad(project.get("id"), cad)
        if not os.path.isfile(path):
            raise SpatialFrameNotFoundError("CAD 空间底图原始文件不存在")
        return path, cad
