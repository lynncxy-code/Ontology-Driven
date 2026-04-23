# CLAUDE.md — Claude Code 工作手册

> 本文件是 Claude Code 进入本项目时**第一个要读的文件**。
> 读完后，必须继续读 `docs/PROJECT_BRIEF.md`。

---

## 一、项目身份

- 项目代号：**OntoTwin Lite**（本次新增的 USD 导出能力）
- 父项目：OntoTwin Nexus（`d:\tmp\digital_twin_aircraft\`）
- 开发者：**单人开发**（用户同时负责产品 + 前端 + 后端 + UE）
- 对接方：**单个训练侧同事**，不构成团队
- 交付物：一个 USD 场景文件 + 一份训练剧本文档

**重要**：本项目不是企业级系统，不要过度工程化。

---

## 二、上下文阅读顺序

Claude Code 必须按以下顺序阅读文档，才能完整理解项目：

1. `CLAUDE.md`（本文件）
2. `docs/PROJECT_BRIEF.md` — 项目是什么、为什么要做
3. `docs/EXISTING_CODEBASE_MAP.md` — 现有代码库现状（不能动的部分）
4. `docs/ARCHITECTURE_DECISIONS.md` — 已决策事项（不要再次提问）
5. `docs/TECH_SPEC.md` — 技术规格（具体怎么写）
6. `docs/IMPLEMENTATION_PLAN.md` — 分步落地计划

每次新开 session 时，**至少读 1、2、4 三份**。

---

## 三、编码原则

### 3.1 优先简单

- **不要**引入 Celery / Redis / RabbitMQ 等异步队列
- **不要**引入 PostgreSQL / MySQL（SQLite 就够）
- **不要**写权限系统、多租户、审计日志
- **不要**做版本管理、操作历史（文件快照足够）
- **不要**写复杂的状态机
- **不要**做微服务拆分

### 3.2 保守修改

- 现有代码（`backend/app.py`、`frontend/*.html` 等）**能不改就不改**
- 需要修改现有文件时，**先在响应里说明清楚改什么、为什么**，等用户确认
- 新功能优先放在**新建的 `lite/` 子目录**下，与现有代码物理隔离

### 3.3 依赖管理

- 后端新依赖添加到 `backend/requirements.txt`，但**先询问用户**再加
- 前端依赖继续走 **CDN 引入**方式（Vue3 / Axios / ECharts 已在用）
- 不要引入 npm / yarn / webpack 等构建工具

### 3.4 命名风格

- Python：`snake_case`
- JavaScript：`camelCase`
- 文件名：`snake_case.py` / `kebab-case.html`
- URL 路径：`/api/v3/lite/scenes`（`/api/v3/lite/` 前缀表示本次新增）

### 3.5 注释密度

- 函数级注释：说明**做什么、为什么**（不要说 "how"，代码自己会说）
- 重要逻辑旁加 1-2 行中文注释
- 不要写大段文档型注释（Docstring 一两行即可）

---

## 四、协作模式

用户选择了**"边做边讨论"**模式。这意味着：

- **不要**一次性输出几千行代码
- 每个功能分解为小步骤，**一步一确认**
- 完成一小块后停下来，让用户验证再继续
- 遇到架构选择时，**先列出 2-3 个方案的利弊，让用户选**，不要自作主张

---

## 五、禁止事项（重要）

以下行为会破坏项目，**绝对不要做**：

1. 擅自修改现有数据库 / JSON 存储文件的结构
2. 擅自改动现有前端的路由、菜单、HTML 文件
3. 把新功能硬塞进 `app.py` 主文件（会导致该文件膨胀到难以维护）
4. 在未征求用户同意时添加新的 Python 包依赖
5. 把本次任务拆成 "大型企业级架构"（参考前文的"优先简单"）
6. 直接翻译 `docs/legacy/` 下的旧 3.0 文档——那些**已经被废弃**，仅作参考
7. 复述用户或本文档已经明确的决策（避免浪费 token）

---

## 六、输出风格

- 回复简短、聚焦、不啰嗦
- 代码先于解释（用户看代码更快）
- 多用列表和表格
- 中英文都可以，跟随用户的语言

---

## 七、关键路径速查

| 项目位置 | 作用 |
|---|---|
| `d:\tmp\digital_twin_aircraft\backend\` | 现有后端（Flask，慎改）|
| `d:\tmp\digital_twin_aircraft\backend\lite\` | 本次新增后端模块（主战场）|
| `d:\tmp\digital_twin_aircraft\frontend\` | 现有前端（多 HTML 页面，慎改）|
| `d:\tmp\digital_twin_aircraft\frontend\scenes\` | 本次新增场景管理页面 |
| `d:\tmp\digital_twin_aircraft\assets\fbx\` | FBX 源文件 |
| `d:\tmp\digital_twin_aircraft\assets\usd_cache\` | 转换后的 USD 缓存 |
| `d:\tmp\digital_twin_aircraft\exports\` | 导出的 USD 场景文件 |
| `d:\tmp\digital_twin_aircraft\ue_project\` | UE 5 工程（新建）|

---

## 八、当前开发阶段

**阶段**：M0 — 最小可行链路（MVP）

**目标**：能从 Nexus 导出一个包含 5 个物体的 USD，训练同事能在 Isaac Sim 加载。

**完成标志**：
- 后端 `POST /api/v3/lite/scenes/{id}/export` 可调用
- 前端有一个"场景管理"页面，能添加物体、配坐标、点击导出
- 生成的 `.usda` 文件能用 `usdview` 打开

**不在 M0 范围**：UE 集成、回写功能、FBX 自动转换、训练剧本。这些在 M1+ 做。
