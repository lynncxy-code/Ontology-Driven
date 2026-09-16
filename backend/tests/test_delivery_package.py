import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['ONTOTWIN_STORE'] = 'json'
from project_store import ProjectStore
from dataset_package.delivery import DeliveryPackageService, digest
from dataset_package.service import DatasetPackageError
from dataset_package.api import register_dataset_package_routes
from flask import Flask


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = ProjectStore(str(self.root/'source'), str(self.root/'source-active.json'))
        self.target = ProjectStore(str(self.root/'target'), str(self.root/'target-active.json'))
        self.source.create_project('Source', project_id='source')
        self.target.create_project('Target', project_id='target')
        target = self.target.read_project('target')
        target['dataset'] = {'id':'target','name':'Target','graph_data':{'nodes':[], 'links':[]}}
        self.target.write_project('target', target)
        p = self.source.read_project('source')
        p['dataset'] = {'id':'source','name':'Source','graph_data':{'nodes':[], 'links':[]}}
        p['frames'] = [{'id':'frame-one', 'kind':'image', 'image':{'storage_name':'plan.png'}, 'to_ue':{'matrix':[[1,0,0],[0,1,0],[0,0,1]]}}]
        p['web_interactions']['published'] = {'pages':[{'page_id':'monitor','base_url':'http://127.0.0.1:5000/monitor.html?camera_id=18'}], 'web_policy':{'allowed_hosts':['127.0.0.1']}}
        self.source.write_project('source', p)
        self.src_assets = self.root/'source-assets'
        self.dst_assets = self.root/'target-assets'
        spatial = self.src_assets/'source'/'spatial_frames'
        spatial.mkdir(parents=True)
        (spatial/'plan.png').write_bytes(b'fixture-png')
        web = self.root/'frontend'
        web.mkdir()
        (web/'monitor.html').write_text('<link href="/style.css"><script src="/app.js"></script>', encoding='utf-8')
        (web/'style.css').write_text('body {background:transparent}', encoding='utf-8')
        (web/'app.js').write_text('const href="/monitor.html?camera_id=18";', encoding='utf-8')
        self.exporter = DeliveryPackageService(self.source, asset_root=self.src_assets, frontend_root=web)
        self.importer = DeliveryPackageService(self.target, asset_root=self.dst_assets, frontend_root=web)
        self.package = self.exporter.export_package('source')[0]

    def tearDown(self):
        self.tmp.cleanup()

    def test_copy_restores_images_web_and_keeps_active(self):
        result = self.importer.import_delivery(self.package, 'Copy', origin='http://new-host:5000')
        pid = result['project_id']
        self.assertEqual('target', self.target.get_active_id())
        self.assertEqual(b'fixture-png', (self.dst_assets/pid/'spatial_frames/plan.png').read_bytes())
        project = self.target.read_project(pid)
        url = project['web_interactions']['published']['pages'][0]['base_url']
        self.assertEqual(f'http://new-host:5000/api/v2/project-assets/{pid}/web/monitor.html?camera_id=18', url)
        self.assertIn(f'/api/v2/project-assets/{pid}/web/style.css', (self.dst_assets/pid/'web/monitor.html').read_text())
        self.assertEqual(4, result['attachments_restored'])

    def test_update_preserves_binding_and_rollback(self):
        original = self.target.read_project('target')
        original.setdefault('dataset', {}).update(id='target',name='Target',bound_ue_project_id='ue-test',bound_ue_project_name='UE Test')
        self.target.write_project('target',original)
        assets = self.dst_assets/'target'
        assets.mkdir(parents=True)
        (assets/'old.txt').write_text('old')
        preview = self.importer.target_preview(self.package, 'target')
        self.importer.import_delivery(self.package,target_id='target',expected=preview['target']['fingerprint'],stopped=True)
        updated = self.target.read_project('target')
        self.assertEqual('ue-test',updated['dataset']['bound_ue_project_id'])
        self.assertEqual('Target',updated['name'])
        self.assertFalse((assets/'old.txt').exists())
        self.importer.rollback('target',stopped=True)
        self.assertEqual(original,self.target.read_project('target'))
        self.assertEqual('old',(assets/'old.txt').read_text())

    def test_missing_attachment_blocks_full_export(self):
        (self.src_assets/'source/spatial_frames/plan.png').unlink()
        with self.assertRaises(DatasetPackageError): self.exporter.export_package('source')
        package = self.exporter.export_package('source', data_only=True)[0]
        self.assertEqual('data_only',self.importer.preflight(package)['attachments']['mode'])

    def test_stale_preview_and_unconfirmed_stop_rejected(self):
        with self.assertRaises(DatasetPackageError):
            self.importer.import_delivery(self.package,target_id='target',expected='stale',stopped=True)
        with self.assertRaises(DatasetPackageError):
            self.importer.import_delivery(self.package,target_id='target',expected=digest(self.target.read_project('target')))

    def test_failed_update_restores_data_and_attachments(self):
        old = self.target.read_project('target')
        assets = self.dst_assets/'target'
        assets.mkdir(parents=True)
        (assets/'old.txt').write_text('old')
        original_write = self.target.write_project
        calls = []
        def fail_once(pid, project):
            calls.append(pid)
            if len(calls) == 1: raise OSError('injected write failure')
            return original_write(pid, project)
        with patch.object(self.target,'write_project',side_effect=fail_once):
            with self.assertRaises(OSError):
                self.importer.import_delivery(self.package,target_id='target',expected=digest(old),stopped=True)
        self.assertEqual(old,self.target.read_project('target'))
        self.assertEqual('old',(assets/'old.txt').read_text())

    def test_corrupt_attachment_rejected_before_write(self):
        out = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(self.package)) as source, zipfile.ZipFile(out,'w') as dest:
            for name in source.namelist():
                dest.writestr(name, b'corrupt' if name.endswith('plan.png') else source.read(name))
        with self.assertRaises(DatasetPackageError): self.importer.import_delivery(out.getvalue(),'Corrupt')

    def test_extra_path_rejected(self):
        out = io.BytesIO(self.package)
        with zipfile.ZipFile(out,'a') as archive: archive.writestr('../escape.txt',b'bad')
        with self.assertRaises(DatasetPackageError): self.importer.preflight(out.getvalue())

    def test_online_runtime_blocks_update(self):
        with patch('scene_interaction.service.get_runtime_status',return_value={'online':True}):
            with self.assertRaises(DatasetPackageError):
                self.importer.import_delivery(self.package,target_id='target',expected=digest(self.target.read_project('target')),stopped=True)

    def test_reexport_imported_web_remaps_again(self):
        first = self.importer.import_delivery(self.package,'First')
        exported = self.importer.export_package(first['project_id'])[0]
        second = self.importer.import_delivery(exported,'Second',origin='http://second:5000')
        pid = second['project_id']
        project = self.target.read_project(pid)
        self.assertTrue(project['web_interactions']['published']['pages'][0]['base_url'].startswith('http://second:5000/'))
        self.assertIn(f'/api/v2/project-assets/{pid}/web/',(self.dst_assets/pid/'web/app.js').read_text())
        self.assertNotIn(first['project_id'],(self.dst_assets/pid/'web/app.js').read_text())

    def test_http_preflight_import_update_rollback_and_web(self):
        app = Flask(__name__)
        register_dataset_package_routes(app,self.target,asset_root=self.dst_assets)
        client = app.test_client()
        def form(**kwargs):
            return {'file':(io.BytesIO(self.package),'test.otdataset'),**kwargs}
        preview = client.post('/api/v2/ontology/dataset-packages/preflight',data=form(target_id='target')).json
        imported = client.post('/api/v2/ontology/dataset-packages/import',data=form(target_id='target',expected=preview['target']['fingerprint'],stopped='true'))
        self.assertEqual(201,imported.status_code,imported.json)
        page = client.get('/api/v2/project-assets/target/web/monitor.html')
        self.assertEqual(200,page.status_code)
        page.close()
        response = client.post('/api/v2/ontology/datasets/target/package-rollback',json={'stopped':True})
        self.assertEqual(200,response.status_code,response.json)

    def test_v1_legacy_package_copy_allowed_update_blocked(self):
        from tests.test_dataset_package import DatasetPackageTests
        package = self.exporter.export_package('source',data_only=True)[0]
        def legacy(manifest, project):
            manifest['format_version'] = 1
            manifest.pop('delivery_mode',None)
            manifest.pop('attachments',None)
        old = DatasetPackageTests.rebuild_package(package, legacy)
        self.assertEqual('legacy',self.importer.preflight(old)['attachments']['mode'])
        self.importer.import_delivery(old,'Legacy')
        with self.assertRaises(DatasetPackageError):
            self.importer.import_delivery(old,target_id='target',expected=digest(self.target.read_project('target')),stopped=True)

    def test_http_binding_switch_keeps_active_and_old_project(self):
        from ue_project_binding import rebuild_index, index_lookup
        self.target.create_project('Other',project_id='other')
        old = self.target.read_project('target')
        old.setdefault('dataset',{}).update(id='target',name='Target',bound_ue_project_id='ue-test',bound_ue_project_name='UE Test')
        self.target.write_project('target',old)
        active = self.target.get_active_id()
        app = Flask(__name__)
        register_dataset_package_routes(app,self.target,asset_root=self.dst_assets)
        response = app.test_client().post('/api/v2/ontology/datasets/other/package-bind',json={'ue_id':'ue-test','expected_previous':'target','replace':True,'stopped':True})
        self.assertEqual(200,response.status_code,response.json)
        self.assertEqual(active,self.target.get_active_id())
        self.assertEqual('',self.target.read_project('target')['dataset']['bound_ue_project_id'])
        self.assertEqual('other',index_lookup('ue-test'))

    @unittest.skipUnless(os.environ.get('ONTOTWIN_TEST_PG_URL'), 'requires isolated PostgreSQL')
    def test_postgresql_attachments_update_and_rollback(self):
        from db import pg
        pg.DATABASE_URL = os.environ['ONTOTWIN_TEST_PG_URL']
        from project_store_pg import ProjectStorePG
        store = ProjectStorePG()
        original = self.target.read_project('target')
        original['id'] = 'delivery-pg-target'
        original['dataset'].update(id='delivery-pg-target',bound_ue_project_id='ue-delivery-pg')
        store.write_project(original['id'],original)
        before = store.read_project(original['id'])
        service = DeliveryPackageService(store,asset_root=self.dst_assets)
        service.import_delivery(self.package,target_id=original['id'],expected=digest(before),stopped=True)
        self.assertEqual('ue-delivery-pg',store.read_project(original['id'])['dataset']['bound_ue_project_id'])
        self.assertTrue((self.dst_assets/original['id']/'spatial_frames/plan.png').exists())
        service.rollback(original['id'],stopped=True)
        self.assertEqual(before,store.read_project(original['id']))
