import json
import os
import sys
import tempfile
import threading
import unittest
import uuid


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from dataset_activation import (  # noqa: E402
    activate_or_create_project,
    project_dataset_to_object_types,
)
from project_store import ProjectStore  # noqa: E402

try:
    from db import pg as pg_db  # noqa: E402
    from project_store_pg import ProjectStorePG  # noqa: E402
except (ImportError, ModuleNotFoundError):
    pg_db = None
    ProjectStorePG = None


def dataset(dataset_id, name, rid="shared.machine"):
    return {
        "id": dataset_id,
        "name": name,
        "graph_data": {
            "nodes": [{
                "rid": rid,
                "name": f"{name} machine",
                "category": "Equipment",
                "description": f"{name} description",
                "properties": [{"name": "status", "type": "string"}],
                "injected_interfaces": ["I3D_Overlay"],
            }],
            "links": [],
            "categories": [{"name": "Equipment"}],
        },
    }


class DatasetActivationTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.projects_dir = os.path.join(self.temp.name, "projects")
        self.active_file = os.path.join(self.temp.name, "active.json")
        self.store = ProjectStore(self.projects_dir, self.active_file)

    def tearDown(self):
        self.temp.cleanup()

    def test_projection_preserves_capability_extensions_for_same_project(self):
        overlay = {
            "revision": 3,
            "values": {"template_id": "title_body", "slots": {"title": "A"}},
        }
        existing = {
            "shared.machine": {
                "rid": "shared.machine",
                "name": "old name",
                "interface_configs": {"I3D_Overlay": overlay},
                "future_extension": {"revision": 7},
            }
        }

        projected = project_dataset_to_object_types(
            dataset("a", "Project A"), existing_types=existing
        )
        rec = projected["shared.machine"]

        self.assertEqual("Project A machine", rec["name"])
        self.assertEqual(overlay, rec["interface_configs"]["I3D_Overlay"])
        self.assertEqual({"revision": 7}, rec["future_extension"])

        rec["interface_configs"]["I3D_Overlay"]["revision"] = 99
        self.assertEqual(
            3,
            existing["shared.machine"]["interface_configs"]["I3D_Overlay"]["revision"],
        )

    def test_existing_project_switch_a_b_a_is_read_only(self):
        dataset_a = dataset("project_a", "Project A")
        dataset_b = dataset("project_b", "Project B")
        type_a = project_dataset_to_object_types(dataset_a)
        type_a["shared.machine"]["interface_configs"] = {
            "I3D_Overlay": {
                "revision": 3,
                "values": {"template_id": "title_body"},
            }
        }
        self.store.create_project(
            "Project A", type_a, project_id="project_a", dataset=dataset_a
        )

        def add_instance_override(project):
            project["instances"]["machine_01"] = {
                "id": "machine_01",
                "object_type_rid": "shared.machine",
                "render_config": {
                    "interface_overrides": {
                        "I3D_Overlay": {
                            "revision": 1,
                            "values": {"slots": {"title": "Instance A"}},
                        }
                    }
                },
            }

        self.store.transact_active(add_instance_override)
        project_a_path = os.path.join(self.projects_dir, "project_a.json")
        with open(project_a_path, "rb") as handle:
            before = handle.read()

        self.store.create_project(
            "Project B",
            project_dataset_to_object_types(dataset_b),
            project_id="project_b",
            dataset=dataset_b,
        )

        def must_not_rebuild(_dataset):
            self.fail("an existing project must be loaded, not rebuilt from graph nodes")

        for target in (dataset_a, dataset_b, dataset_a):
            object_types, created = activate_or_create_project(
                self.store, target, must_not_rebuild
            )
            self.assertFalse(created)
            self.assertIn("shared.machine", object_types)

        project = self.store.get_active_copy()
        self.assertEqual("project_a", project["id"])
        self.assertEqual(
            3,
            project["object_types"]["shared.machine"]["interface_configs"]
            ["I3D_Overlay"]["revision"],
        )
        self.assertEqual(
            1,
            project["instances"]["machine_01"]["render_config"]
            ["interface_overrides"]["I3D_Overlay"]["revision"],
        )
        with open(project_a_path, "rb") as handle:
            self.assertEqual(before, handle.read())

    def test_catalog_only_dataset_is_created_without_cross_project_extensions(self):
        source = dataset("new_project", "New Project")
        object_types, created = activate_or_create_project(
            self.store,
            source,
            lambda value: project_dataset_to_object_types(value, existing_types={}),
        )

        self.assertTrue(created)
        self.assertEqual("new_project", self.store.get_active_id())
        self.assertNotIn("interface_configs", object_types["shared.machine"])
        with open(
            os.path.join(self.projects_dir, "new_project.json"),
            encoding="utf-8",
        ) as handle:
            self.assertEqual("new_project", json.load(handle)["id"])


