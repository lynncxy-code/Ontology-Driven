---
name: ontotwin-backend
description: OntoTwin 后端 Python/Flask 约定：模块边界与 register_*_routes 注册、API 版本（/api/v2 与 /api/v4.8）、错误处理（ApiError/领域异常统一响应）、请求上下文与鉴权（显式 project_id）、配置与数据库访问（psycopg 原生 SQL）。当新增/修改 /api 路由、后端模块、错误处理或数据库访问时使用。
---

# OntoTwin 后端规范

> 本技能是后端 Python/Flask 改动的标尺，编码「代码里已经存在的既定约定」+「业界成熟实践补强」。前端看 `ontotwin-ui`，UE 看 `ue-super-steward`，分支/发布看 `ontotwin-product-lifecycle`。
>
> 约定分两级标注：
> - **〔事实〕** = 代码里已是既定做法，必须遵循，出处见括注。
> - **〔补强〕** = 业界成熟实践，用于补代码尚未显式写出的缺口；引入新约定前先与用户对齐。

## 0. 一句话心智模型

`app.py` 是唯一 Flask 入口与「组装层」，负责建 app、注入 `project_store`、注册各模块路由；业务逻辑下沉到独立模块的 `service.py`，路由只做「解析请求 → 调 service → 转错误响应」。**新功能不再往 `app.py` 里堆。**

## 1. 模块边界（最高优先级）

- 〔事实〕`app.py` 是单入口，已膨胀到数千行，属于历史债（`01-source/backend/app.py`）。AGENTS.md 明令「新功能优先放独立模块，不继续扩大该文件」。
- 〔事实〕新模块通过一个 `register_*_routes(app, project_store, ...deps)` 函数接入，`app.py` 只 import 并调用它。现有调用点示例：`register_tenant_routes(app, project_store)`、`register_dataset_package_routes(app, project_store, ...)`、`register_overlay_routes(...)`、`register_scene_interaction_routes(...)` 等（均见 `app.py` 尾部组装段）。
- 〔事实〕注册函数有两条等价写法，任选其一、保持一致：
  1. **Blueprint 式**（推荐，`dataset_package/api.py`）：建 `Blueprint(...)`，路由挂在 blueprint 上，最后 `app.register_blueprint(blueprint)` 并返回 service。
  2. **直接 `@app` 式**（`tenant_api.py`）：`register_tenant_routes(app, ...)` 内部直接 `@app.get("/api/v4.8/...")`。
- 〔补强〕新增模块一律走上面两种；除非改的是页面路由本身，否则不要在 `app.py` 里新增 `@app.route('/api/...')`。

## 2. 标准 feature 包结构（以 `dataset_package/` 为范本）

```
<feature>/
  __init__.py     # 只做 re-export：register 函数、异常类、Service
  api.py          # 路由层（薄）：解析 request → 调 service → 转错误
  service.py      # 业务层（厚）：纯逻辑，抛领域异常
  <sub>.py        # 可选子模块（如 attachments.py / delivery.py）
```

- 〔事实〕`dataset_package/__init__.py` 只 re-export `register_dataset_package_routes`、`DatasetPackageError`、`DatasetPackageService`。
- 〔事实〕`dataset_package/api.py` 只做 request 解析与 `try/except`，业务全在 `service.py`。
- 〔补强〕**薄路由 / 厚服务**：`api.py` 禁止写业务逻辑；`service.py` 不 import flask 的 `request`（保持可单测、可复用）。
- 〔补强〕一个包只解决一个能力域；能力变大时再拆子模块，不造「万能模块」。

## 3. 依赖注入与单一事实来源

- 〔事实〕`project_store` 是项目数据的单一事实来源：`project_store = ScopedProjectStore(ProjectStore())`；`instance_store = project_store` 是向后兼容别名（`app.py` 组装段）。
- 〔事实〕模块通过 `register_*_routes(app, project_store, ...)` 的**参数**拿到依赖和回调（如 `on_import`、`asset_root`），不跨模块 import 全局单例。
- 〔事实〕4.8 请求级隔离由 `ScopedProjectStore` + `project_view(base, project_id)` 实现，按请求把「显式项目」绑定到 `g.ontotwin_project_store`（`scoped_project_store.py`、`app.py` 的 `_bind_explicit_v2_project`）。
- 〔补强〕依赖注入优先于全局单例；新增模块若需要共享状态，从 `register_*_routes` 的参数注入，而不是 `import` 一个模块级单例。
- 〔事实〕禁止绕过 `project_store` 直写存储/直写库；迁移冻结守卫（`ProjectMigrationFrozenError`）就是为此存在，所有写路径都要经过它。

## 4. API 版本与路由

| 前缀 | 用途 | 状态 |
| :--- | :--- | :--- |
| `/api/v2/*` | 业务 API（本体/实例/标定/绑定/UE…） | 稳定，继续用 |
| `/api/v4.8/*` | 4.8 租户/账号/组织/显式项目上下文 | 新功能归属地 |
| `/api/state`、`/api/update` | 1.x 遗留 | 冻结，不再扩展 |
| 页面路由（`/`、`/account`、`/nexus`…） | `send_static_file('xxx.html')` | 只加壳不改版 |

