# OntoTwin 3.6 Pixel Streaming 本机推流 Spike (PRD)

> 状态：开发完成，待关闭 VPN 后手动连通验收
> 主线：OntoTwin Nexus / UE Runtime / Pixel Streaming
> 日期：2026-07-09
> 前置：3.5 Runtime Editor 基线
> 目标版本：3.6 Spike

---

## 1. 背景与目标

当前“实例运维与监控”页面已经能查看实例列表、状态快照和下发 Override，但用户仍需要在 UE 窗口与 Web 页面之间来回切换，才能直观看到当前激活数据集在三维运行时中的变化。

3.6 的目标不是完成云渲染平台，而是先用最小改动验证 Pixel Streaming 链路：

```text
当前激活数据集
  -> UE Development exe 运行 OntoTwinSync
  -> Pixel Streaming 默认 player 接收画面
  -> 实例运维与监控页面嵌入该画面
```

第一轮验收只要求“能看到本机 UE Runtime 推流画面”，并确保现有实例状态帧与 Override 功能不被破坏。

---

## 2. 核心决策

- 从 `runtime-editor` 已提交基线创建 spike 分支，建议分支名：`codex/pixel-streaming-instance-spike`。
- 第一轮只做本机验证，不上云。
- UE 运行体使用打包后的 Development exe，不以 UE Editor PIE 作为第一验收形态。
- Pixel Streaming player 使用 Epic 默认 player 页面，直接用 iframe 嵌入，不复制 player 源码到 `frontend/`。
- Nexus 不自动启动 UE exe 或 Pixel Streaming 服务，第一轮全部手动启动。
- 推流地址属于本机运行环境配置，使用 `localStorage` 保存，不写入项目 JSON 或后端存储。
- 推流窗口是场景级运行时画面，不是实例级视频流。
- 第一轮允许默认 player 转发键鼠输入，但仅标注为本机调试输入，不作为最终权限模型。

---

## 3. 范围

### 3.1 本轮做

- 在“实例运维与监控”页面右侧主区域顶部增加“运行时画面”区域。
- 运行时画面始终显示，即使尚未选中实例也显示。
- 支持输入本机 Pixel Streaming player 地址，例如 `http://127.0.0.1:8888/`。
- 支持连接、断开、清空地址、全屏和新窗口打开。
- 连接成功后把地址保存到 `localStorage`。
- 页面再次打开时，如果存在上次地址，则自动恢复并加载。
- 只显示轻量连接状态：未连接/未设置地址、正在加载、已加载推流页面、加载失败。
- 运行时画面区域显示只读上下文：当前激活数据集、当前选中实例。
- 保留现有状态帧 JSON、Override 面板、实例列表和投产流程。
- 第一轮手动启动 Flask、Pixel Streaming 服务和 UE Development exe。

### 3.2 本轮不做

- 不做云端 GPU 部署。
- 不做 TURN、SFU、HTTPS、域名和公网穿透。
- 不做多用户并发。
- 不做 UE exe 或 Pixel Streaming 服务自动拉起。
- 不新增后端进程管理器。
- 不新增后端存储字段。
- 不修改 `ProjectStore` 文件格式。
- 不把推流 URL 写入数据集、项目 JSON 或数据库。
- 不自研 WebRTC player。
- 不检测真实 WebRTC 连接状态。
- 不做实例选中后自动聚焦或高亮 UE。
- 不做权限化输入。
- 不做鼠标移动物体的最终产品交互。
- 不改现有前端路由。

---

## 4. 目标架构

```text
本机开发环境

Flask 后端
  http://127.0.0.1:5000
  - 当前激活数据集
  - /api/v2/state/snapshots
  - /api/v2/state/override

UE Development exe
  - 放置 TwinSceneManager
  - SceneId 留空时跟随后端当前激活数据集
  - 轮询 /api/v2/state/snapshots
  - 渲染 OntoTwin 实例场景

Pixel Streaming 服务
  - Signalling / Web Server
  - 默认 player 页面
  - 本机 URL，例如 http://127.0.0.1:8888/

Nexus 前端
  /instance
  - 顶部嵌入 Pixel Streaming iframe
  - 下方保留状态帧与 Override
```

