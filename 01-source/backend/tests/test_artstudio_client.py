import os
import sys
import types
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace()

import artstudio_client


class ArtStudioClientTests(unittest.TestCase):
    def test_only_self_contained_glb_is_bindable(self):
        gltf_only = {
            "files": [{"ext": "gltf", "download_url": "https://example.test/model.gltf"}]
        }
        self.assertIsNone(artstudio_client.pick_glb_file(gltf_only))

        glb = {
            "files": [{"ext": "glb", "download_url": "https://example.test/model.glb"}]
        }
        self.assertEqual("glb", artstudio_client.pick_glb_file(glb)["ext"])


if __name__ == "__main__":
    unittest.main()
