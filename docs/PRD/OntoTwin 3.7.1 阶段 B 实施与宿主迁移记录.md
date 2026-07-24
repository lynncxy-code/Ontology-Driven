# OntoTwin 3.7.1 阶段 B 实施与宿主迁移记录

> 日期：2026-07-23  
> 主线：OntoTwin Nexus  
> 正式宿主：`D:\ZHHZ\ZHHZ`  
> 回归宿主：`D:\tmp_ue\test0316`（仅编译、Cook 与兼容回归）

## 1. 阶段 B 已实施

### B1：六种共享组件配方

- UE 读取运行载荷中的 `template_id`。
- 只创建一套 Title、Subtitle、Body、Status、Metrics、Media、Controls。
- 通过清理 `ContentStack` 的旧 Slot 并重新挂载共享组件形成六种真实配方。
- 支持：
  - `title_body`
  - `title_subtitle_body`
  - `title_metrics`
  - `title_status_metrics`
  - `title_video`
  - `title_video_body`
- 不允许的旧槽位会清空，空槽位连同间距一起折叠。
- 视频模板之间使用相同 URL 时保留当前 MediaPlayer 会话；切到非视频模板时清除封面、纹理、控制状态并停止媒体。
- World 配方不挂载媒体控制栏。

### B2：主题、字体、状态和 Screen/World Profile

- 新增共享 `FOntoTwinGlassTheme`，集中玻璃色、文字色、状态色和字体。
- 插件内携带 Inter Regular/SemiBold 与 Noto Sans CJK SC Regular/Medium，并保留双方 SIL OFL 许可证。
- Slate 运行时构造 Composite Font：Inter 负责拉丁字符与数字，Noto Sans CJK SC 负责中文 fallback。
- 字体通过 `RuntimeDependencies` 进入 Shipping 依赖清单；缺失时只记录一次并回退引擎字体。
- 状态支持 `normal / info / warning / critical / offline / unknown`，使用语义文字、状态点和关键值三重表达，不只依赖颜色。
- `online=false` 时状态模板强制使用 Offline 语义。
- 指标模板将第一项作为主指标放大，其余指标保持紧凑。
- Screen：High / Balanced / Performance 分别使用 Postbuffer、BackgroundBlur、静态高对比表面。
- World：三档均为伪玻璃，不使用 Postbuffer、BackgroundBlur、SceneCapture 或播放器；High / Balanced / Performance 使用不同透明度和 RT 密度。
- World 的物理尺寸不会随 RT 密度变化：现有 SceneManager 使用实际 DrawSize 反算 WorldScale。

### 渲染器正式化

- 新增 `bEnableGlassUI`，默认开启；缺少新字段的宿主默认使用 Balanced。
- 新增 `bEnableHighQualityRenderer`，仅它负责授权 High Screen 占用一个全局 Slate PostRT。
- 保留旧 `bEnableRendererSpike` 一个兼容周期；旧 0316 配置仍可运行。
- Balanced / Performance 不再因为 High 未授权而退回旧黑板，也不会占用 PostRT。
- High 能力、RT 索引和 Blur 强度标记为重启后生效。
- World 诊断显示 `postbuffer=None`，避免误认为常显面板使用真实背景采样。

### 插件自有 Cook

- 新增 `/OntoTwinSync/UI/PAL_OntoTwinUI`。
- Label 使用 `AlwaysCook`，递归覆盖插件 UI 目录。
- 新宿主不再需要 `+DirectoriesToAlwaysCook=(Path="/OntoTwinSync/UI")`。
- 保留 `scripts/ue_ensure_ontotwin_ui_cook_label.py` 作为可重复验证脚本。

## 2. 已通过的自动验证

- UE5.6 `test0316Editor Win64 Development`：通过。
- UE5.6 `test0316 Win64 Shipping`：通过。
- Shipping Target Receipt 已包含四个字体文件与两份许可证。
- UI PrimaryAssetLabel 二次验证：`action=verified`、`cook_rule=ALWAYS_COOK`。
- 六种后端 preview payload 均返回严格匹配模板的 `resolved_slots`。
- Overlay 与媒体后端单元测试：12 项通过。

## 3. 正式宿主 `D:\ZHHZ\ZHHZ` 当前状态

已满足：

- UE 5.6。
- `.uproject` 已启用 `OntoTwinSync` 与 `glTFRuntime`。
- DX12 + SM6。
- 已配置 `HttpNoProxy=127.0.0.1,localhost`。
- 正式运行关卡为 `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto`。

尚未完成：

- 正式宿主中的插件是独立副本，尚未同步本记录中的 B1/B2 代码和字体资源。
- 尚未确认正式运行关卡中恰好只有一个 `ATwinSceneManager`。
- 尚未确认 `ueproj_zhhz` 与目标 OntoTwin 数据集的绑定。
- 尚未配置 High 所需的 Postbuffer；因此同步插件后默认应以 Balanced 运行。
- 尚未在正式宿主执行 Development、Shipping、Cook、Standalone/EXE 视觉验收。

## 4. 新宿主最小改动

### 所有质量档都需要

1. 安装并启用完整 `OntoTwinSync` 插件及 `glTFRuntime`。
2. 在持久运行 Level 中放置一个 `ATwinSceneManager`；不得每个子关卡重复放置。
3. 后端不是本机时设置 Manager 的 `BackendBaseUrl`。
4. 将新 UE 工程身份绑定到目标 OntoTwin 数据集。默认身份为 `ueproj_<uproject 名>`。
5. 用新宿主做一次 Editor、Shipping 和 Cook 验收。

无需复制六套 WBP、材质到 `/Game`，无需复制 0316 的地图、路线、人物锚点、GameMode 或输入配置，也无需在 Web 工作台中保存 UE 工程文件。

### 只有 High Screen 需要

```ini
[SystemSettings]
Slate.CopyBackbufferToSlatePostRenderTargets=1

[/Script/OntoTwinSync.OntoTwinGlassSettings]
bEnableGlassUI=True
bEnableHighQualityRenderer=True
bEnableRendererSpike=False
ReservedPostBufferIndex=0
GaussianBlurStrength=14.000000
```

同时要求 DX12，并由宿主明确确认 RT0 未被其他 UI 插件占用。配置必须在进程启动前存在，修改后完整重启。阶段 C 起，具体面板请求 High / Balanced / Performance 由 Web 的 `presentation.quality_tier` 决定；宿主的 `RequestedQuality` 只保留为旧载荷和开发诊断的默认值，不是 High 能力授权条件。

Balanced / Performance 不需要上面的 Postbuffer 配置。

## 5. 尚未完成与风险

- High World 当前具备更高 RT 密度和不同伪玻璃透明度，但尚未增加带 Fresnel/视角高光的 WidgetComponent pass-through 材质；完成前不宣称为真实或完整的增强伪玻璃。
- RT1–RT4 的冷启动时序仍需逐槽打包验证；目前正式承诺路径应先使用已验证的 RT0。
- 需要在删除 0316 手工 `DirectoriesToAlwaysCook` 配置的独立 Cook 中再次证明插件 Label 单独生效。
- 正式宿主插件仍存在与 3.7.1 无关的跨项目遗留：硬编码 glTF 默认目录、默认开启的固定 WebSocket 地址、工程名派生 UE Project ID、插件版本号仍为 1.0。
- 阶段 C 已在独立实施记录中完成；没有新增 ProjectStore 顶层字段、PG 列或 schema version。
