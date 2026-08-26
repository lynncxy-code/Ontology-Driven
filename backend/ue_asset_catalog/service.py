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
import uuid


_DEFAULT_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ue_asset_catalogs")
_RUNTIME_SUPPORTED_KINDS = {"StaticMesh", "SkeletalMesh"}
_RECOMMENDABLE_KINDS = {"StaticMesh", "SkeletalMesh", "Blueprint"}
_RELIABLE_SCORE = 0.45
_AMBIGUOUS_GAP = 0.08
_MAX_ASSETS = 10000
_MAX_ITEMS = 2000
_MAX_FOLDERS = 30000
_MAX_THUMBNAIL_CHARS = 512 * 1024

# CAD 图层与 UE 资产目录常使用不同词汇。别名只参与候选推荐，不改写本体名称。
_SEMANTIC_ALIASES = {
    "water_spray": {
        "水幕喷淋", "水幕", "喷淋", "淋雨", "雨淋", "喷雾",
        "spray", "sprinkler", "rain", "shower",
    },
    "electrical_cabinet": {
        "电柜", "电控柜", "控制柜", "配电柜", "开关柜",
        "cabinet", "electricalcabinet", "controlcabinet",
    },
    "material_receiving": {
        "物料接收", "物料接收点", "接料", "收料", "上料", "接驳",
        "loading", "receiving", "materialreceiving",
    },
    "door": {"门", "闸门", "卷帘门", "door", "gate"},
}


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


def _normalized_folder_path(value):
    value = unicodedata.normalize("NFKC", str(value or "")).strip().replace("\\", "/")
    while len(value) > 1 and value.endswith("/"):
        value = value[:-1]
    return value


def _validated_game_folder(value):
    value = _normalized_folder_path(value)
    if value != "/Game" and not value.startswith("/Game/"):
        raise AssetCatalogError("asset_folder_invalid", "模型目录必须是 /Game 或其子目录")
    if len(value) > 500 or "." in value.rsplit("/", 1)[-1]:
        raise AssetCatalogError("asset_folder_invalid", "请填写 UE 内容目录，而不是具体资产路径")
    return value


def _asset_is_inside_folder(asset, folder_path):
    asset_folder = _normalized_folder_path(asset.get("folder_path")).lower()
    folder_path = _normalized_folder_path(folder_path).lower()
    return bool(folder_path and (asset_folder == folder_path or asset_folder.startswith(folder_path + "/")))


def _tokens(value):
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    raw = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", text)
    ignored = {"sm", "sk", "bp", "mesh", "static", "staticmesh", "game", "art", "asset", "assets"}
    return {part for part in raw if part and part not in ignored}


def _semantic_terms(*values):
    terms = set()
    for value in values:
        text = unicodedata.normalize("NFKC", str(value or "")).lower()
        text_tokens = _tokens(text)
        terms.update(text_tokens)
        for chunk in re.findall(r"[\u4e00-\u9fff]+", text):
            terms.add(chunk)
            if len(chunk) >= 2:
                terms.update(chunk[index:index + 2] for index in range(len(chunk) - 1))
        compact = _normalized_text(text)
        if not compact:
            continue
        for concept, aliases in _SEMANTIC_ALIASES.items():
            matched = False
            for alias in aliases:
                alias_text = unicodedata.normalize("NFKC", alias).lower()
                alias_compact = _normalized_text(alias_text)
                if re.search(r"[\u4e00-\u9fff]", alias_text):
                    matched = alias_compact in compact
                else:
                    alias_tokens = _tokens(alias_text)
                    matched = bool(alias_tokens and alias_tokens.issubset(text_tokens))
                    if not matched and len(alias_compact) >= 6:
                        matched = alias_compact in compact
                if matched:
                    break
            if matched:
                terms.add(f"@{concept}")
    return terms


def _semantic_overlap(left, right):
    if not left or not right:
        return None
    shared_concepts = {term for term in left & right if term.startswith("@")}
    if shared_concepts:
        return 1.0
    return _overlap(
        {term for term in left if not term.startswith("@")},
        {term for term in right if not term.startswith("@")},
    )


