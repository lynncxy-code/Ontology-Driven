#!/usr/bin/env python3
"""Publish the acceptance environment on port 5501 (see AGENTS.md).

    python 01-source/tools/publish_5501.py [--task NEW-11 ...] [--dry-run]

Lives outside tools/deployment/ on purpose: that folder is copied into
customer packages, and this command only serves the internal 5501.

One run: assemble the latest dev plus the given task branches in
.worktrees/5501, take the next candidate number rc.N, back up the database,
build the whole image from that committed code, swap the 5501 container
(keeping data, mounts and configuration), check the reported version, roll
back automatically on failure, tag rc.N with the release notes, and keep only
the previous container. Only the Python standard library, git and Docker.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

CONTAINER = 'ontotwin-platform-20261106-candidate'
PREVIOUS = CONTAINER + '-previous'
NEXT = CONTAINER + '-next'
RETIRING = CONTAINER + '-retiring'
DB_CONTAINER = 'ontotwin-platform-20261106-db'
BACKUP_DIR = Path(r'E:\OntoTwin\platform-dev-20261106\backups')
IMAGE_REPO = 'ontotwin/platform'
DOCKERFILE = 'Dockerfile.4.8-rc'
HEALTH_PATH = '/api/v4.8/health'
CANDIDATE_BRANCH = 'candidate/5501'
FIRST_RC = 24
HEALTH_TIMEOUT = 120
ID_RE = re.compile(r'\b(?:BUG|OPT|NEW)-\d{2,}\b')
RC_RE = re.compile(r'^rc\.(\d+)$')


class PublishError(RuntimeError):
    pass


# ---------------------------------------------------------------- pure helpers

def next_rc(tags):
    numbers = [int(m.group(1)) for m in (RC_RE.match(t.strip()) for t in tags) if m]
    return max([FIRST_RC - 1] + numbers) + 1


def latest_rc_tag(tags):
    numbered = [(int(m.group(1)), t.strip()) for t in tags for m in [RC_RE.match(t.strip())] if m]
    return max(numbered)[1] if numbered else None


def task_branch(name):
    name = name.strip()
    return name if name.startswith('task/') else 'task/' + name


def collect_ids(lines):
    return sorted(set(ID_RE.findall('\n'.join(lines))), key=lambda i: (i.split('-')[0], int(i.split('-')[1])))


def container_specific_env(container_env, image_env):
    """Keep only variables set for this environment, not the old image's defaults."""
    defaults = set(image_env or [])
    keep = {}
    for item in container_env or []:
        if item in defaults or '=' not in item:
            continue
        key, value = item.split('=', 1)
        keep[key] = value
    keep.pop('ONTOTWIN_RELEASE_ID', None)
    keep.pop('ONTOTWIN_RELEASE_BUILT_AT', None)
    return keep


def create_args(old, env_keys, image, version, name, built_at=''):
    host = old['HostConfig']
    network = host['NetworkMode']
    args = ['create', '--name', name, '--network', network]
    aliases = (old['NetworkSettings']['Networks'].get(network) or {}).get('Aliases') or []
    for alias in aliases:
        if alias and not old['Id'].startswith(alias) and alias != old['Name'].lstrip('/'):
            args += ['--network-alias', alias]
    for port, bindings in (host.get('PortBindings') or {}).items():
        for b in bindings or []:
            args += ['-p', '{}:{}:{}'.format(b.get('HostIp') or '0.0.0.0', b['HostPort'], port.split('/')[0])]
    policy = (host.get('RestartPolicy') or {}).get('Name')
    if policy and policy != 'no':
        args += ['--restart', policy]
    for m in old.get('Mounts') or []:
        if m['Type'] != 'bind':
            raise PublishError('5501 容器有非目录挂载，发布命令不支持：' + m['Destination'])
        args += ['--mount', 'type=bind,src={},dst={}{}'.format(m['Source'], m['Destination'], '' if m['RW'] else ',readonly')]
    for key in sorted(env_keys):
        args += ['-e', key]          # values come from the process environment, never the command line
    if built_at:
        args += ['-e', 'ONTOTWIN_RELEASE_BUILT_AT=' + built_at]   # shown as the update time in the account menu
    args += ['-e', 'ONTOTWIN_RELEASE_ID=' + version, image]
    return args


