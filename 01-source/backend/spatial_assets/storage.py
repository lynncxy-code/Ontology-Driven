import hashlib
import os
import tempfile
import json

from .validators import (
    CAD_HEADER_BYTES,
    MAX_CAD_BYTES,
    inspect_cad,
    inspect_cad_upload,
    inspect_image,
    safe_storage_segment,
)


DEFAULT_ASSET_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "project_assets"
)


class SpatialAssetStorage:
    def __init__(self, root=None):
        self.root = os.path.realpath(root or DEFAULT_ASSET_ROOT)
        os.makedirs(self.root, exist_ok=True)

    def _project_dir(self, project_id):
        directory = os.path.realpath(os.path.join(
            self.root, safe_storage_segment(project_id), "spatial_frames"
        ))
        if os.path.commonpath([self.root, directory]) != self.root:
            raise ValueError("invalid project asset path")
        return directory

    def store_image(self, project_id, data, original_name=""):
        inspected = inspect_image(data, original_name)
        digest = hashlib.sha256(data).hexdigest()
        asset_id = "asset_" + digest[:24]
        storage_name = f"{asset_id}.{inspected['extension']}"
        directory = self._project_dir(project_id)
        os.makedirs(directory, exist_ok=True)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid image asset path")
        created = False
        if not os.path.exists(path):
            temp = path + ".tmp"
            with open(temp, "wb") as handle:
                handle.write(data)
            os.replace(temp, path)
            created = True
        return {
            "asset_id": asset_id,
            "sha256": digest,
            "width_px": inspected["width_px"],
            "height_px": inspected["height_px"],
            "mime_type": inspected["mime_type"],
            "storage_name": storage_name,
            "original_name": os.path.basename(str(original_name or "")),
        }, path, created

    def store_cad(self, project_id, data, original_name=""):
        inspected = inspect_cad(data, original_name)
        digest = hashlib.sha256(data).hexdigest()
        asset_id = "asset_" + digest[:24]
        storage_name = f"{asset_id}.{inspected['extension']}"
        directory = self._project_dir(project_id)
        os.makedirs(directory, exist_ok=True)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid CAD asset path")
        created = False
        if not os.path.exists(path):
            temp = path + ".tmp"
            with open(temp, "wb") as handle:
                handle.write(data)
            os.replace(temp, path)
            created = True
        return {
            "asset_id": asset_id,
            "sha256": digest,
            "size_bytes": inspected["size_bytes"],
            "mime_type": inspected["mime_type"],
            "storage_name": storage_name,
            "original_name": os.path.basename(str(original_name or "")),
        }, path, created

    def store_cad_stream(self, project_id, stream, original_name=""):
        directory = self._project_dir(project_id)
        os.makedirs(directory, exist_ok=True)
        temp_path = None
        try:
            digest = hashlib.sha256()
            header = bytearray()
            size_bytes = 0
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".cad-upload-", suffix=".tmp",
                dir=directory, delete=False,
            ) as handle:
                temp_path = handle.name
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if size_bytes > MAX_CAD_BYTES:
                        inspect_cad_upload(header, size_bytes, original_name)
                    if len(header) < CAD_HEADER_BYTES:
                        remaining = CAD_HEADER_BYTES - len(header)
                        header.extend(chunk[:remaining])
                    digest.update(chunk)
                    handle.write(chunk)

            inspected = inspect_cad_upload(header, size_bytes, original_name)
            digest_hex = digest.hexdigest()
            asset_id = "asset_" + digest_hex[:24]
            storage_name = f"{asset_id}.{inspected['extension']}"
            path = os.path.realpath(os.path.join(directory, storage_name))
            if os.path.commonpath([directory, path]) != directory:
                raise ValueError("invalid CAD asset path")
            created = not os.path.exists(path)
            if created:
                os.replace(temp_path, path)
            else:
                os.remove(temp_path)
            temp_path = None
            return {
                "asset_id": asset_id,
                "sha256": digest_hex,
                "size_bytes": inspected["size_bytes"],
                "mime_type": inspected["mime_type"],
                "storage_name": storage_name,
                "original_name": os.path.basename(str(original_name or "")),
            }, path, created
        finally:
            if temp_path and os.path.isfile(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def resolve_image(self, project_id, image_metadata):
        storage_name = safe_storage_segment((image_metadata or {}).get("storage_name"))
        directory = self._project_dir(project_id)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid image asset path")
        return path

    def resolve_cad(self, project_id, cad_metadata):
        storage_name = safe_storage_segment((cad_metadata or {}).get("storage_name"))
        directory = self._project_dir(project_id)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid CAD asset path")
        return path

    def type_scan_cache_path(self, project_id, frame_id, source_sha256):
        """Return a safe, rebuildable path outside the ProjectStore JSON."""
        directory = os.path.realpath(os.path.join(
            self._project_dir(project_id), "type_scan_cache"
        ))
        os.makedirs(directory, exist_ok=True)
        safe_frame = safe_storage_segment(frame_id)
        safe_sha = safe_storage_segment(source_sha256)
        path = os.path.realpath(os.path.join(directory, f"{safe_frame}_{safe_sha}.json"))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid type scan cache path")
        return path

    def read_type_scan_cache(self, project_id, frame_id, source_sha256):
        path = self.type_scan_cache_path(project_id, frame_id, source_sha256)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, dict) else None
        except (OSError, ValueError):
            return None

    def write_type_scan_cache(self, project_id, frame_id, source_sha256, value):
        path = self.type_scan_cache_path(project_id, frame_id, source_sha256)
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temp, path)
        return path

    @staticmethod
    def remove_if_created(path, created):
        if created and path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
