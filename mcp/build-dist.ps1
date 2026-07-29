<#
.SYNOPSIS
  重新打包 OntoTwin MCP 发行包（干净的文件夹 + zip），供分发给使用者。

.DESCRIPTION
  从当前 mcp/ 目录挑出「使用者需要的」文件（包代码 + install.ps1 + skill + 样例 + 文档），
  剔除 tests / __pycache__ / *.egg-info 等构建缓存，复制到输出目录并压成 zip。
  改完 mcp/ 里的代码或文档后，跑一次本脚本即可重出发行包。

.PARAMETER OutDir  输出文件夹，默认 D:\ontotwin-mcp
.PARAMETER Zip     输出 zip 路径，默认 D:\ontotwin-mcp.zip

.EXAMPLE
  .\build-dist.ps1
  .\build-dist.ps1 -OutDir D:\dist\ontotwin-mcp -Zip D:\dist\ontotwin-mcp.zip
#>
[CmdletBinding()]
param(
  [string]$OutDir = "D:\ontotwin-mcp",
  [string]$Zip    = "D:\ontotwin-mcp.zip"
)
$ErrorActionPreference = "Stop"
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path   # 本脚本所在 = mcp/ 目录

# 要打进发行包的项（只装使用者需要的；不含 tests/build-dist.ps1 自身）
$Items = @(
  "ontotwin_mcp", "skills", "sample-data",
  "pyproject.toml", "install.ps1", "selfcheck.py",
  "README.md", "DISTRIBUTION.md", "安装说明.md", "测试指南.md"
)

Write-Host "源: $Src"
Write-Host "打包到: $OutDir"

New-Item -ItemType Directory -Force $OutDir | Out-Null
# 清空旧内容（顶层目录可能受保护无法删除，故只清内容，best-effort）
Get-ChildItem $OutDir -Force -ErrorAction SilentlyContinue |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

foreach ($i in $Items) {
  $p = Join-Path $Src $i
  if (Test-Path $p) {
    Copy-Item $p $OutDir -Recurse -Force
  } else {
    Write-Host "  跳过（不存在）: $i" -ForegroundColor Yellow
  }
}

# 剔除构建/缓存产物
Get-ChildItem $OutDir -Recurse -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -eq "__pycache__" -or $_.Name -like "*.egg-info" } |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 压 zip
Compress-Archive -Path "$OutDir\*" -DestinationPath $Zip -Force

$kb = (Get-Item $Zip).Length / 1KB
Write-Host ""
Write-Host "完成 ✔" -ForegroundColor Green
Write-Host ("  发行包: {0}" -f $OutDir)
Write-Host ("  zip:    {0}  ({1:N0} KB)" -f $Zip, $kb)
Write-Host "  顶层文件:"
Get-ChildItem $OutDir | ForEach-Object { Write-Host ("    {0}" -f $_.Name) }
Write-Host ""
Write-Host "发给别人：把 $Zip 发过去，对方解压后跑 install.ps1（见包内 安装说明.md）。"
