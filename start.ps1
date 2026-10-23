# OntoTwin Nexus 2.3 — 一键启动脚本 (Docker 版)
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host " ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host " ║       OntoTwin Nexus 2.3  启动脚本       ║" -ForegroundColor Cyan
Write-Host " ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 检查 Docker 是否运行 ─────────────────────────────────────────
Write-Host " [1/3] 检查 Docker 状态..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "       Docker 运行正常 ✅" -ForegroundColor Green
} catch {
    Write-Host " [错误] Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}

# ── 检查环境配置 (.env & MODELS_HOST_DIR) ───────────────────────
if (-not (Test-Path -LiteralPath (Join-Path $ROOT ".env"))) {
    if (Test-Path -LiteralPath (Join-Path $ROOT ".env.example")) {
        Write-Host " [提示] 未检测到 .env 文件，已从 .env.example 自动创建默认配置" -ForegroundColor Yellow
        Copy-Item (Join-Path $ROOT ".env.example") (Join-Path $ROOT ".env")
    }
}
if (Test-Path -LiteralPath (Join-Path $ROOT ".env")) {
    $envLines = Get-Content (Join-Path $ROOT ".env")
    foreach ($line in $envLines) {
        if ($line -match '^\s*MODELS_HOST_DIR\s*=\s*(.+)$') {
            $mDir = $matches[1].Trim().Trim('"').Trim("'")
            if ($mDir -and -not (Test-Path -LiteralPath $mDir)) {
                try {
                    New-Item -ItemType Directory -Path $mDir -Force | Out-Null
                    Write-Host "       已自动创建宿主机模型目录: $mDir" -ForegroundColor DarkGray
                } catch { }
            }
        }
    }
}

# ── 启动 Docker Compose ──────────────────────────────────────────
Write-Host ""
Write-Host " [2/3] 启动容器 (docker compose up)..." -ForegroundColor Yellow
Set-Location $ROOT
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host " [错误] Docker 启动失败，请检查上方错误信息" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "       容器已启动 ✅" -ForegroundColor Green

# ── 等待服务就绪 ─────────────────────────────────────────────────
Write-Host ""
Write-Host " [3/3] 等待后端服务就绪..." -ForegroundColor Yellow
$maxWait = 20
$ready = $false
for ($i = 1; $i -le $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:5000/api/v2/ue/diagnostics" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        $ready = $true
        break
    } catch {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            $ready = $true
            break
        } catch { }
    }
    Write-Host "       等待中... ($i/$maxWait)" -ForegroundColor DarkGray
}

if (-not $ready) {
    Write-Host " [警告] 服务可能尚未就绪，仍将尝试打开浏览器" -ForegroundColor DarkYellow
} else {
    Write-Host "       后端就绪 ✅" -ForegroundColor Green
}

# ── 打开浏览器 ───────────────────────────────────────────────────
$url = "http://localhost:5000/nexus"
Write-Host ""
Write-Host " 正在打开浏览器: $url" -ForegroundColor Cyan
Start-Process $url

Write-Host ""
Write-Host " ┌──────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host " │  前端入口 : http://localhost:5000/nexus           │" -ForegroundColor Cyan
Write-Host " │  停止服务 : docker compose down                  │" -ForegroundColor Cyan
Write-Host " │  查看日志 : docker compose logs -f               │" -ForegroundColor Cyan
Write-Host " └──────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""
Read-Host "按 Enter 退出"
