# OntoTwin 3.7.1 实施记录

> 记录日期：2026-07-23 至 2026-07-24
> 范围：Renderer Spike、共享模板、液态玻璃表现、Web 质量配置、状态/指标配置与 Value/Gauge 垂直链路
> 设计来源：[液态玻璃 PRD](../../PRD/OntoTwin%203.7.1%20液态玻璃信息面板模板设计%20%28PRD%29.md)、[视频 URL PRD](../../PRD/OntoTwin%203.7.1%20视频%20URL%20面板垂直链路%20%28PRD%29.md)
> 部署和验收：[OntoTwin 3.7.1 宿主接入与验收](OntoTwin%203.7.1%20宿主接入与验收.md)

本文只记录实现事实、关键取舍和最终边界。阶段性的宿主状态、重复配置和重复测试结果已合并到宿主接入与验收文档。

## 1. 当前结论

- 阶段 A Renderer Spike 技术链路通过。
- 阶段 B/B3 的六模板共享组件、三档渲染、静态光学层、事件动效与无障碍降级已完成。
- 阶段 C 的 Web 请求质量、类型默认、实例稀疏覆盖和快照下发已完成。
- 阶段 D 的 Value/Gauge 已完成；Trend 因没有真实历史数据服务保持禁用。
- 阶段 E 的正式宿主集成、Development/Shipping 编译、Cook 和自动化启动验收已完成；人工视觉、输入和目标硬件性能验收仍未完成。

## 2. 阶段 A：Renderer Spike

### 2.1 验证环境

- Unreal Engine：5.6.1，CL 44394996。
- RHI：D3D12，PCD3D_SM6。
- GPU：NVIDIA GeForce RTX 5090，约 32 GB Dedicated VRAM。
- CPU：Intel Core i9-14900K。
- OS：Windows 11 25H2。
- 回归宿主：`D:\tmp_ue\test0316`。
- 目标关卡：`/Game/WarehouseProps_Bundle/Maps/X_Factory_Interior1`。

### 2.2 渲染路径

- Screen High：宿主显式预留一个 `SlatePostRT_N`；Spike 使用 RT0。
- Screen Balanced：`UBackgroundBlur` 与独立 tint/rim。
- Screen Performance：静态、可读的高对比表面。
- World：确定性伪玻璃，不采样 Slate Postbuffer，不创建 SceneCapture。
- 运行时只允许 `High → Balanced → Performance` 向下回退。

### 2.3 Spike 实现

- 增加 `UOntoTwinGlassSettings` 和具体的 Slate Postbuffer Blur Processor。
- 模块在首个 World 初始化前尝试预留宿主指定 RT；已存在不兼容处理器时不覆盖并自动降级。
- 增加 `OntoTwin.Glass.Enable`、`OntoTwin.Glass.ForceQuality`、`OntoTwin.Glass.Dump` 和 `OntoTwin.Glass.Diagnose` 诊断入口。
- 生成 RT0–RT4 五个匹配 `GetSlatePostN` 的 UI Domain 材质：`M_OT_GlassHigh_RT0` 至 `M_OT_GlassHigh_RT4`。
- Spike 阶段没有改动既有 Overlay 数据、模板和媒体生命周期，只在 Widget 根部验证三档 Screen 与 World 渲染层。

### 2.4 Spike 结论

- Editor Development、Win64 Shipping、Cook/Stage 和 Shipping EXE DX12 冒烟均通过。
- RT0 的 High 实际加载通过；关闭 backbuffer copy 后可确定降级到 Balanced。
- Balanced、Performance 和 World 路径均能按请求解析。
- UE5.6 `-nullrhi` 无法通过 `get_used_textures()` 证明 Material Function 内部的 Slate RT 使用；该项以函数对象路径、材质图接线和真实 D3D12 启动共同验证。

## 3. 阶段 B：共享组件与渲染器正式化

### 3.1 六种模板配方

UE 只维护一套 Title、Subtitle、Body、Status、Metrics、Media 和 Controls 组件，通过重新组合共享组件形成：

- `title_body`
- `title_subtitle_body`
- `title_metrics`
- `title_status_metrics`
- `title_video`
- `title_video_body`

