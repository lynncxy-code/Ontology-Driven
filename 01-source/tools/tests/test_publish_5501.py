from pathlib import Path
import runpy
import unittest

ns = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'publish_5501.py'))


OLD = {
    'Id': 'abcdef1234567890',
    'Name': '/ontotwin-platform-20261106-candidate',
    'HostConfig': {
        'NetworkMode': 'net1',
        'PortBindings': {'5000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '5501'}]},
        'RestartPolicy': {'Name': 'unless-stopped'},
    },
    'NetworkSettings': {'Networks': {'net1': {'Aliases': ['abcdef123456', 'backend']}}},
    'Mounts': [
        {'Type': 'bind', 'Source': r'E:\data', 'Destination': '/app/data', 'RW': True},
        {'Type': 'bind', 'Source': r'E:\models', 'Destination': '/models', 'RW': False},
    ],
}


class PublishHelpersTests(unittest.TestCase):
    def test_first_candidate_is_24_and_counter_only_goes_up(self):
        self.assertEqual(ns['next_rc']([]), 24)
        self.assertEqual(ns['next_rc'](['rc.24', 'rc.9', 'v2026.12.1', 'rc.x']), 25)
        self.assertEqual(ns['next_rc'](['rc.3']), 24)
        self.assertEqual(ns['latest_rc_tag'](['rc.9', 'rc.24', 'rc.10']), 'rc.24')
        self.assertIsNone(ns['latest_rc_tag'](['v4.8.0-rc.21']))

    def test_task_branch_and_ids(self):
        self.assertEqual(ns['task_branch']('NEW-11'), 'task/NEW-11')
        self.assertEqual(ns['task_branch']('task/OPT-07'), 'task/OPT-07')
        ids = ns['collect_ids'](['fix(BUG-29): x', 'merge(NEW-08) and NEW-08', 'OPT-05 docs', 'NEW-3 too short', 'task/NEW-11'])
        self.assertEqual(ids, ['BUG-29', 'NEW-08', 'NEW-11', 'OPT-05'])

    def test_only_environment_specific_variables_are_carried_over(self):
        env = ns['container_specific_env'](
            ['PATH=/usr/bin', 'PYTHON_VERSION=3.10', 'DATABASE_URL=postgresql://u:p@db/x', 'ONTOTWIN_RELEASE_ID=old', 'EMPTY='],
            ['PATH=/usr/bin', 'PYTHON_VERSION=3.10'])
        self.assertEqual(env, {'DATABASE_URL': 'postgresql://u:p@db/x', 'EMPTY': ''})

    def test_create_args_keep_port_mounts_network_and_hide_secret_values(self):
        args = ns['create_args'](OLD, ['DATABASE_URL'], 'ontotwin/platform:rc.24', 'rc.24', 'next')
        joined = ' '.join(args)
        self.assertIn('-p 127.0.0.1:5501:5000', joined)
        self.assertIn('--network net1 ', joined)
        self.assertIn('--network-alias backend', joined)
        self.assertNotIn('--network-alias abcdef123456', joined)
        self.assertIn('--restart unless-stopped', joined)
        self.assertIn(r'type=bind,src=E:\models,dst=/models,readonly', joined)
        self.assertIn('-e DATABASE_URL ', joined)
        self.assertNotIn('postgresql', joined)
        self.assertEqual(args[-2:], ['ONTOTWIN_RELEASE_ID=rc.24', 'ontotwin/platform:rc.24'])
        self.assertNotIn('ONTOTWIN_RELEASE_BUILT_AT', joined)
        timed = ns['create_args'](OLD, [], 'img', 'rc.24', 'next', '2026-11-23T09:10:00Z')
        self.assertIn('ONTOTWIN_RELEASE_BUILT_AT=2026-11-23T09:10:00Z', timed)
        self.assertNotIn('ONTOTWIN_RELEASE_BUILT_AT', ns['container_specific_env'](['ONTOTWIN_RELEASE_BUILT_AT=old'], []))
        self.assertEqual(ns['health_url'](OLD), 'http://127.0.0.1:5501/api/v4.8/health')

    def test_non_bind_mount_is_refused(self):
        old = dict(OLD, Mounts=[{'Type': 'volume', 'Source': 'v', 'Destination': '/x', 'RW': True}])
        with self.assertRaises(ns['PublishError']):
            ns['create_args'](old, [], 'img', 'rc.24', 'next')

    def test_notes_name_candidate_sources_and_ids(self):
        notes = ns['render_notes']('rc.24', 'a' * 40, 'b' * 40, ['task/NEW-11'], ['NEW-11'], '8bf6752a7908', '2026-11-23 10:00')
        self.assertIn('OntoTwin 候选 24（rc.24）· 验收版', notes)
        self.assertIn('dev bbbbbbb + 待验收草稿', notes)
        self.assertIn('本版涉及编号：NEW-11', notes)
        only_dev = ns['render_notes']('rc.25', 'c' * 40, 'c' * 40, [], [], None, 't')
        self.assertIn('待验收草稿：无（只有 dev）', only_dev)
        self.assertIn('对比基准：无（首次按新规则发布）', only_dev)


if __name__ == '__main__':
    unittest.main()
