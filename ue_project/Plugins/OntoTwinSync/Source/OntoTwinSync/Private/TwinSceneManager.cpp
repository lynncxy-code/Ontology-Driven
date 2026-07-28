// ============================================================================
// TwinSceneManager.cpp  (v3 — 数据库驱动，废弃固化)
//
// 职责：
//   1. 运行时轮询后端快照，动态 spawn / 更新 / 销毁 ATwinInstance（DB 唯一真源）
//   2. 编辑器：PullPreviewFromDB() 从数据库临时 spawn 预览（RF_Transient，不写 .umap）
//   3. 编辑器：FR-6 历史 actor 迁移工具（导出 / 清除已迁移）
//
// 已废弃（FR-4）：SnapshotToLevel 固化、TakeOverExistingInstances 接管、
//   bEditorPlaced 保护——孪生实例不再持久化进关卡，一律由数据库驱动。
// ============================================================================

#include "TwinSceneManager.h"
#include "OntoTwinRuntimeEditorPanel.h"
#include "OntoTwinOverlayWidget.h"
#include "OntoTwinRuntimeGizmo.h"
#include "RuntimeEditor/TwinRuntimeEditorCameraPawn.h"
#include "TwinInstance.h"
#include "SceneInteraction/TwinInteractionManagerComponent.h"
#include "IWebSocket.h"
#include "WebSocketsModule.h"
#include "Modules/ModuleManager.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "HAL/PlatformTime.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Blueprint/UserWidget.h"
#include "Components/InputComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "MediaPlayer.h"
#include "MediaSoundComponent.h"
#include "MediaTexture.h"
// FR-6 迁移工具用
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Containers/StringConv.h"
#include "HAL/FileManager.h"
#include "Misc/SecureHash.h"
#include "Components/ActorComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "Serialization/JsonWriter.h"
#if WITH_EDITOR
#include "Editor.h"
#endif

namespace
{
FString CleanFolderSegment(FString Segment)
{
    Segment.TrimStartAndEndInline();
    Segment.ReplaceInline(TEXT("\\"), TEXT("_"));
    Segment.ReplaceInline(TEXT("/"), TEXT("_"));
    return Segment;
}

FName BuildTwinFolderPath(const TSharedPtr<FJsonObject>& Snapshot, const TCHAR* RootFolder)
{
    TArray<FString> Segments;
    const TArray<TSharedPtr<FJsonValue>>* Hierarchy = nullptr;
    if (Snapshot.IsValid() && Snapshot->TryGetArrayField(TEXT("hierarchyPath"), Hierarchy))
    {
        for (const TSharedPtr<FJsonValue>& Value : *Hierarchy)
        {
            FString Segment;
            if (Value.IsValid() && Value->TryGetString(Segment))
            {
                Segment = CleanFolderSegment(Segment);
                if (!Segment.IsEmpty())
                {
                    Segments.Add(Segment);
                }
            }
        }
    }

    if (Segments.Num() == 0 && Snapshot.IsValid())
    {
        FString TypeName;
        if (Snapshot->TryGetStringField(TEXT("objectTypeName"), TypeName))
        {
            TypeName = CleanFolderSegment(TypeName);
            if (!TypeName.IsEmpty())
            {
                Segments.Add(TypeName);
            }
        }
    }

    FString Path(RootFolder);
    for (const FString& Segment : Segments)
    {
        Path += TEXT("/");
        Path += Segment;
    }
    return FName(*Path);
}

bool IsInFolderOrChild(const FName ActorFolderName, const FString& RootFolder)
{
    const FString ActorFolder = ActorFolderName.ToString().Replace(TEXT("\\"), TEXT("/"));
    FString CleanRoot = RootFolder;
    CleanRoot.TrimStartAndEndInline();
    CleanRoot.ReplaceInline(TEXT("\\"), TEXT("/"));
    CleanRoot.RemoveFromEnd(TEXT("/"));

    return !CleanRoot.IsEmpty()
        && (ActorFolder == CleanRoot || ActorFolder.StartsWith(CleanRoot + TEXT("/")));
}

FString TruncateRuntimeLabel(const FString& Value, int32 MaxLength)
{
    if (Value.Len() <= MaxLength || MaxLength < 6)
    {
        return Value;
    }
    return Value.Left(MaxLength - 3) + TEXT("...");
}

FString CollisionEnabledToMigrationString(const ECollisionEnabled::Type CollisionEnabled)
{
    switch (CollisionEnabled)
    {
    case ECollisionEnabled::NoCollision:      return TEXT("NoCollision");
    case ECollisionEnabled::QueryOnly:        return TEXT("QueryOnly");
    case ECollisionEnabled::PhysicsOnly:      return TEXT("PhysicsOnly");
    case ECollisionEnabled::QueryAndPhysics:  return TEXT("QueryAndPhysics");
    case ECollisionEnabled::ProbeOnly:        return TEXT("ProbeOnly");
    case ECollisionEnabled::QueryAndProbe:    return TEXT("QueryAndProbe");
    default:                                  return TEXT("NoCollision");
    }
}
}

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinSceneManager::ATwinSceneManager()
{
    PrimaryActorTick.bCanEverTick = true;
    USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    OverlayMediaSound = CreateDefaultSubobject<UMediaSoundComponent>(TEXT("OverlayMediaSound"));
    OverlayMediaSound->SetupAttachment(SceneRoot);
    OverlayMediaSound->SetAutoActivate(false);
    InteractionManager = CreateDefaultSubobject<UTwinInteractionManagerComponent>(TEXT("SceneInteractionManager"));
    UEProjectName = FApp::GetProjectName();
    UEProjectId = FString::Printf(TEXT("ueproj_%s"), *UEProjectName);
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinSceneManager::BeginPlay()
{
    // Customer releases can override serialized level defaults without rebuilding the map.
    // Resolve the backend before Super::BeginPlay(), because that starts actor components and
    // SceneInteractionManager immediately performs its first runtime projection request.
    FString BackendBaseUrlOverride;
    const bool bHasBackendBaseUrlOverride = FParse::Value(
            FCommandLine::Get(),
            TEXT("OntoTwinBackendBaseUrl="),
            BackendBaseUrlOverride);
    if (bHasBackendBaseUrlOverride)
    {
        BackendBaseUrlOverride.TrimStartAndEndInline();
        BackendBaseUrlOverride.RemoveFromEnd(TEXT("/"));
        if (!BackendBaseUrlOverride.IsEmpty())
        {
            BackendBaseUrl = BackendBaseUrlOverride;
        }
    }
    else if (BackendBaseUrl.Equals(TEXT("http://127.0.0.1:5000"), ESearchCase::IgnoreCase))
    {
        // Docker Desktop can leave an installed-release portproxy on IPv4 loopback.
        // localhost prefers Docker's working IPv6 loopback in PIE and packaged builds.
        BackendBaseUrl = TEXT("http://localhost:5000");
    }

    Super::BeginPlay();
    SetActorTickEnabled(true);

    FString RealtimeEnabledOverride;
    if (FParse::Value(
            FCommandLine::Get(),
            TEXT("OntoTwinRealtimeWebSocket="),
            RealtimeEnabledOverride))
    {
        RealtimeEnabledOverride.TrimStartAndEndInline();
        bEnableRealtimeWebSocket = RealtimeEnabledOverride.Equals(TEXT("true"), ESearchCase::IgnoreCase)
            || RealtimeEnabledOverride == TEXT("1")
            || RealtimeEnabledOverride.Equals(TEXT("yes"), ESearchCase::IgnoreCase);
    }

    FString RealtimeUrlOverride;
    if (FParse::Value(
            FCommandLine::Get(),
            TEXT("OntoTwinRealtimeWebSocketUrl="),
            RealtimeUrlOverride))
    {
        RealtimeWebSocketUrl = RealtimeUrlOverride;
    }

    float PollIntervalOverride = 0.0f;
    if (FParse::Value(FCommandLine::Get(), TEXT("OntoTwinPollInterval="), PollIntervalOverride))
    {
        PollInterval = FMath::Clamp(PollIntervalOverride, 0.1f, 10.0f);
    }

    FString IncrementalSnapshotsOverride;
    if (FParse::Value(
            FCommandLine::Get(),
            TEXT("OntoTwinIncrementalSnapshots="),
            IncrementalSnapshotsOverride))
    {
        IncrementalSnapshotsOverride.TrimStartAndEndInline();
        bEnableIncrementalSnapshots = IncrementalSnapshotsOverride.Equals(TEXT("true"), ESearchCase::IgnoreCase)
            || IncrementalSnapshotsOverride == TEXT("1")
            || IncrementalSnapshotsOverride.Equals(TEXT("yes"), ESearchCase::IgnoreCase);
    }

    // 启动定时轮询（FR-4：孪生实例全部由数据库驱动动态 spawn，不再接管关卡预置 Actor）
    SetPollTimerInterval(PollInterval, 1.0f);

    bRealtimeClosing = false;
    if (bEnableRealtimeWebSocket)
    {
        if (!FModuleManager::Get().IsModuleLoaded(TEXT("WebSockets")))
        {
            FModuleManager::Get().LoadModule(TEXT("WebSockets"));
        }
        if (!FHttpModule::Get().GetProxyAddress().IsEmpty())
        {
            UE_LOG(LogTemp, Warning,
                TEXT("[OntoTwinWS] UE HTTP 代理仍处于启用状态，内网 WebSocket 可能被代理拦截: %s"),
                *FHttpModule::Get().GetProxyAddress());
        }
        ConnectRealtimeWebSocket();
    }
    else
    {
        RealtimeConnectionState = TEXT("disabled");
    }

    if (bEnableOverlays && !bEnableRuntimeEditor)
    {
        if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
        {
            EnableInput(PC);
        }
    }

    if (bEnableRuntimeEditor)
    {
        APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
        if (PC)
        {
            EnableInput(PC);
            if (InputComponent)
            {
                InputComponent->BindKey(ToggleEditKey, IE_Pressed, this, &ATwinSceneManager::RequestRuntimeEditToggle);
                if (AlternateToggleEditKey != EKeys::Invalid && AlternateToggleEditKey != ToggleEditKey)
                {
                    InputComponent->BindKey(AlternateToggleEditKey, IE_Pressed, this, &ATwinSceneManager::RequestRuntimeEditToggle);
                }
            }
        }

        UE_LOG(LogTemp, Log,
            TEXT("[RuntimeEditor] 已启用 | 主热键=%s | 备用热键=%s | PIE 中 F8 可能被编辑器 Eject 吃掉，建议用备用热键"),
            *ToggleEditKey.ToString(), *AlternateToggleEditKey.ToString());
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 6.0f, FColor::Cyan,
                FString::Printf(TEXT("Runtime Editor: %s / %s"),
                    *ToggleEditKey.ToString(), *AlternateToggleEditKey.ToString()));
        }
    }
    else
    {
        UE_LOG(LogTemp, Log, TEXT("[RuntimeEditor] 已关闭 (bEnableRuntimeEditor=false)"));
    }

    UE_LOG(LogTemp, Log,
           TEXT("[孪生管理器] 启动完毕 | 后端=%s | 轮询间隔=%.2fs | 预置实例=%d"),
           *BackendBaseUrl, PollInterval, InstanceRegistry.Num());
}

// ── EndPlay ──────────────────────────────────────────────────────────────────

void ATwinSceneManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    GetWorldTimerManager().ClearTimer(PollTimerHandle);
    GetWorldTimerManager().ClearTimer(RealtimeReconnectTimerHandle);
    GetWorldTimerManager().ClearTimer(OverlayMediaRetryTimer);
    bRealtimeClosing = true;
    RealtimeConnectionState = TEXT("disabled");
    ++RealtimeConnectionGeneration;
    if (RealtimeSocket.IsValid() && RealtimeSocket->IsConnected())
    {
        RealtimeSocket->Close();
    }
    RealtimeSocket.Reset();
    bRuntimeEditDirty = false;
    ExitRuntimeEditMode();
    if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
    {
        UpdateOverlayPointerInput(PC, false);
    }
    ClearOverlaySelection();

    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        RuntimeGizmo->Destroy();
    }
    RuntimeGizmo = nullptr;

    // 清理全部运行时 spawn 的孪生体（FR-4：不再有编辑器固化 Actor 需要保留）
    for (auto& Pair : InstanceRegistry)
    {
        if (Pair.Value && IsValid(Pair.Value))
        {
            Pair.Value->Destroy();
        }
    }
    InstanceRegistry.Empty();

    Super::EndPlay(EndPlayReason);
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 已清理运行时孪生体并停止轮询"));
}

void ATwinSceneManager::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    TickRuntimeEditor(DeltaTime);
    TickOverlays();
}

void ATwinSceneManager::TickOverlays()
{
    UpdateOverlayMediaPlaybackClock();
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC)
    {
        if (!bEnableOverlays) ClearOverlaySelection();
        return;
    }

    const bool bPointerOverRuntimePanel =
        RuntimeEditorPanel && IsValid(RuntimeEditorPanel) && RuntimeEditorPanel->IsPointerOverPanel();
    const bool bInteractionOwnsSelection =
        InteractionManager && InteractionManager->IsRoamingActive();

    bool bHasSelectedOverlay = false;
    if (bEnableOverlays)
    {
        for (const auto& Pair : InstanceRegistry)
        {
            if (Pair.Value && IsValid(Pair.Value) && Pair.Value->HasSelectedOverlay())
            {
                bHasSelectedOverlay = true;
                break;
            }
        }
    }

    const bool bInteractiveMediaSelected = OverlaySelectedInstance && SelectedOverlayWidget
        && SelectedOverlayWidget->HasPlayableMedia();
    UpdateOverlayPointerInput(
        PC,
        bEnableOverlays && (bHasSelectedOverlay || bInteractiveMediaSelected)
            && !bInteractionOwnsSelection && !bRuntimeEditMode);

    if (!bEnableOverlays)
    {
        ClearOverlaySelection();
        return;
    }

    const bool bPointerOverOverlay = SelectedOverlayWidget
        && IsValid(SelectedOverlayWidget) && SelectedOverlayWidget->IsPointerOverPanel();
    if (!bInteractionOwnsSelection && !bPointerOverRuntimePanel && !bPointerOverOverlay
        && PC->WasInputKeyJustPressed(EKeys::LeftMouseButton))
    {
        FHitResult Hit;
        ATwinInstance* HitInstance = nullptr;
        if (TraceRuntimeCursor(Hit))
        {
            HitInstance = Cast<ATwinInstance>(Hit.GetActor());
        }
        if (HitInstance && HitInstance->HasSelectedOverlay())
        {
            SelectOverlayInstance(HitInstance);
        }
        else
        {
            ClearOverlaySelection();
        }
    }
    else if (bRuntimeEditMode && RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance)
        && RuntimeSelectedInstance->HasSelectedOverlay())
    {
        SelectOverlayInstance(RuntimeSelectedInstance);
    }

    if (!bInteractionOwnsSelection && !bRuntimeEditMode
        && PC->WasInputKeyJustPressed(EKeys::Escape))
    {
        ClearOverlaySelection();
    }

    if (OverlaySelectedInstance &&
        (!IsValid(OverlaySelectedInstance)
            || !OverlaySelectedInstance->HasSelectedOverlay()))
    {
        ClearOverlaySelection();
    }

    if (OverlaySelectedInstance && SelectedOverlayWidget)
    {
        const uint64 PayloadSerial = OverlaySelectedInstance->GetOverlayPayloadSerial();
        if (PayloadSerial != SelectedOverlayPayloadSerial)
        {
            SelectedOverlayWidget->ApplyOverlayData(OverlaySelectedInstance->GetOverlayData());
            SelectedOverlayPayloadSerial = PayloadSerial;
            RefreshOverlayMediaForSelection();
        }

        const ESlateVisibility InteractiveVisibility = SelectedOverlayWidget->HasPlayableMedia()
            ? ESlateVisibility::Visible : ESlateVisibility::HitTestInvisible;
        if (SelectedOverlayWidget->IsMediaExpanded())
        {
            SelectedOverlayWidget->SetAlignmentInViewport(FVector2D(0.5f, 0.5f));
            SelectedOverlayWidget->SetPositionInViewport(FVector2D::ZeroVector, false);
            SelectedOverlayWidget->SetAnchorsInViewport(FAnchors(0.5f, 0.5f));
            SelectedOverlayWidget->SetVisibility(InteractiveVisibility);
        }
        else
        {
            // UMG 使用经过 DPI 缩放的逻辑坐标，不能直接使用 PlayerController 返回的物理像素。
            // 所有视角统一跟随模型锚点；锚点出屏时把面板约束在最近的屏幕边缘。
            FVector2D WidgetPosition;
            const bool bProjected = UWidgetLayoutLibrary::ProjectWorldLocationToWidgetPosition(
                PC,
                OverlaySelectedInstance->GetOverlayAnchorWorldLocation(),
                WidgetPosition,
                true);
            SelectedOverlayWidget->SetAlignmentInViewport(FVector2D(0.5f, 1.0f));
            SelectedOverlayWidget->SetVisibility(
                bProjected ? InteractiveVisibility : ESlateVisibility::Collapsed);
            if (bProjected)
            {
                constexpr double EdgeMargin = 24.0;
                constexpr double AnchorGap = 16.0;
                const float ViewportScale = FMath::Max(
                    KINDA_SMALL_NUMBER,
                    UWidgetLayoutLibrary::GetViewportScale(this));
                const FVector2D ViewportSize =
                    UWidgetLayoutLibrary::GetViewportSize(this) / ViewportScale;
                const FVector2D PanelSize = SelectedOverlayWidget->GetDesiredRenderSize();

                WidgetPosition.Y -= AnchorGap;
                const double MinX = FMath::Min(
                    EdgeMargin + PanelSize.X * 0.5,
                    FMath::Max(EdgeMargin, ViewportSize.X - EdgeMargin));
                const double MaxX = FMath::Max(
                    MinX,
                    ViewportSize.X - EdgeMargin - PanelSize.X * 0.5);
                const double MaxY = FMath::Max(EdgeMargin, ViewportSize.Y - EdgeMargin);
                const double MinY = FMath::Min(EdgeMargin + PanelSize.Y, MaxY);
                WidgetPosition.X = FMath::Clamp(WidgetPosition.X, MinX, MaxX);
                WidgetPosition.Y = FMath::Clamp(WidgetPosition.Y, MinY, MaxY);
                SelectedOverlayWidget->SetPositionInViewport(WidgetPosition, false);
            }
        }
    }

    UpdateAlwaysOverlays(PC);
}

void ATwinSceneManager::UpdateOverlayPointerInput(
    APlayerController* PlayerController,
    bool bShouldOwnPointer)
{
    if (!PlayerController) return;

    if (bShouldOwnPointer)
    {
        if (!bOverlayPointerInputActive)
        {
            bOverlayPreviousMouseCursor = PlayerController->bShowMouseCursor;
            bOverlayPointerInputActive = true;

            FInputModeGameAndUI InputMode;
            InputMode.SetHideCursorDuringCapture(false);
            InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
            PlayerController->SetInputMode(InputMode);
        }
        PlayerController->bShowMouseCursor = true;
        return;
    }

    if (!bOverlayPointerInputActive) return;
    bOverlayPointerInputActive = false;

    const bool bAnotherSystemOwnsInput = bRuntimeEditMode
        || (InteractionManager && InteractionManager->IsRoamingActive());
    if (bAnotherSystemOwnsInput) return;

    PlayerController->bShowMouseCursor = bOverlayPreviousMouseCursor;
    if (!bOverlayPreviousMouseCursor)
    {
        PlayerController->SetInputMode(FInputModeGameOnly());
    }
}

void ATwinSceneManager::SelectOverlayInstance(ATwinInstance* Instance)
{
    if (!Instance || !IsValid(Instance) || !Instance->HasSelectedOverlay())
    {
        return;
    }
    if (OverlaySelectedInstance != Instance)
    {
        StopOverlayMedia();
        OverlaySelectedInstance = Instance;
        SelectedOverlayPayloadSerial = 0;
    }
    if (!SelectedOverlayWidget)
    {
        APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
        if (!PC) return;
        UClass* WidgetClass = OverlayWidgetClass
            ? OverlayWidgetClass.Get() : UOntoTwinOverlayWidget::StaticClass();
        SelectedOverlayWidget = CreateWidget<UOntoTwinOverlayWidget>(PC, WidgetClass);
        if (!SelectedOverlayWidget) return;
        TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
        SelectedOverlayWidget->SetMediaActionHandler(
            [WeakThis](EOntoTwinOverlayMediaAction Action)
            {
                if (WeakThis.IsValid())
                {
                    WeakThis->HandleOverlayMediaAction(Action);
                }
            });
        SelectedOverlayWidget->SetAlignmentInViewport(FVector2D(0.5f, 1.0f));
        SelectedOverlayWidget->AddToViewport(900);
    }

    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin overlay selected instance=%s roaming=%s widget=%s"),
        *Instance->GetInstanceId(),
        InteractionManager && InteractionManager->IsRoamingActive() ? TEXT("true") : TEXT("false"),
        SelectedOverlayWidget ? TEXT("ready") : TEXT("missing"));
}

void ATwinSceneManager::ClearOverlaySelection()
{
    StopOverlayMedia();
    OverlaySelectedInstance = nullptr;
    SelectedOverlayPayloadSerial = 0;
    UOntoTwinOverlayWidget* WidgetToClose = SelectedOverlayWidget;
    SelectedOverlayWidget = nullptr;
    if (WidgetToClose && IsValid(WidgetToClose))
    {
        const TWeakObjectPtr<UOntoTwinOverlayWidget> WeakWidget(WidgetToClose);
        WidgetToClose->PlayCloseAnimation(
            [WeakWidget]()
            {
                if (WeakWidget.IsValid())
                {
                    WeakWidget->RemoveFromParent();
                }
            });
    }
}

