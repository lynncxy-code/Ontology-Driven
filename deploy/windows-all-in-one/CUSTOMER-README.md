# OntoTwin ZHHZ 客户部署说明

适用版本：OntoTwin ZHHZ __RELEASE_DISPLAY_VERSION__ 一体化客户版

本安装介质用于在一台 Windows GPU 工作站上运行 ZHHZ、OntoTwin 控制台、PostgreSQL 与 Neo4j。客户不需要了解或安装 WSL、Docker Desktop、Python、Node.js、PostgreSQL 或 Neo4j。

第一版不含 Pixel Streaming，实时 WebSocket 默认关闭。ArtStudio 使用 `https://artstudio.digioasis.tech`，如需访问个人资产仍要配置对应 Token。

## 部署前准备

- Windows 10/11 专业版、企业版或教育版，64 位；推荐 Windows 11 专业版。
- NVIDIA 独立显卡，至少 8 GB 显存；至少 32 GB 内存。
- 全新安装会自动选择可用空间不少于 60 GB 的本机固定 NTFS 磁盘保存后台虚拟机、Docker 数据、数据库和备份，并优先使用容量合格的非系统盘。USB、SD 卡、网络盘和虚拟磁盘只作为安装介质，不会被自动选作程序或数据盘。无需手工选择或移动后台数据目录。
- 从旧版本升级时不会自动迁移已有后台数据：安装程序会继续使用已登记的数据目录；未登记数据目录的旧版通常位于 `C:\ProgramData\OntoTwin-ZHHZ`。升级及启动前应确保该目录所在磁盘至少还有 20 GB 可用空间。
- 程序主体所在磁盘另需至少 10 GB 可用空间；升级时建议预留 15 GB，避免新旧版本切换时空间不足。
- 完整安装介质中包含一个大于 5 GB 的文件，不能存放在 FAT32 U 盘。使用 U 盘交付时请采用 NTFS 或 exFAT，也可以先把整个交付目录复制到本机 NTFS 磁盘后再安装。
- BIOS/UEFI 已开启 Intel VT-x 或 AMD-V。
- 使用本机管理员账户安装；Windows Home 和 Windows Server 不在本版支持范围内。

## 一键安装

1. 保持安装介质目录中的所有文件及原始文件名不变，不要只复制 Setup.exe，也不要拆分或单独解压大体积 payload 文件。
2. 右键 `__SETUP_FILE__`，选择“以管理员身份运行”。
3. 如果安装器要求重启 Windows，请重启后再次运行同一个 Setup.exe；它会从上次进度继续。
4. 安装完成后，双击桌面的“灵云智”。
5. 点击“启动系统”。首次启动会创建本机隐藏后台并初始化 ZHHZ 数据，通常比日常启动慢。

日常使用只需打开控制台，点击“启动系统”或“停止系统”。后台数据库不会随程序退出而删除。

## 数据保护与卸载

- 控制台中的“立即备份”会导出 PostgreSQL 与项目媒体文件。
- 全新安装的非系统盘后台数据位于 `X:\OntoTwin-ZHHZ\Data`（`X:` 为安装程序自动选择的磁盘）；只使用系统盘或从旧版本升级时，数据仍位于 `C:\ProgramData\OntoTwin-ZHHZ`。控制中心创建的备份保存在同一数据目录内，请持续监控对应磁盘空间，不要手工移动该目录。
- 普通升级会保留客户数据。
- 从 Windows“已安装的应用”卸载程序时，也默认保留后台数据，避免误删客户成果。
- 需要彻底清理数据时，必须由技术支持确认备份后执行；不要手工删除 Hyper-V 虚拟机或安装程序自动选择的后台数据目录。

## 网络边界

- OntoTwin 控制台仅通过本机 `http://127.0.0.1:5000/nexus` 访问，不向局域网开放。
- 内置后台运行在 Windows Hyper-V 的独立内部网络中；用户无需操作该虚拟机。
- 第一版离线运行不依赖实时 WebSocket。
- 使用 ArtStudio 时需放行 `https://artstudio.digioasis.tech` 的 HTTPS 访问。

如安装或启动失败，请把控制台显示的状态、Windows 版本及安装日志交给技术支持，不要自行安装 Docker 或 WSL。
