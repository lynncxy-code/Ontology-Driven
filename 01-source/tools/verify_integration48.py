"""Destructive only to a NEW EMPTY disposable acceptance environment, never production."""
import argparse
import json
import secrets
from pathlib import Path
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--expected-release', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if not args.url.startswith(('http://127.0.0.1:', 'http://localhost:')) or args.url.endswith(':5000'):
        raise SystemExit('Use an isolated local test port, never production 5000.')
    admin, other = requests.Session(), requests.Session()
    checks = []

    def call(session, method, route, body=None, code=200, headers=None):
        response = session.request(method, args.url + route, json=body, headers=headers, timeout=15)
        assert response.status_code == code, (method, route, response.status_code, response.text)
        return response.json()

    health = call(admin,'GET','/api/v4.8/health')
    assert health['release_id'] == args.expected_release
    password = secrets.token_urlsafe(24)
    seed = call(admin, 'POST', '/api/v4.8/auth/bootstrap', {
        'environment_name':'ACCEPT48_EMPTY','organization_name':'ACCEPT48_ORG',
        'factory_name':'ACCEPT48_FACTORY','login_name':'accept48_admin','password':password},201)
    # Bootstrap returns 409 on any existing environment: no existing data is changed.
    call(admin,'POST','/api/v4.8/auth/login',{'login_name':'accept48_admin','password':password})
    org, factory = seed['organization_id'], seed['factory_id']
    context = {'organization_id':org,'factory_id':factory}
    call(admin,'POST','/api/v4.8/context',context)
    projects = [call(admin,'POST','/api/v4.8/projects',{**context,'name':'ACCEPT48_'+name},201)['project_id'] for name in ['P','Q']]
    call(admin,'POST',f'/api/v4.8/organizations/{org}/members',{'login_name':'accept48_other','password':password,'role':'admin','factory_ids':[factory]},201)
    call(other,'POST','/api/v4.8/auth/login',{'login_name':'accept48_other','password':password})
    ue = call(admin,'POST','/api/v4.8/ue/projects',{'stable_key':'ACCEPT48_UE','display_name':'Acceptance UE'})
    scene = call(admin,'POST',f"/api/v4.8/ue/projects/{ue['ue_project_id']}/scenes",{'stable_key':'/Game/Acceptance'})
    body = {'project_id':projects[0],'ue_project_id':ue['ue_project_id'],'scene_id':scene['scene_id']}
    bound = call(admin,'POST','/api/v4.8/bindings',body)
    # Repeated bind must remain active (regression for status=replaced).
    call(admin,'POST','/api/v4.8/bindings',body)
    headers = {'X-OntoTwin-UE-Project-Id':'ACCEPT48_UE','X-OntoTwin-UE-Scene-Id':'/Game/Acceptance'}
    runtime = requests.Session()
    status = call(runtime,'GET','/api/v2/ue/binding_status',headers=headers)
    assert status['project_id']==projects[0] and status['can_write']
    call(other,'POST','/api/v4.8/context',{**context,'project_id':projects[1]})
    status = call(runtime,'GET','/api/v2/ue/binding_status',headers=headers)
    assert status['project_id']==projects[0] and status['can_write']
    checks.append('two user sessions: changing page context preserves UE binding and write access')
    call(runtime,'POST','/api/v2/ue/bind_active_project',{'target_project_id':projects[1],'force':True},409,headers)
    conflict = call(admin,'POST','/api/v4.8/bindings',{**body,'project_id':projects[1]},409)
    assert conflict['error']=='scene_binding_conflict'
    call(admin,'POST','/api/v4.8/bindings',{**body,'project_id':projects[1],'replace_binding_id':conflict['binding_id']})
    status = call(runtime,'GET','/api/v2/ue/binding_status',headers={**headers,'X-OntoTwin-Project-Id':projects[0]})
    assert status['project_id']==projects[1]
    checks.append('explicit confirmed rebind changes target; stale client target cannot override it')
    unbound = call(runtime,'GET','/api/v2/ue/binding_status',headers={**headers,'X-OntoTwin-UE-Scene-Id':'/Game/Unbound'})
    assert unbound['mode']=='unbound' and not unbound['can_write']
    call(runtime,'GET','/api/v2/instances',headers={**headers,'X-OntoTwin-Project-Id':projects[0]},code=403)
    call(requests.Session(),'GET','/api/v2/instances',code=401)
    call(requests.Session(),'GET','/api/v2/ue/discovered',code=401,headers={'X-OntoTwin-Session':'invalid-cookie'})
    checks.append('unbound scene, wrong project and anonymous reads fail closed')
    call(admin,'POST','/api/v4.8/context',{**context,'project_id':projects[1]})
    read = call(admin,'GET','/api/v4.8/projects')
    assert len(read['items'])==2
    args.report.write_text(json.dumps({'release':health['release_id'],'checks':checks,'projects':projects,'organization_id':org,'factory_id':factory},indent=2),encoding='utf-8')
    # Local-only verification credentials; keep alongside ignored test evidence, never in a package.
    args.report.with_suffix('.local-login.json').write_text(json.dumps({'login_name':'accept48_admin','password':password,'organization_id':org,'factory_id':factory}),encoding='utf-8')
    print(json.dumps({'passed':checks,'report':str(args.report)}))


if __name__ == '__main__':
    main()