void ATwinSceneManager::RefreshOverlayMediaForSelection(bool bForceResolve)
{
    if (!OverlaySelectedInstance || !IsValid(OverlaySelectedInstance)
        || !SelectedOverlayWidget || !IsValid(SelectedOverlayWidget)
        || !SelectedOverlayWidget->HasPlayableMedia())
    {
        StopOverlayMedia();
        return;
    }

    const FString InstanceId = OverlaySelectedInstance->GetInstanceId();
    const FString SourceRevision = SelectedOverlayWidget->GetMediaSourceRevision();
    const bool bSameSource = OverlayMediaInstanceId == InstanceId
        && OverlayMediaSourceRevision == SourceRevision;
    if (bSameSource && (OverlayMediaResolveRequest.IsValid()
        || bOverlayMediaOpening
        || GetWorldTimerManager().IsTimerActive(OverlayMediaRetryTimer)
        || (OverlayMediaPlayer && OverlayMediaPlayer->IsReady())))
    {
        return;
    }
    if (bSameSource && bOverlayMediaManualRetryRequired && !bForceResolve)
    {
        return;
    }

    if (!bSameSource)
    {
        StopOverlayMedia();
        OverlayMediaInstanceId = InstanceId;
        OverlayMediaSourceRevision = SourceRevision;
        bOverlayMediaAutoplay = SelectedOverlayWidget->ShouldAutoplayMedia();
        bOverlayMediaPlayWhenOpened = false;
        OverlayMediaRetryIndex = 0;
    }

    if (bForceResolve || bOverlayMediaAutoplay)
    {
        bOverlayMediaPlayWhenOpened = bForceResolve || bOverlayMediaAutoplay;
        RequestOverlayMediaResolve(false);
    }
    else
    {
        SelectedOverlayWidget->SetMediaPlaybackState(
            false, bOverlayMediaMuted, TEXT("Select Play to start"));
    }
}

void ATwinSceneManager::RequestOverlayMediaResolve(bool bResetRetry)
{
    if (!OverlaySelectedInstance || !IsValid(OverlaySelectedInstance)
        || !SelectedOverlayWidget || !IsValid(SelectedOverlayWidget)
        || !SelectedOverlayWidget->HasPlayableMedia())
    {
        return;
    }
    if (OverlayMediaResolveRequest.IsValid() || bOverlayMediaOpening)
    {
        return;
    }

    if (bResetRetry)
    {
        GetWorldTimerManager().ClearTimer(OverlayMediaRetryTimer);
        OverlayMediaRetryIndex = 0;
        bOverlayMediaManualRetryRequired = false;
    }

    OverlayMediaInstanceId = OverlaySelectedInstance->GetInstanceId();
    OverlayMediaSourceRevision = SelectedOverlayWidget->GetMediaSourceRevision();
    SelectedOverlayWidget->SetMediaPlaybackState(
        false, bOverlayMediaMuted, TEXT("Loading video..."));

    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("instance_id"), OverlayMediaInstanceId);
    FString BodyString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyString);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(
        TEXT("%s/api/v2/overlays/media/resolve"), *BackendBaseUrl));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(Request);
    Request->SetContentAsString(BodyString);
    Request->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnOverlayMediaResolveResponse);
    OverlayMediaResolveRequest = Request;
    if (!Request->ProcessRequest())
    {
        OverlayMediaResolveRequest.Reset();
        ScheduleOverlayMediaRetry(TEXT("Video source request failed"));
    }
}

void ATwinSceneManager::OnOverlayMediaResolveResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
    if (OverlayMediaResolveRequest != HttpRequest)
    {
        return;
    }
    OverlayMediaResolveRequest.Reset();
    if (!OverlaySelectedInstance || !IsValid(OverlaySelectedInstance)
        || OverlaySelectedInstance->GetInstanceId() != OverlayMediaInstanceId)
    {
        return;
    }

    const int32 ResponseCode = Response.IsValid() ? Response->GetResponseCode() : -1;
    if (!bWasSuccessful || !Response.IsValid() || ResponseCode != 200)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("OntoTwin media resolve failed successful=%s response_valid=%s code=%d retry_index=%d"),
            bWasSuccessful ? TEXT("true") : TEXT("false"),
            Response.IsValid() ? TEXT("true") : TEXT("false"),
            ResponseCode,
            OverlayMediaRetryIndex);
        if (ResponseCode < 0 || ResponseCode >= 500)
        {
            ScheduleOverlayMediaRetry(TEXT("Video source unavailable"));
        }
        else if (SelectedOverlayWidget && IsValid(SelectedOverlayWidget))
        {
            bOverlayMediaManualRetryRequired = true;
            SelectedOverlayWidget->SetMediaPlaybackState(
                false,
                bOverlayMediaMuted,
                TEXT("Video source blocked or invalid"),
                true);
        }
        return;
    }

    TSharedPtr<FJsonObject> Payload;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(
        Response->GetContentAsString());
    if (!FJsonSerializer::Deserialize(Reader, Payload) || !Payload.IsValid())
    {
        ScheduleOverlayMediaRetry(TEXT("Invalid video source response"));
        return;
    }

    FString InstanceId;
    FString SourceRevision;
    FString MediaUrl;
    Payload->TryGetStringField(TEXT("instance_id"), InstanceId);
    Payload->TryGetStringField(TEXT("source_revision"), SourceRevision);
    Payload->TryGetStringField(TEXT("kind"), OverlayMediaKind);
    Payload->TryGetStringField(TEXT("url"), MediaUrl);
    if (InstanceId != OverlayMediaInstanceId || MediaUrl.IsEmpty())
    {
        return;
    }
    if (!OverlayMediaSourceRevision.IsEmpty() && !SourceRevision.IsEmpty()
        && SourceRevision != OverlayMediaSourceRevision)
    {
        // The snapshot changed while the signed URL was being resolved.
        RefreshOverlayMediaForSelection(true);
        return;
    }

    const TSharedPtr<FJsonObject>* Playback = nullptr;
    if (Payload->TryGetObjectField(TEXT("playback"), Playback)
        && Playback && Playback->IsValid())
    {
        (*Playback)->TryGetBoolField(TEXT("autoplay"), bOverlayMediaAutoplay);
        (*Playback)->TryGetBoolField(TEXT("muted"), bOverlayMediaMuted);
        (*Playback)->TryGetBoolField(TEXT("loop"), bOverlayMediaLoop);
    }
    if (OverlayMediaKind == TEXT("hls"))
    {
        bOverlayMediaLoop = false;
    }
    bOverlayMediaPlayWhenOpened = bOverlayMediaPlayWhenOpened || bOverlayMediaAutoplay;

    EnsureOverlayMediaPlayer();
    if (!OverlayMediaPlayer)
    {
        ScheduleOverlayMediaRetry(TEXT("Video player unavailable"));
        return;
    }
#if PLATFORM_WINDOWS
    const FName DesiredPlayerName = OverlayMediaKind.Equals(
        TEXT("mp4"), ESearchCase::IgnoreCase)
        ? FName(TEXT("WmfMedia"))
        : FName(TEXT("ElectraPlayer"));
#else
    const FName DesiredPlayerName(TEXT("ElectraPlayer"));
#endif
    OverlayMediaPlayer->SetDesiredPlayerName(DesiredPlayerName);
    OverlayMediaPlayer->SetLooping(bOverlayMediaLoop);
    if (OverlayMediaSound)
    {
        OverlayMediaSound->SetVolumeMultiplier(bOverlayMediaMuted ? 0.0f : 1.0f);
    }
    bOverlayMediaOpening = true;
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media open started instance=%s kind=%s desired_player=%s"),
        *OverlayMediaInstanceId,
        *OverlayMediaKind,
        *DesiredPlayerName.ToString());
    if (!OverlayMediaPlayer->OpenUrl(MediaUrl))
    {
        bOverlayMediaOpening = false;
        ScheduleOverlayMediaRetry(TEXT("Unable to open video"));
    }
}

void ATwinSceneManager::EnsureOverlayMediaPlayer()
{
    if (!OverlayMediaPlayer)
    {
        OverlayMediaPlayer = NewObject<UMediaPlayer>(this, TEXT("OverlayMediaPlayer"));
        if (OverlayMediaPlayer)
        {
            OverlayMediaPlayer->PlayOnOpen = false;
            OverlayMediaPlayer->OnMediaOpened.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaOpened);
            OverlayMediaPlayer->OnTracksChanged.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaTracksChanged);
            OverlayMediaPlayer->OnMediaOpenFailed.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaOpenFailed);
            OverlayMediaPlayer->OnEndReached.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaEndReached);
            OverlayMediaPlayer->OnPlaybackResumed.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaPlaybackResumed);
            OverlayMediaPlayer->OnPlaybackSuspended.AddDynamic(
                this, &ATwinSceneManager::OnOverlayMediaPlaybackSuspended);
        }
    }
    if (!OverlayMediaTexture)
    {
        OverlayMediaTexture = NewObject<UMediaTexture>(this, TEXT("OverlayMediaTexture"));
        if (OverlayMediaTexture)
        {
            OverlayMediaTexture->AutoClear = false;
            OverlayMediaTexture->NewStyleOutput = true;
            OverlayMediaTexture->SetRenderMode(UMediaTexture::ERenderMode::Default);
            OverlayMediaTexture->SetMediaPlayer(OverlayMediaPlayer);
            OverlayMediaTexture->UpdateResource();
        }
    }
    if (OverlayMediaSound)
    {
        if (OverlayMediaSound->GetMediaPlayer() != OverlayMediaPlayer)
        {
            // MediaSound must not create its generator before it has a player.
            // Otherwise UE 5.6 can register an unconsumed audio sink and stall V2 video timing.
            OverlayMediaSound->SetActive(false, true);
            OverlayMediaSound->SetMediaPlayer(OverlayMediaPlayer);
            OverlayMediaSound->SetActive(true, true);
        }
        OverlayMediaSound->SetVolumeMultiplier(bOverlayMediaMuted ? 0.0f : 1.0f);
        UE_LOG(LogTemp, Log,
            TEXT("OntoTwin media sound active=%s bound=%s muted=%s"),
            OverlayMediaSound->IsActive() ? TEXT("true") : TEXT("false"),
            OverlayMediaSound->GetMediaPlayer() == OverlayMediaPlayer
                ? TEXT("true") : TEXT("false"),
            bOverlayMediaMuted ? TEXT("true") : TEXT("false"));
    }
}

void ATwinSceneManager::UpdateOverlayMediaPlaybackClock()
{
    if (!OverlayMediaPlayer || bOverlayMediaLoop || bOverlayMediaReachedEnd
        || bOverlayMediaOpening || !OverlayMediaPlayer->IsReady())
    {
        return;
    }

    if (OverlayMediaDurationSeconds <= 0.0)
    {
        OverlayMediaDurationSeconds = OverlayMediaPlayer->GetDuration().GetTotalSeconds();
    }
    if (OverlayMediaDurationSeconds <= 0.0
        || OverlayMediaPlaybackStartedAtSeconds <= 0.0
        || !OverlayMediaPlayer->IsPlaying())
    {
        return;
    }

    const double NowSeconds = FPlatformTime::Seconds();
    const double ElapsedSeconds = OverlayMediaPlayedSeconds
        + FMath::Max(0.0, NowSeconds - OverlayMediaPlaybackStartedAtSeconds);
    if (!bOverlayMediaTextureSampleLogged && ElapsedSeconds >= 1.0
        && OverlayMediaTexture)
    {
        bOverlayMediaTextureSampleLogged = true;
        const UWorld* World = GetWorld();
        UE_LOG(LogTemp, Log,
            TEXT("OntoTwin media texture size=%dx%d aspect=%.3f samples=%d new_style=%s bound=%s player=%s rate=%.3f media_time=%.3fs next_sample=%.3fs world_paused=%s world_delta=%.6f"),
            OverlayMediaTexture->GetWidth(),
            OverlayMediaTexture->GetHeight(),
            OverlayMediaTexture->GetCurrentAspectRatio(),
            OverlayMediaTexture->GetAvailableSampleCount(),
            OverlayMediaTexture->NewStyleOutput ? TEXT("true") : TEXT("false"),
            OverlayMediaTexture->GetMediaPlayer() == OverlayMediaPlayer
                ? TEXT("true") : TEXT("false"),
            *OverlayMediaPlayer->GetPlayerName().ToString(),
            OverlayMediaPlayer->GetRate(),
            OverlayMediaPlayer->GetTime().GetTotalSeconds(),
            OverlayMediaTexture->GetNextSampleTime().GetTotalSeconds(),
            World && World->IsPaused() ? TEXT("true") : TEXT("false"),
            World ? World->GetDeltaSeconds() : 0.0f);
    }
    if (ElapsedSeconds < OverlayMediaDurationSeconds + 0.15)
    {
        return;
    }

    OverlayMediaPlayedSeconds = OverlayMediaDurationSeconds;
    OverlayMediaPlaybackStartedAtSeconds = 0.0;
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media end fallback elapsed=%.3fs duration=%.3fs"),
        ElapsedSeconds,
        OverlayMediaDurationSeconds);
    OnOverlayMediaEndReached();
}

void ATwinSceneManager::HandleOverlayMediaAction(EOntoTwinOverlayMediaAction Action)
{
    if (!SelectedOverlayWidget || !IsValid(SelectedOverlayWidget)) return;

    if (Action == EOntoTwinOverlayMediaAction::PlayPause)
    {
        UE_LOG(LogTemp, Log,
            TEXT("OntoTwin media play/pause ready=%s playing=%s ended=%s time=%.3fs"),
            OverlayMediaPlayer && OverlayMediaPlayer->IsReady() ? TEXT("true") : TEXT("false"),
            OverlayMediaPlayer && OverlayMediaPlayer->IsPlaying() ? TEXT("true") : TEXT("false"),
            bOverlayMediaReachedEnd ? TEXT("true") : TEXT("false"),
            OverlayMediaPlayer ? OverlayMediaPlayer->GetTime().GetTotalSeconds() : 0.0);
    }

    switch (Action)
    {
    case EOntoTwinOverlayMediaAction::PlayPause:
        if (OverlayMediaPlayer && bOverlayMediaReachedEnd)
        {
            bOverlayMediaReachedEnd = false;
            bOverlayMediaPlayWhenOpened = true;
            OverlayMediaPlayedSeconds = 0.0;
            OverlayMediaPlaybackStartedAtSeconds = 0.0;
            RequestOverlayMediaResolve(true);
        }
        else if (OverlayMediaPlayer && OverlayMediaPlayer->IsPlaying())
        {
            OverlayMediaPlayer->Pause();
            SelectedOverlayWidget->SetMediaPlaybackState(
                false, bOverlayMediaMuted, TEXT("Paused"));
        }
        else if (OverlayMediaPlayer && OverlayMediaPlayer->IsReady())
        {
            if (OverlayMediaPlayer->Play())
            {
                SelectedOverlayWidget->SetMediaPlaybackState(true, bOverlayMediaMuted);
            }
            else
            {
                bOverlayMediaPlayWhenOpened = true;
                RequestOverlayMediaResolve(true);
            }
        }
        else
        {
            bOverlayMediaPlayWhenOpened = true;
            RequestOverlayMediaResolve(true);
        }
        break;
    case EOntoTwinOverlayMediaAction::ToggleMute:
        bOverlayMediaMuted = !bOverlayMediaMuted;
        if (OverlayMediaSound)
        {
            OverlayMediaSound->SetVolumeMultiplier(bOverlayMediaMuted ? 0.0f : 1.0f);
        }
        SelectedOverlayWidget->SetMediaPlaybackState(
            OverlayMediaPlayer && OverlayMediaPlayer->IsPlaying(), bOverlayMediaMuted);
        break;
    case EOntoTwinOverlayMediaAction::ToggleExpanded:
        SelectedOverlayWidget->SetMediaExpanded(!SelectedOverlayWidget->IsMediaExpanded());
        break;
    case EOntoTwinOverlayMediaAction::Close:
        ClearOverlaySelection();
        break;
    case EOntoTwinOverlayMediaAction::Retry:
        bOverlayMediaPlayWhenOpened = true;
        RequestOverlayMediaResolve(true);
        break;
    default:
        break;
    }
}

void ATwinSceneManager::ScheduleOverlayMediaRetry(const FString& StatusMessage)
{
    bOverlayMediaOpening = false;
    static const float RetryDelays[] = {2.0f, 5.0f, 15.0f};
    if (!SelectedOverlayWidget || !IsValid(SelectedOverlayWidget)) return;

    UE_LOG(LogTemp, Warning,
        TEXT("OntoTwin media retry status=%s retry_index=%d"),
        *StatusMessage,
        OverlayMediaRetryIndex);

    if (OverlayMediaRetryIndex >= UE_ARRAY_COUNT(RetryDelays))
    {
        bOverlayMediaManualRetryRequired = true;
        SelectedOverlayWidget->SetMediaPlaybackState(
            false,
            bOverlayMediaMuted,
            StatusMessage + TEXT(" - select Retry"),
            true);
        return;
    }

    const float Delay = RetryDelays[OverlayMediaRetryIndex++];
    SelectedOverlayWidget->SetMediaPlaybackState(
        false,
        bOverlayMediaMuted,
        FString::Printf(TEXT("%s - retrying in %.0fs"), *StatusMessage, Delay));
    TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
    GetWorldTimerManager().SetTimer(
        OverlayMediaRetryTimer,
        FTimerDelegate::CreateLambda([WeakThis]()
        {
            if (WeakThis.IsValid())
            {
                WeakThis->RequestOverlayMediaResolve(false);
            }
        }),
        Delay,
        false);
}

void ATwinSceneManager::StopOverlayMedia(bool bResetWidget)
{
    GetWorldTimerManager().ClearTimer(OverlayMediaRetryTimer);
    bOverlayMediaOpening = false;
    bOverlayMediaReachedEnd = false;
    bOverlayMediaTextureSampleLogged = false;
    OverlayMediaDurationSeconds = 0.0;
    OverlayMediaPlayedSeconds = 0.0;
    OverlayMediaPlaybackStartedAtSeconds = 0.0;
    if (OverlayMediaResolveRequest.IsValid())
    {
        OverlayMediaResolveRequest->CancelRequest();
        OverlayMediaResolveRequest.Reset();
    }
    OverlayMediaInstanceId.Empty();
    OverlayMediaSourceRevision.Empty();
    OverlayMediaKind.Empty();
    OverlayMediaRetryIndex = 0;
    bOverlayMediaPlayWhenOpened = false;
    bOverlayMediaManualRetryRequired = false;
    if (OverlayMediaPlayer)
    {
        OverlayMediaPlayer->Close();
    }
    if (bResetWidget && SelectedOverlayWidget && IsValid(SelectedOverlayWidget))
    {
        SelectedOverlayWidget->SetMediaTexture(nullptr);
        SelectedOverlayWidget->SetMediaPlaybackState(false, bOverlayMediaMuted);
        SelectedOverlayWidget->SetMediaExpanded(false);
    }
}

void ATwinSceneManager::OnOverlayMediaOpened(FString OpenedUrl)
{
    bOverlayMediaOpening = false;
    bOverlayMediaReachedEnd = false;
    bOverlayMediaTextureSampleLogged = false;
    OverlayMediaDurationSeconds = 0.0;
    OverlayMediaPlayedSeconds = 0.0;
    OverlayMediaPlaybackStartedAtSeconds = 0.0;
    GetWorldTimerManager().ClearTimer(OverlayMediaRetryTimer);
    UE_LOG(LogTemp, Log, TEXT("OntoTwin media opened instance=%s"),
        *OverlayMediaInstanceId);
    if (OverlayMediaInstanceId.IsEmpty() || !SelectedOverlayWidget
        || !IsValid(SelectedOverlayWidget) || !OverlayMediaPlayer)
    {
        return;
    }
    OverlayMediaDurationSeconds = OverlayMediaPlayer->GetDuration().GetTotalSeconds();
    UE_LOG(LogTemp, Log, TEXT("OntoTwin media duration=%.3fs"),
        OverlayMediaDurationSeconds);
    OverlayMediaRetryIndex = 0;
    SelectedOverlayWidget->SetMediaTexture(OverlayMediaTexture);
    if (bOverlayMediaPlayWhenOpened)
    {
        OverlayMediaPlayer->Play();
    }
    SelectedOverlayWidget->SetMediaPlaybackState(
        OverlayMediaPlayer->IsPlaying(),
        bOverlayMediaMuted,
        OverlayMediaPlayer->IsPlaying() ? FString() : TEXT("Ready"));
}

void ATwinSceneManager::OnOverlayMediaOpenFailed(FString FailedUrl)
{
    if (OverlayMediaInstanceId.IsEmpty()) return;
    bOverlayMediaOpening = false;
    UE_LOG(LogTemp, Warning, TEXT("OntoTwin media open failed instance=%s kind=%s"),
        *OverlayMediaInstanceId,
        *OverlayMediaKind);
    ScheduleOverlayMediaRetry(TEXT("Unable to play video"));
}

void ATwinSceneManager::OnOverlayMediaTracksChanged()
{
    if (!OverlayMediaPlayer)
    {
        return;
    }

    const int32 VideoTrackCount = OverlayMediaPlayer->GetNumTracks(
        EMediaPlayerTrack::Video);
    int32 SelectedVideoTrack = OverlayMediaPlayer->GetSelectedTrack(
        EMediaPlayerTrack::Video);
    bool bSelectedFallbackTrack = false;
    if (SelectedVideoTrack == INDEX_NONE && VideoTrackCount > 0)
    {
        bSelectedFallbackTrack = OverlayMediaPlayer->SelectTrack(
            EMediaPlayerTrack::Video, 0);
        SelectedVideoTrack = OverlayMediaPlayer->GetSelectedTrack(
            EMediaPlayerTrack::Video);
    }

    const int32 FormatIndex = SelectedVideoTrack == INDEX_NONE
        ? INDEX_NONE
        : OverlayMediaPlayer->GetTrackFormat(
            EMediaPlayerTrack::Video, SelectedVideoTrack);
    const FIntPoint Dimensions = FormatIndex == INDEX_NONE
        ? FIntPoint::ZeroValue
        : OverlayMediaPlayer->GetVideoTrackDimensions(
            SelectedVideoTrack, FormatIndex);
    const float FrameRate = FormatIndex == INDEX_NONE
        ? 0.0f
        : OverlayMediaPlayer->GetVideoTrackFrameRate(
            SelectedVideoTrack, FormatIndex);
    const FString Codec = FormatIndex == INDEX_NONE
        ? FString()
        : OverlayMediaPlayer->GetVideoTrackType(
            SelectedVideoTrack, FormatIndex);

    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media tracks player=%s video_tracks=%d selected=%d fallback_selected=%s format=%d size=%dx%d fps=%.3f codec=%s"),
        *OverlayMediaPlayer->GetPlayerName().ToString(),
        VideoTrackCount,
        SelectedVideoTrack,
        bSelectedFallbackTrack ? TEXT("true") : TEXT("false"),
        FormatIndex,
        Dimensions.X,
        Dimensions.Y,
        FrameRate,
        Codec.IsEmpty() ? TEXT("unknown") : *Codec);
}

