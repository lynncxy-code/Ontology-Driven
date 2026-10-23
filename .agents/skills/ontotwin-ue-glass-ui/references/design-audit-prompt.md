# 3D 液态玻璃视觉审计沉淀与提示词

## 何时使用

当用户提供 UE 截图、Widget 流程、录屏描述或要求把液态玻璃视觉积累为可复用规范时使用。现有 `SKILL.md`、`visual-language.md`、`overlay-templates.md` 和 `qa-checklist.md` 是事实来源；本文件只增加审计和写回方法。

## 1. 先分离证据、决策与提案

- **观察事实**：在指定分辨率、视角、场景亮度和模板中直接看到的表现；附截图/录屏时间点或 Widget 区域。
- **既有决策**：当前技能和 reference 中已确认的 Screen/World、High/Balanced/Performance、六个模板、数据契约、输入与性能边界。
- **待确认提案**：新材质参数、层级、动画、锚定或模板变化；必须说明风险、回退路径和验证方式，不能因为一张效果图就直接写入基线。

不要把 Screen Space 的场景采样、World Space 的伪玻璃、业务告警阈值、或 UE 中未提供的材质能力混为一谈。

## 2. 3D 提取矩阵

1. **场景与渲染**：UE 版本、Widget Space、相机/视角、背景亮度与频率、DPI、安全区、目标平台；Screen/World 路径和质量档位。
2. **玻璃分层**：底面 tint/opacity、blur 或伪玻璃、rim、inner highlight、noise、refraction、scrim、连接线；标出装饰层与锐利内容层、命中测试设置。
3. **内容与模板**：六个用户模板、标题/状态/指标/趋势/媒体/控件层级；文本、图标、图表、视频是否保持锐利。
4. **状态语义**：normal/info/warning/critical/offline/unknown 的颜色角色、文字和形状线索；区分 `status.level` 与 metric `state`。
5. **锚定与输入**：选中/常驻、屏幕边缘避让、跟随平滑、遮挡/出屏/销毁清理、E/指针/键盘焦点、输入恢复。
6. **运动与适配**：打开/关闭/hover/状态变化的时长和幅度；idle 是否静止；ReduceMotion、HighContrast、ReduceTransparency 的替代效果。
7. **性能与失败**：Postbuffer/SceneCapture/RenderTarget 所有权、面板数量、GPU/Slate 预算、缺材质/字体/模糊支持时的可读降级、PIE/Standalone/打包验证。

## 3. 可复制给 AI 的审计提示词

```text
你是 OntoTwin UE5.6 液态玻璃信息叠加层的 UX/技术视觉审计师。请基于我提供的 UE 截图、Widget 流程、录屏描述和数据背景，把视觉表现转换成可复用的 3D 设计需求，同时守住现有 I3D_Overlay 合同、六个模板和渲染性能边界。

项目基线：
- 规范来源：ontotwin-ue-glass-ui/SKILL.md 及其 references；已确认的 Screen/World、High/Balanced/Performance、输入、数据契约和回退规则不可被单张效果图覆盖。
- 视觉基线：visionOS-inspired 但属于 OntoTwin；玻璃装饰层与锐利内容层分离，idle 无连续流光/折射。
- 不得假设 World Space 有真实场景模糊，不得从格式化字符串推断业务阈值。

输入材料：
- UE 版本、Widget Space、相机和目标平台：{填写}
- 目标实例/模板及状态：{填写}
- 截图、录屏或流程来源：{填写}
- 背景亮度、分辨率、DPI 和质量档位：{填写}
- 已确认的业务、输入和性能约束：{填写}

请按以下顺序输出：
1. 场景、用户任务与受影响模板。
2. 观察事实表：区域、可见特征、渲染路径、来源、置信度。
3. 视觉 token：tint/opacity、scrim、rim、highlight、blur/伪玻璃、radius、间距、字体/字号/对比度、状态色和非颜色线索；每项标记“沿用现有 / 观察 / 待确认”。
4. 分层与输入图：装饰层、锐利内容层、实际命中控件；列出 Self Hit Test Invisible 要求。
5. 模板与状态规范：标题、状态、metric、trend、media、control 的 anatomy 和空/加载/失败/离线/未知状态。
6. Screen/World 与 High/Balanced/Performance 决策：说明能力差异、降级顺序、失败时的可读表面。
7. 锚定、焦点和运动：安全区、跟随/遮挡/销毁、打开/关闭/状态 pulse、减少动画替代。
8. 可访问性、性能和打包验收：对比度、DPI、GPU/Slate、面板数量、PIE/Standalone/Development/Shipping。
9. 禁止清单：逐项检查真实场景 blur 误称、每面板 SceneCapture、内容被折射、霓虹大色块、连续液态运动、装饰层抢输入等风险。
10. 待确认问题：只列会改变渲染路径、共享资源、业务语义、输入或验收预算的问题，并说明选择影响。
11. 沉淀补丁草案：指出写入 SKILL.md 或哪个 reference 的具体段落；仅写入已确认内容，提案保留为待确认。

输出要求：给出可执行的逻辑像素、百分比/范围、时长、对比度和预算；不要复制 Apple 标识、SF Symbols 或未授权字体；不要把 UE 玻璃规则带入 OntoTwin Web 编辑器。
```

## 4. 写回技能的规则

- 先复用现有 baseline 和六个模板；截图中的新参数只能作为候选值，并附质量档位、平台和验证条件。
- 只有用户明确确认且通过相应 QA 的提案才能写入 `SKILL.md` 或 reference；不确定项记录为待确认，不改变运行时契约。
- 将跨模板重复的规则写入 shared component/reference；模板特例必须注明适用范围、资源成本和回退路径。
- 每次沉淀注明来源、日期、质量档位和测试环境；不为单一场景的亮度或构图添加全局材质规则。
- 任何新增视觉效果都必须同时说明可读性、命中测试、ReduceMotion/HighContrast/ReduceTransparency 和性能影响。
