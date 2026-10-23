# OntoTwin 3.4 UE 同步数据库与场景管理升级 (PRD)

> 状态：**已实施**（2026-07-01 敲定并开发；2026-07-02 修订A：本体存储改图数据库，见 §12）
> 主线：OntoTwin Nexus（UE 插件 `OntoTwinSync` + 后端 Flask）
> 前置：3.1 三维坐标体系、3.3 运行时模型加载
> 关联记忆：多关卡/多楼层是硬需求；同步库设计决策集。
>
> **修订记录**
> | 版本 | 日期 | 内容 |
> | :-- | :-- | :-- |
> | 草案 | 2026-07-01 | /grill-me 敲定全部决策 |
> | 修订A | 2026-07-02 | **本体（语义层）存储由 PG 改为 Neo4j 图数据库**（对接上游"灵枢"本体注册中心）；PG 保留实例/分区/项目 + 类型绑定缓存。详见 §12，原文冲突处已加〔修订A〕标记 |

---

## 1. 背景与目标

现状痛点（本轮 review 确认）：

- 后端↔UE **没有真正的"场景↔关卡"映射**：`/api/v2/state/snapshots` 无条件返回激活项目全部实例，UE 端 `SceneId` 与后端 `?scene=` 参数**空转被忽略**，`floor_table.ue_level`（`project_store.py:76`）从未接线。
- 数据散在三处（后端 JSON、UE 内存注册表、`.umap` 里的固化 Actor），无统一真源。
- "快照固化到关卡"存得下坐标却**存不下模型**（glTFRuntime 网格是 transient，不进 `.umap`），且固化时不写坐标、重复固化只更新资产路径。
- 历史遗留项目有批量**未经 ontotwin、未本体化**的 UE actor，无法纳入管理。

**目标**：以 PostgreSQL 为单一真源，重组本体/实例存储；建立"分区(zone)→关卡"路由支撑多厂房/多关卡；**废弃"固化"概念**，改为纯数据库驱动；打通 UE→ontotwin 回写与历史数据一次性迁移。

---

## 2. 范围

**本轮做（In scope）**
- 存储层从 JSON 迁移到 PostgreSQL（藏在现有 `ProjectStore` 接口后）。
- 本体（项目级 `object_types`）/ 实例 / 分区 三类数据分表。
- 分区路由：`zone_id` + 分区登记表 + UE 按 zone 过滤。
- 废弃固化，改 DB 驱动 + 编辑器临时预览。
- 用例1：UE→ontotwin 回写（编辑器）。
- 用例2：历史 actor 一次性离线迁移脚本。

**本轮不做（Out of scope）**
- **运行时网格加载性能优化**（异步/共享缓存/分帧）→ **下个版本**（已诊断待定）。
- 运行时（打包 exe）物体拖拽回写 → 未来迭代（本轮仅预留端点中立性）。
- 运行时分区流送触发（相机/后端指定）→ 多关卡且性能吃紧时再做（本轮全加载）。
- 楼层↔Z 数学维护功能（floor 保持名义值）。
- 系统级本体入库（`INTERFACES`/`OBJECT_TYPES`/`mapping_rules` 保持代码/git 配置）。〔修订A：部分推翻——I3D 接口与项目类型已以"灵枢 registry"格式入 **Neo4j** 图库；`mapping_rules` 确认空转已随死页面清除。见 §12。〕

---

## 3. 术语

| 词 | 含义 |
| :-- | :-- |
| 分区 zone | 关卡路由的通用单位，**颗粒度项目自定**（当前=一厂房；未来可=一楼层；机场=一管控区域）。一关卡=一分区=一 Manager，1:1。 |
| 本体 object_type | 项目级类型注册表（会变的运行数据），进 PG。 |
| 收编 | 把历史 UE actor 转成受 Manager 驱动的孪生实例。 |
| rehydrate | 从轻量存储数据重建运行态对象（此处指从 DB 重新 spawn 并加载网格）。 |

---

## 4. 核心架构决策

### 4.1 单一真源 = PostgreSQL，藏在 `ProjectStore` 接口后
〔修订A：真源一分为二——**语义层（本体）真源 = Neo4j**，**运行层（实例/分区/项目）真源 = PG**；PG 的 object_type 表退化为"类型绑定缓存"。见 §12。〕
- PG 成为~~本体+~~实例真源；**把 `ProjectStore` 的存储层从 JSON 换成 PG，方法签名不变**，`app.py` 83 处 `instance_store/project_store` 调用基本不动。
- "唯一可见性规则：一切只认当前激活项目" **不变量保留**。
- 每条实例带 `source` 来源标记（`ontotwin` / `ue_migrated`）。

