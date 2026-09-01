# PAE Beta｜结构化动画说明工作台

这是一个独立的实验性网页样品，用于把结构化动画说明整理成可审阅、可调整的动画行为包。编辑页内置离线程序化 3D mock 资产：可旋转、平移、缩放、拾取对象并随时间轴播放；这些几何只用于审阅，不会写入导出包。它不修改 OntoTwin 主线、UE 工程或 Git 主分支。

## 打开方式

可以直接打开 `index.html`，也可以在本目录启动静态服务器：

```powershell
python -m http.server 8765
```

然后访问 `http://127.0.0.1:8765/`。

## 试用路径

1. 在“说明结构”选择工序、装配或状态模板；
2. 点击“一键生成动画草稿”；
3. 在“动画编辑”确认对象槽位、动作、时长和关键帧；
4. 在 3D 视口中拖拽旋转、Shift+拖拽平移、滚轮缩放，点击对象同步对象树；
5. 在“校验与导出”运行校验，查看 storyboard、Manifest 和 A 角调用样例；
6. 下载 `behavior-package-v1` JSON。

自动生成的动作始终标记为候选草稿，确认前不代表已批准的工艺或安全指导。

## 结构化输入最小格式

对于业务人员，推荐先填写 [结构化任务说明书（表现适配模板）](templates/动画说明书-人工填写模板.md)，而不是直接接触 JSON。模板只要求写业务对象、事项顺序、开始条件、结果状态和依赖关系；唯一编号、时间、坐标、旋转轴、关键帧和具体表现方式由编辑器补齐。截图反推的业务填写示例见 `examples/linkage-assembly-instruction-human.md`。

```json
{
  "title": "设备巡检说明",
  "template_id": "template.state.v1",
  "spec_id": "SPEC-CHECK-001",
  "source": { "version": "1.0", "revision": "R1", "origin": "巡检表" },
  "steps": [
    {
      "code": "C010",
      "name": "确认待机",
      "category": "检查",
      "description": "确认设备处于安全静止状态。",
      "standard": "巡检项 01",
      "targets": ["assembly"]
    }
  ]
}
```

更完整的机器输入示例见 `examples/inspection-spec.json`；如果要直接描述动作、并行关系和素材引用，可参考 `examples/explicit-animation-spec.json`。`examples/linkage-assembly-instruction.json` 是人工说明书经过编辑器适配后的可导入样例；`examples/unbound-target-spec.json` 展示了未绑定目标会如何被保留为占位并在校验时阻断导出，`examples/invalid-action-spec.json` 可用于检查非法动作类型的阻断提示。首期只接受结构化 JSON，不解析自然语言、扫描件或 OCR。

截图反推的最小装配说明见 `examples/linkage-assembly-instruction.json`。它把“物料到位 → 定位左右轴承 → 固定组件”写成 3 个说明块、6 个显式动作；`start_s` 仅用于复现 mock 的时间轴，省略时编辑器会按说明块顺序排程。

内置 mock 资产会按 `asset_ref` / 对象 ID 映射到装配基座、连杆、轴承、泵体、指示灯、阀门、工具、字幕面板或通用部件的三角网格。未知对象仍会显示通用 3D 部件，并保留绑定校验；这不是生产模型库。

在编辑页点击“添加对象”时，可选填写 `3D mock 类型`（例如 `pump-body`、`valve`），用于把新对象映射到对应的 Beta 三角网格；导出时最多保留该识别标签，网格和纹理不会写入行为包。

## 输入边界

- `template_id` 只选择动画模板；“工序”不是固定输入类型。
- 每个说明块可提供 `targets`，也可提供动作闭集字段（`id/event_id`、`kind/action/type`、`target/target_ref`、`duration_s/duration`、`start_s`、`parallel`、`params/extra`、`asset_ref`、`easing`、`loop`、`enabled`）。未列字段不会被自动推断。
- 未知目标不会自动改绑到内置对象，会生成待绑定占位对象；补齐 `slot` 和 `asset_ref` 后才能通过校验。
- 页面只生产逻辑行为包和 storyboard 摘要，不修改 `frontend/`、`backend/`、`ue_project/`、`test0316` 或 `git-main`。Beta 输出需经 A 角适配器映射到受控实时路由协议，不直接注册到 A/UE。
