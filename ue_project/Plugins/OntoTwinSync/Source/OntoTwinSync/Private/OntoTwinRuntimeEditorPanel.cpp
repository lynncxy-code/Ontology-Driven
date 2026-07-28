#include "OntoTwinRuntimeEditorPanel.h"

#include "TwinSceneManager.h"
#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/CheckBox.h"
#include "Components/GridPanel.h"
#include "Components/GridSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateColor.h"
#include "Styling/SlateTypes.h"
#include "Widgets/SWidget.h"

namespace
{
const FLinearColor PanelBackground(0.078f, 0.078f, 0.078f, 0.92f);
const FLinearColor PrimaryText(0.96f, 0.96f, 0.96f, 1.0f);
const FLinearColor SecondaryText(0.64f, 0.64f, 0.64f, 1.0f);
const FLinearColor MutedText(0.46f, 0.46f, 0.46f, 1.0f);
const FLinearColor DividerColor(1.0f, 1.0f, 1.0f, 0.10f);
const FLinearColor HoverBackground(1.0f, 1.0f, 1.0f, 0.10f);
const FLinearColor PressedBackground(1.0f, 1.0f, 1.0f, 0.16f);
const FLinearColor ReadyColor(0.10f, 0.62f, 0.39f, 1.0f);
const FLinearColor WarningColor(0.83f, 0.56f, 0.20f, 1.0f);
const FLinearColor ErrorColor(0.78f, 0.24f, 0.20f, 1.0f);

FButtonStyle BuildButtonStyle(const FButtonStyle& BaseStyle, bool bPrimary)
{
    FButtonStyle Style = BaseStyle;
    const FLinearColor NormalColor = bPrimary ? PrimaryText : FLinearColor(1.0f, 1.0f, 1.0f, 0.04f);
    const FLinearColor HoverColor = bPrimary ? FLinearColor::White : HoverBackground;
    const FLinearColor PressedColor = bPrimary ? FLinearColor(0.82f, 0.82f, 0.82f, 1.0f) : PressedBackground;

    Style.SetNormal(FSlateRoundedBoxBrush(NormalColor, 6.0f));
    Style.SetHovered(FSlateRoundedBoxBrush(HoverColor, 6.0f));
    Style.SetPressed(FSlateRoundedBoxBrush(PressedColor, 6.0f));
    Style.SetDisabled(FSlateRoundedBoxBrush(FLinearColor(1.0f, 1.0f, 1.0f, 0.035f), 6.0f));
    Style.SetNormalPadding(FMargin(10.0f, 6.0f));
    Style.SetPressedPadding(FMargin(10.0f, 7.0f, 10.0f, 5.0f));
    return Style;
}

void SetTextColor(UTextBlock* Text, const FLinearColor& Color)
{
    if (Text)
    {
        Text->SetColorAndOpacity(FSlateColor(Color));
    }
}
}

void UOntoTwinRuntimeEditorPanel::SetSceneManager(ATwinSceneManager* InSceneManager)
{
    SceneManager = InSceneManager;
    RefreshFromManager();
}

TSharedRef<SWidget> UOntoTwinRuntimeEditorPanel::RebuildWidget()
{
    if (!WidgetTree)
    {
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("WidgetTree"), RF_Transient);
    }
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        BuildDefaultLayout();
    }

    return Super::RebuildWidget();
}

void UOntoTwinRuntimeEditorPanel::NativeConstruct()
{
    Super::NativeConstruct();

    if (AccessActionButton)
    {
        AccessActionButton->OnClicked.RemoveAll(this);
        AccessActionButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleAccessActionClicked);
    }
    if (CloseButton)
    {
        CloseButton->OnClicked.RemoveAll(this);
        CloseButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleCloseClicked);
    }
    if (SaveButton)
    {
        SaveButton->OnClicked.RemoveAll(this);
        SaveButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleSaveClicked);
    }
    if (CancelButton)
    {
        CancelButton->OnClicked.RemoveAll(this);
        CancelButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleCancelClicked);
    }
    if (WallSnapCheckBox)
    {
        WallSnapCheckBox->OnCheckStateChanged.RemoveAll(this);
        WallSnapCheckBox->OnCheckStateChanged.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleWallSnapChanged);
    }
    if (GridSnapCheckBox)
    {
        GridSnapCheckBox->OnCheckStateChanged.RemoveAll(this);
        GridSnapCheckBox->OnCheckStateChanged.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleGridSnapChanged);
    }

    RefreshFromManager();
}

