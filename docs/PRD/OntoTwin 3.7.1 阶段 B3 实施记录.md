# OntoTwin 3.7.1 阶段 B3 实施记录

> 日期：2026-07-23  
> 主线：OntoTwin Nexus  
> 范围：UE 信息面板视觉欠账  
> 不包含：阶段 D Gauge/Trend、阶段 E Cook/Shipping/性能验收

## 1. 本轮目标

在不改变 `I3D_Overlay` 数据契约、六模板配方、选中/常显互斥和媒体生命周期的前提下，补齐液态玻璃面板的静态光学层、短时交互动效和无障碍降级开关。

约束继续成立：

- Screen High 使用一个共享 Slate Postbuffer。
- World 只使用确定性的伪玻璃，不采样三维场景，不创建 SceneCapture。
- 装饰层位于文字、指标、视频和真实按钮下方，并设为 `Self Hit Test Invisible`。
- Idle 不存在持续流光、呼吸、折射或噪声动画。

## 2. 已实施

### 2.1 共享光学装饰层

动态 Widget 树已拆分为：

```text
High Postbuffer / Balanced Blur
→ 中性 Tint 与基础 Rim
→ 共享静态细噪声
→ 顶部局部内高光
→ 状态局部边
→ Hover/Focus 交互 Rim
→ 清晰内容与真实控件
```

- 使用一张运行时生成、全插件共享的 32×32 确定性细噪声纹理，不为每个面板创建纹理。
- High 与 Balanced 使用低于 2% 的静态噪声；Performance 关闭噪声。
- 增加顶部局部内高光，不把文字、指标或视频放入噪声/玻璃层。
- 状态颜色只进入状态灯和用户明确勾选“强调”的指标；状态文字保持中性白色，不铺满玻璃底板。
- 统一媒体按钮为中性圆角玻璃控制样式，保留 Hover、Pressed、Disabled 状态。

### 2.2 短时事件动效

- 打开：210 ms 淡入；正常模式附带 `0.97 → 1.0` 轻缩放。
- 关闭：150 ms 淡出；正常模式附带 `1.0 → 0.985` 轻缩放。
- Hover/Focus：140 ms 局部 Rim 与顶部高光过渡。
- 状态等级变化：一次 800 ms 内衰减的状态灯脉冲。
- 动效由仅在事件期间存活的 60 Hz Timer 驱动，结束后立即清除，不增加 Idle Tick。
- World 常显面板不播放交互动效，兼容 `UWidgetComponent` 手动重绘和批量面板性能边界。

### 2.3 无障碍与确定性降级

`UOntoTwinGlassSettings` 新增：

- `bReduceMotion`
- `bReduceTransparency`
- `bHighContrast`

开发/验收 CVar：

```text
OntoTwin.Glass.ReduceMotion
OntoTwin.Glass.ReduceTransparency
OntoTwin.Glass.HighContrast
```

值为 `-1` 时读取项目设置，`0/1` 为开发覆盖。

- ReduceMotion 保留短淡入淡出，移除缩放和状态脉冲。
- Performance 请求自动采用减少动态行为。
- ReduceTransparency 强制实际档位为 Performance，但不修改 Web 保存的请求档位。
- HighContrast 增强中性遮罩、基础 Rim 和顶部内高光，不改变业务状态色。

### 2.4 Screen / World 边界

- High Screen 继续使用匹配 RT0–RT4 的 Postbuffer 材质。
- Balanced Screen 继续使用带圆角的 `UBackgroundBlur`。
- Performance 使用近不透明中性表面、基础 Rim 和清晰内容。
- World High/Balanced 增加静态细噪声、顶部内高光和状态灯；Performance 保持静态可读。
- World 面板始终朝向相机，真实视角 Fresnel 在该 Billboard 结构下不会形成有效变化，因此本轮没有伪造 Fresnel 动态，也不宣称 World 具备真实场景玻璃。

## 3. 当前保留边界

- High 材质仍以共享 Postbuffer 模糊采样为基础；本轮没有加入会影响文字或视频的全屏折射。
- 没有实现持续色散或彩虹边。
- High 的局部亮度自适应仍未加入历史缓冲、GPU→CPU Readback 或额外 RenderTarget。
- 正式宿主的 HDR/SDR、自动曝光、白色地面、强灯背景与多 DPI 视觉验收属于阶段 E，本轮不启动。

## 3.1 B3.1 状态与指标展示配置

- 每个指标增加独立的“强调”布尔配置，默认关闭；不再按数组第一项自动强调。
- 未强调指标统一使用普通字号和白色文字；强调指标才使用大字、较高字重和当前状态强调色。
- 六个标准状态分别保存显示文字与预设灯色，默认值为：在线/绿色、信息/青蓝色、注意/橙色、告警/红色、离线/灰色、未知/灰色。
- Web 只提供绿色、青蓝色、橙色、红色和灰色预设，不提供任意 HEX 输入。
- UE 使用后端下发的 `display_value` 与 `accent_token`，不再硬编码 `OK / INFO / WARNING`。
- 持久化左侧状态边已取消；状态等级变化时只播放一次状态灯脉冲。
- 旧配置缺少新字段时在配置归一化阶段补齐，指标按不强调处理，不增加新的顶层存储结构。

## 4. 验证

- UE5.6 `test0316Editor Win64 Development`：编译通过。
- 所有装饰层保持 `Self Hit Test Invisible`；仅媒体按钮接收输入。
- 没有增加 SceneCapture、Retainer 场景采样或每面板 RenderTarget。
- `git diff --check`：通过。
- 后端 `tests.test_overlay`：12 项全部通过。
- Web 实测：六级状态配置正常呈现；四项指标默认均不强调，临时勾选一项后仅该项进入强调预览，未保存测试数据。
- UE5.6 `ZHHZEditor Win64 Development`：B3.1 增量同步后编译通过。

## 5. 正式宿主状态

正式宿主为 `D:\ZHHZ\ZHHZ`。2026-07-23 已完成 B3 同步：

- 当前正式宿主插件已备份到 `D:\ZHHZ\OntoTwinSync_Backups\ZHHZ-OntoTwinSync-B3-20260723-163808`。
- 已同步 `.uplugin`、`Config`、`Source`、`Content`、`Resources` 和 `README.md`，共 62 个部署文件。
- 源/目标 SHA-256 差异为 0。
- 已清除正式宿主插件旧 `Binaries`、`Intermediate`，未复制 0316 的编译产物。
- 未修改宿主地图、关卡 Actor、项目 Config、路线、出生点、输入或数据绑定。
- 同步后正式宿主已自动重建并加载新的 `OntoTwinSync` 与 `DigitalFactoryBaseEditor` Editor 模块；运行进程响应正常。
