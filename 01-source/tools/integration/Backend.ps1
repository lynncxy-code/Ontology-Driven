[CmdletBinding()]
param([ValidateSet('start','stop','check')][string]$Action='start', [int]$Port=5000, [switch]$NoBrowser)
$ErrorActionPreference='Stop'
$packageRoot=Split-Path -Parent $PSScriptRoot
$manifest=Get-Content (Join-Path $packageRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$stateRoot=Join-Path $packageRoot '.runtime'
$stateFile=Join-Path $stateRoot 'instance.json'
function Run-Docker([string[]]$Arguments) {
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($Arguments[0])" }
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw '请安装并启动 Docker Desktop（Linux containers + Compose v2）。' }
Run-Docker -Arguments @('info','--format','{{.OSType}}') | Out-Null
if (-not (Test-Path -LiteralPath $stateFile)) {
    if ($Action -ne 'start') { throw '尚未初始化，请先运行 Start-OntoTwinBackend.ps1。' }
    New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
    $instanceId='ontotwin-'+[guid]::NewGuid().ToString('N').Substring(0,12)
    $state=[ordered]@{instance_id=$instanceId;port=$Port;source_commit=$manifest.source_commit}
    $state | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding UTF8
    $password=[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N')
    @("INSTANCE_ID=$instanceId","PORT=$Port","DB_PASSWORD=$password","BACKEND_IMAGE=$($manifest.images.backend.tag)","DB_IMAGE=$($manifest.images.db.tag)","NEO4J_IMAGE=$($manifest.images.neo4j.tag)","RELEASE_ID=$($manifest.release_id)") | Set-Content -LiteralPath (Join-Path $stateRoot '.env') -Encoding UTF8
}
$state=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($state.source_commit -ne $manifest.source_commit) { throw '此目录已启动过其他版本。请使用新解压目录；存量数据需走备份、迁移验收流程，不能静默覆盖。' }
$compose=@('compose','--env-file',(Join-Path $stateRoot '.env'),'-p',$state.instance_id,'-f',(Join-Path $packageRoot 'Runtime/compose.yaml'))
if ($Action -eq 'stop') { Run-Docker -Arguments ($compose+@('stop')); return }
if ($Action -eq 'start') {
    $archive=Join-Path $packageRoot 'Runtime/images.tar'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.images_archive_sha256) { throw '镜像包校验失败，请重新复制接入包。' }
    $needLoad=$false
    foreach ($name in @('backend','db','neo4j')) {
        $expected=$manifest.images.$name
        $actual=& docker image inspect $expected.tag --format '{{.Id}}' 2>$null
        if ($LASTEXITCODE -ne 0 -or $actual -ne $expected.id) { $needLoad=$true }
    }
    if ($needLoad) { Run-Docker -Arguments @('load','-i',$archive) }
    foreach ($name in @('backend','db','neo4j')) {
        $expected=$manifest.images.$name
        $actual=Run-Docker -Arguments @('image','inspect',$expected.tag,'--format','{{.Id}}')
        if ($actual -ne $expected.id) { throw "镜像身份不匹配：$name" }
    }
    foreach ($suffix in @('db','graph','data','models')) {
        $volumeName=$state.instance_id+'_'+$suffix
        $raw=& docker volume inspect $volumeName 2>$null
        if ($LASTEXITCODE -eq 0) {
            $vol=($raw | ConvertFrom-Json)[0]
            if ($vol.Labels.'ontotwin.instance' -ne $state.instance_id) { throw "数据卷不属于当前环境，停止启动：$volumeName" }
        }
    }
    Run-Docker -Arguments ($compose+@('up','-d','--pull','never'))
}
$url='http://127.0.0.1:'+$state.port
$ready=$false
for ($i=0; $i -lt 60; $i++) {
    try {
        $health=Invoke-RestMethod -Uri ($url+'/api/v4.8/health') -TimeoutSec 3
        if ($health.ok -and $health.release_id -eq $manifest.release_id) { $ready=$true; break }
    } catch { }
    if ($Action -eq 'check') { break }
    Start-Sleep -Seconds 2
}
if (-not $ready) { Run-Docker -Arguments ($compose+@('logs','--tail','40','backend')); throw '后端未就绪或版本不匹配。请查看日志，不要删除旧数据卷。' }
Write-Host "环境：$($state.instance_id)  版本：$($manifest.release_id)" -ForegroundColor Green
Write-Host "网页后台：$url/account"
Write-Host '首次使用请在网页初始化组织和管理员；随后创建或导入数据集，并明确设置关卡绑定。'
if ($Action -eq 'start' -and -not $NoBrowser) { Start-Process ($url+'/account') }
