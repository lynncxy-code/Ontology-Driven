# OntoTwin 3.7.1 阶段 D-E 实施与验收记录

> 日期：2026-07-24  
> 正式宿主：`D:\ZHHZ\ZHHZ`  
> 范围：阶段 D 的 Value/Gauge 指标展示；阶段 E 的正式宿主集成、Cook、Development/Shipping 与自动化启动验收  
> 不包含：伪造 Trend、宿主 High 授权、人工视觉与鼠标输入结论

## 1. 阶段 D 结论

阶段 D 的 Value/Gauge 垂直链路已经完成。当前没有真实历史数据服务，因此 Trend 在 Web 中可见但禁用，也不会进入保存载荷。

数据链路：

```text
Web 指标展示配置
  → presentation.metrics
  → Overlay 校验与归一化
  → resolved_slots.metrics[].numeric_value
  → resolved_slots.metrics_visual
  → UOntoTwinGaugeWidget
```

### 1.1 后端契约

- `presentation.metrics.style` 仅支持 `value`、`gauge`。
- Gauge 必须选择当前模板内存在的 `primary_metric_id`。
- Gauge 的 `min`、`max` 必须是有限数字且 `max > min`。
- `clamp_visual` 必须是布尔值。
- 只有绑定原值本身是有限数字时才下发 `numeric_value`；字符串 `"36.5"` 不会被猜测为数字。
- Gauge 运行配置通过 `resolved_slots.metrics_visual` 下发；显示文本继续通过 `display_value` 下发。
- 旧配置归一化为 `presentation.metrics.style=value`，没有增加 ProjectStore 顶层字段或 schema version。

### 1.2 Web 工作台

- 指标模板新增“数值 / 仪表 / 趋势图”选择。
- 趋势图保持禁用，并持续说明“尚未接入历史数据”。
- 只有 Gauge 显示主指标、最小值、最大值和超范围钳制选项。
- 结构预览使用灰阶轻量弧线，不模拟 UE 的玻璃、曝光或折射。
- Gauge 原始值不可用时显示“仪表数据不可用，已按数值显示”。
- 实例级继续复用既有 `presentation` 整组覆盖/恢复继承机制。

### 1.3 UE

- 新增 `UOntoTwinGaugeWidget`，内部用一个 `SLeafWidget` 绘制轨道和活动弧线。
- 数值刷新只触发 Paint 失效，不创建新的指标 Widget、RenderTarget 或 SceneCapture。
- 主指标用于 Gauge；其余指标保持紧凑 Value 布局。
- UE 只读取 `numeric_value`，不反解析 `display_value`。
- 原始值、范围非法，或值越界且禁止钳制时，明确回退 Value。
- 允许钳制时只钳制弧线比例，仍显示真实 `display_value`。
- Screen 和 World 共用轻量弧线；World 仍使用确定性的伪玻璃，不声明真实场景模糊。

## 2. High 材质 Cook 修正

第一次 Shipping Cook 成功，但 5 个 High Postbuffer 材质没有进入 Cook 清单。`PAL_OntoTwinUI` 在 UE 5.6 默认只扫描 `/Game` 的宿主中不能独立保证插件目录被收集。

最终处理：

- `UOntoTwinOverlayWidget` 对 `M_OT_GlassHigh_RT0...RT4` 建立插件内硬引用。
- Cooker 通过类引用图自动发现材质。
- 没有向 ZHHZ 的 `DefaultGame.ini` 增加 OntoTwin `DirectoriesToAlwaysCook`。
- 第二次 Cook 后，5 个材质都出现在：
  `Saved/Cooked/Windows/ZHHZ/Plugins/OntoTwinSync/Content/UI/RendererSpike/`。

## 3. 正式宿主集成结果

