# OntoTwin 3.4 验收测试清单

配套 PRD：`OntoTwin 3.4 UE同步数据库与场景管理升级 (PRD).md`

分两类：**后端类**（可在 docker/本机直接跑）和 **UE 手动类**（需在编辑器/打包 exe 里操作）。

---

## 0. 前置环境
- [ ] `docker compose up -d db` → `db` 容器 healthy
- [ ] `docker compose exec -T db psql -U ontotwin -d ontotwin -c "\dt"` 看到 5 表：`project / object_type / instance / zone / app_singleton`
- [ ] `docker compose build backend` 成功（含 psycopg 3.x）
- [ ] 确认 `coord_transform.py` 已有 `build_ue_matrix / invert_affine / apply_transform`（FR-5 绑定实例回写依赖，缺则 bound 用例会失败）

## A. FR-1 存储层换 PG（默认零回归）
- [ ] **默认仍 JSON**：不设 `ONTOTWIN_STORE` 启动后端，`project_store.__class__.__name__` 为 JSON 版；现有页面/接口行为不变
- [ ] **一次性导入**：`docker compose run --rm backend python -m tools.import_json_to_pg` → 报告导入 N 个项目、类型/实例数与 JSON 源一致
- [ ] **pg 模式读回一致**：`ONTOTWIN_STORE=pg` 启动 → 激活项目、类型数、实例数、抽查某实例 `raw_state`（如坐标/旋转）与 JSON 源逐一对上
- [ ] **写入往返**：`/api/v2/state/override` 改一个实例坐标 → 新建 store 实例重读为改后值（落库成功）
- [ ] **软删**：删除一个实例 → `get_all_ids` 不含它，且 PG 行 `deleted_at` 非空（不物理删）
- [ ] **app 启动**：`ONTOTWIN_STORE=pg` 下 Flask 正常起、`_build_snapshot` 出四接口快照、无 import 错
- [ ] **失败回退**：故意配错 `DATABASE_URL` → 后端不崩、回退 JSON（或给出明确报错，按实现约定）

## B. FR-3 分区过滤（snapshots 按 zone）
- [ ] `GET /api/v2/state/snapshots`（不带参）→ 返回激活项目**全部**实例
- [ ] `GET /api/v2/state/snapshots?zone=<zoneA>` → 只返回 `zone_id=zoneA` 的实例
- [ ] `?scene=<x>`（旧参数）与 `?zone=` 等效（兼容）
- [ ] 传一个不存在的 zone → 返回空数组（非报错）
- [ ] 实例无 `zone_id`（MVP 单关卡）时，不带参能正常全量返回

## C. FR-5 空间回写（UE→ontotwin）
- [ ] **自由实例**：对无构件实例 POST `/api/v2/state/writeback` `{instance_id, transform:{tx,ty,tz,rx,ry,rz,sx,sy,sz}}` → `mode:"free"`，`raw_state` 更新为该 UE cm 值
- [ ] **绑定实例**：对绑定 CAD 构件的实例回写 → `mode:"bound"`，构件 `canonical_xy/z` 被逆变换写入、`ue_xy/z` 同步
- [ ] **抗覆盖**（关键）：绑定实例回写后，**触发一次 `_rederive_components`**（改一下 spatial_profile/楼层表再存）→ 该实例位置**保持回写值、未被冲掉**
- [ ] **未标定拒绝**：profile 未标定（仿射不可逆）时对绑定实例回写 → 返回 error，不写入垃圾规范坐标
- [ ] **不存在实例**：回写不存在 id → 404 `instance not found`
- [ ] **旋转约定**：回写 `rz`(Yaw) 后，snapshot 的 `I3D_Spatial.rotation_z` = 回写值（rx=Roll/ry=Pitch/rz=Yaw 对齐）

## D. FR-6 历史迁移

**后端脚本**
- [ ] `--dry-run`：不写库，打印拟迁移统计 + id 映射预览
- [ ] 真跑：匹配 `mesh_type_mapping.json` 命中的 → 归对应类型；未命中 → 进 `legacy.unclassified` 桶（桶不存在则自动建）
- [ ] **幂等重跑**：同一输入再跑 → `new:0 / updated:N`，PG 中**无重复实例**（按 `ext_guid` 判重）
- [ ] 迁移实例落库带 `source=ue_migrated`、`ext_guid`、per-actor `raw_state.asset_id`
- [ ] 迁移实例能出快照（类型名、asset、位置/旋转正确）
- [ ] 输出 `ue_migration_result.json` = `{ext_guid: instance_id}`

**UE 侧（手动）**
- [ ] Manager Details 有"孪生管理器|迁移"分类的两个按钮
- [ ] 框选历史 actor → "① 导出" → `Saved/OntoTwinMigration/ue_actors_export.json` 生成，含 ext_guid/mesh/transform，数量对
- [ ] （跑完后端脚本）"③ 清除已迁移Actor" → 按 ActorGuid 删掉已迁移原 actor，屏幕提示数量；Ctrl+S 后关卡不再含它们
- [ ] 未选中任何 actor 就点导出 → 导出 0 个、不报错

## E. FR-4 废弃固化 + 编辑器预览（UE 手动）
- [ ] Manager Details **不再有**"快照固化到关卡"按钮；改为"孪生管理器|预览"下"从数据库拉取预览""清除预览"
- [ ] 点"从数据库拉取预览" → 按本 Manager 的 zone 从 DB spawn 出实例，位置/资产正确
- [ ] **transient 关键**：预览出实例后 **Ctrl+S 存关卡 → 重开关卡 → 预览实例不在**（证明没写进 .umap）
- [ ] "清除预览" → 预览实例全部消失
- [ ] 重复点"拉取预览"不叠加（先清后拉）
- [ ] **运行时(PIE/exe)**：Play → Manager 轮询自动 spawn 本 zone 实例；后端删实例 → UE 侧对应 despawn；EndPlay 后运行时实例全部清理

## F. 清理死页面（回归）
- [ ] `GET /mapping` → 404（页面路由已删）
- [ ] `/api/v2/mapping/rules`（GET/POST/DELETE）→ 404
- [ ] 各页面导航无指向 `/mapping` 的死链
- [ ] `MockInstanceSimulator`（后台模拟线程）仍正常工作（`MappingStore` 类未被误删）
- [ ] `/api/v2/coord/mapping`（坐标标定映射，与规则映射无关）**仍在**

## G. 整体回归 / 兼容
- [ ] `docker compose up -d --build`（含 db+backend）一键起、`/nexus` 入口正常
- [ ] 现有页面（ontology_graph / instance / coord_workbench / floor_pulse）功能未退化
- [ ] UE 插件在你的引擎版本下**编译通过**（FR-4/FR-6 的 C++）

## H. 翻默认到 PG 的门槛（全绿才翻）
- [ ] A/B/C/D 后端用例全过
- [ ] PG 数据与 JSON 源一致性再确认一次
- [ ] 定好备份/回滚方案（JSON 文件保留、`ONTOTWIN_STORE` 可切回）
