// OntoTwinSync 插件模块定义
// 依赖与原 test0316 游戏模块一致，但去掉了与同步无关的 InputCore / EnhancedInput

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
			"HTTP",
			"Json",
			"JsonUtilities",
			"Niagara",
			"UMG",
			"glTFRuntime"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		// FR-6 迁移工具：编辑器选择集 / EditorDestroyActor 需要 UnrealEd（仅编辑器构建）
		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.Add("UnrealEd");
		}
	}
}
