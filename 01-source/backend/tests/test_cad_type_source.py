import ezdxf
import cad_type_source
import parser_dxf


def drawing(tmp_path):
    doc = ezdxf.new('R2013')
    doc.units = 4
    block = doc.blocks.new('设备A')
    block.add_line((0, 0), (20, 10))
    for _ in range(8):
        insert = doc.modelspace().add_blockref('设备A', (0, 0), dxfattribs={'layer': '设备'})
        insert.add_attrib('编号', '设备01', insert=(5, 5), dxfattribs={'height': 0.1})
    doc.modelspace().add_blockref('设备A', (0, 0), dxfattribs={'layer': '备用'})
    doc.layout().add_blockref('设备A', (0, 0))
    hidden = doc.blocks.new('A$C_filtered')
    hidden.add_line((0, 0), (5, 5))
    doc.modelspace().add_blockref('A$C_filtered', (0, 0))
    path = tmp_path / 'types.dxf'
    doc.saveas(path)
    return path


def test_streaming_preserves_identity_units_and_modelspace(tmp_path, monkeypatch):
    path = drawing(tmp_path)
    full = parser_dxf.extract_block_candidates(path)
    assert full['candidates'][0]['cad_size_cm'] == {'x': 2.0, 'y': 1.0}
    monkeypatch.setattr(cad_type_source, 'LARGE_DRAWING_BYTES', 0)
    def forbidden(*args, **kwargs):
        raise AssertionError('Large type scans must not load full document or expand geometry')
    monkeypatch.setattr(cad_type_source.ezdxf, 'readfile', forbidden)
    monkeypatch.setattr(parser_dxf.bbox, 'extents', forbidden)
    streamed = parser_dxf.extract_block_candidates(path)
    assert streamed['summary'] == full['summary']
    assert streamed['filtered_log'] == full['filtered_log']
    assert streamed['size_scan_mode'] == 'identity_only'
    expected = dict(full['candidates'][0], cad_size=None, cad_size_cm=None)
    assert streamed['candidates'] == [expected]
    assert expected['count'] == 9
    assert expected['primary_layer'] == '设备'


def test_geometry_attempts_bounded_and_filtered_blocks_skipped(tmp_path, monkeypatch):
    path = drawing(tmp_path)
    attempts = []
    def broken(entities, **kwargs):
        attempts.append(entities[0].dxf.name)
        raise ValueError('broken geometry')
    monkeypatch.setattr(parser_dxf.bbox, 'extents', broken)
    result = parser_dxf.extract_block_candidates(path)
    assert attempts == ['设备A'] * 5
    assert result['candidates'][0]['cad_size'] is None
    assert result['candidates'][0]['count'] == 9
