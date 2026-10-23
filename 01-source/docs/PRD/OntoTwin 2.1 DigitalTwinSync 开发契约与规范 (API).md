## 1. 全局唯一标识体系 (Identity Standards)

为了打通本体、模型库和 UE，必须统一 ID 识别规则：

- **InstanceId**：业务实例的唯一 ID（如：`aircraft_001`），用于在本体图数据库中索引对象。
    
- **ObjectTypeRid**：本体中定义的类型 ID（如：`ri.obj.airplane`），用于获取该类资产的通用映射规则。
    
- **FileNumber**：模型资产库中的【文件编号】，作为 3D 模型的唯一索引。
    
- **InterfaceRid**：能力接口的唯一标识（如：`I3D_Movable`），定义了一组标准属性集合。
    

---

## 2. 能力接口定义规范 (Capability Interface Schema)

每个接口定义了模型在 3D 世界中被驱动的“潜力”。

### 2.1 基础表达接口 (`I3D_Representable`)

所有要在场景中露脸的资产必须实现此接口。

- **`file_number` (String)**：指向资产库的唯一识别码。
    
- **`lod_strategy` (Enum)**：选择加载源文件区、一级或二级优化区资产。
    
- **`is_visible` (Boolean)**：控制资产在 UE 中的渲染显隐。
    

### 2.2 运动接口组 (`I3D_Movable` & `I3D_Rotatable`)

- **`translation_x/y/z` (Float)**：基于米或厘米的世界坐标位移。
    
- **`rotation_p/y/r` (Float)**：俯仰、偏航、翻滚角度（0-360°）。
    

### 2.3 动态行为接口 (`I3D_Animatable`)

- **`animation_state` (String)**：驱动 UE 动画蓝图的状态名（如：`open`, `close`, `working`）。
    
- **`play_rate` (Float)**：动画播放倍率。
    

---

## 3. 映射函数规范 (Mapping Function Spec)

映射控制台生成的 `Mapping_Rule.json` 必须包含以下逻辑节点，以实现数据的“非线性翻译”。

### 3.1 线性映射 (Linear Remap)

用于数值范围转换（如：压力值转指针角度）。

- **参数**：`in_min`, `in_max`, `out_min`, `out_max`。
    
- **算法**：$Result = out\_min + (value - in\_min) \times \frac{out\_max - out\_min}{in\_max - in\_min}$。
    

### 3.2 枚举转换 (Enum Map)

用于业务状态转视觉状态。

- **配置**：`{"Running": "Material_Green", "Fault": "Material_Red", "Idle": "Material_Gray"}`。
    

---

## 4. 后端 API 契约 (System API Contract)

### 4.1 获取能力定义集

- **Endpoint**: `GET /api/v2/ontology/interfaces`
    
- **作用**：Web 前端读取此列表，用于渲染“映射控制台”的右侧能力槽。
    

### 4.2 保存/下发映射规则

- **Endpoint**: `POST /api/v2/mapping/publish`
    
- **Payload**：包含 `objectTypeRid` 与其挂载的 `Interfaces` 及 `FunctionHandlers`。
    

### 4.3 实时状态快照 (Transformed State)

- **Endpoint**: `GET /api/v2/state/snapshot?id={instanceId}`
    
- **响应**：返回经由后端 Function 处理后的**“最终表现值”**。
    
    - _不再传原始压力值，直接传 `rotation_z: 45.5`_。
        

---

## 5. 异常处理契约 (Error Handling)

为了防止系统崩溃，三维端与数据端需达成以下共识：

- **数据超时**：若 `/api/v2/state` 超过 3 个周期（1.5s）未更新，UE 插件应将该实例标记为“离线”变体材质。
    
- **非法值拦截**：后端计算映射函数时，若结果超出 3D 属性定义的阈值（如缩放值为负数），必须强制钳位（Clamp）并向管理列表发送预警。
    
- **虚实不符**：当模型库返回的模型包围盒尺寸与本体定义的 `ActualSize` 属性差异超过 10% 时，触发“数据一致性冲突”预警。
    

---

## 6. 核心数据对象示例 (JSON Sample)
{
  "instanceId": "pump_001",
  "implement_interfaces": [
    {
      "rid": "I3D_Movable",
      "properties": {
        "translation_z": { "source": "pressure_val", "function": "linear_remap", "value": 150.5 }
      }
    },
    {
      "rid": "I3D_Representable",
      "properties": {
        "file_number": "6D654-G3-9453",
        "is_visible": true
      }
    }
  ]
}