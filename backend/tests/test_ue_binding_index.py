"""UE-ID→pid 索引 + resolver + bind 互斥 单元测试。"""
import os
import sys
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from project_store import ProjectStore  # noqa: E402
from trash_store import TrashStore  # noqa: E402
import ue_project_binding as ub  # noqa: E402


class FakeRequest:
    def __init__(self, headers=None, args=None, body=None):
        self.headers = headers or {}
        self.args = args or {}
        self._body = body

    def get_json(self, silent=False):
        return self._body


def ue_request(ue_id, browser=False, body=None):
    headers = {"X-OntoTwin-UE-Project-Id": ue_id} if ue_id else {}
    if browser and not ue_id:
        headers["User-Agent"] = "Mozilla/5.0"
    return FakeRequest(headers=headers, body=body)


class UeBindingIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ontotwin_ue_")
        ts = TrashStore(root_dir=os.path.join(self.tmp, "trash"))
        self.ps = ProjectStore(
            projects_dir=os.path.join(self.tmp, "projects"),
            active_file=os.path.join(self.tmp, "active.json"),
            trash_store=ts,
        )
        # 清空全局索引，避免 test 顺序污染
        ub._ue_index.clear()

    def tearDown(self):
        ub._ue_index.clear()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 基础 CRUD ──
    def test_index_set_lookup_unset(self):
        ub.index_set("ueproj_A", "p1")
        self.assertEqual(ub.index_lookup("ueproj_A"), "p1")
        ub.index_unset("ueproj_A")
        self.assertIsNone(ub.index_lookup("ueproj_A"))

    def test_index_forget_project_clears_multiple(self):
        ub.index_set("ueA", "p1")
        ub.index_set("ueB", "p1")
        ub.index_set("ueC", "p2")
        ub.index_forget_project("p1")
        self.assertIsNone(ub.index_lookup("ueA"))
        self.assertIsNone(ub.index_lookup("ueB"))
        self.assertEqual(ub.index_lookup("ueC"), "p2")

    # ── rebuild_index 扫盘 ──
    def test_rebuild_index_from_projects(self):
        p1 = self.ps.create_project(
            "P1",
            dataset={"id": "p1", "name": "P1", "bound_ue_project_id": "ue_x", "bound_ue_project_name": "ue_x"},
        )
        self.ps.deactivate()
        p2 = self.ps.create_project(
            "P2",
            dataset={"id": "p2", "name": "P2", "bound_ue_project_id": "ue_y"},
        )
        ub._ue_index.clear()
        idx = ub.rebuild_index(self.ps)
        # 两个项目都被扫到
        self.assertEqual(idx.get("ue_x"), p1["id"])
        self.assertEqual(idx.get("ue_y"), p2["id"])

    # ── resolve_project_for_ue ──
    def test_resolve_web_bypass(self):
        pid, ok, info = ub.resolve_project_for_ue(self.ps, ue_request(None, browser=True))
        self.assertTrue(ok)
        self.assertIsNone(pid)
        self.assertEqual(info["mode"], "web-bypass")

    def test_resolve_mcp_client_bypass(self):
        """MCP 客户端带 X-OntoTwin-Client:MCP，无 UE-ID 也应放行。"""
        req = FakeRequest(headers={"X-OntoTwin-Client": "MCP"})
        pid, ok, info = ub.resolve_project_for_ue(self.ps, req)
        self.assertTrue(ok)
        self.assertIsNone(pid)
        self.assertEqual(info["mode"], "web-bypass")

    def test_resolve_ue_matched(self):
        ub.index_set("ueX", "pX")
        pid, ok, info = ub.resolve_project_for_ue(self.ps, ue_request("ueX"))
        self.assertTrue(ok)
        self.assertEqual(pid, "pX")
        self.assertEqual(info["mode"], "matched")

    def test_resolve_ue_unbound_rejected(self):
        pid, ok, info = ub.resolve_project_for_ue(self.ps, ue_request("ueGhost"))
        self.assertFalse(ok)
        self.assertIsNone(pid)
        # 错误码沿用 ue_project_mismatch 以兼容 UE 插件里的硬编码
        self.assertEqual(info["error"], "ue_project_mismatch")

    def test_resolve_non_browser_no_header_rejected(self):
        pid, ok, info = ub.resolve_project_for_ue(self.ps, ue_request(None, browser=False))
        self.assertFalse(ok)
        self.assertEqual(info["error"], "ue_project_required")

    # ── bind 互斥 ──
    def test_bind_exclusive_conflict(self):
        p1 = self.ps.create_project("P1", dataset={"id": "p1", "name": "P1"})
        ok, info = ub.bind_active_dataset(self.ps, "ue_alpha", "ue_alpha")
        self.assertTrue(ok, info)

        # 切激活到另一个项目
        self.ps.deactivate()
        p2 = self.ps.create_project("P2", dataset={"id": "p2", "name": "P2"})
        # 再拿同一个 UE-ID 绑 → 应冲突
        ok, info = ub.bind_active_dataset(self.ps, "ue_alpha", "ue_alpha")
        self.assertFalse(ok)
        self.assertEqual(info["error"], "ue_project_already_bound")
        self.assertEqual(info["bound_to"], p1["id"])

    def test_bind_force_migrates(self):
        p1 = self.ps.create_project("P1", dataset={"id": "p1", "name": "P1"})
        ub.bind_active_dataset(self.ps, "ue_beta", "ue_beta")

        self.ps.deactivate()
        p2 = self.ps.create_project("P2", dataset={"id": "p2", "name": "P2"})
        ok, info = ub.bind_active_dataset(self.ps, "ue_beta", "ue_beta", force=True)
        self.assertTrue(ok, info)
        # 索引应指向新项目
        self.assertEqual(ub.index_lookup("ue_beta"), p2["id"])
        # 旧项目的 bound 应被清空
        old = self.ps.read_project(p1["id"])
        self.assertEqual((old.get("dataset") or {}).get("bound_ue_project_id", ""), "")

    def test_bind_write_failure_rolls_back_old_binding(self):
        """新绑定写失败时，旧项目的绑定应被回滚到原状。"""
        p1 = self.ps.create_project("P1", dataset={"id": "p1", "name": "P1"})
        ub.bind_active_dataset(self.ps, "ue_gamma", "ue_gamma")
        self.ps.deactivate()
        p2 = self.ps.create_project("P2", dataset={"id": "p2", "name": "P2"})

        # 让新绑定写失败：patch set_dataset 抛错
        original_set = self.ps.set_dataset
        def boom(*a, **kw):
            raise RuntimeError("simulated write failure")
        self.ps.set_dataset = boom

        ok, info = ub.bind_active_dataset(self.ps, "ue_gamma", "ue_gamma", force=True)
        self.ps.set_dataset = original_set

        self.assertFalse(ok)
        self.assertEqual(info["error"], "write_binding_failed")
        # 索引未更新 → 仍指向旧项目
        self.assertEqual(ub.index_lookup("ue_gamma"), p1["id"])
        # 旧项目的 dataset 绑定应被回滚回原值
        p1_after = self.ps.read_project(p1["id"])
        ds = p1_after.get("dataset") or {}
        self.assertEqual(ds.get("bound_ue_project_id"), "ue_gamma")

    def test_bind_clear_previous_failure_aborts(self):
        """清旧项目绑定失败时应中止，索引不动。"""
        p1 = self.ps.create_project("P1", dataset={"id": "p1", "name": "P1"})
        ub.bind_active_dataset(self.ps, "ue_delta", "ue_delta")
        self.ps.deactivate()
        p2 = self.ps.create_project("P2", dataset={"id": "p2", "name": "P2"})

        original_write = self.ps.write_project
        def boom_write(pid, proj):
            if pid == p1["id"]:
                raise RuntimeError("simulated clear failure")
            return original_write(pid, proj)
        self.ps.write_project = boom_write

        ok, info = ub.bind_active_dataset(self.ps, "ue_delta", "ue_delta", force=True)
        self.ps.write_project = original_write

        self.assertFalse(ok)
        self.assertEqual(info["error"], "clear_previous_binding_failed")
        # 索引未变
        self.assertEqual(ub.index_lookup("ue_delta"), p1["id"])


if __name__ == "__main__":
    unittest.main()
