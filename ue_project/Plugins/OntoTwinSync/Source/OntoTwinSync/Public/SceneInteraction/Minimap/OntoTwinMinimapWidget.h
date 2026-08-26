#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SceneInteraction/Minimap/TwinMinimapTypes.h"
#include "OntoTwinMinimapWidget.generated.h"

class UImage;
class UBorder;
class UButton;
class USizeBox;
class UTextBlock;
class UTextureRenderTarget2D;
class UTwinInteractionManagerComponent;

/** Screen Space map surface with a sharp marker and one explicit collapse control. */
UCLASS()
class ONTOTWINSYNC_API UOntoTwinMinimapWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void SetInteractionManager(UTwinInteractionManagerComponent* InManager);
    void SetMapTexture(UTextureRenderTarget2D* InTexture, const FIntPoint& InCaptureSize);
    void SetMarker(const FVector2D& InUV, float InAngleDegrees, bool bInOffMap);
    void SetTeleportFeedback(
        const FVector2D& InUV,
        ETwinMinimapTeleportFeedback InFeedback,
        const FString& InMessage);
    void SetUndoAvailable(bool bAvailable);
    void ClearTeleportFeedback();
    void HideMarker();
    void ClearMap();

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    virtual FReply NativeOnMouseButtonDown(
        const FGeometry& InGeometry,
        const FPointerEvent& InMouseEvent) override;
    virtual FReply NativeOnMouseButtonDoubleClick(
        const FGeometry& InGeometry,
        const FPointerEvent& InMouseEvent) override;
    virtual FReply NativeOnTouchStarted(
        const FGeometry& InGeometry,
        const FPointerEvent& InGestureEvent) override;
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
    UTwinInteractionManagerComponent* Manager = nullptr;

    UPROPERTY()
    USizeBox* RootBounds = nullptr;

    UPROPERTY()
    UBorder* MapShell = nullptr;

    UPROPERTY()
    UImage* MapImage = nullptr;

    UPROPERTY()
    UButton* ToggleButton = nullptr;

    UPROPERTY()
    UBorder* TeleportStatusPanel = nullptr;

    UPROPERTY()
    UTextBlock* TeleportStatusText = nullptr;

    UPROPERTY()
    UButton* UndoButton = nullptr;

    UPROPERTY()
    UTextureRenderTarget2D* MapTexture = nullptr;

    FVector2D ContentSize = FVector2D(320.0f, 240.0f);
    FVector2D MarkerUV = FVector2D(0.5f, 0.5f);
    float MarkerAngleDegrees = 0.0f;
    float MarkerPulsePhase = 0.0f;
    float ExpandAlpha = 1.0f;
    float FeedbackSecondsRemaining = 0.0f;
    double LastTouchSeconds = -1.0;
    FVector2D TeleportTargetUV = FVector2D(0.5f, 0.5f);
    FVector2D LastTouchLocal = FVector2D::ZeroVector;
    ETwinMinimapTeleportFeedback TeleportFeedback =
        ETwinMinimapTeleportFeedback::Hidden;
    bool bMarkerVisible = false;
    bool bMarkerOffMap = false;
    bool bTeleportTargetVisible = false;
    bool bExpanded = true;

    void BuildDefaultLayout();
    void ApplyMapTexture();
    void ApplyExpansionVisuals();
    bool TryGetMapUV(
        const FGeometry& Geometry,
        const FVector2D& ScreenPosition,
        FVector2D& OutUV) const;
    void HandleMapPreview(const FVector2D& UV);
    void HandleMapTeleport(const FVector2D& UV);

    UFUNCTION()
    void OnToggleExpanded();

    UFUNCTION()
    void OnUndoTeleport();
};
