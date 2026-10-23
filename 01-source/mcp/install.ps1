<#
.SYNOPSIS
  OntoTwin MCP 一键安装器（Windows）——把本机的 MCP server 注册进主流 AI 客户端。

.DESCRIPTION
  MCP server 本身通用（python -m ontotwin_mcp，走 stdio）。本脚本做四件事：
    1. pip 安装 ontotwin-mcp 包
    2. 自动注册进已检测到的客户端：Claude Code / Cursor / Codex CLI（各自格式）
    3. 把 ontotwin-nexus skill 拷进 ~/.claude/skills/（Claude Code 专属）
    4. 打印一段通用 config（JSON + TOML），供 Windsurf / Cline / Continue 等任何其他 MCP 客户端手动粘贴
  DeepSeek 等「模型」通过支持 MCP 的客户端（如 Cline/Continue/Cursor 选 DeepSeek 模型）间接使用——注册进这些客户端即可。

.PARAMETER NexusUrl
  Nexus 后端地址，默认 http://192.168.88.66:5000（需已部署含 M0 的后端；写工具要 M0）。

.PARAMETER DryRun
  只打印将要做什么，不真正安装/写配置。

.PARAMETER AllowedRoots
  可选。限制 AI 可读取/上传的本机目录（分号分隔，写入各客户端 env 的
  NEXUS_ALLOWED_ROOTS）。不传 = 不限制 = 授予「AI 可读本机任意 .csv/.dxf 并上传」。
  生产/共享环境务必用它限制，如 -AllowedRoots "D:\nexus-data"。

.EXAMPLE
  .\install.ps1
  .\install.ps1 -NexusUrl http://10.0.0.9:5000
  .\install.ps1 -AllowedRoots "D:\nexus-data"
  .\install.ps1 -DryRun
#>
[CmdletBinding()]
param(
  [string]$NexusUrl = "http://192.168.88.66:5000",
  [string]$AllowedRoots = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tag = if ($DryRun) { "[DryRun] " } else { "" }

function Info($m){ Write-Host "$Tag$m" }
function Ok($m){ Write-Host "$Tag  OK  $m" -ForegroundColor Green }
function Warn($m){ Write-Host "$Tag  --  $m" -ForegroundColor Yellow }

# ── 0. Python ───────────────────────────────────────────────────────────
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { throw "未找到 python，请先安装 Python 3.10+ 并加入 PATH。" }
& python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "需要 Python 3.10+。" }
Info "Python: $py"

# 服务器命令统一用这个 python 的绝对路径，避免客户端进程 PATH 问题
$PyExe = $py

# ── 1. pip 安装包 ───────────────────────────────────────────────────────
Info "安装 ontotwin-mcp 包（源目录: $ScriptDir）..."
if (-not $DryRun) {
  & python -m pip install --quiet "$ScriptDir"
  if ($LASTEXITCODE -ne 0) { throw "pip install 失败。" }
}
Ok "包已安装（python -m ontotwin_mcp 可用）"

# ── 服务器定义（各客户端共用）──────────────────────────────────────────
$ServerName = "ontotwin"
$ServerArgs = @("-m", "ontotwin_mcp")
$Env = [ordered]@{ NEXUS_BASE_URL = $NexusUrl }
if ($AllowedRoots) { $Env["NEXUS_ALLOWED_ROOTS"] = $AllowedRoots }

# 通用 JSON server 对象
$ServerJson = [ordered]@{ command = $PyExe; args = $ServerArgs; env = $Env }

