import os
import sys
import unittest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from presentation_catalog import catalog_payload, list_resources, validate_selection


class PresentationCatalogTests(unittest.TestCase):
    def test_mock_catalog_has_each_user_channel(self):
        payload = catalog_payload()
        self.assertGreaterEqual(payload["resource_count"], 9)
        self.assertTrue({"animation", "fx", "visual"}.issubset({r["channel"] for r in payload["resources"]}))
        self.assertEqual({"ontotwin_common", "project"}, {s["id"] for s in payload["sources"]})

    def test_catalog_filters_source_channel_and_type(self):
        resources = list_resources(source="ontotwin_common", channel="animation", object_type="AGV")
        self.assertTrue(resources)
        self.assertTrue(all(r["source"] == "ontotwin_common" and r["channel"] == "animation" for r in resources))
        self.assertEqual([], list_resources(source="project"))

    def test_selection_uses_stable_resource_identity(self):
        ok, error, resource = validate_selection({"resource_id": "ot.industrial.alarm_flash", "revision": 1}, channel="fx")
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.assertEqual("fx", resource["channel"])
        ok, error, _ = validate_selection({"resource_id": "ot.industrial.alarm_flash"}, channel="animation")
        self.assertFalse(ok)
        self.assertIn("channel", error)


if __name__ == "__main__":
    unittest.main()