void ATwinSceneManager::OnOverlayMediaEndReached()
{
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media end reached player=%s time=%.3fs rate=%.3f"),
        OverlayMediaPlayer ? *OverlayMediaPlayer->GetPlayerName().ToString() : TEXT("none"),
        OverlayMediaPlayer ? OverlayMediaPlayer->GetTime().GetTotalSeconds() : 0.0,
        OverlayMediaPlayer ? OverlayMediaPlayer->GetRate() : 0.0f);
    if (bOverlayMediaLoop)
    {
        bOverlayMediaReachedEnd = false;
        OverlayMediaPlayedSeconds = 0.0;
        OverlayMediaPlaybackStartedAtSeconds = FPlatformTime::Seconds();
        return;
    }
    bOverlayMediaReachedEnd = true;
    OverlayMediaPlaybackStartedAtSeconds = 0.0;
    if (OverlayMediaDurationSeconds > 0.0)
    {
        OverlayMediaPlayedSeconds = OverlayMediaDurationSeconds;
    }
    if (SelectedOverlayWidget && IsValid(SelectedOverlayWidget))
    {
        SelectedOverlayWidget->SetMediaPlaybackState(
            false, bOverlayMediaMuted, TEXT("Finished - select Play to replay"));
    }
}

void ATwinSceneManager::OnOverlayMediaPlaybackResumed()
{
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media playback resumed player=%s time=%.3fs rate=%.3f"),
        OverlayMediaPlayer ? *OverlayMediaPlayer->GetPlayerName().ToString() : TEXT("none"),
        OverlayMediaPlayer ? OverlayMediaPlayer->GetTime().GetTotalSeconds() : 0.0,
        OverlayMediaPlayer ? OverlayMediaPlayer->GetRate() : 0.0f);
    bOverlayMediaReachedEnd = false;
    if (OverlayMediaPlayer && OverlayMediaDurationSeconds <= 0.0)
    {
        OverlayMediaDurationSeconds = OverlayMediaPlayer->GetDuration().GetTotalSeconds();
    }
    OverlayMediaPlaybackStartedAtSeconds = FPlatformTime::Seconds();
    if (SelectedOverlayWidget && IsValid(SelectedOverlayWidget))
    {
        SelectedOverlayWidget->SetMediaPlaybackState(true, bOverlayMediaMuted);
    }
}

void ATwinSceneManager::OnOverlayMediaPlaybackSuspended()
{
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin media playback suspended player=%s time=%.3fs rate=%.3f"),
        OverlayMediaPlayer ? *OverlayMediaPlayer->GetPlayerName().ToString() : TEXT("none"),
        OverlayMediaPlayer ? OverlayMediaPlayer->GetTime().GetTotalSeconds() : 0.0,
        OverlayMediaPlayer ? OverlayMediaPlayer->GetRate() : 0.0f);
    if (OverlayMediaPlaybackStartedAtSeconds > 0.0)
    {
        OverlayMediaPlayedSeconds += FMath::Max(
            0.0,
            FPlatformTime::Seconds() - OverlayMediaPlaybackStartedAtSeconds);
        OverlayMediaPlaybackStartedAtSeconds = 0.0;
        if (OverlayMediaDurationSeconds > 0.0)
        {
            OverlayMediaPlayedSeconds = FMath::Min(
                OverlayMediaPlayedSeconds, OverlayMediaDurationSeconds);
        }
    }
    if (!bOverlayMediaReachedEnd && SelectedOverlayWidget
        && IsValid(SelectedOverlayWidget))
    {
        SelectedOverlayWidget->SetMediaPlaybackState(
            false, bOverlayMediaMuted, TEXT("Paused"));
    }
}

void ATwinSceneManager::SelectOverlayFromSceneInteraction(ATwinInstance* Instance)
{
    // always 的世界空间面板已经是最终呈现，点击时不能再创建一份 Screen Space 面板。
    // selected 才进入点按选择链路；两个显示模式在单个实例上严格互斥。
    if (!Instance || !IsValid(Instance) || !Instance->HasSelectedOverlay())
    {
        ClearOverlaySelection();
        return;
    }
    SelectOverlayInstance(Instance);
}

void ATwinSceneManager::ClearOverlayFromSceneInteraction()
{
    ClearOverlaySelection();
}

ATwinInstance* ATwinSceneManager::FindAlwaysOverlayAtScreenPosition(
    APlayerController* PlayerController,
    const FVector2D& ScreenPosition) const
{
    if (!PlayerController) return nullptr;

    ATwinInstance* BestInstance = nullptr;
    float BestDistanceSquared = FLT_MAX;
    const FVector CameraLocation = PlayerController->PlayerCameraManager
        ? PlayerController->PlayerCameraManager->GetCameraLocation()
        : FVector::ZeroVector;

    for (const TPair<FString, ATwinInstance*>& Pair : InstanceRegistry)
    {
        ATwinInstance* Instance = Pair.Value;
        if (!Instance || !IsValid(Instance)
            || !Instance->IsScreenPointOverAlwaysOverlay(PlayerController, ScreenPosition))
        {
            continue;
        }

        const float DistanceSquared = FVector::DistSquared(
            CameraLocation, Instance->GetOverlayAnchorWorldLocation());
        if (!BestInstance || DistanceSquared < BestDistanceSquared)
        {
            BestInstance = Instance;
            BestDistanceSquared = DistanceSquared;
        }
    }
    return BestInstance;
}

bool ATwinSceneManager::SelectOverlayAtScreenPosition(const FVector2D& ScreenPosition)
{
    APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
    ATwinInstance* Instance = FindAlwaysOverlayAtScreenPosition(PlayerController, ScreenPosition);
    if (!Instance) return false;
    SelectOverlayFromSceneInteraction(Instance);
    return true;
}

ATwinInstance* ATwinSceneManager::FindOverlayInstanceNearHit(
    const FHitResult& Hit,
    float MaxDistanceCm) const
{
    const FVector HitLocation = Hit.bBlockingHit ? Hit.ImpactPoint : Hit.Location;
    const float MaxDistanceSquared = FMath::Square(FMath::Max(1.0f, MaxDistanceCm));
    ATwinInstance* BestInstance = nullptr;
    float BestDistanceSquared = MaxDistanceSquared;

    for (const TPair<FString, ATwinInstance*>& Pair : InstanceRegistry)
    {
        ATwinInstance* Instance = Pair.Value;
        if (!Instance || !IsValid(Instance) || !Instance->HasOverlay()) continue;

        const FBox Bounds = Instance->GetComponentsBoundingBox(true);
        const FVector Closest = Bounds.IsValid
            ? Bounds.GetClosestPointTo(HitLocation)
            : Instance->GetActorLocation();
        const float DistanceSquared = FVector::DistSquared(HitLocation, Closest);
        if (DistanceSquared <= BestDistanceSquared)
        {
            BestInstance = Instance;
            BestDistanceSquared = DistanceSquared;
        }
    }
    return BestInstance;
}

void ATwinSceneManager::UpdateAlwaysOverlays(APlayerController* PlayerController)
{
    if (!PlayerController || !PlayerController->PlayerCameraManager) return;
    const FVector CameraLocation = PlayerController->PlayerCameraManager->GetCameraLocation();
    const float HorizontalFovRadians = FMath::DegreesToRadians(FMath::Clamp(
        PlayerController->PlayerCameraManager->GetFOVAngle(), 5.0f, 170.0f));
    const float MaxDistanceSquared = FMath::Square(FMath::Max(100.0f, OverlayCullDistanceCm));
    int32 ViewportX = 0;
    int32 ViewportY = 0;
    PlayerController->GetViewportSize(ViewportX, ViewportY);

    TArray<TPair<float, ATwinInstance*>> Candidates;
    for (const TPair<FString, ATwinInstance*>& Pair : InstanceRegistry)
    {
        ATwinInstance* Instance = Pair.Value;
        if (!Instance || !IsValid(Instance) || !Instance->HasAlwaysOverlay())
        {
            if (Instance && IsValid(Instance)) Instance->RefreshAlwaysOverlay(CameraLocation, false);
            continue;
        }
        const FVector Anchor = Instance->GetOverlayAnchorWorldLocation();
        const float DistanceSquared = FVector::DistSquared(CameraLocation, Anchor);
        FVector2D ScreenPosition;
        const bool bProjected = PlayerController->ProjectWorldLocationToScreen(Anchor, ScreenPosition, true);
        const bool bOnScreen = bProjected && ScreenPosition.X >= 0.0f && ScreenPosition.Y >= 0.0f
            && ScreenPosition.X <= ViewportX && ScreenPosition.Y <= ViewportY;
        if (DistanceSquared <= MaxDistanceSquared && bOnScreen)
        {
            Candidates.Emplace(DistanceSquared, Instance);
        }
        else
        {
            Instance->RefreshAlwaysOverlay(CameraLocation, false);
        }
    }

    Candidates.Sort([](const TPair<float, ATwinInstance*>& A, const TPair<float, ATwinInstance*>& B)
    {
        return A.Key < B.Key;
    });
    const int32 VisibleCount = FMath::Min(MaxVisibleAlwaysOverlays, Candidates.Num());
    for (int32 Index = 0; Index < Candidates.Num(); ++Index)
    {
        ATwinInstance* Instance = Candidates[Index].Value;
        if (Index >= VisibleCount)
        {
            Instance->RefreshAlwaysOverlay(CameraLocation, false);
            continue;
        }

        const float DistanceCm = FMath::Sqrt(Candidates[Index].Key);
        const float WorldViewportWidthCm = 2.0f * DistanceCm
            * FMath::Tan(HorizontalFovRadians * 0.5f);
        const float DesiredWorldWidthCm = WorldViewportWidthCm
            * (FMath::Max(1.0f, AlwaysOverlayTargetScreenWidthPx) / FMath::Max(1, ViewportX));
        const float RenderWidthPx = FMath::Max(1.0f, Instance->GetOverlayRenderWidthPixels());
        const float MinScale = FMath::Min(AlwaysOverlayMinWorldScale, AlwaysOverlayMaxWorldScale);
        const float MaxScale = FMath::Max(AlwaysOverlayMinWorldScale, AlwaysOverlayMaxWorldScale);
        const float WorldScale = FMath::Clamp(DesiredWorldWidthCm / RenderWidthPx, MinScale, MaxScale);
        Instance->RefreshAlwaysOverlay(CameraLocation, true, WorldScale);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 快照接口 URL
// ═══════════════════════════════════════════════════════════════════════════

FString ATwinSceneManager::BuildSnapshotsUrl() const
{
    FString Url = FString::Printf(TEXT("%s/api/v2/state/snapshots"), *BackendBaseUrl);
    // SceneId 非空时锁定场景；留空则由后端用当前激活数据集
    if (!SceneId.IsEmpty())
    {
        Url += FString::Printf(TEXT("?scene=%s"), *SceneId);
    }
    return Url;
}

FString ATwinSceneManager::BuildSnapshotChangesUrl() const
{
    FString Url = FString::Printf(TEXT("%s/api/v2/state/snapshot_changes"), *BackendBaseUrl);
    FString Separator = TEXT("?");
    if (!SceneId.IsEmpty())
    {
        Url += FString::Printf(
            TEXT("%sscene=%s"),
            *Separator,
            *FGenericPlatformHttp::UrlEncode(SceneId));
        Separator = TEXT("&");
    }
    if (!IncrementalSnapshotCursor.IsEmpty())
    {
        Url += FString::Printf(
            TEXT("%scursor=%s"),
            *Separator,
            *FGenericPlatformHttp::UrlEncode(IncrementalSnapshotCursor));
    }
    return Url;
}

void ATwinSceneManager::AddUEProjectHeaders(TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest) const
{
    HttpRequest->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), UEProjectId);
    HttpRequest->SetHeader(TEXT("X-OntoTwin-UE-Project-Name"), UEProjectName);
}

void ATwinSceneManager::SetPollTimerInterval(float IntervalSeconds, float FirstDelaySeconds)
{
    UWorld* World = GetWorld();
    if (!World) return;

    const float SafeInterval = FMath::Max(0.1f, IntervalSeconds);
    World->GetTimerManager().ClearTimer(PollTimerHandle);
    World->GetTimerManager().SetTimer(
        PollTimerHandle,
        this,
        &ATwinSceneManager::PollBackend,
        SafeInterval,
        true,
        FMath::Max(0.0f, FirstDelaySeconds));
}

void ATwinSceneManager::BindCurrentUEProjectToActiveDataset()
{
#if WITH_EDITOR
    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Body->SetStringField(TEXT("ue_project_name"), UEProjectName);

    FString BodyStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/ue/bind_active_project"), *BackendBaseUrl));
    HttpRequest->SetVerb(TEXT("POST"));
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->SetContentAsString(BodyStr);
    HttpRequest->OnProcessRequestComplete().BindLambda([](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
    {
        const int32 Code = Resp.IsValid() ? Resp->GetResponseCode() : -1;
        const bool bSuccess = bOk && Resp.IsValid() && Code == 200;
        if (bSuccess)
        {
            UE_LOG(LogTemp, Log, TEXT("[UE绑定] 绑定当前 UE 工程到激活数据集成功 (code=%d)"), Code);
        }
        else
        {
            UE_LOG(LogTemp, Error, TEXT("[UE绑定] 绑定当前 UE 工程到激活数据集失败 (code=%d)"), Code);
        }
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 8.0f, bSuccess ? FColor::Green : FColor::Red,
                bSuccess ? TEXT("已绑定当前 UE 工程到激活数据集") : TEXT("UE 工程绑定失败，请查看 Output Log"));
        }
    });
    HttpRequest->ProcessRequest();
#else
    UE_LOG(LogTemp, Warning, TEXT("[UE绑定] 仅在编辑器模式下可用"));
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// 轮询逻辑
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::PollBackend()
{
    if (bRequestInFlight) return;

    const bool bUseIncremental = bEnableIncrementalSnapshots && !bIncrementalSnapshotsFellBackToFull;
    if (!bUseIncremental)
    {
        UE_LOG(LogTemp, Log,
               TEXT("[孪生管理器] 全量轮询中... 场景=%s | 现有实例数=%d"),
               SceneId.IsEmpty() ? TEXT("(跟随后端)") : *SceneId, InstanceRegistry.Num());
    }

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
        FHttpModule::Get().CreateRequest();

    const FString Url = bUseIncremental ? BuildSnapshotChangesUrl() : BuildSnapshotsUrl();
    HttpRequest->SetURL(Url);
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);

    if (bUseIncremental)
    {
        HttpRequest->OnProcessRequestComplete().BindUObject(
            this, &ATwinSceneManager::OnIncrementalPollResponse);
    }
    else
    {
        HttpRequest->OnProcessRequestComplete().BindUObject(
            this, &ATwinSceneManager::OnPollResponse);
    }

    bRequestInFlight = true;
    HttpRequest->ProcessRequest();
}

void ATwinSceneManager::OnPollResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
    bRequestInFlight = false;

    int32 ResponseCode = Response.IsValid() ? Response->GetResponseCode() : -1;
    if (!bWasSuccessful || !Response.IsValid() || ResponseCode != 200)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生管理器] ❌ 请求失败 | Code=%d | bSuccessful=%s"),
               ResponseCode, bWasSuccessful ? TEXT("true") : TEXT("false"));
        ConsecutiveFailures++;
        if (ConsecutiveFailures >= OfflineThreshold)
        {
            UE_LOG(LogTemp, Warning,
                   TEXT("[孪生管理器] 后端连续 %d 次无响应，标记全部实例离线"),
                   ConsecutiveFailures);
        }
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] ✅ 收到快照响应 Code=200, Body长度=%d"), Response->GetContentLength());

    ConsecutiveFailures = 0;

    // ── 解析 JSON 数组 ───────────────────────────────────────────────────
    FString Body = Response->GetContentAsString();
    TArray<TSharedPtr<FJsonValue>> SnapshotArray;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Body);

    if (!FJsonSerializer::Deserialize(Reader, SnapshotArray))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] ❌ 快照 JSON 数组解析失败:\n%s"), *Body);
        return;
    }

    if (SnapshotArray.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] ⚠️ 收到 200 OK，但快照数组为空 (当前无实例)"));
    }

    // ── 收集后端当前存在的实例 ID ─────────────────────────────────────────
    TSet<FString> BackendInstanceIds;

    for (const auto& Val : SnapshotArray)
    {
        const TSharedPtr<FJsonObject>* SnapObj;
        if (!Val->TryGetObject(SnapObj)) continue;

        FString InstanceId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstanceId)) continue;

        BackendInstanceIds.Add(InstanceId);
        ProcessSnapshot(*SnapObj);
    }

    // ── 检测后端已删除的实例 → 在场景中销毁（FR-4：全部动态 spawn，一律销毁）─────
    TArray<FString> ToRemove;
    for (auto& Pair : InstanceRegistry)
    {
        if (!BackendInstanceIds.Contains(Pair.Key))
        {
            ToRemove.Add(Pair.Key);
        }
    }
    for (const FString& Id : ToRemove)
    {
        DestroyTwinInstance(Id);
    }
}

void ATwinSceneManager::FallBackToFullSnapshots(const FString& Reason)
{
    if (bIncrementalSnapshotsFellBackToFull)
    {
        return;
    }
    bIncrementalSnapshotsFellBackToFull = true;
    IncrementalSnapshotCursor.Empty();
    UE_LOG(LogTemp, Warning,
           TEXT("[孪生管理器] 增量快照不可用，当前会话回退全量接口: %s"), *Reason);
}

void ATwinSceneManager::OnIncrementalPollResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
    bRequestInFlight = false;

    const int32 ResponseCode = Response.IsValid() ? Response->GetResponseCode() : -1;
    if (!bWasSuccessful || !Response.IsValid() || ResponseCode != 200)
    {
        if (Response.IsValid() && (ResponseCode == 400 || ResponseCode == 404 || ResponseCode == 501))
        {
            ConsecutiveFailures = 0;
            FallBackToFullSnapshots(FString::Printf(TEXT("HTTP %d"), ResponseCode));
            PollBackend();
            return;
        }

        UE_LOG(LogTemp, Warning,
               TEXT("[孪生管理器] 增量快照请求失败 | Code=%d | bSuccessful=%s"),
               ResponseCode, bWasSuccessful ? TEXT("true") : TEXT("false"));
        ConsecutiveFailures++;
        return;
    }

    const FString Body = Response->GetContentAsString();
    TSharedPtr<FJsonObject> Envelope;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Body);
    if (!FJsonSerializer::Deserialize(Reader, Envelope) || !Envelope.IsValid())
    {
        FallBackToFullSnapshots(TEXT("响应不是 JSON 对象"));
        PollBackend();
        return;
    }

    FString SchemaVersion;
    FString Mode;
    FString NewCursor;
    const TArray<TSharedPtr<FJsonValue>>* Upserts = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* DeletedIds = nullptr;
    const bool bEnvelopeValid =
        Envelope->TryGetStringField(TEXT("schemaVersion"), SchemaVersion)
        && SchemaVersion == TEXT("snapshot_delta_v1")
        && Envelope->TryGetStringField(TEXT("mode"), Mode)
        && (Mode == TEXT("reset") || Mode == TEXT("delta"))
        && Envelope->TryGetStringField(TEXT("cursor"), NewCursor)
        && !NewCursor.IsEmpty()
        && Envelope->TryGetArrayField(TEXT("upserts"), Upserts)
        && Envelope->TryGetArrayField(TEXT("deletedIds"), DeletedIds);
    if (!bEnvelopeValid)
    {
        FallBackToFullSnapshots(TEXT("schemaVersion 或核心字段不兼容"));
        PollBackend();
        return;
    }

    ConsecutiveFailures = 0;
    double RevisionNumber = 0.0;
    Envelope->TryGetNumberField(TEXT("revision"), RevisionNumber);

    if (Mode == TEXT("reset"))
    {
        TSet<FString> BackendInstanceIds;
        bool bAllApplied = true;
        for (const TSharedPtr<FJsonValue>& Value : *Upserts)
        {
            const TSharedPtr<FJsonObject>* Snapshot = nullptr;
            FString InstanceId;
            if (!Value.IsValid()
                || !Value->TryGetObject(Snapshot)
                || !Snapshot
                || !Snapshot->IsValid()
                || !(*Snapshot)->TryGetStringField(TEXT("instanceId"), InstanceId)
                || InstanceId.IsEmpty())
            {
                bAllApplied = false;
                continue;
            }
            BackendInstanceIds.Add(InstanceId);
            bAllApplied = ProcessSnapshot(*Snapshot, false) && bAllApplied;
        }

        if (!bAllApplied)
        {
            IncrementalSnapshotCursor.Empty();
            UE_LOG(LogTemp, Error, TEXT("[孪生管理器] reset 基线应用不完整，下轮重新请求基线"));
            return;
        }

        TArray<FString> ToRemove;
        for (const auto& Pair : InstanceRegistry)
        {
            if (!BackendInstanceIds.Contains(Pair.Key))
            {
                ToRemove.Add(Pair.Key);
            }
        }
        for (const FString& InstanceId : ToRemove)
        {
            DestroyTwinInstance(InstanceId);
        }

        IncrementalSnapshotCursor = NewCursor;
        UE_LOG(LogTemp, Log,
               TEXT("[孪生管理器] 增量基线已恢复 | revision=%lld | instances=%d | removed=%d | bytes=%d"),
               static_cast<int64>(RevisionNumber), Upserts->Num(), ToRemove.Num(), Response->GetContentLength());
        return;
    }

    for (const TSharedPtr<FJsonValue>& Value : *DeletedIds)
    {
        FString InstanceId;
        if (Value.IsValid() && Value->TryGetString(InstanceId) && !InstanceId.IsEmpty())
        {
            DestroyTwinInstance(InstanceId);
        }
    }

    bool bAllApplied = true;
    for (const TSharedPtr<FJsonValue>& Value : *Upserts)
    {
        const TSharedPtr<FJsonObject>* Snapshot = nullptr;
        if (!Value.IsValid() || !Value->TryGetObject(Snapshot) || !Snapshot || !Snapshot->IsValid())
        {
            bAllApplied = false;
            continue;
        }
        bAllApplied = ProcessSnapshot(*Snapshot, true) && bAllApplied;
    }

    if (!bAllApplied)
    {
        UE_LOG(LogTemp, Error,
               TEXT("[孪生管理器] delta 应用不完整，保留旧 cursor 以便幂等重试"));
        return;
    }

    IncrementalSnapshotCursor = NewCursor;
    if (Upserts->Num() > 0 || DeletedIds->Num() > 0)
    {
        UE_LOG(LogTemp, Log,
               TEXT("[孪生管理器] 增量已应用 | revision=%lld | upserts=%d | deleted=%d | bytes=%d"),
               static_cast<int64>(RevisionNumber), Upserts->Num(), DeletedIds->Num(), Response->GetContentLength());
    }
}

