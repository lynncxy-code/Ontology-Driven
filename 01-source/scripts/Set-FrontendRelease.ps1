param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][ValidateSet('business','test')][string]$Environment,
    [Parameter(Mandatory=$true)][ValidateNotNullOrEmpty()][string]$Version,
    [string]$Backend = '后端版本未标记',
    [string]$Note = '此处显示前端发布信息，不代表 UE 已加载相同版本的插件。'
)
# Run once when preparing a frontend release, never on page refresh or service startup.
$ErrorActionPreference = 'Stop'
$target = (Resolve-Path -LiteralPath $OutputDirectory).Path
[ordered]@{
    environment = $Environment
    version = $Version
    updated_at = [DateTimeOffset]::UtcNow.ToString('o')
    time_zone = 'Asia/Shanghai'
    backend = $Backend
    note = $Note
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $target 'release-info.json') -Encoding utf8
Write-Output "Frontend release stamped: $Environment / $Version"
