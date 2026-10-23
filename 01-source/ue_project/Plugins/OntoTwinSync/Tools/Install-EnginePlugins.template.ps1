param([Parameter(Mandatory = $true)][string]$EngineRoot)
$ErrorActionPreference = 'Stop'
$engine = [IO.Path]::GetFullPath($EngineRoot)
if (-not (Test-Path -LiteralPath (Join-Path $engine 'Engine') -PathType Container)) {
    throw "找不到 UE Engine 目录：$engine"
}
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) {
    throw '请先保存工作并关闭 UE 编辑器，再安装插件。'
}
$sourceRoot = Join-Path $PSScriptRoot 'EnginePlugins\Marketplace'
$targetRoot = Join-Path $engine 'Engine\Plugins\Marketplace'
$backupRoot = Join-Path $engine ('OntoTwinPluginBackups\' + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $backupRoot 'staged'
$plugins = @(__PLUGIN_NAMES__)
$moved = @()
$installed = @()
function Assert-ChildPath($path, $root) {
    $full = [IO.Path]::GetFullPath($path)
    $prefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "路径超出安装范围：$full"
    }
    $cursor = $full
    while ($cursor) {
        if ((Get-Item -LiteralPath $cursor -ErrorAction SilentlyContinue).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "不能自动移动链接目录或其内容：$cursor"
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
Assert-ChildPath $targetRoot $engine
Assert-ChildPath $backupRoot $engine
New-Item -ItemType Directory -Force -Path $targetRoot, $stageRoot | Out-Null
try {
    # 先复制全部新插件；复制失败时旧插件完全不动。
    foreach ($plugin in $plugins) {
        if ($plugin -notmatch '^[A-Za-z0-9_]+$') { throw '插件名不合法' }
        $source = Join-Path $sourceRoot $plugin
        if (-not (Test-Path -LiteralPath (Join-Path $source "$plugin.uplugin") -PathType Leaf)) {
            throw "交付包缺少插件描述：$plugin"
        }
        Copy-Item -LiteralPath $source -Destination $stageRoot -Recurse -Force
    }
    foreach ($plugin in $plugins) {
        # 商城目录可能带哈希后缀；按描述文件名查找，不按目录名猜测。
        $oldDirs = @(Get-ChildItem -LiteralPath $targetRoot -Filter "$plugin.uplugin" -Recurse -File |
            ForEach-Object { $_.Directory.FullName } | Sort-Object -Unique)
        $target = Join-Path $targetRoot $plugin
        if ((Test-Path -LiteralPath $target) -and $oldDirs -notcontains $target) { $oldDirs += $target }
        foreach ($old in $oldDirs) {
            Assert-ChildPath $old $targetRoot
            $backup = Join-Path $backupRoot ('old-' + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath $old -Destination $backup
            $moved += [pscustomobject]@{ Original=$old; Backup=$backup }
        }
        Assert-ChildPath $target $targetRoot
        $installed += $target
        Move-Item -LiteralPath (Join-Path $stageRoot $plugin) -Destination $target
        Write-Host "已安装引擎插件：$plugin"
    }
} catch {
    $failure = $_
    foreach ($target in $installed) {
        if (Test-Path -LiteralPath $target) {
            Assert-ChildPath $target $targetRoot
            Move-Item -LiteralPath $target -Destination (Join-Path $backupRoot ('failed-' + [guid]::NewGuid().ToString('N')))
        }
    }
    [array]::Reverse($moved)
    foreach ($entry in $moved) {
        Assert-ChildPath $entry.Backup $backupRoot
        Move-Item -LiteralPath $entry.Backup -Destination $entry.Original
    }
    throw "安装失败，旧插件已恢复。备份：$backupRoot；原因：$failure"
}
Write-Host "完成。旧插件备份保留在：$backupRoot；请重新启动 UE。"
