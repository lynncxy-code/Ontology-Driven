"""Media URL policy and validation for Overlay video templates."""

import os
import re
from urllib.parse import urlsplit, urlunsplit


MEDIA_KINDS = {"auto", "mp4", "hls"}
POSTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_URL_LENGTH = 2048
MAX_POLICY_RULES = 64
_HOST_RE = re.compile(r"^(?:\*\.)?[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]{1,5})?$")


class MediaPolicyError(ValueError):
    def __init__(self, code, message, path=""):
        self.code = code
        self.path = path
        super().__init__(message)


def _env_rules(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _split_rule(rule):
    text = str(rule or "").strip().lower().rstrip(".")
    if not text or "://" in text or any(char in text for char in "/?#@ \\"):
        raise MediaPolicyError("media_policy_invalid_host", "域名规则格式不正确")
    if not _HOST_RE.fullmatch(text):
        raise MediaPolicyError("media_policy_invalid_host", "域名规则格式不正确")
    host = text
    port = None
    if ":" in text:
        host, raw_port = text.rsplit(":", 1)
        port = int(raw_port)
        if not 1 <= port <= 65535:
            raise MediaPolicyError("media_policy_invalid_port", "端口必须为 1 至 65535")
    wildcard = host.startswith("*.")
    if wildcard:
        host = host[2:]
    if not host or ".." in host:
        raise MediaPolicyError("media_policy_invalid_host", "域名规则格式不正确")
    return host, port, wildcard


def normalize_host_rule(rule):
    host, port, wildcard = _split_rule(rule)
    prefix = "*." if wildcard else ""
    return f"{prefix}{host}:{port}" if port is not None else f"{prefix}{host}"


def _normalize_rule_list(values, path):
    if values is None:
        return []
    if not isinstance(values, list) or len(values) > MAX_POLICY_RULES:
        raise MediaPolicyError("media_policy_invalid", f"{path} 必须是最多 {MAX_POLICY_RULES} 项的数组", path)
    result = []
    seen = set()
    for index, value in enumerate(values):
        try:
            normalized = normalize_host_rule(value)
        except MediaPolicyError as exc:
            exc.path = f"{path}.{index}"
            raise
        if normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _rule_matches(rule, host, port, default_port):
    rule_host, rule_port, wildcard = _split_rule(rule)
    if rule_port is None:
        rule_port = default_port
    host_match = host.endswith("." + rule_host) if wildcard else host == rule_host
    return host_match and port == rule_port


def _rule_covered_by(candidate, parent):
    candidate_host, candidate_port, candidate_wildcard = _split_rule(candidate)
    parent_host, parent_port, parent_wildcard = _split_rule(parent)
    if parent_port != candidate_port:
        return False
    if parent_wildcard:
        if candidate_wildcard:
            return candidate_host == parent_host or candidate_host.endswith("." + parent_host)
        return candidate_host.endswith("." + parent_host)
    return not candidate_wildcard and candidate_host == parent_host


def redact_url(value):
    try:
        parts = urlsplit(str(value or ""))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "<redacted>" if parts.query else "", ""))
    except ValueError:
        return "<invalid-url>"


