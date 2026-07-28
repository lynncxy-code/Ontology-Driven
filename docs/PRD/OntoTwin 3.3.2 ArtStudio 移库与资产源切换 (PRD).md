# OntoTwin 3.3.2 — ArtStudio 移库与资产源切换（PRD）

> 版本：3.3.2  
> 所属主线：OntoTwin Nexus  
> 所属模块：资产中台 / 模型绑定 / UE 运行时同步  
> 父级需求：OntoTwin 3.3 运行时模型加载与 ArtStudio 资产同步  
> 前置补丁：OntoTwin 3.3.1 资产模块模型绑定交互补丁  
> 状态：已实施  
> 日期：2026-07-24

---

## 1. 背景

ArtStudio 已启用新的站点与资产库：

```text
旧站点：http://studio.xjbg.tech:12345/
旧 API：http://studio.xjbg.tech:12345/api

新站点：https://artstudio.digioasis.tech/
新 API：https://artstudio.digioasis.tech/api
```

OntoTwin Nexus 当前仍在 `backend/app.py` 与 `backend/artstudio_client.py` 中使用旧 API。只替换域名虽然可以重新加载列表，但不能完整解决以下问题：

1. 新旧站点连接的是不同资产数据集，资产 id 不能原样视为已迁移。
2. ArtStudio 列表搜索使用 `keyword`，Nexus 当前向上游发送 `q`，搜索不会生效。
3. ArtStudio 的所有者枚举为 `1=组织、2=个人`，Nexus 页面当前标注相反，且后端没有转发该筛选条件。
4. 新库同时存在 GLB 与 FBX；OntoTwin 3.3 运行时链路本期仍只支持 GLB。
5. 旧地址被硬编码在两个模块中，不利于后续环境切换和回滚。

因此，本需求将本次变更定义为一次有明确边界、可验证、可回滚的资产源切换，而不是简单的文本替换。

---

## 2. 现状核验

2026-07-24 对两个公开资产接口进行只读核验：

| 项目 | 旧库 | 新库 |
|---|---:|---:|
| 公开资产总数 | 18 | 4 |
| GLB | 13 | 2 |
| FBX | 4 | 2 |
| 其他格式 | 1 USDA | 0 |
| 新旧资产 id 交集 | 0 | 0 |

新库当前资产：

| id | 名称 | 格式 | 可绑定 |
|---|---|---|---|
| `337876966847811584` | labubu | GLB | 是 |
| `337856526880346112` | agv | GLB | 是 |
| `335366060637163520` | 书桌 | FBX | 否 |
| `335353419894099968` | 不知道是啥 | FBX | 否 |

接口契约仍兼容 OntoTwin 3.3 的核心读取逻辑：

- 列表：`data.list`、`data.total`、`data.page`、`data.size`。
- 资产字段：`id`、`name`、`fileExtensions`、`coverUrl`、`currentVersion`。
- 详情字段：`data.files[].displayName`、`data.files[].downloadUrl`、`data.currentVersion`。
- 下载地址迁移到 `https://s3.digioasis.tech/...`，仍为 S3 预签名 URL。

当前激活项目核验结果：

- 80 个类型中没有 ArtStudio 类型级绑定。
- 228 个实例中没有 `artstudio:` 运行时引用。
- 历史备份中发现 `artstudio:328826891106521088:v1`；该旧 id 在新库返回 404。

因此，当前激活项目不需要写入式数据迁移；历史项目如恢复，必须进行显式重新绑定，禁止按名称猜测映射。

---

## 3. 目标

1. 将 Nexus 的 ArtStudio 资产源切换到 `https://artstudio.digioasis.tech/api`。
2. 把 ArtStudio 地址、超时和可选 Token 改为环境配置，保留快速回滚能力。
3. 修正搜索参数和所有者筛选，使 Nexus 资产列表与新库契约一致。
4. 保持超长资产 id 全链路为字符串，避免 JavaScript 数值精度损失。
5. 在资产选择界面明确区分“可绑定 GLB”和“暂不支持的其他格式”。
6. 保持现有 `artstudio:{id}:v{version}` 稳定标识、Flask 下载代理和 UE 缓存协议不变。
7. 不修改 ProjectStore JSON、PostgreSQL 表、对象类型字段或实例字段结构。

---

## 4. 非目标

