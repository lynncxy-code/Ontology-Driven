#include "OntoTwinBuildIdentity.h"

#include "Dom/JsonObject.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

FString OntoTwinLoadedSourceHash()
{
	return UTF8_TO_TCHAR(ONTOTWIN_BUILD_SOURCE_HASH);
}

const FString& OntoTwinInstalledRelease()
{
	static const FString Release = []()
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("OntoTwinSync"));
		FString Text;
		if (!Plugin.IsValid() || !FFileHelper::LoadFileToString(Text, *FPaths::Combine(Plugin->GetBaseDir(), TEXT("OntoTwinRelease.json"))))
		{
			return FString();
		}
		TSharedPtr<FJsonObject> Json;
		FString Value;
		if (FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Json) && Json.IsValid() && Json->TryGetStringField(TEXT("release"), Value))
		{
			Value.TrimStartAndEndInline();
			return Value.Left(64);
		}
		return FString();
	}();
	return Release;
}