Nexus 页面不是运行 UE 的地方。UE Runtime exe 才是三维运行时，Pixel Streaming 只负责把该 exe 的视口画面送到浏览器。

---

## 5. 用户流程

1. 用户提交并确认 `runtime-editor` 基线。
2. 从该基线创建 `codex/pixel-streaming-instance-spike` 分支。
3. 用户启动 Flask 后端。
4. 用户启动本机 Pixel Streaming Signalling / Web Server。
5. 用户启动 UE Development exe，并开启 Pixel Streaming。
6. UE Runtime 里的 `TwinSceneManager` 跟随后端当前激活数据集，生成运行时孪生实例。
7. 用户打开 Nexus 的“实例运维与监控”页面。
8. 页面右侧顶部显示“运行时画面”区域。
9. 如果 `localStorage` 中已有上次推流地址，页面自动加载该地址。
10. 如果没有上次地址，用户输入本机 player URL 并点击连接。
11. iframe 加载 Pixel Streaming 默认 player，用户能看到 UE Runtime 画面。
12. 用户可以点击全屏放大运行时画面，也可以新窗口打开 player 页面。
13. 用户选择左侧实例时，下方状态帧与 Override 继续按原逻辑工作；顶部运行时画面不重建、不切流。

---

## 6. 前端需求

### 6.1 放置位置

运行时画面放在 `frontend/instance.html` 右侧主区域顶部。

推荐布局：

```text
右侧主区域
  运行时画面
    标题 / 当前上下文 / 状态 / 操作按钮
    Pixel Streaming iframe

  下方现有区域
    状态帧 JSON
    Override 面板
```

运行时画面不依赖 `selectedInst`。未选中实例时也显示；选中实例只影响上下文提示和下方监控内容。

### 6.2 尺寸

- iframe 容器严格保持 `16:9`，与默认 `1280×720` runtime 分辨率一致，避免超宽容器产生左右黑边。
- 普通模式宽度取右侧可用宽度、`1120px` 和约 `103vh` 三者的最小值，在画面尺寸与下方监控可见性之间平衡。
- 不应把下方状态帧与 Override 挤出可见范围。
- 全屏时放大整个运行时画面容器，而不是只放大 iframe 元素。

### 6.3 地址与本地保存

推荐 localStorage key：

```text
ontotwin.pixelStreaming.url
```

行为：

- 首次打开页面时，地址输入框可预填 `http://127.0.0.1:8888/`，但没有保存地址时不强制自动连接。
- 用户点击连接后：
  - trim 地址。
  - 写入 `localStorage`。
  - 设置 iframe `src`。
  - 状态进入“正在加载”。
- iframe `load` 事件触发后，状态显示“已加载推流页面”。
- iframe `error` 或超时后，状态显示“加载失败，请检查本机推流服务”。
- 页面再次打开时，若存在保存地址，自动设置 iframe `src`。
- 断开只清空 iframe `src`，不关闭 UE exe，不关闭 Pixel Streaming 服务。
- 清空地址同时移除 `localStorage` 中的地址，并清空输入框。

### 6.4 操作按钮

运行时画面区域至少包含：

- 连接
- 断开
- 清空地址
- 新窗口
- 全屏

按钮样式遵循现有 OntoTwin 极简黑白灰风格。语义色只用于小面积状态提示，不做大块彩色面板。

### 6.5 iframe 属性

推荐属性：

```html
<iframe
  allow="fullscreen; autoplay; clipboard-read; clipboard-write; gamepad"
  allowfullscreen
></iframe>
```

当 `/instance` 运行在 Nexus 的外层 sandbox iframe 内时，外层必须包含 `allow-pointer-lock`。否则键盘输入可以进入 player，但需要相对位移的鼠标视角控制会被浏览器拦截。

若默认 player 页面因安全头或跨域策略不允许被 iframe 嵌入，本轮不强行改 Nexus 架构，先使用“新窗口打开”作为保底路径，再评估是否需要调整 Pixel Streaming Web Server 配置。

### 6.6 连接状态

第一轮仅显示父页面能可靠判断的状态：