- 〔事实〕`/api/v4.8/*` 由 `tenant_api.py` 的 `register_tenant_routes` 提供；`/api/v2/*` 由各 feature 模块 + `app.py` 里遗留的内联路由提供。
- 〔补强〕新业务端点优先 `/api/v2/*`（沿用既有命名）；新的身份/租户/上下文端点走 `/api/v4.8/*`；不要发明第三个版本前缀。
- 〔事实〕`app.json.ensure_ascii = False`（`app.py`），中文直接输出、不转 `\uXXXX`。

## 5. 错误处理约定

- 〔事实〕领域异常类（各自模块定义或复用）：
  - `ApiError(status, message, code, **extra)` —— 4.8 通用（`tenant_api.py`）。
  - `DatasetPackageError(code, message, status?, details?)` —— 数据集包（`dataset_package/service.py`）。
  - `ProjectMismatch`、`ProjectMigrationFrozenError`、`FloorProfileError`、`SpatialFrameValidationError` —— 跨域（`app.py` 顶部 import）。
- 〔事实〕错误响应统一形状：`{"error": <机器码>, "message": <中文提示>, ...extra}` + HTTP 状态码。机器码稳定、可程序判断；message 给用户看。
- 〔事实〕三种兜底方式，按场景选用：
  1. **`@_api` 装饰器**（`tenant_api.py`）：捕获 `ApiError` → 统一 JSON；捕获未知异常 → `503 {"error":"storage_unavailable"}`。推荐新 4.8 路由复用此模式。
  2. **路由内 `try/except`**（`dataset_package/api.py`）：`except DatasetPackageError → error_response(exc)`。
  3. **全局 `@app.errorhandler`**（`app.py`：`ProjectMigrationFrozenError` → 409）—— 给跨模块、非请求局部的领域错误。
- 〔补强〕异常优先于布尔/错误码返回值：业务失败 `raise` 领域异常，不要 `return (False, msg)` 让上层猜。
- 〔补强〕不返回裸 500、不吞异常静默；确属未知故障用 503 + 机器码 `storage_unavailable` / `database_unavailable` 兜底（见 `@_api`）。

## 6. 请求上下文与鉴权

- 〔事实〕`@app.before_request` `_bind_explicit_v2_project()`（`app.py`）：把每个 `/api/v2/*` 请求绑到显式 `project_id`，写入 `g.ontotwin_project_store` / `g.ontotwin_project_id`，避免多标签页/多场景串写。
- 〔事实〕身份来源：会话 cookie `ontotwin_session`、头 `X-OntoTwin-Session`；UE 身份头 `X-OntoTwin-UE-Project-Id`、`X-OntoTwin-UE-Scene-Id`；显式项目头 `X-OntoTwin-Project-Id`。
- 〔事实〕鉴权语义（PG 运行时）：
  - 无身份访问 `/api/v2/*` → 401 `auth_required`；
  - 有身份但缺 `project_id` → 400 `project_id_required`；
  - 有身份但无项目访问权/编辑权 → 403 `forbidden`；
  - UE 场景与项目不匹配 → 403 `ue_project_mismatch`。
- 〔事实〕不要把浏览器会话的项目选择写回进程级 `app_singleton.active_project_id`（`tenant_api.py` 模块 docstring 明示）。
- 〔补强〕新增有状态业务端点必须复用这条显式 project_id 链路，禁止再引入「全局激活项目」这种隐式状态。

## 7. 配置与数据库访问

- 〔事实〕配置一律环境变量 + 默认值：`ONTOTWIN_STORE`、`ONTOTWIN_RELEASE_ID`、`ONTOTWIN_MOCK_SIMULATOR_ENABLED`、`ARTSTUDIO_BASE_URL/TOKEN/TIMEOUT` 等（`app.py`、`tenant_api.py`）。
- 〔事实〕数据库访问走 `from db import pg`（`db/pg.py`，psycopg3 原生 SQL、无 ORM）；图库走 `from db import graph`（`db/graph.py`）；JSON 列用 `psycopg.types.json.Jsonb`（`tenant_api.py`）。
- 〔事实〕schema 版本由 `CURRENT_SCHEMA_VERSION` 标记；表结构在 `db/schema.sql`（`db/schema.sql`）。
- 〔事实〕**新增表/字段必须进 `db/schema.sql`**，且当前 schema 只在空数据卷 initdb 时执行一次——存量库需要迁移（见 `ontotwin-db-migration` 技能，待补）。
- 〔补强〕SQL 集中在 service/store 层，路由层不拼 SQL；写操作尽量单事务、可重试。
- 〔事实〕项目约束：不引入异步队列、ORM、权限框架、前端构建工具；新增 Python 依赖先确认并更新 `requirements.txt`。

## 8. 禁止清单

- 不往 `app.py` 堆新 `@app.route('/api/...')`。
- 不在 `api.py` 写业务逻辑。
- 不绕过 `project_store` 直写存储或直连库。
- 不引入全局「激活项目」隐式状态（用显式 project_id）。
- 不返回裸 500 / 不吞异常。
- 不新增依赖未经确认、不更新 `requirements.txt`。
- 不未经确认改 `ProjectStore` 文件格式、`mapping_rules.json` 或其它存储结构。

## 9. 改动自检（提交前）

- 〔事实〕`python -m py_compile <改动的模块>`、`git diff --check`。
- 〔补强〕新端点至少覆盖：正常路径 + 一个错误路径（401/403/400/404 选一）。
- 〔补强〕新模块落地即用 `register_*_routes(app, project_store, ...)` 接入 `app.py`，并确认只 import 一次、只注册一次。
