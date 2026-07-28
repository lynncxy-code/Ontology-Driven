# OntoTwin 3.7.1 宿主接入与验收

> 更新日期：2026-07-24
> 正式宿主：`D:\ZHHZ\ZHHZ`
> 回归宿主：`D:\tmp_ue\test0316`
> 实现记录：[OntoTwin 3.7.1 实施记录](OntoTwin%203.7.1%20实施记录.md)

本文是 3.7.1 新宿主接入、正式宿主状态、自动化证据与剩余人工验收的唯一维护位置。阶段文档中的中间状态不再单独保留。

## 1. 当前验收结论

- Renderer Spike 技术链路通过。
- 正式宿主已完成插件同步、Editor Development、Game Development、Shipping 编译和 Cook。
- 后端、Web、UE 自动化与打包启动验收通过。
- 正式宿主当前使用 Balanced；High 尚未获得宿主 Postbuffer 授权。
- 人工视觉、输入、视频生命周期、HDR/SDR 和目标 GPU 性能验收仍待完成。
- 在人工项完成前，3.7.1 不标记为最终视觉验收全通过。

## 2. 新宿主接入清单

1. 关闭 UE Editor 和该宿主的运行 EXE。
2. 安装完整 `OntoTwinSync` 插件，并启用 `OntoTwinSync` 与 `glTFRuntime`。
3. 同步插件的 `.uplugin`、`Config`、`Source`、`Content`、`Resources` 和 `README.md`。
4. 不复制其他项目的 `Binaries`、`Intermediate`、地图、GameMode、人物、路线、出生点、锚点或输入配置。
5. 由新宿主冷编译插件。
6. 在实际持久运行关卡中保留恰好一个 `ATwinSceneManager`。
7. 后端不在本机时，配置 Manager 的 `BackendBaseUrl`。
8. 将该宿主自己的 UE Project ID 绑定到目标 OntoTwin 数据集。
9. 先以默认 Balanced 做 PIE、Standalone 和 EXE 验收，再做 Shipping Cook。

插件 Widget、材质和字体不需要复制到宿主 `/Game`；Web 工作台也不保存 UE 工程文件或固定 UE Level。

## 3. 质量档与宿主配置

### 3.1 Balanced（默认）

- 插件同步后可直接运行。
- 不占用 Slate Postbuffer。
- 不要求宿主修改 `DefaultEngine.ini` 或 `DefaultGame.ini`。

### 3.2 Performance

- 由 Web 对 ObjectType 或 Instance 请求。
- 不占用 Slate Postbuffer。
- 不要求宿主配置。

### 3.3 High Screen

High 必须由宿主显式授权。`DefaultEngine.ini`：

```ini
[SystemSettings]
Slate.CopyBackbufferToSlatePostRenderTargets=1
```

`DefaultGame.ini`：

```ini
[/Script/OntoTwinSync.OntoTwinGlassSettings]
bEnableGlassUI=True
bEnableHighQualityRenderer=True
bEnableRendererSpike=False
ReservedPostBufferIndex=0
GaussianBlurStrength=14.000000
```

同时要求：

- 使用 DX12。
- 宿主明确确认 RT0 未被其他 UI 插件占用。
- 配置在进程启动前存在，修改后完整重启。
- Web 选择 High 只表示请求；宿主未授权、RT 冲突或能力不足时自动降级 Balanced，再不支持则降级 Performance。

`RequestedQuality` 只保留为旧载荷和开发诊断的全局默认，不是正常业务配置或 High 授权条件。

## 4. 正式宿主最终状态

已确认：

- UE 5.6，DX12 + SM6。
- `.uproject` 已启用 `OntoTwinSync` 与 `glTFRuntime`。
- 正式运行关卡为 `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto`。
- 持久运行关卡存在 `TwinSceneManager_0`。
- `ueproj_ZHHZ` 已与目标 OntoTwin 数据集匹配。
- 已配置本机 HTTP 代理绕过。
- 2026-07-23 至 2026-07-24 已同步 `.uplugin`、`Config`、`Source`、`Content`、`Resources` 和 `README.md`；源/目标 SHA-256 差异为 0。
- 同步前已备份旧插件，并清除宿主插件旧 `Binaries`、`Intermediate`，未复制回归宿主编译产物。
- 没有修改宿主地图、关卡 Actor、项目输入、路线、出生点或数据绑定。
- High 仍未授权，正式宿主保持 Balanced。

最终交付产物：

- Development：`D:\ZHHZ\Builds\OntoTwin371_E_20260724_Development\Windows`
- Shipping：`D:\ZHHZ\Builds\OntoTwin371_E_20260724_Shipping_v2\Windows`

第一次 Shipping 目录 `D:\ZHHZ\Builds\OntoTwin371_E_20260724_Shipping\Windows` 只保留为 Cook 问题诊断对照，不是最终交付。

## 5. 自动化验收结果

