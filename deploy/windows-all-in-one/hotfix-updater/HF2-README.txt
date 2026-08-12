OntoTwin ZHHZ RC10.10-HF2 使用说明

适用版本：原始 RC10.10，或已经安装 RC10.10-HF1 的电脑。

1. 关闭“灵云智”控制中心和 ZHHZ 运行时。
2. 双击 OntoTwin-ZHHZ-RC10.10-HF2.exe。
3. 允许管理员权限并等待程序自动完成。
4. 更新完成后，从桌面“灵云智”重新启动系统。

HF2 只更新后台应用载荷，不替换 ZHHZ.exe，不清空 PostgreSQL、Neo4j 或客户配置。
它修复 HF1 中静态 UE 实例被错误显示为“失联”的问题，并在安装结束前核验：
- 38 Types / 669 Instances
- 669 个模型快照
- 15,693 个渲染部件引用
- 实例心跳在线

失败日志：
C:\ProgramData\OntoTwin-ZHHZ\Logs\rc10.10-hf2-update.log