void ATwinSceneManager::ConnectRealtimeWebSocket()
{
    if (bRealtimeClosing)
    {
        return;
    }
    if (!bEnableRealtimeWebSocket)
    {
        RealtimeConnectionState = TEXT("disabled");
        return;
    }
    if (RealtimeWebSocketUrl.IsEmpty())
    {
        RealtimeConnectionState = TEXT("error");
        RealtimeLastError = TEXT("WebSocket URL is empty");
        return;
    }

    bRealtimeReconnectScheduled = false;
    RealtimeConnectionState = TEXT("connecting");
    const int32 ThisGeneration = ++RealtimeConnectionGeneration;

    if (RealtimeSocket.IsValid())
    {
        if (RealtimeSocket->IsConnected())
        {
            RealtimeSocket->Close();
        }
        RealtimeSocket.Reset();
    }

    // 与现场 MetaverseClient 保持一致。部分 libwebsockets 构建需要一个客户端协议名。
    RealtimeSocket = FWebSocketsModule::Get().CreateWebSocket(RealtimeWebSocketUrl, TEXT("ws"));

    RealtimeSocket->OnConnected().AddWeakLambda(this, [this, ThisGeneration]()
    {
        if (ThisGeneration != RealtimeConnectionGeneration) return;
        RealtimeConnectionState = TEXT("connected");
        RealtimeLastError.Empty();
        UE_LOG(LogTemp, Log, TEXT("[OntoTwinWS] 已连接 %s"), *RealtimeWebSocketUrl);
    });

    RealtimeSocket->OnConnectionError().AddWeakLambda(
        this, [this, ThisGeneration](const FString& Error)
    {
        if (ThisGeneration != RealtimeConnectionGeneration) return;
        RealtimeConnectionState = TEXT("error");
        RealtimeLastError = Error;
        UE_LOG(LogTemp, Warning, TEXT("[OntoTwinWS] 连接错误: %s"), *Error);
        ScheduleRealtimeReconnect();
    });

    RealtimeSocket->OnClosed().AddWeakLambda(
        this, [this, ThisGeneration](int32 StatusCode, const FString& Reason, bool bWasClean)
    {
        if (ThisGeneration != RealtimeConnectionGeneration) return;
        RealtimeConnectionState = TEXT("disconnected");
        RealtimeLastError = Reason;
        UE_LOG(LogTemp, Warning,
            TEXT("[OntoTwinWS] 已断开 code=%d clean=%s reason=%s"),
            StatusCode, bWasClean ? TEXT("true") : TEXT("false"), *Reason);
        if (!bRealtimeClosing)
        {
            ScheduleRealtimeReconnect();
        }
    });

    RealtimeSocket->OnMessage().AddWeakLambda(
        this, [this, ThisGeneration](const FString& Message)
    {
        if (ThisGeneration != RealtimeConnectionGeneration) return;
        HandleRealtimeMessage(Message);
    });

    RealtimeSocket->Connect();
}

void ATwinSceneManager::ScheduleRealtimeReconnect()
{
    if (bRealtimeClosing || bRealtimeReconnectScheduled || !GetWorld())
    {
        return;
    }

    bRealtimeReconnectScheduled = true;
    RealtimeConnectionState = TEXT("reconnecting");
    GetWorldTimerManager().SetTimer(
        RealtimeReconnectTimerHandle,
        FTimerDelegate::CreateWeakLambda(this, [this]()
        {
            bRealtimeReconnectScheduled = false;
            ConnectRealtimeWebSocket();
        }),
        FMath::Max(0.5f, RealtimeReconnectSeconds),
        false);
}

void ATwinSceneManager::HandleRealtimeMessage(const FString& Message)
{
    TSharedPtr<FJsonObject> Frame;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Message);
    if (!FJsonSerializer::Deserialize(Reader, Frame) || !Frame.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("[OntoTwinWS] 无法解析状态帧"));
        return;
    }

    const TArray<TSharedPtr<FJsonValue>>* Targets = nullptr;
    if (!Frame->TryGetArrayField(TEXT("targets"), Targets))
    {
        UE_LOG(LogTemp, Warning, TEXT("[OntoTwinWS] 状态帧缺少 targets"));
        return;
    }

    int32 AppliedCount = 0;
    TMap<FString, FString> FrameTargetStates;
    TSet<FString> FrameAppliedInstanceIds;
    for (const TSharedPtr<FJsonValue>& Value : *Targets)
    {
        const TSharedPtr<FJsonObject>* Target = nullptr;
        if (!Value.IsValid() || !Value->TryGetObject(Target) || !Target || !Target->IsValid())
        {
            continue;
        }

        FString InstanceId;
        FString State;
        if (!(*Target)->TryGetStringField(TEXT("key"), InstanceId) || InstanceId.IsEmpty())
        {
            continue;
        }

        (*Target)->TryGetStringField(TEXT("state"), State);
        if (State.IsEmpty())
        {
            State = TEXT("active");
        }
        FrameTargetStates.Add(InstanceId, State.ToLower());
        if (State.Equals(TEXT("lost"), ESearchCase::IgnoreCase))
        {
            continue;
        }

        double X = 0.0;
        double Y = 0.0;
        double Heading = 0.0;
        if (!(*Target)->TryGetNumberField(TEXT("x"), X)
            || !(*Target)->TryGetNumberField(TEXT("y"), Y)
            || !(*Target)->TryGetNumberField(TEXT("heading"), Heading))
        {
            continue;
        }

        ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
        if (Found && *Found && IsValid(*Found))
        {
            (*Found)->ApplyRealtimeSpatial(X, Y, Heading, RealtimeSpatialHoldSeconds);
            RealtimeMissingInstanceWarnings.Remove(InstanceId);
            FrameAppliedInstanceIds.Add(InstanceId);
            ++AppliedCount;
        }
        else if (!RealtimeMissingInstanceWarnings.Contains(InstanceId))
        {
            RealtimeMissingInstanceWarnings.Add(InstanceId);
            UE_LOG(LogTemp, Warning,
                TEXT("[OntoTwinWS] 收到 %s，但 HTTP 档案尚未创建对应 TwinInstance"),
                *InstanceId);
        }
    }

    double SourceTimestampMs = 0.0;
    if (Frame->TryGetNumberField(TEXT("source_timestamp_ms"), SourceTimestampMs)
        || Frame->TryGetNumberField(TEXT("timestamp_ms"), SourceTimestampMs))
    {
        RealtimeLastSourceTimestampMs = FMath::Max<int64>(0, static_cast<int64>(SourceTimestampMs));
    }
    RealtimeTargetStates = MoveTemp(FrameTargetStates);
    RealtimeAppliedInstanceIds = MoveTemp(FrameAppliedInstanceIds);
    RealtimeLastFramePlatformSeconds = FPlatformTime::Seconds();
    ++RealtimeFrameCount;
    if (RealtimeFrameCount == 1 || RealtimeFrameCount % 300 == 0)
    {
        UE_LOG(LogTemp, Log,
            TEXT("[OntoTwinWS] 状态帧=%lld targets=%d applied=%d"),
            RealtimeFrameCount, Targets->Num(), AppliedCount);
    }
}

TSharedRef<FJsonObject> ATwinSceneManager::BuildRealtimeChannelHealth() const
{
    const TSharedRef<FJsonObject> Health = MakeShared<FJsonObject>();
    Health->SetBoolField(TEXT("enabled"), bEnableRealtimeWebSocket);
    Health->SetStringField(TEXT("connection_state"),
        bEnableRealtimeWebSocket ? RealtimeConnectionState : TEXT("disabled"));

    const double LastFrameAgeMs = RealtimeLastFramePlatformSeconds >= 0.0
        ? FMath::Max(0.0, (FPlatformTime::Seconds() - RealtimeLastFramePlatformSeconds) * 1000.0)
        : -1.0;
    const bool bFrameFresh = bEnableRealtimeWebSocket
        && RealtimeConnectionState == TEXT("connected")
        && LastFrameAgeMs >= 0.0
        && LastFrameAgeMs <= FMath::Max(0.1f, RealtimeSpatialHoldSeconds) * 1000.0;

    Health->SetStringField(TEXT("active_source"), bFrameFresh ? TEXT("websocket") : TEXT("http_snapshot"));
    if (LastFrameAgeMs >= 0.0)
    {
        Health->SetNumberField(TEXT("last_frame_age_ms"), LastFrameAgeMs);
    }
    else
    {
        Health->SetField(TEXT("last_frame_age_ms"), MakeShared<FJsonValueNull>());
    }
    Health->SetNumberField(TEXT("frame_count"), static_cast<double>(RealtimeFrameCount));
    Health->SetNumberField(TEXT("source_timestamp_ms"), static_cast<double>(RealtimeLastSourceTimestampMs));
    Health->SetNumberField(TEXT("target_count"), RealtimeTargetStates.Num());
    Health->SetNumberField(TEXT("applied_target_count"), RealtimeAppliedInstanceIds.Num());
    Health->SetStringField(TEXT("error"), RealtimeLastError);

    TArray<FString> InstanceIds;
    RealtimeTargetStates.GetKeys(InstanceIds);
    InstanceIds.Sort();
    TArray<TSharedPtr<FJsonValue>> Targets;
    Targets.Reserve(InstanceIds.Num());
    for (const FString& InstanceId : InstanceIds)
    {
        const TSharedRef<FJsonObject> Target = MakeShared<FJsonObject>();
        Target->SetStringField(TEXT("instance_id"), InstanceId);
        Target->SetStringField(TEXT("state"), RealtimeTargetStates.FindRef(InstanceId));
        Target->SetBoolField(TEXT("applied"), RealtimeAppliedInstanceIds.Contains(InstanceId));
        Targets.Add(MakeShared<FJsonValueObject>(Target));
    }
    Health->SetArrayField(TEXT("targets"), Targets);
    return Health;
}

// ═══════════════════════════════════════════════════════════════════════════
// 实例处理
// ═══════════════════════════════════════════════════════════════════════════

bool ATwinSceneManager::ProcessSnapshot(const TSharedPtr<FJsonObject>& Snapshot, bool bIsDelta)
{
    if (!Snapshot.IsValid())
    {
        return false;
    }

    FString InstanceId;
    if (!Snapshot->TryGetStringField(TEXT("instanceId"), InstanceId) || InstanceId.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 忽略缺少 instanceId 的快照"));
        return false;
    }

    // ── 已存在：更新状态 ─────────────────────────────────────────────────
    ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
    if (Found && *Found && IsValid(*Found))
    {
        (*Found)->ApplySnapshot(Snapshot, bIsDelta);
        return true;
    }

    // ── 不存在：创建新实例 ───────────────────────────────────────────────
    ATwinInstance* NewInst = SpawnTwinInstance(InstanceId, Snapshot);
    if (NewInst)
    {
        InstanceRegistry.Add(InstanceId, NewInst);
        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 新增实例: %s"), *InstanceId);
        return true;
    }
    return false;
}

ATwinInstance* ATwinSceneManager::SpawnTwinInstance(
    const FString& InstanceId,
    const TSharedPtr<FJsonObject>& Snapshot)
{
    UWorld* World = GetWorld();
    if (!World) return nullptr;

    // ── 解析 asset_id（UE 内容路径） ─────────────────────────────────────
    FString AssetPathStr;
    const TSharedPtr<FJsonObject>* InterfacesObj;
    if (Snapshot->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
    {
        const TSharedPtr<FJsonObject>* RepObj;
        if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
        {
            (*RepObj)->TryGetStringField(TEXT("asset_id"), AssetPathStr);
        }
    }

    // ── 解析初始位置 ─────────────────────────────────────────────────────
    FVector SpawnLocation = FVector::ZeroVector;
    if (Snapshot->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
    {
        const TSharedPtr<FJsonObject>* SpatialObj;
        if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Spatial"), SpatialObj))
        {
            double tx = 0, ty = 0, tz = 0;
            (*SpatialObj)->TryGetNumberField(TEXT("translation_x"), tx);
            (*SpatialObj)->TryGetNumberField(TEXT("translation_y"), ty);
            (*SpatialObj)->TryGetNumberField(TEXT("translation_z"), tz);
            SpawnLocation = FVector(tx, ty, tz);
        }
    }

    // ── Spawn ATwinInstance ──────────────────────────────────────────────
    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = FName(*FString::Printf(TEXT("Twin_%s"), *InstanceId));

    UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();

    ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
        SpawnClass,
        SpawnLocation,
        FRotator::ZeroRotator,
        SpawnParams
    );

    if (!Inst)
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] Spawn 失败: %s"), *InstanceId);
        return nullptr;
    }

    // ── 设置标签和名称 ───────────────────────────────────────────────────
    FString DisplayName;
    if (!Snapshot->TryGetStringField(TEXT("displayName"), DisplayName) || DisplayName.IsEmpty())
    {
        DisplayName = InstanceId;
    }
#if WITH_EDITOR
    Inst->SetActorLabel(DisplayName);
#endif
    Inst->Tags.Add(FName(*InstanceId));

    // ── 放入世界大纲特定文件夹下 ─────────────────────────────────────────
#if WITH_EDITOR
    Inst->SetFolderPath(BuildTwinFolderPath(Snapshot, TEXT("TwinInstances")));
#endif

    // ── 初始化孪生实例 ───────────────────────────────────────────────────
    Inst->InitializeTwin(InstanceId, AssetPathStr, BackendBaseUrl);

    // ── 首次应用快照 ─────────────────────────────────────────────────────
    Inst->ApplySnapshot(Snapshot);

    return Inst;
}

void ATwinSceneManager::DestroyTwinInstance(const FString& InstanceId)
{
    ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
    if (Found && *Found && IsValid(*Found))
    {
        if (OverlaySelectedInstance == *Found)
        {
            ClearOverlaySelection();
        }
        if (RuntimeSelectedInstance == *Found)
        {
            ClearRuntimeSelection(false);
        }

        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 销毁实例: %s"), *InstanceId);
        (*Found)->Destroy();
    }
    InstanceRegistry.Remove(InstanceId);
}

// ═══════════════════════════════════════════════════════════════════════════
// Runtime Editor（打包 exe 内轻量编辑模式）
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::ToggleRuntimeEditMode()
{
    if (!bEnableRuntimeEditor)
    {
        RuntimeStatusMessage = TEXT("Runtime Editor disabled on this manager");
        UpdateRuntimeEditorPanel();
        return;
    }

    if (!bRuntimeEditMode && InteractionManager && InteractionManager->IsRoamingActive())
    {
        RuntimeStatusMessage = TEXT("Exit character roaming before entering Runtime Editor");
        InteractionManager->NotifyRuntimeEditorBlocked();
        UpdateRuntimeEditorPanel();
        return;
    }

    if (bRuntimeEditMode)
    {
        ExitRuntimeEditMode();
    }
    else
    {
        EnterRuntimeEditMode();
    }
}

void ATwinSceneManager::RequestRuntimeEditToggle()
{
    UWorld* World = GetWorld();
    const float Now = World ? World->GetTimeSeconds() : 0.0f;
    if (Now - RuntimeLastToggleInputTime < 0.15f)
    {
        return;
    }

    RuntimeLastToggleInputTime = Now;
    ToggleRuntimeEditMode();
}

void ATwinSceneManager::EnterRuntimeEditMode()
{
    if (bRuntimeEditMode || !bEnableRuntimeEditor)
    {
        return;
    }

    bRuntimeEditMode = true;
    RuntimeStatusMessage = TEXT("Runtime edit mode enabled");
    SetPollTimerInterval(EditModePollInterval, EditModePollInterval);

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (PC)
    {
        bRuntimePreviousMouseCursor = PC->bShowMouseCursor;
        if (bEnableRuntimeEditorFreeCamera && !StartRuntimeEditorCamera(PC))
        {
            RuntimeStatusMessage = TEXT("Runtime edit enabled; free camera unavailable");
        }
        PC->bShowMouseCursor = true;

        FInputModeGameAndUI InputMode;
        InputMode.SetHideCursorDuringCapture(false);
        InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        PC->SetInputMode(InputMode);
    }

    EnsureRuntimeGizmo();
    ShowRuntimeEditorPanel();
    CheckRuntimeBindingStatus();
    UpdateRuntimeEditorPanel();
}

void ATwinSceneManager::ExitRuntimeEditMode()
{
    if (!bRuntimeEditMode)
    {
        return;
    }

    if (bRuntimeEditDirty)
    {
        RuntimeStatusMessage = TEXT("Save or cancel the dirty edit before leaving edit mode");
        if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
        {
            RuntimeEditorPanel->ShowToast(
                TEXT("Save or cancel the current change first"),
                EOntoTwinRuntimeToastType::Warning);
        }
        UpdateRuntimeEditorPanel();
        return;
    }

    ClearRuntimeSelection(false);
    HideRuntimeEditorPanel();

    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        RuntimeGizmo->SetGizmoEnabled(false);
    }

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (PC)
    {
        StopRuntimeEditorCamera(PC);
        PC->bShowMouseCursor = bRuntimePreviousMouseCursor;
        FInputModeGameOnly InputMode;
        PC->SetInputMode(InputMode);
    }

    bRuntimeEditMode = false;
    RuntimeStatusMessage = TEXT("Runtime edit mode disabled");
    SetPollTimerInterval(PollInterval, PollInterval);
}

void ATwinSceneManager::TickRuntimeEditor(float DeltaTime)
{
    if (!bEnableRuntimeEditor)
    {
        return;
    }

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC)
    {
        return;
    }

    const bool bPrimaryTogglePressed = PC->WasInputKeyJustPressed(ToggleEditKey);
    const bool bAlternateTogglePressed =
        AlternateToggleEditKey != EKeys::Invalid &&
        AlternateToggleEditKey != ToggleEditKey &&
        PC->WasInputKeyJustPressed(AlternateToggleEditKey);
    if (bPrimaryTogglePressed || bAlternateTogglePressed)
    {
        RequestRuntimeEditToggle();
        return;
    }

    if (!bRuntimeEditMode)
    {
        return;
    }

    const bool bCtrlDown = PC->IsInputKeyDown(EKeys::LeftControl) || PC->IsInputKeyDown(EKeys::RightControl);
    if (bCtrlDown && PC->WasInputKeyJustPressed(SaveKey))
    {
        SaveRuntimeEdit();
    }
    if (PC->WasInputKeyJustPressed(CancelKey))
    {
        CancelRuntimeEdit();
    }

    const bool bPointerOverRuntimePanel =
        RuntimeEditorPanel && IsValid(RuntimeEditorPanel) && RuntimeEditorPanel->IsPointerOverPanel();

    TickRuntimeEditorCamera(PC, DeltaTime, bPointerOverRuntimePanel);

    RuntimeHoverPart = ERuntimeDragPart::None;
    if (!bRuntimeDragging && !bPointerOverRuntimePanel && RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance))
    {
        FHitResult HoverHit;
        if (TraceRuntimeCursor(HoverHit) && RuntimeGizmo && IsValid(RuntimeGizmo))
        {
            const EOntoTwinRuntimeGizmoPart HoverGizmoPart = RuntimeGizmo->GetPartForComponent(HoverHit.GetComponent());
            if (HoverGizmoPart == EOntoTwinRuntimeGizmoPart::MoveXY)
            {
                RuntimeHoverPart = ERuntimeDragPart::MoveXY;
            }
            else if (HoverGizmoPart == EOntoTwinRuntimeGizmoPart::MoveZ)
            {
                RuntimeHoverPart = ERuntimeDragPart::MoveZ;
            }
            else if (HoverGizmoPart == EOntoTwinRuntimeGizmoPart::RotateYaw)
            {
                RuntimeHoverPart = ERuntimeDragPart::RotateYaw;
            }
        }
    }

    if (!bPointerOverRuntimePanel && PC->WasInputKeyJustPressed(EKeys::LeftMouseButton))
    {
        FHitResult Hit;
        if (TraceRuntimeCursor(Hit))
        {
            UPrimitiveComponent* HitComponent = Hit.GetComponent();
            if (RuntimeGizmo && IsValid(RuntimeGizmo))
            {
                const EOntoTwinRuntimeGizmoPart GizmoPart = RuntimeGizmo->GetPartForComponent(HitComponent);
                if (GizmoPart == EOntoTwinRuntimeGizmoPart::MoveXY)
                {
                    BeginRuntimeGizmoDrag(ERuntimeDragPart::MoveXY);
                }
                else if (GizmoPart == EOntoTwinRuntimeGizmoPart::MoveZ)
                {
                    BeginRuntimeGizmoDrag(ERuntimeDragPart::MoveZ);
                }
                else if (GizmoPart == EOntoTwinRuntimeGizmoPart::RotateYaw)
                {
                    BeginRuntimeGizmoDrag(ERuntimeDragPart::RotateYaw);
                }
            }

            if (!bRuntimeDragging)
            {
                if (ATwinInstance* HitInstance = Cast<ATwinInstance>(Hit.GetActor()))
                {
                    SelectRuntimeInstance(HitInstance);
                }
            }
        }
    }

    if (bRuntimeDragging)
    {
        if (PC->IsInputKeyDown(EKeys::LeftMouseButton))
        {
            UpdateRuntimeGizmoDrag();
        }
        else
        {
            EndRuntimeGizmoDrag();
        }
    }

    if (RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance))
    {
        if (!bRuntimeEditDirty && !RuntimeSelectedInstance->bLocalOverrideLock)
        {
            RuntimeEditBaseline = RuntimeSelectedInstance->GetActorTransform();
            RuntimeEditPlaneZ = RuntimeSelectedInstance->GetActorLocation().Z;
        }

        if (RuntimeGizmo && IsValid(RuntimeGizmo))
        {
            RuntimeGizmo->UpdateForTarget(RuntimeSelectedInstance);

            const auto ToGizmoPart = [](ERuntimeDragPart Part)
            {
                if (Part == ERuntimeDragPart::MoveXY) return EOntoTwinRuntimeGizmoPart::MoveXY;
                if (Part == ERuntimeDragPart::MoveZ) return EOntoTwinRuntimeGizmoPart::MoveZ;
                if (Part == ERuntimeDragPart::RotateYaw) return EOntoTwinRuntimeGizmoPart::RotateYaw;
                return EOntoTwinRuntimeGizmoPart::None;
            };
            RuntimeGizmo->SetInteractionState(ToGizmoPart(RuntimeHoverPart), ToGizmoPart(RuntimeDragPart));

            EOntoTwinRuntimeSnapState SnapState = EOntoTwinRuntimeSnapState::None;
            if (RuntimeSnapFeedback == ERuntimeSnapFeedback::Grid)
            {
                SnapState = EOntoTwinRuntimeSnapState::Grid;
            }
            else if (RuntimeSnapFeedback == ERuntimeSnapFeedback::Wall)
            {
                SnapState = EOntoTwinRuntimeSnapState::Wall;
            }
            RuntimeGizmo->SetSnapFeedback(SnapState, RuntimeSnapFeedbackPoint);
        }
    }

    UpdateRuntimeEditorPanel();
}

