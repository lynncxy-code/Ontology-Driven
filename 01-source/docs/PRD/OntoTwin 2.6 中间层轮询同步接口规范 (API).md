# UE 接入中转站接口说明

## 1. 接入目标

UE 侧只需要对接中转站，不需要直接访问上游工人 API。

当前对 UE 开放 2 个接口：

- `GET /api/ue/snapshot`
- `GET /api/ue/events?afterEventId=<number>`

用途：

- `snapshot`：获取当前所有工人的全量状态，主要用于启动、重连、补状态
- `events`：获取某个游标之后的增量变化，主要用于运行中的持续同步

## 2. UE 推荐流程

### 启动阶段

1. UE 请求一次 `GET /api/ue/snapshot`
2. 用返回的 `items` 初始化或更新场景中的工人对象
3. 保存返回里的 `latestEventId`

### 运行阶段

1. UE 持续请求 `GET /api/ue/events?afterEventId=<lastEventId>`
2. 按 `eventId` 升序处理返回的 `items`
3. 每处理完一条事件，更新本地 `lastEventId`
4. 同一轮上游变化可能产生多条事件，UE 不应假设“一次轮询只对应一个变化类型”

### 重连或异常恢复

1. 重新请求一次 `snapshot`
2. 用最新快照覆盖当前本地状态
3. 将本地游标更新为 `snapshot.latestEventId`
4. 再继续轮询 `events`

## 3. 核心约定

- `instanceId` 是工人的唯一主键，直接对应上游工人 ID，例如 `FW-01`
- `entityType` 当前固定为 `human`
- `eventId` 是中转站的全局事件游标
- `version` 是单个工人的版本号，用于防止旧状态覆盖新状态

## 4. 接口 1：获取快照

### 请求

```http
GET /api/ue/snapshot
Accept: application/json
```

### 示例响应

```json
{
  "serverTime": "2026-04-07T13:10:00Z",
  "latestEventId": 18,
  "items": [
    {
      "messageType": "snapshot",
      "instanceId": "FW-01",
      "entityType": "human",
      "version": 3,
      "state": {
        "position": {
          "x": 10.0,
          "y": 0.0,
          "z": 8.0
        },
        "status": "idle",
        "workstationId": "WS-00",
        "workstationName": "休息区",
        "currentMo": null,
        "currentProduct": null
      },
      "metadata": {
        "name": "张明",
        "avatar": "worker-1"
      },
      "updatedAt": "2026-04-07T13:01:16.720898"
    }
  ],
  "workstations": {
    "REST": {
      "id": "WS-00",
      "name": "休息区",
      "position": {
        "x": 10.0,
        "y": 0.0,
        "z": 8.0
      }
    }
  }
}
```

### 字段说明

| 字段 | 说明 |
| --- | --- |
| `serverTime` | 中转站响应时间 |
| `latestEventId` | 当前最新事件游标，UE 后续轮询 `events` 时从这里开始 |
| `items[]` | 当前所有工人的最新状态 |
| `items[].instanceId` | 工人唯一标识，UE 用它定位 Actor |
| `items[].version` | 当前工人版本号 |
| `items[].state.position` | 当前工人三维位置 |
| `items[].state.status` | 当前工人状态，例如 `idle`、`working` |
| `items[].state.workstationId` | 当前工位 ID |
| `items[].state.workstationName` | 当前工位名称 |
| `items[].state.currentMo` | 当前工单号 |
| `items[].state.currentProduct` | 当前产品名 |
| `items[].metadata.name` | 工人姓名 |
| `items[].metadata.avatar` | 头像或模型资源标识 |
| `items[].updatedAt` | 上游数据更新时间 |
| `workstations` | 当前工位字典，可选使用 |

### UE 侧建议处理

- 如果 `instanceId` 对应的对象已经存在：直接更新到 `state.position`
- 如果对象不存在：由 UE 决定是动态创建还是忽略
- `metadata.name`、`state.status`、`state.currentProduct` 可直接用于 UI 展示

## 5. 接口 2：获取增量事件

### 请求

```http
GET /api/ue/events?afterEventId=18
Accept: application/json
```

### 示例响应

