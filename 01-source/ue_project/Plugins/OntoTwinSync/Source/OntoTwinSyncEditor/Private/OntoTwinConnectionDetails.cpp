#include "OntoTwinConnectionDetails.h"

#include "TwinSceneManager.h"
#include "OntoTwinConnectionContext.h"
#include "IDetailCustomization.h"
#include "DetailLayoutBuilder.h"
#include "DetailCategoryBuilder.h"
#include "DetailWidgetRow.h"
#include "PropertyEditorModule.h"
#include "Modules/ModuleManager.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
struct FConnectionStatus
{
    FText Message = FText::FromString(TEXT("尚未检查绑定"));
    TSharedPtr<IHttpRequest, ESPMode::ThreadSafe> Request;
    bool bPending = false;
    ~FConnectionStatus()
    {
        if (Request.IsValid())
        {
            Request->OnProcessRequestComplete().Unbind();
            Request->CancelRequest();
        }
    }
};

void CheckBinding(TWeakObjectPtr<ATwinSceneManager> WeakManager, TSharedRef<FConnectionStatus> State)
{
    ATwinSceneManager* Manager = WeakManager.Get();
    if (!Manager || State->bPending) return;
    FString BaseUrl = Manager->BackendBaseUrl;
    BaseUrl.RemoveFromEnd(TEXT("/"));
    auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl + TEXT("/api/v2/ue/binding_status"));
    Request->SetVerb(TEXT("GET"));
    Request->SetTimeout(10.0f);
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), Manager->UEProjectId);
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Name"), Manager->UEProjectName);
    if (!Manager->SceneId.IsEmpty())
        Request->SetHeader(TEXT("X-OntoTwin-UE-Scene-Id"), Manager->SceneId);
    OntoTwinConnectionContext::Apply(Request, Manager->GetWorld());
    State->Request = Request;
    State->bPending = true;
    State->Message = FText::FromString(TEXT("正在检查绑定…"));
    TWeakPtr<FConnectionStatus> WeakState(State);
    Request->OnProcessRequestComplete().BindLambda(
        [WeakState](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            auto Status = WeakState.Pin();
            if (!Status) return;
            Status->bPending = false;
            TSharedPtr<FJsonObject> Json;
            if (Response.IsValid())
                FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()), Json);
            FString Mode;
            bool bCanWrite = false;
            if (Json.IsValid())
            {
                Json->TryGetStringField(TEXT("mode"), Mode);
                Json->TryGetBoolField(TEXT("can_write"), bCanWrite);
            }
            if (bOk && Response.IsValid() && Response->GetResponseCode() == 200 && Json.IsValid())
            {
                const bool bBound = Mode == TEXT("matched") || Mode == TEXT("scene-matched") || Mode == TEXT("explicit");
                Status->Message = FText::FromString(bBound
                    ? (bCanWrite ? TEXT("已绑定 · 可读写") : TEXT("已绑定 · 当前只读"))
                    : TEXT("当前关卡未绑定，请在平台中配置项目与关卡绑定"));
            }
            else
            {
                FString Message;
                if (Json.IsValid()) Json->TryGetStringField(TEXT("message"), Message);
                Status->Message = FText::FromString(Message.IsEmpty()
                    ? TEXT("连接失败，请检查后台地址和服务状态") : Message);
            }
        });
    if (!Request->ProcessRequest())
    {
        State->bPending = false;
        State->Message = FText::FromString(TEXT("请求未能发出，请检查连接地址"));
    }
}

