# OntoTwin 3.8 Web 交互与业务视图联动（PRD）

> 文档性质：产品需求与技术边界设计  
> 主线：OntoTwin Nexus / 场景交互 / UE Runtime  
> 日期：2026-07-28  
> 状态：访谈决策已闭合，待实施  
> 前置能力：Zone 批量绑定、场景交互运行时配置、UE 实例选择、3.7.1 Screen Space 液态玻璃

---

## 1. 背景

现有 OntoTwin 已能管理 Project、ObjectType、Instance 和 Zone，但还缺少一条统一链路把以下能力连接起来：

1. 在 UE 中按项目、空间、业务或实例打开外部业务网页。
2. 让网页点击与 UE 实例选中、镜头聚焦和模型范围切换产生受控联动。
3. 让一栋楼中的楼层、设备类型、实例和业务视图拥有可解释、可预览的页面解析规则。
4. 避免把网页 URL、BusinessView 或场景动作直接写死在 Actor、Type 或 Instance 上。

典型案例：

```text
http://localhost:5000/ue_hud/pages/s3-building.html?space_id=SF.SB.M01
```

该页面展示楼宇指标、楼层、事件和业务入口。页面中的业务数据由网页自己的系统负责；OntoTwin 只提供稳定上下文、承接点击事件，并在配置允许时联动 UE 场景。

---

## 2. 当前事实与本次新增

### 2.1 当前事实

- UE 插件版本目标为 UE 5.6。
- `TwinInteractionManagerComponent` 已轮询 `/api/v2/scene-interactions/runtime`。
- UE 已具备实例 `select / clear_selection` 能力。
- UE 插件已有 WebSockets 客户端依赖，但当前用于空间目标实时数据，不是 Web 配置广播。
- 项目已有 WebUI 浏览器插件，但尚未有 OntoTwin 共享 Web 页面宿主；不得同时启用 UE 内置 `WebBrowserWidget`，否则会与 WebUI 的 CEF 产生重复链接。
- Zone 已有 `zone_id`、`ue_level`、`streaming` 预留字段；实例已有 `zone_id`。
- UE 当前具备实例显隐能力，但尚未实现按 Zone 的关卡加载/卸载。
- 场景交互配置是项目级低频 JSONB；ProjectStore 也有 JSON 文件兼容模式。

### 2.2 3.8 新增

- 项目级 Web 页面资源注册表。
- 独立 BusinessView 与动态成员规则。
- Web 页面绑定与确定性解析器。
- 场景交互面板下的 Web 交互工作台。
- 独立 `web_interactions` 存储、revision、运行时接口和发布回滚。
- UE 单例 Screen Space WebBrowser 宿主。
- Web Bridge 1.0、透明区域点击穿透和固定场景动作。
- Zone、BusinessView 的实例显隐，以及实例选择与镜头聚焦。

### 2.3 3.8 不做

- 不让 OntoTwin 编辑、代理或推送网页内部业务数据。
- 不给 Type 或 Instance 增加 `business_view` 单值字段。
- 不支持任意 Blueprint、Console Command、JavaScript 或外部 API 命令转发。
- 不做基于告警、状态变化、定时器或进入区域的自动网页触发。
- 不做实例级资源卸载，也不做 Zone Level Streaming。
- 不把网页变成完整桌面浏览器；文件、摄像头、麦克风等能力不纳入 3.8。

---

## 3. 目标与完成定义

3.8 完成后，配置人员应能在 Nexus 中：

1. 注册一个业务网页，并声明允许传入的上下文参数。
2. 建立楼层 Zone 层级并批量绑定实例。
3. 创建消防、能源、运维等 BusinessView，并预览其成员数量。
4. 为 Project、Zone、Type、Zone+Type、Instance 或 BusinessView 绑定页面。
5. 输入一个触发上下文，预览最终命中的规则、页面和 URL。
6. 原子发布整套配置；正式版可回滚到上一已发布版本。
7. 在已打包 UE 中打开页面，通过网页点击联动模型显隐、实例选择和镜头聚焦。

