"""Request-scoped project view for the 4.8 explicit-project contract.

The legacy application was written around one in-memory ``active`` project.
This facade keeps those method calls working while selecting a detached project
snapshot for each request.  It deliberately does not change the process-wide
``app_singleton.active_project_id``; requests which carry ``project_id`` are
therefore safe to interleave across browser tabs and UE scenes.
"""

from __future__ import annotations

import copy
import threading

from flask import g


class ScopedProjectStore:
    """Delegate ProjectStore methods to the request's explicit project view."""

    def __init__(self, base):
        object.__setattr__(self, "_base", base)

    def _target(self):
        try:
            return getattr(g, "ontotwin_project_store", self._base)
        except RuntimeError:
            return self._base

    def __getattr__(self, name):
        return getattr(self._target(), name)

    def __setattr__(self, name, value):
        # A handful of old services update bookkeeping fields directly.  Keep
        # those writes on the request clone when one is active.
        if name == "_base":
            object.__setattr__(self, name, value)
            return
        setattr(self._target(), name, value)

    @property
    def base(self):
        return self._base


def project_view(base, project_id):
    """Create an isolated store view for *project_id*.

    ProjectStorePG exposes ``for_request`` so its database loader can be reused
    without invoking the global activation path.  The JSON test fixture gets a
    small equivalent clone here.
    """
    if not project_id:
        return base
    factory = getattr(base, "for_request", None)
    if callable(factory):
        return factory(str(project_id))
    project = base.read_project(str(project_id))
    if project is None:
        raise KeyError(str(project_id))
    clone = copy.copy(base)
    clone._lock = threading.RLock()
    clone._active_id = str(project_id)
    clone._current = project
    clone._dirty = False
    clone._request_scoped = True
    return clone