class FConnectionDetails : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance() { return MakeShared<FConnectionDetails>(); }
    virtual void CustomizeDetails(IDetailLayoutBuilder& Builder) override
    {
        TArray<TWeakObjectPtr<UObject>> Objects;
        Builder.GetObjectsBeingCustomized(Objects);
        if (Objects.Num() != 1) return;
        ATwinSceneManager* Manager = Cast<ATwinSceneManager>(Objects[0].Get());
        if (!Manager || !OntoTwinConnectionContext::IsExplicit()) return;
        const TWeakObjectPtr<ATwinSceneManager> WeakManager(Manager);
        // This hides the legacy CallInEditor bind button as well as its old fields.
        Builder.HideCategory(TEXT("连接"));
        auto& Category = Builder.EditCategory(TEXT("平台连接"), FText::FromString(TEXT("平台连接")), ECategoryPriority::Important);
        const auto AddValue = [&Category](const TCHAR* Label, TFunction<FString()> Value)
        {
            Category.AddCustomRow(FText::FromString(Label))
            .NameContent()[SNew(STextBlock).Text(FText::FromString(Label)).Font(IDetailLayoutBuilder::GetDetailFont())]
            .ValueContent().MinDesiredWidth(360)
            [SNew(SEditableTextBox).IsReadOnly(true).Font(IDetailLayoutBuilder::GetDetailFont())
                .Text_Lambda([Value]() { return FText::FromString(Value()); })];
        };
        AddValue(TEXT("当前后台地址"), [WeakManager]() { return WeakManager.IsValid() ? WeakManager->BackendBaseUrl : FString(); });
        AddValue(TEXT("平台项目 ID"), []() { return OntoTwinConnectionContext::Setting(TEXT("ProjectId")); });
        AddValue(TEXT("UE 工程 ID"), [WeakManager]() { return WeakManager.IsValid() ? WeakManager->UEProjectId : FString(); });
        AddValue(TEXT("UE 工程名称"), [WeakManager]() { return WeakManager.IsValid() ? WeakManager->UEProjectName : FString(); });
        AddValue(TEXT("实际关卡路径"), [WeakManager]()
        {
            const UWorld* World = WeakManager.IsValid() ? WeakManager->GetWorld() : nullptr;
            if (!World) return FString();
            FString Path = World->GetOutermost()->GetName();
            if (!World->StreamingLevelsPrefix.IsEmpty()) Path.ReplaceInline(*World->StreamingLevelsPrefix, TEXT(""));
            return Path;
        });
        Category.AddCustomRow(FText::FromString(TEXT("绑定状态"))).WholeRowContent()
        [SNew(STextBlock).Text_Lambda([State = State]() { return State->Message; }).AutoWrapText(true)];
        Category.AddCustomRow(FText::FromString(TEXT("检查绑定"))).WholeRowContent()
        [SNew(SButton).Text(FText::FromString(TEXT("检查项目与关卡绑定")))
            .IsEnabled_Lambda([State = State]() { return !State->bPending; })
            .OnClicked_Lambda([WeakManager, State = State]() { CheckBinding(WeakManager, State); return FReply::Handled(); })];
        Category.AddCustomRow(FText::FromString(TEXT("配置来源"))).WholeRowContent()
        [SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(
            TEXT("连接身份来自 Config/DefaultGame.ini 的 OntoTwin.Connection 配置。修改后重新打开工程；关卡身份自动读取。此处仅检查已有绑定。")))];
        // Preserve all existing polling, WebSocket and asset catalog settings.
        for (TFieldIterator<FProperty> It(ATwinSceneManager::StaticClass()); It; ++It)
        {
            const FString Name = It->GetName();
            if (It->GetMetaData(TEXT("Category")).StartsWith(TEXT("连接"))
                && Name != TEXT("BackendBaseUrl") && Name != TEXT("UEProjectId")
                && Name != TEXT("UEProjectName") && Name != TEXT("SceneId"))
                Category.AddProperty(It->GetFName(), ATwinSceneManager::StaticClass());
        }
        Category.AddCustomRow(FText::FromString(TEXT("资产目录"))).WholeRowContent()
        [SNew(SButton).Text(FText::FromString(TEXT("同步 UE 资产目录")))
            .OnClicked_Lambda([WeakManager]()
            {
                if (WeakManager.IsValid()) WeakManager->SyncUEAssetCatalog();
                return FReply::Handled();
            })];
        CheckBinding(WeakManager, State);
    }
private:
    TSharedRef<FConnectionStatus> State = MakeShared<FConnectionStatus>();
};
}

void RegisterOntoTwinConnectionDetails()
{
    auto& Module = FModuleManager::LoadModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor"));
    Module.RegisterCustomClassLayout(TEXT("TwinSceneManager"), FOnGetDetailCustomizationInstance::CreateStatic(&FConnectionDetails::MakeInstance));
    Module.NotifyCustomizationModuleChanged();
}

void UnregisterOntoTwinConnectionDetails()
{
    if (auto* Module = FModuleManager::GetModulePtr<FPropertyEditorModule>(TEXT("PropertyEditor")))
    {
        Module->UnregisterCustomClassLayout(TEXT("TwinSceneManager"));
        Module->NotifyCustomizationModuleChanged();
    }
}

#if WITH_DEV_AUTOMATION_TESTS
#include "Editor.h"
#include "Engine/Selection.h"
#include "IDetailsView.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SWindow.h"
#include "HAL/IConsoleManager.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

// Explicit visual acceptance hook: render the real details customization without editing the actor.
static FAutoConsoleCommand GConnectionPanelCapture(TEXT("OntoTwin.ValidateConnectionPanel"),
    TEXT("Capture the selected scene manager's connection panel to Saved/OntoTwinConnectionPanel.png."),
    FConsoleCommandDelegate::CreateLambda([]()
    {
        if (!GEditor || !FSlateApplication::IsInitialized()) return;
        auto* Manager = Cast<ATwinSceneManager>(GEditor->GetSelectedActors()->GetTop(ATwinSceneManager::StaticClass()));
        if (!Manager) return;
        FDetailsViewArgs Args;
        Args.bUpdatesFromSelection = false;
        Args.bLockable = false;
        Args.NameAreaSettings = FDetailsViewArgs::HideNameArea;
        auto Details = FModuleManager::LoadModuleChecked<FPropertyEditorModule>(TEXT("PropertyEditor")).CreateDetailView(Args);
        Details->SetObject(Manager);
        auto Window = SNew(SWindow).Title(FText::FromString(TEXT("OntoTwin 连接面板验证")))
            .ClientSize(FVector2D(1050, 740))[Details];
        FSlateApplication::Get().AddWindow(Window);
        Window->RegisterActiveTimer(4.0f, FWidgetActiveTimerDelegate::CreateLambda(
            [Window](double, float)
            {
                TArray<FColor> Pixels;
                FIntVector Size;
                const bool bCaptured = FSlateApplication::Get().TakeScreenshot(Window, Pixels, Size);
                if (bCaptured)
                {
                    TArray<uint8> Png;
                    FImageUtils::CompressImageArray(Size.X, Size.Y, Pixels, Png);
                    FFileHelper::SaveArrayToFile(Png, *(FPaths::ProjectSavedDir() / TEXT("OntoTwinConnectionPanel.png")));
                }
                UE_LOG(LogTemp, Display, TEXT("ONTOTWIN_CONNECTION_PANEL_CAPTURE success=%d"), bCaptured);
                Window->RequestDestroyWindow();
                return EActiveTimerReturnType::Stop;
            }));
    }));
#endif
