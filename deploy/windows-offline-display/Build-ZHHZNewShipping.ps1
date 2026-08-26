[CmdletBinding()]
param(
    [string]$ProjectPath = 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject',
    [string]$EngineRoot = 'D:\UE_5.6',
    [Parameter(Mandatory = $true)][string]$RuntimePackDirectory,
    [Parameter(Mandatory = $true)][string]$ArchiveDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$project = [IO.Path]::GetFullPath($ProjectPath)
$engine = [IO.Path]::GetFullPath($EngineRoot)
$pack = [IO.Path]::GetFullPath($RuntimePackDirectory)
$archive = [IO.Path]::GetFullPath($ArchiveDirectory)
$lockedProject = 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject'
if ($project -ne $lockedProject) {
    throw "This builder is identity-locked to $lockedProject. Got: $project"
}
if ((Split-Path -Leaf $project) -ne 'ZHHZ_NEW.uproject') {
    throw "Project identity mismatch: $project"
}

$identity = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $pack 'runtime-pack.json') | ConvertFrom-Json
if ($identity.ue_project_id -ne 'ueproj_ZHHZ_NEW' -or
    $identity.ue_project_name -ne 'ZHHZ_NEW' -or
    $identity.project_id -ne 'ds_1787305683288') {
    throw 'RuntimePack identity does not match ZHHZ_NEW / ds_1787305683288.'
}

$projectRoot = Split-Path -Parent $project
$sourceVideos = @(
    (Join-Path $projectRoot 'Content\Movies\MainScreen_H.mp4'),
    (Join-Path $projectRoot 'Content\Movies\MainScreen_V.mp4')
)
$sourceVideoAssets = @(
    'FMS_MainScreen_H',
    'FMS_MainScreen_V',
    'LS_MainScreenVideoLoop',
    'M_MainScreenVideo',
    'MI_MainScreen_H',
    'MI_MainScreen_V',
    'MP_MainScreen_H',
    'MP_MainScreen_V',
    'MT_MainScreen_H',
    'MT_MainScreen_V'
) | ForEach-Object { Join-Path $projectRoot "Content\MainScreenVideo\$_.uasset" }
$sourceVideoPlugin = Join-Path $projectRoot 'Plugins\MainScreenVideoRuntime\MainScreenVideoRuntime.uplugin'
foreach ($requiredVideoSource in @($sourceVideos + $sourceVideoAssets + $sourceVideoPlugin)) {
    if (-not (Test-Path -LiteralPath $requiredVideoSource -PathType Leaf)) {
        throw "Main-screen video source is missing: $requiredVideoSource"
    }
}
foreach ($sourceVideo in $sourceVideos) {
    if ((Get-Item -LiteralPath $sourceVideo).Length -lt 1MB) {
        throw "Main-screen video source is unexpectedly small: $sourceVideo"
    }
}
$gameConfig = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $projectRoot 'Config\DefaultGame.ini')
foreach ($requiredConfig in @(
    'DirectoriesToAlwaysCook=(Path="/Game/MainScreenVideo")',
    'bSkipMovies=False'
)) {
    if ($gameConfig -notlike "*$requiredConfig*") {
        throw "Main-screen video packaging setting is missing: $requiredConfig"
    }
}

$targetProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^UnrealEditor(?:-Cmd)?\.exe$' -and
    [string]$_.CommandLine -like '*D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject*'
})
if ($targetProcesses.Count -gt 0) {
    throw "ZHHZ_NEW is still open in Unreal Editor (PID $($targetProcesses.ProcessId -join ', ')). Save and close it before packaging."
}

$uat = Join-Path $engine 'Engine\Build\BatchFiles\RunUAT.bat'
if (-not (Test-Path -LiteralPath $uat -PathType Leaf)) { throw "RunUAT not found: $uat" }
if (Test-Path -LiteralPath $archive) {
    if (@(Get-ChildItem -LiteralPath $archive -Force).Count -gt 0) {
        throw "ArchiveDirectory must be empty: $archive"
    }
} else {
    New-Item -ItemType Directory -Path $archive | Out-Null
}

