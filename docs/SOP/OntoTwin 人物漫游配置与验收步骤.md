# OntoTwin 人物漫游配置与验收步骤

适用范围：OntoTwin Nexus 人物漫游页面、UE 5.6 `OntoTwinSync` 插件、PIE/Standalone/打包版本。

## 1. 先理解两层配置

人物漫游不是只在 Nexus 页面勾选后就能运行：

- Nexus 保存“选哪个人物、从哪里出生、速度和相机参数”等业务配置。
- UE 宿主工程提供真正的 Skeletal Mesh、动画、人物 Primary Data Asset、皮肤 Data Asset、地面碰撞和相机/路线锚点。

页面目录中的人物卡片是受控资源目录，不代表当前 UE 工程已经安装了对应模型。目录项标有 `project_asset_required=true` 时，必须先完成第 2 节。

## 2. UE 工程一次性接入

### 2.1 基础条件

1. 把 `OntoTwinSync` 插件安装到目标 UE 工程并完成编译。
2. 在实际运行的关卡中只放置一个 `TwinSceneManager`。
3. 确认 UE 工程 ID 已绑定到当前 Nexus 项目，PIE 能读取 `/api/v2/scene-interactions/runtime`。
4. 地面必须具有碰撞并能响应 `Visibility` 射线，否则人物无法投射到地面。

### 2.2 推荐：安装 Core 人物包

每个新宿主工程不需要重新从外网下载人物。关闭 Unreal Editor 后，从 OntoTwin 母本仓库执行：

```powershell
.\scripts\install_ontotwin_character_pack_core.ps1 `
  -ProjectPath "D:\path\to\YourProject.uproject"
```

安装器会完成四件事：

1. 把 `OntoTwinCharacterPack_Core` 安装到宿主工程 `Plugins/`。
2. 把 Ground Staff 工人的网格、骨架、材质和动画依赖安装到 `/Game/Art/A08_Characters/00_Ground_Staff`，并把 Manny 机器人的依赖安装到 `/Game/Characters/Mannequins`。
3. 在 `.uproject` 中启用内容插件。
4. 在 `DefaultGame.ini` 中幂等写入 Asset Manager 规则。

Core 包提供：

- `TwinCharacter:ObserverBase`
- `TwinSkin:ObserverGray`
- `TwinSkin:ObserverGreen`
- `TwinCharacter:MannyRobot`
- `TwinSkin:MannyRobotDefault`

其中“工人”固定使用 `Ground_Staff/ThirdPerson/SkeletonIK/SK_Charactor`；其 `myAnimBlueprint` 会从隐藏的 Manny 动画源实时重定向行走姿态，隐藏源不会出现在画面中。Manny 同时也是另一个可选人物，不再冒充工人。

安装后执行冷启动验证：

```powershell
.\scripts\verify_ontotwin_character_pack_core.ps1 `
  -ProjectPath "D:\path\to\YourProject.uproject"
```

验证器会检查两套人物网格与各自动画共用有效 Skeleton、五项 Primary Data Asset 可加载、工人两套皮肤和机器人默认机体正确，并要求 Asset Manager 汇总中出现 `TwinCharacter=2`、`TwinSkin=3`。验证结束后会恢复宿主 `.uproject`，不会长期启用 Python 编辑器插件。

### 2.3 准备扩展人物 Primary Data Asset

只要 Nexus 资源目录仍展示六个 RenderPeople 人物，新项目接入流程就必须把它们视为标准迁移项，不能只安装 Core 包。关闭源工程和目标工程的 Unreal Editor 后，使用已验收且具有合法授权的母本工程执行：

```powershell
$env:ONTOTWIN_MIGRATION_DESTINATION = "D:\path\to\TargetProject\Content"
& "D:\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "D:\path\to\LicensedSourceProject.uproject" `
  -run=pythonscript `
  -script="D:\tmp\digital_twin_aircraft\scripts\ue_migrate_renderpeople_to_project.py" `
  -unattended -nop4 -nosplash -nullrhi
