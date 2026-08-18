import copy
import datetime
from urllib.parse import urlsplit

from project_store import _default_web_interactions

from .resolver import resolve_binding
from .runtime_projection import build_runtime_projection
from .validators import normalize_config, validate_config


class WebInteractionNotFoundError(LookupError):
    pass


class WebInteractionConflictError(RuntimeError):
    pass


class WebInteractionService:
    def __init__(self, store):
        self.store = store

    def _project(self):
        project = self.store.get_active_copy()
        if not project:
            raise WebInteractionNotFoundError("当前没有激活项目")
        return project

    @staticmethod
    def _web(project):
        value = project.get("web_interactions")
        return value if isinstance(value, dict) else _default_web_interactions()

    @staticmethod
    def _expected(value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("expected_revision 必须是整数") from exc

    def get(self):
        project = self._project()
        web = copy.deepcopy(self._web(project))
        validation = validate_config(project, web.get("draft") or {})
        return {
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "schema_version": web.get("schema_version", 1),
            "revision": int(web.get("revision") or 0),
            "published": web.get("published") or {},
            "draft": web.get("draft") or {},
            "has_previous_published": web.get("previous_published") is not None,
            "draft_validation": {key: validation[key] for key in ("valid", "errors", "warnings", "summary")},
        }

    def save_draft(self, payload):
        project = self._project()
        project_id = project.get("id")
        expected = self._expected(payload.get("expected_revision"))
        draft_source = payload.get("draft") if "draft" in payload else payload.get("config")
        normalized = normalize_config(draft_source, expected)

        def update(working):
            if working.get("id") != project_id:
                raise WebInteractionConflictError("保存期间当前激活项目已切换")
            web = working.setdefault("web_interactions", _default_web_interactions())
            current = int(web.get("revision") or 0)
            if current != expected:
                raise WebInteractionConflictError(f"web interaction revision conflict: expected {expected}, current {current}")
            web["draft"] = copy.deepcopy(normalized)

        self.store.transact_active(update)
        validation = validate_config(self._project(), normalized)
        return {
            "status": "ok", "project_id": project_id, "revision": expected,
            "draft": normalized,
            "validation": {key: validation[key] for key in ("valid", "errors", "warnings", "summary")},
        }

    def validate(self, payload):
        project = self._project()
        source = payload.get("config") if isinstance(payload, dict) and "config" in payload else self._web(project).get("draft")
        result = validate_config(project, source or {})
        result.pop("config", None)
        result["project_id"] = project.get("id")
        return result

    def resolve_preview(self, payload):
        project = self._project()
        web = self._web(project)
        source_name = str(payload.get("source") or "draft")
        config = payload.get("config") if isinstance(payload.get("config"), dict) else web.get(source_name)
        validation = validate_config(project, config or {})
        if not validation["valid"]:
            return {"project_id": project.get("id"), "resolved": False, "validation": {key: validation[key] for key in ("valid", "errors", "warnings", "summary")}}
        result = resolve_binding(project, validation["config"], payload)
        return {"project_id": project.get("id"), "resolved": True, "result": result, "warnings": validation["warnings"]}

    def publish(self, payload):
        project = self._project()
        project_id = project.get("id")
        expected = self._expected(payload.get("expected_revision"))
        allow_warnings = bool(payload.get("confirm_warnings"))
        validation = validate_config(project, self._web(project).get("draft") or {})
        if not validation["valid"]:
            return {"status": "validation_failed", "published": False, **{key: validation[key] for key in ("errors", "warnings", "summary")}}
        if validation["warnings"] and not allow_warnings:
            return {"status": "warning_confirmation_required", "published": False, "errors": [], "warnings": validation["warnings"], "summary": validation["summary"]}
        published = copy.deepcopy(validation["config"])
        published.pop("base_revision", None)
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise WebInteractionConflictError("发布期间当前激活项目已切换")
            web = working.setdefault("web_interactions", _default_web_interactions())
            current = int(web.get("revision") or 0)
            if current != expected:
                raise WebInteractionConflictError(f"web interaction revision conflict: expected {expected}, current {current}")
            web["previous_published"] = copy.deepcopy(web.get("published"))
            web["published"] = copy.deepcopy(published)
            web["revision"] = current + 1
            web["draft"] = normalize_config(published, current + 1)
            result["revision"] = current + 1

        self.store.transact_active(update)
        return {"status": "ok", "published": True, "project_id": project_id, "revision": result["revision"], "config": published, "warnings": validation["warnings"]}

    def apply(self, payload):
        """Validate and atomically replace draft + published for the 3.8.2 single-page flow."""
        project = self._project()
        project_id = project.get("id")
        expected = self._expected(payload.get("expected_revision"))
        allow_warnings = bool(payload.get("confirm_warnings"))
        source = payload.get("config") if "config" in payload else payload.get("draft")
        validation = validate_config(project, source or {})
        if not validation["valid"]:
            return {"status": "validation_failed", "applied": False,
                    **{key: validation[key] for key in ("errors", "warnings", "summary")}}
        if validation["warnings"] and not allow_warnings:
            return {"status": "warning_confirmation_required", "applied": False,
                    "errors": [], "warnings": validation["warnings"], "summary": validation["summary"]}
        applied = copy.deepcopy(validation["config"])
        applied.pop("base_revision", None)
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise WebInteractionConflictError("保存期间当前激活项目已切换")
            web = working.setdefault("web_interactions", _default_web_interactions())
            current = int(web.get("revision") or 0)
            if current != expected:
                raise WebInteractionConflictError(
                    f"web interaction revision conflict: expected {expected}, current {current}")
            web["previous_published"] = copy.deepcopy(web.get("published"))
            web["published"] = copy.deepcopy(applied)
            web["revision"] = current + 1
            web["draft"] = normalize_config(applied, current + 1)
            result["revision"] = current + 1

        self.store.transact_active(update)
        return {
            "status": "ok", "applied": True, "project_id": project_id,
            "revision": result["revision"], "config": applied,
            "warnings": validation["warnings"],
        }

    def rollback(self, payload):
        project = self._project()
        project_id = project.get("id")
        expected = self._expected(payload.get("expected_revision"))
        if self._web(project).get("previous_published") is None:
            raise ValueError("没有可回滚的上一已发布版本")
        result = {}

        def update(working):
            if working.get("id") != project_id:
                raise WebInteractionConflictError("回滚期间当前激活项目已切换")
            web = working.setdefault("web_interactions", _default_web_interactions())
            current = int(web.get("revision") or 0)
            if current != expected:
                raise WebInteractionConflictError(f"web interaction revision conflict: expected {expected}, current {current}")
            previous = copy.deepcopy(web.get("previous_published"))
            current_published = copy.deepcopy(web.get("published"))
            web["published"] = previous
            web["previous_published"] = current_published
            web["revision"] = current + 1
            web["draft"] = normalize_config(previous, current + 1)
            result["revision"] = current + 1

        self.store.transact_active(update)
        return {"status": "ok", "rolled_back": True, "project_id": project_id, "revision": result["revision"]}

    def runtime(self, known_revision=None, binding=None):
        project = self._project()
        return build_runtime_projection(project, self._web(project), known_revision, binding)

    def runtime_event(self, payload, ue_project):
        allowed = {
            "event_type", "request_id", "binding_id", "page_id", "host",
            "action", "result", "error_code", "scene_result", "web_result",
        }
        event = {key: payload.get(key) for key in allowed if key in payload}
        event["project_id"] = self._project().get("id")
        event["ue_project_id"] = (ue_project or {}).get("id")
        event["received_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        # Deliberately log no URL query, cookies, credentials or page business payload.
        if event.get("host"):
            event["host"] = (urlsplit("//" + str(event["host"])).hostname or str(event["host"]))
        print(f"[web-interaction] {event}")
        return {"status": "accepted", "event": event}
