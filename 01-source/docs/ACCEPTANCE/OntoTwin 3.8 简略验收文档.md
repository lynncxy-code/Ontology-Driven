# OntoTwin 3.8 简略验收文档

日期：2026-07-28  
范围：OntoTwin Nexus 3.8 Web 交互与业务视图联动

## 1. 验收结论

3.8 开发内容已完成，后端完整自动化回归、Nexus 工作台浏览器冒烟测试，以及 UE Editor、Development、Shipping 三种目标编译链接均已通过。

当前可进入实际关卡联调。PIE/Standalone 交互、三档玻璃效果、100 次切换与资源泄漏仍需在目标关卡中人工验收；完成这些项目后才能标记为 3.8-GA。

## 2. 已交付能力

- Nexus“场景交互 → Web 交互”工作台：页面资源、BusinessView、绑定、解析预览、发布和回滚。
- 页面绑定优先级：`Instance > Zone+Type > Type > Zone > Project`；业务视图为 `BusinessView > Project`；支持 `block`。
- Zone 层级、叶子 Zone 绑定、BusinessView 多规则组与排除实例。
- 独立 runtime revision 接口；一期使用 HTTP 轮询，WebSocket 通知已保留在 TODO。
- UE 单例全屏 Web 宿主、High/Balanced/Performance 三档外框、加载/失败/返回/关闭状态。
- Bridge 1.0 握手、交互区域上报、实例选择/聚焦、固定范围跳转。
- Zone、BusinessView、BusinessView + Zone 的实例显隐；未分区实例保持常驻，0 匹配不回退。
- URL 协议、内嵌凭据、域名白名单和当前激活项目校验；Shipping 默认白名单模式。

## 3. 自动验收记录

| 项目 | 结果 | 记录 |
|---|---|---|
| 后端完整回归 | 通过 | 126 项测试全部通过 |
| Web 工作台加载 | 通过 | 页面正常显示当前项目、revision、未分区警告，无测试数据残留 |
| 页面资源草稿 | 通过 | 新建、参数映射、保存草稿成功 |
| 解析预览 | 通过 | 无绑定时返回可解释的未命中结果 |
| Runtime revision | 通过 | 已知 revision 返回 `unchanged` |
| UE Editor | 通过 | `DigitalFactoryBaseEditor Win64 Development` 编译链接成功 |
| UE Development | 通过 | `DigitalFactoryBase Win64 Development` 编译链接成功 |
| UE Shipping | 通过 | `DigitalFactoryBase Win64 Shipping` 编译链接成功 |

说明：UE Web 宿主复用项目现有 WebUI 浏览器内核，未同时启用 UE 内置 WebBrowserWidget，已消除两套 CEF 的链接冲突。

## 4. 人工验收步骤

1. 在 Web 交互工作台注册 S3 页面：`http://localhost:5000/ue_hud/pages/s3-building.html`，将 `zone_id` 映射为 `space_id`。
2. 新建一个 Zone 绑定和一个 BusinessView 绑定，先运行解析预览，再发布；确认 revision 加一。
3. 在 UE PIE 中分别激活 Project、Zone、BusinessView 和 Instance，确认只存在一个网页宿主，页面地址与场景显隐符合绑定结果；Zone/BusinessView 按最终成员联合包围盒平滑取景，Instance 按单模型包围盒平滑聚焦。空范围不得移动镜头，未分区常驻实例不得扩大 Zone/BusinessView 取景范围。
4. 点击页面真实控件，确认网页可交互；点击透明非交互区，确认输入交还 UE；未握手普通网页应整页接收输入。
5. 测试危险协议、非白名单跳转、重定向和新窗口，确认被拒绝；断开网页服务后确认可重试、返回和关闭。
6. 分别选择 High、Balanced、Performance，确认网页文字和点击区域始终清晰，玻璃只在网页下层。
7. 连续执行 100 次页面/实例切换，确认无多余浏览器、不可见输入层、残留回调或明显内存持续增长。
8. 在 Standalone 和最终打包版本重复第 3—7 步；正式部署前配置项目域名白名单。

