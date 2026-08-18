"""Content-addressed project storage for generated narration WAV files."""

import hashlib
import io
import os
import re
import wave


DEFAULT_ASSET_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "project_assets"
)
MAX_WAV_BYTES = 10 * 1024 * 1024
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")


class NarrationAssetError(ValueError):
    code = "narration_asset_invalid"

    def __init__(self, message, code=None):
        if code:
            self.code = code
        super().__init__(message)


def safe_segment(value):
    value = str(value or "")
    if not value or not _SAFE_SEGMENT.fullmatch(value) or value in {".", ".."}:
        raise NarrationAssetError("非法的项目音频资产标识", "narration_asset_path_invalid")
    return value


def inspect_wav(data):
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise NarrationAssetError("语音服务没有返回音频数据")
    data = bytes(data)
    if len(data) > MAX_WAV_BYTES:
        raise NarrationAssetError("单段语音超过 10 MB 限制")
    try:
        with wave.open(io.BytesIO(data), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            sample_rate = handle.getframerate()
            declared_frame_count = handle.getnframes()
            compression = handle.getcomptype()
            frame_bytes = handle.readframes(declared_frame_count)
    except (EOFError, wave.Error) as exc:
        raise NarrationAssetError("语音服务返回的 WAV 文件无法解析") from exc
    if compression != "NONE" or sample_width != 2:
        raise NarrationAssetError("WAV 必须是 16-bit PCM")
    if channels != 1:
        raise NarrationAssetError("WAV 必须是单声道")
    if sample_rate not in {8000, 16000}:
        raise NarrationAssetError("WAV 采样率必须是 8000 或 16000 Hz")
    bytes_per_frame = channels * sample_width
    frame_count = len(frame_bytes) // bytes_per_frame
    duration = frame_count / float(sample_rate or 1)
    if duration < 0.2 or duration > 120.0:
        raise NarrationAssetError("WAV 时长必须在 0.2–120 秒之间")
    return {
        "mime_type": "audio/wav",
        "sample_rate": sample_rate,
        "channels": channels,
        "bits_per_sample": sample_width * 8,
        "duration_sec": round(duration, 3),
        "size_bytes": len(data),
    }


class NarrationAssetStorage:
    def __init__(self, root=None):
        self.root = os.path.realpath(root or DEFAULT_ASSET_ROOT)
        os.makedirs(self.root, exist_ok=True)

    def _project_dir(self, project_id):
        directory = os.path.realpath(os.path.join(
            self.root, safe_segment(project_id), "narration_audio"
        ))
        if os.path.commonpath([self.root, directory]) != self.root:
            raise NarrationAssetError("非法的项目音频目录", "narration_asset_path_invalid")
        return directory

    def store_wav(self, project_id, data):
        inspected = inspect_wav(data)
        digest = hashlib.sha256(data).hexdigest()
        asset_id = "narration_" + digest[:24]
        storage_name = f"{asset_id}.wav"
        directory = self._project_dir(project_id)
        os.makedirs(directory, exist_ok=True)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise NarrationAssetError("非法的项目音频路径", "narration_asset_path_invalid")
        created = False
        if not os.path.exists(path):
            temporary = path + ".tmp"
            with open(temporary, "wb") as handle:
                handle.write(data)
            os.replace(temporary, path)
            created = True
        metadata = {
            "asset_id": asset_id,
            "sha256": digest,
            "storage_name": storage_name,
            **inspected,
        }
        return metadata, path, created

    def resolve(self, project_id, metadata):
        storage_name = safe_segment((metadata or {}).get("storage_name"))
        directory = self._project_dir(project_id)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise NarrationAssetError("非法的项目音频路径", "narration_asset_path_invalid")
        return path

    def exists(self, project_id, metadata):
        try:
            return os.path.isfile(self.resolve(project_id, metadata))
        except NarrationAssetError:
            return False

    @staticmethod
    def remove_if_created(path, created):
        if created and path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
