# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

OntoTwin Nexus — 数字孪生本体驱动平台。单人开发项目，不要过度工程化。

---

## 常用命令

后端是单个 Flask app，前端是无构建的静态多页面（CDN 引入依赖），无需打包步骤。

```bash
# 一键启动（Docker，推荐）—— 起容器 + 等就绪 + 开浏览器
./start.ps1            # 或双击 start.bat
docker compose up -d --build      # 等价手动命令
docker compose down               # 停止
docker compose logs -f            # 看日志

# 直接跑后端（不走 Docker，需先 pip install -r backend/requirements.txt）
cd backend && python app.py       # 监听 0.0.0.0:5000，前端入口 /nexus

# Lite 模块 M0 验证（USD 导出冒烟测试，无 pytest 框架，直接 run）
python backend/lite/tests/test_hardcoded_export.py

# DXF 解析/坐标诊断辅助脚本（开发期排查用）
python backend/verify_parse.py
python backend/diag_layers.py
python backend/diag_bounds.py
```

- 服务统一在 **5000** 端口；Flask 同时托管 `frontend/` 静态文件和 `/api/...` 路由。
- 新增 Python 依赖前先问用户，并改 `backend/requirements.txt`。
- 没有 lint / 格式化工具链，也没有 JS 测试。

---

## 架构大图

### 后端（`backend/`，Flask 单体 + 独立存储模块）

`app.py`（~3600 行，77 条路由）是唯一 Flask app，挂载三类东西：页面路由（`/nexus`、`/ontology`、`/coord` 等 → 直接 `send_static_file`）、`/api/v2/...` 业务 API、以及末尾用 `register_lite_routes(app)` 挂上的 `/api/v3/lite/...`。**新功能放独立子目录/模块，不要继续往 `app.py` 里塞。**

核心数据流与模块职责：

- **`project_store.py` → `ProjectStore`（单一事实来源，v2.9.4 重构后的核心）**：一个 Project = 一个工厂/楼层场景的全部自洽数据（`object_types` 类型表 + `instances` 实例 + `calibration` 标定）。存储为一项目一文件 `data/projects/{id}.json` + `data/active.json` 记录激活态。内存中只保留「当前激活项目」一份——**唯一可见性规则：一切只认当前激活项目**。`app.py` 里 `instance_store = project_store` 是向后兼容别名，启动时 `_init_from_project_store()` 把激活项目同步进运行时内存 `_object_types`。
- **`mapping_store.py`（~3000 行）**：系统级静态定义 + 旧存储。包含 `OBJECT_TYPES`（本体类型注册表）、`INTERFACES`（两层三维能力接口 I3D_Representable + 子能力）、`MOCK_ASSETS`（ArtStudio 资产库不可达时的回退）、`MappingStore`（映射规则 → `data/mapping_rules.json`，作为配置进 git），以及 `MockInstanceSimulator`（后台线程，模拟实例状态变化）。
- **本体导入链**：`ontology_parser.py` 把图数据库导出的 6 张 CSV（`objectdef`/`linkdef`/`linksourcetype`/`linktargettype` 必须 + `propertydef`/`hasproperty` 可选）解析成 ECharts 的 `{nodes, links, categories}`。
- **CAD 坐标标定链（PRD 2.9，无状态）**：`parser_dxf.py`（ezdxf 扫描 INSERT 块 → 候选 ObjectType）→ `coord_filter_rules.py`（图层/块黑名单过滤）→ `coord_transform.py`（numpy 最小二乘求 2D 仿射矩阵，与前端 `coord_transform.js` 算法对称）。`block_asset_mapping.json` 存块名→资产 id 的预填映射。

### 前端（`frontend/`，无构建多页面）

每个 `.html` 是独立页面，由 Flask 路由直接服务，全部走 CDN，不引入构建工具。`vendor/` 放本地化的第三方库。主要页面：`nexus.html`（入口）、`ontology.html` / `ontology_graph.html`（本体编辑 + 图谱）、`instance.html`（实例）、`mapping.html`（映射规则）、`binding.html`（实例绑定台）、`coord_workbench.html`（坐标标定，路由 `/coord`）、`floor_pulse.html`（实时态势）。

### UE5 同步（`ue_project/Plugins/OntoTwinSync/`）

C++ 运行时插件，轮询 Flask 后端状态驱动 UE Actor（1.x 单实例组件 + 2.x 场景管理器/孪生实例）。`ue_project/*` 整体 gitignore，仅追踪 `Plugins/` 源码。

### 两条主线的边界（重要）

仓库里并存第二条主线「具身智能平台」（机器人训练工具链），与 Nexus 共用 Flask app 但**存储完全隔离**：

- `backend/lite/`：USD 场景导出，**独立 SQLite**（`backend/lite/db/lite.db`，所有表 `lite_` 前缀，ADR-012），API 走 `/api/v3/lite/...`。
- `frontend/scenes/`、`pgx_setup.sh`（Isaac Sim/Isaac Lab 环境）、`scripts/`、`assets/urdf_to_fbx.py` 属于这条线。

见下方协作模式：开工前先确认在哪条线，选 Nexus 时忽略并不主动提及 lite/scenes 相关内容。

---

## 编码原则

- 现有文件能不改就不改；需要改时先说明再动手。
- 新功能放独立子目录，不往 `app.py` 里塞。
- 不加异步队列 / 关系型数据库 / 权限系统。
- 新 Python 依赖先问用户；前端走 CDN，不引入构建工具。

---

## 协作模式

每次开发开始前，先询问用户当前在哪条主线工作。
- 若选 **OntoTwin Nexus**：忽略 `backend/lite/`、`frontend/scenes/` 的一切内容，不主动提及。
- 若选 **具身智能平台**：正常处理。

每个功能小步骤推进，一步一确认，遇到架构选择先列方案让用户选。

做任何前端改动前，先调用 `ontotwin-ui` skill 校验是否符合设计规范（极简黑白灰风格）。

涉及前后端或 UE 侧的新知识点，在回复**末尾**以教大学生的方式做简短科普。

---

## 禁止

- 擅自改数据库 / JSON 存储结构（`ProjectStore` 文件格式、`mapping_rules.json`、`lite_*` 表）。
- 未经确认改现有前端路由或 HTML。
- 参考 `docs/legacy/`（已废弃）。
- 复述用户已明确的决策。