实例聚焦补充检查：在 F7 人物漫游中再次选择同一实例，人物位置不得被传送，镜头应切换到观察相机并完整框住实例；按 `V` 应返回人物视角。该聚焦是一次性取景，不持续跟踪移动实例。

## 5. 验收边界

- 3.8 通过实例显隐减少绘制量，不减少首次模型加载时间和内存占用。
- 多 Zone 差量加载、关卡流送、加载前 BusinessView 过滤属于第二、三期。
- WebSocket 仅作为后续 revision 变更加速通知；HTTP 继续作为完整配置获取与断线兜底。

## 6. SCC W19 业务管理测试剧本（2026-08-12）

当前激活项目已准备一套可直接在 UE 中验收的受管场景：共 20 个实例、16 个本体类型、9 个层级分区。新增数据包含 5 个用户已有能源设备和 9 个 ArtStudio 测试实例；另有原来的 6 个 ICT 实例。

### 6.1 分区结构

- `SCC W19 厂房`
  - `SCC W19 1F`
    - `1F ICT 设备区`：原有 6 个 ICT 实例
    - `1F SMT 生产区`：输送机、AGV、物料托盘
    - `1F 物流暂存区`：叉车、AGV、周转箱
    - `1F 能源站房`：储能电池柜、应急发电机、循环油泵
  - `SCC W19 2F`
    - `2F 总装区`：输送机、AGV
  - `室外可再生能源区`：光伏阵列、风力发电机

另保留 `临时待定物料托盘 PL-99` 为未分区实例，用于验证“未分区实例常驻”规则。

### 6.2 五个能源实例

| 实例 | 分区 | 主要测试属性 |
|---|---|---|
| 屋顶光伏阵列 01 | 室外可再生能源区 | 额定功率 120 kW；当日发电量 486.2 kWh；健康度 96 |
| 厂区风力发电机 01 | 室外可再生能源区 | 额定功率 80 kW；风速 6.8 m/s；健康度 91 |
| 储能电池柜 BESS-01 | 1F 能源站房 | 容量 500 kWh；SOC 76%；健康度 94 |
| 柴油应急发电机 DG-01 | 1F 能源站房 | 额定功率 320 kW；燃油 82%；健康度 88 |
| 能源站循环油泵 P-01 | 1F 能源站房 | 流量 38.5 m³/h；出口压力 0.62 MPa；健康度 79 |

风机的塔体和叶轮合并为 1 个实例，油泵的 16 个网格散件合并为 1 个实例。因此业务、属性和显隐均按设备而不是网格零件计算。

### 6.3 三套业务

| 业务 | 选取逻辑 | 命中 | 页面 |
|---|---|---:|---|
| 能源管理 | 室外能源区 + 1F 能源站房 | 5 | 能源管控总览 |
| 移动设备运维 | 全厂 AGV + 叉车，跨 SMT、物流、总装区 | 4 | S3 厂房总览 |
| 重点设备巡检 | 指定发电机、油泵、叉车、AGV、ICT 测试机，再排除检修中的 AGV-02 | 4 | 事件台账 |

每次业务激活后，除命中实例外还会显示 1 个未分区托盘。这是故意保留的边界测试，所以场景可见数依次为 6、5、5。

### 6.4 最短验收步骤

1. 启动后端并打开 SCC2 主关卡，确认场景中存在 `TwinSceneManager`。
2. 进入 PIE 或 Standalone；首次加载 ArtStudio 模型时等待下载完成。
3. 打开场景交互面板，依次激活“能源管理”“移动设备运维”“重点设备巡检”。
4. 确认页面依次打开能源总览、厂房总览、事件台账，URL 带有对应的 `business_view_id`。
5. 确认三次场景可见数分别为 6、5、5；其中都包含未分区托盘 `PL-99`。
6. 再激活单个叶子分区，检查父子分区层级和分区内实例是否与 6.1 一致。

说明：五个能源模型的原始关卡 Actor 已备份后移除，运行时由 OntoTwin 实例接管，避免重影。关卡备份位于 `D:\SCC\SCC2\scc2\Saved\OntoTwinBackups\3.8_business_acceptance_20260812`；数据库写入前快照位于 `backend/tools/scc_w19_business_acceptance_backup.json`。
