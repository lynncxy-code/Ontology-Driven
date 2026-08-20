# OntoTwin 4.0.3 实施记录

> 日期：2026-08-13  
> 状态：MVP 代码完成；后端与 Web 已生效；UE 插件已同步并通过 ZHHZEditor 正式宿主编译；阿里云真实 TTS 与 ZHHZ PIE 端到端已跑通，音色目录和精确结束计时待最终人工复测。

## 1. 已完成

### 数据与后端

- ProjectStore 升级到 schema v7，旧项目以内存惰性迁移补齐 `narration_defaults`、`narration_assets` 和 `narration_audit`。
- 路线点保留稳定 `waypoint_id`，增加字幕/语音模式、文本、分页断点、时长、触发半径和生成状态。
- 保留旧 `waypoints_ue_cm`，同时向新 UE 客户端投影结构化 `waypoints`。
- 增加 Provider 中立 TTS 边界和阿里云智能语音交互实现；未配置密钥时后端正常启动并明确返回未就绪。
- 语音使用项目级内容寻址 WAV 资产，校验 PCM16、单声道、8/16 kHz、大小和时长。
- 路线保存和语音生成分离；生成使用 revision 乐观锁并维护摘要、音频资产与审计记录。
- 增加项目默认声音保存接口；项目音色或参数变化时，继承路线的旧音频立即失效。

### Web 工作台

- 沿用 `/interaction?feature=routes`，未新增路由。
- 在路线检查器内增加项目默认声音、路线覆盖声音、点位解说、模式、触发半径和时长配置。
- 中文标点自动分页，并支持光标处分段和清除手动分页。
- 点位列表显示字幕、待生成、可用和失败状态。
- 未保存路线不能生成语音；项目默认声音和路线修改互相锁定，均采用显式保存和 Toast。
- Provider 未配置时禁用生成，但字幕路线仍可保存和运行。
- 项目默认声音和路线覆盖声音已由手填 `voice_id` 改为 Provider 音色目录下拉；首批提供小云、知小白、知小夏、知硕、艾夏，并继续兼容项目中已保存的目录外音色。

### UE 插件

- 解析带 ID 的运行点位和字幕/音频段，同时兼容旧坐标数组。
- RouteFollower 增加 `PausedForNarration`，按 Spline 累计距离与世界半径共同触发。
- 到点停靠后显示底部居中 Screen Space Narration HUD，提供分段进度和“跳过当前段”。
- WASD 中断整点解说并接管；恢复路线不重播该点；重启路线和新一轮 loop 会重置点位会话。
- 语音优先从 `Saved/OntoTwin/Narration/<sha256>.wav` 读取，缺失时经后端下载；下载与本地文件均校验 SHA-256 和 WAV 格式。
- 使用运行时 `USoundWaveProcedural`/`UAudioComponent` 播放；任何下载、摘要或 WAV 错误都降级为字幕并继续路线。
- 语音完成不再依赖 Provider 标称时长加 5 秒：UE 解析 WAV 副本并按实际 PCM 样本时长加 0.2 秒恢复路线，避免 `FWaveModInfo` 修复流式 WAV 头时污染内容寻址缓存。
- HUD 使用插件内 Noto Sans CJK 字体和现有玻璃主题 token，不需要宿主制作 UMG 资产。

## 2. 已验证