只有 PIE、Standalone、Development 和 Shipping 的目标环境均通过对应验收，3.8-GA 才算完成。

---

## 4. 核心概念

| 概念 | 责任 |
|---|---|
| Project | 当前激活项目，也是所有配置和对象的安全边界 |
| Zone | 物理空间范围，例如园区、楼栋、楼层、房间 |
| ObjectType | 设备或对象类型 |
| Instance | 场景中的具体孪生实例 |
| BusinessView | 跨 Zone、Type、Instance 的业务成员集合 |
| PageResource | 已注册、可复用、可校验的网页资源 |
| WebBinding | 触发条件与 PageResource 的绑定规则 |
| Web Bridge | 网页与 UE 宿主之间的固定消息协议 |

BusinessView 与 Zone 彼此独立：

- Zone 回答“对象在哪里”。
- BusinessView 回答“对象属于什么业务集合”。
- 同一实例可以属于多个 BusinessView。
- BusinessView 成员关系不能复用 `zone_id` 表达。

---

## 5. Zone 层级

### 5.1 数据规则

Zone 增加：

```text
parent_zone_id  可空；空表示项目根级 Zone
level           building | floor | room | area | custom
```

规则：

- 一个 Zone 最多一个父 Zone。
- 禁止形成循环。
- 实例只绑定叶子 Zone。
- 父 Zone 的实例范围由全部后代叶子 Zone 聚合得到。
- `space_id` 可由页面参数映射到 `zone_id`，不再建立第二套空间主键。

### 5.2 3.8 场景行为

激活 Zone 的“网页＋场景”模式时：

- 显示目标 Zone 及其后代 Zone 的已加载实例。
- 隐藏其他已绑定 Zone 的实例。
- `zone_id` 为空的实例默认常驻，不参与隐藏。
- 3.8 只做显隐，不卸载模型或子关卡。

因此，3.8 可以减少绘制量，但不能减少首次全量加载时间和内存占用。Level Streaming、Data Layer、World Partition 或服务端加载前过滤属于后续阶段。

---

## 6. BusinessView

### 6.1 对象模型

BusinessView 是项目级对象，建议字段：

```json
{
  "business_view_id": "bv.fire",
  "name": "消防业务",
  "description": "",
  "enabled": true,
  "rule_groups": [],
  "exclude_instance_ids": []
}
```

不在 ObjectType 或 Instance 上增加 `business_view` 字段。

### 6.2 成员规则

采用有限规则组：

- 同一规则组内为 AND。
- 不同规则组之间为 OR。
- 最后应用 `exclude_instance_ids`。

示例：

```json
{
  "rule_groups": [
    {
      "zone_ids": ["SF.SB.M01.F05"],
      "object_type_rids": ["ri.obj.smoke_detector"]
    },
    {
      "instance_ids": ["pump-001", "door-019"]
    }
  ],
  "exclude_instance_ids": ["smoke-test-device"]
}
```

含义：

```text
(5F AND 烟感类型) OR 指定实例
然后排除 smoke-test-device
```

不支持任意表达式、脚本或 SQL。

### 6.3 与 Zone 的组合

- 只传 `business_view_id`：在全项目范围计算成员。
- 同时传 `business_view_id + zone_id`：取 BusinessView 成员与目标 Zone 后代范围的交集。
- 组合范围必须显式携带 `zone_id`，不能依赖用户之前停留在哪一层。

### 6.4 场景显隐

BusinessView 的“网页＋场景”模式：

- 显示匹配成员。
- 隐藏其他已绑定 Zone 的实例。
- 未绑定 Zone 的实例继续常驻。
- 匹配为 0 是合法结果：保留常驻实例，显示“当前范围匹配 0 个实例”，不回退到 Zone 或全项目。

工作台必须持续显示未分区实例数量，避免漏绑实例长期被当作常驻对象。

---

## 7. 页面资源

### 7.1 PageResource

绑定规则只能引用 `page_id`，不能覆盖 URL。

建议结构：

