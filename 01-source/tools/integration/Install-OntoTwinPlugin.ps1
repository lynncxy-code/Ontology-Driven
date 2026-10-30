[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ProjectPath)
$ErrorActionPreference='Stop'
if (Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue) { throw '请关闭 UE 编辑器后安装。' }
$projectFile=(Resolve-Path -LiteralPath $ProjectPath).Path
if ([IO.Path]::GetExtension($projectFile) -ne '.uproject') { throw '请选择 .uproject 文件。' }
$projectRoot=Split-Path -Parent $projectFile
$descriptor=Get-Content -LiteralPath $projectFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($descriptor.EngineAssociation -ne '5.6') { throw '本包验证版本为 UE 5.6；自编引擎或其他版本需要重新编译验收。' }
$packageRoot=Split-Path -Parent $PSScriptRoot
$names=@('OntoTwinSync','glTFRuntime','WebUI','OntoTwinIndustrialBehavior')
$targetRoot=Join-Path $projectRoot 'Plugins'
foreach ($name in $names) {
    $source=Join-Path $packageRoot ('Plugins/'+$name)
    if (-not (Test-Path -LiteralPath (Join-Path $source ($name+'.uplugin')))) { throw "缺少插件：$name" }
    $target=Join-Path $targetRoot $name
    if (Test-Path -LiteralPath $target) {
        $item=Get-Item -LiteralPath $target -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "目标插件是目录链接，请先确定要更新母本还是独立副本：$target" }
    }
}
$backup=Join-Path $projectRoot ('Saved/OntoTwinInstallBackup/'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,6))
New-Item -ItemType Directory -Path $backup,$targetRoot -Force | Out-Null
Copy-Item -LiteralPath $projectFile -Destination $backup
foreach ($name in $names) {
    $target=Join-Path $targetRoot $name
    if (Test-Path -LiteralPath $target) {
        # Both paths are fixed descendants of the explicitly supplied UE project.
        $resolved=(Resolve-Path -LiteralPath $target).Path
        if (-not $resolved.StartsWith($projectRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw '插件路径超出目标工程，停止安装。' }
        Move-Item -LiteralPath $resolved -Destination (Join-Path $backup $name)
    }
    Copy-Item -LiteralPath (Join-Path $packageRoot ('Plugins/'+$name)) -Destination $target -Recurse
}
$plugins=@($descriptor.Plugins | Where-Object { $null -ne $_ })
foreach ($name in $names) {
    $existing=$plugins | Where-Object Name -eq $name | Select-Object -First 1
    if ($existing) { $existing.Enabled=$true } else { $plugins += [pscustomobject]@{Name=$name;Enabled=$true} }
}
$descriptor | Add-Member NoteProperty Plugins $plugins -Force
$descriptor | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $projectFile -Encoding UTF8
Write-Host "基础插件已安装；备份：$backup" -ForegroundColor Green
Write-Host '需要人物漫游时，再执行 Tools/Install-CoreCharacters.ps1；它会核对同名 Content，避免覆盖项目资产。'
Write-Host '使用 UE 5.6 打开工程；如提示重编译，请安装 Visual Studio 2022 的游戏开发 C++ 和 Windows SDK。'
