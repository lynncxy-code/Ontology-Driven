import io
import os
import struct
import sys
import types
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class FakeRequestException(Exception):
    pass


class FakeHttpError(FakeRequestException):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


# 被测代码写的是 `except requests.RequestException`，所以这两个异常类型必须存在。
#
# 不能用 `if "requests" not in sys.modules` 就整体跳过：同目录的
# test_artstudio_client.py 会先装一个**空的** SimpleNamespace，那时本文件直接
# 跳过，被测代码取 requests.RequestException 就 AttributeError——单独跑能过、
# 全量跑必挂，而且挂在哪取决于文件名排序。改成「缺什么补什么」，与顺序无关。
# 真 requests 已在 sys.modules 时，hasattr 为真，不会覆盖它的任何属性。
_requests_stub = sys.modules.get("requests")
if _requests_stub is None:
    _requests_stub = types.SimpleNamespace()
    sys.modules["requests"] = _requests_stub
if not hasattr(_requests_stub, "RequestException"):
    _requests_stub.RequestException = FakeRequestException
if not hasattr(_requests_stub, "HTTPError"):
    _requests_stub.HTTPError = FakeHttpError

from artstudio_upload.service import ArtStudioUploadError, ArtStudioUploadService


def valid_glb():
    json_chunk = b"{}  "
    return (
        struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(json_chunk))
        + struct.pack("<II", len(json_chunk), 0x4E4F534A)
        + json_chunk
    )


def upload_file(data=None, name="machine.glb", content_type=None):
    return types.SimpleNamespace(
        stream=io.BytesIO(data if data is not None else valid_glb()),
        filename=name,
        content_type=content_type,
    )


def cover_file():
    return upload_file(
        b"\xff\xd8\xff\xe0ontotwin-cover",
        name="machine-cover.jpg",
        content_type="image/jpeg",
    )


class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code = status
        self._body = body or {}
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise FakeHttpError(f"HTTP {self.status_code}", response=self)


class FakeHttp:
    def __init__(self, *, deduped=False, list_status=200):
        self.deduped = deduped
        self.list_status = list_status
        self.requests = []
        self.puts = []

    def request(self, method, url, **kwargs):
        path = url.split("/api", 1)[-1]
        self.requests.append((method, path, kwargs.get("json")))
        if path == "/asset-uploads/init":
            data = (
                {"deduped": True, "fileId": "file-dedup"}
                if self.deduped
                else {"deduped": False, "mode": "single", "url": "https://store.test/model"}
            )
            return FakeResponse(body={"data": data})
        if path == "/asset-uploads/single":
            return FakeResponse(body={
                "data": {"deduped": False, "url": "https://store.test/cover"}
            })
        if path == "/asset-uploads/finalize-single":
            return FakeResponse(body={"data": {"fileId": "file-new"}})
        if path == "/assets":
            payload = kwargs["json"]
            return FakeResponse(body={
                "data": {
                    "id": "asset-123",
                    "name": payload["name"],
                    "currentVersion": 1,
                    "status": 3,
                    "coverUrls": ["https://store.test/cover.jpg"] if payload.get("coverFileIds") else [],
                }
            })
        if path == "/assets/asset-123/list":
            return FakeResponse(
                status=self.list_status,
                body={"message": "listing denied"} if self.list_status >= 400 else {"data": {}},
            )
        raise AssertionError(f"unexpected request {method} {path}")

    def put(self, url, **kwargs):
        payload = kwargs.get("data")
        content = payload.read() if hasattr(payload, "read") else payload
        self.puts.append((url, content))
        return FakeResponse()


class FakeArtStudioClient:
    def auth_headers(self):
        return {"Authorization": "Bearer test"}

    def fetch_identity(self):
        return {
            "ok": True,
            "status": 200,
            "user": {"id": "user-7", "display_name": "Tester"},
        }


class ArtStudioUploadServiceTests(unittest.TestCase):
    def service(self, http, max_size=1024 * 1024):
        return ArtStudioUploadService(
            "https://artstudio.test/api",
            FakeArtStudioClient(),
            max_size_bytes=max_size,
            http=http,
        )

    def test_public_upload_is_immediately_listed(self):
        http = FakeHttp()
        result = self.service(http).upload(
            upload_file(), "叉车模型", visibility="public", description="测试模型"
        )

        self.assertEqual("listed", result["listing_status"])
        self.assertEqual("asset-123", result["asset"]["file_number"])
        paths = [(method, path) for method, path, _ in http.requests]
        self.assertIn(("POST", "/assets/asset-123/list"), paths)
        create_payload = next(
            payload for method, path, payload in http.requests
            if method == "POST" and path == "/assets"
        )
        self.assertEqual(1, create_payload["visibility"])
        self.assertEqual(2, create_payload["ownerType"])
        self.assertEqual(["file-new"], create_payload["fileIds"])

    def test_private_upload_uses_dedup_and_does_not_list(self):
        http = FakeHttp(deduped=True)
        result = self.service(http).upload(upload_file(), "私人模型", visibility="private")

        self.assertEqual("private", result["listing_status"])
        paths = [(method, path) for method, path, _ in http.requests]
        self.assertNotIn(("POST", "/assets/asset-123/list"), paths)
        self.assertNotIn(("POST", "/asset-uploads/finalize-single"), paths)
        create_payload = next(
            payload for method, path, payload in http.requests
            if method == "POST" and path == "/assets"
        )
        self.assertEqual(4, create_payload["visibility"])
        self.assertEqual(["file-dedup"], create_payload["fileIds"])

    def test_cover_is_uploaded_and_attached_when_available(self):
        http = FakeHttp()
        result = self.service(http).upload(
            upload_file(), "带封面模型", visibility="public", cover_file=cover_file()
        )

        paths = [(method, path) for method, path, _ in http.requests]
        self.assertIn(("POST", "/asset-uploads/single"), paths)
        create_payload = next(
            payload for method, path, payload in http.requests
            if method == "POST" and path == "/assets"
        )
        self.assertEqual(["file-new"], create_payload["coverFileIds"])
        self.assertNotIn("coverFileId", create_payload)
        self.assertEqual("https://store.test/cover.jpg", result["asset"]["cover_url"])
        self.assertEqual(2, len(http.puts))
        cover_finalize = next(
            payload for method, path, payload in http.requests
            if method == "POST" and path == "/asset-uploads/finalize-single"
            and payload["mime"] == "image/jpeg"
        )
        self.assertNotIn("kind", cover_finalize)

    def test_invalid_glb_never_calls_upstream(self):
        http = FakeHttp()
        with self.assertRaises(ArtStudioUploadError) as raised:
            self.service(http).upload(upload_file(b"not-a-glb"), "坏模型")

        self.assertEqual("invalid_glb", raised.exception.code)
        self.assertEqual([], http.requests)

    def test_public_listing_failure_reports_created_asset(self):
        http = FakeHttp(list_status=409)
        with self.assertRaises(ArtStudioUploadError) as raised:
            self.service(http).upload(upload_file(), "待处理模型", visibility="public")

        self.assertEqual("artstudio_public_listing_failed", raised.exception.code)
        self.assertTrue(raised.exception.fields["asset_created"])
        self.assertEqual("asset-123", raised.exception.fields["asset"]["file_number"])


if __name__ == "__main__":
    unittest.main()
