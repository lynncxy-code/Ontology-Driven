# OntoTwin MCP — 给使用者的快速上手

把 OntoTwin 数字孪生平台的能力接进你的 AI（Claude Code / Cursor / Codex / 任何支持 MCP 的工具），让 AI 直接查场景、建孪生、改状态。

## 一、你会拿到什么

一个 `mcp/` 文件夹（或它的 zip），里面有：
- `ontotwin_mcp/` —— MCP server 代码（Python 包）
- `install.ps1` —— Windows 一键安装器
- `skills/ontotwin-nexus/` —— 给 Claude Code 的编排 skill
- `README.md` / 本文件

## 二、前置条件

1. **Python 3.10+**（`python --version` 能跑，且在 PATH 里）。
2. **能连到 Nexus 后端**。默认指向 `http://192.168.88.66:5000`。
   - 只读工具（查场景/实例/图谱）：后端在跑就行。
   - 写工具（建项目/标定/绑定/铸造/改状态）：后端需部署过 **M0**（dry_run / 项目校验才生效）。
3. 一个支持 MCP 的 AI 客户端（下面列了主流几个）。

## 三、一键安装（Windows）

```powershell
cd mcp
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

想先看它会做什么、不真改：加 `-DryRun`。
后端不在默认地址：`-NexusUrl http://你的IP:5000`。
限制 AI 可读取/上传的本机目录（**强烈建议**，见第六节安全警告）：`-AllowedRoots "D:\nexus-data"`。

脚本会自动：
1. `pip install` 这个包（`python -m ontotwin_mcp` 可用）
2. 检测并注册进 **Claude Code / Cursor / Codex CLI**（各自配置格式）
3. 把 `ontotwin-nexus` skill 拷进 `~/.claude/skills/`（Claude Code 专属，自动触发）
4. 打印一段**通用配置**（JSON + TOML），供其他 MCP 客户端手动粘贴

装完**重启你的 AI 客户端**，就能看到 `ontotwin` 的 30 个工具。

## 四、各客户端怎么用

| 客户端 | 脚本自动注册 | 配置位置 |
| :-- | :-- | :-- |
| **Claude Code** | ✅（`claude mcp add`）+ skill | `~/.claude.json` |
| **Cursor** | ✅ | `~/.cursor/mcp.json` |
| **Codex CLI** | ✅（TOML） | `~/.codex/config.toml` |
| **Windsurf / Cline / Continue / 其他** | ⚠ 手动 | 把脚本打印的通用 config 粘进各自的 MCP 配置 |

### 关于 DeepSeek 等模型
DeepSeek、GPT 这些是**模型**，不是 MCP 客户端。你在**支持 MCP 的客户端**里把模型选成 DeepSeek（如 Cline / Continue / Cursor 里换模型），这个 MCP server 一样能被那个模型调用——注册进客户端即可，跟用哪个模型无关。

## 五、通用配置（手动粘贴给其他客户端）

**JSON 客户端**（Cursor / Windsurf / Cline / Continue…）：
```json
{
  "mcpServers": {
    "ontotwin": {
      "command": "python",
      "args": ["-m", "ontotwin_mcp"],
      "env": { "NEXUS_BASE_URL": "http://192.168.88.66:5000" }
    }
  }
}
```
> 建议把 `"command": "python"` 换成你 python 的绝对路径（`where python` 查），避免客户端进程 PATH 找不到。

**TOML 客户端**（Codex…）：
```toml
[mcp_servers.ontotwin]
command = "python"
args = ["-m", "ontotwin_mcp"]
env = { NEXUS_BASE_URL = "http://192.168.88.66:5000" }
```

## 六、环境变量

| 变量 | 默认 | 说明 |
| :-- | :-- | :-- |
| `NEXUS_BASE_URL` | `http://192.168.88.66:5000` | Nexus 后端地址 |
| `NEXUS_ALLOWED_ROOTS` | 空（不限制） | 文件上传工具允许读取的本机目录（`;` 分隔）。⚠ **见下方安全警告** |
| `NEXUS_TRUST_ENV` | `0` | 默认绕过系统代理直连内网 Nexus；置 `1` 才走系统代理 |
| `NEXUS_TIMEOUT_READ` 等 | 30/5/60/120 | 分级超时（秒） |

> ⚠️ **安全警告 —— `NEXUS_ALLOWED_ROOTS` 是本地文件读取授权，不只是配置建议。**
> 留空（默认）= **不限制** = 授予了「AI 可读取本机任意 `.csv`/`.dxf` 文件并上传到 Nexus」的权限。
> 一旦某个客户端把本 server 的上传类工具（`import_ontology_csv` / `parse_cad_dxf` / `upload_roster`）设为自动运行，AI 就能在无人确认下读走本机任意路径的 CSV/DXF。
> **生产环境或给他人使用时，务必设置为最小目录**，例如 `NEXUS_ALLOWED_ROOTS=D:\nexus-data`；
> 用 `install.ps1` 时加 `-AllowedRoots "D:\nexus-data"` 会自动写进各客户端配置。

## 七、排错

- **工具全部超时** → 多半是本机装了 clash/VPN 代理把内网请求也走了代理。本 server 默认 `trust_env=False` 已绕过；若你手动设了 `NEXUS_TRUST_ENV=1` 请去掉。
- **后端不可达** → 确认 `NEXUS_BASE_URL` 能 ping/curl 通；浏览器开 `<url>/nexus` 应出页面。
- **写工具报「无激活项目」** → 先让 AI 调 `activate_project` 激活一个真实项目（内置 demo 是只读的）。
- **写工具 dry_run/项目校验不生效** → 后端还没部署 M0，联系后端负责人升级。
- **客户端看不到工具** → 重启客户端；确认 `python -m ontotwin_mcp` 在命令行能启动（Ctrl+C 退出）。

## 八、它能干什么（一句话）

30 个工具覆盖：查项目/实例/场景快照/本体图谱、导本体、CAD 标定、实例绑定与铸造、改运行状态。配 `ontotwin-nexus` skill，Claude Code 能自己按「类型→构件→实例→运行」四段流水线端到端搭一个孪生。详见 `README.md`。
