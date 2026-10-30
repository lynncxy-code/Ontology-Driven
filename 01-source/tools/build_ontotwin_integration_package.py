"""Build the OntoTwin UE integration package.

The package deliberately contains no UE project, map, Content, Art, Saved or
Intermediate directory.  It contains the runtime plugin, its glTFRuntime
compile dependency, and an offline local backend runtime archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


SKIP_DIRS = {"Intermediate", "Saved", "DerivedDataCache", ".git", ".vs", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(root: Path) -> str:
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        records.append(f"{rel}\0{sha256(path)}\n")
    return hashlib.sha256("".join(records).encode("utf-8")).hexdigest()


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RuntimeError(f"destination already exists: {destination}")
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*SKIP_DIRS),
        symlinks=False,
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


INSTALL_PS1 = r'''[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [switch]$SkipGltfRuntime
)

$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectFile = (Resolve-Path -LiteralPath $ProjectPath -ErrorAction Stop).Path
if ([IO.Path]::GetExtension($projectFile).ToLowerInvariant() -ne ".uproject") { throw "ProjectPath 必须是 .uproject 文件" }
$projectRoot = Split-Path -Parent $projectFile
$pluginSource = Join-Path $packageRoot "..\Plugins\OntoTwinSync"
$gltfSource = Join-Path $packageRoot "..\Plugins\glTFRuntime"
$pluginTargetRoot = Join-Path $projectRoot "Plugins"
$pluginTarget = Join-Path $pluginTargetRoot "OntoTwinSync"
$backupRoot = Join-Path $projectRoot ".ontotwin-backups\$(Get-Date -Format yyyyMMdd-HHmmss)"

if (-not (Test-Path -LiteralPath $pluginSource -PathType Container)) { throw "接入包缺少 OntoTwinSync" }
if (-not (Test-Path -LiteralPath $pluginTargetRoot -PathType Container)) { New-Item -ItemType Directory -Path $pluginTargetRoot | Out-Null }
$existing = Get-Item -LiteralPath $pluginTarget -Force -ErrorAction SilentlyContinue
if ($null -ne $existing -and $existing.LinkType) { throw "目标 OntoTwinSync 是 Junction/符号链接；请先确认是否要切换为独立插件副本：$pluginTarget" }
$uprojectBackup = Join-Path $backupRoot ([IO.Path]::GetFileName($projectFile))
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
Copy-Item -LiteralPath $projectFile -Destination $uprojectBackup -Force
if ($null -ne $existing) { Move-Item -LiteralPath $pluginTarget -Destination (Join-Path $backupRoot "OntoTwinSync") }
Copy-Item -LiteralPath $pluginSource -Destination $pluginTarget -Recurse

if (-not $SkipGltfRuntime) {
    $gltfTarget = Join-Path $pluginTargetRoot "glTFRuntime"
    if (Test-Path -LiteralPath $gltfTarget -PathType Container) {
        Write-Host "已存在 glTFRuntime，保留目标工程版本：$gltfTarget" -ForegroundColor Yellow
    } elseif (Test-Path -LiteralPath $gltfSource -PathType Container) {
        Copy-Item -LiteralPath $gltfSource -Destination $gltfTarget -Recurse
    }
}

$json = Get-Content -LiteralPath $projectFile -Raw -Encoding UTF8 | ConvertFrom-Json
$plugins = @($json.Plugins)
foreach ($name in @("OntoTwinSync", "glTFRuntime")) {
    if ($name -eq "glTFRuntime" -and $SkipGltfRuntime) { continue }
    $found = $plugins | Where-Object { $_.Name -eq $name } | Select-Object -First 1
    if ($null -eq $found) {
        $plugins += [pscustomobject]@{ Name = $name; Enabled = $true }
    } else {
        $found.Enabled = $true
    }
}
$json.Plugins = $plugins
$json | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $projectFile -Encoding UTF8

$descriptor = Get-Content (Join-Path $pluginTarget "OntoTwinSync.uplugin") -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "已接入 OntoTwinSync $($descriptor.VersionName)" -ForegroundColor Green
Write-Host "工程：$projectFile"
Write-Host "备份：$backupRoot"
Write-Host "下一步：关闭 UE 后重新生成工程文件并编译 Editor Target，然后运行 Start-OntoTwinBackend.ps1。"
'''


START_PS1 = r'''[CmdletBinding()]
param([switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$archive = Join-Path $packageRoot "..\Runtime\ontotwin-runtime-offline.tar"
$runtimeParent = Join-Path $packageRoot "..\Runtime\docker-runtime"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "未找到 Docker。可安装 Docker Desktop，或改用公司已有的 OntoTwin Windows 一体化运行台。" }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Engine 未运行，请先启动 Docker。" }
if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { throw "接入包缺少 Runtime/ontotwin-runtime-offline.tar" }
if (-not (Test-Path -LiteralPath $runtimeParent -PathType Container)) {
    New-Item -ItemType Directory -Path $runtimeParent -Force | Out-Null
    tar -xf $archive -C $runtimeParent
    if ($LASTEXITCODE -ne 0) { throw "离线运行包解压失败" }
}
$runtimeRoot = Get-ChildItem -LiteralPath $runtimeParent -Directory | Where-Object { Test-Path (Join-Path $_.FullName "compose.yaml") } | Select-Object -First 1
if ($null -eq $runtimeRoot) { throw "未找到 compose.yaml" }
$envFile = Join-Path $runtimeRoot.FullName ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item (Join-Path $runtimeRoot.FullName ".env.example") $envFile
    $envText = Get-Content $envFile -Raw
    $envText = $envText -replace "ONTOTWIN_BIND_ADDRESS=.*", "ONTOTWIN_BIND_ADDRESS=127.0.0.1"
    $envText = $envText -replace "POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=ontotwin-local"
    $envText = $envText -replace "NEO4J_PASSWORD=.*", "NEO4J_PASSWORD=ontotwin-local"
    Set-Content -LiteralPath $envFile -Value $envText -Encoding UTF8
}
$images = @(
    @{ Name = "ontotwin-zhhz/postgres:16"; File = "01-ontotwin-zhhz_postgres_16.tar.gz" },
    @{ Name = "ontotwin-zhhz/neo4j:5"; File = "02-ontotwin-zhhz_neo4j_5.tar.gz" },
    @{ Name = "ontotwin-zhhz/backend:1.0.0_amd64"; File = "03-ontotwin-zhhz_backend_1.0.0_amd64.tar.gz" }
)
foreach ($image in $images) {
    docker image inspect $image.Name *> $null
    if ($LASTEXITCODE -ne 0) {
        $imagePath = Join-Path $runtimeRoot.FullName ("images\" + $image.File)
        Write-Host "导入离线镜像：$($image.Name)"
        docker load -i $imagePath
        if ($LASTEXITCODE -ne 0) { throw "镜像导入失败：$($image.Name)" }
    }
}
Push-Location $runtimeRoot.FullName
try {
    docker compose --env-file $envFile -p ontotwin-ue up -d
    if ($LASTEXITCODE -ne 0) { throw "OntoTwin 后端启动失败" }
} finally { Pop-Location }
for ($i = 0; $i -lt 30; $i++) {
    try { Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep -Seconds 2 }
    if ($i -eq 29) { throw "后端未在预期时间内就绪；可运行 Check-OntoTwinBackend.ps1 查看日志" }
}
Write-Host "OntoTwin 后端已就绪：http://127.0.0.1:5000/nexus" -ForegroundColor Green
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:5000/nexus" }
'''


STOP_PS1 = r'''$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeParent = Join-Path $packageRoot "..\Runtime\docker-runtime"
$runtimeRoot = Get-ChildItem -LiteralPath $runtimeParent -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName "compose.yaml") } | Select-Object -First 1
if ($null -eq $runtimeRoot) { Write-Host "本地后端尚未初始化。"; exit 0 }
Push-Location $runtimeRoot.FullName
try { docker compose --env-file (Join-Path $runtimeRoot.FullName ".env") -p ontotwin-ue down } finally { Pop-Location }
'''


CHECK_PS1 = r'''$ErrorActionPreference = "Continue"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeParent = Join-Path $packageRoot "..\Runtime\docker-runtime"
Write-Host "== Docker =="
docker version
$runtimeRoot = Get-ChildItem -LiteralPath $runtimeParent -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName "compose.yaml") } | Select-Object -First 1
if ($null -eq $runtimeRoot) { Write-Host "尚未解压本地运行包；先执行 Start-OntoTwinBackend.ps1"; exit 1 }
Push-Location $runtimeRoot.FullName
try { docker compose --env-file (Join-Path $runtimeRoot.FullName ".env") -p ontotwin-ue ps; Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing -TimeoutSec 5 | Select-Object StatusCode } finally { Pop-Location }
'''


README = r'''# OntoTwin UE 接入包

这是一个“插件 + 本地后端运行台 + 资产回洗规则”的接入包，**不包含任何 UE 工程、关卡、Content、Art 或业务数据**。

## 里面有什么

- `Plugins/OntoTwinSync`：OntoTwin UE5.6 插件（含源码、编辑器工具、字体和可复用构建产物）。
- `Plugins/glTFRuntime`：OntoTwinSync 的必要编译依赖；如果目标项目已有该插件，安装脚本会保留目标版本。
- `Runtime/ontotwin-runtime-offline.tar`：离线本地后台，内含 OntoTwin 后端、PostgreSQL 和 Neo4j 镜像。
- `Tools/Install-OntoTwinPlugin.ps1`：把插件接入现有 `.uproject`，自动备份原插件和 `.uproject`。
- `Tools/Start-OntoTwinBackend.ps1` / `Stop-OntoTwinBackend.ps1` / `Check-OntoTwinBackend.ps1`：启动、停止和检查网页后台。
- `Docs/UE资产回洗流程.md`：按设备/家具层级把场景静态资产转成数据库控制资产的门禁规则。
- `Skill-Patch/UE超级管家-接入模式补充.md`：给 UE 超级管家使用的本地后端与资产回洗补充规则。

## 使用顺序

1. 目标机准备 UE 5.6、Visual Studio 2022（含 C++ 桌面开发）和 Docker Desktop/Engine + Compose v2。无需另装 Python、Node.js、PostgreSQL、Neo4j。
2. 先运行 `Tools/Install-OntoTwinPlugin.ps1 -ProjectPath "D:\你的工程\项目.uproject"`。它会备份工程并启用 OntoTwinSync；不要在 UE 正在运行时执行。
3. 关闭 UE，右键 `.uproject` 重新生成工程文件，用 UE5.6 编译 Editor Target，再打开工程。
4. 运行 `Tools/Start-OntoTwinBackend.ps1`。首次会导入包内镜像，随后打开 `http://127.0.0.1:5000/nexus`。
5. 使用 UE 超级管家先扫描关卡、输出回洗计划和 `needs_review` 清单；确认后再写入数据库。源 Actor 默认保留，验收通过后才能清理。

## 边界

- 本包只负责 OntoTwin 接入，不替换目标项目已有资产，不自动复制家具、CAD 底图或地图。
- 后端默认只监听本机 `127.0.0.1:5000`，没有登录鉴权；如需局域网访问，必须由部署人员明确修改网络边界。
- 若目标电脑已经安装公司版 OntoTwin Windows 一体化运行台，可跳过本包的 Docker 后端脚本，直接使用现有本地后台地址。
- 目标项目必须是 UE5.6；其他引擎版本需要单独编译和验收。
'''


REWASH_DOC = r'''# UE 静态资产回洗规则（接入包版）

目标：把已有 UE 工程的设备、家具等静态资产接入 OntoTwin 数据库，而不把建筑壳体和装饰误转成业务实例。

## 默认分类

- 一个有明确父 Actor、由多个可见组件组成的物理装配：一个实例，子组件写入 `render_parts`。
- 独立的桌、椅、柜、设备、摄像头：各自一个实例；相同模型只复用 ObjectType，不合并空间实例。
- 墙、地面、天花、柱、建筑外壳、道路、地形、植物和灯光链路：默认保留为环境壳体，不进入业务实例。
- Blueprint：读取可见 StaticMesh/SkeletalMesh 组件；无法判断物理边界的对象标为 `needs_review`。

## 必须经过的门禁

1. 记录 `.uproject`、Unreal ProjectID、OntoTwin `ue_project_id`、`project_id` 四层身份。
2. 只读扫描并输出 `Types / Instances / Parts / Cleanup GUIDs` 预测矩阵。
3. 先生成 dry-run；核对数量、稳定 ID、世界变换和 `needs_review` 清单。
4. 同一输入和 manifest 才能正式写库，写入后从 API/数据库回读。
5. 先在 UE 冷启动和 PIE 中验收；源 Actor 清理是单独步骤，只按精确 GUID 执行。

不要按名称前缀、文件夹或全量“看起来像家具”的方式自动删除源 Actor。
'''


SKILL_PATCH = r'''# UE 超级管家：OntoTwin UE 接入模式补充

当用户要求“只接入 OntoTwin，不交付 UE 工程”时，使用本接入包作为工作边界：

1. 先检查本地后端：优先使用已安装的 OntoTwin Windows 一体化运行台；没有时启动接入包 `Tools/Start-OntoTwinBackend.ps1`。不要把“插件已复制”报告成“网页后台已就绪”。
2. 插件安装只修改用户明确指定的 `.uproject` 和 `Plugins/`；先备份，不覆盖 Junction/符号链接母本；不复制目标工程的 Content、Art、关卡或 Saved。
3. 资产回洗默认是“扫描 → 分类 → dry-run → 人工确认 → 写库 → UE/PIE 验收 → 可选清理”。设备、家具和摄像头按物理实例拆分；建筑壳体默认排除；歧义项进入 `needs_review`。
4. 每轮必须保存项目身份、数据集 ID、插件版本、后端地址、输入清单和 manifest 哈希。后端不可达时停止在只读扫描，不猜测数据库写入已成功。
5. 源 Actor 清理永远是独立批准步骤，必须有精确 GUID 清单、数据库回读和冷启动残留检查。
'''


def main() -> int:
    # Current packages must rebuild images from the clean commit. The legacy
    # constants above are retained only for document compatibility.
    from integration_bundle import main as build_current
    build_current()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
