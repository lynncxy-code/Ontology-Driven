#include "WebInteraction/OntoTwinWebInteractionComponent.h"

#include "TwinInstance.h"
#include "TwinSceneManager.h"
#include "WebInteraction/OntoTwinWebBridge.h"

#include "Blueprint/UserWidget.h"
#include "Dom/JsonValue.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMisc.h"
#include "HttpModule.h"
#include "InputCoreTypes.h"
#include "Interfaces/IHttpResponse.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
TSharedPtr<FJsonObject> ObjectField(const TSharedPtr<FJsonObject>& Parent, const TCHAR* Field)
{
    if (!Parent.IsValid()) return nullptr;
    const TSharedPtr<FJsonObject>* Value = nullptr;
    return Parent->TryGetObjectField(Field, Value) && Value ? *Value : nullptr;
}

FString StringField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field)
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Field, Value) ? Value : FString();
}

bool BoolField(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, bool Default = true)
{
    bool Value = Default;
    return Object.IsValid() && Object->TryGetBoolField(Field, Value) ? Value : Default;
}

FString JsonScalar(const TSharedPtr<FJsonValue>& Value)
{
    if (!Value.IsValid()) return FString();
    if (Value->Type == EJson::String) return Value->AsString();
    if (Value->Type == EJson::Number) return FString::SanitizeFloat(Value->AsNumber());
    if (Value->Type == EJson::Boolean) return Value->AsBool() ? TEXT("true") : TEXT("false");
    return FString();
}

TSharedPtr<FJsonObject> NewContext(const FString& ProjectId)
{
    TSharedPtr<FJsonObject> Context = MakeShared<FJsonObject>();
    Context->SetStringField(TEXT("project_id"), ProjectId);
    return Context;
}

bool ScopeMatches(const TSharedPtr<FJsonObject>& Scope, const TSharedPtr<FJsonObject>& Candidate)
{
    static const TCHAR* Keys[] = {
        TEXT("zone_id"), TEXT("object_type_rid"), TEXT("instance_id"), TEXT("business_view_id")
    };
    for (const TCHAR* Key : Keys)
    {
        const FString Left = StringField(Scope, Key);
        const FString Right = StringField(Candidate, Key);
        if (Left != Right) return false;
    }
    return true;
}

FString ScopeTypeForContext(const TSharedPtr<FJsonObject>& Context)
{
    if (!StringField(Context, TEXT("business_view_id")).IsEmpty()) return TEXT("business_view");
    if (!StringField(Context, TEXT("instance_id")).IsEmpty()) return TEXT("instance");
    if (!StringField(Context, TEXT("zone_id")).IsEmpty()) return TEXT("zone");
    return TEXT("project");
}
}

UOntoTwinWebInteractionComponent::UOntoTwinWebInteractionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UOntoTwinWebInteractionComponent::BeginPlay()
{
    Super::BeginPlay();
    SceneManager = Cast<ATwinSceneManager>(GetOwner());
    PlayerController = UGameplayStatics::GetPlayerController(this, 0);
    bShuttingDown = false;
    FString PolicyOverride;
    if (FParse::Value(FCommandLine::Get(), TEXT("OntoTwinWebUrlPolicy="), PolicyOverride))
    {
        UrlPolicy = PolicyOverride.TrimStartAndEnd().ToLower();
    }
    else
    {
        UrlPolicy = FPlatformMisc::GetEnvironmentVariable(TEXT("WEB_URL_POLICY")).TrimStartAndEnd().ToLower();
    }
    if (UrlPolicy != TEXT("allowlist") && UrlPolicy != TEXT("open"))
    {
#if UE_BUILD_SHIPPING
        UrlPolicy = TEXT("allowlist");
#else
        UrlPolicy = TEXT("open");
#endif
    }
    if (!SceneManager || !bEnableWebInteraction)
    {
        SetComponentTickEnabled(false);
        return;
    }
    PollRuntimeProjection();
}

void UOntoTwinWebInteractionComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bShuttingDown = true;
    RestoreSceneVisibility();
    RestoreInput();
    if (HostWidget)
    {
        HostWidget->RemoveFromParent();
        HostWidget = nullptr;
    }
    BridgeObject = nullptr;
    Super::EndPlay(EndPlayReason);
}

void UOntoTwinWebInteractionComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!SceneManager || bShuttingDown) return;
    if (!PlayerController) PlayerController = UGameplayStatics::GetPlayerController(this, 0);
    PollAccumulator += DeltaTime;
    if (PollAccumulator >= RuntimePollInterval)
    {
        PollAccumulator = 0.0f;
        PollRuntimeProjection();
    }
    VisibilityAccumulator += DeltaTime;
    if (VisibilityAccumulator >= 0.2f)
    {
        VisibilityAccumulator = 0.0f;
        TickVisibilityScope();
    }
    if (HostWidget && HostWidget->GetVisibility() == ESlateVisibility::Visible
        && PlayerController && PlayerController->WasInputKeyJustPressed(EKeys::Escape))
    {
        Back();
    }
}

void UOntoTwinWebInteractionComponent::AddProjectHeaders(
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe>& Request) const
{
    if (!SceneManager) return;
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), SceneManager->UEProjectId);
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Name"), SceneManager->UEProjectName);
#if WITH_EDITOR
    Request->SetHeader(TEXT("X-OntoTwin-UE-Context"), TEXT("editor"));