def health_url(old):
    for bindings in (old['HostConfig'].get('PortBindings') or {}).values():
        for b in bindings or []:
            return 'http://{}:{}{}'.format(b.get('HostIp') or '127.0.0.1', b['HostPort'], HEALTH_PATH)
    raise PublishError('5501 容器没有对外端口')


def tasks_in_notes(notes):
    """The drafts a previous candidate carried, read from its tag notes."""
    for line in (notes or '').splitlines():
        if line.startswith('待验收草稿：'):
            return [t for t in re.split('[、,，\\s]+', line.split('：', 1)[1]) if t.startswith('task/')]
    return []


def choose_tasks(previous, added, dropped, in_dev, missing=()):
    """Keep what 5501 already carried, add new drafts, leave out drafts already in dev or dropped."""
    added = [task_branch(t) for t in added]
    dropped = {task_branch(t) for t in dropped}
    tasks, plan = [], []
    for t in previous + added:
        if t in tasks or t in dropped or t in in_dev or t in missing:
            continue
        tasks.append(t)
    kept = [t for t in previous if t in tasks]
    new = [t for t in tasks if t not in previous]
    if kept:
        plan.append('沿用上一版的待验收草稿：' + '、'.join(kept))
    if new:
        plan.append('这次新加入：' + '、'.join(new))
    gone_dev = [t for t in dict.fromkeys(previous + added) if t in in_dev]
    if gone_dev:
        plan.append('已经存进 dev，不再单独带上：' + '、'.join(gone_dev))
    vanished = [t for t in previous if t in missing]
    if vanished:
        plan.append('分支已不存在（可能已收尾或放弃），不再带上：' + '、'.join(vanished))
    gone = [t for t in previous if t in dropped]
    if gone:
        plan.append('按要求拿掉：' + '、'.join(gone))
    return tasks, plan


def render_notes(version, sha, dev_sha, tasks, ids, base, when):
    lines = ['OntoTwin 候选 {}（{}）· 验收版'.format(version.split('.')[1], version),
             '发布时间：' + when,
             '来源存档：' + sha + ('' if sha == dev_sha else '（dev ' + dev_sha[:7] + ' + 待验收草稿）'),
             '待验收草稿：' + ('、'.join(tasks) if tasks else '无（只有 dev）'),
             '对比基准：' + (base or '无（首次按新规则发布）'),
             '本版涉及编号：' + ('、'.join(ids) if ids else '无')]
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------- side effects

