# OntoTwin 3.3 — 运行时模型加载与 ArtStudio 资产同步（PRD）

> 版本：3.3
> 依据：2.1 DigitalTwinSync（轮询驱动 Actor）+ 2.2 Nexus 资产中台（ArtStudio 接入）+ 2.6 中间层轮询同步接口
> 本轮范围：Phase 0 已落地（glTFRuntime 运行时加载，本仓 commit `5c0e6fd`）；Phase 1~3 为 ArtStudio 直连同步，本 PRD 主体。
> 适用：单人开发，不过度工程化。

---

## 1. 背景

数字孪生的渲染资产此前走 UE 烘焙：模型要先导入工程、`Cook` 进 `.pak`，对象类型绑 `/Game/...` 路径。痛点：

- **改一个模型就要重新打包 exe**——与 ontotwin"数据驱动、配置即生效"的理念冲突；
- 美术在 ArtStudio 资产库里更新了模型，运行中的孪生体感知不到；
- 资产库是真实的事实来源（studio.xjbg.tech），但 UE 侧与它完全脱节。

目标：**模型不参与打包，运行时按 `ue_asset_path` 动态加载；用户在配置中心改绑定，运行中的 exe 直接同步变更。**

---

## 2. 现状（Phase 0，已完成）

已落地并提交（commit `5c0e6fd`），作为本轮基座：

- 引入 **glTFRuntime** 插件，运行时把磁盘上的 `.glb` 解析成动态网格，`SetStaticMesh` 换成插件生成的运行时网格 —— 模型**从不进 Cooker**。
- `LoadMeshFromPath` 分流：`/Game/` 烘焙资产走 `LoadObject`（向后兼容）；其余当 glb 运行时加载；失败回退占位 Cube。
- `ResolveModelFilePath` 固定目录（`DefaultGame.ini` 的 `[OntoTwinSync] ModelsDir` 可配）置顶 + exe 相对兜底 —— 编辑器与打包 exe **共用一份 Models，换模型零拷贝零重打包**。
- 打包配置 `+DirectoriesToAlwaysCook=(Path="/glTFRuntime")` —— 修复母材质未 cook 导致的**贴图丢失**。
- 后端 bind 接口识别 `.glb/.gltf` 为本地运行时资产（`valid=true`）。

**遗留**：模型仍是手工放进固定目录的本地散文件；与 ArtStudio 无连接。本轮解决。

---

## 3. 名词

| 词 | 含义 |
|---|---|
| ArtStudio | 模型资产库，`http://studio.xjbg.tech:12345/api`，资产以数字 id 标识 |
| 资产详情 | `GET /api/assets/{id}` → `data.files[].downloadUrl`（S3 预签名直链，有效期约 1h），含 `currentVersion` |
| `ue_asset_path` | 对象类型上绑定的渲染资产标识；本地走 filename，ArtStudio 走稳定标识 |
| 稳定标识 | `artstudio:{id}:v{version}` —— snapshot 里下发给 UE 的 asset_id，**跨轮询不变**，仅绑定变更或资产升版时才变 |
| 下载代理 | 后端新增路由，UE → Flask → ArtStudio S3 流式转发字节，隐藏 S3/token/presigned |

---

## 4. 已决策（2026-06-26）

1. **下载方式 = 后端代理转发**。UE 只认 Flask 一个地址；后端隐藏 S3/token/presigned 细节。孪生模型数量少，代理带宽不是瓶颈。
2. **本期只支持 glb**。库里 fbx/usd 资产绑定时过滤/提示，不让绑。格式转换（Blender headless / Assimp → glb）作为独立后续项。
3. **带版本号同步**。snapshot 携带 `currentVersion`；资产在 ArtStudio 被重传（同 id 新版本）→ 稳定标识 `:v{n}` 变化 → 触发热更换重下。后端查 ArtStudio 版本结果加短缓存，避免每次 snapshot 都打库。

---

## 5. 关键设计：复用既有同步骨架

运行时同步**不需要新建机制**，2.1/2.6 的轮询 + 热更换已经具备：

```
TwinSceneManager 每 N 秒轮询 snapshot
   └─ 每实例 I3D_Representable.asset_id
        └─ TwinInstance 检测 asset_id 变化 → 热更换重载（TwinInstance.cpp:456）
```

