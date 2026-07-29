# OntoTwin Nexus —— Skills + MCP 接入层设计

> 日期：2026-07-29
> 版本：**v6（Codex 四轮复审通过：补 PG 存储、并发验收、完整写端点表、组合事务、create_empty_project 契约）**
> 状态：**Codex 四轮确认 go**（唯一剩项 `create_empty_project` 固定 `activate=false` 已补）；待用户终审 → 进 writing-plans
> ⚠ 关键修正史：v4 误以为「handler 内 check-then-act」即原子（错）；v5 下沉进 ProjectStore 锁（对，但漏了 PG 子类与组合事务）；v6 补齐。方案 B 实际改动涉及 `app.py` + `project_store.py` + **`project_store_pg.py`**（服务器跑 `ONTOTWIN_STORE=pg`，签名必须两实现一致）。
> 范围：Nexus 主线（`backend/lite`、`frontend/scenes` 已于 `f4685a1`「extract embodied intelligence」抽离出仓库，本仓库现为 Nexus 单线）
> 目标：把 Nexus 从「人用的 Web 系统」变成「IDE / CLI AI 可直接调用的能力」

---

## 修订记录（v1 → v2）

v1 的端点映射有若干与后端实际行为不符之处，经 Codex 评审 + 逐条读 `app.py` 核实后修正。关键修订：

| # | v1 的错 | 代码证据 | v2 修正 |
| :-- | :-- | :-- | :-- |
| 1 | `mint_instances(dry_run=true)` 可预览 | `binding_mint()` 不读 body，直接铸造（app.py:2474） | 删 dry_run；拆 `preview_mint`（MCP 侧非原子预测）+ `mint_instances`（真写） |
| 2 | `get_state_snapshot` = 整场景快照 | `/state/snapshot` 必带 `?id=`，单实例（app.py:2211）；整场景是 `/state/snapshots`（2222） | 拆 `get_instance_snapshot` + `get_state_snapshots` |
| 3 | 建空项目→激活→`import_csv` 即建库 | `import_csv` 只写 `_custom_graph_data` 全局缓存（2578）；`activate` 才写 `_object_types`（2857） | 本体链改为 `import → publish → activate`，见 §8 |
| 4 | `get_ontology_graph`=当前项目图 | `/ontology/custom_graph` 返回最近导入缓存（2664） | 拆 `get_import_staging_graph` + `get_project_ontology_graph`（/datasets/{id}/graph） |
| 5 | `get_active_project` 直接取 `is_active` | Demo 可 `is_active=true` 但 `project_store.get_active()=None` | 归一化返回 `{dataset_id, project_id, writable, kind}` |
| 6 | 客户端审批=人工闸门 | MCP 协议不保证审批；Cursor 可自动运行 | 降级为「兼容客户端可提供的体验」；加 `expected_project_id` + 单写者规约 |

### v2 → v3（对 `33dc0701` 重新核验）
代码从 `2da52f4` 前进到 `33dc0701`（app.py +521 行、project_store +265 行、lite 线抽离）。逐 handler 复核结果：

- **所有映射端点路径 / 方法不变**，仅行号平移；v2 的核心修正（mint 无 dry_run、import 只写 staging、snapshot 单/复数、import→publish→activate 链）**在新代码上全部仍成立**。
- **`activate_dataset` 精细化**：对已有项目改为「只读激活」，不再重投影图节点覆盖类型能力配置（修了旧 bug）；仍会填充 `_object_types`。对 `activate_project` 工具无影响，仅在描述中注明「激活已有项目不会覆盖其类型能力配置」。
- **新增能力**：`POST /api/v2/object-types/{rid}/model-binding/promote`（model overrides）→ 纳入二期工具 `promote_model_binding`。
- **结构**：`backend/lite`、`frontend/scenes` 已移出仓库；本设计范围表述相应更新（不再需要「排除 lite」措辞）。

> 结论：v2 设计经受住了这次代码更新，只做增量补充，未推翻任何决策。

