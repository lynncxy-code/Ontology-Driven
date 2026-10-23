"""get_active_copy 的字段投影。

背景：现场项目 507 个实例，render_config 平均 25KB 全在 render_parts 上（单实例
最多 1013 个部件），整包 14MB。get_active_copy 的全量 deepcopy 单次约 300ms，
而它有 20 个调用点，本体配置中心和实例运维页每次请求都要付这笔钱。

这组测试锁住三件事：
1. 默认副本不带 render_parts，但带 part_count；
2. 其余字段一字不差，且仍是可独立改动的深拷贝（不能退化成浅引用）；
3. with_render_parts=True 仍拿到完整明细（客户改动回写靠它做整包备份）。
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
from instance_model_binding.service import (  # noqa: E402
    is_assembly_render_config as binding_is_assembly,
)
from representation_container.service import (  # noqa: E402
    is_assembly_render_config as container_is_assembly,
)


def _part(i):
    return {
        "part_index": i,
        "component_name": f"SM_{i}",
        "mesh_path": f"/Game/Art/SM_{i}.SM_{i}",
        "material_paths": [f"/Game/Art/MI_{i}.MI_{i}"],
        "relative_transform": {"translation": [1.0 * i, 0.0, 0.0]},
    }


class ActiveCopyProjectionTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project("Projection", project_id="p_proj")
        self.store._current["instances"]["asm_1"] = {
            "id": "asm_1",
            "object_type_rid": "zhhz.machine",
            "object_type_name": "设备",
            "zone_id": "plant/F02",
            "status": "offline",
            "last_seen": None,
            "raw_state": {"translation_x": 1.0, "ui_label_content": "DEV-001"},
            "render_config": {
                "injected_interfaces": ["I3D_Representable"],
                "interface_configs": {"I3D_Spatial": {"enabled": True}},
                "asset_id": "a1",
                "ue_asset_path": "/Game/SM_A",
                "assembly_signature": "sig_abc",
                "render_parts": [_part(i) for i in range(5)],
            },
        }
        self.store._current["instances"]["plain_1"] = {
            "id": "plain_1",
            "object_type_rid": "zhhz.sensor",
            "status": "offline",
            "last_seen": None,
            "raw_state": {},
            "render_config": {"asset_id": "a2", "ue_asset_path": "/Game/SM_B"},
        }

    def tearDown(self):
        self.temp.cleanup()

    # --- 默认投影 ---

    def test_default_copy_drops_render_parts(self):
        config = self.store.get_active_copy()["instances"]["asm_1"]["render_config"]
        self.assertNotIn("render_parts", config)

    def test_default_copy_reports_part_count(self):
        config = self.store.get_active_copy()["instances"]["asm_1"]["render_config"]
        self.assertEqual(5, config["part_count"])

    def test_instance_without_parts_gets_no_part_count(self):
        """没有 render_parts 的普通实例不该凭空多出一个 part_count 字段。"""
        config = self.store.get_active_copy()["instances"]["plain_1"]["render_config"]
        self.assertNotIn("part_count", config)

    def test_other_render_config_fields_survive(self):
        config = self.store.get_active_copy()["instances"]["asm_1"]["render_config"]
        self.assertEqual("sig_abc", config["assembly_signature"])
        self.assertEqual("/Game/SM_A", config["ue_asset_path"])
        self.assertEqual({"I3D_Spatial": {"enabled": True}}, config["interface_configs"])

    def test_non_render_config_fields_survive(self):
        inst = self.store.get_active_copy()["instances"]["asm_1"]
        self.assertEqual("plant/F02", inst["zone_id"])
        self.assertEqual("DEV-001", inst["raw_state"]["ui_label_content"])

    def test_project_level_fields_survive(self):
        project = self.store.get_active_copy()
        self.assertEqual("p_proj", project["id"])
        self.assertIn("object_types", project)
        self.assertIn("scene_interactions", project)

    # --- 仍然是深拷贝 ---

    def test_projection_is_still_a_deep_copy(self):
        """投影必须仍然脱钩：改副本不能污染 _current。"""
        copy_a = self.store.get_active_copy()
        copy_a["instances"]["asm_1"]["raw_state"]["ui_label_content"] = "TAMPERED"
        copy_a["instances"]["asm_1"]["render_config"]["interface_configs"]["x"] = 1
        copy_a["object_types"]["injected"] = {}

        live = self.store.get_active()
        self.assertEqual(
            "DEV-001", live["instances"]["asm_1"]["raw_state"]["ui_label_content"]
        )
        self.assertNotIn(
            "x", live["instances"]["asm_1"]["render_config"]["interface_configs"]
        )
        self.assertNotIn("injected", live["object_types"])

    def test_projection_does_not_mutate_the_live_project(self):
        """取投影副本不能顺手把 _current 的 render_parts 删掉。"""
        self.store.get_active_copy()
        live_config = self.store.get_active()["instances"]["asm_1"]["render_config"]
        self.assertEqual(5, len(live_config["render_parts"]))
        self.assertNotIn("part_count", live_config)

    # --- 全量出口 ---

    def test_with_render_parts_returns_full_detail(self):
        config = self.store.get_active_copy(with_render_parts=True)["instances"][
            "asm_1"
        ]["render_config"]
        self.assertEqual(5, len(config["render_parts"]))
        self.assertEqual("/Game/Art/SM_3.SM_3", config["render_parts"][3]["mesh_path"])

    def test_full_copy_is_detached_too(self):
        full = self.store.get_active_copy(with_render_parts=True)
        full["instances"]["asm_1"]["render_config"]["render_parts"].clear()
        live = self.store.get_active()["instances"]["asm_1"]["render_config"]
        self.assertEqual(5, len(live["render_parts"]))

    def test_no_active_project_returns_none(self):
        empty = ProjectStore(
            os.path.join(self.temp.name, "empty_projects"),
            os.path.join(self.temp.name, "empty_active.json"),
        )
        empty._current = None
        self.assertIsNone(empty.get_active_copy())

    # --- 下游装配判定不能被投影带偏 ---

    def test_assembly_detection_survives_projection(self):
        """part_count 是明细的替身；两处判定都要认它，否则装配实例被当成普通模型。"""
        config = {"part_count": 5}
        self.assertTrue(binding_is_assembly(config))
        self.assertTrue(container_is_assembly(config))

    def test_plain_config_still_not_assembly(self):
        config = {"asset_id": "a2", "ue_asset_path": "/Game/SM_B"}
        self.assertFalse(binding_is_assembly(config))
        self.assertFalse(container_is_assembly(config))


if __name__ == "__main__":
    unittest.main()
