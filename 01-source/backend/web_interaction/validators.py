import copy
import os
import re
from urllib.parse import urlsplit


STABLE_CONTEXT_KEYS = {
    "project_id", "business_view_id", "zone_id", "object_type_rid",
    "instance_id", "trigger",
}
TRIGGERS = {
    "open_detail", "project_home_activated", "zone_activated",
    "business_view_activated",
}
ZONE_LEVELS = {"building", "floor", "room", "area", "custom"}
SCOPE_EFFECTS = {"web_only", "web_and_scene"}
SCENE_BEHAVIORS = {"isolate_focus", "highlight", "web_only"}
ID_RE = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}$")


class WebInteractionValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors or []
        super().__init__("Web interaction validation failed")


def empty_config(base_revision=None):
    result = {
        "pages": [],
        "business_views": [],
        "bindings": [],
        "web_policy": {"allowed_hosts": []},
    }
    if base_revision is not None:
        result["base_revision"] = int(base_revision)
    return result


def normalize_config(value, base_revision=None):
    source = value if isinstance(value, dict) else {}
    normalized = empty_config(base_revision)
    for key in ("pages", "business_views", "bindings"):
        items = source.get(key)
        normalized[key] = copy.deepcopy(items) if isinstance(items, list) else []
    policy = source.get("web_policy")
    if isinstance(policy, dict):
        hosts = policy.get("allowed_hosts")
        normalized["web_policy"] = {
            "allowed_hosts": [str(host).strip().lower() for host in hosts if str(host).strip()]
            if isinstance(hosts, list) else []
        }
    if base_revision is None and "base_revision" in source:
        try:
            normalized["base_revision"] = int(source.get("base_revision"))
        except (TypeError, ValueError):
            normalized["base_revision"] = source.get("base_revision")
    return normalized


def zone_catalog(project):
    explicit = project.get("zones") or {}
    result = {}
    if isinstance(explicit, list):
        explicit = {str(item.get("zone_id") or item.get("id") or ""): item for item in explicit if isinstance(item, dict)}
    if isinstance(explicit, dict):
        for key, raw in explicit.items():
            if not isinstance(raw, dict):
                raw = {}
            zone_id = str(raw.get("zone_id") or raw.get("id") or key or "").strip()
            if not zone_id:
                continue
            result[zone_id] = {
                "zone_id": zone_id,
                "name": str(raw.get("name") or zone_id),
                "parent_zone_id": str(raw.get("parent_zone_id") or "").strip() or None,
                "level": str(raw.get("level") or "custom").strip(),
                "ue_level": str(raw.get("ue_level") or "").strip(),
                "streaming": copy.deepcopy(raw.get("streaming") or {}),
            }
    for instance in (project.get("instances") or {}).values():
        zone_id = str((instance or {}).get("zone_id") or "").strip()
        if zone_id and zone_id not in result:
            result[zone_id] = {
                "zone_id": zone_id, "name": zone_id, "parent_zone_id": None,
                "level": "custom", "ue_level": "", "streaming": {},
            }
    return result


def zone_descendants(zones, zone_id):
    children = {}
    for current_id, zone in zones.items():
        parent = zone.get("parent_zone_id")
        if parent:
            children.setdefault(parent, []).append(current_id)
    found = set()
    pending = [zone_id]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        pending.extend(children.get(current, []))
    return found


def validate_url(url, allowed_hosts=None, policy_mode=None):
    errors = []
    text = str(url or "").strip()
    try:
        parsed = urlsplit(text)
    except ValueError as exc:
        return [{"code": "invalid_url", "message": str(exc)}]
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        errors.append({"code": "dangerous_url_scheme", "message": "页面地址只允许 http 或 https"})
    if parsed.username is not None or parsed.password is not None:
        errors.append({"code": "embedded_credentials", "message": "页面地址不能内嵌账号或密码"})
    if not parsed.hostname:
        errors.append({"code": "url_host_required", "message": "页面地址缺少域名"})
    mode = str(policy_mode or os.environ.get("WEB_URL_POLICY", "open")).strip().lower()
    if mode not in {"open", "allowlist"}:
        mode = "open"
    hosts = {str(item).strip().lower() for item in (allowed_hosts or []) if str(item).strip()}
    if mode == "allowlist" and parsed.hostname:
        host = parsed.hostname.lower()
        netloc = parsed.netloc.lower()
        if host not in hosts and netloc not in hosts:
            errors.append({"code": "host_not_allowed", "message": f"域名 {host} 不在项目白名单"})
    return errors


