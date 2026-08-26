import hashlib
import math
import os
import struct
import tempfile

import requests


OWNER_USER = 2
VISIBILITY_PUBLIC = 1
VISIBILITY_USER_PRIVATE = 4
CATEGORY_MODEL_3D = 1
STATUS_LISTED = 2
GLB_MIME = "model/gltf-binary"


class ArtStudioUploadError(RuntimeError):
    def __init__(self, message, status=400, code="artstudio_upload_failed", fields=None):
        super().__init__(message)
        self.status = int(status)
        self.code = code
        self.fields = fields or {}


class ArtStudioUploadService:
    def __init__(
        self,
        base_url,
        artstudio_client,
        timeout=5,
        max_size_bytes=500 * 1024 * 1024,
        http=None,
    ):
        self.base_url = str(base_url).rstrip("/")
        self.artstudio = artstudio_client
        self.timeout = float(timeout)
        self.max_size_bytes = int(max_size_bytes)
        self.http = http or requests

    @staticmethod
    def _upstream_message(body, fallback):
        if not isinstance(body, dict):
            return fallback
        return str(body.get("msg") or body.get("message") or fallback)[:300]

    @staticmethod
    def _response_body(response):
        try:
            body = response.json() or {}
        except ValueError:
            body = {}
        return body if isinstance(body, dict) else {}

    def _api(self, method, path, *, payload=None, params=None, timeout=None):
        try:
            response = self.http.request(
                method,
                f"{self.base_url}{path}",
                json=payload,
                params=params,
                headers=self.artstudio.auth_headers(),
                timeout=timeout or self.timeout,
            )
        except requests.RequestException as exc:
            raise ArtStudioUploadError(
                "ArtStudio 暂时不可用，请稍后重试。",
                status=502,
                code="artstudio_unavailable",
            ) from exc

        body = self._response_body(response)
        if response.status_code in (401, 403):
            raise ArtStudioUploadError(
                "ArtStudio 登录已失效或当前账号没有上传权限。",
                status=401 if response.status_code == 401 else 403,
                code="artstudio_upload_forbidden",
            )
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ArtStudioUploadError(
                self._upstream_message(body, "ArtStudio 拒绝了本次上传。"),
                status=502,
                code="artstudio_upstream_rejected",
            ) from exc

        code = body.get("code")
        if code not in (None, 0, 200, "0", "200") and body.get("success") is not True:
            raise ArtStudioUploadError(
                self._upstream_message(body, "ArtStudio 未完成本次操作。"),
                status=502,
                code="artstudio_upstream_rejected",
            )
        return body.get("data", body)

    def _copy_and_inspect(self, file_storage):
        original_name = os.path.basename(str(file_storage.filename or "").strip())
        if not original_name.lower().endswith(".glb"):
            raise ArtStudioUploadError(
                "第一版只支持单个 GLB 模型文件。",
                status=422,
                code="unsupported_model_format",
            )

        digest = hashlib.sha256()
        size = 0
        header = b""
        temp_handle = tempfile.NamedTemporaryFile(
            mode="wb", prefix=".ontotwin-glb-upload-", suffix=".tmp", delete=False
        )
        temp_path = temp_handle.name
        try:
            with temp_handle:
                while True:
                    chunk = file_storage.stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_size_bytes:
                        raise ArtStudioUploadError(
                            f"模型文件不能超过 {self.max_size_bytes // (1024 * 1024)} MB。",
                            status=413,
                            code="model_file_too_large",
                        )
                    if len(header) < 12:
                        header += chunk[: 12 - len(header)]
                    digest.update(chunk)
                    temp_handle.write(chunk)

            if size < 20 or len(header) < 12:
                raise ArtStudioUploadError(
                    "GLB 文件内容不完整。", status=422, code="invalid_glb"
                )
            magic, version, declared_length = struct.unpack("<III", header[:12])
            if magic != 0x46546C67 or version != 2:
                raise ArtStudioUploadError(
                    "文件不是有效的 GLB 2.0 模型。", status=422, code="invalid_glb"
                )
            if declared_length != size:
                raise ArtStudioUploadError(
                    "GLB 声明长度与实际文件不一致，文件可能已损坏。",
                    status=422,
                    code="invalid_glb_length",
                )
            return {
                "path": temp_path,
                "filename": original_name,
                "size": size,
                "sha256": digest.hexdigest(),
            }
        except Exception:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise

    def _put_single(self, upload_url, staged):
        try:
            with open(staged["path"], "rb") as handle:
                response = self.http.put(
                    upload_url,
                    data=handle,
                    headers={"Content-Type": GLB_MIME},
                    timeout=(10, 600),
                )
            response.raise_for_status()
        except (OSError, requests.RequestException) as exc:
            raise ArtStudioUploadError(
                "模型文件上传到资产存储失败，请重试。",
                status=502,
                code="artstudio_file_upload_failed",
            ) from exc

    def _put_parts(self, parts, staged):
        if not parts:
            raise ArtStudioUploadError(
                "ArtStudio 未返回有效的分片上传地址。",
                status=502,
                code="artstudio_upload_contract_error",
            )
        part_size = int(math.ceil(staged["size"] / len(parts)))
        completed = []
        try:
            with open(staged["path"], "rb") as handle:
                for item in parts:
                    part_number = int(item.get("partNumber") or 0)
                    upload_url = str(item.get("url") or "")
                    if part_number < 1 or not upload_url:
                        raise ValueError("invalid multipart descriptor")
                    start = (part_number - 1) * part_size
                    handle.seek(start)
                    payload = handle.read(min(part_size, staged["size"] - start))
                    response = self.http.put(
                        upload_url,
                        data=payload,
                        headers={"Content-Type": GLB_MIME},
                        timeout=(10, 600),
                    )
                    response.raise_for_status()
                    etag = str(response.headers.get("ETag") or "").strip('"')
                    if not etag:
                        raise ValueError("missing ETag")
                    completed.append({"partNumber": part_number, "etag": etag})
        except (OSError, ValueError, requests.RequestException) as exc:
            raise ArtStudioUploadError(
                "模型分片上传失败，请重试。",
                status=502,
                code="artstudio_file_upload_failed",
            ) from exc
        return sorted(completed, key=lambda item: item["partNumber"])

    def _upload_file(self, staged):
        common = {
            "sha256": staged["sha256"],
            "size": staged["size"],
            "mime": GLB_MIME,
            "filename": staged["filename"],
        }
        init = self._api("POST", "/asset-uploads/init", payload=common)
        if init.get("deduped"):
            file_id = init.get("fileId")
            if file_id:
                return str(file_id)

        mode = str(init.get("mode") or "").lower()
        finalize = {**common, "kind": "model"}
        if mode == "single" and init.get("url"):
            self._put_single(init["url"], staged)
            data = self._api(
                "POST", "/asset-uploads/finalize-single", payload=finalize, timeout=30
            )
        elif init.get("parts"):
            completed = self._put_parts(init["parts"], staged)
            data = self._api(
                "POST",
                "/asset-uploads/complete",
                payload={
                    "sha256": staged["sha256"],
                    "mime": GLB_MIME,
                    "filename": staged["filename"],
                    "parts": completed,
                    "kind": "model",
                },
                timeout=30,
            )
        else:
            raise ArtStudioUploadError(
                "ArtStudio 返回了无法识别的上传方式。",
                status=502,
                code="artstudio_upload_contract_error",
            )

        file_id = data.get("fileId") if isinstance(data, dict) else None
        if not file_id:
            raise ArtStudioUploadError(
                "ArtStudio 未返回已上传文件标识。",
                status=502,
                code="artstudio_upload_contract_error",
            )
        return str(file_id)

    def _create_asset(self, file_id, name, description, visibility, user_id):
        visibility_code = (
            VISIBILITY_PUBLIC if visibility == "public" else VISIBILITY_USER_PRIVATE
        )
        payload = {
            "name": name,
            "ownerType": OWNER_USER,
            "visibility": visibility_code,
            "category": CATEGORY_MODEL_3D,
            "ownerUserId": user_id,
            "fileIds": [file_id],
        }
        if description:
            payload["description"] = description
        data = self._api("POST", "/assets", payload=payload, timeout=30)
        asset_id = None
        if isinstance(data, dict):
            asset_id = data.get("id") or data.get("assetId")
            if not asset_id and isinstance(data.get("asset"), dict):
                asset_id = data["asset"].get("id") or data["asset"].get("assetId")
        if not asset_id:
            raise ArtStudioUploadError(
                "模型文件已上传，但 ArtStudio 未创建资产记录。",
                status=502,
                code="artstudio_asset_create_failed",
            )
        return str(asset_id), data

    def upload(self, file_storage, name, visibility="public", description=""):
        name = str(name or "").strip()
        description = str(description or "").strip()
        visibility = str(visibility or "public").strip().lower()
        if not name:
            raise ArtStudioUploadError("请输入资产名称。", code="asset_name_required")
        if len(name) > 64:
            raise ArtStudioUploadError(
                "资产名称不能超过 64 个字符。", code="asset_name_too_long"
            )
        if len(description) > 1000:
            raise ArtStudioUploadError(
                "资产描述不能超过 1000 个字符。", code="asset_description_too_long"
            )
        if visibility not in ("public", "private"):
            raise ArtStudioUploadError(
                "请选择公共资产或私人资产。", code="invalid_asset_visibility"
            )
        if file_storage is None:
            raise ArtStudioUploadError("请选择 GLB 模型文件。", code="model_file_required")

        identity = self.artstudio.fetch_identity()
        if not identity.get("ok"):
            raise ArtStudioUploadError(
                identity.get("message") or "请先连接 ArtStudio 账号。",
                status=int(identity.get("status") or 401),
                code=identity.get("code") or "artstudio_login_required",
            )
        user_id = str((identity.get("user") or {}).get("id") or "").strip()
        if not user_id:
            raise ArtStudioUploadError(
                "ArtStudio 当前账号缺少用户标识，请重新连接账号。",
                status=502,
                code="artstudio_identity_incomplete",
            )

        staged = self._copy_and_inspect(file_storage)
        asset_id = None
        created = None
        try:
            file_id = self._upload_file(staged)
            asset_id, created = self._create_asset(
                file_id, name, description, visibility, user_id
            )
            listing_status = "private"
            if visibility == "public":
                try:
                    if int(created.get("status") or 0) != STATUS_LISTED:
                        self._api("POST", f"/assets/{asset_id}/list", timeout=30)
                    listing_status = "listed"
                except ArtStudioUploadError as exc:
                    raise ArtStudioUploadError(
                        "资产已创建，但未能立即发布到公共资产库。请在 ArtStudio 检查上架权限。",
                        status=502,
                        code="artstudio_public_listing_failed",
                        fields={
                            "asset_created": True,
                            "asset": self._asset_payload(asset_id, name, created),
                            "upstream_code": exc.code,
                        },
                    ) from exc

            return {
                "status": "created",
                "visibility": visibility,
                "listing_status": listing_status,
                "asset": self._asset_payload(asset_id, name, created),
                "message": (
                    "公共模型已上传并上架。"
                    if visibility == "public"
                    else "私人模型已上传。"
                ),
            }
        finally:
            try:
                os.remove(staged["path"])
            except OSError:
                pass

    @staticmethod
    def _asset_payload(asset_id, name, data):
        data = data if isinstance(data, dict) else {}
        return {
            "file_number": str(asset_id),
            "name": str(data.get("name") or name),
            "format": "GLB",
            "formats": ["GLB"],
            "bindable": True,
            "bounding_box": {},
            "download_url": "",
            "cover_url": str(data.get("coverUrl") or ""),
            "ue_path": "",
            "current_version": int(data.get("currentVersion") or 1),
            "_source": {"artstudio_id": str(asset_id)},
        }
