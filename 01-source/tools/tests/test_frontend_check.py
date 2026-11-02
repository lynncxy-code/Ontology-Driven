import base64
import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest

validate = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'check_frontend.py'))['validate']


class FrontendCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('ontology', 'instance', 'nexus', 'presentation_library'):
            (self.root / (name + '.html')).write_text('<html></html>', encoding='utf-8')

    def page(self, html):
        (self.root / 'ontology.html').write_text(html, encoding='utf-8')

    def test_local_resource_and_integrity(self):
        data = b'window.test = true;\n'
        (self.root / 'app.js').write_bytes(data)
        digest = base64.b64encode(hashlib.sha384(data).digest()).decode()
        self.page(f'<script src="/app.js?v=1" integrity="sha384-{digest}"></script>')
        validate(self.root)
        (self.root / 'app.js').write_bytes(data + b' ')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            validate(self.root)

    def test_cdn_regression(self):
        for url in ('https://cdn.tailwindcss.com', '//cdn.jsdelivr.net/npm/jsencrypt'):
            with self.subTest(url=url):
                self.page(f'<script src="{url}"></script>')
                with self.assertRaisesRegex(ValueError, 'non-local'):
                    validate(self.root)

    def test_missing_css(self):
        self.page('<link rel="stylesheet" href="/vendor/missing.css">')
        with self.assertRaisesRegex(ValueError, 'missing resource'):
            validate(self.root)

    def test_missing_page(self):
        (self.root / 'nexus.html').unlink()
        with self.assertRaisesRegex(ValueError, 'missing required page'):
            validate(self.root)

    def test_iframe(self):
        self.page('<iframe sandbox="allow-scripts" allow="fullscreen; clipboard-read" allowfullscreen></iframe>')
        validate(self.root)
        for attrs in ('allow="fullscreen"',
                      'sandbox="allow-same-origin allow-scripts"'):
            self.page(f'<iframe {attrs}></iframe>')
            with self.assertRaises(ValueError):
                validate(self.root)

    def test_nested_pages_preloads_and_css_imports(self):
        nested = self.root / 'ue_hud'
        nested.mkdir()
        (nested / 'view.html').write_text('<link rel="PreLoad" href="missing.css">')
        with self.assertRaisesRegex(ValueError, 'missing resource'):
            validate(self.root)
        (nested / 'missing.css').write_text('@import "next.css";')
        with self.assertRaisesRegex(ValueError, 'next.css'):
            validate(self.root)
        (nested / 'next.css').write_text('a {background:url(data:image/png;base64,AAAA)}')
        validate(self.root)

    def test_dynamic_import_and_inline_resources(self):
        self.page('<script src="a.js"></script><link rel="STYLESHEET" href="blob:generated">')
        (self.root / 'a.js').write_text('import("./missing.js")')
        with self.assertRaisesRegex(ValueError, 'missing.js'):
            validate(self.root)
        (self.root / 'missing.js').write_text('export const ok=1;')
        validate(self.root)

    def test_imports_inside_inline_script_and_style_are_checked(self):
        self.page('<script type="module">import("./inside.js")</script><style>@import "inside.css";</style>')
        with self.assertRaisesRegex(ValueError, 'inside.js'):
            validate(self.root)
        (self.root / 'inside.js').write_text('export const ok=1;')
        with self.assertRaisesRegex(ValueError, 'inside.css'):
            validate(self.root)
        (self.root / 'inside.css').write_text('a {color: black}')
        validate(self.root)


if __name__ == '__main__':
    unittest.main()