```json
{
  "page_id": "page.s3-building",
  "name": "楼宇总览",
  "enabled": true,
  "base_url": "http://localhost:5000/ue_hud/pages/s3-building.html",
  "param_mapping": {
    "zone_id": "space_id",
    "project_id": "project_id",
    "business_view_id": "business_view_id",
    "instance_id": "instance_id",
    "object_type_rid": "object_type_rid",
    "trigger": "trigger"
  },
  "declared_extra_params": ["event_id"],
  "scope_effects": {
    "zone": "web_only",
    "business_view": "web_only",
    "instance": "web_and_scene"
  }
}
```

`scope_effects` 每个页面按目标范围类型配置：

```text
web_only
web_and_scene
```

不细化到页面中的每一个按钮。

### 7.2 URL 参数

平台内置上下文来源只允许：

- `project_id`
- `business_view_id`
- `zone_id`
- `object_type_rid`
- `instance_id`
- `trigger`

页面可声明少量业务参数，例如 `event_id`。未声明参数拒绝传递。

禁止：

- 任意字符串模板执行。
- 将 `raw_state` 整体拼入 URL。
- 传递 Cookie、访问令牌或账号密码。
- 页面请求任意目标 URL。

### 7.3 同页面切换对象

- 页面 ID 或最终 URL 变化：重新加载。
- 页面 ID 与最终 URL 完全相同：不刷新，只重新显示。
- 3.8 不通过 Bridge 热更新页面上下文。

---

## 8. 触发与绑定解析

### 8.1 WebBinding

3.8 只交付一个可配置动作：`open_web`。Zone、BusinessView 和 Instance 的场景联动是页面打开后的固定宿主效果，不扩展为任意动作编排。

建议结构：

```json
{
  "binding_id": "bind.fire",
  "name": "消防业务主页",
  "enabled": true,
  "trigger": "business_view_activated",
  "activation_mode": "direct",
  "effect": "open_web",
  "scope": {
    "business_view_id": "bv.fire"
  },
  "page_id": "page.fire-overview"
}
```

`scope` 只允许以下稳定键：

```text
Project          空 scope
Zone             zone_id
Type             object_type_rid
Zone+Type        zone_id + object_type_rid
Instance         instance_id
BusinessView     business_view_id
```

不使用 `hierarchy_path` 参与页面解析。同一 trigger、同一有效作用域不得存在两条并列 `open_web` 规则，否则作为硬错误禁止发布。

### 8.2 3.8 固定触发

```text
open_detail
project_home_activated
zone_activated
business_view_activated
```

3.8 不实现 `zone_entered`、`alarm_raised`、`state_changed`、定时器等自动触发。

### 8.3 激活模式

绑定支持：

```text
direct
explicit
```

- Actor 选择默认 `explicit`，避免仅悬停或状态变化就打开网页。
- BusinessView 和明确的 UI 按钮默认 `direct`。

### 8.4 对象详情解析

`open_detail` 使用唯一命中规则：

```text
Instance > Zone+Type > Type > Zone > Project
```

同一层级只能有一个有效获胜规则。加载失败不继续尝试低优先级页面。

### 8.5 BusinessView 解析

`business_view_activated` 使用统一绑定表：

```text
BusinessView 精确绑定 > Project
```

可选 `zone_id` 只影响模型交集和 URL 参数，不改变页面选择。

### 8.6 规则状态

- `enabled:false`：忽略该规则，继续向下解析。
- `effect:block`：命中后停止解析，并明确表示当前范围禁止打开页面。
- `effect:open_web`：打开绑定的 `page_id`。

工作台必须显示完整解析链，而不只显示最终页面。

---

## 9. Web 交互工作台

### 9.1 位置

Web 交互工作台放在现有“场景交互”面板下，不新增 Nexus 顶级模块和前端路由。

工作区包括：

1. 页面资源。
2. BusinessView。
3. 页面绑定。
4. 解析预览。
5. 草稿、发布与回滚。

### 9.2 视觉与交互

遵循 OntoTwin 黑白灰 UI 规范：

- 白底、灰阶结构、黑色主操作。
- 状态色只用于小面积状态点、左边线和错误文字。
- 不使用 emoji、原生 `alert`、`confirm`、`prompt`。
- 一个区域只保留一个主按钮。
- 保存后继续保留编辑状态，不形成单向死路。
- 删除、覆盖发布、回滚使用 OntoTwin 模态确认。
- 异步操作提供加载状态；空列表提供下一步入口。

