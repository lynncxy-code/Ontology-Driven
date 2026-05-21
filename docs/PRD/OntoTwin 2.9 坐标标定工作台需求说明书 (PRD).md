# OntoTwin 2.9 坐标标定工作台需求说明书 (PRD)

> **文档版本说明：**
> - **2.9** — 初始版本，CAD/DXF 模式坐标标定与实体管理
> - **2.9.1** — 扩展版本，新增图片模式、多实体类型解析、Y 轴翻转等

## 1. 产品背景

在数字孪生工厂项目中，需要将 AutoCAD 平面图纸中的设备位置映射到 Unreal Engine 5 的世界坐标系中。传统做法是人工在 CAD 中逐一读取坐标、手动换算、再填入 UE 编辑器——效率低、误差大、无法验证。

**坐标标定工作台**（Coordinate Calibration Workbench）提供了一个可视化的 Web 端工具，实现：

1. **上传 DXF 图纸 → 自动解析全图层图元 → 画布预览**
2. **锚点标定 → 最小二乘仿射变换 → CAD 坐标自动映射为 UE 世界坐标**
3. **实体管理 → 批量导出 JSON/CSV → 直接用于 UE 场景构建**

---

## 2. 核心功能概览

| 功能模块 | 说明 |
| :--- | :--- |
| **DXF 解析引擎** | 后端 Python (ezdxf) 提取 LWPOLYLINE / LINE / CIRCLE / ARC / ELLIPSE / SPLINE / POLYLINE / INSERT 等实体类型 |
| **CAD 模式** | 上传 DXF → 图层管理 → 锚点标定 → 实体管理 → 导出 |
| **图片模式** | 上传截图 → 像素锚点标定 → 设备打点标注 → 导出 CSV |
| **仿射变换** | 前后端对称实现的 6 参数仿射变换（最小二乘法），支持 2+ 锚点 |
| **画布交互** | 自适应网格背景、X/Y 坐标轴（Y 轴向上，与 CAD 一致）、缩放/平移/居中控制 |

---

## 3. 系统架构

### 3.1 技术栈

| 层 | 技术 | 说明 |
| :--- | :--- | :--- |
| 前端 | 纯 HTML + Canvas + JS | 单文件 SPA，无框架依赖 |
| 后端 | Flask (Python) | `/api/v2/coord/*` 路由族 |
| DXF 解析 | ezdxf | Python 库，支持 DXF R12~R2018 |
| 数学库 | `coord_transform.js` / `coord_transform.py` | 前后端对称的仿射变换算法 |

### 3.2 文件清单

| 文件路径 | 职责 |
| :--- | :--- |
| `frontend/coord_workbench.html` | 工作台前端页面（SPA） |
| `frontend/coord_transform.js` | 前端仿射变换计算模块 |
| `backend/coord_transform.py` | 后端仿射变换计算模块 |
| `backend/parser_dxf.py` | DXF 解析引擎 |
| `backend/app.py` | Flask 路由注册（`/api/v2/coord/*`） |

### 3.3 API 路由

