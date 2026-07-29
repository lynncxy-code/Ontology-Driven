import httpx

from .errors import map_bad_response, map_response_error, map_transport_error


class NexusClient:
    def __init__(self, settings, transport=None):
        self.s = settings
        self._c = httpx.Client(
            base_url=settings.base_url,
            timeout=httpx.Timeout(settings.timeout_read, connect=settings.timeout_connect),
            transport=transport,
            # MCP 直连内网 Nexus REST，默认不读系统代理（HTTP(S)_PROXY/ALL_PROXY），
            # 否则发往内网的请求会被 clash/VPN 错误劫持导致超时或 ImportError。
            # 逃生口：置 NEXUS_TRUST_ENV=1 时才走系统代理（远程 Nexus 场景）。
            trust_env=settings.trust_env,
        )

    def _handle(self, operation, resp):
        if resp.is_success:
            ct = resp.headers.get("content-type", "")
            if "application/json" not in ct:
                return resp.text
            try:
                return resp.json()
            except Exception:
                # 2xx + application/json 但 body 畸形：映射成 NexusError，
                # 别让裸 JSONDecodeError 漏到工具层。
                raise map_bad_response(operation, resp.status_code)
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
        to = timeout if timeout is not None else self.s.timeout_read
        try:
            r = self._c.post(path, json=json or {}, timeout=to)
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
