#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "OntoTwinRoamingHUDWidget.generated.h"

class UButton;
class UTextBlock;
class UVerticalBox;
class UTwinInteractionManagerComponent;

/** Lingjing Mode 1 的原生 UMG 等价实现：轻量玻璃状态条 + 可展开控制面板。 */
UCLASS()
class ONTOTWINSYNC_API UOntoTwinRoamingHUDWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void SetInteractionManager(UTwinInteractionManagerComponent* InManager);
    void RefreshFromManager();
    void SetInteractionOpen(bool bOpen);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    UPROPERTY()
    UTwinInteractionManagerComponent* Manager = nullptr;

    UPROPERTY()
    UTextBlock* StatusText = nullptr;

    UPROPERTY()
    UTextBlock* HintText = nullptr;

    UPROPERTY()
    UTextBlock* DetailText = nullptr;

    UPROPERTY()
    UVerticalBox* DetailPanel = nullptr;

    void BuildDefaultLayout();
    UButton* AddActionButton(UVerticalBox* Parent, const FName Name, const FString& Label);

    UFUNCTION()
    void OnCycleSkin();

    UFUNCTION()
    void OnResumeRoute();

    UFUNCTION()
    void OnRestartRoute();

    UFUNCTION()
    void OnReloadCharacter();
};