bool ATwinSceneManager::StartRuntimeEditorCamera(APlayerController* PlayerController)
{
    if (!PlayerController || !GetWorld()) return false;
    if (RuntimeEditorCameraPawn && IsValid(RuntimeEditorCameraPawn)) return true;

    RuntimeEditorOriginalPawn = PlayerController->GetPawn();
    const FTransform CameraTransform = BuildRuntimeEditorCameraTransform(PlayerController);

    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = this;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    RuntimeEditorCameraPawn = GetWorld()->SpawnActor<ATwinRuntimeEditorCameraPawn>(
        ATwinRuntimeEditorCameraPawn::StaticClass(), CameraTransform, SpawnParams);
    if (!RuntimeEditorCameraPawn)
    {
        RuntimeEditorOriginalPawn = nullptr;
        UE_LOG(LogTemp, Error, TEXT("[RuntimeEditor] Failed to spawn free camera pawn"));
        return false;
    }

    RuntimeEditorCameraPawn->Configure(
        RuntimeEditorCameraMoveSpeedCmS,
        RuntimeEditorCameraLookSensitivity);
    PlayerController->Possess(RuntimeEditorCameraPawn);
    PlayerController->SetControlRotation(CameraTransform.Rotator());

    if (PlayerController->GetPawn() != RuntimeEditorCameraPawn)
    {
        RuntimeEditorCameraPawn->Destroy();
        RuntimeEditorCameraPawn = nullptr;
        RuntimeEditorOriginalPawn = nullptr;
        UE_LOG(LogTemp, Error, TEXT("[RuntimeEditor] Failed to possess free camera pawn"));
        return false;
    }

    const FVector Location = CameraTransform.GetLocation();
    const FRotator Rotation = CameraTransform.Rotator();
    UE_LOG(LogTemp, Log,
        TEXT("[RuntimeEditor] Free camera ready at (%.0f, %.0f, %.0f), pitch=%.1f yaw=%.1f"),
        Location.X, Location.Y, Location.Z, Rotation.Pitch, Rotation.Yaw);
    return true;
}

void ATwinSceneManager::StopRuntimeEditorCamera(APlayerController* PlayerController)
{
    if (!PlayerController) return;
    EndRuntimeEditorCameraLook(PlayerController);

    ATwinRuntimeEditorCameraPawn* CameraPawn = RuntimeEditorCameraPawn;
    if (CameraPawn && IsValid(CameraPawn) && PlayerController->GetPawn() == CameraPawn)
    {
        if (RuntimeEditorOriginalPawn && IsValid(RuntimeEditorOriginalPawn))
        {
            PlayerController->Possess(RuntimeEditorOriginalPawn);
        }
        else
        {
            PlayerController->UnPossess();
        }
    }

    if (CameraPawn && IsValid(CameraPawn))
    {
        CameraPawn->Destroy();
    }
    RuntimeEditorCameraPawn = nullptr;
    RuntimeEditorOriginalPawn = nullptr;
}

void ATwinSceneManager::TickRuntimeEditorCamera(
    APlayerController* PlayerController,
    float DeltaTime,
    bool bPointerOverRuntimePanel)
{
    (void)DeltaTime;
    if (!PlayerController || !RuntimeEditorCameraPawn || !IsValid(RuntimeEditorCameraPawn)
        || PlayerController->GetPawn() != RuntimeEditorCameraPawn)
    {
        return;
    }

    if (bRuntimeDragging && bRuntimeCameraRotating)
    {
        EndRuntimeEditorCameraLook(PlayerController);
    }
    if (!bRuntimeDragging && !bRuntimeCameraRotating && !bPointerOverRuntimePanel
        && PlayerController->WasInputKeyJustPressed(EKeys::RightMouseButton))
    {
        BeginRuntimeEditorCameraLook(PlayerController);
    }
    if (bRuntimeCameraRotating)
    {
        if (PlayerController->IsInputKeyDown(EKeys::RightMouseButton))
        {
            float MouseX = 0.0f;
            float MouseY = 0.0f;
            PlayerController->GetInputMouseDelta(MouseX, MouseY);
            RuntimeEditorCameraPawn->Look(FVector2D(MouseX, MouseY));
        }
        else
        {
            EndRuntimeEditorCameraLook(PlayerController);
        }
    }

    if (bRuntimeDragging) return;

    FVector2D MoveInput(
        (PlayerController->IsInputKeyDown(EKeys::D) ? 1.0f : 0.0f)
            - (PlayerController->IsInputKeyDown(EKeys::A) ? 1.0f : 0.0f),
        (PlayerController->IsInputKeyDown(EKeys::W) ? 1.0f : 0.0f)
            - (PlayerController->IsInputKeyDown(EKeys::S) ? 1.0f : 0.0f));
    MoveInput = MoveInput.GetClampedToMaxSize(1.0f);
    if (!MoveInput.IsNearlyZero())
    {
        RuntimeEditorCameraPawn->MovePlanar(MoveInput);
    }

    const float VerticalInput =
        (PlayerController->IsInputKeyDown(EKeys::E) ? 1.0f : 0.0f)
        - (PlayerController->IsInputKeyDown(EKeys::Q) ? 1.0f : 0.0f);
    if (!FMath::IsNearlyZero(VerticalInput))
    {
        RuntimeEditorCameraPawn->MoveVertical(VerticalInput);
    }

    RuntimeEditorCameraPawn->AdjustSpeed(
        PlayerController->GetInputAnalogKeyState(EKeys::MouseWheelAxis));
}

void ATwinSceneManager::BeginRuntimeEditorCameraLook(APlayerController* PlayerController)
{
    if (!PlayerController || bRuntimeCameraRotating) return;
    float MouseX = 0.0f;
    float MouseY = 0.0f;
    if (PlayerController->GetMousePosition(MouseX, MouseY))
    {
        RuntimeCameraCursorRestorePosition = FVector2D(MouseX, MouseY);
    }
    bRuntimeCameraRotating = true;
    PlayerController->bShowMouseCursor = false;
    PlayerController->SetInputMode(FInputModeGameOnly());
}

void ATwinSceneManager::EndRuntimeEditorCameraLook(APlayerController* PlayerController)
{
    if (!PlayerController || !bRuntimeCameraRotating) return;
    bRuntimeCameraRotating = false;
    PlayerController->bShowMouseCursor = true;

    FInputModeGameAndUI InputMode;
    InputMode.SetHideCursorDuringCapture(false);
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    PlayerController->SetInputMode(InputMode);
    PlayerController->SetMouseLocation(
        FMath::RoundToInt(RuntimeCameraCursorRestorePosition.X),
        FMath::RoundToInt(RuntimeCameraCursorRestorePosition.Y));
}

FTransform ATwinSceneManager::BuildRuntimeEditorCameraTransform(
    APlayerController* PlayerController) const
{
    FTransform GodViewTransform;
    if (InteractionManager && InteractionManager->GetGodViewTransform(GodViewTransform))
    {
        return GodViewTransform;
    }

    FVector ViewLocation = FVector::ZeroVector;
    FRotator ViewRotation = FRotator::ZeroRotator;
    if (PlayerController)
    {
        PlayerController->GetPlayerViewPoint(ViewLocation, ViewRotation);
        return FTransform(ViewRotation, ViewLocation);
    }

    return RuntimeEditorOriginalPawn && IsValid(RuntimeEditorOriginalPawn)
        ? RuntimeEditorOriginalPawn->GetActorTransform()
        : GetActorTransform();
}

void ATwinSceneManager::ShowRuntimeEditorPanel()
{
    if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
    {
        RuntimeEditorPanel->SetVisibility(ESlateVisibility::Visible);
        return;
    }

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC)
    {
        return;
    }

    UClass* PanelClass = RuntimeEditorPanelClass ? RuntimeEditorPanelClass.Get() : UOntoTwinRuntimeEditorPanel::StaticClass();
    RuntimeEditorPanel = CreateWidget<UOntoTwinRuntimeEditorPanel>(PC, PanelClass);
    if (!RuntimeEditorPanel)
    {
        RuntimeStatusMessage = TEXT("Failed to create runtime editor panel");
        return;
    }

    RuntimeEditorPanel->SetSceneManager(this);
    RuntimeEditorPanel->AddToViewport(1000);
    UE_LOG(LogTemp, Log, TEXT("[RuntimeEditor] 面板已创建并添加到视口"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 4.0f, FColor::Cyan, TEXT("Runtime Editor panel opened"));
    }
}

void ATwinSceneManager::HideRuntimeEditorPanel()
{
    if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
    {
        RuntimeEditorPanel->RemoveFromParent();
    }
    RuntimeEditorPanel = nullptr;
}

void ATwinSceneManager::EnsureRuntimeGizmo()
{
    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        return;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UClass* GizmoClass = RuntimeGizmoClass ? RuntimeGizmoClass.Get() : AOntoTwinRuntimeGizmo::StaticClass();

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = TEXT("OntoTwinRuntimeGizmo");
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    RuntimeGizmo = World->SpawnActor<AOntoTwinRuntimeGizmo>(GizmoClass, FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
    if (RuntimeGizmo)
    {
        RuntimeGizmo->SetGizmoEnabled(false);
    }
}

void ATwinSceneManager::UpdateRuntimeEditorPanel()
{
    if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
    {
        RuntimeEditorPanel->RefreshFromManager();
    }
}

void ATwinSceneManager::CheckRuntimeBindingStatus()
{
    if (bRuntimeBindingRequestInFlight)
    {
        return;
    }

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/ue/binding_status"), *BackendBaseUrl));
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);

    bRuntimeBindingRequestInFlight = true;
    RuntimeStatusMessage = TEXT("Checking UE project binding...");
    UpdateRuntimeEditorPanel();

    TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
        {
            ATwinSceneManager* Self = WeakThis.Get();
            if (!Self) return;

            Self->bRuntimeBindingRequestInFlight = false;
            Self->bRuntimeCanSave = false;
            Self->RuntimeBindingMode = TEXT("unknown");

            const int32 Code = Resp.IsValid() ? Resp->GetResponseCode() : -1;
            TSharedPtr<FJsonObject> Root;
            if (Resp.IsValid())
            {
                TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Resp->GetContentAsString());
                FJsonSerializer::Deserialize(Reader, Root);
            }

            FString Mode;
            FString Error;
            if (Root.IsValid())
            {
                Root->TryGetStringField(TEXT("mode"), Mode);
                Root->TryGetStringField(TEXT("error"), Error);
            }

            if (bOk && Resp.IsValid() && Code == 200)
            {
                if (Mode == TEXT("matched"))
                {
                    Self->RuntimeBindingMode = TEXT("matched");
                    Self->bRuntimeCanSave = true;
                    Self->RuntimeStatusMessage = TEXT("UE project binding matched");
                }
                else if (Mode == TEXT("unbound"))
                {
                    Self->RuntimeBindingMode = TEXT("unbound");
                    Self->RuntimeStatusMessage = TEXT("Active dataset is unbound; bind before saving");
                }
                else
                {
                    Self->RuntimeBindingMode = Mode.IsEmpty() ? TEXT("unknown") : Mode;
                    Self->RuntimeStatusMessage = TEXT("Binding status is not save-ready");
                }
            }
            else
            {
                Self->RuntimeBindingMode = Error.IsEmpty() ? TEXT("error") : Error;
                if (Error == TEXT("ue_project_mismatch"))
                {
                    Self->RuntimeStatusMessage = TEXT("UE project mismatch; save disabled");
                }
                else
                {
                    Self->RuntimeStatusMessage = FString::Printf(TEXT("Binding check failed (code=%d)"), Code);
                    if (Self->RuntimeEditorPanel && IsValid(Self->RuntimeEditorPanel))
                    {
                        Self->RuntimeEditorPanel->ShowToast(
                            TEXT("Access check failed"),
                            EOntoTwinRuntimeToastType::Error);
                    }
                }
            }

            Self->UpdateRuntimeEditorPanel();
        });

    HttpRequest->ProcessRequest();
}

void ATwinSceneManager::RetryRuntimeBindingStatus()
{
    if (!bRuntimeEditMode || bRuntimeBindingRequestInFlight)
    {
        return;
    }

    CheckRuntimeBindingStatus();
}

void ATwinSceneManager::BindCurrentRuntimeProject()
{
    if (!bRuntimeEditMode || bRuntimeBindingRequestInFlight)
    {
        return;
    }

    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Body->SetStringField(TEXT("ue_project_name"), UEProjectName);

    FString BodyStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/ue/bind_active_project"), *BackendBaseUrl));
    HttpRequest->SetVerb(TEXT("POST"));
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->SetContentAsString(BodyStr);

    bRuntimeBindingRequestInFlight = true;
    RuntimeStatusMessage = TEXT("Binding active dataset to this UE project...");
    UpdateRuntimeEditorPanel();

    TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
        {
            ATwinSceneManager* Self = WeakThis.Get();
            if (!Self) return;

            Self->bRuntimeBindingRequestInFlight = false;
            const int32 Code = Resp.IsValid() ? Resp->GetResponseCode() : -1;
            if (bOk && Resp.IsValid() && Code == 200)
            {
                Self->RuntimeBindingMode = TEXT("matched");
                Self->bRuntimeCanSave = true;
                Self->RuntimeStatusMessage = TEXT("Active dataset bound to this UE project");
                if (Self->RuntimeEditorPanel && IsValid(Self->RuntimeEditorPanel))
                {
                    Self->RuntimeEditorPanel->ShowToast(
                        TEXT("Active dataset bound"),
                        EOntoTwinRuntimeToastType::Success);
                }
            }
            else
            {
                Self->bRuntimeCanSave = false;
                Self->RuntimeBindingMode = TEXT("error");
                Self->RuntimeStatusMessage = FString::Printf(TEXT("Bind failed (code=%d)"), Code);
                if (Self->RuntimeEditorPanel && IsValid(Self->RuntimeEditorPanel))
                {
                    Self->RuntimeEditorPanel->ShowToast(
                        TEXT("Dataset binding failed"),
                        EOntoTwinRuntimeToastType::Error);
                }
            }
            Self->UpdateRuntimeEditorPanel();
        });

    HttpRequest->ProcessRequest();
}

void ATwinSceneManager::SelectRuntimeInstance(ATwinInstance* Instance)
{
    if (!Instance || !IsValid(Instance))
    {
        return;
    }

    if (RuntimeSelectedInstance == Instance)
    {
        return;
    }

    if (bRuntimeEditDirty)
    {
        RuntimeStatusMessage = TEXT("Save or cancel the current edit before selecting another instance");
        if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
        {
            RuntimeEditorPanel->ShowToast(
                TEXT("Save or cancel the current change first"),
                EOntoTwinRuntimeToastType::Warning);
        }
        UpdateRuntimeEditorPanel();
        return;
    }

    ClearRuntimeSelection(false);

    RuntimeSelectedInstance = Instance;
    RuntimeEditBaseline = Instance->GetActorTransform();
    RuntimeEditPlaneZ = Instance->GetActorLocation().Z;
    RuntimePreviousAnimState = Instance->PauseRuntimeEditorAnimation(bRuntimePreviousAnimRunning);
    Instance->bLocalOverrideLock = true;
    bRuntimeEditDirty = false;

    EnsureRuntimeGizmo();
    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        RuntimeGizmo->UpdateForTarget(Instance);
    }

    RuntimeStatusMessage = FString::Printf(TEXT("Selected %s"), *Instance->GetInstanceId());
    UpdateRuntimeEditorPanel();
}

void ATwinSceneManager::ClearRuntimeSelection(bool bRestoreBaseline)
{
    if (RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance))
    {
        if (bRestoreBaseline)
        {
            RuntimeSelectedInstance->SetActorTransform(RuntimeEditBaseline);
        }

        RuntimeSelectedInstance->bLocalOverrideLock = false;
        RuntimeSelectedInstance->ResumeRuntimeEditorAnimation(RuntimePreviousAnimState, bRuntimePreviousAnimRunning);
    }

    RuntimeSelectedInstance = nullptr;
    RuntimePreviousAnimState.Empty();
    bRuntimePreviousAnimRunning = false;
    bRuntimeEditDirty = false;
    bRuntimeEditSaving = false;
    SetRuntimeCameraLookSuppressed(false);
    bRuntimeDragging = false;
    RuntimeHoverPart = ERuntimeDragPart::None;
    RuntimeDragPart = ERuntimeDragPart::None;
    RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
    RuntimeSnapFeedbackPoint = FVector::ZeroVector;

    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        RuntimeGizmo->SetGizmoEnabled(false);
    }

    UpdateRuntimeEditorPanel();
}

bool ATwinSceneManager::TraceRuntimeCursor(FHitResult& OutHit) const
{
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    UWorld* World = GetWorld();
    if (!PC || !World)
    {
        return false;
    }

    FVector RayOrigin = FVector::ZeroVector;
    FVector RayDirection = FVector::ForwardVector;
    if (PC->DeprojectMousePositionToWorld(RayOrigin, RayDirection) &&
        RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance) &&
        RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        FCollisionQueryParams GizmoQueryParams(SCENE_QUERY_STAT(OntoTwinRuntimeGizmoTrace), true);
        GizmoQueryParams.AddIgnoredActor(RuntimeSelectedInstance);
        GizmoQueryParams.AddIgnoredActor(this);

        FHitResult GizmoHit;
        if (World->LineTraceSingleByChannel(
            GizmoHit,
            RayOrigin,
            RayOrigin + RayDirection * 1000000.0f,
            ECC_Visibility,
            GizmoQueryParams) &&
            GizmoHit.GetActor() == RuntimeGizmo &&
            RuntimeGizmo->GetPartForComponent(GizmoHit.GetComponent()) != EOntoTwinRuntimeGizmoPart::None)
        {
            OutHit = GizmoHit;
            return true;
        }
    }

    return PC->GetHitResultUnderCursor(ECC_Visibility, false, OutHit);
}

bool ATwinSceneManager::GetRuntimeCursorPointOnPlane(const FPlane& Plane, FVector& OutPoint) const
{
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC)
    {
        return false;
    }

    float MouseX = 0.0f;
    float MouseY = 0.0f;
    if (!PC->GetMousePosition(MouseX, MouseY))
    {
        return false;
    }

    FVector RayOrigin = FVector::ZeroVector;
    FVector RayDirection = FVector::ForwardVector;
    if (!PC->DeprojectScreenPositionToWorld(MouseX, MouseY, RayOrigin, RayDirection))
    {
        return false;
    }

    const FVector PlaneNormal(Plane.X, Plane.Y, Plane.Z);
    if (FMath::IsNearlyZero(FVector::DotProduct(RayDirection, PlaneNormal)))
    {
        return false;
    }

    OutPoint = FMath::LinePlaneIntersection(
        RayOrigin,
        RayOrigin + RayDirection * 1000000.0f,
        Plane);
    return true;
}

bool ATwinSceneManager::GetRuntimeCursorPlanePoint(FVector& OutPoint) const
{
    return GetRuntimeCursorPointOnPlane(
        FPlane(FVector(0.0f, 0.0f, RuntimeDragPlaneZ), FVector::UpVector),
        OutPoint);
}

void ATwinSceneManager::BeginRuntimeGizmoDrag(ERuntimeDragPart Part)
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance) || Part == ERuntimeDragPart::None)
    {
        return;
    }

    if (!RuntimeSelectedInstance->bLocalOverrideLock)
    {
        RuntimeEditBaseline = RuntimeSelectedInstance->GetActorTransform();
        RuntimeEditPlaneZ = RuntimeSelectedInstance->GetActorLocation().Z;
        RuntimePreviousAnimState = RuntimeSelectedInstance->PauseRuntimeEditorAnimation(bRuntimePreviousAnimRunning);
        RuntimeSelectedInstance->bLocalOverrideLock = true;
    }

    RuntimeDragPart = Part;
    RuntimeHoverPart = Part;
    RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
    RuntimeSnapFeedbackPoint = FVector::ZeroVector;
    RuntimeDragStartTransform = RuntimeSelectedInstance->GetActorTransform();
    RuntimeDragStartYaw = RuntimeSelectedInstance->GetActorRotation().Yaw;
    RuntimeDragPlaneZ = RuntimeEditPlaneZ;
    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        if (Part == ERuntimeDragPart::MoveXY)
        {
            RuntimeDragPlaneZ = RuntimeGizmo->GetMoveInteractionPlaneZ();
        }
        else if (Part == ERuntimeDragPart::RotateYaw)
        {
            RuntimeDragPlaneZ = RuntimeGizmo->GetRotateInteractionPlaneZ();
        }
    }
    bRuntimeDragging = true;
    SetRuntimeCameraLookSuppressed(true);

    if (Part == ERuntimeDragPart::MoveZ)
    {
        APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
        const FVector ActorLocation = RuntimeSelectedInstance->GetActorLocation();
        FVector CameraLocation = FVector::ZeroVector;
        FRotator CameraRotation = FRotator::ZeroRotator;
        if (PC)
        {
            PC->GetPlayerViewPoint(CameraLocation, CameraRotation);
        }

        FVector PlaneNormal = CameraLocation - ActorLocation;
        PlaneNormal.Z = 0.0f;
        if (!PlaneNormal.Normalize())
        {
            PlaneNormal = -CameraRotation.Vector();
            PlaneNormal.Z = 0.0f;
            if (!PlaneNormal.Normalize())
            {
                PlaneNormal = FVector::ForwardVector;
            }
        }

        RuntimeZDragPlane = FPlane(ActorLocation, PlaneNormal);
        if (!GetRuntimeCursorPointOnPlane(RuntimeZDragPlane, RuntimeZDragStartPoint))
        {
            RuntimeZDragStartPoint = ActorLocation;
        }
        return;
    }

    FVector PlanePoint = FVector::ZeroVector;
    if (GetRuntimeCursorPlanePoint(PlanePoint))
    {
        RuntimeDragStartPoint = PlanePoint;
        const FVector ToCursor = PlanePoint - RuntimeSelectedInstance->GetActorLocation();
        RuntimeDragStartAngleDeg = FMath::RadiansToDegrees(FMath::Atan2(ToCursor.Y, ToCursor.X));
    }
    else
    {
        RuntimeDragStartPoint = RuntimeSelectedInstance->GetActorLocation();
        RuntimeDragStartAngleDeg = RuntimeDragStartYaw;
    }
}

