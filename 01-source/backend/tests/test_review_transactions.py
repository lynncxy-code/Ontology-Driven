"""Audit regressions: real transaction boundaries, without importing app startup."""
import ast
import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask, jsonify


def test_nonactive_transaction_rollback_and_serialization(store):
    store.create_project('B', project_id='b', dataset={'id':'b', 'name':'B', 'graph_data':{'nodes':[]}})
    store.activate('p_test')
    active_before = store.get_active_copy()
    disk_before = store.read_project('b')
    with patch.object(store, '_save_current', side_effect=OSError('disk unavailable')):
        with pytest.raises(OSError):
            store.transact_project('b', lambda w: w.update(name='changed'))
    assert store.get_active_copy() == active_before
    assert store.read_project('b') == disk_before
    def increment(_):
        store.transact_project('b', lambda w: w.update(counter=w.get('counter', 0) + 1))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(increment, range(20)))
    assert store.read_project('b')['counter'] == 20
    assert store.get_active_copy() == active_before


def test_merge_conflict_does_not_change_memory_or_disk(store):
    ds = {'id':'b', 'name':'B', 'graph_data':{'nodes':[{'rid':'old'}]}}
    store.create_project('B', project_id='b', dataset=ds)
    store.activate('p_test')
    source = Path(__file__).parents[1] / 'app.py'
    function = next(n for n in ast.parse(source.read_text(encoding='utf-8')).body
                    if isinstance(n, ast.FunctionDef) and n.name == '_commit_merge')
    scope = {'project_store':store, '_datasets':[copy.deepcopy(ds)], '_active_dataset_id':'p_test',
             '_object_types':{}, 'copy':copy, 'jsonify':jsonify,
             '_item_to_node':lambda item, source: {'rid':item['block_name']},
             '_project_dataset_to_object_types':lambda ds, existing_types: {n['rid']:n for n in ds['graph_data']['nodes']},
             '_write_back_asset_mapping':lambda _:0}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), scope)
    before = copy.deepcopy(scope['_datasets'])
    disk_before = store.read_project('b')
    with Flask(__name__).app_context(), patch.object(store, 'transact_project', side_effect=ValueError('changed')):
        response, status = scope['_commit_merge']({'merge_options':{'target_dataset_id':'b'}},
                                                  [{'block_name':'new'}], 'test.dxf', False)
    assert status == 409
    assert scope['_datasets'] == before
    assert store.read_project('b') == disk_before


def test_discovered_engine_context_and_capacity(monkeypatch):
    import ue_project_binding as binding
    monkeypatch.setattr(binding, '_discovered_ue', {})
    monkeypatch.setattr(binding, '_DISCOVERY_MAX_ENTRIES', 2)
    app = Flask(__name__)
    def observe(engine, context=None):
        headers = {binding.UE_ID_HEADER: engine}
        if context:
            headers['X-OntoTwin-UE-Context'] = context
        with app.test_request_context(headers=headers):
            from flask import request
            binding.observe_ue_project(request)
    with patch.object(binding.time, 'time', return_value=1):
        observe('a', 'pie')
    with patch.object(binding.time, 'time', return_value=2):
        observe('b', 'runtime')
        observe('b')
    assert binding._discovered_ue['b']['context'] == 'runtime'
    with patch.object(binding.time, 'time', return_value=3):
        observe('c', 'editor')
    assert set(binding._discovered_ue) == {'b', 'c'}
    with patch.object(binding.time, 'time', return_value=1000):
        observe('d')
    assert set(binding._discovered_ue) == {'d'}