- 后端相关回归测试：55 项通过。
- 音色目录、WAV 实际帧时长、场景交互与 ProjectStore 定向回归：57 项通过；`interaction.html` JavaScript 语法检查通过。
- `interaction.html` 内联 JavaScript 语法检查通过。
- 浏览器实际加载通过：点位解说、分页预览、脏状态、生成禁用态和项目默认声音互锁均正常，控制台无错误。
- UE 5.6 `test0316Editor Win64 Development` 完整编译通过。
- UE 5.6 `ZHHZEditor Win64 Development` 正式宿主完整编译通过（2026-08-13）。
- 后端容器已重启，Provider 状态与路线接口返回 200。
- 已开通阿里云智能语音交互免费试用并创建 `OntoTwin-Narration` 仅语音合成项目；默认小云、中文普通话、16 kHz、WAV。
- 已用临时 AccessToken 完成真实语音合成：线路三起点生成 1 段 9.6 秒 WAV，RIFF/WAVE、SHA-256 与资产下载接口校验通过。
- 首次 ZHHZ PIE 发现 Windows 平台调用 `FPlatformMisc::GetSHA256Signature` 会触发 `No SHA256 Platform implementation` 断言；已改用 Windows BCrypt，并规定摘要校验不可用或失败时只降级字幕、不得终止 PIE。修复后的插件已再次通过 `ZHHZEditor Win64 Development` 编译（2026-08-13）。
- 阿里云部分流式 WAV 的头部声明时长大于实际文件内容，曾造成“声音结束后约 10 秒才继续”：例如标称 7.6 秒的片段实际 PCM 约 3.4 秒，再叠加旧保险时间 5 秒。后端现按实际可读取帧数记录时长，UE 按实际 PCM 长度恢复；修复版再次通过 ZHHZEditor 编译。
- 多段解说曾出现第一段结束后第二段只显示字幕：`USoundWaveProcedural` 被主动停止后，延迟到达的 `OnAudioFinished` 会误推进分段并取消第二段下载。现已移除该回调，实际 PCM 定时器成为唯一自动推进来源；手动跳过仍走显式操作路径。修复版已同步正式宿主并通过 ZHHZEditor 编译（2026-08-13）。

## 3. 正式宿主状态

- 源插件：`D:\tmp\digital_twin_aircraft\ue_project\Plugins\OntoTwinSync`
- 正式宿主：`D:\ZHHZ\ZHHZ\Plugins\OntoTwinSync`
- 已采用增量复制同步源码、Resources、Content 和描述文件；没有删除宿主额外文件，也没有覆盖 `Binaries`/`Intermediate`。
- 关闭 ZHHZ Unreal Editor 后已再次同步最终版本，并完成 `ZHHZEditor Win64 Development` 完整重建；OntoTwinSync、OntoTwinSyncEditor 与宿主模块均链接成功。

## 4. 明日需处理/人工确认

1. 当前 `.env` 使用阿里云控制台临时 AccessToken，仅供本轮测试且约 24 小时失效；长期部署需创建专用 RAM 程序用户并仅授予 NLS 语音服务权限。不要把密钥提交到 Git。
2. “下载—校验—缓存—播放”已在 ZHHZ PIE 跑通；最新的多音色选择和“实际 PCM 时长 + 0.2 秒恢复”需做一次最终人工复测。
3. 当前实现按需下载当前音频并永久缓存；PRD 中“当前点 + 后续 2 个语音点预取”尚未实现。
4. 背景声压低尚未启用。要保证告警声不被压低，需要 ZHHZ 明确提供“环境声”和“告警声”两个 SoundClass；在没有分类契约前不做全局压低。
5. 项目 JSON/PG 元数据可迁移，但产品级“单文件导出/导入同时打包二进制语音资产”尚无既有统一能力，需要和空间底图二进制一起设计归档格式。
6. ZHHZ PIE 需重点验收：起点解说、途经点解说、末点后继续/完成、跳过、WASD 接管、R 归线、重启、循环、断开后端后的本地缓存播放。
7. 全库 `unittest discover` 可执行 198 项，但仍有 6 个历史测试模块依赖未安装的 `pytest` 而在导入阶段失败；本轮未擅自新增依赖，4.0.3 定向回归无失败。

## 5. 最短续作顺序

1. 在 `.env` 配置测试用阿里云凭证并重建后端容器。
2. Web 给一个路线点输入两段解说，保存并生成语音。
3. ZHHZ PIE 验证字幕、声音、跳过和 WASD 中断。
4. 断开后端后再次运行，验证已缓存语音仍可播放。
5. 再决定是否补“后续 2 点预取”和 SoundClass ducking。
