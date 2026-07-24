#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "OntoTwinRoamingHUDWidget.generated.h"

class UBorder;
class UButton;
class USizeBox;
class UTextBlock;
class UVerticalBox;
class UTwinInteractionManagerComponent;

/**
 * Performance 级漫游 HUD：无底板状态文字、按键胶囊提示和 Tab 操作抽屉。
 * 静态深灰半透明表面不依赖 Blur/Postbuffer，装饰层不参与命中测试。
 */
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
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    UPROPERTY()
    UTwinInteractionManagerComponent* Manager = nullptr;

    UPROPERTY()
    UTextBlock* StatusText = nullptr;

    UPROPERTY()
    USizeBox* StatusPulse = nullptr;

    UPROPERTY()
    UVerticalBox* HintList = nullptr;

    UPROPERTY()
    UTextBlock* DetailText = nullptr;

    UPROPERTY()
    UBorder* DetailPanel = nullptr;

    UPROPERTY()
    UButton* FirstPersonButton = nullptr;

    UPROPERTY()
    UButton* ShoulderButton = nullptr;

    UPROPERTY()
    UButton* GlobalButton = nullptr;

    FString ShortcutSignature;
    float StatusPulsePhase = 0.0f;

    void BuildDefaultLayout();
    UBorder* BuildGlassSurface(
        const FName Name,
        const FMargin& SurfacePadding,
        float Radius);
    void RefreshShortcutList();
    void AddShortcutRow(int32 Index, const FString& Key, const FString& Description);
    UButton* AddActionButton(UVerticalBox* Parent, const FName Name, const FString& Label);

    UFUNCTION()
    void OnCycleSkin();

    UFUNCTION()
    void OnResumeRoute();

    UFUNCTION()
    void OnRestartRoute();

    UFUNCTION()
    void OnReloadCharacter();

    UFUNCTION()
    void OnFirstPerson();

    UFUNCTION()
    void OnShoulder();

    UFUNCTION()
    void OnGlobal();
};
