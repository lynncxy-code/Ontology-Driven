#!/usr/bin/env python3
"""Move live ZHHZ aircraft-related instances under the 航模设备 hierarchy path."""

from __future__ import annotations

import argparse
import json
import os

import psycopg
from psycopg.types.json import Jsonb


PROJECT_ID = "ds_1784694647848"
PROJECT_NAME = "ZHHZ"
TARGET_PATH = ["航空展馆", "航模设备"]
SOURCE_PATH_COUNTS = {
    ("航空展馆", "固定翼航空器"): 36,
    ("航空展馆", "航电、传感器与对抗设备"): 6,
    ("航空展馆", "航空部件与子系统"): 3,
    ("航空展馆", "航空武器与弹药"): 36,
    ("航空展馆", "无人及新型航空器"): 21,
    ("航空展馆", "旋翼航空器"): 18,
    ("航空展馆", "座舱与模拟训练系统"): 5,
}
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ontotwin:ontotwin@db:5432/ontotwin"
)


def inspect(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM project WHERE id = %s", (PROJECT_ID,))
        project = cur.fetchone()
        if project != (PROJECT_NAME,):
            raise RuntimeError(f"Expected ZHHZ project, got {project!r}")

        cur.execute(
            "SELECT hierarchy_path, count(*) FROM instance "
            "WHERE project_id = %s AND deleted_at IS NULL "
            "GROUP BY hierarchy_path",
            (PROJECT_ID,),
        )
        counts = {tuple(path or []): count for path, count in cur.fetchall()}

        cur.execute(
            "SELECT count(*) FROM instance WHERE project_id = %s AND deleted_at IS NULL",
            (PROJECT_ID,),
        )
        total = cur.fetchone()[0]

    unexpected = {
        "/".join(path): {"expected": expected, "actual": counts.get(path, 0)}
        for path, expected in SOURCE_PATH_COUNTS.items()
        if counts.get(path, 0) not in (0, expected)
    }
    if unexpected:
        raise RuntimeError("Source path counts changed: " + json.dumps(unexpected, ensure_ascii=False))

    return {
        "project_id": PROJECT_ID,
        "project_name": PROJECT_NAME,
        "live_instances": total,
        "target_path": TARGET_PATH,
        "target_before": counts.get(tuple(TARGET_PATH), 0),
        "source_counts": {
            "/".join(path): counts.get(path, 0) for path in SOURCE_PATH_COUNTS
        },
        "affected_instances": sum(counts.get(path, 0) for path in SOURCE_PATH_COUNTS),
    }


def apply(conn):
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (1784694647848,))
        before = inspect(conn)
        if before["affected_instances"] == 0:
            return before, before

        updated = 0
        with conn.cursor() as cur:
            for source_path in SOURCE_PATH_COUNTS:
                cur.execute(
                    "UPDATE instance SET hierarchy_path = %s "
                    "WHERE project_id = %s AND deleted_at IS NULL AND hierarchy_path = %s",
                    (Jsonb(TARGET_PATH), PROJECT_ID, Jsonb(list(source_path))),
                )
                updated += cur.rowcount

        if updated != before["affected_instances"]:
            raise RuntimeError(
                f"Updated {updated} rows, expected {before['affected_instances']}"
            )

        after = inspect(conn)
        if after["live_instances"] != before["live_instances"]:
            raise RuntimeError("Live instance count changed during path reclassification")
        if after["affected_instances"] != 0:
            raise RuntimeError("One or more source paths remain after reclassification")
        if after["target_before"] != before["target_before"] + updated:
            raise RuntimeError("Target hierarchy count does not match the expected result")
        return before, after


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with psycopg.connect(DATABASE_URL) as conn:
        if args.apply:
            before, after = apply(conn)
            result = {"mode": "apply", "before": before, "after": after}
        else:
            result = {"mode": "dry-run", "before": inspect(conn)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