void UOntoTwinRuntimeEditorPanel::NativeDestruct()
{
    if (UWorld* World = GetWorld())
    {
        World->GetTimerManager().ClearTimer(ToastTimerHandle);
    }
    Super::NativeDestruct();
}

void UOntoTwinRuntimeEditorPanel::BuildDefaultLayout()
{
    if (!WidgetTree) return;

    UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RuntimeEditorRoot"));
    Root->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    WidgetTree->RootWidget = Root;

    USizeBox* PanelBounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("PanelBounds"));
    PanelBounds->SetWidthOverride(400.0f);
    PanelBounds->SetMinDesiredHeight(306.0f);

    PanelBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PanelBorder"));
    PanelBorder->SetPadding(FMargin(16.0f));
    PanelBorder->SetBrush(FSlateRoundedBoxBrush(PanelBackground, 6.0f));
    PanelBounds->AddChild(PanelBorder);

    UCanvasPanelSlot* PanelSlot = Root->AddChildToCanvas(PanelBounds);
    if (PanelSlot)
    {
        PanelSlot->SetAnchors(FAnchors(0.0f, 0.0f));
        PanelSlot->SetPosition(FVector2D(24.0f, 24.0f));
        PanelSlot->SetAutoSize(true);
    }

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("PanelStack"));
    PanelBorder->SetContent(Stack);

    UHorizontalBox* Header = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Header"));
    UVerticalBoxSlot* HeaderSlot = Stack->AddChildToVerticalBox(Header);
    HeaderSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    UTextBlock* TitleText = CreateText(TEXT("TitleText"), TEXT("Runtime Editor"), 16, PrimaryText, true);
    UHorizontalBoxSlot* TitleSlot = Header->AddChildToHorizontalBox(TitleText);
    TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    TitleSlot->SetVerticalAlignment(VAlign_Center);

    HeaderStateText = CreateText(TEXT("HeaderStateText"), TEXT("Editing"), 11, SecondaryText, true);
    UHorizontalBoxSlot* HeaderStateSlot = Header->AddChildToHorizontalBox(HeaderStateText);
    HeaderStateSlot->SetPadding(FMargin(8.0f, 0.0f, 8.0f, 0.0f));
    HeaderStateSlot->SetVerticalAlignment(VAlign_Center);

    UTextBlock* CloseLabel = nullptr;
    CloseButton = CreateButton(TEXT("CloseButton"), TEXT("X"), CloseLabel, false);
    CloseButton->SetToolTipText(FText::FromString(TEXT("Close editor")));
    USizeBox* CloseBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("CloseBox"));
    CloseBox->SetWidthOverride(24.0f);
    CloseBox->SetHeightOverride(24.0f);
    CloseBox->AddChild(CloseButton);
    UHorizontalBoxSlot* CloseSlot = Header->AddChildToHorizontalBox(CloseBox);
    CloseSlot->SetVerticalAlignment(VAlign_Center);

    UBorder* Divider = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("HeaderDivider"));
    Divider->SetBrushColor(DividerColor);
    USizeBox* DividerBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("HeaderDividerBox"));
    DividerBox->SetHeightOverride(1.0f);
    DividerBox->AddChild(Divider);
    UVerticalBoxSlot* DividerSlot = Stack->AddChildToVerticalBox(DividerBox);
    DividerSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    UTextBlock* DeviceLabel = CreateText(TEXT("DeviceLabel"), TEXT("DEVICE"), 10, MutedText, true);
    Stack->AddChildToVerticalBox(DeviceLabel);

    DisplayNameText = CreateText(TEXT("DisplayNameText"), TEXT("No instance selected"), 14, PrimaryText, true);
    UVerticalBoxSlot* DisplayNameSlot = Stack->AddChildToVerticalBox(DisplayNameText);
    DisplayNameSlot->SetPadding(FMargin(0.0f, 1.0f, 0.0f, 0.0f));

    InstanceIdText = CreateText(TEXT("InstanceIdText"), TEXT("-"), 11, SecondaryText);
    UVerticalBoxSlot* InstanceIdSlot = Stack->AddChildToVerticalBox(InstanceIdText);
    InstanceIdSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 7.0f));

    UGridPanel* TransformGrid = WidgetTree->ConstructWidget<UGridPanel>(UGridPanel::StaticClass(), TEXT("TransformGrid"));
    TransformGrid->SetColumnFill(1, 1.0f);
    TransformGrid->SetColumnFill(3, 1.0f);
    UVerticalBoxSlot* TransformGridSlot = Stack->AddChildToVerticalBox(TransformGrid);
    TransformGridSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));

    auto AddTransformCell = [this, TransformGrid](const FName LabelName, const FString& Label,
        UTextBlock*& ValueText, const FName ValueName, int32 Row, int32 Column)
    {
        UTextBlock* LabelText = CreateText(LabelName, Label, 11, MutedText, true);
        UGridSlot* LabelSlot = TransformGrid->AddChildToGrid(LabelText, Row, Column);
        LabelSlot->SetPadding(FMargin(Column == 0 ? 0.0f : 12.0f, 1.0f, 6.0f, 1.0f));
        LabelSlot->SetVerticalAlignment(VAlign_Center);

        ValueText = CreateText(ValueName, TEXT("-"), 12, PrimaryText);
        UGridSlot* ValueSlot = TransformGrid->AddChildToGrid(ValueText, Row, Column + 1);
        ValueSlot->SetPadding(FMargin(0.0f, 1.0f));
        ValueSlot->SetHorizontalAlignment(HAlign_Right);
        ValueSlot->SetVerticalAlignment(VAlign_Center);
    };

    AddTransformCell(TEXT("XLabel"), TEXT("X"), XValueText, TEXT("XValue"), 0, 0);
    AddTransformCell(TEXT("YLabel"), TEXT("Y"), YValueText, TEXT("YValue"), 0, 2);
    AddTransformCell(TEXT("ZLabel"), TEXT("Z"), ZValueText, TEXT("ZValue"), 1, 0);
    AddTransformCell(TEXT("YawLabel"), TEXT("Yaw"), YawValueText, TEXT("YawValue"), 1, 2);

    UTextBlock* AccessLabel = CreateText(TEXT("AccessLabel"), TEXT("DATASET ACCESS"), 10, MutedText, true);
    Stack->AddChildToVerticalBox(AccessLabel);

    UHorizontalBox* AccessRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("AccessRow"));
    UVerticalBoxSlot* AccessRowSlot = Stack->AddChildToVerticalBox(AccessRow);
    AccessRowSlot->SetPadding(FMargin(0.0f, 2.0f, 0.0f, 7.0f));

    AccessStatusDot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("AccessStatusDot"));
    AccessStatusDot->SetBrush(FSlateRoundedBoxBrush(MutedText, 3.0f));
    USizeBox* AccessDotBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("AccessDotBox"));
    AccessDotBox->SetWidthOverride(6.0f);
    AccessDotBox->SetHeightOverride(6.0f);
    AccessDotBox->AddChild(AccessStatusDot);
    UHorizontalBoxSlot* AccessDotSlot = AccessRow->AddChildToHorizontalBox(AccessDotBox);
    AccessDotSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
    AccessDotSlot->SetVerticalAlignment(VAlign_Center);

    AccessStatusText = CreateText(TEXT("AccessStatusText"), TEXT("Checking access"), 12, PrimaryText);
    UHorizontalBoxSlot* AccessTextSlot = AccessRow->AddChildToHorizontalBox(AccessStatusText);
    AccessTextSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    AccessTextSlot->SetVerticalAlignment(VAlign_Center);

    AccessActionButton = CreateButton(TEXT("AccessActionButton"), TEXT("Checking..."), AccessActionLabel, false);
    UHorizontalBoxSlot* AccessActionSlot = AccessRow->AddChildToHorizontalBox(AccessActionButton);
    AccessActionSlot->SetPadding(FMargin(8.0f, 0.0f, 0.0f, 0.0f));
    AccessActionSlot->SetVerticalAlignment(VAlign_Center);

    UHorizontalBox* Toggles = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SnapToggles"));
    UVerticalBoxSlot* TogglesSlot = Stack->AddChildToVerticalBox(Toggles);
    TogglesSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 9.0f));

    auto AddSnapToggle = [this, Toggles](const FName CheckName, const FString& Label, UCheckBox*& OutCheckBox)
    {
        OutCheckBox = WidgetTree->ConstructWidget<UCheckBox>(UCheckBox::StaticClass(), CheckName);
        UTextBlock* ToggleLabel = CreateText(FName(*(CheckName.ToString() + TEXT("Label"))), Label, 11, SecondaryText);
        OutCheckBox->SetContent(ToggleLabel);
        UHorizontalBoxSlot* ToggleSlot = Toggles->AddChildToHorizontalBox(OutCheckBox);
        ToggleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ToggleSlot->SetVerticalAlignment(VAlign_Center);
    };

    AddSnapToggle(TEXT("WallSnapCheckBox"), TEXT("Wall snap"), WallSnapCheckBox);
    AddSnapToggle(TEXT("GridSnapCheckBox"), TEXT("Grid snap"), GridSnapCheckBox);

    UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Footer"));
    Stack->AddChildToVerticalBox(Footer);

    UTextBlock* CancelLabel = nullptr;
    CancelButton = CreateButton(TEXT("CancelButton"), TEXT("Cancel"), CancelLabel, false);
    UHorizontalBoxSlot* CancelSlot = Footer->AddChildToHorizontalBox(CancelButton);
    CancelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CancelSlot->SetPadding(FMargin(0.0f, 0.0f, 4.0f, 0.0f));

    SaveButton = CreateButton(TEXT("SaveButton"), TEXT("Save changes"), SaveButtonLabel, true);
    UHorizontalBoxSlot* SaveSlot = Footer->AddChildToHorizontalBox(SaveButton);
    SaveSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    SaveSlot->SetPadding(FMargin(4.0f, 0.0f, 0.0f, 0.0f));

    ToastBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ToastBorder"));
    ToastBorder->SetPadding(FMargin(0.0f));
    ToastBorder->SetBrush(FSlateRoundedBoxBrush(FLinearColor(0.055f, 0.055f, 0.055f, 0.96f), 6.0f));
    ToastBorder->SetVisibility(ESlateVisibility::Collapsed);

    UCanvasPanelSlot* ToastSlot = Root->AddChildToCanvas(ToastBorder);
    if (ToastSlot)
    {
        ToastSlot->SetAnchors(FAnchors(1.0f, 0.0f));
        ToastSlot->SetAlignment(FVector2D(1.0f, 0.0f));
        ToastSlot->SetPosition(FVector2D(-24.0f, 24.0f));
        ToastSlot->SetAutoSize(true);
    }

    UHorizontalBox* ToastRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("ToastRow"));
    ToastBorder->SetContent(ToastRow);

    ToastAccent = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ToastAccent"));
    ToastAccent->SetBrush(FSlateRoundedBoxBrush(SecondaryText, 1.0f));
    USizeBox* ToastAccentBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("ToastAccentBox"));
    ToastAccentBox->SetWidthOverride(2.0f);
    ToastAccentBox->SetMinDesiredHeight(36.0f);
    ToastAccentBox->AddChild(ToastAccent);
    ToastRow->AddChildToHorizontalBox(ToastAccentBox);

    ToastText = CreateText(TEXT("ToastText"), TEXT(""), 12, PrimaryText);
    ToastText->SetAutoWrapText(true);
    ToastText->SetWrapTextAt(300.0f);
    USizeBox* ToastTextBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("ToastTextBox"));
    ToastTextBox->SetMaxDesiredWidth(320.0f);
    ToastTextBox->AddChild(ToastText);
    UHorizontalBoxSlot* ToastTextSlot = ToastRow->AddChildToHorizontalBox(ToastTextBox);
    ToastTextSlot->SetPadding(FMargin(12.0f, 9.0f, 14.0f, 9.0f));
    ToastTextSlot->SetVerticalAlignment(VAlign_Center);
}

