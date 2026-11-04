"""Build a source-identifiable, offline UE5.6 integration candidate from a clean commit."""
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = Path(__file__).with_name('integration')


def run(*args):
    return subprocess.check_output(list(map(str, args)), cwd=REPO, text=True, encoding='utf-8').strip()


def digest(path):
    with path.open('rb') as stream:
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
        return value.hexdigest()


def source_hash(plugin):
    files = sorted([p for p in (plugin / 'Source').rglob('*') if p.is_file()] + list(plugin.glob('*.uplugin')),
                   key=lambda p: p.relative_to(plugin).as_posix())
    payload = ''.join(f'{p.relative_to(plugin).as_posix()}\0{digest(p)}\n' for p in files)
    return hashlib.sha256(payload.encode()).hexdigest()


def copy_plugin(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('Intermediate', 'Saved', 'DerivedDataCache',
        '.git', '.vs', '__pycache__', '*.pdb', '*.exp', '*.lib', '*.obj', '*.log'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8-sig' if path.suffix == '.ps1' else 'utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gltf-plugin', type=Path, required=True)
    parser.add_argument('--webui-plugin', type=Path, required=True)
    parser.add_argument('--package-version', help='Release version; unchanged plugins retain their own versions')
    parser.add_argument('--no-zip', action='store_true')
    args = parser.parse_args()
    if run('git', 'status', '--porcelain'):
        raise SystemExit('Working tree must be clean; commit reviewed source before packaging.')
    from check_frontend import validate
    validate(REPO / '01-source/frontend')
    commit = run('git', 'rev-parse', 'HEAD')
    plugin_root = REPO / '01-source/ue_project/Plugins'
    core = plugin_root / 'OntoTwinSync'
    version = args.package_version or json.loads((core/'OntoTwinSync.uplugin').read_text('utf-8'))['VersionName']
    import re
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.]+)?', version):
        raise SystemExit('Invalid package version')
    fingerprint = source_hash(core)
    binary = core/'Binaries/Win64/UnrealEditor-OntoTwinSync.dll'
    if not binary.exists() or not any(token in binary.read_bytes() for token in (fingerprint.encode(), fingerprint.encode('utf-16-le'))):
        raise SystemExit('UE editor DLL is absent or built from different source. Compile this checkout first.')
    sources = {name:plugin_root/name for name in ('OntoTwinSync','OntoTwinIndustrialBehavior','OntoTwinCharacterPack_Core')}
    sources.update(glTFRuntime=args.gltf_plugin.resolve(), WebUI=args.webui_plugin.resolve())
    for name, source in sources.items():
        if not (source/(name+'.uplugin')).is_file():
            raise SystemExit(f'Missing plugin dependency: {name}: {source}')
    webui_path_source=sources['WebUI']/'Source/WebBrowserUtils/Private/WebBrowserUtils.cpp'
    if 'FPaths::ConvertRelativePathToFull(Plugin->GetBaseDir())' not in webui_path_source.read_text('utf-8-sig'):
        raise SystemExit('WebUI must include the project-plugin path fix; the engine-only vendor build cannot be shipped in a project integration package.')
    for required in ('Binaries/Win64/TracerWebHelper.exe','Binaries/Win64/UnrealEditor-WebBrowserUtils.dll','Binaries/ThirdParty/CEF3/Win64/libcef.dll'):
        if not (sources['WebUI']/required).is_file():
            raise SystemExit(f'Missing WebUI runtime dependency: {required}')
    output = args.output.resolve()
    if output.exists() or (output.parent / (output.name + '.zip')).exists():
        raise SystemExit('Output already exists; use a new versioned directory.')
    output.mkdir(parents=True)
    (output/'Runtime').mkdir()
    release = f'{version}-{commit[:12]}'
    images = {'backend':f'ontotwin-integration/backend:{release}', 'db':f'ontotwin-integration/db:{release}', 'neo4j':'neo4j:5'}
    for key, dockerfile in [('backend','Dockerfile.4.8-rc'), ('db','Dockerfile.4.8-rc-db')]:
        subprocess.run(['docker','build','-f',dockerfile,'--label',f'org.opencontainers.image.revision={commit}',
            '--label',f'org.opencontainers.image.version={version}','-t',images[key],'.'],cwd=REPO,check=True)
    metadata={k:{'tag':v,'id':run('docker','image','inspect',v,'--format','{{.Id}}')} for k,v in images.items()}
    subprocess.run(['docker','save','-o',str(output/'Runtime/images.tar'),*images.values()],check=True)
    for name, source in sources.items():
        copy_plugin(source, output/'Plugins'/name)
    for name in ('Backend.ps1','DockerCommand.ps1','Install-OntoTwinPlugin.ps1'):
        write(output/'Tools'/name,(TEMPLATES/name).read_text('utf-8'))
    shutil.copy2(TEMPLATES/'compose.yaml', output/'Runtime/compose.yaml')
    for action in ('Start','Stop','Check'):
        write(output/'Tools'/f'{action}-OntoTwinBackend.ps1',f"[CmdletBinding()]\nparam([int]$Port=5000,[switch]$NoBrowser)\n$options=@{{Action='{action.lower()}';NoBrowser=$NoBrowser}}\nif ($PSBoundParameters.ContainsKey('Port')) {{ $options.Port=$Port }}\n& (Join-Path $PSScriptRoot 'Backend.ps1') @options\n")
    for label, action in [('启动后台','Start'),('停止后台','Stop'),('检查后台','Check')]:
        # ASCII content; Chinese only in the filename, so cmd's codepage is irrelevant.
        (output/(label+'.cmd')).write_bytes((f'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tools\\{action}-OntoTwinBackend.ps1"\r\nif errorlevel 1 (pause & exit /b 1)\r\npause\r\n').encode('ascii'))
    shutil.copy2(REPO/'01-source/scripts/install_ontotwin_character_pack_core.ps1',output/'Tools/install_ontotwin_character_pack_core.ps1')
    write(output/'Tools/assert_ontotwin_project_idle.ps1',(REPO/'01-source/scripts/assert_ontotwin_project_idle.ps1').read_text('utf-8'))
    write(output/'Tools/Install-CoreCharacters.ps1', "[CmdletBinding()]\nparam([Parameter(Mandatory=$true)][string]$ProjectPath)\n& (Join-Path $PSScriptRoot 'install_ontotwin_character_pack_core.ps1') -ProjectPath $ProjectPath -SourcePluginPath (Join-Path $PSScriptRoot '../Plugins/OntoTwinCharacterPack_Core')\n")
    from build_ontotwin_integration_package import REWASH_DOC, SKILL_PATCH
    write(output/'Docs/UE资产回洗流程.md',REWASH_DOC)
    write(output/'Skill-Patch/UE超级管家-接入模式补充.md',SKILL_PATCH)
    shutil.copy2(TEMPLATES/'README.md',output/'README.md')
    deployment = REPO/'01-source/tools/deployment'
    shutil.copytree(deployment, output/'Tools/Deployment', ignore=shutil.ignore_patterns('__pycache__','test_*.py','acceptance.py'))
    (output/'部署管理.cmd').write_bytes(b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tools\\Deployment\\Launch-Manager.ps1"\r\nif errorlevel 1 pause\r\n')
    manifest={'package_version':version,'release_id':release,'source_commit':commit,
        'generated_at':datetime.now(timezone.utc).isoformat(),'contains_ue_project':False,
        'contains_customer_data':False,'status':'release-candidate','ue_version':'5.6',
        'plugin_source_hash':fingerprint,'images':metadata,'images_archive_sha256':digest(output/'Runtime/images.tar'),
        'plugins':{name:{'source_hash':source_hash(source),'version':json.loads((source/(name+'.uplugin')).read_text('utf-8-sig')).get('VersionName')} for name,source in sources.items()},
        'deployment_manager': {'version': '0.1.0', 'update_input': 'full-integration-zip', 'schema_upgrade': 'identical-only'}}
    write(output/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    checksums={p.relative_to(output).as_posix():digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    write(output/'SHA256SUMS.json',json.dumps(checksums,ensure_ascii=False,indent=2)+'\n')
    if not args.no_zip:
        zip_path=output.parent / (output.name + '.zip')
        with ZipFile(zip_path,'w',ZIP_DEFLATED,compresslevel=5,allowZip64=True) as archive:
            for p in sorted(output.rglob('*')):
                if p.is_file(): archive.write(p,p.relative_to(output).as_posix())
        write(zip_path.with_suffix('.zip.sha256'),digest(zip_path)+'  '+zip_path.name+'\n')
    print(json.dumps({'directory':str(output),'release_id':release,'source_commit':commit},ensure_ascii=True))


if __name__ == '__main__':
    main()
