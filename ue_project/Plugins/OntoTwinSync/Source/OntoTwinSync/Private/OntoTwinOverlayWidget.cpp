#include "OntoTwinOverlayWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/GridPanel.h"
#include "Components/GridSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/PanelWidget.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateColor.h"

namespace
{
const FLinearColor OverlayBackground(0.055f, 0.055f, 0.055f, 0.94f);
const FLinearColor PrimaryText(0.96f, 0.96f, 0.96f, 1.0f);
const FLinearColor SecondaryText(0.70f, 0.70f, 0.70f, 1.0f);
const FLinearColor MutedText(0.52f, 0.52f, 0.52f, 1.0f);
const FLinearColor Divider(1.0f, 1.0f, 1.0f, 0.12f);
const FLinearColor NormalColor(0.08f, 0.55f, 0.33f, 1.0f);
const FLinearColor WarningColor(0.80f, 0.52f, 0.12f, 1.0f);
const FLinearColor CriticalColor(0.72f, 0.18f, 0.16f, 1.0f);
constexpr float ScreenPanelWidth = 360.0f;
constexpr float ScreenPanelMinHeight = 80.0f;
constexpr float WorldRenderDensity = 2.0f;

FString SlotDisplayValue(const TSharedPtr<FJsonObject>& Slots, const TCHAR* SlotName)
{
    if (!Slots.IsValid()) return FString();
    const TSharedPtr<FJsonObject>* Slot = nullptr;
    FString Value;
    if (Slots->TryGetObjectField(SlotName, Slot) && Slot && Slot->IsValid())
    {
        (*Slot)->TryGetStringField(TEXT("display_value"), Value);
    }
    return Value;
}
}

TSharedRef<SWidget> UOntoTwinOverlayWidget::RebuildWidget()
{
    if (!WidgetTree)
    {
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("OverlayWidgetTree"), RF_Transient);
    }
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        BuildDefaultLayout();
    }
    TSharedRef<SWidget> Result = Super::RebuildWidget();
    ApplyPendingData();
    return Result;
}

UTextBlock* UOntoTwinOverlayWidget::CreateText(
    const FName Name, int32 FontSize, const FLinearColor& Color, bool bBold) const
{
    if (!WidgetTree) return nullptr;
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
    Text->SetColorAndOpacity(FSlateColor(Color));
    Text->SetFont(FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), FontSize));
    Text->SetAutoWrapText(true);
    return Text;
}

