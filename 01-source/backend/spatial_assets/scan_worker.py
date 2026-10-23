"""Bounded subprocess for large CAD scans; writes only its caller's temp file."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parser_dxf import extract_block_candidates, extract_preview_data


def main():
    source, output, mapping_path, mode = sys.argv[1:]
    try:
        mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        mapping = {}
    result = (extract_preview_data(source) if mode == 'preview'
              else extract_block_candidates(source, mapping=mapping))
    Path(output).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
