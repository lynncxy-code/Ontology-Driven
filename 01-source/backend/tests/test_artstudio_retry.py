"""ArtStudio 瞬时故障重试。

背景：把超时从 5s 放宽到 20s 之后，现场成功率只从 66.7% 提到 80%。剩下的失败
拆开看是连接层 ConnectionError（"Max retries exceeded"），失败耗时固定停在
4.18s——不随超时线走，说明根本不是超时。30 轮实测：首次失败 2 次，重试全部
救回、0 次仍失败，即这类故障是瞬时抖动。

这组测试锁住两件事：
1. 传输层故障和 5xx 会重试，且重试能救回；
2. 4xx 是上游的确定性答复，绝不重试——否则查一个不存在的资产要白等三轮。
"""
import os
import sys
import unittest
from unittest import mock

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

import artstudio_client  # noqa: E402

# 打桩带 create=True：同目录的 test_artstudio_client / test_artstudio_upload
# 会把 sys.modules["requests"] 换成假模块且不还原。


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"data": {}}
        self.headers = {"Content-Length": "1"}
        self.closed = False

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size=65536):
        yield b"x"

    def close(self):
        self.closed = True


def _no_sleep():
    return mock.patch.object(artstudio_client.time, "sleep", lambda *_: None)


class GetWithRetryTestCase(unittest.TestCase):
    def test_transport_failure_then_success(self):
        """连接失败是瞬时的——重试应当救回来。"""
        calls = []

        def flaky(url, **kw):
            calls.append(url)
            if len(calls) == 1:
                raise OSError("Max retries exceeded")
            return _Resp(200)

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=flaky), _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertIsNotNone(resp)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(calls))

    def test_gives_up_after_all_attempts(self):
        """一直失败时要收手，不能无限重试。"""
        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=OSError("down")) as g, _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertIsNone(resp)
        self.assertEqual(len(artstudio_client._RETRY_BACKOFF) + 1, g.call_count)

    def test_server_error_is_retried(self):
        calls = []

        def flaky(url, **kw):
            calls.append(url)
            return _Resp(503) if len(calls) == 1 else _Resp(200)

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=flaky), _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(calls))

    def test_client_error_is_not_retried(self):
        """404 是确定性答复：资产就是不存在，重试只会让用户多等。"""
        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_Resp(404)) as g, _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertEqual(404, resp.status_code)
        self.assertEqual(1, g.call_count, "4xx 不该重试")

    def test_success_does_not_retry(self):
        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_Resp(200)) as g, _no_sleep():
            artstudio_client._get_with_retry("http://x/y")
        self.assertEqual(1, g.call_count)

    def test_backoff_is_applied_between_attempts(self):
        """重试之间要退避，别把上游按在地上打。"""
        waited = []
        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=OSError("down")), \
             mock.patch.object(artstudio_client.time, "sleep", waited.append):
            artstudio_client._get_with_retry("http://x/y")
        self.assertEqual(list(artstudio_client._RETRY_BACKOFF), waited)

    def test_slow_failure_is_not_retried(self):
        """慢性劣化不该重试：已经挂了很久的请求，再试一次只是让调用方干等。

        没有这个预算，最坏情况会把 S3 的 180s 读超时乘以 3（≈570s），
        而 Flask 是 threaded=True 无线程池上限。
        """
        clock = [0.0]
        calls = []

        def slow_fail(url, **kw):
            calls.append(url)
            clock[0] += 40.0          # 单次就烧掉超过预算的时间
            raise OSError("hang then fail")

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=slow_fail), \
             mock.patch.object(artstudio_client.time, "time", lambda: clock[0]), \
             _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertIsNone(resp)
        self.assertEqual(1, len(calls), "超出时间预算后不该再重试")

    def test_fast_failure_still_retried_within_budget(self):
        """快速失败仍要重试——这才是重试真正要救的那一类。"""
        clock = [0.0]
        calls = []

        def fast_fail(url, **kw):
            calls.append(url)
            clock[0] += 4.18          # 现场实测的 ConnectionError 固定耗时
            if len(calls) < 3:
                raise OSError("Max retries exceeded")
            return _Resp(200)

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=fast_fail), \
             mock.patch.object(artstudio_client.time, "time", lambda: clock[0]), \
             _no_sleep():
            resp = artstudio_client._get_with_retry("http://x/y")
        self.assertIsNotNone(resp)
        self.assertEqual(3, len(calls))

    def test_server_error_response_is_closed(self):
        """stream=True 的 5xx 响应要关掉，别漏连接。"""
        bad = _Resp(503)
        calls = []

        def flaky(url, **kw):
            calls.append(url)
            return bad if len(calls) == 1 else _Resp(200)

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=flaky), _no_sleep():
            artstudio_client._get_with_retry("http://x/y", stream=True)
        self.assertTrue(bad.closed)