- 不在本需求中向新 ArtStudio 上传、覆盖或删除资产。
- 不自动生成旧 id 到新 id 的映射。
- 不按资产名称自动重绑，避免同名模型误配。
- 不实现 FBX/USD 到 GLB 的自动转换。
- 不修改现有前端页面路由或 UE HTTP 协议。
- 不引入新 Python、UE 依赖或前端构建工具；登录加密仅通过 CDN 引入 JSEncrypt。
- 不建设双库聚合、异步队列或复杂资产治理系统。

---

## 5. 已决策方案

### 5.1 迁移模式

采用“单一活动资产源 + 环境变量回滚”：

```text
ARTSTUDIO_BASE_URL=https://artstudio.digioasis.tech/api
ARTSTUDIO_TIMEOUT=5
# 可选：仅用于无人值守部署或管理员调试回退
ARTSTUDIO_TOKEN=
```

运行时只访问一个 ArtStudio，不把旧库与新库混在同一列表。普通用户不需要获取或填写 Token，直接在“我的资产”中连接 ArtStudio 账号；需要回滚时修改环境变量并重新创建后端容器。

### 5.2 API 适配

Nexus 对外仍保留现有接口：

```text
GET /api/v2/assets?source=studio&page=1&size=10&q=...
```

后端向 ArtStudio 转换为：

```text
GET {ARTSTUDIO_BASE_URL}/assets?page=1&size=10&keyword=...
```

筛选映射：

| Nexus 参数 | ArtStudio 参数 | 规则 |
|---|---|---|
| `q` | `keyword` | 空值不发送 |
| `category` | `category` | 枚举保持 1–5 |
| `ownerType` | `ownerType` | `1=组织、2=个人` |
| `sort` | `sort` | 默认 `newest` |

### 5.3 格式可用性

- `fileExtensions` 包含 `GLB`：`bindable=true`。
- 不包含 `GLB`：`bindable=false`，资产仍显示，但不能被选中绑定。
- 后端 bind 接口继续进行最终详情校验，前端禁用态不能替代服务端校验。
- 前端“本地默认资产库”入口替换为“我的资产”；旧 mock 接口仅保留兼容，不再作为绑定台入口。

### 5.4 id 与版本

- ArtStudio `id` 在 Python、JSON、JavaScript 和 UE URL 中始终作为字符串处理。
- 稳定标识继续使用 `artstudio:{id}:v{currentVersion}`。
- S3 预签名 URL 不进入 ProjectStore，也不下发为稳定 id。

### 5.5 个人身份与“我的资产”

- 用户在“我的资产”中输入 ArtStudio 用户名、密码和图形验证码，不需要理解或手工复制 Token。
- Nexus 先读取 ArtStudio 登录公钥；密码在浏览器内使用 RSA PKCS#1 v1.5 加密，清空明文后仅将密文提交给本机后端。
- 本机后端按 ArtStudio 官方账号登录协议换取 Token，再通过 `GET {ARTSTUDIO_BASE_URL}/auth/user/info` 校验身份；页面和 Nexus API 均不返回 Token。
- 当前设备仅保存 `access_token` 和 `tenant_id` 到 Git 忽略的 `backend/data/.artstudio_session.json`，不保存用户名、密码、验证码或密码密文。
- 登录与断开接口只接受当前 Nexus 同源页面的浏览器写请求；无 `Origin` 的本机管理脚本保留兼容能力。
- `ARTSTUDIO_TOKEN` 仅作为无人值守部署或管理员调试回退，普通用户流程不依赖 `.env`。
- “我的资产”查询固定携带 `ownerType=2&mine=true`，且必须先通过身份校验。
- 未登录、无效或过期会话返回明确的 401，不得退化为匿名公开资产。
- “断开连接”会清除运行时凭据和当前设备会话文件；ArtStudio 公开资产始终匿名可读。

### 5.6 UE 边界

UE 继续请求：

```text
{BackendBaseUrl}/api/v2/assets/download?id={assetId}
```

UE 不直接感知 ArtStudio 或 S3 域名，因此本次不修改 UE 插件。

---

## 6. 实施范围

### 6.1 后端配置

修改 `backend/app.py`：

- 从环境变量读取 `ARTSTUDIO_BASE_URL`、`ARTSTUDIO_TIMEOUT`、`ARTSTUDIO_TOKEN`。
- 新地址作为默认值。
- 对 base URL 去除末尾 `/`，避免路径出现双斜杠。

修改 `backend/artstudio_client.py`：

- 默认地址更新为新 API。
- `configure()` 统一规范化 base URL。
- 增加运行时 Token/tenant 切换、请求头生成与 `/auth/user/info` 身份校验。
- 文档注释更新为新域名。

新增 `backend/artstudio_auth.py`：

