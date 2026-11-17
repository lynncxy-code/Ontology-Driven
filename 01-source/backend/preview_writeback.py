"""Commit editor-preview transforms together, using the project state read under lock."""
import copy
from part_transform_writeback import _normalize as normalize_parts, patch_project_parts
from writeback import _normalize_transform, apply_writeback, runtime_edit_state_hash


class PreviewConflict(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status

    def response(self):
        return {"error": str(self)}


def commit_preview(store, changes):
    if not isinstance(changes, list) or not 1 <= len(changes) <= 5000:
        raise PreviewConflict("expected 1 to 5000 changed instances", 400)
    ids = set()
    roots = []
    part_changes = []
    for change in changes:
        if not isinstance(change, dict):
            raise PreviewConflict("invalid change", 400)
        iid = change.get("instance_id")
        if not isinstance(iid, str) or not iid or iid in ids:
            raise PreviewConflict("missing or duplicate instance id", 400)
        ids.add(iid)
        if "transform" in change:
            tf, error = _normalize_transform(change["transform"])
            if error:
                raise PreviewConflict(error, 400)
            roots.append((iid, change.get("expected_state_hash"), tf))
        if "parts" in change:
            part_changes.append(change)
        elif "transform" not in change:
            raise PreviewConflict("empty change", 400)
    normalized = normalize_parts(part_changes) if part_changes else None
    pid = store.get_active_id()

    def mutate(project):
        # Existing CAD conversion and raw-state methods operate on _current.
        # Point a private store view at this transaction's detached working copy.
        view = copy.copy(store)
        view._current = project
        for iid, expected, tf in roots:
            raw = view.get_raw_state(iid)
            if raw is None or expected != runtime_edit_state_hash(raw):
                raise PreviewConflict("instance changed since preview: " + iid, 409)
            if raw.get("runtime_spatial_editable", True) is False:
                raise PreviewConflict("spatial editing disabled: " + iid, 403)
            ok, result = apply_writeback(view, iid, tf, persist=False)
            if not ok:
                raise PreviewConflict(result["error"], 409)
        if normalized:
            patch_project_parts(project, *normalized)
        return len(ids)

    return store.transact_project(pid, mutate)
