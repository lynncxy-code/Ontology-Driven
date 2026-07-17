#include "SceneInteraction/OntoTwinRoamingHUDWidget.h"

#include "SceneInteraction/TwinInteractionManagerComponent.h"
#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/BackgroundBlur.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"

namespace
{
const FLinearColor GlassFill(0.035f, 0.055f, 0.075f, 0.70f);
const FLinearColor GlassStroke(0.68f, 0.82f, 0.92f, 0.22f);
const FLinearColor PrimaryText(0.94f, 0.97f, 1.0f, 1.0f);
const FLinearColor SecondaryText(0.66f, 0.76f, 0.84f, 1.0f);
}

TSharedRef<SWidget> UOntoTwinRoamingHUDWidget::RebuildWidget()
{
    if (!WidgetTree)
    {
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("RoamingHUDWidgetTree"), RF_Transient);
    }
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        BuildDefaultLayout();
    }
    TSharedRef<SWidget> Result = Super::RebuildWidget();
    RefreshFromManager();
    return Result;
}

void UOntoTwinRoamingHUDWidget::BuildDefaultLayout()
{
    USizeBox* Bounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("HUDWidth"));
    Bounds->SetWidthOverride(520.0f);
    WidgetTree->RootWidget = Bounds;

    UBackgroundBlur* Blur = WidgetTree->ConstructWidget<UBackgroundBlur>(UBackgroundBlur::StaticClass(), TEXT("GlassBlur"));
    Blur->SetBlurStrength(10.0f);
    Blur->SetApplyAlphaToBlur(true);
    Bounds->AddChild(Blur);

    UBorder* Glass = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GlassPanel"));
    Glass->SetPadding(FMargin(16.0f, 11.0f));
    Glass->SetBrush(FSlateRoundedBoxBrush(GlassFill, 14.0f, GlassStroke, 1.0f));
    Blur->SetContent(Glass);

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("HUDStack"));
    Glass->SetContent(Stack);

    StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StatusText"));
    StatusText->SetColorAndOpacity(PrimaryText);
    StatusText->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 14));
    Stack->AddChildToVerticalBox(StatusText);

    HintText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("HintText"));
    HintText->SetColorAndOpacity(SecondaryText);
    HintText->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 10));
    HintText->SetAutoWrapText(true);
    HintText->SetWrapTextAt(488.0f);
    UVerticalBoxSlot* HintSlot = Stack->AddChildToVerticalBox(HintText);
    HintSlot->SetPadding(FMargin(0.0f, 3.0f, 0.0f, 0.0f));

    DetailPanel = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("DetailPanel"));
    UVerticalBoxSlot* DetailSlot = Stack->AddChildToVerticalBox(DetailPanel);
    DetailSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));

    DetailText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DetailText"));
    DetailText->SetColorAndOpacity(SecondaryText);
    DetailText->SetAutoWrapText(true);
    DetailText->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 11));
    DetailPanel->AddChildToVerticalBox(DetailText);

    UHorizontalBox* Actions = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Actions"));
    UVerticalBoxSlot* ActionsSlot = DetailPanel->AddChildToVerticalBox(Actions);
    ActionsSlot->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 0.0f));

    UButton* SkinButton = AddActionButton(nullptr, TEXT("SkinButton"), TEXT("切换皮肤"));
    UButton* ResumeButton = AddActionButton(nullptr, TEXT("ResumeButton"), TEXT("继续路线"));
    UButton* RestartButton = AddActionButton(nullptr, TEXT("RestartButton"), TEXT("从头开始"));
    UButton* ReloadButton = AddActionButton(nullptr, TEXT("ReloadButton"), TEXT("重载人物"));
    for (UButton* Button : {SkinButton, ResumeButton, RestartButton, ReloadButton})
    {
        UHorizontalBoxSlot* ActionSlot = Actions->AddChildToHorizontalBox(Button);
        ActionSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
    }

    SkinButton->OnClicked.AddDynamic(this, &UOntoTwinRoamingHUDWidget::OnCycleSkin);
    ResumeButton->OnClicked.AddDynamic(this, &UOntoTwinRoamingHUDWidget::OnResumeRoute);
    RestartButton->OnClicked.AddDynamic(this, &UOntoTwinRoamingHUDWidget::OnRestartRoute);
    ReloadButton->OnClicked.AddDynamic(this, &UOntoTwinRoamingHUDWidget::OnReloadCharacter);
    DetailPanel->SetVisibility(ESlateVisibility::Collapsed);
}

UButton* UOntoTwinRoamingHUDWidget::AddActionButton(
    UVerticalBox* Parent,
    const FName Name,
    const FString& Label)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(
        UTextBlock::StaticClass(), FName(*(Name.ToString() + TEXT("Text"))));
    Text->SetText(FText::FromString(Label));
    Text->SetColorAndOpacity(PrimaryText);
    Text->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 10));
    Button->SetContent(Text);
    if (UButtonSlot* ButtonSlot = Cast<UButtonSlot>(Text->Slot))
    {
        ButtonSlot->SetPadding(FMargin(10.0f, 6.0f));
    }
    if (Parent) Parent->AddChildToVerticalBox(Button);
    return Button;
}

void UOntoTwinRoamingHUDWidget::SetInteractionManager(UTwinInteractionManagerComponent* InManager)
{
    Manager = InManager;
    RefreshFromManager();
}

void UOntoTwinRoamingHUDWidget::RefreshFromManager()
{
    if (!Manager || !StatusText) return;
    StatusText->SetText(FText::FromString(Manager->GetHudStatusText()));
    HintText->SetText(FText::FromString(Manager->GetHudHintText()));
    DetailText->SetText(FText::FromString(Manager->GetHudDetailText()));
}

void UOntoTwinRoamingHUDWidget::SetInteractionOpen(bool bOpen)
{
    if (DetailPanel)
    {
        DetailPanel->SetVisibility(bOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    }
    SetVisibility(bOpen ? ESlateVisibility::Visible : ESlateVisibility::HitTestInvisible);
}

void UOntoTwinRoamingHUDWidget::OnCycleSkin() { if (Manager) Manager->CycleSkin(); }
void UOntoTwinRoamingHUDWidget::OnResumeRoute() { if (Manager) Manager->ResumeRoute(); }
void UOntoTwinRoamingHUDWidget::OnRestartRoute() { if (Manager) Manager->RestartRoute(); }
void UOntoTwinRoamingHUDWidget::OnReloadCharacter() { if (Manager) Manager->ApplyPendingReload(); }
