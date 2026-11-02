"""Explicit isolated Docker/UE acceptance; never points at an existing production environment."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import urllib.request
import uuid

from manager import Manager, command, digest, read_json, verify_directory, write_json, REQUIRED_PLUGINS, UpdateError


def request(port, path, data):
    req = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
                                 data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as response: return json.load(response)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('--port', type=int, default=5428)
    parser.add_argument('--action', choices=['setup', 'update', 'rollback', 'stop'], required=True)
    args = parser.parse_args()
    if args.port in (5000, 5432, 7474, 7687) or 'new02' not in args.root.name.lower():
        raise SystemExit('Require NEW02-named isolated folder and a non-production port')
    args.root = args.root.absolute()
    m = Manager(args.root / 'environment', log=lambda s: print(s, flush=True))
    project = args.root / 'UE/NEW02.uproject'
    if args.action == 'setup':
        existing = args.root / 'old-install'
        manifest, checks = verify_directory(args.old)
        print('Copying verified old release', flush=True)
        for name in (*checks, 'SHA256SUMS.json'):
            target = existing / name; target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists(): shutil.copy2(args.old / name, target)
        command(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                 existing / 'Tools/Start-OntoTwinBackend.ps1', '-Port', args.port, '-NoBrowser'], timeout=600)
        print('Old isolated backend started', flush=True)
        project.parent.mkdir(parents=True, exist_ok=True)
        if not project.exists(): write_json(project, {'FileVersion': 3, 'EngineAssociation': '5.6', 'Plugins': [{'Name': n, 'Enabled': True} for n in REQUIRED_PLUGINS]})
        for name in REQUIRED_PLUGINS:
            if not (project.parent / 'Plugins' / name).exists(): shutil.copytree(existing / 'Plugins' / name, project.parent / 'Plugins' / name)
        (project.parent / 'Content').mkdir(exist_ok=True)
        (project.parent / 'Content/NEW02_customer_asset.txt').write_text('customer-owned scene content', encoding='utf-8')
        (project.parent / 'Plugins/OntoTwinSync/customer-note.txt').write_text('custom additional file', encoding='utf-8')
        if not m.state_file.exists(): m.adopt(existing)
        m.add_project(project)
        state = m.state()
        password = 'NEW02-acceptance-only-' + uuid.uuid4().hex[:10]
        write_json(args.root / 'test-login.json', {'password': password})
        initial = request(args.port, '/api/v4.8/auth/bootstrap', {
            'environment_name': 'ACCEPT_NEW02', 'organization_name': 'ACCEPT_NEW02_集团',
            'factory_name': 'ACCEPT_NEW02_工厂', 'login_name': 'accept_new02', 'password': password})
        initial = initial.get('data', initial)
        env, org, fac, user = [initial[k] for k in ('environment_id', 'organization_id', 'factory_id', 'user_id')]
        sql = f"""
