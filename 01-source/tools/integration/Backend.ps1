[CmdletBinding()]
param([ValidateSet('start','stop','check')][string]$Action='start', [ValidateRange(1,65535)][int]$Port=5000, [switch]$NoBrowser)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'DockerCommand.ps1')
$packageRoot=Split-Path -Parent $PSScriptRoot
$manifest=Get-Content (Join-Path $packageRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$stateRoot=Join-Path $packageRoot '.runtime'
$stateFile=Join-Path $stateRoot 'instance.json'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw '请安装并启动 Docker Desktop（Linux containers + Compose v2）。' }
if ((Run-Docker -Arguments @('info','--format','{{.OSType}}') -TimeoutSeconds 20) -ne 'linux') { throw '请将 Docker Desktop 切换为 Linux containers。' }
Run-Docker -Arguments @('compose','version','--short') -TimeoutSeconds 20 | Out-Null
if (-not (Test-Path -LiteralPath $stateFile)) {
    if ($Action -ne 'start') { throw '尚未初始化，请先运行 Start-OntoTwinBackend.ps1。' }
    if (Test-Path -LiteralPath (Join-Path $stateRoot '.env')) { throw '运行配置不完整：存在 .env 但缺少 instance.json。请恢复原配置，不能重新生成数据库密码。' }
    New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
    $instanceId='ontotwin-'+[guid]::NewGuid().ToString('N').Substring(0,12)
    $state=[ordered]@{instance_id=$instanceId;port=$Port;source_commit=$manifest.source_commit}
    $password=[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N')
    @("INSTANCE_ID=$instanceId","PORT=$Port","DB_PASSWORD=$password","BACKEND_IMAGE=$($manifest.images.backend.tag)","DB_IMAGE=$($manifest.images.db.tag)","NEO4J_IMAGE=$($manifest.images.neo4j.tag)","RELEASE_ID=$($manifest.release_id)") | Set-Content -LiteralPath (Join-Path $stateRoot '.env') -Encoding UTF8
    $state | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding UTF8
}
$state=Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($state.source_commit -ne $manifest.source_commit) { throw '此目录已启动过其他版本。请使用新解压目录；存量数据需走备份、迁移验收流程，不能静默覆盖。' }
$envFile=Join-Path $stateRoot '.env'
if (-not (Test-Path -LiteralPath $envFile)) { throw '缺少 .runtime/.env。请恢复原配置；不要删除数据卷或重新生成密码。' }
$settings=@{}
Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object { if ($_ -match '^([A-Z_][A-Z0-9_]*)=(.*)$') { $settings[$matches[1]]=$matches[2] } }
if ($state.instance_id -notmatch '^ontotwin-[a-f0-9]{12}$' -or [int]$state.port -lt 1 -or [int]$state.port -gt 65535) { throw '运行环境编号或端口无效。' }
$expectedSettings=@{INSTANCE_ID=$state.instance_id;PORT=[string]$state.port;BACKEND_IMAGE=$manifest.images.backend.tag;DB_IMAGE=$manifest.images.db.tag;NEO4J_IMAGE=$manifest.images.neo4j.tag;RELEASE_ID=$manifest.release_id}
foreach ($key in $expectedSettings.Keys) { if ($settings[$key] -cne $expectedSettings[$key]) { throw "运行配置与当前包不一致：$key。请恢复原配置。" } }
if ($settings['DB_PASSWORD'] -notmatch '^[a-f0-9]{64}$') { throw '数据库凭据配置缺失或无效，请恢复原 .env；不要重置数据库。' }
$compose=@('compose','--env-file',(Join-Path $stateRoot '.env'),'-p',$state.instance_id,'-f',(Join-Path $packageRoot 'Runtime/compose.yaml'))
if ($Action -eq 'stop') { Run-Docker -Arguments ($compose+@('stop')); return }
if ($Action -eq 'start') {
    # A running instance may reuse its own port; other services must not be displaced.
    $ownBackend=Run-Docker -Arguments ($compose+@('ps','--status','running','-q','backend')) -TimeoutSeconds 20
    if (-not $ownBackend) {
        $listener=New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback,[int]$state.port)
        try { $listener.Start() } catch { throw "端口 $($state.port) 已被占用。停止对应服务或在新的解压目录使用 -Port 指定空闲端口；不会停止现有服务。" } finally { $listener.Stop() }
    }
    $archive=Join-Path $packageRoot 'Runtime/images.tar'
    $stream=[IO.File]::OpenRead($archive)
    $hasher=[Security.Cryptography.SHA256]::Create()
    try { $archiveHash=([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant() } finally { $stream.Dispose(); $hasher.Dispose() }
    if ($archiveHash -ne $manifest.images_archive_sha256) { throw '镜像包校验失败，请重新复制接入包。' }
    $needLoad=$false
    foreach ($name in @('backend','db','neo4j')) {
        $expected=$manifest.images.$name
        $actual=Invoke-OntoTwinDocker -Arguments @('image','inspect',$expected.tag,'--format','{{.Id}}') -TimeoutSeconds 20
        if ($actual.ExitCode -ne 0 -or $actual.Output -ne $expected.id) { $needLoad=$true }
    }
    if ($needLoad) { Write-Host '正在导入包内镜像，首次启动需要几分钟……'; Run-Docker -Arguments @('load','-i',$archive) -TimeoutSeconds 1800 }
    foreach ($name in @('backend','db','neo4j')) {
        $expected=$manifest.images.$name
        $actual=Run-Docker -Arguments @('image','inspect',$expected.tag,'--format','{{.Id}}')
        if ($actual -ne $expected.id) { throw "镜像身份不匹配：$name" }
    }
    foreach ($suffix in @('db','graph','data','models')) {
        $volumeName=$state.instance_id+'_'+$suffix
        $raw=Invoke-OntoTwinDocker -Arguments @('volume','inspect',$volumeName) -TimeoutSeconds 20
        if ($raw.ExitCode -eq 0) {
            $vol=($raw.Output | ConvertFrom-Json)[0]
            if ($vol.Labels.'ontotwin.instance' -ne $state.instance_id) { throw "数据卷不属于当前环境，停止启动：$volumeName" }
        }
    }
    Run-Docker -Arguments ($compose+@('up','-d','--pull','never')) -TimeoutSeconds 180
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
