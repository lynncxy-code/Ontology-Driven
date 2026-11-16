# BUG-20 资产目录身份错位（4.8）

- 日期：2026-11-03
- 影响版本：4.8.0-rc.21（`9a74412`）及之前带 4.8 场景级绑定的构建
- 影响场景：新环境 / 异机新装、在网页重新做过“关卡绑定”的项目
- 严重度：阻断类型审核里的“从已同步目录选择资产”

## 症状

- UE 侧日志：`[UE资产目录] 同步成功 | assets=94 | code=201`
- 网页类型审核：`已同步 0 个资产`，没有“最后同步”时间
- 直接查询 `GET /api/v2/ue/assets/catalog?ue_project_id=<UE 上报 ID>` 能拿到资产，
  但网页用的是另一个 ID

## 根因

4.8 的 `ue_project` 有两个标识：

| 字段 | 含义 | 示例 |
|---|---|---|
| `ue_project.ue_project_id` | 数据库主键，`project_scene_binding` 存的是它 | `ue_9c94e525…` |
| `ue_project.stable_key` | UE 客户端自己上报的工程 ID | `ueproj_scc_w18` |

资产目录按 UE 上报身份落盘（`backend/data/ue_asset_catalogs/<sha256(id)>.json`），
UE 心跳与场景在线判定同样使用上报身份。

`/api/v2/ontology/datasets` 在引入场景级绑定后，把 `ue_project.ue_project_id`
（内部主键）当作 `bound_ue_project_id` 返回。网页据此查目录，与 UE 写入的
文件名不一致，永远查不到；同时 `get_catalog` 对不存在的文件返回空目录而不是
404，把“身份对不上”伪装成了“已同步 0 个资产”。

## 修复

1. `app.py`：新增 `_active_scene_bindings()`，同时取内部主键与 `stable_key`，
   对网页返回 UE 上报身份；4.8 场景绑定优先于旧 `dataset.bound_ue_project_id`
   字段（旧字段可能在换绑后残留）。
2. `ue_asset_catalog/service.py`：目录不存在时返回 404 `asset_catalog_missing`，
   不再返回空目录。
3. 前端无需改动：`coord_workbench.html` 已把 404 渲染为“尚未同步”状态。

## 回归

- 新增 `tests/test_ue_asset_catalog_identity.py`：
  绑定映射使用上报身份、`stable_key` 缺失时退回主键、接口返回上报身份、
  场景绑定覆盖旧字段、未同步工程读目录 404、按上报身份读到资产。
- 更新 `tests/test_ue_asset_catalog_guard.py`（浏览器显式项目读目录需先有清单）、
  `tests/test_ue_asset_picker_binding.py`（未同步工程改为 404）。
- 后端全量测试：`python -m pytest tests -q` 通过（本地 Windows 环境存在与本改动
  无关的偶发用例，单跑与相关用例集稳定通过）。

## 部署与回滚

- 纯后端读路径改动，不改表结构、不做数据迁移，历史目录文件继续可用。
- 源码挂载部署：重启后端容器；镜像部署：重建镜像或临时替换 `/app/app.py`。
- 回滚：还原 `app.py` 与 `ue_asset_catalog/service.py` 两个文件即可。

## 后续（需重编 UE 插件，另行安排）

- 资产目录同步开始时打印解析后的后端地址，避免“面板显示 5000、实际请求另一端口”。
- 把 `-OntoTwinBackendBaseUrl=` 的应用时机提前到 `OnConstruction`，让编辑器内
  也能看到生效值。
