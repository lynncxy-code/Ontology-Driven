# OntoTwin-ZHHZ 一体化打包方案（完整版 SOP）

> 文档编号：SOP-WIN-AIO-ZHHZ-001  
> 文档版本：v1.0  
> 编写日期：2026-08-27  
> 当前实现基线：RC16 / 3.7.1-r1-rc16  
> 适用对象：OntoTwin 单项目 Windows 一体化交付（当前为 ZHHZ_NEW；后续版本沿用同一门禁）  
> 维护原则：发布清单和脚本实际检查结果优先于口头描述、界面标题和历史截图。

## 0. 文档定位、来源与阅读约定

本 SOP 是面向构建人员、验收人员和现场支持人员的可执行发布规程。它把以下两份附件作为历史参考，并把本轮 RC15、RC15.1、RC16 的实际故障补充为强制门禁：

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

| 层级 | 字段 | 当前 RC16 示例 | 必须来自 |
|---|---|---|---|
| UE 源工程 | .uproject 绝对路径 | D:\ZHHZ\ZHHZ_NEW\ZHHZ_NEW.uproject | 构建命令参数 |
| UE 运行时 | project_name / target_name | ZHHZ_NEW / ZHHZ_NEW | ontotwin-runtime-manifest.json |
| OntoTwin-UE 绑定 | ue_project_id / name | ueproj_ZHHZ_NEW / ZHHZ_NEW | release manifest、绑定 API |
| OntoTwin 数据集 | project_id / name | ds_1787305683288 / ZHHZ_NEW | data-manifest.json、release manifest |

当前 RC16 的数据证据为 6 个类型、507 个实例；类型、实例、Parts/渲染引用是三个不同维度，不能把旧文档的计数混写。

### 2.1 旧基线只能标为历史

RC12 文档中的 D:\ZHHZ\ZHHZ\ZHHZ.uproject、ZHHZ、ds_1784694647848、38 types、669 instances 和旧 appliance/backend 版本，仅用于解释历史包。它们不是 ZHHZ_NEW 的默认值。脚本若仍显示这些默认值，必须显式传入新值并把脚本/清单门禁修正后再构建。

历史证据也必须保留原样但标明版本：RC12 曾记录 69 个输入文件、5 张地图、13 个 GLB、动态几何 10,974/10,974，以及 80 项 manifest 文件。这些数字不能拿来替代当前版本的 manifest 计数。

### 2.2 身份契约

1. 文件名不能替代身份：不能把旧 ZHHZ.exe 重命名成 ZHHZ_NEW.exe 来冒充新工程。
2. active 数据集不能替代写入授权：active 只是当前路由状态，所有绑定和激活都要经过正式 API。
3. UI、backend、UE、数据库读回的身份必须全部与发布清单一致。
4. 任一层不一致，停止打包；不要在客户机上直接改 PostgreSQL 表来“修正”。

## 3. 版本、输入冻结和 PackagingRun

### 3.1 版本单一事实

版本只在 Build-RuntimeOnlyRelease.ps1 的 ReleaseVersion 参数传入一次，采用小写规范：

~~~
3.7.1-r1-rc16
~~~

脚本从这一值生成：

| 用途 | RC16 示例 |
|---|---|
| release_version | 3.7.1-r1-rc16 |
| appliance_version | 3.7.1-r1-rc16-appliance1 |
| Windows Binary/Bundle | 3.7.1.1600 |
| MSI 三段版本 | 3.7.1600 |
| Setup 文件名 | OntoTwin-ZHHZ-3.7.1-R1-RC16-Setup.exe |
| cloud-init instance-id | ontotwin-zhhz-3-7-1-r1-rc16-appliance1 |

RC16.1、RC16.2 等小版本必须生成新的发布清单、payload、appliance seed（若系统盘或 guest 源有变化）和 SHA，不得覆盖 RC16 目录。

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

### 阶段 4：构建 AppPayload

~~~powershell
& "$deploy\hyperv\Build-InstallerAppPayload.ps1" -ReleaseDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\03_release' -ApplianceDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\04_appliance' -OutputDirectory 'D:\ZHHZ\PackagingRuns\ZHHZ_NEW_RC16_20260826-164424\05_app-payload' -WslDistribution 'Ubuntu-22.04'
if ($LASTEXITCODE -ne 0) { throw 'AppPayload build failed' }
~~~

该阶段必须校验：