### 4.2 废弃"固化(SnapshotToLevel)"
- 理由：DB 唯一真源、UE 完全由 DB 驱动，无需把孪生 Actor 永久烘进 `.umap`；连带解决 glTFRuntime 网格不持久问题。
- 取而代之是**一个核心机制 + 两个动作**：
  - **核心机制 = 从 DB spawn 并驱动 Actor**，一套代码两场合：编辑器手动触发（临时预览/授权微调，**transient 不写盘**）；运行时自动轮询（持续驱动 + 按分区加载/卸载）。
  - **回写**（用例1）、**一次性历史导入**（用例2）。
- `.umap` 里只留**非孪生的静态建筑（壳子）+ TwinSceneManager**；孪生实例全归 DB。
- `TakeOverExistingInstances` 不再需要。

---

## 5. 数据模型（PostgreSQL）

技术：**psycopg3 + 原生 SQL + JSONB**（嵌套块用 JSONB 列，不全量规范化）。docker-compose 增 `postgres` 服务。新增依赖 `psycopg[binary]`（**加依赖前须用户确认**）。

分表（概念，字段以实现为准）：

- **ontology（本体/项目级类型）**：`rid`, `project_id`, `name`, `category`, `injected_interfaces`(JSONB), `asset_id`, `source`, `properties`(JSONB), `created_at`, `deleted_at` …〔修订A：该表语义部分降级为**绑定缓存**（语义真源在 Neo4j，由同步工具单向刷新；绑定字段 asset 等仍归本表所有）。见 §12。〕
- **instance（实例）**：`id`, `project_id`, `object_type_rid`, `zone_id`, `component_id`(可空), `source`(ontotwin/ue_migrated), `ext_guid`(UE ActorGuid, 迁移用), `render_config`(JSONB), `raw_state`(JSONB), `created_at`, `last_seen`, `status`, `deleted_at` …
- **zone（分区登记表）**：`zone_id`, `project_id`, `name`, `ue_level`(地图路径), `streaming`(JSONB, 流送信息), `created_at`, `deleted_at` …
- 系统级 `INTERFACES`/`OBJECT_TYPES`/`mapping_rules` **不入库**。
- `floor_table` 保留在 `spatial_profile`，仅管 `z_base_mm`（删死字段 `ue_level`/`map_codes`）；`floor` 与 `zone_id` 正交。

**删除语义 = 全面软删**：删除打 `deleted_at`、保留行、UE despawn；所有查询过滤 `deleted_at IS NULL`。

---

## 6. 功能需求

### FR-1 存储层迁移（PG）
- `ProjectStore` 内部改 PG 实现，对外方法签名不变；启动时若 PG 有数据即以 PG 为准。
- 提供从现有 `data/projects/*.json` 一次性导入 PG 的初始化路径。

### FR-2 本体/实例/分区分表
- 按第 5 节建表；嵌套块用 JSONB。

### FR-3 分区路由
- 实例带 `zone_id`；正向流程在**绑定时选分区**（下拉），可由 CAD 来源（图纸/图层/楼层）预填建议。
- 分区登记表维护 `zone_id → ue_level + 流送信息`。
- **UE 端：一子关卡放一个 `TwinSceneManager`，配 `zone_id`**（替换空转的 `SceneId`）。
- **后端：`/api/v2/state/snapshots` 真正读 zone 参数并过滤**（现状被忽略，需修）。

### FR-4 DB 驱动 + 编辑器临时预览
- 运行时：Manager 轮询 DB，按 zone spawn/驱动/despawn（沿用现有轮询链路，去掉固化接管逻辑）。
- 编辑器：Manager 面板加 **"从数据库拉取预览" + "清除预览"** 两个 `CallInEditor` 按钮；**预览 Actor 必须 `RF_Transient`**（保存关卡绝不写进 `.umap`，杜绝误固化）；重新拉取先清上一批（去重）。

### FR-5 回写（UE→ontotwin，用例1）
- 触发：**编辑器按钮 + 变更预览**（扫有位移的 actor → 弹旧值→新值差异 → 确认后 POST）。
  〔实施注：落地形态 = **回写对象限定为 FR-4 的预览 Actor**（方案A，用户拍板）。拉取预览时记基线，"提交空间变更(回写)"按钮 diff 当前 transform vs 基线，仅提交动过的；无轮询拉锯、无 PIE 丢弃陷阱。差异确认以屏幕消息呈现（CallInEditor 能力内），复杂弹窗留待 runtime 迭代。〕