#else
    Request->SetHeader(TEXT("X-OntoTwin-UE-Context"), TEXT("packaged"));
#endif
}

void UOntoTwinWebInteractionComponent::PollRuntimeProjection()
{
    if (bRuntimeRequestInFlight || bShuttingDown || !SceneManager) return;
    bRuntimeRequestInFlight = true;
    FString BaseUrl = SceneManager->BackendBaseUrl;
    BaseUrl.RemoveFromEnd(TEXT("/"));
    FString Url = BaseUrl + TEXT("/api/v2/web-interactions/runtime");
    if (AppliedRevision >= 0)
    {
        Url += FString::Printf(TEXT("?known_revision=%d"), AppliedRevision);
    }
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(Url);
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddProjectHeaders(Request);
    const TWeakObjectPtr<UOntoTwinWebInteractionComponent> WeakThis(this);
    Request->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr, FHttpResponsePtr Response, bool bSuccess)
        {
            UOntoTwinWebInteractionComponent* Self = WeakThis.Get();
            if (!Self || Self->bShuttingDown) return;
            Self->bRuntimeRequestInFlight = false;
            if (!bSuccess || !Response.IsValid() || Response->GetResponseCode() < 200 || Response->GetResponseCode() >= 300)
            {
                if (Self->HostWidget && Self->HostWidget->GetVisibility() == ESlateVisibility::Visible)
                {
                    Self->HostWidget->SetHostStatus(TEXT("Web 配置服务不可用，保留当前页面"), true);
                }
                return;
            }
            TSharedPtr<FJsonObject> Payload;
            const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
            if (FJsonSerializer::Deserialize(Reader, Payload) && Payload.IsValid())
            {
                Self->HandleRuntimeProjection(Payload);
            }
        });
    if (!Request->ProcessRequest()) bRuntimeRequestInFlight = false;
}

void UOntoTwinWebInteractionComponent::HandleRuntimeProjection(const TSharedPtr<FJsonObject>& Payload)
{
    if (StringField(Payload, TEXT("status")) == TEXT("unchanged")) return;
    double RevisionNumber = 0.0;
    if (!Payload->TryGetNumberField(TEXT("revision"), RevisionNumber)) return;
    RebuildRuntimeIndexes(Payload);
    AppliedRevision = static_cast<int32>(RevisionNumber);
    if (bHasCurrentFrame)
    {
        const bool bStillResolved = ResolveAndOpen(
            CurrentFrame.Trigger, CurrentFrame.Context, nullptr, false);
        if (!bStillResolved && HostWidget)
        {
            HostWidget->SetHostStatus(TEXT("当前页面已被新配置禁用"), true);
        }
    }
}

void UOntoTwinWebInteractionComponent::RebuildRuntimeIndexes(const TSharedPtr<FJsonObject>& Payload)
{
    ActiveProjectId = StringField(Payload, TEXT("project_id"));
    PublishedConfig = ObjectField(Payload, TEXT("config"));
    PagesById.Reset();
    InstancesById.Reset();
    BusinessViewMembers.Reset();
    ZoneParents.Reset();
    AllowedHosts.Reset();
    if (!PublishedConfig.IsValid()) PublishedConfig = MakeShared<FJsonObject>();

    const TArray<TSharedPtr<FJsonValue>>* Pages = nullptr;
    if (PublishedConfig->TryGetArrayField(TEXT("pages"), Pages) && Pages)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Pages)
        {
            const TSharedPtr<FJsonObject> Page = Value.IsValid() ? Value->AsObject() : nullptr;
            const FString PageId = StringField(Page, TEXT("page_id"));
            if (!PageId.IsEmpty()) PagesById.Add(PageId, Page);
        }
    }
    const TArray<TSharedPtr<FJsonValue>>* InstanceIndex = nullptr;
    if (Payload->TryGetArrayField(TEXT("instance_index"), InstanceIndex) && InstanceIndex)
    {
        for (const TSharedPtr<FJsonValue>& Value : *InstanceIndex)
        {
            const TSharedPtr<FJsonObject> Instance = Value.IsValid() ? Value->AsObject() : nullptr;
            const FString InstanceId = StringField(Instance, TEXT("instance_id"));
            if (!InstanceId.IsEmpty()) InstancesById.Add(InstanceId, Instance);
        }
    }
    const TArray<TSharedPtr<FJsonValue>>* Zones = nullptr;
    if (Payload->TryGetArrayField(TEXT("zones"), Zones) && Zones)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Zones)
        {
            const TSharedPtr<FJsonObject> Zone = Value.IsValid() ? Value->AsObject() : nullptr;
            const FString ZoneId = StringField(Zone, TEXT("zone_id"));
            if (!ZoneId.IsEmpty()) ZoneParents.Add(ZoneId, StringField(Zone, TEXT("parent_zone_id")));
        }
    }
    const TSharedPtr<FJsonObject> Memberships = ObjectField(Payload, TEXT("business_view_memberships"));
    if (Memberships.IsValid())
    {
        for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Memberships->Values)
        {
            TSet<FString> Members;
            const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
            if (Pair.Value.IsValid() && Pair.Value->TryGetArray(Values) && Values)
            {
                for (const TSharedPtr<FJsonValue>& Value : *Values)
                {
                    FString InstanceId;
                    if (Value.IsValid() && Value->TryGetString(InstanceId)) Members.Add(InstanceId);
                }
            }
            BusinessViewMembers.Add(Pair.Key, MoveTemp(Members));
        }
    }
    const TSharedPtr<FJsonObject> Policy = ObjectField(PublishedConfig, TEXT("web_policy"));
    const TArray<TSharedPtr<FJsonValue>>* Hosts = nullptr;
    if (Policy.IsValid() && Policy->TryGetArrayField(TEXT("allowed_hosts"), Hosts) && Hosts)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Hosts)
        {
            FString Host;
            if (Value.IsValid() && Value->TryGetString(Host)) AllowedHosts.Add(Host.TrimStartAndEnd().ToLower());
        }
    }
}