模板切换时会清理不再允许的旧槽位；空槽位和相邻间距一起折叠。视频模板之间 URL 相同时复用当前媒体会话，切换到非视频模板时清理封面、纹理、控制状态并关闭媒体。World 配方不挂载媒体控制栏。

### 3.2 共享主题、字体和状态

- `FOntoTwinGlassTheme` 集中管理玻璃色、文字色、状态色和字体。
- 插件携带 Inter Regular/SemiBold 与 Noto Sans CJK SC Regular/Medium，并保留 SIL OFL 许可证。
- Slate Composite Font 使用 Inter 处理拉丁字符和数字，Noto Sans CJK SC 处理中文 fallback。
- 字体缺失时只记录一次并回退引擎字体。
- 状态支持 `normal / info / warning / critical / offline / unknown`，通过文字、图形和局部强调共同表达。
- `online=false` 时状态模板强制使用 Offline 语义。

### 3.3 正式质量策略

- `bEnableGlassUI` 默认开启；旧载荷缺少质量字段时按 Balanced 解析。
- `bEnableHighQualityRenderer` 是 High Screen 占用全局 Slate PostRT 的宿主授权。
- 旧 `bEnableRendererSpike` 保留一个兼容周期。
- Balanced/Performance 不因 High 未授权而回退为旧黑板，也不占用 PostRT。
- High 能力、RT 索引和 Blur 强度在完整重启后生效。
- World 诊断固定显示 `postbuffer=None`。

## 4. 阶段 B3：光学层、动效与无障碍

### 4.1 共享光学层

最终层级为：

```text
High Postbuffer / Balanced Blur
→ 中性 Tint 与基础 Rim
→ 共享静态细噪声
→ 顶部局部内高光
→ 状态灯与局部强调
→ Hover/Focus Rim
→ 清晰内容与真实控件
```

- 细噪声使用一张运行时生成、全插件共享的 32×32 确定性纹理。
- High/Balanced 噪声低于 2%；Performance 不使用噪声。
- 文字、指标、图表、视频和真实控件始终位于玻璃装饰层之上。
- 装饰层保持 `Self Hit Test Invisible`。
- World Billboard 不伪造无有效变化的 Fresnel；只使用静态高光、噪声和状态灯表达伪玻璃。

### 4.2 事件动效

- 打开：210 ms 淡入，正常模式附带 `0.97 → 1.0` 轻缩放。
- 关闭：150 ms 淡出，正常模式附带 `1.0 → 0.985` 轻缩放。
- Hover/Focus：140 ms 局部 Rim 与顶部高光过渡。
- 状态变化：一次 800 ms 内衰减的状态灯脉冲。
- 动效由事件期间存在的 Timer 驱动，结束后清除，不增加 Idle Tick。
- World 常显面板不播放交互动效。

### 4.3 无障碍和确定性降级

项目设置和开发 CVar 支持：

- `ReduceMotion`：保留淡入淡出，移除缩放和状态脉冲；Performance 自动采用。
- `ReduceTransparency`：强制实际档位为 Performance，但不改写 Web 保存的请求档位。
- `HighContrast`：提高中性遮罩、Rim 和内高光对比，不改变业务状态语义。

## 5. 状态与指标展示配置

- 每个指标使用独立 `emphasized` 布尔配置，默认 `false`，不再按数组第一项自动强调。
- 未强调指标使用普通字号和白色文字；强调指标才使用大字、较高字重和当前状态强调色。
- 六个标准状态分别保存展示文字和预设灯色。
- 默认映射为：在线/绿色、信息/青蓝色、注意/橙色、告警/红色、离线/灰色、未知/灰色。
- Web 只允许绿色、青蓝色、橙色、红色和灰色 token，不允许任意 HEX。
- UE 消费后端解析后的 `display_value` 与 `accent_token`，不硬编码英文状态文字。
- 持久化左侧状态边已取消；状态变化只播放一次状态灯脉冲。
- 旧配置缺少新字段时在归一化阶段补齐，指标按不强调处理，不增加 ProjectStore 顶层结构。

## 6. 阶段 C：Web 质量配置与存储

