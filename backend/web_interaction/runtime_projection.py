import copy

from .validators import business_view_members, zone_catalog


def build_runtime_projection(project, web, known_revision=None, binding=None):
    revision = int(web.get("revision") or 0)
    try:
        known = int(known_revision) if known_revision not in (None, "") else None
    except (TypeError, ValueError):
        known = None
    base = {
        "status": "unchanged" if known == revision else "ok",
        "project_id": project.get("id"),
        "revision": revision,
    }
    if binding is not None:
        base["binding"] = binding
    if known == revision:
        return base
    config = copy.deepcopy(web.get("published") or {})
    zones = zone_catalog(project)
    memberships = {}
    for view in config.get("business_views") or []:
        if view.get("enabled", True):
            memberships[view.get("business_view_id")] = sorted(business_view_members(project, view, zones))
    base.update({
        "schema_version": int(web.get("schema_version") or 1),
        "config": config,
        "zones": list(zones.values()),
        "instance_index": [
            {
                "instance_id": instance_id,
                "zone_id": (instance or {}).get("zone_id"),
                "object_type_rid": (instance or {}).get("object_type_rid"),
            }
            for instance_id, instance in (project.get("instances") or {}).items()
        ],
        "business_view_memberships": memberships,
    })
    return base
