[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$EngineRoot = "D:\UE_5.6",

    [switch]$UseExistingHostContent
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Assert-UnrealEditorClosed {
    $processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd")
    })
    if ($processes.Count -gt 0) {
        $summary = ($processes | ForEach-Object { "$($_.ProcessName) PID=$($_.Id)" }) -join ", "
        throw "Close every Unreal Editor process before verifying: $summary"
    }
}

function Enable-EditorPlugin([string]$Path, [string]$PluginName) {
    $project = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    $plugins = @($project.Plugins)
    $entry = $plugins | Where-Object { $_.Name -eq $PluginName } | Select-Object -First 1
    if ($entry) {
        $entry.Enabled = $true
    }
    else {
        $plugins += [pscustomobject][ordered]@{
            Name = $PluginName
            Enabled = $true
            TargetAllowList = @("Editor")
        }
    }
    $project.Plugins = $plugins
    $json = $project | ConvertTo-Json -Depth 64
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, $Utf8NoBom)
}

Assert-UnrealEditorClosed
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Leaf)) {
    throw "UE project file does not exist: $ProjectPath"
}
$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$projectRoot = Split-Path -Parent $resolvedProject
$editorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$verifyPython = Join-Path $PSScriptRoot "ue_verify_ontotwin_character_pack_core.py"
foreach ($requiredFile in @($editorCmd, $verifyPython)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Verification dependency does not exist: $requiredFile"
    }
}

& (Join-Path $PSScriptRoot "install_ontotwin_character_pack_core.ps1") `
    -ProjectPath $resolvedProject `
    -UseExistingHostContent:$UseExistingHostContent | Out-Host

$verifyRoot = Join-Path $projectRoot ("Saved\OntoTwinCharacterPack_Core\Verify_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $verifyRoot -Force | Out-Null
$uProjectBackup = Join-Path $verifyRoot (Split-Path $resolvedProject -Leaf)
$verifyLog = Join-Path $verifyRoot "verify.log"
Copy-Item -LiteralPath $resolvedProject -Destination $uProjectBackup

try {
    Enable-EditorPlugin $resolvedProject "PythonScriptPlugin"
    Enable-EditorPlugin $resolvedProject "EditorScriptingUtilities"
    $arguments = @(
        $resolvedProject,
        "-ExecutePythonScript=$verifyPython",
        "-abslog=$verifyLog",
        "-unattended",
        "-nop4",
        "-nullrhi",
        "-nosplash",
        "-NoSound",
        "-UTF8Output"
    )
    & $editorCmd @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal verification failed with exit code $LASTEXITCODE. Log: $verifyLog"
    }
}
finally {
    Copy-Item -LiteralPath $uProjectBackup -Destination $resolvedProject -Force
}

$logText = Get-Content -LiteralPath $verifyLog -Raw -Encoding UTF8
if (-not $logText.Contains("ONTOTWIN_CORE_VERIFY_BEGIN") -or
    -not $logText.Contains("ONTOTWIN_CORE_VERIFY_END") -or
    -not $logText.Contains('"success": true') -or
    $logText.Contains("LogPython: Error:")) {
    throw "OntoTwinCharacterPack_Core verification did not produce a clean success result: $verifyLog"
}
if ($logText -notmatch 'TwinCharacter:\s+Class TwinCharacterAsset, Count 2' -or
    $logText -notmatch 'TwinSkin:\s+Class TwinSkinAsset, Count 3') {
    throw "Asset Manager did not scan the expected Core assets: $verifyLog"
}

[pscustomobject][ordered]@{
    success = $true
    project = $resolvedProject
    verification_log = $verifyLog
    uproject_restored = $true
} | ConvertTo-Json -Depth 8
