# OntoTwin ZHHZ Windows 一体化部署

当前方案采用“Windows 前台 + Hyper-V 隐藏后台设备”：ZHHZ 和控制中心直接运行在 Windows；OntoTwin 后台、PostgreSQL、Neo4j 与内置容器引擎运行在随安装包交付的 Linux VHDX 中。客户侧不依赖 WSL 或 Docker Desktop。

第一版不包含 Pixel Streaming，实时 WebSocket 默认关闭，ArtStudio 使用已迁移的 HTTPS 资产库地址。

## 数据隔离规则

- PostgreSQL 发布种子只保留 `ds_1784694647848 / ZHHZ`，其他开发、测试和历史项目不得进入客户包。
- Neo4j 不复制开发数据卷；首次启动从 ZHHZ ontology registry 生成的 seed 初始化。
- 客户数据位于单独的 Hyper-V 数据盘，系统 VHDX 可升级替换，数据盘默认保留。
- 多项目共享部署仍被 [`docs/TODO.md`](../../docs/TODO.md) 中的 Neo4j 项目隔离事项阻断；当前版本只允许单 ZHHZ 项目交付。

## 版本单一事实来源

发布版本只在调用 `Build-RuntimeOnlyRelease.ps1` 时传入一次，例如 RC9.4 使用：

```powershell
$releaseVersion = "3.7.1-r1-rc9.4"
```

该值写入 `release-manifest.json`，后续 payload、安装器文件名、检测条件校验和客户文档均从清单读取。不要在后续步骤另行指定或重命名版本。Windows 数字版本按 `RC主号 × 100 + RC次号` 自动生成：RC9.4 对应 Binary/Bundle `3.7.1.904`、MSI `3.7.904`。`CUSTOMER-README.md` 与 `BASIC-OPERATIONS.md` 是带版本占位符的模板，只有构建输出才是可交付文档。

## RC9.4 构建顺序

1. 使用 `Build-ShippingRuntime.ps1` 从唯一允许的 `D:\ZHHZ\ZHHZ\ZHHZ.uproject` 编译、Cook、Stage 并归档 Win64 Shipping 运行时。
2. 使用 `Build-RuntimeOnlyRelease.ps1 -ReleaseVersion $releaseVersion -SourceProjectPath D:\ZHHZ\ZHHZ\ZHHZ.uproject` 合并已经验证的基础数据与新运行时，并生成包含 `component_versions` 的发布清单。脚本会核对 `.uproject`，记录全部 `.umap` 和 Shipping 主文件哈希。
3. 使用 `hyperv\Build-InstallerAppPayload.ps1` 组合 Windows 运行时、后台 appliance 和首次启动 payload。此步骤从发布清单继承版本，并校验嵌套的 `release.tar.gz`。
4. 使用 `installer\Build-Installer.ps1` 生成 Setup、MSI 与外置大文件 payload。此步骤从 AppPayload 清单继承版本，不再接受独立 `ReleaseLabel`。
5. 在交付前执行 SHA-256 校验，并在隔离客户机完成“旧版覆盖升级”和“全新安装”两条烟测。

只有需要重建 Linux 系统盘时才运行 `hyperv\Build-Appliance.ps1`。仅更新 UE 视角或地图时，应继承上一版已验证的 appliance、后台镜像、数据库和模型资产，不得重新选择旧 staging 目录。

## 强制门禁

- UE project/target 必须同时为 `ZHHZ`；UFS 和 NonUFS 清单必须存在。
- `SourceProjectPath` 必须指向本次实际构建的 `ZHHZ.uproject`，其哈希必须与 runtime manifest 一致；所有源 `.umap` 和最终 EXE/PAK/UCAS/UTOC 都进入证据清单。
- UFS 必须包含 `ZHHZ.uproject`、OntoTwinSync 和 `glTFRuntime`；不得包含 `test0316`、`tmp_ue` 或 Pixel Streaming。
- appliance manifest、系统盘、seed、Docker Engine 和 Docker Compose 的哈希必须一致；seed 与 guest bootstrap 必须使用宿主端口 `48075`。
- 根发布清单、AppPayload、复用 ZIP 和嵌套 `release.tar.gz` 的版本及组件身份必须完全一致。
- `customer.env.example` 的发布版本必须更新为新版本；三个镜像 tag 必须与 `component_versions` 及对应 Docker tar 内的 `RepoTags` 一致。
- 复用 `OntoTwin-ZHHZ.payload.zip` 时，不仅校验其自带 SHA，还必须与当前 AppPayload 的 UE 主文件、runtime manifest、appliance 和嵌套发布包逐项匹配。

任一门禁失败都必须终止构建，不能通过重命名可执行文件或安装包继续交付。

## 安装介质与生命周期

安装介质必须按整个目录交付，因为超过 4 GB 的业务 payload 不内嵌进 MSI。客户应运行 Setup；单独的 MSI 主要用于企业软件分发系统，不能替代同目录的环境和 payload 阶段。

- payload 文件本身超过 FAT32 的 4 GiB 单文件上限；物理介质必须使用 NTFS/exFAT，或先完整复制到本机 NTFS 磁盘。
- `DataRoot` 必须持久化在 `HKLM\SOFTWARE\OntoTwin\ZHHZ\DataRoot`。全新安装只从 Ready、Fixed、NTFS、Windows Storage 判定为本机磁盘且至少有 60 GiB 可用空间的卷中选择，优先使用 App 所在的非系统卷，其次按可用空间选择其他非系统卷，最后才使用系统卷；USB、SD/MMC、网络盘、文件虚拟盘和无法可靠识别的非系统卷不得自动入选。非系统卷使用 `X:\OntoTwin-ZHHZ\Data`，系统卷使用 `C:\ProgramData\OntoTwin-ZHHZ`。
- 已存在注册表 DataRoot 或 legacy `C:\ProgramData\OntoTwin-ZHHZ` 数据时必须原地沿用，绝不自动迁移；旧根在启动/Provision 前仍要求至少 20 GiB 可用空间。HostService、HostControl、Launcher、备份、卸载与重装必须解析同一持久化值。

- MSI 安装 Windows 控制中心与 LocalSystem 管理服务。
- Setup 检查并启用 Hyper-V；需要重启时返回标准 3010，重启后重跑 Setup 即可继续。
- 首次点击“启动系统”时，管理服务注册隐藏 VM、创建独立数据盘、加载离线镜像并等待后台健康检查。
- 普通升级替换程序和系统 VHDX，但保留数据盘。
- 普通卸载移除程序、服务、VM 注册和内部网络，默认保留注册表 `DataRoot` 指向的后台数据。

不要改回 Docker Desktop/WSL 客户部署，也不要在多项目隔离完成前把第二个项目装入同一 Neo4j 实例。