void ATwinSceneManager::UpdateRuntimeGizmoDrag()
{
    if (!bRuntimeDragging || !RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        return;
    }

    FVector NewLocation = RuntimeDragStartTransform.GetLocation();
    FRotator NewRotation = RuntimeDragStartTransform.Rotator();

    if (RuntimeDragPart == ERuntimeDragPart::MoveZ)
    {
        FVector ZPlanePoint = FVector::ZeroVector;
        if (!GetRuntimeCursorPointOnPlane(RuntimeZDragPlane, ZPlanePoint))
        {
            return;
        }

        NewLocation.Z += ZPlanePoint.Z - RuntimeZDragStartPoint.Z;
        RuntimeEditPlaneZ = NewLocation.Z;
        RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
        RuntimeSnapFeedbackPoint = FVector::ZeroVector;
    }
    else
    {
        FVector PlanePoint = FVector::ZeroVector;
        if (!GetRuntimeCursorPlanePoint(PlanePoint))
        {
            return;
        }

        if (RuntimeDragPart == ERuntimeDragPart::MoveXY)
        {
            const FVector Delta = PlanePoint - RuntimeDragStartPoint;
            NewLocation.X += Delta.X;
            NewLocation.Y += Delta.Y;
            NewLocation.Z = RuntimeEditPlaneZ;
        }
        else if (RuntimeDragPart == ERuntimeDragPart::RotateYaw)
        {
            const FVector ToCursor = PlanePoint - RuntimeDragStartTransform.GetLocation();
            if (!ToCursor.IsNearlyZero())
            {
                const float CurrentAngleDeg = FMath::RadiansToDegrees(FMath::Atan2(ToCursor.Y, ToCursor.X));
                NewRotation.Yaw = RuntimeDragStartYaw + FMath::FindDeltaAngleDegrees(RuntimeDragStartAngleDeg, CurrentAngleDeg);
                NewRotation.Pitch = RuntimeDragStartTransform.Rotator().Pitch;
                NewRotation.Roll = RuntimeDragStartTransform.Rotator().Roll;
            }
        }

        ApplyRuntimeSnaps(NewLocation, NewRotation);
    }

    RuntimeSelectedInstance->SetActorLocation(NewLocation);
    RuntimeSelectedInstance->SetActorRotation(NewRotation);
    MarkRuntimeDirtyFromTransform();

    if (RuntimeGizmo && IsValid(RuntimeGizmo))
    {
        RuntimeGizmo->UpdateForTarget(RuntimeSelectedInstance);
    }
}

void ATwinSceneManager::EndRuntimeGizmoDrag()
{
    SetRuntimeCameraLookSuppressed(false);
    bRuntimeDragging = false;
    RuntimeHoverPart = ERuntimeDragPart::None;
    RuntimeDragPart = ERuntimeDragPart::None;
    RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
    RuntimeSnapFeedbackPoint = FVector::ZeroVector;
}

void ATwinSceneManager::SetRuntimeCameraLookSuppressed(bool bSuppress)
{
    if (bRuntimeCameraLookSuppressed == bSuppress)
    {
        return;
    }

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC)
    {
        bRuntimeCameraLookSuppressed = false;
        bRuntimeLookInputWasAlreadyIgnored = false;
        return;
    }

    if (bSuppress)
    {
        bRuntimeLookInputWasAlreadyIgnored = PC->IsLookInputIgnored();
        if (!bRuntimeLookInputWasAlreadyIgnored)
        {
            PC->SetIgnoreLookInput(true);
        }
        bRuntimeCameraLookSuppressed = true;
        return;
    }

    if (!bRuntimeLookInputWasAlreadyIgnored)
    {
        PC->SetIgnoreLookInput(false);
    }
    bRuntimeCameraLookSuppressed = false;
    bRuntimeLookInputWasAlreadyIgnored = false;
}

void ATwinSceneManager::ApplyRuntimeSnaps(FVector& InOutLocation, FRotator& InOutRotation)
{
    RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
    RuntimeSnapFeedbackPoint = InOutLocation;
    InOutLocation.Z = RuntimeEditPlaneZ;

    if (bEnableGridSnap && GridSnapSizeCm > 0.0f)
    {
        const FVector BeforeGridSnap = InOutLocation;
        InOutLocation.X = FMath::GridSnap(InOutLocation.X, GridSnapSizeCm);
        InOutLocation.Y = FMath::GridSnap(InOutLocation.Y, GridSnapSizeCm);
        if (!FMath::IsNearlyEqual(BeforeGridSnap.X, InOutLocation.X, 0.01f) ||
            !FMath::IsNearlyEqual(BeforeGridSnap.Y, InOutLocation.Y, 0.01f))
        {
            RuntimeSnapFeedback = ERuntimeSnapFeedback::Grid;
            RuntimeSnapFeedbackPoint = InOutLocation;
        }
    }

    if (!bEnableWallSnap || WallTag.IsNone() || !RuntimeSelectedInstance || !GetWorld())
    {
        return;
    }

    TArray<AActor*> Walls;
    UGameplayStatics::GetAllActorsWithTag(GetWorld(), WallTag, Walls);
    if (Walls.Num() == 0)
    {
        return;
    }

    AActor* BestWall = nullptr;
    FVector BestClosest = FVector::ZeroVector;
    float BestDistSq = FMath::Square(WallSnapDistanceCm);

    for (AActor* Wall : Walls)
    {
        if (!Wall || !IsValid(Wall))
        {
            continue;
        }

        const FBox WallBounds = Wall->GetComponentsBoundingBox(true);
        if (!WallBounds.IsValid)
        {
            continue;
        }

        FVector Closest = WallBounds.GetClosestPointTo(InOutLocation);
        Closest.Z = InOutLocation.Z;

        const FVector2D Delta2D(InOutLocation.X - Closest.X, InOutLocation.Y - Closest.Y);
        const float DistSq = Delta2D.SizeSquared();
        if (DistSq <= BestDistSq)
        {
            BestDistSq = DistSq;
            BestWall = Wall;
            BestClosest = Closest;
        }
    }

    if (!BestWall)
    {
        return;
    }

    const FBox WallBounds = BestWall->GetComponentsBoundingBox(true);
    FVector Normal = InOutLocation - BestClosest;
    Normal.Z = 0.0f;
    if (!Normal.Normalize())
    {
        const FVector Center = WallBounds.GetCenter();
        Normal = InOutLocation - Center;
        Normal.Z = 0.0f;
        if (!Normal.Normalize())
        {
            Normal = FVector::ForwardVector;
        }
    }

    const FBox TargetBounds = RuntimeSelectedInstance->GetComponentsBoundingBox(true);
    const FVector TargetExtent = TargetBounds.GetExtent();
    const float TargetRadiusAlongNormal =
        FMath::Abs(Normal.X) * TargetExtent.X +
        FMath::Abs(Normal.Y) * TargetExtent.Y +
        2.0f;

    InOutLocation.X = BestClosest.X + Normal.X * TargetRadiusAlongNormal;
    InOutLocation.Y = BestClosest.Y + Normal.Y * TargetRadiusAlongNormal;
    InOutLocation.Z = RuntimeEditPlaneZ;

    const FVector Tangent(-Normal.Y, Normal.X, 0.0f);
    InOutRotation.Yaw = Tangent.Rotation().Yaw;
    RuntimeSnapFeedback = ERuntimeSnapFeedback::Wall;
    RuntimeSnapFeedbackPoint = BestClosest;
}

void ATwinSceneManager::MarkRuntimeDirtyFromTransform()
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        bRuntimeEditDirty = false;
        return;
    }

    bRuntimeEditDirty = !RuntimeSelectedInstance->GetActorTransform().Equals(RuntimeEditBaseline, 0.01f);
    RuntimeStatusMessage = bRuntimeEditDirty ? TEXT("Dirty edit; save or cancel") : TEXT("Transform matches baseline");
}

void ATwinSceneManager::SaveRuntimeEdit()
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        RuntimeStatusMessage = TEXT("Select an instance before saving");
        if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
        {
            RuntimeEditorPanel->ShowToast(TEXT("Select an instance first"), EOntoTwinRuntimeToastType::Info);
        }
        UpdateRuntimeEditorPanel();
        return;
    }
    if (!bRuntimeEditDirty)
    {
        RuntimeStatusMessage = TEXT("No dirty transform to save");
        UpdateRuntimeEditorPanel();
        return;
    }
    if (!bRuntimeCanSave)
    {
        RuntimeStatusMessage = TEXT("Binding is not matched; save disabled");
        if (RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
        {
            RuntimeEditorPanel->ShowToast(
                TEXT("Dataset access is not ready"),
                EOntoTwinRuntimeToastType::Warning);
        }
        UpdateRuntimeEditorPanel();
        return;
    }
    if (bRuntimeEditSaving)
    {
        return;
    }

    const FTransform Cur = RuntimeSelectedInstance->GetActorTransform();
    const FVector L = Cur.GetLocation();
    const FRotator R = Cur.Rotator();
    const FVector S = Cur.GetScale3D();

    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("instance_id"), RuntimeSelectedInstance->GetInstanceId());

    TSharedPtr<FJsonObject> TF = MakeShared<FJsonObject>();
    TF->SetNumberField(TEXT("tx"), L.X);
    TF->SetNumberField(TEXT("ty"), L.Y);
    TF->SetNumberField(TEXT("tz"), L.Z);
    TF->SetNumberField(TEXT("rx"), R.Roll);
    TF->SetNumberField(TEXT("ry"), R.Pitch);
    TF->SetNumberField(TEXT("rz"), R.Yaw);
    TF->SetNumberField(TEXT("sx"), S.X);
    TF->SetNumberField(TEXT("sy"), S.Y);
    TF->SetNumberField(TEXT("sz"), S.Z);
    Body->SetObjectField(TEXT("transform"), TF);

    FString BodyStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/state/writeback"), *BackendBaseUrl));
    HttpRequest->SetVerb(TEXT("POST"));
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->SetContentAsString(BodyStr);

    bRuntimeEditSaving = true;
    RuntimeStatusMessage = TEXT("Saving transform...");
    UpdateRuntimeEditorPanel();

    TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
    HttpRequest->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
        {
            ATwinSceneManager* Self = WeakThis.Get();
            if (!Self) return;

            Self->bRuntimeEditSaving = false;

            const int32 Code = Resp.IsValid() ? Resp->GetResponseCode() : -1;
            TSharedPtr<FJsonObject> Root;
            if (Resp.IsValid())
            {
                TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Resp->GetContentAsString());
                FJsonSerializer::Deserialize(Reader, Root);
            }

            if (bOk && Resp.IsValid() && Code == 200)
            {
                Self->ApplyRuntimeSnapshotIfPresent(Root);

                if (Self->RuntimeSelectedInstance && IsValid(Self->RuntimeSelectedInstance))
                {
                    Self->RuntimeSelectedInstance->bLocalOverrideLock = false;
                    Self->RuntimeSelectedInstance->ResumeRuntimeEditorAnimation(Self->RuntimePreviousAnimState, Self->bRuntimePreviousAnimRunning);
                    Self->RuntimePreviousAnimState.Empty();
                    Self->bRuntimePreviousAnimRunning = false;
                    Self->RuntimeEditBaseline = Self->RuntimeSelectedInstance->GetActorTransform();
                }

                Self->bRuntimeEditDirty = false;
                Self->RuntimeStatusMessage = TEXT("Saved; backend snapshot applied");
                if (Self->RuntimeEditorPanel && IsValid(Self->RuntimeEditorPanel))
                {
                    Self->RuntimeEditorPanel->ShowToast(
                        TEXT("Changes saved"),
                        EOntoTwinRuntimeToastType::Success);
                }
            }
            else
            {
                FString Error;
                if (Root.IsValid())
                {
                    Root->TryGetStringField(TEXT("error"), Error);
                }
                Self->RuntimeStatusMessage = Error.IsEmpty()
                    ? FString::Printf(TEXT("Save failed (code=%d)"), Code)
                    : FString::Printf(TEXT("Save failed: %s"), *Error);
                if (Self->RuntimeEditorPanel && IsValid(Self->RuntimeEditorPanel))
                {
                    Self->RuntimeEditorPanel->ShowToast(
                        TEXT("Save failed. Changes are still local."),
                        EOntoTwinRuntimeToastType::Error);
                }
            }

            Self->UpdateRuntimeEditorPanel();
        });

    HttpRequest->ProcessRequest();
}

void ATwinSceneManager::ApplyRuntimeSnapshotIfPresent(const TSharedPtr<FJsonObject>& ResponseObj)
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance) || !ResponseObj.IsValid())
    {
        return;
    }

    const TSharedPtr<FJsonObject>* SnapshotObj = nullptr;
    if (ResponseObj->TryGetObjectField(TEXT("snapshot"), SnapshotObj) && SnapshotObj && SnapshotObj->IsValid())
    {
        RuntimeSelectedInstance->bLocalOverrideLock = false;
        RuntimeSelectedInstance->ApplySnapshot(*SnapshotObj);
    }
}

void ATwinSceneManager::CancelRuntimeEdit()
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        RuntimeStatusMessage = TEXT("No selected instance");
        UpdateRuntimeEditorPanel();
        return;
    }

    const bool bRestore = bRuntimeEditDirty;
    ClearRuntimeSelection(bRestore);
    RuntimeStatusMessage = bRestore ? TEXT("Edit canceled; transform restored") : TEXT("Selection cleared");
    if (bRestore && RuntimeEditorPanel && IsValid(RuntimeEditorPanel))
    {
        RuntimeEditorPanel->ShowToast(
            TEXT("Changes reverted"),
            EOntoTwinRuntimeToastType::Info);
    }
    UpdateRuntimeEditorPanel();
}

void ATwinSceneManager::SetRuntimeWallSnapEnabled(bool bEnabled)
{
    bEnableWallSnap = bEnabled;
    RuntimeStatusMessage = bEnabled ? TEXT("Wall snap enabled") : TEXT("Wall snap disabled");
    UpdateRuntimeEditorPanel();
}

void ATwinSceneManager::SetRuntimeGridSnapEnabled(bool bEnabled)
{
    bEnableGridSnap = bEnabled;
    RuntimeStatusMessage = bEnabled ? TEXT("Grid snap enabled") : TEXT("Grid snap disabled");
    UpdateRuntimeEditorPanel();
}

FString ATwinSceneManager::GetRuntimeEditorModeText() const
{
    return bRuntimeEditMode ? TEXT("Mode: Runtime Edit") : TEXT("Mode: Runtime View");
}

FString ATwinSceneManager::GetRuntimeEditorBindingText() const
{
    switch (GetRuntimeEditorAccessState())
    {
    case EOntoTwinRuntimeAccessState::Checking:
        return TEXT("Dataset access: checking");
    case EOntoTwinRuntimeAccessState::Ready:
        return TEXT("Dataset access: ready");
    case EOntoTwinRuntimeAccessState::Unbound:
        return TEXT("Dataset access: not bound");
    case EOntoTwinRuntimeAccessState::Mismatch:
        return TEXT("Dataset access: bound to another UE project");
    case EOntoTwinRuntimeAccessState::Error:
    default:
        return TEXT("Dataset access: unable to verify");
    }
}

FString ATwinSceneManager::GetRuntimeEditorSelectionText() const
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        return TEXT("Selection: none");
    }
    return FString::Printf(TEXT("Selection: %s%s"),
        *RuntimeSelectedInstance->GetInstanceId(),
        bRuntimeEditDirty ? TEXT(" *") : TEXT(""));
}

FString ATwinSceneManager::GetRuntimeEditorTransformText() const
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        return TEXT("Transform: -");
    }

    const FVector L = RuntimeSelectedInstance->GetActorLocation();
    const FRotator R = RuntimeSelectedInstance->GetActorRotation();
    return FString::Printf(TEXT("Transform: X %.1f | Y %.1f | Z %.1f | Yaw %.1f"),
        L.X, L.Y, L.Z, R.Yaw);
}

FString ATwinSceneManager::GetRuntimeEditorStatusText() const
{
    return FString::Printf(TEXT("Status: %s"), *RuntimeStatusMessage);
}

FString ATwinSceneManager::GetRuntimeEditorHeaderStateText() const
{
    if (bRuntimeEditSaving)
    {
        return TEXT("Saving");
    }
    if (bRuntimeDragging && RuntimeSnapFeedback == ERuntimeSnapFeedback::Wall)
    {
        return TEXT("Wall snap");
    }
    if (bRuntimeDragging && RuntimeSnapFeedback == ERuntimeSnapFeedback::Grid)
    {
        return TEXT("Grid snap");
    }
    if (bRuntimeDragging && RuntimeDragPart == ERuntimeDragPart::MoveXY)
    {
        return TEXT("Moving XY");
    }
    if (bRuntimeDragging && RuntimeDragPart == ERuntimeDragPart::MoveZ)
    {
        return TEXT("Moving Z");
    }
    if (bRuntimeDragging && RuntimeDragPart == ERuntimeDragPart::RotateYaw)
    {
        return TEXT("Rotating Yaw");
    }
    if (bRuntimeEditDirty)
    {
        return TEXT("Unsaved");
    }
    if (RuntimeHoverPart == ERuntimeDragPart::MoveXY)
    {
        return TEXT("Move XY");
    }
    if (RuntimeHoverPart == ERuntimeDragPart::MoveZ)
    {
        return TEXT("Move Z");
    }
    if (RuntimeHoverPart == ERuntimeDragPart::RotateYaw)
    {
        return TEXT("Rotate Yaw");
    }
    return TEXT("Editing");
}

FString ATwinSceneManager::GetRuntimeEditorDisplayName() const
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        return TEXT("No instance selected");
    }

    const FString DisplayName = RuntimeSelectedInstance->GetTwinDisplayName();
    return TruncateRuntimeLabel(DisplayName.IsEmpty() ? TEXT("Twin instance") : DisplayName, 34);
}

FString ATwinSceneManager::GetRuntimeEditorInstanceIdText() const
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        return TEXT("-");
    }

    const FString InstanceId = RuntimeSelectedInstance->GetInstanceId();
    if (InstanceId.Len() <= 18)
    {
        return InstanceId;
    }
    return InstanceId.Left(8) + TEXT("...") + InstanceId.Right(5);
}

bool ATwinSceneManager::GetRuntimeEditorTransform(FVector& OutLocation, float& OutYaw) const
{
    if (!RuntimeSelectedInstance || !IsValid(RuntimeSelectedInstance))
    {
        OutLocation = FVector::ZeroVector;
        OutYaw = 0.0f;
        return false;
    }

    OutLocation = RuntimeSelectedInstance->GetActorLocation();
    OutYaw = RuntimeSelectedInstance->GetActorRotation().Yaw;
    return true;
}

EOntoTwinRuntimeAccessState ATwinSceneManager::GetRuntimeEditorAccessState() const
{
    if (bRuntimeBindingRequestInFlight)
    {
        return EOntoTwinRuntimeAccessState::Checking;
    }
    if (RuntimeBindingMode == TEXT("matched"))
    {
        return EOntoTwinRuntimeAccessState::Ready;
    }
    if (RuntimeBindingMode == TEXT("unbound"))
    {
        return EOntoTwinRuntimeAccessState::Unbound;
    }
    if (RuntimeBindingMode == TEXT("ue_project_mismatch"))
    {
        return EOntoTwinRuntimeAccessState::Mismatch;
    }
    return EOntoTwinRuntimeAccessState::Error;
}

bool ATwinSceneManager::CanBindRuntimeProject() const
{
    return bRuntimeEditMode && !bRuntimeBindingRequestInFlight && RuntimeBindingMode == TEXT("unbound");
}

bool ATwinSceneManager::CanRetryRuntimeBindingStatus() const
{
    return bRuntimeEditMode && !bRuntimeBindingRequestInFlight &&
        GetRuntimeEditorAccessState() == EOntoTwinRuntimeAccessState::Error;
}

bool ATwinSceneManager::CanSaveRuntimeEdit() const
{
    return bRuntimeEditMode &&
        RuntimeSelectedInstance &&
        IsValid(RuntimeSelectedInstance) &&
        bRuntimeEditDirty &&
        !bRuntimeEditSaving &&
        bRuntimeCanSave;
}

bool ATwinSceneManager::CanCancelRuntimeEdit() const
{
    return bRuntimeEditMode &&
        RuntimeSelectedInstance &&
        IsValid(RuntimeSelectedInstance) &&
        bRuntimeEditDirty &&
        !bRuntimeEditSaving;
}

bool ATwinSceneManager::HasRuntimeEditSelection() const
{
    return RuntimeSelectedInstance && IsValid(RuntimeSelectedInstance);
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-6 历史 actor 迁移工具（编辑器一次性）
// ═══════════════════════════════════════════════════════════════════════════

FString ATwinSceneManager::MigrationExportPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_actors_export.json")));
}

FString ATwinSceneManager::MigrationResultPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_migration_result.json")));
}

FString ATwinSceneManager::MigrationPreviewSnapshotPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_snapshots.json")));
}

FString ATwinSceneManager::MigrationPreviewAuditPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_preview_audit.json")));
}

