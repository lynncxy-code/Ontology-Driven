# CLAUDE.md

OntoTwin Nexus 是本体驱动的数字孪生平台。项目由单人维护，避免过度工程化。

## 常用命令

```powershell
./start.ps1
docker compose up -d --build
docker compose down
docker compose logs -f

cd backend
python app.py

python backend/verify_parse.py
python backend/diag_layers.py
python backend/diag_bounds.py
```

- 服务统一使用 5000 端口；Flask 同时托管静态前端和 `/api/...`。
- 新增 Python 依赖前先征得用户确认，并更新 `backend/requirements.txt`。
- 前端无构建步骤，项目没有统一 lint 或 JavaScript 测试链。

## 架构边界

- `backend/app.py` 是 Flask 入口。新功能放独立模块，不继续扩大该文件。
- `backend/project_store.py` 是项目数据的单一事实来源；系统只认当前激活项目。
- `backend/mapping_store.py` 管理本体类型、三维能力接口、映射规则和模拟器。
- `backend/ontology_parser.py` 负责本体 CSV 导入。
- `backend/parser_dxf.py`、`coord_filter_rules.py`、`coord_transform.py` 组成 CAD 坐标标定链路。
- `frontend/` 是由 Flask 直接托管的无构建多页面。
- `ue_project/Plugins/OntoTwinSync/` 是 UE5.6 同步插件源码。

## 工作原则

- 禁止未经确认更改 `ProjectStore` 文件格式、`mapping_rules.json` 或其他存储结构。
- 未经确认不要修改现有前端路由或 HTML。
- 前端改动前使用 `ontotwin-ui` 规范检查视觉与交互一致性。
- 小步骤推进；架构选择先给方案。
- 不引入异步队列、权限系统或前端构建工具。
- 不参考 `docs/legacy/`，不复述用户已明确的决定。
- 涉及前后端或 UE 的新知识点时，在回复末尾做简短科普。