void UOntoTwinOverlayWidget::BuildDefaultLayout()
{
    if (!WidgetTree) return;

    OverlayBounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("OverlayBounds"));
    OverlayBounds->SetWidthOverride(ScreenPanelWidth);
    OverlayBounds->SetMinDesiredHeight(ScreenPanelMinHeight);
    WidgetTree->RootWidget = OverlayBounds;

    PanelBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("OverlayPanel"));
    PanelBorder->SetPadding(FMargin(14.0f, 12.0f));
    PanelBorder->SetBrush(FSlateRoundedBoxBrush(OverlayBackground, 6.0f));
    OverlayBounds->AddChild(PanelBorder);

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("OverlayStack"));
    PanelBorder->SetContent(Stack);

    TitleText = CreateText(TEXT("OverlayTitle"), 15, PrimaryText, true);
    Stack->AddChildToVerticalBox(TitleText);

    SubtitleText = CreateText(TEXT("OverlaySubtitle"), 11, SecondaryText);
    UVerticalBoxSlot* SubtitleSlot = Stack->AddChildToVerticalBox(SubtitleText);
    SubtitleSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 0.0f));

    BodyText = CreateText(TEXT("OverlayBody"), 12, SecondaryText);
    UVerticalBoxSlot* BodySlot = Stack->AddChildToVerticalBox(BodyText);
    BodySlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));

    UHorizontalBox* StatusRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("OverlayStatusRow"));
    UVerticalBoxSlot* StatusRowSlot = Stack->AddChildToVerticalBox(StatusRow);
    StatusRowSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));

    StatusDot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("OverlayStatusDot"));
    StatusDot->SetBrush(FSlateRoundedBoxBrush(MutedText, 3.0f));
    StatusDotBounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("OverlayStatusDotBounds"));
    StatusDotBounds->SetWidthOverride(6.0f);
    StatusDotBounds->SetHeightOverride(6.0f);
    StatusDotBounds->AddChild(StatusDot);
    UHorizontalBoxSlot* DotSlot = StatusRow->AddChildToHorizontalBox(StatusDotBounds);
    DotSlot->SetPadding(FMargin(0.0f, 0.0f, 7.0f, 0.0f));
    DotSlot->SetVerticalAlignment(VAlign_Center);

    StatusText = CreateText(TEXT("OverlayStatusText"), 12, PrimaryText);
    StatusRow->AddChildToHorizontalBox(StatusText);

    MetricsGrid = WidgetTree->ConstructWidget<UGridPanel>(UGridPanel::StaticClass(), TEXT("OverlayMetrics"));
    MetricsGrid->SetColumnFill(0, 0.45f);
    MetricsGrid->SetColumnFill(1, 0.55f);
    UVerticalBoxSlot* GridSlot = Stack->AddChildToVerticalBox(MetricsGrid);
    GridSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));

    for (int32 Index = 0; Index < 4; ++Index)
    {
        UTextBlock* Label = CreateText(FName(*FString::Printf(TEXT("MetricLabel%d"), Index)), 10, MutedText);
        UGridSlot* LabelSlot = MetricsGrid->AddChildToGrid(Label, Index, 0);
        LabelSlot->SetPadding(FMargin(0.0f, 4.0f, 8.0f, 4.0f));

        UTextBlock* Value = CreateText(FName(*FString::Printf(TEXT("MetricValue%d"), Index)), 12, PrimaryText);
        Value->SetJustification(ETextJustify::Right);
        UGridSlot* ValueSlot = MetricsGrid->AddChildToGrid(Value, Index, 1);
        ValueSlot->SetPadding(FMargin(8.0f, 4.0f, 0.0f, 4.0f));

        MetricLabels.Add(Label);
        MetricValues.Add(Value);
    }

    OfflineText = CreateText(TEXT("OverlayOffline"), 10, MutedText);
    OfflineText->SetText(FText::FromString(TEXT("Offline - last known values")));
    UVerticalBoxSlot* OfflineSlot = Stack->AddChildToVerticalBox(OfflineText);
    OfflineSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));

    ApplyPresentationStyle();
}

void UOntoTwinOverlayWidget::SetWorldSpacePresentation(bool bEnabled)
{
    if (bWorldSpacePresentation == bEnabled) return;
    bWorldSpacePresentation = bEnabled;
    ApplyPresentationStyle();
}

FVector2D UOntoTwinOverlayWidget::GetDesiredRenderSize()
{
    ForceLayoutPrepass();
    FVector2D Desired = GetDesiredSize();
    const float Density = bWorldSpacePresentation ? WorldRenderDensity : 1.0f;
    Desired.X = FMath::Max(Desired.X, ScreenPanelWidth * Density);
    Desired.Y = FMath::Clamp(
        Desired.Y,
        ScreenPanelMinHeight * Density,
        360.0f * Density);
    return FVector2D(FMath::CeilToFloat(Desired.X), FMath::CeilToFloat(Desired.Y));
}

