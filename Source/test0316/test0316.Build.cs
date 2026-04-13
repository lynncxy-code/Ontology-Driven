// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class test0316 : ModuleRules
{
	public test0316(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "Niagara", "UMG", "Json", "JsonUtilities", "HTTP", "RealtimeMeshComponent" });

		PrivateDependencyModuleNames.AddRange(new string[] {  });

		// Slate UI (required for programmatic UMG widget construction)
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });
		
		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
