[CmdletBinding()]
param(
    [string]$ProjectPath = "D:\SCC\DigitalFactoryBase_SCC\DigitalFactoryBase.uproject",
    [string]$EngineRoot = "D:\UE_5.6"
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd")
})
if ($processes.Count -gt 0) {
    throw "Close every Unreal Editor process before inspecting Ground Staff assets."
}
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Leaf)) {
    throw "UE project file does not exist: $ProjectPath"
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$projectRoot = Split-Path -Parent $resolvedProject
$editorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$pythonScript = Join-Path $PSScriptRoot "ue_inspect_ground_staff.py"
$runRoot = Join-Path $projectRoot ("Saved\OntoTwinCharacterPack_Core\Inspect_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$backup = Join-Path $runRoot (Split-Path $resolvedProject -Leaf)
$log = Join-Path $runRoot "inspect.log"
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
Copy-Item -LiteralPath $resolvedProject -Destination $backup

try {
    $project = Get-Content -LiteralPath $resolvedProject -Raw -Encoding UTF8 | ConvertFrom-Json
    $plugins = @($project.Plugins)
    foreach ($pluginName in @("PythonScriptPlugin", "EditorScriptingUtilities")) {
        $entry = $plugins | Where-Object { $_.Name -eq $pluginName } | Select-Object -First 1
        if ($entry) {
            $entry.Enabled = $true
        }
        else {
            $plugins += [pscustomobject][ordered]@{
                Name = $pluginName
                Enabled = $true
                TargetAllowList = @("Editor")
            }
        }
    }
    $project.Plugins = $plugins
    [System.IO.File]::WriteAllText(
        $resolvedProject,
        ($project | ConvertTo-Json -Depth 64) + [Environment]::NewLine,
        $Utf8NoBom)

    & $editorCmd @(
        $resolvedProject,
        "-ExecutePythonScript=$pythonScript",
        "-abslog=$log",
        "-unattended", "-nop4", "-nullrhi", "-nosplash", "-NoSound", "-UTF8Output"
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal Ground Staff inspection failed with exit code $LASTEXITCODE. Log: $log"
    }
}
finally {
    Copy-Item -LiteralPath $backup -Destination $resolvedProject -Force
}

$text = Get-Content -LiteralPath $log -Raw -Encoding UTF8
if (-not $text.Contains("ONTOTWIN_GROUND_STAFF_INSPECT_BEGIN") -or
    -not $text.Contains("ONTOTWIN_GROUND_STAFF_INSPECT_END") -or
    -not $text.Contains('"success": true')) {
    throw "Ground Staff inspection did not produce a clean result: $log"
}

$line = ($text -split "`r?`n" | Where-Object {
    $_ -match 'ONTOTWIN_GROUND_STAFF_INSPECT_BEGIN|ONTOTWIN_GROUND_STAFF_INSPECT_END|\{"anim_blueprint"'
}) -join [Environment]::NewLine
[pscustomobject][ordered]@{
    success = $true
    log = $log
    result = $line
    uproject_restored = $true
} | ConvertTo-Json -Depth 8
