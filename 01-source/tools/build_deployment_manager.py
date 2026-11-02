"""Build the standalone OntoTwin deployment manager from a clean checkpoint."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    def git(*values):
        return subprocess.check_output(['git', *values], cwd=ROOT, text=True, encoding='utf-8').strip()
    if git('status', '--porcelain'):
        raise SystemExit('Commit the reviewed source before building the manager.')
    output = args.output.absolute()
    archive = output.with_suffix('.zip')
    if output.exists() or archive.exists():
        raise SystemExit('Use a new output name; existing artifacts are immutable.')
    shutil.copytree(ROOT / '01-source/tools/deployment', output,
                    ignore=shutil.ignore_patterns('__pycache__', 'test_*.py', 'acceptance.py'))
    (output / 'manager-release.json').write_text(json.dumps({
        'product': 'OntoTwin Deployment Manager', 'version': '0.1.0', 'status': 'release-candidate',
        'source_commit': git('rev-parse', 'HEAD'), 'generated_at': datetime.now(timezone.utc).isoformat(),
        'ue_version': '5.6', 'update_input': 'full-integration-zip', 'database_upgrade': 'identical-schema-only',
        'contains_customer_data': False}, ensure_ascii=False, indent=2), encoding='utf-8')
    checks = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in output.rglob('*') if p.is_file()}
    (output / 'SHA256SUMS.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for p in output.rglob('*'):
            if p.is_file(): zipped.write(p, p.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        for name, expected in checks.items():
            assert hashlib.sha256(zipped.read(name)).hexdigest() == expected, name
    value = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(value + '  ' + archive.name + '\n', encoding='ascii')
    print(json.dumps({'package': str(archive), 'sha256': value, 'source_commit': git('rev-parse', 'HEAD')}))


if __name__ == '__main__': main()