### v3 → v4 → v5（用户选 B + Codex 二轮复审）
- **v4（选 B）**：用户选择「允许极小后端改动」。上表第 1 行「删 dry_run」与「v2 修正在新代码仍成立」中关于「mint 无 dry_run」的部分**已被 supersede**——B 方案下 mint 通过后端扩展获得真 `dry_run`（§14.1）。`preview_mint` 工具随之取消。
- **v5（Codex 二轮）**：Codex 指出 v4 的原子性论证错误（handler 内两次独立加锁 ≠ 原子）。v5 将 `expected_project_id` 校验**下沉进 ProjectStore 锁内事务**，`save_components` 收敛为单事务，`bind_batch` 一次持锁，`dry_run` 抽共享 `_plan_mint`，并明确端点覆盖与 multipart 载体。故 B 实际改动涉及 `app.py` + `project_store.py`（见 §14）。
- **v6（Codex 三轮）**：补齐 v5 遗漏——① `project_store_pg.py` 必须同步透传新参数（服务器跑 PG，否则 `mint(dry_run=)` 抛 TypeError，§14.0）；② 并发验收断言修正为「activate 先拿锁→写 409 / 写先拿锁→落在 A 绝不到 B」（§14.3，等待中的 activate 不会让当前写 409）；③ 写端点表补全 publish/activate/import/CAD 及各自并发语义（§14.2），`activate`/`publish`/全局 staging 不套 expected；④ `save_component_bundle` 组合事务、`bind_batch` 批内部分成功单保存语义定死。
- 上方 v1→v3 历史表中涉及 mint/dry_run 的行为**历史决策记录**，以 §14、§5.1、§5.2 为准。

---

## 1. 目标与非目标

### 目标
- 让 Claude Code、Cursor 等 AI 客户端通过 **MCP** 直接驱动 Nexus 的读 / 写 / 运维能力。
- 配一套 **skill**，把「四段流水线（类型 → 构件 → 实例 → 运行）该怎么走」的编排知识交给 AI。
- MCP 主体是包在现有 `/api/v2` REST 外面的转译层；仅为安全做**两处向后兼容的后端能力扩展**（§14）。

### 非目标（本轮不做）
- 除 §14 两项加法式扩展外，不改后端其他行为 / 不改存储结构。
- 不做远程多客户端 MCP（HTTP-SSE）——留作未来升级，本轮只做本地 stdio。
- 不做鉴权 / 权限系统（内网访问，沿用单人定位）。
- 不做会话级项目隔离（沿用后端「全局唯一激活项目」，见 §5）。

### 选定方案 B：两项加法式后端能力扩展
用户已选 B。为消除纯转译层无法解决的两个真风险，允许做**两项「可选新字段、缺省即旧行为」的向后兼容扩展**（详见 §14）。两项都需触及 `app.py` + `project_store.py`（原子性必须在存储层的锁内实现，不能只在 handler 加护栏）。取舍后的现状：

| 风险 | 纯转译层（A） | 选 B 后 |
| :-- | :-- | :-- |
| 可靠 dry-run | 只能 MCP 侧非原子估算 | **已解决**：mint 支持 `dry_run` 真预览（§5.1、§14.1） |
| 写-写竞态（TOCTOU） | 只能缩小窗口 + 单写者规约 | **已解决**：写端点 `expected_project_id` 原子校验（§5.2、§14.2） |
| 强制人工审批 | MCP 协议无此保证 | **仍存在**：属 MCP 协议层限制，非后端能解（§5.3） |

**B 的两处改动均为可选新字段**：现有 Web UI 不发这些字段 → 行为 100% 不变（零用户工作量、低运行风险）。

---

## 2. 架构

```
Claude Code / Cursor  ──stdio(MCP)──▶  ontotwin-mcp (Python 本地进程)
                                             │ HTTP (httpx)
                                             ▼
                              Nexus REST API  ${NEXUS_BASE_URL}/api/v2
                                             │
                                   PostgreSQL + Neo4j（已部署于 192.168.88.66）
```
- **纯转译层**：MCP 不 import 后端任何模块，只发 HTTP。
- **本地 stdio 进程**：每个 AI 客户端各起一个 MCP 进程，用 `NEXUS_BASE_URL` 指向 Nexus。
- **文件的传递由 MCP 进程完成**：工具收 `file_path`（本地路径），MCP 进程读文件后用 httpx 组 multipart 上传——**绝不把路径字符串直接发给 Flask**（见 §7）。
- **实现栈**：Python + 官方 `mcp` SDK（FastMCP）+ `httpx`。

---

## 3. 工具清单

### 3.1 操作分级（决定审批策略，不能只按 GET/POST）

| 级别 | 含义 |
| :-- | :-- |
| `read` | 纯读，无副作用 |
| `compute` | 纯计算，不落库（如 calibrate、automatch） |
| `stage-write` | 改全局临时态（import 写 staging、parse 写 latest CAD 缓存） |
| `persist-write` | 落库 / 改全局激活态（高危，默认关闭自动批准） |