$arguments = @(
    'BuildCookRun',
    "-project=$project",
    '-target=ZHHZ_NEW',
    '-noP4',
    '-platform=Win64',
    '-clientconfig=Shipping',
    '-build',
    '-cook',
    '-stage',
    '-pak',
    '-iostore',
    '-prereqs',
    '-archive',
    "-archivedirectory=$archive",
    '-unattended',
    '-utf8output'
)
$log = Join-Path $archive 'ZHHZ_NEW-UAT-build.log'
& $uat @arguments 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { throw "ZHHZ_NEW BuildCookRun failed with exit code $LASTEXITCODE" }

$runtime = Join-Path $archive 'Windows'
$exe = Join-Path $runtime 'ZHHZ_NEW.exe'
$ufs = Join-Path $runtime 'Manifest_UFSFiles_Win64.txt'
$nonUfs = Join-Path $runtime 'Manifest_NonUFSFiles_Win64.txt'
foreach ($required in @($exe, $ufs, $nonUfs, (Join-Path $runtime 'ZHHZ_NEW\Content\Paks'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Shipping output is incomplete: $required" }
}
$manifestText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ufs
if ($manifestText -match '(?i)(^|[/\\])(test0316|tmp_ue)([/\\]|$)') {
    throw 'Shipping output contains a forbidden test-project identity.'
}
if ($manifestText -notmatch '(?im)^ZHHZ_NEW[/\\]ZHHZ_NEW\.uproject(?:\s|$)') {
    throw 'Shipping manifest does not contain ZHHZ_NEW.uproject.'
}
if ($manifestText -notmatch '(?im)^ZHHZ_NEW[/\\]Plugins[/\\]OntoTwinSync[/\\]OntoTwinSync\.uplugin(?:\s|$)') {
    throw 'Shipping manifest does not contain OntoTwinSync.'
}

$snapshots = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $pack 'snapshots.json') | ConvertFrom-Json
$assetPaths = @($snapshots | ForEach-Object {
    @($_.interfaces.I3D_Representable.render_parts) | ForEach-Object { [string]$_.asset_path }
} | Where-Object { $_ -like '/Game/*' } | Sort-Object -Unique)
$materialPaths = @($snapshots | ForEach-Object {
    @($_.interfaces.I3D_Representable.render_parts) | ForEach-Object {
        @($_.material_paths) | ForEach-Object { [string]$_ }
    }
} | Where-Object { $_ -like '/Game/*' } | Sort-Object -Unique)
$requiredPackagePaths = @(($assetPaths + $materialPaths) | Sort-Object -Unique)
$missingSource = @()
foreach ($requiredPath in $requiredPackagePaths) {
    $packagePath = ($requiredPath -split '\.', 2)[0]
    $source = Join-Path $projectRoot ('Content\' + $packagePath.Substring(6).Replace('/', '\') + '.uasset')
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { $missingSource += $requiredPath }
}
if ($missingSource.Count -gt 0) {
    throw "RuntimePack references $($missingSource.Count) missing source assets. First: $($missingSource[0])"
}

$packagedPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($line in [IO.File]::ReadLines($ufs, [Text.UTF8Encoding]::new($false))) {
    $path = ($line -split "`t", 2)[0].Replace('\', '/')
    if ($path) { [void]$packagedPaths.Add($path) }
}
$packagedNonUfsPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($line in [IO.File]::ReadLines($nonUfs, [Text.UTF8Encoding]::new($false))) {
    $path = ($line -split "`t", 2)[0].Replace('\', '/')
    if ($path) { [void]$packagedNonUfsPaths.Add($path) }
}
$missingCooked = @()
foreach ($requiredPath in $requiredPackagePaths) {
    $packagePath = ($requiredPath -split '\.', 2)[0]
    $expected = 'ZHHZ_NEW/Content/' + $packagePath.Substring(6) + '.uasset'
    if (-not $packagedPaths.Contains($expected)) { $missingCooked += $expected }
}
$requiredVideoUfs = @(
    'ZHHZ_NEW/Plugins/MainScreenVideoRuntime/MainScreenVideoRuntime.uplugin',
    'Engine/Plugins/Media/WmfMedia/WmfMedia.uplugin',
    'Engine/Plugins/Media/MediaCompositing/MediaCompositing.uplugin',
    'ZHHZ_NEW/Content/MainScreenVideo/FMS_MainScreen_H.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/FMS_MainScreen_V.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/LS_MainScreenVideoLoop.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/M_MainScreenVideo.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MI_MainScreen_H.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MI_MainScreen_V.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MP_MainScreen_H.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MP_MainScreen_V.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MT_MainScreen_H.uasset',
    'ZHHZ_NEW/Content/MainScreenVideo/MT_MainScreen_V.uasset',
    'ZHHZ_NEW/Content/AVIC_Show/Art/Material_Renew/MI/MI_OP_LED屏_吊装长方形主屏幕.uasset'
)
$requiredVideoNonUfs = @(
    'ZHHZ_NEW/Content/Movies/MainScreen_H.mp4',
    'ZHHZ_NEW/Content/Movies/MainScreen_V.mp4'
)
$missingVideoUfs = @($requiredVideoUfs | Where-Object { -not $packagedPaths.Contains($_) })
$missingVideoNonUfs = @($requiredVideoNonUfs | Where-Object { -not $packagedNonUfsPaths.Contains($_) })
$videoHashMismatches = @()
foreach ($sourceVideo in $sourceVideos) {
    $stagedVideo = Join-Path $runtime ('ZHHZ_NEW\Content\Movies\' + (Split-Path -Leaf $sourceVideo))
    if (-not (Test-Path -LiteralPath $stagedVideo -PathType Leaf)) {
        $videoHashMismatches += "missing:$stagedVideo"
        continue
    }
    $sourceHash = (Get-FileHash -LiteralPath $sourceVideo -Algorithm SHA256).Hash
    $stagedHash = (Get-FileHash -LiteralPath $stagedVideo -Algorithm SHA256).Hash
    if ($sourceHash -ne $stagedHash) {
        $videoHashMismatches += "hash:$stagedVideo"
    }
}
$audit = [ordered]@{
    schema_version = 1
    source_project = $project
    project_id = $identity.project_id
    ue_project_id = $identity.ue_project_id
    snapshot_count = $identity.snapshot_count
    render_part_count = $identity.render_part_count
    required_asset_count = $assetPaths.Count
    required_material_count = $materialPaths.Count
    required_package_count = $requiredPackagePaths.Count
    missing_source_count = $missingSource.Count
    missing_cooked_count = $missingCooked.Count
    missing_cooked = $missingCooked
    main_screen_video = [ordered]@{
        source_files = @($sourceVideos | ForEach-Object {
            [ordered]@{
                name = Split-Path -Leaf $_
                bytes = (Get-Item -LiteralPath $_).Length
                sha256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        })
        missing_ufs = $missingVideoUfs
        missing_non_ufs = $missingVideoNonUfs
        hash_mismatches = $videoHashMismatches
    }
    generated_at = (Get-Date).ToString('o')
}
[IO.File]::WriteAllText(
    (Join-Path $runtime 'offline-cook-audit.json'),
    ($audit | ConvertTo-Json -Depth 5),
    [Text.UTF8Encoding]::new($false))
if ($missingCooked.Count -gt 0) {
    throw "Cook audit failed: $($missingCooked.Count) RuntimePack assets are absent from Shipping. First: $($missingCooked[0])"
}
if ($missingVideoUfs.Count -gt 0 -or $missingVideoNonUfs.Count -gt 0 -or $videoHashMismatches.Count -gt 0) {
    throw "Main-screen video audit failed: missing UFS=$($missingVideoUfs.Count), missing NonUFS=$($missingVideoNonUfs.Count), hash mismatches=$($videoHashMismatches.Count)."
}

$runtimeManifest = [ordered]@{
    schema_version = 1
    project_name = 'ZHHZ_NEW'
    target_name = 'ZHHZ_NEW'
    source_project_path = $project
    source_project_sha256 = (Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash.ToLowerInvariant()
    project_id = $identity.project_id
    ue_project_id = $identity.ue_project_id
    uat_log_sha256 = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash.ToLowerInvariant()
    generated_at = (Get-Date).ToString('o')
}
[IO.File]::WriteAllText(
    (Join-Path $runtime 'offline-runtime-manifest.json'),
    ($runtimeManifest | ConvertTo-Json -Depth 4),
    [Text.UTF8Encoding]::new($false))

Write-Host "ZHHZ_NEW Shipping runtime created: $runtime" -ForegroundColor Green
