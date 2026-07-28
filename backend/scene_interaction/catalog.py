import copy
import hashlib
import json
import os
import threading


DEFAULT_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "resource_catalog.json")


class CatalogValidationError(ValueError):
    pass


class ResourceCatalog:
    KINDS = ("characters", "skins", "spawn_anchors", "routes", "god_cameras")

    def __init__(self, path=None):
        self.path = path or DEFAULT_CATALOG_PATH
        self._lock = threading.RLock()
        self._mtime_ns = None
        self._snapshot = None
        self._indexes = {}

    @staticmethod
    def _validate(raw):
        if not isinstance(raw, dict):
            raise CatalogValidationError("resource catalog must be an object")
        normalized = copy.deepcopy(raw)
        for kind in ResourceCatalog.KINDS:
            items = normalized.get(kind, [])
            if not isinstance(items, list):
                raise CatalogValidationError(f"catalog.{kind} must be an array")
            seen = set()
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    raise CatalogValidationError(f"catalog.{kind}[{index}] must be an object")
                resource_id = str(item.get("id") or "").strip()
                if not resource_id:
                    raise CatalogValidationError(f"catalog.{kind}[{index}].id is required")
                if resource_id in seen:
                    raise CatalogValidationError(f"duplicate catalog id: {resource_id}")
                seen.add(resource_id)
                item["id"] = resource_id
                item["display_name"] = str(item.get("display_name") or resource_id)
        version = str(normalized.get("catalog_version") or "").strip()
        if not version:
            payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            version = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        normalized["catalog_version"] = version
        return normalized

    def _load(self):
        try:
            stat = os.stat(self.path)
        except OSError as exc:
            raise CatalogValidationError(f"resource catalog is unavailable: {self.path}") from exc
        if self._snapshot is not None and self._mtime_ns == stat.st_mtime_ns:
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        snapshot = self._validate(raw)
        indexes = {
            kind: {item["id"]: item for item in snapshot.get(kind, [])}
            for kind in self.KINDS
        }
        self._snapshot = snapshot
        self._indexes = indexes
        self._mtime_ns = stat.st_mtime_ns

    def snapshot(self):
        with self._lock:
            self._load()
            return copy.deepcopy(self._snapshot)

    @property
    def version(self):
        return self.snapshot()["catalog_version"]

    def get(self, kind, resource_id):
        with self._lock:
            self._load()
            value = self._indexes.get(kind, {}).get(resource_id)
            return copy.deepcopy(value) if value else None

    def require(self, kind, resource_id):
        value = self.get(kind, resource_id)
        if value is None:
            raise CatalogValidationError(f"catalog resource not found: {kind}/{resource_id}")
        return value