bool UOntoTwinWebInteractionComponent::OpenProjectHome()
{
    if (!SceneManager) return false;
    return ResolveAndOpen(TEXT("project_home_activated"), NewContext(ActiveProjectId));
}

bool UOntoTwinWebInteractionComponent::OpenZone(const FString& ZoneId)
{
    if (!SceneManager || !IsZoneKnown(ZoneId)) return false;
    TSharedPtr<FJsonObject> Context = NewContext(ActiveProjectId);
    Context->SetStringField(TEXT("zone_id"), ZoneId);
    return ResolveAndOpen(TEXT("zone_activated"), Context);
}

bool UOntoTwinWebInteractionComponent::OpenBusinessView(
    const FString& BusinessViewId,
    const FString& ZoneId)
{
    if (!SceneManager || !IsBusinessViewKnown(BusinessViewId)
        || (!ZoneId.IsEmpty() && !IsZoneKnown(ZoneId))) return false;
    TSharedPtr<FJsonObject> Context = NewContext(ActiveProjectId);
    Context->SetStringField(TEXT("business_view_id"), BusinessViewId);
    if (!ZoneId.IsEmpty()) Context->SetStringField(TEXT("zone_id"), ZoneId);
    return ResolveAndOpen(TEXT("business_view_activated"), Context);
}

bool UOntoTwinWebInteractionComponent::OpenInstanceDetail(const FString& InstanceId)
{
    if (!SceneManager || !IsInstanceKnown(InstanceId)) return false;
    TSharedPtr<FJsonObject> Context = NewContext(ActiveProjectId);
    Context->SetStringField(TEXT("instance_id"), InstanceId);
    const TSharedPtr<FJsonObject>* Instance = InstancesById.Find(InstanceId);
    if (Instance && Instance->IsValid())
    {
        const FString ZoneId = StringField(*Instance, TEXT("zone_id"));
        const FString TypeRid = StringField(*Instance, TEXT("object_type_rid"));
        if (!ZoneId.IsEmpty()) Context->SetStringField(TEXT("zone_id"), ZoneId);
        if (!TypeRid.IsEmpty()) Context->SetStringField(TEXT("object_type_rid"), TypeRid);
    }
    const bool bOpened = ResolveAndOpen(TEXT("open_detail"), Context);
    if (bOpened) SelectAndFocusInstance(InstanceId);
    return bOpened;
}

TSharedPtr<FJsonObject> UOntoTwinWebInteractionComponent::ResolveBinding(
    const FString& Trigger,
    const TSharedPtr<FJsonObject>& Context,
    TArray<FString>& OutChain,
    bool& bBlocked) const
{
    bBlocked = false;
    if (!PublishedConfig.IsValid()) return nullptr;
    TArray<TSharedPtr<FJsonObject>> Candidates;
    TArray<FString> Labels;
    auto AddCandidate = [&Candidates, &Labels](const FString& Label, const TMap<FString, FString>& Values)
    {
        TSharedPtr<FJsonObject> Scope = MakeShared<FJsonObject>();
        bool bMissing = false;
        for (const TPair<FString, FString>& Pair : Values)
        {
            if (Pair.Value.IsEmpty()) bMissing = true;
            else Scope->SetStringField(Pair.Key, Pair.Value);
        }
        if (!bMissing)
        {
            Labels.Add(Label);
            Candidates.Add(Scope);
        }
    };
    if (Trigger == TEXT("open_detail"))
    {
        AddCandidate(TEXT("Instance"), {{TEXT("instance_id"), StringField(Context, TEXT("instance_id"))}});
        AddCandidate(TEXT("Zone+Type"), {{TEXT("zone_id"), StringField(Context, TEXT("zone_id"))}, {TEXT("object_type_rid"), StringField(Context, TEXT("object_type_rid"))}});
        AddCandidate(TEXT("Type"), {{TEXT("object_type_rid"), StringField(Context, TEXT("object_type_rid"))}});
        AddCandidate(TEXT("Zone"), {{TEXT("zone_id"), StringField(Context, TEXT("zone_id"))}});
    }
    else if (Trigger == TEXT("business_view_activated"))
    {
        AddCandidate(TEXT("BusinessView"), {{TEXT("business_view_id"), StringField(Context, TEXT("business_view_id"))}});
    }
    else if (Trigger == TEXT("zone_activated"))
    {
        AddCandidate(TEXT("Zone"), {{TEXT("zone_id"), StringField(Context, TEXT("zone_id"))}});
    }
    AddCandidate(TEXT("Project"), {});

    const TArray<TSharedPtr<FJsonValue>>* Bindings = nullptr;
    if (!PublishedConfig->TryGetArrayField(TEXT("bindings"), Bindings) || !Bindings) return nullptr;
    for (int32 CandidateIndex = 0; CandidateIndex < Candidates.Num(); ++CandidateIndex)
    {
        bool bFoundDisabled = false;
        for (const TSharedPtr<FJsonValue>& Value : *Bindings)
        {
            const TSharedPtr<FJsonObject> Binding = Value.IsValid() ? Value->AsObject() : nullptr;
            if (!Binding.IsValid() || StringField(Binding, TEXT("trigger")) != Trigger) continue;
            const TSharedPtr<FJsonObject> Scope = ObjectField(Binding, TEXT("scope"));
            if (!ScopeMatches(Scope.IsValid() ? Scope : MakeShared<FJsonObject>(), Candidates[CandidateIndex])) continue;
            if (!BoolField(Binding, TEXT("enabled"), true))
            {
                bFoundDisabled = true;
                continue;
            }
            const FString Effect = StringField(Binding, TEXT("effect"));
            OutChain.Add(Labels[CandidateIndex] + TEXT(":") + StringField(Binding, TEXT("binding_id")));
            bBlocked = Effect == TEXT("block");
            return Binding;
        }
        OutChain.Add(Labels[CandidateIndex] + (bFoundDisabled ? TEXT(":disabled") : TEXT(":none")));
    }
    return nullptr;
}

