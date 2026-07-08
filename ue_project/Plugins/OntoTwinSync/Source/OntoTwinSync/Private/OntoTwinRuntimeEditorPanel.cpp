#include "OntoTwinRuntimeEditorPanel.h"

#include "TwinSceneManager.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/CheckBox.h"
#include "Components/HorizontalBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Styling/SlateColor.h"
#include "Widgets/SWidget.h"

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

    if (BindButton)
    {
        BindButton->OnClicked.RemoveAll(this);
        BindButton->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::HandleBindClicked);
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

void UOntoTwinRuntimeEditorPanel::BuildDefaultLayout()
{
    if (!WidgetTree) return;

    UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RuntimeEditorRoot"));
    WidgetTree->RootWidget = Root;

    UBorder* Border = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PanelBorder"));
    Border->SetPadding(FMargin(12.f));
    Border->SetBrushColor(FLinearColor(0.02f, 0.02f, 0.02f, 0.82f));

    UCanvasPanelSlot* BorderSlot = Root->AddChildToCanvas(Border);
    if (BorderSlot)
    {
        BorderSlot->SetAnchors(FAnchors(0.f, 0.f));
        BorderSlot->SetPosition(FVector2D(24.f, 80.f));
        BorderSlot->SetSize(FVector2D(420.f, 330.f));
    }

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("PanelStack"));
    Border->SetContent(Stack);

    ModeText = AddTextLine(Stack, TEXT("ModeText"), TEXT("Runtime Editor"));
    BindingText = AddTextLine(Stack, TEXT("BindingText"), TEXT("Binding: checking"));
    SelectionText = AddTextLine(Stack, TEXT("SelectionText"), TEXT("Selection: none"));
    TransformText = AddTextLine(Stack, TEXT("TransformText"), TEXT("Transform: -"));
    StatusText = AddTextLine(Stack, TEXT("StatusText"), TEXT("F8/F10 toggle | Ctrl+S save | Esc cancel"));

    UHorizontalBox* Buttons = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Buttons"));
    Stack->AddChildToVerticalBox(Buttons);
    BindButton = AddButton(Buttons, TEXT("BindButton"), TEXT("Bind"));
    SaveButton = AddButton(Buttons, TEXT("SaveButton"), TEXT("Save"));
    CancelButton = AddButton(Buttons, TEXT("CancelButton"), TEXT("Cancel"));

    UHorizontalBox* Toggles = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Toggles"));
    Stack->AddChildToVerticalBox(Toggles);

    WallSnapCheckBox = WidgetTree->ConstructWidget<UCheckBox>(UCheckBox::StaticClass(), TEXT("WallSnapCheckBox"));
    Toggles->AddChildToHorizontalBox(WallSnapCheckBox);
    AddTextLine(Stack, TEXT("WallSnapLabel"), TEXT("Wall snap / grid snap toggles above"));

    GridSnapCheckBox = WidgetTree->ConstructWidget<UCheckBox>(UCheckBox::StaticClass(), TEXT("GridSnapCheckBox"));
    Toggles->AddChildToHorizontalBox(GridSnapCheckBox);
}

UTextBlock* UOntoTwinRuntimeEditorPanel::AddTextLine(UVerticalBox* Parent, const FName Name, const FString& InitialText) const
{
    if (!WidgetTree || !Parent) return nullptr;

    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
    Text->SetText(FText::FromString(InitialText));
    Text->SetColorAndOpacity(FSlateColor(FLinearColor::White));
    Parent->AddChildToVerticalBox(Text);
    return Text;
}

UButton* UOntoTwinRuntimeEditorPanel::AddButton(UHorizontalBox* Parent, const FName Name, const FString& Label) const
{
    if (!WidgetTree || !Parent) return nullptr;

    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(*(Label + TEXT("Label"))));
    Text->SetText(FText::FromString(Label));
    Button->SetContent(Text);
    Parent->AddChildToHorizontalBox(Button);
    return Button;
}

void UOntoTwinRuntimeEditorPanel::RefreshFromManager()
{
    if (!SceneManager) return;

    if (ModeText) ModeText->SetText(FText::FromString(SceneManager->GetRuntimeEditorModeText()));
    if (BindingText) BindingText->SetText(FText::FromString(SceneManager->GetRuntimeEditorBindingText()));
    if (SelectionText) SelectionText->SetText(FText::FromString(SceneManager->GetRuntimeEditorSelectionText()));
    if (TransformText) TransformText->SetText(FText::FromString(SceneManager->GetRuntimeEditorTransformText()));
    if (StatusText) StatusText->SetText(FText::FromString(SceneManager->GetRuntimeEditorStatusText()));
    if (BindButton) BindButton->SetIsEnabled(SceneManager->CanBindRuntimeProject());
    if (SaveButton) SaveButton->SetIsEnabled(SceneManager->CanSaveRuntimeEdit());
    if (CancelButton) CancelButton->SetIsEnabled(SceneManager->HasRuntimeEditSelection());
    if (WallSnapCheckBox && WallSnapCheckBox->IsChecked() != SceneManager->IsRuntimeWallSnapEnabled())
    {
        WallSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeWallSnapEnabled());
    }
    if (GridSnapCheckBox && GridSnapCheckBox->IsChecked() != SceneManager->IsRuntimeGridSnapEnabled())
    {
        GridSnapCheckBox->SetIsChecked(SceneManager->IsRuntimeGridSnapEnabled());
    }
}

void UOntoTwinRuntimeEditorPanel::HandleBindClicked()
{
    if (SceneManager) SceneManager->BindCurrentRuntimeProject();
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
