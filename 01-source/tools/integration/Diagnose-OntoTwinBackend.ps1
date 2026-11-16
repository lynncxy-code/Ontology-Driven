<#
.SYNOPSIS
    OntoTwin 接入包后端启动失败只读诊断（不改数据、不删卷、不重启容器）。

.DESCRIPTION
    backend 报 “PostgreSQL 在 60s 内不可达 / 拒绝以空数据状态启动” 时运行本脚本。
    注意：backend 此时通常已经 exit，`docker exec` 会报 “is not running”，所以本脚本
    不依赖 backend 存活：它从 db 容器内经 TCP 实测 DNS、密码、库是否存在。

.PARAMETER PackageRoot
    解压后的接入包根目录（含 manifest.json 的目录）。省略时依次尝试：
    当前目录、脚本目录、脚本上级目录。

.PARAMETER LogLines
    日志尾部行数，默认 120。

.PARAMETER ShowSecret
    显示 .runtime\.env 中的 DB_PASSWORD（默认打码）。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Tools\Diagnose-OntoTwinBackend.ps1
#>
[CmdletBinding()]
param(
    [string]$PackageRoot,
    [int]$LogLines = 120,
    [switch]$ShowSecret
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$script:Findings = @()
$script:LastExit = 0
$script:LastOut = ''

function Hide-Secret([string]$url) {
    if (-not $url) { return '' }
    return ($url -replace '//([^:@/]+):[^@]*@', '//$1:****@')
}

function Say([string]$text) { Write-Host "`n=== $text ===" -ForegroundColor Cyan }
function Note([string]$text) { Write-Host "    $text" -ForegroundColor DarkGray }
function Flag([string]$text) { $script:Findings += $text; Write-Host "  [!] $text" -ForegroundColor Yellow }

function Invoke-Docker([string[]]$arguments) {
    $display = foreach ($item in $arguments) { if ($item -match '://[^:@/]+:[^@]*@') { Hide-Secret $item } else { $item } }
    Write-Host ("`$ docker " + ($display -join ' ')) -ForegroundColor DarkGray
    $raw = & docker @arguments 2>&1
    $script:LastExit = $LASTEXITCODE
    $script:LastOut = [string]($raw | Out-String)
    if ($script:LastOut.Trim()) { Write-Host $script:LastOut.TrimEnd() }
}

function Resolve-PackageRoot {
    if ($PackageRoot) {
        if (Test-Path -LiteralPath (Join-Path $PackageRoot 'manifest.json')) { return (Resolve-Path -LiteralPath $PackageRoot).Path }
        throw "不是接入包目录（缺少 manifest.json）：$PackageRoot"
    }
    $candidates = @((Get-Location).Path, $PSScriptRoot, (Split-Path -Parent $PSScriptRoot))
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath (Join-Path $candidate 'manifest.json'))) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw '未找到接入包目录（manifest.json）。请用 -PackageRoot 指定解压目录。'
}

Say '环境'
if (-not (Get-Command docker -CommandType Application -ErrorAction SilentlyContinue)) {
    Write-Host '  [x] 未找到 docker 命令：请先安装并启动 Docker Desktop（Linux containers）。' -ForegroundColor Red
    exit 1
}
$root = Resolve-PackageRoot
Note "接入包：$root"
$manifest = Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Note "release：$($manifest.release_id) / commit：$($manifest.source_commit)"
Invoke-Docker @('version', '--format', 'server={{.Server.Version}} os={{.Server.Os}}')
if ($script:LastExit -ne 0) {
    Write-Host '  [x] 无法连接 Docker 引擎：Docker Desktop 未运行，或当前用户不在 docker-users 组。' -ForegroundColor Red
    exit 1
}

$stateDir = Join-Path $root '.runtime'
$instanceId = $null
$envFile = Join-Path $stateDir '.env'
$composeFile = Join-Path $root 'Runtime/compose.yaml'
$port = 5000
$dbPassword = $null

