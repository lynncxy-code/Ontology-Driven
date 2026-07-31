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
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Framework/Application/SlateApplication.h"
#include "InputCoreTypes.h"
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
    SetIsFocusable(true);

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
    if (UndoButton)
    {
        UndoButton->OnClicked.RemoveAll(this);
        UndoButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleUndoClicked);
    }
    if (RedoButton)
    {
        RedoButton->OnClicked.RemoveAll(this);
        RedoButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleRedoClicked);
    }
    if (RemoveButton)
    {
        RemoveButton->OnClicked.RemoveAll(this);
        RemoveButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleRemoveClicked);
    }
    if (PendingToggleButton)
    {
        PendingToggleButton->OnClicked.RemoveAll(this);
        PendingToggleButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandlePendingToggleClicked);
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
    if (ConfirmationPrimaryButton)
    {
        ConfirmationPrimaryButton->OnClicked.RemoveAll(this);
        ConfirmationPrimaryButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleConfirmationPrimaryClicked);
    }
    if (ConfirmationSecondaryButton)
    {
        ConfirmationSecondaryButton->OnClicked.RemoveAll(this);
        ConfirmationSecondaryButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleConfirmationSecondaryClicked);
    }
    if (ConfirmationContinueButton)
    {
        ConfirmationContinueButton->OnClicked.RemoveAll(this);
        ConfirmationContinueButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleConfirmationContinueClicked);
    }

    RefreshFromManager();
}