UTextBlock* UOntoTwinRuntimeEditorPanel::CreateText(const FName Name, const FString& InitialText,
    int32 FontSize, const FLinearColor& Color, bool bBold) const
{
    if (!WidgetTree) return nullptr;

    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
    Text->SetText(FText::FromString(InitialText));
    Text->SetColorAndOpacity(FSlateColor(Color));
    Text->SetFont(FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), FontSize));
    Text->SetAutoWrapText(false);
    return Text;
}

UButton* UOntoTwinRuntimeEditorPanel::CreateButton(const FName Name, const FString& Label,
    UTextBlock*& OutLabel, bool bPrimary) const
{
    if (!WidgetTree) return nullptr;

    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
    Button->SetStyle(BuildButtonStyle(Button->GetStyle(), bPrimary));

    OutLabel = CreateText(FName(*(Name.ToString() + TEXT("Label"))), Label, 11,
        bPrimary ? PanelBackground : PrimaryText, true);
    OutLabel->SetJustification(ETextJustify::Center);
    Button->SetContent(OutLabel);
    return Button;
}

void UOntoTwinRuntimeEditorPanel::ShowToast(const FString& Message, EOntoTwinRuntimeToastType Type)
{
    if (!ToastBorder || !ToastAccent || !ToastText) return;

    FLinearColor AccentColor = SecondaryText;
    switch (Type)
    {
    case EOntoTwinRuntimeToastType::Success:
        AccentColor = ReadyColor;
        break;
    case EOntoTwinRuntimeToastType::Warning:
        AccentColor = WarningColor;
        break;
    case EOntoTwinRuntimeToastType::Error:
        AccentColor = ErrorColor;
        break;
    case EOntoTwinRuntimeToastType::Info:
    default:
        break;
    }

    ToastText->SetText(FText::FromString(Message));
    ToastAccent->SetBrush(FSlateRoundedBoxBrush(AccentColor, 1.0f));
    ToastBorder->SetVisibility(ESlateVisibility::HitTestInvisible);

    if (UWorld* World = GetWorld())
    {
        World->GetTimerManager().ClearTimer(ToastTimerHandle);
        World->GetTimerManager().SetTimer(
            ToastTimerHandle,
            this,
            &UOntoTwinRuntimeEditorPanel::HideToast,
            2.5f,
            false);
    }
}

