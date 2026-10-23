"""Delivery orchestration, using existing ProjectStore format and APIs."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile
from contextlib import nullcontext

from . import attachments
from .service import DatasetPackageService, DatasetPackageError, _canonical_json, _summary


def digest(project):
    return hashlib.sha256(_canonical_json(project)).hexdigest()


class DeliveryPackageService(DatasetPackageService):
    def target_preview(self, package_bytes, target_id):
        report, incoming, _ = self._preflight(package_bytes)
        target = self.store.read_project(target_id)
        if not target or target_id == 'demo':
            raise DatasetPackageError('target_missing', '请选择已有的非内置项目', 404)
        removed = {}
        for key in ('instances', 'object_types', 'zones'):
            removed[key] = sorted(set(target.get(key) or {}) - set(incoming.get(key) or {}))
        for key, before, after, id_key in (
            ('frames', target.get('frames'), incoming.get('frames'), 'id'),
            ('routes', (target.get('scene_interactions') or {}).get('routes'), (incoming.get('scene_interactions') or {}).get('routes'), 'id'),
            ('pages', ((target.get('web_interactions') or {}).get('published') or {}).get('pages'), ((incoming.get('web_interactions') or {}).get('published') or {}).get('pages'), 'page_id'),
        ):
            def ids(items):
                if isinstance(items, dict):
                    return set(items)
                return {str(item.get(id_key) or item.get('frame_id') or item.get('route_id')) for item in (items or []) if isinstance(item, dict)}
            removed[key] = sorted(ids(before) - ids(after))
        report['warnings'] = [w for w in report['warnings'] if w['code'] not in ('source_ue_binding_cleared','dataset_name_conflict')]
        if report['attachments']['mode'] != 'project_assets':
            report['blockers'].append({'code':'full_package_required','message':'更新已有项目需要完整交付包；旧包可新建副本。'})
            report['can_import'] = False
        report['target'] = {'id': target_id, 'name': target.get('name'),
                            'ue': (target.get('dataset') or {}).get('bound_ue_project_name'),
                            'before': _summary(target), 'after': _summary(incoming),
                            'removed': removed, 'fingerprint': digest(target)}
        return report

    def _notify(self, project):
        if self.on_import:
            self.on_import(copy.deepcopy(project.get('dataset') or {}))

    def _backup_dir(self, target_id):
        return attachments.project_dir(Path(self.asset_root).parent / 'delivery_backups', target_id)

    def _backup(self, target):
        directory = self._backup_dir(target['id']) / uuid.uuid4().hex
        directory.mkdir(parents=True)
        (directory / 'project.json').write_bytes(_canonical_json(target))
        assets = attachments.project_dir(self.asset_root, target['id'])
        if assets.exists():
            # collect validates links before copying.
            attachments.collect(target, self.asset_root)
            shutil.copytree(assets, directory / 'assets')
        return directory

    def import_delivery(self, package_bytes, target_name=None, target_id=None,
                        expected=None, stopped=False, origin='http://127.0.0.1:5000'):
        with getattr(self.store, '_lock', nullcontext()):
            report, incoming, manifest = self._preflight(package_bytes)
            if report['blockers']:
                raise DatasetPackageError('package_preflight_blocked', '预检未通过', 422, report)
            old = None
            if target_id:
                old = self.store.read_project(target_id)
                if not old or target_id == 'demo' or digest(old) != expected:
                    raise DatasetPackageError('target_changed', '目标已变化，请重新预检', 409)
                if not stopped:
                    raise DatasetPackageError('stop_ue_required', '请停止 UE 运行后确认更新', 409)
                self._require_offline(target_id)
                if manifest.get('delivery_mode') != 'project_assets':
                    raise DatasetPackageError('full_package_required', '更新已有项目需要包含附件的完整交付包', 422)
            Path(self.asset_root).mkdir(parents=True, exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix='.delivery-', dir=self.asset_root))
            new_id = None
            destination = None
            displaced = None
            installed = False
            backup = None
            try:
                backup = self._backup(old) if old else None
                with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
                    attachments.install(archive, manifest, stage / 'assets')
                if old:
                    new_id = target_id
                    imported = copy.deepcopy(incoming)
                    imported.update(id=new_id, name=old['name'], created_at=old.get('created_at'))
                    ds = imported.setdefault('dataset', {})
                    old_ds = old.get('dataset') or {}
                    for key in ('id', 'name', 'created_at', 'bound_ue_project_id', 'bound_ue_project_name'):
                        ds[key] = old_ds.get(key, old.get(key, ''))
                    ds['id'], ds['name'] = new_id, old['name']
                    result = {'status': 'ok', 'dataset_id': new_id, 'project_id': new_id,
                              'dataset_name': old['name'], 'updated': True,
                              'bound': bool(ds.get('bound_ue_project_id'))}
                else:
                    callback, self.on_import = self.on_import, None
                    try:
                        result = super().import_package(package_bytes, target_name)
                    finally:
                        self.on_import = callback
                    new_id = result['project_id']
                    imported = self.store.read_project(new_id)
                attachments.remap_project(imported, str(incoming.get('id')), new_id, manifest,
                                          (imported.get('dataset') or {}).get('bound_ue_project_id') or '', origin)
                attachments.relocate_web(stage / 'assets', new_id, str(incoming.get('id')))
                destination = attachments.project_dir(self.asset_root, new_id)
                if destination.exists():
                    displaced = stage / 'previous-assets'
                    os.replace(destination, displaced)
                os.replace(stage / 'assets', destination)
                installed = True
                self.store.write_project(new_id, imported)
                self._notify(imported)
                if old:
                    marker = {'backup': backup.name, 'after': digest(imported)}
                    marker_path = self._backup_dir(new_id) / 'latest.json'
                    temp_marker = marker_path.with_suffix('.tmp')
                    temp_marker.write_text(json.dumps(marker), encoding='utf-8')
                    os.replace(temp_marker, marker_path)
                result['attachments_restored'] = len(manifest.get('attachments') or [])
                return result
            except Exception:
                if installed and destination and destination.exists():
                    shutil.rmtree(destination)
                if displaced and displaced.exists():
                    os.replace(displaced, destination)
                if old:
                    self.store.write_project(old['id'], old)
                    self._notify(old)
                elif new_id:
                    self.store.delete_project(new_id)
                raise
            finally:
                shutil.rmtree(stage, ignore_errors=True)

    def rollback(self, target_id, stopped=False):
        with getattr(self.store, '_lock', nullcontext()):
            root = self._backup_dir(target_id)
            self._require_offline(target_id)
            if not stopped or not (root / 'latest.json').exists():
                raise DatasetPackageError('rollback_unavailable', '请先停止 UE；此项目必须有更新备份', 409)
            marker = json.loads((root / 'latest.json').read_text(encoding='utf-8'))
            current = self.store.read_project(target_id)
            if digest(current) != marker['after']:
                raise DatasetPackageError('target_changed', '更新后项目已变化，不能直接回退覆盖后续修改', 409)
            backup = root / attachments.safe_relative(marker['backup'])
            previous = json.loads((backup / 'project.json').read_text(encoding='utf-8'))
            self._backup(current)
            destination = attachments.project_dir(self.asset_root, target_id)
            hold = destination.with_name('.rollback-' + uuid.uuid4().hex)
            if destination.exists():
                os.replace(destination, hold)
            try:
                if (backup / 'assets').exists():
                    shutil.copytree(backup / 'assets', destination)
                self.store.write_project(target_id, previous)
                self._notify(previous)
            except Exception:
                if destination.exists():
                    shutil.rmtree(destination)
                if hold.exists():
                    os.replace(hold, destination)
                self.store.write_project(target_id, current)
                self._notify(current)
                raise
            if hold.exists():
                shutil.rmtree(hold)
            (root / 'latest.json').unlink()
            return {'status': 'ok', 'dataset_id': target_id}

    @staticmethod
    def _require_offline(project_id):
        from scene_interaction.service import get_runtime_status
        if (get_runtime_status(project_id) or {}).get('online'):
            raise DatasetPackageError('ue_still_online', 'UE 仍在运行，请停止后稍候再试', 409)
