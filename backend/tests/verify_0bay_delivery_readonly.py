"""Read-only production export -> temporary JSON store. Never import into live API."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['ONTOTWIN_STORE'] = 'json'
os.environ['DATABASE_URL'] = ''
from project_store import ProjectStore
from dataset_package.delivery import DeliveryPackageService

with urlopen('http://127.0.0.1:5000/api/v2/ontology/datasets/ds_1788856616035/package') as response:
    package = response.read()
with tempfile.TemporaryDirectory(prefix='delivery-0bay-') as temp:
    root = Path(temp)
    store = ProjectStore(str(root/'projects'),str(root/'active.json'))
    store.create_project('Isolated',project_id='isolated')
    service = DeliveryPackageService(store,asset_root=root/'assets')
    result = service.import_delivery(package,'0bay-isolated-check')
    target = root/'assets'/result['project_id']
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        source = json.loads(archive.read('project.json'))
        verified = []
        for item in manifest['attachments']:
            path = item['file'].removeprefix('attachments/')
            restored = target/path
            assert restored.exists(), path
            if not path.startswith('web/'):
                assert hashlib.sha256(restored.read_bytes()).hexdigest() == item['sha256']
            verified.append(path)
    imported = store.read_project(result['project_id'])
    assert imported['frames'] == source['frames'] or all(a.get('to_ue') == b.get('to_ue') for a,b in zip(imported['frames'],source['frames']))
    assert store.get_active_id() == 'isolated'
    assert imported['dataset']['bound_ue_project_id'] == ''
    print(json.dumps({'status':'passed','production_write':False,'attachments':verified,'frames':len(imported['frames']),'instances':len(imported['instances']),'package_bytes':len(package)},ensure_ascii=False))
