"""Run inside a dedicated test container, never inside production or test0316.

Reuses real Nexus HTML/API; keeps account state in the container's separate data
volume. It is a navigation integration, not complete production authorization.
"""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, quote

if os.environ.get('ONTOTWIN_48_ISOLATED') != '1':
    raise RuntimeError('Requires dedicated isolated test container')
sys.path.insert(0, '/app')
os.environ['ONTOTWIN_STORE'] = 'json'
os.environ['ONTOTWIN_MOCK_SIMULATOR_ENABLED'] = 'false'
# No external assets, voice services or middleware writes in this environment.
import requests
def no_external_requests(*args, **kwargs):
    raise requests.ConnectionError('4.8 isolated test: external services disabled')
requests.sessions.Session.request = no_external_requests
import app as legacy
from flask import request, jsonify, redirect, send_file, make_response
from model import Workspace, Rejected

app = legacy.app
ROOT = Path(__file__).parent
STATE = Path('/app/data/collaboration48.json')
w = Workspace()
if STATE.exists():
    saved = json.loads(STATE.read_text(encoding='utf-8'))
    w.org, w.users, w.projects = saved['org'], saved['users'], saved['projects']

def persist():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix('.pending')
    temp.write_text(json.dumps(dict(org=w.org, users=w.users, projects=w.projects), ensure_ascii=False), encoding='utf-8')
    temp.replace(STATE)

def sync_projects():
    for p in legacy._datasets:
        if p['id'] not in w.projects:
            w.projects[p['id']] = dict(id=p['id'], name=p['name'], editors=[], objects={})
        else:
            w.projects[p['id']]['name'] = p['name']
    live = {p['id'] for p in legacy._datasets}
    w.projects = {k: v for k, v in w.projects.items() if k in live}

def token():
    return request.cookies.get('ot48test', '')

def next_path(value):
    parsed = urlsplit(value or '')
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/') or parsed.path.startswith('//') or '\\' in value:
        return '/nexus'
    if parsed.path not in ('/nexus', '/ontology_graph', '/ontology', '/binding', '/coord', '/interaction', '/instance', '/trash', '/organization'):
        return '/nexus'
    return parsed.path + ('?' + parsed.query if parsed.query else '')

@app.before_request
def protect_test_environment():
    if request.host != '127.0.0.1:5148':
        return jsonify(error='Use local test address 127.0.0.1:5148'), 403
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('Origin') != 'http://127.0.0.1:5148':
            return jsonify(error='Cross-origin write rejected'), 403
    if request.path.startswith('/_collab48/') or request.path in ('/account', '/prototype48'):
        return None
    try:
        user = w.identity(token())
    except Rejected:
        if request.path.startswith('/api/'):
            return jsonify(error='请先登录', login_url='/account'), 401
        return redirect('/account?next=' + quote(next_path(request.full_path.rstrip('?')), safe=''))
    # Conservative test gate: legacy APIs are not all project-scoped yet.
    if request.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if user['role'] != 'admin' and not (user['role'] == 'editor' and request.path == '/api/v2/ontology/datasets' and request.method == 'POST'):
            return jsonify(error='此旧业务写入口尚未完成 4.8 权限适配；测试环境暂仅管理员可操作'), 403

@app.route('/account')
@app.route('/organization')
def account_page():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    html = html.replace('/style.css', '/_collab48/style.css').replace('/app.js', '/_collab48/app.js')
    html = html.replace('4.8 MVP 交互试验 · 隔离内存数据，重启清空 · 未连接正式后端或 UE', '4.8 联通测试环境 · 独立测试数据 · 未连接真实 UE')
    return html

@app.route('/prototype48')
def product_prototype():
    return send_file(ROOT / 'prototype.html')

@app.route('/_collab48/<name>')
def integration_asset(name):
    if name == 'brand.svg':
        return send_file('/frontend/assets/ontotwin-logo.svg')
    if name not in ('style.css', 'app.js', 'navigation.js', 'integration-ui.js', 'integration.css', 'prototype.css', 'prototype.js'):
        return '', 404
    if name == 'app.js':
        script = (ROOT / name).read_text(encoding='utf-8')
        script = script.replace("'/api/", "'/_collab48/api/")
        script = script.replace("let state, page='organization'", "let state, page=new URLSearchParams(location.search).get('tab')==='members'?'members':'organization'")
        # Add integration hooks without duplicating or editing the product page.
        return app.response_class(script + '\n' + (ROOT / 'integration-ui.js').read_text(encoding='utf-8'), mimetype='text/javascript')
    return send_file(ROOT / name)

@app.route('/_collab48/api/state')
def integration_state():
    with w.lock:
        sync_projects()
        result = w.state(token())
        result['integration'] = True
        return jsonify(result)

@app.route('/_collab48/api/<action>', methods=['POST'])
def integration_action(action):
    data = request.get_json(silent=True) or {}
    try:
        with w.lock:
            if action == 'login':
                result = make_response(jsonify(ok=True))
                result.set_cookie('ot48test', w.login(data['account'], data['password']), httponly=True, samesite='Strict')
                return result
            if action == 'logout':
                w.sessions.pop(token(), None)
                result = make_response(jsonify(ok=True))
                result.delete_cookie('ot48test')
                return result
            if action == 'initialize':
                group = data.get('group_file')
                if group and (group.get('format') != 'ontotwin-group' or group.get('version') != 1 or not group.get('group_id')):
                    raise Rejected('组织信息格式不兼容')
                w.initialize(group['group'] if group else data['group'], data['factory'], data['account'], data['name'], data['password'], True, group['group_id'] if group else None)
                persist()
                result = make_response(jsonify(ok=True))
                result.set_cookie('ot48test', w.login(data['account'], data['password']), httponly=True, samesite='Strict')
                return result
            if action == 'export':
                return jsonify(w.export_group(token()))
            if action not in ('member', 'grant', 'enabled', 'organization', 'password'):
                raise Rejected('请从已有业务页面进行此操作')
            sync_projects()
            result = w.action(token(), action, data)
            persist()
            return jsonify(result)
    except Rejected as e:
        return jsonify(error=str(e)), 409
    except (KeyError, ValueError, TypeError):
        return jsonify(error='请求参数无效'), 400

@app.after_request
def integrate_response(response):
    if request.path == '/api/v2/ontology/datasets' and request.method == 'POST' and response.status_code == 200:
        payload = response.get_json(silent=True) or {}
        pid = payload.get('dataset_id')
        if pid:
            with w.lock:
                sync_projects()
                if pid in w.projects:
                    account = w.identity(token())['account']
                    if account not in w.projects[pid]['editors']:
                        w.projects[pid]['editors'].append(account)
                    persist()
    if response.mimetype == 'text/html' and response.status_code == 200 and request.path != '/prototype48':
        response.direct_passthrough = False
        text = response.get_data(as_text=True)
        tags = '<link rel="stylesheet" href="/_collab48/integration.css"><script defer src="/_collab48/navigation.js"></script>'
        response.set_data(text.replace('</head>', tags + '</head>'))
        response.headers.pop('Content-Length', None)
    return response

if __name__ == '__main__':
    print('4.8 integrated test: http://127.0.0.1:5148/nexus', flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
