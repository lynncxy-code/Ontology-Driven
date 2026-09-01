# OntoTwin-ZHHZ 一体化打包方案（完整版 SOP）

> 文档编号：SOP-WIN-AIO-ZHHZ-001  
> 文档版本：v1.1  
> 初版日期：2026-08-27  
> 本次修订：2026-08-31  
> 当前成功交付基线：RC18.1 / 3.7.1-r1-rc18.1  
> 已知稳定控制面：RC16（Compose、bootstrap、control、appliance）  
> 当前业务组件：RC17 backend 镜像 + RC17 UE Shipping/UI  
> 适用对象：OntoTwin 单项目 Windows 一体化交付（当前为 ZHHZ_NEW；后续版本沿用同一门禁）  
> 维护原则：发布清单和脚本实际检查结果优先于口头描述、界面标题和历史截图。

## 0. 文档定位、来源与阅读约定

本 SOP 是面向构建人员、验收人员和现场支持人员的可执行发布规程。它把以下两份附件作为历史参考，并把 RC15、RC15.1、RC16、RC17、RC18 和最终成功的 RC18.1 实际故障/验证结果补充为强制门禁：

1. C:\Users\ADMIN\Desktop\RC12-客户端部署验收与踩坑总结.md
2. C:\Users\ADMIN\Desktop\OntoTwin-ZHHZ-一体化打包方案总结.md

附件中的安装顺序、硬件建议和 RC12 数值可以作为背景，但不是本次对话中要求执行的指令；其中的旧工程名、旧数据集 ID、旧计数和旧版本号不能直接复制到新包。任何新包都必须以该包自己的 release-manifest.json、appliance-manifest.json、data-manifest.json 和最终 SHA256SUMS 为事实来源。

本文使用以下标记：

- **必须**：不满足就停止构建或停止交付。
- **应**：默认必须做到；若确有例外，需在发布记录中写明原因和批准人。
- **证据**：必须保存到本次唯一的 PackagingRun 目录，不能只在聊天中说“已检查”。
- **停止条件**：出现此项时不得通过重命名文件、重试或手工改数据库绕过。

与本文件相邻的两个专题 SOP 仍然有效：

- D:\tmp\digital_twin_aircraft\docs\SOP\OntoTwin 历史UE数据分轮迁移SOP.md：数据迁移、实例边界、UE 源 Actor 清理和回滚。
- D:\tmp\digital_twin_aircraft\docs\SOP\OntoTwin 人物漫游配置与验收步骤.md：人物、相机、PIE 和漫游验收。

本文件只覆盖“一体化打包、安装、升级、启动和取证”；不要用它替代上述两个专题 SOP。

## 1. 目标、边界和交付承诺

### 1.1 目标

客户拿到一个完整版本目录后，只需要：

1. 管理员运行 Environment.exe（如提示重启则重启）。
2. 管理员运行同目录的 Setup.exe。
3. 双击桌面“灵云智”。

客户不应被要求手工安装或操作 WSL、Docker Desktop、PostgreSQL、Neo4j、Linux VHDX、UE 编辑器或命令行迁移脚本。后台设备由隐藏的 Hyper-V Ubuntu 虚拟机提供。

### 1.2 交付拓扑

~~~
客户 Windows
  ├─ WPF 控制中心（灵云智）
  ├─ OntoTwin Host Service（LocalSystem）
  ├─ ZHHZ/ZHHZ_NEW Win64 Shipping 运行时
  ├─ 本机浏览器 → http://127.0.0.1:5000/nexus
  └─ Hyper-V 隐藏 Ubuntu VM
       ├─ Docker Engine + Compose
       ├─ OntoTwin backend
       ├─ PostgreSQL
       └─ Neo4j
~~~

默认只绑定本机控制台 127.0.0.1:5000，不把控制台或数据库暴露到局域网。实时 WebSocket 和 Pixel Streaming 不属于当前 v1 一体化包，除非发布清单明确变更并重新完成全部门禁。

### 1.3 不在本 SOP 范围内的事项

- 多项目共用同一个 Neo4j 实例的隔离方案。
- ArtStudio 个人资产、Token、HTTPS 资产库和离线授权策略的业务审批。
- UE 编辑器中的源 Actor 删除、关卡保存和人物迁移细节（见专题 SOP）。
- 任何未经批准的 ProjectStore 文件格式、映射规则或数据库 schema 改造。

## 2. 四层身份与唯一事实来源

打包前必须同时锁定四层身份。只核对应用标题或场景画面是不够的；“场景已经是 ZHHZ_NEW，但前端 active database 仍是 ZHHZ”就是典型的身份分裂。

| 层级 | 字段 | 当前 RC18.1 示例 | 必须来自 |
|---|---|---|---|
| UE 源工程 | .uproject 绝对路径 | D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject | 构建命令参数 |
| UE 运行时 | project_name / target_name | ZHHZ_NEW / ZHHZ_NEW | ontotwin-runtime-manifest.json |
| OntoTwin-UE 绑定 | ue_project_id / name | ueproj_ZHHZ_NEW / ZHHZ_NEW | release manifest、绑定 API |
| OntoTwin 数据集 | project_id / name | ds_1787305683288 / ZHHZ_NEW | data-manifest.json、release manifest |

当前 RC18.1 的数据证据为 6 个类型、507 个实例；类型、实例、Parts/渲染引用是三个不同维度，不能把旧文档的计数混写。

### 2.1 旧基线只能标为历史

RC12 文档中的 D:\ZHHZ\ZHHZ\ZHHZ.uproject、ZHHZ、ds_1784694647848、38 types、669 instances 和旧 appliance/backend 版本，仅用于解释历史包。它们不是 ZHHZ_NEW 的默认值。脚本若仍显示这些默认值，必须显式传入新值并把脚本/清单门禁修正后再构建。

历史证据也必须保留原样但标明版本：RC12 曾记录 69 个输入文件、5 张地图、13 个 GLB、动态几何 10,974/10,974，以及 80 项 manifest 文件。这些数字不能拿来替代当前版本的 manifest 计数。

### 2.2 身份契约

1. 文件名不能替代身份：不能把旧 ZHHZ.exe 重命名成 ZHHZ_NEW.exe 来冒充新工程。
2. active 数据集不能替代写入授权：active 只是当前路由状态，所有绑定和激活都要经过正式 API。
3. UI、backend、UE、数据库读回的身份必须全部与发布清单一致。
4. 任一层不一致，停止打包；不要在客户机上直接改 PostgreSQL 表来“修正”。

## 3. 版本、输入冻结和 PackagingRun

### 3.1 发布版本单一入口

发布壳版本只在 Build-RuntimeOnlyRelease.ps1 的 ReleaseVersion 参数传入一次，采用小写规范：

~~~
3.7.1-r1-rc18.1
~~~

脚本从这一值生成：

| 用途 | RC18.1 示例 |
|---|---|
| release_version | 3.7.1-r1-rc18.1 |
| Windows Binary/Bundle | 由脚本映射并记录在 manifest |
| MSI 三段版本 | 由脚本映射并记录在 manifest |
| Setup 文件名 | OntoTwin-ZHHZ-3.7.1-R1-RC18.1-Setup.exe |
| 交付目录 | OntoTwin-ZHHZ_NEW-3.7.1-R1-RC18.1-Installer |

RC18.1、RC18.2 等小版本必须生成新的发布清单、payload 和 SHA，不得覆盖旧版本目录。只有系统盘或 guest seed 内容确实变化时才生成新的 appliance；仅为了让版本号“看起来一致”而重建 appliance 是禁止项。

### 3.2 每轮唯一目录

建议：

