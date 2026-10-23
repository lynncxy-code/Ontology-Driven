# 2026-09-16 遗漏修复与 main 发布记录

## 本轮纳入

| 批次 | 提交 | 内容 |
|---|---|---|
| UE 与 Presentation | ce8f022 | 找回 F7 按钮、重复点击保护、空正文/空白字符收缩、原 Dock/Overlay 自测；恢复三方案选中态；补齐 5 个 Presentation 函数；纳入本地方案切换、Dock、小地图投影、实时通道与高亮实现及配套材质/测试 |
| 品牌与 ArtStudio | 4deeb3c | 新 Logo/页签图标/标题、缺失的 BufferGeometryUtils.js、ArtStudio coverUrls 数组兼容、静态资源回归检查 |
| 运行态与标定 | 0d7ab64 | 外部数据多流状态/健康监测、UE/网页读取当前项目一致性、漫游底图方向和版本冲突保留草稿、标定页滚动与方向恢复、Web 交互配置布局 |
| 部署 | 6d27565 | Hyper-V 前置重启、按发布版本保留升级前基线且同包重试不重复备份、源码指纹缓存参数、安装包运行验收入口 |
| 测试隔离 | b6ac106 | 场景测试使用临时回收站，不再依赖当前机器已有 data/trash |
| 发布记录 | 本文件所在提交 | 记录实际验证范围、未纳入内容与跨机使用边界 |

代码批次共 42 个文件，3883 行新增、812 行删除，含两个高亮材质资产。本文件是额外的发布记录。

## 不是整目录回滚

恢复时把原修复叠加到当前源码，保留后来已做的新 Dock 等修改。三方案选中态按当前按钮结构恢复，选中项禁用重复选择，同时使用可读的黑白文字/背景和“当前”提示，不覆盖旧版整个小地图类。

前端遵循现有 OntoTwin UI 结构，不重新设计 Logo/布局；UE 信息面板按六模板现有结构恢复可选空行与间距折叠，没有改数据协议、玻璃渲染路径、媒体生命周期或业务存储格式。

## 已执行验证

### 干净检出，而非只测脏工作区

使用独立工作树 D:/tmp/ontotwin-omission-verify-20260916 验证已提交版本，不携带主工作区未提交数据和源码。UE 验证宿主和外部 glTFRuntime 依赖仅放在验证目录，没有加入 main。

- UE 5.6：独立 OmissionVerifyEditor / Win64 / Development，101 项构建动作，完整编译和 DLL 链接成功。
- 编译覆盖 OntoTwinSync、OntoTwinSyncEditor、OntoTwinIndustrialBehavior 与 glTFRuntime。MSVC 14.44 有“非首选版本”提示，构建结果为 Succeeded。
- 两项无业务写入的 UE 自动测试通过，失败/警告均为 0：
  - OntoTwin.UI.RecoveredDockOverlayAndSchemeSelection：两种纯文字模板、Screen/World、空串/全空白收缩、清零间距、内容恢复、Dock 实体按钮及点击绑定、三个选中态轮转。
  - OntoTwin.WebInteraction.BusinessHighlight：成员选择、材质恢复、动画不变、切换/返回/退出与销毁清理。
- OntoTwin.Presentation.ExecutableChannels：冷进程运行通过；动画运动、特效切换、材质覆盖、复位和业务变换不变。
- 后端和资源 84 项测试：在禁止联网、显式 JSON 存储、源码只读挂载的一次性容器中通过。覆盖 presentation_catalog、presentation_routing、snapshot_delta、external_data_control、scene_interaction、release_assets。
- 前端 7 个脚本块/模块通过 Node 语法检查。
- 安装基线重置 Bash 回归在一次性容器临时目录中通过；没有操作实际业务磁盘、服务或数据库。
- 修改的 PowerShell 通过 AST 语法检查，WiX XML 解析通过。
- git diff --check 通过；发布差异不含 beta/zero_bay_twin/。

首次干净环境后端测试暴露了测试回收站默认指向源码目录的问题，已修复测试隔离并重跑全部 84 项通过。没有靠复制本机 data 目录让测试通过。

本地证据保留在：
- _runs/omission-repair-20260916/ue-tests/index.json
- _runs/omission-repair-20260916/ue-tests.log
- _runs/omission-repair-20260916/presentation-tests/index.json
- _runs/omission-repair-20260916/presentation-tests.log
- _runs/omission-audit-20260916/（原始历史补丁和审计）
这些原始日志/本机历史材料未打包上传。

## 验证边界

- 本轮 UI 自动测试使用 NullRHI；没有声称通过 ZHHZ 实际场景的人工视觉验收或 Shipping Cook。
- Dock 按钮的真实角色进入/重复点击测试原实现已恢复，但依赖 ZHHZ 场景的完整 69 项历史自测本轮未重新执行。独立宿主已验证按钮存在、绑定和代码编译。
- 没有覆盖正在运行的 0bay 工程插件，也没有把新 DLL/源码部署到 ZHHZ 工程副本；没有保存地图、修改业务数据库、更新安装包或改变服务器运行状态。
- 本轮不修复审计提到的 F10 无碰撞点击回退覆盖不足；它不是已确认的历史回退，需单独运行场景验收。

## 明确未纳入

- beta/zero_bay_twin/：按用户要求保持不上传。
- 9 月 16 日进行中的数据集交付包/附件/绑定更新：保留本地，不混入遗漏修复。backend/app.py 仅提交 ArtStudio 封面兼容部分，交付包回调修改仍留本地。
- monitor-test 页面、流送试验工具、本机迁移结果/映射数据、文档删除、技能规则及无关草稿。
- 旧 RC10 热修复器、origin/ue-project 旧工程历史，以及独立远端 fix/artstudio-download-timeout 分支：属于旧版/另行待合并内容，不冒充此次丢失修复直接覆盖 main。

## 另一台电脑怎么生效

1. 在本地修改已妥善保存的前提下，更新 main，核对本文件与上述修复提交存在。
2. Web：更新实际运行的源码/镜像并重启相应服务，必要时强制刷新浏览器；只更新 Git 不会更新已经构建的 Docker 镜像。
3. UE：先核对目标工程插件与 main 的双向差异、备份工程特有修改，确认目标 UE 进程已退出，再同步匹配源码/Content 并重新编译。不要只拿旧 DLL，也不要用旧工程插件反向覆盖 main。
4. 如需发布安装包，重新 Cook/打包并验收。
5. 三方案配置、项目地图/模型和业务数据独立于插件代码；仍需对应的 ZHHZ 工程与数据交付，git pull 不会自动获得它们。

插件同步脚本“成功复制”不等于功能最新。再次同步前必须检查工程是否存在主仓库未收录的差异，避免已验收修改被旧副本覆盖。

