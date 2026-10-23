"""Loopback-only experimental server. No production database or UE calls."""
import argparse
import json
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from model import Workspace, Rejected, demo_workspace

ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def token(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get('Cookie', ''))
        return cookie['ot48'].value if 'ot48' in cookie else ''

    def reply(self, code, data, cookie=None):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        if cookie is not None:
            self.send_header('Set-Cookie', f'ot48={cookie}; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers()
        self.wfile.write(payload)

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {'error': '仅支持本机 127.0.0.1 地址'})
        if self.path == '/api/state':
            return self.reply(200, self.server.workspace.state(self.token()))
        if self.path in ('/', '/app.js', '/style.css'):
            file = ROOT / ('index.html' if self.path == '/' else self.path[1:])
            self.send_response(200)
            self.send_header('Content-Type', {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css'}[file.suffix] + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            return self.wfile.write(file.read_bytes())
        self.reply(404, {'error': '不存在'})

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}':
            return self.reply(403, {'error': '拒绝跨来源请求'})
        if self.headers.get('Content-Type') != 'application/json':
            return self.reply(415, {'error': '仅接受 JSON'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 65536:
                return self.reply(413, {'error': '请求大小无效'})
            data = json.loads(self.rfile.read(length))
            action = self.path.removeprefix('/api/')
            w = self.server.workspace
            if action == 'login':
                return self.reply(200, {'ok': True}, w.login(data['account'], data['password']))
            if action == 'logout':
                w.sessions.pop(self.token(), None)
                return self.reply(200, {'ok': True}, '')
            if action == 'initialize':
                group = data.get('group_file')
                if group and (group.get('format') != 'ontotwin-group' or group.get('version') != 1 or not group.get('group_id')):
                    raise Rejected('组织信息文件格式不兼容')
                w.initialize(group['group'] if group else data['group'], data['factory'], data['account'], data['name'], data['password'], self.client_address[0] == '127.0.0.1', group['group_id'] if group else None)
                return self.reply(200, {'ok': True}, w.login(data['account'], data['password']))
            if action == 'export':
                return self.reply(200, w.export_group(self.token()))
            return self.reply(200, w.action(self.token(), action, data))
        except Rejected as e:
            return self.reply(409, {'error': str(e)})
        except (KeyError, ValueError, TypeError):
            return self.reply(400, {'error': '参数或目标无效'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--port', type=int, default=5048)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.workspace = demo_workspace() if args.demo else Workspace()
    print(f'MVP sandbox: http://127.0.0.1:{args.port} (memory only; no production data)', flush=True)
    server.serve_forever()
