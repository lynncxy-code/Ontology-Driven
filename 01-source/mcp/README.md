# OntoTwin Nexus MCP Server

把 Nexus 的读 / 写 / 运维能力（30 个工具）以 **MCP** 暴露给 Claude Code、Cursor 等 AI 客户端。本地 stdio 进程，不 import 后端任何模块，只对 `${NEXUS_BASE_URL}/api/v2` 发 HTTP。工具怎么编排见 `skills/ontotwin-nexus/SKILL.md`。

## 安装

```bash
cd mcp
pip install -e .
```

装完可用三种方式启动（等价）：`ontotwin-mcp`（console script）、`python -m ontotwin_mcp`、`python -m ontotwin_mcp.server`。下文注册统一用 `python -m ontotwin_mcp`。

## 环境变量

| 变量 | 默认 | 说明 |
| :-- | :-- | :-- |
| `NEXUS_BASE_URL` | `http://192.168.88.66:5000` | Nexus 后端地址；尾部斜杠会被自动去掉 |
| `NEXUS_ALLOWED_ROOTS` | 空（不限制） | 上传文件（DXF/CSV）允许的本地根目录，多个用 `;` 分隔；空表示本地开发不限制 |
| `NEXUS_TIMEOUT_CONNECT` | `5` | 连接超时（秒） |
| `NEXUS_TIMEOUT_READ` | `30` | 普通读超时 |
| `NEXUS_TIMEOUT_UPLOAD` | `60` | 上传超时 |
| `NEXUS_TIMEOUT_CADPARSE` | `120` | DXF 解析超时（`parse_cad_dxf` 专用，耗时长） |
| `NEXUS_TRUST_ENV` | `0`（不走代理） | 是否读系统代理（`HTTP(S)_PROXY`/`ALL_PROXY`）。默认 `0` 直连内网 Nexus；置 `1`/`true` 才读系统代理，供确需经代理访问远程 Nexus 的场景 |

分级超时是刻意的：非幂等写超时后结果状态不确定，MCP 侧不自动重试（详见 SKILL「失败自救」）。

## Claude Code 注册

```bash
claude mcp add ontotwin -- python -m ontotwin_mcp
```

带环境变量（`-e KEY=VALUE`，可多次）：

```bash
claude mcp add ontotwin \
  -e NEXUS_BASE_URL=http://192.168.88.66:5000 \
  -e NEXUS_ALLOWED_ROOTS="D:/twin-inputs;D:/cad" \
  -- python -m ontotwin_mcp
```

或写进项目 `.mcp.json` / 用户级 MCP 配置：

```json
{
  "mcpServers": {
    "ontotwin": {
      "command": "python",
      "args": ["-m", "ontotwin_mcp"],
      "env": {
        "NEXUS_BASE_URL": "http://192.168.88.66:5000",
        "NEXUS_ALLOWED_ROOTS": "D:/twin-inputs;D:/cad"
      }
    }
  }
}
```

用 `claude mcp list` 确认已连接。

## Cursor 注册

编辑 `~/.cursor/mcp.json`（或项目级 `.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "ontotwin": {
      "command": "python",
      "args": ["-m", "ontotwin_mcp"],
      "env": {
        "NEXUS_BASE_URL": "http://192.168.88.66:5000",
        "NEXUS_ALLOWED_ROOTS": "D:/twin-inputs;D:/cad"
      }
    }
  }
}
```

保存后在 Cursor 的 Settings → MCP 面板确认服务已加载、工具已列出。

## 人工审批配置（重要）

**MCP 协议本身不强制「写工具必须人工审批」**——是否弹出审批、能否自动运行，完全取决于客户端版本与配置（例如 Cursor 可被设置为自动运行工具）。因此本项目的写安全**不能只依赖客户端审批**：真正的护栏是后端锁内的 `expected_project_id` 原子校验（见设计 spec §5.2）与 SKILL 的黄金铁律。客户端审批只是「兼容客户端**可**提供的额外体验」，不是协议保证。

工具已按操作分级：`read` / `compute` / `stage-write` 相对安全，`persist-write`（落库 / 改全局激活态）为高危。**persist-write 工具默认应关闭自动批准**，逐次人工确认。涉及的 persist-write 工具：`activate_project`、`upload_roster`、`save_components`、`bind_instance`、`bind_instances_batch`、`unbind_instance`、`mint_instances(dry_run=false)`、`set_instance_state`。注意 `upload_roster` 虽是上传 CSV，但后端会把花名册**直接写进当前激活项目**，属 persist-write（应带 `expected_project_id`）。

- **Claude Code**：默认对工具调用逐次询问；避免用 `--dangerously-skip-permissions` / 全局「始终允许」把写工具一次性放行。可在权限设置里对本 server 的读工具批量允许、对上述 persist-write 工具保持每次询问。具体开关名称以所用 Claude Code 版本为准。
- **Cursor**：MCP 工具存在「自动运行 / auto-run」开关。**务必不要**对本 server 开全局自动运行；把上述 persist-write 工具保持为需手动确认。开关位置（Settings → MCP / Tools 下的 auto-run）以所用 Cursor 版本为准。

不确定某客户端当前版本的确切开关位置时，按「宁可多问一次」处理，勿默认放行写工具。

## Skill 安装

把编排手册装进 Claude Code 的 skills 目录（用户级或项目级二选一）：

```bash
# 用户级（对所有项目生效）
cp -r skills/ontotwin-nexus ~/.claude/skills/

# 或项目级
cp -r skills/ontotwin-nexus <你的项目>/.claude/skills/
```

装好后，涉及数字孪生场景、设备实例、坐标标定、本体类型时 Claude Code 会自动触发该 skill。Cursor 无 skill 机制，靠工具 description 自解释：单点操作可用，多步流程需用户多引导。

## 已知边界

- **写工具需后端已部署 M0 扩展**：`mint_instances` 的 `dry_run` 真预览、以及各写工具的 `expected_project_id` 原子校验，都依赖后端两项加法式扩展（spec §14）。后端未部署该扩展时，缺省字段仍是旧行为，但 `dry_run=true` 可能不生效（会真写）、`expected_project_id` 不做校验（防不住写-写竞态）。部署到 88.66（PG 模式）后才完整生效。
- **文件路径是「MCP 进程侧」的本地路径**：上传类工具（`import_ontology_csv` / `parse_cad_dxf` / `upload_roster`）由 MCP 进程读本地文件再组 multipart 上传。容器 / SSH / 远程开发环境下，看到的是运行 MCP 进程那一侧的文件系统，注意路径归属。受 `NEXUS_ALLOWED_ROOTS` 约束。
- **本体 CSV 保留原始文件名**：后端按 basename 识别 6 张表（`objectdef`/`linkdef`/`linksourcetype`/`linktargettype` 必须 + `propertydef`/`hasproperty` 可选），别改名。
- **已注册 3 个二期只读工具（transform / ue_binding_status / spatial_frames）**：位置诊断（`get_instance_transform`）、UE 身份绑定状态（`get_ue_binding_status`）、空间坐标系列举（`list_spatial_frames`）均为只读，已并入 30 个工具中。二期**写**工具（promote_model_binding、transform PUT、spatial 写）按 spec 收敛策略仍暂不开。
- **本机装了代理（clash/VPN）也不影响**：MCP 默认 `trust_env=False` 直连内网 Nexus，已绕过系统代理，无需另设 `NO_PROXY`。若确需经代理访问远程 Nexus，再置 `NEXUS_TRUST_ENV=1`。
