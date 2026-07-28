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
    normalize_anchors,
    positive_int,
)


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
        return value

    def list_frames(self):
        project = self._project()
        frames = [
            self._public_frame(frame) for frame in project.get("frames") or []
            if isinstance(frame, dict) and frame.get("kind") == "image" and isinstance(frame.get("image"), dict)
        ]
        return {"project_id": project.get("id"), "frames": frames}

    def get_frame(self, frame_id):
        project = self._project()
        frame = _find_frame(project, frame_id)
        if not frame or frame.get("kind") != "image" or not isinstance(frame.get("image"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
        return self._public_frame(frame)

    def create_image_frame(self, file_storage, fields):
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
            self.store.transact_active(update)
        except Exception:
            self.storage.remove_if_created(path, created)
            raise
        return {"status": "ok", "frame": self._public_frame(frame)}

    def save_draft(self, frame_id, payload):
        if not isinstance(payload, dict):
            raise SpatialFrameValidationError("invalid_request", "请求体必须是对象", status=400)
        project = self._project()
        current = _find_frame(project, frame_id)
        if not current or current.get("kind") != "image" or not isinstance(current.get("image"), dict):
            raise SpatialFrameNotFoundError("当前项目中找不到该空间底图")
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

        self.store.transact_active(update)
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

    def publish(self, frame_id, payload):
        payload = payload if isinstance(payload, dict) else {}
        project = self._project()
        current = _find_frame(project, frame_id)
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
        if rmse > 20.0 or max_residual > 50.0:
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
                target = {
                    "floor": published.get("floor"),
                    "floor_id": published.get("floor_id"),
                    "z_base_mm": reference.get("canonical_z_base_mm", 0.0),
                    "map_codes": [],
                }
                floors.append(target)
            target["floor_id"] = published.get("floor_id")
            target["ue_ground_z_cm"] = reference.get("ue_ground_z_cm")
            target["ue_level"] = published.get("ue_level")

        self.store.transact_active(update)
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