### 3.2 核心工具（M1–M2，27 个）

| 工具 | 端点 / 方法 | 级别 | 说明 |
| :-- | :-- | :-- | :-- |
| `list_projects` | GET `/ontology/datasets` | read | 响应含 `is_active` |
| `get_active_project` | 由 `list_projects` 归一化 | read | 返回 `{dataset_id, project_id, writable, kind}`；见 §5.4 |
| `activate_project` | POST `/ontology/datasets/activate` | **persist-write** | 改全局激活态；高危、不纳入默认自动编排。注：激活已有项目为只读，不覆盖其类型能力配置（33dc0701 精细化） |
| `create_empty_project` | POST `/ontology/datasets` | stage-write | 建**空**数据集（类型库需另经 import→publish→activate 填充）。**MCP 固定传 `activate=false`**，不隐式切换全局激活态；不套 expected（见 §14.2） |
| `import_ontology_csv` | POST `/ontology/import_csv` | stage-write | multipart；只写 staging 缓存，保留原始 basename（后端按文件名识别 6 表） |
| `publish_ontology_dataset` | POST `/ontology/publish` | stage-write | 把 staging 缓存追加为新数据集，返回 `dataset_id`（不激活） |
| `get_import_staging_graph` | GET `/ontology/custom_graph` | read | 最近导入缓存（**非**当前项目图，名字已澄清） |
| `get_project_ontology_graph` | GET `/ontology/datasets/{id}/graph` | read | 指定/当前数据集的图谱 |
| `list_object_types` | GET `/ontology/types` | read | 当前项目类型库 |
| `get_object_type` | GET `/ontology/types/{rid}` | read | 单类型详情 |
| `parse_cad_dxf` | POST `/cad/parse` | **stage-write** | multipart（字段名必须 `file`，可带 wall_height/thickness）；会改全局 latest CAD 缓存 |
| `calibrate_coordinates` | POST `/coord/calibrate` | compute | 纯算仿射矩阵 + RMSE，**无 dry_run 概念** |
| `save_components` | POST `/coord/save_components` | persist-write | 存构件；类型库为空时后端会拒绝对应块 |
| `list_components` | GET `/binding/components` | read | 当前项目构件（含绑定状态） |
| `get_spatial_profile` | GET `/spatial/profile` | read | 单位 / 原点 / 楼层 z_base，帮 AI 理解坐标系 |
| `upload_roster` | POST `/binding/roster/upload` | stage-write | multipart（字段名 `file`） |
| `list_roster` | GET `/binding/roster` | read | 撮合前核对清单 |
| `automatch_bindings` | POST `/binding/automatch` | compute | 只出建议，不落库 |
| `bind_instance` | POST `/binding/bind` | persist-write | 单条绑定 |
| `bind_instances_batch` | POST `/binding/bind_batch` | persist-write | 批量绑定，避免循环调用 |
| `unbind_instance` | POST `/binding/unbind` | persist-write | 解绑，保证可逆 |
| `mint_instances` | POST `/binding/mint` | read（dry_run=true）/ persist-write（false） | 支持 `dry_run`：true 返回真实预览不落库，false 真铸造。带 `expected_project_id` |
| `list_instances` | GET `/instances` | read | 当前项目实例列表 |
| `get_instance_state` | GET `/instances/{id}` | read | 实例元数据 + raw_state |
| `get_instance_snapshot` | GET `/state/snapshot?id=` | read | 单实例接口映射后快照 |
| `get_state_snapshots` | GET `/state/snapshots?zone=` | read | 整场景快照（不传 zone=激活项目全部） |
| `set_instance_state` | POST `/state/override` | persist-write | Body `{instance_id, patch}` |

### 3.3 二期 / 可选工具（M4+，高风险或非通用）

- `get_instance_transform`（GET `/instances/{id}/transform`，read）—— 位置诊断
- `promote_model_binding`（POST `/object-types/{rid}/model-binding/promote`，persist-write）—— model overrides：把迁移候选模型提升为类型正式渲染绑定
- `get_ue_binding_status`（GET `/ue/binding_status`，read）
- `bind_ue_project`（POST `/ue/bind_active_project`，persist-write）—— UE 身份绑定，非建模必需
- `list_spatial_frames` / `preview_spatial_transform`（read/compute）
- `set_spatial_profile` / frame calibrate / instance transform PUT —— **触发全场重算或持久化，二期再开**