def _value_name_quality(value):
    raw = unicodedata.normalize("NFKC", str(value or "")).lower().strip()
    compact = _normalized_text(raw)
    if not compact:
        return 0.0
    if re.fullmatch(r"\d{5,}", compact):
        return 0.0
    if re.search(r"\$[0-9a-f]{6,}", raw) or re.search(r"\$c[0-9a-f]{5,}", raw):
        return 0.0
    digit_ratio = sum(char.isdigit() for char in compact) / len(compact)
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", compact))
    return 0.2 if len(compact) >= 14 and digit_ratio >= 0.45 and not has_chinese else 1.0


def _name_quality(item):
    return max(_value_name_quality(item.get("block_name")), _value_name_quality(item.get("name")))


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


def _runtime_supported(raw, asset_kind):
    if asset_kind in _RUNTIME_SUPPORTED_KINDS:
        return True
    if asset_kind == "Blueprint":
        return raw.get("runtime_loadable") is True
    return False


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
        if _value_name_quality(source) < 0.5:
            continue
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
    def _upload_identity(payload, request_identity, label):
        body_id = str((payload or {}).get("ue_project_id") or "").strip()
        header_id = str((request_identity or {}).get("id") or "").strip()
        if not body_id and not header_id:
            raise AssetCatalogError("ue_project_id_required", f"{label}必须携带工程 ID")
        if body_id and header_id and body_id != header_id:
            raise AssetCatalogError("ue_project_identity_mismatch", "请求头与正文中的 UE 工程 ID 不一致", 409)
        return header_id or body_id

    @staticmethod
    def _empty_catalog(ue_project_id, ue_project_name=""):
        return {
            "schema_version": 2,
            "ue_project_id": ue_project_id,
            "ue_project_name": ue_project_name or ue_project_id,
            "roots": [],
            "synced_at": "",
            "catalog_revision": "",
            "assets": [],
            "binding_memory": {},
            "available_folders": [],
            "folders_synced_at": "",
        }

    @staticmethod
    def _clean_asset(raw):
        if not isinstance(raw, dict):
            return None
        object_path = str(raw.get("object_path") or raw.get("asset_path") or "").strip().replace("\\", "/")
        if not (object_path.startswith("/Game/") or object_path.startswith("/Engine/")):
            return None
        asset_kind = _kind(raw.get("asset_kind") or raw.get("asset_class"))
        runtime_supported = _runtime_supported(raw, asset_kind)
        asset_name = str(raw.get("asset_name") or object_path.rsplit("/", 1)[-1].split(".", 1)[0]).strip()
        folder_path = str(raw.get("folder_path") or object_path.rsplit("/", 1)[0]).strip().replace("\\", "/")
        result = {
            "object_path": object_path,
            "package_name": str(raw.get("package_name") or object_path.split(".", 1)[0]).strip(),
            "asset_name": asset_name,
            "display_name": str(raw.get("display_name") or asset_name).strip(),
            "folder_path": folder_path,
            "asset_kind": asset_kind,
            "supported": runtime_supported,
            "runtime_supported": runtime_supported,
            "recommendable": runtime_supported and asset_kind in _RECOMMENDABLE_KINDS,
            "runtime_loadable": runtime_supported,
            "runtime_reason": str(raw.get("runtime_reason") or (
                "需重新同步 UE 资产目录以校验 Blueprint 生成类"
                if asset_kind == "Blueprint"
                else asset_kind
            )).strip(),
            "generated_class_path": str(raw.get("generated_class_path") or "").strip(),
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
        ue_project_id = self._resolve_id(self._upload_identity(payload, request_identity, "UE 资产目录同步"))
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
            f'{item["object_path"]}|{item["asset_kind"]}|{item.get("runtime_loadable")}|'
            f'{item.get("generated_class_path")}|{json.dumps(item.get("size_cm"), sort_keys=True)}'
            for item in assets
        )
        with self._lock:
            existing = self._read(ue_project_id, required=False) or self._empty_catalog(ue_project_id)
            scan_request = copy.deepcopy(existing.get("scan_request") or {})
            scan_request_id = str(payload.get("scan_request_id") or "").strip()
            if scan_request_id:
                if not scan_request or scan_request_id != str(scan_request.get("request_id") or ""):
                    raise AssetCatalogError("scan_request_mismatch", "按需扫描请求已失效，请从 OntoTwin 重新发起", 409)
                scan_request.update({
                    "status": "completed",
                    "completed_at": _utc_now(),
                    "asset_count": len(assets),
                    "catalog_roots": [str(item).strip() for item in (payload.get("roots") or []) if str(item).strip()],
                    "error": "",
                })
            value = {
                "schema_version": 2,
                "ue_project_id": ue_project_id,
                "ue_project_name": str(payload.get("ue_project_name") or (request_identity or {}).get("name") or ue_project_id).strip(),
                "roots": [str(item).strip() for item in (payload.get("roots") or []) if str(item).strip()],
                "synced_at": _utc_now(),
                "catalog_revision": hashlib.sha256(revision_seed.encode("utf-8")).hexdigest()[:20],
                "assets": assets,
                "binding_memory": existing.get("binding_memory") or {},
                "available_folders": existing.get("available_folders") or [],
                "folders_synced_at": existing.get("folders_synced_at") or "",
            }
            if scan_request:
                value["scan_request"] = scan_request
            self._write(ue_project_id, value)
        return self._public_catalog(value)

    def replace_folder_index(self, payload, request_identity=None):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(self._upload_identity(payload, request_identity, "UE 目录索引同步"))
        raw_folders = payload.get("folders") or []
        if not isinstance(raw_folders, list):
            raise AssetCatalogError("folders_invalid", "folders 必须是数组")
        if len(raw_folders) > _MAX_FOLDERS:
            raise AssetCatalogError("folders_too_many", f"单次最多同步 {_MAX_FOLDERS} 个目录", 413)
        folders = []
        for raw in raw_folders:
            try:
                folders.append(_validated_game_folder(raw))
            except AssetCatalogError:
                continue
        folders = sorted(set(folders), key=lambda item: item.lower())
        if "/Game" not in folders:
            folders.insert(0, "/Game")
        with self._lock:
            value = self._read(ue_project_id, required=False) or self._empty_catalog(
                ue_project_id,
                str(payload.get("ue_project_name") or (request_identity or {}).get("name") or ue_project_id).strip(),
            )
            value["schema_version"] = 2
            value["ue_project_name"] = str(
                payload.get("ue_project_name") or (request_identity or {}).get("name")
                or value.get("ue_project_name") or ue_project_id
            ).strip()
            value["available_folders"] = folders
            value["folders_synced_at"] = _utc_now()
            self._write(ue_project_id, value)
        return {
            "status": "ok",
            "ue_project_id": ue_project_id,
            "folder_count": len(folders),
            "folders_synced_at": value["folders_synced_at"],
        }

    def create_scan_request(self, payload):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(payload.get("ue_project_id"))
        folder_path = _validated_game_folder(payload.get("folder_path"))
        with self._lock:
            value = self._read(ue_project_id)
            scan_request = {
                "request_id": uuid.uuid4().hex,
                "folder_path": folder_path,
                "status": "pending",
                "requested_at": _utc_now(),
                "completed_at": "",
                "asset_count": 0,
                "error": "",
            }
            value["scan_request"] = scan_request
            self._write(ue_project_id, value)
        return copy.deepcopy(scan_request)

    def get_scan_request(self, ue_project_id=None):
        ue_project_id = self._resolve_id(ue_project_id)
        with self._lock:
            value = self._read(ue_project_id)
            scan_request = copy.deepcopy(value.get("scan_request") or {})
        if not scan_request:
            return {"ue_project_id": ue_project_id, "status": "idle"}
        scan_request["ue_project_id"] = ue_project_id
        return scan_request

    def get_pending_scan_request(self, request_identity=None):
        ue_project_id = self._resolve_id(
            self._upload_identity({}, request_identity, "UE 扫描请求")
        )
        with self._lock:
            value = self._read(ue_project_id)
            scan_request = copy.deepcopy(value.get("scan_request") or {})
        if scan_request.get("status") != "pending":
            return {"ue_project_id": ue_project_id, "status": "idle"}
        scan_request["ue_project_id"] = ue_project_id
        return scan_request

    def report_scan_result(self, payload, request_identity=None):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(self._upload_identity(payload, request_identity, "UE 扫描结果"))
        request_id = str(payload.get("request_id") or "").strip()
        status = str(payload.get("status") or "").strip().lower()
        if status not in {"failed"}:
            raise AssetCatalogError("scan_result_status_invalid", "扫描结果状态不支持")
        with self._lock:
            value = self._read(ue_project_id)
            scan_request = value.get("scan_request") or {}
            if not request_id or request_id != str(scan_request.get("request_id") or ""):
                raise AssetCatalogError("scan_request_mismatch", "按需扫描请求已失效", 409)
            scan_request.update({
                "status": "failed",
                "completed_at": _utc_now(),
                "error": str(payload.get("error") or "UE 无法扫描该目录").strip()[:1000],
            })
            value["scan_request"] = scan_request
            self._write(ue_project_id, value)
        return copy.deepcopy(scan_request)

    @staticmethod
    def _decorate_availability(asset):
        asset_kind = _kind(asset.get("asset_kind"))
        asset["asset_kind"] = asset_kind
        runtime_supported = _runtime_supported(asset, asset_kind)
        asset["runtime_supported"] = runtime_supported
        asset["runtime_loadable"] = runtime_supported
        asset["recommendable"] = runtime_supported and asset_kind in _RECOMMENDABLE_KINDS
        if not asset.get("runtime_reason"):
            asset["runtime_reason"] = (
                "需重新同步 UE 资产目录以校验 Blueprint 生成类"
                if asset_kind == "Blueprint"
                else asset_kind
            )
        # 兼容旧前端与旧目录文件：supported 继续表示当前 TwinInstance 可直接加载。
        asset["supported"] = asset["runtime_supported"]
        return asset

    @staticmethod
    def _public_catalog(value):
        result = copy.deepcopy(value)
        assets = result.get("assets") or []
        for item in assets:
            UEAssetCatalogService._decorate_availability(item)
        result["asset_count"] = len(assets)
        result["runtime_supported_count"] = sum(1 for item in assets if item.get("runtime_supported"))
        result["recommendable_count"] = sum(1 for item in assets if item.get("recommendable"))
        result["supported_count"] = result["runtime_supported_count"]
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
    def _category_memory_path(memory, item):
        category_key = _normalized_text(item.get("category") or item.get("primary_layer"))
        if not category_key:
            return ""
        path_weights = {}
        for value in memory.values():
            if not isinstance(value, dict) or _normalized_text(value.get("category")) != category_key:
                continue
            path = str(value.get("asset_path") or "").strip()
            if path:
                path_weights[path] = path_weights.get(path, 0) + max(1, int(value.get("confirmations") or 1))
        if not path_weights:
            return ""
        return sorted(path_weights, key=lambda path: (-path_weights[path], path.lower()))[0]

    @staticmethod
    def _rank(item, asset, remembered_path, category_remembered_path):
        if remembered_path and asset["object_path"] == remembered_path:
            return 1.0, ["该 UE 工程中曾人工确认"]
        if item.get("preset_asset_id") and asset["object_path"] == item.get("preset_asset_id"):
            return 0.9, ["命中旧版人工对应记录，仍需本次确认"]

        signals = []
        reasons = []
        quality = _name_quality(item)
        item_terms = _semantic_terms(
            item.get("block_name"), item.get("name"),
            item.get("category"), item.get("primary_layer"),
        )
        label_terms = _semantic_terms(
            asset.get("asset_name"), asset.get("display_name"),
            " ".join(asset.get("tags") or []),
        )
        folder_terms = _semantic_terms(
            asset.get("folder_path"), " ".join(asset.get("tags") or []),
        )
        direct_semantic = _semantic_overlap(item_terms, label_terms)
        folder_semantic = _semantic_overlap(item_terms, folder_terms)
        dimensions = _dimension_score(item.get("cad_size_cm"), asset.get("size_cm"))

        if quality >= 0.5:
            name_score = _name_score(item, asset)
            signals.append((0.42, name_score))
            if name_score >= 0.8:
                reasons.append("类型名与资产名高度相似")
            elif name_score >= 0.55:
                reasons.append("类型名与资产名部分相似")
            if direct_semantic is not None:
                signals.append((0.22, direct_semantic))
            if folder_semantic is not None:
                signals.append((0.21, folder_semantic))
            if dimensions is not None:
                signals.append((0.15, dimensions))
        else:
            # 纯数字/CAD 句柄不能与资产编号做模糊字符串匹配，否则会制造看似精确的假推荐。
            if direct_semantic is not None:
                signals.append((0.36, direct_semantic))
            if folder_semantic is not None:
                signals.append((0.52, folder_semantic))
            if dimensions is not None:
                signals.append((0.12, dimensions))

        if direct_semantic is not None and direct_semantic >= 0.8:
            reasons.append("CAD 分类/类型与 UE 资产名称语义匹配")
        if folder_semantic is not None and folder_semantic >= 0.8:
            reasons.append("CAD 分类/类型与 UE 资产目录语义匹配")
        if dimensions is not None and dimensions >= 0.78:
            reasons.append("CAD 与模型尺寸接近")
        if quality < 0.5:
            reasons.append("已忽略纯数字或 CAD 句柄名称，避免数字巧合误导")

        total_weight = sum(weight for weight, _ in signals) or 1.0
        score = sum(weight * value for weight, value in signals) / total_weight
        if category_remembered_path and asset["object_path"] == category_remembered_path:
            score = max(score, 0.86)
            reasons.insert(0, "同一 CAD 分类曾人工确认该资产")
        if not reasons:
            reasons.append("没有足够的名称、分类或尺寸证据")
        return score, reasons

    def recommend(self, payload):
        if not isinstance(payload, dict):
            raise AssetCatalogError("invalid_request", "请求体必须是对象")
        ue_project_id = self._resolve_id(payload.get("ue_project_id"))
        if not _normalized_folder_path(payload.get("folder_path")):
            raise AssetCatalogError("recommendation_folder_required", "请先指定推荐模型目录")
        folder_path = _validated_game_folder(payload.get("folder_path"))
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
        assets = []
        for raw_asset in catalog.get("assets") or []:
            asset = self._decorate_availability(copy.deepcopy(raw_asset))
            if asset.get("recommendable") and _asset_is_inside_folder(asset, folder_path):
                assets.append(asset)
        if not assets:
            raise AssetCatalogError(
                "recommendation_folder_empty",
                "指定目录不在当前同步范围内，或目录中没有可运行资产",
                422,
            )
        memory = catalog.get("binding_memory") or {}
        recommendations = []
        for raw_item in items:
            item = raw_item if isinstance(raw_item, dict) else {}
            key = self._memory_key(item)
            remembered_path = (memory.get(key) or {}).get("asset_path") if key else ""
            category_remembered_path = self._category_memory_path(memory, item)
            ranked = []
            for asset in assets:
                score, reasons = self._rank(item, asset, remembered_path, category_remembered_path)
                candidate = copy.deepcopy(asset)
                candidate["score"] = round(score, 4)
                candidate["confidence"] = "high" if score >= 0.78 else ("medium" if score >= 0.50 else "low")
                candidate["reasons"] = reasons
                candidate["recommended"] = False
                candidate["ambiguous"] = False
                ranked.append(candidate)
            ranked.sort(key=lambda value: (-value["score"], value["object_path"].lower()))
            if ranked:
                runner_up = ranked[1]["score"] if len(ranked) > 1 else 0.0
                gap = ranked[0]["score"] - runner_up
                ambiguous = ranked[0]["score"] < 0.98 and gap < _AMBIGUOUS_GAP
                ranked[0]["ambiguous"] = ambiguous
                ranked[0]["recommended"] = ranked[0]["score"] >= _RELIABLE_SCORE and not ambiguous
                if ambiguous:
                    ranked[0]["reasons"].append("前两名分数接近，需人工比较候选")
            recommendations.append({
                "block_name": str(item.get("block_name") or ""),
                "candidates": ranked[:limit],
            })
        return {
            "ue_project_id": ue_project_id,
            "ue_project_name": catalog.get("ue_project_name") or ue_project_id,
            "catalog_revision": catalog.get("catalog_revision"),
            "folder_path": folder_path,
            "candidate_asset_count": len(assets),
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
                item.get("object_path")
                for item in catalog.get("assets") or []
                if self._decorate_availability(copy.deepcopy(item)).get("recommendable")
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
