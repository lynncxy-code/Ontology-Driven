"""
Build a Neo4j Cypher patch from an edited UE migration classification CSV.

Rows with action=create_experimental create project/legacy candidate ObjectTypes in the
ontology graph. They are marked EXPERIMENTAL and trace their UE source fields through x_*.
After applying the Cypher, run:
  python -m tools.sync_types_from_graph --apply --add-missing
"""

import argparse
import csv
import hashlib
import json
import os
import re
import uuid


API_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def _api_name(raw):
    slug = re.sub(r"[^a-z0-9]+", "_", str(raw or "").lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not API_RE.match(slug):
        slug = "mig_" + hashlib.md5(str(raw).encode("utf-8")).hexdigest()[:10]
    return slug


def _rid(group_key):
    return f"ri.obj.{uuid.uuid5(uuid.NAMESPACE_URL, 'ontotwin:migration:' + group_key)}"


def _cypher_str(value):
    return json.dumps(value or "", ensure_ascii=False)


def build(csv_path, output_path, default_interfaces=None):
    default_interfaces = default_interfaces or ["i3d_representable", "i3d_spatial"]
    lines = [
        "// OntoTwin UE migration ontology patch",
        "// Apply in Neo4j Browser or cypher-shell, then sync_types_from_graph --apply --add-missing.",
        "",
    ]
    created = 0
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            action = (row.get("action") or "").strip().lower()
            if action != "create_experimental":
                continue
            group_key = (row.get("group_key") or "").strip()
            name = (row.get("suggested_object_type_name") or "").strip()
            if not group_key or not name:
                continue
            rid = (row.get("suggested_object_type_rid") or "").strip() or _rid(group_key)
            api = _api_name(name or group_key)
            x_block_name = rid
            lines.append(
                "MERGE (o:ObjectType {rid: %s})\n"
                "SET o.api_name = %s,\n"
                "    o.display_name = %s,\n"
                "    o.lifecycle_status = 'EXPERIMENTAL',\n"
                "    o.x_block_name = %s,\n"
                "    o.x_source = 'ue_migration',\n"
                "    o.x_origin = 'ue_migration_csv',\n"
                "    o.x_group_key = %s,\n"
                "    o.x_source_folder_path = %s,\n"
                "    o.x_source_asset_path = %s;"
                % (
                    _cypher_str(rid),
                    _cypher_str(api),
                    _cypher_str(name),
                    _cypher_str(x_block_name),
                    _cypher_str(group_key),
                    _cypher_str(row.get("source_folder_path")),
                    _cypher_str(row.get("asset_path")),
                )
            )
            for iface_api in default_interfaces:
                lines.append(
                    "MATCH (o:ObjectType {rid: %s})\n"
                    "MATCH (i:InterfaceType {api_name: %s})\n"
                    "MERGE (o)-[:IMPLEMENTS]->(i);"
                    % (_cypher_str(rid), _cypher_str(iface_api))
                )
            lines.append("")
            created += 1

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"写出 {created} 个实验态本体类型补丁: {output_path}")


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(here, "ue_migration_classification.csv"))
    ap.add_argument("--output", default=os.path.join(here, "ue_migration_ontology_patch.cypher"))
    args = ap.parse_args()
    build(args.csv, args.output)
