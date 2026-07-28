"""Instance-scoped model override service for OntoTwin Nexus 3.3.3."""

import copy
import datetime as dt
import time


class InstanceModelBindingError(RuntimeError):
    def __init__(self, code, message, status=422, fields=None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.fields = fields or {}


class ActiveProjectChangedError(InstanceModelBindingError):
    def __init__(self):
        super().__init__(
            "active_project_changed",
            "当前项目已切换。请刷新实例列表后重新操作。",
            status=409,
        )


def is_assembly_render_config(config):
    return isinstance(config, dict) and (
        "render_parts" in config or "assembly_signature" in config
    )


def model_source(path, asset_id=""):
    value = str(path or asset_id or "").strip()
    if not value:
        return "none"
    if value.startswith("artstudio:"):
        return "artstudio"
    if value.startswith("/Game/") or value.startswith("/Engine/"):
        return "ue_cooked"
    if value.lower().endswith((".glb", ".gltf")):
        return "local"
    return "manual"


def model_label(path, asset_id=""):
    value = str(path or asset_id or "").strip().replace("\\", "/")
    if not value:
        return "未配置模型"
    if value.startswith("artstudio:"):
        stable_asset_id = value[len("artstudio:"):].split(":v", 1)[0]
        return f"ArtStudio 资产 {stable_asset_id}"
    return value.rsplit("/", 1)[-1] or value


def _model_payload(mode, asset_id, ue_asset_path, source=None, label=None):
    return {
        "mode": mode,
        "asset_id": str(asset_id or ""),
        "ue_asset_path": str(ue_asset_path or ""),
        "source": source or model_source(ue_asset_path, asset_id),
        "label": label or model_label(ue_asset_path, asset_id),
    }


def resolve_effective_model(raw_state, render_config, object_type, asset_catalog):
    """Resolve representation using override > type > assembly > placeholder."""
    raw_state = raw_state or {}
    render_config = render_config or {}
    object_type = object_type or {}
    asset_catalog = asset_catalog or {}

    override = render_config.get("model_override")
    if isinstance(override, dict) and (
        override.get("ue_asset_path") or override.get("asset_id")
    ):
        return _model_payload(
            "instance_override",
            override.get("asset_id"),
            override.get("ue_asset_path") or override.get("asset_id"),
            override.get("source"),
            override.get("label"),
        )

    if object_type:
        # A type default exists only when the type itself has a binding.  Do not
        # fall back to raw_state here: migrated instances often carry an old
        # asset_id there, and treating it as a type default would hide their
        # preserved original assembly.
        asset_id = object_type.get("asset_id") or ""
        asset_meta = asset_catalog.get(asset_id, {})
        ue_asset_path = (
            object_type.get("ue_asset_path")
            or asset_meta.get("ue_path")
            or asset_id
        )
        if asset_id or ue_asset_path:
            return _model_payload("type_default", asset_id, ue_asset_path)

    if is_assembly_render_config(render_config):
        asset_id = render_config.get("asset_id") or raw_state.get("asset_id", "")
        return _model_payload(
            "original_assembly",
            asset_id,
            render_config.get("ue_asset_path") or asset_id,
            "assembly",
            render_config.get("object_type_name") or "原始组合模型",
        )

    # Compatibility only: a moved instance can still render its old frozen config.
    if render_config:
        asset_id = render_config.get("asset_id") or raw_state.get("asset_id", "")
        ue_asset_path = render_config.get("ue_asset_path") or asset_id
        mode = "legacy_frozen" if (asset_id or ue_asset_path) else "placeholder"
        return _model_payload(mode, asset_id, ue_asset_path)

    return _model_payload("placeholder", "", "")


def _normalize_runtime_model_name(value):
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        return ""
    lower = text.lower()
    for prefix in ("/static/models/", "static/models/", "/models/", "models/"):
        if lower.startswith(prefix):
            text = text.rsplit("/", 1)[-1]
            lower = text.lower()
            break
    if "/" in text:
        return ""
    if lower.endswith((".glb", ".gltf")):
        return text
    if "." not in text:
        return f"{text}.glb"
    return ""


class InstanceModelBindingService:
    def __init__(
        self,
        project_store,
        asset_catalog,
        artstudio_client,
        on_object_types_changed=None,
    ):
        self.project_store = project_store
        self.asset_catalog = asset_catalog or {}
        self.artstudio = artstudio_client
        self.on_object_types_changed = on_object_types_changed

    @staticmethod
    def _has_capability(object_type):
        return "I3D_Representable" in (object_type or {}).get("injected_interfaces", [])

    def _active_context(self, instance_id):
        project = self.project_store.get_active_copy()
        if not project:
            raise InstanceModelBindingError(
                "active_project_not_found", "请先激活一个项目。", status=404
            )
        instance = (project.get("instances") or {}).get(instance_id)
        if not instance:
            raise InstanceModelBindingError(
                "instance_not_found", "未找到这个实例，请刷新后重试。", status=404
            )
        object_type = (project.get("object_types") or {}).get(
            instance.get("object_type_rid"), {}
        )
        return project, instance, object_type

    def _model_status(self, effective, capability_enabled):
        if not capability_enabled:
            return {
                "code": "capability_blocked",
                "label": "暂不可渲染",
                "message": "当前类型尚未启用三维表现能力。",
            }
        if effective["mode"] == "placeholder":
            return {
                "code": "unconfigured",
                "label": "等待配置",
                "message": "当前没有可用模型，UE 将显示占位模型。",
            }
        path = effective.get("ue_asset_path") or ""
        if path.startswith(getattr(self.artstudio, "PREFIX", "artstudio:")):
            return {
                "code": "available",
                "label": "可获取",
                "message": "UE 首次使用时会下载模型，并缓存到当前项目或程序。",
            }
        return {"code": "ready", "label": "已就绪", "message": "模型配置可直接下发。"}

    def summary(self, instance_id):
        project, instance, object_type = self._active_context(instance_id)
        render_config = instance.get("render_config") or {}
        effective = resolve_effective_model(
            instance.get("raw_state"), render_config, object_type, self.asset_catalog
        )
        inherited_config = copy.deepcopy(render_config)
        inherited_config.pop("model_override", None)
        inherited = resolve_effective_model(
            instance.get("raw_state"), inherited_config, object_type, self.asset_catalog
        )
        capability_enabled = self._has_capability(object_type)
        online = (time.time() - float(instance.get("last_seen") or 0)) < 3.0
        model_status = self._model_status(effective, capability_enabled)
        if not capability_enabled:
            delivery = {
                "code": "not_applicable",
                "label": "未下发",
                "message": "启用三维表现能力后才能下发模型。",
            }
        elif online:
            delivery = {
                "code": "delivered",
                "label": "已下发",
                "message": "实例在线；模型配置已进入实时快照。",
            }
        else:
            delivery = {
                "code": "waiting_for_instance",
                "label": "等待实例上线",
                "message": "配置已保存，实例上线后自动生效。",
            }

        type_asset_id = object_type.get("asset_id") or ""
        type_path = object_type.get("ue_asset_path") or (
            self.asset_catalog.get(type_asset_id, {}).get("ue_path") if type_asset_id else ""
        ) or type_asset_id
        type_default = _model_payload(
            "type_default" if type_path else "placeholder", type_asset_id, type_path
        )
        assembly = None
        if is_assembly_render_config(render_config):
            assembly = {
                "part_count": len(render_config.get("render_parts") or []),
                "assembly_signature": render_config.get("assembly_signature") or "",
                "label": render_config.get("object_type_name") or "原始组合模型",
            }
        override = render_config.get("model_override")
        return {
            "project_id": project.get("id"),
            "instance_id": instance_id,
            "object_type_rid": instance.get("object_type_rid") or "",
            "object_type_name": instance.get("object_type_name") or "",
            "capability": {
                "enabled": capability_enabled,
                "required": "I3D_Representable",
            },
            "effective_model": effective,
            "inherited_model": inherited,
            "type_default": type_default,
            "instance_override": copy.deepcopy(override) if isinstance(override, dict) else None,
            "original_assembly": assembly,
            "model_status": model_status,
            "delivery_status": delivery,
        }

    def _validate_selection(self, payload):
        file_number = str(payload.get("file_number") or "").strip()
        requested_path = str(payload.get("ue_asset_path") or "").strip()
        candidate = file_number or requested_path
        if not candidate:
            raise InstanceModelBindingError(
                "model_required", "请选择一个模型，或填写可用的模型路径。",
                fields={"file_number": "required"},
            )

        if candidate.isdigit():
            detail = self.artstudio.fetch_detail(candidate)
            if not detail:
                raise InstanceModelBindingError(
                    "artstudio_asset_unavailable",
                    "暂时无法读取这个 ArtStudio 资产，请稍后重试。",
                    status=502,
                )
            if not self.artstudio.pick_glb_file(detail):
                raise InstanceModelBindingError(
                    "unsupported_model_format",
                    "这个资产暂不包含可用的 GLB/GLTF 模型。",
                )
            version = detail.get("version") or 1
            stable_id = self.artstudio.make_stable_id(candidate, version)
            return {
                "asset_id": candidate,
                "ue_asset_path": stable_id,
                "source": "artstudio_mine" if payload.get("source") == "artstudio_mine" else "artstudio",
                "label": detail.get("name") or f"ArtStudio 资产 {candidate}",
            }

        asset_meta = self.asset_catalog.get(candidate)
        if asset_meta:
            return {
                "asset_id": candidate,
                "ue_asset_path": requested_path or asset_meta.get("ue_path") or candidate,
                "source": "mock",
                "label": asset_meta.get("name") or candidate,
            }

        if candidate.startswith("/Game/") or candidate.startswith("/Engine/"):
            return {
                "asset_id": candidate,
                "ue_asset_path": requested_path or candidate,
                "source": "ue_cooked",
                "label": model_label(requested_path or candidate, candidate),
            }

        runtime_name = _normalize_runtime_model_name(candidate)
        if runtime_name:
            return {
                "asset_id": runtime_name,
                "ue_asset_path": runtime_name,
                "source": "local",
                "label": runtime_name,
            }

        raise InstanceModelBindingError(
            "invalid_model_reference",
            "模型路径不可用。可填写 ArtStudio 资产编号、Models 目录文件名，或 /Game、/Engine 资产路径。",
            fields={"file_number": "invalid"},
        )

    def save(self, instance_id, payload):
        payload = payload or {}
        project, _instance, object_type = self._active_context(instance_id)
        expected_project_id = str(
            payload.get("expected_project_id") or project.get("id") or ""
        ).strip()
        if expected_project_id != str(project.get("id") or ""):
            raise ActiveProjectChangedError()
        if not self._has_capability(object_type):
            raise InstanceModelBindingError(
                "representable_capability_required",
                "当前类型尚未启用三维表现能力，请先到本体配置中心启用。",
                status=409,
            )

        selection = self._validate_selection(payload)
        saved_at = dt.datetime.now(dt.timezone.utc).isoformat()

        def update(working):
            if expected_project_id != str(working.get("id") or ""):
                raise ActiveProjectChangedError()
            instance = (working.get("instances") or {}).get(instance_id)
            if not instance:
                raise InstanceModelBindingError(
                    "instance_not_found", "未找到这个实例，请刷新后重试。", status=404
                )
            current_type = (working.get("object_types") or {}).get(
                instance.get("object_type_rid"), {}
            )
            if not self._has_capability(current_type):
                raise InstanceModelBindingError(
                    "representable_capability_required",
                    "当前类型尚未启用三维表现能力，请先到本体配置中心启用。",
                    status=409,
                )
            config = instance.setdefault("render_config", {})
            previous = config.get("model_override") or {}
            config["model_override"] = {
                "schema_version": 1,
                **selection,
                "revision": int(previous.get("revision") or 0) + 1,
                "updated_at": saved_at,
            }

        self.project_store.transact_active(update)
        result = self.summary(instance_id)
        result["message"] = "已为此实例保存模型覆盖。"
        return result

    def clear(self, instance_id, payload=None):
        payload = payload or {}
        project, _instance, _object_type = self._active_context(instance_id)
        expected_project_id = str(
            payload.get("expected_project_id") or project.get("id") or ""
        ).strip()
        if expected_project_id != str(project.get("id") or ""):
            raise ActiveProjectChangedError()

        def update(working):
            if expected_project_id != str(working.get("id") or ""):
                raise ActiveProjectChangedError()
            instance = (working.get("instances") or {}).get(instance_id)
            if not instance:
                raise InstanceModelBindingError(
                    "instance_not_found", "未找到这个实例，请刷新后重试。", status=404
                )
            config = instance.setdefault("render_config", {})
            config.pop("model_override", None)

        self.project_store.transact_active(update)
        result = self.summary(instance_id)
        mode = result["effective_model"]["mode"]
        messages = {
            "type_default": "已取消实例模型覆盖，当前跟随类型默认模型。",
            "original_assembly": "已取消实例模型覆盖，当前使用实例原始模型。",
            "placeholder": "已取消实例模型覆盖，当前暂无可用模型。",
        }
        result["message"] = messages.get(mode, "已取消实例模型覆盖。")
        return result

    def clear_type_default(self, object_type_rid):
        project = self.project_store.get_active_copy()
        if not project:
            raise InstanceModelBindingError(
                "active_project_not_found", "请先激活一个项目。", status=404
            )
        if object_type_rid not in (project.get("object_types") or {}):
            raise InstanceModelBindingError(
                "object_type_not_found", "未找到这个类型，请刷新后重试。", status=404
            )

        affected_instance_count = 0
        for instance in (project.get("instances") or {}).values():
            if instance.get("object_type_rid") != object_type_rid:
                continue
            override = (instance.get("render_config") or {}).get("model_override")
            if not isinstance(override, dict) or not (
                override.get("ue_asset_path") or override.get("asset_id")
            ):
                affected_instance_count += 1

        def update(working):
            object_type = (working.get("object_types") or {}).get(object_type_rid)
            if object_type is None:
                raise InstanceModelBindingError(
                    "object_type_not_found", "未找到这个类型，请刷新后重试。", status=404
                )
            object_type["asset_id"] = ""
            object_type["ue_asset_path"] = ""

        self.project_store.transact_active(update)
        if self.on_object_types_changed:
            self.on_object_types_changed()
        return {
            "status": "ok",
            "object_type_rid": object_type_rid,
            "asset_id": "",
            "ue_asset_path": "",
            "affected_instance_count": affected_instance_count,
            "message": "已清除类型默认模型。未设置实例覆盖的实例将使用各自原始模型或占位模型。",
        }