> 工具面收敛策略：M1–M2 只注册 3.2 的核心集，避免 30+ 工具压垮模型选择；二期工具按需开启。

---

## 4. Skill 层

一个 skill：`ontotwin-nexus/SKILL.md`（YAGNI）。内容：

1. **触发描述**：涉及数字孪生场景、设备实例、坐标标定、本体类型、Nexus 时使用。
2. **四段流水线心智图**：类型 → 构件 → 实例 → 运行。
3. **端到端配方**：见 §8 例 2（已按 import→publish→activate 修正）。
4. **黄金铁律**：
   - 一切只认当前激活项目；写前先 `get_active_project` 且 `writable=true` 才可写。
   - 写工具必传 `expected_project_id`；写前把「将在项目 X 做 Y」说给人听。
   - 术语链「类型 / 构件 / 实例」不可混。
   - 铸造前先 `mint_instances(dry_run=true)` 看无副作用预览；真写用 `dry_run=false` 且带 `expected_project_id`。预览与真写之间若有人改了绑定，结果可能有出入（见 §5.1）。
5. **失败自救**：无激活项目、Demo 只读、图库降级、后端不可达。

> Skill 主要惠及 Claude Code；Cursor 靠工具 description 自解释（单点操作可，多步流程需用户多引导）。

---

## 5. 项目上下文、写安全与残余风险

### 5.1 mint dry-run（选 B 后支持，但非「预览=提交保证」）
后端 `binding_mint()` 增加可选 `dry_run` 分支（§14.1）：`dry_run=true` 时**在 ProjectStore 同一把锁内、对项目快照的深拷贝运行与真 mint 完全相同的规划函数**，返回 `to_create/to_update`，不落库。因此它是**基于单一一致快照、复用真实 mint 规划逻辑的无副作用预览**——不是「MCP 侧估算」，也不是「预览结果 = 后续提交结果」的保证：预览与真写是两次请求，其间若有人改了 components/bindings，真写结果可能不同。若要求「所见即所提交」，需后端返回 plan revision/etag、真写时原子校验（本轮不做，留作升级）。
> `will_update` 定义：**业务字段实际变化**的实例，而非「所有已存在实例」——因 mint 每次都会刷新 `last_seen`，若按整条 diff 判断会把所有旧实例都误列为 update。规划函数需排除 `last_seen` 这类无语义刷新字段。（`preview_mint` 工具取消，由 `mint_instances(dry_run=true)` 取代。）

### 5.2 写-写竞态（TOCTOU）（选 B 后已解决，但必须在存储层锁内）
**v4 的错**：在 handler 里「先 `_check_expected_project()` 再调 `project_store.bind()`」——这是**两次独立加锁**，中间可被别的请求 `activate()` 插入，TOCTOU 未消除。
**v5 的对**：校验必须与写操作**共享同一次持锁**。做法（§14.2）：给 ProjectStore 写方法加可选 `expected_project_id`，进入 `with self._lock` 后**先核对 `_active_id`、再改、再存**，全程不放锁；或提供 `transact_expected_active(expected_id, updater)` 原子入口（复用现有 `transact_active`，补一个锁内校验）。因此：
- 所有**项目级落库写**工具必带 `expected_project_id`；由**存储层锁内**原子校验，真正消除窗口。（`activate`/`publish`/全局 staging 写不套此规则，另有语义，见 §14.2 表。）
- 缺省该字段 → 跳过校验 → 旧行为（Web UI 不受影响）。
- **`instance_store` 就是 `ProjectStore` 同一对象**（app.py:66 `instance_store = project_store`），`override` 走 `update_raw_state`（同一把 `RLock`）——所以共享事务边界是既成事实，实现时给 `update_raw_state` 加锁内 expected 校验即可，并同步改 PG 子类。
- `activate_project` 仍单列为高危工具、不进默认自动编排。
- 保留「写后回显当前项目」用于向人复述，但不再是防线。

### 5.3 人工审批不是协议保证
MCP 协议不强制「写工具必人工审批」；是否展示、能否自动运行取决于客户端版本与配置（Cursor 可自动运行）。因此：
- 文档表述为「兼容客户端**可**提供审批体验」，不称「真正人工闸门」。
- README 分别记录 Claude Code / Cursor 的具体审批配置与验证结果。
- persist-write 工具默认标 destructive、默认关闭自动批准。
- 工具 description / skill 是模型提示，非强制访问控制。

