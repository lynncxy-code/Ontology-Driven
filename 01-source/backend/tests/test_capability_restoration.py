"""BUG-17: independently attachable appearance and behavior capabilities."""
import pytest


@pytest.fixture(params=['legacy', 'scoped'])
def capability_client(client, store, monkeypatch, request):
    import app as module
    if request.param == 'scoped':
        from scoped_project_store import ScopedProjectStore
        facade = ScopedProjectStore(store)
        monkeypatch.setattr(module, 'project_store', facade)
        monkeypatch.setattr(module, 'instance_store', facade)
        # A distinct global fallback must never enter the selected project's store.
        monkeypatch.setattr(module, '_object_types', module._ScopedObjectTypes({'GLOBAL_ONLY': {'name': 'Global'}}))
        client.environ_base['HTTP_X_ONTOTWIN_PROJECT_ID'] = store.get_active_id()
    else:
        monkeypatch.setattr(module, '_object_types', store.get_object_types())
    monkeypatch.setattr(module, '_active_dataset_id', store.get_active_id())
    monkeypatch.setattr(module, '_datasets', [])
    return client


@pytest.mark.parametrize('interfaces', [['I3D_Visual'], ['I3D_Behavioral'], ['I3D_Visual', 'I3D_Behavioral']])
def test_independent_capability_save_and_reload(capability_client, store, interfaces):
    result = capability_client.post('/api/v2/ontology/inject', json={'object_type_rid': 'PE16A', 'interfaces': interfaces})
    assert result.status_code == 200, result.json
    assert set(result.json['injected_interfaces']) == set(interfaces)
    store.activate(store.get_active_id())
    assert set(store.get_object_types()['PE16A']['injected_interfaces']) == set(interfaces)
    read = capability_client.get('/api/v2/ontology/types/PE16A')
    assert set(read.json['injected_interfaces']) == set(interfaces)
    assert read.json['has_representable'] is False


@pytest.mark.parametrize('interface', ['I3D_Spatial', 'I3D_Overlay', 'I3D_Presentation'])
def test_hierarchical_capability_still_needs_model(capability_client, interface):
    result = capability_client.post('/api/v2/ontology/inject', json={'object_type_rid': 'PE16A', 'interfaces': [interface]})
    assert result.status_code == 400


def test_removing_model_retains_independent_capabilities(capability_client, store):
    result = capability_client.post('/api/v2/ontology/inject', json={'object_type_rid': 'PE16A', 'interfaces': ['I3D_Representable', 'I3D_Spatial', 'I3D_Visual', 'I3D_Behavioral']})
    assert result.status_code == 200
    result = capability_client.post('/api/v2/ontology/inject/remove', json={'object_type_rid': 'PE16A', 'interface_rid': 'I3D_Representable'})
    assert result.status_code == 200
    assert set(result.json['injected_interfaces']) == {'I3D_Visual', 'I3D_Behavioral'}
    assert set(store.read_project('p_test')['object_types']['PE16A']['injected_interfaces']) == {'I3D_Visual', 'I3D_Behavioral'}


def test_missing_type_rejected(capability_client):
    assert capability_client.post('/api/v2/ontology/inject', json={'object_type_rid': 'BUG17_missing', 'interfaces': ['I3D_Visual']}).status_code == 404


def test_library_status_describes_current_capability(capability_client):
    result = capability_client.get('/api/v2/presentation-library/status')
    assert result.status_code == 200
    assert result.json['interface_rid'] == 'I3D_Behavioral'
    assert result.json['legacy_interface_rid'] == 'I3D_Presentation'
    assert result.json['catalog_version']
    assert result.json['resource_count'] > 0


def test_scoped_save_preserves_other_project_and_global_selection(client, store, monkeypatch):
    import app as module
    from scoped_project_store import ScopedProjectStore
    original = store.read_project('p_test')['object_types']
    store.create_project('BUG17 second project', project_id='BUG17_other',
                         object_types={'OTHER': {'rid': 'OTHER', 'name': 'Other'}})
    store.activate('p_test')
    facade = ScopedProjectStore(store)
    monkeypatch.setattr(module, 'project_store', facade)
    monkeypatch.setattr(module, 'instance_store', facade)
    monkeypatch.setattr(module, '_object_types', module._ScopedObjectTypes(original))
    monkeypatch.setattr(module, '_active_dataset_id', 'p_test')
    monkeypatch.setattr(module, '_datasets', [])
    result = client.post('/api/v2/ontology/inject',
                         headers={'X-OntoTwin-Project-Id': 'BUG17_other'},
                         json={'object_type_rid': 'OTHER', 'interfaces': ['I3D_Visual']})
    assert result.status_code == 200, result.json
    assert store.read_project('p_test')['object_types'] == original
    other = store.read_project('BUG17_other')['object_types']
    assert set(other) == {'OTHER'}
    assert other['OTHER']['injected_interfaces'] == ['I3D_Visual']
    assert store.get_active_id() == 'p_test'
