# OntoTwin 3.6 本机 Pixel Streaming

这组脚本负责手动启动和停止本机 Pixel Streaming spike。它不接入 Flask 进程管理，也不写入 Nexus 项目数据。

## 固定端口

| 端口 | 用途 | 使用方 |
| --- | --- | --- |
| `5000` | OntoTwin Nexus / Flask | 浏览器、UE OntoTwinSync |
| `8888` | Pixel Streaming player HTTP/WS | Nexus iframe、浏览器 |
| `8889` | Pixel Streaming streamer WebSocket | UE Runtime |
| `8890` | Pixel Streaming SFU 预留 | Signalling Server |

浏览器地址是 `http://127.0.0.1:8888/`；UE 启动参数使用 `-PixelStreamingURL=ws://127.0.0.1:8889`。两者不是同一个端口。

Runtime 默认带 `-ExecCmds=DisableAllScreenMessages`，隐藏 `Print String`、渲染警告等屏幕调试文字，让推流画面保持干净；这些信息仍会写入 UE 日志。

本机 spike 默认 `MaxPlayers=1`。这是为了避免多个已打开的 Nexus 标签页和独立 player 同时触发 WebRTC 协商；需要切换到新窗口时，先断开嵌入画面或关闭其他 player 标签页。

## 前置条件

1. UE 项目启用 `PixelStreaming` 插件，并重新打包 Development Runtime。
2. 已准备 UE 5.6 对应的 `PixelStreamingInfrastructure`，并完成 `npm install` 和 `npm run build:all:cjs`。
3. 默认路径如下，可通过脚本参数覆盖：

```text
D:\tmp\pixel-streaming-infra-UE5.6\PixelStreamingInfrastructure-UE5.6
<YOUR_PACKAGED_UE_RUNTIME.exe>
```

## 使用

只做环境预检，不启动进程：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe" -PreflightOnly
```

启动 Signalling Server 和 UE Runtime：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe"
```

脚本可以重复执行：若完整会话已运行，会直接显示当前进程；若 Signalling Server 仍在但 UE 已退出，会复用现有服务并只补启 UE。

UE Runtime 通过 Windows 原生 `CreateProcess` 以 `DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP` 独立创建，不绑定启动脚本所在的 PowerShell 控制台。关闭终端或临时命令会话不会再向 UE 发送 `ConsoleCtrl RequestExit`。

手动验收时应从桌面上的普通 PowerShell 运行启动脚本，并在验收期间保留该终端窗口。IDE、自动化工具或受管临时终端可能主动回收整个子进程树，即使 UE 已使用 detached flags 启动。

如需显式覆盖连接上限：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe" -MaxPlayers 1
```

启动后同时打开独立 player 页面：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe" -OpenPlayer
```

查看状态和日志位置：

```powershell
.\scripts\pixel_streaming\Get-LocalPixelStreamingStatus.ps1
```

停止这组脚本启动的进程：

```powershell
.\scripts\pixel_streaming\Stop-LocalPixelStreaming.ps1
```

运行状态和 Signalling Server 日志保存在：

```text
%LOCALAPPDATA%\OntoTwin\PixelStreaming
```

## 手动验收

1. 关闭或暂停会接管本机回环流量的 VPN / 全局代理。
2. 启动 Flask，确认 `http://127.0.0.1:5000/nexus` 可访问。
3. 运行预检，再运行启动脚本。
4. 先在新窗口打开 `http://127.0.0.1:8888/`，确认能看到 UE 画面。
5. 进入“实例运维与监控”，连接默认地址，检查嵌入画面、全屏、新窗口、断开和地址恢复。
6. 选择实例并提交一次 Override，确认下方原有监控功能未受影响。

页面中的“已加载推流页面”只代表 iframe 已加载，不能代替 WebRTC 视频状态判断。真实视频是否连通以 player 画面和 Signalling Server 日志为准。

## VPN / 代理说明

UE Pixel Streaming 的 WebSocket 客户端也可能受系统级 VPN、TUN 或全局代理规则影响。若 UE 日志持续显示连接 `ws://127.0.0.1:8889` 失败，而端口已经监听，先关闭全局代理再验收。`NO_PROXY` 不能保证绕过所有 TUN 驱动。

启动脚本会在 UE 命令行末尾添加 `-httpproxy=`，明确覆盖 Unreal `FHttpModule` 读取到的系统 HTTP 代理，保证本机 signalling WebSocket 走直连。空代理参数必须位于末尾，避免 Unreal 把下一个启动参数误读为代理地址。该参数只影响本次 UE Runtime 进程，不修改 Windows 或 VPN 配置。