- 代理 ArtStudio 公钥、验证码开关和图形验证码。
- 接收浏览器端加密后的密码，完成账号登录与身份复核。
- 只持久化 Token 和 tenant，不保存用户凭据。
- 提供当前设备断开连接，并对浏览器写请求执行同源校验。

修改 `docker-compose.yml`：

- 为 backend 注入上述三个环境变量。

### 6.2 列表适配

修改 `GET /api/v2/assets` 的 ArtStudio 分支：

- `q` 转为 `keyword`。
- 读取并转发 `ownerType`。
- `source=mine` 先校验当前登录会话，再固定转发 `ownerType=2&mine=true`。
- 标准化 `fileExtensions`。
- 返回 `formats` 与 `bindable`。
- `file_number` 和 `_source.artstudio_id` 均返回字符串。

### 6.3 前端交互

修改本体配置中心资产选择区域：

- 将“本地默认资产库”标签改为“我的资产”。
- 进入“我的资产”时自动校验当前设备会话，并行内显示当前用户或连接状态。
- 未连接时提供“连接账号”弹窗，包含用户名、密码、验证码和验证码刷新。
- 登录过程中提供禁用/加载状态，错误在弹窗内就地显示；支持 ESC、遮罩关闭和焦点返回。
- 已连接时提供“断开连接”，清除本机登录状态并清空个人资产列表。
- 修正所有者选项为 `组织资产=1、个人资产=2`。
- 不可绑定格式使用灰色禁用态。
- 卡片行内显示“暂不支持运行时绑定”。
- 点击不可绑定卡片不改变当前选择。
- 确认按钮对不可绑定资产保持禁用。
- 保持极简黑白灰，不新增 emoji、原生弹窗或大面积语义色。

---

## 7. 数据迁移规则

本需求不改变任何存储结构，数据处理遵守以下规则：

1. 当前激活项目无 ArtStudio 引用，不执行写入。
2. 已保存的旧 `asset_id` 和 `ue_asset_path` 不做批量替换。
3. 旧 id 在新库不存在时，保留原值并在使用时进入现有不可达/占位模型降级路径。
4. 只有用户明确选择新库资产后，才通过现有 bind 接口写入新 id。
5. 若后续需要恢复历史项目，先产出人工确认的映射表，再调用现有 bind 接口逐项迁移。

禁止直接修改 ProjectStore 文件、PostgreSQL JSON 字段或备份文件。

---

## 8. 回滚

代码不需要回滚即可切回旧源：

```text
ARTSTUDIO_BASE_URL=http://studio.xjbg.tech:12345/api
```

修改环境变量并重新创建 backend 容器后：

- 列表、详情、版本查询和下载代理重新访问旧库。
- `keyword`、`ownerType` 等适配对旧版同契约接口保持兼容。
- 已保存的稳定标识格式不变。

若旧服务停止，则回滚仅保留为配置能力，不保证旧源可用性。

---

## 9. 验收标准

### 9.1 配置与列表

1. 默认启动后，`GET /api/v2/assets?source=studio` 返回新库资产。
2. 当前数据下总数为 4，且资产 id 与新 ArtStudio 一致。
3. `q=labubu` 只返回 `labubu`。
4. `ownerType=2` 返回个人资产；`ownerType=1` 不返回个人资产。
5. 封面从 `s3.digioasis.tech` 正常加载。

### 9.2 格式与绑定

6. GLB 资产显示为可选并可发起绑定。
7. FBX 资产保持可见，但显示禁用说明且不能提交绑定。
8. 绑定 GLB 后保存：

```text
asset_id={新库字符串 id}
ue_asset_path=artstudio:{新库字符串 id}:v1
```

9. 直接调用 bind 接口绑定 FBX 时仍被服务端拒绝，且不写入绑定。

### 9.3 身份与我的资产

10. 登录弹窗可取得真实 ArtStudio 公钥和图形验证码，验证码可以刷新。
11. 浏览器登录请求不包含明文密码；后端会话文件不包含用户名、密码、验证码或密码密文。
12. 登录成功后返回标准化用户信息，“我的资产”仅展示该用户的个人资产。
13. 后端重启后可恢复当前设备会话；断开连接后运行时凭据和设备会话文件均被清除。
14. 未登录、无效或过期会话下，身份接口和 mine 列表均返回 401，且不返回公开资产。
15. 非同源浏览器不能调用账号登录或断开接口。
16. 公开资产列表在未登录时仍可正常读取。

### 9.4 下载与 UE

