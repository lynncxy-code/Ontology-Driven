#include "OntoTwinRuntimeEditorPanel.h"
#include "TwinSceneManager.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/NativeWidgetHost.h"
#include "Dom/JsonObject.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/STextComboBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

class SRuntimePlacementForm : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SRuntimePlacementForm) {}
        SLATE_ARGUMENT(ATwinSceneManager*, Manager)
        SLATE_ARGUMENT(TSharedPtr<FJsonObject>, Options)
        SLATE_ARGUMENT(FString, Message)
    SLATE_END_ARGS()

    void Feedback(const FString& Text) { Message = Text; bSaving = false; }
    void Construct(const FArguments& Args)
    {
        Manager = Args._Manager;
        Message = Args._Message;
        const auto Options = Args._Options;
        bReady = Options.IsValid();
        if (Options)
        {
            Options->TryGetStringField(TEXT("default_name"), DefaultName);
            for (const auto& Row : Options->GetArrayField(TEXT("types")))
            {
                const auto Object = Row->AsObject();
                auto Name = MakeShared<FString>(Object->GetStringField(TEXT("name")));
                Types.Add(Name);
                TypeKeys.Add(Name,Object->GetStringField(TEXT("rid")));
            }
            for (const auto& Row : Options->GetArrayField(TEXT("roster")))
            {
                const auto Object = Row->AsObject();
                FString Id = Object->GetStringField(TEXT("instance_id"));
                RosterOptions.Add(MakeShared<FString>(Id));
                Roster.Add(Id,Object);
            }
            for (const auto& V : Options->GetArrayField(TEXT("active_ids"))) Active.Add(V->AsString());
            for (const auto& V : Options->GetArrayField(TEXT("deleted_ids"))) Deleted.Add(V->AsString());
        }
        auto Form = SNew(SVerticalBox);
        auto Line = [&](TSharedRef<SWidget> Widget){ Form->AddSlot().AutoHeight().Padding(2,4)[Widget]; };
        auto Caption = [](const TCHAR* Text){return SNew(STextBlock).Text(FText::FromString(Text));};
        Line(Caption(TEXT("放置信息")));
        Line(Caption(TEXT("实例编号（留空保存为布景）")));
        Line(SAssignNew(IdBox,SEditableTextBox)
            .OnTextChanged_Lambda([this](const FText& T){OnId(T.ToString().TrimStartAndEnd());})
            .OnTextCommitted_Lambda([this](const FText&,ETextCommit::Type How){if (How == ETextCommit::OnEnter) Save();}));
        Line(SNew(STextComboBox).OptionsSource(&RosterOptions)
            .ContentPadding(2).ToolTipText(FText::FromString(TEXT("选择待投产编号")))
            .OnSelectionChanged_Lambda([this](TSharedPtr<FString> Id,ESelectInfo::Type){if (Id) IdBox->SetText(FText::FromString(*Id));}));
        Line(Caption(TEXT("名称")));
        Line(SAssignNew(NameBox,SEditableTextBox).Text(FText::FromString(DefaultName))
            .OnTextCommitted_Lambda([this](const FText&,ETextCommit::Type How){if (How == ETextCommit::OnEnter) Save();}));
        Line(SAssignNew(TypeBox,STextComboBox).OptionsSource(&Types)
            .Visibility_Lambda([this]{return BusinessId.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;})
            .ToolTipText(FText::FromString(TEXT("选择业务类型")))
            .OnSelectionChanged_Lambda([this](TSharedPtr<FString> Name,ESelectInfo::Type){Rid=TypeKeys.FindRef(Name);}));
        Line(SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return FText::FromString(Message);}));
        auto Actions = SNew(SHorizontalBox);
        Actions->AddSlot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("定位")))
            .Visibility_Lambda([this]{return Active.Contains(BusinessId)?EVisibility::Visible:EVisibility::Collapsed;})
            .OnClicked_Lambda([this]{if(Manager.IsValid() && !Manager->LocatePlacementConflict(BusinessId))
                Feedback(TEXT("该实例当前未加载，可在实例列表中重新加载")); return FReply::Handled();})];
        Actions->AddSlot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("取消")))
            .IsEnabled_Lambda([this]{return !bSaving;})
            .OnClicked_Lambda([this]{if(Manager.IsValid()) Manager->CancelUnconfirmedModelPlacement();return FReply::Handled();})];
        Actions->AddSlot().AutoWidth()[SNew(SButton).Text(FText::FromString(TEXT("确定")))
            .IsEnabled_Lambda([this]{return CanSave();}).OnClicked_Lambda([this]{Save();return FReply::Handled();})];
        Line(Actions);
        ChildSlot[SNew(SBorder).Padding(14).BorderBackgroundColor(FLinearColor(.06f,.06f,.06f,.99f))[
            SNew(SBox).WidthOverride(330)[Form]]];
        if (bReady) FSlateApplication::Get().SetKeyboardFocus(IdBox);
    }