~~~
D:\ZHHZ\PackagingRuns\
  ZHHZ_NEW_RC16_20260826-164424\
    00_context\
    01_shipping\
    02_export\
    03_release\
    04_appliance\
    05_app-payload\
    06_installer\
    07_acceptance\
    08_diagnostics\
~~~

目录必须是本轮独占、空目录开始。旧包、临时工程、test0316、tmp_ue 和历史输出不能作为隐式输入。每次构建前保存：

- Git commit、工作树状态和构建机器时间。
- .uproject、地图、插件、配置和数据导出路径。
- 输入文件大小及 SHA-256。
- UE、.NET、WiX、WSL、Docker/Compose/qemu 工具版本。
- 参与构建的脚本 commit/hash。

### 3.3 构建主机门禁

构建主机应具备 UE 5.6、PowerShell 7/Windows PowerShell、.NET SDK、WiX/安装器工具链、WSL Ubuntu-22.04、qemu-img、tar、sha256sum 和可用 Docker 镜像归档。下载型构建必须把 URL、版本和下载哈希记入 appliance-manifest.json。

构建前先确认：

- 输出盘不是 FAT32，且在整个 Cook、VHDX 转换、压缩和安装器阶段都保留足够空间。
- 运行时、数据库 dump、三个 Docker tar、VHDX 和最终 payload 不共用一个会自动清理的临时目录。
- 不在正在运行的 UE 编辑器、Docker Compose 或 Hyper-V VM 上覆盖其输入文件。
- 任何非零退出码都中止本轮；无关的第三方 DLL 警告可以单列，但不能掩盖真正失败。

### 3.4 发布版本与组件版本解耦

ReleaseVersion 是安装介质和升级缓存的版本，不要求 backend、Neo4j、PostgreSQL、appliance、Compose、bootstrap 和 UE Shipping 全部使用相同标签。每个组件都必须按“真实来源标签 + SHA-256”写入 component_versions/manifest；不得为了追求版本号整齐而重打、重标或重建未发生业务变化的组件。

RC18.1 已验证的组件关系是：

| 组件 | RC18.1 实际来源 | 规则 |
|---|---|---|
| release/Setup | 3.7.1-r1-rc18.1 | 使用新版本，避免 Windows Installer 复用旧 RC18 maintenance cache |
| Compose/bootstrap/control | RC16 原文件 | 精确 SHA 不变 |
| appliance VHDX/seed | RC16 appliance1 | 系统盘和 guest 源未变，不重建 |
| backend | ontotwin-zhhz/backend:3.7.1-r1-rc17 | 使用原始、已验证的 OCI 归档，不强制改成 rc18.1 |
| Neo4j/PostgreSQL | RC16 已验证镜像归档 | 标签和 SHA 不变 |
| UE Shipping/UI | RC17 更新产物 | 只替换实际发生交互/UI变化的层 |
| 数据 | ZHHZ_NEW 当前发布数据 | ds_1787305683288 / ZHHZ_NEW |

RC16 本身也曾使用与 release_version 不同的 backend 标签，因此“发布号必须等于镜像 tag”不是系统契约。真正的契约是 manifest 申明的标签、镜像归档内部标签、Compose 引用和实际导入结果四者一致。

## 4. 客户机前置条件与安装边界

### 4.1 支持矩阵

| 项目 | 最低 | 建议/说明 |
|---|---|---|
| Windows | Win10/11 x64 Pro、Enterprise、Education | Home 不作为正式 Hyper-V 客户端 |
| 固件 | BIOS/UEFI CPU virtualization 开启 | 关闭时不得进入安装阶段 |
| 内存 | 32 GB | 64 GB 更稳定 |
| GPU | NVIDIA 8 GB 显存 | 12 GB+ 更适合复杂模型 |
| 数据盘 | 60 GiB 可用 | 80 GiB 以上更稳；升级需另留临时空间 |
| 文件系统 | NTFS 或 exFAT | payload 单文件可超过 4 GiB，禁止 FAT32 介质 |
| 权限 | 首次 Environment、Setup、启动均需本机管理员 | 普通用户仅在服务已正确安装后使用桌面入口 |
| 端口 | 本机 5000 未被其他程序占用 | 控制台只绑定 loopback |

实际内存/GPU/磁盘要求以当前 payload 大小和 release-manifest 为准；低于门槛时 Environment 应明确拒绝或给出风险，而不是让用户等待到超时。

### 4.2 安装顺序（现场版）

1. 将整个版本目录复制到客户机本地 NTFS/exFAT 目录。不能只复制 Setup，也不能从压缩包内直接运行。
2. 管理员运行 Environment.exe。启用 Hyper-V 后按提示重启；重启后再继续 Setup。
3. 管理员运行同目录的 OntoTwin-...-Setup.exe。MSI 仅供企业软件分发系统使用，不能替代 Environment 和 payload 阶段。
4. 安装完成后双击桌面“灵云智”。
5. 首次启动会注册 VM、创建/挂载数据盘、导入离线镜像、初始化数据库和模型，可能需要数分钟。不要连续点击“启动系统”、不要在 600 秒前强杀窗口。
6. 必须看到“后台服务已就绪”“ZHHZ/ZHHZ_NEW 运行中”“模型加载完成”后才进入漫游。

安装目录默认：

~~~
C:\Program Files\OntoTwin\ZHHZ
~~~

数据根由注册表 HKLM\SOFTWARE\OntoTwin\ZHHZ\DataRoot 指定。典型位置为 D:\OntoTwin-ZHHZ\Data，没有合适的固定 NTFS 数据盘时才回退到 C:\ProgramData\OntoTwin-ZHHZ。升级、卸载和重装必须解析同一 DataRoot；普通卸载默认保留客户数据。

## 5. 数据准备、数据库种子与 active 路由

### 5.1 数据输入清单

每次导出必须是显式目录，而不是脚本自己“猜最近一次”：

~~~powershell
$DataDirectory = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\02_export\ReleaseData'
$ProjectId = 'ds_1787305683288'
$ProjectName = 'ZHHZ_NEW'
$UeProjectId = 'ueproj_ZHHZ_NEW'
~~~

数据目录至少包含：

- data-manifest.json
- PostgreSQL 自包含 dump（通常为 Database/postgres/zhhz.dump）
- PostgreSQL restore hook：Database/postgres/01-restore.sh
- Neo4j seed/导入所需文件或由 ontology registry 生成的 seed
- 项目媒体/模型资产及其清单
- 类型、实例、Parts/渲染引用计数
- 导出时间、来源 commit、项目 ID/name 和每个文件 SHA-256

### 5.2 PostgreSQL restore hook 是一等交付物

Compose 挂载的路径必须和归档路径完全一致：

~~~
Database/postgres/01-restore.sh
~~~

该文件必须由当前 deployment source 注入发布目录，而不是依赖旧 BaseReleaseDirectory 恰好带过来。构建门禁必须同时验证：

1. 文件存在、非空、UTF-8 无 BOM、LF-only、以 #!/usr/bin/env bash 开头并以 LF 结束。
2. release-manifest.json 中恰有一个对应条目。
3. 嵌套 release.tar.gz 中恰有一个 Database/postgres/01-restore.sh。
4. restore hook 的内容/hash 与当前 checkout 的 database\postgres\01-restore.sh 相同。
5. 在全新 PostgreSQL volume 中做一次实际恢复或至少完成隔离恢复演练，确认目标 dataset 可读。

RC15.1 的关键事故就是发布包遗漏此 hook。旧机已有数据库 volume 时可能被旧状态掩盖；一旦 reset_backend_baseline_on_upgrade=true 创建了全新的 PG volume，数据库只剩 demo，后续激活 gate 必然失败。因此“旧机能打开”不等于“干净机可安装”。

