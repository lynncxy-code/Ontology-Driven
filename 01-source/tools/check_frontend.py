"""BUG-09: validate actual staged frontend bytes before building a bundle.

Also usable against an extracted image's frontend directory. No network access.
"""
import argparse
import base64
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

REQUIRED = ('ontology.html', 'instance.html', 'presentation_library.html', 'nexus.html')


class ResourceCheck(HTMLParser):
    def __init__(self, root, page):
        super().__init__()
        self.root, self.page, self.errors = root.resolve(), page, []
        self.resources = set()
        self.imports = {}
        self.in_importmap = False
        self.inline_tag = None
        self.inline_js, self.inline_css = [], []

    def handle_data(self, data):
        if self.in_importmap:
            try:
                self.imports.update(json.loads(data).get('imports', {}))
            except ValueError:
                self.fail('invalid import map')
        elif self.inline_tag == 'script':
            self.inline_js.append(data)
        elif self.inline_tag == 'style':
            self.inline_css.append(data)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_importmap = False
        if tag == self.inline_tag:
            self.inline_tag = None

    def fail(self, message):
        self.errors.append(f'{self.page.name}:{self.getpos()[0]}: {message}')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.in_importmap = tag == 'script' and attrs.get('type') == 'importmap'
        if tag == 'style' or tag == 'script' and not attrs.get('src'):
            self.inline_tag = tag
        if tag == 'iframe':
            # Redundant fullscreen is harmless, unlike an unreviewed trust boundary.
            trusted = (self.page.name in ('nexus.html', 'nexus48.html') and attrs.get('data-ontotwin-trust') == 'same-origin-app'
                       and (attrs.get('src') or '').startswith('/') and not attrs.get('src', '').startswith('//'))
            trusted = trusted or (self.page.name == 'instance.html'
                                 and attrs.get('data-ontotwin-trust') == 'configured-runtime-stream'
                                 and attrs.get(':src') == 'runtimeStreamSrc')
            if 'sandbox' not in attrs and not trusted:
                self.fail('iframe requires sandbox or reviewed application trust policy')
            sandbox = (attrs.get('sandbox') or '').split()
            if 'allow-scripts' in sandbox and 'allow-same-origin' in sandbox:
                self.fail('combined allow-scripts/allow-same-origin sandbox needs review')
        url = None
        if tag == 'script':
            url = attrs.get('src')
        elif tag == 'link' and {'stylesheet', 'preload', 'modulepreload'} & set((attrs.get('rel') or '').lower().split()):
            url = attrs.get('href')
        if not url:
            return
        parsed = urlsplit(url)
        if parsed.scheme in ('data', 'blob'):
            return
        if parsed.scheme or parsed.netloc:
            self.fail(f'non-local script/stylesheet: {url}')
            return
        resource = unquote(parsed.path)
        target = ((self.root / resource.lstrip('/')) if resource.startswith('/')
                  else (self.page.parent / resource)).resolve()
        if not target.is_relative_to(self.root):
            self.fail(f'resource escapes frontend root: {url}')
            return
        if not target.is_file():
            self.fail(f'missing resource: {url}')
            return
        self.resources.add(target)
        integrity = attrs.get('integrity')
        if integrity:
            hashes = {}
            for token in integrity.split():
                algo, sep, expected = token.partition('-')
                if sep and algo in ('sha256', 'sha384', 'sha512'):
                    hashes.setdefault(algo, []).append(expected)
            if not hashes:
                self.fail(f'unsupported integrity: {url}')
            else:
                # Browsers use the strongest supported algorithm, not any match.
                algo = max(hashes, key=lambda value: int(value[3:]))
                actual = base64.b64encode(hashlib.new(algo, target.read_bytes()).digest()).decode()
                if actual not in hashes[algo]:
                    self.fail(f'integrity mismatch: {url}')


def nested_resources(root, files, imports=None, inline=None):
    """Follow CSS dependencies and literal ES imports (including dynamic imports).

    Computed runtime URLs require browser acceptance and are not inferred here.
    """
    pending, seen, errors = list(files), set(), []
    while pending:
        source = pending.pop()
        supplied = (inline or {}).get(source)
        if source in seen or not supplied and source.suffix not in ('.js', '.mjs', '.css'):
            continue
        seen.add(source)
        kind, text = supplied or (source.suffix, source.read_text(encoding='utf-8-sig'))
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        if kind == '.css':
            urls = re.findall(r'@import\s+[\"\']([^\"\']+)', text, flags=re.I)
            urls += re.findall(r'url\(\s*[\"\']?([^\"\')\s]+)', text, flags=re.I)
        else:
            urls = re.findall(r'\bimport\s*\(\s*[\"\']([^\"\']+)[\"\']\s*\)', text)
            urls += re.findall(r'\b(?:import|export)\s+(?:[^;\n]*?\bfrom\s*)?[\"\']([^\"\']+)[\"\']', text)
        for url in urls:
            if not url.startswith(('.', '/', 'data:', 'blob:')) and not urlsplit(url).scheme:
                mapping = imports or {}
                key = next((key for key in sorted(mapping, key=len, reverse=True)
                            if url == key or key.endswith('/') and url.startswith(key)), None)
                if key is not None:
                    url = mapping[key] + url[len(key):]
            parsed = urlsplit(url)
            if parsed.scheme in ('data', 'blob') or url.startswith('#'):
                continue
            if parsed.scheme or parsed.netloc:
                errors.append(f'{source.name}: non-local nested resource: {url}')
                continue
            target = ((root / parsed.path.lstrip('/')) if parsed.path.startswith('/') else
                      (source.parent / unquote(parsed.path))).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f'{source.name}: missing resource: {url}')
            else:
                pending.append(target)
    return errors


def validate(root):
    root = Path(root).resolve()
    errors = [f'missing required page: {name}' for name in REQUIRED if not (root / name).is_file()]
    resources = set()
    for page in sorted(root.rglob('*.html')):
        check = ResourceCheck(root, page)
        check.feed(page.read_text(encoding='utf-8-sig'))
        errors.extend(check.errors)
        resources.update(check.resources)
        errors.extend(nested_resources(root, check.resources, check.imports))
        for kind, fragments in (('.js', check.inline_js), ('.css', check.inline_css)):
            if fragments:
                errors.extend(nested_resources(root, [page], check.imports,
                                               {page: (kind, '\n'.join(fragments))}))
    # Regression gate for the cross-page utilities lost in the original CDN
    # migration. The stylesheet itself is generated from ALL HTML/JS sources.
    tailwind = root / 'vendor/tailwind-3.4.17.min.css'
    if tailwind in resources:
        css = tailwind.read_text(encoding='utf-8')
        for name in ('sr-only', 'min-h-screen', 'overflow-auto', 'max-w-6xl', 'mx-4', 'space-y-5'):
            if not re.search(r'\.' + re.escape(name) + r'(?=[\s:{>~+])', css):
                errors.append(f'Tailwind coverage missing: {name}')
    if errors:
        raise ValueError('Frontend release check failed:\n' + '\n'.join(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frontend', type=Path)
    args = parser.parse_args()
    validate(args.frontend)
    print(f'PASS: frontend resources and iframe declarations: {args.frontend.resolve()}')
