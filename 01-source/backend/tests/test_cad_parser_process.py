"""Large CAD must use an isolated process; failed preview must not replace a frame."""
import io
import ast
import json
import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import Flask, jsonify, request
from spatial_assets.cad_parser import parse_cad
from spatial_assets.validators import SpatialFrameValidationError
from spatial_assets.api import register_spatial_asset_routes
from .test_spatial_assets import minimal_dxf


def test_preview_endpoint_uses_bounded_parser():
    source=Path(__file__).parents[1]/'app.py'
    function=next(n for n in ast.parse(source.read_text(encoding='utf-8')).body
                  if isinstance(n,ast.FunctionDef) and n.name=='coord_preview')
    app=Flask(__name__)
    from unittest.mock import Mock
    parser=Mock(return_value={'layers':[]})
    scope={'app':app,'request':request,'jsonify':jsonify,'os':os,'tempfile':tempfile,
           'parse_cad':parser,'SpatialFrameValidationError':SpatialFrameValidationError}
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),scope)
    response=app.test_client().post('/api/v2/coord/preview',data={'file':(io.BytesIO(minimal_dxf()),'test.dxf')})
    assert response.status_code==200
    assert parser.call_args.args[1]=='preview'
    assert not os.path.exists(parser.call_args.args[0])


def test_large_parse_uses_bounded_child_and_handles_timeout(tmp_path):
    source = tmp_path / 'test.dxf'
    source.write_bytes(minimal_dxf())
    def run(command, **kwargs):
        assert command[-1] == 'types'
        assert kwargs['timeout'] == 900
        Path(command[3]).write_text(json.dumps({'candidates': []}), encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)
    with patch('spatial_assets.cad_parser.os.path.getsize', return_value=342*1024*1024):
        with patch('spatial_assets.cad_parser.subprocess.run', side_effect=run) as child:
            assert parse_cad(source, 'types') == {'candidates': []}
            assert child.call_count == 1
        with patch('spatial_assets.cad_parser.subprocess.run', side_effect=subprocess.TimeoutExpired('worker', 900)):
            with pytest.raises(SpatialFrameValidationError, match='超时'):
                parse_cad(source, 'types')


def test_real_child_process_roundtrip(tmp_path):
    source = tmp_path / 'worker.dxf'
    source.write_bytes(minimal_dxf())
    # Force the large-file branch, but run the real child interpreter/parser.
    with patch('spatial_assets.cad_parser.os.path.getsize', return_value=33*1024*1024):
        result = parse_cad(source, 'types')
    assert isinstance(result['candidates'], list)


def test_replace_preview_failure_is_atomic_and_success_returns_preview(store, tmp_path):
    app = Flask(__name__)
    register_spatial_asset_routes(app, store, str(tmp_path / 'assets'))
    client = app.test_client()
    frame = client.post('/api/v2/spatial-frames/cad-assets', data={
        'file':(io.BytesIO(minimal_dxf()),'a.dxf')}).json['frame']
    before = store.get_active_copy()
    def replace():
        return client.post('/api/v2/spatial-frames/cad-assets', data={
            'file':(io.BytesIO(minimal_dxf()), 'b.dxf'), 'update_frame_id':frame['id'],
            'expected_project_id':'p_test','expected_draft_revision':'0', 'include_preview':'1'})
    with patch('spatial_assets.service.parse_cad', return_value={'error':'bad DXF'}):
        assert replace().status_code == 422
    assert store.get_active_copy() == before
    with patch('spatial_assets.service.parse_cad', return_value={'layers':[]}) as parser:
        result = replace()
        assert result.status_code == 201
        assert result.json['preview'] == {'layers':[]}
        assert parser.call_count == 1
    assert store.get_active_copy()['frames'][0]['draft_revision'] == 1
    assert 'preview' not in store.get_active_copy()['frames'][0]
