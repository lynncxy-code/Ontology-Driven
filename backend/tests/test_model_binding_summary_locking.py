"""类型列表的 model_binding 汇总：行为不变，但别再逐实例抢锁。

背景：/api/v2/ontology/types 每个类型都要算 model_binding.migration_models，
旧实现对每个实例调一次 instance_store.get_render_config()，等于抢 N 次锁。
而写路径 update_raw_state(persist=True) -> _save_current() 是握着同一把锁
全量重写整个项目（14MB 现场实测一次一秒多）。UE 实时上报时，读侧那 507 次抢锁
每次都可能排在一次全量写后面，接口就慢到几秒。

这组测试锁住两件事：
1. migration_models 的分组、计数、排序、样本一字不变（含只能从 render_config
   取路径的装配实例）；
2. 取 render_config 的抢锁次数不再随实例数增长——带 source_asset_path 的实例
   一次都不该取。
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


class CountingStore(ProjectStore):
    """记录 render_config 的两种取法各被调用多少次。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.single_calls = 0
        self.batch_calls = 0
        self.batch_ids = 0

    def get_render_config(self, instance_id):
        self.single_calls += 1
        return super().get_render_config(instance_id)

    def get_render_configs(self, instance_ids):
        ids = list(instance_ids)
        self.batch_calls += 1
        self.batch_ids += len(ids)
        return super().get_render_configs(ids)


class ModelBindingSummaryTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CountingStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project("Summary", project_id="p_summary")

        import app as backend_app
        self.app = backend_app
        self._saved_store = backend_app.instance_store
        backend_app.instance_store = self.store

    def tearDown(self):
        self.app.instance_store = self._saved_store
        self.temp.cleanup()

    def _add(self, iid, rid="zhhz.machine", source_asset_path="", render_config=None):
        self.store._current["instances"][iid] = {
            "id": iid,
            "object_type_rid": rid,
            "object_type_name": "设备",
            "status": "offline",
            "last_seen": None,
            "created_at": 1787554293.378,
            "source_asset_path": source_asset_path,
            "raw_state": {},
            "render_config": render_config if render_config is not None else {},
        }

    def _summary(self, rid="zhhz.machine", ot=None):
        instances = self.store.list_all()
        by_type = {}
        for inst in instances:
            by_type.setdefault(inst.get("object_type_rid"), []).append(inst)
        return self.app._model_binding_summary(rid, ot or {}, by_type)

    # --- 行为不变 ---

    def test_groups_by_source_asset_path_with_counts(self):
        self._add("i1", source_asset_path="/Game/Art/SM_A")
        self._add("i2", source_asset_path="/Game/Art/SM_A")
        self._add("i3", source_asset_path="/Game/Art/SM_B")
        models = self._summary()["migration_models"]
        self.assertEqual(["/Game/Art/SM_A", "/Game/Art/SM_B"],
                         [m["path"] for m in models])
        self.assertEqual([2, 1], [m["instance_count"] for m in models])

    def test_sorted_by_count_desc_then_path(self):
        for n in range(3):
            self._add(f"b{n}", source_asset_path="/Game/B")
        self._add("a1", source_asset_path="/Game/A")
        models = self._summary()["migration_models"]
        self.assertEqual(["/Game/B", "/Game/A"], [m["path"] for m in models])

    def test_assembly_path_still_falls_back_to_render_config(self):
        """没有 source_asset_path 的装配实例，路径仍要从 render_config 里取到。"""
        self._add("asm", source_asset_path="", render_config={
            "assembly_signature": "sig_x",
            "ue_asset_path": "/Game/Art/SM_Assembly",
            "render_parts": [{"part_index": 0}],
        })
        models = self._summary()["migration_models"]
        self.assertEqual(["/Game/Art/SM_Assembly"], [m["path"] for m in models])
        self.assertEqual(1, models[0]["instance_count"])

    def test_assembly_falls_back_to_asset_id_when_no_ue_path(self):
        self._add("asm2", source_asset_path="", render_config={
            "assembly_signature": "sig_y", "asset_id": "a_fallback",
        })
        self.assertEqual(["a_fallback"],
                         [m["path"] for m in self._summary()["migration_models"]])

    def test_non_assembly_without_path_is_skipped(self):
        """既没有 source_asset_path 又不是装配的实例，不该产生分组。"""
        self._add("plain", source_asset_path="", render_config={"asset_id": "x"})
        self.assertEqual([], self._summary()["migration_models"])

    def test_sample_instances_capped_at_five(self):
        for n in range(9):
            self._add(f"s{n}", source_asset_path="/Game/Same")
        models = self._summary()["migration_models"]
        self.assertEqual(9, models[0]["instance_count"])
        self.assertEqual(5, len(models[0]["sample_instances"]))

    def test_default_model_comes_from_type_not_instances(self):
        self._add("i1", source_asset_path="/Game/Art/SM_A")
        summary = self._summary(ot={"ue_asset_path": "/Game/Default/SM_D"})
        self.assertEqual("/Game/Default/SM_D", summary["default_model"]["path"])

    def test_mixed_population_matches_expected_grouping(self):
        """带 path 的和只能靠 render_config 的混在一起，结果要合并正确。"""
        self._add("m1", source_asset_path="/Game/Art/SM_A")
        self._add("m2", source_asset_path="", render_config={
            "assembly_signature": "sig", "ue_asset_path": "/Game/Art/SM_A"})
        self._add("m3", source_asset_path="/Game/Art/SM_B")
        models = {m["path"]: m["instance_count"]
                  for m in self._summary()["migration_models"]}
        self.assertEqual({"/Game/Art/SM_A": 2, "/Game/Art/SM_B": 1}, models)

    # --- 抢锁次数 ---

    def test_no_render_config_lookup_when_all_have_source_path(self):
        """现场形态：迁移实例都带 source_asset_path，一次锁都不该抢。"""
        for n in range(50):
            self._add(f"p{n}", source_asset_path=f"/Game/Art/SM_{n % 7}")
        self._summary()
        self.assertEqual(0, self.store.single_calls)
        self.assertEqual(0, self.store.batch_calls)

    def test_lookup_is_batched_not_per_instance(self):
        """确实需要 render_config 时，也只能抢一次锁。"""
        for n in range(50):
            self._add(f"q{n}", source_asset_path="", render_config={
                "assembly_signature": f"sig{n}", "ue_asset_path": f"/Game/X_{n % 3}"})
        self._summary()
        self.assertEqual(0, self.store.single_calls,
                         "不应再逐实例调 get_render_config")
        self.assertEqual(1, self.store.batch_calls,
                         "批量取只能抢一次锁")
        self.assertEqual(50, self.store.batch_ids)

    def test_batch_only_fetches_instances_that_need_it(self):
        """带 path 的实例不该混进批量请求里白取。"""
        for n in range(10):
            self._add(f"has{n}", source_asset_path=f"/Game/Has_{n}")
        for n in range(3):
            self._add(f"non{n}", source_asset_path="", render_config={
                "assembly_signature": "s", "ue_asset_path": "/Game/Non"})
        self._summary()
        self.assertEqual(3, self.store.batch_ids)

    # --- 批量取本身 ---

    def test_get_render_configs_returns_detached_copies(self):
        self._add("d1", render_config={"asset_id": "a", "nested": {"k": 1}})
        got = self.store.get_render_configs(["d1"])["d1"]
        got["asset_id"] = "TAMPERED"
        live = self.store.get_active()["instances"]["d1"]["render_config"]
        self.assertEqual("a", live["asset_id"])

    def test_get_render_configs_skips_unknown_ids(self):
        self._add("d1", render_config={"asset_id": "a"})
        got = self.store.get_render_configs(["d1", "does_not_exist"])
        self.assertEqual(["d1"], list(got))

    def test_get_render_configs_empty_input(self):
        self.assertEqual({}, self.store.get_render_configs([]))


if __name__ == "__main__":
    unittest.main()
