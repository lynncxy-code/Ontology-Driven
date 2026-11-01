"""Execute the real launcher under Windows PowerShell 5.1 and pwsh; no live Docker writes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

TEMPLATES = Path(__file__).resolve().parents[1] / 'integration'
SHELLS = [str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'), shutil.which('pwsh')]

FAKE = r'''
using System; using System.IO; using System.Linq;
class Docker {
 static int Main(string[] a) {
  string root=Environment.GetEnvironmentVariable("FAKE_DOCKER_ROOT"), cmd=String.Join(" ",a);
  File.AppendAllText(Path.Combine(root,"calls.txt"), cmd+"\n");
  if(a[0]=="info") {Console.WriteLine("linux");return 0;}
  if(a[0]=="compose") {
   if(a.Contains("version")) {Console.WriteLine("2.40.0"); return 0;}
   if(a.Contains("up")) {File.WriteAllText(Path.Combine(root,"up"),"yes");return 0;}
   return 0;
  }
  if(a[0]=="load") {File.WriteAllText(Path.Combine(root,"loaded"),"yes");return 0;}
  if(a[0]=="image") {
   if(!File.Exists(Path.Combine(root,"loaded"))) {Console.Error.WriteLine("Error: No such image: "+a[2]);return 1;}
   Console.WriteLine("sha256:test");return 0;
  }
  if(a[0]=="volume") {
   if(File.Exists(Path.Combine(root,"foreign"))) {Console.WriteLine("[{\"Labels\":{\"ontotwin.instance\":\"someone-else\"}}]");return 0;}
   Console.Error.WriteLine("Error: No such volume: "+a[2]);return 1;
  }
  return 9;
 }
}'''


@pytest.fixture(scope='module')
def fake_docker(tmp_path_factory):
    root = tmp_path_factory.mktemp('native docker')
    src = root/'Docker.cs'
    src.write_text(FAKE)
    csc = Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    subprocess.run([str(csc),'/nologo',f'/out:{root / "docker.exe"}',str(src)],check=True,capture_output=True)
    return root


@pytest.fixture(params=[s for s in SHELLS if s and Path(s).exists()], ids=lambda s: Path(s).name)
def launcher(tmp_path, fake_docker, request):
    root = tmp_path/'package with spaces'
    shutil.copytree(TEMPLATES, root/'Tools')
    (root/'Runtime').mkdir()
    (root/'Runtime/images.tar').write_bytes(b'test offline image archive')
    shutil.copy2(TEMPLATES/'compose.yaml',root/'Runtime/compose.yaml')
    manifest = {'source_commit':'test-commit','release_id':'test-release','images_archive_sha256':hashlib.sha256((root/'Runtime/images.tar').read_bytes()).hexdigest(),
                'images':{k:{'tag':k+':test','id':'sha256:test'} for k in ['backend','db','neo4j']}}
    (root/'manifest.json').write_text(json.dumps(manifest))
    # Production bundle writes a BOM, required for Chinese strings on PS5.1.
    for p in (root/'Tools').glob('*.ps1'): p.write_text(p.read_text('utf-8-sig'),encoding='utf-8-sig')
    def run(action='start', port=54321):
        harness = root/'run.ps1'
        harness.write_text("$ErrorActionPreference='Stop'\nfunction Invoke-RestMethod { if(Test-Path (Join-Path $env:FAKE_DOCKER_ROOT 'up')) {return @{ok=$true;release_id='test-release'}}; throw 'not started' }\n"
                           +f"& '{root / 'Tools/Backend.ps1'}' -Action {action} -Port {port} -NoBrowser\n",encoding='utf-8-sig')
        env = dict(os.environ, PATH=str(fake_docker)+os.pathsep+os.environ['PATH'],FAKE_DOCKER_ROOT=str(root))
        env.pop('PSModulePath', None)  # Each shell loads its own bundled modules.
        return subprocess.run([request.param,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(harness)],env=env,capture_output=True,timeout=45)
    return root, run


def test_empty_machine_imports_then_starts_and_restarts(launcher):
    root, run = launcher
    first = run()
    assert first.returncode == 0, first.stderr.decode("utf-8", errors="replace")
    original = (root/'.runtime/instance.json').read_bytes()
    assert (root/'loaded').exists() and (root/'up').exists()
    assert run('stop').returncode == 0
    assert run().returncode == 0
    assert (root/'.runtime/instance.json').read_bytes() == original
    calls = (root/'calls.txt').read_text()
    assert calls.count('load -i ') == 1
    assert '--pull never' in calls and 'down' not in calls


def test_foreign_volume_prevents_start(launcher):
    root, run = launcher
    (root/'foreign').touch()
    assert run().returncode != 0
    assert 'volume inspect' in (root/'calls.txt').read_text()
    assert not (root/'up').exists()


def test_missing_credentials_does_not_regenerate(launcher):
    root, run = launcher
    assert run().returncode == 0
    original = (root/'.runtime/instance.json').read_bytes()
    (root/'.runtime/.env').unlink()
    assert run().returncode != 0
    assert not (root/'.runtime/.env').exists()
    assert (root/'.runtime/instance.json').read_bytes() == original


def test_occupied_port_stops_before_import(launcher):
    root, run = launcher
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); s.listen()
        assert run(port=s.getsockname()[1]).returncode != 0
    assert not (root/'loaded').exists()
    assert not (root/'up').exists()


def test_tampered_archive_prevents_import(launcher):
    root, run = launcher
    (root/'Runtime/images.tar').write_bytes(b'corrupt')
    assert run().returncode != 0
    assert not (root/'loaded').exists()


def test_page_integrity_matches_shipped_vendor():
    import base64, re
    frontend=TEMPLATES.parents[1]/'frontend'
    for name in ['instance.html','ontology.html']:
        html=(frontend/name).read_text('utf-8')
        tags=re.findall(r'<script[^>]+src="(/vendor/(?:vue|axios)[^"]+)"[^>]+>',html)
        assert len(tags)==2
        for path in tags:
            actual='sha384-'+base64.b64encode(hashlib.sha384((frontend/path.lstrip('/')).read_bytes()).digest()).decode()
            assert f'integrity="{actual}"' in html


@pytest.mark.parametrize('case,expected', [('target',1),('shared_dll',1),('other',0)])
@pytest.mark.parametrize('shell',[s for s in SHELLS if s and Path(s).exists()])
def test_only_idle_target_can_be_installed(tmp_path,case,expected,shell):
    helper=TEMPLATES.parents[1]/'scripts/assert_ontotwin_project_idle.ps1'
    script=tmp_path/'guard.ps1'
    command='UnrealEditor.exe D:/target/Test.uproject' if case=='target' else 'UnrealEditor.exe D:/other/Other.uproject'
    module='D:/target/Plugins/a.dll' if case=='shared_dll' else 'D:/other/Plugins/a.dll'
    script.write_text("$ErrorActionPreference='Stop'\n"+helper.read_text('utf-8')+
        f"\nfunction Get-CimInstance {{ return [pscustomobject]@{{ProcessId=123;CommandLine='{command}'}} }}\n"
        +f"function Get-Process {{ return [pscustomobject]@{{Modules=@([pscustomobject]@{{FileName='{module}'}})}} }}\n"
        +"Assert-OntoTwinProjectIdle 'D:\\target\\Test.uproject'\n",encoding='utf-8-sig')
    result=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],capture_output=True,timeout=15)
    assert (result.returncode!=0)==bool(expected),result.stderr