if (Test-Path -LiteralPath (Join-Path $stateDir 'instance.json')) {
    $state = Get-Content -LiteralPath (Join-Path $stateDir 'instance.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $instanceId = $state.instance_id
    if ($state.port) { $port = [int]$state.port }
    Note "实例：$instanceId   端口：$port"
} else {
    Flag '缺少 .runtime\instance.json：该目录从未成功启动，或 .runtime 被删除（再次启动会生成新实例和新卷）。'
}

if (Test-Path -LiteralPath $envFile) {
    foreach ($line in Get-Content -LiteralPath $envFile -Encoding UTF8) {
        if ($line -match '^\s*DB_PASSWORD\s*=\s*(.+)$') { $dbPassword = $matches[1].Trim() }
        if ($line -match '^\s*RELEASE_ID\s*=\s*(.+)$') { Note "环境 release：$($matches[1].Trim())" }
    }
    if ($dbPassword) {
        $shown = if ($ShowSecret) { $dbPassword } else { $dbPassword.Substring(0, 4) + '****' }
        Note "DB_PASSWORD：$shown"
    }
} else {
    Flag '缺少 .runtime\.env：compose 变量（镜像、密码、端口）无法解析，启动必然失败。'
}

Say 'Docker 容器状态'
Invoke-Docker @('ps', '-a', '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}')
if ($instanceId -and (Test-Path -LiteralPath $composeFile)) {
    Invoke-Docker @('compose', '--env-file', $envFile, '-p', $instanceId, '-f', $composeFile, 'ps')
}

function Get-ServiceContainer([string]$service) {
    $name = $null
    if ($instanceId) {
        $raw = & docker ps -a --filter "label=com.docker.compose.project=$instanceId" --filter "label=com.docker.compose.service=$service" --format '{{.Names}}' 2>$null
        $name = @($raw)[0]
    }
    if (-not $name) {
        $raw = & docker ps -a --filter 'name=ontotwin-' --format '{{.Names}}' 2>$null
        $name = @($raw | Where-Object { $_ -like "*-$service-1" })[0]
    }
    return $name
}

$dbContainer = Get-ServiceContainer 'db'
$backendContainer = Get-ServiceContainer 'backend'
Note "db 容器：$(if ($dbContainer) { $dbContainer } else { '（不存在）' })"
Note "backend 容器：$(if ($backendContainer) { $backendContainer } else { '（不存在）' })"
if (-not $dbContainer) { Flag '找不到 db 容器：compose 没有成功创建数据库服务（镜像缺失或 compose 变量错误）。' }

$running = @{}
foreach ($pair in @(@('db', $dbContainer), @('backend', $backendContainer))) {
    $service = $pair[0]
    $name = $pair[1]
    if (-not $name) { continue }
    Say "$service 容器状态"
    Invoke-Docker @('inspect', $name, '--format',
        'status={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}} started={{.State.StartedAt}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}')
    $text = $script:LastOut
    $running[$service] = ($text -match 'status=running')
    if ($text -match 'status=running') {
        if ($text -match 'health=unhealthy') { Flag "$service 在运行但健康检查为 unhealthy（内部服务没有真正就绪）。" }
    } elseif ($text -match 'status=exited') {
        if ($text -match 'exit=137') { Flag "$service 被强制终止（exit 137）：常见于内存不足被 OOM，或 Docker Desktop 资源被抢占。" }
        elseif ($text -match 'exit=1') { Flag "$service 以 exit 1 退出：进程内错误，见下面日志。" }
        else { Flag "$service 已退出（$text）。" }
    } elseif ($text -match 'status=restarting') {
        Flag "$service 处于 restarting：崩溃后被反复拉起。"
    }
}

$backendUrl = $null
if ($backendContainer) {
    Say 'backend 的 DATABASE_URL（从容器配置读取，容器不运行也能读）'
    Invoke-Docker @('inspect', $backendContainer, '--format', '{{range .Config.Env}}{{println .}}{{end}}')
    foreach ($line in ($script:LastOut -split "`r?`n")) {
        if ($line -match '^DATABASE_URL=(.+)$') { $backendUrl = $matches[1].Trim() }
    }
    if ($backendUrl) { Note ('DATABASE_URL：' + (Hide-Secret $backendUrl)) } else { Flag 'backend 容器里没有 DATABASE_URL：compose 环境变量传递失败。' }
}

if ($backendContainer -and $dbContainer) {
    Say '网络一致性（backend 与 db 是否在同一 compose 网络）'
    Invoke-Docker @('inspect', $backendContainer, '--format', '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}')
    $backendNet = $script:LastOut.Trim()
    Invoke-Docker @('inspect', $dbContainer, '--format', '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}')
    $dbNet = $script:LastOut.Trim()
    Note "backend：$backendNet"
    Note "db：$dbNet"
    if ($backendNet -and $dbNet -and $backendNet -ne $dbNet) {
        Flag '两个容器不在同一网络：backend 里的 db 主机名解析不到（常因单独启动了 backend，或项目名/网络被重建）。'
    }
}

Say '真实连接测试（经 db 容器走 TCP：一次校验 DNS、密码、库是否存在）'
$probeUrl = $backendUrl
if (-not $probeUrl -and $dbPassword) { $probeUrl = "postgresql://ontotwin:$dbPassword@db:5432/ontotwin" }
if ($dbContainer -and $probeUrl) {
    Invoke-Docker @('exec', $dbContainer, 'psql', $probeUrl, '-c', 'select 1')
    if ($script:LastExit -ne 0) { Flag 'TCP 连接失败，看上面 psql 的原始报错（password authentication failed / could not translate host name / database ... does not exist / starting up）。' }
} elseif (-not $dbContainer) {
    Note 'db 容器不存在，跳过连接测试。'
} else {
    Note '拿不到 DATABASE_URL 和密码，跳过连接测试。'
}

if ($dbContainer) {
    Say "db 日志（尾部 $LogLines 行）"
    Invoke-Docker @('logs', '--tail', "$LogLines", $dbContainer)
}

if ($backendContainer -and $running['backend'] -and $dbContainer) {
    Say '在运行中的 backend 容器内实测（同一条 SQL）'
    Invoke-Docker @('exec', $backendContainer, 'python', '-c',
        "import os,psycopg;print(psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=5).execute('select 1').fetchone())")
    Say 'backend 日志（尾部 60 行）'
    Invoke-Docker @('logs', '--tail', '60', $backendContainer)
} elseif ($backendContainer) {
    Note 'backend 未在运行，跳过容器内实测（上面的 db 侧 TCP 测试已覆盖同样的连接路径）。'
}

Say '数据卷与磁盘'
if ($instanceId) {
    foreach ($suffix in @('db', 'graph', 'data', 'models')) {
        $volume = "${instanceId}_$suffix"
        Invoke-Docker @('volume', 'inspect', $volume, '--format', '{{.Name}} labels={{index .Labels "ontotwin.instance"}}')
        if ($script:LastExit -ne 0) { Flag "缺少数据卷 $volume（首次启动未完成，或卷被手工删除）。" }
    }
}
Invoke-Docker @('system', 'df')

Say "端口 $port 占用"
if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        $ownerPid = @($listener.OwningProcess)[0]
        $process = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
        Note ("端口 {0} 被 PID {1}（{2}）占用" -f $port, $ownerPid, $(if ($process) { $process.ProcessName } else { '?' }))
    } else {
        Note "端口 $port 当前无人监听（backend 没起来，符合预期）。"
    }
} else {
    Note '缺少 Get-NetTCPConnection，跳过端口检查。'
}

