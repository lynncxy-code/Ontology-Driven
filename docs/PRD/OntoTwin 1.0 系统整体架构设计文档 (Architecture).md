

> **目标**：定义系统各组件的职责及数据流向，确保“本体驱动”的逻辑解耦。

### 1. 总体架构

本系统采用解耦架构设计，确保数据源（Web）与渲染端（UE）通过统一的本体语义接口通信。

- **数据接入层 (Data Ingestion)**：Web 前端作为模拟数据源，通过 API 提交属性变更。
    
- **本体服务层 (Twin Core)**：Python 后端负责维护实体的“权威状态快照（State Store）”。
    
- **渲染适配层 (3D Runtime)**：Unreal Engine 5 通过 REST 客户端定期同步状态，并驱动 3D 行为。
    

### 2. 技术栈

- **Backend**: Python 3.10+, Flask (RESTful API)。
    
- **Frontend**: HTML5, JavaScript (Vue.js CDN), Axios。
    
- **3D Engine**: Unreal Engine 5.x (Python Scripting 或 Blueprints)。
    
- **Communication**: HTTP/JSON (Polling 模式)。
    

### 3. 数据流设计

1. **用户输入**：用户在 Web 页面拖动滑块（如高度 $Z$）。
    
2. **状态更新**：Web 前端发送 `POST` 请求至后端 `/api/update`。
    
3. **状态存储**：后端更新内存中的 JSON 对象，记录 `I3DSpatial` 等接口数据。
    
4. **状态分发**：UE 5 每隔 $0.5s$ 发送 `GET` 请求至 `/api/state`。
    
5. **驱动行为**：UE 5 根据状态差异，调用 `SetActorLocation` 或 `SetMaterial`。