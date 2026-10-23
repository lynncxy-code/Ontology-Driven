#!/usr/bin/env python3
"""Compare live ZHHZ rows with the pre-consolidation restore database."""

from __future__ import annotations

import copy
import json
import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from consolidate_zhhz_types import DATABASE_URL, PROJECT_ID, TARGETS  # noqa: E402


BEFORE_URL = os.environ.get(
    "BEFORE_DATABASE_URL",
    "postgresql://ontotwin:ontotwin@db:5432/codex_verify_type_consolidation",
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def rows(conn, table, where_column):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table} WHERE {where_column} = %s ORDER BY 1, 2", (PROJECT_ID,))
        columns = [item.name for item in cur.description]
        return [dict(zip(columns, values)) for values in cur.fetchall()]


def keyed(items, keys):
    return {tuple(item[key] for key in keys): item for item in items}


def main() -> int:
    source_to_target = {
        source: (spec["rid"], spec["name"])
        for spec in TARGETS
        for source in spec["sources"]
    }
    with psycopg.connect(BEFORE_URL) as before, psycopg.connect(DATABASE_URL) as live:
        before_project = rows(before, "project", "id")
        live_project = rows(live, "project", "id")
        old = before_project[0] if before_project else {}
        new = live_project[0] if live_project else {}
        volatile_component_bindings = []
        for component_id in sorted(
            set((old.get("components") or {})) | set((new.get("components") or {}))
        ):
            before_binding = ((old.get("components") or {}).get(component_id) or {}).get(
                "bound_instance_id"
            )
            after_binding = ((new.get("components") or {}).get(component_id) or {}).get(
                "bound_instance_id"
            )
            if before_binding != after_binding:
                volatile_component_bindings.append(
                    {
                        "component_id": component_id,
                        "before": before_binding,
                        "after": after_binding,
                    }
                )
        old_project_compare = copy.deepcopy(before_project)
        new_project_compare = copy.deepcopy(live_project)
        for project_rows in (old_project_compare, new_project_compare):
            if project_rows:
                for component in (project_rows[0].get("components") or {}).values():
                    component.pop("bound_instance_id", None)
        if canonical(old_project_compare) != canonical(new_project_compare):
            changed = {
                key: {
                    "before_sha256": __import__("hashlib").sha256(
                        canonical(old.get(key)).encode("utf-8")
                    ).hexdigest(),
                    "after_sha256": __import__("hashlib").sha256(
                        canonical(new.get(key)).encode("utf-8")
                    ).hexdigest(),
                    "before_type": type(old.get(key)).__name__,
                    "after_type": type(new.get(key)).__name__,
                }
                for key in sorted(set(old) | set(new))
                if canonical(old.get(key)) != canonical(new.get(key))
            }
            raise RuntimeError(
                "Project row changed outside the approved Type consolidation: "
                + json.dumps(changed, ensure_ascii=False, sort_keys=True)
            )

        before_zones = rows(before, "zone", "project_id")
        live_zones = rows(live, "zone", "project_id")
        if canonical(before_zones) != canonical(live_zones):
            raise RuntimeError("Zone rows changed")

        before_instances = keyed(rows(before, "instance", "project_id"), ("project_id", "id"))
        live_instances = keyed(rows(live, "instance", "project_id"), ("project_id", "id"))
        if set(before_instances) != set(live_instances):
            raise RuntimeError("Instance row identity set changed")

        affected_all = 0
        affected_live = 0
        heartbeat_updates = 0
        for key, old_row in before_instances.items():
            new_row = copy.deepcopy(live_instances[key])
            expected = source_to_target.get(old_row.get("object_type_rid"))
            if expected:
                affected_all += 1
                if old_row.get("deleted_at") is None:
                    affected_live += 1
                if (new_row.get("object_type_rid"), new_row.get("object_type_name")) != expected:
                    raise RuntimeError(f"Unexpected target Type for instance {old_row['id']}")
            elif (
                new_row.get("object_type_rid") != old_row.get("object_type_rid")
                or new_row.get("object_type_name") != old_row.get("object_type_name")
            ):
                raise RuntimeError(f"Unapproved Type change for instance {old_row['id']}")

            old_compare = copy.deepcopy(old_row)
            old_compare.pop("object_type_rid", None)
            old_compare.pop("object_type_name", None)
            new_row.pop("object_type_rid", None)
            new_row.pop("object_type_name", None)
            old_last_seen = old_compare.pop("last_seen", None)
            new_last_seen = new_row.pop("last_seen", None)
            if canonical(old_last_seen) != canonical(new_last_seen):
                heartbeat_updates += 1
                if (
                    old_last_seen is not None
                    and new_last_seen is not None
                    and new_last_seen < old_last_seen
                ):
                    raise RuntimeError(f"last_seen moved backwards for instance {old_row['id']}")
            if canonical(old_compare) != canonical(new_row):
                changed = {
                    field: {
                        "before": old_compare.get(field),
                        "after": new_row.get(field),
                    }
                    for field in sorted(set(old_compare) | set(new_row))
                    if canonical(old_compare.get(field)) != canonical(new_row.get(field))
                }
                raise RuntimeError(
                    f"Non-Type fields changed for instance {old_row['id']}: "
                    + json.dumps(changed, ensure_ascii=False, default=str)
                )

        before_types = keyed(rows(before, "object_type", "project_id"), ("project_id", "rid"))
        live_types = keyed(rows(live, "object_type", "project_id"), ("project_id", "rid"))
        source_rids = set(source_to_target)
        target_rids = {spec["rid"] for spec in TARGETS}
        retained_rids = {key[1] for key in before_types} - source_rids
        if {key[1] for key in live_types} != retained_rids | target_rids:
            raise RuntimeError("Post-consolidation Type RID set is unexpected")
        for rid in retained_rids:
            key = (PROJECT_ID, rid)
            if canonical(before_types[key]) != canonical(live_types[key]):
                raise RuntimeError(f"Retained Type changed: {rid}")

        result = {
            "status": "VERIFY_OK",
            "before_types": len(before_types),
            "after_types": len(live_types),
            "all_instances": len(live_instances),
            "live_instances": sum(row.get("deleted_at") is None for row in live_instances.values()),
            "affected_all_instances": affected_all,
            "affected_live_instances": affected_live,
            "realtime_last_seen_updates": heartbeat_updates,
            "volatile_component_binding_changes_after_backend_restart": volatile_component_bindings,
            "unchanged_instance_fields": [
                "id",
                "transform/raw_state",
                "render_config",
                "classification",
                "hierarchy_path",
                "status",
                "created_at",
                "deleted_at",
            ],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