```json
{
  "serverTime": "2026-04-07T13:10:05Z",
  "fromEventId": 18,
  "latestEventId": 20,
  "items": [
    {
      "messageType": "event",
      "eventId": 19,
      "eventType": "position_changed",
      "instanceId": "FW-04",
      "entityType": "human",
      "version": 4,
      "occurredAt": "2026-04-07T13:10:02Z",
      "from": {
        "position": {
          "x": 2.0,
          "y": 0.0,
          "z": 3.0
        },
        "status": "working",
        "workstationId": "WS-01",
        "workstationName": "X100 主控板工位",
        "currentMo": "MO-AUTO-5428",
        "currentProduct": "IoT Sensor Board"
      },
      "to": {
        "position": {
          "x": 6.0,
          "y": 0.0,
          "z": 3.0
        },
        "status": "working",
        "workstationId": "WS-02",
        "workstationName": "X200 传感板工位",
        "currentMo": "MO-AUTO-5428",
        "currentProduct": "IoT Sensor Board"
      },
      "metadata": {
        "name": "赵伟",
        "avatar": "worker-4"
      }
    }
  ]
}
```

### 字段说明

| 字段 | 说明 |
| --- | --- |
| `fromEventId` | 本次请求的起始游标 |
| `latestEventId` | 当前中转站最新事件游标 |
| `items[]` | 本次新增事件列表 |
| `items[].eventId` | 全局事件 ID |
| `items[].eventType` | 事件类型 |
| `items[].instanceId` | 工人唯一标识 |
| `items[].version` | 当前工人版本号 |
| `items[].occurredAt` | 事件发生时间 |
| `items[].from` | 变化前状态 |
| `items[].to` | 变化后状态 |
| `items[].metadata` | 姓名和头像等静态信息 |

### 当前事件类型

| `eventType` | 含义 | UE 建议处理 |
| --- | --- | --- |
| `created` | 新工人出现 | 创建对象或标记上线 |
| `removed` | 工人消失 | 隐藏、删除或标记离线 |
| `position_changed` | 位置变化 | 根据 `from.position` 和 `to.position` 驱动移动 |
| `state_changed` | 状态变化 | 更新状态、工位、工单、产品显示 |

说明：

- 同一个工人在同一轮同步里，可能先收到 `position_changed`，再收到 `state_changed`
- UE 应按 `eventId` 顺序逐条消费，而不是假设一个工人在一次同步中只会收到一条事件

### UE 侧建议处理

- 必须按 `eventId` 升序处理
- `position_changed` 不要只看 `to.position`，建议同时保留 `from.position` 以便平滑移动
- `state_changed` 主要更新 UI 或状态机，不一定要求对象移动
- 如果本地收到的事件 `version` 小于当前对象版本，应忽略该事件

## 6. 推荐轮询频率

- 中转站轮询上游：每 `5` 秒
- UE 轮询中转站 `events`：建议每 `1` 到 `2` 秒
- `snapshot`：启动、重连、异常恢复时拉一次

## 7. 错误处理建议

### `snapshot` 失败

- 不要直接进入事件消费流程
- 先重试 `snapshot`

### `events` 失败

- 保持当前 `lastEventId` 不变
- 下次继续用同一个 `afterEventId` 重试

### `events` 返回 `stale_after_event_id`

当中转站返回：

```json
{
  "error": {
    "code": "stale_after_event_id",
    "message": "Query parameter 'afterEventId' is older than the earliest retained event. Refresh snapshot and restart event consumption.",
    "details": {
      "requestedAfterEventId": 100,
      "oldestAvailableEventId": 180
    }
  }
}
```

说明：

- UE 当前持有的事件游标已经太旧
- 中转站本地已不再保留这段历史事件

建议处理：

1. 重新拉一次 `snapshot`
2. 用 `snapshot` 覆盖本地状态
3. 将本地游标重置为新的 `snapshot.latestEventId`
4. 再继续轮询 `events`

### 本地状态和服务状态不一致

- 重新拉一次 `snapshot`
- 用快照覆盖当前状态

## 8. 健康检查

中转站还提供：

```http
GET /health
```

说明：

- 这个接口只用于服务状态检查
- 不属于 UE 主同步协议
- UE 主逻辑不需要依赖它

## 9. 一句话接入原则

- UE 只认 `instanceId`
- 启动先拉 `snapshot`
- 运行中持续拉 `events`
- 丢状态时重新拉 `snapshot`
