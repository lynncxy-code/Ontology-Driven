# PRD 2.5: TwinSceneBuilder CAD 自动化生成插件

> **版本**：2.5
> **更新日期**：2026-04-02
> **状态**：进行中

---

## 1. 业务目标与核心愿景

- **短期目标 (本期)**：实现从标准 DXF 图纸到 UE5 工业场景的自动化生成，覆盖墙体、地坪、立柱三大核心结构，跑通全链路核心逻辑。
    
- **长期愿景**：构建“数据即模型”的交付体系，将原本以“周”为单位的美术建模工作量降至“分钟”级，实现全要素（设备、电力、感知层）的数据驱动。
    

---

## 2. 系统架构设计 (Scalability Priority)

为确保后续 7.xx (电力)、9.xx (监控) 模块的平滑接入，系统采用 **“插件化分发架构”**。

### 2.1 核心组件逻辑

- **TwinDataParser (Python 中间件)**：采用 **`ezdxf`** 库，负责将 DXF 图纸文件转化为语义化的标准 JSON 数据。（*注：原生 DWG 需先转存为 DXF*）
    
- **TwinSceneManager (UE 调度中心)**：作为主入口，解析 JSON 并根据元素 `generate_type` 派发任务。
    
- **TwinStructureBuilder (本期新增)**：处理 `PROCEDURAL_WALL` 与 `PROCEDURAL_FLOOR` 类型，利用 RMC (RuntimeMeshComponent) 或其他可用网格体组件实时生成。
    
- **TwinInstance (存量优化)**：处理 `INSTANCE` 类型（柱子、未来设备），利用 HISM 摆放预制模型。

---

## 3. CAD 数据规范 (The Standard)

**没有标准的数据就是噪声。** 本期 Demo 强制要求 DXF 遵循以下图层及实体规范：

|**资产类型**|**匹配图层关键字**|**CAD 实体类型**|**转换逻辑**|
|---|---|---|---|
|**立柱**|`1.20-柱子`|Block (块引用)|提取 `Position` & `Rotation` -> 映射预设模型基础路径|
|**墙体**|`1.21-墙体`|Polyline (闭合/非闭合)|提取顶点坐标路径 -> RMC 挤压 (Extrude) 生成|
|**地坪**|`4.10-地坪`|Closed Polyline|提取闭合轮廓 -> RMC 面片生成|

---

## 4. 功能需求详细说明

### 4.1 混合生成策略 (Hybrid Logic)

- **[生成类] 墙体/地坪**：
    
    - **输入**：路径坐标数组、墙高参数、厚度参数。
        
    - **算法**：C++ 根据路径生成三角面索引，支持非 90 度转角的自动切宽处理。
        
    - **材质**：强制应用 **World-Aligned Material**，解决 UV 拉伸问题。
        
- **[摆放类] 立柱**：
    
    - **输入**：中心点坐标、旋转角度、缩放比例。
        
    - **逻辑**：采用固定模型映射，根据客户端提供的特定模型路径和模型名字获取资产，并加入 HISM (层次化实例化渲染) 队列。
        

### 4.2 材质与 TA 美学规格

本期跑通版只需集成最基础的光照特性：

1. **实时光照兼容**：所有动态生成 Mesh 必须开启 `Affect Distance Field Lighting`，确保在 **Lumen** 全局光照下有正确的环境光遮蔽 (AO)。要求配置具有基于世界坐标映射 (World Aligned) 特性的通用父材质。

> *(说明：原定方案中的「自动踢脚线」和「动态脏迹 Vertex Dirt」本期不做强制要求，可先忽略以保证核心主干流程走通。)*


---

## 5. 数据交换协议 (JSON Schema Sample)

这是 `TwinSceneManager` 与外部沟通的凭证。`generate_type` 统一枚举值为 `PROCEDURAL_WALL`、`PROCEDURAL_FLOOR`、`INSTANCE` 三类：

```json
{
  "header": { "version": "1.0", "project": "Factory_A", "origin": [0,0,0] },
  "entities": [
    {
      "id": "wall_north_01",
      "layer": "1.21-墙体",
      "generate_type": "PROCEDURAL_WALL",
      "data": {
        "path": [[0,0], [1500,0], [1500,800]],
        "height": 4500,
        "thickness": 240,
        "material_params": { "color": "#C0C0C0" }
      }
    },
    {
      "id": "column_p1",
      "layer": "1.20-柱子",
      "generate_type": "INSTANCE",
      "data": {
        "mesh_id": "SM_Std_Column_500",
        "transform": { "loc": [500, 500, 0], "rot": [0,0,90], "scale": [1,1,1] }
      }
    }
  ]
}
```

---

## 6. 性能与优化指标 (Performance)

- **核心目标**：本期优先打通功能链路，验证从 DXF -> Python -> JSON -> UE5 的场景跑通。“秒级”等极致性能优化后续再做硬性要求。
- **Draw Call 控制**：所有实例化的柱子建议合并入单次 Draw Call。
- **异步计算**：RuntimeMesh 的顶点计算逻辑建议在 **非渲染线程 (Async Thread)** 执行，以避免界面挂起。
- **碰撞体生成**：仅针对墙体和柱子生成 `Simple Collision`，地坪可暂不生成碰撞以节省开销。
    
---

## 7. 未来迭代路线图 (Future Roadmap)

- **Phase 2 (机电模块)**：支持 7.xx 图层，自动生成电缆桥架（利用 Spline 逻辑）及配电柜点位。
    
- **Phase 3 (感知模块)**：支持 9.xx 图层，自动 Spawn 摄像机蓝图、温感传感器，并根据 CAD 编号自动绑定 IoT 数据 ID。
    
- **Phase 4 (进阶渲染与 AI)**：加入基于大语言模型(LLM)的图层纠错能力；后期补全墙体底部“自动踢脚线”及“Vertex Dirt 动态物理脏迹”以提升画面表现力。
    

---

### 老马的执行建议：

1. **前端/FDE解析阶段**：利用 `ezdxf` 库编写 Python 脚本，以 DXF 工程图纸为基准，提取 `1.20` 和 `1.21` 的图元数据，输出符合第 5 章规范的 JSON。
    
2. **UE 开发链路跑通阶段**：无需急着写复杂的异形墙体计算逻辑，先在 `TwinSceneManager` 里把 JSON 读取功能打通；对立柱实体直接利用已知的基础预制体路径，先使用 HISM 把方块铺出来测试坐标映射关系的准确性。
    
3. **资产筹备阶段**：开发或提供一套稳定的、具备基准 World Aligned 属性的技术向材质，供 Runtime Mesh 生成挂载。