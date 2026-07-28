import itertools
import math
import os


MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_DIMENSION = 30000
MAX_ANCHORS = 64


class SpatialFrameValidationError(ValueError):
    def __init__(self, code, message, status=422, fields=None):
        self.code = code
        self.status = status
        self.fields = fields or []
        super().__init__(message)


def finite_number(value, path, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 必须是数字",
            fields=[{"path": path, "message": "必须是数字"}],
        )
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 必须是数字",
            fields=[{"path": path, "message": "必须是数字"}],
        ) from exc
    if not math.isfinite(number):
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 必须是有限数字",
            fields=[{"path": path, "message": "必须是有限数字"}],
        )
    if minimum is not None and number < minimum:
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 不能小于 {minimum}",
            fields=[{"path": path, "message": f"不能小于 {minimum}"}],
        )
    if maximum is not None and number > maximum:
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 不能大于 {maximum}",
            fields=[{"path": path, "message": f"不能大于 {maximum}"}],
        )
    return number


def positive_int(value, path, default=1):
    if value in (None, ""):
        return default
    number = finite_number(value, path, 1, 10000)
    if int(number) != number:
        raise SpatialFrameValidationError(
            "spatial_frame_validation_failed", f"{path} 必须是整数",
            fields=[{"path": path, "message": "必须是整数"}],
        )
    return int(number)


def clean_name(value, fallback, maximum=120):
    name = str(value or "").strip() or fallback
    if len(name) > maximum:
        raise SpatialFrameValidationError("name_too_long", f"名称不能超过 {maximum} 个字符")
    return name


def safe_storage_segment(value):
    text = str(value or "")
    cleaned = "".join(ch for ch in text if ch.isascii() and (ch.isalnum() or ch in "-_."))
    return cleaned or "project"


def _png_dimensions(data):
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"), "png", "image/png"
    return None


def _jpeg_dimensions(data):
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    offset = 2
    while offset + 8 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in sof_markers and length >= 7:
            height = int.from_bytes(data[offset + 3:offset + 5], "big")
            width = int.from_bytes(data[offset + 5:offset + 7], "big")
            return width, height, "jpg", "image/jpeg"
        offset += length
    return None


def _webp_dimensions(data):
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height, "webp", "image/webp"
    if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        b0, b1, b2, b3 = data[21:25]
        width = 1 + b0 + ((b1 & 0x3F) << 8)
        height = 1 + ((b1 & 0xC0) >> 6) + (b2 << 2) + ((b3 & 0x0F) << 10)
        return width, height, "webp", "image/webp"
    if chunk == b"VP8 ":
        signature = data.find(b"\x9d\x01\x2a", 20)
        if signature >= 0 and signature + 7 <= len(data):
            width = int.from_bytes(data[signature + 3:signature + 5], "little") & 0x3FFF
            height = int.from_bytes(data[signature + 5:signature + 7], "little") & 0x3FFF
            return width, height, "webp", "image/webp"
    return None


def inspect_image(data, original_name=""):
    if not data:
        raise SpatialFrameValidationError("image_empty", "图片文件为空", status=400)
    if len(data) > MAX_IMAGE_BYTES:
        raise SpatialFrameValidationError("image_too_large", "图片不能超过 20 MB", status=413)
    info = _png_dimensions(data) or _jpeg_dimensions(data) or _webp_dimensions(data)
    if not info:
        extension = os.path.splitext(str(original_name or ""))[1].lower()
        raise SpatialFrameValidationError(
            "image_format_unsupported",
            f"无法识别图片内容（{extension or '未知格式'}）；仅支持 PNG、JPEG、WebP",
            status=415,
        )
    width, height, extension, mime_type = info
    if width <= 0 or height <= 0 or width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise SpatialFrameValidationError("image_dimensions_invalid", "图片尺寸无效或超过 30000 像素")
    return {
        "width_px": width,
        "height_px": height,
        "extension": extension,
        "mime_type": mime_type,
    }


def normalize_anchors(value):
    if not isinstance(value, list):
        raise SpatialFrameValidationError("anchors_invalid", "anchors 必须是数组")
    if len(value) > MAX_ANCHORS:
        raise SpatialFrameValidationError("anchors_too_many", f"标定锚点不能超过 {MAX_ANCHORS} 个")
    result = []
    ids = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise SpatialFrameValidationError("anchor_invalid", f"第 {index + 1} 个锚点必须是对象")
        anchor_id = str(item.get("id") or f"anchor-{index + 1}").strip()
        if not anchor_id or anchor_id in ids:
            raise SpatialFrameValidationError("anchor_id_invalid", "锚点 ID 不能为空或重复")
        ids.add(anchor_id)
        source = item.get("source_px")
        world = item.get("ue_world_cm")
        if not isinstance(source, (list, tuple)) or len(source) != 2:
            raise SpatialFrameValidationError("anchor_source_invalid", f"第 {index + 1} 个锚点缺少图片坐标")
        if not isinstance(world, (list, tuple)) or len(world) != 3:
            raise SpatialFrameValidationError("anchor_world_invalid", f"第 {index + 1} 个锚点缺少 UE XYZ")
        result.append({
            "id": anchor_id,
            "source_px": [
                finite_number(source[0], f"anchors[{index}].source_px[0]"),
                finite_number(source[1], f"anchors[{index}].source_px[1]"),
            ],
            "ue_world_cm": [
                finite_number(world[0], f"anchors[{index}].ue_world_cm[0]"),
                finite_number(world[1], f"anchors[{index}].ue_world_cm[1]"),
                finite_number(world[2], f"anchors[{index}].ue_world_cm[2]"),
            ],
        })
    return result


def ensure_non_collinear(anchors):
    if len(anchors) < 3:
        raise SpatialFrameValidationError("anchors_insufficient", "发布至少需要 3 个标定锚点")
    points = [item["source_px"] for item in anchors]
    span = max(
        max(point[0] for point in points) - min(point[0] for point in points),
        max(point[1] for point in points) - min(point[1] for point in points),
        1.0,
    )
    threshold = span * span * 1e-6
    for a, b, c in itertools.combinations(points, 3):
        twice_area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if twice_area > threshold:
            return
    raise SpatialFrameValidationError("anchors_collinear", "标定锚点近似共线，无法确定二维平面变换")
