# OntoTwin Nexus · 逆向建模 Beta

这是一个与 OntoTwin 主工具隔离的试验页面。它只复用当前本地运行的 Hunyuan3D 服务，不修改 Hunyuan3D 源码、OntoTwin 主前端、后端存储、UE 工程或 Git 主线。

## 使用方法

1. 双击 `D:\AI\Hunyuan3D-2.1-local\start_hunyuan3d_multiview.bat`，启动 Hunyuan3D-2mv，并确认服务地址为 `http://127.0.0.1:8081/`。
2. 双击 `start_reverse_modeling.bat`。
3. 浏览器打开 `http://127.0.0.1:8766/`。

不要直接双击 `index.html`：生成、导出和样例读取都需要本目录中的本地桥接服务。

## 已保留的原始能力

- 上传正面、后面、左侧、右侧 1–4 张 PNG、JPG 或 WebP 参考图，其中正面必需；
- 生成几何模型或带纹理模型；
- 去背景、随机种子及高级生成参数；
- 交互式三维结果查看；
- 导出 GLB、OBJ、PLY、STL，并可选择简化网格与目标面数；
- 生成完成但桥接任务中断时，可恢复最近一次本地多视图结果，无需重新推理；
- 使用 Hunyuan3D 自带样例图片。

## 产品边界

“逆向建模”是面向业务用户的入口名称，底层调用 Hunyuan3D-2mv 多视图 AI 三维近似重建。结果适合概念验证、数字孪生素材草拟和后续人工修整，不替代测量、CAD 工程模型或正式设计验收。

页面默认展示前、后、左、右四个方向。模型支持 1–4 个视图；Beta 要求正面视图作为主参考，其余方向可选。多个视图应是同一对象、同一状态，并尽量保持相近比例和一致的上下方向。

## 目录与运行数据

- `index.html`、`reverse-modeling.css`、`reverse-modeling.js`：独立前端；
- `server.py`：静态页面服务及对现有 Hunyuan3D Gradio API 的轻量桥接；
- `runtime/`：临时上传与生成结果，仅在运行后创建，已被本目录 `.gitignore` 忽略。

桥接服务默认监听 `127.0.0.1:8766`，只接受本机访问；Hunyuan3D 默认地址为 `127.0.0.1:8081`。二者均可通过 `server.py` 参数调整。