FReply UOntoTwinRuntimeEditorPanel::NativeOnKeyDown(
    const FGeometry& InGeometry,
    const FKeyEvent& InKeyEvent)
{
    if (InKeyEvent.GetKey() == EKeys::Escape && IsConfirmationOpen())
    {
        HideConfirmation();
        return FReply::Handled();
    }
    return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
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

    PanelBounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("PanelBounds"));
    PanelBounds->SetWidthOverride(440.0f);
    PanelBounds->SetMinDesiredHeight(420.0f);
    PanelBounds->SetMaxDesiredHeight(720.0f);

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

    UTextBlock* TitleText = CreateText(TEXT("TitleText"), TEXT("运行时编辑器"), 16, PrimaryText, true);
    UHorizontalBoxSlot* TitleSlot = Header->AddChildToHorizontalBox(TitleText);
    TitleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    TitleSlot->SetVerticalAlignment(VAlign_Center);

    HeaderStateText = CreateText(TEXT("HeaderStateText"), TEXT("编辑中"), 11, SecondaryText, true);
    UHorizontalBoxSlot* HeaderStateSlot = Header->AddChildToHorizontalBox(HeaderStateText);
    HeaderStateSlot->SetPadding(FMargin(8.0f, 0.0f, 6.0f, 0.0f));
    HeaderStateSlot->SetVerticalAlignment(VAlign_Center);

    UTextBlock* UndoLabel = nullptr;
    UndoButton = CreateButton(TEXT("UndoButton"), TEXT("撤销"), UndoLabel, false);
    UndoButton->SetToolTipText(FText::FromString(TEXT("撤销上一步（Ctrl+Z）")));
    UHorizontalBoxSlot* UndoSlot = Header->AddChildToHorizontalBox(UndoButton);
    UndoSlot->SetPadding(FMargin(0.0f, 0.0f, 4.0f, 0.0f));
    UndoSlot->SetVerticalAlignment(VAlign_Center);

    UTextBlock* RedoLabel = nullptr;
    RedoButton = CreateButton(TEXT("RedoButton"), TEXT("重做"), RedoLabel, false);
    RedoButton->SetToolTipText(FText::FromString(TEXT("重做（Ctrl+Y）")));
    UHorizontalBoxSlot* RedoSlot = Header->AddChildToHorizontalBox(RedoButton);
    RedoSlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 0.0f));
    RedoSlot->SetVerticalAlignment(VAlign_Center);

    UTextBlock* CloseLabel = nullptr;
    CloseButton = CreateButton(TEXT("CloseButton"), TEXT("×"), CloseLabel, false);
    CloseButton->SetToolTipText(FText::FromString(TEXT("退出编辑器")));
    USizeBox* CloseBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("CloseBox"));
    CloseBox->SetWidthOverride(30.0f);
    CloseBox->SetHeightOverride(28.0f);
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

    UScrollBox* BodyScroll = WidgetTree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(), TEXT("BodyScroll"));
    BodyScroll->SetScrollBarVisibility(ESlateVisibility::Visible);
    UVerticalBoxSlot* BodyScrollSlot = Stack->AddChildToVerticalBox(BodyScroll);
    BodyScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

    UVerticalBox* Body = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("Body"));
    BodyScroll->AddChild(Body);

    UTextBlock* DeviceLabel = CreateText(TEXT("DeviceLabel"), TEXT("选中对象"), 10, MutedText, true);
    Body->AddChildToVerticalBox(DeviceLabel);

    UGridPanel* IdentityGrid = WidgetTree->ConstructWidget<UGridPanel>(UGridPanel::StaticClass(), TEXT("IdentityGrid"));
    IdentityGrid->SetColumnFill(1, 1.0f);
    UVerticalBoxSlot* IdentitySlot = Body->AddChildToVerticalBox(IdentityGrid);
    IdentitySlot->SetPadding(FMargin(0.0f, 4.0f, 6.0f, 4.0f));

    UTextBlock* NameLabel = CreateText(TEXT("NameLabel"), TEXT("实例名称"), 11, MutedText, true);
    UGridSlot* NameLabelSlot = IdentityGrid->AddChildToGrid(NameLabel, 0, 0);
    NameLabelSlot->SetPadding(FMargin(0.0f, 2.0f, 12.0f, 2.0f));
    DisplayNameText = CreateText(TEXT("DisplayNameText"), TEXT("未选择实例"), 12, PrimaryText, true);
    DisplayNameText->SetAutoWrapText(true);
    DisplayNameText->SetWrapTextAt(280.0f);
    UGridSlot* DisplayNameSlot = IdentityGrid->AddChildToGrid(DisplayNameText, 0, 1);
    DisplayNameSlot->SetPadding(FMargin(0.0f, 2.0f));
    DisplayNameSlot->SetHorizontalAlignment(HAlign_Right);

    UTextBlock* IdLabel = CreateText(TEXT("IdLabel"), TEXT("实例 ID"), 11, MutedText, true);
    UGridSlot* IdLabelSlot = IdentityGrid->AddChildToGrid(IdLabel, 1, 0);
    IdLabelSlot->SetPadding(FMargin(0.0f, 2.0f, 12.0f, 2.0f));
    InstanceIdText = CreateText(TEXT("InstanceIdText"), TEXT("-"), 11, SecondaryText);
    UGridSlot* InstanceIdSlot = IdentityGrid->AddChildToGrid(InstanceIdText, 1, 1);
    InstanceIdSlot->SetPadding(FMargin(0.0f, 2.0f));
    InstanceIdSlot->SetHorizontalAlignment(HAlign_Right);

    UTextBlock* RemoveLabel = nullptr;
    RemoveButton = CreateButton(TEXT("RemoveButton"), TEXT("从场景移除"), RemoveLabel, false);
    RemoveButton->SetToolTipText(FText::FromString(TEXT("立即隐藏所选实例，保存后可在 Web 端重新加载")));
    UVerticalBoxSlot* RemoveSlot = Body->AddChildToVerticalBox(RemoveButton);
    RemoveSlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 10.0f));

    UGridPanel* TransformGrid = WidgetTree->ConstructWidget<UGridPanel>(UGridPanel::StaticClass(), TEXT("TransformGrid"));
    TransformGrid->SetColumnFill(1, 1.0f);
    TransformGrid->SetColumnFill(3, 1.0f);
    UVerticalBoxSlot* TransformGridSlot = Body->AddChildToVerticalBox(TransformGrid);
    TransformGridSlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 10.0f));

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
    AddTransformCell(TEXT("YawLabel"), TEXT("偏航"), YawValueText, TEXT("YawValue"), 1, 2);
    YawLabelText = Cast<UTextBlock>(WidgetTree->FindWidget(TEXT("YawLabel")));

    UTextBlock* AccessLabel = CreateText(TEXT("AccessLabel"), TEXT("数据集访问"), 10, MutedText, true);
    Body->AddChildToVerticalBox(AccessLabel);

    UHorizontalBox* AccessRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("AccessRow"));
    UVerticalBoxSlot* AccessRowSlot = Body->AddChildToVerticalBox(AccessRow);
    AccessRowSlot->SetPadding(FMargin(0.0f, 2.0f, 6.0f, 9.0f));

    AccessStatusDot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("AccessStatusDot"));
    AccessStatusDot->SetBrush(FSlateRoundedBoxBrush(MutedText, 3.0f));
    USizeBox* AccessDotBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("AccessDotBox"));
    AccessDotBox->SetWidthOverride(6.0f);
    AccessDotBox->SetHeightOverride(6.0f);
    AccessDotBox->AddChild(AccessStatusDot);
    UHorizontalBoxSlot* AccessDotSlot = AccessRow->AddChildToHorizontalBox(AccessDotBox);
    AccessDotSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
    AccessDotSlot->SetVerticalAlignment(VAlign_Center);

    AccessStatusText = CreateText(TEXT("AccessStatusText"), TEXT("正在检查"), 12, PrimaryText);
    UHorizontalBoxSlot* AccessTextSlot = AccessRow->AddChildToHorizontalBox(AccessStatusText);
    AccessTextSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    AccessTextSlot->SetVerticalAlignment(VAlign_Center);

    AccessActionButton = CreateButton(TEXT("AccessActionButton"), TEXT("检查中..."), AccessActionLabel, false);
    UHorizontalBoxSlot* AccessActionSlot = AccessRow->AddChildToHorizontalBox(AccessActionButton);
    AccessActionSlot->SetPadding(FMargin(8.0f, 0.0f, 0.0f, 0.0f));
    AccessActionSlot->SetVerticalAlignment(VAlign_Center);

    UHorizontalBox* Toggles = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("SnapToggles"));
    UVerticalBoxSlot* TogglesSlot = Body->AddChildToVerticalBox(Toggles);
    TogglesSlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 10.0f));

    auto AddSnapToggle = [this, Toggles](const FName CheckName, const FString& Label, UCheckBox*& OutCheckBox)
    {
        OutCheckBox = WidgetTree->ConstructWidget<UCheckBox>(UCheckBox::StaticClass(), CheckName);
        UTextBlock* ToggleLabel = CreateText(FName(*(CheckName.ToString() + TEXT("Label"))), Label, 11, SecondaryText);
        OutCheckBox->SetContent(ToggleLabel);
        UHorizontalBoxSlot* ToggleSlot = Toggles->AddChildToHorizontalBox(OutCheckBox);
        ToggleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        ToggleSlot->SetVerticalAlignment(VAlign_Center);
    };

    AddSnapToggle(TEXT("WallSnapCheckBox"), TEXT("靠墙吸附"), WallSnapCheckBox);
    AddSnapToggle(TEXT("GridSnapCheckBox"), TEXT("网格吸附"), GridSnapCheckBox);

    PendingToggleButton = CreateButton(TEXT("PendingToggleButton"), TEXT("待保存修改（0）"), PendingToggleLabel, false);
    UVerticalBoxSlot* PendingToggleSlot = Body->AddChildToVerticalBox(PendingToggleButton);
    PendingToggleSlot->SetPadding(FMargin(0.0f, 0.0f, 6.0f, 4.0f));

    PendingList = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("PendingList"));
    PendingList->SetVisibility(ESlateVisibility::Collapsed);
    UVerticalBoxSlot* PendingListSlot = Body->AddChildToVerticalBox(PendingList);
    PendingListSlot->SetPadding(FMargin(8.0f, 0.0f, 12.0f, 10.0f));

    UBorder* FooterDivider = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("FooterDivider"));
    FooterDivider->SetBrushColor(DividerColor);
    USizeBox* FooterDividerBox = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("FooterDividerBox"));
    FooterDividerBox->SetHeightOverride(1.0f);
    FooterDividerBox->AddChild(FooterDivider);
    UVerticalBoxSlot* FooterDividerSlot = Stack->AddChildToVerticalBox(FooterDividerBox);
    FooterDividerSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 10.0f));

    UHorizontalBox* Footer = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Footer"));
    Stack->AddChildToVerticalBox(Footer);

    UTextBlock* CancelLabel = nullptr;
    CancelButton = CreateButton(TEXT("CancelButton"), TEXT("取消全部修改"), CancelLabel, false);
    UHorizontalBoxSlot* CancelSlot = Footer->AddChildToHorizontalBox(CancelButton);
    CancelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    CancelSlot->SetPadding(FMargin(0.0f, 0.0f, 4.0f, 0.0f));

    SaveButton = CreateButton(TEXT("SaveButton"), TEXT("保存全部修改"), SaveButtonLabel, true);
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

    ConfirmationOverlay = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("ConfirmationOverlay"));
    ConfirmationOverlay->SetBrushColor(FLinearColor(0.0f, 0.0f, 0.0f, 0.58f));
    ConfirmationOverlay->SetHorizontalAlignment(HAlign_Center);
    ConfirmationOverlay->SetVerticalAlignment(VAlign_Center);
    ConfirmationOverlay->SetVisibility(ESlateVisibility::Collapsed);
    UCanvasPanelSlot* ConfirmationSlot = Root->AddChildToCanvas(ConfirmationOverlay);
    if (ConfirmationSlot)
    {
        ConfirmationSlot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
        ConfirmationSlot->SetOffsets(FMargin(0.0f));
    }

    USizeBox* DialogBounds = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(), TEXT("DialogBounds"));
    DialogBounds->SetWidthOverride(380.0f);
    UBorder* DialogBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("DialogBorder"));
    DialogBorder->SetPadding(FMargin(18.0f));
    DialogBorder->SetBrush(FSlateRoundedBoxBrush(FLinearColor(0.07f, 0.07f, 0.07f, 0.99f), 6.0f));
    DialogBounds->AddChild(DialogBorder);
    ConfirmationOverlay->SetContent(DialogBounds);

    UVerticalBox* DialogStack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("DialogStack"));
    DialogBorder->SetContent(DialogStack);
    ConfirmationTitleText = CreateText(TEXT("ConfirmationTitleText"), TEXT("确认操作"), 15, PrimaryText, true);
    DialogStack->AddChildToVerticalBox(ConfirmationTitleText);
    ConfirmationBodyText = CreateText(TEXT("ConfirmationBodyText"), TEXT(""), 12, SecondaryText);
    ConfirmationBodyText->SetAutoWrapText(true);
    ConfirmationBodyText->SetWrapTextAt(338.0f);
    UVerticalBoxSlot* ConfirmationBodySlot = DialogStack->AddChildToVerticalBox(ConfirmationBodyText);
    ConfirmationBodySlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 14.0f));

    ConfirmationPrimaryButton = CreateButton(TEXT("ConfirmationPrimaryButton"), TEXT("确认"), ConfirmationPrimaryLabel, true);
    UVerticalBoxSlot* ConfirmationPrimarySlot = DialogStack->AddChildToVerticalBox(ConfirmationPrimaryButton);
    ConfirmationPrimarySlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 6.0f));
    ConfirmationSecondaryButton = CreateButton(TEXT("ConfirmationSecondaryButton"), TEXT("放弃"), ConfirmationSecondaryLabel, false);
    UVerticalBoxSlot* ConfirmationSecondarySlot = DialogStack->AddChildToVerticalBox(ConfirmationSecondaryButton);
    ConfirmationSecondarySlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 6.0f));
    ConfirmationContinueButton = CreateButton(TEXT("ConfirmationContinueButton"), TEXT("继续编辑"), ConfirmationContinueLabel, false);
    DialogStack->AddChildToVerticalBox(ConfirmationContinueButton);
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

