# OntoTwin 2.9.1 + 2.9.2 合并实施记录

> **作用：** 给后续接手者（或自己几个月后）看的"工程笔记"。沉淀本次实施的关键决策、改动位置、测试结果与已知限制，避免重新读两份 PRD 才能上手。
>
> **关联 PRD：**
> - `docs/PRD/OntoTwin 2.9.2 CAD本体类型自动建库需求说明书 (PRD).md`
> - `docs/PRD/OntoTwin 2.9.1 CAD实体批量入实例库需求说明书 (PRD).md`
>
> **完工状态：** 全部里程碑 ✅ 后端通过 curl 完整测试；前端通过 `node --check` 语法校验。浏览器端真实点击验证由用户自行完成。

---

## 1. 两模块的关系（看代码前先看这里）

```
                 用户上传 DXF（"新块.dxf"）
                         │
                         ▼
   ┌─────────────────────────────────────────────────┐
   │ ① 上传                                          │
   │ ② 类型审核   ← 2.9.2 主战场（建 ObjectType）    │
   │ ③ 标定                                          │
   │ ④ 实体                                          │
   │ ⑤ 导出 + ★投入实例库  ← 2.9.1 主战场（建 Instance）│
   └─────────────────────────────────────────────────┘
                         │
                         ▼
                  /instance（实例运维监控中心）
                  /ontology_graph（语义图谱总览）
```

- **2.9.2 解决"类型不存在"问题**：CAD 里的 block_name 在本体库里没对应类型，所以建不了实例
- **2.9.1 解决"类型有了但实例没投"问题**：用 2.9.2 建好的 ObjectType 把 CAD 实体投入 InstanceStore

**先 2.9.2，后 2.9.1，不可颠倒。**

---

## 2. 完成情况一览

### 2.9.2 — CAD 本体类型自动建库

| M | 任务 | 关键产出 |
| :-: | :--- | :--- |
| M0 | 前置改造（新建空数据集）| `POST /api/v2/ontology/datasets` + ontology_graph.html "+ 新建空数据集"按钮 |
| M1 | 后端骨架（过滤 + scan）| `coord_filter_rules.py` + `parser_dxf.extract_block_candidates()` + `POST /coord/types/scan` |
| M2 | 审核 UI 骨架 | CAD 步骤条改 4→5 + 新 step2 panel + 候选列表渲染 |
| M3 | commit 后端 | `commit` (publish/merge) + `check_conflicts` + `check_coverage` + 副作用预检 |
| M4 | commit UI | header 激活集指示 + 写入策略 + 冲突弹窗 + 副作用警告 + 双出口 |
| M5 | 边界 + 联调 | edge case 测试 + 状态机审计 + 联通验证 + 清理 |

### 2.9.1 — CAD 实体批量入实例库

| N | 任务 | 关键产出 |
| :-: | :--- | :--- |
| N1 | 后端 `/spawn_instances` | dry-run + commit + 三态校验 + 四态分类 + 三策略 |
| N2 | CAD Step5 投入按钮 | `spawnInstances()` + 四态弹窗 + 成功面板 |
| N3 | 图片模式 import 补全 | `importToInstanceLib()` 复用同一接口 |
| N4 | curl 端到端测试 | 全部 9 条断言通过 |

共 **29 个原子任务**（M0-M5 共 25 + N1-N4 共 4），TaskCreate/TaskUpdate 全程可追溯。

---

## 3. 文件改动清单

### 后端

| 文件 | 类型 | 说明 |
| :--- | :-: | :--- |
| `backend/coord_filter_rules.py` | 🆕新建 | 图层/块名/灰色地带规则，独立模块便于维护 |
| `backend/parser_dxf.py` | ✏️扩展 | `extract_block_candidates(file, mapping)` 函数 (~105 行) |
| `backend/app.py` | ✏️扩展 | 8 个新路由 + 7 个 helper 函数 + activate_dataset 重构 |

**app.py 新增的路由（全部 `/api/v2/`）：**