bool UOntoTwinWebInteractionComponent::ResolveAndOpen(
    const FString& Trigger,
    const TSharedPtr<FJsonObject>& Context,
    const TSharedPtr<FJsonObject>& ExtraParams,
    bool bPushHistory)
{
    TArray<FString> Chain;
    bool bBlocked = false;
    const TSharedPtr<FJsonObject> Binding = ResolveBinding(Trigger, Context, Chain, bBlocked);
    if (!Binding.IsValid() || bBlocked)
    {
        SendRuntimeEvent(TEXT("resolve"), bBlocked ? TEXT("blocked") : TEXT("no_binding"));
        return false;
    }
    const FString PageId = StringField(Binding, TEXT("page_id"));
    const TSharedPtr<FJsonObject>* Page = PagesById.Find(PageId);
    if (!Page || !Page->IsValid() || !BoolField(*Page, TEXT("enabled"), true)) return false;
    return OpenPage(*Page, Trigger, Context, ExtraParams, bPushHistory);
}

bool UOntoTwinWebInteractionComponent::OpenPage(
    const TSharedPtr<FJsonObject>& Page,
    const FString& Trigger,
    const TSharedPtr<FJsonObject>& Context,
    const TSharedPtr<FJsonObject>& ExtraParams,
    bool bPushHistory)
{
    FString Error;
    const FString FinalUrl = BuildFinalUrl(Page, Context, ExtraParams, Error);
    if (FinalUrl.IsEmpty())
    {
        SendRuntimeEvent(TEXT("navigation"), TEXT("rejected"), Error);
        return false;
    }
    FOntoTwinWebNavigationFrame Next;
    Next.PageId = StringField(Page, TEXT("page_id"));
    Next.FinalUrl = FinalUrl;
    Next.Trigger = Trigger;
    Next.Context = Context;
    ApplySceneScope(Page, Context, Next);
    if (bPushHistory && bHasCurrentFrame
        && (CurrentFrame.PageId != Next.PageId || CurrentFrame.FinalUrl != Next.FinalUrl))
    {
        NavigationHistory.Add(CurrentFrame);
    }
    const bool bSamePage = bHasCurrentFrame
        && CurrentFrame.PageId == Next.PageId && CurrentFrame.FinalUrl == Next.FinalUrl;
    CurrentFrame = Next;
    bHasCurrentFrame = true;
    ApplyVisibilityFrame(CurrentFrame);
    EnsureHostWidget();
    if (!HostWidget) return false;
    HostWidget->SetVisibility(ESlateVisibility::Visible);
    CaptureWebInput();
    if (!bSamePage) HostWidget->Navigate(FinalUrl);
    else HostWidget->SetHostStatus(TEXT("页面已重新显示"));
    SendRuntimeEvent(TEXT("navigation"), bSamePage ? TEXT("shown_without_reload") : TEXT("loading"));
    return true;
}

