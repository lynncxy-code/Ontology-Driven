from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .validators import business_view_members, validate_url, zone_catalog, zone_descendants


def _scope_label(scope):
    if scope.get("instance_id"):
        return "instance"
    if scope.get("business_view_id"):
        return "business_view"
    if scope.get("zone_id") and scope.get("object_type_rid"):
        return "zone_type"
    if scope.get("object_type_rid"):
        return "type"
    if scope.get("zone_id"):
        return "zone"
    return "project"


def _candidate_scopes(trigger, context):
    if trigger == "open_detail":
        return [
            ("Instance", {"instance_id": context.get("instance_id")}),
            ("Zone+Type", {"zone_id": context.get("zone_id"), "object_type_rid": context.get("object_type_rid")}),
            ("Type", {"object_type_rid": context.get("object_type_rid")}),
            ("Zone", {"zone_id": context.get("zone_id")}),
            ("Project", {}),
        ]
    if trigger == "business_view_activated":
        return [
            ("BusinessView", {"business_view_id": context.get("business_view_id")}),
            ("Project", {}),
        ]
    if trigger == "zone_activated":
        return [("Zone", {"zone_id": context.get("zone_id")}), ("Project", {})]
    return [("Project", {})]


def _scope_equal(binding_scope, candidate):
    left = {key: value for key, value in (binding_scope or {}).items() if value not in (None, "")}
    right = {key: value for key, value in candidate.items() if value not in (None, "")}
    return left == right


def build_final_url(page, context, extra_params=None, allowed_hosts=None, policy_mode=None):
    base_url = str(page.get("base_url") or "").strip()
    issues = validate_url(base_url, allowed_hosts, policy_mode)
    if issues:
        raise ValueError(issues[0]["message"])
    parsed = urlsplit(base_url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    mapping = page.get("param_mapping") or {}
    for source, destination in mapping.items():
        value = context.get(source)
        if value not in (None, ""):
            query.append((str(destination), str(value)))
    declared = set(page.get("declared_extra_params") or [])
    for key, value in (extra_params or {}).items():
        if key not in declared:
            raise ValueError(f"额外参数未声明：{key}")
        if value not in (None, ""):
            query.append((str(key), str(value)))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def resolve_binding(project, config, payload):
    context = dict(payload.get("context") or {})
    trigger = str(payload.get("trigger") or context.get("trigger") or "").strip()
    context["trigger"] = trigger
    context.setdefault("project_id", project.get("id"))
    instance_id = context.get("instance_id")
    instance = (project.get("instances") or {}).get(instance_id) if instance_id else None
    if instance:
        context.setdefault("zone_id", instance.get("zone_id"))
        context.setdefault("object_type_rid", instance.get("object_type_rid"))

    bindings = config.get("bindings") or []
    chain = []
    winner = None
    for level, candidate in _candidate_scopes(trigger, context):
        if any(value in (None, "") for value in candidate.values()):
            chain.append({"level": level, "scope": candidate, "result": "context_missing"})
            continue
        matches = [binding for binding in bindings if isinstance(binding, dict) and binding.get("trigger") == trigger and _scope_equal(binding.get("scope"), candidate)]
        if not matches:
            chain.append({"level": level, "scope": candidate, "result": "no_binding"})
            continue
        selected = None
        disabled = []
        for binding in matches:
            if not binding.get("enabled", True):
                disabled.append(binding.get("binding_id"))
                continue
            selected = binding
            break
        if not selected:
            chain.append({"level": level, "scope": candidate, "result": "disabled", "binding_ids": disabled})
            continue
        winner = selected
        chain.append({
            "level": level, "scope": candidate, "result": "blocked" if selected.get("effect") == "block" else "matched",
            "binding_id": selected.get("binding_id"),
        })
        break

    result = {
        "trigger": trigger,
        "context": context,
        "chain": chain,
        "matched": bool(winner),
        "blocked": bool(winner and winner.get("effect") == "block"),
        "binding": winner,
        "page": None,
        "final_url": None,
        "scene_scope": None,
    }
    if not winner or result["blocked"]:
        return result
    page = next((item for item in config.get("pages") or [] if item.get("page_id") == winner.get("page_id") and item.get("enabled", True)), None)
    if not page:
        result["error"] = "page_disabled_or_not_found"
        return result
    policy = config.get("web_policy") or {}
    result["page"] = page
    result["final_url"] = build_final_url(
        page, context, payload.get("extra_params") or {}, policy.get("allowed_hosts") or [], None,
    )
    scope_type = _scope_label(winner.get("scope") or {})
    if context.get("business_view_id"):
        scope_type = "business_view"
    elif context.get("instance_id"):
        scope_type = "instance"
    elif context.get("zone_id"):
        scope_type = "zone"
    effect = (page.get("scope_effects") or {}).get(scope_type, "web_only")
    scene_behavior = "isolate_focus" if effect == "web_and_scene" else "web_only"
    if scope_type == "business_view" and context.get("business_view_id"):
        view = next((item for item in config.get("business_views") or []
                     if item.get("business_view_id") == context["business_view_id"]), None)
        if view and view.get("scene_behavior") in {"isolate_focus", "highlight", "web_only"}:
            scene_behavior = view["scene_behavior"]
    result["scene_scope"] = build_scene_scope(project, config, context, scope_type) if scene_behavior != "web_only" else None
    if result["scene_scope"] is not None:
        result["scene_scope"]["behavior"] = scene_behavior
    result["scope_effect"] = effect
    result["scene_behavior"] = scene_behavior
    return result


def build_scene_scope(project, config, context, scope_type):
    zones = zone_catalog(project)
    instances = project.get("instances") or {}
    visible = set()
    if scope_type == "instance" and context.get("instance_id") in instances:
        visible.add(context["instance_id"])
    elif scope_type == "zone" and context.get("zone_id"):
        permitted = zone_descendants(zones, context["zone_id"])
        visible = {instance_id for instance_id, item in instances.items() if (item or {}).get("zone_id") in permitted}
    elif scope_type == "business_view" and context.get("business_view_id"):
        view = next((item for item in config.get("business_views") or [] if item.get("business_view_id") == context["business_view_id"] and item.get("enabled", True)), None)
        visible = business_view_members(project, view or {}, zones)
        if context.get("zone_id"):
            permitted = zone_descendants(zones, context["zone_id"])
            visible = {instance_id for instance_id in visible if (instances.get(instance_id) or {}).get("zone_id") in permitted}
    unzoned = {instance_id for instance_id, item in instances.items() if not (item or {}).get("zone_id")}
    return {
        "scope_type": scope_type,
        "business_view_id": context.get("business_view_id"),
        "zone_id": context.get("zone_id"),
        "instance_id": context.get("instance_id"),
        "visible_instance_ids": sorted(visible | unzoned),
        "matched_instance_ids": sorted(visible),
        "matched_instance_count": len(visible),
        "unzoned_instance_count": len(unzoned),
    }