```
POST   /ontology/datasets             # 新建空数据集（M0）
POST   /coord/types/scan              # DXF 扫描候选 ObjectType（M1）
POST   /coord/types/check_conflicts   # rid 冲突检查（M3）
POST   /coord/types/check_coverage    # 跳过此步前的覆盖率检查（M3）
POST   /coord/types/commit            # publish/merge 双模式提交（M3）
POST   /coord/spawn_instances         # 批量入实例库 dry-run/commit（2.9.1 N1）
```

**app.py 新增的 helper 函数：**

```
_project_dataset_to_object_types(ds)      # 数据集 → _object_types 投影（含 4 行修复）
_detect_dangling_refs(rids)               # 找出会让实例悬空的 rid
_item_to_node(item, source_file)          # commit item → 数据集 node
_write_back_asset_mapping(items)          # asset_id 回写 block_asset_mapping.json
_commit_publish / _commit_merge           # commit 路由的两个子流程
_derive_instance_id(item, rid)            # instance_id 推导（EQUIP_ID/hash）
_find_rid_in_other_datasets(rid)          # 三态校验中的"未激活集"查找
_has_real_coord(raw_state)                # 判断 "translation 全为 0"
```

### 前端

| 文件 | 类型 | 说明 |
| :--- | :-: | :--- |
| `frontend/ontology_graph.html` | ✏️扩展 | "+ 新建空数据集"按钮 + JS（~60 行） |
| `frontend/coord_workbench.html` | ✏️大改 | 步骤条 4→5；新增 step2 类型审核 panel；写入策略 UI；冲突/副作用/成功弹窗群；Step5 ★投入实例库；图片模式 import 重写 |

**State 字段新增**：

```js
// State (CAD 模式)
scanResult, auditChecked, auditName, auditAsset, lastUploadedFile  // M2 类型审核
activeDsId, activeDsName, datasetList                                // M4 数据集状态
```

**步骤条 renumber 映射**（接手时要知道）：

```
旧编号                 新编号             含义
step1 (上传)        →  step1 (上传)
                       step2 (类型审核) ← 新增
step2 (标定)        →  step3 (标定)
step3 (实体)        →  step4 (实体)
step4 (导出)        →  step5 (导出)
```

JS 中 `goToStep(N)` / `State.currentStep` 的数字含义全部按新编号。`btnToStep3` 同步重命名为 `btnToStep4`。

---

## 4. 关键设计决策（落地版）

| 决策 | 选项 | 原因 |
| :--- | :--- | :--- |
| ObjectType 数据结构 | **保持现有平铺结构**，只加 `source` 字段 | CLAUDE.md "保守修改"。嵌套结构会触发链式改动；CAD 不需要类型级特殊默认值 |
| 接口属性默认值来源 | 仍由 `INTERFACES` 表统一提供 | 与现有实例 spawn 逻辑兼容 |
| `injected_interfaces` 默认值 | `["I3D_Representable", "I3D_Spatial"]` | CAD 设备必有 3D 表达 + 空间坐标；其他接口用户自行注入 |
| `asset_id` 双轨同步 | mapping 是种子，ObjectType.asset_id 是权威值 | 避免"mapping 改动反向污染已存类型"的幽灵改动 |
| 跨数据集 rid 唯一性 | **不强制全局唯一** | 多数据集独立存在；激活时以激活集为准 |
| `_object_types` 写入路径 | 必须经数据集体系（publish/merge）| 不允许 2.9.2 绕过数据集直接写 `_object_types`，否则切数据集会丢失 |
| Demo 数据集 | 只读，不能作为 merge target | 系统初始状态保护 |
| 数据集激活默认行为 | publish 后默认激活 | M4 故事 3 推荐路径 |
| 副作用警告触发 | publish + 默认激活 / merge + target==active | 任何会刷新 `_object_types` 的操作都检查 |
| instance_id 推导 | `EQUIP_ID` > 自动 `<rid>-<hash6>` | 用户提供 ID 优先；缺失也能批量入库 |
| `to_update_coord_only` 判定 | 同 ID 实例存在且 translation 全为 0 | 兼容 PRD 2.3.1（MES 预注册无坐标） |
| Z 坐标 | 固定 `0`，不支持 3D 高程 | PRD 已知限制；未来 M 演进 |
| Flask JSON 中文 | `app.json.ensure_ascii = False`（Flask 2.2+ 语法）| `JSON_AS_ASCII` 已废弃 |
| DXF 编码 | `ezdxf` 自动处理 GBK → unicode，无需转码 | 验证过 doc.encoding == 'gbk' |

