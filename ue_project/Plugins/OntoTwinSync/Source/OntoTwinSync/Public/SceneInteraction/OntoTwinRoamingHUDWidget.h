#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Types/SlateEnums.h"
#include "OntoTwinRoamingHUDWidget.generated.h"

class UBorder;
class UButton;
class UComboBoxString;
class UOntoTwinMinimapWidget;
class USizeBox;
class UTextBlock;
class UTextureRenderTarget2D;
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
    void SetMinimapTexture(UTextureRenderTarget2D* Texture, const FIntPoint& CaptureSize);
    void SetMinimapMarker(const FVector2D& UV, float AngleDegrees, bool bOffMap);
    void HideMinimapMarker();
    void ClearMinimap();

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
    UOntoTwinMinimapWidget* MinimapWidget = nullptr;

    UPROPERTY()
    UComboBoxString* RouteSelector = nullptr;

    UPROPERTY()
    UButton* FirstPersonButton = nullptr;

    UPROPERTY()
    UButton* ShoulderButton = nullptr;

    UPROPERTY()
    UButton* GlobalButton = nullptr;

    FString ShortcutSignature;
    FString RouteSignature;
    TArray<FString> RouteOptionIds;
    TArray<FString> RouteOptionLabels;
    bool bRefreshingRouteSelector = false;
    float StatusPulsePhase = 0.0f;

    void BuildDefaultLayout();
    UBorder* BuildGlassSurface(
        const FName Name,
        const FMargin& SurfacePadding,
        float Radius);
    void RefreshShortcutList();
    void RefreshRouteSelector();
    void AddShortcutRow(int32 Index, const FString& Key, const FString& Description);
    UButton* AddActionButton(UVerticalBox* Parent, const FName Name, const FString& Label);

    UFUNCTION()
    UWidget* GenerateRouteOptionWidget(FString Item);

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

    UFUNCTION()
    void OnRouteSelected(FString SelectedItem, ESelectInfo::Type SelectionType);
};