17. `/api/v2/assets/download?id={GLB id}` 返回 `model/gltf-binary`。
18. 后端能够访问新的 HTTPS S3 预签名地址。
19. UE 侧无需改动，仍通过 Flask 下载代理加载模型。

### 9.5 回归

20. 路径直连、UE `/Game/...` 引用和历史实例模型提升功能不受影响。
21. Python 文件通过语法检查，前端脚本无语法错误。
22. ProjectStore/PostgreSQL 数据结构无变化。

---

## 10. 风险与处理

| 风险 | 影响 | 处理 |
|---|---|---|
| 新旧 id 完全不同 | 历史绑定在新库不可解析 | 不猜测映射；人工确认后重绑 |
| 新库可用 GLB 数量少 | 资产选择范围缩小 | 显示 FBX 但禁用；格式转换另立需求 |
| HTTPS/DNS 在部署环境不可达 | 列表和下载失败 | 保留超时、错误提示和环境变量回滚 |
| 用户凭据泄漏 | ArtStudio 账号暴露 | 密码在浏览器内公钥加密并立即清空；后端只接收密文且不落盘 |
| Token 泄漏 | 个人资产权限暴露 | Token 仅进入 Git 忽略的设备会话文件和后端请求头，API/日志/页面均不回传 |
| 跨站调用本机账号接口 | 当前连接被恶意替换或断开 | 登录与断开仅接受当前 Nexus 同源浏览器请求 |
| 匿名 mine 参数被上游忽略 | “我的资产”误显示公开个人资产 | Nexus 先强制校验 `/auth/user/info`，失败即返回 401 |
| 组织资产需要租户上下文 | 个人 Token 不能代表组织选择 | 本期只实现个人资产；组织身份接入另立需求 |
| 预签名 URL 过期 | 长期保存后下载失败 | 每次下载前重新查询详情，不保存 URL |

---

## 11. 实施清单

- [x] 新增本 PRD。
- [x] 后端 ArtStudio 配置环境化并切换新地址。
- [x] 修正搜索和所有者筛选参数。
- [x] 资产列表返回格式可用性。
- [x] 前端修正所有者枚举与不可绑定态。
- [x] “本地默认资产库”入口替换为“我的资产”。
- [x] 增加 ArtStudio 用户名、密码、验证码登录弹窗。
- [x] 增加浏览器端公钥加密、登录会话持久化与断开连接。
- [x] 增加身份校验接口与 mine 查询强制校验。
- [x] 增加每机 `.env.example` 配置模板。
- [x] Python 静态检查。
- [x] 新库列表、搜索、筛选、详情和 S3 下载联调。
- [x] 本地 `/api/v2/assets` 迁移后验证。
- [x] 记录旧绑定审计结果，不写入数据。

---

## 12. 实施结果（2026-07-24）

- backend 已默认切换到 `https://artstudio.digioasis.tech/api`。
- 本地列表返回新库 4 个资产：2 个 GLB 可绑定、2 个 FBX 禁用。
- 搜索 `labubu` 返回 1 个结果。
- `ownerType=2` 返回 4 个个人资产，`ownerType=1` 返回 0 个组织资产。
- “我的资产”标签、账号连接弹窗、身份状态、断开连接和行内错误提示已接入。
- 实时登录 challenge 已联通 ArtStudio：公钥加密开启，图形验证码可加载和刷新。
- 浏览器侧已验证 JSEncrypt 可按实时公钥生成密码密文；提交前会立即清空明文密码。
- 浏览器拦截验证登录请求只包含 `encrypted_password`，不包含 `password` 明文字段。
- 后端模拟成功登录已验证只保存 Token/tenant，不保存用户名、密码、验证码或密文。
- 跨站 Origin 调用登录/断开接口返回 403；公开资产详情在失效会话下可匿名回退。
- 未登录时，身份接口与 mine 列表均返回 401，且不返回公开资产。
- 未使用真实个人账号执行登录；真实账号成功登录与个人资产内容由用户在页面输入凭据后验收。
- 公开资产保持匿名可读：本地验证返回 4 个资产，其中 2 个 GLB 可绑定。
- GLB 下载代理 HEAD 验证返回 200、`model/gltf-binary`、10,669,420 字节。
- FBX 通过下载代理验证返回 404，未进入运行时加载链路。
- 浏览器验证通过：FBX 点击后绑定按钮保持禁用，GLB 点击后按钮启用。
- 页面无新增运行时错误；仅存在项目原有的 Tailwind CDN 开发提示。
- 未修改任何项目数据、数据库记录、备份文件或 UE 代码。
