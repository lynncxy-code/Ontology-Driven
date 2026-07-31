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
3. 在 UE PIE 中分别激活 Project、Zone、BusinessView 和 Instance，确认只存在一个网页宿主，页面地址与场景显隐符合绑定结果。
4. 点击页面真实控件，确认网页可交互；点击透明非交互区，确认输入交还 UE；未握手普通网页应整页接收输入。
5. 测试危险协议、非白名单跳转、重定向和新窗口，确认被拒绝；断开网页服务后确认可重试、返回和关闭。
6. 分别选择 High、Balanced、Performance，确认网页文字和点击区域始终清晰，玻璃只在网页下层。
7. 连续执行 100 次页面/实例切换，确认无多余浏览器、不可见输入层、残留回调或明显内存持续增长。
8. 在 Standalone 和最终打包版本重复第 3—7 步；正式部署前配置项目域名白名单。

## 5. 验收边界

- 3.8 通过实例显隐减少绘制量，不减少首次模型加载时间和内存占用。
- 多 Zone 差量加载、关卡流送、加载前 BusinessView 过滤属于第二、三期。
- WebSocket 仅作为后续 revision 变更加速通知；HTTP 继续作为完整配置获取与断线兜底。
