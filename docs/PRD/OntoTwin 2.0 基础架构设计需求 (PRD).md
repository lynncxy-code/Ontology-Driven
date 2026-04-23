## 一、 2.0 核心架构大纲：三位一体映射体系

我们要构建一个以 **“映射规则集（Mapping Schema）”** 为核心的解耦架构。

1. **数据源层（Ontology）**：提供实体的实时属性（如：油量、状态、位置）。
    
2. **配置层（Mapping Console - Web）**：**本次开发的重头戏**。负责定义“逻辑属性”如何翻译成“视觉行为”，并关联对应的“资产编号”。
    
3. **资产层（Model Library）**：提供标准化的 3D 模型文件（通过【文件编号】索引）。
    
4. **表现层（UE Plugin）**：万能插头升级。它不再死盯着某一个属性，而是下载映射规则，自动解析并驱动模型。
    

---

## 二、 2.0 MVP 升级 PRD：功能与目标

### 1. 前端（Web Mapping Console）

**目标：做成“左右连线”的可视化界面，实现配置化。**

- **左侧：本体属性树（Ontology Source）**
    
    - 通过 API 获取 ObjectType 的属性列表（如：`ri.obj.airplane` 下的 `altitude`）。
        
- **中间：画布区（Mapping Canvas）**
    
    - 用户可以从左侧拖出属性节点，连线到右侧的 3D 参数节点。
        
    - 支持**转换函数（Function Node）**：例如“数值缩放”、“颜色映射（正常=绿，故障=红）”。
        
- **右侧：UE 行为参数（Target Behaviors）**
    
    - 预设标准的 3D 接口参数：`Translation`, `Rotation`, `Visibility`, `MaterialParameter`, `AnimationState`。
        
- **资产绑定区**：
    
    - 通过【文件编号】搜索模型资产库，给这个 ObjectType 绑定一个默认的 3D 外壳。
        

### 2. 后端（Logic & Rule Server）

**目标：管理“规则 JSON”，充当数据中转站。**

- **规则存储**：保存用户在前端连好的线，生成 `Mapping_Rule.json`。
    
- **资产代理**：对接模型资产库 API，当 UE 请求某个【文件编号】时，转发下载地址。
    
- **状态分发**：继续维持 `/api/state` 接口，但需支持按 `ObjectType` 批量推送数据。
    

### 3. UE 插件（DigitalTwinSync 2.0）

**目标：从“手动搬运”进化为“规则执行引擎”。**

- **动态加载（Spawn Logic）**：
    
    - 读取规则文件，发现 `ri.obj.airplane` 对应的资产是 `6D654-G3`。
        
    - 如果场景中没有该模型，自动从二级优化区下载并加载。
        
- **规则解析（Interpreter）**：
    
    - 不再硬编码 `translation_z`。而是解析规则：“如果收到 `alt` 属性，应用到 `ISpatial.translation_z`”。
        
- **多实例支持**：
    
    - 只要 Actor 的 Tag 符合规则定义的 `ObjectType`，全部自动继承该映射逻辑。
        

---

## 三、 Vibe Coding 实施指南（给 AI 的 Prompt 建议）

你可以分三步来调教你的 AI：

### 第一步：定义映射规则 JSON（后端/前后端契约）

> “请设计一个 JSON 结构，用于描述本体属性到 UE 行为的映射。需要包含：`objectTypeRid`、绑定的模型库`file_number`、以及一个映射数组。数组内每个项包含 `source_property`（如 alt）、`target_behavior`（如 Transform.Z）和 `transform_logic`（如数值转换系数）。”

### 第二步：开发 Web 连线界面（前端）

> “请使用 Vue.js 和一个连线库（如 Vue Flow 或 LiteGraph.js），开发一个映射控制台。左侧显示从 API 获取的本体字段，右侧显示 UE 预设行为（位置、旋转、颜色、动画）。用户连线后，点击‘发布’，将映射规则以 JSON 格式 POST 到后端。”

### 第三步：升级 UE 万能插头（UE 5）

> “请重构 UE5 插件逻辑。
> 
> 1. 启动时访问 `/api/mapping/rules` 获取所有映射规则。
>     
> 2. 遍历场景中带有特定 Tag 的 Actor。
>     
> 3. 根据规则，从模型库 API 动态加载模型资产。
>     
> 4. 根据规则，将 `/api/state` 返回的业务属性实时分发给 Actor 的对应组件（位置、材质、动画）。”
>