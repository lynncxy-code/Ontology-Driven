import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
import hashlib

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from dataset_package.api import register_dataset_package_routes
from dataset_package.service import DatasetPackageError, DatasetPackageService
from project_store import CURRENT_SCHEMA_VERSION, ProjectStore


def graph_dataset(project_id="source-a", name="Factory A"):
    return {
        "id": project_id,
        "name": name,
        "created_at": "2026-09-01 10:00",
        "node_count": 1,
        "link_count": 0,
        "graph_data": {
            "nodes": [{"id": "pump", "rid": "pump", "name": "泵", "category": "Machine"}],
            "links": [],
            "categories": [{"name": "Machine"}],
        },
        "bound_ue_project_id": "ue-source-a",
        "bound_ue_project_name": "UE Source A",
    }


class DatasetPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.source = ProjectStore(
            os.path.join(self.temp.name, "source-projects"),
            os.path.join(self.temp.name, "source-active.json"),
        )
        self.source.create_project(
            "Factory A",
            project_id="source-a",
            dataset=graph_dataset(),
            object_types={
                "pump": {
                    "rid": "pump",
                    "name": "泵",
                    "ue_asset_path": "/Game/Factory/BP_Pump.BP_Pump_C",
                    "injected_interfaces": ["interface.motion"],
                    "overlay_config": {"enabled": True, "template": "status-card"},
                }
            },
        )
        self.source.spawn("pump-01", "pump")

        def seed(project):
            project["components"] = {"component-01": {"id": "component-01", "frame_id": "frame-a"}}
            project["instance_roster"] = [{"instance_id": "pump-01", "object_type_rid": "pump"}]
            project["calibration"] = {"matrix": [1, 0, 0, 1], "source": "cad"}
            project["spatial_profile"] = {"floor_table": [{"floor_id": "floor-a", "floor": 1}]}
            project["frames"] = [{
                "frame_id": "frame-a",
                "name": "一层底图",
                "source_path": "C:\\Factory\\floor-a.png",
            }]
            project["zones"] = {
                "zone-a": {"zone_id": "zone-a", "name": "A 区", "level": "area"}
            }
            project["instances"]["pump-01"].update({
                "zone_id": "zone-a",
                "last_seen": 123456,
                "status": "online",
                "raw_state": {"temperature": 42, "access_token": "must-not-export"},
            })
            project["scene_interactions"] = {
                "revision": 3,
                "roaming": {"enabled": True, "route": {"route_id": "route-a"}},
                "routes": [{"id": "route-a", "name": "巡检路线", "waypoints": []}],
                "narration_assets": {
                    "narration-a": {"asset_id": "narration-a", "storage_name": "narration-a.wav"}
                },
                "narration_defaults": {},
                "narration_audit": [],
            }
            project["media_policy"] = {
                "revision": 1,
                "mode": "project",
                "allowed_hosts": ["media.factory.local"],
                "http_exceptions": [],
            }
            project["web_interactions"] = {
                "schema_version": 1,
                "revision": 2,
                "published": {
                    "pages": [{"page_id": "status", "base_url": "http://localhost:5000/status"}],
                    "business_views": [],
                    "bindings": [{"binding_id": "open-status", "page_id": "status"}],
                    "web_policy": {"allowed_hosts": ["localhost"]},
                },
                "draft": {"pages": [], "business_views": [], "bindings": [], "web_policy": {}},
                "previous_published": None,
            }

        self.source.transact_active(seed)
        self.exporter = DatasetPackageService(self.source)
        self.package_bytes, _, self.manifest = self.exporter.export_package("source-a")

        self.target = ProjectStore(
            os.path.join(self.temp.name, "target-projects"),
            os.path.join(self.temp.name, "target-active.json"),
        )
        self.target.create_project(
            "Factory A",
            project_id="target-active",
            dataset=graph_dataset("target-active", "Factory A"),
        )
        self.imported_catalog = []
        self.importer = DatasetPackageService(
            self.target,
            dataset_names=lambda: ["Factory A"] + [item["name"] for item in self.imported_catalog],
            on_import=lambda dataset: self.imported_catalog.append(dataset),
        )

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def rebuild_package(package_bytes, mutate):
        with zipfile.ZipFile(io.BytesIO(package_bytes), "r") as archive:
            manifest = json.loads(archive.read("manifest.json"))
            project = json.loads(archive.read("project.json"))
        mutate(manifest, project)
        payload = json.dumps(
            project, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        manifest["payload"] = {
            "file": "project.json",
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        target = io.BytesIO()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            manifest_bytes = json.dumps(
                manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            integrity = {
                "kind": "ontotwin.dataset-package",
                "format_version": 1,
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
            }
            archive.writestr(
                "integrity.json",
                json.dumps(integrity, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
            archive.writestr(
                "manifest.json",
                manifest_bytes,
            )
            archive.writestr("project.json", payload)
        return target.getvalue()

    def test_preflight_reports_complete_project_and_portability_risks(self):
        report = self.importer.preflight(self.package_bytes)
        self.assertTrue(report["can_import"], report["blockers"])
        self.assertEqual("Factory A（副本）", report["suggested_name"])
        self.assertEqual(1, report["summary"]["types"])
        self.assertEqual(1, report["summary"]["instances"])
        self.assertEqual(1, report["summary"]["frames"])
        self.assertEqual(1, report["summary"]["zones"])
        self.assertEqual(1, report["summary"]["routes"])
        self.assertEqual(1, report["summary"]["web_pages"])
        self.assertGreaterEqual(report["resource_summary"]["local_paths"], 1)
        self.assertGreaterEqual(report["resource_summary"]["internal_urls"], 1)
        self.assertEqual("ue-source-a", report["source"]["ue_project"]["project_id"])
        self.assertIn("interface.motion", report["capability_dependencies"])

    def test_import_preserves_business_config_resets_runtime_and_stays_inactive(self):
        result = self.importer.import_package(self.package_bytes, "Factory A（副本）")
        self.assertFalse(result["active"])
        self.assertFalse(result["bound"])
        self.assertEqual("target-active", self.target.get_active_id())
        self.assertNotEqual("source-a", result["project_id"])

        imported = self.target.read_project(result["project_id"])
        self.assertEqual("", imported["dataset"]["bound_ue_project_id"])
        self.assertEqual("source-a", imported["dataset"]["migration_source"]["source_dataset_id"])
        self.assertEqual("ue-source-a", imported["dataset"]["migration_source"]["source_ue_project"]["project_id"])
        self.assertEqual("frame-a", imported["frames"][0]["frame_id"])
        self.assertIn("zone-a", imported["zones"])
        self.assertEqual("route-a", imported["scene_interactions"]["routes"][0]["id"])
        self.assertEqual("status", imported["web_interactions"]["published"]["pages"][0]["page_id"])
        instance = imported["instances"]["pump-01"]
        self.assertEqual("offline", instance["status"])
        self.assertNotIn("last_seen", instance)
        self.assertEqual(42, instance["raw_state"]["temperature"])
        self.assertNotIn("access_token", instance["raw_state"])

        source = self.source.read_project("source-a")
        self.assertEqual("online", source["instances"]["pump-01"]["status"])
        self.assertEqual("ue-source-a", source["dataset"]["bound_ue_project_id"])

    def test_integrity_failure_is_blocked_before_write(self):
        with zipfile.ZipFile(io.BytesIO(self.package_bytes), "r") as archive:
            integrity_bytes = archive.read("integrity.json")
            manifest_bytes = archive.read("manifest.json")
            project = bytearray(archive.read("project.json"))
        project[-2] = ord(" ")
        target = io.BytesIO()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("integrity.json", integrity_bytes)
            archive.writestr("manifest.json", manifest_bytes)
            archive.writestr("project.json", bytes(project))
        with self.assertRaises(DatasetPackageError) as caught:
            self.importer.preflight(target.getvalue())
        self.assertEqual("package_integrity_failed", caught.exception.code)
        self.assertEqual(["target-active"], [item["id"] for item in self.target.list_projects()])

    def test_newer_schema_and_broken_relationship_are_preflight_blockers(self):
        newer = self.rebuild_package(
            self.package_bytes,
            lambda manifest, project: project.update({"schema_version": CURRENT_SCHEMA_VERSION + 1}),
        )
        newer_report = self.importer.preflight(newer)
        self.assertFalse(newer_report["can_import"])
        self.assertIn("project_schema_newer", {item["code"] for item in newer_report["blockers"]})

        def break_type(_manifest, project):
            project["instances"]["pump-01"]["object_type_rid"] = "missing-type"

        broken = self.rebuild_package(self.package_bytes, break_type)
        broken_report = self.importer.preflight(broken)
        self.assertFalse(broken_report["can_import"])
        self.assertIn("instance_type_missing", {item["code"] for item in broken_report["blockers"]})

        def break_graph_link(_manifest, project):
            project["dataset"]["graph_data"]["links"] = [{"source": "pump", "target": "missing-node"}]

        broken_graph = self.rebuild_package(self.package_bytes, break_graph_link)
        graph_report = self.importer.preflight(broken_graph)
        self.assertFalse(graph_report["can_import"])
        self.assertIn("graph_link_endpoint_missing", {item["code"] for item in graph_report["blockers"]})

    def test_http_preflight_is_read_only_and_import_creates_inactive_dataset(self):
        app = Flask(__name__)
        register_dataset_package_routes(
            app,
            self.target,
            dataset_names=lambda: ["Factory A"] + [item["name"] for item in self.imported_catalog],
            on_import=lambda dataset: self.imported_catalog.append(dataset),
        )
        client = app.test_client()
        preflight = client.post(
            "/api/v2/ontology/dataset-packages/preflight",
            data={"file": (io.BytesIO(self.package_bytes), "factory.otdataset")},
            content_type="multipart/form-data",
        )
        self.assertEqual(200, preflight.status_code)
        self.assertEqual(1, len(self.target.list_projects()))

        imported = client.post(
            "/api/v2/ontology/dataset-packages/import",
            data={
                "file": (io.BytesIO(self.package_bytes), "factory.otdataset"),
                "target_name": "Factory Migrated",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(201, imported.status_code)
        self.assertEqual("target-active", self.target.get_active_id())
        self.assertEqual("Factory Migrated", imported.get_json()["dataset_name"])

    def test_http_export_download_does_not_change_active_project(self):
        app = Flask(__name__)
        register_dataset_package_routes(app, self.source)
        client = app.test_client()
        summary = client.get("/api/v2/ontology/datasets/source-a/package-summary")
        self.assertEqual(200, summary.status_code)
        self.assertEqual(1, summary.get_json()["summary"]["instances"])
        download = client.get("/api/v2/ontology/datasets/source-a/package")
        self.assertEqual(200, download.status_code)
        self.assertEqual("application/vnd.ontotwin.dataset-package", download.mimetype)
        self.assertIn("attachment", download.headers.get("Content-Disposition", ""))
        self.assertEqual("source-a", self.source.get_active_id())
        download.close()

    def test_never_activated_graph_dataset_can_be_exported_without_materializing(self):
        never_active = graph_dataset("never-active", "Never Active")
        service = DatasetPackageService(
            self.source,
            dataset_lookup=lambda dataset_id: never_active if dataset_id == "never-active" else None,
        )
        before = self.source.get_active_id()
        data, filename, manifest = service.export_package("never-active")
        self.assertTrue(data)
        self.assertTrue(filename.endswith(".otdataset"))
        self.assertEqual(1, manifest["summary"]["types"])
        self.assertEqual(before, self.source.get_active_id())
        self.assertIsNone(self.source.read_project("never-active"))

    def test_older_supported_schema_is_migrated_during_preflight(self):
        def downgrade(manifest, project):
            manifest["project_schema_version"] = 5
            project["schema_version"] = 5
            project.pop("zones", None)
            project.pop("web_interactions", None)

        older = self.rebuild_package(self.package_bytes, downgrade)
        report = self.importer.preflight(older)
        self.assertTrue(report["can_import"], report["blockers"])
        self.assertTrue(report["compatibility"]["migration_required"])
        self.assertIn("project_schema_upgraded", {item["code"] for item in report["warnings"]})

    @unittest.skipUnless(os.environ.get("ONTOTWIN_TEST_PG_URL"), "requires isolated PostgreSQL test database")
    def test_json_to_postgresql_to_json_round_trip(self):
        from db import pg
        pg.DATABASE_URL = os.environ["ONTOTWIN_TEST_PG_URL"]
        from project_store_pg import ProjectStorePG

        pg_store = ProjectStorePG()
        pg_importer = DatasetPackageService(pg_store, dataset_names=lambda: [])
        first = pg_importer.import_package(self.package_bytes, "PG Migrated")
        pg_project = pg_store.read_project(first["project_id"])
        self.assertEqual("route-a", pg_project["scene_interactions"]["routes"][0]["id"])
        self.assertEqual("status", pg_project["web_interactions"]["published"]["pages"][0]["page_id"])

        pg_exporter = DatasetPackageService(pg_store)
        pg_package, _, _ = pg_exporter.export_package(first["project_id"])
        json_target = ProjectStore(
            os.path.join(self.temp.name, "roundtrip-projects"),
            os.path.join(self.temp.name, "roundtrip-active.json"),
        )
        json_target.create_project("Keep Active", project_id="keep-active")
        second = DatasetPackageService(json_target, dataset_names=lambda: []).import_package(
            pg_package, "JSON Returned"
        )
        returned = json_target.read_project(second["project_id"])
        self.assertEqual("keep-active", json_target.get_active_id())
        self.assertEqual(set(pg_project["object_types"]), set(returned["object_types"]))
        self.assertEqual(set(pg_project["instances"]), set(returned["instances"]))
        self.assertEqual(pg_project["zones"], returned["zones"])
        self.assertEqual(pg_project["frames"], returned["frames"])
        self.assertEqual(
            pg_project["web_interactions"]["published"],
            returned["web_interactions"]["published"],
        )


if __name__ == "__main__":
    unittest.main()