def run(*cmd, cwd=None, env=None, check=True):
    proc = subprocess.run(list(cmd), cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and proc.returncode:
        raise PublishError('命令失败：{}\n{}'.format(' '.join(cmd[:4]), (proc.stderr or proc.stdout)[-1500:]))
    return proc.stdout.strip()


def repo_root():
    common = Path(run('git', 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    return common.parent


def inspect(kind, name):
    out = run('docker', kind, 'inspect', name, check=False) if kind else run('docker', 'inspect', name, check=False)
    try:
        data = json.loads(out or '[]')
    except ValueError:
        data = []
    return data[0] if data else None


def worktrees(root):
    result, path = {}, None
    for line in run('git', 'worktree', 'list', '--porcelain', cwd=root).splitlines():
        if line.startswith('worktree '):
            path = line[9:]
        elif line.startswith('branch refs/heads/') and path:
            result[line[18:]] = path
    return result


def assemble(root, tasks):
    wt = root / '.worktrees' / '5501'
    if wt.exists():
        if run('git', 'status', '--porcelain', cwd=wt):
            raise PublishError('候选组装区 {} 里有未存档的改动，先处理掉再发布'.format(wt))
        run('git', 'checkout', '-q', '-B', CANDIDATE_BRANCH, 'dev', cwd=wt)
    else:
        run('git', 'worktree', 'add', '-q', '-B', CANDIDATE_BRANCH, str(wt), 'dev', cwd=root)
    open_trees = worktrees(root)
    warnings = []
    for branch in tasks:
        if not run('git', 'rev-parse', '--verify', '--quiet', branch, cwd=root, check=False):
            raise PublishError('找不到分支 ' + branch)
        tree = open_trees.get(branch)
        if tree and run('git', 'status', '--porcelain', cwd=tree, check=False):
            warnings.append('{} 的草稿里有未存档的改动，不会带上 5501'.format(branch))
        merged = subprocess.run(['git', 'merge', '--no-ff', '--no-edit', '-m', 'candidate: include ' + branch, branch],
                                cwd=wt, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if merged.returncode:
            run('git', 'merge', '--abort', cwd=wt, check=False)
            raise PublishError('{} 和前面的内容合不到一起（冲突），请先在该草稿里调整：\n{}'.format(branch, merged.stdout[-800:]))
    return wt, run('git', 'rev-parse', 'HEAD', cwd=wt), warnings


def backup_database(old, version):
    url = next((e.split('=', 1)[1] for e in old['Config']['Env'] if e.startswith('DATABASE_URL=')), '')
    parsed = urlparse(url)
    user, dbname = parsed.username or 'ontotwin', (parsed.path or '/ontotwin').lstrip('/')
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / 'pre-{}.dump'.format(version)
    inner = '/tmp/pre-{}.dump'.format(version)
    run('docker', 'exec', DB_CONTAINER, 'pg_dump', '-U', user, '-d', dbname, '-Fc', '-f', inner)
    run('docker', 'cp', '{}:{}'.format(DB_CONTAINER, inner), str(target))
    run('docker', 'exec', DB_CONTAINER, 'rm', '-f', inner, check=False)
    if target.stat().st_size < 1024:
        raise PublishError('数据库备份太小，可能没备份成功：' + str(target))
    return target


def wait_healthy(url, version):
    deadline = time.time() + HEALTH_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as res:
                if json.loads(res.read()).get('release_id') == version:
                    return
        except (OSError, ValueError):
            pass
        time.sleep(2)
    raise PublishError('新版本 {} 秒内没有报出版本号 {}'.format(HEALTH_TIMEOUT, version))


def swap(old, image, version, built_at):
    old_image = inspect('image', old['Image']) or {}
    env_values = container_specific_env(old['Config']['Env'], (old_image.get('Config') or {}).get('Env'))
    if inspect('', NEXT):
        run('docker', 'rm', '-f', NEXT)
    child_env = os.environ.copy()
    child_env.update(env_values)
    new_id = run('docker', *create_args(old, env_values.keys(), image, version, NEXT, built_at), env=child_env)
    had_previous = inspect('', PREVIOUS) is not None
    url = health_url(old)
    run('docker', 'stop', old['Id'])
    try:
        if had_previous:
            run('docker', 'rename', PREVIOUS, RETIRING)
        run('docker', 'rename', old['Id'], PREVIOUS)
        run('docker', 'rename', new_id, CONTAINER)
        run('docker', 'start', new_id)
        wait_healthy(url, version)
    except BaseException:
        run('docker', 'stop', new_id, check=False)
        run('docker', 'rm', '-f', new_id, check=False)
        run('docker', 'rename', old['Id'], CONTAINER, check=False)
        if had_previous:
            run('docker', 'rename', RETIRING, PREVIOUS, check=False)
        run('docker', 'start', old['Id'], check=False)
        raise
    if had_previous:
        run('docker', 'rm', '-f', RETIRING, check=False)


def prune_images():
    used = {c['Config']['Image'] for c in filter(None, (inspect('', CONTAINER), inspect('', PREVIOUS)))}
    removed = []
    for ref in run('docker', 'images', IMAGE_REPO, '--format', '{{.Repository}}:{{.Tag}}').splitlines():
        if ref.split(':', 1)[1].startswith('rc.') and ref not in used:
            if not subprocess.run(['docker', 'rmi', ref], capture_output=True).returncode:
                removed.append(ref)
    return removed


# ---------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description='发布 5501 验收环境')
    parser.add_argument('--task', action='append', default=[], help='新加入的待验收草稿编号，可重复，例如 --task NEW-11；上一版已带的草稿自动沿用')
    parser.add_argument('--drop', action='append', default=[], help='从 5501 上拿掉的草稿编号，可重复')
    parser.add_argument('--dry-run', action='store_true', help='只组装并显示将要发布的内容，不打包、不切换')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    root = repo_root()
    lock = root / '.worktrees' / '5501.lock'
    lock.parent.mkdir(exist_ok=True)
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print('另一个发布正在进行（{} 存在）。确认没有发布在跑后可删除它。'.format(lock))
        return 2
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    try:
        old = inspect('', CONTAINER)
        if not old or not old['State']['Running']:
            raise PublishError('5501 容器 {} 不在运行，先查明原因'.format(CONTAINER))
        tags = run('git', 'tag', '--list', 'rc.*', cwd=root).splitlines()
        version = 'rc.{}'.format(next_rc(tags))
        previous = latest_rc_tag(tags)
        previous_tasks = tasks_in_notes(run('git', 'tag', '--list', previous, '--format=%(contents)', cwd=root)) if previous else []
        exists = lambda t: bool(run('git', 'rev-parse', '--verify', '--quiet', t, cwd=root, check=False))
        missing = {t for t in previous_tasks if not exists(t)}
        in_dev = {t for t in previous_tasks + [task_branch(x) for x in args.task]
                  if t not in missing and exists(t)
                  and not subprocess.run(['git', 'merge-base', '--is-ancestor', t, 'dev'], cwd=root).returncode}
        tasks, plan = choose_tasks(previous_tasks, args.task, args.drop, in_dev, missing)
        wt, sha, warnings = assemble(root, tasks)
        dev_sha = run('git', 'rev-parse', 'dev', cwd=root)
        base = previous or (old['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')
        if base and not previous and subprocess.run(['git', 'merge-base', '--is-ancestor', base, sha], cwd=root).returncode:
            base = None
        # Merge commits only say which drafts were assembled; what is new is in the other commits.
        log = run('git', 'log', '--no-merges', '--format=%s%n%b', '{}..{}'.format(base, sha) if base else sha, '-n', '400', cwd=root)
        ids = collect_ids(log.splitlines() + [t for t in tasks if t not in previous_tasks])
        notes = render_notes(version, sha, dev_sha, tasks, ids, base and (base if base.startswith('rc.') else base[:12]),
                             datetime.now().strftime('%Y-%m-%d %H:%M'))
        for line in plan + ['提醒：' + w for w in warnings]:
            print(line)
        print(notes)
        if args.dry_run:
            print('（空跑：没有打包、没有切换 5501）')
            return 0

        dump = backup_database(old, version)
        print('数据库已备份：{}'.format(dump))
        image = '{}:{}'.format(IMAGE_REPO, version)
        run('docker', 'build', '-q', '-f', DOCKERFILE, '-t', image,
            '--label', 'org.opencontainers.image.revision=' + sha,
            '--label', 'org.opencontainers.image.version=' + version, '.', cwd=wt)
        print('已打包镜像：' + image)
        built_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        swap(old, image, version, built_at)
        run('git', 'tag', '-a', version, sha, '-m', notes, cwd=root)
        removed = prune_images()
        print('5501 已切换到 {}，版本号核对一致。上一版保留为容器 {}。'.format(version, PREVIOUS))
        if removed:
            print('已删除更早的候选镜像：' + '、'.join(removed))
        print('请把台账“5501 当前运行的版本”改为：候选 {}（{}）'.format(version.split('.')[1], version))
        return 0
    except PublishError as exc:
        print('发布失败，5501 保持原样：\n' + str(exc))
        return 1
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())