class FetchDetailRetryTestCase(unittest.TestCase):
    def setUp(self):
        artstudio_client._version_cache.clear()

    def test_detail_survives_transient_failure(self):
        payload = {"data": {"name": "沙发", "currentVersion": 2, "files": [
            {"displayName": "m.glb", "downloadUrl": "https://s3/x.glb"}]}}
        calls = []

        def flaky(url, **kw):
            calls.append(url)
            if len(calls) == 1:
                raise OSError("connection reset")
            return _Resp(200, payload)

        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=flaky), _no_sleep():
            detail = artstudio_client.fetch_detail("a1")
        self.assertIsNotNone(detail)
        self.assertEqual(2, detail["version"])
        self.assertEqual(1, len(detail["files"]))

    def test_detail_404_returns_none_without_retry(self):
        with mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_Resp(404)) as g, _no_sleep():
            self.assertIsNone(artstudio_client.fetch_detail("missing"))
        self.assertEqual(1, g.call_count)


class DownloadRetryTestCase(unittest.TestCase):
    def setUp(self):
        artstudio_client._version_cache.clear()

    def _detail(self):
        return {"name": "x", "version": 1, "files": [
            {"ext": "glb", "download_url": "https://s3/x.glb", "name": "x.glb"}]}

    def test_s3_transient_failure_is_retried(self):
        """S3 这一跳和详情接口一样会抖，必须同样重试。"""
        calls = []

        def flaky(url, **kw):
            calls.append(url)
            if len(calls) == 1:
                raise OSError("Max retries exceeded")
            return _Resp(200)

        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=self._detail()), \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=flaky), _no_sleep():
            stream, name, info = artstudio_client.open_download_stream("a1", 1)
        self.assertIsNotNone(stream)
        self.assertEqual("ok", info["reason"])
        self.assertEqual(2, len(calls))

    def test_s3_permanent_failure_reports_unreachable(self):
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=self._detail()), \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=OSError("down")), _no_sleep():
            stream, _, info = artstudio_client.open_download_stream("a1", 1)
        self.assertIsNone(stream)
        self.assertEqual("unreachable", info["reason"])
        self.assertEqual(1, info["current_version"])

    def test_s3_404_is_not_retried(self):
        """预签名链接失效是确定性的，重试没意义。"""
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=self._detail()), \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_Resp(404)) as g, _no_sleep():
            stream, _, info = artstudio_client.open_download_stream("a1", 1)
        self.assertIsNone(stream)
        self.assertEqual("unreachable", info["reason"])
        self.assertEqual(1, g.call_count)

    def test_version_mismatch_never_reaches_network(self):
        """版本不符是确定性结论，不该再去碰 S3。"""
        detail = self._detail()
        detail["version"] = 9
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=detail), \
             mock.patch.object(artstudio_client.requests, "get", create=True) as g, \
             _no_sleep():
            stream, _, info = artstudio_client.open_download_stream("a1", 1)
        self.assertIsNone(stream)
        self.assertEqual("version_mismatch", info["reason"])
        self.assertEqual(0, g.call_count)


if __name__ == "__main__":
    unittest.main()
