# OntoTwin 外部数据监控台：WebSocket 监控与开关

## 1. 目标

在现有“外部数据监控台”中，只监控当前激活 Database 对应的 UE WebSocket 实时流，并允许操作人员开启或关闭该流。

这不是独立插件，也不是面向人物、车辆等某一种业务对象的管理器。页面只关心当前 Database 与外部实时流的连接关系，因此后续换成人流、车辆或其他 WebSocket 数据时无需改页面的信息架构。

## 2. 已确认的 10 个核心问题

1. **入口在哪里？** 使用现有“外部数据监控台”，不增加新的插件入口。
2. **监控谁？** 只显示当前激活的 Database，不同时罗列所有 Database。
3. **监控什么协议？** 只监控 UE 使用的 WebSocket 实时流。
4. **“关闭”做什么？** 主动关闭 WebSocket、停止该连接的自动重连，并立即回收该流已生成的人流目标；不得把最后一帧继续伪装为实时态。
5. **“开启”做什么？** 立即发起 WebSocket 连接；失败后仍沿用 UE 现有重连机制。
6. **会不会停掉 HTTP？** 不会。HTTP 快照、实例建档、模型绑定和非空间属性同步继续工作。
7. **状态从哪里来？** 以 UE 心跳回报的实际状态为准，不用浏览器本地状态冒充连接状态。
8. **需要显示“连了哪个”吗？** 需要显示当前 Database 名称/ID、绑定的 UE 工程和 WebSocket URL。
9. **怎么判断操作完成？** 页面同时显示“期望状态”和“UE 实际状态”；两者一致才算同步完成。
10. **切换 Database 怎么办？** 页面自动跟随新激活 Database，控制命令按 Database ID 隔离，不串台。

## 3. 页面范围

页面显示：

- 当前激活 Database：名称、ID。
- 绑定 UE 工程：名称、ID。
- WebSocket URL。
- 实际连接状态：`disabled / connecting / connected / reconnecting / disconnected / error / unknown`。
- 开关的期望状态，以及期望状态与实际状态是否一致。
- UE 是否在线、最后心跳时间、最后实时帧延迟、累计帧数、目标数、错误信息。
- 固定提示：“此开关不影响 HTTP 快照”。

页面不再把“工人数量/工位状态”作为核心监控信息；业务载荷仍可由其原有页面或接口查看。

## 4. 控制与状态链路

1. 监控台调用后端控制接口，写入当前 Database 的期望 `enabled` 状态。
2. 后端按 Database ID 保存运行期控制状态。
3. UE 通过已有运行心跳响应读取控制状态。
4. UE 仅开启或关闭 WebSocket；HTTP 轮询不变。
5. UE 下一次心跳回报实际连接状态，监控台据此更新。

控制状态按 Database 持久化。后端重启后仍恢复最后一次明确的开关选择，并在 UE 下一次心跳时重新下发；没有保存过选择的旧 Database 才沿用 UE 工程自身的默认配置。

### 4.1 断线与目标生命周期

- 操作人员关闭流时，UE 立即回收该流当前生成的全部目标。
- WebSocket 发生连接错误或关闭时，UE 立即回收当前目标，然后再按既有策略重连。
- 收到新的有效全量帧后，目标可重新生成；未收到新帧时场景保持无人流状态。
- 断线前最后一帧只可作为“候选缓存”，不得自动显示。是否加载缓存必须由操作人员在前端明确选择。
- UE 离线时，后端返回的帧数、目标数和活动数据源属于最后一次心跳历史值；页面不得把它们显示为当前在线状态。

## 5. 接口契约

### `GET /api/v2/external-data/realtime`

返回当前激活 Database 及 WebSocket 实际/期望状态。

关键字段：

```json
{
  "database": { "id": "...", "name": "..." },
  "ue": { "online": true, "project_id": "...", "project_name": "..." },
  "websocket": {
    "url": "ws://...",
    "desired_enabled": true,
    "reported_enabled": true,
    "connection_state": "connected",
    "in_sync": true
  },
  "http_snapshot": { "enabled": true, "affected_by_switch": false }
}
```

没有激活 Database 时返回 `404 active_database_not_found`。

### `PUT /api/v2/external-data/realtime`

请求：

```json
{
  "enabled": false,
  "expected_database_id": "当前页面看到的 Database ID"
}
```

`expected_database_id` 与当前激活 Database 不一致时返回 `409 active_database_changed`，避免页面过期时误操作新 Database。