### 5.4 Demo 与可写项目的双语义
`list_datasets` 的 `is_active` 可能指向内置 `demo`，此时 `project_store.get_active()` 为 `None`，多数写接口会报「无激活项目」。故 `get_active_project` 归一化：
```json
{ "dataset_id": "demo", "dataset_name": "...", "project_id": null, "writable": false, "kind": "demo" }
```
仅当 `is_active=true` 且非 Demo 且 `project_id` 非空时 `writable=true`，才允许 persist-write。

---

## 6. 错误映射

不再把所有 400 当「无激活项目」。MCP 客户端**先保留后端原始状态码 + 错误体 + operation**，再分类：

```json
{ "code": "NEXUS_VALIDATION_ERROR", "http_status": 400, "operation": "upload_roster",
  "backend_error": "缺少必须的文件: ...", "retryable": false }
```

至少区分：
- 400 校验失败 / 无激活项目（仅错误文本明确匹配「无激活项目」时才给 activate 提示）
- 403 项目 / UE 绑定不匹配
- 404 资源不存在
- 409 冲突
- 413 本地或远端体积超限
- 5xx 后端失败
- connect / read / write / pool 超时
- 非 JSON 响应 / content-type 异常
- MCP 请求取消
- Neo4j 相关降级：如实说「语义图库暂不可达」，**不**一律承诺「不影响主功能」

---

## 7. 文件上传工具的参数与安全边界

三个 multipart 工具（`import_ontology_csv` / `parse_cad_dxf` / `upload_roster`）在 stdio 本地首版：

- 参数用**显式本地路径**：`parse_cad_dxf(file_path, wall_height?, wall_thickness?)`、`import_ontology_csv(file_paths[])`、`upload_roster(file_path)`。
- **MCP 进程读文件 → httpx 组 multipart 上传**；不把路径交给 Flask。
- 路径必须：规范化、存在、普通文件、落在配置的 **allowed roots** 内。
- 校验：扩展名、文件个数、单文件与总大小上限。
- **本体 CSV 保留原始 basename**（后端按 filename 识别 6 表）。
- 文档写明：容器 / SSH / 远程开发环境下，MCP 看到的是**哪一侧文件系统**（路径歧义来源）。
- 首版不用 base64（体积与日志泄露风险）。

---

## 8. 使用范例（写进 skill）

### 例 1 · 只读查询
「场景里现在有哪些设备，在线几个?」
→ `get_active_project`（确认 writable）→ `list_instances` → `get_state_snapshots` → 汇总。

### 例 2 · 端到端搭孪生（**已按 import→publish→activate 修正**）
「用这份 DXF 和设备清单，搭一个五楼孪生」
```
① import_ontology_csv(file_paths=[6 张表])      → staging 缓存
② get_import_staging_graph()                     → 预览导入内容
③ publish_ontology_dataset(name="五楼")          → 得 dataset_id = ds_...
④ activate_project(ds_id, expected=ds_id)        ⚠ 高危：建立类型库 + 切激活态
⑤ list_object_types()                            → 验证类型库非空
⑥ parse_cad_dxf(file_path=五楼.dxf)              → 48 个设备块候选
⑦ calibrate_coordinates(anchors=4 点)            → RMSE 0.03m
⑧ save_components(...)                            ⚠ persist-write
⑨ upload_roster(file_path=清单.csv) + list_roster
⑩ automatch_bindings() → bind_instances_batch(...) ⚠ persist-write
⑪ mint_instances(dry_run=true)（真实预览）→ mint_instances(dry_run=false, expected_project_id) ⚠ 真写
```
> 关键：**不是**「建空项目再导入」；而是导入→发布→激活直接从 CSV 生成并激活类型库。

### 例 3 · 运行态运维
「把 DW-007 标成告警」
→ `get_active_project`（回显 + writable 校验）→ `list_instances`（定位）→ 复述「将在项目 X 置告警」→ `set_instance_state(instance_id, patch={status:warning}, expected_project_id=X)`。

---

## 9. Repo 布局（独立子目录，不碰 backend/）