Web 预览只展示页面结构、最终 URL、参数、解析链、成员数量和风险提示，不在 Nexus 中模拟 UE 液态玻璃。

### 9.3 发布校验

硬错误，禁止发布：

- ID 重复。
- 引用不存在。
- Zone 层级循环或实例绑定非叶子 Zone。
- 绑定结构、触发或参数映射格式非法。
- `javascript:`、`file:`、`data:` 等危险协议。
- URL 内嵌账号密码。
- 正式模式下域名不在项目白名单。

警告，可确认后发布：

- BusinessView 匹配 0 个实例。
- 页面暂时不可访问。
- 某些范围没有绑定。
- 规则被更高优先级规则覆盖。
- 存在未分区实例。

---

## 10. 存储、草稿与版本

### 10.1 存储

Project 新增独立 `web_interactions` JSONB；ProjectStore JSON 文件模式增加同名字段。

逻辑结构：

```json
{
  "schema_version": 1,
  "revision": 12,
  "published": {
    "pages": [],
    "business_views": [],
    "bindings": [],
    "web_policy": {
      "allowed_hosts": []
    }
  },
  "draft": {
    "base_revision": 12,
    "pages": [],
    "business_views": [],
    "bindings": [],
    "web_policy": {
      "allowed_hosts": []
    }
  },
  "previous_published": null
}
```

页面、BusinessView 和绑定不拆成多张关系表。

### 10.2 版本规则

- `web_interactions.revision` 独立于 `scene_interactions.revision`。
- 草稿保存不影响 UE。
- 发布必须携带 `expected_revision`。
- 整套配置原子发布，revision 加一。
- 回滚不是把 revision 减一，而是用上一已发布快照创建一个新的 revision。
- 只要求保留上一已发布版本，不做无限历史版本库。

### 10.3 Schema 兼容

- 旧项目读取时在内存补齐空 `web_interactions`。
- JSON 与 PostgreSQL 两种存储后端必须同步支持。
- 高于当前支持版本的数据拒绝写回。
- 不修改现有 Type/Instance 的 BusinessView 字段，因为不存在该字段。

---

## 11. 后端模块与 API

### 11.1 模块边界

新增独立模块，不继续向 `app.py` 塞业务逻辑：

```text
backend/web_interaction/
├─ api.py
├─ service.py
├─ validators.py
├─ resolver.py
└─ runtime_projection.py
```

`app.py` 只注册 Blueprint。

### 11.2 建议 API

```text
GET    /api/v2/web-interactions
PUT    /api/v2/web-interactions/draft
POST   /api/v2/web-interactions/validate
POST   /api/v2/web-interactions/resolve-preview
POST   /api/v2/web-interactions/publish
POST   /api/v2/web-interactions/rollback

GET    /api/v2/web-interactions/runtime?known_revision={revision}
POST   /api/v2/web-interactions/runtime-events
```

`runtime-events` 接收 UE 的运行结果、错误和关键动作日志；不接收网页业务数据。

### 11.3 运行时投影

UE 按与场景交互配置相同的调度节奏轮询独立 Web runtime endpoint：

- revision 未变化：只返回未变化状态。
- revision 变化：返回完整已发布运行投影。
- UE 立即重新解析当前上下文。
- 最终页面和 URL 未变化则不刷新。
- 当前二级详情页面仍有效时保持；其背后的业务主页更新，返回时使用新版本。
- 页面或绑定被禁用时关闭或切换到错误状态，不使用旧配置继续运行。

运行接口只认当前激活项目，并继续执行 UE 项目 ID/名称绑定校验。

---

## 12. UE Web 宿主

### 12.1 Renderer

只使用一个 Screen Space WebBrowser 实例，不提供 World Space 网页。

结构从底到顶：

```text
UE 三维场景
→ Screen Space 玻璃装饰层
→ WebBrowser 网页像素
→ 网页文字、图表和点击区域
→ OntoTwin 加载/错误/状态控制层
```

