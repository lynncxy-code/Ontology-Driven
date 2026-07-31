#include "WebInteraction/OntoTwinWebHostWidget.h"

#include "WebInteraction/OntoTwinWebBridge.h"
#include "WebInteraction/OntoTwinWebInteractionComponent.h"

#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "SWebInterface.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBackgroundBlur.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

void UOntoTwinWebHostWidget::Configure(
    UOntoTwinWebInteractionComponent* InOwner,
    UOntoTwinWebBridge* InBridge,
    EOntoTwinWebGlassQuality InQuality)
{
    OwnerComponent = InOwner;
    BridgeObject = InBridge;
    EffectiveQuality = InQuality;
}

TSharedRef<SWidget> UOntoTwinWebHostWidget::RebuildWidget()
{
    const float BlurStrength = EffectiveQuality == EOntoTwinWebGlassQuality::High ? 18.0f : 8.0f;
    TSharedRef<SWidget> GlassLayer = EffectiveQuality == EOntoTwinWebGlassQuality::Performance
        ? StaticCastSharedRef<SWidget>(SNew(SBorder)
            .BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
            .BorderBackgroundColor(FLinearColor(0.04f, 0.045f, 0.05f, 0.96f)))
        : StaticCastSharedRef<SWidget>(SNew(SBackgroundBlur)
            .BlurStrength(BlurStrength)
            .BlurRadius(EffectiveQuality == EOntoTwinWebGlassQuality::High ? 12 : 6)
            .LowQualityFallbackBrush(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"))));
    GlassLayer->SetVisibility(EVisibility::HitTestInvisible);

    SAssignNew(Browser, SWebInterface)
        .InitialURL(TEXT("about:blank"))
        .FrameRate(60)
        .BackgroundColor(FColor::Transparent)
        .OnLoadStarted(FSimpleDelegate::CreateUObject(this, &UOntoTwinWebHostWidget::HandleLoadStarted))
        .OnLoadCompleted(FSimpleDelegate::CreateUObject(this, &UOntoTwinWebHostWidget::HandleLoadCompleted))
        .OnLoadError(FSimpleDelegate::CreateUObject(this, &UOntoTwinWebHostWidget::HandleLoadError))
        .OnUrlChanged(FOnTextChanged::CreateUObject(this, &UOntoTwinWebHostWidget::HandleUrlChanged))
        .OnBeforePopup(FOnBeforePopupDelegate::CreateUObject(this, &UOntoTwinWebHostWidget::HandleBeforePopup))
        .OnBeforeNavigation(SWebInterface::FOnBeforeBrowse::CreateUObject(this, &UOntoTwinWebHostWidget::HandleBeforeNavigation));

    if (BridgeObject)
    {
        Browser->BindUObject(TEXT("ontotwinWebBridge"), BridgeObject, true);
    }

    return SNew(SOverlay)
        + SOverlay::Slot()
        [
            GlassLayer
        ]
        + SOverlay::Slot()
        [
            SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().Padding(18.0f, 12.0f)
            [
                SNew(SHorizontalBox)
                + SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, 8.0f, 0.0f)
                [
                    SNew(SButton)
                    .Text(FText::FromString(TEXT("返回")))
                    .OnClicked_UObject(this, &UOntoTwinWebHostWidget::HandleBackClicked)
                ]
                + SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, 8.0f, 0.0f)
                [
                    SNew(SButton)
                    .Text(FText::FromString(TEXT("重试")))
                    .OnClicked_UObject(this, &UOntoTwinWebHostWidget::HandleRetryClicked)
                ]
                + SHorizontalBox::Slot().FillWidth(1.0f).VAlign(VAlign_Center)
                [
                    SAssignNew(StatusText, STextBlock)
                    .Text(FText::FromString(TEXT("准备打开页面")))
                    .ColorAndOpacity(FSlateColor(FLinearColor(0.88f, 0.9f, 0.93f, 1.0f)))
                ]
                + SHorizontalBox::Slot().AutoWidth()
                [
                    SNew(SButton)
                    .Text(FText::FromString(TEXT("关闭")))
                    .OnClicked_UObject(this, &UOntoTwinWebHostWidget::HandleCloseClicked)
                ]
            ]
            + SVerticalBox::Slot().FillHeight(1.0f).Padding(12.0f, 0.0f, 12.0f, 12.0f)
            [
                SNew(SBorder)
                .BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
                .BorderBackgroundColor(FLinearColor(1.0f, 1.0f, 1.0f, 0.02f))
                .Padding(0.0f)
                [
                    Browser.ToSharedRef()
                ]
            ]
        ];
}

void UOntoTwinWebHostWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (!Browser.IsValid()) return;
    if (!bBridgeReady || InteractiveRegions.Num() == 0)
    {
        Browser->SetVisibility(EVisibility::Visible);
        return;
    }
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    float MouseX = 0.0f;
    float MouseY = 0.0f;
    if (!PC || !PC->GetMousePosition(MouseX, MouseY))
    {
        Browser->SetVisibility(EVisibility::Visible);
        return;
    }
    const FVector2D Local = Browser->GetCachedGeometry().AbsoluteToLocal(FVector2D(MouseX, MouseY));
    const bool bInsideInteractive = InteractiveRegions.ContainsByPredicate(
        [&Local](const FSlateRect& Region)
        {
            return Local.X >= Region.Left && Local.X <= Region.Right
                && Local.Y >= Region.Top && Local.Y <= Region.Bottom;
        });
    Browser->SetVisibility(bInsideInteractive ? EVisibility::Visible : EVisibility::HitTestInvisible);
}

void UOntoTwinWebHostWidget::NativeDestruct()
{
    if (Browser.IsValid() && BridgeObject)
    {
        Browser->UnbindUObject(TEXT("ontotwinWebBridge"), BridgeObject, true);
    }
    Browser.Reset();
    StatusText.Reset();
    Super::NativeDestruct();
}

void UOntoTwinWebHostWidget::Navigate(const FString& Url)
{
    if (Browser.IsValid()) Browser->LoadURL(Url);
}

void UOntoTwinWebHostWidget::ReloadPage()
{
    if (Browser.IsValid()) Browser->Reload();
}

void UOntoTwinWebHostWidget::ExecuteJavascript(const FString& Script)
{
    if (Browser.IsValid()) Browser->ExecuteJavascript(Script);
}

FString UOntoTwinWebHostWidget::GetCurrentUrl() const
{
    return Browser.IsValid() ? Browser->GetUrl() : FString();
}

void UOntoTwinWebHostWidget::SetHostStatus(const FString& Status, bool bError)
{
    bStatusError = bError;
    if (StatusText.IsValid())
    {
        StatusText->SetText(FText::FromString(Status));
        StatusText->SetColorAndOpacity(bStatusError
            ? FSlateColor(FLinearColor(0.95f, 0.35f, 0.3f, 1.0f))
            : FSlateColor(FLinearColor(0.88f, 0.9f, 0.93f, 1.0f)));
    }
}

void UOntoTwinWebHostWidget::SetBridgeReady(bool bReady)
{
    bBridgeReady = bReady;
    if (!bReady) InteractiveRegions.Reset();
}

void UOntoTwinWebHostWidget::SetInteractiveRegions(const TArray<FSlateRect>& Regions)
{
    InteractiveRegions = Regions;
}

void UOntoTwinWebHostWidget::HandleLoadStarted()
{
    bBridgeReady = false;
    InteractiveRegions.Reset();
    if (OwnerComponent) OwnerComponent->HandlePageLoadStarted();
    SetHostStatus(TEXT("正在加载页面"));
}

void UOntoTwinWebHostWidget::HandleLoadCompleted()
{
    SetHostStatus(TEXT("页面已加载"));
    if (OwnerComponent) OwnerComponent->HandlePageLoaded();
}

void UOntoTwinWebHostWidget::HandleLoadError()
{
    SetHostStatus(TEXT("页面加载失败，可重试、返回或关闭"), true);
    if (OwnerComponent) OwnerComponent->HandlePageLoadError();
}

void UOntoTwinWebHostWidget::HandleUrlChanged(const FText& UrlText)
{
    if (OwnerComponent) OwnerComponent->HandleUrlChanged(UrlText.ToString());
}

bool UOntoTwinWebHostWidget::HandleBeforePopup(FString Url, FString Frame)
{
    return !OwnerComponent || OwnerComponent->HandlePopupNavigation(Url);
}

bool UOntoTwinWebHostWidget::HandleBeforeNavigation(
    const FString& Url,
    const FWebNavigationRequest& Request)
{
    FString Reason;
    return !OwnerComponent || !OwnerComponent->ValidateNavigation(Url, Reason);
}

FReply UOntoTwinWebHostWidget::HandleBackClicked()
{
    if (OwnerComponent) OwnerComponent->Back();
    return FReply::Handled();
}

FReply UOntoTwinWebHostWidget::HandleCloseClicked()
{
    if (OwnerComponent) OwnerComponent->Close();
    return FReply::Handled();
}

FReply UOntoTwinWebHostWidget::HandleRetryClicked()
{
    if (OwnerComponent) OwnerComponent->Retry();
    return FReply::Handled();
}
