# OntoTwin Nexus 4.8 UE 接入包（候选版）

把已有 UE5.6 工程接入 OntoTwin，并在本机打开网页后台。不含示例工程、关卡和客户数据；内附可选核心人物资源、工业行为插件。

## 准备

- Windows 10/11、UE 5.6、Docker Desktop（Linux containers，启动后再执行脚本）。
- 建议安装 Visual Studio 2022 的「使用 C++ 的游戏开发」与 Windows SDK；工程引擎构建不一致时需重新编译插件。
- 插件与网页后端已在包内，无需另装 Python、数据库或 Node.js。首次启动使用包内镜像，无需在线拉取。

## 使用

1. 解压到短路径，例如 `D:\OntoTwin48`。请勿覆盖旧接入包目录。
2. 关闭 UE。在 PowerShell 执行 `Tools\Install-OntoTwinPlugin.ps1 -ProjectPath "D:\你的工程\项目.uproject"`。现有同名插件会先备份；目录链接会停止安装，避免误改母本。
3. 需要人物漫游时执行 `Tools\Install-CoreCharacters.ps1 -ProjectPath "D:\你的工程\项目.uproject"`。该步骤会检查同名 Content 冲突。
4. 执行 `Tools\Start-OntoTwinBackend.ps1`，浏览器打开本机后台。在网页首次初始化组织和管理员，随后创建或导入数据集。
5. 打开工程并启动关卡。在网页数据集卡片点「关卡绑定」，选择已发现的工程和关卡。该关卡以后固定使用此数据集；切换网页项目不会改变绑定。更换数据集必须明确确认换绑。
6. 先用少量设备/家具验证实例位置、表现与交互，再扩大接入范围。资产回洗方法见 `Docs`，源 Actor 清理需另行确认。

端口默认 5000；若已有其他服务，使用 `Tools\Start-OntoTwinBackend.ps1 -Port 5400`，并把 UE 后端地址改为 `http://127.0.0.1:5400`。初始化后的端口保存在 `.runtime`，再次启动沿用原配置。

## 数据、版本与恢复

- 新解压目录首次启动创建独立环境和数据卷，不复用旧 W18 或其他项目的 Docker 数据卷，不自动导入、激活数据集。
- `manifest.json` 记录 Git 提交、插件指纹和镜像身份；`SHA256SUMS.json` 是逐文件校验清单。没有静默更新或自动拉取 main。
- `Stop-OntoTwinBackend.ps1` 仅停止当前环境，保留数据；`Check-OntoTwinBackend.ps1` 核对运行版本。请勿手动删除不明数据卷。
- 旧环境升级先导出数据集包、备份数据库，在新环境导入验收。此包不自动迁移旧账号、组织和权限。
- 插件备份位于目标工程 `Saved/OntoTwinInstallBackup`；回退时关闭 UE，按备份恢复 `.uproject` 和同名插件。
- 第三方 glTFRuntime、WebUI 及人物资产保留原许可与使用限制；本包用于已获授权的项目接入，不代表取得对外再分发这些资产的额外许可。

本包为开发集成候选版；源代码验证、编译通过不等于目标机器的全部业务场景已验收。
