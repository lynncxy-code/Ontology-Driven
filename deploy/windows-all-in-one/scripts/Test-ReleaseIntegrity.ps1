[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "Common.ps1")

$manifestPath = Join-Path $script:ReleaseRoot "release-manifest.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Release manifest is missing: $manifestPath"
}

$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
$releasePrefix = [System.IO.Path]::GetFullPath($script:ReleaseRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$failures = New-Object System.Collections.Generic.List[string]

foreach ($entry in @($manifest.files)) {
    $relativePath = ([string]$entry.path).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $script:ReleaseRoot $relativePath))
    if (-not $fullPath.StartsWith($releasePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $failures.Add("Unsafe manifest path: $($entry.path)")
        continue
    }
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        $failures.Add("Missing file: $($entry.path)")
        continue
    }

    $item = Get-Item -LiteralPath $fullPath
    if ($item.Length -ne [long]$entry.bytes) {
        $failures.Add("Size mismatch: $($entry.path)")
        continue
    }
    $actualHash = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne ([string]$entry.sha256).ToLowerInvariant()) {
        $failures.Add("SHA-256 mismatch: $($entry.path)")
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    throw "Release integrity validation failed for $($failures.Count) file(s)."
}

Write-Host "Release integrity: PASS ($(@($manifest.files).Count) files checked)." -ForegroundColor Green
