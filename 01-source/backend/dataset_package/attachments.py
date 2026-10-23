"""Project-owned attachment transport. Never fetch URLs or trust archive paths."""
import hashlib
import os
import re
from urllib.parse import urlsplit, unquote, urljoin
from pathlib import Path, PurePosixPath

from spatial_assets.storage import DEFAULT_ASSET_ROOT


def safe_relative(value):
    path = PurePosixPath(str(value))
    if not value or '\\' in str(value) or ':' in str(value) or path.is_absolute() or any(x in ('', '.', '..') for x in str(value).split('/')):
        raise ValueError('非法附件路径')
    return path.as_posix()


def project_dir(root, project_id):
    project_id = safe_relative(project_id)
    if '/' in project_id:
        raise ValueError('非法项目编号')
    root = Path(root).resolve()
    target = (root / project_id).resolve()
    if not target.is_relative_to(root):
        raise ValueError('项目目录越界')
    return target


def referenced_files(project):
    refs = set()
    for frame in project.get('frames') or []:
        for key in ('image', 'cad'):
            meta = frame.get(key) or {}
            if meta.get('storage_name'):
                refs.add('spatial_frames/' + safe_relative(meta['storage_name']))
    for meta in ((project.get('scene_interactions') or {}).get('narration_assets') or {}).values():
        if isinstance(meta, dict) and meta.get('storage_name'):
            refs.add('narration_audio/' + safe_relative(meta['storage_name']))
    return refs


def collect(project, root=DEFAULT_ASSET_ROOT):
    directory = project_dir(root, project['id'])
    refs = referenced_files(project)
    # Include project-owned images and web bundles without exporting another project.
    if directory.is_dir():
        for file in directory.rglob('*'):
            if file.is_file():
                if file.is_symlink() or not file.resolve().is_relative_to(directory):
                    raise ValueError('附件目录包含外部链接')
                refs.add(file.relative_to(directory).as_posix())
    files, missing = {}, []
    for relative in sorted(refs):
        file = directory / safe_relative(relative)
        if not file.resolve().is_relative_to(directory):
            raise ValueError('附件路径越界')
        if file.is_file():
            files['attachments/' + relative] = file.read_bytes()
        else:
            missing.append(relative)
    return files, missing


def collect_web(project, frontend_root):
    """Snapshot local public pages and statically referenced dependencies only."""
    root = Path(frontend_root).resolve()
    urls = set()
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'base_url' and isinstance(item, str):
                    parsed = urlsplit(item)
                    if not parsed.netloc or parsed.hostname in ('localhost', '127.0.0.1') and parsed.port in (None, 5000):
                        if not parsed.path.startswith('/api/'):
                            urls.add(item)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(project.get('web_interactions') or {})
    queue = [urlsplit(url).path for url in urls]
    files, missing, seen = {}, [], set()
    allowed = {'.html', '.css', '.js', '.mjs', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.gif'}
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        relative = safe_relative(unquote(path).lstrip('/'))
        file = (root / relative).resolve()
        if not file.is_relative_to(root) or file.suffix.lower() not in allowed:
            missing.append('web/' + relative)
            continue
        if not file.is_file():
            missing.append('web/' + relative)
            continue
        data = file.read_bytes()
        files['attachments/web/' + relative] = data
        if file.suffix.lower() in {'.html', '.css', '.js', '.mjs'}:
            text = data.decode('utf-8')
            # Public static resources, not APIs, dynamic expressions or remote URLs.
            candidates = re.findall(r'''(?:src|href)\s*=\s*["']([^"']+)|url\(\s*["']?([^\s)'";]+)|["'`](/[^"'`\s?]+\.(?:html|css|js|png|svg|woff2?))[?"'`]''', text)
            for group in candidates:
                ref = next((part for part in group if part), '')
                if ref.startswith(('#', 'data:', 'javascript:')) or urlsplit(ref).netloc:
                    continue
                resolved = urlsplit(urljoin(path, ref)).path
                if Path(resolved).suffix.lower() in allowed:
                    queue.append(resolved)
    return files, sorted(set(missing)), sorted(urls)


def remap_project(project, source_id, target_id, manifest, ue_id='', origin='http://127.0.0.1:5000'):
    from urllib.parse import urlunsplit
    web_urls = set(manifest.get('local_web_urls') or [])
    def walk(value):
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if key == 'bound_ue_project_id':
                    value[key] = ue_id
                elif isinstance(item, str) and item in web_urls:
                    parsed = urlsplit(item)
                    value[key] = origin.rstrip('/') + urlunsplit(('', '', f'/api/v2/project-assets/{target_id}/web/' + parsed.path.lstrip('/'), parsed.query, parsed.fragment))
                elif isinstance(item, str) and key in ('url', 'image_url', 'audio_url', 'base_url', 'source_url'):
                    value[key] = item.replace('/' + source_id + '/', '/' + target_id + '/')
                    if '/api/v2/project-assets/' + target_id + '/web/' in value[key]:
                        parsed = urlsplit(value[key])
                        value[key] = origin.rstrip('/') + urlunsplit(('', '', parsed.path, parsed.query, parsed.fragment))
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(project)
    if web_urls:
        def policy_walk(value):
            if isinstance(value, dict):
                if isinstance(value.get('web_policy'), dict):
                    hosts = value['web_policy'].setdefault('allowed_hosts', [])
                    hostname = urlsplit(origin).hostname
                    if hostname and hostname not in hosts:
                        hosts.append(hostname)
                for item in value.values():
                    policy_walk(item)
            elif isinstance(value, list):
                for item in value:
                    policy_walk(item)
        policy_walk(project.get('web_interactions') or {})


def relocate_web(destination, target_id, source_id=''):
    """Rewrite only references to files actually bundled, never external streams."""
    web = Path(destination) / 'web'
    if not web.exists():
        return
    relatives = [p.relative_to(web).as_posix() for p in web.rglob('*') if p.is_file()]
    for file in web.rglob('*'):
        if file.suffix in ('.html', '.css', '.js', '.mjs'):
            text = file.read_text(encoding='utf-8')
            if source_id:
                text = text.replace(f'/api/v2/project-assets/{source_id}/web/', f'/api/v2/project-assets/{target_id}/web/')
            for relative in sorted(relatives, key=len, reverse=True):
                text = re.sub(r'''(["'`(])/''' + re.escape(relative) + r'''(?=[?"'`)])''',
                              lambda m: m.group(1) + f'/api/v2/project-assets/{target_id}/web/' + relative, text)
            file.write_text(text, encoding='utf-8')


def manifest_for(files):
    return [{'file': name, 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            for name, data in sorted(files.items())]


def validate(archive, manifest):
    items = manifest.get('attachments') or []
    expected = set()
    if not isinstance(items, list):
        raise ValueError('附件清单无效')
    for item in items:
        name = safe_relative(item['file'])
        if not name.startswith('attachments/') or name in expected:
            raise ValueError('附件清单路径无效或重复')
        expected.add(name)
        data = archive.read(name)
        if len(data) != item['size_bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('附件完整性校验失败')
    if set(archive.namelist()) != expected | {'manifest.json', 'project.json', 'integrity.json'}:
        raise ValueError('数据集包含未声明附件')


def install(archive, manifest, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for item in manifest.get('attachments') or []:
        relative = safe_relative(item['file']).removeprefix('attachments/')
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError('附件目标越界')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(archive.read(item['file']))
