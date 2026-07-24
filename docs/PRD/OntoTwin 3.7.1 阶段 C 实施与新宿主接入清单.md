# OntoTwin 3.7.1 阶段 C 实施与新宿主接入清单

> 日期：2026-07-23  
> 主线：OntoTwin Nexus  
> 正式宿主：`D:\ZHHZ\ZHHZ`  
> 回归宿主：`D:\tmp_ue\test0316`（只用于编译与兼容回归）

## 1. 阶段 C 已完成

- Web 信息面板编辑器新增正常白底的“展示效果”区域。
- 支持 `high / balanced / performance` 三档请求质量，默认 `balanced`。
- ObjectType 保存类型默认；实例只保存稀疏 `presentation` 覆盖，恢复继承时删除该覆盖。
- 批量覆盖和批量恢复使用现有模态确认与原子 revision 保存。
- Web 只做结构预览，并明确最终透明、模糊、曝光和遮挡以 UE 为准。
- 后端校验质量枚举；缺失时在内存补齐 `balanced`。
- 运行快照向 UE 下发：

```json
{
  "presentation": {
    "quality_tier": "balanced"
  }
}
```

- UE Widget 读取每个面板的 `quality_tier`；宿主设置只决定 High 能力是否可用及占用哪个 PostRT。
- 运行端仍只允许向下回退，不把 `effective_quality` 或降级原因写回项目。

## 2. 存储影响

本阶段没有增加 ProjectStore 顶层字段、`schema_version`、PG 列或迁移脚本。

质量档位保存在既有位置：

- 类型默认：`object_type.interface_configs.I3D_Overlay.values.presentation`
- 实例覆盖：`instance.render_config.interface_overrides.I3D_Overlay.values.presentation`

JSON 继续保存嵌套对象；PostgreSQL 继续保存到既有 JSONB。旧配置不在读取时强制写盘，下次用户正常保存时才补齐 `balanced`。

## 3. 任意新宿主真正需要做的事

1. 关闭 UE Editor 和该宿主的 EXE。
2. 安装完整的 `OntoTwinSync` 插件，并启用 `OntoTwinSync` 与 `glTFRuntime`。
3. 同步插件的 `.uplugin`、`Source`、`Content`、`Resources`；不要复制其他项目的 `Binaries` 或 `Intermediate`。
4. 由新宿主冷编译插件。
5. 在实际持久运行关卡中保留恰好一个 `ATwinSceneManager`。
6. 后端不在本机时，配置 Manager 的 `BackendBaseUrl`。
7. 将该宿主自己的 UE Project ID 绑定到目标 OntoTwin 数据集。
8. 先用默认 Balanced 做 PIE、Standalone 与 EXE 验收，再做 Shipping Cook。

无需复制 0316 的地图、GameMode、输入、人物、路线、出生点或锚点；无需把插件 Widget、材质和字体复制到 `/Game`；无需为 3.7.1 填写固定 UE Level。

## 4. 三档质量对宿主配置的影响

### Balanced（默认）

- 插件同步后开箱运行。
- 不占用 Slate Postbuffer。
- 不要求修改 `DefaultEngine.ini` 或 `DefaultGame.ini`。

### Performance

- 由 Web 对类型或实例选择。
- 不占用 Slate Postbuffer。
- 不要求宿主配置。

### High Screen

只有宿主允许 High Screen 时，才增加以下配置。

`DefaultEngine.ini`：

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

此外必须使用 DX12，确认 RT0 没被其他 UI 插件占用，并在修改后完整重启。Web 中选择 High 只是“请求”；宿主没授权、RT 冲突或运行能力不足时，UE 自动降到 Balanced，再不支持则降到 Performance。

`RequestedQuality` 仍作为旧载荷或开发诊断的全局默认保留，但阶段 C 的正常业务配置不依赖它。

## 5. 正式宿主 `D:\ZHHZ\ZHHZ` 当前状态

已满足：

- UE 5.6，DX12 + SM6。
- `.uproject` 已启用 `OntoTwinSync` 与 `glTFRuntime`。
- 正式关卡已有 `TwinSceneManager_0`。
- `ueproj_ZHHZ` 已与当前目标数据集匹配。
- 已配置本机 HTTP 代理绕过。
- 2026-07-23 已将本仓库当前最终版 `OntoTwinSync` 同步到正式宿主。
- 已同步 `.uplugin`、`Config`、`Source`、`Content`、`Resources` 和 `README.md`，共 62 个部署文件；源/目标 SHA-256 差异为 0。
- 正式宿主旧插件已备份到 `D:\ZHHZ\OntoTwinSync_Backups\ZHHZ-OntoTwinSync-20260723-153450`。
- 正式宿主插件中的旧 `Binaries`、`Intermediate` 已清除，未从 0316 复制编译产物或项目内容。

后续状态（2026-07-24）：

- 阶段 D 已完成 Value/Gauge 垂直链路；没有真实历史数据，因此 Trend 保持禁用。
- 正式宿主已完成 Editor Development、Game Development 和 Shipping 编译/Cook。
- High 材质已由插件类硬引用自动进入 Cook，无需宿主新增 OntoTwin AlwaysCook 目录。
- High 仍未授权；正式宿主继续保持 Balanced。
- 自动化结果和剩余人工窗口验收见《OntoTwin 3.7.1 阶段 D-E 实施与验收记录》。

本次只替换正式宿主的 `Plugins\OntoTwinSync`；未修改地图、关卡 Actor、项目 Config、输入、路线、出生点或数据绑定。

## 6. Cook 前置验证

插件已经包含 `/OntoTwinSync/UI/PAL_OntoTwinUI`，目标是由插件自己保证 UI 资源 Cook，不让每个宿主永久维护 `DirectoriesToAlwaysCook`。

但 UE 5.6 默认的 PrimaryAssetLabel 扫描路径以 `/Game` 为主，因此仍需在一个没有手工 AlwaysCook 目录的新宿主做干净 Shipping Cook 证明：

- 五个 `M_OT_GlassHigh_RT0...RT4` 进入 Cooked Asset Registry / 容器。
- 插件字体进入 Stage 目录。
- 打包 EXE 能加载 High 材质；缺失时仍可读地回退。

正式宿主第一次迁移先不要手工增加 `DirectoriesToAlwaysCook`。若干净 Cook 失败，应修正插件侧扫描或 Cook 清单；临时宿主配置只能作为诊断兜底，不能成为长期交付要求。

## 7. 已完成验证

- 后端 Overlay、媒体和 ProjectStore：24 项通过，包含真实 PostgreSQL JSONB 往返。
- 前端内联 JavaScript：语法检查通过。
- 浏览器只读验收：三档、回退说明、类型默认和实例继承状态正确，无控制台错误。
- 运行快照：`presentation.quality_tier=balanced`、`config_revision=t1-i0` 已进入 UE 接口载荷。
- UE5.6 Editor Development：通过。
- UE5.6 Shipping：通过。

## 8. 正式迁移顺序

已完成：关闭正式宿主 UE → 备份旧插件 → 同步完整插件部署文件 → 清除旧插件编译产物。

阶段 D/E 已执行；下一步只进行记录中列出的真实窗口、输入、视频生命周期、性能与 High 授权后验收。
