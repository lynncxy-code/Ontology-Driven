# EXISTING_CODEBASE_MAP.md — 现有代码库地图

> 本文档描述本项目在 OntoTwin Nexus 现有代码基础上添加功能。
> **Claude Code 必须理解哪些代码不能动、哪些地方可以加。**

---

## 一、项目根目录

```
d:\tmp\digital_twin_aircraft\
```

---

## 二、现有技术栈

### 后端

| 项 | 值 |
|---|---|
| 语言 | Python 3 |
| Web 框架 | Flask 3.0.2 |
| 跨域 | flask-cors |
| HTTP 客户端 | requests |
| DXF 解析 | ezdxf |
| 数据存储 | **无持久化数据库**，混合策略（见下）|

### 前端

| 项 | 值 |
|---|---|
| 架构 | **多页应用（MPA）**，不是 SPA |
| 技术 | 原生 HTML/CSS/JS + CDN 引入的 Vue3、Axios、ECharts |
| 构建工具 | 无（不用 webpack/vite） |
| 路由 | 通过 `<a href>` 跳转不同 HTML 文件 |

---

## 三、现有后端目录结构

```
backend/
├── app.py                    # Flask 主入口，所有路由 + 静态文件托管
├── mapping_store.py          # MappingStore / InstanceStore / MockInstanceSimulator
├── ontology.py               # 本体数据模型
├── ontology_parser.py        # 本体 CSV 解析器（parse_ontology_csvs）
├── parser_dxf.py             # DXF 解析（ezdxf 封装）
├── build_*.py / generate_*.py# DXF 生成/处理辅助脚本
├── demo_*.dxf                # 测试用 DXF 文件
├── mapping_rules.json        # MappingStore 持久化文件
└── requirements.txt          # Python 依赖
```

### 各文件职责（不要随意改）

| 文件 | 职责 | 可改动程度 |
|---|---|---|
| `app.py` | Flask 应用主入口，挂载所有路由 | **只能在末尾加新路由**，不要改现有路由 |
| `mapping_store.py` | 内存存储 + 模拟器 | **不要改** |
| `ontology.py` | 本体模型定义 | **不要改** |
| `ontology_parser.py` | CSV → ECharts 图谱数据 | **不要改** |
| `parser_dxf.py` | DXF 解析 | **可复用函数**，不要改内部 |
| `mapping_rules.json` | 映射规则持久化 | **不要动** |

---

## 四、现有前端目录结构

```
frontend/
├── index.html            # 控制台主界面
├── ontology_graph.html   # 三维语义图谱总览
├── ontology.html         # 本体能力接口与资产配置中心
├── instance.html         # 数字孪生实例管理与状态大盘
├── mapping.html          # 规则映射控制台
├── cad_generator.html    # CAD 图纸场景自动生成器
├── floor_pulse.html      # 数字脉搏和事件监控
├── css/                  # 公共样式
├── js/                   # 公共脚本
└── assets/               # 图片等
```

### 页面特点

- 每个 HTML 文件**独立挂载自己的 Vue 实例**
- CDN 依赖在每个 HTML 的 `<head>` 里单独声明
- 页面之间通过 `<a href="/xxx">` 跳转
- 后端 `app.py` 为每个 HTML 注册独立路由

**可改动程度**：
- **不要**改任何现有 HTML 文件
- **可以**新增 HTML 文件（放在 `frontend/scenes/` 子目录）
- **可以**在 `index.html` 里加一个链接跳转到新页面（**需用户确认**）

---

## 五、现有数据存储策略

### 1. 内存缓存（非持久化）

```python
# mapping_store.py 中
states = {}              # 实例状态
_object_types = {}       # 对象类型
_datasets = []           # 数据集列表
_custom_graph_data = {}  # 自定义图数据
```

**特点**：服务重启后全部重置。

### 2. JSON 文件持久化

```python
# mapping_store.py 中
MappingStore → backend/mapping_rules.json
```

**特点**：读写本地 JSON 文件。

