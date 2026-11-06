# 显式连接已有项目与关卡

在目标 UE 工程的 `Config/DefaultGame.ini` 中配置以下段落，填写平台已经建立绑定的真实身份：

```ini
[OntoTwin.Connection]
BackendBaseUrl="http://localhost:5000"
ProjectId=平台项目ID
UEProjectId=UE工程稳定ID
```

URL 必须加双引号，避免 Unreal INI 将 `//` 后的内容视为注释。修改后重启编辑器或游戏。配置随工程参与后续打包；已生成的旧程序需要重新构建。

插件在加载关卡和开始运行时读取地址及工程身份，并为快照、业务网页、场景交互及资产请求补充项目和实际关卡身份。PIE 自动去掉关卡路径的临时前缀。切换到未绑定关卡会被后台拒绝，不借用其他关卡身份。

显式配置模式只检查已有绑定，不自动绑定后台当前激活的数据集。`-OntoTwinBackendBaseUrl=` 启动参数仍可覆盖连接地址。未配置 `ProjectId` 的工程保留原有协议。

客户地址、项目 ID 和专用功能保存在各自 UE 工程中，不写入平台插件源码。