# ── 通用 JSON 配置合并（Claude Code fallback / Cursor）────────────────────
# 铁律：绝不因解析失败而清空用户配置。返回 $true=已合并/$false=已跳过（未改文件）。
function Merge-JsonMcp($path) {
  $dir = Split-Path $path
  if (-not $DryRun -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

  $cfg = $null
  if (Test-Path $path) {
    $raw = Get-Content $path -Raw -Encoding UTF8
    if ($raw -and $raw.Trim()) {
      try {
        $cfg = $raw | ConvertFrom-Json
      } catch {
        # 解析失败：绝不覆盖原文件，跳过该客户端并提示用户手动配。
        Warn "配置文件解析失败（非法 JSON），已跳过以避免覆盖: $path"
        Warn "请手动把下方「通用配置」JSON 里的 $ServerName 项加进该文件的 mcpServers。"
        return $false
      }
      # 顶层必须是 JSON 对象，否则不硬塞。
      if ($cfg -isnot [pscustomobject] -and $cfg -isnot [hashtable]) {
        Warn "配置文件顶层不是 JSON 对象，已跳过以避免破坏: $path"
        return $false
      }
    }
  }
  if ($null -eq $cfg) { $cfg = [pscustomobject]@{} }

  if (-not ($cfg.PSObject.Properties.Name -contains "mcpServers")) {
    $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) -Force
  } elseif ($null -eq $cfg.mcpServers -or ($cfg.mcpServers -isnot [pscustomobject] -and $cfg.mcpServers -isnot [hashtable])) {
    # mcpServers 存在但不是对象（如被误写成字符串/数组）→ 跳过，别硬塞。
    Warn "配置文件里 mcpServers 不是对象，已跳过以避免破坏: $path"
    return $false
  }
  $cfg.mcpServers | Add-Member -NotePropertyName $ServerName -NotePropertyValue ([pscustomobject]$ServerJson) -Force
  $json = $cfg | ConvertTo-Json -Depth 12

  if ($DryRun) {
    Info "将写入 $path :"; Write-Host $json
    return $true
  }

  # 写前备份原文件（若存在），再原子替换（temp → Move-Item -Force）。
  if (Test-Path $path) {
    $bak = "$path.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -Path $path -Destination $bak -Force
    Info "已备份原配置到 $bak"
  }
  $tmp = "$path.tmp-$(Get-Date -Format 'yyyyMMddHHmmssfff')"
  # 无 BOM UTF-8：PS 5.1 的 Set-Content -Encoding UTF8 会写 BOM，
  # 而严格 JSON 解析器读到 BOM 可能报错（正是「安装器砸用户配置」隐患）。
  [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding($false)))
  Move-Item -Path $tmp -Destination $path -Force
  return $true
}

# ── 2a. Claude Code ─────────────────────────────────────────────────────
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if ($claude) {
  Info "检测到 Claude Code CLI，注册（user 作用域）..."
  if ($DryRun) {
    Info "将执行: claude mcp add --scope user $ServerName -e NEXUS_BASE_URL=$NexusUrl$(if($AllowedRoots){" -e NEXUS_ALLOWED_ROOTS=$AllowedRoots"}) -- $PyExe -m ontotwin_mcp"
    Ok "Claude Code 将注册（claude mcp add）"
  } else {
    # 组装 -e 参数（含可选 NEXUS_ALLOWED_ROOTS）
    $eArgs = @("-e", "NEXUS_BASE_URL=$NexusUrl")
    if ($AllowedRoots) { $eArgs += @("-e", "NEXUS_ALLOWED_ROOTS=$AllowedRoots") }
    # 先尝试直接 add，不吞诊断；重复时再 remove 后重试，两步都检查退出码。
    $addOut = & claude mcp add --scope user $ServerName @eArgs -- $PyExe -m ontotwin_mcp
    if ($LASTEXITCODE -ne 0) {
      Info "直接 add 失败（可能已存在同名），尝试先 remove 再 add..."
      $rmOut = & claude mcp remove --scope user $ServerName
      if ($LASTEXITCODE -ne 0) {
        Warn "claude mcp remove 失败（退出码 $LASTEXITCODE）: $rmOut"
      }
      $addOut = & claude mcp add --scope user $ServerName @eArgs -- $PyExe -m ontotwin_mcp
    }
    if ($LASTEXITCODE -eq 0) {
      Ok "Claude Code 已注册（claude mcp add）"
    } else {
      Warn "Claude Code 注册失败（退出码 $LASTEXITCODE）: $addOut"
      Warn "请用文末「通用配置」JSON 手动加进 ~/.claude.json 的 mcpServers。"
    }
  }
} else {
  $claudeJson = Join-Path $HOME ".claude.json"
  Warn "未检测到 claude CLI，改写 $claudeJson 的 mcpServers"
  if (Merge-JsonMcp $claudeJson) { Ok "Claude Code 配置已合并" }
}

# ── 2b. Cursor ──────────────────────────────────────────────────────────
$cursorDir = Join-Path $HOME ".cursor"
$cursorJson = Join-Path $cursorDir "mcp.json"
if ((Test-Path $cursorDir) -or $DryRun) {
  Info "注册 Cursor: $cursorJson"
  if (Merge-JsonMcp $cursorJson) { Ok "Cursor 已注册" }
} else {
  Warn "未检测到 Cursor（无 ~/.cursor），跳过；见文末通用 config"
}

# ── 2c. Codex CLI（TOML）────────────────────────────────────────────────
# TOML 基本转义：反斜杠 → \\，双引号 → \"（顺序：先反斜杠再双引号）。
function Escape-Toml($s) { ($s -replace '\\','\\') -replace '"','\"' }

