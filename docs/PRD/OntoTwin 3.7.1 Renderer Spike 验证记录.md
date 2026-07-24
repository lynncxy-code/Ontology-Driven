# OntoTwin 3.7.1 Renderer Spike 验证记录

> 验证日期：2026-07-23  
> 阶段：PRD 3.7.1 阶段 A  
> 宿主：`D:\tmp_ue\test0316`  
> 结论：技术链路通过；人工视觉与持续性能验收待完成

## 1. 本阶段边界

本阶段只验证 UE5.6 的液态玻璃渲染可行性，没有修改 OntoTwin Web 前端、前端路由、后端 API、ProjectStore 或数据库结构。

实现范围：

- Screen High：宿主显式预留一个 `SlatePostRT_N`，当前 `test0316` 使用 RT0。
- Screen Balanced：使用 `UBackgroundBlur` 与独立 tint/rim。
- Screen Performance：使用可读的静态半透明面板。
- World：始终使用伪玻璃，不采样 Slate Postbuffer。
- 质量只允许 `High → Balanced → Performance` 向下回退。

## 2. 环境

- Unreal Engine：5.6.1，CL 44394996。
- RHI：D3D12，PCD3D_SM6。
- GPU：NVIDIA GeForce RTX 5090，约 32 GB Dedicated VRAM。
- CPU：Intel Core i9-14900K。
- OS：Windows 11 25H2。
- 目标关卡：`/Game/WarehouseProps_Bundle/Maps/X_Factory_Interior1`。

## 3. 实现结果

### 3.1 插件运行时

- 新增 `UOntoTwinGlassSettings`，默认不启用 Spike，避免未配置宿主无意占用全局 RT。
- 新增具体 `UOntoTwinSlatePostBufferBlur` 处理器。
- 模块在首个 World 初始化前预留宿主指定 RT。
- 若 RT 已配置其他处理器，OntoTwin 不覆盖并自动降级。
- 新增 `OntoTwin.Glass.Enable`、`OntoTwin.Glass.ForceQuality`、`OntoTwin.Glass.Dump` 与 `OntoTwin.Glass.Diagnose` 诊断入口。
- 现有 Overlay 内容、数据与视频生命周期未拆改，只在根部增加 High、Balanced、Performance、World 渲染层。

### 3.2 材质资产

已生成并校验：

- `M_OT_GlassHigh_RT0`
- `M_OT_GlassHigh_RT1`
- `M_OT_GlassHigh_RT2`
- `M_OT_GlassHigh_RT3`
- `M_OT_GlassHigh_RT4`

每个材质均为 UI Domain、Translucent，使用匹配的 `GetSlatePostN`，`RGB` 接 UI Final Color，Opacity 为 1。脚本再次运行时结果为 `created_count=0`、`verified_count=5`，没有重写已有资产。

UE5.6 在 `-nullrhi` 下不会通过 `get_used_textures()` 报告 Material Function 内部的 Slate RT，因此命令行验证以函数对象路径和图接线为事实；真实 D3D12 启动进一步验证了 RT0 材质可加载。

### 3.3 test0316 宿主配置

`DefaultEngine.ini`：

```ini
[SystemSettings]
Slate.CopyBackbufferToSlatePostRenderTargets=1
```

`DefaultGame.ini`：

```ini
[/Script/UnrealEd.ProjectPackagingSettings]
+DirectoriesToAlwaysCook=(Path="/OntoTwinSync/UI")

[/Script/OntoTwinSync.OntoTwinGlassSettings]
bEnableRendererSpike=True
RequestedQuality=High
ReservedPostBufferIndex=0
GaussianBlurStrength=14.000000
```

首次修改前已保存：

- `DefaultEngine.ini.before-ontotwin-glass-spike.bak`
- `DefaultGame.ini.before-ontotwin-glass-spike.bak`

## 4. 自动验证结果

| 验证项 | 结果 | 证据 |
| --- | --- | --- |
| UE Editor Development 冷编译 | 通过 | UHT、Overlay、Glass Renderer、模块链接成功 |
| 五个材质生成 | 通过 | RT0–RT4 均已保存 |
| 材质幂等校验 | 通过 | 5 verified / 0 created |
| DX12 High | 通过 | Screen `High → High`，RT0 材质加载成功 |
| High 自动回退 | 通过 | 关闭 backbuffer copy 后 `High → Balanced` |
| Balanced 请求 | 通过 | `Balanced → Balanced` |
| Performance 请求 | 通过 | `Performance → Performance` |
| World 边界 | 通过 | 所有请求均为 World pseudo-glass，不加载材质 |
| Win64 Shipping 编译 | 通过 | `test0316-Win64-Shipping.exe` 链接成功 |
| Shipping Cook/Stage | 通过 | BuildCookRun ExitCode 0 |
| 插件 UI 资产 Cook | 通过 | Cooked 目录存在 RT0–RT4 五个资产 |
| Shipping EXE 冒烟 | 通过 | 打包 EXE 以 DX12 离屏启动并正常退出 |

关键 DX12 诊断：

```text
context=Screen requested=High effective=High postbuffer=RT0 rhi=D3D12
material=/OntoTwinSync/UI/RendererSpike/M_OT_GlassHigh_RT0.M_OT_GlassHigh_RT0

context=Screen requested=High effective=Balanced postbuffer=RT0 rhi=D3D12
reason=High downgraded to Balanced: Slate postbuffer backbuffer copy is disabled

context=World requested=High effective=Performance postbuffer=RT0 rhi=D3D12
reason=World Space uses deterministic pseudo-glass and never samples a Slate postbuffer
```

验证日志：

- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassHigh.log`
- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassFallback.log`
- `D:\tmp_ue\test0316\Saved\Logs\OntoTwinGlassQualityTiers.log`

Shipping Stage：

- `D:\tmp_ue\test0316\Saved\OntoTwinGlassSpikeStage\Windows`

## 5. 已发现但未归属于玻璃实现的问题

- Shipping 首次构建期间，另一个任务同时新增人物准星源码，UHT 扫描与文件落盘交错，首次构建失败；文件稳定后原命令重跑成功，未修改对方代码。
- 宿主关卡仍会报告 PCB 后端 HTTP 503、CitizenNPC 缺少旧 Humanoid 依赖、部分 Nanite 网格使用 Translucent 材质等既有警告；不影响本次玻璃质量解析与打包。
- UE5.6 多窗口 PIE 不适合作为 Slate Postbuffer 验收环境，视觉验收应使用单窗口 PIE、Standalone 或打包 EXE。

## 6. 待人工验收

以下内容不能由离屏日志替代：

1. 明亮和暗色厂房背景上的文字可读性、玻璃染色与边缘质量。
2. High 是否形成稳定的局部真实模糊，且没有矩形边缘、拉伸或 UV 偏移。
3. Balanced、Performance 与 World 伪玻璃的视觉差异是否符合产品预期。
4. Screen 面板点击、视频按钮、always/selected 互斥是否保持正常。
5. 1080p、4K 的 60 秒 GPU median/p95，以及面板可见数量上限。

在上述人工视觉与性能项完成前，阶段 A 的技术可行性可以判定通过，但 3.7.1 整体验收不能判定完成。
