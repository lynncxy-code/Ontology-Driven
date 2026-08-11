"""冒烟自测：回收站 put/list/restore/delete/purge/expire。"""
import os
import sys
import time
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from trash_store import TrashStore  # noqa: E402
from project_store import ProjectStore  # noqa: E402


class TrashSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ontotwin_trash_")
        self.ts = TrashStore(root_dir=os.path.join(self.tmp, "trash"))
        self.ps = ProjectStore(
            projects_dir=os.path.join(self.tmp, "projects"),
            active_file=os.path.join(self.tmp, "active.json"),
            trash_store=self.ts,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed_instance(self, iid, name="demo"):
        self.ps._current["instances"][iid] = {"id": iid, "name": name}
        self.ps._save_current()

    def test_remove_instance_goes_to_trash_and_restores(self):
        self.ps.create_project("测试", object_types={"T1": {"name": "T1"}})
        self._seed_instance("i1")
        self.ps.remove("i1")

        items = self.ts.list_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "instance")

        entry, payload = self.ts.get_snapshot(items[0]["id"])
        self.assertIsNotNone(payload)
        self.ps.restore_instance(payload)
        self.assertIn("i1", self.ps._current["instances"])

    def test_clear_scene_snapshots_and_restores(self):
        self.ps.create_project("测试")
        self._seed_instance("a")
        self._seed_instance("b")
        self.ps.clear_instances()

        items = [i for i in self.ts.list_items() if i["kind"] == "scene"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["instance_count"], 2)
        self.assertEqual(self.ps._current["instances"], {})

        _, payload = self.ts.get_snapshot(items[0]["id"])
        self.ps.restore_scene(payload)
        self.assertEqual(len(self.ps._current["instances"]), 2)

    def test_delete_project_snapshots_and_restores(self):
        proj = self.ps.create_project("测试")
        pid = proj["id"]
        self._seed_instance("x")
        self.ps.delete_project(pid)

        # 项目文件已删除
        self.assertFalse(os.path.exists(self.ps._path(pid)))
        items = [i for i in self.ts.list_items() if i["kind"] == "project"]
        self.assertEqual(len(items), 1)

        _, payload = self.ts.get_snapshot(items[0]["id"])
        self.ps.restore_project(payload)
        self.assertTrue(os.path.exists(self.ps._path(pid)))

    def test_purge_and_delete(self):
        self.ps.create_project("p1")
        self._seed_instance("i1")
        self.ps.remove("i1")
        self._seed_instance("i2")
        self.ps.remove("i2")
        self.assertEqual(len(self.ts.list_items()), 2)

        one = self.ts.list_items()[0]["id"]
        self.assertTrue(self.ts.delete(one))
        self.assertEqual(len(self.ts.list_items()), 1)

        n = self.ts.purge_all()
        self.assertEqual(n, 1)
        self.assertEqual(self.ts.list_items(), [])

    def test_sweep_expired(self):
        # 用 TTL=0 关闭清理；再用极短 TTL 触发
        ts = TrashStore(root_dir=os.path.join(self.tmp, "trash2"), ttl_seconds=1)
        ps = ProjectStore(
            projects_dir=os.path.join(self.tmp, "projects2"),
            active_file=os.path.join(self.tmp, "active2.json"),
            trash_store=ts,
        )
        ps.create_project("测试")
        ps._current["instances"]["z"] = {"id": "z"}
        ps._save_current()
        ps.remove("z")
        self.assertEqual(len(ts.list_items()), 1)
        time.sleep(2.2)  # 秒级取整 + TTL=1，需超过 2s 以避免整秒边界
        # list_items 内会顺带 sweep
        self.assertEqual(len(ts.list_items()), 0)


if __name__ == "__main__":
    unittest.main()