```
mcp/
  ontotwin_mcp/
    __init__.py
    server.py        # FastMCP 应用 + 工具注册（python -m ontotwin_mcp）
    client.py        # httpx 客户端 + multipart 上传 + 错误映射
    config.py        # NEXUS_BASE_URL / 超时 / allowed roots
    errors.py        # API 错误 → 结构化 MCP 错误
    files.py         # 本地文件校验（allowed roots / 大小 / 扩展名 / basename 保留）
    tools/
      project.py ontology.py cad.py binding.py runtime.py
  skills/ontotwin-nexus/SKILL.md
  tests/
    test_route_contract.py   # 从 Flask URL map 校验路径 + 方法
    test_tools_integration.py# Flask test client + 隔离临时 ProjectStore，跑真 handler
    test_files.py            # multipart / BOM / 中文名 / 缺表 / 坏 DXF / 超大
    test_mcp_stdio.py        # 真实 MCP 子进程 initialize / tools.list / tools.call
    test_race.py             # 两 MCP 进程交替 activate/write，验证检测与告警
  pyproject.toml   # 依赖: mcp, httpx（独立子项目，不动 backend/requirements.txt）
  README.md        # Claude Code / Cursor 注册命令 + 审批配置记录
```

---

## 10. 配置与分发

- 环境变量：`NEXUS_BASE_URL`（默认 `http://192.168.88.66:5000`）；分级超时 `NEXUS_TIMEOUT_CONNECT` / `_READ` / `_UPLOAD` / `_CADPARSE`；`NEXUS_ALLOWED_ROOTS`。
- **Claude Code**：`claude mcp add ontotwin -- python -m ontotwin_mcp`，或 `.mcp.json` 片段。
- **Cursor**：`~/.cursor/mcp.json` 片段。
- Skill 安装：`ontotwin-nexus/` 拷进 `~/.claude/skills/` 或项目 `.claude/skills/`。

### 超时与重试
- 分操作类超时：connect / 普通 read / upload / CAD parse 各设一档。
- **非幂等写**（create/save/mint/bind/override）**超时后禁止自动重试**（结果状态不确定）。
- 只读 / 纯计算可有限次退避重试。
- CAD parse 超时后用 `/cad/status`、`/cad/latest` 查是否实际完成。

---

## 11. 测试策略（不只 mock）

mock 会「按错误设计证明自己对」，故必须有真 handler 层：
- **路由契约**：从 Flask URL map 校验路径 + 方法（防再次映射错端点）。
- **Flask test client 集成**：隔离临时数据目录 + 临时 ProjectStore，跑真实 handler。
- **MCP stdio 协议**：真实子进程走 initialize / tools.list / tools.call。
- **文件上传**：真 multipart、BOM、中文名、缺表、坏 DXF、大文件。
- **竞态**：两 MCP 进程交替 activate/write。

必加回归用例：
- Demo 为 active 但无 writable project。
- `/state/snapshot` 无 id 返回 400；`/state/snapshots` 返回全量。
- **`mint(dry_run=true)` 不落库**（项目文件 / 内存实例 / `last_seen` / dirty 均不变），且返回精确 create/update 规划；随后无并发修改时真 mint 的集合与预览一致。
- import 后类型库不变、publish+activate 后才变。
- **并发竞态（两线程 + 同步栅栏，非顺序交替）**：`expected_project_id` 校验后、写入前，第二线程 `activate` 切项目 → 断言写被 409 拒绝、未写错项目。
- **`save_components` 事务性**：profile/frame/components 中途切项目 → 整请求拒绝或全部落在同一项目，绝不分裂。
- **`bind_batch` 不跨项目**：一次 batch 全程持同一项目锁。
- `mint` body 边界：空 body / 非 JSON / 畸形 JSON（应 400）/ 布尔 true/false / 字符串 `"true"`（应拒绝）。
- 409/403/404/非 JSON 500/各类超时；MCP 取消清理。
真部署只读冒烟保留，写路径只对隔离临时 ProjectStore 跑，不碰生产库。

---

## 12. 依赖说明

新增 `mcp` + `httpx` 只进 `mcp/pyproject.toml`，**不碰 `backend/requirements.txt`**，不违反「后端新依赖先问」的约定。

---

## 13. 交付里程碑

| 阶段 | 内容 |
| :-- | :-- |
| **M0** | **后端两项扩展（§14）：改 `app.py` + `project_store.py` + `project_store_pg.py`（锁内 expected 校验 / 纯 `_plan_mint` / `transact_expected_active` / `save_component_bundle` 单事务 / bind_batch 批事务）；JSON+PG 两后端各跑回归+新行为+并发两用例测试；改后重新部署到 88.66（PG 模式）** |
| M1 | httpx 客户端 + 分级错误映射 + 只读工具（project/ontology 读/runtime 读）+ 路由契约测试 |
| M2 | 写工具（本体 import→publish→activate 链、CAD、绑定链、运维）+ 各写工具带 `expected_project_id` + `mint_instances(dry_run)` + 文件参数与校验 + Flask 集成测试 |
| M3 | skill 文件 + README（含 Claude Code / Cursor 审批配置记录）+ Claude Code 端到端联调 |
| M4 | Cursor 端验证；二期工具（transform/ue/spatial 只读）；只读冒烟；交付 |