void ATwinSceneManager::ExportSelectedActorsForMigration()
{
#if WITH_EDITOR
    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GetWorld();
    if (!World)
    {
        return;
    }

    FString TargetFolder = MigrationFolderName;
    TargetFolder.TrimStartAndEndInline();
    TSet<AActor*> CandidateActors;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || A == this) continue;
        if (A->IsA(ATwinInstance::StaticClass())) continue;
        if (IsInFolderOrChild(A->GetFolderPath(), TargetFolder))
        {
            CandidateActors.Add(A);
        }
    }

    // 文件夹里只需要放母 Actor。若一个候选又附着在另一个候选下面，只导出最上层母 Actor，
    // 防止同一批后代既作为部件又被重复建实例。
    TArray<AActor*> RootActors;
    for (AActor* Candidate : CandidateActors)
    {
        bool bHasCandidateAncestor = false;
        for (AActor* Parent = Candidate ? Candidate->GetAttachParentActor() : nullptr;
             Parent;
             Parent = Parent->GetAttachParentActor())
        {
            if (CandidateActors.Contains(Parent))
            {
                bHasCandidateAncestor = true;
                break;
            }
        }
        if (!bHasCandidateAncestor)
        {
            RootActors.Add(Candidate);
        }
    }
    RootActors.Sort([](const AActor& Lhs, const AActor& Rhs)
    {
        return Lhs.GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens)
            < Rhs.GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens);
    });

    auto ActorGuidString = [](const AActor* A)
    {
        return A
            ? A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens)
            : FString();
    };
    auto TransformToJson = [](const FTransform& Transform)
    {
        const FVector Loc = Transform.GetLocation();
        const FRotator Rot = Transform.Rotator();
        const FVector Scale = Transform.GetScale3D();
        TSharedPtr<FJsonObject> Json = MakeShared<FJsonObject>();
        Json->SetNumberField(TEXT("tx"), Loc.X);
        Json->SetNumberField(TEXT("ty"), Loc.Y);
        Json->SetNumberField(TEXT("tz"), Loc.Z);
        // 与 ApplySpatialFromSnapshot 约定一致：rx=Roll, ry=Pitch, rz=Yaw。
        Json->SetNumberField(TEXT("rx"), Rot.Roll);
        Json->SetNumberField(TEXT("ry"), Rot.Pitch);
        Json->SetNumberField(TEXT("rz"), Rot.Yaw);
        Json->SetNumberField(TEXT("sx"), Scale.X);
        Json->SetNumberField(TEXT("sy"), Scale.Y);
        Json->SetNumberField(TEXT("sz"), Scale.Z);
        return Json;
    };
    auto UnsupportedComponentKind = [](const UActorComponent* Component)
    {
        if (!Component || !Component->GetClass()) return FString();
        const FString ClassName = Component->GetClass()->GetName();
        if (Component->IsA<USkeletalMeshComponent>()) return FString(TEXT("skeletal_mesh"));
        if (Component->IsA<UInstancedStaticMeshComponent>())
        {
            return ClassName.Contains(TEXT("Hierarchical"), ESearchCase::IgnoreCase)
                ? FString(TEXT("hierarchical_instanced_static_mesh"))
                : FString(TEXT("instanced_static_mesh"));
        }
        if (ClassName.Contains(TEXT("Spline"), ESearchCase::IgnoreCase))
            return FString(TEXT("spline"));
        if (ClassName.Contains(TEXT("ProceduralMesh"), ESearchCase::IgnoreCase))
            return FString(TEXT("procedural_mesh"));
        if (ClassName.Contains(TEXT("GeometryCollection"), ESearchCase::IgnoreCase))
            return FString(TEXT("geometry_collection"));
        if (ClassName.Contains(TEXT("Niagara"), ESearchCase::IgnoreCase))
            return FString(TEXT("niagara"));
        if (ClassName.Contains(TEXT("Decal"), ESearchCase::IgnoreCase))
            return FString(TEXT("decal"));
        if (ClassName.Contains(TEXT("ChildActor"), ESearchCase::IgnoreCase))
            return FString(TEXT("child_actor"));
        if (ClassName.Contains(TEXT("GeometryCache"), ESearchCase::IgnoreCase))
            return FString(TEXT("geometry_cache"));
        if (ClassName.Contains(TEXT("Groom"), ESearchCase::IgnoreCase))
            return FString(TEXT("groom"));
        if (ClassName.Contains(TEXT("ParticleSystem"), ESearchCase::IgnoreCase))
            return FString(TEXT("particle_system"));
        return FString();
    };

    TArray<TSharedPtr<FJsonValue>> ActorsJson;
    int32 TotalSourceActors = 0;
    int32 TotalRenderParts = 0;
    int32 TotalUnsupported = 0;
    for (AActor* RootActor : RootActors)
    {
        if (!RootActor) continue;

        TArray<AActor*> AssemblyActors;
        TSet<AActor*> VisitedActors;
        TFunction<void(AActor*)> CollectAttachedTree = [&](AActor* Current)
        {
            if (!Current || VisitedActors.Contains(Current)) return;
            VisitedActors.Add(Current);
            AssemblyActors.Add(Current);

            TArray<AActor*> DirectChildren;
            Current->GetAttachedActors(DirectChildren, /*bResetArray=*/true, /*bRecursivelyIncludeAttachedActors=*/false);
            DirectChildren.Sort([&ActorGuidString](const AActor& Lhs, const AActor& Rhs)
            {
                return ActorGuidString(&Lhs) < ActorGuidString(&Rhs);
            });
            for (AActor* Child : DirectChildren)
            {
                CollectAttachedTree(Child);
            }
        };
        CollectAttachedTree(RootActor);

        TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
        const FString RootGuid = ActorGuidString(RootActor);
        Obj->SetStringField(TEXT("ext_guid"), RootGuid);
        Obj->SetStringField(TEXT("name"), RootActor->GetActorLabel());
        Obj->SetStringField(TEXT("actor_label"), RootActor->GetActorLabel());
        Obj->SetStringField(TEXT("actor_name"), RootActor->GetName());
        Obj->SetStringField(TEXT("source_folder_path"), RootActor->GetFolderPath().ToString());
        if (UClass* ActorClass = RootActor->GetClass())
        {
            Obj->SetStringField(TEXT("actor_class"), ActorClass->GetName());
            Obj->SetStringField(TEXT("actor_class_path"), ActorClass->GetPathName());
            if (ActorClass->ClassGeneratedBy)
            {
                Obj->SetStringField(TEXT("blueprint_class_path"), ActorClass->ClassGeneratedBy->GetPathName());
            }
        }
        Obj->SetObjectField(TEXT("transform"), TransformToJson(RootActor->GetActorTransform()));

        TArray<TSharedPtr<FJsonValue>> SourceActorGuids;
        TArray<TSharedPtr<FJsonValue>> SourceActors;
        TArray<TSharedPtr<FJsonValue>> RenderParts;
        TArray<TSharedPtr<FJsonValue>> StaticMeshAssets;
        TArray<TSharedPtr<FJsonValue>> SkeletalMeshAssets;
        TArray<TSharedPtr<FJsonValue>> UnsupportedComponents;
        TArray<TSharedPtr<FJsonValue>> MigrationWarnings;
        TMap<FString, int32> ActorClassCounts;
        TMap<FString, int32> ComponentClassCounts;
        TArray<FString> SignatureParts;
        FString FirstMeshAsset;
        FString FirstSkeletalMeshAsset;

        const FTransform RootWorldTransform = RootActor->GetActorTransform();
        for (AActor* SourceActor : AssemblyActors)
        {
            if (!SourceActor) continue;
            const FString SourceGuid = ActorGuidString(SourceActor);
            SourceActorGuids.Add(MakeShared<FJsonValueString>(SourceGuid));

            TSharedPtr<FJsonObject> SourceActorJson = MakeShared<FJsonObject>();
            SourceActorJson->SetStringField(TEXT("guid"), SourceGuid);
            SourceActorJson->SetStringField(TEXT("actor_label"), SourceActor->GetActorLabel());
            SourceActorJson->SetStringField(TEXT("actor_name"), SourceActor->GetName());
            SourceActorJson->SetStringField(TEXT("folder_path"), SourceActor->GetFolderPath().ToString());
            SourceActorJson->SetStringField(TEXT("parent_guid"), ActorGuidString(SourceActor->GetAttachParentActor()));
            if (UClass* SourceClass = SourceActor->GetClass())
            {
                SourceActorJson->SetStringField(TEXT("actor_class"), SourceClass->GetName());
                SourceActorJson->SetStringField(TEXT("actor_class_path"), SourceClass->GetPathName());
                ActorClassCounts.FindOrAdd(SourceClass->GetPathName())++;
                if (SourceClass->ClassGeneratedBy)
                {
                    SourceActorJson->SetStringField(
                        TEXT("blueprint_class_path"), SourceClass->ClassGeneratedBy->GetPathName());
                }
            }
            SourceActors.Add(MakeShared<FJsonValueObject>(SourceActorJson));

            // Datasmith 大量使用负缩放做镜像。assembly_v1 会在部件相对 FTransform 中
            // 原样保留它；这里只把事实写入审计，不把正常镜像误判为禁止迁移。
            const FVector SourceActorScale = SourceActor->GetActorScale3D();
            SourceActorJson->SetBoolField(TEXT("has_mirrored_scale"),
                SourceActorScale.X < 0.0 || SourceActorScale.Y < 0.0 || SourceActorScale.Z < 0.0);

            TInlineComponentArray<UActorComponent*> Components(SourceActor);
            Components.Sort([](const UActorComponent& Lhs, const UActorComponent& Rhs)
            {
                return Lhs.GetName() < Rhs.GetName();
            });
            for (UActorComponent* Component : Components)
            {
                if (!Component || !Component->GetClass()) continue;
                const FString ComponentClassPath = Component->GetClass()->GetPathName();
                ComponentClassCounts.FindOrAdd(ComponentClassPath)++;

                const FString UnsupportedKind = UnsupportedComponentKind(Component);
                if (!UnsupportedKind.IsEmpty())
                {
                    TSharedPtr<FJsonObject> Unsupported = MakeShared<FJsonObject>();
                    Unsupported->SetStringField(TEXT("kind"), UnsupportedKind);
                    Unsupported->SetStringField(TEXT("source_actor_guid"), SourceGuid);
                    Unsupported->SetStringField(TEXT("source_actor_label"), SourceActor->GetActorLabel());
                    Unsupported->SetStringField(TEXT("component_name"), Component->GetName());
                    Unsupported->SetStringField(TEXT("component_class"), ComponentClassPath);
                    UnsupportedComponents.Add(MakeShared<FJsonValueObject>(Unsupported));

                    if (USkeletalMeshComponent* Skeletal = Cast<USkeletalMeshComponent>(Component))
                    {
                        if (USkeletalMesh* SkeletalAsset = Skeletal->GetSkeletalMeshAsset())
                        {
                            const FString AssetPath = SkeletalAsset->GetPathName();
                            if (FirstSkeletalMeshAsset.IsEmpty()) FirstSkeletalMeshAsset = AssetPath;
                            SkeletalMeshAssets.Add(MakeShared<FJsonValueString>(AssetPath));
                        }
                    }
                    continue;
                }

                UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(Component);
                if (!StaticMeshComponent || !StaticMeshComponent->GetStaticMesh()) continue;

                const FString AssetPath = StaticMeshComponent->GetStaticMesh()->GetPathName();
                const FTransform RelativeTransform =
                    StaticMeshComponent->GetComponentTransform().GetRelativeTransform(RootWorldTransform);
                if (FirstMeshAsset.IsEmpty()) FirstMeshAsset = AssetPath;
                StaticMeshAssets.Add(MakeShared<FJsonValueString>(AssetPath));

                TSharedPtr<FJsonObject> Part = MakeShared<FJsonObject>();
                Part->SetStringField(TEXT("asset_path"), AssetPath);
                Part->SetStringField(TEXT("source_actor_guid"), SourceGuid);
                Part->SetStringField(TEXT("source_actor_label"), SourceActor->GetActorLabel());
                Part->SetStringField(TEXT("source_component_name"), StaticMeshComponent->GetName());
                Part->SetStringField(TEXT("source_component_class"), ComponentClassPath);
                Part->SetObjectField(TEXT("relative_transform"), TransformToJson(RelativeTransform));

                TArray<TSharedPtr<FJsonValue>> MaterialPaths;
                TArray<FString> MaterialSignaturePaths;
                const int32 MaterialSlotCount = StaticMeshComponent->GetNumMaterials();
                MaterialPaths.Reserve(MaterialSlotCount);
                MaterialSignaturePaths.Reserve(MaterialSlotCount);
                for (int32 MaterialIndex = 0; MaterialIndex < MaterialSlotCount; ++MaterialIndex)
                {
                    UMaterialInterface* EffectiveMaterial = StaticMeshComponent->GetMaterial(MaterialIndex);
                    const FString MaterialPath = EffectiveMaterial
                        ? EffectiveMaterial->GetPathName()
                        : FString();
                    MaterialPaths.Add(MakeShared<FJsonValueString>(MaterialPath));
                    MaterialSignaturePaths.Add(MaterialPath);
                }
                // visible 与 hidden_in_game 分别保存原始标志，避免 IsVisible() 的上下文合成结果丢信息。
                const bool bPartVisible = StaticMeshComponent->GetVisibleFlag();
                const bool bPartHiddenInGame = StaticMeshComponent->bHiddenInGame;
                const bool bPartCastShadow = StaticMeshComponent->CastShadow;
                const FString CollisionEnabled = CollisionEnabledToMigrationString(
                    StaticMeshComponent->GetCollisionEnabled());
                Part->SetArrayField(TEXT("material_paths"), MaterialPaths);
                Part->SetBoolField(TEXT("visible"), bPartVisible);
                Part->SetBoolField(TEXT("hidden_in_game"), bPartHiddenInGame);
                Part->SetBoolField(TEXT("cast_shadow"), bPartCastShadow);
                Part->SetStringField(TEXT("collision_enabled"), CollisionEnabled);
                RenderParts.Add(MakeShared<FJsonValueObject>(Part));

                const FVector RelativeLocation = RelativeTransform.GetLocation();
                const FRotator RelativeRotation = RelativeTransform.Rotator();
                const FVector RelativeScale = RelativeTransform.GetScale3D();
                SignatureParts.Add(FString::Printf(
                    TEXT("%s|%.3f,%.3f,%.3f|%.3f,%.3f,%.3f|%.5f,%.5f,%.5f|%s|%d|%d|%d|%s"),
                    *AssetPath,
                    RelativeLocation.X, RelativeLocation.Y, RelativeLocation.Z,
                    RelativeRotation.Roll, RelativeRotation.Pitch, RelativeRotation.Yaw,
                    RelativeScale.X, RelativeScale.Y, RelativeScale.Z,
                    *FString::Join(MaterialSignaturePaths, TEXT(",")),
                    bPartVisible ? 1 : 0,
                    bPartHiddenInGame ? 1 : 0,
                    bPartCastShadow ? 1 : 0,
                    *CollisionEnabled));
            }
        }

        if (RenderParts.Num() == 0)
        {
            MigrationWarnings.Add(MakeShared<FJsonValueString>(TEXT("no_supported_static_mesh_parts")));
        }
        if (UnsupportedComponents.Num() > 0)
        {
            MigrationWarnings.Add(MakeShared<FJsonValueString>(TEXT("contains_unsupported_components")));
        }

        SignatureParts.Sort();
        const FString SignatureSource = FString::Join(SignatureParts, TEXT("\n"));
        Obj->SetStringField(TEXT("assembly_signature"), FMD5::HashAnsiString(*SignatureSource));
        Obj->SetArrayField(TEXT("source_actor_guids"), SourceActorGuids);
        Obj->SetArrayField(TEXT("source_actors"), SourceActors);
        Obj->SetArrayField(TEXT("render_parts"), RenderParts);
        Obj->SetArrayField(TEXT("unsupported_components"), UnsupportedComponents);
        Obj->SetArrayField(TEXT("migration_warnings"), MigrationWarnings);

        // 旧版字段保留，便于旧工具读取与分类脚本逐步升级。
        Obj->SetStringField(TEXT("mesh_asset"), FirstMeshAsset);
        Obj->SetStringField(TEXT("static_mesh_asset"), FirstMeshAsset);
        Obj->SetArrayField(TEXT("static_mesh_assets"), StaticMeshAssets);
        Obj->SetStringField(TEXT("skeletal_mesh_asset"), FirstSkeletalMeshAsset);
        Obj->SetArrayField(TEXT("skeletal_mesh_assets"), SkeletalMeshAssets);

        TSharedPtr<FJsonObject> ActorClassesJson = MakeShared<FJsonObject>();
        for (const TPair<FString, int32>& Pair : ActorClassCounts)
        {
            ActorClassesJson->SetNumberField(Pair.Key, Pair.Value);
        }
        TSharedPtr<FJsonObject> ComponentClassesJson = MakeShared<FJsonObject>();
        for (const TPair<FString, int32>& Pair : ComponentClassCounts)
        {
            ComponentClassesJson->SetNumberField(Pair.Key, Pair.Value);
        }
        TSharedPtr<FJsonObject> ComponentAudit = MakeShared<FJsonObject>();
        ComponentAudit->SetNumberField(TEXT("source_actor_count"), AssemblyActors.Num());
        ComponentAudit->SetNumberField(TEXT("descendant_actor_count"), FMath::Max(0, AssemblyActors.Num() - 1));
        ComponentAudit->SetNumberField(TEXT("render_part_count"), RenderParts.Num());
        ComponentAudit->SetNumberField(TEXT("unsupported_component_count"), UnsupportedComponents.Num());
        // 兼容旧版审计字段；ISM/HISM 不会计入 static_mesh_components。
        ComponentAudit->SetNumberField(TEXT("static_mesh_components"), RenderParts.Num());
        ComponentAudit->SetNumberField(TEXT("skeletal_mesh_components"), SkeletalMeshAssets.Num());
        ComponentAudit->SetObjectField(TEXT("actor_classes"), ActorClassesJson);
        ComponentAudit->SetObjectField(TEXT("component_classes"), ComponentClassesJson);
        Obj->SetObjectField(TEXT("component_audit"), ComponentAudit);
        Obj->SetObjectField(TEXT("component_summary"), ComponentAudit);

        ActorsJson.Add(MakeShared<FJsonValueObject>(Obj));
        TotalSourceActors += AssemblyActors.Num();
        TotalRenderParts += RenderParts.Num();
        TotalUnsupported += UnsupportedComponents.Num();
    }

    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("schema_version"), TEXT("assembly_v1"));
    Root->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Root->SetStringField(TEXT("ue_project_name"), UEProjectName);
    // project_id 留空→后端用当前激活项目；zone_id 用本 Manager 的 SceneId（=分区）
    if (!SceneId.IsEmpty())
    {
        Root->SetStringField(TEXT("zone_id"), SceneId);
    }
    Root->SetArrayField(TEXT("actors"), ActorsJson);

    FString OutStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutStr);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);

    const FString Path = MigrationExportPath();
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), /*Tree=*/true);
    // 后端工具按 UTF-8 读取；Windows 默认编码会把含中文标签的 FString 写成 UTF-16LE。
    const bool bOk = FFileHelper::SaveStringToFile(
        OutStr,
        *Path,
        FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);

    UE_LOG(LogTemp, Log,
        TEXT("[迁移] assembly_v1 导出 %d 个母 Actor / %d 个源 Actor / %d 个渲染部件 / %d 个不支持组件 → %s (%s)"),
        RootActors.Num(), TotalSourceActors, TotalRenderParts, TotalUnsupported,
        *Path, bOk ? TEXT("成功") : TEXT("写入失败"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.0f,
            bOk ? FColor::Green : FColor::Red,
            RootActors.Num() > 0
                ? FString::Printf(
                    TEXT("导出 %d 个母 Actor（%d 个部件，%d 个不支持组件）→ %s\n把它交给后端 migrate_ue_actors.py"),
                    RootActors.Num(), TotalRenderParts, TotalUnsupported, *Path)
                : FString::Printf(
                    TEXT("文件夹「%s」及其子文件夹下没有 actor\n请先框选历史 actor，右键→移动到文件夹→填「%s」"),
                    *MigrationFolderName, *MigrationFolderName));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[迁移] 导出仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::RemoveMigratedActors()
{
#if WITH_EDITOR
    const FString Path = MigrationResultPath();
    FString Content;
    if (!FFileHelper::LoadFileToString(Content, *Path))
    {
        UE_LOG(LogTemp, Error, TEXT("[迁移] 读不到结果文件: %s"), *Path);
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Red,
                FString::Printf(TEXT("读不到 %s\n请先跑后端迁移脚本产出结果"), *Path));
        }
        return;
    }

    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Content);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[迁移] 结果 JSON 解析失败"));
        return;
    }

    TSet<FString> MigratedGuids;
    FString ResultFormat = TEXT("legacy_flat_mapping");

    // assembly_v1 的 canonical 删除清单最精确：它包含母 Actor 与全部已收编后代。
    const TArray<TSharedPtr<FJsonValue>>* DeleteActorGuids = nullptr;
    if (Root->TryGetArrayField(TEXT("delete_actor_guids"), DeleteActorGuids) && DeleteActorGuids)
    {
        ResultFormat = TEXT("assembly_v1.delete_actor_guids");
        for (const TSharedPtr<FJsonValue>& Value : *DeleteActorGuids)
        {
            FString Guid;
            if (Value.IsValid() && Value->TryGetString(Guid) && !Guid.IsEmpty())
            {
                MigratedGuids.Add(Guid);
            }
        }
    }
    else
    {
        // 新结果缺删除清单时只删除 canonical instances 的 key（母 Actor），不误读保留字段。
        const TSharedPtr<FJsonObject>* Instances = nullptr;
        if (Root->TryGetObjectField(TEXT("instances"), Instances) && Instances && Instances->IsValid())
        {
            ResultFormat = TEXT("assembly_v1.instances_fallback");
            for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Instances)->Values)
            {
                FGuid ParsedGuid;
                if (FGuid::Parse(Pair.Key, ParsedGuid))
                {
                    MigratedGuids.Add(Pair.Key);
                }
            }
        }
        else
        {
            // 兼容旧版根对象 {ext_guid: instance_id}。
            for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : Root->Values)
            {
                FGuid ParsedGuid;
                FString InstanceId;
                if (FGuid::Parse(Pair.Key, ParsedGuid)
                    && Pair.Value.IsValid()
                    && Pair.Value->TryGetString(InstanceId))
                {
                    MigratedGuids.Add(Pair.Key);
                }
            }
        }
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GetWorld();
    if (!World) return;

    TArray<AActor*> ToDelete;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || A == this) continue;
        if (A->IsA(ATwinInstance::StaticClass())) continue;
        const FString Guid = A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens);
        if (MigratedGuids.Contains(Guid))
        {
            ToDelete.Add(A);
        }
    }

    int32 Deleted = 0;
    for (AActor* A : ToDelete)
    {
        if (A && IsValid(A) && !A->IsActorBeingDestroyed()
            && World->EditorDestroyActor(A, /*bShouldModifyLevel=*/true))
        {
            Deleted++;
        }
    }

    UE_LOG(LogTemp, Log,
        TEXT("[迁移] 按 %s 已删除 %d 个已收编的原 actor（结果含 %d GUID，共匹配 %d）"),
        *ResultFormat, Deleted, MigratedGuids.Num(), ToDelete.Num());
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Green,
            FString::Printf(TEXT("已清除 %d 个已迁移原 actor\n记得保存关卡(Ctrl+S)"), Deleted));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[迁移] 清除仅在编辑器模式下可用"));
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-4 编辑器预览（从数据库临时 spawn 供查看/微调，绝不写入 .umap）
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::PullPreviewFromDB()
{
#if WITH_EDITOR
    ClearPreview();  // 先清掉上一批，避免重叠

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
        FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(BuildSnapshotsUrl());
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnPreviewResponse);
    HttpRequest->ProcessRequest();

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Cyan,
            TEXT("正在从数据库拉取预览..."));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 预览仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::PreviewMigratedActorsFromSnapshotFile()
{
#if WITH_EDITOR
    ClearPreview();
    IFileManager::Get().Delete(*MigrationPreviewAuditPath(), false, true, true);
    const FString SnapshotPath = MigrationPreviewSnapshotPath();
    FString JsonPayload;
    if (!FFileHelper::LoadFileToString(JsonPayload, *SnapshotPath))
    {
        UE_LOG(LogTemp, Error, TEXT("[迁移预览] 无法读取快照文件: %s"), *SnapshotPath);
        return;
    }

    const int32 Count = SpawnPreviewActorsFromJson(JsonPayload, TEXT("migration_snapshot_file"));
    UE_LOG(LogTemp, Log,
        TEXT("[迁移预览] 从 %s 生成 %d 个 transient Actor；关卡未保存"),
        *SnapshotPath, Count);
#else
    UE_LOG(LogTemp, Warning, TEXT("[迁移预览] 仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::ClearPreview()
{
#if WITH_EDITOR
    int32 Cleared = 0;
    for (ATwinInstance* A : PreviewActors)
    {
        if (A && IsValid(A))
        {
            A->Destroy();
            Cleared++;
        }
    }
    PreviewActors.Empty();
    PreviewBaseline.Empty();
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 已清除 %d 个预览 Actor"), Cleared);
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-5 空间回写：预览 Actor 手动调整后提交回后端真源
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::CommitPreviewChanges()
{
#if WITH_EDITOR
    // ── 1. diff：找出被手动挪动过的预览 Actor ────────────────────────────
    struct FChange { FString Id; FTransform Cur; };
    TArray<FChange> Changes;

    for (ATwinInstance* A : PreviewActors)
    {
        if (!A || !IsValid(A)) continue;
        const FString Id = A->GetInstanceId();
        const FTransform* Base = PreviewBaseline.Find(Id);
        if (!Base) continue;

        const FTransform Cur = A->GetActorTransform();
        if (Cur.Equals(*Base, 0.01f)) continue;   // 没动过（容差 0.01）

        Changes.Add({Id, Cur});
    }

    if (Changes.Num() == 0)
    {
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Yellow,
                TEXT("没有检测到位置变更（先拉取预览、挪动后再提交）"));
        }
        return;
    }

    // ── 2. 逐条 POST /api/v2/state/writeback ────────────────────────────
    PendingWritebacks = Changes.Num();
    SucceededWritebacks = 0;

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Cyan,
            FString::Printf(TEXT("正在提交 %d 处空间变更..."), Changes.Num()));
    }

    for (const FChange& C : Changes)
    {
        TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
        Body->SetStringField(TEXT("instance_id"), C.Id);

        const FVector L = C.Cur.GetLocation();
        const FRotator R = C.Cur.Rotator();
        const FVector S = C.Cur.GetScale3D();
        TSharedPtr<FJsonObject> TF = MakeShared<FJsonObject>();
        TF->SetNumberField(TEXT("tx"), L.X);
        TF->SetNumberField(TEXT("ty"), L.Y);
        TF->SetNumberField(TEXT("tz"), L.Z);
        // 与后端 writeback.py / ApplySpatialFromSnapshot 约定一致：rx=Roll, ry=Pitch, rz=Yaw
        TF->SetNumberField(TEXT("rx"), R.Roll);
        TF->SetNumberField(TEXT("ry"), R.Pitch);
        TF->SetNumberField(TEXT("rz"), R.Yaw);
        TF->SetNumberField(TEXT("sx"), S.X);
        TF->SetNumberField(TEXT("sy"), S.Y);
        TF->SetNumberField(TEXT("sz"), S.Z);
        Body->SetObjectField(TEXT("transform"), TF);

        FString BodyStr;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
        FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

        TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
            FHttpModule::Get().CreateRequest();
        HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/state/writeback"), *BackendBaseUrl));
        HttpRequest->SetVerb(TEXT("POST"));
        HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
        AddUEProjectHeaders(HttpRequest);
        HttpRequest->SetContentAsString(BodyStr);

        TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
        const FString Id = C.Id;
        const FTransform Committed = C.Cur;
        HttpRequest->OnProcessRequestComplete().BindLambda(
            [WeakThis, Id, Committed](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
            {
                ATwinSceneManager* Self = WeakThis.Get();
                if (!Self) return;
                Self->PendingWritebacks--;

                const bool bSuccess = bOk && Resp.IsValid() && Resp->GetResponseCode() == 200;
                if (bSuccess)
                {
                    Self->SucceededWritebacks++;
                    // 基线推进到已提交值：重复点提交不会再发同一条
                    Self->PreviewBaseline.Add(Id, Committed);
                    UE_LOG(LogTemp, Log, TEXT("[回写] %s 提交成功"), *Id);
                }
                else
                {
                    UE_LOG(LogTemp, Error, TEXT("[回写] %s 提交失败 (code=%d)"),
                           *Id, Resp.IsValid() ? Resp->GetResponseCode() : -1);
                    if (GEngine)
                    {
                        GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Red,
                            FString::Printf(TEXT("回写失败: %s（详见 Output Log）"), *Id));
                    }
                }

                // 全部返回后给一条汇总
                if (Self->PendingWritebacks <= 0 && GEngine)
                {
                    GEngine->AddOnScreenDebugMessage(-1, 8.0f,
                        Self->SucceededWritebacks > 0 ? FColor::Green : FColor::Red,
                        FString::Printf(TEXT("回写完成：成功 %d 处"), Self->SucceededWritebacks));
                }
            });

        HttpRequest->ProcessRequest();
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 回写提交仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::OnPreviewResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
#if WITH_EDITOR
    if (!bWasSuccessful || !Response.IsValid() || Response->GetResponseCode() != 200)
    {
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red,
                TEXT("预览拉取失败，请确认后端在运行"));
        }
        return;
    }

    const int32 Count = SpawnPreviewActorsFromJson(
        Response->GetContentAsString(), TEXT("backend_http"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green,
            FString::Printf(TEXT("预览已生成 %d 个（transient，不会存进关卡）"), Count));
    }