$codexDir = Join-Path $HOME ".codex"
$codexToml = Join-Path $codexDir "config.toml"
$argsToml = ($ServerArgs | ForEach-Object { "`"$(Escape-Toml $_)`"" }) -join ", "
$envToml = "NEXUS_BASE_URL = `"$(Escape-Toml $NexusUrl)`""
if ($AllowedRoots) { $envToml += ", NEXUS_ALLOWED_ROOTS = `"$(Escape-Toml $AllowedRoots)`"" }
$codexBlock = @"

[mcp_servers.$ServerName]
command = "$(Escape-Toml $PyExe)"
args = [$argsToml]
env = { $envToml }
"@
if ((Test-Path $codexDir) -or $DryRun) {
  Info "注册 Codex CLI: $codexToml"
  if ($DryRun) {
    Info "将追加 TOML 块:"; Write-Host $codexBlock
  } else {
    if (-not (Test-Path $codexDir)) { New-Item -ItemType Directory -Force -Path $codexDir | Out-Null }
    $existing = if (Test-Path $codexToml) { Get-Content $codexToml -Raw -Encoding UTF8 } else { "" }
    # 重复检测同时匹配 [mcp_servers.ontotwin] 与 [mcp_servers."ontotwin"]（允许周围空白）。
    if ($existing -match "(?m)^\s*\[mcp_servers\.(`"$ServerName`"|$ServerName)\]\s*$") {
      Warn "config.toml 已有 [mcp_servers.$ServerName]，跳过（避免重复；如需更新请手动改）"
    } else {
      if (Test-Path $codexToml) {
        # 已有文件：先备份，再 Add-Content 追加（追加不会给已有文件另加 BOM）。
        $codexBak = "$codexToml.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item -Path $codexToml -Destination $codexBak -Force
        Info "已备份 config.toml 到 $codexBak"
        Add-Content -Path $codexToml -Value $codexBlock -Encoding UTF8
      } else {
        # 新建 config.toml：写无 BOM UTF-8（PS 5.1 的 -Encoding UTF8 会给新文件加 BOM，
        # 而 TOML 解析器遇 BOM 可能报错）。
        [System.IO.File]::WriteAllText($codexToml, $codexBlock, (New-Object System.Text.UTF8Encoding($false)))
      }
      Ok "Codex CLI 已注册（追加 TOML 块）"
    }
  }
} else {
  Warn "未检测到 Codex CLI（无 ~/.codex），跳过；见文末通用 config"
}

# ── 3. Skill（Claude Code 专属）─────────────────────────────────────────
$skillSrc = Join-Path $ScriptDir "skills\ontotwin-nexus"
$skillDst = Join-Path $HOME ".claude\skills\ontotwin-nexus"
if (Test-Path $skillSrc) {
  Info "安装 skill: $skillSrc -> $skillDst"
  if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Split-Path $skillDst) | Out-Null
    Copy-Item -Path $skillSrc -Destination $skillDst -Recurse -Force
  }
  Ok "ontotwin-nexus skill 已安装（Claude Code 自动触发）"
} else {
  Warn "未找到 skill 源目录 $skillSrc，跳过"
}

# ── 4. 通用兜底 config（其他 MCP 客户端手动粘贴）──────────────────────────
$genericJson = @{ mcpServers = @{ $ServerName = $ServerJson } } | ConvertTo-Json -Depth 12
Write-Host ""
Write-Host "==================== 通用配置（其他 MCP 客户端手动粘贴）====================" -ForegroundColor Cyan
Write-Host "Windsurf(~/.codeium/windsurf/mcp_config.json) / Cline / Continue 等 —— JSON 客户端用这段："
Write-Host $genericJson
Write-Host ""
Write-Host "Codex 等 TOML 客户端用这段："
Write-Host $codexBlock.Trim()
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""
Info "完成。已注册的客户端请重启后即可看到 $($ServerName) 的 30 个工具。"
Info "后端地址 NEXUS_BASE_URL = $NexusUrl（写工具需后端已部署 M0）。"
Info "本机装了 clash/VPN 代理也没关系：MCP 默认 trust_env=False 绕过代理直连内网 Nexus。"

# ── 安全提示（本地文件读取授权，务必阅读）────────────────────────────────
Write-Host ""
Write-Host "==================== 安全提示（务必阅读）====================" -ForegroundColor Red
if ($AllowedRoots) {
  Write-Host "  已限制文件读取范围 NEXUS_ALLOWED_ROOTS = $AllowedRoots" -ForegroundColor Green
  Write-Host "  AI 只能读取/上传该目录下的 .csv/.dxf 文件。" -ForegroundColor Green
} else {
  Write-Host "  未设置 -AllowedRoots：默认【不限制】文件读取范围！" -ForegroundColor Red
  Write-Host "  这等于授予了「AI 可读取本机任意 .csv/.dxf 文件并上传到 Nexus」的权限。" -ForegroundColor Red
  Write-Host "  生产环境或给他人使用时，务必用 -AllowedRoots 限制，例如：" -ForegroundColor Yellow
  Write-Host "    .\install.ps1 -AllowedRoots `"D:\nexus-data`"" -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor Red
