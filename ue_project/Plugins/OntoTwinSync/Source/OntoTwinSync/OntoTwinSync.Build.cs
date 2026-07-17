// OntoTwinSync 插件模块定义
// 依赖与原 test0316 游戏模块一致；4.0 人物漫游使用 UE 内置 Enhanced Input。

using UnrealBuildTool;

public class OntoTwinSync : ModuleRules
{
	public OntoTwinSync(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"EnhancedInput",
			"HTTP",
			"InputCore",
			"Json",
			"JsonUtilities",
			"Niagara",
			"UMG",
			"glTFRuntime"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "WebSockets" });

		// FR-6 迁移工具：编辑器选择集 / EditorDestroyActor 需要 UnrealEd（仅编辑器构建）
		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.Add("UnrealEd");
		}
	}
}