- 源插件已增量同步到 `D:\ZHHZ\ZHHZ\Plugins\OntoTwinSync`。
- `ZHHZEditor Win64 Development`：成功。
- `ZHHZ Win64 Development`：成功。
- `ZHHZ Win64 Shipping`：成功。
- Development 与 Shipping 均 Cook 29,323 个 Package、58,017 个 IoStore Chunk。
- 4 个插件字体均进入 Stage，并在 Development 运行日志中实际完成 LazyLoad。
- 默认地图成功进入 `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto`。

最终交付产物：

- Development：`D:\ZHHZ\Builds\OntoTwin371_E_20260724_Development\Windows`
- Shipping：`D:\ZHHZ\Builds\OntoTwin371_E_20260724_Shipping_v2\Windows`

第一次 Shipping 目录只保留为诊断对照，不是最终交付：
`D:\ZHHZ\Builds\OntoTwin371_E_20260724_Shipping\Windows`。

## 4. 自动化验收结果

### 4.1 后端与 Web

- `tests.test_overlay.OverlayTestCase`：14/14 通过。
- 覆盖 Gauge 正常解析、非法主指标、非法范围、字符串禁止猜数值和旧配置默认值。
- Web 内联 JavaScript 语法通过。
- 浏览器实测条件字段、Trend 禁用、无效 Gauge 回退均正确。
- 浏览器控制台错误：0。

### 4.2 打包运行

Development 包分别以以下参数进入运行时：

- 1280×720
- 1920×1080
- 2560×1440
- 3840×2160

四次日志均确认：

- `OntoTwinSync` 项目插件成功 Mount。
- `Game Engine Initialized`。
- 默认地图开始 Load。
- Screen 默认请求 Balanced，并在 NullRHI 冒烟环境保持 Balanced。
- World 明确走确定性伪玻璃且不采样 Slate Postbuffer。
- Inter Regular/SemiBold 与 Noto CJK Regular/Medium 均从打包插件目录成功加载。
- 没有 Fatal Error、Unhandled Exception 或 Crash 目录。

Shipping 包可持续进入运行状态，未生成崩溃产物。Shipping 默认关闭日志，测试进程由验收脚本终止。

## 5. 阶段 E 尚需人工窗口验收

以下项目依赖真实 DX12 窗口、场景可见内容和人工输入，不能由 NullRHI 启动日志替代：

- 720p / 1080p / 2K / 4K 下 Screen 面板的智能锚定、边缘翻转和无右侧偏移。
- 100% / 125% / 150% Windows DPI 的文字清晰度与面板尺寸。
- 近身 `E`、上帝视角左键、漫游视角切换后的面板选中与输入恢复。
- `always` 与 `selected` 的互斥视觉行为。
- 视频打开、切换实例、关闭面板后的声音、纹理和播放器生命周期。
- 白色地面、暗部、高曝光、SDR/HDR 下的文字对比度。
- 30 分钟连续开关面板的内存稳定性，以及目标 GPU 上的 GPU/Slate 性能。
- 正式宿主授权 High 后的 DX12 Postbuffer 实际视觉；未授权前保持 Balanced。

代码路径已静态核查：点选与常显分别使用 `HasSelectedOverlay` / `HasAlwaysOverlay`；关闭点选面板恢复 `FInputModeGameOnly`；媒体复位调用 `UMediaPlayer::Close()` 并清空 Widget 纹理状态。上述人工项通过前，阶段 E 的工程集成和自动化验收完成，但 3.7.1 最终视觉验收不能标记为全通过。

## 6. 本轮变更文件

- `backend/overlay/schema.py`
- `backend/overlay/service.py`
- `backend/tests/test_overlay.py`
- `frontend/interaction.html`
- `ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/Public/UI/OntoTwinGaugeWidget.h`
- `ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/Private/UI/OntoTwinGaugeWidget.cpp`
- `ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/Public/OntoTwinOverlayWidget.h`
- `ue_project/Plugins/OntoTwinSync/Source/OntoTwinSync/Private/OntoTwinOverlayWidget.cpp`