---

## 14. 后端能力扩展（方案 B，两项，均加法式向后兼容）

原则：**只加可选字段，缺省即旧行为**；不改存储结构。但原子性必须在存储层锁内实现，故改动涉及 `app.py`（handler 透传字段）+ `project_store.py`（锁内校验 / 规划函数 / 组合事务）+ **`project_store_pg.py`（PG 子类签名同步透传）** + 测试。缺省字段时行为与改前逐字一致。

### 14.0 双实现签名平价（阻断，勿漏）
`ProjectStore` 在 `ONTOTWIN_STORE=pg` 时被 `ProjectStorePG` 替换（project_store.py:~880），后者覆盖了 `mint_instances(self)` 等写方法（project_store_pg.py:~297，无新参数）。**服务器正是 PG 模式**。因此：
- 本节新增的每个方法 / 参数（`dry_run`、`expected_project_id`、`_plan_mint`、`save_component_bundle`、`transact_expected_active`）**必须在 JSON 版与 PG 版保持接口一致**。
- 逐项核对 PG 覆盖了哪些写方法，全部同步透传新参数；PG 版验证 `transact_expected_active` 的落盘语义。
- 测试矩阵对 JSON、PG 两后端各跑一遍（PG 用容器内隔离库或 testcontainers）。

### 14.1 mint 支持 `dry_run`（抽共享纯规划函数）
- 现状：`binding_mint()`（app.py:~2643）不读 body，直接 `mint_instances()`（project_store.py:~829，一把锁内读 components/instances/spatial_profile 并改实例、刷 `last_seen`、调 `apply_instance_metadata`）。
- 存储层：把 mint 的「算」与「写」拆开 —— 抽**真正纯**的 `_plan_mint(snapshot, now) -> {to_create, to_update, result_instances}`，dry_run 与真写都调它：
  - **纯度硬要求**（Codex 提醒：深拷贝 snapshot 不够，planner 自身不能改入参）：planner 不得原地修改传入 snapshot；须逐条**深拷贝**旧实例记录再改，自行构造完全分离的 `result_instances`；`now` 在锁内**只生成一次**并传入，planner 内不再调 `time.time()`。
  - `mint_instances(dry_run=True)`：`with self._lock` 内对状态深拷贝跑 planner，返回差异，不 save。
  - `mint_instances(dry_run=False)`：同一锁内跑同一 planner，赋回并 save。
  - `will_update` 只比较**明确列出的业务字段**，排除 `last_seen`/`created_at` 等时间性字段（否则全量误报）。
- handler：`data = request.get_json(silent=True) or {}` 取 `dry_run`。兼容边界：空 body / 非 JSON → `{}` → 旧真写路径；但 `Content-Type: application/json` 且 body 非空却解析失败 → **400，不静默真写**；`dry_run` 只接受 JSON boolean，字符串 `"true"` 拒绝。
- 兼容性：Web UI 不带 `dry_run` → 真写路径，零影响。

### 14.2 写操作接受可选 `expected_project_id`（锁内原子校验）
- **必须锁内校验**：给 ProjectStore 各写方法加可选 `expected_project_id`，进 `with self._lock` 后**先核对 `_active_id`**，不符抛 `ProjectMismatch`；符合再改再存。或统一走 `transact_expected_active(expected_id, updater)`（在现有 `transact_active` project_store.py:~451 的锁内深拷贝+一次保存基础上补 expected 校验）。handler 捕获 → 409 `{"error":"project changed","expected":...,"actual":...}`。

