"""
ArtStudio 资产库客户端（OntoTwin 3.3）。

封装对 artstudio.digioasis.tech 的访问，供 bind / snapshot / 下载代理复用：
- 详情查询：拿 files[].downloadUrl（S3 预签名直链）+ currentVersion
- 版本查询：供显式重新绑定时生成缓存版本键
- glb 校验：本期只支持单文件 glb，gltf/fbx/usd 在 bind 处拦截
- 下载流式转发：UE → Flask → S3，隐藏 presigned/token

ArtStudio 模型不再预取到后端 Models 目录。UE 在 PIE 或打包程序中
通过下载代理获取模型，并保存到各自的 Saved/ModelCache。下方预取函数
仅保留给旧部署兼容，不参与模型绑定与快照链路。

与 app.py 解耦：启动时由 app.py 调 configure() 注入配置。
"""

import os
import time
import threading
import requests

# ── 配置（由 app.py 启动时 configure 注入）──────────────────────────
_BASE_URL = "https://artstudio.digioasis.tech/api"
_TOKEN = None
_TENANT_ID = None
_TIMEOUT = 5
_MODELS_DIR = None   # 旧部署兼容：后端预取目录；当前 ArtStudio 链路不再使用
_credentials_guard = threading.Lock()

# 预取去重：同一文件并发只下一次（后台线程）
_downloading = set()
_download_failures = {}
_dl_guard = threading.Lock()
_DOWNLOAD_RETRY_COOLDOWN = 30

# ── 版本缓存：asset_id -> (version:int, expire_ts) ──────────────────
_VERSION_TTL = 30  # 秒
_version_cache = {}

# asset_id 稳定标识前缀：snapshot 下发给 UE 的 asset_id 形如 artstudio:{id}:v{n}
PREFIX = "artstudio:"


def configure(base_url=None, token=None, timeout=None, models_dir=None, tenant_id=None):
    global _BASE_URL, _TIMEOUT, _MODELS_DIR
    if base_url:
        _BASE_URL = base_url.rstrip("/")
    if token is not None or tenant_id is not None:
        set_credentials(token, tenant_id)
    if timeout:
        _TIMEOUT = timeout
    if models_dir:
        _MODELS_DIR = models_dir


def _headers():
    with _credentials_guard:
        token = _TOKEN
        tenant_id = _TENANT_ID
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if tenant_id:
        headers["X-Tenant-Id"] = str(tenant_id)
    return headers


def set_credentials(token, tenant_id=None):
    """运行时切换当前设备的 ArtStudio 会话；允许传 None 主动断开。"""
    global _TOKEN, _TENANT_ID
    with _credentials_guard:
        _TOKEN = str(token).strip() if token else None
        _TENANT_ID = str(tenant_id).strip() if tenant_id else None


def auth_headers():
    """供同一后端内的 ArtStudio 请求复用当前会话请求头。"""
    return _headers()


def has_token():
    """当前进程是否配置了 ArtStudio 个人 Token（不返回 Token 本身）。"""
    with _credentials_guard:
        return bool(_TOKEN)