要求：

- 网页像素、文字、图表和点击目标始终位于玻璃装饰之上。
- 不对网页内容做模糊、折射或色散。
- 装饰层必须 `Self Hit Test Invisible`。
- 透明网页区域可把输入交还 UE；真实网页交互区由 WebBrowser 接收。
- 始终只有一个 WebBrowser、一个逻辑页面会话和最多一个共享 Slate Postbuffer。

### 12.2 质量降级

外层采用 visionOS-inspired 共享玻璃框架：

```text
High → Balanced → Performance
```

- High：一个共享 Slate Postbuffer。
- Balanced：`UBackgroundBlur` 与保守遮罩。
- Performance：静态或近不透明可读表面。
- 只能向下降级，不能自动升档。
- 任一玻璃资源缺失都必须降级为可读界面，不能出现透明空白或棋盘格。

### 12.3 导航模型

- 逻辑上维护“业务主页 + 当前详情页”两级页面。
- 只保留一个浏览器实例，不同时常驻多个页面。
- 可保存轻量导航历史：页面 ID、最终 URL、场景范围 ID 和镜头状态。
- “返回”同时恢复页面与场景。
- “关闭”只隐藏网页，保留当前模型范围和镜头。

### 12.4 输入恢复

关闭、Esc、目标切换或错误退出时必须恢复：

- 进入网页前的 UE 输入模式。
- 光标显示状态。
- 漫游与相机控制。
- 场景选择能力。

网页点击不能误触发场景清空选择。

---

## 13. Web Bridge 1.0

### 13.1 能力等级

普通网页允许注册和显示。

- 未完成 Bridge 握手：整个网页区域由浏览器接收输入；透明区域不穿透；不能发送 UE 动作。
- 完成 `ready(version, capabilities)`：启用交互区域上报、透明穿透和固定动作。
- 版本不兼容：降级为普通网页并提示，不阻止页面显示。

已注册且完成握手的页面默认可信，可调用全部 3.8 固定动作；UE 仍校验所有目标属于当前激活项目。

### 13.2 Web → UE

```text
ready
interactive_regions
select_instance
clear_selection
request_open_scope
request_open_page
```

示例：

```json
{
  "type": "request_open_scope",
  "request_id": "req-019",
  "payload": {
    "scope_type": "business_view",
    "business_view_id": "bv.fire",
    "zone_id": "SF.SB.M01.F05"
  }
}
```

约束：

- `request_open_scope` 只支持 Zone、BusinessView、Instance。
- `request_open_page` 只能引用已注册 `page_id`。
- 额外参数必须在 PageResource 中声明。
- 不接受任意 URL、任意命令或任意 JSON 透传。

### 13.3 UE → Web

```text
host_ready
context
action_result
navigation_result
visibility_changed
```

`context` 只包含稳定 ID 和触发来源，不包含业务指标、事件详情、`raw_state`、Cookie 或令牌。

### 13.4 交互区域

集成网页使用统一标记：

```html
data-ontotwin-interactive
```

网页负责在加载、布局变化、滚动和窗口尺寸变化后上报交互矩形。当前原型中的 `data-ue-interactive` 可由兼容适配器读取，但新页面统一使用 `data-ontotwin-interactive`。

安全回退：

- 未收到有效矩形前，网页区域全部由浏览器接收点击。
- 越界、NaN、负尺寸或数量超限的矩形拒绝应用。
- 装饰层不能进入交互矩形列表。

---

## 14. 网页与场景联动

### 14.1 每页按范围类型配置

每个 PageResource 分别配置：

```text
Zone          web_only | web_and_scene
BusinessView  web_only | web_and_scene
Instance      web_only | web_and_scene
```

### 14.2 Zone

`web_and_scene`：

- 显示目标 Zone 及其后代实例。
- 隐藏其他已分区实例。
- 未分区实例保持显示。
- 不做资源卸载。

### 14.3 BusinessView

`web_and_scene`：

- 计算全项目成员，或与显式 Zone 取交集。
- 显示匹配成员，隐藏其他已分区实例。
- 未分区实例保持显示。
- 0 匹配不回退。

