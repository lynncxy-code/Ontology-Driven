import copy
import pytest


@pytest.mark.parametrize('active', [True, False])
@pytest.mark.parametrize('dataset', [None, {}])
def test_first_merge_initializes_existing_project(client, store, monkeypatch, active, dataset):
    import app
    monkeypatch.setattr(app, '_datasets', [])
    monkeypatch.setattr(app, '_write_back_asset_mapping', lambda _: 0)
    store.create_project('Empty factory', project_id='first', dataset=dataset)
    if not active:
        store.activate('p_test')
    before = store.read_project('p_test')
    payload = {'mode': 'merge', 'items': [{'block_name': 'pump', 'name': 'Pump'}],
               'merge_options': {'target_dataset_id': 'first'}}
    response = client.post('/api/v2/coord/types/commit', json=payload)
    assert response.status_code == 200, response.json
    saved = store.read_project('first')
    assert saved['dataset']['graph_data']['nodes'][0]['rid'] == 'pump'
    assert 'pump' in saved['object_types']
    assert store.read_project('p_test') == before
    again = client.post('/api/v2/coord/types/commit', json=payload)
    assert again.status_code == 200, again.json
    assert again.json['added'] == 0
    assert len(store.read_project('first')['dataset']['graph_data']['nodes']) == 1


def test_missing_project_is_not_created(client, store):
    before = copy.deepcopy(store.get_active_copy())
    response = client.post('/api/v2/coord/types/commit', json={
        'mode': 'merge', 'merge_options': {'target_dataset_id': 'absent'},
        'items': [{'block_name': 'pump'}]})
    assert response.status_code == 404
    assert store.read_project('absent') is None
    assert store.get_active_copy() == before


def test_first_graph_keeps_existing_types_and_instances(client, store, monkeypatch):
    import app
    monkeypatch.setattr(app, '_datasets', [])
    before = store.get_active_copy()
    response = client.post('/api/v2/coord/types/commit', json={
        'mode': 'merge', 'merge_options': {'target_dataset_id': 'p_test'},
        'items': [{'block_name': 'pump'}]})
    assert response.status_code == 200, response.json
    saved = store.read_project('p_test')
    assert {'PE16A', 'pump'} <= saved['object_types'].keys()
    assert saved['instances'] == before['instances']
    assert saved['components'] == before['components']
