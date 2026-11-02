"""Offline, data-preserving OntoTwin deployment manager. Python standard library only."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import stat
import subprocess
import sys
import time
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
VOLUMES = ('db', 'graph', 'data', 'models')
REQUIRED_PLUGINS = ('OntoTwinSync', 'OntoTwinIndustrialBehavior', 'glTFRuntime', 'WebUI')
ENV_KEYS = ('INSTANCE_ID', 'PORT', 'DB_PASSWORD', 'BACKEND_IMAGE', 'DB_IMAGE',
            'NEO4J_IMAGE', 'RELEASE_ID', 'COMPOSE_FILE', 'COMPOSE_PROJECT_NAME')
TERMINAL = ('complete', 'recovered', 'prepared')


class UpdateError(RuntimeError):
    pass


def disk_path(value):
    """Use Win32 extended paths for filesystem IO, keep ordinary paths in UI/state/Docker."""
    value = str(Path(value).absolute())
    if os.name != 'nt' or value.startswith('\\\\?\\'):
        return Path(value)
    return Path('\\\\?\\UNC\\' + value[2:] if value.startswith('\\\\') else '\\\\?\\' + value)


def read_json(path):
    return json.loads(disk_path(path).read_text('utf-8-sig'))


def write_json(path, data):
    path = disk_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def digest(path):
    value = hashlib.sha256()
    with disk_path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def copy_file(source, target):
    # CopyFile2 used by copy2 on Windows fails for long character-pack asset paths.
    shutil.copyfile(disk_path(source), disk_path(target))
    shutil.copystat(disk_path(source), disk_path(target))
    return str(target)


def copy_tree(source, target, **kwargs):
    return shutil.copytree(disk_path(source), disk_path(target), copy_function=copy_file, **kwargs)


def safe_name(name):
    """ZIP/manifest paths must be portable, relative, and unambiguous on Windows."""
    p = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or p.is_absolute()
            or any(x in ('', '.', '..') or x.rstrip(' .') != x for x in name.split('/'))
            or any(x.lower().split('.')[0] in {'con', 'prn', 'aux', 'nul',
                   *(f'com{i}' for i in range(10)), *(f'lpt{i}' for i in range(10))} for x in p.parts)):
        raise UpdateError(f'包内路径不安全：{name}')
    if any(x.lower() in ('.runtime', '.env', '__pycache__') for x in p.parts):
        raise UpdateError(f'更新包不能包含运行数据：{name}')
    return p


def no_links(path):
    path = disk_path(path)
    for item in (path, *path.parents):
        if item.exists() and (item.is_symlink() or getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise UpdateError(f'暂不更新共享链接目录，请先建立独立副本：{item}')


def files(root):
    root = disk_path(root)
    no_links(root)
    result = {}
    for p in root.rglob('*'):
        no_links(p)
        if p.is_file():
            result[p.relative_to(root).as_posix()] = p
    return result


def command(args, *, input=None, timeout=180, check=True):
    env = os.environ.copy()
    for key in ENV_KEYS:
        env.pop(key, None)
    if Path(str(args[0])).name.lower() == 'powershell.exe':
        env.pop('PSModulePath', None)  # Do not inject PowerShell 7 modules into Windows PowerShell 5.
    result = subprocess.run(list(map(str, args)), input=input, capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout,
                            env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if check and result.returncode:
        # Do not echo arguments, compose config, or environment credentials.
        raise UpdateError((result.stderr or result.stdout or '命令执行失败')[-2500:])
    return result.stdout.strip() if check else result


def validate_manifest(manifest):
    release = manifest.get('release_id', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{1,110}', release):
        raise UpdateError('无效的发布编号')
    if manifest.get('contains_customer_data') is not False or manifest.get('contains_ue_project') is not False:
        raise UpdateError('请选择不含客户数据和 UE 工程的完整接入包')
    if manifest.get('ue_version') != '5.6':
        raise UpdateError('当前更新器只支持 UE 5.6 接入包')
    if not re.fullmatch('[a-f0-9]{40}', manifest.get('source_commit', '')):
        raise UpdateError('缺少可追溯的源码提交')
    for component in ('backend', 'db', 'neo4j'):
        if not re.fullmatch('sha256:[a-f0-9]{64}', manifest.get('images', {}).get(component, {}).get('id', '')):
            raise UpdateError(f'缺少镜像身份：{component}')
    for name in manifest.get('plugins', {}):
        if not re.fullmatch('[A-Za-z0-9_]+', name):
            raise UpdateError('插件名称无效')
    if not set(REQUIRED_PLUGINS) <= manifest.get('plugins', {}).keys():
        raise UpdateError('接入包缺少必要插件')


def verify_directory(root):
    root = Path(root)
    checks = read_json(root / 'SHA256SUMS.json')
    manifest = read_json(root / 'manifest.json')
    validate_manifest(manifest)
    if 'manifest.json' not in checks or 'Runtime/images.tar' not in checks:
        raise UpdateError('包校验清单不完整')
    for name, value in checks.items():
        safe_name(name)
        p = root.joinpath(*PurePosixPath(name).parts)
        no_links(p)
        if not disk_path(p).is_file() or digest(p) != value:
            raise UpdateError(f'文件校验失败：{name}')
    if checks['Runtime/images.tar'] != manifest['images_archive_sha256']:
        raise UpdateError('镜像包身份与清单不一致')
    return manifest, checks


class Manager:
    def __init__(self, home, log=print):
        self.home = Path(home).absolute()
        no_links(self.home)
        if self.home == Path(self.home.anchor) or self.home == Path.home():
            raise UpdateError('请选择专用的空环境文件夹，不能选择磁盘根目录或用户目录')
        self.home.mkdir(parents=True, exist_ok=True)
        marker = self.home / '.ontotwin-environment'
        if not marker.exists():
            if any(self.home.iterdir()):
                raise UpdateError('此目录已有其他内容；请选择空文件夹，或已经由部署管理器建立的环境')
            marker.write_text('OntoTwin deployment environment format 1\n', encoding='utf-8')
        self.log = log
        self.state_file = self.home / 'environment.json'
        self.journal_file = self.home / 'transaction.json'

    @contextlib.contextmanager
    def locked(self):
        # OS releases this lock if the process crashes; no unsafe stale-PID removal.
        lock = (self.home / 'update.lock').open('a+b')
        if lock.tell() == 0:
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock.close()
            raise UpdateError('此环境正在由另一个部署管理窗口处理')
        try:
            yield
        finally:
            lock.close()

    def state(self):
        if not self.state_file.exists():
            raise UpdateError('请先接管已有安装目录')
        state = read_json(self.state_file)
        if not re.fullmatch('ontotwin-[a-f0-9]{12}', state.get('instance_id', '')):
            raise UpdateError('环境身份无效')
        if not 1 <= int(state['port']) <= 65535:
            raise UpdateError('端口无效')
        return state

    def protect(self):
        if os.name == 'nt':
            command(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                     HERE / 'Protect-Environment.ps1', '-EnvironmentPath', self.home], timeout=30)
        else:
            self.home.chmod(0o700)

    def release(self, state=None):
        release = (state or self.state())['release']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{1,110}', release):
            raise UpdateError('发布编号无效')
        return self.home / 'releases' / release

    def pending(self):
        if self.journal_file.exists():
            item = read_json(self.journal_file)
            if item['stage'] not in TERMINAL:
                return item
        return None

    def assert_ready(self):
        if self.pending():
            raise UpdateError('上次更新尚未完成，请先点击“恢复上次更新”')

    def stage(self, package):
        """Validate every byte before accepting ZIP. Never execute scripts from imported ZIP."""
        source = Path(package).absolute()
        no_links(source)
        self.log('正在核验接入包；大包需要几分钟……')
        temporary = self.home / 'staging' / uuid.uuid4().hex
        temporary.mkdir(parents=True)
        if source.is_dir():
            manifest, checks = verify_directory(source)
            existing_release = self.home / 'releases' / manifest['release_id']
            if existing_release.exists():
                _, existing_checks = verify_directory(existing_release)
                if existing_checks != checks:
                    raise UpdateError('同一发布编号的内容不同，拒绝覆盖')
                self.log(f"已核验并复用缓存：{manifest['package_version']}")
                return manifest['release_id']
            size = sum(disk_path(source / name).stat().st_size for name in checks)
            if shutil.disk_usage(self.home).free < size + 1024 ** 3:
                raise UpdateError('空间不足，至少需要包解压大小再加 1 GB')
            for name in (*checks, 'SHA256SUMS.json'):
                target = temporary / name
                disk_path(target.parent).mkdir(parents=True, exist_ok=True)
                copy_file(source / name, target)
        else:
            with zipfile.ZipFile(source) as archive:
                entries = {}
                for entry in archive.infolist():
                    name = entry.filename.rstrip('/')
                    safe_name(name)
                    key = name.casefold()
                    if key in entries or stat.S_ISLNK(entry.external_attr >> 16):
                        raise UpdateError(f'包内路径重复或包含链接：{name}')
                    entries[key] = entry
                checks = json.loads(archive.read('SHA256SUMS.json'))
                manifest = json.loads(archive.read('manifest.json'))
                validate_manifest(manifest)
                actual = {e.filename for e in archive.infolist() if not e.is_dir()}
                if actual != set(checks) | {'SHA256SUMS.json'}:
                    raise UpdateError('包清单与实际文件不一致')
                size = sum(e.file_size for e in archive.infolist())
                if shutil.disk_usage(self.home).free < size + 1024 ** 3:
                    raise UpdateError('空间不足，至少需要包解压大小再加 1 GB')
                for name in actual:
                    safe_name(name)
                    target = temporary / name
                    disk_path(target.parent).mkdir(parents=True, exist_ok=True)
                    with archive.open(name) as stream, disk_path(target).open('wb') as output:
                        shutil.copyfileobj(stream, output, 4 * 1024 * 1024)
        manifest, checks = verify_directory(temporary)
        target = self.home / 'releases' / manifest['release_id']
        if target.exists():
            _, existing = verify_directory(target)
            if existing != checks:
                raise UpdateError('同一发布编号的内容不同，拒绝覆盖')
            # Leave redundant staging for explicit later cleanup, never touch installed files.
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.rename(target)
        self.log(f"已核验：{manifest['package_version']}（{manifest['source_commit'][:12]}）")
        return manifest['release_id']

    def docker(self, *args, **kwargs):
        return command(['docker', *args], **kwargs)

    def check_docker(self):
        if self.docker('info', '--format', '{{.OSType}}', timeout=20) != 'linux':
            raise UpdateError('请启动 Docker Desktop，使用 Linux containers')

    def verify_volumes(self, state):
        if set(state.get('volumes', {})) != set(VOLUMES):
            raise UpdateError('环境数据卷清单不完整')
        for name in state['volumes'].values():
            if not re.fullmatch(r'ontotwin-[a-f0-9]{12}[_a-z0-9-]+', name):
                raise UpdateError('数据卷名称无效')
            data = json.loads(self.docker('volume', 'inspect', name))[0]
            if data.get('Labels', {}).get('ontotwin.instance') != state['instance_id']:
                raise UpdateError(f'数据卷归属不匹配：{name}')

    def ensure_images(self, release):
        manifest, _ = verify_directory(release)
        for image in manifest['images'].values():
            result = self.docker('image', 'inspect', image['id'], check=False, timeout=20)
            if result.returncode:
                self.log('正在导入离线镜像……')
                self.docker('load', '-i', release / 'Runtime/images.tar', timeout=1800)
                break
        for name, image in manifest['images'].items():
            value = json.loads(self.docker('image', 'inspect', image['id']))[0]
            if value['Id'] != image['id']:
                raise UpdateError(f'镜像身份不匹配：{name}')
        return manifest

    def adopt(self, existing):
        with self.locked():
            if self.state_file.exists():
                raise UpdateError('已配置固定环境；不能用另一个安装覆盖它')
            self.check_docker()
            existing = Path(existing).absolute()
            old = read_json(existing / '.runtime/instance.json')
            settings = {}
            for line in (existing / '.runtime/.env').read_text('utf-8-sig').splitlines():
                if '=' in line:
                    key, value = line.split('=', 1); settings[key] = value
            manifest, _ = verify_directory(existing)
            expected = {'INSTANCE_ID': old['instance_id'], 'PORT': str(old['port']),
                        'RELEASE_ID': manifest['release_id'], **{k.upper() + '_IMAGE': v['tag'] for k, v in manifest['images'].items()}}
            if any(settings.get(k) != v for k, v in expected.items()) or old['source_commit'] != manifest['source_commit']:
                raise UpdateError('安装目录、运行配置与发布清单不一致，请选择实际使用的安装目录')
            if not re.fullmatch('[a-f0-9]{64}', settings.get('DB_PASSWORD', '')):
                raise UpdateError('缺少原有数据库凭据，不能重新生成')
            state = {'format': 1, 'instance_id': old['instance_id'], 'port': int(old['port']),
                     'release': manifest['release_id'], 'projects': [], 'adopted_from': str(existing),
                     'volumes': {v: old['instance_id'] + '_' + v for v in VOLUMES}, 'status': '已接管'}
            self.verify_volumes(state)
            state['release'] = self.stage(existing)
            self.protect()
            write_json(self.home / 'credentials.json', {'db_password': settings['DB_PASSWORD']})
            write_json(self.state_file, state)
            self.log('已接管原环境；原端口、数据卷、账号和绑定保持不变。以后从本窗口启动和更新。')
            return state

    def add_project(self, project):
        with self.locked():
            self.assert_ready()
            state = self.state()
            project = Path(project).absolute()
            self.check_project(project)
            if str(project).casefold() not in {p.casefold() for p in state['projects']}:
                state['projects'].append(str(project))
                write_json(self.state_file, state)
            return state

    def check_project(self, project):
        project = Path(project)
        no_links(project)
        if project.suffix.lower() != '.uproject' or read_json(project).get('EngineAssociation') != '5.6':
            raise UpdateError(f'请选择 UE 5.6 工程：{project}')
        for name in REQUIRED_PLUGINS:
            target = project.parent / 'Plugins' / name
            no_links(target)
            if not (target / (name + '.uplugin')).is_file():
                raise UpdateError(f'工程未安装完整 OntoTwin 接入插件：{name}')

    def idle(self, projects):
        if os.name != 'nt':
            raise UpdateError('UE 插件更新目前仅支持 Windows')
        command(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                 HERE / 'Check-ProjectsIdle.ps1', '-ProjectsJson', json.dumps(projects)], timeout=30)

    def compose(self, state, *args, public=True, timeout=180):
        # Use our own template, immutable image IDs and explicit existing volume names.
        template = read_json(HERE / 'compose.json')
        manifest = read_json(self.release(state) / 'manifest.json')
        password = read_json(self.home / 'credentials.json')['db_password']
        if not re.fullmatch('[a-f0-9]{64}', password):
            raise UpdateError('环境凭据无效')
        for name in ('backend', 'db', 'neo4j'):
            template['services'][name]['image'] = manifest['images'][name]['id']
        template['services']['db']['environment']['POSTGRES_PASSWORD'] = password
        template['services']['neo4j']['environment']['NEO4J_AUTH'] = 'neo4j/' + password
        backend = template['services']['backend']
        backend['environment'].update(DATABASE_URL=f'postgresql://ontotwin:{password}@db:5432/ontotwin',
                                      NEO4J_PASSWORD=password, ONTOTWIN_RELEASE_ID=state['release'])
        backend['ports'] = [f"127.0.0.1:{state['port']}:5000"] if public else []
        template['volumes'] = {key: {'external': True, 'name': value} for key, value in state['volumes'].items()}
        config = self.home / 'compose.runtime.json'
        write_json(config, template)
        return self.docker('compose', '-p', state['instance_id'], '-f', config, *args, timeout=timeout)

    def health(self, state):
        code = "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:5000/api/v4.8/health',timeout=3))))"
        for _ in range(60):
            try:
                health = json.loads(self.compose(state, 'exec', '-T', 'backend', 'python', '-c', code, public=False, timeout=10))
                if health.get('ok') and health.get('release_id') == state['release']:
                    return
            except (UpdateError, ValueError, subprocess.TimeoutExpired):
                pass
            time.sleep(2)
        raise UpdateError('后台未通过版本和健康检查')

    def audit(self, state):
        # Fingerprints, not customer rows/password hashes, are persisted in diagnostics.
        query = "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
        def sql(query):
            return self.compose(state, 'exec', '-T', 'db', 'psql', '-U', 'ontotwin', '-d', 'ontotwin',
                                '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-c', query, public=False)
        result = {}
        for table in sql(query).splitlines():
            if table in ('user_session', 'audit_event', 'ue_connection'):
                continue  # Runtime sessions/heartbeats are not stable business data.
            if not re.fullmatch('[a-z_]+', table):
                raise UpdateError('数据库表名不符合当前升级协议')
            row = sql(f'SELECT count(*),md5(coalesce(string_agg(j,E\'\\n\' ORDER BY j),\'\')) FROM '
                      f'(SELECT row_to_json(t)::text AS j FROM "{table}" t) s;')
            result[table] = row
        return result

    def file_audit(self, state):
        image = read_json(self.release(state) / 'manifest.json')['images']['backend']['id']
        # Backend runtime currently uses Python 3.10, where file_digest is absent.
        script = ('import hashlib,json,pathlib\nr=pathlib.Path("/source")\nout={}\n'
                  'for p in r.rglob("*"):\n'
                  ' if p.is_file():\n'
                  '  h=hashlib.sha256()\n'
                  '  with p.open("rb") as f:\n'
                  '   for b in iter(lambda:f.read(4194304),b""): h.update(b)\n'
                  '  out[str(p.relative_to(r))]=h.hexdigest()\n'
                  'print(json.dumps(out,sort_keys=True))')
        return {key: json.loads(self.docker('run', '--rm', '--network', 'none',
                    '--mount', f'type=volume,src={state["volumes"][key]},dst=/source,readonly',
                    '--entrypoint', 'python', image, '-c', script, timeout=600)) for key in ('data', 'models')}

    def verify_preserved_files(self, before, after):
        for group, records in before.items():
            for name, checksum in records.items():
                if after.get(group, {}).get(name) != checksum:
                    raise UpdateError(f'原文件内容发生变化：{group}/{name}')

    def schema(self, manifest):
        return self.docker('run', '--rm', '--network', 'none', '--entrypoint', 'sha256sum',
                           manifest['images']['db']['id'], '/docker-entrypoint-initdb.d/schema.sql')

    def preflight(self, release):
        self.assert_ready()
        state = self.state()
        self.check_docker()
        self.verify_volumes(state)
        target = self.release({'release': release})
        old = self.ensure_images(self.release(state))
        new = self.ensure_images(target)
        if new['release_id'] == old['release_id']:
            raise UpdateError('已经是这个版本，无需重复更新')
        if old['images']['neo4j']['id'] != new['images']['neo4j']['id'] or self.schema(old) != self.schema(new):
            raise UpdateError('此包包含未经验证的数据库结构或图数据库升级；已停止，原环境未修改')
        # Pin exact PostgreSQL major version too, not just schema text.
        for item in (old, new):
            version = self.docker('run', '--rm', '--network', 'none', '--entrypoint', 'postgres', item['images']['db']['id'], '--version')
            if not re.search(r'\b16\.', version):
                raise UpdateError('当前更新器只支持 PostgreSQL 16 同结构升级')
        if not state['projects']:
            raise UpdateError('请添加使用此后台的 UE 工程，统一更新插件')
        old_checks = read_json(self.release(state) / 'SHA256SUMS.json')
        new_checks = read_json(target / 'SHA256SUMS.json')
        host_assets = 'Plugins/OntoTwinCharacterPack_Core/HostContent/'
        if {k: v for k, v in old_checks.items() if k.startswith(host_assets)} != {k: v for k, v in new_checks.items() if k.startswith(host_assets)}:
            raise UpdateError('人物库包含工程 Content 资源变更，需要单独检查同名客户资产；本次不自动覆盖')
        self.idle(state['projects'])
        plans = []
        for index, p in enumerate(state['projects']):
            project = Path(p)
            self.check_project(project)
            project_space = sum(item.stat().st_size for name in new['plugins']
                                if (project.parent / 'Plugins' / name).exists()
                                for item in files(project.parent / 'Plugins' / name).values())
            if shutil.disk_usage(project.parent).free < project_space * 2 + 512 * 1024 ** 2:
                raise UpdateError(f'工程所在磁盘空间不足：{project}')
            for name in new['plugins']:
                installed = project.parent / 'Plugins' / name
                if not installed.exists():
                    continue  # Optional character pack stays optional.
                owned = {key.split('/', 2)[2]: value for key, value in old_checks.items() if key.startswith(f'Plugins/{name}/')}
                if not owned:
                    raise UpdateError(f'无法确认现有插件来源：{installed}')
                actual = files(installed)
                changed = [key for key, value in owned.items() if key not in actual or digest(actual[key]) != value]
                custom_code = [key for key in actual if key not in owned and (key.startswith('Source/') or key.endswith('.uplugin'))]
                if changed or custom_code:
                    raise UpdateError(f'插件含本地修改，停止覆盖：{project.stem}/{name}：{(changed + custom_code)[0]}')
                plans.append({'project': str(project), 'name': name, 'index': index})
        self.log(f"检查通过：{old['package_version']} → {new['package_version']}，{len(state['projects'])} 个工程；全部原有数据保留")
        return state, plans

    def mark(self, transaction, stage):
        transaction['stage'] = stage
        transaction['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        write_json(self.journal_file, transaction)

    def backup(self, state, plans, destination):
        destination.mkdir(parents=True, exist_ok=True)
        write_json(destination / 'environment.json', state)
        copy_file(self.home / 'credentials.json', destination / 'credentials.json')
        image = read_json(self.release(state) / 'manifest.json')['images']['db']['id']
        for key, volume in state['volumes'].items():
            self.log(f'正在备份 {dict(db="业务数据库与账号绑定", graph="图数据", data="CAD、底图与附件", models="模型文件")[key]}……')
            self.docker('run', '--rm', '--network', 'none', '--mount', f'type=volume,src={volume},dst=/source,readonly',
                        '--mount', f'type=bind,src={destination},dst=/backup', '--entrypoint', 'tar', image,
                        '-cpf', f'/backup/{key}.tar', '-C', '/source', '.', timeout=1800)
            self.docker('run', '--rm', '--network', 'none', '--mount', f'type=bind,src={destination},dst=/backup,readonly',
                        '--entrypoint', 'tar', image, '-tf', f'/backup/{key}.tar', timeout=180)
        for item in plans:
            source = Path(item['project']).parent / 'Plugins' / item['name']
            target = destination / 'projects' / str(item['index']) / item['name']
            copy_tree(source, target)
            project = Path(item['project'])
            copy_file(project, target.parent / project.name)
        hashes = {name: digest(p) for name, p in files(destination).items()}
        write_json(destination / 'backup.json', {'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                                               'instance_id': state['instance_id'], 'hashes': hashes, 'plans': plans})
        self.verify_backup(destination)

    def verify_backup(self, backup):
        data = read_json(backup / 'backup.json')
        for name, value in data['hashes'].items():
            safe_name(name)
            if digest(backup / name) != value:
                raise UpdateError(f'备份校验失败：{name}')
        return data

    def install_plugins(self, transaction):
        old_checks = read_json(self.release(transaction['old']) / 'SHA256SUMS.json')
        new_root = self.release(transaction['new'])
        for item in transaction['plans']:
            target = Path(item['project']).parent / 'Plugins' / item['name']
            prefix = f"Plugins/{item['name']}/"
            # Never park a .uplugin inside Plugins: UE recursively discovers duplicates.
            staging = Path(item['project']).parent / 'Saved/OntoTwinUpdates' / transaction['id'] / item['name']
            no_links(staging)
            staging.mkdir(parents=True, exist_ok=True)
            prepared = staging / 'new'
            no_links(target)
            if prepared.exists():
                raise UpdateError(f'暂存目录已存在：{prepared}')
            copy_tree(target, prepared)
            for key in old_checks:
                if key.startswith(prefix):
                    p = prepared / key[len(prefix):]
                    if disk_path(p).is_file():
                        disk_path(p).unlink()  # Only prior vendor-owned files in our new staging directory.
            copy_tree(new_root / 'Plugins' / item['name'], prepared, dirs_exist_ok=True)
            parked = staging / 'previous'
            item['parked'] = str(parked)
            item['prepared'] = str(prepared)
            self.mark(transaction, 'installing_plugins')
            target.rename(parked)
            prepared.rename(target)

    def update(self, release, all_projects_confirmed=False):
        with self.locked():
            if not all_projects_confirmed:
                raise UpdateError('请确认已添加所有使用此后台的 UE 工程')
            state, plans = self.preflight(release)
            # Estimate cold-volume backup + plugins; retain generous workspace overhead.
            image = read_json(self.release(state) / 'manifest.json')['images']['db']['id']
            total = 0
            for volume in state['volumes'].values():
                size = self.docker('run', '--rm', '--network', 'none', '--mount', f'type=volume,src={volume},dst=/source,readonly',
                                   '--entrypoint', 'du', image, '-sk', '/source')
                total += int(size.split()[0]) * 1024
            total += sum(p.stat().st_size for item in plans for p in files(Path(item['project']).parent / 'Plugins' / item['name']).values())
            if shutil.disk_usage(self.home).free < total * 2 + 1024 ** 3:
                raise UpdateError('备份和恢复空间不足，请释放空间后重试')
            txid = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
            backup = self.home / 'backups' / txid
            new = {**state, 'release': release, 'previous_release': state['release'], 'last_backup': str(backup)}
            tx = {'id': txid, 'old': state, 'new': new, 'plans': plans, 'backup': str(backup)}
            self.mark(tx, 'stopping')
            try:
                self.log('进入维护状态：暂时关闭网页访问，备份现有数据……')
                self.compose(state, 'stop', 'backend', 'neo4j')
                self.compose(state, 'up', '-d', '--pull', 'never', 'db', public=False)
                self.wait_db(state)
                tx['before'] = self.audit(state)
                self.compose(state, 'stop')
                tx['files_before'] = self.file_audit(state)
                self.mark(tx, 'backing_up')
                self.backup(state, plans, backup)
                self.mark(tx, 'backed_up')
                # Recheck UE after lengthy backup; no file replacement until it is idle.
                self.idle(state['projects'])
                self.install_plugins(tx)
                self.mark(tx, 'validating_private')
                self.log('备份已校验。正在更新前后端与插件，验证原有数据和绑定……')
                self.compose(new, 'up', '-d', '--pull', 'never', public=False)
                self.health(new)
                if self.audit(new) != tx['before']:
                    raise UpdateError('更新前后的业务数据指纹不一致，拒绝开放新版本')
                self.verify_preserved_files(tx['files_before'], self.file_audit(new))
                self.mark(tx, 'publishing')
                self.compose(new, 'up', '-d', '--pull', 'never', public=True)
                new['status'] = '程序已更新，待 UE 重启验证'
                new['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                write_json(self.state_file, new)
                self.mark(tx, 'complete')
                self.log('前后端和插件已更新，数据与绑定校验一致；请重启 UE 验证场景加载。')
                return new
            except BaseException as exc:
                tx['error'] = str(exc)
                write_json(self.journal_file, tx)
                self.log('更新未完成，保留备份与现场。请使用“恢复上次更新”，不会删除原数据卷。')
                raise

    def wait_db(self, state):
        for _ in range(60):
            try:
                self.compose(state, 'exec', '-T', 'db', 'pg_isready', '-U', 'ontotwin', '-d', 'ontotwin', public=False, timeout=10)
                return
            except UpdateError:
                time.sleep(1)
        raise UpdateError('数据库未就绪')

    def restore_volumes(self, state, backup, txid):
        self.verify_backup(backup)
        restored = {}
        image = read_json(self.release(state) / 'manifest.json')['images']['db']['id']
        for key in VOLUMES:
            name = state['instance_id'] + '_restore_' + txid.replace('-', '_') + '_' + key
            if self.docker('volume', 'inspect', name, check=False).returncode == 0:
                raise UpdateError('恢复目标已存在；保留现场，请重新开始恢复')
            self.docker('volume', 'create', '--label', 'ontotwin.instance=' + state['instance_id'], name)
            self.docker('run', '--rm', '--network', 'none', '--mount', f'type=volume,src={name},dst=/restore',
                        '--mount', f'type=bind,src={backup},dst=/backup,readonly', '--entrypoint', 'tar', image,
                        '-xpf', f'/backup/{key}.tar', '-C', '/restore', timeout=1800)
            restored[key] = name
        return {**state, 'volumes': restored}

    def recover(self):
        with self.locked():
            tx = self.pending()
            if not tx:
                raise UpdateError('没有中断的更新需要恢复')
            prior_stage = tx['stage']
            if prior_stage in ('publishing', 'recovering_public'):
                # Data may have been edited since the public port opened: never roll it back.
                self.log('新版本可能已对外提供访问；保留当前数据，仅恢复原程序和插件。')
            self.idle(tx['old']['projects'])
            self.compose(tx['new'], 'stop', public=False)
            old = tx.get('recovery_state', tx['old'])
            backup = Path(tx['backup'])
            if prior_stage == 'validating_private':
                old = self.restore_volumes(old, backup, uuid.uuid4().hex[:12])
            for item in tx['plans']:
                parked = Path(item['parked']) if item.get('parked') else None
                target = Path(item['project']).parent / 'Plugins' / item['name']
                if parked and parked.exists():
                    no_links(target); no_links(parked)
                    if target.exists():
                        target.rename(parked.parent / ('failed-' + uuid.uuid4().hex[:8]))
                    parked.rename(target)
            self.compose(old, 'up', '-d', '--pull', 'never', public=False)
            self.health(old)
            if prior_stage not in ('publishing', 'recovering_public') and tx.get('before') and self.audit(old) != tx['before']:
                raise UpdateError('恢复后数据校验未通过，保持维护状态')
            if prior_stage not in ('publishing', 'recovering_public') and tx.get('files_before'):
                self.verify_preserved_files(tx['files_before'], self.file_audit(old))
            tx['recovery_state'] = old
            self.mark(tx, 'recovering_public')
            self.compose(old, 'up', '-d', '--pull', 'never', public=True)
            old['status'] = '已恢复原版本，待 UE 重启验证'
            write_json(self.state_file, old)
            self.mark(tx, 'recovered')
            self.log('已恢复原程序、插件和数据；旧数据卷与备份均保留。')

    def start(self):
        with self.locked():
            self.assert_ready()
            state = self.state()
            self.check_docker(); self.verify_volumes(state)
            self.ensure_images(self.release(state))
            own = self.compose(state, 'ps', '--status', 'running', '-q', 'backend')
            if not own:
                with socket.socket() as listener:
                    try:
                        listener.bind(('127.0.0.1', state['port']))
                    except OSError:
                        raise UpdateError(f"端口 {state['port']} 已被其他程序占用，未停止任何服务")
            self.compose(state, 'up', '-d', '--pull', 'never')
            self.health(state)
            return state


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', required=True, type=Path)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('adopt').add_argument('package')
    sub.add_parser('add-project').add_argument('project')
    sub.add_parser('stage').add_argument('package')
    sub.add_parser('check').add_argument('release')
    update = sub.add_parser('update')
    update.add_argument('release')
    update.add_argument('--all-projects', action='store_true')
    sub.add_parser('start'); sub.add_parser('recover'); sub.add_parser('status')
    args = parser.parse_args()
    manager = Manager(args.home)
    if args.action == 'adopt': manager.adopt(args.package)
    elif args.action == 'add-project': manager.add_project(args.project)
    elif args.action == 'stage':
        with manager.locked(): print(manager.stage(args.package))
    elif args.action == 'check':
        with manager.locked(): manager.preflight(args.release)
    elif args.action == 'update': manager.update(args.release, args.all_projects)
    elif args.action == 'start': manager.start()
    elif args.action == 'recover': manager.recover()
    else: print(json.dumps(manager.state(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