def fetch_identity():
    """校验个人 Token，并返回适合内部消费的标准化身份结果。"""
    if not _TOKEN:
        return {
            "ok": False,
            "configured": False,
            "status": 401,
            "code": "artstudio_token_missing",
            "message": "尚未连接 ArtStudio 账号。完成账号连接后，即可查看你的个人资产。",
        }

    try:
        resp = requests.get(
            f"{_BASE_URL}/auth/user/info",
            headers=_headers(), timeout=_TIMEOUT,
        )
    except requests.RequestException:
        return {
            "ok": False,
            "configured": True,
            "status": 502,
            "code": "artstudio_identity_unavailable",
            "message": "暂时无法确认 ArtStudio 登录状态，请稍后再试。",
        }

    if resp.status_code in (401, 403):
        return {
            "ok": False,
            "configured": True,
            "status": 401,
            "code": "artstudio_token_invalid",
            "message": "ArtStudio 登录状态已失效，请重新连接账号后再试。",
        }

    try:
        resp.raise_for_status()
        body = resp.json() or {}
    except (requests.RequestException, ValueError):
        return {
            "ok": False,
            "configured": True,
            "status": 502,
            "code": "artstudio_identity_unavailable",
            "message": "暂时无法确认 ArtStudio 登录状态，请稍后再试。",
        }

    user = body.get("data", body) if isinstance(body, dict) else {}
    if isinstance(user, dict) and isinstance(user.get("user"), dict):
        user = user["user"]
    if not isinstance(user, dict):
        user = {}

    user_id = user.get("id") or user.get("userId") or ""
    username = user.get("username") or user.get("userName") or ""
    nickname = user.get("nickname") or user.get("nickName") or user.get("name") or ""
    display_name = nickname or username or (f"用户 {user_id}" if user_id else "ArtStudio 用户")
    return {
        "ok": True,
        "configured": True,
        "status": 200,
        "user": {
            "id": str(user_id),
            "username": str(username),
            "nickname": str(nickname),
            "display_name": str(display_name),
        },
    }


def _ext_of(file_obj):
    """从 file 对象推断扩展名（小写，不含点）。"""
    name = file_obj.get("displayName") or file_obj.get("downloadUrl") or file_obj.get("url") or ""
    base = name.split("?")[0]
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""


def fetch_detail(asset_id):
    """
    拉资产详情。返回 dict 或 None（不可达/不存在）：
      { "name": str, "version": int, "files": [{"ext","download_url","name"}...] }
    """
    try:
        headers = _headers()
        resp = requests.get(
            f"{_BASE_URL}/assets/{asset_id}",
            headers=headers, timeout=_TIMEOUT,
        )
        # 公开资产不能被设备上的过期会话拖累；私有资产匿名重试仍会被上游拒绝。
        if headers and resp.status_code in (401, 403):
            resp = requests.get(
                f"{_BASE_URL}/assets/{asset_id}",
                timeout=_TIMEOUT,
            )
        resp.raise_for_status()
        data = (resp.json() or {}).get("data", {})
    except Exception:
        return None

    files = []
    for f in data.get("files", []):
        url = f.get("downloadUrl") or f.get("url")
        if not url:
            continue
        files.append({
            "ext": _ext_of(f),
            "download_url": url,
            "name": f.get("displayName", ""),
        })
    return {
        "name": str(data.get("name") or ""),
        "version": int(data.get("currentVersion", 1) or 1),
        "files": files,
    }


def pick_glb_file(detail):
    """从详情里挑出可独立运行时加载的 GLB 文件；没有则 None。"""
    if not detail:
        return None
    for f in detail.get("files", []):
        if f["ext"] == "glb":
            return f
    return None


def is_glb_asset(asset_id):
    """该 ArtStudio 资产是否含 glb 文件。"""
    return pick_glb_file(fetch_detail(asset_id)) is not None


def get_version(asset_id):
    """当前版本号，带 TTL 缓存。不可达时返回 None。"""
    now = time.time()
    hit = _version_cache.get(asset_id)
    if hit and hit[1] > now:
        return hit[0]
    detail = fetch_detail(asset_id)
    if not detail:
        return None
    ver = detail["version"]
    _version_cache[asset_id] = (ver, now + _VERSION_TTL)
    return ver


def make_stable_id(asset_id, version):
    """组装下发给 UE 的稳定标识。"""
    return f"{PREFIX}{asset_id}:v{version}"


def parse_stable_id(stable_id):
    """artstudio:{id}:v{n} -> (asset_id, version)；非该格式返回 (None, None)。"""
    if not isinstance(stable_id, str) or not stable_id.startswith(PREFIX):
        return None, None
    rest = stable_id[len(PREFIX):]
    if ":v" in rest:
        aid, _, ver = rest.rpartition(":v")
        try:
            return aid, int(ver)
        except ValueError:
            return aid, None
    return rest, None