### activate_dataset 的 4 行修复

```python
# 修改前（仅从 old 取）
"color":               old.get("color", "#888888"),
"injected_interfaces": old.get("injected_interfaces", []),
"asset_id":            old.get("asset_id"),
"mock_instances":      old.get("mock_instances", []),

# 修改后（node 自带优先 fallback old/默认）
"color":               node.get("color")               or old.get("color", "#888888"),
"injected_interfaces": node.get("injected_interfaces") or old.get("injected_interfaces", []),
"asset_id":            node.get("asset_id") if node.get("asset_id") is not None else old.get("asset_id"),
"mock_instances":      node.get("mock_instances", [])  or old.get("mock_instances", []),
```

**向后兼容性：** 对 CSV 导入的旧数据集（node 没有这些字段）行为完全不变；2.9.2 commit 的新数据集（node 自带字段）能正确读取。

---

## 5. PRD 漏洞修正落地表

实施过程中识别并修复了 11 个 PRD 设计漏洞，全部落地：

| # | 漏洞描述 | 修复实现位置 |
| :-: | :--- | :--- |
| 1 | publish + 默认激活会让实例引用悬空 | `_detect_dangling_refs` + `confirmDanglingWarning` |
| 2 | "合并"语义不清（双向 union？合并后原集是否存在？）| § 10.3 单向追加 + 同名 CAD 优先 + 原集保留 |
| 3 | asset_id 双轨可能不一致 | mapping 仅作种子；ObjectType 写入即权威 |
| 4 | 2.9.1 校验"在哪儿存在"未说清 | 三态：在激活集 / 在未激活集 / 完全没有 |
| 5 | 多 CAD 累积失忆（每次激活替换）| 推荐"先建空集再 merge"路径 + UI 智能默认 merge |
| 6 | Demo 只读，首次 commit 无合并目标 | "立即新建空数据集"快捷按钮（quickCreateWorkDs） |
| 7 | publish/merge 冲突弹窗语义混乱 | 拆 `in_target_dataset`（merge 真冲突）/ `in_other_datasets`（publish 信息提示）|
| 8 | merge 到 active 集也会引发副作用 | 副作用预检扩展到 merge 模式 |
| 9 | "跳过此步"没有覆盖率检查 | `skipAudit()` + `/check_coverage` 三态弹窗 |
| 10 | 第一次跑 active=Demo 没快捷入口 | Demo 检测时 UI 直接给一键按钮 |
| 11 | 数据集重名无提示 | publish 模式 409 拦截 + 前端"改名/合并到那个"对话 |

---

## 6. 数据载体最终关系图

四个数据载体的角色（任何人接手必看）：

| 载体 | 持久化 | 谁写 | 谁读 |
| :--- | :-: | :--- | :--- |
| `block_asset_mapping.json` | ✅ JSON 文件 | 2.9 工作台 / 2.9.2 commit | 2.9 工作台 / 2.9.2 scan |
| `_datasets`（数据集列表）| ❌ 内存 | 2.9.2 commit / CSV/API 导入 / 新建空集 | 语义图谱 / 激活操作 / check_conflicts |
| `_object_types` | ❌ 内存 | **被动**——由激活操作触发，从激活数据集投影 | 实例运维 / 2.9.1 spawn / 本体注入 |
| `InstanceStore` | ❌ 内存 | 2.3.1 / 2.9.1 spawn_instances / 手动 spawn | 实例运维 / UE 同步 |

**关键不变量：** `_object_types` 不是权威源，它是 `_datasets[active]` 的投影。任何修改 `_object_types` 的操作都必须通过数据集体系（避免切换数据集时丢改动）。

---

## 7. 端到端测试矩阵

### 2.9.2 后端测试（M3-T5 + M5-T1）

