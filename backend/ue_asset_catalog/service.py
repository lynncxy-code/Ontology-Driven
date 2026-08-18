import copy
import datetime
import difflib
import hashlib
import json
import math
import os
import re
import threading
import unicodedata


_DEFAULT_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ue_asset_catalogs")
_SUPPORTED_KINDS = {"StaticMesh"}
_MAX_ASSETS = 10000
_MAX_ITEMS = 2000
_MAX_THUMBNAIL_CHARS = 512 * 1024


class AssetCatalogError(RuntimeError):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code = code
        self.status = status


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_text(value):
    value = unicodedata.normalize("NFKC", str(value or "")).lower()
    value = value.replace("\\", "/")
    value = re.sub(r"(^|[/_.\-])(sm|sk|bp|mesh|staticmesh)(?=[/_.\-])", " ", value)
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value)


def _tokens(value):
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    raw = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text)
    ignored = {"sm", "sk", "bp", "mesh", "static", "staticmesh", "game", "art", "asset", "assets"}
    return {part for part in raw if part and part not in ignored}


def _kind(value):
    tail = str(value or "").rsplit(".", 1)[-1].lower()
    if tail == "staticmesh":
        return "StaticMesh"
    if tail == "skeletalmesh":
        return "SkeletalMesh"
    if tail in {"blueprint", "widgetblueprint", "animblueprint"} or tail.endswith("blueprint"):
        return "Blueprint"
    return str(value or "Unknown").rsplit(".", 1)[-1] or "Unknown"


def _safe_size(value):
    if not isinstance(value, dict):
        return None
    result = {}
    for key in ("x", "y", "z"):
        try:
            number = float(value.get(key) or 0)
        except (TypeError, ValueError):
            number = 0
        if math.isfinite(number) and number > 0:
            result[key] = round(number, 4)
    return result or None


def _safe_thumbnail(value):
    value = str(value or "")
    if not value or len(value) > _MAX_THUMBNAIL_CHARS:
        return ""
    if not (value.startswith("data:image/png;base64,") or value.startswith("data:image/jpeg;base64,")):
        return ""
    return value


def _overlap(left, right):
    if not left or not right:
        return None
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _name_score(item, asset):
    sources = [item.get("block_name"), item.get("name")]
    targets = [asset.get("asset_name"), asset.get("display_name")]
    best = 0.0
    for source in sources:
        left = _normalized_text(source)
        if not left:
            continue
        for target in targets:
            right = _normalized_text(target)
            if not right:
                continue
            score = difflib.SequenceMatcher(None, left, right).ratio()
            if left == right:
                score = 1.0
            elif min(len(left), len(right)) >= 4 and (left in right or right in left):
                score = max(score, 0.86)
            best = max(best, score)
    return best


def _dimension_score(cad_size, asset_size):
    if not isinstance(cad_size, dict) or not isinstance(asset_size, dict):
        return None
    left = sorted([float(v) for v in cad_size.values() if float(v) > 0], reverse=True)
    right = sorted([float(v) for v in asset_size.values() if float(v) > 0], reverse=True)
    count = min(len(left), len(right))
    if count < 2:
        return None
    errors = [abs(math.log(max(left[i], 1e-6) / max(right[i], 1e-6))) for i in range(count)]
    return math.exp(-sum(errors) / count)


