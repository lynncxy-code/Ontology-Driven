# AGENTS.md

OntoTwin Nexus 是本体驱动的数字孪生平台。项目由单人维护，避免过度工程化。

## 常用命令

后端是单个 Flask 应用，前端是无构建的静态多页面。

```powershell
./start.ps1
docker compose up -d --build
docker compose down
docker compose logs -f

cd 01-source/backend
python app.py

python 01-source/backend/verify_parse.py
python 01-source/backend/diag_layers.py
python 01-source/backend/diag_bounds.py
```

- 服务统一使用 5000 端口；Flask 同时托管 `01-source/frontend/` 与 `/api/...` 路由。
- 新增 Python 依赖前先征得用户确认，并更新 `01-source/backend/requirements.txt`。
- 项目没有前端构建步骤，也没有统一的 lint 或 JavaScript 测试链。

## 架构

### 后端

- `01-source/backend/app.py`：Flask 入口，提供页面路由和 `/api/v2/...` API。新功能优先放独立模块，不继续扩大该文件。
- `01-source/backend/project_store.py`：项目数据的单一事实来源。一个项目包含类型、实例和标定信息；系统只展示当前激活项目。
- `01-source/backend/mapping_store.py`：本体类型、三维能力接口、映射规则和模拟器。
- `01-source/backend/ontology_parser.py`：把图数据库导出的 CSV 转换为本体图数据。
- `01-source/backend/parser_dxf.py`、`coord_filter_rules.py`、`coord_transform.py`：CAD 解析、过滤和坐标标定链路。

禁止未经确认更改 `ProjectStore` 文件格式、`mapping_rules.json` 或其他存储结构。

### 前端

`01-source/frontend/` 是由 Flask 直接托管的独立 HTML 页面，依赖通过 CDN 或 `vendor/` 引入。主要页面包括 Nexus 入口、本体编辑、实例管理、映射、绑定、坐标标定和实时态势。

任何前端改动前，先使用 `ontotwin-ui` 规范检查极简黑白灰风格、组件和交互一致性。未经确认不要修改现有路由或 HTML。

### UE5 同步

`01-source/ue_project/Plugins/OntoTwinSync/` 是 UE5.6 运行时插件，轮询 Flask 后端并驱动场景 Actor。`01-source/ue_project/*` 默认忽略，只跟踪插件源码。

## 协作原则

- 处理编号统一使用 `BUG-xx`（缺陷修复）、`OPT-xx`（体验优化）、`NEW-xx`（新增功能），各类别分别连续编号，至少两位数字；分配前检查已有编号，避免重复。后续不再新增 `FIX-日期-序号` 编号，历史编号保留以便追溯。
- **主动推进与持续跟进**：当用户明确表达开展新工作或修复现有问题的意图时，应根据用户指令和已有上下文推断真实任务范围，主动采取必要的只读检查、隔离工作区、实现、测试和交接行动，并持续推进直到目标真正完成。不要仅因为存在可选方案、信息尚未完全确定或出现普通执行阻碍就主动停下；应先采取安全的最小行动并报告关键分支。只有在操作明显具有破坏性或不可逆、或缺少会实质改变结果的必要授权时，才暂停并向用户确认。
- 小步骤推进并逐步确认；遇到架构选择先列出方案。
- 尽量减少对现有文件的修改，新能力放独立目录或模块。
- 不引入异步队列、权限系统或前端构建工具。
- 不参考 `docs/legacy/`。
- 不复述用户已明确的决定。
- 涉及前后端或 UE 的新知识点时，在回复末尾做简短科普。
