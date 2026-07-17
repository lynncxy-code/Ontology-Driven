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
#include "TwinInstance.h"
#include "SceneInteraction/TwinInteractionManagerComponent.h"
#include "IWebSocket.h"
#include "WebSocketsModule.h"
#include "Modules/ModuleManager.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Blueprint/UserWidget.h"
#include "Components/InputComponent.h"
#include "Components/PrimitiveComponent.h"
// FR-6 迁移工具用
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/App.h"
#include "HAL/FileManager.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
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
}

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinSceneManager::ATwinSceneManager()
{
    PrimaryActorTick.bCanEverTick = true;
    InteractionManager = CreateDefaultSubobject<UTwinInteractionManagerComponent>(TEXT("SceneInteractionManager"));
    UEProjectName = FApp::GetProjectName();
    UEProjectId = FString::Printf(TEXT("ueproj_%s"), *UEProjectName);
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinSceneManager::BeginPlay()
{
    Super::BeginPlay();
    SetActorTickEnabled(true);

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

    UpdateOverlayPointerInput(
        PC,
        bEnableOverlays && bHasSelectedOverlay && !bInteractionOwnsSelection && !bRuntimeEditMode);

    if (!bEnableOverlays)
    {
        ClearOverlaySelection();
        return;
    }

    if (!bInteractionOwnsSelection && !bPointerOverRuntimePanel
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
            || (bInteractionOwnsSelection
                ? !OverlaySelectedInstance->HasOverlay()
                : !OverlaySelectedInstance->HasSelectedOverlay())))
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
        }

        FVector2D ScreenPosition;
        int32 ViewportX = 0;
        int32 ViewportY = 0;
        PC->GetViewportSize(ViewportX, ViewportY);
        const bool bProjected = PC->ProjectWorldLocationToScreen(
            OverlaySelectedInstance->GetOverlayAnchorWorldLocation(), ScreenPosition, true);
        const bool bOnScreen = bProjected && ScreenPosition.X >= 0.0f && ScreenPosition.Y >= 0.0f
            && ScreenPosition.X <= ViewportX && ScreenPosition.Y <= ViewportY;
        SelectedOverlayWidget->SetVisibility(
            bOnScreen ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
        if (bOnScreen)
        {
            SelectedOverlayWidget->SetPositionInViewport(ScreenPosition, false);
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

void ATwinSceneManager::SelectOverlayInstance(ATwinInstance* Instance, bool bAllowAnyMode)
{
    if (!Instance || !IsValid(Instance)
        || (bAllowAnyMode ? !Instance->HasOverlay() : !Instance->HasSelectedOverlay()))
    {
        return;
    }
    if (OverlaySelectedInstance != Instance)
    {
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
        SelectedOverlayWidget->SetAlignmentInViewport(FVector2D(0.5f, 1.0f));
        SelectedOverlayWidget->AddToViewport(900);
    }
}

void ATwinSceneManager::ClearOverlaySelection()
{
    OverlaySelectedInstance = nullptr;
    SelectedOverlayPayloadSerial = 0;
    if (SelectedOverlayWidget && IsValid(SelectedOverlayWidget))
    {
        SelectedOverlayWidget->RemoveFromParent();
    }
    SelectedOverlayWidget = nullptr;
}

void ATwinSceneManager::SelectOverlayFromSceneInteraction(ATwinInstance* Instance)
{
    SelectOverlayInstance(Instance, true);
}

void ATwinSceneManager::ClearOverlayFromSceneInteraction()
{
    ClearOverlaySelection();
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

    UE_LOG(LogTemp, Log,
           TEXT("[孪生管理器] 轮询中... 场景=%s | 现有实例数=%d"),
           SceneId.IsEmpty() ? TEXT("(跟随后端)") : *SceneId, InstanceRegistry.Num());

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
        FHttpModule::Get().CreateRequest();

    FString Url = BuildSnapshotsUrl();
    HttpRequest->SetURL(Url);
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);

    HttpRequest->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnPollResponse);

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

void ATwinSceneManager::ProcessSnapshot(const TSharedPtr<FJsonObject>& Snapshot)
{
    FString InstanceId;
    Snapshot->TryGetStringField(TEXT("instanceId"), InstanceId);

    // ── 已存在：更新状态 ─────────────────────────────────────────────────
    ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
    if (Found && *Found && IsValid(*Found))
    {
        (*Found)->ApplySnapshot(Snapshot);
        return;
    }

    // ── 不存在：创建新实例 ───────────────────────────────────────────────
    ATwinInstance* NewInst = SpawnTwinInstance(InstanceId, Snapshot);
    if (NewInst)
    {
        InstanceRegistry.Add(InstanceId, NewInst);
        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 新增实例: %s"), *InstanceId);
    }
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

void ATwinSceneManager::ExportSelectedActorsForMigration()
{
#if WITH_EDITOR
    // 扫描「待迁移文件夹」而非当前选择集：UE 细节面板多选不同类型 Actor 时，
    // 只显示共同按钮，Manager 专属按钮会被隐藏——无法"同时选中 actor + Manager"
    // 再点击本按钮。改用文件夹两步走：先把 actor 移进文件夹，再单独选中 Manager 点击。
    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GetWorld();
    if (!World)
    {
        return;
    }

    FString TargetFolder = MigrationFolderName;
    TargetFolder.TrimStartAndEndInline();
    TArray<TSharedPtr<FJsonValue>> ActorsJson;
    int32 Count = 0;

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || A == this) continue;
        // 已受管的孪生体不迁移（它本就来自 DB）
        if (A->IsA(ATwinInstance::StaticClass())) continue;
        // 导出「待迁移文件夹」及其全部子文件夹下的 actor
        if (!IsInFolderOrChild(A->GetFolderPath(), TargetFolder)) continue;

        TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
        Obj->SetStringField(TEXT("ext_guid"),
            A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens));
        Obj->SetStringField(TEXT("name"), A->GetActorLabel());
        Obj->SetStringField(TEXT("actor_label"), A->GetActorLabel());
        Obj->SetStringField(TEXT("actor_name"), A->GetName());
        Obj->SetStringField(TEXT("source_folder_path"), A->GetFolderPath().ToString());
        if (UClass* ActorClass = A->GetClass())
        {
            Obj->SetStringField(TEXT("actor_class"), ActorClass->GetName());
            Obj->SetStringField(TEXT("actor_class_path"), ActorClass->GetPathName());
            if (ActorClass->ClassGeneratedBy)
            {
                Obj->SetStringField(TEXT("blueprint_class_path"), ActorClass->ClassGeneratedBy->GetPathName());
            }
        }

        // 取第一个静态网格组件的资产路径（/Game/... 或引擎资产）
        FString MeshAsset;
        TArray<UStaticMeshComponent*> StaticMeshComponents;
        A->GetComponents<UStaticMeshComponent>(StaticMeshComponents);
        TArray<TSharedPtr<FJsonValue>> StaticMeshAssets;
        if (StaticMeshComponents.Num() > 0)
        {
            for (UStaticMeshComponent* SMC : StaticMeshComponents)
            {
                if (SMC && SMC->GetStaticMesh())
                {
                    const FString Path = SMC->GetStaticMesh()->GetPathName();
                    if (MeshAsset.IsEmpty())
                    {
                        MeshAsset = Path;
                    }
                    StaticMeshAssets.Add(MakeShared<FJsonValueString>(Path));
                }
            }
        }
        Obj->SetStringField(TEXT("mesh_asset"), MeshAsset);
        Obj->SetStringField(TEXT("static_mesh_asset"), MeshAsset);
        Obj->SetArrayField(TEXT("static_mesh_assets"), StaticMeshAssets);

        FString SkeletalMeshAsset;
        TArray<USkeletalMeshComponent*> SkeletalMeshComponents;
        A->GetComponents<USkeletalMeshComponent>(SkeletalMeshComponents);
        TArray<TSharedPtr<FJsonValue>> SkeletalMeshAssets;
        for (USkeletalMeshComponent* SKC : SkeletalMeshComponents)
        {
            if (SKC && SKC->GetSkeletalMeshAsset())
            {
                const FString Path = SKC->GetSkeletalMeshAsset()->GetPathName();
                if (SkeletalMeshAsset.IsEmpty())
                {
                    SkeletalMeshAsset = Path;
                }
                SkeletalMeshAssets.Add(MakeShared<FJsonValueString>(Path));
            }
        }
        Obj->SetStringField(TEXT("skeletal_mesh_asset"), SkeletalMeshAsset);
        Obj->SetArrayField(TEXT("skeletal_mesh_assets"), SkeletalMeshAssets);

        TSharedPtr<FJsonObject> ComponentSummary = MakeShared<FJsonObject>();
        ComponentSummary->SetNumberField(TEXT("static_mesh_components"), StaticMeshComponents.Num());
        ComponentSummary->SetNumberField(TEXT("skeletal_mesh_components"), SkeletalMeshComponents.Num());
        Obj->SetObjectField(TEXT("component_summary"), ComponentSummary);

        const FVector Loc = A->GetActorLocation();
        const FRotator Rot = A->GetActorRotation();
        const FVector Scale = A->GetActorScale3D();
        TSharedPtr<FJsonObject> TF = MakeShared<FJsonObject>();
        TF->SetNumberField(TEXT("tx"), Loc.X);
        TF->SetNumberField(TEXT("ty"), Loc.Y);
        TF->SetNumberField(TEXT("tz"), Loc.Z);
        // 与 ApplySpatialFromSnapshot 的约定对齐：rx=Roll, ry=Pitch, rz=Yaw
        TF->SetNumberField(TEXT("rx"), Rot.Roll);
        TF->SetNumberField(TEXT("ry"), Rot.Pitch);
        TF->SetNumberField(TEXT("rz"), Rot.Yaw);
        TF->SetNumberField(TEXT("sx"), Scale.X);
        TF->SetNumberField(TEXT("sy"), Scale.Y);
        TF->SetNumberField(TEXT("sz"), Scale.Z);
        Obj->SetObjectField(TEXT("transform"), TF);

        ActorsJson.Add(MakeShared<FJsonValueObject>(Obj));
        Count++;
    }

    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
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
    const bool bOk = FFileHelper::SaveStringToFile(OutStr, *Path);

    UE_LOG(LogTemp, Log, TEXT("[迁移] 文件夹「%s」及其子文件夹导出 %d 个 actor → %s (%s)"),
           *MigrationFolderName, Count, *Path, bOk ? TEXT("成功") : TEXT("写入失败"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.0f,
            bOk ? FColor::Green : FColor::Red,
            Count > 0
                ? FString::Printf(TEXT("导出 %d 个 actor → %s\n把它交给后端 migrate_ue_actors.py"),
                                   Count, *Path)
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

    // 结果文件是 {ext_guid: instance_id}，收集已成功迁移的 guid
    TSet<FString> MigratedGuids;
    for (const auto& Pair : Root->Values)
    {
        MigratedGuids.Add(Pair.Key);
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
        if (World->EditorDestroyActor(A, /*bShouldModifyLevel=*/true))
        {
            Deleted++;
        }
    }

    UE_LOG(LogTemp, Log, TEXT("[迁移] 已删除 %d 个已收编的原 actor（共匹配 %d）"),
           Deleted, ToDelete.Num());
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

    TArray<TSharedPtr<FJsonValue>> Arr;
    TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(Response->GetContentAsString());
    if (!FJsonSerializer::Deserialize(Reader, Arr))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 预览 JSON 解析失败"));
        return;
    }

    UWorld* World = GetWorld();
    if (!World) return;

    UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();
    int32 Count = 0;

    for (const auto& Val : Arr)
    {
        const TSharedPtr<FJsonObject>* SnapObj;
        if (!Val->TryGetObject(SnapObj)) continue;

        FString InstId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstId)) continue;

        FString AssetPathStr;
        const TSharedPtr<FJsonObject>* InterfacesObj;
        if ((*SnapObj)->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
        {
            const TSharedPtr<FJsonObject>* RepObj;
            if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
            {
                (*RepObj)->TryGetStringField(TEXT("asset_id"), AssetPathStr);
            }
        }

        // 关键：RF_Transient → 保存关卡时绝不写入 .umap（杜绝“误固化”）
        FActorSpawnParameters SpawnParams;
        SpawnParams.ObjectFlags |= RF_Transient;

        ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
            SpawnClass, FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
        if (!Inst) continue;

        FString DisplayName;
        if (!(*SnapObj)->TryGetStringField(TEXT("displayName"), DisplayName) || DisplayName.IsEmpty())
        {
            DisplayName = InstId;
        }
        Inst->SetActorLabel(FString::Printf(TEXT("[预览] %s"), *DisplayName));
        Inst->SetFolderPath(BuildTwinFolderPath(*SnapObj, TEXT("TwinPreview")));
        Inst->InitializeTwin(InstId, AssetPathStr, BackendBaseUrl);
        Inst->ApplySnapshot(*SnapObj);   // 应用位置/材质等，摆到正确位置

        // FR-5：记录回写基线 = 数据库此刻给的 transform（提交时 diff 用）
        PreviewBaseline.Add(InstId, Inst->GetActorTransform());

        PreviewActors.Add(Inst);
        Count++;
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 预览已生成 %d 个 transient Actor"), Count);
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green,
            FString::Printf(TEXT("预览已生成 %d 个（transient，不会存进关卡）"), Count));
    }
#endif
}
