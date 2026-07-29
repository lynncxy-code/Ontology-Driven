import httpx


class NexusError(Exception):
    def __init__(self, code, http_status, operation, backend_error, retryable, hint=""):
        self.code, self.http_status, self.operation = code, http_status, operation
        self.backend_error, self.retryable, self.hint = backend_error, retryable, hint
        msg = f"[{code}] {operation}"
        if http_status:
            msg += f" (HTTP {http_status})"
        if backend_error:
            msg += f": {backend_error}"
        if hint:
            msg += f" — {hint}"
        super().__init__(msg)


def map_bad_response(operation, status=0):
    """成功响应体不是合法 JSON（2xx + application/json 但 body 畸形）时的映射。"""
    return NexusError("NEXUS_BAD_RESPONSE", status, operation, "", False,
                      "后端返回了非法 JSON")


def map_response_error(operation, status, body_text, parsed_json):
    pj = parsed_json if isinstance(parsed_json, dict) else {}
    berr = pj.get("error") if isinstance(parsed_json, dict) else (body_text or "")[:300]
    if status == 400:
        if isinstance(berr, str) and "无激活项目" in berr:
            return NexusError("NEXUS_NO_ACTIVE_PROJECT", 400, operation, berr, False,
                              "请先用 activate_project 激活一个项目")
        return NexusError("NEXUS_VALIDATION_ERROR", 400, operation, berr, False)
    if status == 403:
        return NexusError("NEXUS_FORBIDDEN", 403, operation, berr, False, "项目/UE 绑定不匹配")
    if status == 404:
        return NexusError("NEXUS_NOT_FOUND", 404, operation, berr, False)
    if status == 409:
        # 只有确属「激活项目并发漂移」才映射 NEXUS_PROJECT_CHANGED：
        # 后端要么带 expected/actual 字段，要么 error == "project changed"。
        # 其它 409（如 create_empty_project 重名 name_duplicated）映射 NEXUS_CONFLICT，
        # 透传后端 error 文本，避免误导为「激活项目已变」。
        if "expected" in pj or "actual" in pj or berr == "project changed":
            exp = pj.get("expected"); act = pj.get("actual")
            return NexusError("NEXUS_PROJECT_CHANGED", 409, operation, berr, False,
                              f"当前激活项目已变（expected={exp} actual={act}），请重新确认后再写")
        return NexusError("NEXUS_CONFLICT", 409, operation, berr, False,
                          "后端返回冲突（非激活项目漂移），请检查上述 error")
    if status == 413:
        return NexusError("NEXUS_TOO_LARGE", 413, operation, berr, False)
    if status == 503:
        return NexusError("NEXUS_DEGRADED", 503, operation, berr, True, "语义图库暂不可达")
    if 500 <= status < 600:
        return NexusError("NEXUS_BACKEND_ERROR", status, operation, berr, False)
    return NexusError("NEXUS_HTTP_ERROR", status, operation, berr, False)


def map_transport_error(operation, exc):
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
        return NexusError("NEXUS_UNREACHABLE", 0, operation, str(exc), False,
                          "Nexus 后端不可达，检查 NEXUS_BASE_URL")
    if isinstance(exc, httpx.TimeoutException):
        return NexusError("NEXUS_TIMEOUT", 0, operation, str(exc), True,
                          "请求超时，检查 NEXUS_BASE_URL 或后端负载")
    return NexusError("NEXUS_TRANSPORT_ERROR", 0, operation, str(exc), False)