```text
未连接 / 未设置地址
正在加载
已加载推流页面
加载失败，请检查本机推流服务
```

不得把“iframe 已加载”展示为“UE 已连接”或“视频正常”，因为父页面无法可靠读取默认 player 内部的 WebRTC 状态。

### 6.7 当前上下文

运行时画面标题栏显示只读上下文：

```text
当前激活数据集：<dataset.name>
当前实例：<selectedInst.id> / <currentSnap.objectTypeName>
```

数据来源：

- 当前激活数据集：复用 `GET /api/v2/ontology/datasets`，取 `is_active=true` 的项。
- 当前实例：复用 `selectedInst` 和 `currentSnap`。

上下文只负责提示，不在第一轮驱动 UE 聚焦、高亮或切换视角。

---

## 7. 手动启动约定

第一轮不由 Nexus 页面或 Flask 后端启动任何本机进程。

需要手动启动：

1. Flask 后端。
2. Pixel Streaming Signalling / Web Server。
3. UE Development exe。

本次实现提供仓库内的手动启动脚本，不由 Nexus 页面或 Flask 后端自动拉起进程：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe"
```

脚本使用以下本机约定：

- Pixel Streaming player：`http://127.0.0.1:8888/`
- UE streamer WebSocket：`ws://127.0.0.1:8889`
- SFU 预留端口：`8890`
- 本机 spike 最大 player 数：`1`，避免多个标签页并发协商触发 UE 5.6 经典插件异常
- UE Runtime：启动时通过 `-RuntimeExe` 显式指定，不设置项目级默认值
- UE 参数：`-RenderOffscreen -ForceRes -ResX=1280 -ResY=720 -AudioMixer -PixelStreamingURL=ws://127.0.0.1:8889 -ExecCmds=DisableAllScreenMessages -log -httpproxy=`

完整预检、状态、停止与验收命令见 `scripts/pixel_streaming/README.md`。

---

## 8. 输入策略

第一轮使用默认 Pixel Streaming player，因此允许默认键鼠输入进入 UE Runtime。

页面需要在运行时画面区域标注：

```text
本机调试输入
```

含义：

- 这是 spike 阶段用于快速验证推流和基础交互感的输入通道。
- 它不是最终权限模型。
- 它不承诺只能移动对象，也不承诺屏蔽其他 UE 输入。

后续产品化交互应改为语义化命令：

```json
{
  "action": "focus_instance",
  "instance_id": "truck_3"
}
```

或：

```json
{
  "action": "move_object",
  "instance_id": "truck_3",
  "delta": [10, 0, 0]
}
```

这些命令需要由 UE 侧和后端共同校验权限，不能只靠前端隐藏按钮。

---

## 9. 数据与存储约束

本轮不得修改以下结构：

- `ProjectStore` 项目文件格式。
- `backend/data/projects/*.json` 的业务字段。
- `mapping_rules.json`。
- Lite 线的 SQLite 表。

本轮唯一允许新增的持久化是浏览器本地的 `localStorage`。

推流 URL 是本机环境配置，不属于当前激活数据集，也不属于项目事实数据。

---

## 10. 验收标准

### 10.1 功能验收

- 从 `runtime-editor` 已提交基线创建 `codex/pixel-streaming-instance-spike` 分支。
- 本机手动启动 Flask、Pixel Streaming 服务和 UE Development exe。
- 打开 `/instance` 或 Nexus 壳层里的“实例运维与监控”，右侧顶部能看到运行时画面区域。
- 输入或自动恢复本机推流地址后，iframe 能加载默认 Pixel Streaming player 页面。
- 全屏可用。
- 新窗口打开可用。
- 断开可用。
- 清空地址可用。
- 未选中实例时，运行时画面仍显示。
- 选中实例后，运行时画面不重建、不切流。
- 下方实例状态帧 JSON 仍能轮询更新。
- Override 原功能仍可提交。

### 10.2 非目标验收

以下事项不作为 3.6 第一轮通过条件：

- UE 自动启动。
- Pixel Streaming 服务自动启动。
- 真实 WebRTC 状态检测。
- 多用户并发。
- 云端部署。
- 实例选中后自动聚焦 UE。
- UE 内对象高亮。
- 权限化输入。
- 鼠标移动物体的最终交互闭环。

