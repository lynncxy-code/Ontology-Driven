"""Export one bound UE project's published runtime view without mutating it.

Run inside the existing backend container so the exporter uses the exact
application code and database connection of the authoring environment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


def compact_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=False, separators=(",", ":")
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> dict[str, Any]:
    payload = compact_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "path": path.name,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def walk_values(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def require_response(client, path: str, headers: dict[str, str]):
    response = client.get(path, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(
            f"GET {path} returned HTTP {response.status_code}: "
            f"{response.get_data(as_text=True)[:1000]}"
        )
    value = response.get_json(silent=True)
    if value is None:
        raise RuntimeError(f"GET {path} did not return JSON")
    return response, value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--ue-project-id", required=True)
    parser.add_argument("--ue-project-name", required=True)
    args = parser.parse_args()

    # Import after parsing so --help never initializes the application.  The
    # release container bind-mounts the backend at /app while this reusable
    # exporter is copied to /tmp.
    sys.path.insert(0, os.environ.get("ONTOTWIN_BACKEND_ROOT", "/app"))
    from app import app

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    headers = {
        "X-OntoTwin-UE-Project-Id": args.ue_project_id,
        "X-OntoTwin-UE-Project-Name": args.ue_project_name,
        "X-OntoTwin-UE-Context": "packaged",
    }
    client = app.test_client()

    binding_response, binding = require_response(
        client, "/api/v2/ue/binding_status", headers
    )
    if binding.get("mode") != "matched" or binding.get("project_id") != args.project_id:
        raise RuntimeError(
            "UE binding mismatch: "
            + json.dumps(binding, ensure_ascii=False, sort_keys=True)
        )

    snapshot_response, snapshots = require_response(
        client, "/api/v2/state/snapshots", headers
    )
    if not isinstance(snapshots, list):
        raise RuntimeError("Snapshot endpoint must return a JSON array")

    scene_response, scene_runtime = require_response(
        client, "/api/v2/scene-interactions/runtime", headers
    )
    web_response, web_runtime = require_response(
        client, "/api/v2/web-interactions/runtime", headers
    )
    if scene_runtime.get("project_id") != args.project_id:
        raise RuntimeError("Scene interaction projection resolved another project")
    if web_runtime.get("project_id") != args.project_id:
        raise RuntimeError("Web interaction projection resolved another project")

    snapshot_bytes = compact_json(snapshots)
    snapshot_digest = hashlib.sha256(snapshot_bytes).hexdigest()
    cursor = f"offline-{snapshot_digest[:20]}-1"
    reset = {
        "schemaVersion": "snapshot_delta_v1",
        "mode": "reset",
        "cursor": cursor,
        "revision": 1,
        "upserts": snapshots,
        "deletedIds": [],
    }
    delta = {
        "schemaVersion": "snapshot_delta_v1",
        "mode": "delta",
        "cursor": cursor,
        "revision": 1,
        "upserts": [],
        "deletedIds": [],
    }

    files: list[dict[str, Any]] = []
    files.append(write_json(output / "binding.json", binding))
    files.append(write_json(output / "snapshots.json", snapshots))
    files.append(write_json(output / "snapshot-reset.json", reset))
    files.append(write_json(output / "snapshot-delta.json", delta))
    files.append(write_json(output / "scene-runtime.json", scene_runtime))
    files.append(write_json(output / "web-runtime.json", web_runtime))

    narration_ids = sorted(
        {
            value
            for value in walk_values(scene_runtime)
            if isinstance(value, str) and value.startswith("narration_")
        }
    )
    audio_files: list[dict[str, Any]] = []
    for asset_id in narration_ids:
        response = client.get(
            f"/api/v2/scene-interactions/narration-assets/{asset_id}",
            headers=headers,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Narration asset {asset_id} returned HTTP {response.status_code}"
            )
        content_type = response.headers.get("Content-Type", "audio/wav")
        extension = ".wav" if "wav" in content_type.lower() else ".bin"
        destination = output / "Audio" / f"{asset_id}{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.data)
        audio_files.append(
            {
                "asset_id": asset_id,
                "path": destination.relative_to(output).as_posix(),
                "content_type": content_type,
                "bytes": len(response.data),
                "sha256": hashlib.sha256(response.data).hexdigest(),
            }
        )

    render_parts = [
        part
        for snapshot in snapshots
        for part in (
            ((snapshot.get("interfaces") or {}).get("I3D_Representable") or {}).get(
                "render_parts"
            )
            or []
        )
        if isinstance(part, dict)
    ]
    asset_paths = sorted(
        {
            str(part.get("asset_path"))
            for part in render_parts
            if part.get("asset_path")
        }
    )
    external_models = [path for path in asset_paths if not path.startswith("/Game/")]
    page_config = (web_runtime.get("config") or {}).get("pages") or []
    metadata = {
        "schema_version": 1,
        "package_kind": "ontotwin_offline_runtime_pack",
        "project_id": args.project_id,
        "ue_project_id": args.ue_project_id,
        "ue_project_name": args.ue_project_name,
        "binding": binding,
        "snapshot_count": len(snapshots),
        "object_type_count": len(
            {item.get("objectTypeRid") for item in snapshots if item.get("objectTypeRid")}
        ),
        "render_part_count": len(render_parts),
        "asset_path_count": len(asset_paths),
        "external_model_references": external_models,
        "scene_revision": int(scene_runtime.get("revision") or 0),
        "scene_runtime_token": scene_runtime.get("runtime_token"),
        "roaming_enabled": bool((scene_runtime.get("config") or {}).get("enabled")),
        "web_revision": int(web_runtime.get("revision") or 0),
        "web_page_count": len(page_config),
        "narration_assets": audio_files,
        "source_response_bytes": {
            "binding": len(binding_response.data),
            "snapshots": len(snapshot_response.data),
            "scene_runtime": len(scene_response.data),
            "web_runtime": len(web_response.data),
        },
        "files": files + audio_files,
    }
    write_json(output / "runtime-pack.json", metadata)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
