---
name: ue-super-steward
description: Safely onboard, migrate, repair, and accept Unreal Engine 5.6 projects for OntoTwin, including plugin, Actor, runtime, PIE/F8, branch, test, release, and rollback work. Use when a request includes a .uproject, UE map, OntoTwin plugin, Actor migration, roaming, camera, packaging, or UE project acceptance.
---

# UE 超级管家

这是仓库内可被其他 AI 发现的 UE 超级管家入口。它负责 UE 工程身份、插件、地图、资产、运行时行为、PIE/F8 验收和回滚证据；涉及分支、环境或发布时，必须联动 `ontotwin-product-lifecycle`。

## 联动规则

当任务同时涉及 UE 与以下任一内容时，先加载 `ontotwin-product-lifecycle`：

- `feature/*`、`dev`、`release/*`、`main`、`backup/main` 或 `hotfix/*`；
- 测试、RC/UAT、生产、发布、回滚或版本标签；
- 未提交修改、提交、上传、推送、PR、合并、删除分支或同步备份。

UE 超级管家给出 UE 证据，生命周期 Skill 决定代码应进入哪个分支、运行在哪个环境以及是否允许晋级。PIE/F8 通过不等于可以发布。

## 默认执行顺序

1. 识别 `.uproject`、目标地图、UE ProjectID、OntoTwin `ue_project_id`、`project_id`、插件版本和后端地址。
2. 只读检查当前分支、工作树、插件加载、地图和运行配置；保留不相关的用户修改，不使用 `git add .`、硬重置或无授权删除。
3. 将工作拆成一个可验收批次：插件接入、迁移、运行时、编辑器、UI 或回滚修复，并写出验收条件。
4. 在本地或明确的测试环境执行验证；记录实际 commit、环境、地图、日志和失败证据。
5. 若需要晋级，交给生命周期 Skill 检查工作树、数据库迁移、权限/项目绑定、客户专项文件、用户授权和目标分支。
6. 交付报告必须说明：包含内容、排除内容、验证结果、当前环境、当前 commit、Promotion decision（ready / blocked / rejected）和阻塞原因。

## 固定门禁

- 测试与生产必须使用独立数据库、凭据、存储和服务地址。
- 不从未提交工作树制作发布包；生产只能从 `main` 上不可变版本标签部署。
- 生成 JSON、日志、过程材料、客户专项资产和临时验收文件默认不进入平台标准发布批次。
- 数据库写入/迁移、源 Actor 清理、远程推送、PR、远端删除、`backup/main` 同步和生产发布都必须单独确认。
- 发现旧路由绕过权限、冻结或删除保护时，将批次标记为 `blocked`，不得用主流程通过替代专项验证。

## 何时不联动生命周期

仅解释 UE API/蓝图、只读查看材质或动画、或不涉及版本和环境的临时本地 PIE 检查，可以只使用本 Skill；一旦任务结果要进入 `dev`、测试、发布或生产，立即切换为双 Skill 协同。

## 可用调用方式

- 明确调用：`$ue-super-steward`。
- 自然语言触发：提到“UE 超级管家”、`.uproject`、UE 插件/地图/Actor 迁移、PIE/F8、漫游、摄像头、打包或 UE 验收。
- 生命周期联动触发：同一请求出现“接入测试环境、合并到 dev、准备发布、同步 main、回滚 UE 插件”等词时，同时加载 `$ontotwin-product-lifecycle`。
