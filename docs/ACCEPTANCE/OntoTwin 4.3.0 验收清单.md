# OntoTwin 4.3.0 验收清单

> 日期：2026-08-18  
> 状态：编译验收通过，待 UE 重启后运行验收

## A. 编译与部署

- [x] OntoTwinSync Development Editor 编译及后缀模块链接成功。
- [x] 插件描述版本为 4.3.0。
- [x] 当前工程通过 Junction 使用主仓插件源码。
- [x] `/Game/Art` 已进入 `DirectoriesToAlwaysCook`。
- [x] 非编辑器 `DigitalFactoryBase Win64 Development` 编译链接成功。

## B. StaticMesh 回归

- [ ] 原有 `/Game/...` StaticMesh 正常加载。
- [ ] 本地 glb 与 ArtStudio 路径正常加载。
- [ ] `assembly_v1` 多部件预览不受影响。
- [ ] 资产热替换、显隐、运行时编辑正常。

## C. SkeletalMesh

- [ ] 类型审核可确认 SkeletalMesh，状态显示“运行时支持”。
- [ ] 直接绑定“淋雨” SkeletalMesh 后显示参考姿势和正确材质。
- [ ] 射线选择、聚焦、Runtime Gizmo 和信息面板锚点正确。
- [ ] Representable 卸载后组件释放，重新加载后恢复。

## D. Actor Blueprint

- [ ] `BP_LY` 被识别为可运行 Actor Blueprint。
- [ ] 绑定后以 TwinInstance 子 Actor 生成。
- [ ] Construction Script、BeginPlay、Tick 和资产自身动画正常。
- [ ] 子组件命中后可以解析回所属 TwinInstance。
- [ ] Blueprint 与 StaticMesh/SkeletalMesh 双向热切换无残留 Actor。
- [ ] Representable 卸载后子 Actor 销毁；重新加载后重建。

## E. 非法 Blueprint 与失败回退

- [ ] Widget/Anim/Component/Pawn/Character/Controller Blueprint 不可确认，并显示原因。
- [ ] 未 Cook 或不存在的资产路径输出结构化日志。
- [ ] 加载失败显示占位 Cube，轮询与运行时编辑器不崩溃。

## F. 打包程序

- [ ] Development/Shipping 包中 StaticMesh 正常加载。
- [ ] Development/Shipping 包中 SkeletalMesh 正常加载。
- [ ] Development/Shipping 包中 `BP_LY` 正常生成并运行。
- [ ] 打包程序中的热替换、显隐和选择行为与 PIE 一致。

## G. 验收结论

- 编译版本：待填写
- 宿主工程：`DigitalFactoryBase_SCC`
- 验收人：待填写
- 结论：待填写