def _error(errors, path, code, message):
    errors.append({"path": path, "code": code, "message": message})


def _check_id(errors, value, path, label):
    if not isinstance(value, str) or not ID_RE.fullmatch(value.strip()):
        _error(errors, path, "invalid_id", f"{label} 必须是 1-128 位稳定 ID")
        return ""
    return value.strip()


def validate_zone_hierarchy(project):
    errors = []
    zones = zone_catalog(project)
    for zone_id, zone in zones.items():
        parent = zone.get("parent_zone_id")
        if zone.get("level") not in ZONE_LEVELS:
            _error(errors, f"zones.{zone_id}.level", "invalid_zone_level", "Zone level 不受支持")
        if parent and parent not in zones:
            _error(errors, f"zones.{zone_id}.parent_zone_id", "zone_parent_not_found", "父 Zone 不存在")
    visiting = set()
    visited = set()

    def visit(zone_id):
        if zone_id in visiting:
            _error(errors, f"zones.{zone_id}.parent_zone_id", "zone_cycle", "Zone 层级不能形成循环")
            return
        if zone_id in visited:
            return
        visiting.add(zone_id)
        parent = (zones.get(zone_id) or {}).get("parent_zone_id")
        if parent in zones:
            visit(parent)
        visiting.discard(zone_id)
        visited.add(zone_id)

    for zone_id in zones:
        visit(zone_id)
    parents = {zone.get("parent_zone_id") for zone in zones.values() if zone.get("parent_zone_id")}
    for instance_id, instance in (project.get("instances") or {}).items():
        zone_id = str((instance or {}).get("zone_id") or "").strip()
        if zone_id and zone_id in parents:
            _error(errors, f"instances.{instance_id}.zone_id", "instance_bound_to_non_leaf_zone", "实例只能绑定叶子 Zone")
    return errors


def business_view_members(project, business_view, zones=None):
    zones = zones or zone_catalog(project)
    instances = project.get("instances") or {}
    groups = business_view.get("rule_groups") if isinstance(business_view, dict) else []
    if not isinstance(groups, list):
        return set()
    members = set()
    for group in groups:
        if not isinstance(group, dict):
            continue
        has_filter = any(isinstance(group.get(key), list) and group.get(key) for key in ("zone_ids", "object_type_rids", "instance_ids"))
        if not has_filter:
            continue
        permitted_zones = set()
        for zone_id in group.get("zone_ids") or []:
            permitted_zones.update(zone_descendants(zones, str(zone_id)))
        for instance_id, instance in instances.items():
            if group.get("zone_ids") and str((instance or {}).get("zone_id") or "") not in permitted_zones:
                continue
            if group.get("object_type_rids") and (instance or {}).get("object_type_rid") not in group["object_type_rids"]:
                continue
            if group.get("instance_ids") and instance_id not in group["instance_ids"]:
                continue
            members.add(instance_id)
    members.difference_update(str(item) for item in (business_view.get("exclude_instance_ids") or []))
    return members


