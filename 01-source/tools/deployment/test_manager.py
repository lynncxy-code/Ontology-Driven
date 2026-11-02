"""Safety regressions. No Docker, real databases or installed projects are touched."""
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

from manager import Manager, UpdateError, digest, disk_path, read_json, safe_name, verify_directory, write_json


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manager = Manager(self.root / 'environment', log=lambda _: None)
        self.package = self.root / 'package'
        self.package.mkdir()
        (self.package / 'Runtime').mkdir()
        (self.package / 'Runtime/images.tar').write_bytes(b'test-archive')
        self.manifest = {'release_id': '4.8.0-test-abc123', 'package_version': '4.8.0-test',
                         'source_commit': 'a'*40, 'contains_customer_data': False,
                         'contains_ue_project': False, 'ue_version': '5.6',
                         'images_archive_sha256': digest(self.package / 'Runtime/images.tar'),
                         'images': {n: {'id': 'sha256:' + 'b'*64, 'tag': n} for n in ('backend', 'db', 'neo4j')},
                         'plugins': {n: {} for n in ('OntoTwinSync', 'OntoTwinIndustrialBehavior', 'glTFRuntime', 'WebUI')}}
        write_json(self.package / 'manifest.json', self.manifest)
        self.checks()

    def tearDown(self):
        # Only delete this test's own generated temporary directory (extended paths).
        target = self.root.resolve()
        assert target.parent == Path(tempfile.gettempdir()).resolve() and target.name.startswith('tmp')
        shutil.rmtree(disk_path(target))
        self.temp.cleanup()

    def checks(self):
        write_json(self.package / 'SHA256SUMS.json', {p.relative_to(self.package).as_posix(): digest(p)
                   for p in self.package.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.json'})

    def zip(self):
        target = self.root / 'release.zip'
        with zipfile.ZipFile(target, 'w') as archive:
            for p in self.package.rglob('*'):
                if p.is_file(): archive.write(p, p.relative_to(self.package).as_posix())
        return target

    def test_valid_zip_has_same_release_and_checksum(self):
        release = self.manager.stage(self.zip())
        manifest, checks = verify_directory(self.manager.home / 'releases' / release)
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(checks, read_json(self.package / 'SHA256SUMS.json'))

    def test_windows_long_character_asset_paths(self):
        name = 'Plugins/OntoTwinSync/Content/' + ('long-directory/' * 15) + 'asset.uasset'
        target = disk_path(self.package / name)
        target.parent.mkdir(parents=True); target.write_bytes(b'asset')
        checks = read_json(self.package / 'SHA256SUMS.json'); checks[name] = digest(target)
        write_json(self.package / 'SHA256SUMS.json', checks)
        release = self.manager.stage(self.package)
        self.assertEqual(digest(self.manager.home / 'releases' / release / name), digest(target))

    def test_corrupt_zip_never_enters_releases(self):
        (self.package / 'Runtime/images.tar').write_bytes(b'corrupted')
        with self.assertRaisesRegex(UpdateError, '校验失败'):
            self.manager.stage(self.zip())
        self.assertFalse((self.manager.home / 'releases').exists())

    def test_unlisted_payload_rejected(self):
        (self.package / 'malicious.ps1').write_text('unexpected')
        with self.assertRaisesRegex(UpdateError, '清单'):
            self.manager.stage(self.zip())

    def test_traversal_and_windows_ambiguous_names(self):
        for name in ('../escape', 'C:/data', '/tmp/data', 'a\\b', 'a/../b', 'a//b', 'a.', 'CON.txt', '.runtime/instance.json', 'a:stream'):
            with self.subTest(name=name), self.assertRaises(UpdateError): safe_name(name)

    def test_zip_case_collision(self):
        target = self.zip()
        with zipfile.ZipFile(target, 'a') as archive: archive.writestr('MANIFEST.JSON', '{}')
        with self.assertRaisesRegex(UpdateError, '重复'):
            self.manager.stage(target)

    def test_same_release_different_bytes_rejected(self):
        self.manager.stage(self.zip())
        self.manifest['generated_at'] = 'changed'
        write_json(self.package / 'manifest.json', self.manifest); self.checks()
        with self.assertRaisesRegex(UpdateError, '同一发布编号'):
            self.manager.stage(self.zip())

    def test_exclusive_environment_lock(self):
        other = Manager(self.manager.home)
        with self.manager.locked(), self.assertRaisesRegex(UpdateError, '另一个'):
            with other.locked(): pass

    def test_partial_update_cannot_start(self):
        write_json(self.manager.journal_file, {'stage': 'validating_private'})
        with self.assertRaisesRegex(UpdateError, '上次更新'):
            self.manager.start()

    def test_backup_corruption_rejected(self):
        backup = self.root / 'backup'; backup.mkdir()
        (backup / 'db.tar').write_bytes(b'old')
        write_json(backup / 'backup.json', {'hashes': {'db.tar': digest(backup / 'db.tar')}})
        (backup / 'db.tar').write_bytes(b'changed')
        with self.assertRaisesRegex(UpdateError, '备份校验失败'):
            self.manager.verify_backup(backup)

    def test_modified_files_are_not_silently_accepted(self):
        with self.assertRaisesRegex(UpdateError, '原文件内容发生变化'):
            self.manager.verify_preserved_files({'data': {'CAD.dxf': 'abc'}}, {'data': {'CAD.dxf': 'xyz'}})
        self.manager.verify_preserved_files({'data': {'CAD.dxf': 'abc'}}, {'data': {'CAD.dxf': 'abc', 'new': '123'}})

    def test_update_requires_explicit_complete_project_scope(self):
        with self.assertRaisesRegex(UpdateError, '所有'):
            self.manager.update('new')

    def test_unrelated_nonempty_directory_is_never_adopted_as_home(self):
        root = self.root / 'customer'; root.mkdir(); (root / 'existing.txt').write_text('keep')
        with self.assertRaisesRegex(UpdateError, '已有其他内容'):
            Manager(root)
        self.assertEqual((root / 'existing.txt').read_text(), 'keep')

    def test_foreign_volume_ownership_is_rejected(self):
        state = {'instance_id': 'ontotwin-123456abcdef',
                 'volumes': {k: 'ontotwin-123456abcdef_' + k for k in ('db', 'graph', 'data', 'models')}}
        with patch.object(self.manager, 'docker', return_value='[{"Labels":{"ontotwin.instance":"other"}}]'), self.assertRaisesRegex(UpdateError, '归属'):
            self.manager.verify_volumes(state)

    def test_schema_upgrade_stops_before_idle_backup_or_install(self):
        old = self.manager.stage(self.package)
        next_manifest = {**self.manifest, 'release_id': '4.8-next'}
        next_path = self.manager.home / 'releases/4.8-next'; next_path.mkdir()
        write_json(next_path / 'manifest.json', next_manifest)
        write_json(self.manager.state_file, {'instance_id': 'ontotwin-123456abcdef', 'port': 5428, 'release': old})
        with patch.object(self.manager, 'check_docker'), patch.object(self.manager, 'verify_volumes'), \
             patch.object(self.manager, 'ensure_images', side_effect=[self.manifest, next_manifest]), \
             patch.object(self.manager, 'schema', side_effect=['old', 'new']), \
             patch.object(self.manager, 'idle') as idle, patch.object(self.manager, 'backup') as backup:
            with self.assertRaisesRegex(UpdateError, '数据库结构'):
                self.manager.preflight('4.8-next')
            idle.assert_not_called(); backup.assert_not_called()
        self.assertFalse(self.manager.journal_file.exists())

    def test_recovery_after_publication_preserves_post_update_data(self):
        state = {'instance_id': 'ontotwin-123456abcdef', 'port': 5428, 'release': 'old', 'projects': []}
        tx = {'stage': 'publishing', 'old': state, 'new': {**state, 'release': 'new'}, 'plans': [],
              'backup': str(self.root / 'backup'), 'before': {}}
        write_json(self.manager.journal_file, tx)
        with patch.object(self.manager, 'idle'), patch.object(self.manager, 'compose'), \
             patch.object(self.manager, 'health'), patch.object(self.manager, 'restore_volumes') as restore:
            self.manager.recover()
            restore.assert_not_called()
        self.assertEqual(read_json(self.manager.journal_file)['stage'], 'recovered')

    def test_plugin_staging_preserves_customer_content_and_avoids_duplicate_plugins(self):
        project = self.root / 'UE/Project.uproject'
        project.parent.mkdir(); write_json(project, {'EngineAssociation': '5.6'})
        installed = project.parent / 'Plugins/OntoTwinSync'
        installed.mkdir(parents=True)
        (installed / 'OntoTwinSync.uplugin').write_text('old')
        (installed / 'customer.txt').write_text('keep')
        old = self.manager.home / 'releases/old'; old.mkdir(parents=True)
        write_json(old / 'SHA256SUMS.json', {'Plugins/OntoTwinSync/OntoTwinSync.uplugin': 'ignored'})
        new = self.manager.home / 'releases/new/Plugins/OntoTwinSync'; new.mkdir(parents=True)
        (new / 'OntoTwinSync.uplugin').write_text('new')
        tx = {'id': 'test', 'old': {'release': 'old'}, 'new': {'release': 'new'},
              'plans': [{'project': str(project), 'name': 'OntoTwinSync', 'index': 0}]}
        self.manager.install_plugins(tx)
        self.assertEqual((installed / 'customer.txt').read_text(), 'keep')
        self.assertEqual((installed / 'OntoTwinSync.uplugin').read_text(), 'new')
        self.assertEqual(len(list((project.parent / 'Plugins').rglob('*.uplugin'))), 1)
        self.assertEqual((Path(tx['plans'][0]['parked']) / 'OntoTwinSync.uplugin').read_text(), 'old')


if __name__ == '__main__': unittest.main()
