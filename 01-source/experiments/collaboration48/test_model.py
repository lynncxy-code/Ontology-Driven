import unittest
from model import Workspace, Rejected, demo_workspace


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.w = demo_workspace()
        self.admin = self.w.login('admin', 'DemoAdmin2026!')
        self.editor = self.w.login('engineer', 'DemoEditor2026!')
        self.viewer = self.w.login('viewer', 'DemoViewer2026!')
        self.a, self.b = list(self.w.projects)

    def enter(self, scene, client='one', token=None):
        return self.w.action(token or self.editor, 'enter', dict(engine='GroupFactory', scene=scene, client=client))

    def save(self, project, x, version=0, client='one'):
        return self.w.action(self.editor, 'save', dict(project=project, object='same-id', value={'x': x}, version=version, client=client))

    def test_init_local_and_once(self):
        w = Workspace()
        with self.assertRaises(Rejected):
            w.initialize('G','F','a','A','long-password',False)
        w.initialize('G','F','a','A','long-password')
        with self.assertRaises(Rejected):
            w.initialize('G','F','b','B','long-password')

    def test_editor_can_create_but_viewer_cannot(self):
        p = self.w.action(self.editor,'create',{'name':'新工厂'})['id']
        self.assertIn('engineer', self.w.projects[p]['editors'])
        self.assertIn(p, [x['id'] for x in self.w.state(self.viewer)['projects']])
        with self.assertRaises(Rejected):
            self.w.action(self.viewer,'create',{'name':'no'})

    def test_editor_cannot_manage_members(self):
        with self.assertRaises(Rejected):
            self.w.action(self.editor,'member',dict(account='x',name='X',password='long-password',role='admin'))

    def test_two_scenes_same_object_no_leak(self):
        self.enter('suzhou')
        self.save(self.a,10)
        self.enter('wuxi')
        with self.assertRaises(Rejected):
            self.save(self.a,99,1)
        self.save(self.b,20)
        a=self.enter('suzhou')
        self.assertEqual(a['objects']['same-id']['value']['x'],10)
        self.assertEqual(self.w.projects[self.b]['objects']['same-id']['value']['x'],20)

    def test_single_connection_and_timeout(self):
        now=[0]
        self.w.clock=lambda:now[0]
        self.enter('suzhou')
        with self.assertRaises(Rejected):
            self.enter('suzhou','two')
        now[0]=60
        self.enter('suzhou','two')
        self.assertEqual(self.w.bindings[('GroupFactory','suzhou')],self.a)

    def test_conflict_preserves_winner(self):
        self.enter('suzhou')
        self.save(self.a,10)
        with self.assertRaises(Rejected):
            self.save(self.a,20)
        self.assertEqual(self.w.projects[self.a]['objects']['same-id']['value']['x'],10)

    def test_revoke_blocks_live_session(self):
        self.enter('suzhou')
        self.w.action(self.admin,'grant',dict(project=self.a,account='engineer',edit=False))
        with self.assertRaises(Rejected):
            self.save(self.a,10)

    def test_export_no_identity_secrets(self):
        data=self.w.export_group(self.admin)
        self.assertEqual(set(data),{'format','version','group_id','group'})
        with self.assertRaises(Rejected):
            self.w.export_group(self.viewer)

    def test_admin_self_disable_rejected(self):
        with self.assertRaises(Rejected):
            self.w.action(self.admin,'enabled',{'account':'admin'})

    def test_first_password_required(self):
        self.w.action(self.admin,'member',dict(account='new',name='新成员',password='long-password',role='editor'))
        token=self.w.login('new','long-password')
        with self.assertRaises(Rejected):
            self.w.action(token,'create',{'name':'test'})
        self.w.action(token,'password',{'password':'another-long-password'})
        self.w.action(token,'create',{'name':'test'})

    def test_binding_cannot_silently_move(self):
        with self.assertRaises(Rejected):
            self.w.action(self.admin,'bind',dict(engine='GroupFactory',scene='suzhou',project=self.b))

    def test_switch_rechecks_target_permission(self):
        self.w.action(self.admin,'grant',dict(project=self.b,account='engineer',edit=False))
        self.enter('suzhou')
        with self.assertRaises(Rejected):
            self.enter('wuxi')
        self.save(self.a,1)


if __name__ == '__main__':
    unittest.main()
