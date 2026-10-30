"""A page selection must never retarget a UE level in the 4.8 runtime."""
from unittest.mock import MagicMock
from flask import request
import pytest


def fake_db(monkeypatch, rows):
    from db import pg
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = rows
    monkeypatch.setattr(pg, "get_conn", lambda: conn)
    conn.__enter__.return_value = conn
    return cur


@pytest.mark.parametrize("force", [False, True])
def test_old_ue_bind_cannot_mutate_pg_project(client, store, monkeypatch, force):
    monkeypatch.setenv("ONTOTWIN_STORE", "pg")
    response = client.post('/api/v2/ue/bind_active_project',
        headers={'X-OntoTwin-UE-Project-Id': 'ue_test'},
        json={'force': force, 'target_project_id': 'p_test'})
    assert response.status_code == 409
    assert response.json['error'] == 'explicit_binding_required'
    assert not (store.get_active_dataset() or {}).get('bound_ue_project_id')


def test_scene_without_binding_never_falls_back_to_legacy(client, store, monkeypatch):
    import ue_project_binding as binding
    import app
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    fake_db(monkeypatch, [None])
    monkeypatch.setattr(binding, 'lookup_with_heal', lambda *_: pytest.fail('legacy fallback'))
    with app.app.test_request_context('/api/v2/ue/binding_status', headers={
        'X-OntoTwin-UE-Project-Id':'ue_test', 'X-OntoTwin-UE-Scene-Id':'/Game/Other'}):
        body, code = binding.binding_status(store, request)
    assert code == 200 and body['mode'] == 'unbound'
    assert body['can_write'] is False


def test_bound_scene_remains_writable_when_another_page_selects_project(client, store, monkeypatch):
    import ue_project_binding as binding
    import app
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    fake_db(monkeypatch, [('fixed-target',)])
    with app.app.test_request_context('/api/v2/ue/binding_status', headers={
        'X-OntoTwin-UE-Project-Id':'ue_test', 'X-OntoTwin-UE-Scene-Id':'/Game/Factory',
        'X-OntoTwin-Project-Id':'stale-browser-selection'}):
        body, code = binding.binding_status(store, request)
    assert code == 200 and body['project_id'] == 'fixed-target'
    assert body['can_write'] is True


def test_scene_db_error_fails_closed(client, store, monkeypatch):
    import ue_project_binding as binding
    import app
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    with app.app.test_request_context('/api/v2/ue/binding_status', headers={
        'X-OntoTwin-UE-Project-Id':'ue_test', 'X-OntoTwin-UE-Scene-Id':'/Game/Factory'}):
        body, code = binding.binding_status(store, request)
    assert code == 403 and body['error'] == 'binding_storage_unavailable'


def test_scene_permission_cannot_fall_back_to_project_binding(client, monkeypatch):
    import tenant_api
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    cur = fake_db(monkeypatch, [None, (1,)])
    assert not tenant_api.legacy_project_ue_allowed('p_test', 'ue_test', '/Game/Other')
    assert cur.execute.call_count == 1


def test_context_selection_only_changes_user_session(client, store, monkeypatch):
    import tenant_api
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    cur = fake_db(monkeypatch, [])
    monkeypatch.setattr(tenant_api, '_load_session', lambda _: {'user_id':'u', 'session_id':'s'})
    monkeypatch.setattr(tenant_api, '_org_role', lambda *_: 'admin')
    monkeypatch.setattr(tenant_api, '_factory_allowed', lambda *_: (True, 'admin'))
    monkeypatch.setattr(tenant_api, '_project_allowed', lambda *_: {'organization_id':'o', 'factory_id':'f'})
    # Route's injected store may differ from the fixture: its global activate must never run.
    from scoped_project_store import ScopedProjectStore
    monkeypatch.setattr(ScopedProjectStore, 'activate', lambda *_: pytest.fail('global activation'), raising=False)
    response = client.post('/api/v4.8/context', json={'organization_id':'o','factory_id':'f','project_id':'p'})
    assert response.status_code == 200, response.json
    assert cur.execute.call_count == 1
    assert 'UPDATE user_session' in cur.execute.call_args.args[0]


def test_projectless_discovery_requires_valid_session(client, monkeypatch):
    monkeypatch.setenv('ONTOTWIN_STORE', 'pg')
    fake_db(monkeypatch, [None])
    response = client.get('/api/v2/ue/discovered', headers={'X-OntoTwin-Session':'invalid'})
    assert response.status_code == 401
