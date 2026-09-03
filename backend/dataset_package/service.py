"""Product-level, storage-neutral dataset package contract.

The transport deliberately contains a logical Project snapshot rather than a JSON
store file or a database dump.  Import writes through ProjectStore's public API so
JSON and PostgreSQL deployments share the same behavior.
"""

import copy
import datetime
import hashlib
import io
import ipaddress
import json
import os
import re
import time
import uuid
import zipfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dataset_activation import project_dataset_to_object_types
from project_store import (
    CURRENT_SCHEMA_VERSION,
    UnsupportedProjectSchemaError,
    _default_media_policy,
    _default_scene_interactions,
    _default_spatial_profile,
    _default_web_interactions,
    migrate_project_schema,
)


PACKAGE_KIND = "ontotwin.dataset-package"
PACKAGE_FORMAT_VERSION = 1
PRODUCT_VERSION = "2.3.2"
PACKAGE_EXTENSION = ".otdataset"
PACKAGE_MIMETYPE = "application/vnd.ontotwin.dataset-package"
MAX_PACKAGE_BYTES = 64 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
PAYLOAD_NAME = "project.json"
MANIFEST_NAME = "manifest.json"
INTEGRITY_NAME = "integrity.json"

_SENSITIVE_KEYS = {
    "password", "passwd", "secret", "client_secret", "token", "access_token",
    "refresh_token", "api_key", "apikey", "authorization", "cookie",
    "session_id", "sessionid",
}
_RESOURCE_KEYS = {
    "asset_id", "ue_asset_path", "container_blueprint_id", "container_blueprint_path",
    "source_asset_path", "base_url", "url", "uri", "media_url", "video_url",
    "image_url", "image_path", "audio_url", "storage_name", "resource_path",
}
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


class DatasetPackageError(ValueError):
    def __init__(self, code, message, status=400, details=None):
        self.code = code
        self.status = int(status)
        self.details = details
        super().__init__(message)