| 路由 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/coord` | GET | 提供工作台 HTML 页面 |
| `/api/v2/coord/preview` | POST | 上传 DXF 文件，返回全图层预览数据 |
| `/api/v2/coord/calibrate` | POST | 接收锚点对，返回变换矩阵与 RMSE |
| `/api/v2/coord/export` | POST | 接收标定结果 + 实体选择，返回导出 JSON |
| `/api/v2/coord/mapping` | GET/POST | 资产路径映射的持久化读写 |

---

## 4. CAD 模式：四步工作流

### Step 1: 上传与预览

- 用户上传 `.dxf` 文件
- 后端 `extract_preview_data()` 解析全部图层与图元
- 返回 `{ polylines, inserts, layers, bounds, warnings }` 至前端
- 前端在 Canvas 上渲染全部几何，右侧展示图层列表（可折叠/滚动/单层显隐切换）

### Step 2: 锚点标定

- 用户在画布上**点击已知位置**放置锚点，每个锚点填写对应的 UE 世界坐标 (X, Y)，单位 cm
- 至少 2 个锚点即可计算，推荐 3~4 个以提高精度
- 实时计算 **6 参数仿射变换矩阵**（最小二乘法）：

$$
\begin{bmatrix} ue_x \\ ue_y \end{bmatrix} = \begin{bmatrix} a & b \\ c & d \end{bmatrix} \begin{bmatrix} cad_x \\ cad_y \end{bmatrix} + \begin{bmatrix} t_x \\ t_y \end{bmatrix}
$$

- 计算质量指标：
  - **RMSE 残差**（cm）：< 50 合格 / 50~200 偏大 / > 200 不可用
  - **逐锚点残差**：高亮最大误差锚点
  - **缩放一致性**：X/Y 方向缩放比差异百分比

### Step 3: 实体管理

- 展示全部 INSERT（块引用 = 设备）和 POLYLINE（线段 = 墙体/地面）
- 每个实体显示：类型、块名/图层、CAD 坐标、UE 坐标（实时映射）
- 支持：逐行勾选、生成类型修改（INSTANCE / PROCEDURAL_WALL / PROCEDURAL_FLOOR）
- 悬停高亮画布上对应图元

### Step 4: 导出

- **JSON 导出**：调用 `/api/v2/coord/export` 生成完整场景描述文件
- **CSV 导出**：前端本地生成设备坐标表（设备ID、块名、CAD_XY、UE_XY、资产路径）
- 可选保存资产映射（块名 → SM 资产路径）供下次复用

---

## 5. 图片模式

针对无 DXF 原文件、仅有平面图截图的场景：

| 步骤 | 说明 |
| :--- | :--- |
| 上传图片 | 支持 JPG / PNG |
| 像素锚点标定 | 点击图片上已知位置，填写 UE 坐标，计算像素→UE 仿射变换 |
| 设备标注 | 点击图片标注设备位置，填写名称/ID/类型，系统自动计算 UE 坐标 |
| CSV 导出 | 导出设备名称、像素坐标、UE 坐标 |

---

## 6. DXF 解析引擎详细设计

### 6.1 支持的实体类型

| DXF 类型 | 处理方式 | 输出类别 |
| :--- | :--- | :--- |
| `LWPOLYLINE` | 直接提取顶点序列 | polylines |
| `LINE` | 提取起止点为 2 点折线 | polylines |
| `CIRCLE` | 离散为 36 段等分多边形 | polylines (closed) |
| `ARC` | 按角度离散为折线（最少 8 段） | polylines |
| `ELLIPSE` | 含旋转/长短轴比例，离散为 36 段 | polylines |
| `SPLINE` | ezdxf `flattening()` 精确采样 | polylines |
| `POLYLINE` | 旧版重量级多段线，提取顶点 | polylines |
| `INSERT` | 提取位置/块名/旋转/缩放/属性 | inserts |

### 6.2 过滤的实体类型

| DXF 类型 | 过滤原因 |
| :--- | :--- |
| `DIMENSION` | 尺寸标注线，非设备几何 |
| `TEXT` / `MTEXT` | 纯文字标签 |
| `HATCH` | 填充图案 |
| `TOLERANCE` | 公差标注 |
| `VIEWPORT` | 布局视口 |

### 6.3 复合实体处理

| DXF 类型 | 处理方式 |
| :--- | :--- |
| `LEADER` / `MULTILEADER` | 提取插入点/首顶点作为位置标记 |
| `MLINE` | 提取插入点作为位置标记 |

### 6.4 未处理实体类型

对于以上未覆盖的 DXF 实体类型，系统计数后通过 `warnings` 字段返回前端，前端以可折叠提示条形式展示（如"未渲染的实体类型: 3DSOLID x 5 个"），不再静默丢弃。

### 6.5 性能优化

- **Douglas-Peucker 降采样**：当总点数超过 20,000 时，以 bounding box 对角线 1% 为容差自动简化折线
- **图层颜色映射**：AutoCAD Color Index → HEX，支持标准 ACI 色号及算法派生色

---

## 7. 画布交互设计

### 7.1 坐标系

- **Y 轴向上**（与 AutoCAD 一致），通过 `w2s` / `s2w` 函数中 Y 取反实现
- 画布中心为相机焦点，支持任意平移和缩放

### 7.2 控制方式

| 操作 | 方式 |
| :--- | :--- |
| 平移 | 鼠标中键拖拽 / Alt + 左键拖拽 |
| 缩放 | 鼠标滚轮（以光标为中心） |
| 快速操作 | 浮动控制面板：放大(+) / 缩小(-) / 适配全图 |

### 7.3 视觉辅助

| 元素 | 说明 |
| :--- | :--- |
| 自适应网格 | 根据缩放级别自动选择网格间距（100~100,000），动态显示坐标刻度 |
| 坐标轴 | 原点处显示 X(红)/Y(绿) 轴箭头与标注 |
| 状态栏 | 实时显示光标的世界坐标与当前缩放比例 |

### 7.4 图层面板

- 默认展开，最大高度 480px，超出部分滚动条
- 每个图层显示：色块 + 名称 + 实体数 + 显隐切换
- 全局显隐切换按钮
- 解析警告折叠为一行摘要（如"3 条解析提示"），点击展开详情

---

## 8. 仿射变换算法

### 8.1 数学模型

6 参数仿射变换，支持平移、旋转、缩放、剪切：

```
dst_x = a * src_x + b * src_y + tx
dst_y = c * src_x + d * src_y + ty
```

### 8.2 求解方法

构造超定方程组 `A * params = b`，通过正规方程 `(A^T A)^{-1} A^T b` 求最小二乘解。

前端 `coord_transform.js` 与后端 `coord_transform.py` 算法完全对称，保证前后端计算结果一致。

### 8.3 质量评估指标

| 指标 | 公式 | 阈值 |
| :--- | :--- | :--- |
| RMSE | $\sqrt{\frac{1}{n}\sum{(predicted - actual)^2}}$ | < 50cm 合格 |
| 缩放一致性 | $\|scaleX - scaleY\| / max * 100\%$ | 越接近 100% 越好 |
| 逐锚点残差 | 每个锚点的预测误差 | 用于定位问题锚点 |

---

## 9. 导出数据格式

### 9.1 JSON 导出结构

```json
{
  "header": {
    "version": "1.0",
    "calibration": {
      "matrix": [[a, b, tx], [c, d, ty]],
      "rmse_cm": 12.5,
      "anchor_count": 3
    }
  },
  "entities": [
    {
      "id": "insert_001",
      "layer": "设备",
      "generate_type": "INSTANCE",
      "data": {
        "mesh_id": "SM_Equipment_A",
        "transform": { "loc": [1200, -800, 0], "rot": [0, 0, 45], "scale": [1,1,1] },
        "metadata": { "EQUIP_ID": "EQ-001" }
      }
    },
    {
      "id": "poly_001",
      "layer": "墙体",
      "generate_type": "PROCEDURAL_WALL",
      "data": {
        "path": [[0,0], [1000,0], [1000,500]],
        "height": 4500,
        "thickness": 240
      }
    }
  ]
}
```

### 9.2 CSV 导出字段

```
设备ID, 块名, 图层, CAD_X, CAD_Y, UE_X, UE_Y, UE_Z, 旋转角, UE资产路径
```

---

## 10. 与其他模块的关系

| 模块 | 关系 |
| :--- | :--- |
| **TwinSceneBuilder (PRD 2.5)** | 导出的 JSON 直接作为 TwinSceneBuilder 的输入，驱动 UE5 场景自动构建 |
| **Nexus 资产中台 (PRD 2.2)** | 实体管理中的资产路径映射对接 Nexus 资产库 |
| **AGV 巡逻组件 (PRD 2.8)** | AGV 路线坐标同样需要 CAD→UE 映射，可复用本工作台的仿射变换矩阵 |
| **PCBWorkerSync (PRD 2.7)** | 工人位置坐标同理复用变换矩阵 |

---

## 11. 已知限制与约束

1. **仅支持 DXF 格式**：不支持 DWG（DWG 为 Autodesk 私有二进制格式，需商业 SDK）。用户可通过 AutoCAD 的 `另存为 → DXF` 或 `WBLOCK` 命令转换
2. **2D 坐标映射**：当前仅处理 XY 平面，Z 轴统一为 0
3. **块内容不展开**：INSERT 实体仅提取插入点和块名，不递归展开块定义内部的几何。如需完整设备轮廓，需在 CAD 中先炸开（EXPLODE）
4. **大文件性能**：超过 20,000 个顶点时启用 Douglas-Peucker 降采样，可能损失微小细节

---

## 12. 未来演进路线

1. **DWG 支持**：集成 ODA (Open Design Alliance) SDK 或 LibreDWG 实现原生 DWG 解析
2. **块定义展开**：对 INSERT 实体递归展开块定义，渲染完整的设备轮廓图形
3. **3D 预览**：集成 Three.js 实现 DXF 3D 预览，支持楼层切换
4. **多文件叠加**：支持同时加载建筑底图 + 设备布局图 + 管线图等多 DXF 叠加显示
5. **导入实例库**：图片模式标注的设备一键导入 Nexus 实例库，完成设备台账建立
6. **坐标反向验证**：在 UE 场景截图上叠加 CAD 投影，可视化验证标定精度