### 5.3 数据一致性与激活

构建前和启动后都要核对：

- project_id、project_name 与 UE 运行时身份一致。
- 目标数据集恰好一个，名称精确匹配。
- Types、Instances、Parts/渲染引用分别与 manifest 相符。
- 所有 GLB/媒体文件存在且 hash 相符。
- Neo4j seed 与 PostgreSQL registry 属于同一导出时刻。

启动时必须按正式 API 顺序执行：

1. backend health 通过。
2. GET /api/v2/ontology/datasets，目标 ID/name 必须恰好一个。
3. 若目标缺失，先导入正确 seed，记录导入错误；不能静默选择旧 ZHHZ。
4. POST /api/v2/ontology/datasets/activate，body：

~~~json
{"dataset_id":"ds_1787305683288"}
~~~

5. 再次 GET，确认唯一 active 就是目标。
6. POST /api/v2/ue/bind_active_project，然后 GET /api/v2/ue/binding_status。
7. 用 X-OntoTwin-UE-Project-Id 和 X-OntoTwin-UE-Project-Name 读回 UE 路由。

app_singleton.active_project_id 是持久化事实，但不能只用 SQL 改它；backend 有缓存，必须调用正式 API 并读回验证。

## 6. UE Win64 Shipping 运行时

### 6.1 输入冻结

当前目标示例：

~~~powershell
$Uproject = 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject'
$EngineRoot = 'D:\UE_5.6'
$TargetName = 'ZHHZ_NEW'
$ShippingOut = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\01_shipping'
~~~

工程名、TargetName、runtime manifest 的 project_name/target_name 必须一致。不要使用临时复制工程、test0316、tmp_ue 或上一次 RC 的旧 EXE。

### 6.2 Cook/Stage/Archive

地图、蓝图、插件、Config、DirectoriesToAlwaysCook 或任何动态几何发生变化时，必须重新 Cook、Stage、Archive。可以使用仓库脚本：

~~~powershell
$deploy = 'D:\tmp\digital_twin_aircraft\deploy\windows-all-in-one'
& "$deploy\Build-ShippingRuntime.ps1" -ProjectPath 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject' -EngineRoot 'D:\UE_5.6' -ArchiveDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\01_shipping' -TargetName 'ZHHZ_NEW'
if ($LASTEXITCODE -ne 0) { throw 'Shipping build failed' }
~~~

运行时脚本必须验证：

- UFS 和 NonUFS manifest 均存在。
- .uproject、OntoTwinSync、glTFRuntime 已被打入 Shipping。
- 动态几何源目录存在且对应 Cook 规则存在；缺失数量为 0。
- 最终 EXE、PAK、UCAS、UTOC、地图和所有 manifest 都记录 hash。
- 不含 Pixel Streaming、test0316、tmp_ue、开发调试目录。
- Cook 前后源工程 hash 没有改变；若改变，整轮作废并重跑。

### 6.3 运行时验收

在合并进发布包前，先单独运行 Shipping：

1. 启动正确主地图。
2. 检查 OntoTwinSync 能连到指定 backend。
3. 检查模型、坐标、人物和相机。
4. 关闭 UE 后再次冷启动，排除编辑器缓存掩盖问题。

## 7. 一体化构建流水线

以下顺序不可颠倒。每个阶段产出都要写入本轮 PackagingRun，下一阶段只接受上一阶段的清单和 hash。

### 7.1 先做变更分层，再决定构建范围

每次发布先填写变更矩阵。未发生变化的层必须复用上一已知成功产物及其 hash；不能因为某一层改了 UI/数据，就顺手重建整个后台控制面。

| 变更类型 | 必须重建 | 默认不得重建 |
|---|---|---|
| UE 交互/UI/蓝图/地图 | UE Shipping、release、AppPayload、Setup | appliance、Compose、bootstrap、数据库镜像 |
| backend 代码 | backend 镜像、release、AppPayload、Setup | appliance、Neo4j/PostgreSQL 镜像 |
| 项目数据 | data export/seed、release、AppPayload、Setup | UE Shipping、appliance（除非同时有变化） |
| guest/bootstrap/Docker | appliance/seed、AppPayload、Setup | UE/业务数据（除非同时有变化） |
| 仅安装器/版本缓存 | Setup/MSI 及其 manifest | backend 镜像、appliance、UE/data |

RC18.1 的成功关键是先退回 RC16 已验证控制面，再只装入 RC17 的 UE Shipping/UI、RC17 原始 backend OCI 归档和当前 ZHHZ_NEW 数据，最后用全新的 RC18.1 release/installer 版本出包。这个“最小差异”原则是后续版本的默认路线。

开始构建前必须把“复用项”和“重建项”分别写入 00_context/component-diff.md，并给每个复用项记录来源版本、绝对路径、大小和 SHA-256。复用不是口头说“和以前一样”，而是 hash 相同。

### 阶段 0：建立上下文

记录版本、四层身份、源路径、Git commit、工具版本、输出盘空间和构建人。确认输出目录为空。若发现旧 RC 文件混入，立即停止。

仓库中的 README 和部分脚本参数仍带有 ZHHZ 的历史默认值（例如 Build-ShippingRuntime 的 TargetName 默认值）。当目标是 ZHHZ_NEW 时，必须显式传入 ProjectPath、TargetName、ProjectId、ProjectName、DataDirectory 和 ReleaseVersion，并在运行时清单中复核；不能因为脚本“默认能跑”就省略参数。

### 阶段 1：构建并验收 Shipping

执行第 6 节；生成 ontotwin-runtime-manifest.json、UFS/NonUFS manifest、UAT 日志和输入/输出 hash。

### 阶段 2：合并发布数据和运行时

Build-RuntimeOnlyRelease.ps1 会以当前运行时身份为准合并 base release、数据导出、模型和 deployment source。示例：

~~~powershell
$deploy = 'D:\tmp\digital_twin_aircraft\deploy\windows-all-in-one'
$baseRelease = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC15.1\03_release'
$runtime = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\01_shipping'
$data = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\02_export\ReleaseData'
$releaseOut = 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\03_release'
$version = '3.7.1-r1-rc16'
& "$deploy\Build-RuntimeOnlyRelease.ps1" -BaseReleaseDirectory $baseRelease -RuntimeDirectory $runtime -SourceProjectPath 'D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject' -OutputDirectory $releaseOut -ReleaseVersion $version -DataDirectory $data -ProjectId 'ds_1787305683288' -ProjectName 'ZHHZ_NEW' -ResetBackendBaselineOnUpgrade
if ($LASTEXITCODE -ne 0) { throw 'Release merge failed' }
~~~

ResetBackendBaselineOnUpgrade 只在发布包明确要把客户机旧后台切换到新种子时使用；客户数据必须保留时，应先完成数据迁移和备份审批，不要把 reset 当作万能修复。

阶段 2 的停止条件：

- source project hash 与 runtime manifest 不同。
- data manifest 的 ID/name 与参数不同。
- restore hook 缺失或不是当前 deployment source 版本。
- 旧 ZHHZ 数据、旧 active ID 或临时工程混入。
- 输出目录非空或含上一轮 manifest。

RC18.1 类型的最小差异发布还必须满足：

- BaseReleaseDirectory 指向已验证且 manifest 完整的上一业务版本，不能指向开发目录或“最新”符号目录。
- BackendImageArchive/BackendImageTag 分别指向原始 RC17 归档及其真实 rc17 标签；禁止强行改成 rc18.1。
- deployment source 先复制到本轮 deploy_snapshot，随后冻结；最终包内的 Compose/bootstrap/control 必须与选定控制面基线逐文件比 hash。
- ReleaseVersion 使用未曾安装过的新版本号，避免 Windows Installer maintenance cache 继续复用同名/同版本旧 payload。
- 合并后反读 release-manifest.json，检查 base_release_version、runtime_source_sha256、component_versions.images 和 installer 版本，而不是只看命令退出码。

