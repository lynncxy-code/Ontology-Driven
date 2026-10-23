# OntoTwin 3.2.1 — 楼层空间高度配置补丁实施记录

> 日期：2026-08-19  
> 状态：开发完成，待现场验收  
> 对应 PRD：`docs/PRD/OntoTwin 3.2.1 楼层空间高度配置补丁 (PRD).md`

## 1. 已完成

- 新增项目级楼层查询与单楼层写入接口；
- 楼层基准、构件 Z 和已有绑定实例 Z 改为单事务更新；
- 楼层基准变化时保留构件相对旧楼层基准的个别微调；
- 新实例铸造优先使用构件 `ue_z`，不再丢失 Z 微调；
- CAD 和图片空间底图发布前检查楼层是否已配置，不再自动创建 0 mm 楼层；
- 保存 CAD/图片构件时写入当前标定楼层，并阻止未配置楼层保存；
- 坐标标定工作台新增楼层空间配置卡片；
- 规范楼层标高、UE 实际地面 Z、UE 运行关卡在 UI 中分区解释；
- 图片地面锚点覆盖已有 UE 地面 Z 前增加确认；
- 实例位置编辑增加“楼层基准 / 个别 Z 微调”说明；
- 人物路线编辑读取实时 `floor_table`，不再只显示空间底图发布时快照；
- 修复从会话恢复到图片模式时步骤内容可能未激活的问题。

## 2. 主要文件

### 新增

- `backend/floor_profile_service.py`
- `backend/tests/test_floor_profile_service.py`

### 修改

- `backend/app.py`
- `backend/project_store.py`
- `backend/spatial_assets/service.py`
- `backend/tests/test_spatial_assets.py`
- `frontend/coord_workbench.html`
- `frontend/instance.html`
- `frontend/interaction.html`

项目存储格式、schema 版本和现有页面路由均未修改。

## 3. 接口

```text
GET /api/v2/spatial/floors
PUT /api/v2/spatial/floors/{floor}
```

旧 `PUT /api/v2/spatial/profile` 保持兼容，楼层表写入改为复用相同校验和原子重算逻辑。只修改 `ue_transform.display` 时不再触发全场位置重算。

## 4. 验证结果

### Python 语法

```text
python -m py_compile floor_profile_service.py app.py project_store.py spatial_assets/service.py
```

通过。

### JavaScript 语法

对以下页面的内联脚本执行 `node --check`：

- `frontend/coord_workbench.html`
- `frontend/instance.html`
- `frontend/interaction.html`

全部通过。

### Docker 隔离回归

```text
docker compose run --rm -e ONTOTWIN_STORE=json backend python -m unittest \
  tests.test_floor_profile_service \
  tests.test_spatial_assets \
  tests.test_scene_interaction \
  tests.test_binding_components \
  tests.test_project_store_v3
```

结果：66 项通过，0 失败。

### 浏览器验证

- 已配置楼层能够正确回填；
- 输入 `4500 mm` 时只读结果实时显示 `450 cm`；
- 未配置 2F 时，保存楼层配置前发布按钮保持禁用；
- 保存楼层基准前显示构件和绑定实例重算说明；
- 取消确认后不产生服务器写入；
- UE 运行关卡区域明确显示“不设置楼层高度或构件 Z”；
- 页面无 console error / warning；
- 图片模式从会话恢复后能够正常显示第一步内容。

浏览器验证使用现有项目只做读取和本地表单状态测试，没有提交楼层写入。

## 5. 保留边界

- 本补丁不提供楼层删除功能；
- 新建楼层没有“撤销为不存在”的操作，保存后可继续修改高度；
- 已有楼层保存成功后提供一次前端撤销；
- 自由实例继续使用自身绝对 UE 坐标，不随楼层基准移动；
- CAD 锚点仍为 XY，UE 实际地面 Z 在 CAD 模式中手工维护；
- 现场仍需用实际 2F/3F 数据确认模型轴心、地面厚度和人物行走面偏移。