def refresh_stable_id(stable_id):
    """
    给定已存的稳定标识，用 TTL 缓存的当前版本刷新它。
    版本变了 → 返回新标识（触发 UE 热更换）；查不到则原样返回。
    """
    asset_id, _ = parse_stable_id(stable_id)
    if not asset_id:
        return stable_id
    ver = get_version(asset_id)
    return make_stable_id(asset_id, ver) if ver is not None else stable_id


def ensure_local_glb(asset_id, version):
    """
    后端预取（非阻塞）：确保 {MODELS_DIR}/{id}_v{ver}.glb 存在。
    - 已就绪 → 返回本地文件名（snapshot 下发，UE 本地加载）
    - 未就绪 → 后台线程开始下载，立即返回 None（snapshot 先占位，下个轮询再下发）
    绝不阻塞 snapshot 响应（模型可达 80MB+，同步下载会拖垮轮询）。
    """
    if not _MODELS_DIR:
        return None
    filename = f"{asset_id}_v{version}.glb"
    path = os.path.join(_MODELS_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return filename

    # 未就绪：去重后后台下载
    with _dl_guard:
        if filename in _downloading:
            return None
        failed_at = _download_failures.get(filename)
        if failed_at and (time.time() - failed_at) < _DOWNLOAD_RETRY_COOLDOWN:
            return None
        _downloading.add(filename)
    threading.Thread(target=_download_worker, args=(asset_id, filename, path), daemon=True).start()
    return None


def local_glb_status(asset_id, version):
    """Return the non-blocking preparation state used by instance model binding."""
    if not _MODELS_DIR:
        return "failed"
    filename = f"{asset_id}_v{version}.glb"
    path = os.path.join(_MODELS_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return "ready"
    with _dl_guard:
        if filename in _downloading:
            return "preparing"
        failed_at = _download_failures.get(filename)
        if failed_at and (time.time() - failed_at) < _DOWNLOAD_RETRY_COOLDOWN:
            return "failed"
    return "preparing"


def _download_worker(asset_id, filename, path):
    tmp = path + ".part"
    succeeded = False
    try:
        for attempt in range(3):   # S3 链路不稳，重试 3 次
            upstream, _ = open_download_stream(asset_id)
            if upstream is None:
                time.sleep(2)
                continue
            try:
                os.makedirs(_MODELS_DIR, exist_ok=True)
                with open(tmp, "wb") as f:
                    for chunk in upstream.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                os.replace(tmp, path)   # 原子落盘，避免 UE 读到半截文件
                succeeded = True
                print(f"[ArtStudio预取] ✅ {filename} ({os.path.getsize(path)} bytes)", flush=True)
                return
            except Exception as e:
                print(f"[ArtStudio预取] ✗ {filename} 第{attempt+1}次失败: {e}", flush=True)
                try:
                    os.remove(tmp)
                except Exception:
                    pass
            finally:
                upstream.close()
            time.sleep(2)
    finally:
        with _dl_guard:
            _downloading.discard(filename)
            if succeeded:
                _download_failures.pop(filename, None)
            else:
                _download_failures[filename] = time.time()


def open_download_stream(asset_id, expected_version=None):
    """
    打开 glb 的流式下载（供代理转发）。
    返回 (requests.Response, filename) 或 (None, None)。
    调用方负责 iter_content 并最终 close。
    """
    detail = fetch_detail(asset_id)
    if expected_version is not None and detail:
        if int(detail.get("version") or 1) != int(expected_version):
            return None, None
    f = pick_glb_file(detail)
    if not f:
        return None, None
    try:
        # 大模型(80MB+) over S3 慢链路：连接 10s，读 180s（两次读之间的间隔上限）
        r = requests.get(f["download_url"], stream=True, timeout=(10, 180))
        r.raise_for_status()
    except Exception:
        return None, None
    filename = f["name"] or f"{asset_id}.glb"
    return r, filename