### 阶段 3：构建或重建 appliance

只有系统盘、guest bootstrap、Docker Engine/Compose 或云初始化内容变化时，才从头运行：

~~~powershell
& "$deploy\hyperv\Build-Appliance.ps1" -OutputDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\04_appliance' -ApplianceVersion '3.7.1-r1-rc16-appliance1' -WslDistribution 'Ubuntu-22.04' -DockerVersion '29.1.5' -ComposeVersion '5.1.4'
if ($LASTEXITCODE -ne 0) { throw 'Appliance build failed' }
~~~

若只需基于已验证的系统盘更新 seed，使用：

~~~powershell
& "$deploy\hyperv\Rebuild-ApplianceSeed.ps1" -BaseApplianceDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC15.1\04_appliance' -OutputDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\04_appliance' -ApplianceVersion '3.7.1-r1-rc16-appliance1' -WslDistribution 'Ubuntu-22.04'
if ($LASTEXITCODE -ne 0) { throw 'Appliance seed rebuild failed' }
~~~

appliance 必须记录系统 VHDX、seed ISO、Docker Engine、Compose 的版本和 SHA-256。当前容量契约为系统盘 20 GiB、根分区至少 16 GiB、根可用至少 8 GiB；guest bootstrap 必须显式扩容并检查容量。

若本轮只改 UE、UI、backend 或数据，阶段 3 的正确动作是“复制并验证已知成功 appliance”，不是重建。RC18.1 复用了 RC16 appliance；其 VHDX SHA-256 为 `b277b5a4fe3858ed1975ec93f2ead6971173db7dbea4c887e2e3998cb7a1a639`。以后复用时以目标 manifest 中的实际 hash 为准。

### 阶段 4：构建 AppPayload

~~~powershell
& "$deploy\hyperv\Build-InstallerAppPayload.ps1" -ReleaseDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\03_release' -ApplianceDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\04_appliance' -OutputDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\05_app-payload' -WslDistribution 'Ubuntu-22.04'
if ($LASTEXITCODE -ne 0) { throw 'AppPayload build failed' }
~~~

该阶段必须校验：

- release、appliance、runtime、data、component_versions 版本完全一致。
- 三个 Docker tar 的传统 manifest.json RepoTags、OCI index.json annotations、Compose 引用与 component_versions 四方一致。
- payload 内的 release.tar.gz 恰有一个 restore hook。
- docker-compose.release.yml 与当前 deployment source 一致。
- guest bootstrap 是 LF-only、无 BOM、解释器行正确。
- network 子网与宿主传输子网不重叠。
- 不使用 docker volume rm 或 docker volume prune。

### 阶段 5：构建 Setup/MSI

~~~powershell
& "$deploy\installer\Build-Installer.ps1" -AppPayloadDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\05_app-payload' -OutputDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\06_installer'
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
~~~

安装器必须从 AppPayload 继承版本，不能另外输入 ReleaseLabel。MSI launcher 发布目录必须完整 harvest；不得只挑 DLL 或手动替换 EXE。最终要验证文件数量、相对路径、大小和 hash 均一致。

### 阶段 6：生成最终清单和交付目录

最终目录至少包含：

~~~
OntoTwin-ZHHZ-3.7.1-R1-RC18.1-Setup.exe
Environment.exe
PayloadInstaller.exe
OntoTwin-ZHHZ.payload.zip
OntoTwin-ZHHZ.payload.zip.sha256
MSI/
Appliance/
release-manifest.json
appliance-manifest.json
SHA256SUMS
部署指南、操作指南、故障取证说明
~~~

最终 SHA256SUMS 必须覆盖 Setup、payload、MSI、manifest 和所有外置交付文件。交付目录名、文件名、清单中的版本和客户文档中的版本必须一致，禁止把新包覆盖到 RC10/RC11/RC15 旧目录。

## 8. Hyper-V guest/bootstrap 契约

### 8.1 启动阶段

guest 启动应可观察地经过：

1. VM Running。
2. GuestControl 可达（动态端口，不能硬编码旧端口）。
3. payload SHA256SUMS 下载并校验。
4. Docker Engine/Compose 就绪。
5. 三个镜像存在且 hash/RepoTags 正确。
6. Compose 启动 backend、PostgreSQL、Neo4j。
7. backend health 通过。
8. datasets 检查、激活、UE bind/readback 通过。
9. 写入完成 marker，guest status 返回 ready。

VMState=Running 但 GuestIPs=为空，或 GuestControl=http://172.28.251.2:49274 暂时不可达，只说明第 1/2 层尚未稳定；不能直接断言数据库或 UE 失败。HostControl 的 600 秒超时必须带上最后 status、compose error 和 bootstrap tail。

### 8.2 幂等 marker 和事务

以下 marker 必须是原子写入，并与 payload fingerprint/版本绑定：

- bootstrap.in-progress
- bootstrap-payload.sha256
- backend-baseline-captured
- backend-baseline-capture.in-progress
- image/payload 安装完成 marker

基线移动必须先写 transaction intent，再移动 docker 和 release-data，最后确认两者都是普通目录后写成功 marker。重试只能恢复未完成 transaction，不能再次复制一个完整基线。基线快照至少保留最早的完整快照、用户备份和不认识的未来/外部目录。

### 8.3 备份与 reset

- 旧 docker、release-data 的一次性 baseline backup 放在 DataRoot\baseline-backups。
- 客户普通备份放在 DataRoot\backups，不能被 reset 清理。
- release.env、密码、Token、客户集成配置放在持久区域，升级时合并新默认值但保留客户秘密。
- 先检查 DataRoot 剩余空间；空间不足时停止，不得继续重试。
- Compose teardown 只允许 down --remove-orphans 等不删除命名 volume 的形式；禁止 --volumes、docker volume rm、docker volume prune。

RC15.1 的重试链必须写入回归测试：

~~~
systemd bootstrap 失败
  → Restart=on-failure 无限重试
  → previous_bootstrap_incomplete 再次触发备份
  → baseline-backups 重复增长
  → 40 GiB 数据盘耗尽
  → docker load / mkdir -p 同时失败
~~~

RC16 的修复要求：

- 仅当 failed marker 与 RC15.1 payload SHA 精确匹配时，才识别旧坏包。
- 只删除可证明是该坏包生成的、具有精确 suffix 的重复完整快照。
- 保留最早完整基线、部分快照、用户备份、符号链接/挂载点和外部目录。
- 永不因自动重试删除 Docker volume 或客户数据。
- 正常启动若 payload fingerprint 未变且系统文件完整，跳过重复解包和镜像重载。

### 8.4 激活状态机

健康检查不能只检查 HTTP 200。必须把激活和 UE 路由纳入 ready 条件，并把每次尝试的阶段、耗时、attempt ID 写入日志。指数退避应有上限；达到超时后停止服务重试并导出诊断，不让 UI 永远显示“启动中”。

## 9. 升级、重启和回滚矩阵

