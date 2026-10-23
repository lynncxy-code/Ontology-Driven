"""ArtStudio 当前设备登录会话。

账号密码由前端按 ArtStudio 公钥加密后提交；本模块只接收密文，
向 ArtStudio 换取 access token，并将 token 保存在当前设备的忽略文件中。
"""

import json
import os
import threading
from urllib.parse import urlsplit

import requests
from flask import jsonify, request

import artstudio_client


CLIENT_ID = "ef51c9a3e9046c4f2ea45142c8a8344a"

_base_url = "https://artstudio.digioasis.tech/api"
_timeout = 5
_session_path = os.path.join(os.path.dirname(__file__), "data", ".artstudio_session.json")
_session_guard = threading.Lock()
_session_owned = False


def configure(base_url=None, timeout=None, session_path=None):
    """注入上游配置并恢复当前设备已保存的会话。"""
    global _base_url, _timeout, _session_path, _session_owned
    if base_url:
        _base_url = base_url.rstrip("/")
    if timeout:
        _timeout = timeout
    if session_path:
        _session_path = session_path

    try:
        with open(_session_path, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
        token = saved.get("access_token")
        if token:
            artstudio_client.set_credentials(token, saved.get("tenant_id"))
            _session_owned = True
    except (FileNotFoundError, OSError, ValueError, TypeError, AttributeError):
        _session_owned = False


def _body(response):
    try:
        value = response.json() or {}
        return value if isinstance(value, dict) else {}
    except ValueError:
        return {}


def _upstream_message(body, fallback):
    return str(body.get("msg") or body.get("message") or fallback)[:200]


def _same_origin_request():
    """浏览器写操作仅允许来自当前 Nexus 页面；无 Origin 的本机脚本仍可调用。"""
    origin = request.headers.get("Origin")
    if not origin:
        return True
    origin_parts = urlsplit(origin)
    host_parts = urlsplit(request.host_url)
    return (
        origin_parts.scheme.lower() == host_parts.scheme.lower()
        and origin_parts.netloc.lower() == host_parts.netloc.lower()
    )


def _origin_error():
    return _json_result({
        "ok": False,
        "status": 403,
        "code": "artstudio_auth_origin_rejected",
        "message": "请从当前 Nexus 页面连接 ArtStudio 账号。",
    })


def _get(path):
    return requests.get(f"{_base_url}{path}", timeout=_timeout)


def get_captcha():
    """获取一次性图形验证码。"""
    try:
        response = _get("/auth/captcha")
        body = _body(response)
        response.raise_for_status()
        data = body.get("data") or {}
        if not data.get("uuid") or not data.get("img"):
            raise ValueError("captcha payload incomplete")
        return {
            "ok": True,
            "status": 200,
            "captcha": {
                "uuid": str(data["uuid"]),
                "image": str(data["img"]),
                "expires_in": int(data.get("expiresIn") or 120),
            },
        }
    except (requests.RequestException, ValueError, TypeError):
        return {
            "ok": False,
            "status": 502,
            "code": "artstudio_captcha_unavailable",
            "message": "暂时无法加载验证码，请稍后再试。",
        }


def get_login_challenge():
    """返回前端登录所需的公钥、验证码开关和验证码。"""
    try:
        key_response = _get("/auth/public-key")
        status_response = _get("/auth/captcha/status")
        key_body = _body(key_response)
        status_body = _body(status_response)
        key_response.raise_for_status()
        status_response.raise_for_status()

        key_data = key_body.get("data") or {}
        status_data = status_body.get("data") or {}
        encryption_enabled = bool(key_data.get("enabled"))
        public_key = str(key_data.get("publicKey") or "")
        if not encryption_enabled or not public_key:
            return {
                "ok": False,
                "status": 503,
                "code": "artstudio_secure_login_unavailable",
                "message": "ArtStudio 安全登录暂不可用，请稍后再试。",
            }

        result = {
            "ok": True,
            "status": 200,
            "encryption_enabled": True,
            "public_key": public_key,
            "captcha_enabled": bool(status_data.get("enabled")),
        }
        if result["captcha_enabled"]:
            captcha = get_captcha()
            if not captcha.get("ok"):
                return captcha
            result["captcha"] = captcha["captcha"]
        return result
    except (requests.RequestException, ValueError, TypeError):
        return {
            "ok": False,
            "status": 502,
            "code": "artstudio_login_unavailable",
            "message": "暂时无法连接 ArtStudio，请稍后再试。",
        }


def _save_session(access_token, tenant_id):
    parent = os.path.dirname(_session_path)
    os.makedirs(parent, exist_ok=True)
    temporary = f"{_session_path}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump({
            "version": 1,
            "access_token": access_token,
            "tenant_id": tenant_id,
        }, handle, ensure_ascii=False)
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, _session_path)


