[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $true)]
    [string]$EngineRoot,

    [Parameter(Mandatory = $true)]
    [string]$ArchiveDirectory,

    [string]$TargetName = "ZHHZ",
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$project = [System.IO.Path]::GetFullPath($ProjectPath)
$engine = [System.IO.Path]::GetFullPath($EngineRoot)
$archive = [System.IO.Path]::GetFullPath($ArchiveDirectory)
$uat = Join-Path $engine "Engine\Build\BatchFiles\RunUAT.bat"
$projectName = [System.IO.Path]::GetFileNameWithoutExtension($project)

if (-not (Test-Path -LiteralPath $project -PathType Leaf)) {
    throw "Unreal project was not found: $project"
}
if ($projectName -ne $TargetName) {
    throw "Unreal project identity mismatch: project '$projectName' cannot be packaged as target '$TargetName'. Select the intended .uproject instead of renaming its executable."
}
if (-not (Test-Path -LiteralPath $uat -PathType Leaf)) {
    throw "RunUAT.bat was not found: $uat"
}
if (Test-Path -LiteralPath $archive) {
    if (@(Get-ChildItem -LiteralPath $archive -Force).Count -gt 0) {
        throw "ArchiveDirectory must be empty: $archive"
    }
} else {
    New-Item -ItemType Directory -Path $archive | Out-Null
}

$arguments = @(
    "BuildCookRun",
    "-project=$project",
    "-target=$TargetName",
    "-noP4",
    "-platform=Win64",
    "-clientconfig=Shipping",
    "-cook",
    "-stage",
    "-pak",
    "-iostore",
    "-prereqs",
    "-archive",
    "-archivedirectory=$archive",
    "-unattended",
    "-utf8output"
)
if (-not $SkipBuild) {
    $arguments += "-build"
}

Write-Host "Building $TargetName Win64 Shipping..."
$uatLog = Join-Path $archive "$TargetName-UAT-build.log"
& $uat @arguments 2>&1 | Tee-Object -FilePath $uatLog
if ($LASTEXITCODE -ne 0) {
    throw "Unreal BuildCookRun failed with exit code $LASTEXITCODE"
}

$runtime = Join-Path $archive "Windows"
$executable = Join-Path $runtime "$TargetName.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Shipping runtime did not contain $TargetName.exe: $runtime"
}
$projectRuntime = Join-Path $runtime $projectName
if (-not (Test-Path -LiteralPath $projectRuntime -PathType Container)) {
    throw "Shipping runtime identity directory is missing: $projectRuntime"
}
$sourceMaps = @(
    Get-ChildItem -LiteralPath (Join-Path ([System.IO.Path]::GetDirectoryName($project)) "Content") `
        -Recurse -File -Filter "*.umap" | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring([System.IO.Path]::GetDirectoryName($project).Length + 1).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)
$cookedArtifacts = @(
    foreach ($name in @(
        "$TargetName.exe",
        "Manifest_UFSFiles_Win64.txt",
        "Manifest_NonUFSFiles_Win64.txt"
    )) {
        $path = Join-Path $runtime $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Shipping provenance input is missing: $path"
        }
        [ordered]@{
            path = $name
            bytes = (Get-Item -LiteralPath $path).Length
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)
$runtimeIdentity = [ordered]@{
    schema_version = 2
    project_name = $projectName
    target_name = $TargetName
    source_project_path = $project
    source_project_sha256 = (Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash.ToLowerInvariant()
    source_maps = $sourceMaps
    cooked_artifacts = $cookedArtifacts
    uat_log_path = $uatLog
    uat_log_sha256 = (Get-FileHash -LiteralPath $uatLog -Algorithm SHA256).Hash.ToLowerInvariant()
    generated_at = (Get-Date).ToString("o")
}
[System.IO.File]::WriteAllText(
    (Join-Path $runtime "ontotwin-runtime-manifest.json"),
    ($runtimeIdentity | ConvertTo-Json -Depth 5),
    [System.Text.UTF8Encoding]::new($false))

Write-Host "Shipping runtime created: $runtime" -ForegroundColor Green
