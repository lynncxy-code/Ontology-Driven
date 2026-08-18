#include "SceneInteraction/OntoTwinNarrationHUDWidget.h"

#include "SceneInteraction/TwinInteractionManagerComponent.h"
#include "UI/OntoTwinGlassTheme.h"
#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

TSharedRef<SWidget> UOntoTwinNarrationHUDWidget::RebuildWidget()
{
    if (!WidgetTree)
    {
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("NarrationHUDWidgetTree"), RF_Transient);
    }
    if (WidgetTree && !WidgetTree->RootWidget) BuildDefaultLayout();
    return Super::RebuildWidget();
}

void UOntoTwinNarrationHUDWidget::SetInteractionManager(
    UTwinInteractionManagerComponent* InManager)
{
    Manager = InManager;
}

void UOntoTwinNarrationHUDWidget::BuildDefaultLayout()
{
    UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(
        UCanvasPanel::StaticClass(), TEXT("NarrationCanvas"));
    Root->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    WidgetTree->RootWidget = Root;

    USizeBox* Bounds = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("NarrationBounds"));
    Bounds->SetWidthOverride(760.0f);
    Bounds->SetMinDesiredHeight(112.0f);
    Bounds->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UCanvasPanelSlot* BoundsSlot = Root->AddChildToCanvas(Bounds);
    BoundsSlot->SetAnchors(FAnchors(0.5f, 1.0f));
    BoundsSlot->SetAlignment(FVector2D(0.5f, 1.0f));
    BoundsSlot->SetPosition(FVector2D(0.0f, -74.0f));
    BoundsSlot->SetAutoSize(true);

    Surface = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("NarrationGlass"));
    Surface->SetPadding(FMargin(20.0f, 14.0f));
    Surface->SetBrush(FSlateRoundedBoxBrush(
        FOntoTwinGlassTheme::ScreenTint(EOntoTwinGlassQuality::Performance),
        18.0f,
        FOntoTwinGlassTheme::Rim(),
        1.0f));
    Surface->SetVisibility(ESlateVisibility::Collapsed);
    Bounds->AddChild(Surface);

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("NarrationStack"));
    Stack->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    Surface->SetContent(Stack);

    UHorizontalBox* Meta = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("NarrationMeta"));
    Meta->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UVerticalBoxSlot* MetaSlot = Stack->AddChildToVerticalBox(Meta);
    MetaSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 7.0f));

    ProgressText = WidgetTree->ConstructWidget<UTextBlock>(
        UTextBlock::StaticClass(), TEXT("NarrationProgress"));
    ProgressText->SetFont(FOntoTwinGlassTheme::Font(11.0f, true));
    ProgressText->SetColorAndOpacity(FOntoTwinGlassTheme::SecondaryText());
    ProgressText->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    Meta->AddChildToHorizontalBox(ProgressText);

    ModeText = WidgetTree->ConstructWidget<UTextBlock>(
        UTextBlock::StaticClass(), TEXT("NarrationMode"));
    ModeText->SetFont(FOntoTwinGlassTheme::Font(10.0f));
    ModeText->SetColorAndOpacity(FOntoTwinGlassTheme::MutedText());
    ModeText->SetJustification(ETextJustify::Right);
    ModeText->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UHorizontalBoxSlot* ModeSlot = Meta->AddChildToHorizontalBox(ModeText);
    ModeSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ModeSlot->SetHorizontalAlignment(HAlign_Right);

    BodyText = WidgetTree->ConstructWidget<UTextBlock>(
        UTextBlock::StaticClass(), TEXT("NarrationBody"));
    BodyText->SetFont(FOntoTwinGlassTheme::Font(18.0f, false));
    BodyText->SetColorAndOpacity(FOntoTwinGlassTheme::PrimaryText());
    BodyText->SetAutoWrapText(true);
    BodyText->SetWrapTextAt(700.0f);
    BodyText->SetLineHeightPercentage(1.22f);
    BodyText->SetShadowOffset(FVector2D(1.0f, 1.0f));
    BodyText->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.42f));
    BodyText->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UVerticalBoxSlot* BodySlot = Stack->AddChildToVerticalBox(BodyText);
    BodySlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 10.0f));

    SkipButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("NarrationSkip"));
PRAGMA_DISABLE_DEPRECATION_WARNINGS
    SkipButton->IsFocusable = false;
PRAGMA_ENABLE_DEPRECATION_WARNINGS
    FButtonStyle ButtonStyle;
    ButtonStyle
        .SetNormal(FSlateRoundedBoxBrush(
            FLinearColor(0.95f, 0.95f, 0.95f, 0.10f), 8.0f,
            FLinearColor(0.96f, 0.96f, 0.96f, 0.18f), 1.0f))
        .SetHovered(FSlateRoundedBoxBrush(
            FLinearColor(0.98f, 0.98f, 0.98f, 0.18f), 8.0f,
            FLinearColor(1.0f, 1.0f, 1.0f, 0.34f), 1.0f))
        .SetPressed(FSlateRoundedBoxBrush(
            FLinearColor(0.98f, 0.98f, 0.98f, 0.24f), 8.0f,
            FLinearColor(1.0f, 1.0f, 1.0f, 0.42f), 1.0f));
    ButtonStyle.SetNormalPadding(FMargin(12.0f, 6.0f));
    ButtonStyle.SetPressedPadding(FMargin(12.0f, 7.0f, 12.0f, 5.0f));
    SkipButton->SetStyle(ButtonStyle);
    SkipButton->OnClicked.AddDynamic(this, &UOntoTwinNarrationHUDWidget::OnSkipClicked);
    UTextBlock* SkipLabel = WidgetTree->ConstructWidget<UTextBlock>(
        UTextBlock::StaticClass(), TEXT("NarrationSkipLabel"));
    SkipLabel->SetText(FText::FromString(TEXT("跳过当前段")));
    SkipLabel->SetFont(FOntoTwinGlassTheme::Font(10.0f, true));
    SkipLabel->SetColorAndOpacity(FOntoTwinGlassTheme::PrimaryText());
    SkipLabel->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    SkipButton->AddChild(SkipLabel);
    UVerticalBoxSlot* SkipSlot = Stack->AddChildToVerticalBox(SkipButton);
    SkipSlot->SetHorizontalAlignment(HAlign_Right);
}

void UOntoTwinNarrationHUDWidget::ShowSegment(
    const FString& Text,
    int32 SegmentIndex,
    int32 SegmentCount,
    const FString& Mode,
    bool bAudioFallback,
    bool bShowText)
{
    if (!Surface) return;
    ProgressText->SetText(FText::FromString(FString::Printf(
        TEXT("路线解说  %d / %d"), SegmentIndex + 1, SegmentCount)));
    FString ModeLabel = Mode == TEXT("subtitle") ? TEXT("字幕")
        : Mode == TEXT("voice") ? TEXT("语音") : TEXT("字幕与语音");
    if (bAudioFallback) ModeLabel += TEXT(" · 音频不可用，已显示字幕");
    ModeText->SetText(FText::FromString(ModeLabel));
    BodyText->SetText(FText::FromString(Text));
    BodyText->SetVisibility(bShowText
        ? ESlateVisibility::SelfHitTestInvisible
        : ESlateVisibility::Collapsed);
    Surface->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void UOntoTwinNarrationHUDWidget::HideNarration()
{
    if (Surface) Surface->SetVisibility(ESlateVisibility::Collapsed);
}

void UOntoTwinNarrationHUDWidget::OnSkipClicked()
{
    if (Manager) Manager->SkipNarrationSegment();
}
