"""Catalog-backed selection: never write a stale or cross-project model binding."""
import copy
import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask, jsonify, request

from .test_instance_model_binding import ProjectStore, FakeArtStudio
from instance_model_binding.service import InstanceModelBindingService, InstanceModelBindingError
from ue_asset_catalog.service import UEAssetCatalogService, AssetCatalogError


class CatalogPickerBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(os.path.join(self.temp.name, "projects"), os.path.join(self.temp.name, "active.json"))
        self.store.create_project("QA", {"type": {
            "name": "设备", "injected_interfaces": ["I3D_Representable"],
            "asset_id": "old.glb", "ue_asset_path": "old.glb",
        }}, project_id="qa", dataset={"id": "qa", "bound_ue_project_id": "ue-qa"})
        self.store.spawn("one", "type", render_config={})
        self.store.spawn("two", "type", render_config={})
        self.catalog = UEAssetCatalogService(self.store, os.path.join(self.temp.name, "catalog"))
        self.upload = {
            "ue_project_id": "ue-qa", "roots": ["/Game/Models"],
            "assets": [
                {"object_path": "/Game/Models/SM_A.SM_A", "asset_kind": "StaticMesh", "display_name": "测试机"},
                {"object_path": "/Game/Models/SK_A.SK_A", "asset_kind": "SkeletalMesh"},
                {"object_path": "/Game/Models/BP_A.BP_A", "asset_kind": "Blueprint"},
            ],
        }
        self.catalog.replace_catalog(self.upload)
        self.payload = {
            "source": "ue_catalog", "expected_project_id": "qa", "ue_project_id": "ue-qa",
            "catalog_revision": self.catalog.get_catalog()["catalog_revision"],
            "file_number": "/Game/Models/SM_A.SM_A", "object_type_rid": "type",
        }
        self.instance = InstanceModelBindingService(self.store, {}, FakeArtStudio())
        self.instance.ue_asset_catalog = self.catalog

    def tearDown(self):
        self.temp.cleanup()

    def assertRejectedWithoutWrite(self, payload):
        before = self.store.get_active_copy()
        with self.assertRaises(AssetCatalogError):
            self.catalog.bind_type(payload)
        self.assertEqual(before, self.store.get_active_copy())
        with self.assertRaises(InstanceModelBindingError):
            self.instance.save("one", payload)
        self.assertEqual(before, self.store.get_active_copy())

    def test_type_selection_preserves_instance_overrides_and_schema(self):
        self.instance.save("one", {"file_number": "other.glb"})
        old = self.store.get_render_config("one")
        result = self.catalog.bind_type(self.payload)
        self.assertTrue(result["valid"])
        self.assertEqual(result["name"], "测试机")
        self.assertEqual(self.store.get_object_types()["type"]["ue_asset_path"], self.payload["file_number"])
        self.assertEqual(self.store.get_render_config("one"), old)
        self.assertEqual(self.store.get_render_config("two"), {})

    def test_instance_only_selection_uses_existing_schema(self):
        self.instance.save("one", self.payload)
        selected = self.store.get_render_config("one")["model_override"]
        self.assertEqual(selected["label"], "测试机")
        self.assertEqual(selected["source"], "ue_cooked")
        self.assertEqual(self.store.get_render_config("two"), {})
        self.assertEqual(self.store.get_object_types()["type"]["ue_asset_path"], "old.glb")

    def test_stale_wrong_project_and_unsupported_selections_rejected(self):
        for changes in [
            {"expected_project_id": "other"}, {"ue_project_id": "other"},
            {"catalog_revision": "old"}, {"file_number": "/Game/Missing.Missing"},
            {"ue_asset_path": "/Game/Other.Other"}, {"file_number": "/Game/Models/BP_A.BP_A"},
        ]:
            with self.subTest(changes=changes):
                self.assertRejectedWithoutWrite({**self.payload, **changes})

    def test_rebind_between_selection_and_write_rejected(self):
        original = self.store.transact_active
        expected = []
        def concurrent_rebind(updater, *args, **kwargs):
            dataset = copy.deepcopy(self.store.get_active_dataset())
            dataset["bound_ue_project_id"] = "new-ue"
            self.store.set_dataset(dataset)
            expected.append(self.store.get_active_copy())
            return original(updater, *args, **kwargs)
        with patch.object(self.store, 'transact_active', side_effect=concurrent_rebind):
            with self.assertRaises(InstanceModelBindingError):
                self.instance.save('one', self.payload)
        self.assertEqual(len(expected), 1, 'The race must occur AFTER preflight validation')
        self.assertEqual(self.store.get_active_copy(), expected[0])

    def test_scoped_scan_keeps_other_directories_and_first_scan_is_available(self):
        first = self.catalog.get_catalog('new-engine')
        self.assertEqual(first['available_folders'], ['/Game'])
        self.catalog.create_scan_request({'ue_project_id':'new-engine', 'folder_path':'/Game'})
        request = self.catalog.create_scan_request({**self.payload, 'folder_path':'/Game/Other'})
        result = self.catalog.replace_catalog({'ue_project_id':'ue-qa', 'roots':['/Game/Other'],
            'scan_request_id':request['request_id'], 'assets':[
                {'object_path':'/Game/Other/SM_B.SM_B', 'asset_kind':'StaticMesh'}]})
        self.assertEqual(len(result['assets']), 4)
        self.assertIn('/Game/Models', result['roots'])

    def test_selection_does_not_copy_public_catalog(self):
        with patch.object(self.catalog, 'get_catalog', side_effect=AssertionError('full copy')):
            self.catalog.validate_selection(self.payload)
            self.instance.save('one', self.payload)

    def test_replaced_catalog_invalidates_selection(self):
        updated = copy.deepcopy(self.upload)
        updated["assets"].pop()
        self.catalog.replace_catalog(updated)
        self.assertRejectedWithoutWrite(self.payload)

    def test_scan_checks_current_project_before_replacing_request(self):
        payload = {**self.payload, "folder_path": "/Game/Models"}
        request = self.catalog.create_scan_request(payload)
        with self.assertRaises(AssetCatalogError):
            self.catalog.create_scan_request({**payload, "expected_project_id": "other"})
        self.assertEqual(self.catalog.get_scan_request()["request_id"], request["request_id"])

    def test_type_http_route_uses_catalog_validation_and_readable_errors(self):
        # Load the actual route without app.py's production-store startup side effects.
        source = Path(__file__).parents[1] / "app.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "bind_asset")
        app = Flask(__name__)
        scope = {
            "app": app, "jsonify": jsonify, "request": request,
            "_object_types": self.store.get_object_types(),
            "ue_asset_catalog_service": self.catalog,
            "_refresh_object_types_after_overlay_save": lambda: None,
        }
        exec(compile(ast.Module(body=[route], type_ignores=[]), str(source), "exec"), scope)
        client = app.test_client()
        response = client.post("/api/v2/assets/bind", json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["valid"])
        before = self.store.get_active_copy()
        response = client.post("/api/v2/assets/bind", json={**self.payload, "ue_project_id": "wrong"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("UE 工程", response.json["message"])
        self.assertEqual(self.store.get_active_copy(), before)


if __name__ == "__main__":
    unittest.main()