#endif
}

int32 ATwinSceneManager::SpawnPreviewActorsFromJson(
    const FString& JsonPayload,
    const FString& SourceLabel)
{
#if WITH_EDITOR
    const FString AuditPath = MigrationPreviewAuditPath();
    IFileManager::Get().Delete(*AuditPath, false, true, true);
    TArray<TSharedPtr<FJsonValue>> Arr;
    TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(JsonPayload);
    if (!FJsonSerializer::Deserialize(Reader, Arr))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 预览 JSON 解析失败"));
        return 0;
    }

    UWorld* World = GetWorld();
    if (!World && GEditor)
    {
        World = GEditor->GetEditorWorldContext().World();
    }
    if (!World)
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 预览失败：编辑器世界不可用"));
        return 0;
    }

    UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();
    int32 Count = 0;
    int32 ExpectedRenderParts = 0;
    int32 LoadedRenderParts = 0;
    int32 AssemblyInstances = 0;
    int32 CompleteAssemblies = 0;
    int32 PartStateValidAssemblies = 0;
    int32 SpatialSnapshots = 0;
    int32 SpatialSchemaErrors = 0;
    int32 MalformedSnapshots = 0;
    int32 TransientActors = 0;
    TArray<TSharedPtr<FJsonValue>> IncompleteAssemblies;
    TArray<TSharedPtr<FJsonValue>> PartStateFailures;
    TArray<TSharedPtr<FJsonValue>> SpatialMismatches;
    TArray<TSharedPtr<FJsonValue>> SpatialSchemaErrorInstances;
    TArray<TSharedPtr<FJsonValue>> NonTransientInstances;

    for (const auto& Val : Arr)
    {
        const TSharedPtr<FJsonObject>* SnapObj = nullptr;
        if (!Val.IsValid() || !Val->TryGetObject(SnapObj) || !SnapObj || !SnapObj->IsValid())
        {
            ++MalformedSnapshots;
            continue;
        }

        FString InstId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstId) || InstId.IsEmpty())
        {
            ++MalformedSnapshots;
            continue;
        }

        FString AssetPathStr;
        FString ExpectedAssemblySignature;
        int32 ExpectedPartCount = 0;
        bool bExpectedOverallVisible = true;
        const TArray<TSharedPtr<FJsonValue>>* ExpectedParts = nullptr;
        const TSharedPtr<FJsonObject>* InterfacesObj = nullptr;
        if ((*SnapObj)->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
        {
            const TSharedPtr<FJsonObject>* RepObj;
            if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
            {
                (*RepObj)->TryGetStringField(TEXT("asset_id"), AssetPathStr);
                (*RepObj)->TryGetStringField(
                    TEXT("assembly_signature"), ExpectedAssemblySignature);
                (*RepObj)->TryGetBoolField(
                    TEXT("is_visible"), bExpectedOverallVisible);
                if ((*RepObj)->TryGetArrayField(TEXT("render_parts"), ExpectedParts)
                    && ExpectedParts)
                {
                    ExpectedPartCount = ExpectedParts->Num();
                }
            }
        }

        // 关键：RF_Transient → 保存关卡时绝不写入 .umap（杜绝“误固化”）
        FActorSpawnParameters SpawnParams;
        SpawnParams.ObjectFlags |= RF_Transient;

        ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
            SpawnClass, FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
        if (!Inst) continue;
        if (Inst->HasAnyFlags(RF_Transient))
        {
            ++TransientActors;
        }
        else
        {
            NonTransientInstances.Add(MakeShared<FJsonValueString>(InstId));
        }

        FString DisplayName;
        if (!(*SnapObj)->TryGetStringField(TEXT("displayName"), DisplayName) || DisplayName.IsEmpty())
        {
            DisplayName = InstId;
        }
        Inst->SetActorLabel(FString::Printf(TEXT("[预览] %s"), *DisplayName));
        Inst->SetFolderPath(BuildTwinFolderPath(*SnapObj, TEXT("TwinPreview")));
        Inst->InitializeTwin(InstId, AssetPathStr, BackendBaseUrl);
        Inst->ApplySnapshot(*SnapObj);   // 应用位置/材质等，摆到正确位置

        const int32 ActualPartCount = Inst->GetRenderPartComponentCount();
        ExpectedRenderParts += ExpectedPartCount;
        LoadedRenderParts += ActualPartCount;
        if (ExpectedPartCount > 0)
        {
            ++AssemblyInstances;
            const bool bAssemblyComplete = Inst->IsAssemblyRenderActive()
                && ActualPartCount == ExpectedPartCount
                && !ExpectedAssemblySignature.IsEmpty()
                && Inst->GetCurrentAssemblySignature() == ExpectedAssemblySignature;
            if (bAssemblyComplete)
            {
                ++CompleteAssemblies;
            }
            else
            {
                TSharedPtr<FJsonObject> Failure = MakeShared<FJsonObject>();
                Failure->SetStringField(TEXT("instance_id"), InstId);
                Failure->SetNumberField(TEXT("expected_render_parts"), ExpectedPartCount);
                Failure->SetNumberField(TEXT("loaded_render_parts"), ActualPartCount);
                Failure->SetStringField(
                    TEXT("expected_assembly_signature"), ExpectedAssemblySignature);
                Failure->SetStringField(
                    TEXT("loaded_assembly_signature"), Inst->GetCurrentAssemblySignature());
                IncompleteAssemblies.Add(MakeShared<FJsonValueObject>(Failure));
            }

            TArray<TSharedPtr<FJsonValue>> InstancePartFailures;
            if (ExpectedParts
                && Inst->ValidateRenderPartsAgainstSnapshot(
                    *ExpectedParts,
                    bExpectedOverallVisible,
                    InstancePartFailures))
            {
                ++PartStateValidAssemblies;
            }
            else
            {
                TSharedPtr<FJsonObject> Failure = MakeShared<FJsonObject>();
                Failure->SetStringField(TEXT("instance_id"), InstId);
                Failure->SetArrayField(
                    TEXT("part_failures"), InstancePartFailures);
                PartStateFailures.Add(MakeShared<FJsonValueObject>(Failure));
            }
        }

        const TSharedPtr<FJsonObject>* SpatialObj = nullptr;
        if (InterfacesObj
            && (*InterfacesObj)->TryGetObjectField(TEXT("I3D_Spatial"), SpatialObj)
            && SpatialObj && SpatialObj->IsValid())
        {
            bool bSpatialSchemaValid = true;
            auto ReadNumber = [SpatialObj, &bSpatialSchemaValid](
                const TCHAR* Field, double DefaultValue)
            {
                double Value = DefaultValue;
                if (!(*SpatialObj)->TryGetNumberField(Field, Value) || !FMath::IsFinite(Value))
                {
                    bSpatialSchemaValid = false;
                    return DefaultValue;
                }
                return Value;
            };
            const FVector ExpectedLocation(
                ReadNumber(TEXT("translation_x"), 0.0),
                ReadNumber(TEXT("translation_y"), 0.0),
                ReadNumber(TEXT("translation_z"), 0.0));
            const FRotator ExpectedRotation(
                ReadNumber(TEXT("rotation_y"), 0.0),
                ReadNumber(TEXT("rotation_z"), 0.0),
                ReadNumber(TEXT("rotation_x"), 0.0));
            const FVector ExpectedScale(
                ReadNumber(TEXT("scale_x"), 1.0),
                ReadNumber(TEXT("scale_y"), 1.0),
                ReadNumber(TEXT("scale_z"), 1.0));
            if (bSpatialSchemaValid)
            {
                ++SpatialSnapshots;
                constexpr double LocationToleranceCm = 0.01;
                constexpr double ScaleTolerance = 1.0e-5;
                constexpr double RotationToleranceDegrees = 0.01;
                const FVector ActualLocation = Inst->GetActorLocation();
                const FVector ActualScale = Inst->GetActorScale3D();
                const FQuat ExpectedQuat = ExpectedRotation.Quaternion();
                const FQuat ActualQuat = Inst->GetActorQuat();
                const double RotationErrorDegrees = FMath::RadiansToDegrees(
                    ActualQuat.AngularDistance(ExpectedQuat));
                const bool bLocationMatches = ActualLocation.Equals(
                    ExpectedLocation, LocationToleranceCm);
                const bool bScaleMatches = ActualScale.Equals(
                    ExpectedScale, ScaleTolerance);
                const bool bRotationMatches =
                    RotationErrorDegrees <= RotationToleranceDegrees;

                if (!bLocationMatches || !bScaleMatches || !bRotationMatches)
                {
                    auto VectorToJson = [](const FVector& Value)
                    {
                        TSharedPtr<FJsonObject> Object = MakeShared<FJsonObject>();
                        Object->SetNumberField(TEXT("x"), Value.X);
                        Object->SetNumberField(TEXT("y"), Value.Y);
                        Object->SetNumberField(TEXT("z"), Value.Z);
                        return Object;
                    };
                    TSharedPtr<FJsonObject> Mismatch = MakeShared<FJsonObject>();
                    Mismatch->SetStringField(TEXT("instance_id"), InstId);
                    Mismatch->SetObjectField(
                        TEXT("expected_location_cm"), VectorToJson(ExpectedLocation));
                    Mismatch->SetObjectField(
                        TEXT("actual_location_cm"), VectorToJson(ActualLocation));
                    Mismatch->SetObjectField(
                        TEXT("expected_scale"), VectorToJson(ExpectedScale));
                    Mismatch->SetObjectField(
                        TEXT("actual_scale"), VectorToJson(ActualScale));
                    Mismatch->SetNumberField(
                        TEXT("rotation_error_degrees"), RotationErrorDegrees);
                    Mismatch->SetBoolField(
                        TEXT("location_matches"), bLocationMatches);
                    Mismatch->SetBoolField(TEXT("scale_matches"), bScaleMatches);
                    Mismatch->SetBoolField(
                        TEXT("rotation_matches"), bRotationMatches);
                    SpatialMismatches.Add(MakeShared<FJsonValueObject>(Mismatch));
                }
            }
            else
            {
                ++SpatialSchemaErrors;
                SpatialSchemaErrorInstances.Add(MakeShared<FJsonValueString>(InstId));
            }
        }
        else
        {
            ++SpatialSchemaErrors;
            SpatialSchemaErrorInstances.Add(MakeShared<FJsonValueString>(InstId));
        }

        // FR-5：记录回写基线 = 数据库此刻给的 transform（提交时 diff 用）
        PreviewBaseline.Add(InstId, Inst->GetActorTransform());

        PreviewActors.Add(Inst);
        Count++;
    }

    TSharedPtr<FJsonObject> Audit = MakeShared<FJsonObject>();
    FTCHARToUTF8 SnapshotUtf8(*JsonPayload);
    Audit->SetStringField(TEXT("schema_version"), TEXT("zhhz_ue_preview_audit_v1"));
    Audit->SetStringField(TEXT("source"), SourceLabel);
    Audit->SetStringField(
        TEXT("snapshot_md5"),
        FMD5::HashBytes(
            reinterpret_cast<const uint8*>(SnapshotUtf8.Get()),
            static_cast<uint64>(SnapshotUtf8.Length())));
    Audit->SetBoolField(TEXT("transient"), Count > 0 && TransientActors == Count);
    Audit->SetBoolField(TEXT("level_save_requested"), false);
    Audit->SetNumberField(TEXT("requested_instances"), Arr.Num());
    Audit->SetNumberField(TEXT("spawned_instances"), Count);
    Audit->SetNumberField(TEXT("expected_render_parts"), ExpectedRenderParts);
    Audit->SetNumberField(TEXT("loaded_render_parts"), LoadedRenderParts);
    Audit->SetNumberField(TEXT("assembly_instances"), AssemblyInstances);
    Audit->SetNumberField(TEXT("complete_assemblies"), CompleteAssemblies);
    Audit->SetNumberField(
        TEXT("part_state_valid_assemblies"), PartStateValidAssemblies);
    Audit->SetNumberField(TEXT("spatial_snapshots"), SpatialSnapshots);
    Audit->SetNumberField(TEXT("spatial_schema_errors"), SpatialSchemaErrors);
    Audit->SetNumberField(TEXT("malformed_snapshots"), MalformedSnapshots);
    Audit->SetNumberField(TEXT("transient_actors"), TransientActors);
    Audit->SetArrayField(TEXT("incomplete_assemblies"), IncompleteAssemblies);
    Audit->SetArrayField(TEXT("part_state_failures"), PartStateFailures);
    Audit->SetArrayField(TEXT("spatial_mismatch_instances"), SpatialMismatches);
    Audit->SetArrayField(
        TEXT("spatial_schema_error_instances"), SpatialSchemaErrorInstances);
    Audit->SetArrayField(TEXT("non_transient_instances"), NonTransientInstances);
    const bool bRequireAssemblies = SourceLabel == TEXT("migration_snapshot_file");
    const bool bAuditPassed =
        Arr.Num() > 0
            && Count > 0
            && Count == Arr.Num()
            && MalformedSnapshots == 0
            && SpatialSnapshots == Count
            && SpatialSchemaErrors == 0
            && TransientActors == Count
            && ExpectedRenderParts == LoadedRenderParts
            && IncompleteAssemblies.Num() == 0
            && PartStateFailures.Num() == 0
            && SpatialMismatches.Num() == 0
            && (!bRequireAssemblies
                || (AssemblyInstances == Count
                    && CompleteAssemblies == Count
                    && PartStateValidAssemblies == Count
                    && ExpectedRenderParts > 0));
    Audit->SetBoolField(TEXT("passed"), bAuditPassed);

    FString AuditJson;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&AuditJson);
    FJsonSerializer::Serialize(Audit.ToSharedRef(), Writer);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AuditPath), true);
    const bool bAuditSaved = FFileHelper::SaveStringToFile(
        AuditJson,
        *AuditPath,
        FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    if (bAuditSaved)
    {
        UE_LOG(LogTemp, Log,
            TEXT("[孪生管理器] 预览审计 %s：%d 个 transient Actor；部件 %d/%d；完整装配 %d/%d；逐部件状态 %d/%d；审计=%s"),
            bAuditPassed ? TEXT("PASS") : TEXT("FAIL"),
            Count, LoadedRenderParts, ExpectedRenderParts,
            CompleteAssemblies, AssemblyInstances,
            PartStateValidAssemblies, AssemblyInstances, *AuditPath);
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(
                -1,
                12.0f,
                bAuditPassed ? FColor::Green : FColor::Red,
                FString::Printf(
                    TEXT("迁移预览审计 %s：实例 %d，渲染部件 %d/%d"),
                    bAuditPassed ? TEXT("PASS") : TEXT("FAIL"),
                    Count,
                    LoadedRenderParts,
                    ExpectedRenderParts));
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 无法写入预览审计"));
    }
    return Count;
#else
    return 0;
#endif
}
