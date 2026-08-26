"""Type-level Blueprint containers for single-mesh UE representations."""

import copy
import re


DEFAULT_SLOT = "primary"
_SLOT_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")


class RepresentationContainerError(RuntimeError):
    def __init__(self, code, message, status=422, fields=None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.fields = fields or {}


def _text(value):
    return str(value or "").strip()


def normalize_blueprint_path(value):
    path = _text(value).replace("\\", "/")
    for prefix in ("BlueprintGeneratedClass'", "Blueprint'"):
        if path.startswith(prefix) and path.endswith("'"):
            path = path[len(prefix):-1]
            break
    return path


def normalize_slot(value):
    return _text(value) or DEFAULT_SLOT


def is_assembly_render_config(config):
    return isinstance(config, dict) and bool(
        config.get("render_parts") or config.get("assembly_signature")
    )


def resolve_effective_container(render_config, object_type, effective_model=None):
    """Resolve current type config, then frozen config when the type is unavailable."""
    render_config = render_config if isinstance(render_config, dict) else {}
    object_type = object_type if isinstance(object_type, dict) else {}
    effective_model = effective_model if isinstance(effective_model, dict) else {}

    if effective_model.get("mode") == "original_assembly":
        return {
            "enabled": False,
            "mode": "suppressed_assembly",
            "container_blueprint_id": "",
            "container_slot": DEFAULT_SLOT,
            "message": "组合模型不进入单模型 BP 容器。",
        }

    if object_type:
        path = normalize_blueprint_path(object_type.get("container_blueprint_id"))
        return {
            "enabled": bool(path),
            "mode": "type_default" if path else "direct",
            "container_blueprint_id": path,
            "container_slot": normalize_slot(object_type.get("container_slot")),
            "message": "使用类型 BP 容器。" if path else "直接加载表现资产。",
        }

    path = normalize_blueprint_path(render_config.get("container_blueprint_id"))
    return {
        "enabled": bool(path),
        "mode": "frozen" if path else "direct",
        "container_blueprint_id": path,
        "container_slot": normalize_slot(render_config.get("container_slot")),
        "message": "类型不可用，使用实例冻结的 BP 容器。" if path else "直接加载表现资产。",
    }


class RepresentationContainerService:
    def __init__(self, project_store, on_object_types_changed=None):
        self.project_store = project_store
        self.on_object_types_changed = on_object_types_changed

    @staticmethod
    def _has_capability(object_type):
        return "I3D_Representable" in (object_type or {}).get("injected_interfaces", [])

    @staticmethod
    def _validate_config(payload, allow_empty=True):
        path = normalize_blueprint_path((payload or {}).get("container_blueprint_id"))
        slot = normalize_slot((payload or {}).get("container_slot"))
        if not path and not allow_empty:
            raise RepresentationContainerError(
                "container_blueprint_required",
                "请填写容器 Blueprint 的 /Game 或 /Engine 路径。",
                fields={"container_blueprint_id": "required"},
            )
        if path and not path.startswith(("/Game/", "/Engine/")):
            raise RepresentationContainerError(
                "invalid_container_blueprint",
                "容器 Blueprint 必须使用 /Game 或 /Engine 资产路径。",
                fields={"container_blueprint_id": "invalid"},
            )
        if not _SLOT_PATTERN.fullmatch(slot):
            raise RepresentationContainerError(
                "invalid_container_slot",
                "容器槽位必须以英文字母开头，且只能包含字母、数字、点、短横线或下划线。",
                fields={"container_slot": "invalid"},
            )
        return path, slot

    @staticmethod
    def _require_expected_project(project, payload):
        expected = _text((payload or {}).get("expected_project_id"))
        if not expected:
            raise RepresentationContainerError(
                "expected_project_id_required",
                "缺少项目身份，请刷新页面后重试。",
                fields={"expected_project_id": "required"},
            )
        if expected != _text(project.get("id")):
            raise RepresentationContainerError(
                "active_project_changed",
                "当前项目已切换。请刷新类型列表后重新操作。",
                status=409,
            )
        return expected

    @staticmethod
    def _assembly_conflict_count(project, object_type_rid, object_type):
        if object_type.get("asset_id") or object_type.get("ue_asset_path"):
            return 0
        conflicts = 0
        for instance in (project.get("instances") or {}).values():
            if instance.get("object_type_rid") != object_type_rid:
                continue
            config = instance.get("render_config") or {}
            override = config.get("model_override") or {}
            if is_assembly_render_config(config) and not (
                override.get("asset_id") or override.get("ue_asset_path")
            ):
                conflicts += 1
        return conflicts

    def _active_type(self, object_type_rid):
        project = self.project_store.get_active_copy()
        if not project:
            raise RepresentationContainerError(
                "active_project_not_found", "请先激活一个项目。", status=404
            )
        object_type = (project.get("object_types") or {}).get(object_type_rid)
        if object_type is None:
            raise RepresentationContainerError(
                "object_type_not_found", "未找到这个类型，请刷新后重试。", status=404
            )
        return project, object_type

    def summary(self, object_type_rid):
        project, object_type = self._active_type(object_type_rid)
        resolved = resolve_effective_container({}, object_type)
        return {
            "project_id": project.get("id"),
            "object_type_rid": object_type_rid,
            "capability_enabled": self._has_capability(object_type),
            "assembly_conflict_count": self._assembly_conflict_count(
                project, object_type_rid, object_type
            ),
            **resolved,
        }

    def save(self, object_type_rid, payload):
        project, object_type = self._active_type(object_type_rid)
        expected = self._require_expected_project(project, payload)
        path, slot = self._validate_config(payload, allow_empty=True)
        if path and not self._has_capability(object_type):
            raise RepresentationContainerError(
                "representable_capability_required",
                "请先为该类型启用 I3D_Representable。",
                status=409,
            )
        conflict_count = self._assembly_conflict_count(project, object_type_rid, object_type)
        if path and conflict_count:
            raise RepresentationContainerError(
                "assembly_container_conflict",
                f"该类型有 {conflict_count} 个实例仍使用组合模型，不能启用单模型 BP 容器。",
                status=409,
            )

        def update(working):
            if expected != _text(working.get("id")):
                raise RepresentationContainerError(
                    "active_project_changed",
                    "当前项目已切换。请刷新类型列表后重新操作。",
                    status=409,
                )
            current = (working.get("object_types") or {}).get(object_type_rid)
            if current is None:
                raise RepresentationContainerError(
                    "object_type_not_found", "未找到这个类型，请刷新后重试。", status=404
                )
            if path:
                current["container_blueprint_id"] = path
                current["container_slot"] = slot
            else:
                current.pop("container_blueprint_id", None)
                current.pop("container_slot", None)

        self.project_store.transact_active(update)
        if self.on_object_types_changed:
            self.on_object_types_changed()
        result = self.summary(object_type_rid)
        result["message"] = "BP 容器配置已保存。" if path else "BP 容器已清除，实例恢复直接表现。"
        return result

    def clear(self, object_type_rid, payload):
        return self.save(object_type_rid, {
            **(payload or {}),
            "container_blueprint_id": "",
            "container_slot": DEFAULT_SLOT,
        })

    def apply_batch(self, payload):
        project = self.project_store.get_active_copy()
        if not project:
            raise RepresentationContainerError(
                "active_project_not_found", "请先激活一个项目。", status=404
            )
        expected = self._require_expected_project(project, payload)
        path, slot = self._validate_config(payload, allow_empty=False)
        requested = payload.get("object_type_rids")
        requested = set(requested) if isinstance(requested, list) else None
        eligible = []
        skipped = []
        for rid, object_type in (project.get("object_types") or {}).items():
            if requested is not None and rid not in requested:
                continue
            reason = ""
            if not self._has_capability(object_type):
                reason = "missing_representable"
            elif not (object_type.get("asset_id") or object_type.get("ue_asset_path")):
                reason = "missing_type_model"
            elif self._assembly_conflict_count(project, rid, object_type):
                reason = "assembly_conflict"
            if reason:
                skipped.append({"object_type_rid": rid, "reason": reason})
            else:
                eligible.append(rid)

        def update(working):
            if expected != _text(working.get("id")):
                raise RepresentationContainerError(
                    "active_project_changed",
                    "当前项目已切换。请刷新类型列表后重新操作。",
                    status=409,
                )
            types = working.get("object_types") or {}
            for rid in eligible:
                current = types.get(rid)
                if current is None:
                    continue
                current["container_blueprint_id"] = path
                current["container_slot"] = slot

        self.project_store.transact_active(update)
        if self.on_object_types_changed:
            self.on_object_types_changed()
        return {
            "status": "ok",
            "project_id": project.get("id"),
            "container_blueprint_id": path,
            "container_slot": slot,
            "affected_count": len(eligible),
            "affected_object_type_rids": eligible,
            "skipped": copy.deepcopy(skipped),
            "message": f"已为 {len(eligible)} 个已绑定资产类型应用 BP 容器。",
        }
