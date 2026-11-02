"""Project cards must resolve live UE heartbeats by stable identity, not the DB primary key."""
import sqlite3
from unittest.mock import MagicMock


def test_project_list_joins_binding_to_live_stable_identity(client, monkeypatch):
    import tenant_api
    import ue_project_binding
    from db import pg
    from flask import request

    # Execute the real list SELECT against isolated relational fixtures, so selecting
    # the internal FK instead of u.stable_key causes a real offline-state regression.
    db = sqlite3.connect(':memory:')
    db.executescript('''
        CREATE TABLE project(id,name,created_at,schema_version,status,organization_id,factory_id,deleted_at);
        CREATE TABLE object_type(project_id,deleted_at);
        CREATE TABLE instance(project_id,deleted_at);
        CREATE TABLE project_scene_binding(project_id,ue_project_id,scene_id,status);
        CREATE TABLE ue_project(ue_project_id,display_name,stable_key);
        CREATE TABLE ue_scene(scene_id,level_path,display_name,stable_key);
        INSERT INTO project VALUES('p','Test','today',7,'active','org','factory',NULL);
        INSERT INTO ue_project VALUES('db_internal_123','UE test','stable_ue_456');
        INSERT INTO ue_scene VALUES('scene_internal','/Game/A','A','/Game/A');
        INSERT INTO project_scene_binding VALUES('p','db_internal_123','scene_internal','active');
    ''')
    cursor = db.cursor()
    cur = MagicMock()
    cur.execute.side_effect = lambda sql, args=(): cursor.execute(sql.replace('%s', '?'), args)
    cur.fetchall.side_effect = cursor.fetchall
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur
    monkeypatch.setattr(pg, 'get_conn', lambda: conn)
    monkeypatch.setattr(tenant_api, '_require_pg', lambda: None)
    monkeypatch.setattr(tenant_api, '_load_session', lambda c: {'user_id':'user','organization_id':'org','factory_id':'factory','project_id':'p'})
    monkeypatch.setattr(tenant_api, '_factory_allowed', lambda *a, **kw: (True, 'admin'))
    monkeypatch.setattr(ue_project_binding, '_discovered_ue', {})
    try:
        assert client.get('/api/v4.8/projects').json['items'][0]['ue_online'] is False
        with client.application.test_request_context(headers={'X-OntoTwin-UE-Project-Id':'stable_ue_456','X-OntoTwin-UE-Scene-Id':'/Game/A'}):
            ue_project_binding.observe_ue_project(request)
        result = client.get('/api/v4.8/projects')
        assert result.status_code == 200
        assert result.json['items'][0]['ue_online'] is True
        monkeypatch.setattr(tenant_api, '_factory_allowed', lambda *a, **kw: (False, None))
        assert client.get('/api/v4.8/projects').status_code == 403
    finally:
        db.close()