class _DuplicateJsonKey(ValueError):
    pass


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _json_with_unique_keys(data, label):
    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _DuplicateJsonKey(f"{label} 包含重复字段: {key}")
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=pairs_hook)
    except UnicodeDecodeError as exc:
        raise DatasetPackageError("package_encoding_invalid", f"{label} 不是 UTF-8 数据") from exc
    except _DuplicateJsonKey as exc:
        raise DatasetPackageError("package_duplicate_key", str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise DatasetPackageError("package_json_invalid", f"{label} 无法解析") from exc


def _walk(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, str(index), child
            yield from _walk(child, child_path)


def _scrub_sensitive(value, path="$", removed=None):
    removed = removed if removed is not None else []
    if isinstance(value, dict):
        cleaned = {}
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).strip().lower() in _SENSITIVE_KEYS:
                removed.append(child_path)
                continue
            cleaned[key] = _scrub_sensitive(child, child_path, removed)
        return cleaned
    if isinstance(value, list):
        return [
            _scrub_sensitive(child, f"{path}[{index}]", removed)
            for index, child in enumerate(value)
        ]
    if isinstance(value, str):
        try:
            parsed = urlsplit(value)
        except ValueError:
            return value
        if parsed.scheme in {"http", "https"} and parsed.hostname:
            changed = False
            hostname = parsed.hostname
            if ":" in hostname and not hostname.startswith("["):
                hostname = f"[{hostname}]"
            netloc = hostname
            try:
                port = parsed.port
            except ValueError:
                return value
            if port:
                netloc += f":{port}"
            if parsed.username is not None or parsed.password is not None:
                changed = True
            query = []
            for key, item in parse_qsl(parsed.query, keep_blank_values=True):
                if key.strip().lower() in _SENSITIVE_KEYS:
                    changed = True
                    continue
                query.append((key, item))
            fragment = parsed.fragment
            fragment_lower = fragment.lower()
            if any(f"{key}=" in fragment_lower for key in _SENSITIVE_KEYS):
                changed = True
                fragment = ""
            if changed:
                removed.append(path + "#url_credentials")
                return urlunsplit((parsed.scheme, netloc, parsed.path, urlencode(query), fragment))
    return value


def _url_portability(value):
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    hostname = parsed.hostname.lower()
    internal = hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local")
    try:
        internal = internal or ipaddress.ip_address(hostname).is_private
    except ValueError:
        pass
    return "internal_url" if internal else "external_url"


def _resource_references(project):
    refs = []
    seen = set()
    for path, key, value in _walk(project):
        if not isinstance(value, str) or not value.strip():
            continue
        text = value.strip()
        lower_key = key.lower()
        kind = _url_portability(text)
        if kind is None and (_WINDOWS_ABSOLUTE.match(text) or text.startswith("/")):
            kind = "local_path"
        if kind is None and lower_key in _RESOURCE_KEYS:
            kind = "resource_reference"
        if kind is None and (
            lower_key.endswith("_url")
            or lower_key.endswith("_uri")
            or lower_key.endswith("_path")
            or lower_key.endswith("_asset_id")
        ):
            kind = "resource_reference"
        if kind is None:
            continue
        fingerprint = (path, kind, text)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        refs.append({
            "path": path,
            "kind": kind,
            "value": text,
            "status": "needs_verification",
        })
    return refs


def _capability_dependencies(project):
    dependencies = set()
    for object_type in (project.get("object_types") or {}).values():
        if not isinstance(object_type, dict):
            continue
        for item in object_type.get("injected_interfaces") or []:
            if isinstance(item, str) and item.strip():
                dependencies.add(item.strip())
            elif isinstance(item, dict):
                identity = item.get("interface_id") or item.get("id") or item.get("name")
                if identity:
                    dependencies.add(str(identity))
    return sorted(dependencies)


def _overlay_count(project):
    count = 0
    for object_type in (project.get("object_types") or {}).values():
        if not isinstance(object_type, dict):
            continue
        text = json.dumps(object_type, ensure_ascii=False, default=str).lower()
        if "overlay" in text:
            count += 1
    return count


def _summary(project):
    dataset = project.get("dataset") or {}
    graph = dataset.get("graph_data") or {}
    scene = project.get("scene_interactions") or {}
    web = project.get("web_interactions") or {}
    published = web.get("published") or {}
    return {
        "types": len(project.get("object_types") or {}),
        "instances": len(project.get("instances") or {}),
        "components": len(project.get("components") or {}),
        "roster_entries": len(project.get("instance_roster") or []),
        "graph_nodes": len(graph.get("nodes") or []),
        "graph_links": len(graph.get("links") or []),
        "frames": len(project.get("frames") or []),
        "zones": len(project.get("zones") or {}),
        "routes": len(scene.get("routes") or []),
        "overlays": _overlay_count(project),
        "web_pages": len(published.get("pages") or []),
        "web_bindings": len(published.get("bindings") or []),
        "has_calibration": project.get("calibration") is not None,
        "has_spatial_profile": isinstance(project.get("spatial_profile"), dict),
    }


def _validate_project(project):
    blockers = []

    def block(code, message, path=None):
        item = {"code": code, "message": message}
        if path:
            item["path"] = path
        blockers.append(item)

    if not isinstance(project, dict):
        block("project_missing", "数据集包缺少项目数据")
        return blockers
    for key in ("id", "name", "schema_version", "dataset", "object_types", "instances"):
        if key not in project:
            block("core_field_missing", f"缺少核心内容: {key}", f"$.{key}")
    dataset = project.get("dataset")
    if not isinstance(dataset, dict) or not isinstance(dataset.get("graph_data"), dict):
        block("graph_dataset_missing", "数据集包缺少可迁移的语义图谱", "$.dataset.graph_data")
    if not isinstance(project.get("object_types"), dict):
        block("object_types_invalid", "类型数据格式无效", "$.object_types")
    if not isinstance(project.get("instances"), dict):
        block("instances_invalid", "实例数据格式无效", "$.instances")

    graph = (dataset or {}).get("graph_data") or {}
    node_ids = set()
    node_references = set()
    for index, node in enumerate(graph.get("nodes") or []):
        if not isinstance(node, dict):
            block("graph_node_invalid", "图谱节点格式无效", f"$.dataset.graph_data.nodes[{index}]")
            continue
        identity = node.get("rid") or node.get("id")
        if not identity:
            block("graph_node_id_missing", "图谱节点缺少身份", f"$.dataset.graph_data.nodes[{index}]")
        elif str(identity) in node_ids:
            block("graph_node_id_duplicate", f"图谱节点身份重复: {identity}")
        else:
            node_ids.add(str(identity))
        for candidate in (node.get("id"), node.get("rid"), node.get("name")):
            if candidate is not None and str(candidate):
                node_references.add(str(candidate))

    for index, link in enumerate(graph.get("links") or []):
        if not isinstance(link, dict):
            block("graph_link_invalid", "图谱关系格式无效", f"$.dataset.graph_data.links[{index}]")
            continue
        for endpoint in ("source", "target"):
            reference = link.get(endpoint)
            if isinstance(reference, dict):
                reference = reference.get("id") or reference.get("rid") or reference.get("name")
            if isinstance(reference, int):
                if reference < 0 or reference >= len(graph.get("nodes") or []):
                    block("graph_link_endpoint_missing", f"图谱关系引用了不存在的节点序号: {reference}")
            elif reference is None or str(reference) not in node_references:
                block("graph_link_endpoint_missing", f"图谱关系引用了不存在的节点: {reference}")

    object_types = project.get("object_types") or {}
    for rid, record in object_types.items():
        if not isinstance(record, dict):
            block("object_type_invalid", f"类型 {rid} 的内容无效")
        elif record.get("rid") not in {None, rid}:
            block("object_type_id_mismatch", f"类型键与内部身份不一致: {rid}")

    instances = project.get("instances") or {}
    for instance_id, record in instances.items():
        if not isinstance(record, dict):
            block("instance_invalid", f"实例 {instance_id} 的内容无效")
            continue
        if record.get("id") not in {None, instance_id}:
            block("instance_id_mismatch", f"实例键与内部身份不一致: {instance_id}")
        rid = record.get("object_type_rid")
        if rid and rid not in object_types:
            block("instance_type_missing", f"实例 {instance_id} 引用了不存在的类型 {rid}")
    return blockers


def _safe_download_stem(value):
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", str(value or "dataset"))
    return value.strip("._-")[:80] or "dataset"


class DatasetPackageService:
    def __init__(
        self,
        store,
        dataset_lookup=None,
        dataset_names=None,
        on_import=None,
    ):
        self.store = store
        self.dataset_lookup = dataset_lookup or (lambda _dataset_id: None)
        self.dataset_names = dataset_names or self._store_dataset_names
        self.on_import = on_import

    def _store_dataset_names(self):
        return [item.get("name") for item in self.store.all_datasets() if item.get("name")]

    def _source_project(self, dataset_id):
        if not dataset_id or dataset_id == "demo":
            raise DatasetPackageError("dataset_not_exportable", "内置数据集不能导出", 400)
        project = self.store.read_project(dataset_id)
        if project:
            return project
        dataset = self.dataset_lookup(dataset_id)
        if not isinstance(dataset, dict):
            raise DatasetPackageError("dataset_not_found", f"找不到数据集: {dataset_id}", 404)
        return {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "id": dataset_id,
            "name": dataset.get("name") or dataset_id,
            "created_at": dataset.get("created_at") or "",
            "dataset": copy.deepcopy(dataset),
            "object_types": project_dataset_to_object_types(dataset),
            "instances": {},
            "components": {},
            "instance_roster": [],
            "calibration": None,
            "spatial_profile": _default_spatial_profile(),
            "frames": [],
            "scene_interactions": _default_scene_interactions(),
            "media_policy": _default_media_policy(),
            "zones": {},
            "web_interactions": _default_web_interactions(),
        }

    def _sanitized_export(self, dataset_id):
        source = copy.deepcopy(self._source_project(dataset_id))
        dataset = source.get("dataset") or {}
        if not isinstance(dataset, dict):
            raise DatasetPackageError("dataset_export_blocked", "数据集元数据格式无效", 422)
        source_ue = {
            "project_id": str(dataset.get("bound_ue_project_id") or ""),
            "project_name": str(dataset.get("bound_ue_project_name") or ""),
        }
        dataset["bound_ue_project_id"] = ""
        dataset["bound_ue_project_name"] = ""
        source["dataset"] = dataset

        for record in (source.get("instances") or {}).values():
            if not isinstance(record, dict):
                continue
            record["status"] = "offline"
            record.pop("last_seen", None)
            record.pop("last_seen_at", None)

        removed = []
        source = _scrub_sensitive(source, removed=removed)
        migrate_project_schema(source)
        blockers = _validate_project(source)
        if blockers:
            raise DatasetPackageError(
                "dataset_export_blocked",
                "数据集存在无法迁移的核心关系问题",
                422,
                {"blockers": blockers},
            )
        return source, source_ue, removed

    def _manifest(self, project, source_ue, removed, payload_bytes=None):
        dataset = project.get("dataset") or {}
        refs = _resource_references(project)
        manifest = {
            "kind": PACKAGE_KIND,
            "format_version": PACKAGE_FORMAT_VERSION,
            "package_id": f"pkg_{uuid.uuid4().hex}",
            "product_version": PRODUCT_VERSION,
            "exported_at": _utc_now(),
            "project_schema_version": int(project.get("schema_version") or 1),
            "source": {
                "project_id": project.get("id"),
                "dataset_id": dataset.get("id") or project.get("id"),
                "dataset_name": dataset.get("name") or project.get("name"),
                "ue_project": source_ue,
            },
            "summary": _summary(project),
            "resource_references": refs,
            "resource_summary": {
                "total": len(refs),
                "local_paths": sum(item["kind"] == "local_path" for item in refs),
                "internal_urls": sum(item["kind"] == "internal_url" for item in refs),
                "external_urls": sum(item["kind"] == "external_url" for item in refs),
                "needs_verification": len(refs),
            },
            "capability_dependencies": _capability_dependencies(project),
            "excluded": {
                "active_state": True,
                "effective_ue_binding": True,
                "runtime_liveness": True,
                "platform_mapping_rules": True,
                "credentials_and_sessions": True,
                "external_resource_binaries": True,
                "scrubbed_sensitive_field_count": len(removed),
            },
        }
        if payload_bytes is not None:
            manifest["payload"] = {
                "file": PAYLOAD_NAME,
                "size_bytes": len(payload_bytes),
                "sha256": hashlib.sha256(payload_bytes).hexdigest(),
            }
        return manifest

    def export_summary(self, dataset_id):
        project, source_ue, removed = self._sanitized_export(dataset_id)
        manifest = self._manifest(project, source_ue, removed)
        return {
            "dataset_id": dataset_id,
            "dataset_name": manifest["source"]["dataset_name"],
            "summary": manifest["summary"],
            "resource_summary": manifest["resource_summary"],
            "resource_references": manifest["resource_references"][:100],
            "capability_dependencies": manifest["capability_dependencies"],
            "source_ue_project": source_ue,
            "excluded": manifest["excluded"],
        }

    def export_package(self, dataset_id):
        project, source_ue, removed = self._sanitized_export(dataset_id)
        payload = _canonical_json(project)
        manifest = self._manifest(project, source_ue, removed, payload)
        target = io.BytesIO()
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            manifest_bytes = _canonical_json(manifest)
            integrity = {
                "kind": PACKAGE_KIND,
                "format_version": PACKAGE_FORMAT_VERSION,
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
            }
            archive.writestr(INTEGRITY_NAME, _canonical_json(integrity))
            archive.writestr(MANIFEST_NAME, manifest_bytes)
            archive.writestr(PAYLOAD_NAME, payload)
        name = _safe_download_stem(manifest["source"]["dataset_name"]) + PACKAGE_EXTENSION
        return target.getvalue(), name, manifest

    @staticmethod
    def _read_package(package_bytes):
        if not isinstance(package_bytes, (bytes, bytearray)) or not package_bytes:
            raise DatasetPackageError("package_missing", "请选择数据集包")
        package_bytes = bytes(package_bytes)
        if len(package_bytes) > MAX_PACKAGE_BYTES:
            raise DatasetPackageError("package_too_large", "数据集包超过 64 MB 限制", 413)
        try:
            archive = zipfile.ZipFile(io.BytesIO(package_bytes), "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise DatasetPackageError("package_unrecognized", "无法识别 OntoTwin 数据集包") from exc
        with archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)) or set(names) != {
                INTEGRITY_NAME, MANIFEST_NAME, PAYLOAD_NAME
            }:
                raise DatasetPackageError("package_layout_invalid", "数据集包内部结构无效")
            total = 0
            for info in infos:
                if info.is_dir() or info.flag_bits & 0x1:
                    raise DatasetPackageError("package_layout_invalid", "数据集包包含不受支持的条目")
                total += int(info.file_size)
                if total > MAX_UNCOMPRESSED_BYTES:
                    raise DatasetPackageError("package_expansion_too_large", "数据集包展开后超过限制", 413)
                if info.compress_size and info.file_size > max(1024 * 1024, info.compress_size * 200):
                    raise DatasetPackageError("package_compression_suspicious", "数据集包压缩比例异常")
            try:
                integrity_bytes = archive.read(INTEGRITY_NAME)
                manifest_bytes = archive.read(MANIFEST_NAME)
                payload_bytes = archive.read(PAYLOAD_NAME)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise DatasetPackageError("package_integrity_failed", "数据集包无法完整读取") from exc

        integrity = _json_with_unique_keys(integrity_bytes, "完整性信息")
        if not isinstance(integrity, dict):
            raise DatasetPackageError("package_integrity_failed", "数据集包完整性信息无效")
        if (
            integrity.get("kind") != PACKAGE_KIND
            or integrity.get("format_version") != PACKAGE_FORMAT_VERSION
            or integrity.get("manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest()
            or integrity.get("payload_sha256") != hashlib.sha256(payload_bytes).hexdigest()
        ):
            raise DatasetPackageError("package_integrity_failed", "数据集包完整性校验失败")
        manifest = _json_with_unique_keys(manifest_bytes, "包清单")
        if not isinstance(manifest, dict):
            raise DatasetPackageError("manifest_invalid", "数据集包清单格式无效")
        payload_meta = manifest.get("payload") or {}
        if not isinstance(payload_meta, dict):
            raise DatasetPackageError("package_integrity_failed", "数据集包载荷信息无效")
        expected_hash = str(payload_meta.get("sha256") or "")
        actual_hash = hashlib.sha256(payload_bytes).hexdigest()
        if (
            payload_meta.get("file") != PAYLOAD_NAME
            or payload_meta.get("size_bytes") != len(payload_bytes)
            or expected_hash != actual_hash
        ):
            raise DatasetPackageError("package_integrity_failed", "数据集包完整性校验失败")
        project = _json_with_unique_keys(payload_bytes, "项目数据")
        return manifest, project

    def _existing_names(self):
        return {
            str(value).strip()
            for value in (self.dataset_names() or [])
            if str(value or "").strip()
        }

    @staticmethod
    def _suggest_name(source_name, existing):
        source_name = str(source_name or "导入的数据集").strip() or "导入的数据集"
        if source_name not in existing:
            return source_name
        candidate = f"{source_name}（副本）"
        if candidate not in existing:
            return candidate
        sequence = 2
        while f"{source_name}（副本 {sequence}）" in existing:
            sequence += 1
        return f"{source_name}（副本 {sequence}）"

    def _preflight(self, package_bytes):
        manifest, raw_project = self._read_package(package_bytes)
        if not isinstance(raw_project, dict):
            raise DatasetPackageError("package_project_invalid", "数据集包中的项目数据格式无效")
        blockers = []
        warnings = []

        if manifest.get("kind") != PACKAGE_KIND:
            blockers.append({"code": "package_kind_unsupported", "message": "不是受支持的 OntoTwin 数据集包"})
        try:
            format_version = int(manifest.get("format_version"))
        except (TypeError, ValueError):
            format_version = -1
        if format_version != PACKAGE_FORMAT_VERSION:
            blockers.append({
                "code": "package_format_unsupported",
                "message": f"数据集包格式 v{format_version} 不受支持",
            })

        try:
            source_schema = int(raw_project.get("schema_version", 1))
        except (TypeError, ValueError):
            source_schema = -1
            blockers.append({"code": "schema_version_invalid", "message": "数据结构版本无效"})
        try:
            declared_schema = int(manifest.get("project_schema_version"))
        except (TypeError, ValueError):
            declared_schema = -1
        if declared_schema != source_schema:
            blockers.append({
                "code": "manifest_payload_mismatch",
                "message": "包清单声明的数据结构版本与项目数据不一致",
            })

        project = copy.deepcopy(raw_project)
        if source_schema > CURRENT_SCHEMA_VERSION:
            blockers.append({
                "code": "project_schema_newer",
                "message": f"包内数据结构 v{source_schema} 高于当前支持的 v{CURRENT_SCHEMA_VERSION}",
            })
        elif source_schema >= 1:
            try:
                migrated = migrate_project_schema(project)
                if migrated:
                    warnings.append({
                        "code": "project_schema_upgraded",
                        "message": f"导入时会将数据结构从 v{source_schema} 安全升级到 v{CURRENT_SCHEMA_VERSION}",
                    })
            except UnsupportedProjectSchemaError:
                blockers.append({"code": "project_schema_newer", "message": "数据结构版本高于当前系统"})
            except (TypeError, ValueError) as exc:
                blockers.append({"code": "project_schema_invalid", "message": str(exc)})

        if source_schema <= CURRENT_SCHEMA_VERSION:
            blockers.extend(_validate_project(project))

        source = manifest.get("source") or {}
        if not isinstance(source, dict):
            source = {}
        source_name = source.get("dataset_name") or (project.get("dataset") or {}).get("name") or project.get("name")
        existing = self._existing_names()
        suggested_name = self._suggest_name(source_name, existing)
        if suggested_name != source_name:
            warnings.append({
                "code": "dataset_name_conflict",
                "message": f"本地已有同名数据集，建议使用“{suggested_name}”",
            })

        refs = _resource_references(project)
        resource_summary = {
            "total": len(refs),
            "local_paths": sum(item["kind"] == "local_path" for item in refs),
            "internal_urls": sum(item["kind"] == "internal_url" for item in refs),
            "external_urls": sum(item["kind"] == "external_url" for item in refs),
            "needs_verification": len(refs),
        }
        if refs:
            warnings.append({
                "code": "external_resources_need_verification",
                "message": f"发现 {len(refs)} 个外部资源引用，绑定目标 UE 工程后需要核对",
            })
        source_ue = source.get("ue_project") or {}
        if source_ue.get("project_id") or source_ue.get("project_name"):
            warnings.append({
                "code": "source_ue_binding_cleared",
                "message": "来源 UE 工程信息仅作说明；导入后不会自动绑定",
            })

        report = {
            "can_import": not blockers,
            "package": {
                "package_id": manifest.get("package_id"),
                "format_version": format_version,
                "product_version": manifest.get("product_version"),
                "exported_at": manifest.get("exported_at"),
            },
            "source": {
                "project_id": source.get("project_id") or raw_project.get("id"),
                "dataset_id": source.get("dataset_id") or (raw_project.get("dataset") or {}).get("id"),
                "dataset_name": source_name,
                "ue_project": source_ue,
            },
            "compatibility": {
                "source_schema_version": source_schema,
                "target_schema_version": CURRENT_SCHEMA_VERSION,
                "migration_required": source_schema != CURRENT_SCHEMA_VERSION,
            },
            "suggested_name": suggested_name,
            "summary": _summary(project),
            "resource_summary": resource_summary,
            "resource_references": refs[:100],
            "capability_dependencies": _capability_dependencies(project),
            "excluded": manifest.get("excluded") or {},
            "blockers": blockers,
            "warnings": warnings,
        }
        return report, project, manifest

    def preflight(self, package_bytes):
        report, _, _ = self._preflight(package_bytes)
        return report

    def _new_project_id(self):
        for _ in range(8):
            candidate = f"p_{time.time_ns()}_{uuid.uuid4().hex[:8]}"
            if self.store.read_project(candidate) is None:
                return candidate
        raise DatasetPackageError("project_id_allocation_failed", "无法生成新的数据集身份", 500)

    def import_package(self, package_bytes, target_name=None):
        report, project, manifest = self._preflight(package_bytes)
        if report["blockers"]:
            raise DatasetPackageError(
                "package_preflight_blocked",
                "数据集包未通过预检",
                422,
                report,
            )
        name = str(target_name or report["suggested_name"] or "").strip()
        if not name:
            raise DatasetPackageError("dataset_name_required", "请输入导入后的数据集名称")
        if len(name) > 128:
            raise DatasetPackageError("dataset_name_too_long", "数据集名称不能超过 128 个字符")
        if name in self._existing_names():
            raise DatasetPackageError("dataset_name_conflict", f"已存在同名数据集: {name}", 409)

        new_id = self._new_project_id()
        imported = copy.deepcopy(project)
        source = report["source"]
        imported["id"] = new_id
        imported["name"] = name
        imported["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        imported["schema_version"] = CURRENT_SCHEMA_VERSION
        dataset = imported.get("dataset") or {}
        dataset["id"] = new_id
        dataset["name"] = name
        dataset["created_at"] = imported["created_at"]
        dataset["bound_ue_project_id"] = ""
        dataset["bound_ue_project_name"] = ""
        dataset["migration_source"] = {
            "package_id": (manifest or {}).get("package_id"),
            "source_project_id": source.get("project_id"),
            "source_dataset_id": source.get("dataset_id"),
            "source_dataset_name": source.get("dataset_name"),
            "source_ue_project": copy.deepcopy(source.get("ue_project") or {}),
            "exported_at": (manifest or {}).get("exported_at"),
            "imported_at": _utc_now(),
        }
        graph = dataset.get("graph_data") or {}
        dataset["node_count"] = len(graph.get("nodes") or [])
        dataset["link_count"] = len(graph.get("links") or [])
        imported["dataset"] = dataset

        active_before = self.store.get_active_id()
        written = False
        try:
            self.store.write_project(new_id, imported)
            written = True
            if self.on_import:
                self.on_import(copy.deepcopy(dataset))
        except Exception:
            if written:
                try:
                    self.store.delete_project(new_id)
                except Exception:
                    pass
            raise
        if self.store.get_active_id() != active_before:
            if active_before:
                self.store.activate(active_before)
            else:
                self.store.deactivate()
            try:
                self.store.delete_project(new_id)
            except Exception:
                pass
            raise DatasetPackageError(
                "import_changed_active_project",
                "导入未能保持当前项目，已撤销本次导入",
                500,
            )
        return {
            "status": "ok",
            "project_id": new_id,
            "dataset_id": new_id,
            "dataset_name": name,
            "active": False,
            "bound": False,
            "preflight": report,
        }


__all__ = [
    "DatasetPackageError",
    "DatasetPackageService",
    "MAX_PACKAGE_BYTES",
    "PACKAGE_EXTENSION",
    "PACKAGE_MIMETYPE",
]