FString UOntoTwinWebInteractionComponent::BuildFinalUrl(
    const TSharedPtr<FJsonObject>& Page,
    const TSharedPtr<FJsonObject>& Context,
    const TSharedPtr<FJsonObject>& ExtraParams,
    FString& OutError) const
{
    FString Url = StringField(Page, TEXT("base_url")).TrimStartAndEnd();
    if (!ValidateNavigation(Url, OutError)) return FString();
    FString Fragment;
    int32 HashIndex = INDEX_NONE;
    if (Url.FindChar(TEXT('#'), HashIndex))
    {
        Fragment = Url.Mid(HashIndex);
        Url.LeftInline(HashIndex);
    }
    TArray<FString> Params;
    const TSharedPtr<FJsonObject> Mapping = ObjectField(Page, TEXT("param_mapping"));
    if (Mapping.IsValid())
    {
        for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Mapping->Values)
        {
            const FString Destination = JsonScalar(Pair.Value);
            const FString SourceValue = StringField(Context, *Pair.Key);
            if (!Destination.IsEmpty() && !SourceValue.IsEmpty())
            {
                Params.Add(FGenericPlatformHttp::UrlEncode(Destination) + TEXT("=")
                    + FGenericPlatformHttp::UrlEncode(SourceValue));
            }
        }
    }
    TSet<FString> Declared;
    const TArray<TSharedPtr<FJsonValue>>* DeclaredValues = nullptr;
    if (Page->TryGetArrayField(TEXT("declared_extra_params"), DeclaredValues) && DeclaredValues)
    {
        for (const TSharedPtr<FJsonValue>& Value : *DeclaredValues)
        {
            FString Key;
            if (Value.IsValid() && Value->TryGetString(Key)) Declared.Add(Key);
        }
    }
    if (ExtraParams.IsValid())
    {
        for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : ExtraParams->Values)
        {
            if (!Declared.Contains(Pair.Key))
            {
                OutError = TEXT("extra_param_not_declared");
                return FString();
            }
            const FString Value = JsonScalar(Pair.Value);
            if (!Value.IsEmpty()) Params.Add(FGenericPlatformHttp::UrlEncode(Pair.Key) + TEXT("=") + FGenericPlatformHttp::UrlEncode(Value));
        }
    }
    if (Params.Num() > 0)
    {
        Url += Url.Contains(TEXT("?")) ? TEXT("&") : TEXT("?");
        Url += FString::Join(Params, TEXT("&"));
    }
    return Url + Fragment;
}

bool UOntoTwinWebInteractionComponent::ValidateNavigation(const FString& Url, FString& OutReason) const
{
    FString Clean = Url.TrimStartAndEnd();
    const FString Lower = Clean.ToLower();
    if (Lower == TEXT("about:blank")) return true;
    if (!Lower.StartsWith(TEXT("http://")) && !Lower.StartsWith(TEXT("https://")))
    {
        OutReason = TEXT("dangerous_url_scheme");
        return false;
    }
    const int32 SchemeEnd = Clean.Find(TEXT("://"));
    const int32 AuthorityStart = SchemeEnd + 3;
    int32 AuthorityEnd = Clean.Find(TEXT("/"), ESearchCase::CaseSensitive, ESearchDir::FromStart, AuthorityStart);
    if (AuthorityEnd == INDEX_NONE) AuthorityEnd = Clean.Len();
    FString Authority = Clean.Mid(AuthorityStart, AuthorityEnd - AuthorityStart);
    const int32 QueryInAuthority = Authority.Find(TEXT("?"));
    if (QueryInAuthority != INDEX_NONE) Authority.LeftInline(QueryInAuthority);
    if (Authority.Contains(TEXT("@")))
    {
        OutReason = TEXT("embedded_credentials");
        return false;
    }
    FString Host = Authority;
    int32 ColonIndex = INDEX_NONE;
    if (Host.FindChar(TEXT(':'), ColonIndex)) Host.LeftInline(ColonIndex);
    Host = Host.ToLower();
    if (Host.IsEmpty())
    {
        OutReason = TEXT("url_host_required");
        return false;
    }
    if (UrlPolicy == TEXT("allowlist") && !AllowedHosts.Contains(Host) && !AllowedHosts.Contains(Authority.ToLower()))
    {
        OutReason = TEXT("host_not_allowed");
        return false;
    }
    return true;
}

bool UOntoTwinWebInteractionComponent::HandlePopupNavigation(const FString& Url)
{
    FString Reason;
    if (ValidateNavigation(Url, Reason) && HostWidget)
    {
        HostWidget->Navigate(Url);
        SendRuntimeEvent(TEXT("popup"), TEXT("reused_single_browser"));
    }
    else if (HostWidget)
    {
        HostWidget->SetHostStatus(TEXT("已阻止不安全的新窗口地址"), true);
        SendRuntimeEvent(TEXT("popup"), TEXT("rejected"), Reason);
    }
    return true; // Always suppress creation of a second browser window.
}

void UOntoTwinWebInteractionComponent::EnsureHostWidget()
{
    if (HostWidget || !PlayerController) return;
    BridgeObject = NewObject<UOntoTwinWebBridge>(this);
    BridgeObject->Initialize(this);
    HostWidget = CreateWidget<UOntoTwinWebHostWidget>(
        PlayerController, UOntoTwinWebHostWidget::StaticClass());
    if (!HostWidget) return;
    HostWidget->Configure(this, BridgeObject, GlassQuality);
    HostWidget->AddToViewport(1500);
}