void UOntoTwinRuntimeEditorPanel::ShowExitConfirmation()
{
    if (!ConfirmationOverlay) return;

    ConfirmationMode = EOntoTwinRuntimePanelConfirmation::ExitEditor;
    if (ConfirmationTitleText) ConfirmationTitleText->SetText(FText::FromString(TEXT("退出运行时编辑器？")));
    if (ConfirmationBodyText)
    {
        ConfirmationBodyText->SetText(FText::FromString(
            FString::Printf(TEXT("当前有 %d 个实例包含未保存修改。"),
                SceneManager ? SceneManager->GetRuntimeEditPendingCount() : 0)));
    }
    if (ConfirmationPrimaryLabel) ConfirmationPrimaryLabel->SetText(FText::FromString(TEXT("保存并退出")));
    if (ConfirmationSecondaryLabel) ConfirmationSecondaryLabel->SetText(FText::FromString(TEXT("放弃修改并退出")));
    if (ConfirmationContinueLabel) ConfirmationContinueLabel->SetText(FText::FromString(TEXT("继续编辑")));
    if (ConfirmationSecondaryButton) ConfirmationSecondaryButton->SetVisibility(ESlateVisibility::Visible);
    ConfirmationOverlay->SetVisibility(ESlateVisibility::Visible);
    SetKeyboardFocus();
}