private:
    bool CanSave() const
    {
        return Manager.IsValid() && Manager->CanPlaceRuntimeModel() && bReady && !bSaving &&
            !Active.Contains(BusinessId) && !Deleted.Contains(BusinessId) && (BusinessId.IsEmpty() || !Rid.IsEmpty());
    }
    void Save()
    {
        if (!CanSave()) return;
        FString Name = NameBox->GetText().ToString().TrimStartAndEnd();
        if (BusinessId.IsEmpty() && Name == DefaultName) Name.Reset();
        bSaving = true;
        Message = TEXT("正在保存…");
        Manager->SavePlacementDetails(BusinessId,Name,Rid);
    }
    void OnId(const FString& Id)
    {
        BusinessId=Id;
        Rid.Reset();
        TypeBox->ClearSelection();
        Message.Reset();
        if (Active.Contains(Id)) Message=TEXT("已投产，可定位已加载的实例");
        else if (Deleted.Contains(Id)) Message=TEXT("此编号位于回收站，请先在网页恢复或彻底删除");
        else if (!Id.IsEmpty() && Types.IsEmpty()) Message=TEXT("当前数据集还没有可用类型，请先在网页配置");
        else if (const auto* Entry=Roster.Find(Id))
        {
            FString Name, Type;
            (*Entry)->TryGetStringField(TEXT("name"),Name);
            (*Entry)->TryGetStringField(TEXT("type"),Type);
            NameBox->SetText(FText::FromString(Name));
            for (const auto& T:Types) if (Type==*T || Type==TypeKeys[T]) {TypeBox->SetSelectedItem(T);break;}
        }
        else if (Id.IsEmpty()) NameBox->SetText(FText::FromString(DefaultName));
    }
    TWeakObjectPtr<ATwinSceneManager> Manager;
    TArray<TSharedPtr<FString>> Types, RosterOptions;
    TMap<TSharedPtr<FString>,FString> TypeKeys;
    TMap<FString,TSharedPtr<FJsonObject>> Roster;
    TSet<FString> Active, Deleted;
    TSharedPtr<SEditableTextBox> IdBox,NameBox;
    TSharedPtr<STextComboBox> TypeBox;
    FString DefaultName,BusinessId,Rid,Message;
    bool bReady=false,bSaving=false;
};

void UOntoTwinRuntimeEditorPanel::ShowPlacementDetails(const FString&,const TSharedPtr<FJsonObject>& Options,const FString& Error)
{
    if (!PlacementFormHost)
    {
        auto* Root=Cast<UCanvasPanel>(WidgetTree->RootWidget);
        if (!Root) return;
        PlacementFormHost=WidgetTree->ConstructWidget<UNativeWidgetHost>();
        auto* FormSlot=Root->AddChildToCanvas(PlacementFormHost);
        FormSlot->SetAnchors(FAnchors(.5f,.5f));
        FormSlot->SetAlignment(FVector2D(.5f,.5f));
        FormSlot->SetAutoSize(true);
        FormSlot->SetZOrder(50);
    }
    PlacementFormHost->SetVisibility(ESlateVisibility::Visible);
    PlacementFormHost->SetContent(SAssignNew(PlacementForm,SRuntimePlacementForm).Manager(SceneManager).Options(Options).Message(Error));
}
void UOntoTwinRuntimeEditorPanel::ClosePlacementDetails()
{
    if (PlacementFormHost) PlacementFormHost->SetVisibility(ESlateVisibility::Collapsed);
    PlacementForm.Reset();
}
void UOntoTwinRuntimeEditorPanel::SetPlacementFeedback(const FString& Message)
{
    if (PlacementForm) PlacementForm->Feedback(Message);
}