void UOntoTwinWebInteractionComponent::CaptureWebInput()
{
    if (!PlayerController || !HostWidget || bInputCaptured) return;
    bPreviousMouseCursor = PlayerController->bShowMouseCursor;
    PlayerController->bShowMouseCursor = true;
    FInputModeGameAndUI Mode;
    Mode.SetWidgetToFocus(HostWidget->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    Mode.SetHideCursorDuringCapture(false);
    PlayerController->SetInputMode(Mode);
    bInputCaptured = true;
}

void UOntoTwinWebInteractionComponent::RestoreInput()
{
    if (!PlayerController || !bInputCaptured) return;
    PlayerController->bShowMouseCursor = bPreviousMouseCursor;
    if (!bPreviousMouseCursor) PlayerController->SetInputMode(FInputModeGameOnly());
    bInputCaptured = false;
}

void UOntoTwinWebInteractionComponent::Back()
{
    if (NavigationHistory.Num() == 0)
    {
        RestoreSceneVisibility();
        bHasCurrentFrame = false;
        if (HostWidget) HostWidget->SetVisibility(ESlateVisibility::Collapsed);
        RestoreInput();
        return;
    }
    const FOntoTwinWebNavigationFrame Previous = NavigationHistory.Pop();
    CurrentFrame = Previous;
    bHasCurrentFrame = true;
    ApplyVisibilityFrame(CurrentFrame);
    EnsureHostWidget();
    if (HostWidget)
    {
        HostWidget->SetVisibility(ESlateVisibility::Visible);
        if (HostWidget->GetCurrentUrl() != CurrentFrame.FinalUrl) HostWidget->Navigate(CurrentFrame.FinalUrl);
    }
    CaptureWebInput();
}

void UOntoTwinWebInteractionComponent::Close()
{
    if (HostWidget) HostWidget->SetVisibility(ESlateVisibility::Collapsed);
    RestoreInput();
    SendToPage(TEXT("visibility_changed"), FString(), nullptr);
}

void UOntoTwinWebInteractionComponent::Retry()
{
    if (HostWidget && bHasCurrentFrame) HostWidget->Navigate(CurrentFrame.FinalUrl);
}

void UOntoTwinWebInteractionComponent::ApplySceneScope(
    const TSharedPtr<FJsonObject>& Page,
    const TSharedPtr<FJsonObject>& Context,
    FOntoTwinWebNavigationFrame& Frame)
{
    const FString ScopeType = ScopeTypeForContext(Context);
    const TSharedPtr<FJsonObject> Effects = ObjectField(Page, TEXT("scope_effects"));
    if (StringField(Effects, *ScopeType) != TEXT("web_and_scene")) return;
    Frame.bSceneScopeActive = true;
    TSet<FString> Target;
    if (ScopeType == TEXT("instance"))
    {
        const FString InstanceId = StringField(Context, TEXT("instance_id"));
        if (IsInstanceKnown(InstanceId)) Target.Add(InstanceId);
    }
    else if (ScopeType == TEXT("zone"))
    {
        const TSet<FString> Zones = DescendantZones(StringField(Context, TEXT("zone_id")));
        for (const TPair<FString, TSharedPtr<FJsonObject>>& Pair : InstancesById)
        {
            if (Zones.Contains(StringField(Pair.Value, TEXT("zone_id")))) Target.Add(Pair.Key);
        }
    }
    else if (ScopeType == TEXT("business_view"))
    {
        const FString BusinessViewId = StringField(Context, TEXT("business_view_id"));
        if (const TSet<FString>* Members = BusinessViewMembers.Find(BusinessViewId)) Target = *Members;
        const FString ZoneId = StringField(Context, TEXT("zone_id"));
        if (!ZoneId.IsEmpty())
        {
            const TSet<FString> Zones = DescendantZones(ZoneId);
            for (auto It = Target.CreateIterator(); It; ++It)
            {
                const TSharedPtr<FJsonObject>* Instance = InstancesById.Find(*It);
                if (!Instance || !Zones.Contains(StringField(*Instance, TEXT("zone_id")))) It.RemoveCurrent();
            }
        }
    }
    for (const TPair<FString, TSharedPtr<FJsonObject>>& Pair : InstancesById)
    {
        if (StringField(Pair.Value, TEXT("zone_id")).IsEmpty()) Target.Add(Pair.Key);
    }
    Frame.VisibleInstanceIds = MoveTemp(Target);
}

void UOntoTwinWebInteractionComponent::ApplyVisibilityFrame(const FOntoTwinWebNavigationFrame& Frame)
{
    if (!Frame.bSceneScopeActive) return;
    TArray<ATwinInstance*> Instances;
    SceneManager->GetManagedInstances(Instances);
    for (ATwinInstance* Instance : Instances)
    {
        if (!Instance || !IsValid(Instance)) continue;
        const TWeakObjectPtr<ATwinInstance> Key(Instance);
        if (!OriginalHiddenStates.Contains(Key)) OriginalHiddenStates.Add(Key, Instance->IsHidden());
        const bool bOriginallyHidden = OriginalHiddenStates.FindRef(Key);
        Instance->SetActorHiddenInGame(
            !Frame.VisibleInstanceIds.Contains(Instance->GetInstanceId()) || bOriginallyHidden);
    }
}

void UOntoTwinWebInteractionComponent::TickVisibilityScope()
{
    if (bHasCurrentFrame && CurrentFrame.bSceneScopeActive) ApplyVisibilityFrame(CurrentFrame);
}

void UOntoTwinWebInteractionComponent::RestoreSceneVisibility()
{
    for (const TPair<TWeakObjectPtr<ATwinInstance>, bool>& Pair : OriginalHiddenStates)
    {
        if (Pair.Key.IsValid()) Pair.Key->SetActorHiddenInGame(Pair.Value);
    }
    OriginalHiddenStates.Reset();
    NavigationHistory.Reset();
}

TSet<FString> UOntoTwinWebInteractionComponent::DescendantZones(const FString& ZoneId) const
{
    TSet<FString> Result;
    if (ZoneId.IsEmpty()) return Result;
    Result.Add(ZoneId);
    bool bChanged = true;
    while (bChanged)
    {
        bChanged = false;
        for (const TPair<FString, FString>& Pair : ZoneParents)
        {
            if (Result.Contains(Pair.Value) && !Result.Contains(Pair.Key))
            {
                Result.Add(Pair.Key);
                bChanged = true;
            }
        }
    }
    return Result;
}

bool UOntoTwinWebInteractionComponent::IsInstanceKnown(const FString& InstanceId) const
{
    return !InstanceId.IsEmpty() && InstancesById.Contains(InstanceId);
}

bool UOntoTwinWebInteractionComponent::IsZoneKnown(const FString& ZoneId) const
{
    return !ZoneId.IsEmpty() && ZoneParents.Contains(ZoneId);
}

bool UOntoTwinWebInteractionComponent::IsBusinessViewKnown(const FString& BusinessViewId) const
{
    return !BusinessViewId.IsEmpty() && BusinessViewMembers.Contains(BusinessViewId);
}

void UOntoTwinWebInteractionComponent::SelectAndFocusInstance(const FString& InstanceId)
{
    if (!SceneManager) return;
    if (ATwinInstance* Instance = SceneManager->FindManagedInstance(InstanceId))
    {
        SceneManager->SelectOverlayFromSceneInteraction(Instance);
        SceneManager->FocusManagedInstance(Instance);
    }
}

void UOntoTwinWebInteractionComponent::HandleBridgeMessage(const FString& MessageJson)
{
    TSharedPtr<FJsonObject> Message;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(MessageJson);
    if (!FJsonSerializer::Deserialize(Reader, Message) || !Message.IsValid()) return;
    const FString Type = StringField(Message, TEXT("type"));
    const FString RequestId = StringField(Message, TEXT("request_id"));
    const TSharedPtr<FJsonObject> Payload = ObjectField(Message, TEXT("payload"));
    auto Reply = [this, &RequestId](const FString& Result, const FString& Error = FString())
    {
        TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
        Body->SetStringField(TEXT("result"), Result);
        if (!Error.IsEmpty()) Body->SetStringField(TEXT("error_code"), Error);
        SendToPage(TEXT("action_result"), RequestId, Body);
    };
    if (Type == TEXT("ready"))
    {
        const FString Version = StringField(Payload, TEXT("version"));
        bBridgeReady = Version == TEXT("1.0");
        if (HostWidget) HostWidget->SetBridgeReady(bBridgeReady);
        TSharedPtr<FJsonObject> Ready = MakeShared<FJsonObject>();
        Ready->SetStringField(TEXT("version"), TEXT("1.0"));
        Ready->SetBoolField(TEXT("compatible"), bBridgeReady);
        SendToPage(TEXT("host_ready"), RequestId, Ready);
        SendContextToPage();
        return;
    }
    if (!bBridgeReady)
    {
        Reply(TEXT("rejected"), TEXT("bridge_not_ready"));
        return;
    }
    if (Type == TEXT("interactive_regions"))
    {
        TArray<FSlateRect> Regions;
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!Payload.IsValid() || !Payload->TryGetArrayField(TEXT("regions"), Values) || !Values || Values->Num() > 256)
        {
            if (HostWidget) HostWidget->SetInteractiveRegions({});
            Reply(TEXT("rejected"), TEXT("invalid_interactive_regions"));
            return;
        }
        for (const TSharedPtr<FJsonValue>& Value : *Values)
        {
            const TSharedPtr<FJsonObject> Region = Value.IsValid() ? Value->AsObject() : nullptr;
            double X = 0, Y = 0, Width = 0, Height = 0;
            if (!Region.IsValid() || !Region->TryGetNumberField(TEXT("x"), X)
                || !Region->TryGetNumberField(TEXT("y"), Y)
                || !Region->TryGetNumberField(TEXT("width"), Width)
                || !Region->TryGetNumberField(TEXT("height"), Height)
                || !FMath::IsFinite(X) || !FMath::IsFinite(Y)
                || !FMath::IsFinite(Width) || !FMath::IsFinite(Height)
                || X < 0 || Y < 0 || Width <= 0 || Height <= 0
                || X + Width > 16384 || Y + Height > 16384)
            {
                if (HostWidget) HostWidget->SetInteractiveRegions({});
                Reply(TEXT("rejected"), TEXT("invalid_interactive_regions"));
                return;
            }
            Regions.Emplace(X, Y, X + Width, Y + Height);
        }
        if (HostWidget) HostWidget->SetInteractiveRegions(Regions);
        Reply(TEXT("ok"));
        return;
    }
    if (Type == TEXT("select_instance"))
    {
        const FString InstanceId = StringField(Payload, TEXT("instance_id"));
        if (!IsInstanceKnown(InstanceId)) Reply(TEXT("rejected"), TEXT("instance_not_found"));
        else { SelectAndFocusInstance(InstanceId); Reply(TEXT("ok")); }
        return;
    }
    if (Type == TEXT("clear_selection"))
    {
        if (SceneManager) SceneManager->ClearOverlayFromSceneInteraction();
        Reply(TEXT("ok"));
        return;
    }
    if (Type == TEXT("request_open_scope"))
    {
        const FString ScopeType = StringField(Payload, TEXT("scope_type"));
        bool bOpened = false;
        if (ScopeType == TEXT("zone")) bOpened = OpenZone(StringField(Payload, TEXT("zone_id")));
        else if (ScopeType == TEXT("business_view")) bOpened = OpenBusinessView(
            StringField(Payload, TEXT("business_view_id")), StringField(Payload, TEXT("zone_id")));
        else if (ScopeType == TEXT("instance")) bOpened = OpenInstanceDetail(StringField(Payload, TEXT("instance_id")));
        Reply(bOpened ? TEXT("ok") : TEXT("rejected"), bOpened ? FString() : TEXT("scope_not_found"));
        return;
    }
    if (Type == TEXT("request_open_page"))
    {
        const FString PageId = StringField(Payload, TEXT("page_id"));
        const TSharedPtr<FJsonObject>* Page = PagesById.Find(PageId);
        const TSharedPtr<FJsonObject> Extra = ObjectField(Payload, TEXT("extra_params"));
        if (!Page || !Page->IsValid() || !BoolField(*Page, TEXT("enabled"), true) || !bHasCurrentFrame)
        {
            Reply(TEXT("rejected"), TEXT("page_not_found"));
        }
        else
        {
            const bool bOpened = OpenPage(*Page, CurrentFrame.Trigger, CurrentFrame.Context, Extra, true);
            Reply(bOpened ? TEXT("ok") : TEXT("rejected"), bOpened ? FString() : TEXT("navigation_rejected"));
        }
        return;
    }
    Reply(TEXT("rejected"), TEXT("unsupported_action"));
}