bool UOntoTwinRuntimeEditorPanel::IsPointerOverPanel() const
{
    if (!PanelBorder || !PanelBorder->IsVisible() || !FSlateApplication::IsInitialized())
    {
        return false;
    }

    return PanelBorder->GetCachedGeometry().IsUnderLocation(FSlateApplication::Get().GetCursorPos());
}

void UOntoTwinRuntimeEditorPanel::HideToast()
{
    if (ToastBorder)
    {
        ToastBorder->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void UOntoTwinRuntimeEditorPanel::RefreshFromManager()
{
    if (!SceneManager) return;

    if (HeaderStateText)
    {
        HeaderStateText->SetText(FText::FromString(SceneManager->GetRuntimeEditorHeaderStateText()));
        SetTextColor(HeaderStateText,
            SceneManager->IsRuntimeEditDirty() && !SceneManager->IsRuntimeEditSaving() ? WarningColor : SecondaryText);
    }

    if (DisplayNameText)
    {
        DisplayNameText->SetText(FText::FromString(SceneManager->GetRuntimeEditorDisplayName()));
    }
    if (InstanceIdText)
    {
        InstanceIdText->SetText(FText::FromString(SceneManager->GetRuntimeEditorInstanceIdText()));
    }

    FVector Location = FVector::ZeroVector;
    float Yaw = 0.0f;
    const bool bHasTransform = SceneManager->GetRuntimeEditorTransform(Location, Yaw);
    if (XValueText) XValueText->SetText(FText::FromString(bHasTransform ? FString::Printf(TEXT("%.1f"), Location.X) : TEXT("-")));
    if (YValueText) YValueText->SetText(FText::FromString(bHasTransform ? FString::Printf(TEXT("%.1f"), Location.Y) : TEXT("-")));
    if (ZValueText) ZValueText->SetText(FText::FromString(bHasTransform ? FString::Printf(TEXT("%.1f"), Location.Z) : TEXT("-")));
    if (YawValueText) YawValueText->SetText(FText::FromString(bHasTransform ? FString::Printf(TEXT("%.1f"), Yaw) : TEXT("-")));

    const EOntoTwinRuntimeAccessState AccessState = SceneManager->GetRuntimeEditorAccessState();
    FLinearColor AccessColor = MutedText;
    FString AccessText = TEXT("Unable to verify");
    FString ActionText;
    bool bShowAccessAction = false;
    bool bEnableAccessAction = false;

    switch (AccessState)
    {
    case EOntoTwinRuntimeAccessState::Checking:
        AccessText = TEXT("Checking access");
        ActionText = TEXT("Checking...");
        bShowAccessAction = true;
        break;
    case EOntoTwinRuntimeAccessState::Ready:
        AccessColor = ReadyColor;
        AccessText = TEXT("Ready");
        break;
    case EOntoTwinRuntimeAccessState::Unbound:
        AccessColor = WarningColor;
        AccessText = TEXT("Not bound");
        ActionText = TEXT("Bind active dataset");
        bShowAccessAction = true;
        bEnableAccessAction = SceneManager->CanBindRuntimeProject();
        break;
    case EOntoTwinRuntimeAccessState::Mismatch:
        AccessColor = ErrorColor;
        AccessText = TEXT("Bound to another UE project");
        break;
    case EOntoTwinRuntimeAccessState::Error:
    default:
        AccessColor = ErrorColor;
        AccessText = TEXT("Unable to verify");
        ActionText = TEXT("Retry");
        bShowAccessAction = true;
        bEnableAccessAction = SceneManager->CanRetryRuntimeBindingStatus();
        break;
    }

    if (AccessStatusDot)
    {
        AccessStatusDot->SetBrush(FSlateRoundedBoxBrush(AccessColor, 3.0f));
    }
    if (AccessStatusText)
    {
        AccessStatusText->SetText(FText::FromString(AccessText));
    }
    if (AccessActionLabel)
    {
        AccessActionLabel->SetText(FText::FromString(ActionText));
    }
    if (AccessActionButton)
    {
        AccessActionButton->SetVisibility(bShowAccessAction ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
        AccessActionButton->SetIsEnabled(bEnableAccessAction);
    }

    if (SaveButtonLabel)
    {
        SaveButtonLabel->SetText(FText::FromString(SceneManager->IsRuntimeEditSaving() ? TEXT("Saving...") : TEXT("Save changes")));
    }
    if (SaveButton) SaveButton->SetIsEnabled(SceneManager->CanSaveRuntimeEdit());
    if (CancelButton) CancelButton->SetIsEnabled(SceneManager->CanCancelRuntimeEdit());
    if (CloseButton) CloseButton->SetIsEnabled(!SceneManager->IsRuntimeEditSaving());

    if (WallSnapCheckBox && WallSnapCheckBox->IsChecked() != SceneManager->IsRuntimeWallSnapEnabled())
    {
        WallSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeWallSnapEnabled());
    }
    if (GridSnapCheckBox && GridSnapCheckBox->IsChecked() != SceneManager->IsRuntimeGridSnapEnabled())
    {
        GridSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeGridSnapEnabled());
    }
}

void UOntoTwinRuntimeEditorPanel::HandleAccessActionClicked()
{
    if (!SceneManager) return;

    if (SceneManager->GetRuntimeEditorAccessState() == EOntoTwinRuntimeAccessState::Unbound)
    {
        SceneManager->BindCurrentRuntimeProject();
    }
    else
    {
        SceneManager->RetryRuntimeBindingStatus();
    }
}

void UOntoTwinRuntimeEditorPanel::HandleCloseClicked()
{
    if (SceneManager) SceneManager->ToggleRuntimeEditMode();
}

void UOntoTwinRuntimeEditorPanel::HandleSaveClicked()
{
    if (SceneManager) SceneManager->SaveRuntimeEdit();
}

void UOntoTwinRuntimeEditorPanel::HandleCancelClicked()
{
    if (SceneManager) SceneManager->CancelRuntimeEdit();
}

void UOntoTwinRuntimeEditorPanel::HandleWallSnapChanged(bool bIsChecked)
{
    if (SceneManager) SceneManager->SetRuntimeWallSnapEnabled(bIsChecked);
}

void UOntoTwinRuntimeEditorPanel::HandleGridSnapChanged(bool bIsChecked)
{
    if (SceneManager) SceneManager->SetRuntimeGridSnapEnabled(bIsChecked);
}