本轮要做的只是：**让 asset_id 能携带 ArtStudio 资产 + UE 据此下载**。版本同步几乎免费——`v{version}` 变化即复用热更换。

**坑①**：S3 预签名 URL ~1h 过期，**绝不能把 URL 当 asset_id 下发**（轮询频繁会让 URL 每次都变 → UE 误判持续热更换 → 重下风暴）。必须用稳定标识，下载时再现取新鲜 URL。

---

## 6. 数据结构 / 接口变更

### 6.1 对象类型绑定（后端存储，结构不变，仅语义扩展）

```jsonc
object_type = {
  …,
  "asset_id": "328748...",            // ArtStudio 数字 id（或本地 glb 文件名）
  "ue_asset_path": "artstudio:328748...:v1"   // 稳定标识；本地仍为 filename
}
```

### 6.2 snapshot（推给 UE，I3D_Representable）

```jsonc
"I3D_Representable": {
  "asset_id": "artstudio:328748...:v1",   // ★ 稳定标识，跨轮询不变
  "file_number": "328748...",
  "is_visible": true
}
```

### 6.3 新增后端路由

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v2/assets/download?id={id}` | 后端调 ArtStudio 详情拿 `downloadUrl` → 流式转发字节给 UE。仅 glb。 |
| —（改造） | bind 接口 | 绑 ArtStudio id 时查详情：非 glb 拒绝；glb 则写 `ue_asset_path = artstudio:{id}:v{version}` |
| —（改造） | snapshot 构建 | ArtStudio 资产的 `ue_asset_path` 透传为 asset_id；version 查询加短缓存（TTL 例如 30s） |

---

## 7. 分阶段实现

### Phase 1 — 后端
- [ ] bind 接口：绑 ArtStudio 数字 id 时拉详情，校验格式（非 glb 返回 warning、不写绑定），glb 则组装 `artstudio:{id}:v{version}`。
- [ ] snapshot：ArtStudio 资产下发稳定标识；version 加 TTL 缓存。
- [ ] 下载代理路由 `/api/v2/assets/download`：流式 `requests.get(downloadUrl, stream=True)` → `Response(stream_with_context(...))`。

### Phase 2 — UE
- [ ] `LoadMeshFromPath` 加分流：`artstudio:` 前缀 → 走 `LoadRemoteGltf`。
- [ ] `LoadRemoteGltf`：异步 `FHttpModule` 拉 `/assets/download?id=` → 存缓存 `Saved/ModelCache/{id}_v{version}.glb` → 复用 `LoadRuntimeGltf` 加载；已缓存则跳过下载。
- [ ] 下载期间维持占位 Cube，回调里替换；**弱引用保护**（实例可能在回调前销毁）。

### Phase 3 — 版本同步
- [ ] 复用热更换：`v{version}` 变 → asset_id 变 → 自动重下重载。缓存 key 含 version，旧版本文件可保留或定期清理。

---

## 8. 验收

1. 配置中心给对象类型绑一个 ArtStudio **glb** 资产 → 运行中的 exe 下个轮询周期自动出现该模型（带材质贴图）。
2. 配置中心改绑成另一个 glb 资产 → exe 自动换模型，无需重启。
3. 在 ArtStudio 重传该资产（升版本）→ exe 自动重下新版本。
4. 绑一个 **fbx/usd** 资产 → 配置中心提示"暂不支持非 glb"，不写入绑定。
5. 断网 / ArtStudio 不可达 → exe 维持占位 Cube，不崩溃。

---

## 9. 风险

- **格式墙**：仅 glb，库里 fbx/usd 占比若高，可用资产受限。转换管线是后续大项。
- **首屏延迟**：大模型下载数秒，占位 Cube 期间体验割裂；可加进度/淡入优化（非本期）。
- **异步生命周期**：下载回调跨帧，实例销毁 / 资产再次变更的竞态要弱引用 + version 校验兜住。
- **可移植性**：固定目录默认值写死本机盘符；ArtStudio 同步落地后，本地固定目录退化为缓存兜底，可移植性问题随之缓解。
