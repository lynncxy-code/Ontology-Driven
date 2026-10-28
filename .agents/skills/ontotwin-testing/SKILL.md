---
name: ontotwin-testing
description: OntoTwin 后端测试纪律（pytest）：运行方式、conftest 隔离 fixture（tmp_data/store/client/isolated_default_trash）、测试命名与组织、覆盖要求（正常路径 + 401/403/400/404 错误路径）、验收/回归夹具前缀（ACCEPT48_/BUG01_）。当写后端测试、跑回归、验证 4.8 鉴权或验收脚本时使用。
---

# OntoTwin 测试规范

> 后端测试用 pytest。核心红线只有一条：**测试绝不碰真实 `backend/data`、真实数据库、真实 UE 状态**——全部用隔离 fixture 或 `ONTOTWIN_TEST_PG_URL` 指到测试库。

## 0. 运行方式

- 〔事实〕工作目录必须是 `01-source/backend/`，因为 `app.py` 用无包顶层 import（`conftest.py` docstring 明示）：

```powershell
cd 01-source/backend
python -m pytest -q                     # 全量
python -m pytest tests/test_x.py -q     # 单文件
python -m pytest tests/test_x.py::test_foo -q   # 单测
```

- 〔事实〕历史全量基线约「476 passed, 4 skipped」（验收文档），但**该数字必须与本次提交关联**才有效，不要拿旧数字当新证据。

## 1. 隔离原则（最高优先级）

- 〔事实〕`conftest.py` 提供四个 fixture，测试只准用它们，不碰真实数据：
  - `tmp_data` —— 临时数据根目录，测试结束自动 `shutil.rmtree` 清理。
  - `store` —— 已激活的隔离 `ProjectStore`，含 1 个类型（rid=PE16A）+ 2 个已绑定构件（DW-001/DW-002）。
  - `client` —— Flask test client，`app.project_store` / `app.instance_store` 已重定向到隔离 store。
  - `isolated_default_trash` —— autouse，把默认回收站也指到临时目录。
- 〔事实〕隔离手段：`monkeypatch` 把 `project_store._DATA_DIR / _PROJECTS_DIR / _ACTIVE_FILE` 全部指到临时目录；PG 则用环境变量 `ONTOTWIN_TEST_PG_URL` 注入测试库，未设置时走 JSON fallback（`conftest.py`）。
- 〔补强〕测试必须是确定性的：不依赖执行顺序、系统时间、网络、`sleep`；每个测试独立可单独跑。

## 2. 命名与组织

- 〔事实〕`tests/test_<模块>.py`，一个 backend 模块对应一个测试文件（当前 61 个文件，覆盖各模块）。
- 〔事实〕测试函数 `test_*`，集合类 `Test*`。
- 〔补强〕文件名与 `01-source/backend/` 下的模块名对齐（`test_dataset_package.py` ↔ `dataset_package/`、`test_migration_assembly.py` ↔ 迁移组装），找起来不迷路。

## 3. 覆盖要求

- 〔补强〕每个端点/写路径至少覆盖：**正常路径 + 一个错误路径**。
- 〔事实〕4.8 鉴权矩阵是验收重点（`ontotwin-backend` 第 6 节 + 验收文档 BUG-01），必须覆盖：
  - 匿名访问 `/api/v2/*` → 401 `auth_required`
  - 有身份但缺 `project_id` → 400 `project_id_required`
  - 跨组织读 → 403 `forbidden`
  - 无 edit 权限写 → 403 `forbidden`
  - UE 场景与项目不匹配 → 403 `ue_project_mismatch`

## 4. 验收/回归夹具前缀

- 〔事实〕在线回归/验收夹具统一带前缀，且**只处理带前缀的夹具，不碰真实数据**（验收文档）：
  - 组织/工厂/项目：`ACCEPT48_20261027_*`、`BUG01_20261027_ORG_B / FACTORY_B / PROJECT_B`
  - 账号：`bug01_viewer_20261027` 这类带日期与用途的可辨识名。
- 〔补强〕任何验收脚本创建的夹具都要可枚举、可清理（清范围只针对本批前缀，不跑全局 purge）。

## 5. 业界成熟实践（补强）

- **AAA 结构**：Arrange（准备）→ Act（执行）→ Assert（断言），三段分明。
- **一个测试只断言一个行为**：错误码、副作用、返回结构分开测，避免一条测试既测 401 又测写入。
- **fixture 不共享可变状态**：需要新状态就新 fixture，不往 `store` 里塞全局可变数据。
- **慢测试/集成测试与单元测试分离**：当前未区分，新增外部依赖（真实 PG/Neo4j/网络）的测试应标记或独立目录，不进默认全量。
- 失败信息要有上下文：断言带消息，别只 `assert x`。

## 6. 禁止清单

- 不碰真实 `backend/data`、真实数据库、真实 UE 工程。
- 不在测试里 `sleep`、发真实网络请求、依赖外部服务在线。
- 不写依赖执行顺序的测试（`-p no:randomly` 也不该救它）。
- 不把一次性验收脚本混进 `tests/`（那是脚本，不是回归用例）。
- 不拿旧「476 passed」当本次提交的验证证据——每次跑都要关联到当前 commit。

## 7. 自检

- 〔事实〕改完先跑相关测试文件，再跑全量 `python -m pytest -q`。
- 〔事实〕新增/改动后端模块同时 `python -m py_compile <模块>` + `git diff --check`。
- 〔补强〕新增端点必有对应测试；4.8 改动必补鉴权矩阵里对应的一条。