### 14.4 Instance

`web_and_scene`：

1. 确保实例可见。
2. 选中实例。
3. 根据有效模型包围盒移动镜头聚焦。
4. 无有效包围盒时使用实例根节点与受限默认距离。

若实例不在当前 Zone/BusinessView 范围内：

- 将其作为“临时聚焦例外”加入当前可见集合。
- 保留原范围中的模型。
- 返回时移除例外并恢复原范围。

### 14.5 页面与场景失败

执行前统一校验目标、绑定、页面和 URL 策略，然后页面与场景并行执行。

- 网页失败：显示内置错误面板，场景状态保留。
- 场景失败：网页保留，并显示“场景未完成”状态。
- 不自动回滚另一侧。
- 不自动尝试低优先级页面。

---

## 15. 网页数据、登录与浏览器能力

### 15.1 数据所有权

网页自行请求和编辑业务系统数据。

OntoTwin：

- 只传稳定上下文 ID。
- 接收页面点击与固定 Bridge 消息。
- 不代理业务 API。
- 不编辑页面指标、事件或业务记录。
- 不把实例 `raw_state` 推送给网页。

### 15.2 登录

- 网页自行处理登录。
- 共享 WebBrowser 使用默认 Cookie 会话。
- 不同项目访问同一域名时可能共用登录身份。
- OntoTwin 不读取、保存或清理 Cookie、账号和令牌。

### 15.3 3.8 浏览器边界

支持：

- 页面浏览。
- 普通表单。
- 页面登录。
- Web Bridge。

不作为 3.8 验收能力：

- 文件上传与下载。
- 摄像头、麦克风、地理位置和系统通知。
- 多窗口和独立弹窗。

相关权限请求默认拒绝并给出说明。

---

## 16. URL 安全

### 16.1 部署模式

部署级开关：

```text
WEB_URL_POLICY=open | allowlist
```

- 3.8-MVP 测试部署可使用 `open`。
- 正式部署必须使用 `allowlist`。
- 项目白名单随 `web_interactions` 发布和回滚。
- 项目管理员维护当前项目的允许域名。

任何模式下都禁止：

- `javascript:`
- `file:`
- `data:`
- URL 内嵌用户名或密码

### 16.2 全程导航校验

以下地址都必须执行当前策略：

- 初始 URL。
- 普通链接。
- 服务端和客户端重定向。
- `target="_blank"`。

`target="_blank"` 不创建第二个浏览器，而是在共享 WebBrowser 中打开并进入逻辑历史。

正式环境的第三方登录若跨多个域名，相关认证域名必须全部进入项目白名单。

---

## 17. 错误、日志与诊断

### 17.1 内置错误面板

网页加载失败、超时或断网时显示 OntoTwin 控制层，提供：

- 重试。
- 返回上一页。
- 关闭。

错误面板保留上一份有效导航记录，不展示 Cookie、完整查询参数或网页响应正文。

### 17.2 关键决策日志

记录：

- 配置 revision。
- trigger。
- scope 类型与稳定 ID。
- 解析链与获胜 binding ID。
- page ID 和域名。
- Bridge 动作名与 request ID。
- 页面和场景各自的结果与错误码。

不记录：

- Cookie。
- 网页业务数据。
- 完整 URL 查询参数。
- 登录凭据。

### 17.3 配置更新

UE 发现新 revision 后立即重新解析当前上下文：

- 结果未变化：不刷新。
- 页面或 URL 变化：重新加载。
- 页面被禁用或域名失效：关闭或进入错误状态。
- 当前详情仍有效：保持详情，仅更新返回目标。

---

## 18. 交付里程碑

### 18.1 3.8-MVP

- 新增 `web_interactions` 契约与兼容读取。
- 页面资源、BusinessView、绑定和解析预览。
- 本地测试发布链路。
- 独立 runtime endpoint 与 revision 轮询。
- 单例 Screen Space WebBrowser。
- 普通网页显示与 Bridge 1.0 握手。
- 透明区域交互上报。
- 固定触发、绑定优先级与 `block`。
- Zone/BusinessView 实例显隐。
- 实例选择、临时例外和镜头聚焦。
- `WEB_URL_POLICY=open` 下跑通本地 S3 示例页面。

