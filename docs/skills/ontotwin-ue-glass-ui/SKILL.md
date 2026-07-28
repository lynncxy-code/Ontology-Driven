---
name: ontotwin-ue-glass-ui
description: Design, review, implement, document, and validate visionOS-inspired liquid-glass information overlays for OntoTwin UE5.6. Use for I3D_Overlay templates, status/metric/video panels, Screen/World renderer choices, glass quality tiers, smart anchoring, input behavior, Web configuration, runtime data contracts, host integration, or packaged-build acceptance.
---

# OntoTwin UE Liquid Glass UI

为 OntoTwin `I3D_Overlay` 建立统一、可读、可降级的液态玻璃信息面板。保留工业语义和既有数据/输入生命周期，不照搬 Apple 组件。

## 工作流

1. 先判断任务属于功能设计、视觉规范、实现、代码审查、宿主接入还是验收。
2. 读取当前 UE 版本、Widget Space、Overlay 生命周期、数据契约、输入路径和目标宿主配置；不要从旧阶段记录推断当前状态。
3. 以六个既有模板为用户入口，通过共享 Glass、Title、Body、Status、Metric、Media 和 Controls 组件组合，不复制六套 Widget。
4. 根据 Screen/World 和请求质量选择渲染路径。World Space 永远不承诺真实场景模糊。
5. 将玻璃装饰与清晰内容分层；文字、图标、图表、视频和交互控件始终位于模糊/折射层之上。
6. 保持业务状态判断和展示格式化位于后端契约；UE 不推断告警阈值，也不从 `display_value` 反解析数值。
7. 按 DPI、背景亮度、质量回退、输入恢复、性能、Cook 和 Development/Shipping 包完成验证。

设计任务不得顺带修改 C++、WBP、材质、`.uasset`、Web、路由或存储。实现任务只做符合已确认 PRD 的最小修改；修改或同步 UE 插件前先确认目标 Editor/EXE 已关闭。

## 渲染选择

| 场景 | High | Balanced | Performance |
| --- | --- | --- | --- |
| `selected / Screen` | 共享 Slate Postbuffer + Blur Processor + UI Glass Material | `UBackgroundBlur` + tint/rim | 静态半透明或近不透明表面 |
| `always / World` | 高密度伪玻璃 + 静态高光 | 标准伪玻璃 | 静态高对比表面 |

把 High、Balanced、Performance 视为“请求质量”。只允许 `High → Balanced → Performance`、`Balanced → Performance` 的向下回退；Performance 不自动升档。实际档位和降级原因属于 UE 本地诊断，不写回项目配置。

## 不可违反的边界

- OntoTwin Overlay 最多预留并共享一个 Slate Postbuffer。
- 禁止每面板 SceneCapture、独立全屏场景缓冲、独立 MediaPlayer 或持续 GPU→CPU Readback。
- 不把 Retainer Box 当作 Widget 背后的三维场景来源。
- 不模糊或折射文字、图标、图表、视频像素和点击目标。
- Glass、Blur、Rim、Noise、Glow、Connector、Chart Fill 均设为 `Self Hit Test Invisible`。
- 只允许真实按钮和媒体控件拦截输入。
- 同一实例的 `selected` 与 `always` 保持互斥；同时最多一个 selected Screen Widget 和一个共享媒体会话。
- Idle 不使用持续流光、液体波动、彩虹边或折射动画；只使用短时事件动效。
- World Billboard 使用确定性静态高光，不伪造无有效变化的动态 Fresnel。
- 状态色只作用于状态灯、图标、Gauge/Trend 主体或显式强调指标，不铺满整块玻璃。
- 指标默认不强调；只有 `emphasized=true` 时进入主值视觉层级。
- 不复制 Apple 标识、专有素材、Figma 组件或未授权 SF 字体；描述为 visionOS-inspired。
- Web 编辑器继续使用 OntoTwin 黑白灰规范，不把 UE 玻璃视觉搬进浏览器。

## 文档职责

- PRD 只写功能设计变化、约束、契约、失败行为和验收标准。
- 实施记录写实际代码路径、技术取舍、偏离设计的最终结论和未完成边界。
- 宿主接入与验收写部署配置、构建/Cook 证据、当前宿主状态和人工待验项。
- 同一事实只保留一个权威位置，其他文档使用链接，不复制完整段落。
- 早期结论被后续验证推翻时，保留最终结论并简要记录替代关系；不要让两个互相冲突的“当前状态”并列存在。

项目文档权威来源：

- `docs/PRD/OntoTwin 3.7 顶部信息面板垂直链路 (PRD).md`
- `docs/PRD/OntoTwin 3.7.1 视频 URL 面板垂直链路 (PRD).md`
- `docs/PRD/OntoTwin 3.7.1 液态玻璃信息面板模板设计 (PRD).md`
- `docs/IMPLEMENTATION/3.7.1/OntoTwin 3.7.1 实施记录.md`
- `docs/IMPLEMENTATION/3.7.1/OntoTwin 3.7.1 宿主接入与验收.md`

## 参考资料路由

- 设计玻璃层次、颜色、字体、状态、动效或可访问性时，读取 [visual-language.md](references/visual-language.md)。
- 设计六模板、指标样式、视频容器、尺寸或锚点时，读取 [overlay-templates.md](references/overlay-templates.md)。
- 选择 Slate Postbuffer、BackgroundBlur、WidgetComponent、Retainer 或 SceneCapture 方案前，读取 [ue56-rendering-boundaries.md](references/ue56-rendering-boundaries.md)。
- 修改 Web 信息面板、继承、质量档或条件字段时，读取 [web-configuration.md](references/web-configuration.md)，并同时应用仓库 `ontotwin-ui` skill。
- 修改质量、状态、Gauge 或 Trend 的配置和运行载荷前，读取 [data-contract.md](references/data-contract.md)。
- 做实现审查、宿主验收或打包验收时，读取 [qa-checklist.md](references/qa-checklist.md)。

## 输出要求

功能设计或 PRD：

- 明确本次相对 3.7 基线的变化，不重述完整基础链路。
- 明确 Screen/World 差异、请求质量与自动回退。
- 区分当前可用能力和保留设计；Trend 没有真实历史提供者时必须标为禁用。
- 给出失败行为、可访问性、性能预算和验收标准。

实现：

- 保持 SceneManager、选择、继承、revision 和媒体生命周期，除非用户明确改变。
- 优先共享 Theme/Profile、Renderer 和内容组件。
- 材质、字体、Postbuffer 或 Blur 缺失时回退到可读面板，禁止透明空板或棋盘格。
- 先做静态/自动验证，再在真实 DX12 窗口、Standalone、Development 和 Shipping 中验收。

审查：

- 拒绝 per-panel SceneCapture、World 假“真实模糊”、整板霓虹状态色、持续折射和可命中的装饰层。
- 核对模型关联、文本对比、输入恢复、确定性回退、资源 Cook 和媒体释放。

