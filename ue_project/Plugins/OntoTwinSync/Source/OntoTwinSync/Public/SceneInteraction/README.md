# OntoTwin 4.0 Scene Interaction — UE 项目接入

本目录提供平台侧通用运行能力；人物 Mesh、动画、皮肤、路线和相机仍由具体 UE 项目提供。

## 最小资源

1. 创建 `UTwinCharacterAsset`，资产名 `ObserverBase`，对应后端 `TwinCharacter:ObserverBase`。
2. 创建两个 `UTwinSkinAsset`，资产名 `ObserverGray`、`ObserverGreen`，对应后端 `TwinSkin:*`。
3. 人物与皮肤使用同一个 Skeleton，并为人物配置可打包的 Animation Blueprint。
4. 关卡放置 `ATwinRoamingSpawnAnchor`，将 `SpawnId` 设为 `spawn.character.default`。把 Actor 放在目标楼层地面附近；默认只在锚点上方 1 米至下方 10 米的局部范围内寻找地面，避免跨楼层误投射。
5. `ATwinRoamingRoute.bSplineAtGroundLevel=true` 时，Route Actor 与各 Spline 点的 Z 表示地面表面高度，不要手动加人物胶囊半高。自动路线只从 Spline 读取平面位置和朝向，贴地高度继续由 CharacterMovement 维护。
6. 关卡放置 `ATwinRoamingRoute`，将 `RouteId` 设为 `route.test.default`。默认认为 Spline Z 位于地面；若点已是胶囊中心高度，关闭 `bSplineAtGroundLevel`。
7. 关卡放置 `ATwinGodViewAnchor`，将 `CameraId` 设为 `camera.god.default`。
8. 关卡只需原有一个 `ATwinSceneManager`；4.0 组件由其构造函数自动创建。

## Asset Manager

实际宿主项目必须让 Asset Manager 扫描 `TwinCharacter` 和 `TwinSkin`，并确保 Development/Shipping 构建会 Cook 这些资产。示例目录和规则应在宿主项目中按实际 Content 路径配置，不在插件源码里猜测：

```ini
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinCharacter",AssetBaseClass=/Script/OntoTwinSync.TwinCharacterAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/Game/OntoTwin/SceneInteraction/Characters")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinSkin",AssetBaseClass=/Script/OntoTwinSync.TwinSkinAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/Game/OntoTwin/SceneInteraction/Skins")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
```

## 关卡约定

- 地面和可选对象需能被 `Visibility` 射线检测。
- 人物出生点和路线起点必须能容纳配置胶囊；阻挡时运行时拒绝生成或拒绝归线，不穿墙传送。
- 上帝视角锚点只决定本次会话第一次进入的位置；之后会恢复自由相机的会话位置。
- 普通漫游人物是观察者，不会自动成为 OntoTwin Instance，也不会在心跳上传位置。

## 验收顺序

1. PIE：资源解析、出生、F7、V、Tab、WASD、E/左键选择。
2. 路线：自动接入、WASD 接管、R 归线、从头开始、非闭合 loop 降级。
3. 热更新：速度/相机/皮肤直接生效，人物/出生/路线/上帝相机显示待重载。
4. Development exe：绑定失败关闭、后端断线保持最后配置、Primary Asset Cook 完整。
5. Pixel Streaming：桌面浏览器键鼠输入和 HUD 不穿透。