### 18.2 3.8-GA

- 正式项目域名白名单。
- 完整发布校验和上一版本回滚。
- 内置加载/错误/部分失败状态。
- 关键决策日志与诊断。
- 配置更新即时重解析。
- High/Balanced/Performance 降级验收。
- Development 与 Shipping 打包验收。
- 输入恢复、100 次切换和资源泄漏回归。

两阶段使用同一数据结构、Bridge 版本和运行时接口，不做二次迁移。

---

## 19. 性能与可访问性预算

### 19.1 硬预算

- 最多一个 WebBrowser 实例。
- 最多一个共享 Slate Postbuffer。
- 不创建页面级 SceneCapture 或私有全屏场景缓冲。
- revision 未变化时不重建网页宿主和场景范围。
- 交互矩形更新必须节流，持续布局变化时不高于 10 Hz，静止时不发送。
- 单页交互矩形默认上限 256 个，超限进入安全回退。
- 页面关闭、切换 100 次后不能残留不可见输入层、浏览器实例或回调。

### 19.2 测量

在 1080p 和 2K 下记录：

- Web 宿主开启/关闭的 CPU、GPU、Slate 和内存差值。
- High、Balanced、Performance 三档差值。
- 页面首次加载、同 URL 重开、不同实例重载耗时。
- BusinessView 规则解析和实例显隐耗时。

外部网页自身网络耗时单独记录，不归因到 UE 玻璃装饰。

### 19.3 可访问性

- 支持 720p、1080p、2K、4K 和常见 DPI。
- 文字与控件保持清晰，不受模糊和折射。
- 支持键盘焦点、Esc 返回/关闭和可见 focus 状态。
- ReduceMotion 关闭缩放和高光移动。
- ReduceTransparency 强制 Performance。
- HighContrast 增强遮罩与边缘对比。
- 普通网页内部的业务内容可访问性由网页负责；OntoTwin 负责宿主控制和错误层。

---

## 20. 验收

### 20.1 配置与解析

- [ ] 可注册 S3 楼宇页面并将 `zone_id` 映射为 `space_id`。
- [ ] 页面绑定不允许覆盖 URL。
- [ ] `Instance > Zone+Type > Type > Zone > Project` 解析结果稳定可解释。
- [ ] `business_view_activated` 使用 `BusinessView > Project`。
- [ ] `enabled:false` 继续回退，`effect:block` 停止回退。
- [ ] Zone 层级循环、无效引用和危险协议不能发布。
- [ ] 0 匹配、网页暂时不可达和未分区实例作为可确认警告。
- [ ] 草稿不影响 UE；发布 revision 加一；回滚产生新 revision。

### 20.2 页面

- [ ] 未接入 Bridge 的普通网页可以显示和操作。
- [ ] 未握手页面不能透明穿透，也不能调用 UE 动作。
- [ ] 已握手页面只有声明的交互区域接收网页点击，其余透明区域点击 UE。
- [ ] 页面或最终 URL 变化时重载；完全相同 URL 不重载。
- [ ] 所有链接、重定向和新窗口都经过 URL 策略。
- [ ] 网页文字、图表、像素和点击区域不被玻璃模糊或折射。

### 20.3 场景

- [ ] 激活 Zone 后只显示该 Zone 后代与未分区实例。
- [ ] 激活 BusinessView 后只显示匹配成员与未分区实例。
- [ ] `BusinessView + Zone` 正确取交集。
- [ ] 0 匹配不回退，且明确显示匹配数量。
- [ ] 实例不在当前范围时可以临时显示、选中和聚焦。
- [ ] 返回时恢复页面、可见范围和镜头；关闭网页保留当前场景。
- [ ] 网页失败不回滚已完成的场景动作；场景失败不关闭可用网页。
- [ ] 3.8 不宣称减少首次模型加载量或内存占用。

### 20.4 安全与恢复

