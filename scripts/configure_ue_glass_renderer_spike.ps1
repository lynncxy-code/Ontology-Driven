param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,

    [ValidateRange(0, 4)]
    [int]$PostBufferIndex = 0,

    [ValidateSet("High", "Balanced", "Performance")]
    [string]$RequestedQuality = "High"
)

$ErrorActionPreference = "Stop"

function Get-IniLines {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "INI file does not exist: $Path"
    }

    $result = [System.Collections.Generic.List[string]]::new()
    foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
        $result.Add($line)
    }
    return ,$result
}

function Find-IniSection {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Section
    )

    $header = "[$Section]"
    for ($index = 0; $index -lt $Lines.Count; $index++) {
        if ($Lines[$index].Trim() -eq $header) {
            return $index
        }
    }
    return -1
}

function Find-NextIniSection {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [int]$SectionIndex
    )

    for ($index = $SectionIndex + 1; $index -lt $Lines.Count; $index++) {
        if ($Lines[$index].Trim() -match '^\[.+\]$') {
            return $index
        }
    }
    return $Lines.Count
}

function Ensure-IniValue {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Section,
        [string]$Key,
        [string]$Value
    )

    $sectionIndex = Find-IniSection -Lines $Lines -Section $Section
    if ($sectionIndex -lt 0) {
        if ($Lines.Count -gt 0 -and $Lines[$Lines.Count - 1] -ne "") {
            $Lines.Add("")
        }
        $Lines.Add("[$Section]")
        $Lines.Add("$Key=$Value")
        return
    }

    $nextSectionIndex = Find-NextIniSection -Lines $Lines -SectionIndex $sectionIndex
    $escapedKey = [Regex]::Escape($Key)
    for ($index = $sectionIndex + 1; $index -lt $nextSectionIndex; $index++) {
        if ($Lines[$index] -match "^\s*$escapedKey\s*=") {
            $Lines[$index] = "$Key=$Value"
            return
        }
    }

    $Lines.Insert($nextSectionIndex, "$Key=$Value")
}

function Ensure-IniLine {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Section,
        [string]$Line
    )

    $sectionIndex = Find-IniSection -Lines $Lines -Section $Section
    if ($sectionIndex -lt 0) {
        if ($Lines.Count -gt 0 -and $Lines[$Lines.Count - 1] -ne "") {
            $Lines.Add("")
        }
        $Lines.Add("[$Section]")
        $Lines.Add($Line)
        return
    }

    $nextSectionIndex = Find-NextIniSection -Lines $Lines -SectionIndex $sectionIndex
    for ($index = $sectionIndex + 1; $index -lt $nextSectionIndex; $index++) {
        if ($Lines[$index].Trim() -eq $Line) {
            return
        }
    }

    $Lines.Insert($nextSectionIndex, $Line)
}

function Save-IniLines {
    param(
        [string]$Path,
        [System.Collections.Generic.List[string]]$Lines
    )

    $utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllLines($Path, $Lines, $utf8WithoutBom)
}

$resolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$configDir = Join-Path $resolvedProjectRoot "Config"
$defaultEnginePath = Join-Path $configDir "DefaultEngine.ini"
$defaultGamePath = Join-Path $configDir "DefaultGame.ini"

foreach ($iniPath in @($defaultEnginePath, $defaultGamePath)) {
    $backupPath = "$iniPath.before-ontotwin-glass-spike.bak"
    if (-not (Test-Path -LiteralPath $backupPath)) {
        [System.IO.File]::Copy($iniPath, $backupPath, $false)
    }
}

$engineLines = Get-IniLines -Path $defaultEnginePath
Ensure-IniValue `
    -Lines $engineLines `
    -Section "SystemSettings" `
    -Key "Slate.CopyBackbufferToSlatePostRenderTargets" `
    -Value "1"
Save-IniLines -Path $defaultEnginePath -Lines $engineLines

$gameLines = Get-IniLines -Path $defaultGamePath
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "bEnableGlassUI" `
    -Value "True"
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "bEnableHighQualityRenderer" `
    -Value "True"
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "bEnableRendererSpike" `
    -Value "False"
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "RequestedQuality" `
    -Value $RequestedQuality
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "ReservedPostBufferIndex" `
    -Value $PostBufferIndex
Ensure-IniValue `
    -Lines $gameLines `
    -Section "/Script/OntoTwinSync.OntoTwinGlassSettings" `
    -Key "GaussianBlurStrength" `
    -Value "14.000000"
Save-IniLines -Path $defaultGamePath -Lines $gameLines

Write-Output "ONTOTWIN_GLASS_CONFIG_OK"
Write-Output "ProjectRoot=$resolvedProjectRoot"
Write-Output "RequestedQuality=$RequestedQuality"
Write-Output "ReservedPostBufferIndex=$PostBufferIndex"
Write-Output "PluginOwnedUICook=True"
