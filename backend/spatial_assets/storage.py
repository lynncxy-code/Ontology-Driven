import hashlib
import os

from .validators import inspect_image, safe_storage_segment


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

    def resolve_image(self, project_id, image_metadata):
        storage_name = safe_storage_segment((image_metadata or {}).get("storage_name"))
        directory = self._project_dir(project_id)
        path = os.path.realpath(os.path.join(directory, storage_name))
        if os.path.commonpath([directory, path]) != directory:
            raise ValueError("invalid image asset path")
        return path

    @staticmethod
    def remove_if_created(path, created):
        if created and path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