void UOntoTwinOverlayWidget::ApplyPresentationStyle()
{
    if (!OverlayBounds || !PanelBorder || !TitleText) return;

    const float Density = bWorldSpacePresentation ? WorldRenderDensity : 1.0f;
    const auto FontSize = [this, Density](int32 ScreenSize, int32 WorldSize)
    {
        return FMath::RoundToInt((bWorldSpacePresentation ? WorldSize : ScreenSize) * Density);
    };
    const auto SetFont = [](UTextBlock* Text, int32 Size, bool bBold = false)
    {
        if (Text)
        {
            Text->SetFont(FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size));
        }
    };

    OverlayBounds->SetWidthOverride(ScreenPanelWidth * Density);
    OverlayBounds->SetMinDesiredHeight(ScreenPanelMinHeight * Density);
    PanelBorder->SetPadding(FMargin(14.0f * Density, 12.0f * Density));
    PanelBorder->SetBrush(FSlateRoundedBoxBrush(OverlayBackground, 6.0f * Density));

    SetFont(TitleText, FontSize(15, 20), true);
    SetFont(SubtitleText, FontSize(11, 14));
    SetFont(BodyText, FontSize(12, 16));
    SetFont(StatusText, FontSize(12, 16));
    SetFont(OfflineText, FontSize(10, 13));

    const float TextWrapWidth = (ScreenPanelWidth - 28.0f) * Density;
    TitleText->SetWrapTextAt(TextWrapWidth);
    SubtitleText->SetWrapTextAt(TextWrapWidth);
    BodyText->SetWrapTextAt(TextWrapWidth);
    StatusText->SetWrapTextAt(TextWrapWidth);

    if (UVerticalBoxSlot* LayoutSlot = Cast<UVerticalBoxSlot>(SubtitleText->Slot))
    {
        LayoutSlot->SetPadding(FMargin(0.0f, 2.0f * Density, 0.0f, 0.0f));
    }
    if (UVerticalBoxSlot* LayoutSlot = Cast<UVerticalBoxSlot>(BodyText->Slot))
    {
        LayoutSlot->SetPadding(FMargin(0.0f, 8.0f * Density, 0.0f, 0.0f));
    }
    if (UVerticalBoxSlot* LayoutSlot = StatusText->GetParent()
        ? Cast<UVerticalBoxSlot>(StatusText->GetParent()->Slot) : nullptr)
    {
        LayoutSlot->SetPadding(FMargin(0.0f, 8.0f * Density, 0.0f, 0.0f));
    }
    if (UVerticalBoxSlot* LayoutSlot = MetricsGrid ? Cast<UVerticalBoxSlot>(MetricsGrid->Slot) : nullptr)
    {
        LayoutSlot->SetPadding(FMargin(0.0f, 8.0f * Density, 0.0f, 0.0f));
    }
    if (UVerticalBoxSlot* LayoutSlot = Cast<UVerticalBoxSlot>(OfflineText->Slot))
    {
        LayoutSlot->SetPadding(FMargin(0.0f, 8.0f * Density, 0.0f, 0.0f));
    }

    if (StatusDotBounds)
    {
        StatusDotBounds->SetWidthOverride(6.0f * Density);
        StatusDotBounds->SetHeightOverride(6.0f * Density);
        if (UHorizontalBoxSlot* LayoutSlot = Cast<UHorizontalBoxSlot>(StatusDotBounds->Slot))
        {
            LayoutSlot->SetPadding(FMargin(0.0f, 0.0f, 7.0f * Density, 0.0f));
        }
    }

    for (int32 Index = 0; Index < MetricLabels.Num(); ++Index)
    {
        SetFont(MetricLabels[Index], FontSize(10, 14));
        SetFont(MetricValues.IsValidIndex(Index) ? MetricValues[Index] : nullptr, FontSize(12, 16));
        if (UGridSlot* LayoutSlot = Cast<UGridSlot>(MetricLabels[Index]->Slot))
        {
            LayoutSlot->SetPadding(FMargin(0.0f, 4.0f * Density, 8.0f * Density, 4.0f * Density));
        }
        if (MetricValues.IsValidIndex(Index))
        {
            if (UGridSlot* LayoutSlot = Cast<UGridSlot>(MetricValues[Index]->Slot))
            {
                LayoutSlot->SetPadding(FMargin(8.0f * Density, 4.0f * Density, 0.0f, 4.0f * Density));
            }
        }
    }

    InvalidateLayoutAndVolatility();
    ForceLayoutPrepass();
}