INSERT INTO project(id,name,environment_id,organization_id,factory_id) VALUES
('ACCEPT_NEW02_project','保留数据验收','{env}','{org}','{fac}'),('ACCEPT_NEW02_empty','合法空数据集','{env}','{org}','{fac}');
INSERT INTO object_type(project_id,rid,name,data) VALUES ('ACCEPT_NEW02_project','camera','摄像头','{{"label":"中文类型"}}');
INSERT INTO instance(project_id,id,object_type_rid,display_name,raw_state) VALUES ('ACCEPT_NEW02_project','camera18','camera','摄像头18','{{"value":123,"customer":"unchanged"}}');
INSERT INTO project_permission(project_id,user_id,permission) VALUES ('ACCEPT_NEW02_project','{user}','edit');
INSERT INTO ue_project(ue_project_id,stable_key,display_name) VALUES ('ACCEPT_NEW02_ue','ACCEPT_NEW02_ue','NEW02');
INSERT INTO ue_scene(scene_id,ue_project_id,stable_key,level_path) VALUES ('ACCEPT_NEW02_scene','ACCEPT_NEW02_ue','ACCEPT_NEW02_scene','/Game/NEW02');
INSERT INTO project_scene_binding(binding_id,project_id,organization_id,factory_id,ue_project_id,scene_id,bound_by) VALUES
('ACCEPT_NEW02_binding','ACCEPT_NEW02_project','{org}','{fac}','ACCEPT_NEW02_ue','ACCEPT_NEW02_scene','{user}');
"""
        # SQL errors must fail the test, never silently skip fixture setup.
        m.compose(state, 'exec', '-T', 'db', 'psql', '-U', 'ontotwin', '-d', 'ontotwin', '-v', 'ON_ERROR_STOP=1', '-c', sql)
        code = "from pathlib import Path; p=Path('/app/data/NEW02'); p.mkdir(exist_ok=True); (p/'cad.dxf').write_text('customer CAD'); (p/'floor.png').write_bytes(b'customer image'); Path('/models/NEW02_model.glb').write_bytes(b'customer model')"
        m.compose(state, 'exec', '-T', 'backend', 'python', '-c', code)
        write_json(args.root / 'before.json', {'audit': m.audit(state), 'files': m.file_audit(state), 'volumes': state['volumes'], 'uproject': digest(project)})
        print('SETUP PASS', flush=True)
    elif args.action == 'update':
        with m.locked(): release = m.stage(args.new)
        new = m.update(release, all_projects_confirmed=True)
        before = read_json(args.root / 'before.json')
        assert m.audit(new) == before['audit']
        assert new['volumes'] == before['volumes']
        assert digest(project) == before['uproject']
        assert (project.parent / 'Plugins/OntoTwinSync/customer-note.txt').read_text() == 'custom additional file'
        assert (project.parent / 'Content/NEW02_customer_asset.txt').exists()
        assert len(list((project.parent / 'Plugins').rglob('OntoTwinSync.uplugin'))) == 1
        password = read_json(args.root / 'test-login.json')['password']
        login = request(args.port, '/api/v4.8/auth/login', {'login_name': 'accept_new02', 'password': password})
        assert login.get('ok', True), 'Old login must still work'
        m.compose(new, 'stop'); m.start()
        request(args.port, '/api/v4.8/auth/login', {'login_name': 'accept_new02', 'password': password})
        write_json(args.root / 'update-result.json', {'result': 'PASS', 'old_release': new['previous_release'],
                   'release': new['release'], 'backup': new['last_backup'], 'retained': ['accounts', 'permissions', 'dataset', 'empty dataset', 'instance', 'fixed level binding', 'CAD', 'image', 'model', 'uproject', 'customer content'], 'restart': 'PASS', 'login': 'PASS', 'ue_runtime': 'not yet verified'})
        print('UPDATE + RESTART + LOGIN PASS', flush=True)
    elif args.action == 'rollback':
        with m.locked(): release = m.stage(args.old)
        before = m.audit(m.state())
        original_health = m.health
        def injected(state):
            original_health(state)
            raise UpdateError('ACCEPT_NEW02 intentional private-health failure')
        m.health = injected
        try:
            m.update(release, all_projects_confirmed=True)
            raise AssertionError('Failure injection did not stop update')
        except UpdateError as exc:
            assert 'intentional' in str(exc), str(exc)
        m.health = original_health
        m.recover()
        state = m.state()
        assert m.audit(state) == before
        assert all('_restore_' in name for name in state['volumes'].values())
        request(args.port, '/api/v4.8/auth/login', {'login_name': 'accept_new02', 'password': read_json(args.root / 'test-login.json')['password']})
        write_json(args.root / 'rollback-result.json', {'result': 'PASS', 'recovered_release': state['release'], 'volumes_restored_into_new_names': True, 'original_volumes_preserved': True})
        print('INJECTED FAILURE + FULL BACKUP RESTORE + LOGIN PASS', flush=True)
    else:
        m.compose(m.state(), 'stop')


if __name__ == '__main__': main()