void UOntoTwinRuntimeEditorPanel::ShowCancelAllConfirmation()
{
    if (!ConfirmationOverlay) return;

    ConfirmationMode = EOntoTwinRuntimePanelConfirmation::CancelAll;
    if (ConfirmationTitleText) ConfirmationTitleText->SetText(FText::FromString(TEXT("取消全部修改？")));
    if (ConfirmationBodyText)
    {
        ConfirmationBodyText->SetText(FText::FromString(
            FString::Printf(TEXT("将恢复本次编辑会话中 %d 个实例的全部修改，此操作不能通过重做恢复。"),
                SceneManager ? SceneManager->GetRuntimeEditPendingCount() : 0)));
    }
    if (ConfirmationPrimaryLabel) ConfirmationPrimaryLabel->SetText(FText::FromString(TEXT("确认取消全部修改")));
    if (ConfirmationContinueLabel) ConfirmationContinueLabel->SetText(FText::FromString(TEXT("继续编辑")));
    if (ConfirmationSecondaryButton) ConfirmationSecondaryButton->SetVisibility(ESlateVisibility::Collapsed);
    ConfirmationOverlay->SetVisibility(ESlateVisibility::Visible);
    SetKeyboardFocus();
}

bool UOntoTwinRuntimeEditorPanel::IsConfirmationOpen() const
{
    return ConfirmationMode != EOntoTwinRuntimePanelConfirmation::None &&
        ConfirmationOverlay && ConfirmationOverlay->GetVisibility() != ESlateVisibility::Collapsed;
}