def validate_config(project, value):
    config = normalize_config(value)
    errors = validate_zone_hierarchy(project)
    warnings = []
    pages = {}
    views = {}
    bindings = {}
    allowed_hosts = config["web_policy"]["allowed_hosts"]
    policy_mode = os.environ.get("WEB_URL_POLICY", "open").strip().lower()

    for index, page in enumerate(config["pages"]):
        path = f"pages[{index}]"
        if not isinstance(page, dict):
            _error(errors, path, "invalid_page", "页面资源必须是对象")
            continue
        page_id = _check_id(errors, page.get("page_id"), f"{path}.page_id", "page_id")
        if page_id in pages:
            _error(errors, f"{path}.page_id", "duplicate_page_id", "page_id 不能重复")
        elif page_id:
            pages[page_id] = page
        for issue in validate_url(page.get("base_url"), allowed_hosts, policy_mode):
            _error(errors, f"{path}.base_url", issue["code"], issue["message"])
        mapping = page.get("param_mapping") or {}
        if not isinstance(mapping, dict):
            _error(errors, f"{path}.param_mapping", "invalid_param_mapping", "参数映射必须是对象")
        else:
            destinations = set()
            for source, destination in mapping.items():
                if source not in STABLE_CONTEXT_KEYS:
                    _error(errors, f"{path}.param_mapping.{source}", "unsupported_context_key", "不支持的上下文来源")
                if not isinstance(destination, str) or not destination.strip():
                    _error(errors, f"{path}.param_mapping.{source}", "invalid_query_key", "URL 参数名不能为空")
                elif destination in destinations:
                    _error(errors, f"{path}.param_mapping.{source}", "duplicate_query_key", "URL 参数名不能重复")
                destinations.add(destination)
        extras = page.get("declared_extra_params") or []
        if not isinstance(extras, list) or any(not isinstance(item, str) or not item.strip() for item in extras):
            _error(errors, f"{path}.declared_extra_params", "invalid_extra_params", "额外参数声明必须是字符串数组")
        effects = page.get("scope_effects") or {}
        if not isinstance(effects, dict):
            _error(errors, f"{path}.scope_effects", "invalid_scope_effects", "范围效果必须是对象")
        else:
            for scope_type, effect in effects.items():
                if scope_type not in {"zone", "business_view", "instance"} or effect not in SCOPE_EFFECTS:
                    _error(errors, f"{path}.scope_effects.{scope_type}", "invalid_scope_effect", "只支持 web_only 或 web_and_scene")

    zones = zone_catalog(project)
    instance_ids = set((project.get("instances") or {}).keys())
    type_ids = set((project.get("object_types") or {}).keys())
    for index, view in enumerate(config["business_views"]):
        path = f"business_views[{index}]"
        if not isinstance(view, dict):
            _error(errors, path, "invalid_business_view", "BusinessView 必须是对象")
            continue
        view_id = _check_id(errors, view.get("business_view_id"), f"{path}.business_view_id", "business_view_id")
        if view_id in views:
            _error(errors, f"{path}.business_view_id", "duplicate_business_view_id", "business_view_id 不能重复")
        elif view_id:
            views[view_id] = view
        groups = view.get("rule_groups") or []
        if not isinstance(groups, list):
            _error(errors, f"{path}.rule_groups", "invalid_rule_groups", "规则组必须是数组")
            groups = []
        for group_index, group in enumerate(groups):
            group_path = f"{path}.rule_groups[{group_index}]"
            if not isinstance(group, dict):
                _error(errors, group_path, "invalid_rule_group", "规则组必须是对象")
                continue
            if not any(group.get(key) for key in ("zone_ids", "object_type_rids", "instance_ids")):
                _error(errors, group_path, "empty_rule_group", "规则组至少需要一个条件")
            for key, known in (("zone_ids", set(zones)), ("object_type_rids", type_ids), ("instance_ids", instance_ids)):
                values = group.get(key) or []
                if not isinstance(values, list):
                    _error(errors, f"{group_path}.{key}", "invalid_rule_values", "规则值必须是数组")
                else:
                    for value_id in values:
                        if value_id not in known:
                            _error(errors, f"{group_path}.{key}", "rule_reference_not_found", f"引用不存在：{value_id}")
        for value_id in view.get("exclude_instance_ids") or []:
            if value_id not in instance_ids:
                _error(errors, f"{path}.exclude_instance_ids", "instance_not_found", f"实例不存在：{value_id}")
        scene_behavior = view.get("scene_behavior")
        if scene_behavior not in (None, "") and scene_behavior not in SCENE_BEHAVIORS:
            _error(errors, f"{path}.scene_behavior", "invalid_scene_behavior", "场景行为不受支持")
        if view_id and not business_view_members(project, view, zones):
            warnings.append({"path": path, "code": "business_view_empty", "message": f"{view.get('name') or view_id} 当前匹配 0 个实例"})

    duplicate_keys = set()
    for index, binding in enumerate(config["bindings"]):
        path = f"bindings[{index}]"
        if not isinstance(binding, dict):
            _error(errors, path, "invalid_binding", "页面绑定必须是对象")
            continue
        binding_id = _check_id(errors, binding.get("binding_id"), f"{path}.binding_id", "binding_id")
        if binding_id in bindings:
            _error(errors, f"{path}.binding_id", "duplicate_binding_id", "binding_id 不能重复")
        elif binding_id:
            bindings[binding_id] = binding
        trigger = binding.get("trigger")
        if trigger not in TRIGGERS:
            _error(errors, f"{path}.trigger", "invalid_trigger", "触发类型不受支持")
        if binding.get("activation_mode") not in {"direct", "explicit"}:
            _error(errors, f"{path}.activation_mode", "invalid_activation_mode", "激活模式只支持 direct 或 explicit")
        effect = binding.get("effect")
        if effect not in {"open_web", "block"}:
            _error(errors, f"{path}.effect", "invalid_effect", "效果只支持 open_web 或 block")
        page_id = binding.get("page_id")
        if effect == "open_web" and page_id not in pages:
            _error(errors, f"{path}.page_id", "page_not_found", "绑定引用的页面不存在")
        if effect == "block" and page_id:
            _error(errors, f"{path}.page_id", "block_has_page", "block 规则不能引用页面")
        scope = binding.get("scope") or {}
        if not isinstance(scope, dict):
            _error(errors, f"{path}.scope", "invalid_scope", "scope 必须是对象")
            scope = {}
        allowed_scope_keys = {"zone_id", "object_type_rid", "instance_id", "business_view_id"}
        if any(key not in allowed_scope_keys for key in scope):
            _error(errors, f"{path}.scope", "invalid_scope_key", "scope 含不支持的字段")
        present = {key for key in allowed_scope_keys if scope.get(key)}
        if present not in (set(), {"zone_id"}, {"object_type_rid"}, {"zone_id", "object_type_rid"}, {"instance_id"}, {"business_view_id"}):
            _error(errors, f"{path}.scope", "invalid_scope_shape", "scope 组合不受支持")
        for key, known in (("zone_id", set(zones)), ("object_type_rid", type_ids), ("instance_id", instance_ids), ("business_view_id", set(views))):
            if scope.get(key) and scope[key] not in known:
                _error(errors, f"{path}.scope.{key}", "scope_reference_not_found", f"引用不存在：{scope[key]}")
        if binding.get("enabled", True) and effect == "open_web":
            duplicate_key = (trigger, tuple(sorted((key, str(value)) for key, value in scope.items() if value)))
            if duplicate_key in duplicate_keys:
                _error(errors, path, "duplicate_open_web_binding", "同一 trigger 与作用域只能有一条有效 open_web 规则")
            duplicate_keys.add(duplicate_key)

    unzoned = sum(1 for instance in (project.get("instances") or {}).values() if not (instance or {}).get("zone_id"))
    if unzoned:
        warnings.append({"path": "instances", "code": "unzoned_instances", "message": f"当前有 {unzoned} 个未分区实例会保持常驻", "count": unzoned})
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "config": config,
        "summary": {
            "page_count": len(config["pages"]),
            "business_view_count": len(config["business_views"]),
            "binding_count": len(config["bindings"]),
            "unzoned_instance_count": unzoned,
            "url_policy": policy_mode if policy_mode in {"open", "allowlist"} else "open",
        },
    }