```

该步骤会连同网格、骨架、材质和动画依赖迁移 Carla、Claudia、Eric、Manuel、Nathan、Sophia 六套人物与默认皮肤。随后必须合并第 2.5 节的 Asset Manager 扫描目录，并在目标工程冷启动执行：

```powershell
& "D:\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "D:\path\to\TargetProject.uproject" `
  -run=pythonscript `
  -script="D:\tmp\digital_twin_aircraft\scripts\ue_install_renderpeople_characters.py" `
  -unattended -nop4 -nosplash
```

安装器把六个人物配置为 RenderPeople Skeleton 原生的 idle/walk 单节点动画。以下旧配置必须为空：人物和皮肤的 `AnimInstanceClass`、隐藏 `AnimationSourceMesh`、`AnimationSourceAnimInstanceClass`、`AutoRouteAnimation`。不能把工人的 `myAnimBlueprint` 或 Manny/Quinn 动画蓝图复制给 RenderPeople；它们属于不同 Skeleton，混用会造成“六人正常时工人漂移，工人正常时六人加载失败”的互斥故障。运行时由 `CharacterMovement` 独占胶囊位移，原生动画忽略 Root Motion，避免模型漂移。

然后执行冷启动验证：

```powershell
& "D:\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "D:\path\to\TargetProject.uproject" `
  -run=pythonscript `
  -script="D:\tmp\digital_twin_aircraft\scripts\ue_verify_renderpeople_characters.py" `
  -unattended -nop4 -nosplash -nullrhi