| 测试场景 | 期望 | 结果 |
| :--- | :--- | :-: |
| scan 真实 DXF（260 块 / 7239 INSERT）| 145 候选 / 732 系统块 / 1663 XREF | ✅ |
| 红警告（0 图层）默认不勾选 | 15 个 / 0 勾选 | ✅ |
| 黄警告（0XX*）默认勾选 | 4 个 / 4 勾选 | ✅ |
| publish 模式 | 200 + 数据集创建 + 5 写入 + 2 asset 回写 | ✅ |
| publish 重名 | 409 + existing_id | ✅ |
| publish 默认激活 → `_object_types` 替换 | count: 5 + source/asset/interfaces 保留 | ✅ |
| merge skip 策略 | 同名保留老定义 / 新 rid 追加 | ✅ |
| merge overwrite 策略 | 同名以 CAD 为准 | ✅ |
| 副作用预检（实例引用 + overwrite）| pending_warnings + dangling_refs 列表 | ✅ |
| force=true 后真写入 | overwritten=1 | ✅ |
| check_coverage 三态返回 | covered/missing/samples | ✅ |
| 边界 case（空 items / 未知 mode / Demo target / 不存在 target / 未知 strategy） | 全部 400/404 | ✅ |

### 2.9.1 后端测试（N4）

| 测试场景 | 期望 | 结果 |
| :--- | :--- | :-: |
| dry-run 四态分类（3 new / 1 update / 1 conflict / 2 errors）| 摘要正确 | ✅ |
| `update_coord` 策略 | PRE-001(0,0)→(130,240) / CNC-X(999,888)→(150,260) | ✅ |
| `skip` 策略 | 现有不变 | ✅ |
| `duplicate` 策略 | 全部加 -2 后缀，实例数从 5→10 | ✅ |
| `type_not_found` 错误 | hint="请先 2.9.2 创建" | ✅ |
| `type_not_in_active_dataset` 错误 | hint="存在于 X 数据集" | ✅ |
| instance_id 推导：EQUIP_ID 优先 | CNC-NEW-A 来自 attribs | ✅ |
| instance_id 推导：缺失 → hash6 | AGV-781838 等 | ✅ |
| 应用变换矩阵 | (10,20) + [[1,0,100],[0,1,200]] → (110,220) | ✅ |
| rotation_z 写入 | 90°/45° 正确 | ✅ |

### 联通验证（M5-T3）

| 检查项 | 结果 |
| :--- | :-: |
| 旧 `/api/v2/coord/mapping` GET/POST 仍正常 | ✅ |
| 旧 `/api/v2/coord/calibrate` 仍正常 | ✅ |
| `/api/v2/instances` GET/POST 仍正常 | ✅ |
| `/api/v2/ontology/types` GET 仍正常 | ✅ |
| 数据集激活后 _object_types 投影正确（含 4 行修复）| ✅ |

---

## 8. API 路由总清单（新增 + 现有相关）

```
新增（2.9.2 + 2.9.1）：
  POST /api/v2/ontology/datasets               新建空数据集
  POST /api/v2/coord/types/scan                DXF 扫描候选
  POST /api/v2/coord/types/check_conflicts     rid 冲突检查
  POST /api/v2/coord/types/check_coverage      跳过覆盖率检查
  POST /api/v2/coord/types/commit              publish/merge 提交
  POST /api/v2/coord/spawn_instances           批量入实例库

复用（2.9 + 2.2 + 2.3）：
  POST /api/v2/coord/preview                   DXF 图层+几何预览（2.9）
  POST /api/v2/coord/calibrate                 仿射变换求解（2.9）
  POST /api/v2/coord/export                    JSON 导出（2.9）
  GET/POST /api/v2/coord/mapping               块名→资产映射读写（2.9）
  GET/POST /api/v2/ontology/datasets           数据集列表/新建
  POST /api/v2/ontology/datasets/activate      激活数据集
  GET  /api/v2/ontology/types                  当前激活集投影 _object_types
  GET/POST /api/v2/instances                   实例列表/创建
```

---

## 9. 验证步骤（给后续接手者）