| 场景 | 默认动作 | 数据处理 | 通过条件 |
|---|---|---|---|
| 全新安装 | 创建 VM/数据根，导入 payload，恢复种子 | 无旧基线；写 fresh-install marker | backend、active、UE bind 全通过 |
| RC12/RC15 → 新版 | 先备份一次，再按清单切换 | 保留 DataRoot、secret 和用户备份 | 只生成一次 baseline，空间不异常下降 |
| RC15.1 坏包 → RC16 | 识别精确坏包 fingerprint，安全整理重复快照 | 保留最早完整基线，不删 volume | 新 hook 恢复出目标数据集 |
| 普通重启 | 复用已安装 payload | 不重备份、不重载镜像 | marker/hash 命中，服务 ready |
| bootstrap 中断 | 恢复 transaction intent | 继续原子移动或回滚 | 不生成第二个同类基线 |
| 客户数据必须保留 | 禁用 reset，先走迁移 SOP | 数据库/媒体/Neo4j 均有恢复点 | 人工批准后才发布 |
| 回滚旧版本 | 停服务，恢复上一已知可启动快照 | 不删除当前失败证据 | 旧版本 active/UE 路由读回正确 |
| 卸载/重装 | 移除程序和 VM 注册 | 默认保留 DataRoot 和 registry | 可用版本重新挂载并读回数据 |

任何“全新重置”路径都必须二次确认，显示数据目录和预计空间；绝不能嵌入 systemd 自动重试。

## 10. 自动化门禁清单

### 10.1 源工程门禁

- [ ] .uproject 路径存在且是本轮指定工程。
- [ ] 文件名、runtime project/target、UE target name 完全一致。
- [ ] 源工程、主地图、插件和 Config hash 已记录。
- [ ] Cook 前后源 hash 不变。

### 10.2 Shipping 门禁

- [ ] UFS/NonUFS manifest 存在。
- [ ] OntoTwinSync、glTFRuntime 和项目 descriptor 存在。
- [ ] Pixel Streaming、test0316、tmp_ue 不存在。
- [ ] EXE/PAK/UCAS/UTOC 和地图可读，动态几何缺失为 0。
- [ ] UAT 日志无错误；警告已分类。

### 10.3 数据门禁

- [ ] data-manifest 的 ID/name 等于目标参数。
- [ ] dump 非空，可列出并能在隔离 PG volume 恢复。
- [ ] restore hook 存在、LF-only、hash 等于当前 deployment source。
- [ ] Types、Instances、Parts/引用、GLB 数量和 hash 有证据。
- [ ] Neo4j seed 与同一导出时刻匹配。

### 10.4 appliance/guest 门禁

- [ ] VHDX/seed/Docker/Compose hash 与 appliance manifest 一致。
- [ ] 系统盘 20/16/8 GiB 容量契约通过。
- [ ] cloud-init instance-id 从 appliance version 派生。
- [ ] guest bootstrap bash -n 通过，无 CR、无 BOM。
- [ ] root capacity、payload hash、network 不重叠检查通过。
- [ ] baseline transaction、marker、重试上限和空间保护测试通过。
- [ ] bootstrap 中不含 docker volume rm/prune，teardown 不含 --volumes。

### 10.5 payload/installer 门禁

- [ ] release/app-payload/appliance 版本和四层身份一致。
- [ ] nested release.tar.gz 恰含一个 Database/postgres/01-restore.sh。
- [ ] 三个镜像 tar 的 manifest.json RepoTags、OCI index.json annotations、Compose 和 component_versions 一致。
- [ ] MSI launcher 完整发布目录路径/大小/hash 相符。
- [ ] Setup/MSI/payload 无未解析版本 token。
- [ ] 最终 SHA256SUMS 完整且可重算。

### 10.6 Docker/OCI 镜像归档门禁

`docker save` 归档可能同时包含传统 `manifest.json` 和 OCI `index.json`。只替换 `manifest.json` 中的 RepoTags 不足以完成 retag；Docker/containerd 仍可能根据 `index.json` 的 `io.containerd.image.name` 或 `org.opencontainers.image.ref.name` 导入旧标签，从而出现：

~~~
Bootstrap failed: required image was not provided by the payload
~~~

每个镜像归档必须在不解包重打的前提下检查：

1. 外层文件 SHA-256 与 manifest 一致。
2. tar 可以完整列出，关键 blob/manifest 均存在。
3. 传统 manifest.json 的 RepoTags 等于 Compose 所引用标签。
4. OCI index.json 的相关 annotations 等于同一标签。
5. 在隔离 Docker data-root 中执行一次 `docker load`，加载后 `docker image inspect <tag>` 成功。
6. inspect 的 image ID/digest 与发布记录一致，然后清理隔离环境。

禁止用字符串替换、十六进制替换或“解 tar → 改 JSON → 再 tar”修改历史镜像归档。重新打 tar 可能改变 entry 顺序、header、PAX 元数据或链接语义，RC18 曾因此出现 `docker load --input ... exit=1`。需要新标签时，应从已加载镜像通过标准 `docker tag` + `docker save` 生成新归档并完整复验；若业务不要求新标签，优先直接使用原始已验证归档。

任何一项失败都必须终止交付。不能靠改文件名、替换单个 EXE、手工 SQL、重复点击启动或删掉日志目录“通过”。

## 11. 干净客户机验收

### 11.1 安装前记录

记录以下内容并附到验收报告：

- Windows 版本、版本类型、补丁、用户名和是否管理员。
- CPU virtualization/Hyper-V 功能状态。
- RAM、GPU、数据盘文件系统和可用空间。
- 5000 端口占用、杀毒/防火墙策略。
- 安装介质目录、Setup SHA、payload SHA、manifest 版本。

### 11.2 首次冷启动

1. Environment → 必要重启 → Setup。
2. 启动“灵云智”，只点击一次。
3. 记录每一阶段开始/结束时间。
4. 确认后台服务 ready、VM running、backend health、active dataset 和 UE binding。
5. 打开本地控制台，核对 ZHHZ_NEW、ds_1787305683288、ueproj_ZHHZ_NEW 和计数。
6. 等模型加载完成后进行人物/相机/漫游验收。

### 11.3 停止、重启和升级

- 点击停止系统，确认容器和 VM 按预期停止。
- 再次冷启动，确认不重复 baseline、不重载不变镜像、数据不丢失。
- 从上一已知版本覆盖升级，确认 DataRoot、secret、用户备份和 active 路由保留。
- 在断电/GuestControl 短暂断线后恢复一次，确认不会重复产生备份。
- 执行一次备份，并在隔离目录验证可读。

### 11.4 通过标准

所有身份、计数、状态、日志、hash 和时间均有记录；任一未通过项必须标为阻断，不得用“本机能打开”替代干净机验收。

### 11.5 验收环境必须分层

以下四类环境解决的是不同问题，结果不得互相冒充：

| 环境 | 证明内容 | 是否是交付门禁 |
|---|---|---|
| 隔离 Docker 全栈 | 镜像可加载、Compose、种子、API、备份/恢复可工作 | 是 |
| 干净 Windows + Hyper-V | Environment、Setup、VM、首次启动、桌面入口可工作 | 是 |
| 已知成功 RC16 → 新版升级机 | baseline、secret、数据和升级状态机可工作 | 是（有升级承诺时） |
| 长期开发/反复安装的污染机 | 旧 DataRoot、VHDX、marker、release.env 的恢复兼容性 | 否；属于支持/恢复专项 |

开发机 `C:\ProgramData\OntoTwin-ZHHZ` 曾保留多轮旧 VHDX、release.env 和 marker。RC17 在该机失败并不能单独证明同一介质在干净客户机必然失败；反过来，干净机成功也不能证明污染机无需恢复。必须先给机器贴上“干净安装 / 已知版本升级 / 污染恢复”标签，再解释日志。

## 12. 日志、状态和故障取证

### 12.1 Windows 侧

首要日志：

~~~
D:\OntoTwin-ZHHZ\Data\Logs\host-service.log
~~~

从 HostControl 输出中复制实际的 GuestControl URL（地址和端口可能变化），不要硬编码旧端口。只读检查示例：

