# HANDOFF_README — 给用户的交接说明

> 这是一份给你（用户）的操作说明，**不需要给 Claude Code 看**。
> 告诉你这套文档怎么用、放到哪里、怎么和 Claude Code 对话。

---

## 一、本次给你的文件清单

| 文件 | 作用 | 放到哪 |
|---|---|---|
| `CLAUDE.md` | Claude Code 工作手册 | 项目根目录 |
| `PROJECT_BRIEF.md` | 项目简报 | `docs/` |
| `EXISTING_CODEBASE_MAP.md` | 现有代码地图 | `docs/` |
| `ARCHITECTURE_DECISIONS.md` | 架构决策记录 | `docs/` |
| `TECH_SPEC.md` | 技术规格 | `docs/` |
| `IMPLEMENTATION_PLAN.md` | 落地计划 | `docs/` |

---

## 二、操作步骤

### Step 1：放置文档

```cmd
cd d:\tmp\digital_twin_aircraft

# 如果 docs 目录不存在，创建
mkdir docs
mkdir docs\legacy

# 把 6 份文档放到对应位置：
# CLAUDE.md → d:\tmp\digital_twin_aircraft\CLAUDE.md
# 其他 5 份 → d:\tmp\digital_twin_aircraft\docs\
```

### Step 2：归档旧文档（可选）

把我之前给你的 3.0 系列 6 份文档（ARCH_CHANGELOG、USD导出PRD 等）**移到 `docs/legacy/`**。

**不要删除**，它们作为你自己的技术参考保留，但**不要给 Claude Code 看**（那套方案是多人协作版，会误导它）。

### Step 3：启动 Claude Code

在 `d:\tmp\digital_twin_aircraft\` 目录下启动 Claude Code：

```cmd
cd d:\tmp\digital_twin_aircraft
claude
```

Claude Code 会自动读取 `CLAUDE.md`。

### Step 4：第一条消息怎么说

建议的开场白：

```
请先完整阅读 CLAUDE.md，然后按其中指示的顺序读完 
docs/ 下的所有文档。读完后跟我确认你已经理解以下几点：

1. 项目是什么、谁在做、交付给谁
2. 现有后端的哪些文件不能改
3. 本次要新增的模块放在哪个目录
4. 我们已经定下的关键决策有哪些

确认后，我们开始 M0 阶段的第一个任务。
```

这样能强制 Claude Code 先把上下文吃透，再动手。

---

## 三、和 Claude Code 的协作方式

### 推荐做法

**每次开启新 session 时**（比如第二天重新开始）：

```
请重新阅读 CLAUDE.md 和 docs/PROJECT_BRIEF.md，然后告诉我
我们上次进行到哪个 Task。
```

**当 Claude Code 想搞大事情时**（比如要一次写 5 个文件）：

```
停一下，我们一次做一件事。先做 [任务X]，我验证过再继续。
```

**当 Claude Code 自作主张时**（擅自引入新依赖、改了现有代码）：

```
你改了 [文件名]，这不在我们的计划里。请先说明为什么需要改，
等我确认。
```

### 不推荐做法

❌ 把我们这整个对话 copy 给 Claude Code —— 太长，它读不完，反而混乱  
❌ 让 Claude Code 一次把 M0-M4 都写完 —— 必定出错  
❌ 跳过 M0 直接做 M1 —— M0 是保底验证，不能跳

---

## 四、有问题找谁？

### 架构层面问题

如果 Claude Code 提出一个你不确定的架构建议，**先和我（这个 Claude 对话）再聊一次**，我帮你判断。再把结论以 ADR-0XX 的形式补充到 `ARCHITECTURE_DECISIONS.md`。

### 代码层面问题

调试、报错、具体实现 bug —— 直接和 Claude Code 对话解决。

### 产品层面问题

需求变化、优先级调整、和训练同事的协作 —— 你自己拍板，然后告诉 Claude Code 更新计划。

---

## 五、重要提醒

### 1. 别把 `docs/legacy/` 下的文档给 Claude Code

那套是**废弃的过度设计**，会误导 Claude Code。保留仅供你本人参考。

### 2. M0 必须先跑通

不要跳过 M0 直接做数据库。M0 是**保险**：
- 先确认你的 Python 环境能生成 USD
- 先确认训练同事能加载
- 这两件事确认了，后面才有意义

### 3. 遇到新架构决策要及时记录

每当你和 Claude Code 讨论出一个新的决策（比如 ORM 用 SQLAlchemy），把它加到 `ARCHITECTURE_DECISIONS.md` 里作为新的 ADR。这样下次开新 session，Claude Code 能看到。

### 4. 前端是你自己的工具，不要追求完美

`frontend/scenes/` 下的页面**只是你自己用的工作台**。能添加数据、能点导出就行，不要在 UI 美观上花太多时间。

### 5. UE 部分如果卡住，可以推迟

UE 集成在 M2，如果遇到困难，可以跳过，直接把 M0/M1 生成的 USD 交付给训练同事。UE 可视化是"nice to have"，不是交付必需品。

---

## 六、里程碑期望时间

基于我对你现有基础设施的判断：

| 阶段 | 预计时间 | 关键产出 |
|---|---|---|
| M0 | 1 天 | 硬编码场景能导出成 USD |
| M1 | 2-3 天 | 前端点击能导出 |
| M2 | 2-3 天 | UE 能加载 |
| M3 | 1-2 天 | 回写功能 |
| M4 | 1 天 | 训练剧本 + 交付 |

**总计 1-2 周**，节奏看你自己。

---

## 七、最后说一句

这套文档是基于我们 30+ 轮对话沉淀的精华。Claude Code 只要按这套走，应该能避开大部分坑。

但它毕竟是个 AI，还是可能犯错。**你作为项目经理的角色不能缺位**：
- 每个任务完成后**自己验证**一下
- 遇到可疑决策**多问一句"为什么"**
- 代码 review 不要偷懒

祝顺利。
