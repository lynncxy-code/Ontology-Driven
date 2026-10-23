#!/usr/bin/env python3
"""Surgically roll back only the first, all-shapes round-five migration."""

from __future__ import annotations

import json
from pathlib import Path

from psycopg.types.json import Jsonb

from db import pg


PROJECT_ID = "ds_1784694647848"
PROJECT_NAME = "ZHHZ"
TYPE_RID = "zhhz.support"
TYPE_NAME = "支撑"
EXPECTED_INSTANCE_COUNT = 4441
RESULT_PATH = Path("/app/tools/ue_migration_result.json")


def main() -> None:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8-sig"))
    expected_ids = set((result.get("instances") or {}).values())
    if len(expected_ids) != EXPECTED_INSTANCE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_INSTANCE_COUNT} result instance IDs, got {len(expected_ids)}"
        )

    with pg.get_conn() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT name, dataset FROM project WHERE id=%s AND deleted_at IS NULL FOR UPDATE",
                    (PROJECT_ID,),
                )
                row = cur.fetchone()
                if not row or row[0] != PROJECT_NAME:
                    raise RuntimeError(f"Unexpected target project: {row!r}")
                dataset = row[1] or {}

                cur.execute(
                    """SELECT id FROM instance
                       WHERE project_id=%s AND deleted_at IS NULL AND object_type_rid=%s
                       ORDER BY id FOR UPDATE""",
                    (PROJECT_ID, TYPE_RID),
                )
                live_ids = {value[0] for value in cur.fetchall()}
                if live_ids != expected_ids:
                    raise RuntimeError(
                        "Live support instances do not exactly match the migration result: "
                        f"live={len(live_ids)} expected={len(expected_ids)} "
                        f"extra={len(live_ids - expected_ids)} missing={len(expected_ids - live_ids)}"
                    )

                cur.execute(
                    """SELECT name FROM object_type
                       WHERE project_id=%s AND rid=%s FOR UPDATE""",
                    (PROJECT_ID, TYPE_RID),
                )
                type_row = cur.fetchone()
                if type_row != (TYPE_NAME,):
                    raise RuntimeError(f"Unexpected support Type row: {type_row!r}")

                cur.execute(
                    """UPDATE instance SET deleted_at=now()
                       WHERE project_id=%s AND deleted_at IS NULL
                         AND object_type_rid=%s AND id=ANY(%s)""",
                    (PROJECT_ID, TYPE_RID, list(expected_ids)),
                )
                if cur.rowcount != EXPECTED_INSTANCE_COUNT:
                    raise RuntimeError(
                        f"Soft-deleted {cur.rowcount} support instances, expected {EXPECTED_INSTANCE_COUNT}"
                    )

                cur.execute(
                    "DELETE FROM object_type WHERE project_id=%s AND rid=%s",
                    (PROJECT_ID, TYPE_RID),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(f"Deleted {cur.rowcount} support Type rows, expected 1")

                graph_data = dataset.get("graph_data")
                removed_nodes = 0
                if isinstance(graph_data, dict):
                    nodes = graph_data.get("nodes") or []
                    kept_nodes = [
                        node
                        for node in nodes
                        if node.get("rid") != TYPE_RID and node.get("id") != TYPE_RID
                    ]
                    removed_nodes = len(nodes) - len(kept_nodes)
                    if removed_nodes != 1:
                        raise RuntimeError(
                            f"Removed {removed_nodes} support dataset nodes, expected 1"
                        )
                    graph_data["nodes"] = kept_nodes
                    dataset["node_count"] = len(kept_nodes)
                else:
                    raise RuntimeError("Project dataset has no graph_data object")

                cur.execute(
                    "UPDATE project SET dataset=%s WHERE id=%s",
                    (Jsonb(dataset), PROJECT_ID),
                )
                if cur.rowcount != 1:
                    raise RuntimeError("Failed to update the project dataset")

    audit = {
        "status": "rolled_back",
        "project_id": PROJECT_ID,
        "type_rid": TYPE_RID,
        "soft_deleted_instance_count": EXPECTED_INSTANCE_COUNT,
        "deleted_type_count": 1,
        "removed_dataset_node_count": 1,
        "scope_validation": "exact migration result ID set",
    }
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