~~~powershell
$dataRoot = 'D:\OntoTwin-ZHHZ\Data'
Get-Content -LiteralPath "$dataRoot\Logs\host-service.log" -Tail 200
Get-Service -Name 'OntoTwin*' -ErrorAction SilentlyContinue
Get-VM -Name 'OntoTwin-ZHHZ-Backend' -ErrorAction SilentlyContinue | Select-Object Name, State, Status
Get-Volume | Select-Object DriveLetter, FileSystem, SizeRemaining, Size
~~~

如果 HostControl 报：

~~~
VMInstalled=True
VMState=Running
GuestIPs=
GuestControl=http://172.28.251.2:49274
BackendReady=False
~~~

这表示 VM 可能已开机，但 guest control 或网络还没有稳定；继续看 host-service.log 和 bootstrap tail，不要立即卸载。

### 12.2 Guest/VM 侧

若能打开 Hyper-V VM console，Ubuntu 出现 ontotwin-zhhz login: 是系统已到登录提示，不是自动登录失败。VMConnect 弹出“没有所需权限”时，先以管理员运行控制中心/VMConnect，并检查 Hyper-V 管理员组和 Hyper-V 服务；这与数据库内容错误是不同问题。

在有控制台权限时收集：

~~~bash
journalctl -u ontotwin-bootstrap -n 200 --no-pager
systemctl status ontotwin-bootstrap ontotwin-control ontotwin-stack --no-pager
tail -n 200 /var/lib/ontotwin/bootstrap-last.log
df -h
docker compose --env-file /var/lib/ontotwin/release/Deploy/.env -f /var/lib/ontotwin/release/Deploy/docker-compose.release.yml ps --all
docker compose --env-file /var/lib/ontotwin/release/Deploy/.env -f /var/lib/ontotwin/release/Deploy/docker-compose.release.yml logs --tail=200
~~~

路径以本包实际 RELEASE_ROOT 为准；如果只有控制中心可用，优先使用其状态快照和“导出诊断”功能，不把 SSH 当作客户必备条件。

### 12.3 RC15.1 日志反例

以下序列是“备份副作用被无限重试”而不是用户点击错误：

~~~
[14:33:00] Bootstrap failed while starting Docker Compose
[14:33:21] Bootstrap failed: exit=1 line=458 command=docker load --input "$WORK_ROOT/$image_archive"
[14:33:42] Bootstrap failed: exit=1 line=415 command=mkdir -p "$baseline_backup_root"
[14:34:03] Bootstrap failed: exit=1 line=415 command=mkdir -p "$baseline_backup_root"
[14:34:24] Bootstrap failed: exit=1 line=415 command=mkdir -p "$baseline_backup_root"
~~~

推断链：

1. 01-restore.sh 漏出发布归档。
2. reset 创建空 PG volume，目标数据集不存在。
3. bootstrap 在健康/激活路径失败。
4. systemd Restart=on-failure 重试。
5. previous_bootstrap_incomplete 再次触发 baseline capture。
6. baseline-backups 重复增长，数据盘填满。
7. 后续 docker load 和 mkdir 一起失败。

因此故障处理顺序是“停止重试、保留证据、确认空间、恢复正确 payload”，不是反复点击启动。

### 12.4 Neo4j unhealthy 的分层判读

控制中心中的：

~~~json
{"Status":"unhealthy","FailingStreak":0,"Log":[]}
~~~

信息不足，不能直接归因于 healthcheck。必须先看 Neo4j 容器主进程状态，再看健康检查明细：

~~~bash
docker inspect ontotwin-zhhz-neo4j-1 --format '{{json .State}}'
docker logs --tail=200 ontotwin-zhhz-neo4j-1
docker inspect ontotwin-zhhz-neo4j-1 --format '{{json .Config.Env}}'
docker compose --env-file /var/lib/ontotwin/release/Deploy/.env -f /var/lib/ontotwin/release/Deploy/docker-compose.release.yml config
~~~

| 主状态/健康状态 | 含义 | 首查项 | 禁止动作 |
|---|---|---|---|
| `restarting`，`ExitCode=64` | Neo4j 主进程因参数、配置或持久状态立即退出 | `docker logs`、最终 Compose config、release.env、旧 volume/data 兼容性 | 延长 healthcheck、反复重启 |
| `running`，FailingStreak 持续增长且有 health log | 主进程存活，真正的探针失败 | 探针命令、认证、端口、启动时长、资源 | 把它等同于 exit=64 |
| `unhealthy`，FailingStreak=0，Log=[] | 摘要缺失或容器尚未形成健康记录 | `.State.Status/.ExitCode/.Error` 和容器日志 | 仅凭该 JSON 修改 Compose |
| `exited`/OOMKilled | 进程崩溃或资源问题 | ExitCode、OOMKilled、内存/磁盘、内核日志 | 修改数据库种子掩盖资源问题 |

RC18 在污染开发机上的完整 host-service.log 记录为 `status=restarting exit=64 error=`，因此该轮的主因类别是“Neo4j 启动/配置/持久状态失败”，不是“健康检查等待不够”。RC17 的 Compose/bootstrap/control/Neo4j/PostgreSQL 与 RC16 hash 相同却在该开发机失败，也证明开发机历史状态是独立变量。

如果日志连续重复 `Discarding the incomplete first-install backend baseline before retry`、`Loading ...-image.tar` 或 `Installing OntoTwin release files`，这是 systemd/Host Service 失败重启循环，不是正常进度条。立即停止继续点击，保存 host-service.log、bootstrap tail、容器 inspect/log、marker 和磁盘状态；在副作用幂等性未确认前不得让它无限跑。

## 13. 备份、回滚和数据保护

### 13.1 发布前

- PostgreSQL 自包含 dump、Neo4j seed、媒体/GLB、DataRoot 元数据和版本清单分别备份。
- 备份文件记录时间、来源版本、项目四元组、大小和 SHA-256。
- 将备份恢复到隔离位置做最小可读性验证。

### 13.2 升级前

- 确认旧 VM 和 Compose 已停止或可安全 teardown。
- 生成一次可定位的 baseline snapshot，包含 docker、release-data 和必要的配置，但不复制可重新生成的无限缓存。
- 保留 release.env、客户密钥和 DataRoot registry。
- 记录升级前 active dataset/UE binding。

### 13.3 升级失败

1. 停止 Host Service/bootstrap 重试。
2. 复制 host-service.log、bootstrap tail、manifest、marker、磁盘空间和 VM console 最后一屏到 08_diagnostics。
3. 不删除 C:\ProgramData\OntoTwin-ZHHZ、注册表 DataRoot、Data.vhdx、数据库 volume 或用户备份。
4. 按 transaction intent 判断是恢复移动、回滚完整 baseline，还是修复 payload 后重试。
5. 恢复后重新执行 datasets/activate/binding readback。

只有在备份完整、路径已解析且用户明确确认后，才允许“全新重置”。任何自动化修复都不得以 Remove-Item 或 Docker volume prune 代替回滚。

## 14. 本轮已验证问题与预防表

