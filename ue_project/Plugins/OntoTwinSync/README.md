# OntoTwinSync 插件使用说明

OntoTwin Nexus 的 UE5 数字孪生同步插件。把整个 `OntoTwinSync/` 文件夹拷进任意 UE5 工程的 `Plugins/` 目录即可，不再需要挑选单个源文件。

源码迁移自仓库根目录 `ue5/`（原文件保留作参考，不再维护）。

## 安装

1. 把本文件夹整体复制到目标工程：`<你的工程>/Plugins/OntoTwinSync/`
2. 右键 `.uproject` → Generate Visual Studio project files
3. 打开工程，UE 提示编译插件 → 确认
4. 菜单 Edit → Plugins，确认 "OntoTwin Sync" 已启用（依赖 Niagara 插件，会自动启用）

> 工程是纯蓝图工程也可以——放入 C++ 插件后 UE 会自动转为代码工程并要求装 VS 工具链。

## 包含的三个类与对应前端页面

| 类 | 对接后端 API | 对应前端页面 | 用法 |
|---|---|---|---|
| `ATwinSceneManager`（孪生场景管理器） | `GET /api/v2/state/snapshots` 轮询 | instance.html / ontology.html / coord_workbench.html（2.x 全家） | **关卡里放 1 个即可**，自动 Spawn/销毁/驱动所有孪生体 |
| `ATwinInstance`（孪生实例） | 不发 HTTP，由 Manager 驱动 | 同上 | 不手动放置；可在编辑器用 Manager 的"📸 快照固化到关卡"按钮生成持久 Actor |
| `UDigitalTwinSyncComponent`（⚠ legacy，1.x） | `GET /api/state` + `POST /api/update` | index.html 演示页 | 加到单个 Actor 上，Tags[0] 填实例 ID（如 `vehicle_01`） |

## 典型工作流（2.x，日常用这个）

1. 启动 Flask 后端（默认 `http://127.0.0.1:5000`）
2. 在前端 ontology.html 给 ObjectType 绑定 `ue_asset_path`（UE 内容路径，如 `/Game/Meshes/SM_Forklift.SM_Forklift`）——**没绑的类型 UE 不会渲染**
3. 在 coord_workbench.html 或 instance.html 创建实例
4. UE 关卡中放置 `TwinSceneManager`，细节面板确认：
   - 后端基础URL：`http://127.0.0.1:5000`
   - 孪生体蓝图类：选你的 `BP_TwinInstance`（不选则用 C++ 基类）
5. 点 Play：实例自动出现；前端改状态（位置/材质/动画），UE 0.5 秒内跟随

## 1.x legacy 组件什么时候用

- 配合 index.html 的单实例演示（vehicle_01 / equipment_01 / tooling_01）
- 需要 **UE→后端回写**时：组件在 BeginPlay 把 Actor 的真实世界坐标 `POST /api/update` 写回后端——这是目前全项目唯一的回写通道

## 迁移备注（相对原 ue5/ 目录的差异）

- API 宏 `TEST0316_API` → `ONTOTWINSYNC_API`，与具体工程模块名解耦
- 删除了 `DigitalTwinSyncComponent.cpp` 里的 `#include "test0316.h"`
- 模块依赖去掉了与同步无关的 `InputCore` / `EnhancedInput`
- 所有源文件统一为 UTF-8 BOM 编码（中文注释在 MSVC 下不再有编码风险）
- 逻辑零改动

## 已知限制

- `SetActorLabel` 调用未包在 `WITH_EDITOR` 里（沿袭原代码），打包发行版会编译失败；编辑器内开发/PIE 不受影响
- 轮询为 HTTP 短轮询（0.5s），无推送机制