void UOntoTwinWebInteractionComponent::HandlePageLoadStarted()
{
    bBridgeReady = false;
}

void UOntoTwinWebInteractionComponent::HandlePageLoaded()
{
    SendRuntimeEvent(TEXT("page_load"), TEXT("completed"));
}

void UOntoTwinWebInteractionComponent::HandlePageLoadError()
{
    SendRuntimeEvent(TEXT("page_load"), TEXT("failed"), TEXT("browser_load_error"));
}

void UOntoTwinWebInteractionComponent::HandleUrlChanged(const FString& Url)
{
    FString Reason;
    if (!ValidateNavigation(Url, Reason) && HostWidget)
    {
        HostWidget->SetHostStatus(TEXT("已阻止不安全的页面跳转"), true);
        SendRuntimeEvent(TEXT("navigation"), TEXT("rejected"), Reason);
    }
}

void UOntoTwinWebInteractionComponent::SendContextToPage()
{
    if (!bHasCurrentFrame || !CurrentFrame.Context.IsValid()) return;
    TSharedPtr<FJsonObject> Context = MakeShared<FJsonObject>();
    static const TCHAR* Keys[] = {
        TEXT("project_id"), TEXT("business_view_id"), TEXT("zone_id"),
        TEXT("object_type_rid"), TEXT("instance_id")
    };
    for (const TCHAR* Key : Keys)
    {
        const FString Value = StringField(CurrentFrame.Context, Key);
        if (!Value.IsEmpty()) Context->SetStringField(Key, Value);
    }
    Context->SetStringField(TEXT("trigger"), CurrentFrame.Trigger);
    SendToPage(TEXT("context"), FString(), Context);
}

