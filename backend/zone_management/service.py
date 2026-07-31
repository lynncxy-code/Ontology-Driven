import copy
from collections import Counter

from project_store import ProjectMismatch
from web_interaction.validators import ZONE_LEVELS, validate_zone_hierarchy, zone_catalog


class ZoneManagementError(ValueError):
    def __init__(self, code, message, fields=None):
        self.code = code
        self.fields = fields or []
        super().__init__(message)


class ZoneManagementConflictError(RuntimeError):
    pass


def _normalize_instance_ids(value):
    if not isinstance(value, list) or not value:
        raise ZoneManagementError(
            "invalid_instance_ids",
            "请至少选择一个实例",
            [{"path": "instance_ids", "message": "必须是非空数组"}],
        )
    if len(value) > 5000:
        raise ZoneManagementError(
            "too_many_instances",
            "单次最多处理 5000 个实例",
            [{"path": "instance_ids", "message": "数量不能超过 5000"}],
        )

    normalized = []
    seen = set()
    for index, raw in enumerate(value):
        instance_id = str(raw or "").strip()
        if not instance_id:
            raise ZoneManagementError(
                "invalid_instance_id",
                "实例 ID 不能为空",
                [{"path": f"instance_ids[{index}]", "message": "不能为空"}],
            )
        if instance_id not in seen:
            seen.add(instance_id)
            normalized.append(instance_id)
    return normalized


def _normalize_zone_id(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ZoneManagementError(
            "invalid_zone_id",
            "分区 ID 必须是字符串或 null",
            [{"path": "zone_id", "message": "必须是字符串或 null"}],
        )
    zone_id = value.strip()
    if not zone_id:
        return None
    if len(zone_id) > 128:
        raise ZoneManagementError(
            "invalid_zone_id",
            "分区 ID 最多 128 个字符",
            [{"path": "zone_id", "message": "长度不能超过 128"}],
        )
    if any(ord(char) < 32 for char in zone_id):
        raise ZoneManagementError(
            "invalid_zone_id",
            "分区 ID 不能包含控制字符",
            [{"path": "zone_id", "message": "不能包含控制字符"}],
        )
    return zone_id


class ZoneManagementService:
    def __init__(self, project_store):
        self.store = project_store

    def _active_project(self):
        project = self.store.get_active_copy()
        if not project:
            raise ZoneManagementError("active_project_not_found", "当前没有激活项目")
        return project

    def summary(self):
        project = self._active_project()
        instances = project.get("instances") or {}
        counts = Counter()
        unassigned_count = 0
        for instance in instances.values():
            zone_id = str((instance or {}).get("zone_id") or "").strip()
            if zone_id:
                counts[zone_id] += 1
            else:
                unassigned_count += 1
        catalog = zone_catalog(project)
        zones = []
        for zone_id in sorted(set(catalog) | set(counts), key=str.casefold):
            item = {"id": zone_id, "instance_count": counts.get(zone_id, 0)}
            explicit = (project.get("zones") or {}).get(zone_id) if isinstance(project.get("zones"), dict) else None
            if isinstance(explicit, dict):
                item.update({
                    "name": explicit.get("name") or zone_id,
                    "parent_zone_id": explicit.get("parent_zone_id"),
                    "level": explicit.get("level") or "custom",
                    "ue_level": explicit.get("ue_level") or "",
                    "streaming": copy.deepcopy(explicit.get("streaming") or {}),
                })
            zones.append(item)
        return {
            "project_id": project.get("id"),
            "zones": zones,
            "unassigned_count": unassigned_count,
            "total_instances": len(instances),
        }

    def save_catalog(self, payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("zones"), list):
            raise ZoneManagementError(
                "invalid_zone_catalog", "zones 必须是数组",
                [{"path": "zones", "message": "必须是数组"}],
            )
        project = self._active_project()
        expected_project_id = str(payload.get("expected_project_id") or "").strip()
        if expected_project_id and expected_project_id != project.get("id"):
            raise ZoneManagementConflictError("保存期间当前激活项目已切换")
        normalized = {}
        for index, raw in enumerate(payload["zones"]):
            if not isinstance(raw, dict):
                raise ZoneManagementError("invalid_zone", "Zone 必须是对象", [{"path": f"zones[{index}]", "message": "必须是对象"}])
            zone_id = _normalize_zone_id(raw.get("zone_id") or raw.get("id"))
            if not zone_id:
                raise ZoneManagementError("invalid_zone_id", "Zone ID 不能为空", [{"path": f"zones[{index}].zone_id", "message": "不能为空"}])
            if zone_id in normalized:
                raise ZoneManagementError("duplicate_zone_id", "Zone ID 不能重复", [{"path": f"zones[{index}].zone_id", "message": "不能重复"}])
            level = str(raw.get("level") or "custom").strip()
            if level not in ZONE_LEVELS:
                raise ZoneManagementError("invalid_zone_level", "Zone level 不受支持", [{"path": f"zones[{index}].level", "message": "仅支持 building/floor/room/area/custom"}])
            normalized[zone_id] = {
                "zone_id": zone_id,
                "name": str(raw.get("name") or zone_id).strip() or zone_id,
                "parent_zone_id": _normalize_zone_id(raw.get("parent_zone_id")),
                "level": level,
                "ue_level": str(raw.get("ue_level") or "").strip(),
                "streaming": copy.deepcopy(raw.get("streaming") or {}),
            }
        candidate = copy.deepcopy(project)
        candidate["zones"] = normalized
        hierarchy_errors = validate_zone_hierarchy(candidate)
        if hierarchy_errors:
            raise ZoneManagementError("invalid_zone_hierarchy", "Zone 层级校验失败", hierarchy_errors)
        project_id = project.get("id")

        def update(working):
            if working.get("id") != project_id:
                raise ZoneManagementConflictError("保存期间当前激活项目已切换")
            working["zones"] = copy.deepcopy(normalized)

        self.store.transact_active(update)
        return {"status": "ok", "project_id": project_id, "zones": list(normalized.values())}

    def assign(self, payload):
        if not isinstance(payload, dict):
            raise ZoneManagementError("invalid_request", "请求体必须是对象")
        project = self._active_project()
        expected_project_id = str(payload.get("expected_project_id") or "").strip()
        if expected_project_id and expected_project_id != project.get("id"):
            raise ZoneManagementConflictError(
                f"激活项目已从 {expected_project_id} 切换为 {project.get('id')}，请刷新后重试"
            )

        instance_ids = _normalize_instance_ids(payload.get("instance_ids"))
        zone_id = _normalize_zone_id(payload.get("zone_id"))
        if zone_id:
            catalog = zone_catalog(project)
            if zone_id in catalog and any(zone.get("parent_zone_id") == zone_id for zone in catalog.values()):
                raise ZoneManagementError(
                    "non_leaf_zone", "实例只能绑定叶子 Zone",
                    [{"path": "zone_id", "message": "该 Zone 仍有子 Zone"}],
                )
        try:
            result = self.store.assign_zone(
                instance_ids, zone_id,
                expected_project_id=expected_project_id or None,
            )
        except ProjectMismatch as e:
            raise ZoneManagementConflictError(
                f"激活项目已从 {e.expected} 切换为 {e.actual}，请刷新后重试"
            )
        result["updated_count"] = len(result["updated"])
        result["unchanged_count"] = len(result["unchanged"])
        result["missing_count"] = len(result["missing"])
        return result
