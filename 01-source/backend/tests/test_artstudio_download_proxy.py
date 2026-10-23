"""ArtStudio 下载代理：外网往返次数、版本语义、超时默认值。

背景：现场「换了模型但 UE 里显示不出来」是间歇性的——同一个资产连打 5 次，
不带 version 的 3 次全成功，带 version 的 3 次里 2 次 404。原因是带 version 时
端点要先 get_version 再 open_download_stream，两次外网往返；而 ArtStudio 详情
接口中位 0.39s 却偶发 4.19s，超时线只有 5s，任一次撞上就整体失败。
UE 下载必带 version（TwinInstance.cpp 拼的就是 ?id=..&version=..），所以它走的
正是失败率翻倍的那条路。

这组测试锁住三件事：
1. 一次下载只打一次 ArtStudio 详情接口；
2. 版本不符要回 409（资产更新了），不是 404（资产没了）；
3. 超时默认值不再是 5 秒。
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

# 打桩一律带 create=True：同目录下 test_artstudio_client / test_artstudio_upload
# 会把 sys.modules["requests"] 换成不带 get 的假模块且不还原，全量跑到这里时
# artstudio_client.requests 可能就是那个空壳。加 create=True 让本文件与执行顺序无关。


def _detail(version=1, with_glb=True):
    files = []
    if with_glb:
        files.append({
            "ext": "glb",
            "download_url": "https://s3.example.test/blob.glb",
            "name": "model.glb",
        })
    return {"name": "测试资产", "version": version, "files": files}


class _FakeResponse:
    status_code = 200
    headers = {"Content-Length": "123"}

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=65536):
        yield b"glb-bytes"

    def close(self):
        pass


class DownloadStreamTestCase(unittest.TestCase):
    def setUp(self):
        artstudio_client._version_cache.clear()

    # --- 外网往返次数 ---

    def test_single_detail_fetch_per_download(self):
        """一次下载只许打一次详情接口——这正是这次故障的根因。"""
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(version=3)) as fd, \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_FakeResponse()):
            stream, name, info = artstudio_client.open_download_stream("a1", 3)
        self.assertEqual(1, fd.call_count)
        self.assertIsNotNone(stream)
        self.assertEqual("ok", info["reason"])
        self.assertEqual("model.glb", name)

    def test_download_primes_version_cache(self):
        """详情已经拉过了，紧随其后的 get_version 不该再打一次外网。"""
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(version=7)) as fd, \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_FakeResponse()):
            artstudio_client.open_download_stream("a2", 7)
            self.assertEqual(7, artstudio_client.get_version("a2"))
        self.assertEqual(1, fd.call_count, "get_version 应命中缓存，不该二次拉详情")

    # --- 版本语义 ---

    def test_version_mismatch_is_reported_distinctly(self):
        """版本不符 = 资产更新了，必须和「没有/不可达」区分开。"""
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(version=9)):
            stream, _, info = artstudio_client.open_download_stream("a3", 4)
        self.assertIsNone(stream)
        self.assertEqual("version_mismatch", info["reason"])
        self.assertEqual(9, info["current_version"])

    def test_expected_version_none_skips_version_check(self):
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(version=2)), \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               return_value=_FakeResponse()):
            stream, _, info = artstudio_client.open_download_stream("a4", None)
        self.assertIsNotNone(stream)
        self.assertEqual("ok", info["reason"])

    def test_missing_glb_reports_no_glb(self):
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(with_glb=False)):
            stream, _, info = artstudio_client.open_download_stream("a5", None)
        self.assertIsNone(stream)
        self.assertEqual("no_glb", info["reason"])

    def test_unreachable_detail_reports_unreachable(self):
        with mock.patch.object(artstudio_client, "fetch_detail", return_value=None):
            stream, _, info = artstudio_client.open_download_stream("a6", None)
        self.assertIsNone(stream)
        self.assertEqual("unreachable", info["reason"])
        self.assertIsNone(info["current_version"])

    def test_upstream_failure_reports_unreachable_but_keeps_version(self):
        """S3 取不到时仍要带回版本号，便于调用方区分故障类型。"""
        with mock.patch.object(artstudio_client, "fetch_detail",
                               return_value=_detail(version=5)), \
             mock.patch.object(artstudio_client.requests, "get", create=True,
                               side_effect=RuntimeError("boom")):
            stream, _, info = artstudio_client.open_download_stream("a7", None)
        self.assertIsNone(stream)
        self.assertEqual("unreachable", info["reason"])
        self.assertEqual(5, info["current_version"])

    # --- 返回值形状（内部预取调用方依赖它）---

    def test_returns_three_tuple(self):
        with mock.patch.object(artstudio_client, "fetch_detail", return_value=None):
            result = artstudio_client.open_download_stream("a8")
        self.assertEqual(3, len(result))


class TimeoutDefaultTestCase(unittest.TestCase):
    def test_default_timeout_is_not_five_seconds(self):
        """5 秒贴着现场尖峰（实测 4.19s），必须放宽。"""
        source = os.path.join(BACKEND_DIR, "app.py")
        with open(source, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn('os.environ.get("ARTSTUDIO_TIMEOUT", "5")', text)
        self.assertIn('os.environ.get("ARTSTUDIO_TIMEOUT", "20")', text)

    def test_compose_default_matches_code_default(self):
        """compose 的 ${VAR:-默认} 会盖住 Python 的默认值，两处必须一致。"""
        compose = os.path.join(os.path.dirname(BACKEND_DIR), "docker-compose.yml")
        with open(compose, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("ARTSTUDIO_TIMEOUT=${ARTSTUDIO_TIMEOUT:-20}", text)


if __name__ == "__main__":
    unittest.main()