Say '结论建议'
if ($script:Findings.Count -eq 0) {
    Write-Host '  未发现明显异常。可再次运行 Tools\Start-OntoTwinBackend.ps1（PG 首次初始化慢时 60s 等待可能不够）。' -ForegroundColor Green
} else {
    foreach ($finding in $script:Findings) { Write-Host "  - $finding" -ForegroundColor Yellow }
}
Write-Host ''
Write-Host '  对照处理：' -ForegroundColor Cyan
Write-Host '  1) db 日志出现 "database files are incompatible with server" → 数据卷与镜像版本不符，先备份再重建卷，不要直接删。'
Write-Host '  2) db 日志出现 "No space left on device" → 清理 Docker 磁盘空间（Docker Desktop 磁盘镜像）。'
Write-Host '  3) db 日志出现 "Permission denied"、"chmod"、"initdb: error" → Windows 侧权限或杀软拦截，重启 Docker Desktop 后重试。'
Write-Host '  4) psql 报 "password authentication failed" → 容器里 DATABASE_URL 的密码与数据卷里的不一致（卷沿用旧实例）。'
Write-Host '     健康检查发现不了：pg_isready 不校验密码，也不校验库是否存在。'
Write-Host '  5) psql 报 "could not translate host name db" → 不在同一 compose 网络。'
Write-Host '  6) psql 报 "database ... does not exist" → 卷里没有 ontotwin 库（初始化阶段中断）。'
Write-Host ''
Write-Host '  本脚本只读：不重启、不停止、不删除任何容器或数据卷。' -ForegroundColor DarkGray