def login(username, encrypted_password, captcha="", uuid=""):
    """使用公钥加密后的密码登录；函数内不接收、保存或记录明文密码。"""
    global _session_owned
    username = str(username or "").strip()
    encrypted_password = str(encrypted_password or "").strip()
    captcha = str(captcha or "").strip()
    uuid = str(uuid or "").strip()
    if not username or not encrypted_password:
        return {
            "ok": False,
            "status": 400,
            "code": "artstudio_login_fields_required",
            "message": "请输入用户名和密码。",
        }
    if len(username) > 128 or len(encrypted_password) > 4096 or len(captcha) > 16 or len(uuid) > 128:
        return {
            "ok": False,
            "status": 400,
            "code": "artstudio_login_fields_invalid",
            "message": "登录信息格式不正确，请重新输入。",
        }

    payload = {
        "authType": "ACCOUNT",
        "clientId": CLIENT_ID,
        "username": username,
        "password": encrypted_password,
        "captcha": captcha,
        "uuid": uuid,
    }
    try:
        response = requests.post(
            f"{_base_url}/auth/login",
            json=payload,
            timeout=_timeout,
        )
        body = _body(response)
        data = body.get("data") or {}
        access_token = data.get("accessToken")
        if not response.ok or not access_token:
            return {
                "ok": False,
                "status": 401,
                "code": "artstudio_login_failed",
                "message": _upstream_message(body, "登录失败，请检查账号、密码或验证码。"),
            }

        tenant_id = data.get("tenantId")
        artstudio_client.set_credentials(access_token, tenant_id)
        identity = artstudio_client.fetch_identity()
        if not identity.get("ok"):
            artstudio_client.set_credentials(None)
            return {
                "ok": False,
                "status": 401,
                "code": "artstudio_login_failed",
                "message": "登录状态验证失败，请重新登录。",
            }

        try:
            with _session_guard:
                _save_session(str(access_token), str(tenant_id) if tenant_id else None)
                _session_owned = True
        except OSError:
            artstudio_client.set_credentials(None)
            return {
                "ok": False,
                "status": 500,
                "code": "artstudio_session_save_failed",
                "message": "无法保存当前设备的登录状态，请稍后再试。",
            }

        return {
            "ok": True,
            "status": 200,
            "user": identity.get("user", {}),
        }
    except requests.RequestException:
        return {
            "ok": False,
            "status": 502,
            "code": "artstudio_login_unavailable",
            "message": "暂时无法连接 ArtStudio，请稍后再试。",
        }


def logout():
    """断开当前设备会话；环境变量仅作为重启后的管理员兼容回退。"""
    global _session_owned
    headers = artstudio_client.auth_headers()
    if _session_owned and headers.get("Authorization"):
        try:
            requests.post(f"{_base_url}/auth/logout", headers=headers, timeout=_timeout)
        except requests.RequestException:
            pass

    artstudio_client.set_credentials(None)
    with _session_guard:
        try:
            os.remove(_session_path)
        except FileNotFoundError:
            pass
        except OSError:
            return {
                "ok": False,
                "status": 500,
                "code": "artstudio_logout_failed",
                "message": "暂时无法断开账号连接，请稍后再试。",
            }
        _session_owned = False
    return {"ok": True, "status": 200}


def _json_result(result):
    payload = {key: value for key, value in result.items() if key not in ("ok", "status")}
    payload["success"] = bool(result.get("ok"))
    return jsonify(payload), int(result.get("status", 500))


def register_routes(app):
    @app.route("/api/v2/assets/auth/challenge", methods=["GET"])
    def artstudio_login_challenge():
        return _json_result(get_login_challenge())

    @app.route("/api/v2/assets/auth/captcha", methods=["GET"])
    def artstudio_login_captcha():
        return _json_result(get_captcha())

    @app.route("/api/v2/assets/auth/login", methods=["POST"])
    def artstudio_login():
        if not _same_origin_request():
            return _origin_error()
        data = request.get_json(silent=True) or {}
        return _json_result(login(
            data.get("username"),
            data.get("encrypted_password"),
            data.get("captcha"),
            data.get("uuid"),
        ))

    @app.route("/api/v2/assets/auth/logout", methods=["POST"])
    def artstudio_logout():
        if not _same_origin_request():
            return _origin_error()
        return _json_result(logout())