| 范围 | 结果 | 备注 |
| --- | --- | --- |
| UE5.6 回归宿主 Editor Development | 通过 | 包含 Renderer、六模板、B3 与 Gauge 增量 |
| UE5.6 回归宿主 Shipping/Cook/Stage | 通过 | RT0–RT4 材质和字体进入最终包 |
| 正式宿主 Editor Development | 通过 | 插件完成重建和加载 |
| 正式宿主 Game Development | 通过 | 默认地图进入加载 |
| 正式宿主 Shipping | 通过 | Cook 29,323 Packages、58,017 IoStore Chunks |
| Overlay/媒体/ProjectStore | 通过 | 阶段 C 为 24 项；Value/Gauge 最终用例 14/14 |
| Web 内联 JavaScript | 通过 | 条件字段、Trend 禁用、Gauge 回退无语法错误 |
| 浏览器只读/交互检查 | 通过 | 三档、继承、状态/指标配置和结构预览正确，控制台错误 0 |
| DX12 High RT0 | 通过 | 回归宿主 `High → High`，材质加载成功 |
| High 自动降级 | 通过 | 关闭 backbuffer copy 后 `High → Balanced` |
| World 边界 | 通过 | 确定性伪玻璃，不采样 Postbuffer |
| 打包分辨率启动冒烟 | 通过 | 720p、1080p、2K、4K 均完成引擎初始化和地图加载 |

打包启动验证还确认：

- Screen 默认请求 Balanced。
- World 诊断不包含 Postbuffer。
- Inter Regular/SemiBold 与 Noto CJK Regular/Medium 从打包插件目录加载。
- 没有 Fatal Error、Unhandled Exception 或 Crash 目录。
- Shipping 可持续进入运行状态；测试进程由验收脚本终止。

## 6. Renderer Spike 证据

关键诊断结果：

```text
context=Screen requested=High effective=High postbuffer=RT0 rhi=D3D12
material=/OntoTwinSync/UI/RendererSpike/M_OT_GlassHigh_RT0.M_OT_GlassHigh_RT0

context=Screen requested=High effective=Balanced postbuffer=RT0 rhi=D3D12
reason=High downgraded to Balanced: Slate postbuffer backbuffer copy is disabled

context=World requested=High effective=Performance postbuffer=RT0 rhi=D3D12
reason=World Space uses deterministic pseudo-glass and never samples a Slate postbuffer
```

回归宿主日志：

- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassHigh.log`
- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassFallback.log`
- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassQualityTiers.log`

Spike Shipping Stage：`D:\tmp_ue\test0316\Saved\OntoTwinGlassSpikeStage\Windows`。

## 7. 剩余人工窗口验收

- 720p、1080p、2K、4K 下 Screen 面板的智能锚定、边缘翻转和无固定右侧偏移。
- 100%、125%、150%、200% DPI 下的文字清晰度、面板尺寸和 DPI 只换算一次。
- 近身 `E`、上帝视角左键和漫游视角切换后的选中与输入恢复。
- `always` 与 `selected` 的互斥视觉行为。
- 视频打开、切换实例和关闭面板后的声音、纹理、请求与播放器释放。
- 白色地面、暗部、高曝光、SDR/HDR 下的文字对比度与玻璃可读性。
- High 的真实局部模糊是否存在矩形边缘、拉伸或 UV 偏移。
- Balanced、Performance 与 World 伪玻璃的视觉区分。
- 1080p/2K 目标 GPU 的 Overlay GPU 增量、`stat Slate`、median/p95。
- 20、50、100 个 always 面板的数量上限、帧时间和内存稳定性。
- 连续切换/关闭面板 100 次及持续运行 30 分钟后的 Widget、RenderTarget、回调和 MediaPlayer 泄漏检查。

代码路径已静态核查：点选与常显分别使用 `HasSelectedOverlay` / `HasAlwaysOverlay`；关闭点选面板恢复 `FInputModeGameOnly`；媒体复位调用 `UMediaPlayer::Close()` 并清空 Widget 纹理状态。静态核查不能代替上述人工验收。

## 8. 视频能力发布与回滚

### 8.1 发布前检查

1. 为部署环境设置平台媒体白名单。
2. 确认 PostgreSQL `media_policy` 加法字段已经应用。
3. 部署后端和无构建前端静态文件。
4. 编译启用 `ElectraPlayer` 的 OntoTwinSync 插件。
5. 使用 HTTPS MP4、HTTPS HLS、批准的内网 HTTP HLS 各验收一次。
6. 验证关闭、切换、重试和日志脱敏。

### 8.2 回滚原则

- 前端可停止提供视频模板，不影响既有非视频模板。
- 后端可保留 v5 数据但不下发可播放媒体状态。
- UE 可忽略未知 `media` 槽位，继续展示标题和正文。
- `media_policy` 是加法字段，回滚业务代码时不删除 PostgreSQL 列。