bool UOntoTwinRuntimeEditorPanel::IsPointerOverPanel() const
{
    if (IsConfirmationOpen())
    {
        return true;
    }
    if (!PanelBorder || !PanelBorder->IsVisible() || !FSlateApplication::IsInitialized())
    {
        return false;
    }

    return PanelBorder->GetCachedGeometry().IsUnderLocation(FSlateApplication::Get().GetCursorPos());
}

void UOntoTwinRuntimeEditorPanel::HideConfirmation()
{
    ConfirmationMode = EOntoTwinRuntimePanelConfirmation::None;
    if (ConfirmationOverlay)
    {
        ConfirmationOverlay->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void UOntoTwinRuntimeEditorPanel::RefreshPendingList()
{
    if (!SceneManager || !PendingList || !PendingToggleLabel) return;

    TArray<FString> PendingLines;
    SceneManager->GetRuntimeEditPendingLines(PendingLines);
    bool bContainsConflict = false;
    for (const FString& Line : PendingLines)
    {
        bContainsConflict |= Line.Contains(TEXT("冲突"));
    }
    if (bContainsConflict)
    {
        bPendingListExpanded = true;
    }

    PendingToggleLabel->SetText(FText::FromString(FString::Printf(
        TEXT("%s 待保存修改（%d）"),
        bPendingListExpanded ? TEXT("收起") : TEXT("展开"),
        PendingLines.Num())));
    PendingList->ClearChildren();
    for (const FString& Line : PendingLines)
    {
        const FName LineName = MakeUniqueObjectName(WidgetTree, UTextBlock::StaticClass(), TEXT("PendingLine"));
        UTextBlock* LineText = CreateText(LineName, Line, 11,
            Line.Contains(TEXT("冲突")) ? ErrorColor : SecondaryText);
        LineText->SetAutoWrapText(true);
        LineText->SetWrapTextAt(380.0f);
        UVerticalBoxSlot* LineSlot = PendingList->AddChildToVerticalBox(LineText);
        LineSlot->SetPadding(FMargin(0.0f, 2.0f));
    }
    PendingList->SetVisibility(
        bPendingListExpanded && PendingLines.Num() > 0
            ? ESlateVisibility::SelfHitTestInvisible
            : ESlateVisibility::Collapsed);
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

    if (PanelBounds && GEngine && GEngine->GameViewport)
    {
        FVector2D ViewportSize = FVector2D::ZeroVector;
        GEngine->GameViewport->GetViewportSize(ViewportSize);
        if (ViewportSize.Y > 0.0f)
        {
            PanelBounds->SetMaxDesiredHeight(FMath::Max(420.0f, ViewportSize.Y * 0.70f));
        }
    }

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
    if (YawLabelText)
    {
        YawLabelText->SetText(FText::FromString(
            SceneManager->IsRuntimeSelectionMultiple() ? TEXT("偏航增量") : TEXT("偏航")));
    }

    const EOntoTwinRuntimeAccessState AccessState = SceneManager->GetRuntimeEditorAccessState();
    FLinearColor AccessColor = MutedText;
    FString AccessText = TEXT("无法验证");
    FString ActionText;
    bool bShowAccessAction = false;
    bool bEnableAccessAction = false;

    switch (AccessState)
    {
    case EOntoTwinRuntimeAccessState::Checking:
        AccessText = TEXT("正在检查");
        ActionText = TEXT("检查中...");
        bShowAccessAction = true;
        break;
    case EOntoTwinRuntimeAccessState::Ready:
        AccessColor = ReadyColor;
        AccessText = TEXT("已就绪");
        break;
    case EOntoTwinRuntimeAccessState::Unbound:
        AccessColor = WarningColor;
        AccessText = TEXT("尚未绑定");
        ActionText = TEXT("绑定当前数据集");
        bShowAccessAction = true;
        bEnableAccessAction = SceneManager->CanBindRuntimeProject();
        break;
    case EOntoTwinRuntimeAccessState::Mismatch:
        AccessColor = ErrorColor;
        AccessText = TEXT("已绑定其他 UE 工程");
        break;
    case EOntoTwinRuntimeAccessState::Error:
    default:
        AccessColor = ErrorColor;
        AccessText = TEXT("无法验证");
        ActionText = TEXT("重试");
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
        SaveButtonLabel->SetText(FText::FromString(
            SceneManager->IsRuntimeEditSaving() ? TEXT("正在保存...") : TEXT("保存全部修改")));
    }
    if (SaveButton) SaveButton->SetIsEnabled(SceneManager->CanSaveRuntimeEdit());
    if (CancelButton) CancelButton->SetIsEnabled(SceneManager->CanCancelRuntimeEdit());
    if (CloseButton) CloseButton->SetIsEnabled(!SceneManager->IsRuntimeEditSaving());
    if (UndoButton) UndoButton->SetIsEnabled(SceneManager->CanUndoRuntimeEdit());
    if (RedoButton) RedoButton->SetIsEnabled(SceneManager->CanRedoRuntimeEdit());
    if (RemoveButton) RemoveButton->SetIsEnabled(SceneManager->CanRemoveRuntimeSelection());

    if (WallSnapCheckBox && WallSnapCheckBox->IsChecked() != SceneManager->IsRuntimeWallSnapEnabled())
    {
        WallSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeWallSnapEnabled());
    }
    if (GridSnapCheckBox && GridSnapCheckBox->IsChecked() != SceneManager->IsRuntimeGridSnapEnabled())
    {
        GridSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeGridSnapEnabled());
    }

    RefreshPendingList();
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
    if (SceneManager && SceneManager->CanCancelRuntimeEdit())
    {
        ShowCancelAllConfirmation();
    }
}