class DatasetActivationPostgresTestCase(unittest.TestCase):
    """Exercise the A→B→A contract against the deployment storage backend."""

    @classmethod
    def setUpClass(cls):
        if ProjectStorePG is None or pg_db is None or not pg_db.ping():
            raise unittest.SkipTest("PostgreSQL is unavailable")

    def setUp(self):
        suffix = uuid.uuid4().hex
        self.project_a = f"switch_a_{suffix}"
        self.project_b = f"switch_b_{suffix}"
        with pg_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT v FROM app_singleton WHERE k='active_project_id'")
                row = cur.fetchone()
                self.original_active_id = row[0] if row else None

        self.store = ProjectStorePG.__new__(ProjectStorePG)
        self.store._lock = threading.RLock()
        self.store._active_id = None
        self.store._current = None
        self.store._dirty = False

    def tearDown(self):
        with pg_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM project WHERE id = ANY(%s)",
                    ([self.project_a, self.project_b],),
                )
                cur.execute(
                    """INSERT INTO app_singleton (k, v)
                       VALUES ('active_project_id', %s)
                       ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v""",
                    (self.original_active_id,),
                )

    def test_existing_postgres_project_switch_preserves_type_and_instance_config(self):
        dataset_a = dataset(self.project_a, "PG Project A")
        dataset_b = dataset(self.project_b, "PG Project B")
        type_a = project_dataset_to_object_types(dataset_a)
        type_a["shared.machine"]["interface_configs"] = {
            "I3D_Overlay": {
                "revision": 3,
                "values": {"template_id": "title_body"},
            }
        }
        self.store.create_project(
            "PG Project A", type_a, project_id=self.project_a, dataset=dataset_a
        )

        def add_instance_override(project):
            project["instances"]["machine_01"] = {
                "id": "machine_01",
                "object_type_rid": "shared.machine",
                "object_type_name": "PG Project A machine",
                "display_name": "Machine 01",
                "render_config": {
                    "interface_overrides": {
                        "I3D_Overlay": {
                            "revision": 1,
                            "values": {"slots": {"title": "Instance A"}},
                        }
                    }
                },
                "raw_state": {},
            }

        self.store.transact_active(add_instance_override)
        self.store.create_project(
            "PG Project B",
            project_dataset_to_object_types(dataset_b),
            project_id=self.project_b,
            dataset=dataset_b,
        )

        def must_not_rebuild(_dataset):
            self.fail("an existing PG project must not be rebuilt on activation")

        for target in (dataset_a, dataset_b, dataset_a):
            _, created = activate_or_create_project(
                self.store, target, must_not_rebuild
            )
            self.assertFalse(created)

        reloaded = self.store._read_project(self.project_a)
        self.assertEqual(
            3,
            reloaded["object_types"]["shared.machine"]["interface_configs"]
            ["I3D_Overlay"]["revision"],
        )
        self.assertEqual(
            1,
            reloaded["instances"]["machine_01"]["render_config"]
            ["interface_overrides"]["I3D_Overlay"]["revision"],
        )


if __name__ == "__main__":
    unittest.main()