void UOntoTwinOverlayWidget::ApplyOverlayData(const TSharedPtr<FJsonObject>& OverlayData)
{
    PendingData = OverlayData;
    ApplyPendingData();
}

void UOntoTwinOverlayWidget::ApplyPendingData()
{
    if (!PendingData.IsValid() || !PanelBorder || !TitleText) return;

    PendingData->TryGetStringField(TEXT("config_revision"), ConfigRevision);
    bool bOnline = true;
    PendingData->TryGetBoolField(TEXT("online"), bOnline);
    PanelBorder->SetRenderOpacity(bOnline ? 1.0f : 0.68f);
    OfflineText->SetVisibility(bOnline ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);

    const TSharedPtr<FJsonObject>* SlotsPtr = nullptr;
    TSharedPtr<FJsonObject> Slots;
    if (PendingData->TryGetObjectField(TEXT("resolved_slots"), SlotsPtr) && SlotsPtr)
    {
        Slots = *SlotsPtr;
    }

    const FString Title = SlotDisplayValue(Slots, TEXT("title"));
    TitleText->SetText(FText::FromString(Title.IsEmpty() ? TEXT("--") : Title));

    const FString Subtitle = SlotDisplayValue(Slots, TEXT("subtitle"));
    SubtitleText->SetText(FText::FromString(Subtitle));
    SubtitleText->SetVisibility(Subtitle.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);

    const FString Body = SlotDisplayValue(Slots, TEXT("body"));
    BodyText->SetText(FText::FromString(Body));
    BodyText->SetVisibility(Body.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);

    const TSharedPtr<FJsonObject>* StatusPtr = nullptr;
    FString StatusValue;
    FString StatusLevel = TEXT("unknown");
    if (Slots.IsValid() && Slots->TryGetObjectField(TEXT("status"), StatusPtr) && StatusPtr && StatusPtr->IsValid())
    {
        (*StatusPtr)->TryGetStringField(TEXT("display_value"), StatusValue);
        (*StatusPtr)->TryGetStringField(TEXT("level"), StatusLevel);
    }
    const bool bHasStatus = !StatusValue.IsEmpty();
    StatusText->SetText(FText::FromString(StatusValue));
    StatusText->GetParent()->SetVisibility(bHasStatus ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
    FLinearColor StatusColor = MutedText;
    if (StatusLevel == TEXT("normal") || StatusLevel == TEXT("info")) StatusColor = NormalColor;
    else if (StatusLevel == TEXT("warning")) StatusColor = WarningColor;
    else if (StatusLevel == TEXT("critical")) StatusColor = CriticalColor;
    const float Density = bWorldSpacePresentation ? WorldRenderDensity : 1.0f;
    StatusDot->SetBrush(FSlateRoundedBoxBrush(StatusColor, 3.0f * Density));

    const TArray<TSharedPtr<FJsonValue>>* Metrics = nullptr;
    const bool bHasMetrics = Slots.IsValid() && Slots->TryGetArrayField(TEXT("metrics"), Metrics) && Metrics;
    for (int32 Index = 0; Index < MetricLabels.Num(); ++Index)
    {
        FString LabelValue;
        FString MetricValue;
        if (bHasMetrics && Metrics->IsValidIndex(Index))
        {
            const TSharedPtr<FJsonObject> Metric = (*Metrics)[Index]->AsObject();
            if (Metric.IsValid())
            {
                Metric->TryGetStringField(TEXT("label"), LabelValue);
                Metric->TryGetStringField(TEXT("display_value"), MetricValue);
            }
        }
        MetricLabels[Index]->SetText(FText::FromString(LabelValue));
        MetricValues[Index]->SetText(FText::FromString(MetricValue));
        const ESlateVisibility RowVisibility = LabelValue.IsEmpty() && MetricValue.IsEmpty()
            ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible;
        MetricLabels[Index]->SetVisibility(RowVisibility);
        MetricValues[Index]->SetVisibility(RowVisibility);
    }
    MetricsGrid->SetVisibility(bHasMetrics && Metrics->Num() > 0
        ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
}