void UOntoTwinRuntimeEditorPanel::HandleUndoClicked()
{
    if (SceneManager) SceneManager->UndoRuntimeEdit();
}

void UOntoTwinRuntimeEditorPanel::HandleRedoClicked()
{
    if (SceneManager) SceneManager->RedoRuntimeEdit();
}

void UOntoTwinRuntimeEditorPanel::HandleRemoveClicked()
{
    if (SceneManager) SceneManager->RemoveRuntimeSelectionFromScene();
}

void UOntoTwinRuntimeEditorPanel::HandlePendingToggleClicked()
{
    bPendingListExpanded = !bPendingListExpanded;
    RefreshPendingList();
}

void UOntoTwinRuntimeEditorPanel::HandleConfirmationPrimaryClicked()
{
    if (!SceneManager)
    {
        HideConfirmation();
        return;
    }

    const EOntoTwinRuntimePanelConfirmation Action = ConfirmationMode;
    HideConfirmation();
    if (Action == EOntoTwinRuntimePanelConfirmation::ExitEditor)
    {
        SceneManager->SaveAndExitRuntimeEdit();
    }
    else if (Action == EOntoTwinRuntimePanelConfirmation::CancelAll)
    {
        SceneManager->CancelRuntimeEdit();
    }
}

void UOntoTwinRuntimeEditorPanel::HandleConfirmationSecondaryClicked()
{
    const EOntoTwinRuntimePanelConfirmation Action = ConfirmationMode;
    HideConfirmation();
    if (SceneManager && Action == EOntoTwinRuntimePanelConfirmation::ExitEditor)
    {
        SceneManager->DiscardAndExitRuntimeEdit();
    }
}

void UOntoTwinRuntimeEditorPanel::HandleConfirmationContinueClicked()
{
    HideConfirmation();
}

void UOntoTwinRuntimeEditorPanel::HandleWallSnapChanged(bool bIsChecked)
{
    if (SceneManager) SceneManager->SetRuntimeWallSnapEnabled(bIsChecked);
}

void UOntoTwinRuntimeEditorPanel::HandleGridSnapChanged(bool bIsChecked)
{
    if (SceneManager) SceneManager->SetRuntimeGridSnapEnabled(bIsChecked);
}
