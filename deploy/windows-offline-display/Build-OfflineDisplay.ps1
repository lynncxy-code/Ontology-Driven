[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RuntimeDirectory,
    [Parameter(Mandatory = $true)][string]$RuntimePackDirectory,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$ProjectPath = 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$runtime = [IO.Path]::GetFullPath($RuntimeDirectory)
$pack = [IO.Path]::GetFullPath($RuntimePackDirectory)
$output = [IO.Path]::GetFullPath($OutputDirectory)
$project = [IO.Path]::GetFullPath($ProjectPath)

if ($project -ne 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject') {
    throw "Offline display builds are locked to ZHHZ_NEW.uproject: $project"
}
foreach ($required in @(
    $project,
    (Join-Path $runtime 'ZHHZ_NEW.exe'),
    (Join-Path $runtime 'ZHHZ_NEW\Content\Paks'),
    (Join-Path $pack 'runtime-pack.json'),
    (Join-Path $pack 'snapshots.json'),
    (Join-Path $pack 'scene-runtime.json'),
    (Join-Path $pack 'web-runtime.json')
)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required input is missing: $required" }
}

$identity = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $pack 'runtime-pack.json') | ConvertFrom-Json
if ($identity.ue_project_id -ne 'ueproj_ZHHZ_NEW' -or $identity.ue_project_name -ne 'ZHHZ_NEW') {
    throw "RuntimePack identity is not ZHHZ_NEW."
}
if ($identity.project_id -ne 'ds_1787305683288') {
    throw "RuntimePack dataset is not the approved ZHHZ_NEW dataset: $($identity.project_id)"
}

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$runtimeOutput = Join-Path $output 'ZHHZ_NEW'
Copy-Item -LiteralPath $runtime -Destination $runtimeOutput -Recurse -Force
Copy-Item -LiteralPath $pack -Destination (Join-Path $output 'RuntimePack') -Recurse -Force

$hostProject = Join-Path $PSScriptRoot 'OfflineDisplayHost\OfflineDisplayHost.csproj'
$hostIcon = Join-Path $PSScriptRoot '..\windows-all-in-one\launcher\OntoTwin.ZHHZ.Launcher\LingYunZhi.ico'
$hostSourceIcon = Join-Path $PSScriptRoot 'OfflineDisplayHost\LingYunZhi.ico'
Copy-Item -LiteralPath $hostIcon -Destination $hostSourceIcon -Force
$publish = Join-Path $output '.host-publish'
dotnet publish $hostProject -c Release -r win-x64 --self-contained true -o $publish
if ($LASTEXITCODE -ne 0) { throw "Offline host publish failed with exit code $LASTEXITCODE" }
Move-Item -LiteralPath (Join-Path $publish 'LingYunZhi-Offline.exe') -Destination (Join-Path $output '灵云智离线展示.exe')
Remove-Item -LiteralPath $publish -Recurse -Force

$readme = @'
灵云智离线展示版

双击“灵云智离线展示.exe”即可运行。
无需安装 OntoTwin、数据库、Docker、WSL2 或 Hyper-V。

快捷键：
F7  进入或退出人物漫游
WASD 移动
V   切换视角
Tab 打开漫游面板

说明：
本版本为只读展示版。配置来自打包时已发布的 ZHHZ_NEW 数据快照，运行时不会连接或修改数据库。
'@
[IO.File]::WriteAllText((Join-Path $output '使用说明.txt'), $readme, [Text.UTF8Encoding]::new($true))

$files = @(Get-ChildItem -LiteralPath $output -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($output.Length + 1).Replace('\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$manifest = [ordered]@{
    schema_version = 1
    product = 'LingYunZhi ZHHZ_NEW Offline Display'
    generated_at = (Get-Date).ToString('o')
    source_project = $project
    project_id = $identity.project_id
    ue_project_id = $identity.ue_project_id
    snapshot_count = $identity.snapshot_count
    render_part_count = $identity.render_part_count
    roaming_enabled = $identity.roaming_enabled
    requires_ontotwin = $false
    requires_database = $false
    requires_hyperv = $false
    files = $files
}
[IO.File]::WriteAllText(
    (Join-Path $output 'offline-release-manifest.json'),
    ($manifest | ConvertTo-Json -Depth 6),
    [Text.UTF8Encoding]::new($false))

Write-Host "Offline display created: $output" -ForegroundColor Green
