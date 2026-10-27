"""Isolated, in-memory PRD 4.8 executable model. NOT production authentication."""
import copy
import hashlib
import hmac
import secrets
import threading
import time


class Rejected(Exception):
    pass


class Workspace:
    def __init__(self, clock=time.monotonic):
        self.lock = threading.RLock()
        self.clock = clock
        self.org = None
        self.users = {}
        self.projects = {}
        self.bindings = {}
        self.connections = {}
        self.sessions = {}

    @staticmethod
    def password(value, salt):
        return hashlib.pbkdf2_hmac('sha256', value.encode(), salt.encode(), 100000).hex()

    def add_user(self, account, name, password, role, first_login=True):
        if role not in ('admin', 'editor', 'viewer') or not account.strip() or not name.strip():
            raise Rejected('请填写账号、姓名和有效角色')
        if account in self.users:
            raise Rejected('账号已存在')
        if len(password) < 12:
            raise Rejected('密码至少 12 位')
        salt = secrets.token_hex(16)
        self.users[account] = dict(account=account, name=name, role=role, enabled=True,
                                   salt=salt, password=self.password(password, salt), first_login=first_login)

    def initialize(self, group, factory, account, name, password, local=True, group_id=None):
        with self.lock:
            if not local or self.org:
                raise Rejected('仅未初始化环境的部署本机可创建首个管理员')
            if not group.strip() or not factory.strip():
                raise Rejected('请填写集团和本地工厂')
            self.add_user(account, name, password, 'admin', False)
            self.org = dict(group=group, factory=factory, group_id=group_id or secrets.token_hex(12),
                            factory_id=secrets.token_hex(12), environment_id=secrets.token_hex(12))

    def login(self, account, password):
        with self.lock:
            user = self.users.get(account)
            if not user or not user['enabled'] or not hmac.compare_digest(user['password'], self.password(password, user['salt'])):
                raise Rejected('账号或密码不正确')
            token = secrets.token_urlsafe(32)
            self.sessions[token] = account
            return token

    def identity(self, token, allow_initial=False):
        user = self.users.get(self.sessions.get(token))
        if not user or not user['enabled']:
            raise Rejected('请先登录')
        if user['first_login'] and not allow_initial:
            raise Rejected('请先修改初始密码')
        return user

    def can_edit(self, user, project):
        return user['role'] == 'admin' or user['account'] in project['editors']

    def public_user(self, user):
        return {k: user[k] for k in ('account', 'name', 'role', 'enabled', 'first_login')}

    def state(self, token):
        with self.lock:
            result = dict(initialized=bool(self.org), org=copy.deepcopy(self.org), demo=True)
            try:
                user = self.identity(token, True)
            except Rejected:
                return result
            result['me'] = self.public_user(user)
            if user['first_login']:
                return result
            result['projects'] = copy.deepcopy(list(self.projects.values()))
            result['bindings'] = [dict(engine=k[0], scene=k[1], project=v) for k, v in self.bindings.items()]
            if user['role'] == 'admin':
                result['users'] = [self.public_user(u) for u in self.users.values()]
            return result

    def action(self, token, action, data):
        with self.lock:
            u = self.identity(token, action == 'password')
            admin = u['role'] == 'admin'
            if action == 'password':
                value = data['password']
                if len(value) < 12:
                    raise Rejected('密码至少 12 位')
                u['salt'] = secrets.token_hex(16)
                u['password'] = self.password(value, u['salt'])
                u['first_login'] = False
                for key in list(self.sessions):
                    if self.sessions[key] == u['account'] and key != token:
                        del self.sessions[key]
            elif action == 'member':
                if not admin:
                    raise Rejected('仅管理员可管理成员')
                self.add_user(data['account'], data['name'], data['password'], data['role'])
            elif action == 'enabled':
                if not admin or data['account'] == u['account']:
                    raise Rejected('不能停用自己，且必须由管理员操作')
                target = self.users[data['account']]
                if target['role'] == 'admin' and target['enabled'] and sum(x['enabled'] and x['role'] == 'admin' for x in self.users.values()) <= 1:
                    raise Rejected('必须保留一名可用管理员')
                target['enabled'] = not target['enabled']
                for key in list(self.sessions):
                    if self.sessions[key] == target['account']:
                        del self.sessions[key]
            elif action == 'organization':
                if not admin:
                    raise Rejected('仅管理员可维护组织信息')
                if not data['group'].strip() or not data['factory'].strip():
                    raise Rejected('名称不能为空')
                self.org.update(group=data['group'], factory=data['factory'])
            elif action == 'create':
                if u['role'] not in ('admin', 'editor') or not data['name'].strip():
                    raise Rejected('仅管理员与编辑者可创建项目，名称不能为空')
                pid = secrets.token_hex(8)
                self.projects[pid] = dict(id=pid, name=data['name'], editors=[u['account']], objects={})
                return {'id': pid}
            elif action == 'grant':
                if not admin:
                    raise Rejected('仅管理员可授权')
                project = self.projects[data['project']]
                account = data['account']
                if account not in self.users:
                    raise Rejected('成员不存在')
                if data['edit'] and account not in project['editors']:
                    project['editors'].append(account)
                elif not data['edit'] and account in project['editors']:
                    project['editors'].remove(account)
            elif action == 'bind':
                project = self.projects[data['project']]
                key = (data['engine'].strip(), data['scene'].strip())
                if not all(key) or not self.can_edit(u, project):
                    raise Rejected('请选择工程、场景及有编辑权的项目')
                if key in self.bindings and self.bindings[key] != project['id']:
                    raise Rejected('场景已有绑定；MVP 不提供隐式覆盖')
                if project['id'] in self.bindings.values() and self.bindings.get(key) != project['id']:
                    raise Rejected('该项目已绑定另一场景')
                self.bindings[key] = project['id']
            elif action == 'enter':
                key = (data['engine'], data['scene'])
                pid = self.bindings.get(key)
                if not pid or not self.can_edit(u, self.projects[pid]):
                    raise Rejected('场景未绑定或无编辑权限')
                self.connections = {k: v for k, v in self.connections.items() if self.clock() - v['time'] < 60}
                client = data['client']
                existing = self.connections.get(pid)
                if existing and (existing['client'] != client or existing['account'] != u['account']):
                    raise Rejected('项目正在被另一份 UE 使用')
                self.connections = {k: v for k, v in self.connections.items() if not (v['client'] == client and v['account'] == u['account'])}
                self.connections[pid] = dict(client=client, account=u['account'], time=self.clock(), scene=key)
                return dict(project=pid, objects=copy.deepcopy(self.projects[pid]['objects']))
            elif action == 'save':
                pid = data['project']
                project = self.projects[pid]
                if not self.can_edit(u, project):
                    raise Rejected('没有项目编辑权限')
                if data.get('client'):
                    connection = self.connections.get(pid)
                    if not connection or connection['client'] != data['client'] or connection['account'] != u['account'] or self.clock() - connection['time'] >= 60:
                        raise Rejected('场景连接已失效，请重新进入')
                obj = project['objects'].get(data['object'], {'version': 0})
                if obj['version'] != data['version']:
                    raise Rejected('对象已更新，请重新载入；本次输入未提交')
                project['objects'][data['object']] = dict(version=obj['version']+1, value=copy.deepcopy(data['value']), author=u['name'])
                return copy.deepcopy(project['objects'][data['object']])
            else:
                raise Rejected('不支持的操作')
            return {'ok': True}

    def export_group(self, token):
        if self.identity(token)['role'] != 'admin':
            raise Rejected('仅管理员可导出组织信息')
        return dict(format='ontotwin-group', version=1, group_id=self.org['group_id'], group=self.org['group'])


def demo_workspace():
    w = Workspace()
    w.initialize('华东制造集团', '苏州工厂', 'admin', '陈经理', 'DemoAdmin2026!')
    w.add_user('engineer', '张工程师', 'DemoEditor2026!', 'editor', False)
    w.add_user('viewer', '李访客', 'DemoViewer2026!', 'viewer', False)
    token = w.login('admin', 'DemoAdmin2026!')
    for scene, name in [('suzhou', '苏州工厂 · 总装车间'), ('wuxi', '无锡工厂 · 验证样例')]:
        pid = w.action(token, 'create', {'name': name})['id']
        w.action(token, 'grant', dict(project=pid, account='engineer', edit=True))
        w.action(token, 'bind', dict(engine='GroupFactory', scene=scene, project=pid))
    w.sessions.clear()
    return w