### UE 心跳响应

当当前 Database 存在明确控制命令时，`POST /api/v2/scene-interactions/runtime` 响应附带：

```json
{
  "realtime_control": {
    "database_id": "...",
    "enabled": false,
    "updated_at": "..."
  }
}
```

## 6. 验收标准

- 页面只显示当前激活 Database。
- UE 在线且 WebSocket 已连接时，页面显示 `connected` 和实际 URL。
- 关闭后，UE 主动断开 WebSocket，停止自动重连，实际状态最终变为 `disabled`。
- 关闭、连接错误或连接关闭后，上一帧生成的人流目标全部回收，目标数回报为 `0`。
- 后端重启后，最后一次明确的开关选择仍存在，并在 UE 恢复心跳后重新同步。
- 关闭期间 HTTP 快照轮询继续运行。
- 开启后，UE 立即连接；成功时实际状态最终变为 `connected`。
- UE 离线时可记录期望状态，页面明确显示“等待 UE 心跳同步”，不伪报已完成。
- 操作期间若激活 Database 已切换，后端拒绝旧页面请求。

## 7. 项目初始化与 WebSocket 归属规则

初始化时不按项目名称、人物/车辆类型或 URL 猜测连接归属，使用下面四层显式身份：

1. `project_id`：OntoTwin Database ID，例如 `ds_1787305683288`。
2. `ue_project_id`：UE 工程稳定 ID，例如 `ueproj_ZHHZ_NEW`。
3. `stream_id`：工程内实时流的稳定 ID，例如 `metaverse.targets.primary`。
4. `url`：该流当前连接的传输地址，例如 `ws://10.191.12.40:8080/ws/targets`。

Database 通过已有 UE 工程绑定决定“由哪个 UE 工程消费”；UE 工程通过自己的初始化配置决定“启动哪些流、每条流连接哪个 URL”。以 `ZHHZ_NEW` 为例：

```ini
[MetaverseClient.AutoStart]
bEnabled=True
StreamId="metaverse.targets.primary"
Url="ws://10.191.12.40:8080/ws/targets"
```

真正持有 socket 的插件必须注册 `IOntoTwinRealtimeStreamProvider` 适配器。OntoTwin 心跳从适配器读取实际状态，监控台控制也下发给同一个适配器。因此人物流由 `MetaverseClient/ABridgeClient` 上报和执行；未来车辆插件实现相同接口即可接入，不需要把车辆逻辑写进监控台。

初始化判定顺序：

1. Database 是否激活。
2. Database 是否唯一绑定 `ue_project_id`。
3. 该 UE 工程心跳是否在线。
4. 心跳是否上报预期 `stream_id`、`owner` 和 `url`。
5. `desired_enabled` 是否等于 `reported_enabled`。
6. 开启时 `connection_state` 是否为 `connected`，且实时帧持续更新。

状态结论：

- 缺 Database 或绑定：`未配置`。
- 已绑定但无心跳：`等待 UE`。
- 有心跳但缺预期 `stream_id`：`驱动未注册/版本不匹配`。
- 期望与实际不同：`同步中`。
- 已开启、已连接且帧新鲜：`正常`。
- 已关闭且实际为 `disabled`：`已关闭（HTTP 不受影响）`。
- 连接错误或帧过期：`异常/降级`。

## 8. 可选快照缓存（后续能力边界）

缓存用于离线演示、网络故障复现和验收对比，不属于实时流的自动降级。第一阶段只修复断线清理和开关持久化，不在本次直接加入缓存存储。

建议的后续交互：

1. WebSocket 正常收到有效帧后，操作人员在前端点击“保存当前人流快照”。
2. 后端按 Database 和 `stream_id` 保存快照，记录采集时间、源时间戳、目标数量、坐标单位和目标数组。
3. 前端列出快照时间与目标数；操作人员点击“加载缓存”后，UE 才以 `cache_snapshot` 数据源生成静态人流。
4. 页面和 UE 必须持续显示“缓存 · <采集时间>”，不得显示为 WebSocket 已连接。
5. “停止使用缓存”立即回收缓存目标；重新连接实时流时也必须先退出缓存模式，避免两套目标重叠。

缓存不得：

- 在 WebSocket 断开时自动启用。
- 覆盖或回写实时实例状态。
- 省略 Database、UE 工程、`stream_id` 和坐标口径校验。
- 保存人物模型资产本体；缓存只保存可重建目标的轻量状态。
