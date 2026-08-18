"""Authoring and runtime helpers for route waypoint narration (OntoTwin 4.0.3)."""

import copy
import hashlib
import json
import math
import re
import unicodedata


LANGUAGE = "zh-CN"
SEGMENTATION_VERSION = "zh-punct-v1"
MAX_TEXT_CHARS = 4000
MAX_TTS_CHARS = 280
VALID_MODES = {"subtitle", "voice", "subtitle_voice"}
VOICE_MODES = {"voice", "subtitle_voice"}

DEFAULT_NARRATION_SETTINGS = {
    "language": LANGUAGE,
    "provider_id": "alibaba.isi.standard",
    "voice_id": "xiaoyun",
    "speech_rate": 0,
    "pitch_rate": 0,
    "volume": 50,
    "trigger_radius_cm": 100.0,
}

_STRONG_END = set("。！？!?；;\n")
_WEAK_END = set("，,、：:")


def _error(errors, path, message):
    errors.append({"path": path, "message": message})


def normalize_text(value):
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _split_piece(piece, limit=MAX_TTS_CHARS, target=60):
    result = []
    remaining = piece.strip()
    while remaining:
        if len(remaining) <= target:
            result.append(remaining)
            break
        ceiling = min(len(remaining), limit)
        floor = min(max(20, target // 2), ceiling)
        split_at = None
        for markers in (_STRONG_END, _WEAK_END):
            for index in range(ceiling - 1, floor - 2, -1):
                if remaining[index] in markers:
                    split_at = index + 1
                    break
            if split_at:
                break
        if not split_at:
            split_at = min(target, ceiling)
        result.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return [item for item in result if item]


def split_text(text, manual_break_offsets=None):
    """Return deterministic subtitle/TTS segments without dropping characters."""
    normalized = normalize_text(text)
    offsets = sorted({
        int(value) for value in (manual_break_offsets or [])
        if not isinstance(value, bool) and isinstance(value, (int, float))
        and int(value) == value and 0 < int(value) < len(normalized)
    })
    pieces = []
    start = 0
    for offset in offsets + [len(normalized)]:
        piece = normalized[start:offset]
        if piece.strip():
            pieces.extend(_split_piece(piece))
        start = offset
    return pieces


def estimated_duration(text):
    visible = len(re.sub(r"\s+", "", text or ""))
    return round(max(2.5, min(12.0, visible / 4.0 + 0.8)), 3)


def _number(value, path, errors, minimum, maximum, integer=False, nullable=False):
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error(errors, path, "必须是数值")
        return None
    number = float(value)
    if not math.isfinite(number) or number < minimum or number > maximum:
        _error(errors, path, f"必须在 {minimum}–{maximum} 之间")
        return None
    return int(number) if integer else round(number, 3)


def normalize_project_defaults(raw, errors=None, path="narration_defaults"):
    errors = errors if errors is not None else []
    value = copy.deepcopy(DEFAULT_NARRATION_SETTINGS)
    if isinstance(raw, dict):
        value.update({key: raw.get(key) for key in value if raw.get(key) is not None})
    if str(value.get("language") or "") != LANGUAGE:
        _error(errors, f"{path}.language", "4.0.3 仅支持 zh-CN")
    value["language"] = LANGUAGE
    provider = str(value.get("provider_id") or "").strip()
    voice = str(value.get("voice_id") or "").strip()
    if not provider:
        _error(errors, f"{path}.provider_id", "缺少语音服务标识")
    if not voice or len(voice) > 80:
        _error(errors, f"{path}.voice_id", "音色标识必须为 1–80 个字符")
    value["provider_id"] = provider
    value["voice_id"] = voice
    value["speech_rate"] = _number(value.get("speech_rate"), f"{path}.speech_rate", errors, -500, 500, True)
    value["pitch_rate"] = _number(value.get("pitch_rate"), f"{path}.pitch_rate", errors, -500, 500, True)
    value["volume"] = _number(value.get("volume"), f"{path}.volume", errors, 0, 100, True)
    value["trigger_radius_cm"] = _number(
        value.get("trigger_radius_cm"), f"{path}.trigger_radius_cm", errors, 30, 500
    )
    return value


def normalize_route_profile(raw, errors, path="narration_profile"):
    raw = raw if isinstance(raw, dict) else {}
    inherit = raw.get("inherit_project", True)
    if not isinstance(inherit, bool):
        _error(errors, f"{path}.inherit_project", "必须是布尔值")
        inherit = True
    result = {"inherit_project": inherit}
    validators = {
        "speech_rate": (-500, 500, True),
        "pitch_rate": (-500, 500, True),
        "volume": (0, 100, True),
        "trigger_radius_cm": (30, 500, False),
    }
    voice = raw.get("voice_id")
    if voice is not None:
        voice = str(voice).strip()
        if not voice or len(voice) > 80:
            _error(errors, f"{path}.voice_id", "音色标识必须为 1–80 个字符")
        else:
            result["voice_id"] = voice
    for key, (minimum, maximum, integer) in validators.items():
        if raw.get(key) is not None:
            result[key] = _number(raw.get(key), f"{path}.{key}", errors, minimum, maximum, integer)
    return result


def effective_voice_profile(project_defaults, route_profile):
    errors = []
    result = normalize_project_defaults(project_defaults, errors)
    route_profile = route_profile if isinstance(route_profile, dict) else {}
    for key in ("voice_id", "speech_rate", "pitch_rate", "volume", "trigger_radius_cm"):
        if route_profile.get(key) is not None:
            result[key] = route_profile[key]
    result["audio_format"] = "wav"
    result["sample_rate"] = 16000
    return result


def content_digest(text, breaks, profile):
    material = {
        "text": normalize_text(text),
        "manual_break_offsets": list(breaks or []),
        "segmentation_version": SEGMENTATION_VERSION,
        "language": LANGUAGE,
        "provider_id": profile.get("provider_id"),
        "voice_id": profile.get("voice_id"),
        "speech_rate": profile.get("speech_rate"),
        "pitch_rate": profile.get("pitch_rate"),
        "volume": profile.get("volume"),
        "audio_format": "wav",
        "sample_rate": 16000,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_waypoint_narration(raw, current, effective_profile, errors, path):
    if raw is None:
        return None
    if not isinstance(raw, dict):
        _error(errors, path, "点位解说必须是对象")
        return None
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        _error(errors, f"{path}.enabled", "必须是布尔值")
        enabled = True
    if not enabled:
        return {"enabled": False}

    mode = str(raw.get("mode") or "subtitle").strip()
    if mode not in VALID_MODES:
        _error(errors, f"{path}.mode", "必须是 subtitle、voice 或 subtitle_voice")
        mode = "subtitle"
    language = str(raw.get("language") or LANGUAGE)
    if language != LANGUAGE:
        _error(errors, f"{path}.language", "4.0.3 仅支持 zh-CN")
        language = LANGUAGE
    text = normalize_text(raw.get("text"))
    if not text:
        _error(errors, f"{path}.text", "请填写解说词")
    elif len(text) > MAX_TEXT_CHARS:
        _error(errors, f"{path}.text", f"解说词不能超过 {MAX_TEXT_CHARS} 个字符")

    raw_breaks = raw.get("manual_break_offsets") or []
    if not isinstance(raw_breaks, list):
        _error(errors, f"{path}.manual_break_offsets", "分页断点必须是数组")
        raw_breaks = []
    breaks = []
    for index, value in enumerate(raw_breaks):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            _error(errors, f"{path}.manual_break_offsets[{index}]", "断点必须是整数")
            continue
        offset = int(value)
        if offset <= 0 or offset >= len(text):
            _error(errors, f"{path}.manual_break_offsets[{index}]", "断点超出文本范围")
            continue
        breaks.append(offset)
    breaks = sorted(set(breaks))

    duration_mode = str(raw.get("duration_mode") or "auto")
    if duration_mode not in {"auto", "manual"}:
        _error(errors, f"{path}.duration_mode", "必须是 auto 或 manual")
        duration_mode = "auto"
    duration_sec = None
    if duration_mode == "manual":
        duration_sec = _number(raw.get("duration_sec"), f"{path}.duration_sec", errors, 1, 600)
    trigger_radius = None
    if raw.get("trigger_radius_cm") is not None:
        trigger_radius = _number(
            raw.get("trigger_radius_cm"), f"{path}.trigger_radius_cm", errors, 30, 500
        )

    texts = split_text(text, breaks) if text else []
    digest = content_digest(text, breaks, effective_profile)
    previous = current if isinstance(current, dict) and current.get("content_digest") == digest else {}
    previous_by_order = {
        int(item.get("order") or 0): item for item in previous.get("segments") or []
        if isinstance(item, dict)
    }
    automatic = [estimated_duration(item) for item in texts]
    if duration_mode == "manual" and duration_sec and texts:
        weights = [max(1, len(re.sub(r"\s+", "", item))) for item in texts]
        total_weight = sum(weights)
        durations = [max(1.0, duration_sec * weight / total_weight) for weight in weights]
    else:
        durations = automatic

    segments = []
    for index, segment_text in enumerate(texts, 1):
        previous_segment = previous_by_order.get(index) or {}
        value = {
            "segment_id": f"seg-{digest[7:19]}-{index}",
            "order": index,
            "text": segment_text,
            "duration_sec": round(durations[index - 1], 3),
        }
        if (
            mode in VOICE_MODES
            and previous_segment.get("text") == segment_text
            and previous_segment.get("audio_asset_id")
            and previous_segment.get("audio_sha256")
        ):
            for key in ("audio_asset_id", "audio_sha256", "audio_duration_sec"):
                value[key] = previous_segment.get(key)
        segments.append(value)

    has_all_audio = bool(segments) and all(item.get("audio_asset_id") for item in segments)
    result = {
        "enabled": True,
        "mode": mode,
        "language": language,
        "text": text,
        "manual_break_offsets": breaks,
        "duration_mode": duration_mode,
        "duration_sec": duration_sec,
        "trigger_radius_cm": trigger_radius,
        "segmentation_version": SEGMENTATION_VERSION,
        "content_digest": digest,
        "generation_state": (
            "not_required" if mode == "subtitle" else "available" if has_all_audio else "pending"
        ),
        "segments": segments,
    }
    if previous and previous.get("last_generation"):
        result["last_generation"] = copy.deepcopy(previous["last_generation"])
    return result


def runtime_narration(narration, route_trigger_radius):
    if not isinstance(narration, dict) or not narration.get("enabled"):
        return None
    segments = []
    for item in narration.get("segments") or []:
        if not isinstance(item, dict) or not item.get("text"):
            continue
        segment = {
            "segment_id": str(item.get("segment_id") or ""),
            "text": str(item.get("text")),
            "duration_sec": float(item.get("duration_sec") or estimated_duration(item.get("text"))),
        }
        for key in ("audio_asset_id", "audio_sha256", "audio_duration_sec"):
            if item.get(key) is not None:
                segment[key] = item.get(key)
        segments.append(segment)
    if not segments:
        return None
    return {
        "mode": narration.get("mode") or "subtitle",
        "audio_state": narration.get("generation_state") or "pending",
        "trigger_radius_cm": float(narration.get("trigger_radius_cm") or route_trigger_radius or 100.0),
        "segments": segments,
    }