- [ ] open 模式仍拒绝危险协议和内嵌账号密码。
- [ ] allowlist 模式对初始地址、重定向和内部链接逐次校验。
- [ ] Bridge 目标必须属于当前激活项目。
- [ ] Cookie、业务数据和完整查询参数不进入日志。
- [ ] 加载失败提供重试、返回、关闭。
- [ ] Esc、关闭、切换目标后恢复 UE 输入和相机控制。

### 20.5 打包

- [ ] 项目 WebUI 浏览器插件与所需资源在目标构建中启用并 Cook，且不同时链接第二套 CEF。
- [ ] PIE、Standalone、Development、Shipping 均通过。
- [ ] High 失败时只降级到 Balanced，再到 Performance。
- [ ] Performance 始终可读，不出现透明空白。
- [ ] 100 次页面/实例切换无浏览器、Widget、回调或输入层泄漏。

---

## 21. 已知风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| WebBrowser 透明像素仍吞点击 | 无法操作底层 UE | Bridge 矩形上报；未握手时安全降级；先做输入 Spike |
| 网页跨域登录依赖多个域名 | 正式模式登录失败 | 将认证域名纳入项目白名单并做完整重定向测试 |
| Zone 绑定不完整 | 大量实例被当作常驻 | 工作台持续显示未分区数量，发布时警告 |
| BusinessView 规则错误 | 误隐藏模型或出现 0 匹配 | 成员预览、硬错误/警告分级、可返回 |
| 只显隐不卸载 | 首次加载和内存问题仍存在 | 明确 3.8 边界；后续 Level Streaming 与加载前过滤 |
| 页面默认可信 | 已注册页面可触发全部固定动作 | 生产域名白名单、固定 Schema、活动项目校验、禁止任意命令 |
| 外部网页性能不可控 | UE 帧率或输入延迟波动 | 单例宿主、质量降级、分别记录网页与宿主成本 |
| 配置更新打断当前操作 | 页面或场景被重解析 | 仅结果变化时切换；详情仍有效时保持 |

---

## 22. 后续能力

以下内容不进入 3.8：

1. WebSocket 配置变更通知；HTTP revision 轮询永久保留为兜底。
2. 同一页面通过 Bridge `context_changed` 热切换对象。
3. Zone Level Streaming、Data Layer、World Partition 与加载前过滤。
4. 文件上传下载、剪贴板、摄像头、麦克风和系统通知。
5. 告警、状态变化、定时器、进入区域等自动触发。
6. 通用动作注册与扩展机制。

任何未来动作仍禁止任意 UE 命令和任意 JSON 透传。

---

## 23. 网页制作约定

业务网页生成或改造时可使用以下要求：

```text
制作一个可嵌入 OntoTwin UE 全屏透明 WebBrowser 的业务页面。
页面 body 和场景展示区域必须真正透明，不使用假背景图。
网页文字、图表和按钮必须清晰，不对它们应用 blur、filter 或折射。
所有需要接收鼠标点击的元素添加 data-ontotwin-interactive；
透明非交互区域不得拦截点击，以便事件穿透给 UE 三维场景。
页面加载后通过 OntoTwin Web Bridge 发送 ready，
并在布局、滚动和尺寸变化后上报交互区域。
页面业务数据由网页自己的接口获取；
只从 URL 或 Bridge context 读取 project_id、zone_id、
business_view_id、object_type_rid、instance_id 等稳定标识。
禁止向 UE 发送任意命令，只使用约定的固定 Bridge 消息。
```

---

## 24. 简短技术说明

WebSocket 和 HTTP 在本设计中职责不同：HTTP 负责获取完整、可校验、可重试的配置；未来 WebSocket 只负责通知 UE“revision 已变化”。网页开发者不需要发送这条配置通知，它由 OntoTwin 后端发给 UE。

Zone 与 BusinessView 也属于两个不同维度：Zone 是空间集合，BusinessView 是业务集合。两者同时出现时求交集，就能表达“5F 的消防设备”。3.8 先在已加载实例上做显隐；后续再把同样的集合结果前移到加载阶段，才能真正减少首次加载量和内存占用。