| 问题/表象 | 真正原因 | 预防与修复 |
|---|---|---|
| RC15 能打开，RC15.1 失败 | 旧数据库 volume 掩盖了漏包 restore hook；reset 后暴露 | 对全新 PG volume 强制恢复演练；归档恰含一个 hook |
| 前端场景是 ZHHZ_NEW，database 选 ZHHZ | 四层身份未统一，激活状态未走正式 API | manifest 驱动 datasets→activate→UE bind→readback |
| 启动窗口反复 Starting container stack | systemd 无限重试，副作用在重试中重复执行 | marker/transaction/idempotence；失败停止并导出诊断 |
| docker load 失败 | 归档缺失/损坏或数据盘被重复备份占满 | 预检存在/大小/hash/空间；镜像导入只做一次 |
| required image was not provided，实际归档看似有 tag | 只改了传统 manifest.json，OCI index.json 仍指向旧标签 | 同时检查 RepoTags 和 OCI annotations；优先使用原始归档 |
| 手工改 tag 后 docker load exit=1 | 解包/重打 tar 改变了 OCI 布局或元数据 | 禁止手工 re-tar；用 docker tag + docker save 正式生成并隔离加载验证 |
| mkdir -p baseline_backup_root 失败 | 40 GiB 数据盘已被重复快照耗尽，或目标状态不安全 | 先检查容量；保留最早完整快照；禁止盲目清理 |
| Neo4j unhealthy，FailingStreak=0、Log=[] | 摘要不完整；本轮真实状态曾是 restarting/exit=64 | 先 inspect 主状态和 ExitCode，再查 logs/config/旧 volume；不先改 healthcheck |
| RC17 与 RC16 控制面 hash 相同但开发机失败 | 开发机残留旧 DataRoot、VHDX、release.env 和 marker，环境不是干净验收基线 | 区分干净安装、已知版本升级、污染恢复；污染机失败单独取证 |
| 为修 Neo4j 连续改 Compose/bootstrap/appliance 后问题越来越多 | 未证明这些层发生变化，扩大了故障面 | 回到最后成功控制面，按组件最小差异替换 |
| Setup 版本/文件名变化但安装仍复用旧行为 | Windows Installer maintenance cache 命中旧版本/产品状态 | 新发布使用真实递增版本并输出到独立目录；核对已安装 Bundle/MSI 版本 |
| VM Running 但 GuestIPs 为空 | guest 网络/控制端口瞬时未就绪 | 区分 VM、GuestControl、backend 三层，采用退避和最终复核 |
| VMConnect 权限弹窗 | 当前用户无 Hyper-V VMConnect 授权或未管理员运行 | 管理员打开、检查 Hyper-V Administrators；不误判为数据库坏 |
| 双击桌面无反应 | Host Service/快捷方式/权限/启动阶段日志未被观察 | 先查服务、host-service.log、控制中心状态；不假设是 UE 崩溃 |
| 脚本成功但包里仍是 ZHHZ | 采用了历史 README/参数默认值，或复用了旧 runtime/base release | 目标为 ZHHZ_NEW 时所有身份参数显式传入；构建后反查四层身份 |
| RC10/RC11 旧目录被新文件覆盖 | 版本目录和输出目录没有隔离 | 每版独立目录、清单版本一致、最终 SHA |
| 单独拿 Setup 到另一台机器 | 外置 payload、Environment、MSI/manifest 缺失 | 整目录复制到 NTFS/exFAT；Setup 不能脱离 payload |
| 直接 SQL 改 active 后 UI 仍旧 | backend 缓存未刷新 | 正式 API 激活并 GET 读回；SQL 仅作审计 |
| 客户反复点启动系统 | 首次初始化耗时，UI 未明确阶段 | UI 显示阶段/attempt/耗时；文档明确一次点击、等待和取证 |

## 15. 交付前最终清单

### 构建输入

- [ ] 当前 .uproject 绝对路径、工程名、TargetName 已确认。
- [ ] 主地图、插件、配置、数据导出和模型输入均有 hash。
- [ ] release_version、appliance_version、ProjectId/Name、UE ID 已冻结。
- [ ] component-diff.md 已明确本轮重建层、复用层及每个复用层的来源/hash。
- [ ] 本轮 PackagingRun 独立且输出目录开始为空。

### 构建产物

- [ ] Shipping runtime 重新 Cook/Stage/Archive，UAT 日志归档。
- [ ] release-manifest.json、data-manifest.json、appliance-manifest.json 完整。
- [ ] Database/postgres/01-restore.sh 存在且嵌套归档恰一份。
- [ ] 三个镜像 tar 的 RepoTags/OCI annotations/隔离 docker load 均通过。
- [ ] VHDX、seed、Compose、bootstrap、control 与声明的控制面基线 hash 一致。
- [ ] AppPayload、MSI、Setup 版本继承关系通过。
- [ ] 最终 SHA256SUMS 可在另一目录重算。

### 运行时安全

- [ ] baseline capture 有空间门禁、事务 intent、完成 marker 和单次语义。
- [ ] 正常重启不重复备份、不重复解包、不删除 volume。
- [ ] bootstrap 失败会停止/限次，不会无限制造快照。
- [ ] active dataset、UE binding 和 backend route 由 API 读回确认。

### 客户验收

- [ ] 隔离 Docker 全栈恢复、启动、备份/恢复和切换通过。
- [ ] 干净 Win Pro/Enterprise/Education 机器安装通过。
- [ ] Environment/重启/Setup/桌面启动顺序通过。
- [ ] 首次冷启动和第二次冷启动都通过。
- [ ] RC15/历史版本升级、失败恢复和回滚演练通过。
- [ ] 低磁盘、端口占用、GuestControl 瞬断、非管理员、VMConnect 权限场景有明确结果。
- [ ] 日志、截图、状态快照、版本和 hash 已交付支持人员。

未勾满不得交付。

## 16. 当前稳定基线与 RC18.1 成功记录

### 16.1 RC16 控制面基线

以下 hash 是 RC18.1 复用 RC16 控制面的审计依据。以后若声称“沿用 RC16”，必须逐项相等；有一项不同就应按新控制面重新验收。

| 组件 | SHA-256 / 版本 |
|---|---|
| docker-compose.release.yml | ac5e22459bc48582e28f69fb38fa84ac76a778955774796dda2e08de4281ea05 |
| bootstrap.sh | 205ddd908a7138ab72068892400ce04f55e3a4444ce8ced78372e1b1e92b9161 |
| control.py | 4f03b7164868ea3ab91f22b2bfee9334b2fc0892e3c469e35946aecab27686cc |
| appliance version | 3.7.1-r1-rc16-appliance1 |
| system VHDX | b277b5a4fe3858ed1975ec93f2ead6971173db7dbea4c887e2e3998cb7a1a639 |
| Neo4j image archive | d3032549bfbe15e432d94cabbb1e78d1fcaa7964253807849ce63ce214f69c5f |
| PostgreSQL image archive | a515bf337c96966561a2ba83ede0038993e3600b2e621f5d96ae5af3d1b7ffe5 |

### 16.2 RC18.1 交付证据

| 项目 | 值 |
|---|---|
| release | 3.7.1-r1-rc18.1 |
| base release | 3.7.1-r1-rc17 |
| appliance | 3.7.1-r1-rc16-appliance1 |
| backend | ontotwin-zhhz/backend:3.7.1-r1-rc17 |
| backend archive SHA-256 | 7b6ef4549a40903eba0bb4baa7eca68358777c3ec2e3f4f8f39e313246b07882 |
| dataset | ds_1787305683288 / ZHHZ_NEW |
| UE | ueproj_ZHHZ_NEW / ZHHZ_NEW |
| 源工程 | D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject |
| 源工程 SHA-256 | 68d47aef322736a1be501c341cbe59e8e4a7f9d1de2b141b1c7434838221e899 |
| Types / Instances | 6 / 507 |
| Neo4j Nodes / Relationships | 118 / 220 |
| Setup SHA-256 | d67b06df635e09d855af8b7c6a143f1ac110dc82fcb0fab89f363700a08915c3 |
| payload ZIP SHA-256 | 60c1ac4983de7ca8a90df203ed489c04f5e6cf0fce8e3e75a9b0e5c47bb06658 |
| PackagingRun | E:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC18.1_20260828-RC16BASE |
| 交付目录 | E:\ZHHZ\Releases\OntoTwin-ZHHZ_NEW-3.7.1-R1-RC18.1-Installer |
| MSI launcher 校验 | 463 个文件的路径、大小、SHA 全部匹配 |
| 隔离全栈验收 | Neo4j healthy、init 成功、PostgreSQL healthy、backend started；备份/恢复/数据集切换通过 |
| 构建结果 | 0 warnings / 0 errors |
| 实际验收 | 2026-08-31 用户确认可用 |

