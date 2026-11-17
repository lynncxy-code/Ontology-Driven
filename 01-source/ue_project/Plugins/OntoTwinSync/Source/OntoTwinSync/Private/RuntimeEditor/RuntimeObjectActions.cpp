#include "TwinSceneManager.h"
#include "TwinInstance.h"
#include "OntoTwinRuntimeEditorPanel.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "HttpModule.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonSerializer.h"

void ATwinSceneManager::PostObjectAction(const FString& Action,TSharedRef<FJsonObject> Body,
                                        TFunction<void(const TSharedPtr<FJsonObject>&)> Success)
{
    if (!CanPlaceRuntimeModel() || bRuntimeEditSaving) return;
    const FString Project = BoundProjectId;
    Body->SetStringField(TEXT("expected_project_id"),Project);
    FString Json;
    FJsonSerializer::Serialize(Body,TJsonWriterFactory<>::Create(&Json));
    auto Request=FHttpModule::Get().CreateRequest();
    Request->SetURL(BackendBaseUrl / TEXT("api/v2/runtime-editor/objects/") + Action);
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"),TEXT("application/json"));
    AddUEProjectHeaders(Request);
    Request->SetContentAsString(Json);
    Request->SetTimeout(15);
    bRuntimeEditSaving=true;
    Request->OnProcessRequestComplete().BindWeakLambda(this,[this,Project,Success=MoveTemp(Success)](FHttpRequestPtr,FHttpResponsePtr Response,bool bOk){
        bRuntimeEditSaving=false;
        if (Project != BoundProjectId || !bRuntimeEditMode) return;
        TSharedPtr<FJsonObject> Root;
        if (Response) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()),Root);
        if (!bOk || !Response || !EHttpResponseCodes::IsOk(Response->GetResponseCode()) || !Root)
        {
            FString Message=TEXT("保存未成功，可重试");
            if (Root) Root->TryGetStringField(TEXT("message"),Message);
            if (RuntimeEditorPanel)
            {
                RuntimeEditorPanel->SetPlacementFeedback(Message);
                RuntimeEditorPanel->ShowToast(Message,EOntoTwinRuntimeToastType::Error);
            }
            return;
        }
        Success(Root);
        UpdateRuntimeEditorPanel();
    });
    if (!Request->ProcessRequest())
    {
        bRuntimeEditSaving=false;
        if (RuntimeEditorPanel) RuntimeEditorPanel->SetPlacementFeedback(TEXT("连接失败，请重试"));
    }
}
void ATwinSceneManager::RunObjectHistory(const FRuntimeEditCommand& Command,int32 Direction,bool bConfirmed)
{
    const bool bDelete = Direction == 0 || (Direction < 0 ? Command.bCreatedObjects : !Command.bCreatedObjects);
    auto Body=MakeShared<FJsonObject>();
    TArray<TSharedPtr<FJsonValue>> Ids;
    for (const FString& Id:Command.SavedObjectIds) Ids.Add(MakeShared<FJsonValueString>(Id));
    Body->SetArrayField(TEXT("ids"),Ids);
    if (bDelete && !bConfirmed)
    {
        PostObjectAction(TEXT("inspect"),Body,[this,Command,Direction](const TSharedPtr<FJsonObject>& Root){
            FString Message;
            bool bAttached=false;
            for (const auto& V:Root->GetArrayField(TEXT("objects")))
            {
                const auto Item=V->AsObject();
                Message+=Item->GetStringField(TEXT("name"))+TEXT("\n");
                for (const auto& Reason:Item->GetArrayField(TEXT("reasons")))
                { Message+=TEXT("  ")+Reason->AsString()+TEXT("\n"); bAttached=true; }
                if (!Item->GetBoolField(TEXT("scenery"))) Message+=TEXT("编号将回到实例清单的待投产状态。\n");
            }
            Message+=TEXT("删除后进入回收站，可在网页恢复。");
            if (Direction == 0 || bAttached)
                RuntimeEditorPanel->ConfirmObjectDeletion(Message,FSimpleDelegate::CreateWeakLambda(this,
                    [this,Command,Direction]{RunObjectHistory(Command,Direction,true);}));
            else RunObjectHistory(Command,Direction,true);
        });
        return;
    }
    Body->SetBoolField(TEXT("confirm_business"),bConfirmed);
    PostObjectAction(bDelete?TEXT("delete"):TEXT("restore"),Body,[this,Command,Direction,bDelete](const TSharedPtr<FJsonObject>& Root){
        if (bDelete) for (const FString& Id:Command.SavedObjectIds) DestroyTwinInstance(Id);
        else for (const auto& Snap:Root->GetArrayField(TEXT("snapshots"))) ProcessSnapshot(Snap->AsObject());
        if (Direction < 0) {RuntimeUndoStack.Pop(); RuntimeRedoStack.Add(Command);}
        else if (Direction > 0) {RuntimeRedoStack.Pop(); RuntimeUndoStack.Add(Command);}
        else {FRuntimeEditCommand Copy = Command; RecordRuntimeCommand(MoveTemp(Copy));}
        if (RuntimeEditorPanel) RuntimeEditorPanel->ShowToast(
            Command.Label+(bDelete?TEXT("已移入回收站"):TEXT("已恢复")),EOntoTwinRuntimeToastType::Success);
    });
}
void ATwinSceneManager::DeleteSelectedObjects()
{
    if (!CanPlaceRuntimeModel() || bRuntimeEditSaving) return;
    FRuntimeEditCommand Command;
    GetRuntimeSelectedInstanceIds(Command.SavedObjectIds);
    TArray<FString> Names;
    GetRuntimeSelectedInstanceDisplayNames(Names);
    Command.Label=FString::Join(Names,TEXT("、"));
    if (Command.SavedObjectIds.Num()) RunObjectHistory(Command,0);
}
void ATwinSceneManager::DismissObjectForm()
{
    if (bRuntimeEditSaving || bPlacementSending) return;
    CancelUnconfirmedModelPlacement();
    if (RuntimeEditorPanel) RuntimeEditorPanel->ClosePlacementDetails();
}
void ATwinSceneManager::EditSelectedIdentity()
{
    if (!CanPlaceRuntimeModel() || !RuntimeSelectedInstance || GetRuntimeEditSelectionCount()!=1) return;
    const FString Id=RuntimeSelectedInstance->GetInstanceId(), Project=BoundProjectId;
    auto Request=FHttpModule::Get().CreateRequest();
    Request->SetURL(BackendBaseUrl / TEXT("api/v2/runtime-editor/placement-options?expected_project_id=")
        +FGenericPlatformHttp::UrlEncode(Project)+TEXT("&selected_id=")+FGenericPlatformHttp::UrlEncode(Id));
    Request->SetVerb(TEXT("GET"));
    AddUEProjectHeaders(Request);
    Request->OnProcessRequestComplete().BindWeakLambda(this,[this,Project](FHttpRequestPtr,FHttpResponsePtr Response,bool bOk){
        if (Project!=BoundProjectId || !bRuntimeEditMode) return;
        TSharedPtr<FJsonObject> Root;
        if (bOk && Response && EHttpResponseCodes::IsOk(Response->GetResponseCode()))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()),Root);
        if (RuntimeEditorPanel) RuntimeEditorPanel->ShowPlacementDetails(TEXT(""),Root,Root?FString():TEXT("读取对象失败，请关闭后重试"));
    });
    Request->ProcessRequest();
}
void ATwinSceneManager::SaveEditedIdentity(const FString& SourceId,const FString& Id,const FString& Name,const FString& Rid)
{
    auto Body=MakeShared<FJsonObject>();
    Body->SetArrayField(TEXT("ids"),{MakeShared<FJsonValueString>(SourceId)});
    Body->SetStringField(TEXT("instance_id"),Id);
    Body->SetStringField(TEXT("display_name"),Name);
    Body->SetStringField(TEXT("object_type_rid"),Rid);
    PostObjectAction(TEXT("identity"),Body,[this,SourceId](const TSharedPtr<FJsonObject>& Root){
        const FString Destination=Root->GetStringField(TEXT("instance_id"));
        if (SourceId!=Destination)
        {
            for (auto* History : {&RuntimeUndoStack, &RuntimeRedoStack})
                for (auto& Command : *History)
                    for (FString& Id : Command.SavedObjectIds) if (Id == SourceId) Id = Destination;
            DestroyTwinInstance(SourceId);
        }
        for (const auto& Snap:Root->GetArrayField(TEXT("snapshots"))) ProcessSnapshot(Snap->AsObject());
        if (auto* Instance=InstanceRegistry.FindRef(Destination)) SelectRuntimeInstance(Instance,false);
        if (RuntimeEditorPanel) RuntimeEditorPanel->ClosePlacementDetails();
    });
}
void UOntoTwinRuntimeEditorPanel::DeleteSelectedObjects() {if(SceneManager) SceneManager->DeleteSelectedObjects();}
void UOntoTwinRuntimeEditorPanel::EditSelectedIdentity() {if(SceneManager) SceneManager->EditSelectedIdentity();}
void UOntoTwinRuntimeEditorPanel::ConfirmObjectDeletion(const FString& Message,FSimpleDelegate Accept)
{
    PendingDeleteAction=MoveTemp(Accept);
    ConfirmationMode=EOntoTwinRuntimePanelConfirmation::DeleteObjects;
    ConfirmationTitleText->SetText(FText::FromString(TEXT("删除对象？")));
    ConfirmationBodyText->SetText(FText::FromString(Message));
    ConfirmationPrimaryLabel->SetText(FText::FromString(TEXT("删除到回收站")));
    ConfirmationContinueLabel->SetText(FText::FromString(TEXT("取消")));
    ConfirmationSecondaryButton->SetVisibility(ESlateVisibility::Collapsed);
    ConfirmationOverlay->SetVisibility(ESlateVisibility::Visible);
    SetKeyboardFocus();
}
