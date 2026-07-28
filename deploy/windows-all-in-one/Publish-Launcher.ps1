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
}

$publishArguments = @(
    "publish", $project,
    "--configuration", "Release",
    "--runtime", "win-x64",
    "--self-contained", "true",
    "--output", $output,
    "-p:PublishSingleFile=true",
    "-p:IncludeNativeLibrariesForSelfExtract=true"
)
& dotnet @publishArguments
if ($LASTEXITCODE -ne 0) {
    throw "Launcher publish failed."
}

Write-Host "Launcher published: $output" -ForegroundColor Green
