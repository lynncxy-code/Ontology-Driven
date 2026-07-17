#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Dom/JsonObject.h"
#include "OntoTwinOverlayWidget.generated.h"

class UBorder;
class UGridPanel;
class USizeBox;
class UTextBlock;

UCLASS()
class ONTOTWINSYNC_API UOntoTwinOverlayWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    void ApplyOverlayData(const TSharedPtr<FJsonObject>& OverlayData);
    void SetWorldSpacePresentation(bool bEnabled);
    FVector2D GetDesiredRenderSize();
    FString GetConfigRevision() const { return ConfigRevision; }

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    UPROPERTY()
    USizeBox* OverlayBounds = nullptr;

    UPROPERTY()
    UBorder* PanelBorder = nullptr;

    UPROPERTY()
    UTextBlock* TitleText = nullptr;

    UPROPERTY()
    UTextBlock* SubtitleText = nullptr;

    UPROPERTY()
    UTextBlock* BodyText = nullptr;

    UPROPERTY()
    UBorder* StatusDot = nullptr;

    UPROPERTY()
    USizeBox* StatusDotBounds = nullptr;

    UPROPERTY()
    UTextBlock* StatusText = nullptr;

    UPROPERTY()
    UGridPanel* MetricsGrid = nullptr;

    UPROPERTY()
    TArray<UTextBlock*> MetricLabels;

    UPROPERTY()
    TArray<UTextBlock*> MetricValues;

    UPROPERTY()
    UTextBlock* OfflineText = nullptr;

    FString ConfigRevision;
    TSharedPtr<FJsonObject> PendingData;
    bool bWorldSpacePresentation = false;

    void BuildDefaultLayout();
    UTextBlock* CreateText(const FName Name, int32 FontSize, const FLinearColor& Color, bool bBold = false) const;
    void ApplyPresentationStyle();
    void ApplyPendingData();
};