- **端点做成"传输中立"的普通 HTTP POST**（收 `instanceId/zone_id/transform/source`，业务逻辑在后端，UE 只发请求）——为将来 runtime 拖拽回写预留，禁止写成编辑器专用。
- **落点分类处理**：绑定 CAD 构件的实例 → UE cm **逆变换回规范系 mm** 写进构件 `canonical_*`（否则被 `_rederive_components` 覆盖，需实现 `coord_canon_to_ue` 的逆）；自由实例 → 直接写 `raw_state` cm。
- 字段范围：**仅 transform**（材质/标签/动画仍以后端为唯一来源）。
- 权威：回写=一次性提交，权威归 ontotwin；`bLocalOverrideLock` 独立保留，仅作 PIE 运行时临时冻结。

### FR-6 历史迁移（一次性离线脚本，用例2）
- 形态：`backend/tools/` 下独立脚本，**不挂路由**；豁免"不新增"限制；人工把关；**幂等可重跑**。
- 身份：**按 UE ActorGuid 收编** → 读 transform+mesh → PG 建实例（`source=ue_migrated`, `ext_guid=ActorGuid`）→ 回写 `InstanceId` 到 actor / 原地换 `ATwinInstance`。按 GUID 幂等。
  〔实施注1：收编语义最终定为**导出→迁移→删原 actor**（与废弃固化一致，不回写 InstanceId 不保留原 actor）。〕
  〔实施注2：UE 侧导出改为**扫描 Outliner「待迁移文件夹」**（默认 `ToMigrate`，Manager 面板可配）而非读选择集——UE 细节面板多选不同类型时会隐藏 Manager 专属按钮，"同时选中 actor+Manager"不可行（用户验收时发现）。〕
- 类型归属：按 StaticMesh/资产名匹配已有类型（复用 2.9.2 `block_asset_mapping` 思路）；匹配不上进单一 **Legacy 兜底桶**，事后在 ontotwin 人工本体化；不批量造类型。
- 收编后走正向流程，可被 ontotwin 修改。

### FR-7 删除/生命周期
- 全面软删（见第 5 节）；UE 侧检测到实例消失即 despawn。

### FR-8 运行时分区加载（MVP）
- **MVP：全部加载**（当前 1 个，最多 3 个），不建运行时流送。
- **架构预留**：zone 表 / 每分区一 Manager / 按 zone 过滤查询三样先做进去，将来加流送为纯增量（数据模型不变）。

---

## 7. 非功能需求 / 约束

- 运行时 API：**只读 + 改，不开放 insert**（保"实例只诞生于 ontotwin"不变量；新增仅走离线迁移脚本）。
- 保持"单激活项目"可见性不变量。
- 前端走 CDN、无构建；不加异步队列/权限系统。
- CLAUDE.md 已删除"不加关系型数据库"限制。

---

## 8. 前向兼容预留

| 预留点 | 现在做 | 将来加时 |
| :-- | :-- | :-- |
| runtime 回写 | 回写端点传输中立（HTTP POST） | 加 UE 拖拽交互 + 拖动期临时锁，不动 DB/端点 |
| 运行时流送 | zone 分区架构 | 在某时机调 `LoadStreamLevel`；触发按产品形态选后端指定 or 相机 |
| 楼层 Z 基准 | floor 与 zone 正交、floor 名义保留 | 需要每层不同 Z 时给 zone 表加可选 `z_base` |

---

## 9. 明确不做（本轮）

- 运行时网格加载性能优化（异步/共享缓存/分帧）→ **下个版本**。
- 运行时拖拽、运行时流送触发、楼层维护功能、系统级本体入库。

---

## 10. 待办 / 未决（2026-07-02 刷新）

**已了结**
- ~~依赖批准~~：`psycopg[binary]`、`neo4j` 驱动均已获批并落地。
- ~~task_93990702 清理死页面~~：已完成（`/mapping` 页、`/api/v2/mapping/rules`、`mapping_rules.json` 均已移除）。

**仍开放**
- 运行时加载性能：先诊断（Output Log 计时 / `stat unit`）再定方案，**下版处理**（用户已拍板）。
- 流送触发（后端指定 vs 相机）：多关卡时再选。
- **翻默认存储到 PG**（`ONTOTWIN_STORE` 默认仍 json，切 pg 待用户拍板；验收清单 H 组全绿为门槛）。
- 分区赋值链路：`spawn/mint` 尚不写 `zone_id`（"绑定时选分区"未实现）；zone 登记表无 CRUD API。MVP 单关卡可接受，多关卡前补。
- UE 侧代码（FR-4/5/6 按钮）由用户在 UE 工程编译实测（源码经 junction 直连仓库）。

---

## 11. 涉及的主要改动点（实现参考）

