"""实例元信息对空心跳的容错。

回归背景：UE 反向收编（source=ue_migrated）的实例入库时从未上报心跳，
PG 的 instance.last_seen 就是 NULL。旧代码直接 `now - inst["last_seen"]`，
507 个这类实例让 /api/v2/instances 与 /api/v2/state/snapshots 全部 500，
实例运维页打不开、UE 也拉不到快照。
"""
import os
import sys
import tempfile
import unittest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import ProjectStore  # noqa: E402


class NullHeartbeatTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project("Null Heartbeat", project_id="p_null_hb")

    def tearDown(self):
        self.temp.cleanup()

    def _put(self, instance_id, **overrides):
        """直接塞一条实例记录，模拟迁移工具写库的形状。"""
        rec = {
            "id": instance_id,
            "object_type_rid": "zhhz.exhibit",
            "object_type_name": "展品",
            "status": "offline",
            "created_at": 1787554293.378,
            "last_seen": None,
            "raw_state": {},
            "render_config": {},
        }
        rec.update(overrides)
        self.store._current["instances"][instance_id] = rec
        return rec

    def test_list_all_survives_null_last_seen(self):
        """核心回归：last_seen 为 None 时不得抛 TypeError。"""
        self._put("ue_MIGRATED_1")
        rows = self.store.list_all()          # 修复前这里 TypeError
        self.assertEqual(1, len(rows))
        self.assertEqual("offline", rows[0]["status"])
        self.assertIsNone(rows[0]["last_seen"])

    def test_null_last_seen_reads_as_offline_not_online(self):
        """语义：从未上报 = 离线，不能因为 None 被当成 0 或当成刚上报。"""
        self._put("ue_MIGRATED_2")
        row = self.store.list_all()[0]
        self.assertEqual("offline", row["status"])

    def test_missing_last_seen_key_also_tolerated(self):
        """键整个缺失（老快照 / 手工构造）同样不能崩。"""
        rec = self._put("ue_MIGRATED_3")
        del rec["last_seen"]
        row = self.store.list_all()[0]
        self.assertEqual("offline", row["status"])
        self.assertIsNone(row["last_seen"])

    def test_fresh_heartbeat_still_reads_online(self):
        """不能为了容错把正常心跳也判成离线。"""
        import time
        self._put("live_1", last_seen=time.time())
        row = next(r for r in self.store.list_all() if r["id"] == "live_1")
        self.assertEqual("online", row["status"])

    def test_stale_heartbeat_reads_offline(self):
        """超过 3s 阈值仍判离线，边界行为不变。"""
        import time
        self._put("stale_1", last_seen=time.time() - 10)
        row = next(r for r in self.store.list_all() if r["id"] == "stale_1")
        self.assertEqual("offline", row["status"])

    def test_mixed_population_does_not_break_the_whole_list(self):
        """一条脏数据不能连累整份列表——这正是线上 507 实例全挂的形态。"""
        import time
        self._put("ue_MIGRATED_4")
        self._put("live_2", last_seen=time.time())
        rows = {r["id"]: r for r in self.store.list_all()}
        self.assertEqual(2, len(rows))
        self.assertEqual("offline", rows["ue_MIGRATED_4"]["status"])
        self.assertEqual("online", rows["live_2"]["status"])

    def test_get_instance_metadata_single_also_tolerated(self):
        """单条查询走同一个 _instance_metadata，一并覆盖。"""
        self._put("ue_MIGRATED_5")
        meta = self.store.get_instance_metadata("ue_MIGRATED_5")
        self.assertIsNotNone(meta)
        self.assertEqual("offline", meta["status"])

    def test_null_created_at_tolerated(self):
        """created_at 同样用 .get 取，缺失不应 KeyError。"""
        rec = self._put("ue_MIGRATED_6")
        del rec["created_at"]
        row = self.store.list_all()[0]
        self.assertIsNone(row["created_at"])


if __name__ == "__main__":
    unittest.main()