### 3. 中间件代理

```python
ONTOTWIN_MIDDLEWARE_URL   # 默认端口 5001
```

**特点**：Floor Pulse 等实时数据不存后端，直接代理到中间件。

---

## 六、本次新增部分的放置规则

### 后端

**新增目录**：

```
backend/lite/
├── __init__.py
├── api/                        # 新 REST 路由
│   ├── __init__.py
│   ├── scenes.py               # /api/v3/lite/scenes/*
│   ├── assets.py               # /api/v3/lite/assets/*
│   └── export.py               # /api/v3/lite/export/*
├── models/                     # SQLAlchemy / dataclass 模型
│   ├── __init__.py
│   ├── scene.py
│   ├── instance.py             # Lite 版本的 Instance（和现有 InstanceStore 无关）
│   └── asset.py
├── services/                   # 业务逻辑
│   ├── __init__.py
│   ├── scene_service.py
│   ├── usd_exporter.py         # 核心 USD 导出
│   ├── fbx_converter.py        # FBX → USD
│   └── dxf_structure.py        # 复用 parser_dxf
├── db/                         # SQLite 管理
│   ├── __init__.py
│   ├── connection.py
│   └── lite.db                 # SQLite 文件（.gitignore）
└── tests/
    └── test_exporter.py
```

### 后端注册方式

在 `app.py` **末尾**添加一行（仅此一处修改现有文件）：

```python
# 新增 lite 模块路由
from lite.api import register_lite_routes
register_lite_routes(app)
```

**其他地方一律不动**。

### 前端

**新增目录**：

```
frontend/scenes/
├── scenes.html                 # 场景列表 + 编辑
├── scene_detail.html           # 单个场景详情（如需要）
├── scenes.css
└── scenes.js
```

**导航接入方式**：

不修改 `index.html` 原有导航（避免破坏）。**新页面通过直接访问 URL** `/scenes` 打开。

或者：在某个合适时机（由用户决定），在 `index.html` 顶部导航加一个入口。**要改时先问用户**。

---

## 七、端口与路由约定

### 现有端口

| 端口 | 服务 |
|---|---|
| 5000（推测）| Flask 主服务 |
| 5001 | 中间件代理 |

### 新增路由前缀

| 前缀 | 用途 |
|---|---|
| `/api/v3/lite/` | 所有本次新增的 API（和 v2 完全隔离）|
| `/scenes` | 场景管理前端页面 |
| `/scenes/{id}` | 场景详情页 |

---

## 八、UE 项目

### 位置

```
d:\tmp\digital_twin_aircraft\ue_project\
```

### 状态

**新建项目**（本次从零开始，不在现有代码范围内）。

### 类型

UE 5.x Blank 项目，开启 USD 插件。

**不需要改造任何现有 UE 代码**（之前的 2.5 TwinSceneBuilder / 2.7 PCBWorkerSync / 2.8 AGVPatrol 等不在本项目范围）。

---

## 九、不在本项目范围的代码

以下代码存在于 OntoTwin 生态，但**本次不碰**：

- 所有 UE 现有插件（TwinSceneBuilder / PCBWorkerSyncComponent / AGVPatrolComponent）
- Floor Pulse 中间件（5001 端口）
- 工人/AGV 的运行态同步
- 本体 CSV 解析和语义图谱展示

如果需要复用其中的逻辑（比如 `parser_dxf.py`），**直接 import 调用**，不要重写。

---

## 十、环境与启动

### 后端启动

```bash
cd d:\tmp\digital_twin_aircraft\backend
pip install -r requirements.txt
python app.py
# 默认 http://localhost:5000
```

### 前端访问

通过浏览器访问 `http://localhost:5000/`（Flask 托管静态文件）。

### 新增依赖

本次预计需要加到 `requirements.txt`：

- `usd-core` — OpenUSD Python SDK
- `SQLAlchemy` 或 `sqlite3`（标准库）— 数据库 ORM
- 其他按需

**每次加依赖前必须征求用户同意**。
