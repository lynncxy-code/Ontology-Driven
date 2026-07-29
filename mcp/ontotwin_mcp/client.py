import httpx

from .errors import map_response_error, map_transport_error


class NexusClient:
    def __init__(self, settings, transport=None):
        self.s = settings
        self._c = httpx.Client(
            base_url=settings.base_url,
            timeout=httpx.Timeout(settings.timeout_read, connect=settings.timeout_connect),
            transport=transport,
        )

    def _handle(self, operation, resp):
        if resp.is_success:
            ct = resp.headers.get("content-type", "")
            return resp.json() if "application/json" in ct else resp.text
        try:
            parsed = resp.json()
        except Exception:
            parsed = None
        raise map_response_error(operation, resp.status_code, resp.text, parsed)

    def get(self, operation, path, params=None):
        try:
            r = self._c.get(path, params=params)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)

    def post_json(self, operation, path, json=None, timeout=None):
        try:
            r = self._c.post(path, json=json or {}, timeout=timeout)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)

    def post_multipart(self, operation, path, files, data=None, timeout=None):
        mp = [(field, (fname, content)) for (field, fname, content) in files]
        to = timeout if timeout is not None else self.s.timeout_upload
        try:
            r = self._c.post(path, files=mp, data=data or {}, timeout=to)
        except httpx.HTTPError as e:
            raise map_transport_error(operation, e)
        return self._handle(operation, r)
