"""Restore Equipment as a business ObjectType in SCC W18.

Dry-run is the default. Pass ``--apply`` to persist both the project dataset and
the Neo4j semantic registry patch. The migration is idempotent and writes a
JSON backup before changing PostgreSQL.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from project_store import ProjectStore  # noqa: E402
from scc_w18_semantic_mapping import (  # noqa: E402
    DATASET_ID,
    LEGACY_EQUIPMENT_INTERFACE_RID,
    ensure_equipment_semantics,
)


PATCH_PATH = BACKEND_DIR / "ontology_registry" / "ontotwin.ds_1786957368669.equipment_object_fix.cypher"


def _split_cypher(text: str) -> list[str]:
    return [statement.strip() for statement in text.split(";") if statement.strip()]


def _neo4j_snapshot_and_apply(apply: bool) -> dict:
    from db.graph import get_driver

    driver = get_driver()
    snapshot_query = """
    MATCH (i:InterfaceType {rid: $legacy_rid})
    OPTIONAL MATCH (source:ObjectType)-[:IMPLEMENTS]->(i)
    RETURN i{.*} AS interface, collect(DISTINCT source{.*}) AS mapped_types
    """
    with driver.session() as session:
        row = session.run(snapshot_query, legacy_rid=LEGACY_EQUIPMENT_INTERFACE_RID).single()
        snapshot = dict(row) if row else {"interface": None, "mapped_types": []}
        if apply:
            statements = _split_cypher(PATCH_PATH.read_text(encoding="utf-8"))
            session.execute_write(lambda tx: [tx.run(statement).consume() for statement in statements])
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--backup-dir",
        default=str(BACKEND_DIR / "tools"),
        help="directory for the pre-migration JSON backup",
    )
    args = parser.parse_args()

    store = ProjectStore()
    active_before = store.get_active_id()
    if active_before != DATASET_ID and not store.activate(DATASET_ID):
        raise SystemExit(f"SCC W18 project not found: {DATASET_ID}")

    dataset = copy.deepcopy(store.get_active_dataset() or {})
    object_types = copy.deepcopy(store.get_object_types() or {})
    backup = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_id": DATASET_ID,
        "active_project_before": active_before,
        "dataset": copy.deepcopy(dataset),
        "object_types": copy.deepcopy(object_types),
        "neo4j": _neo4j_snapshot_and_apply(False),
    }
    result = ensure_equipment_semantics(dataset, object_types)

    if not args.apply:
        print(json.dumps({
            "mode": "dry_run",
            **result,
            "neo4j_mapped_types": len(backup["neo4j"].get("mapped_types") or []),
        }, ensure_ascii=False, indent=2))
        return 0

    backup_dir = Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"scc_w18_equipment_semantics_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2), encoding="utf-8")

    store.set_dataset(dataset)
    store.set_object_types(object_types)
    neo4j_before = _neo4j_snapshot_and_apply(True)
    print(json.dumps({
        "mode": "applied",
        **result,
        "backup": str(backup_path),
        "neo4j_mapped_types_before": len(neo4j_before.get("mapped_types") or []),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
