"""Offline checks for files previously omitted from main; run on a clean checkout."""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


class ReleaseAssetTests(unittest.TestCase):
    def test_nexus_branding_and_logo_ship_together(self):
        page = (FRONTEND / "nexus.html").read_text(encoding="utf-8")
        self.assertIn("<title>OntoTwin Nexus | 本体驱动工业数字孪生平台</title>", page)
        self.assertIn('rel="icon"', page)
        self.assertGreaterEqual(page.count("/assets/ontotwin-logo.svg"), 2)
        logo = ET.parse(FRONTEND / "assets/ontotwin-logo.svg").getroot()
        self.assertTrue(logo.tag.endswith("svg"))

    def test_gltf_loader_relative_dependencies_exist(self):
        pending = [FRONTEND / "vendor/three/addons/loaders/GLTFLoader.js"]
        checked = set()
        while pending:
            source = pending.pop().resolve()
            if source in checked:
                continue
            checked.add(source)
            self.assertTrue(source.is_file(), f"Missing imported module: {source}")
            text = source.read_text(encoding="utf-8")
            for relative in re.findall(r"(?:from\s*|import\s*)['\"](\.[^'\"]+)['\"]", text):
                pending.append(source.parent / relative)
        self.assertIn((FRONTEND / "vendor/three/addons/utils/BufferGeometryUtils.js").resolve(), checked)


if __name__ == "__main__":
    unittest.main()