- 后端：`project_store.py`（存储层换 PG）、`app.py`（snapshots 读 zone 过滤、新增回写端点）、`backend/tools/`（迁移脚本）。
- UE：`TwinSceneManager`（zone 配置、去固化/接管、编辑器预览按钮、回写按钮）、`TwinInstance`（transient 预览、回写取值）。
- 部署：`docker-compose` 加 `postgres`；`requirements.txt` 加 `psycopg[binary]`。

---

## 12. 修订A（2026-07-02）：本体存储拓扑变更——Neo4j 图数据库

### 12.1 变更动因
用户确认：**后期需与上游"灵枢(Lingshu)"本体注册中心直接对接**。上游形态为 Foundry 风格的本体 registry：本体 JSON（五段式 `shared_property_types / interface_types / object_types / link_types / action_types`，RID 形如 `ri.obj.<uuid>`）→ `generate_ontology_cypher.py` 校验并生成 Cypher → 灌入 Neo4j。为使 OntoTwin 的本体层与上游"住进同一栋楼"，本体（语义层）真源由 PG 改为 **Neo4j**。

### 12.2 兼容策略（核心决策）
**逐字节 vendor 上游工具链、一行不改**（`backend/tools/lingshu/`：`ontology_rules.py` + `generate_ontology_cypher.py` + `ontology.schema.json`）。图模型由上游生成器唯一定义（6 种节点标签均带 `:OntologyEntity`；7 种边 `BELONGS_TO/BASED_ON/EXTENDS/REQUIRES/IMPLEMENTS/CONNECTS/OPERATES_ON`；写入 `MERGE by rid + SET +=` → 幂等、多来源共存、扩展属性不被冲掉）。将来对接 = 上游本体灌进**同一个库**，rid（UUID）不撞、模型同源，无需翻译层。

### 12.3 数据流（终态）
```
本体 registry JSON（git 追踪，RID 一次生成永不再生）
  └─ build_ontology_json.py：ProjectStore 类型 + I3D 接口 → registry
       └─ generate_ontology_cypher.py（上游原版）：校验 + 生成 Cypher
            └─ Neo4j（语义唯一真源；写入只走此链，不走 API）
                 ├─ db/graph.py（只读）→ GET /api/v2/ontology/registry
                 ├─ fetch_graph_echarts() → POST /api/v2/ontology/graph_from_registry
                 │    → 图谱页「本体图库」Tab 一键出图（CSV 导入保留、放后面）
                 └─ tools/sync_types_from_graph.py（单向：图→表）
                      → PG/项目类型表 = 「类型绑定缓存」
                        语义字段（name/接口/生命周期/graph_rid）随图刷新
                        绑定字段（asset_id 等）归表所有、同步绝不触碰
```

### 12.4 已落地清单
| 项 | 内容 |
| :-- | :-- |
| 部署 | docker-compose 加 `neo4j:5`（7474 浏览器 / 7687 bolt，healthcheck，持久卷） |
| 工具链 | `backend/tools/lingshu/` 三件套逐字节 vendor |
| registry | `backend/ontology_registry/ontotwin.ontology.json`（**必须进 git**；16 共享属性 + 4 接口(EXTENDS 继承) + 53 类型；官方校验器全量通过） |
| 灌库 | 713 节点入图；重灌幂等（节点数不变）；`x_block_name/x_source` 扩展属性重灌后存活 |
| 运行时读 | `neo4j>=5.28,<6` 驱动（已批）；`db/graph.py` 只读层；`GET /api/v2/ontology/registry`（图库不可达降级 503） |
| 图谱页 | 「本体图库」Tab（默认首选）直查出图，与 CSV 解析产物同构，预览/发布数据集链路零改动复用 |
| 绑定缓存 | `sync_types_from_graph.py`：dry-run 默认 / `--apply` 落库 / `--add-missing` 补入图库独有类型（=上游下发新类型的通道）；已验证 53 类型刷新、绑定保留、重跑幂等 |

### 12.5 约束与身份规则
- **图的写入永远走工具链灌库**，运行时 API 对本体只读——与"实例只诞生于 ontotwin"同构的"本体只诞生于 registry 文档"不变量。
- RID 一次生成、进 git、永不重发；转换器按 api_name 对齐保留已有 rid（幂等）。
- CAD 自动建类型 lifecycle=`EXPERIMENTAL`，与上游对齐/人工确认后升 `ACTIVE`；中文/非法名退化为前缀+哈希 api_name，原块名存 `x_block_name` 扩展属性。
- 上游侧仍缺的输入：他们的存量本体 JSON（拿到后灌同一库、人工做 EXPERIMENTAL↔正式类型认领合并）。
