[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$project = Join-Path $PSScriptRoot "launcher\OntoTwin.ZHHZ.Launcher\OntoTwin.ZHHZ.Launcher.csproj"
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
if (-not (Test-Path -LiteralPath $output)) {
    New-Item -ItemType Directory -Path $output | Out-Null
} elseif (@(Get-ChildItem -LiteralPath $output -Force).Count -ne 0) {
    throw "OutputDirectory must be empty: $output"
}

$publishArguments = @(
    "publish", $project,
    "--configuration", "Release",
    "--runtime", "win-x64",
    "--self-contained", "true",
    "--output", $output,
    "-p:PublishSingleFile=false"
)
& dotnet @publishArguments
if ($LASTEXITCODE -ne 0) {
    throw "Launcher publish failed."
}

foreach ($requiredFile in @(
    "OntoTwin-ZHHZ-Launcher.exe",
    "OntoTwin-ZHHZ-Launcher.dll",
    "OntoTwin-ZHHZ-Launcher.deps.json",
    "OntoTwin-ZHHZ-Launcher.runtimeconfig.json",
    "D3DCompiler_47_cor3.dll",
    "PenImc_cor3.dll",
    "PresentationNative_cor3.dll",
    "vcruntime140_cor3.dll",
    "wpfgfx_cor3.dll"
)) {
    if (-not (Test-Path -LiteralPath (Join-Path $output $requiredFile) -PathType Leaf)) {
        throw "Launcher folder publish is incomplete: $requiredFile"
    }
}

Write-Host "Launcher published: $output" -ForegroundColor Green