class MediaPolicyService:
    def __init__(self, store, platform_policy=None):
        self.store = store
        source = platform_policy or {
            "allowed_hosts": _env_rules("ONTOTWIN_MEDIA_ALLOWED_HOSTS"),
            "http_exceptions": _env_rules("ONTOTWIN_MEDIA_HTTP_EXCEPTIONS"),
        }
        self.platform_policy = {
            "allowed_hosts": _normalize_rule_list(source.get("allowed_hosts"), "allowed_hosts"),
            "http_exceptions": _normalize_rule_list(source.get("http_exceptions"), "http_exceptions"),
        }
        self.allowlist_enforced = bool(self.platform_policy["allowed_hosts"])
        for rule in self.platform_policy["http_exceptions"]:
            if not any(_rule_covered_by(rule, parent) for parent in self.platform_policy["allowed_hosts"]):
                raise MediaPolicyError(
                    "media_policy_invalid_http_exception",
                    "HTTP 例外必须同时存在于平台允许域名中",
                    "http_exceptions",
                )

    def validate_project_policy(self, policy):
        if not isinstance(policy, dict):
            raise MediaPolicyError("media_policy_invalid", "项目媒体策略必须是对象")
        mode = policy.get("mode", "inherit_platform")
        if mode not in {"inherit_platform", "restricted"}:
            raise MediaPolicyError("media_policy_invalid_mode", "媒体策略模式不支持", "mode")
        allowed = _normalize_rule_list(policy.get("allowed_hosts"), "allowed_hosts")
        http_exceptions = _normalize_rule_list(policy.get("http_exceptions"), "http_exceptions")
        if mode == "restricted" and self.allowlist_enforced:
            for rule in allowed:
                if not any(_rule_covered_by(rule, parent) for parent in self.platform_policy["allowed_hosts"]):
                    raise MediaPolicyError(
                        "media_policy_outside_platform",
                        f"项目域名 {rule} 不在平台允许范围内",
                        "allowed_hosts",
                    )
            for rule in http_exceptions:
                if rule not in allowed:
                    raise MediaPolicyError(
                        "media_policy_invalid_http_exception",
                        "项目 HTTP 例外必须同时加入项目允许域名",
                        "http_exceptions",
                    )
                if not any(_rule_covered_by(rule, parent) for parent in self.platform_policy["http_exceptions"]):
                    raise MediaPolicyError(
                        "media_policy_outside_platform",
                        f"HTTP 例外 {rule} 不在平台允许范围内",
                        "http_exceptions",
                    )
        return {
            "revision": int(policy.get("revision") or 0),
            "mode": mode,
            "allowed_hosts": allowed,
            "http_exceptions": http_exceptions,
        }

    def describe(self, project_policy):
        normalized = self.validate_project_policy(project_policy or {})
        effective_hosts = (
            self.platform_policy["allowed_hosts"]
            if normalized["mode"] == "inherit_platform"
            else normalized["allowed_hosts"]
        )
        effective_http = (
            self.platform_policy["http_exceptions"]
            if normalized["mode"] == "inherit_platform"
            else normalized["http_exceptions"]
        )
        return {
            "enforced": self.allowlist_enforced,
            "platform": {
                "allowed_hosts": list(self.platform_policy["allowed_hosts"]),
                "http_exceptions": list(self.platform_policy["http_exceptions"]),
            },
            "project": normalized,
            "effective": {
                "allowed_hosts": list(effective_hosts),
                "http_exceptions": list(effective_http),
            },
        }

    def validate_url(self, value, project_policy, purpose="video", requested_kind="auto"):
        if not isinstance(value, str) or not value.strip():
            raise MediaPolicyError("media_url_empty", "媒体地址不能为空", "url")
        url = value.strip()
        if len(url) > MAX_URL_LENGTH:
            raise MediaPolicyError("media_url_too_long", "媒体地址最长为 2048 字符", "url")
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError as exc:
            raise MediaPolicyError("media_url_invalid", "媒体地址格式不正确", "url") from exc
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"}:
            raise MediaPolicyError("media_scheme_not_allowed", "媒体地址只允许 HTTP 或 HTTPS", "url")
        if parts.username or parts.password:
            raise MediaPolicyError("media_credentials_not_allowed", "媒体地址不能包含账号或密码", "url")
        host = (parts.hostname or "").lower().rstrip(".")
        if not host:
            raise MediaPolicyError("media_url_invalid", "媒体地址缺少域名", "url")
        effective_port = port or (443 if scheme == "https" else 80)
        policy = self.describe(project_policy)["effective"]
        if not self.allowlist_enforced and scheme == "http":
            raise MediaPolicyError("media_http_not_allowed", "Open test mode only allows HTTPS", "url")
        if self.allowlist_enforced and not any(_rule_matches(rule, host, effective_port, 443 if scheme == "https" else 80)
                   for rule in policy["allowed_hosts"]):
            raise MediaPolicyError("media_domain_not_allowed", "该媒体来源未被项目允许", "url")
        if self.allowlist_enforced and scheme == "http" and not any(
            _rule_matches(rule, host, effective_port, 80) for rule in policy["http_exceptions"]
        ):
            raise MediaPolicyError("media_http_not_allowed", "该地址未获得内网 HTTP 例外", "url")

        path = parts.path.lower()
        if purpose == "poster":
            extension = next((ext for ext in POSTER_EXTENSIONS if path.endswith(ext)), None)
            if not extension:
                raise MediaPolicyError("media_poster_type_not_allowed", "封面只支持 JPEG、PNG 或 WebP", "poster")
            return {"url": url, "kind": extension.lstrip("."), "scheme": scheme, "host": host}

        kind = requested_kind or "auto"
        if kind not in MEDIA_KINDS:
            raise MediaPolicyError("media_kind_not_allowed", "视频类型必须为自动、MP4 或 HLS", "kind")
        detected = "mp4" if path.endswith(".mp4") else ("hls" if path.endswith(".m3u8") else None)
        if kind == "auto":
            kind = detected
        if kind not in {"mp4", "hls"}:
            raise MediaPolicyError("media_kind_unknown", "无法从地址识别视频类型，请明确选择 MP4 或 HLS", "kind")
        if detected and detected != kind:
            raise MediaPolicyError("media_kind_mismatch", "视频类型与 URL 扩展名不一致", "kind")
        return {"url": url, "kind": kind, "scheme": scheme, "host": host}