void UOntoTwinWebInteractionComponent::SendToPage(
    const FString& Type,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload)
{
    if (!HostWidget) return;
    TSharedPtr<FJsonObject> Message = MakeShared<FJsonObject>();
    Message->SetStringField(TEXT("type"), Type);
    if (!RequestId.IsEmpty()) Message->SetStringField(TEXT("request_id"), RequestId);
    Message->SetObjectField(TEXT("payload"), Payload.IsValid() ? Payload : MakeShared<FJsonObject>());
    HostWidget->ExecuteJavascript(FString::Printf(
        TEXT("window.OntoTwinBridge&&window.OntoTwinBridge.receive(%s);"), *JsonString(Message)));
}

void UOntoTwinWebInteractionComponent::SendRuntimeEvent(
    const FString& EventType,
    const FString& Result,
    const FString& ErrorCode) const
{
    if (!SceneManager || bShuttingDown) return;
    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("event_type"), EventType);
    Body->SetStringField(TEXT("result"), Result);
    if (!ErrorCode.IsEmpty()) Body->SetStringField(TEXT("error_code"), ErrorCode);
    if (bHasCurrentFrame) Body->SetStringField(TEXT("page_id"), CurrentFrame.PageId);
    const FString JsonBody = JsonString(Body);
    FString BaseUrl = SceneManager->BackendBaseUrl;
    BaseUrl.RemoveFromEnd(TEXT("/"));
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl + TEXT("/api/v2/web-interactions/runtime-events"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddProjectHeaders(Request);
    Request->SetContentAsString(JsonBody);
    Request->ProcessRequest();
}

FString UOntoTwinWebInteractionComponent::JsonString(const TSharedPtr<FJsonObject>& Object)
{
    FString Result;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Result);
    FJsonSerializer::Serialize(Object.ToSharedRef(), Writer);
    return Result;
}