- **完整 M1–M2 mutation 表 + 各自并发语义**（Codex #3：不能用一句「所有 persist-write」覆盖）：

  | 工具 / 路由 | 写类型 | 并发前置 |
  | :-- | :-- | :-- |
  | `create_empty_project` `/ontology/datasets` | 追加空 dataset | **不套 expected**；**MCP 固定传 `activate=false`**（后端支持 `activate=true` 会切全局激活态，禁止隐式触发） |
  | `import_ontology_csv` `/ontology/import_csv` | 全局 staging 缓存（`_custom_graph_data`），非项目级 | **不套 expected**；属全局暂存，语义由 publish 前的 staging 归属界定 |
  | `publish_ontology_dataset` `/ontology/publish` | 追加新 dataset（不写当前项目） | **不套 expected**；它凭 staging 造新集，可选校验「staging 未被他人覆盖」（staging revision，二期） |
  | `activate_project` `/ontology/datasets/activate` | 切全局激活态 | **不套「expected==当前」**（它本职就是切）；如需防呆，可选 `expected_current`（切换前当前应是谁），与 `dataset_id`（切到谁）分开 |
  | `parse_cad_dxf` `/cad/parse` | 全局 latest CAD 缓存 | 不套 expected（全局暂存） |
  | `save_components` `/coord/save_components` | 项目级（profile+frame+components） | **expected + 单事务**（见下） |
  | `upload_roster` `/binding/roster/upload` | 项目级 | expected（**multipart form field `expected_project_id`**，见下） |
  | `bind_instance` `/binding/bind` | 项目级 | expected（JSON body） |
  | `bind_instances_batch` `/binding/bind_batch` | 项目级 | expected + 批事务（见下） |
  | `unbind_instance` `/binding/unbind` | 项目级 | expected（JSON body） |
  | `mint_instances` `/binding/mint` | 项目级 | expected（JSON body） |
  | `set_instance_state` `/state/override` | 项目级（`update_raw_state`） | expected（JSON body） |

- **`save_components` 组合事务（新增 API）**（Codex #4）：现三个 setter（`set_spatial_profile` ~695 / `upsert_frame` ~738 / `set_components` ~755）各自加锁各自保存，加 expected 参数仍是三次事务。**新增** `save_component_bundle(expected_project_id, profile_patch, frame_patch, component_plan, mode)`：在一次持锁内校验 expected、读旧态（深拷贝，勿用返回内部引用的 getter）、在工作副本上完成 profile+frame+components 全部修改、**只调一次 `_save_current()`**。handler 改调它。

- **`bind_batch` 批次语义（定死）**（Codex #5）：采用**批内部分成功、单事务单保存**——一次持锁内顺序对工作副本执行每对绑定，逐条做「构件存在 + 1:1 占用」校验，失败项记入 `failed[]`，成功项写入；**全程同一项目锁、末尾只保存一次**；若无任何成功项则不保存。响应 `{bound: n, failed:[{pair, reason}]}`。MCP 侧据此不自动重试整批（非幂等）。

- **二期工具**（§3.3：`promote_model_binding`、transform PUT、writeback、spatial 写、实例创建/删除）为项目级写，开放前**逐端点**纳入 expected 保护并补进本表；本轮先覆盖 M1–M2。

### 14.3 测试与部署
- 每项：① 缺省字段 → 与改前逐字一致（回归）；② 带字段 → 新行为；③ **并发（两线程 + 同步栅栏）**。
- **并发验收拆两例**（Codex #2：锁语义决定「等待中的 activate 不会让当前写 409」）：
  - **A｜activate 先拿锁**：activate 切到 B → 后到的写校验 expected≠B → **409 拒绝**。
  - **B｜写先拿锁并通过校验**：activate 被阻塞等待 → 写**完整落在 A** → 之后才切 B。断言**绝不写到 B**（而非断言写被拒）。
- JSON、PG 两后端各跑；Flask test client + 隔离临时库，不碰生产。
- 改后重新部署到 88.66（M0）。

---

## 附：核心风险科普（TOCTOU）

本设计最硬的风险叫 **TOCTOU（Time-Of-Check to Time-Of-Use，检查时与使用时不一致）**：AI 先确认「当前是项目 A」，不代表几毫秒后写请求执行时仍是 A。**关键教训（v4→v5 修正）**：把校验和写操作放进「同一个 Flask 同步 handler」**并不等于**原子——只要二者是**两次独立加锁**（`get_active_id()` 锁一次、`bind()` 再锁一次），中间就有缝，别的请求能插进来 `activate` 切项目。唯一根除法：让**校验与写入共享同一次持锁**（下沉进 ProjectStore 的 `with self._lock`，先核对 `_active_id` 再改再存）。方案 B 的 §14.2 正是这么做的；这也是 CAS / 乐观锁 / `SELECT ... FOR UPDATE` 的同一思想——把「比较」和「交换」焊成不可分割的一步。
