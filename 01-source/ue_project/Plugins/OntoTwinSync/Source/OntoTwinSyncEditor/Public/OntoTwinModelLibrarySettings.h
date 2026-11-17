#pragma once

#include "Engine/DeveloperSettings.h"
#include "OntoTwinModelLibrarySettings.generated.h"

UCLASS(Config=Game, DefaultConfig, meta=(DisplayName="模型库"))
class UOntoTwinModelLibrarySettings : public UDeveloperSettings
{
    GENERATED_BODY()
public:
    virtual FName GetCategoryName() const override { return TEXT("OntoTwin"); }

    UPROPERTY(Config, EditAnywhere, Category="模型库", meta=(LongPackageName, DisplayName="工程模型文件夹"))
    TArray<FDirectoryPath> Roots;

    UPROPERTY(Config, EditAnywhere, Category="模型库", meta=(DisplayName="自定义显示名", ToolTip="键为完整资产路径，如 /Game/StandardModels/Rack.Rack"))
    TMap<FString, FString> DisplayNames;
};

namespace OntoTwinEditorLibrary
{
    void Register();
    void Unregister();
}
