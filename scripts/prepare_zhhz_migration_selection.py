"""Split the reviewed ZHHZ taxonomy into UE-resolvable and deferred rows.

The reviewed taxonomy is based on Datasmith handles.  A row is safe for the
mother-Actor migration only when the read-only UE audit resolved that handle to
one concrete UE actor GUID under the 0713 scene root.  Unmatched source groups
remain explicit in a deferred CSV instead of being silently discarded.
"""

from __future__ import annotations

import argparse
import csv
import json
import os


SELECTION_FIELDS = (
    "handle",
    "label",
    "business_type",
    "selection_source",
    "ue_guid",
    "ue_scene_root",
    "ue_path",
)
DEFERRED_FIELDS = (
    "handle",
    "label",
    "business_type",
    "selection_source",
    "defer_reason",
)


def _write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build(taxonomy_path, crosswalk_path, selection_path, deferred_path):
    with open(taxonomy_path, "r", encoding="utf-8-sig", newline="") as stream:
        taxonomy = list(csv.DictReader(stream))
    with open(crosswalk_path, "r", encoding="utf-8") as stream:
        crosswalk = json.load(stream)
    by_handle = {
        str(row.get("datasmith_handle") or "").strip(): row
        for row in crosswalk.get("groups") or []
    }

    selected = []
    deferred = []
    seen = set()
    selected_guid_to_row = {}
    for source in taxonomy:
        handle = str(source.get("handle") or "").strip()
        if not handle or handle in seen:
            raise ValueError(f"Invalid or duplicate taxonomy handle: {handle!r}")
        seen.add(handle)
        match = by_handle.get(handle) or {}
        guid = str(match.get("ue_guid") or "").strip()
        scene_root = str(match.get("ue_scene_root") or "").strip()
        if guid and scene_root == "0713":
            normalized_guid = "".join(
                character for character in guid.upper()
                if character in "0123456789ABCDEF"
            )
            previous = selected_guid_to_row.get(normalized_guid)
            if previous:
                if previous["business_type"] != (source.get("business_type") or ""):
                    raise ValueError(
                        "One UE mother Actor was assigned conflicting business types: "
                        f"{previous['handle']} and {handle}"
                    )
                deferred.append({
                    "handle": handle,
                    "label": source.get("label") or "",
                    "business_type": source.get("business_type") or "",
                    "selection_source": source.get("selection_source") or "",
                    "defer_reason": (
                        "Duplicate Datasmith source record for selected UE mother Actor "
                        f"(canonical handle {previous['handle']})"
                    ),
                })
                continue
            row = {
                "handle": handle,
                "label": source.get("label") or "",
                "business_type": source.get("business_type") or "",
                "selection_source": source.get("selection_source") or "",
                "ue_guid": guid,
                "ue_scene_root": scene_root,
                "ue_path": match.get("ue_path") or "",
            }
            selected.append(row)
            selected_guid_to_row[normalized_guid] = row
        else:
            reason = (
                "Datasmith source group has no unique UE mother Actor match"
                if not guid
                else f"Resolved outside required 0713 scene root: {scene_root or 'unknown'}"
            )
            deferred.append({
                "handle": handle,
                "label": source.get("label") or "",
                "business_type": source.get("business_type") or "",
                "selection_source": source.get("selection_source") or "",
                "defer_reason": reason,
            })

    _write_csv(selection_path, SELECTION_FIELDS, selected)
    _write_csv(deferred_path, DEFERRED_FIELDS, deferred)
    print(json.dumps({
        "reviewed": len(taxonomy),
        "selected": len(selected),
        "deferred": len(deferred),
        "selection_path": os.path.abspath(selection_path),
        "deferred_path": os.path.abspath(deferred_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--crosswalk", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--deferred", required=True)
    args = parser.parse_args()
    build(args.taxonomy, args.crosswalk, args.selection, args.deferred)