- `/interaction` 信息面板编辑器增加普通白底“展示效果”区域。
- 支持 `high / balanced / performance` 三档请求质量，默认 `balanced`。
- ObjectType 保存类型默认；实例只保存稀疏 `presentation` 覆盖，恢复继承时删除覆盖。
- 批量覆盖和批量恢复沿用现有模态确认与原子 revision 保存。
- Web 只做结构预览，并声明透明、模糊、曝光和遮挡以 UE 为准。
- 后端校验质量枚举；旧配置只在内存补齐默认值，不因读取而强制写盘。
- 快照向 UE 下发 `presentation.quality_tier`；UE 的有效档位和降级原因不写回项目。

存储继续使用既有位置：

- 类型默认：`object_type.interface_configs.I3D_Overlay.values.presentation`
- 实例覆盖：`instance.render_config.interface_overrides.I3D_Overlay.values.presentation`

本阶段没有增加 ProjectStore 顶层字段、`schema_version`、PostgreSQL 列或迁移脚本；JSON 使用既有嵌套对象，PostgreSQL 使用既有 JSONB。

## 7. 阶段 D：Value/Gauge 垂直链路

### 7.1 数据契约

- `presentation.metrics.style` 当前可保存 `value` 或 `gauge`。
- Gauge 必须选择当前模板中存在的 `primary_metric_id`。
- Gauge 的 `min`、`max` 必须是有限数字且 `max > min`；`clamp_visual` 必须是布尔值。
- 只有绑定原值本身是有限数字时才下发 `numeric_value`；不从字符串猜测数值。
- Gauge 运行配置通过 `resolved_slots.metrics_visual` 下发；显示文本继续通过 `display_value` 下发。
- 旧配置归一化为 `presentation.metrics.style=value`。

### 7.2 Web 与 UE

- Web 显示“数值 / 仪表 / 趋势图”；Trend 因无真实历史服务保持禁用且不会进入保存载荷。
- Gauge 条件字段包括主指标、最小值、最大值和视觉钳制。
- 结构预览使用灰阶轻量弧线，不模拟 UE 玻璃、曝光或折射。
- UE 使用 `UOntoTwinGaugeWidget` 内部的轻量 `SLeafWidget` 绘制弧线。
- 数值刷新只触发 Paint 失效，不创建新的 Widget、RenderTarget 或 SceneCapture。
- 原始值、范围非法，或值越界且不允许视觉钳制时，明确回退 Value。
- 允许钳制时只钳制弧线比例，文本仍显示真实 `display_value`。

## 8. 实施中形成的最终取舍

### 8.1 插件 UI Cook

早期方案使用 `/OntoTwinSync/UI/PAL_OntoTwinUI`，希望通过 `AlwaysCook` 递归收集插件 UI 目录。正式宿主第一次 Shipping Cook 证明：UE5.6 默认只扫描 `/Game` 的宿主中，该 Label 不能独立保证五个 High Postbuffer 材质进入 Cook。

最终方案为：`UOntoTwinOverlayWidget` 对 `M_OT_GlassHigh_RT0...RT4` 建立插件内硬引用，让 Cooker 通过类引用图发现材质。正式宿主无需增加 OntoTwin `DirectoriesToAlwaysCook`。早期“PrimaryAssetLabel 可独立完成 Cook”的结论已被本结论替代。

### 8.2 保留边界

- Trend 只有设计契约，没有真实历史提供者，因此保持禁用。
- High 的局部亮度自适应没有引入历史 RT 或 GPU→CPU Readback。
- World 只提供确定性伪玻璃，不宣称真实后景模糊或动态 Fresnel。
- RT1–RT4 的冷启动和打包时序仍需逐槽验证；当前正式承诺路径是已验证的 RT0。
- 正式宿主未授权 High，当前生产式验收基线仍为 Balanced。

## 9. 主要变更面

- 后端：`backend/overlay/schema.py`、`backend/overlay/service.py`、Overlay 测试。
- Web：`frontend/interaction.html`。
- UE：Overlay Widget、Gauge Widget、Glass Settings、渲染器、主题、字体和插件 UI 资产。
