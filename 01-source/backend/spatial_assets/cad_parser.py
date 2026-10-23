"""Bounded CAD parsing, without a worker service or new dependencies."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

from .validators import SpatialFrameValidationError

_PARSE_LOCK = threading.RLock()

def parse_cad(path, mode, mapping=None):
    # One parser per Flask process across preview, replacement and type scan.
    # Waiting releases the GIL; request threads serving UE snapshots stay free.
    with _PARSE_LOCK:
        return _parse_cad_locked(path, mode, mapping)


def _parse_cad_locked(path, mode, mapping=None):
    if os.path.getsize(path) < 32 * 1024 * 1024:
        from parser_dxf import extract_block_candidates, extract_preview_data
        return (extract_preview_data(path) if mode == 'preview'
                else extract_block_candidates(path, mapping=mapping or {}))
    with tempfile.TemporaryDirectory(prefix='ontotwin-cad-parse-') as temp:
        output, mapping_path = Path(temp) / 'result.json', Path(temp) / 'mapping.json'
        mapping_path.write_text(json.dumps(mapping or {}), encoding='utf-8')
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('scan_worker.py')),
                                     str(path), str(output), str(mapping_path), mode],
                                    capture_output=True, timeout=900)
            if result.returncode:
                raise SpatialFrameValidationError('cad_parse_failed', 'CAD 解析失败，请检查图纸后重试')
            return json.loads(output.read_text(encoding='utf-8'))
        except subprocess.TimeoutExpired:
            raise SpatialFrameValidationError('cad_parse_timeout', 'CAD 解析超时，请拆分图纸后重试')
