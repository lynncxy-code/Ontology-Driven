#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "OntoTwinMinimapWidget.generated.h"

class UImage;
class UBorder;
class UButton;
class USizeBox;
class UTextureRenderTarget2D;

/** Screen Space map surface with a sharp marker and one explicit collapse control. */
UCLASS()
class ONTOTWINSYNC_API UOntoTwinMinimapWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void SetMapTexture(UTextureRenderTarget2D* InTexture, const FIntPoint& InCaptureSize);
    void SetMarker(const FVector2D& InUV, float InAngleDegrees, bool bInOffMap);
    void HideMarker();
    void ClearMap();

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    virtual int32 NativePaint(
        const FPaintArgs& Args,
        const FGeometry& AllottedGeometry,
        const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements,
        int32 LayerId,
        const FWidgetStyle& InWidgetStyle,
        bool bParentEnabled) const override;

private:
    UPROPERTY()
    USizeBox* RootBounds = nullptr;

    UPROPERTY()
    UBorder* MapShell = nullptr;

    UPROPERTY()
    UImage* MapImage = nullptr;

    UPROPERTY()
    UButton* ToggleButton = nullptr;

    UPROPERTY()
    UTextureRenderTarget2D* MapTexture = nullptr;

    FVector2D ContentSize = FVector2D(320.0f, 240.0f);
    FVector2D MarkerUV = FVector2D(0.5f, 0.5f);
    float MarkerAngleDegrees = 0.0f;
    float MarkerPulsePhase = 0.0f;
    float ExpandAlpha = 1.0f;
    bool bMarkerVisible = false;
    bool bMarkerOffMap = false;
    bool bExpanded = true;

    void BuildDefaultLayout();
    void ApplyMapTexture();
    void ApplyExpansionVisuals();

    UFUNCTION()
    void OnToggleExpanded();
};