---

## 11. 风险与处理

### 11.1 iframe 跨域限制

父页面无法读取默认 player 的内部 WebRTC 状态。处理方式：第一轮只显示 iframe 加载状态，不伪装成真实视频连接状态。

### 11.2 默认 player 不允许嵌入

若 Pixel Streaming 默认 player 返回禁止 iframe 嵌入的安全头，第一轮允许退回“新窗口打开”作为验收辅助，并记录需要调整 Web Server 配置或进入自定义 player shell。

### 11.3 本机端口冲突

`5000` 端口归 Flask；Pixel Streaming player 端口以实际服务为准。页面不假定固定端口，只提供默认建议地址。

### 11.4 输入权限误解

默认 player 输入只是本机调试输入。任何生产级权限都必须在后续通过语义化命令、UE 侧校验和后端权限规则实现。

### 11.5 Mixed Content

本轮 Nexus 和 Pixel Streaming 都按本机 HTTP 调试处理。未来如果 Nexus 切到 HTTPS，嵌入 HTTP player 会触发浏览器 mixed content 限制，需要一起切 HTTPS 或改部署拓扑。

---

## 12. 后续待办

- 评估本机运行时启动器：管理 UE exe 路径、启动参数、日志、端口占用和关闭策略。
- 评估 Pixel Streaming 服务启动器：管理 Signalling / Web Server 生命周期。
- 做自定义 player shell 或消息桥，读取真实 WebRTC 状态。
- 实现“选中实例 -> UE 聚焦视角”。
- 实现“选中实例 -> UE 高亮实例”。
- 实现有限动作交互：平面移动、旋转、保存回写。
- 将默认键鼠输入收敛为语义化命令。
- 引入 UE 侧和后端侧权限校验。
- 评估云端 GPU 部署、TURN/SFU、公网访问和并发成本。

---

## 13. 实现备注

建议第一轮只改：

```text
frontend/instance.html
```

可新增的前端状态：

```text
runtimeStreamUrl
runtimeStreamSrc
runtimeStreamStatus
runtimeStreamError
activeDataset
```

可新增的方法：

```text
loadActiveDatasetContext()
connectRuntimeStream()
disconnectRuntimeStream()
clearRuntimeStreamUrl()
openRuntimeStreamWindow()
fullscreenRuntimeStream()
```

不建议第一轮新增后端 API。当前激活数据集上下文可通过 `GET /api/v2/ontology/datasets` 取得。

---

## 14. 2026-07-10 开发记录

### 14.1 已完成

- 已创建分支 `codex/pixel-streaming-instance-spike`。
- `frontend/instance.html` 已增加运行时画面、地址保存/恢复、连接、断开、清空、新窗口和全屏。
- `frontend/nexus.html` 已允许内嵌页面申请全屏和打开 player 新窗口。
- UE 5.6 项目已启用经典 `PixelStreaming` 插件并完成 Development staged build。
- 已准备 UE 5.6 对应的官方 Pixel Streaming Infrastructure 和默认 player。
- 已增加本机启动、状态、停止脚本及手动验收说明。

### 14.2 待手动验收

开发期间 UE 日志能够初始化 Pixel Streaming streamer，但连接本机 WebSocket 时失败；同时原始 TCP 监听没有收到 UE 请求。已确认当时系统开启 VPN 全局模式，会接管或阻断本机回环连接。因此该现象不再作为代码阻塞，关闭 VPN 后按 `scripts/pixel_streaming/README.md` 完成最终连通验收。

后续测试已验证首次连接以及断开后的第二次连接都能完成 ICE；自动化临时终端启动的 UE 会被宿主回收并记录 `ConsoleCtrl RequestExit`，因此最终稳定性验收必须从桌面普通 PowerShell 启动 runtime，并在验收期间保留该终端。

验收前可先运行只读预检：

```powershell
.\scripts\pixel_streaming\Start-LocalPixelStreaming.ps1 -RuntimeExe "D:\path\to\YourProject.exe" -PreflightOnly
```