- release、appliance、runtime、data、component_versions 版本完全一致。
- 三个 Docker tar 的 RepoTags 与清单一致。
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
OntoTwin-ZHHZ-3.7.1-R1-RC16-Setup.exe
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
- [ ] 三个镜像 tar 的 RepoTags 与 component_versions 一致。
- [ ] MSI launcher 完整发布目录路径/大小/hash 相符。
- [ ] Setup/MSI/payload 无未解析版本 token。
- [ ] 最终 SHA256SUMS 完整且可重算。

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
| mkdir -p baseline_backup_root 失败 | 40 GiB 数据盘已被重复快照耗尽，或目标状态不安全 | 先检查容量；保留最早完整快照；禁止盲目清理 |
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
- [ ] 本轮 PackagingRun 独立且输出目录开始为空。

### 构建产物

- [ ] Shipping runtime 重新 Cook/Stage/Archive，UAT 日志归档。
- [ ] release-manifest.json、data-manifest.json、appliance-manifest.json 完整。
- [ ] Database/postgres/01-restore.sh 存在且嵌套归档恰一份。
- [ ] 三个镜像 tar、VHDX、seed、Compose hash 通过。
- [ ] AppPayload、MSI、Setup 版本继承关系通过。
- [ ] 最终 SHA256SUMS 可在另一目录重算。

### 运行时安全

- [ ] baseline capture 有空间门禁、事务 intent、完成 marker 和单次语义。
- [ ] 正常重启不重复备份、不重复解包、不删除 volume。
- [ ] bootstrap 失败会停止/限次，不会无限制造快照。
- [ ] active dataset、UE binding 和 backend route 由 API 读回确认。

### 客户验收

- [ ] 干净 Win Pro/Enterprise/Education 机器安装通过。
- [ ] Environment/重启/Setup/桌面启动顺序通过。
- [ ] 首次冷启动和第二次冷启动都通过。
- [ ] RC15/历史版本升级、失败恢复和回滚演练通过。
- [ ] 低磁盘、端口占用、GuestControl 瞬断、非管理员、VMConnect 权限场景有明确结果。
- [ ] 日志、截图、状态快照、版本和 hash 已交付支持人员。

未勾满不得交付。

## 16. 当前 RC16 基线记录（示例）

以下是本轮可作为审计样例的事实，不应被复制为以后所有项目的硬编码：

| 项目 | 值 |
|---|---|
| release | 3.7.1-r1-rc16 |
| appliance | 3.7.1-r1-rc16-appliance1 |
| dataset | ds_1787305683288 / ZHHZ_NEW |
| UE | ueproj_ZHHZ_NEW / ZHHZ_NEW |
| Types / Instances | 6 / 507 |
| PostgreSQL dump SHA-256 | 53ed7ca541eb1bf596d2988fec71c80d3f56ac09822eef18b4608c4f723317db |
| Setup SHA-256 | 3e3f799f05850aa36c1f59602ee0bdfc9824514fd4720bad6120a4330674d9d2 |
| payload ZIP SHA-256 | 0684747cdf0d95a04c6229e4e62334552c832c7e8f784cc68cbea728bdf62e5a |
| RC16 bad-payload cleanup fingerprint（仅历史修复条件） | 30f273786738d9aff87e805adf97da6ae670771a443f9d77e6e6cd2d9d709de7 |
| 本轮交付目录（示例） | E:\ZHHZ\Releases\OntoTwin-ZHHZ_NEW-3.7.1-R1-RC16-Installer |
| 自动化 SHA 条目 | 11 项全部通过 |
| MSI launcher 校验 | 463 个文件的路径、大小、hash 全部匹配 |
| 构建结果 | 0 warnings / 0 errors（以本轮构建日志为准） |

本表只证明 RC16 的构建证据；每一版必须重新计算并把新值写入自己的 manifest/SHA 文件。

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
构建门禁结果：
干净机结果：
旧版升级结果：
第二次冷启动结果：
回滚结果：
已知风险/例外及批准人：
诊断日志目录：
~~~

## 19. 一句话结论

一体化包不是“把 EXE、VHDX 和数据库压成一个 Setup”这么简单；它是四层身份一致、数据种子可恢复、UE Shipping 可复现、Hyper-V bootstrap 幂等、升级可回滚、失败可取证的完整发布系统。任何新版本都必须先证明“全新 PostgreSQL volume 能恢复正确的 ZHHZ_NEW 数据，并且自动重试不会再次制造备份副作用”，然后才谈桌面双击是否能打开。