本表是 RC18.1 的审计快照，不是后续版本硬编码。每一版必须重新生成 manifest、重算 SHA 并记录自己的验收证据。

## 17. 支持人员最短取证包

客户无法启动时，先收集而不是卸载：

~~~
<版本目录>\release-manifest.json
<版本目录>\appliance-manifest.json
<版本目录>\SHA256SUMS
D:\OntoTwin-ZHHZ\Data\Logs\host-service.log
D:\OntoTwin-ZHHZ\Data\bootstrap.in-progress
D:\OntoTwin-ZHHZ\Data\bootstrap-payload.sha256
D:\OntoTwin-ZHHZ\Data\backend-baseline-captured
D:\OntoTwin-ZHHZ\Data\baseline-backups\
~~~

同时记录：

- HostControl 完整错误文本（包括 VMState、GuestIPs、GuestControl、LastError、ComposeError、BootstrapLogTail）。
- VM console 最后一屏（若可得）。
- Get-VM、服务状态、DataRoot、剩余空间和 5000 端口占用。
- 失败开始时间、点击次数、是否重启/断电、安装介质 SHA。

不要先删除日志、不要先清空 DataRoot、不要先导入另一份数据库。证据保全后再决定恢复路径。

## 18. 附录：发布记录模板

~~~text
发布版本：
ReleaseVersion：
ApplianceVersion：
组件变更矩阵（重建/复用）：
控制面基线及 Compose/bootstrap/control SHA：
构建时间/构建人：
Git commit：
源 .uproject：
主地图：
UE project_name/target_name：
UE project_id/name：
OntoTwin dataset project_id/name：
Types / Instances / Parts：
DataDirectory：
PostgreSQL dump SHA：
Restore hook SHA：
Runtime manifest SHA：
Appliance manifest SHA：
Payload SHA：
Setup SHA：
镜像传统 RepoTags / OCI annotations / load-inspect 结果：
构建门禁结果：
隔离 Docker 全栈结果：
干净机结果：
旧版升级结果：
污染开发机结果（仅恢复专项）：
第二次冷启动结果：
回滚结果：
已知风险/例外及批准人：
诊断日志目录：
~~~

## 19. RC18/RC18.1 本轮复盘：从扩大改动回到成功基线

### 19.1 本轮真正的变更边界

需求本质是更新 ZHHZ_NEW 的交互/UI，并携带当前正确数据。它没有要求更换 Ubuntu、Docker、Compose、guest bootstrap、Host control、Neo4j 或 PostgreSQL。因此后台控制面本应作为冻结依赖处理。

### 19.2 为什么一度陷入“越修越坏”

失败路径同时引入了多项无必要变量：

1. 为新 release 重新构建/修改 appliance、seed、Compose 或 bootstrap。
2. 强制把 RC17 backend 镜像改成 RC18 标签。
3. 只改传统 manifest.json，遗漏 OCI index.json，导致 Docker 仍导入旧 tag。
4. 解 tar/再 tar 后归档布局变化，导致 `docker load` 直接失败。
5. 看到 `neo4j unhealthy` 后继续改 healthcheck/环境变量，但没有先确认主进程已 `restarting exit=64`。
6. 把长期反复安装的开发机当成干净客户机，忽略旧 DataRoot/VHDX/release.env/marker 的影响。

这些动作让“业务层变更”和“控制面实验”纠缠在同一个安装包内，任何失败都无法快速定位到单一变量。

### 19.3 RC18.1 的成功做法

RC18.1 采用了可审计的最小差异组合：

1. 用 hash 锁定 RC16 的 Compose、bootstrap、control、appliance、Neo4j/PostgreSQL 镜像。
2. 使用 RC17 原始 backend OCI 归档及其真实 rc17 标签，不再 retag。
3. 使用 RC17 已完成的 ZHHZ_NEW UE Shipping/UI。
4. 使用当前 ZHHZ_NEW 数据：`ds_1787305683288 / ZHHZ_NEW`，并在 manifest 中固定 UE 绑定 `ueproj_ZHHZ_NEW / ZHHZ_NEW`。
5. 仅把 release/installer 版本提升为 RC18.1，避开旧 RC18 安装缓存，同时保持组件真实版本可追溯。
6. 在隔离环境完成镜像导入、Compose、PG/Neo4j/backend、备份/恢复、数据集切换和 MSI 文件级校验。
7. 最终整目录交付，由用户完成实际换机验收并确认可用。

### 19.4 后续版本标准步骤（最短可执行版）

1. 冻结需求，写明到底改了 UE、backend、数据、控制面还是安装器。
2. 选择最后一个真实成功版本；按文件 SHA 建立控制面基线，不按目录名猜。
3. 为本轮创建唯一 PackagingRun 和 deploy_snapshot，输出目录必须为空。
4. 仅重建变更层；未变层从成功基线复制并复核 SHA。
5. 镜像使用真实标签；检查 manifest.json、OCI index.json、Compose 和 component_versions。
6. 在隔离 Docker data-root 实际 `docker load` 三个归档并 inspect 标签/digest。
7. 合并 release 后反读四层身份、组件矩阵、计数和 restore hook。
8. 若 guest 源未变，复用成功 appliance；不得为了 release 号重建系统盘。
9. 构建 AppPayload/Setup，使用新的递增 release/MSI/Bundle 版本和独立交付目录。
10. 完成隔离全栈、干净 Windows、已知版本升级三套验收；污染机恢复另开记录。
11. 重算最终 SHA256SUMS，按相对路径/大小/SHA 比较 MSI launcher 全目录。
12. 交付整个 installer media 目录，并把 manifest、SHA、取证说明一并交付。

### 19.5 明确禁止事项

- 禁止在“只改 UI/UE/数据”的发布中顺带修改 Compose、bootstrap 或 appliance。
- 禁止通过字符串替换或解包重打 tar 来给 OCI 镜像改 tag。
- 禁止让 release 版本号强迫所有组件使用相同标签。
- 禁止把复制文件成功、脚本退出码为 0或开发机本地 Docker 能启动当成完整验收。
- 禁止把污染开发机失败直接外推为所有客户机都会失败，也禁止忽略污染机的恢复问题。
- 禁止自动删除 DataRoot、Data.vhdx、Docker volume 或 baseline；任何清理必须先备份、精确解析路径并获得明确批准。
- 禁止覆盖历史 release/PackagingRun；禁止只交付 Setup.exe。

### 19.6 出包决策口诀

先问“哪一层真的变了”，再问“最后成功层的 hash 是什么”。能复用的已验证层保持逐字节不变；必须变化的层独立构建、独立验证、在 manifest 中如实写版本。失败时先收全量状态和主进程 ExitCode，再修改最小的一处变量。

## 20. 一句话结论

一体化打包的可靠路径是：固定最后成功的控制面，只替换实际变化的业务组件，用真实组件标签和 SHA 组成新发布，再通过隔离全栈、干净机和升级机三层证据验收。RC18.1 的价值不在于“多加了一次修复”，而在于停止扩大改动面，恢复了可复现、可定位、可回滚的发布纪律。