class UEAssetCatalogService:
    def __init__(self, project_store, catalog_root=None):
        self.project_store = project_store
        self.catalog_root = catalog_root or os.environ.get("ONTOTWIN_UE_ASSET_CATALOG_DIR") or _DEFAULT_ROOT
        self._lock = threading.RLock()
        os.makedirs(self.catalog_root, exist_ok=True)

    def _path(self, ue_project_id):
        digest = hashlib.sha256(ue_project_id.encode("utf-8")).hexdigest()[:32]
        return os.path.join(self.catalog_root, f"{digest}.json")

    def _active_ue_project_id(self):
        dataset = self.project_store.get_active_dataset() if hasattr(self.project_store, "get_active_dataset") else None
        if not isinstance(dataset, dict):
            return ""
        return str(dataset.get("bound_ue_project_id") or "").strip()

    def _resolve_id(self, explicit=None):
        ue_project_id = str(explicit or "").strip() or self._active_ue_project_id()
        if not ue_project_id:
            raise AssetCatalogError(
                "ue_project_not_bound",
                "目标类型库尚未绑定 UE 工程；请先完成工程绑定或保持类型未绑定。",
                409,
            )
        if len(ue_project_id) > 200:
            raise AssetCatalogError("ue_project_id_invalid", "UE 工程 ID 过长")
        return ue_project_id

    def _read(self, ue_project_id, required=True):
        path = self._path(ue_project_id)
        if not os.path.exists(path):
            if required:
                raise AssetCatalogError(
                    "asset_catalog_missing",
                    "该 UE 工程尚未同步资产目录；请在 UE 的 Twin Scene Manager 执行同步。",
                    404,
                )
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, ValueError) as exc:
            raise AssetCatalogError("asset_catalog_unreadable", f"资产目录读取失败：{exc}", 500) from exc
        if value.get("ue_project_id") != ue_project_id:
            raise AssetCatalogError("asset_catalog_identity_mismatch", "资产目录工程身份不一致", 409)
        return value

    def _write(self, ue_project_id, value):
        path = self._path(ue_project_id)
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)

    @staticmethod
    def _clean_asset(raw):
        if not isinstance(raw, dict):
            return None
        object_path = str(raw.get("object_path") or raw.get("asset_path") or "").strip().replace("\\", "/")
        if not (object_path.startswith("/Game/") or object_path.startswith("/Engine/")):
            return None
        asset_kind = _kind(raw.get("asset_kind") or raw.get("asset_class"))
        asset_name = str(raw.get("asset_name") or object_path.rsplit("/", 1)[-1].split(".", 1)[0]).strip()
        folder_path = str(raw.get("folder_path") or object_path.rsplit("/", 1)[0]).strip().replace("\\", "/")
        result = {
            "object_path": object_path,
            "package_name": str(raw.get("package_name") or object_path.split(".", 1)[0]).strip(),
            "asset_name": asset_name,
            "display_name": str(raw.get("display_name") or asset_name).strip(),
            "folder_path": folder_path,
            "asset_kind": asset_kind,
            "supported": asset_kind in _SUPPORTED_KINDS,
            "size_cm": _safe_size(raw.get("size_cm")),
            "thumbnail_data_url": _safe_thumbnail(raw.get("thumbnail_data_url")),
        }
        tags = raw.get("tags")
        if isinstance(tags, list):
            result["tags"] = [str(item).strip() for item in tags[:50] if str(item).strip()]
        return result

    def replace_catalog(self, payload, request_identity=None):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        body_id = str(payload.get("ue_project_id") or "").strip()
        header_id = str((request_identity or {}).get("id") or "").strip()
        if not body_id and not header_id:
            raise AssetCatalogError("ue_project_id_required", "UE 资产目录同步必须携带工程 ID")
        if body_id and header_id and body_id != header_id:
            raise AssetCatalogError("ue_project_identity_mismatch", "请求头与目录中的 UE 工程 ID 不一致", 409)
        ue_project_id = self._resolve_id(header_id or body_id)
        raw_assets = payload.get("assets") or []
        if not isinstance(raw_assets, list):
            raise AssetCatalogError("assets_invalid", "assets 必须是数组")
        if len(raw_assets) > _MAX_ASSETS:
            raise AssetCatalogError("assets_too_many", f"单次最多同步 {_MAX_ASSETS} 个资产", 413)

        by_path = {}
        for raw in raw_assets:
            asset = self._clean_asset(raw)
            if asset:
                by_path[asset["object_path"]] = asset
        assets = sorted(by_path.values(), key=lambda item: (item["folder_path"].lower(), item["asset_name"].lower()))
        revision_seed = "\n".join(
            f'{item["object_path"]}|{item["asset_kind"]}|{json.dumps(item.get("size_cm"), sort_keys=True)}'
            for item in assets
        )
        with self._lock:
            existing = self._read(ue_project_id, required=False) or {}
            value = {
                "schema_version": 1,
                "ue_project_id": ue_project_id,
                "ue_project_name": str(payload.get("ue_project_name") or (request_identity or {}).get("name") or ue_project_id).strip(),
                "roots": [str(item).strip() for item in (payload.get("roots") or []) if str(item).strip()],
                "synced_at": _utc_now(),
                "catalog_revision": hashlib.sha256(revision_seed.encode("utf-8")).hexdigest()[:20],
                "assets": assets,
                "binding_memory": existing.get("binding_memory") or {},
            }
            self._write(ue_project_id, value)
        return self._public_catalog(value)

    @staticmethod
    def _public_catalog(value):
        result = copy.deepcopy(value)
        result["asset_count"] = len(result.get("assets") or [])
        result["supported_count"] = sum(1 for item in result.get("assets") or [] if item.get("supported"))
        result.pop("binding_memory", None)
        return result

    def get_catalog(self, ue_project_id=None):
        ue_project_id = self._resolve_id(ue_project_id)
        with self._lock:
            return self._public_catalog(self._read(ue_project_id))

    @staticmethod
    def _memory_key(item):
        return _normalized_text(item.get("block_name") or item.get("name"))

    @staticmethod
    def _rank(item, asset, remembered_path):
        if remembered_path and asset["object_path"] == remembered_path:
            return 1.0, ["该 UE 工程中曾人工确认"]
        if item.get("preset_asset_id") and asset["object_path"] == item.get("preset_asset_id"):
            return 0.9, ["命中旧版人工对应记录，仍需本次确认"]

        signals = []
        reasons = []
        name_score = _name_score(item, asset)
        signals.append((0.58, name_score))
        if name_score >= 0.8:
            reasons.append("类型名与资产名高度相似")
        elif name_score >= 0.55:
            reasons.append("类型名与资产名部分相似")

        category_tokens = _tokens(item.get("category") or item.get("primary_layer"))
        folder_tokens = _tokens(asset.get("folder_path")) | _tokens(" ".join(asset.get("tags") or []))
        category_score = _overlap(category_tokens, folder_tokens)
        if category_score is not None:
            signals.append((0.16, category_score))
            if category_score > 0:
                reasons.append("CAD 分类与 UE 目录有共同关键词")

        dimensions = _dimension_score(item.get("cad_size_cm"), asset.get("size_cm"))
        if dimensions is not None:
            signals.append((0.18, dimensions))
            if dimensions >= 0.78:
                reasons.append("CAD 与模型平面尺寸接近")

        type_tokens = _tokens(item.get("block_name")) | _tokens(item.get("name"))
        path_score = _overlap(type_tokens, folder_tokens)
        if path_score is not None:
            signals.append((0.08, path_score))
            if path_score > 0:
                reasons.append("资产路径提供了同类上下文")

        total_weight = sum(weight for weight, _ in signals) or 1.0
        score = sum(weight * value for weight, value in signals) / total_weight
        if not reasons:
            reasons.append("现有名称与目录线索较弱，请重点人工核对")
        return score, reasons

    def recommend(self, payload):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(payload.get("ue_project_id"))
        items = payload.get("items") or []
        if not isinstance(items, list):
            raise AssetCatalogError("items_invalid", "items 必须是数组")
        if len(items) > _MAX_ITEMS:
            raise AssetCatalogError("items_too_many", f"单次最多推荐 {_MAX_ITEMS} 个类型", 413)
        try:
            limit = max(1, min(10, int(payload.get("limit") or 3)))
        except (TypeError, ValueError) as exc:
            raise AssetCatalogError("limit_invalid", "limit 必须是整数") from exc

        with self._lock:
            catalog = self._read(ue_project_id)
        assets = [item for item in catalog.get("assets") or [] if item.get("supported")]
        memory = catalog.get("binding_memory") or {}
        recommendations = []
        for raw_item in items:
            item = raw_item if isinstance(raw_item, dict) else {}
            key = self._memory_key(item)
            remembered_path = (memory.get(key) or {}).get("asset_path") if key else ""
            ranked = []
            for asset in assets:
                score, reasons = self._rank(item, asset, remembered_path)
                candidate = copy.deepcopy(asset)
                candidate["score"] = round(score, 4)
                candidate["confidence"] = "high" if score >= 0.78 else ("medium" if score >= 0.56 else "low")
                candidate["reasons"] = reasons
                ranked.append(candidate)
            ranked.sort(key=lambda value: (-value["score"], value["object_path"].lower()))
            recommendations.append({
                "block_name": str(item.get("block_name") or ""),
                "candidates": ranked[:limit],
            })
        return {
            "ue_project_id": ue_project_id,
            "ue_project_name": catalog.get("ue_project_name") or ue_project_id,
            "catalog_revision": catalog.get("catalog_revision"),
            "recommendations": recommendations,
        }

    def remember_confirmations(self, payload):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(payload.get("ue_project_id"))
        selections = payload.get("selections") or []
        if not isinstance(selections, list):
            raise AssetCatalogError("selections_invalid", "selections 必须是数组")
        with self._lock:
            catalog = self._read(ue_project_id)
            supported_paths = {
                item.get("object_path") for item in catalog.get("assets") or [] if item.get("supported")
            }
            memory = catalog.setdefault("binding_memory", {})
            remembered = 0
            now = _utc_now()
            for selection in selections:
                if not isinstance(selection, dict):
                    continue
                asset_path = str(selection.get("asset_path") or selection.get("ue_asset_path") or "").strip()
                key = self._memory_key(selection)
                if not key or asset_path not in supported_paths:
                    continue
                previous = memory.get(key) or {}
                memory[key] = {
                    "asset_path": asset_path,
                    "block_name": str(selection.get("block_name") or ""),
                    "name": str(selection.get("name") or ""),
                    "category": str(selection.get("category") or ""),
                    "confirmations": int(previous.get("confirmations") or 0) + 1,
                    "confirmed_at": now,
                }
                remembered += 1
            self._write(ue_project_id, catalog)
        return {"status": "ok", "ue_project_id": ue_project_id, "remembered": remembered}