```

验收必须同时满足 `TwinCharacter=8`、`TwinSkin=9`，且六个人物均返回 `success=true`。如果没有合法人物资产源，则应在 Nexus 目录中停用相应人物，不能继续显示一个目标 UE 工程无法解析的选项。

以 Nexus 中的“黑西装女士”为例：

- 目录人物 ID：`character.renderpeople.carla`
- UE Primary Asset ID：`TwinCharacter:RenderPeopleCarla`
- Data Asset 文件名必须是：`RenderPeopleCarla`

操作：

1. 把有合法授权的 Skeletal Mesh、Skeleton 和行走动画导入宿主工程。
2. 在 `/Game/OntoTwin/SceneInteraction/Characters` 中创建 `TwinCharacterAsset` 类型的 Primary Data Asset。
3. 将文件命名为 `RenderPeopleCarla`，大小写必须与 Primary Asset ID 名称部分一致。
4. 至少设置 `BaseMesh`、与该 Mesh 共用 Skeleton 的 `DirectIdleAnimation` 和 `DirectWalkAnimation`；RenderPeople 的 `AnimInstanceClass` 必须为空。
5. `CharacterClass` 可以留空，运行时会使用插件的 `ATwinRoamingCharacter`；如果自定义，必须继承该类。
6. 检查胶囊半高、半径、Mesh 偏移和朝向，避免人物悬空或陷入地面。

仅有页面缩略图不能代替该 Data Asset，也不能代替真正的 Skeletal Mesh。

### 2.4 准备扩展皮肤 Data Asset

“黑西装女士”的默认皮肤对应：

- Nexus 皮肤 ID：`skin.renderpeople.carla.default`
- UE Primary Asset ID：`TwinSkin:RenderPeopleCarlaDefault`
- Data Asset 文件名必须是：`RenderPeopleCarlaDefault`

在 `/Game/OntoTwin/SceneInteraction/Skins` 中创建 `TwinSkinAsset`，设置：

- `SkeletonId = skeleton.renderpeople.ue4.v1`
- `Mesh` 为与人物共用 Skeleton 的 Skeletal Mesh
- `AnimInstanceClass` 留空；动画由人物 Data Asset 的 Skeleton 原生 direct clips 驱动
- 如需换装，再设置材质覆盖

人物和皮肤必须属于同一 Skeleton 体系。皮肤缺失时运行时可能降级，但不能作为正式验收状态。

### 2.5 配置 Asset Manager

Core 安装器会自动写入以下规则，不需要手工重复添加：

```ini
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinCharacter",AssetBaseClass=/Script/OntoTwinSync.TwinCharacterAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/OntoTwinCharacterPack_Core/Characters"),(Path="/Game/OntoTwin/SceneInteraction/Characters/RenderPeople")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinSkin",AssetBaseClass=/Script/OntoTwinSync.TwinSkinAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/OntoTwinCharacterPack_Core/Skins"),(Path="/Game/OntoTwin/SceneInteraction/Skins/RenderPeople")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
```

增加 Renderpeople 等扩展人物时，每一种 `PrimaryAssetType` 仍应只有一条扫描规则；把扩展目录合并进现有 `Directories`，不要再添加第二条同类型规则。修改后完全重启 UE，否则 Asset Manager 可能仍无法解析新资产，打包时也可能漏 Cook。

### 2.6 关卡中的条件资源

- 使用手动底图出生点：不需要放 `TwinRoamingSpawnAnchor`，但底图必须已发布并完成坐标标定。
- 使用兼容锚点出生：放置 `TwinRoamingSpawnAnchor`，其 `SpawnId` 与配置一致；默认值为 `spawn.character.default`。
- 希望退出漫游后恢复固定镜头：再放置一个 `TwinGodViewAnchor`，其 `CameraId` 为 `camera.startup.default`。
- 启用旧式 UE 测试路线：放置 `TwinRoamingRoute`，其 `RouteId` 与目录值一致；默认测试值为 `route.test.default`。
- 使用 Nexus 绘制的项目路线：路线必须已审核、启用且至少有两个有效点，不需要重复放旧式路线 Actor。

不使用的路线和相机模式不要求放置相应 Actor。

### 2.7 上帝视角的硬性前置条件

只要页面默认视角选择“上帝视角”，或者希望按 `V` 切换到上帝视角，就必须在**实际运行的关卡**中配置相机锚点：

1. 从“放置 Actor”面板把 `TwinGodViewAnchor` 拖入关卡；它就是 OntoTwin 上帝视角所需的相机位置与朝向载体，不需要另写蓝图。
2. 在 Details 中把 `CameraId` 精确设置为 `camera.god.default`。
3. 将该 Actor 移动到期望的厂房全局观察位置，并旋转到期望的俯视方向。
4. 同一个运行关卡中，同一 `CameraId` 只保留一个锚点。
5. 保存关卡并重新进入 PIE；只在编辑器视口中摆好但未保存，不算完成配置。

如果缺少该锚点：

- 页面配置的默认上帝视角会降级为过肩视角，并上报 `god_camera_missing` 或 `god_camera_unavailable`。
- `V` 仍然有效，但只在过肩视角与第一人称之间循环，直到关卡补上 `camera.god.default`。
- 从操作面板显式选择“上帝视角”会保留错误提示，便于定位缺失项。

### 2.8 小地图的硬性前置条件

页面上的“启用小地图”只负责下发业务开关。要在 UE 中看到真实场景小地图，还必须在**实际运行的关卡**中配置唯一的取景锚点：

1. 从“放置 Actor”面板把 `TwinMinimapAnchor` 拖入关卡，不需要制作蓝图。
2. 在 Details 中把 `MinimapId` 精确设置为 `minimap.default`；同一运行关卡只保留一个同 ID 锚点。
3. 将锚点移动到场景上方并朝下俯视。厂房平面图推荐把相机设为 `Orthographic`，再用 `Ortho Width` 控制覆盖范围。
4. `Capture Width`、`Capture Height` 默认使用 `1024 × 768`；`Crop Fraction Per Edge` 默认 `0.20`。先以完整覆盖可通行区域为准，再调整留白。
5. 保存关卡，回到 Nexus 勾选“启用小地图”并“保存并应用”，随后重新进入 PIE。

运行机制与状态：

- UE 只在进入漫游或配置热更新时抓取一次场景画面，不会每帧重复渲染整张小地图；人物方向标记以约 20 Hz 更新。
- `minimap_state=ready`：小地图已生成；右上角应显示小地图，且只有收起/展开按钮拦截鼠标。
- `minimap_state=anchor_missing`：关卡没有 `minimap.default`。
- `minimap_state=anchor_ambiguous`：同一关卡存在多个 `minimap.default`，必须删除或改 ID。
- `minimap_state=capture_failed`：锚点存在但场景抓取失败，应检查渲染目标、相机方向和运行日志。

小地图锚点与上帝视角锚点用途不同，不能互相替代：`TwinMinimapAnchor` 只负责右上角地图取景，`TwinGodViewAnchor` 负责玩家切换后的主相机视角。

## 3. Nexus 页面配置

1. 进入“场景交互 → 人物漫游”。
2. 打开“启用人物漫游”。
3. 选择已经在当前 UE 工程中完成第 2 节接入的人物；不要只根据缩略图选择。
4. 选择允许皮肤，并保证默认皮肤包含在允许皮肤中。
5. 配置出生来源：
   - 未启用有效项目路线时，必须在已发布空间底图上单击放置人物出生点并设置朝向。
   - 底图或坐标标定变化后，必须重新放置出生点，直到红色“请重新放置人物出生点”提示消失。
   - 启用有效项目路线时，路线首点自动成为出生点。
6. 是否启用路线由“启用路线”复选框决定；只在下拉框中选中路线并不代表路线已启用。
7. 配置行走、奔跑、跳跃、相机和小地图参数。
   - 如果默认视角选择“上帝视角”，必须先完成第 2.7 节的关卡相机锚点配置。
   - 如果勾选“启用小地图”，必须先完成第 2.8 节的关卡小地图锚点配置。
8. “运行时自动进入”打开时，PIE 应自动进入漫游；关闭时用 `F7` 进入。
9. 单击“保存并应用”，确认 revision 增加，并等待 UE 上报 `applied_revision` 等于新 revision。

## 4. PIE 验收顺序

1. 启动后端，打开包含 `TwinSceneManager` 的目标关卡。
2. 进入 PIE，先单击一次游戏视口，使键盘焦点进入 PIE。
3. 如果未开启自动进入，按一次 `F7`；开启自动进入时人物应直接生成，`F7` 用于退出/再次进入。
4. 检查以下控制：
   - `WASD`：移动
   - `近身/第一人称鼠标`：释放状态显示指针并可点击；按住鼠标右键进入镜头观察，松开后恢复指针
   - `上帝视角鼠标`：按住鼠标右键观察，松开后恢复指针；左键按指针位置选择
   - `V`：切换第一人称、过肩、上帝视角；关卡没有 `camera.god.default` 时只在前两种视角间循环
   - `Tab`：打开/关闭漫游操作面板
   - `E`：近景交互
   - `Space`：近身与第一人称模式下跳跃；不暂停或恢复路线
   - `P`：暂停/继续自动路线；解说播放期间只切换“解说后暂停/继续”，当前语音和字幕不停
   - `R`：恢复路线
   - `F7`：进入/退出漫游
5. 如果启用了小地图，检查右上角地图可见、人物标记随移动和转向更新、收起/展开有效，地图装饰区域不抢占 WASD 与鼠标观察输入。
6. 退出网页、HUD 交互或漫游后，再次确认 WASD 和相机输入已经恢复。
7. PIE 通过后，继续在 Standalone、Development 和 Shipping 中验证人物资产与皮肤均已 Cook。
8. 八个角色逐一验收：工人和 Manny 使用各自 AnimBP；六个 RenderPeople 使用各自 Skeleton 的 direct idle/walk。所有角色都必须能进入 `F7`、原地站立不漂移、行走时胶囊与模型不分离，并且切换任一角色不影响其他角色下次加载。

## 5. 故障定位顺序

按以下顺序检查，避免只反复按 F7：

1. 后端 `runtime` 是否显示 `config.enabled=true`，且 `blocked_reason=null`。
2. `last_client_status.applied_revision` 是否等于页面 revision。
3. UE 日志是否出现 `OntoTwin F7 roaming toggle received`：
   - 没有：检查 PIE 焦点、PlayerController 和 `TwinSceneManager`。
   - 有：F7 已生效，继续读取紧随其后的具体失败信息。
4. `Character asset TwinCharacter:* is missing`：人物 Data Asset 不存在或 Asset Manager 未扫描。
5. `Base character Skeletal Mesh cannot be loaded`：人物 Data Asset 存在，但没有有效 BaseMesh。
6. `Configured roaming spawn anchor was not found`：锚点模式缺少对应关卡 Actor。
7. 出生点/路线地面投射失败：检查位置、胶囊空间、地面碰撞和 `Visibility` 响应。
8. 上帝视角不可用：检查 `camera.god.default` 相机锚点；这通常会降级，不应与人物资源缺失混为一谈。
9. `V` 无响应：检查日志是否出现 `OntoTwin V camera toggle applied` 或 `OntoTwin V camera toggle ignored`；前者表示按键已处理，后者会直接说明是 HUD 打开、切换动画未结束还是人物未就绪。
10. 页面已勾选小地图但 UE 不显示：依次检查 `config.minimap.enabled=true`、`last_client_status.minimap_state`，再按第 2.8 节检查 `minimap.default` 锚点；不要把页面开关当作自动生成相机。
11. 工人/Manny 与 RenderPeople 表现互斥或漂移：读取人物 Data Asset；RenderPeople 的 `AnimInstanceClass`、隐藏动画源和 `AutoRouteAnimation` 必须为空，direct idle/walk 的 Skeleton 必须与人物 Mesh 完全相同。不要用重定向器或“骨骼名称看起来相似”代替精确 Skeleton 校验。

## 6. SCC2 当前安装结果（2026-08-13）

- F7 输入正常，日志已经收到多次漫游切换请求。
- `OntoTwinCharacterPack_Core` 已安装到 SCC2，并写回 OntoTwin 母本插件目录。
- Asset Manager 冷启动汇总：`TwinCharacter=2`、`TwinSkin=3`。
- “工人”使用 `/Game/Art/A08_Characters/00_Ground_Staff/ThirdPerson/SkeletonIK/SK_Charactor` 和同 Skeleton 的 `myAnimBlueprint`；Manny 机器人作为独立人物 `TwinCharacter:MannyRobot` 保留。
- SCC2 `DefaultGame.ini` 中的 Core 扫描规则只有一组，重复安装不会增加重复项。
- 使用页面中的“工人”即可加载 `TwinCharacter:ObserverBase`；Core 包不包含黑西装女士等 Renderpeople 商城人物，选择这些扩展人物仍需要另装相应授权资产。
- 当前运行时投影中的手动出生点和坐标标定状态为 `valid`；截图里的出生点红色提示需要刷新页面复核，但它不是此次 F7 失败的第一原因。
- `V` 已改为漫游运行时直接读取并完成 SCC2 Editor 编译；没有 `camera.god.default` 时在第一人称和过肩视角之间循环，补锚点后才加入上帝视角。
- SCC2 当前运行关卡尚无 `TwinGodViewAnchor`；若要验收上帝视角，仍需按第 2.7 节由项目方确定取景位置并保存。
- SCC2 已安装小地图运行模块，并在 `/Game/SCC_W9/Art/Maps/L_SCC_W9_Main` 放置唯一的 `minimap.default`：正交俯视、`1024 × 768`、`Ortho Width=52000 cm`，覆盖 W9 建筑。
- 小地图与 V 键已完成编译和静态配置验收；实际画面、按钮输入及人物标记仍需重新打开 UE 后按第 4 节执行一次 PIE 验收。