```bash
# 1. 启动后端
cd backend
python app.py

# 2. 浏览器打开
http://localhost:5000/coord

# 3. 完整流程演练
#    a) header 应显示"📊 当前激活：标准实践（内置 Demo）"
#    b) 上传 backend/新块.dxf（项目目录里有真实测试文件）
#    c) 自动进入 ② 类型审核 — 看到 145 个候选 + 红/黄警告 + 系统过滤明细
#    d) 写入策略区因 active=Demo 显示快捷按钮 — 点"立即新建空数据集'我的工厂本体'并激活"
#    e) 自动切到 merge 模式；勾选若干设备，点"提交"
#    f) 弹冲突信息（半球摄像头等可能在 Demo 集也有）— 确认
#    g) 成功面板 — 点"继续标定"
#    h) ③ 标定：在画布上点 3-4 个锚点，填 UE 坐标 → 点"计算变换"
#    i) ④ 实体：勾选要导出的实体
#    j) ⑤ 导出：点"★ 投入实例库" — 弹四态弹窗 — 确认
#    k) 跳转 /instance — 看到刚投入的实例
```

---

## 10. 已知限制 & 待办

### 已知限制（与 PRD 11/12 节一致）

1. **不持久化** — `_datasets` / `_object_types` / `InstanceStore` 均在内存，服务重启丢失
2. **2D 坐标** — Z 固定 0；rotation 仅绕 Z 轴
3. **过滤规则硬编码** — 改 `coord_filter_rules.py` 需重启
4. **图片模式不解析图层** — 2.9.2 仅 CAD 适用；图片模式继续走"下拉选 type"
5. **PRD 2.3.1 联动** — 自动走 `to_update_coord_only` 路径（坐标全 0 视为待部署），但若 MES 实例坐标非 0 则归冲突

### 待办（M+ 路线）

- [ ] **GDFGHFDHJHJ 类边界处理**：被过滤的 block_name 用户可手动恢复（PRD § 14 第 1 项隐含需求）
- [ ] **持久化方案** — 与现有本体体系一并迁移到 JSON/SQLite
- [ ] **跨页面同步** — 现状靠 hint 提示手动刷新；后续可用 BroadcastChannel 自动同步
- [ ] **header 切换数据集** — 当前用 prompt() 实现，应改为下拉/抽屉
- [ ] **批次撤销** — `spawn_instances` 返回 batch_id 用于一键撤销整批
- [ ] **AGV 路径线投入** — 识别 POLYLINE 在 AGV 图层 → 建 AGVRoute 实例（衔接 PRD 2.8）

### 浏览器端未做的形式验证（用户需自测）

- 完整闭环流程（上传 → 类型审核 → 标定 → 实体 → 投入实例 → /instance 可见）
- 步骤前进/回退时的状态保持
- 重新上传 DXF（点"重新开始"后）的 State 清理
- 三种冲突弹窗的 UI 渲染
- 副作用警告弹窗的 UI 渲染

---

## 11. 关键代码定位（快速跳转表）

| 想看什么 | 文件 + 行号附近 |
| :--- | :--- |
| 过滤规则 | `backend/coord_filter_rules.py` 全文 |
| DXF 扫描入口 | `backend/parser_dxf.py::extract_block_candidates` |
| commit publish 流程 | `backend/app.py::_commit_publish` |
| commit merge 流程 | `backend/app.py::_commit_merge` |
| 副作用预检 | `backend/app.py::_detect_dangling_refs` |
| activate_dataset 4 行修复 | `backend/app.py::_project_dataset_to_object_types` |
| asset 回写 | `backend/app.py::_write_back_asset_mapping` |
| spawn_instances 主体 | `backend/app.py::coord_spawn_instances` |
| instance_id 推导 | `backend/app.py::_derive_instance_id` |
| 类型审核 UI | `frontend/coord_workbench.html::renderAuditList` |
| 写入策略 UI 切换 | `frontend/coord_workbench.html::refreshStrategyUI` |
| 一键新建工作集 | `frontend/coord_workbench.html::quickCreateWorkDs` |
| 跳过此步检查 | `frontend/coord_workbench.html::skipAudit` |
| commit 主流程 | `frontend/coord_workbench.html::doCommit` |
| 冲突弹窗 | `frontend/coord_workbench.html::confirmMergeConflict` |
| 副作用弹窗 | `frontend/coord_workbench.html::confirmDanglingWarning` |
| 投入实例库（CAD）| `frontend/coord_workbench.html::spawnInstances` |
| 投入实例库（图片）| `frontend/coord_workbench.html::importToInstanceLib` |
| 四态弹窗 | `frontend/coord_workbench.html::spawnConfirmDialog` |
