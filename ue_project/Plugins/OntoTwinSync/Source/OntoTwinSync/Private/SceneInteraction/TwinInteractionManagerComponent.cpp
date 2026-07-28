#include "SceneInteraction/TwinInteractionManagerComponent.h"

#include "SceneInteraction/OntoTwinCrosshairWidget.h"
#include "SceneInteraction/OntoTwinRoamingHUDWidget.h"
#include "SceneInteraction/TwinCameraModeComponent.h"
#include "SceneInteraction/TwinGodViewPawn.h"
#include "SceneInteraction/TwinRoamingCharacter.h"
#include "SceneInteraction/TwinRoamingRoute.h"
#include "SceneInteraction/TwinRoamingSpawnAnchor.h"
#include "SceneInteraction/TwinRouteFollowerComponent.h"
#include "SceneInteraction/TwinSkinComponent.h"
#include "TwinInstance.h"
#include "TwinSceneManager.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Components/CapsuleComponent.h"
#include "Components/SplineComponent.h"
#include "Dom/JsonValue.h"
#include "Engine/AssetManager.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/Level.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/PlayerController.h"
#include "HttpModule.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Interfaces/IHttpResponse.h"
#include "Kismet/GameplayStatics.h"
#include "Widgets/Layout/Anchors.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
const TSharedPtr<FJsonObject> GetObject(const TSharedPtr<FJsonObject>& Parent, const TCHAR* Field)
{
    if (!Parent.IsValid()) return nullptr;
    const TSharedPtr<FJsonObject>* Result = nullptr;
    return Parent->TryGetObjectField(Field, Result) && Result ? *Result : nullptr;
}

double NumberOr(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, double Default)
{
    double Value = Default;
    return Object.IsValid() && Object->TryGetNumberField(Field, Value) ? Value : Default;
}

bool BoolOr(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, bool Default)
{
    bool Value = Default;
    return Object.IsValid() && Object->TryGetBoolField(Field, Value) ? Value : Default;
}

FString StringOr(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, const FString& Default = FString())
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Field, Value) ? Value : Default;
}

FString NormalizeLevelPackageName(FString Value)
{
    Value.TrimStartAndEndInline();
    int32 ObjectSeparator = INDEX_NONE;
    if (Value.FindChar(TEXT('.'), ObjectSeparator)) Value.LeftInline(ObjectSeparator);

    int32 LastSlash = INDEX_NONE;
    Value.FindLastChar(TEXT('/'), LastSlash);
    FString Prefix = LastSlash == INDEX_NONE ? FString() : Value.Left(LastSlash + 1);
    FString Leaf = LastSlash == INDEX_NONE ? Value : Value.Mid(LastSlash + 1);
    if (Leaf.StartsWith(TEXT("UEDPIE_")))
    {
        const int32 NameSeparator = Leaf.Find(
            TEXT("_"), ESearchCase::CaseSensitive, ESearchDir::FromStart, 7);
        if (NameSeparator != INDEX_NONE) Leaf = Leaf.Mid(NameSeparator + 1);
    }
    return Prefix + Leaf;
}

FString CameraModeId(ETwinRoamingCameraMode Mode)
{
    if (Mode == ETwinRoamingCameraMode::FirstPerson) return TEXT("first_person");
    if (Mode == ETwinRoamingCameraMode::God) return TEXT("god");
    return TEXT("near_follow");
}

FString CameraModeLabel(ETwinRoamingCameraMode Mode)
{
    if (Mode == ETwinRoamingCameraMode::FirstPerson) return TEXT("第一人称");
    if (Mode == ETwinRoamingCameraMode::God) return TEXT("全局视角");
    return TEXT("过肩视角");
}

FString CompactHudLabel(const FString& Value, const TCHAR* Fallback, int32 MaxCharacters = 24)
{
    FString Result = Value.TrimStartAndEnd();
    if (Result.IsEmpty()) Result = Fallback;
    if (Result.Len() > MaxCharacters)
    {
        Result = Result.Left(MaxCharacters - 1) + TEXT("…");
    }
    return Result;
}
}

UTwinInteractionManagerComponent::UTwinInteractionManagerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UTwinInteractionManagerComponent::BeginPlay()
{
    Super::BeginPlay();
    bShuttingDown = false;
    SceneManager = Cast<ATwinSceneManager>(GetOwner());
    PlayerController = UGameplayStatics::GetPlayerController(this, 0);
    if (!SceneManager)
    {
        RuntimeState = TEXT("blocked");
        LastError = TEXT("TwinInteractionManager must be owned by ATwinSceneManager");
        SetComponentTickEnabled(false);
        return;
    }
    SetupInput();
    PollRuntimeProjection();
}

void UTwinInteractionManagerComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bShuttingDown = true;
    ExitRoaming();
    RemoveInput();
    Super::EndPlay(EndPlayReason);
}

void UTwinInteractionManagerComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!SceneManager) return;
    if (!PlayerController)
    {
        PlayerController = UGameplayStatics::GetPlayerController(this, 0);
        if (PlayerController) SetupInput();
    }

    PollAccumulator += DeltaTime;
    if (PollAccumulator >= RuntimePollInterval)
    {
        PollAccumulator = 0.0f;
        PollRuntimeProjection();
    }

    HeartbeatAccumulator += DeltaTime;
    if (HeartbeatAccumulator >= 2.0f)
    {
        HeartbeatAccumulator = 0.0f;
        SendHeartbeat();
    }

    // F7 is the global entry/exit switch. Poll it directly so it remains
    // available even when the host project replaces or reorders Enhanced
    // Input components while possessing a different pawn.
    if (PlayerController && PlayerController->WasInputKeyJustPressed(ToggleRoamingKey))
    {
        ToggleRoaming();
    }

    if (!bEnhancedInputReady)
    {
        TickFallbackInput(DeltaTime);
    }
    UpdateCrosshairTarget();
    RefreshHud();
}

void UTwinInteractionManagerComponent::AddProjectHeaders(
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

void UTwinInteractionManagerComponent::PollRuntimeProjection()
{
    if (bShuttingDown || !SceneManager || bRuntimeRequestInFlight) return;
    bRuntimeRequestInFlight = true;

    FString BaseUrl = SceneManager->BackendBaseUrl;
    BaseUrl.RemoveFromEnd(TEXT("/"));
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl + TEXT("/api/v2/scene-interactions/runtime"));
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddProjectHeaders(Request);

    const TWeakObjectPtr<UTwinInteractionManagerComponent> WeakThis(this);
    Request->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr, FHttpResponsePtr Response, bool bWasSuccessful)
        {
            UTwinInteractionManagerComponent* Self = WeakThis.Get();
            if (!Self || Self->bShuttingDown) return;
            Self->bRuntimeRequestInFlight = false;
            if (!bWasSuccessful || !Response.IsValid())
            {
                Self->RecordBackendFailure(TEXT("Scene Interaction backend is unreachable"));
                return;
            }
            if (Response->GetResponseCode() == 403)
            {
                Self->bBackendOnline = true;
                Self->RuntimeState = TEXT("blocked");
                Self->LastError = Response->GetContentAsString();
                Self->ExitRoaming();
                Self->RuntimeState = TEXT("blocked");
                return;
            }
            if (Response->GetResponseCode() < 200 || Response->GetResponseCode() >= 300)
            {
                Self->RecordBackendFailure(FString::Printf(
                    TEXT("Runtime projection HTTP %d"), Response->GetResponseCode()));
                return;
            }

            TSharedPtr<FJsonObject> Payload;
            const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
            if (!FJsonSerializer::Deserialize(Reader, Payload) || !Payload.IsValid())
            {
                Self->RecordBackendFailure(TEXT("Runtime projection returned invalid JSON"));
                return;
            }
            Self->bBackendOnline = true;
            Self->ConsecutiveFailures = 0;
            Self->HandleRuntimeProjection(Payload);
        });
    if (!Request->ProcessRequest())
    {
        bRuntimeRequestInFlight = false;
        RecordBackendFailure(TEXT("Runtime projection request could not be started"));
    }
}

void UTwinInteractionManagerComponent::RecordBackendFailure(const FString& Error)
{
    ++ConsecutiveFailures;
    LastError = Error;
    if (ConsecutiveFailures >= RuntimeOfflineThreshold)
    {
        bBackendOnline = false;
        RuntimeState = TEXT("offline");
    }
}

bool UTwinInteractionManagerComponent::ParseRuntimeConfig(
    const TSharedPtr<FJsonObject>& Payload,
    FTwinRoamingRuntimeConfig& OutConfig,
    int32& OutRevision,
    FString& OutToken,
    FString& OutCatalogVersion,
    FString& OutBlockedReason) const
{
    if (!Payload.IsValid()) return false;
    OutRevision = FMath::Max(0, FMath::RoundToInt(NumberOr(Payload, TEXT("revision"), 0.0)));
    OutToken = StringOr(Payload, TEXT("runtime_token"));
    OutCatalogVersion = StringOr(Payload, TEXT("catalog_version"));
    OutBlockedReason = StringOr(Payload, TEXT("blocked_reason"));

    const TSharedPtr<FJsonObject> Config = GetObject(Payload, TEXT("config"));
    if (!Config.IsValid()) return false;
    OutConfig.bEnabled = BoolOr(Config, TEXT("enabled"), false);
    OutConfig.bAutoEnter = BoolOr(Config, TEXT("auto_enter"), false);
    OutConfig.CharacterId = StringOr(Config, TEXT("character_id"));
    OutConfig.DefaultSkinId = StringOr(Config, TEXT("default_skin_id"));

    const TSharedPtr<FJsonObject> Spawn = GetObject(Config, TEXT("spawn_ue"));
    if (OutConfig.bEnabled && !Spawn.IsValid()) return false;
    OutConfig.bSpawnFromAnchor = StringOr(Spawn, TEXT("mode")) == TEXT("ue_anchor");
    OutConfig.SpawnAnchorId = StringOr(Spawn, TEXT("anchor_id"));
    OutConfig.SpawnLocation.X = NumberOr(Spawn, TEXT("x_cm"), 0.0);
    OutConfig.SpawnLocation.Y = NumberOr(Spawn, TEXT("y_cm"), 0.0);
    OutConfig.SpawnTraceOriginZCm = NumberOr(Spawn, TEXT("trace_origin_z_cm"), 1000.0);
    OutConfig.SpawnYawDeg = NumberOr(Spawn, TEXT("yaw_deg"), 0.0);
    double ZHint = 0.0;
    OutConfig.bHasZHint = Spawn.IsValid() && Spawn->TryGetNumberField(TEXT("z_hint_cm"), ZHint);
    OutConfig.ZHintCm = ZHint;

    const TSharedPtr<FJsonObject> Movement = GetObject(Config, TEXT("movement"));
    OutConfig.Movement.WalkSpeedCmS = NumberOr(Movement, TEXT("walk_speed_cm_s"), 250.0);
    OutConfig.Movement.SprintSpeedCmS = NumberOr(Movement, TEXT("sprint_speed_cm_s"), 500.0);
    OutConfig.Movement.AutoRouteSpeedCmS = NumberOr(Movement, TEXT("auto_route_speed_cm_s"), 180.0);
    OutConfig.Movement.JumpHeightCm = NumberOr(Movement, TEXT("jump_height_cm"), 80.0);

    const TSharedPtr<FJsonObject> Camera = GetObject(Config, TEXT("camera"));
    const FString DefaultCameraMode = StringOr(Camera, TEXT("default_mode"));
    if (DefaultCameraMode == TEXT("first_person"))
    {
        OutConfig.DefaultCameraMode = ETwinRoamingCameraMode::FirstPerson;
    }
    else if (DefaultCameraMode == TEXT("god"))
    {
        OutConfig.DefaultCameraMode = ETwinRoamingCameraMode::God;
    }
    else
    {
        OutConfig.DefaultCameraMode = ETwinRoamingCameraMode::NearFollow;
    }
    const TSharedPtr<FJsonObject> FirstPerson = GetObject(Camera, TEXT("first_person"));
    OutConfig.FirstPersonCamera.EyeHeightCm = NumberOr(
        FirstPerson, TEXT("eye_height_cm"), 165.0);
    OutConfig.FirstPersonCamera.FovDeg = NumberOr(
        FirstPerson, TEXT("fov_deg"), 85.0);
    OutConfig.FirstPersonCamera.LookSensitivity = NumberOr(
        FirstPerson, TEXT("look_sensitivity"), 1.0);
    const TSharedPtr<FJsonObject> Near = GetObject(Camera, TEXT("near_follow"));
    OutConfig.NearCamera.DistanceCm = NumberOr(Near, TEXT("distance_cm"), 120.0);
    OutConfig.NearCamera.HeightCm = NumberOr(Near, TEXT("height_cm"), 35.0);
    OutConfig.NearCamera.LookSensitivity = NumberOr(Near, TEXT("look_sensitivity"), 1.0);
    const TSharedPtr<FJsonObject> God = GetObject(Camera, TEXT("god"));
    OutConfig.GodCamera.CameraId = StringOr(God, TEXT("camera_id"));
    OutConfig.GodCamera.MoveSpeedCmS = NumberOr(God, TEXT("move_speed_cm_s"), 1800.0);
    OutConfig.GodCamera.LookSensitivity = NumberOr(God, TEXT("look_sensitivity"), 1.0);

    const TSharedPtr<FJsonObject> RouteConfig = GetObject(Config, TEXT("route"));
    OutConfig.bRouteEnabled = BoolOr(RouteConfig, TEXT("enabled"), false);
    OutConfig.bRouteAutoStart = BoolOr(RouteConfig, TEXT("auto_start"), true);
    OutConfig.bTakeoverEnabled = BoolOr(RouteConfig, TEXT("takeover_enabled"), true);
    OutConfig.bRouteLoop = StringOr(RouteConfig, TEXT("completion_mode")) == TEXT("loop");
    OutConfig.RouteId = StringOr(RouteConfig, TEXT("route_id"));

    const TSharedPtr<FJsonObject> Resources = GetObject(Payload, TEXT("resources"));
    const TSharedPtr<FJsonObject> Character = GetObject(Resources, TEXT("character"));
    OutConfig.CharacterDisplayName = StringOr(
        Character, TEXT("display_name"), OutConfig.CharacterId);
    OutConfig.CharacterPrimaryAssetId = StringOr(Character, TEXT("ue_primary_asset_id"));
    const TArray<TSharedPtr<FJsonValue>>* Skins = nullptr;
    if (Resources.IsValid() && Resources->TryGetArrayField(TEXT("skins"), Skins) && Skins)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Skins)
        {
            const TSharedPtr<FJsonObject> Skin = Value.IsValid() ? Value->AsObject() : nullptr;
            const FString Id = StringOr(Skin, TEXT("id"));
            const FString PrimaryId = StringOr(Skin, TEXT("ue_primary_asset_id"));
            if (!Id.IsEmpty() && !PrimaryId.IsEmpty()) OutConfig.SkinPrimaryAssetIds.Add(Id, PrimaryId);
        }
    }
    const TSharedPtr<FJsonObject> RouteResource = GetObject(Resources, TEXT("route"));
    OutConfig.RouteDisplayName = StringOr(RouteResource, TEXT("display_name"));
    if (OutConfig.bRouteEnabled)
    {
        OutConfig.RouteId = StringOr(RouteResource, TEXT("ue_route_id"), OutConfig.RouteId);
    }

    const TSharedPtr<FJsonObject> RuntimeRoute = GetObject(Payload, TEXT("runtime_route"));
    if (OutConfig.bRouteEnabled && RuntimeRoute.IsValid())
    {
        OutConfig.RouteId = StringOr(RuntimeRoute, TEXT("route_id"), OutConfig.RouteId);
        OutConfig.RuntimeRouteRevision = FMath::Max(
            0, FMath::RoundToInt(NumberOr(RuntimeRoute, TEXT("route_revision"), 0.0)));
        OutConfig.RuntimeRouteLevel = NormalizeLevelPackageName(
            StringOr(RuntimeRoute, TEXT("ue_level")));
        OutConfig.RuntimeRouteGroundZHintCm = NumberOr(
            RuntimeRoute, TEXT("floor_ground_z_hint_cm"), 0.0);
        OutConfig.bRouteLoop = BoolOr(RuntimeRoute, TEXT("loop"), OutConfig.bRouteLoop);
        OutConfig.Movement.AutoRouteSpeedCmS = NumberOr(
            RuntimeRoute, TEXT("speed_cm_s"), OutConfig.Movement.AutoRouteSpeedCmS);

        const TArray<TSharedPtr<FJsonValue>>* Waypoints = nullptr;
        if (!RuntimeRoute->TryGetArrayField(TEXT("waypoints_ue_cm"), Waypoints)
            || !Waypoints || Waypoints->Num() < 2)
        {
            return false;
        }
        for (const TSharedPtr<FJsonValue>& Value : *Waypoints)
        {
            if (!Value.IsValid() || Value->Type != EJson::Array) return false;
            const TArray<TSharedPtr<FJsonValue>>& Coordinates = Value->AsArray();
            if (Coordinates.Num() < 3
                || !Coordinates[0].IsValid() || Coordinates[0]->Type != EJson::Number
                || !Coordinates[1].IsValid() || Coordinates[1]->Type != EJson::Number
                || !Coordinates[2].IsValid() || Coordinates[2]->Type != EJson::Number)
            {
                return false;
            }
            const FVector Point(
                Coordinates[0]->AsNumber(),
                Coordinates[1]->AsNumber(),
                Coordinates[2]->AsNumber());
            if (Point.ContainsNaN()) return false;
            OutConfig.RuntimeRoutePoints.Add(Point);
        }
        OutConfig.bHasRuntimeRoute = true;
    }
    const TSharedPtr<FJsonObject> CameraResource = GetObject(Resources, TEXT("god_camera"));
    OutConfig.GodCamera.CameraId = StringOr(
        CameraResource, TEXT("ue_camera_id"), OutConfig.GodCamera.CameraId);
    return true;
}

void UTwinInteractionManagerComponent::HandleRuntimeProjection(const TSharedPtr<FJsonObject>& Payload)
{
    FTwinRoamingRuntimeConfig Incoming;
    int32 Revision = 0;
    FString Token;
    FString IncomingCatalogVersion;
    FString BlockedReason;
    if (!ParseRuntimeConfig(Payload, Incoming, Revision, Token, IncomingCatalogVersion, BlockedReason))
    {
        RuntimeState = TEXT("blocked");
        LastError = TEXT("Runtime projection is incomplete");
        return;
    }

    const TSharedPtr<FJsonObject> Binding = GetObject(Payload, TEXT("binding"));
    const FString BindingMode = StringOr(Binding, TEXT("mode"));
    BindingWarning = BindingMode == TEXT("unbound_dev")
        ? StringOr(Binding, TEXT("warning"), TEXT("当前项目尚未绑定 UE 工程")) : FString();

    CatalogVersion = IncomingCatalogVersion;
    if (!Incoming.bEnabled)
    {
        CurrentConfig = Incoming;
        AppliedRevision = Revision;
        RuntimeToken = Token;
        if (bRoamingActive) ExitRoaming();
        RuntimeState = BlockedReason.IsEmpty() ? TEXT("disabled") : TEXT("blocked");
        LastError = BlockedReason;
        return;
    }

    if (RuntimeToken.IsEmpty() || !bRoamingActive)
    {
        CurrentConfig = Incoming;
        AppliedRevision = Revision;
        RuntimeToken = Token;
        RuntimeState = TEXT("available");
        LastError.Reset();
        if (Incoming.bAutoEnter && !bDefaultModeApplied)
        {
            FString Error;
            if (!EnterRoaming(Error))
            {
                RuntimeState = TEXT("blocked");
                LastError = Error;
            }
        }
        return;
    }

    if (Token == RuntimeToken) return;
    if (IsStructuralChange(CurrentConfig, Incoming))
    {
        PendingConfig = Incoming;
        PendingRevision = Revision;
        PendingRuntimeToken = Token;
        bPendingReload = true;
        RuntimeState = TEXT("reload_required");
    }
    else
    {
        CurrentConfig = Incoming;
        AppliedRevision = Revision;
        RuntimeToken = Token;
        ApplyHotConfig(CurrentConfig);
    }
}

bool UTwinInteractionManagerComponent::IsStructuralChange(
    const FTwinRoamingRuntimeConfig& A,
    const FTwinRoamingRuntimeConfig& B) const
{
    return A.CharacterPrimaryAssetId != B.CharacterPrimaryAssetId
        || A.bSpawnFromAnchor != B.bSpawnFromAnchor
        || A.SpawnAnchorId != B.SpawnAnchorId
        || !A.SpawnLocation.Equals(B.SpawnLocation, 0.1f)
        || !FMath::IsNearlyEqual(A.SpawnYawDeg, B.SpawnYawDeg, 0.1f)
        || A.bRouteEnabled != B.bRouteEnabled
        || A.RouteId != B.RouteId
        || A.bHasRuntimeRoute != B.bHasRuntimeRoute
        || A.RuntimeRouteRevision != B.RuntimeRouteRevision
        || A.RuntimeRouteLevel != B.RuntimeRouteLevel
        || A.GodCamera.CameraId != B.GodCamera.CameraId;
}

void UTwinInteractionManagerComponent::ApplyHotConfig(const FTwinRoamingRuntimeConfig& Config)
{
    bTakeoverEnabled = Config.bTakeoverEnabled;
    if (!RoamingCharacter) return;
    RoamingCharacter->ApplyMovementSettings(Config.Movement);
    RoamingCharacter->CameraMode->Configure(
        Config.FirstPersonCamera, Config.NearCamera, Config.GodCamera);
    RoamingCharacter->RouteFollower->SetSpeed(Config.Movement.AutoRouteSpeedCmS);
    RoamingCharacter->RouteFollower->SetLoop(Config.bRouteLoop);
    RoamingCharacter->SkinComponent->Configure(Config.SkinPrimaryAssetIds, Config.DefaultSkinId);
    if (RoamingCharacter->SkinComponent->GetActiveSkinId().IsEmpty())
    {
        FString SkinError;
        if (!RoamingCharacter->SkinComponent->ApplyDefaultSkin(SkinError))
        {
            DegradedFeatures.AddUnique(TEXT("default_skin_missing"));
        }
    }
}

UObject* UTwinInteractionManagerComponent::ResolvePrimaryAsset(const FString& PrimaryAssetId) const
{
    const FPrimaryAssetId AssetId = FPrimaryAssetId::FromString(PrimaryAssetId);
    if (!AssetId.IsValid()) return nullptr;
    UAssetManager& AssetManager = UAssetManager::Get();
    if (UObject* Existing = AssetManager.GetPrimaryAssetObject(AssetId)) return Existing;
    const FSoftObjectPath AssetPath = AssetManager.GetPrimaryAssetPath(AssetId);
    return AssetPath.IsValid() ? AssetPath.TryLoad() : nullptr;
}

UTwinCharacterAsset* UTwinInteractionManagerComponent::ResolveCharacterAsset(FString& OutError) const
{
    UTwinCharacterAsset* Asset = Cast<UTwinCharacterAsset>(
        ResolvePrimaryAsset(CurrentConfig.CharacterPrimaryAssetId));
    if (!Asset)
    {
        OutError = FString::Printf(
            TEXT("Character asset %s is missing. Create the UTwinCharacterAsset and configure Asset Manager scan rules."),
            *CurrentConfig.CharacterPrimaryAssetId);
    }
    return Asset;
}

bool UTwinInteractionManagerComponent::ResolveSpawnTransform(
    UTwinCharacterAsset* CharacterAsset,
    FTransform& OutTransform,
    FString& OutError) const
{
    if (!CharacterAsset || !GetWorld())
    {
        OutError = TEXT("Cannot resolve the character spawn point");
        return false;
    }

    FVector SourceLocation = CurrentConfig.SpawnLocation;
    FRotator SourceRotation(0.0f, CurrentConfig.SpawnYawDeg, 0.0f);
    const ATwinRoamingSpawnAnchor* SpawnAnchor = nullptr;
    // An enabled runtime route owns the spawn position independently of
    // auto-start.  Auto-start only decides whether the follower begins moving
    // after the character has been placed at the route's first point.
    const bool bSpawnFromRuntimeRoute = CurrentConfig.bRouteEnabled
        && CurrentConfig.bHasRuntimeRoute
        && ActiveRoute
        && ActiveRoute->Spline
        && ActiveRoute->Spline->GetNumberOfSplinePoints() >= 2;
    if (bSpawnFromRuntimeRoute)
    {
        SourceLocation = ActiveRoute->Spline->GetLocationAtSplinePoint(
            0, ESplineCoordinateSpace::World);
        SourceRotation = ActiveRoute->Spline->GetDirectionAtSplinePoint(
            0, ESplineCoordinateSpace::World).Rotation();
    }
    else if (CurrentConfig.bSpawnFromAnchor)
    {
        SpawnAnchor = FindSpawnAnchor(CurrentConfig.SpawnAnchorId);
        if (!SpawnAnchor)
        {
            OutError = FString::Printf(
                TEXT("Configured roaming spawn anchor was not found: %s"),
                *CurrentConfig.SpawnAnchorId);
            return false;
        }
        SourceLocation = SpawnAnchor->GetActorLocation();
        SourceRotation = SpawnAnchor->GetActorRotation();
    }

    const bool bProjectToGround = bSpawnFromRuntimeRoute || !SpawnAnchor || SpawnAnchor->bProjectToGround;
    const FVector TraceStart(
        SourceLocation.X,
        SourceLocation.Y,
        bSpawnFromRuntimeRoute
            ? SourceLocation.Z + RuntimeRouteTraceUpCm
            : CurrentConfig.bSpawnFromAnchor
            ? SourceLocation.Z + 100.0f
            : CurrentConfig.SpawnTraceOriginZCm);
    const FVector TraceEnd = bSpawnFromRuntimeRoute
        ? SourceLocation - FVector(0.0f, 0.0f, RuntimeRouteTraceDownCm)
        : CurrentConfig.bSpawnFromAnchor
        ? FVector(SourceLocation.X, SourceLocation.Y, SourceLocation.Z - 1000.0f)
        : TraceStart - FVector(0.0f, 0.0f, 200000.0f);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(TwinRoamingSpawn), false, SceneManager);
    if (SpawnAnchor) QueryParams.AddIgnoredActor(SpawnAnchor);
    FHitResult GroundHit;
    FVector CapsuleCenter;
    if (bProjectToGround && GetWorld()->LineTraceSingleByChannel(
        GroundHit, TraceStart, TraceEnd, ECC_Visibility, QueryParams))
    {
        CapsuleCenter = GroundHit.ImpactPoint + FVector(
            0.0f, 0.0f, CharacterAsset->CapsuleHalfHeightCm + 2.0f);
    }
    else if (SpawnAnchor && !bProjectToGround)
    {
        CapsuleCenter = SourceLocation;
    }
    else if (bSpawnFromRuntimeRoute)
    {
        // Runtime route points have already been projected in BuildRuntimeRoute.
        // A host floor may block Pawn while intentionally ignoring Visibility,
        // so the route point itself is a valid spawn-height fallback.
        CapsuleCenter = SourceLocation + FVector(
            0.0f, 0.0f, CharacterAsset->CapsuleHalfHeightCm + 2.0f);
        UE_LOG(LogTemp, Warning,
            TEXT("OntoTwin runtime route spawn Visibility trace missed; using projected route Z %.1f cm"),
            SourceLocation.Z);
    }
    else if (!CurrentConfig.bSpawnFromAnchor && CurrentConfig.bHasZHint)
    {
        CapsuleCenter = FVector(
            SourceLocation.X,
            SourceLocation.Y,
            CurrentConfig.ZHintCm + CharacterAsset->CapsuleHalfHeightCm);
    }
    else
    {
        OutError = bSpawnFromRuntimeRoute
            ? TEXT("Runtime route start could not resolve walkable ground")
            : CurrentConfig.bSpawnFromAnchor
            ? TEXT("Spawn anchor could not find visible ground within 10 meters below its local position")
            : TEXT("Spawn ground trace failed and no z_hint_cm fallback is configured");
        return false;
    }

    const FCollisionShape Capsule = FCollisionShape::MakeCapsule(
        CharacterAsset->CapsuleRadiusCm, CharacterAsset->CapsuleHalfHeightCm);
    TArray<FOverlapResult> BlockingOverlaps;
    if (GetWorld()->OverlapMultiByChannel(
        BlockingOverlaps,
        CapsuleCenter,
        FQuat::Identity,
        ECC_Pawn,
        Capsule,
        QueryParams))
    {
        for (const FOverlapResult& Overlap : BlockingOverlaps)
        {
            const AActor* BlockingActor = Overlap.GetActor();
            const UPrimitiveComponent* BlockingComponent = Overlap.GetComponent();
            UE_LOG(LogTemp, Warning,
                TEXT("OntoTwin roaming spawn overlap actor=%s component=%s location=(%.1f,%.1f,%.1f) capsule=(r=%.1f,h=%.1f)"),
                BlockingActor ? *BlockingActor->GetName() : TEXT("none"),
                BlockingComponent ? *BlockingComponent->GetName() : TEXT("none"),
                CapsuleCenter.X,
                CapsuleCenter.Y,
                CapsuleCenter.Z,
                CharacterAsset->CapsuleRadiusCm,
                CharacterAsset->CapsuleHalfHeightCm);
        }
        OutError = TEXT("Character capsule overlaps scene collision at the configured spawn point");
        return false;
    }
    OutTransform = FTransform(
        FRotator(0.0f, SourceRotation.Yaw, 0.0f), CapsuleCenter);
    return true;
}

ATwinRoamingRoute* UTwinInteractionManagerComponent::FindRoute(const FString& RouteId) const
{
    if (!GetWorld() || RouteId.IsEmpty()) return nullptr;
    for (TActorIterator<ATwinRoamingRoute> It(GetWorld()); It; ++It)
    {
        if (It->RouteId == RouteId) return *It;
    }
    return nullptr;
}

bool UTwinInteractionManagerComponent::ProjectRuntimeRoutePointToGround(
    const FVector& Source,
    FVector& OutGroundPoint,
    FString& OutError,
    int32 PointIndex) const
{
    if (!GetWorld())
    {
        OutError = TEXT("Runtime route cannot access the current world");
        return false;
    }

    // Routes in 4.0 target a calibrated floor. Keep the search close to that
    // floor hint so horizontal roofs and upper platforms cannot win merely
    // because they also have walkable collision.
    const float TraceUpCm = FMath::Max(RuntimeRouteTraceUpCm, 10.0f);
    const float TraceDownCm = FMath::Max(RuntimeRouteTraceDownCm, 10.0f);
    const FVector TraceStart = Source + FVector(0.0f, 0.0f, TraceUpCm);
    const FVector TraceEnd = Source - FVector(0.0f, 0.0f, TraceDownCm);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(TwinRuntimeRouteGround), true, SceneManager);
    if (RuntimeRouteActor) QueryParams.AddIgnoredActor(RuntimeRouteActor);
    if (RoamingCharacter) QueryParams.AddIgnoredActor(RoamingCharacter);
    FCollisionObjectQueryParams ObjectTypes;
    ObjectTypes.AddObjectTypesToQuery(ECC_WorldStatic);
    ObjectTypes.AddObjectTypesToQuery(ECC_WorldDynamic);

    TArray<FHitResult> Hits;
    if (!GetWorld()->LineTraceMultiByObjectType(
        Hits, TraceStart, TraceEnd, ObjectTypes, QueryParams))
    {
        OutError = FString::Printf(
            TEXT("Runtime route point %d found no collidable walkable ground at UE XY (%.1f, %.1f)"),
            PointIndex + 1, Source.X, Source.Y);
        UE_LOG(LogTemp, Error, TEXT("OntoTwin %s"), *OutError);
        return false;
    }

    const FHitResult* BestHit = nullptr;
    float BestDistanceToHint = TNumericLimits<float>::Max();
    for (const FHitResult& Hit : Hits)
    {
        if (!Hit.bBlockingHit || Hit.ImpactNormal.Z < RuntimeRouteMinGroundNormalZ) continue;
        const float DistanceToHint = FMath::Abs(
            Hit.ImpactPoint.Z - CurrentConfig.RuntimeRouteGroundZHintCm);
        if (DistanceToHint < BestDistanceToHint)
        {
            BestDistanceToHint = DistanceToHint;
            BestHit = &Hit;
        }
    }
    if (!BestHit)
    {
        OutError = FString::Printf(
            TEXT("Runtime route point %d only hit non-walkable surfaces at UE XY (%.1f, %.1f)"),
            PointIndex + 1, Source.X, Source.Y);
        UE_LOG(LogTemp, Error, TEXT("OntoTwin %s"), *OutError);
        return false;
    }
    OutGroundPoint = BestHit->ImpactPoint;
    return true;
}

ATwinRoamingRoute* UTwinInteractionManagerComponent::BuildRuntimeRoute(FString& OutError)
{
    DestroyRuntimeRoute();
    if (!CurrentConfig.bHasRuntimeRoute) return nullptr;
    if (!GetWorld() || !GetWorld()->PersistentLevel)
    {
        OutError = TEXT("Runtime route cannot resolve the current UE level");
        return nullptr;
    }
    if (CurrentConfig.RuntimeRoutePoints.Num() < 2)
    {
        OutError = TEXT("Runtime route requires at least two points");
        return nullptr;
    }

    const FString CurrentLevel = NormalizeLevelPackageName(
        GetWorld()->PersistentLevel->GetOutermost()->GetName());
    const FString RequiredLevel = NormalizeLevelPackageName(CurrentConfig.RuntimeRouteLevel);
    if (RequiredLevel.IsEmpty() || !CurrentLevel.Equals(RequiredLevel, ESearchCase::CaseSensitive))
    {
        OutError = FString::Printf(
            TEXT("Runtime route level mismatch: current %s, configured %s"),
            *CurrentLevel,
            RequiredLevel.IsEmpty() ? TEXT("<empty>") : *RequiredLevel);
        return nullptr;
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = SceneManager;
    SpawnParams.ObjectFlags |= RF_Transient;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    RuntimeRouteActor = GetWorld()->SpawnActor<ATwinRoamingRoute>(
        ATwinRoamingRoute::StaticClass(), FTransform::Identity, SpawnParams);
    if (!RuntimeRouteActor || !RuntimeRouteActor->Spline)
    {
        RuntimeRouteActor = nullptr;
        OutError = TEXT("Runtime route actor could not be created");
        return nullptr;
    }

    RuntimeRouteActor->RouteId = CurrentConfig.RouteId;
    RuntimeRouteActor->bRuntimeGenerated = true;
    RuntimeRouteActor->bSplineAtGroundLevel = true;
    RuntimeRouteActor->SetActorEnableCollision(false);
    RuntimeRouteActor->Spline->ClearSplinePoints(false);
    for (int32 Index = 0; Index < CurrentConfig.RuntimeRoutePoints.Num(); ++Index)
    {
        FVector GroundPoint;
        if (!ProjectRuntimeRoutePointToGround(
            CurrentConfig.RuntimeRoutePoints[Index], GroundPoint, OutError, Index))
        {
            DestroyRuntimeRoute();
            return nullptr;
        }
        RuntimeRouteActor->Spline->AddSplinePoint(
            GroundPoint, ESplineCoordinateSpace::World, false);
        RuntimeRouteActor->Spline->SetSplinePointType(
            Index, ESplinePointType::CurveClamped, false);
    }
    RuntimeRouteActor->Spline->SetClosedLoop(CurrentConfig.bRouteLoop, false);
    RuntimeRouteActor->Spline->UpdateSpline();
    UE_LOG(LogTemp, Log, TEXT("OntoTwin runtime route %s revision %d created with %d points in %s"),
        *CurrentConfig.RouteId,
        CurrentConfig.RuntimeRouteRevision,
        CurrentConfig.RuntimeRoutePoints.Num(),
        *CurrentLevel);
    return RuntimeRouteActor;
}

void UTwinInteractionManagerComponent::DestroyRuntimeRoute()
{
    if (ActiveRoute == RuntimeRouteActor) ActiveRoute = nullptr;
    if (RuntimeRouteActor && IsValid(RuntimeRouteActor)) RuntimeRouteActor->Destroy();
    RuntimeRouteActor = nullptr;
}

ATwinRoamingSpawnAnchor* UTwinInteractionManagerComponent::FindSpawnAnchor(const FString& SpawnId) const
{
    if (!GetWorld() || SpawnId.IsEmpty()) return nullptr;
    for (TActorIterator<ATwinRoamingSpawnAnchor> It(GetWorld()); It; ++It)
    {
        if (It->SpawnId == SpawnId) return *It;
    }
    return nullptr;
}

ATwinGodViewAnchor* UTwinInteractionManagerComponent::FindGodViewAnchor(const FString& CameraId) const
{
    if (!GetWorld() || CameraId.IsEmpty()) return nullptr;
    for (TActorIterator<ATwinGodViewAnchor> It(GetWorld()); It; ++It)
    {
        if (It->CameraId == CameraId) return *It;
    }
    return nullptr;
}

bool UTwinInteractionManagerComponent::GetGodViewTransform(FTransform& OutTransform) const
{
    const FString CameraId = CurrentConfig.GodCamera.CameraId.IsEmpty()
        ? TEXT("camera.god.default")
        : CurrentConfig.GodCamera.CameraId;
    const ATwinGodViewAnchor* Anchor = GodViewAnchor && IsValid(GodViewAnchor)
        ? GodViewAnchor
        : FindGodViewAnchor(CameraId);
    if (!Anchor) return false;

    OutTransform = Anchor->GetActorTransform();
    return true;
}

bool UTwinInteractionManagerComponent::EnterRoaming(FString& OutError)
{
    if (bRoamingActive) return true;
    if (!CurrentConfig.bEnabled)
    {
        OutError = TEXT("Roaming is disabled in the active project");
        return false;
    }
    if (!PlayerController)
    {
        OutError = TEXT("Local player controller is unavailable");
        return false;
    }
    if (SceneManager && SceneManager->IsRuntimeEditModeActive())
    {
        OutError = TEXT("Exit Runtime Editor before entering character roaming");
        return false;
    }

    UTwinCharacterAsset* CharacterAsset = ResolveCharacterAsset(OutError);
    if (!CharacterAsset) return false;
    UClass* CharacterClass = CharacterAsset->CharacterClass.LoadSynchronous();
    if (!CharacterClass) CharacterClass = ATwinRoamingCharacter::StaticClass();
    if (!CharacterClass->IsChildOf(ATwinRoamingCharacter::StaticClass()))
    {
        OutError = TEXT("Configured CharacterClass must derive from ATwinRoamingCharacter");
        return false;
    }

    ActiveRoute = nullptr;
    DestroyRuntimeRoute();
    if (CurrentConfig.bRouteEnabled)
    {
        if (CurrentConfig.bHasRuntimeRoute)
        {
            ActiveRoute = BuildRuntimeRoute(OutError);
            if (!ActiveRoute) return false;
        }
        else
        {
            ActiveRoute = FindRoute(CurrentConfig.RouteId);
        }
    }

    FTransform SpawnTransform;
    if (!ResolveSpawnTransform(CharacterAsset, SpawnTransform, OutError))
    {
        DestroyRuntimeRoute();
        return false;
    }

    OriginalPawn = PlayerController->GetPawn();
    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = SceneManager;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
    RoamingCharacter = GetWorld()->SpawnActor<ATwinRoamingCharacter>(
        CharacterClass, SpawnTransform, SpawnParams);
    if (!RoamingCharacter)
    {
        DestroyRuntimeRoute();
        OutError = TEXT("Character could not be spawned");
        return false;
    }
    if (!RoamingCharacter->ApplyCharacterAsset(CharacterAsset, OutError))
    {
        RoamingCharacter->Destroy();
        RoamingCharacter = nullptr;
        DestroyRuntimeRoute();
        return false;
    }

    DegradedFeatures.Reset();
    bTakeoverEnabled = CurrentConfig.bTakeoverEnabled;
    RoamingCharacter->ApplyMovementSettings(CurrentConfig.Movement);
    RoamingCharacter->CameraMode->Configure(
        CurrentConfig.FirstPersonCamera, CurrentConfig.NearCamera, CurrentConfig.GodCamera);
    RoamingCharacter->SkinComponent->Configure(
        CurrentConfig.SkinPrimaryAssetIds, CurrentConfig.DefaultSkinId);
    FString SkinError;
    if (!RoamingCharacter->SkinComponent->ApplyDefaultSkin(SkinError))
    {
        DegradedFeatures.AddUnique(TEXT("default_skin_missing"));
    }

    RoamingCharacter->RouteFollower->Configure(
        ActiveRoute,
        CurrentConfig.Movement.AutoRouteSpeedCmS,
        CurrentConfig.bRouteLoop,
        false);
    if (CurrentConfig.bRouteEnabled && !ActiveRoute)
    {
        DegradedFeatures.AddUnique(TEXT("route_missing"));
    }
    else if (ActiveRoute && CurrentConfig.bRouteLoop && !ActiveRoute->Spline->IsClosedLoop())
    {
        DegradedFeatures.AddUnique(TEXT("route_not_closed"));
    }

    GodViewAnchor = FindGodViewAnchor(CurrentConfig.GodCamera.CameraId);
    if (!GodViewAnchor) DegradedFeatures.AddUnique(TEXT("god_camera_missing"));
    RoamingCharacter->CameraMode->ActivateNear(PlayerController, true);
    bRoamingActive = true;
    ActivateRoamingInput();
    bDefaultModeApplied = true;
    CreateHud();

    if (ActiveRoute && CurrentConfig.bRouteAutoStart)
    {
        FString RouteError;
        const bool bRouteStarted = CurrentConfig.bHasRuntimeRoute
            ? RoamingCharacter->RouteFollower->RestartFromBeginning(RouteError)
            : RoamingCharacter->RouteFollower->TryStartFromSpawn(RouteError);
        if (!bRouteStarted)
        {
            DegradedFeatures.AddUnique(CurrentConfig.bHasRuntimeRoute
                ? TEXT("runtime_route_start_rejected")
                : TEXT("route_join_rejected"));
            LastError = RouteError;
            UE_LOG(LogTemp, Warning, TEXT("OntoTwin route auto-start rejected: %s"), *RouteError);
        }
        else if (CurrentConfig.bHasRuntimeRoute)
        {
            UE_LOG(LogTemp, Log, TEXT("OntoTwin runtime route %s started from its first point"),
                *CurrentConfig.RouteId);
        }
    }

    if (CurrentConfig.DefaultCameraMode != ETwinRoamingCameraMode::NearFollow)
    {
        FString CameraError;
        if (!RoamingCharacter->CameraMode->ActivateMode(
            CurrentConfig.DefaultCameraMode,
            PlayerController,
            GodViewAnchor,
            CameraError,
            true))
        {
            DegradedFeatures.AddUnique(
                CurrentConfig.DefaultCameraMode == ETwinRoamingCameraMode::God
                    ? TEXT("god_camera_unavailable")
                    : TEXT("first_person_unavailable"));
        }
    }
    SetHudInteraction(false);
    RuntimeState = RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God
        ? TEXT("god_view")
        : (RoamingCharacter->RouteFollower->IsFollowing() ? TEXT("auto_route") : TEXT("manual"));
    RefreshHud();
    return true;
}

void UTwinInteractionManagerComponent::RestoreOriginalPawn()
{
    if (!PlayerController) return;
    if (OriginalPawn && IsValid(OriginalPawn))
    {
        PlayerController->Possess(OriginalPawn);
    }
    else
    {
        PlayerController->UnPossess();
    }
    OriginalPawn = nullptr;
}

void UTwinInteractionManagerComponent::ExitRoaming()
{
    if (!bRoamingActive && !RoamingCharacter)
    {
        DeactivateRoamingInput();
        DestroyHud();
        DestroyRuntimeRoute();
        return;
    }
    SetHudInteraction(false);
    DeactivateRoamingInput();
    if (SceneManager) SceneManager->ClearOverlayFromSceneInteraction();
    if (RoamingCharacter && IsValid(RoamingCharacter))
    {
        RoamingCharacter->CameraMode->Shutdown(PlayerController);
    }
    RestoreOriginalPawn();
    if (RoamingCharacter && IsValid(RoamingCharacter))
    {
        RoamingCharacter->Destroy();
    }
    RoamingCharacter = nullptr;
    ActiveRoute = nullptr;
    DestroyRuntimeRoute();
    GodViewAnchor = nullptr;
    bRoamingActive = false;
    bHudInteraction = false;
    DestroyHud();
    RuntimeState = CurrentConfig.bEnabled
        ? (bBackendOnline ? TEXT("available") : TEXT("offline"))
        : TEXT("disabled");
}

void UTwinInteractionManagerComponent::ToggleRoaming()
{
    UE_LOG(LogTemp, Log, TEXT("OntoTwin F7 roaming toggle received; active=%s revision=%d"),
        bRoamingActive ? TEXT("true") : TEXT("false"), AppliedRevision);
    if (bRoamingActive)
    {
        ExitRoaming();
        return;
    }
    FString Error;
    if (!EnterRoaming(Error))
    {
        RuntimeState = TEXT("blocked");
        LastError = Error;
        UE_LOG(LogTemp, Warning, TEXT("OntoTwin roaming entry failed: %s"), *Error);
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(
                -1,
                6.0f,
                FColor::Red,
                FString::Printf(TEXT("OntoTwin roaming unavailable: %s"), *Error));
        }
    }
}

void UTwinInteractionManagerComponent::ToggleCameraMode()
{
    if (!bRoamingActive || !RoamingCharacter || bHudInteraction
        || RoamingCharacter->CameraMode->IsTransitioning()) return;
    FString Error;
    if (!RoamingCharacter->CameraMode->Cycle(PlayerController, GodViewAnchor, Error))
    {
        LastError = Error;
        if (RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God)
        {
            DegradedFeatures.AddUnique(TEXT("god_camera_unavailable"));
        }
        return;
    }
    LastError.Reset();
    SetHudInteraction(false);
    RefreshHud();
}

void UTwinInteractionManagerComponent::SetCameraMode(ETwinRoamingCameraMode Mode)
{
    if (!bRoamingActive || !RoamingCharacter
        || RoamingCharacter->CameraMode->IsTransitioning()
        || Mode == RoamingCharacter->CameraMode->GetMode()) return;
    FString Error;
    if (!RoamingCharacter->CameraMode->ActivateMode(
        Mode, PlayerController, GodViewAnchor, Error, false))
    {
        LastError = Error;
        if (Mode == ETwinRoamingCameraMode::God)
        {
            DegradedFeatures.AddUnique(TEXT("god_camera_unavailable"));
        }
        RefreshHud();
        return;
    }
    LastError.Reset();
    SetHudInteraction(false);
    RefreshHud();
}

bool UTwinInteractionManagerComponent::IsCameraTransitioning() const
{
    return RoamingCharacter && RoamingCharacter->CameraMode
        && RoamingCharacter->CameraMode->IsTransitioning();
}

ETwinRoamingCameraMode UTwinInteractionManagerComponent::GetCameraMode() const
{
    return RoamingCharacter && RoamingCharacter->CameraMode
        ? RoamingCharacter->CameraMode->GetMode()
        : ETwinRoamingCameraMode::NearFollow;
}

void UTwinInteractionManagerComponent::ToggleHudInteraction()
{
    if (bRoamingActive && !IsCameraTransitioning()) SetHudInteraction(!bHudInteraction);
}

void UTwinInteractionManagerComponent::SetHudInteraction(bool bOpen)
{
    bHudInteraction = bOpen && bRoamingActive;
    if (RoamingHUD) RoamingHUD->SetInteractionOpen(bHudInteraction);
    if (!PlayerController) return;

    const bool bGodMode = RoamingCharacter
        && RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God;
    PlayerController->bShowMouseCursor = bHudInteraction || bGodMode;
    if (bHudInteraction || bGodMode)
    {
        FInputModeGameAndUI InputMode;
        InputMode.SetHideCursorDuringCapture(false);
        InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        PlayerController->SetInputMode(InputMode);
    }
    else
    {
        PlayerController->SetInputMode(FInputModeGameOnly());
    }
    RefreshHud();
}

void UTwinInteractionManagerComponent::CycleSkin()
{
    if (!RoamingCharacter) return;
    FString Error;
    if (!RoamingCharacter->SkinComponent->CycleSkin(Error)) LastError = Error;
    else
    {
        LastError.Reset();
        DegradedFeatures.Remove(TEXT("default_skin_missing"));
    }
    RefreshHud();
}

void UTwinInteractionManagerComponent::ResumeRoute()
{
    if (!RoamingCharacter) return;
    FString Error;
    if (!RoamingCharacter->RouteFollower->TryResume(Error)) LastError = Error;
    else
    {
        LastError.Reset();
        DegradedFeatures.Remove(TEXT("route_join_rejected"));
    }
    RefreshHud();
}

void UTwinInteractionManagerComponent::RestartRoute()
{
    if (!RoamingCharacter) return;
    FString Error;
    if (!RoamingCharacter->RouteFollower->RestartFromBeginning(Error)) LastError = Error;
    else
    {
        LastError.Reset();
        DegradedFeatures.Remove(TEXT("route_join_rejected"));
    }
    RefreshHud();
}

void UTwinInteractionManagerComponent::ApplyPendingReload()
{
    if (!bPendingReload) return;
    const bool bWasActive = bRoamingActive;
    ExitRoaming();
    CurrentConfig = PendingConfig;
    AppliedRevision = PendingRevision;
    RuntimeToken = PendingRuntimeToken;
    PendingRevision = -1;
    PendingRuntimeToken.Reset();
    bPendingReload = false;
    if (bWasActive)
    {
        FString Error;
        if (!EnterRoaming(Error))
        {
            RuntimeState = TEXT("blocked");
            LastError = Error;
        }
    }
}

void UTwinInteractionManagerComponent::CreateHud()
{
    if (!PlayerController) return;
    if (!RoamingHUD)
    {
        UClass* WidgetClass = RoamingHUDClass
            ? RoamingHUDClass.Get() : UOntoTwinRoamingHUDWidget::StaticClass();
        RoamingHUD = CreateWidget<UOntoTwinRoamingHUDWidget>(PlayerController, WidgetClass);
        if (RoamingHUD)
        {
            RoamingHUD->SetInteractionManager(this);
            RoamingHUD->AddToViewport(850);
            RoamingHUD->SetPositionInViewport(FVector2D::ZeroVector, true);
            RoamingHUD->SetAnchorsInViewport(FAnchors(0.0f, 0.0f));
            RoamingHUD->SetAlignmentInViewport(FVector2D::ZeroVector);
        }
    }
    if (!CrosshairHUD)
    {
        CrosshairHUD = CreateWidget<UOntoTwinCrosshairWidget>(
            PlayerController, UOntoTwinCrosshairWidget::StaticClass());
        if (CrosshairHUD)
        {
            CrosshairHUD->AddToViewport(851);
            CrosshairHUD->SetPositionInViewport(FVector2D::ZeroVector, false);
            CrosshairHUD->SetAnchorsInViewport(FAnchors(0.0f, 0.0f));
            CrosshairHUD->SetAlignmentInViewport(FVector2D(0.5f, 0.5f));
            CrosshairHUD->SetDesiredSizeInViewport(FVector2D(46.0f, 46.0f));
        }
    }
    RefreshHud();
}

void UTwinInteractionManagerComponent::DestroyHud()
{
    if (RoamingHUD && IsValid(RoamingHUD)) RoamingHUD->RemoveFromParent();
    RoamingHUD = nullptr;
    if (CrosshairHUD && IsValid(CrosshairHUD)) CrosshairHUD->RemoveFromParent();
    CrosshairHUD = nullptr;
    bCrosshairInteractive = false;
}

void UTwinInteractionManagerComponent::RefreshHud()
{
    if (RoamingHUD)
    {
        if (PlayerController)
        {
            int32 ViewportX = 0;
            int32 ViewportY = 0;
            PlayerController->GetViewportSize(ViewportX, ViewportY);
            const float ViewportScale = FMath::Max(
                0.01f, UWidgetLayoutLibrary::GetViewportScale(this));
            RoamingHUD->SetDesiredSizeInViewport(
                FVector2D(ViewportX / ViewportScale, ViewportY / ViewportScale));
        }
        RoamingHUD->RefreshFromManager();
    }
    if (CrosshairHUD)
    {
        if (PlayerController)
        {
            int32 ViewportX = 0;
            int32 ViewportY = 0;
            PlayerController->GetViewportSize(ViewportX, ViewportY);
            CrosshairHUD->SetPositionInViewport(
                FVector2D(ViewportX * 0.5f, ViewportY * 0.5f), true);
        }
        const bool bFirstPerson = bRoamingActive
            && RoamingCharacter
            && RoamingCharacter->CameraMode
            && RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::FirstPerson;
        CrosshairHUD->SetReticleState(
            bFirstPerson && !bHudInteraction && !IsCameraTransitioning(),
            bCrosshairInteractive);
    }
}

void UTwinInteractionManagerComponent::UpdateCrosshairTarget()
{
    bCrosshairInteractive = false;
    if (!bRoamingActive || bHudInteraction || !PlayerController || !SceneManager
        || !RoamingCharacter || !RoamingCharacter->CameraMode
        || RoamingCharacter->CameraMode->IsTransitioning()
        || RoamingCharacter->CameraMode->GetMode() != ETwinRoamingCameraMode::FirstPerson)
    {
        return;
    }

    int32 ViewportX = 0;
    int32 ViewportY = 0;
    PlayerController->GetViewportSize(ViewportX, ViewportY);
    FVector Origin;
    FVector Direction;
    if (!PlayerController->DeprojectScreenPositionToWorld(
        ViewportX * 0.5f, ViewportY * 0.5f, Origin, Direction))
    {
        return;
    }

    FHitResult Hit;
    FCollisionQueryParams Params(
        SCENE_QUERY_STAT(TwinRoamingCrosshairTarget), true, RoamingCharacter);
    if (!GetWorld()->LineTraceSingleByChannel(
        Hit, Origin, Origin + Direction * 100000.0f, ECC_Visibility, Params))
    {
        return;
    }

    ATwinInstance* Instance = ResolveInteractionInstance(Hit);
    if (!Instance)
    {
        Instance = SceneManager->FindOverlayInstanceNearHit(Hit);
    }
    bCrosshairInteractive = Instance && Instance->HasSelectedOverlay();
}

void UTwinInteractionManagerComponent::BuildDefaultInputContext()
{
    if (DefaultMappingContext) return;
    DefaultMappingContext = NewObject<UInputMappingContext>(this, TEXT("OntoTwinRoamingDefaultContext"));

    auto MakeAction = [this](const TCHAR* Name, EInputActionValueType Type)
    {
        UInputAction* Action = NewObject<UInputAction>(this, Name);
        Action->ValueType = Type;
        return Action;
    };
    ToggleAction = MakeAction(TEXT("IA_TwinRoamingToggle"), EInputActionValueType::Boolean);
    MoveAction = MakeAction(TEXT("IA_TwinRoamingMove"), EInputActionValueType::Axis2D);
    LookAction = MakeAction(TEXT("IA_TwinRoamingLook"), EInputActionValueType::Axis2D);
    VerticalAction = MakeAction(TEXT("IA_TwinRoamingVertical"), EInputActionValueType::Axis1D);
    ViewAction = MakeAction(TEXT("IA_TwinRoamingView"), EInputActionValueType::Boolean);
    HudAction = MakeAction(TEXT("IA_TwinRoamingHUD"), EInputActionValueType::Boolean);
    InteractAction = MakeAction(TEXT("IA_TwinRoamingInteract"), EInputActionValueType::Boolean);
    RouteAction = MakeAction(TEXT("IA_TwinRoamingRoute"), EInputActionValueType::Boolean);
    JumpAction = MakeAction(TEXT("IA_TwinRoamingJump"), EInputActionValueType::Boolean);
    CrouchAction = MakeAction(TEXT("IA_TwinRoamingCrouch"), EInputActionValueType::Boolean);
    SprintAction = MakeAction(TEXT("IA_TwinRoamingSprint"), EInputActionValueType::Boolean);
    SelectAction = MakeAction(TEXT("IA_TwinRoamingSelect"), EInputActionValueType::Boolean);
    SpeedAction = MakeAction(TEXT("IA_TwinRoamingSpeed"), EInputActionValueType::Axis1D);

    DefaultMappingContext->MapKey(ViewAction, ToggleViewKey);
    DefaultMappingContext->MapKey(HudAction, ToggleHudKey);
    DefaultMappingContext->MapKey(InteractAction, InteractKey);
    DefaultMappingContext->MapKey(RouteAction, ResumeRouteKey);
    DefaultMappingContext->MapKey(JumpAction, EKeys::SpaceBar);
    DefaultMappingContext->MapKey(CrouchAction, EKeys::C);
    DefaultMappingContext->MapKey(SprintAction, EKeys::LeftShift);
    DefaultMappingContext->MapKey(SelectAction, EKeys::LeftMouseButton);
    DefaultMappingContext->MapKey(LookAction, EKeys::Mouse2D);
    DefaultMappingContext->MapKey(SpeedAction, EKeys::MouseWheelAxis);

    FEnhancedActionKeyMapping& MoveForward = DefaultMappingContext->MapKey(MoveAction, EKeys::W);
    UInputModifierSwizzleAxis* ForwardSwizzle = NewObject<UInputModifierSwizzleAxis>(DefaultMappingContext);
    ForwardSwizzle->Order = EInputAxisSwizzle::YXZ;
    MoveForward.Modifiers.Add(ForwardSwizzle);

    FEnhancedActionKeyMapping& MoveBackward = DefaultMappingContext->MapKey(MoveAction, EKeys::S);
    UInputModifierSwizzleAxis* BackwardSwizzle = NewObject<UInputModifierSwizzleAxis>(DefaultMappingContext);
    BackwardSwizzle->Order = EInputAxisSwizzle::YXZ;
    MoveBackward.Modifiers.Add(BackwardSwizzle);
    MoveBackward.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));

    FEnhancedActionKeyMapping& MoveLeft = DefaultMappingContext->MapKey(MoveAction, EKeys::A);
    MoveLeft.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));
    DefaultMappingContext->MapKey(MoveAction, EKeys::D);

    FEnhancedActionKeyMapping& MoveDown = DefaultMappingContext->MapKey(VerticalAction, EKeys::Q);
    MoveDown.Modifiers.Add(NewObject<UInputModifierNegate>(DefaultMappingContext));
    DefaultMappingContext->MapKey(VerticalAction, EKeys::E);
}

void UTwinInteractionManagerComponent::SetupInput()
{
    if (!PlayerController) return;
    BuildDefaultInputContext();
    if (!bEnhancedInputReady)
    {
        BindEnhancedInput();
    }
    if (bRoamingActive)
    {
        ActivateRoamingInput();
    }
}

void UTwinInteractionManagerComponent::ActivateRoamingInput()
{
    if (!PlayerController || ActiveMappingContext) return;
    BuildDefaultInputContext();
    if (ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer())
    {
        if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
            LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            Subsystem->AddMappingContext(DefaultMappingContext, 20);
            ActiveMappingContext = DefaultMappingContext;
        }
    }
}

void UTwinInteractionManagerComponent::DeactivateRoamingInput()
{
    if (!PlayerController || !ActiveMappingContext) return;
    if (ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer())
    {
        if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
            LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            Subsystem->RemoveMappingContext(ActiveMappingContext);
        }
    }
    ActiveMappingContext = nullptr;
}

void UTwinInteractionManagerComponent::BindEnhancedInput()
{
    UEnhancedInputComponent* Input = PlayerController
        ? Cast<UEnhancedInputComponent>(PlayerController->InputComponent) : nullptr;
    if (!Input)
    {
        bEnhancedInputReady = false;
        return;
    }
    Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &UTwinInteractionManagerComponent::OnMove);
    Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &UTwinInteractionManagerComponent::OnLook);
    Input->BindAction(VerticalAction, ETriggerEvent::Triggered, this, &UTwinInteractionManagerComponent::OnVertical);
    Input->BindAction(ViewAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnToggleView);
    Input->BindAction(HudAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnToggleHud);
    Input->BindAction(InteractAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnInteract);
    Input->BindAction(RouteAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnRoute);
    Input->BindAction(JumpAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnJump);
    Input->BindAction(CrouchAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnCrouchStarted);
    Input->BindAction(CrouchAction, ETriggerEvent::Completed, this, &UTwinInteractionManagerComponent::OnCrouchEnded);
    Input->BindAction(SprintAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnSprintStarted);
    Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &UTwinInteractionManagerComponent::OnSprintEnded);
    Input->BindAction(SelectAction, ETriggerEvent::Started, this, &UTwinInteractionManagerComponent::OnSelect);
    Input->BindAction(SpeedAction, ETriggerEvent::Triggered, this, &UTwinInteractionManagerComponent::OnAdjustSpeed);
    bEnhancedInputReady = true;
}

void UTwinInteractionManagerComponent::RemoveInput()
{
    DeactivateRoamingInput();
    bEnhancedInputReady = false;
}

void UTwinInteractionManagerComponent::TickFallbackInput(float DeltaTime)
{
    if (!PlayerController) return;
    if (!bRoamingActive || !RoamingCharacter) return;
    if (RoamingCharacter->CameraMode->IsTransitioning()) return;
    if (PlayerController->WasInputKeyJustPressed(ToggleHudKey)) ToggleHudInteraction();
    if (bHudInteraction) return;
    if (PlayerController->WasInputKeyJustPressed(ToggleViewKey)) ToggleCameraMode();
    if (PlayerController->WasInputKeyJustPressed(ResumeRouteKey)) ResumeRoute();

    const bool bGod = RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God;
    if (PlayerController->WasInputKeyJustPressed(EKeys::LeftMouseButton)
        || (!bGod && PlayerController->WasInputKeyJustPressed(InteractKey)))
    {
        SelectFromView(bGod);
    }

    FVector2D Move(
        (PlayerController->IsInputKeyDown(EKeys::D) ? 1.0f : 0.0f)
            - (PlayerController->IsInputKeyDown(EKeys::A) ? 1.0f : 0.0f),
        (PlayerController->IsInputKeyDown(EKeys::W) ? 1.0f : 0.0f)
            - (PlayerController->IsInputKeyDown(EKeys::S) ? 1.0f : 0.0f));
    Move = Move.GetClampedToMaxSize(1.0f);
    if (!Move.IsNearlyZero())
    {
        if (bGod && RoamingCharacter->CameraMode->GetGodPawn())
        {
            RoamingCharacter->CameraMode->GetGodPawn()->MovePlanar(Move);
        }
        else
        {
            if (bTakeoverEnabled) RoamingCharacter->RouteFollower->PauseByUser();
            RoamingCharacter->MoveRelativeToView(
                Move, PlayerController->IsInputKeyDown(EKeys::LeftShift));
        }
    }

    float MouseX = 0.0f;
    float MouseY = 0.0f;
    PlayerController->GetInputMouseDelta(MouseX, MouseY);
    if (bGod)
    {
        if (PlayerController->IsInputKeyDown(EKeys::RightMouseButton))
        {
            RoamingCharacter->CameraMode->GetGodPawn()->Look(FVector2D(MouseX, MouseY));
        }
        const float Vertical = (PlayerController->IsInputKeyDown(EKeys::E) ? 1.0f : 0.0f)
            - (PlayerController->IsInputKeyDown(EKeys::Q) ? 1.0f : 0.0f);
        RoamingCharacter->CameraMode->GetGodPawn()->MoveVertical(Vertical);
        RoamingCharacter->CameraMode->GetGodPawn()->AdjustSpeed(
            PlayerController->GetInputAnalogKeyState(EKeys::MouseWheelAxis));
    }
    else
    {
        const float Sensitivity = RoamingCharacter->CameraMode->GetMode()
                == ETwinRoamingCameraMode::FirstPerson
            ? CurrentConfig.FirstPersonCamera.LookSensitivity
            : CurrentConfig.NearCamera.LookSensitivity;
        RoamingCharacter->Look(FVector2D(MouseX, MouseY), Sensitivity);
        if (PlayerController->WasInputKeyJustPressed(EKeys::SpaceBar)) RoamingCharacter->Jump();
        if (PlayerController->WasInputKeyJustPressed(EKeys::C)) RoamingCharacter->Crouch();
        if (PlayerController->WasInputKeyJustReleased(EKeys::C)) RoamingCharacter->UnCrouch();
    }
}

void UTwinInteractionManagerComponent::OnMove(const FInputActionValue& Value)
{
    if (!bRoamingActive || bHudInteraction || !RoamingCharacter
        || RoamingCharacter->CameraMode->IsTransitioning()) return;
    const FVector2D Move = Value.Get<FVector2D>().GetClampedToMaxSize(1.0f);
    if (Move.IsNearlyZero()) return;
    if (RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God)
    {
        if (ATwinGodViewPawn* Pawn = RoamingCharacter->CameraMode->GetGodPawn()) Pawn->MovePlanar(Move);
    }
    else
    {
        if (bTakeoverEnabled) RoamingCharacter->RouteFollower->PauseByUser();
        RoamingCharacter->MoveRelativeToView(Move, bSprintHeld);
    }
}

void UTwinInteractionManagerComponent::OnLook(const FInputActionValue& Value)
{
    if (!bRoamingActive || bHudInteraction || !RoamingCharacter || !PlayerController
        || RoamingCharacter->CameraMode->IsTransitioning()) return;
    const FVector2D Look = Value.Get<FVector2D>();
    if (RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God)
    {
        if (PlayerController->IsInputKeyDown(EKeys::RightMouseButton))
        {
            if (ATwinGodViewPawn* Pawn = RoamingCharacter->CameraMode->GetGodPawn()) Pawn->Look(Look);
        }
    }
    else
    {
        const float Sensitivity = RoamingCharacter->CameraMode->GetMode()
                == ETwinRoamingCameraMode::FirstPerson
            ? CurrentConfig.FirstPersonCamera.LookSensitivity
            : CurrentConfig.NearCamera.LookSensitivity;
        RoamingCharacter->Look(Look, Sensitivity);
    }
}

void UTwinInteractionManagerComponent::OnVertical(const FInputActionValue& Value)
{
    if (!bRoamingActive || bHudInteraction || !RoamingCharacter
        || RoamingCharacter->CameraMode->IsTransitioning()) return;
    if (RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God)
    {
        if (ATwinGodViewPawn* Pawn = RoamingCharacter->CameraMode->GetGodPawn())
        {
            Pawn->MoveVertical(Value.Get<float>());
        }
    }
}

void UTwinInteractionManagerComponent::OnToggle(const FInputActionValue&) { ToggleRoaming(); }
void UTwinInteractionManagerComponent::OnToggleView(const FInputActionValue&) { ToggleCameraMode(); }
void UTwinInteractionManagerComponent::OnToggleHud(const FInputActionValue&) { ToggleHudInteraction(); }
void UTwinInteractionManagerComponent::OnRoute(const FInputActionValue&) { ResumeRoute(); }

void UTwinInteractionManagerComponent::OnInteract(const FInputActionValue&)
{
    if (RoamingCharacter
        && !RoamingCharacter->CameraMode->IsTransitioning()
        && RoamingCharacter->CameraMode->GetMode() != ETwinRoamingCameraMode::God)
    {
        SelectFromView(false);
    }
}

void UTwinInteractionManagerComponent::OnSelect(const FInputActionValue&)
{
    if (RoamingCharacter && !RoamingCharacter->CameraMode->IsTransitioning())
    {
        const bool bGodMode =
            RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God;
        SelectFromView(bGodMode);
    }
}

void UTwinInteractionManagerComponent::OnJump(const FInputActionValue&)
{
    if (RoamingCharacter && !bHudInteraction
        && !RoamingCharacter->CameraMode->IsTransitioning()
        && RoamingCharacter->CameraMode->GetMode() != ETwinRoamingCameraMode::God)
    {
        RoamingCharacter->Jump();
    }
}

void UTwinInteractionManagerComponent::OnCrouchStarted(const FInputActionValue&)
{
    if (RoamingCharacter && !bHudInteraction
        && !RoamingCharacter->CameraMode->IsTransitioning()
        && RoamingCharacter->CameraMode->GetMode() != ETwinRoamingCameraMode::God)
    {
        RoamingCharacter->Crouch();
    }
}

void UTwinInteractionManagerComponent::OnCrouchEnded(const FInputActionValue&)
{
    if (RoamingCharacter) RoamingCharacter->UnCrouch();
}

void UTwinInteractionManagerComponent::OnSprintStarted(const FInputActionValue&) { bSprintHeld = true; }
void UTwinInteractionManagerComponent::OnSprintEnded(const FInputActionValue&) { bSprintHeld = false; }

void UTwinInteractionManagerComponent::OnAdjustSpeed(const FInputActionValue& Value)
{
    if (RoamingCharacter && !bHudInteraction
        && !RoamingCharacter->CameraMode->IsTransitioning()
        && RoamingCharacter->CameraMode->GetMode() == ETwinRoamingCameraMode::God)
    {
        if (ATwinGodViewPawn* Pawn = RoamingCharacter->CameraMode->GetGodPawn())
        {
            Pawn->AdjustSpeed(Value.Get<float>());
        }
    }
}

void UTwinInteractionManagerComponent::SelectFromView(bool bCursorTrace)
{
    if (!PlayerController || !SceneManager || bHudInteraction || IsCameraTransitioning()) return;
    FHitResult Hit;
    bool bHit = false;
    int32 ViewportX = 0;
    int32 ViewportY = 0;
    PlayerController->GetViewportSize(ViewportX, ViewportY);
    FVector2D ScreenPoint(ViewportX * 0.5f, ViewportY * 0.5f);
    if (bCursorTrace)
    {
        float MouseX = 0.0f;
        float MouseY = 0.0f;
        if (PlayerController->GetMousePosition(MouseX, MouseY))
        {
            ScreenPoint = FVector2D(MouseX, MouseY);
        }
        bHit = PlayerController->GetHitResultUnderCursor(ECC_Visibility, true, Hit);
    }
    else
    {
        FVector Origin;
        FVector Direction;
        if (PlayerController->DeprojectScreenPositionToWorld(
            ViewportX * 0.5f, ViewportY * 0.5f, Origin, Direction))
        {
            FCollisionQueryParams Params(SCENE_QUERY_STAT(TwinRoamingSelect), true, RoamingCharacter);
            bHit = GetWorld()->LineTraceSingleByChannel(
                Hit, Origin, Origin + Direction * 100000.0f, ECC_Visibility, Params);
        }
    }
    ATwinInstance* Instance = bHit ? ResolveInteractionInstance(Hit) : nullptr;
    if (!Instance && bHit)
    {
        Instance = SceneManager->FindOverlayInstanceNearHit(Hit);
    }
    const bool bSelectedByOverlay = !Instance
        && SceneManager->SelectOverlayAtScreenPosition(ScreenPoint);
    UE_LOG(LogTemp, Log,
        TEXT("OntoTwin interaction select mode=%s hit=%s actor=%s instance=%s overlay=%s screen_overlay=%s point=(%.1f,%.1f)"),
        bCursorTrace ? TEXT("cursor") : TEXT("crosshair"),
        bHit ? TEXT("true") : TEXT("false"),
        bHit && Hit.GetActor() ? *Hit.GetActor()->GetName() : TEXT("none"),
        Instance ? *Instance->GetInstanceId() : TEXT("none"),
        Instance && Instance->HasOverlay() ? TEXT("true") : TEXT("false"),
        bSelectedByOverlay ? TEXT("true") : TEXT("false"),
        ScreenPoint.X,
        ScreenPoint.Y);
    if (Instance && Instance->HasOverlay())
    {
        SceneManager->SelectOverlayFromSceneInteraction(Instance);
    }
    else if (!bSelectedByOverlay)
    {
        SceneManager->ClearOverlayFromSceneInteraction();
    }
}

ATwinInstance* UTwinInteractionManagerComponent::ResolveInteractionInstance(
    const FHitResult& Hit) const
{
    AActor* Candidate = Hit.GetActor();
    TSet<const AActor*> Visited;
    for (int32 Depth = 0; Candidate && Depth < 8 && !Visited.Contains(Candidate); ++Depth)
    {
        Visited.Add(Candidate);
        if (ATwinInstance* Instance = Cast<ATwinInstance>(Candidate))
        {
            return Instance;
        }

        AActor* Parent = Candidate->GetAttachParentActor();
        Candidate = Parent ? Parent : Candidate->GetOwner();
    }
    return nullptr;
}

void UTwinInteractionManagerComponent::SendHeartbeat()
{
    if (bShuttingDown || !SceneManager || !bBackendOnline) return;

    FString State = RuntimeState;
    FString CameraMode;
    FString RouteState;
    FString ActiveSkin;
    if (bPendingReload) State = TEXT("reload_required");
    else if (!CurrentConfig.bEnabled) State = TEXT("disabled");
    else if (!bRoamingActive) State = TEXT("available");
    else if (bHudInteraction) State = TEXT("ui_interaction");
    else if (RoamingCharacter)
    {
        const ETwinRoamingCameraMode ActiveCameraMode =
            RoamingCharacter->CameraMode->GetMode();
        const bool bGod = ActiveCameraMode == ETwinRoamingCameraMode::God;
        CameraMode = CameraModeId(ActiveCameraMode);
        RouteState = RoamingCharacter->RouteFollower->GetRouteStateText();
        ActiveSkin = RoamingCharacter->SkinComponent->GetActiveSkinId();
        if (bGod) State = TEXT("god_view");
        else if (RoamingCharacter->RouteFollower->IsFollowing()) State = TEXT("auto_route");
        else State = TEXT("manual");
    }

    const TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
    if (AppliedRevision >= 0) Payload->SetNumberField(TEXT("applied_revision"), AppliedRevision);
    else Payload->SetField(TEXT("applied_revision"), MakeShared<FJsonValueNull>());
    if (PendingRevision >= 0) Payload->SetNumberField(TEXT("pending_revision"), PendingRevision);
    else Payload->SetField(TEXT("pending_revision"), MakeShared<FJsonValueNull>());
    Payload->SetStringField(TEXT("catalog_version"), CatalogVersion);
    Payload->SetStringField(TEXT("runtime_state"), State);
    Payload->SetStringField(TEXT("camera_mode"), CameraMode);
    Payload->SetStringField(TEXT("route_state"), RouteState);
    Payload->SetStringField(TEXT("active_skin_id"), ActiveSkin);
    TArray<TSharedPtr<FJsonValue>> DegradedValues;
    for (const FString& Feature : DegradedFeatures)
    {
        DegradedValues.Add(MakeShared<FJsonValueString>(Feature));
    }
    Payload->SetArrayField(TEXT("degraded_features"), DegradedValues);
    Payload->SetObjectField(TEXT("realtime_channel"), SceneManager->BuildRealtimeChannelHealth());
    if (LastError.IsEmpty())
    {
        Payload->SetField(TEXT("error"), MakeShared<FJsonValueNull>());
    }
    else
    {
        const TSharedRef<FJsonObject> Error = MakeShared<FJsonObject>();
        Error->SetStringField(TEXT("message"), LastError);
        Payload->SetObjectField(TEXT("error"), Error);
    }

    FString Body;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Body);
    FJsonSerializer::Serialize(Payload, Writer);

    FString BaseUrl = SceneManager->BackendBaseUrl;
    BaseUrl.RemoveFromEnd(TEXT("/"));
    const TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl + TEXT("/api/v2/scene-interactions/runtime"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddProjectHeaders(Request);
    Request->SetContentAsString(Body);
    const TWeakObjectPtr<UTwinInteractionManagerComponent> WeakThis(this);
    Request->OnProcessRequestComplete().BindLambda(
        [WeakThis](FHttpRequestPtr, FHttpResponsePtr Response, bool bWasSuccessful)
        {
            UTwinInteractionManagerComponent* Self = WeakThis.Get();
            if (!Self || Self->bShuttingDown || !bWasSuccessful || !Response.IsValid()) return;
            if (Response->GetResponseCode() == 403)
            {
                Self->LastError = TEXT("UE project binding was rejected while reporting roaming status");
                Self->ExitRoaming();
                Self->RuntimeState = TEXT("blocked");
            }
        });
    Request->ProcessRequest();
}

FString UTwinInteractionManagerComponent::GetHudStatusText() const
{
    if (!bRoamingActive) return TEXT("人物漫游");
    const FString Character = CompactHudLabel(
        CurrentConfig.CharacterDisplayName, TEXT("漫游人物"), 16);
    const FString View = RoamingCharacter
        ? CameraModeLabel(RoamingCharacter->CameraMode->GetMode())
        : TEXT("视角不可用");

    FString RouteStatus = TEXT("自由漫游");
    if (RoamingCharacter && RoamingCharacter->RouteFollower)
    {
        const FString RouteName = CompactHudLabel(
            CurrentConfig.RouteDisplayName, TEXT("当前线路"), 24);
        switch (RoamingCharacter->RouteFollower->GetRouteState())
        {
        case ETwinRoamingRouteState::AutoRoute:
            RouteStatus = FString::Printf(TEXT("线路漫游 - %s"), *RouteName);
            break;
        case ETwinRoamingRouteState::Joining:
            RouteStatus = FString::Printf(TEXT("正在返回线路 - %s"), *RouteName);
            break;
        case ETwinRoamingRouteState::Blocked:
            RouteStatus = FString::Printf(TEXT("线路受阻 - %s"), *RouteName);
            break;
        case ETwinRoamingRouteState::Completed:
            RouteStatus = FString::Printf(TEXT("线路已完成 - %s"), *RouteName);
            break;
        default:
            break;
        }
    }
    const FString ViewStatus = IsCameraTransitioning()
        ? View + TEXT(" · 切换中") : View;
    return FString::Printf(
        TEXT("%s   ·   %s   ·   %s"), *Character, *ViewStatus, *RouteStatus);
}

FString UTwinInteractionManagerComponent::GetHudHintText() const
{
    TArray<FString> Keys;
    TArray<FString> Descriptions;
    GetHudShortcutItems(Keys, Descriptions);
    FString Text;
    for (int32 Index = 0; Index < Keys.Num() && Index < Descriptions.Num(); ++Index)
    {
        if (!Text.IsEmpty()) Text += TEXT("\n");
        Text += Keys[Index] + TEXT("  ") + Descriptions[Index];
    }
    return Text;
}

void UTwinInteractionManagerComponent::GetHudShortcutItems(
    TArray<FString>& OutKeys,
    TArray<FString>& OutDescriptions) const
{
    OutKeys.Reset();
    OutDescriptions.Reset();
    const auto AddShortcut = [&OutKeys, &OutDescriptions](
        const FString& Key,
        const FString& Description)
    {
        OutKeys.Add(Key);
        OutDescriptions.Add(Description);
    };

    if (bHudInteraction)
    {
        AddShortcut(ToggleHudKey.ToString(), TEXT("收起操作"));
        AddShortcut(TEXT("鼠标"), TEXT("选择按钮"));
        AddShortcut(ToggleRoamingKey.ToString(), TEXT("退出漫游"));
        return;
    }

    const ETwinRoamingCameraMode Mode = GetCameraMode();
    if (Mode == ETwinRoamingCameraMode::God)
    {
        AddShortcut(TEXT("WASD"), TEXT("平移"));
        AddShortcut(TEXT("右键"), TEXT("观察"));
        AddShortcut(TEXT("Q / E"), TEXT("升降"));
        AddShortcut(TEXT("滚轮"), TEXT("调整速度"));
        AddShortcut(TEXT("左键"), TEXT("选择"));
        AddShortcut(ToggleViewKey.ToString(), TEXT("切换视角"));
        AddShortcut(ToggleHudKey.ToString(), TEXT("更多操作"));
        AddShortcut(ToggleRoamingKey.ToString(), TEXT("退出漫游"));
        return;
    }

    AddShortcut(TEXT("WASD"), TEXT("移动"));
    AddShortcut(TEXT("E / 左键"), TEXT("交互"));
    const bool bPausedByUser = RoamingCharacter
        && RoamingCharacter->RouteFollower
        && RoamingCharacter->RouteFollower->GetRouteState()
            == ETwinRoamingRouteState::PausedByUser;
    if (bPausedByUser)
    {
        AddShortcut(ResumeRouteKey.ToString(), TEXT("返回线路"));
    }
    AddShortcut(ToggleViewKey.ToString(), TEXT("切换视角"));
    AddShortcut(ToggleHudKey.ToString(), TEXT("更多操作"));
    AddShortcut(ToggleRoamingKey.ToString(), TEXT("退出漫游"));
}

FString UTwinInteractionManagerComponent::GetHudDetailText() const
{
    FString Text = bPendingReload
        ? TEXT("存在待重载配置，可点击“重载人物”应用。")
        : TEXT("选择视角，或执行人物与线路操作。");
    if (!bBackendOnline) Text += TEXT("  后端离线，当前使用最后一次有效配置。");
    if (!BindingWarning.IsEmpty()) Text += TEXT("\n") + BindingWarning;
    if (!LastError.IsEmpty()) Text += TEXT("\n提示：") + LastError;
    return Text;
}

void UTwinInteractionManagerComponent::NotifyRuntimeEditorBlocked()
{
    LastError = TEXT("人物漫游运行中；请先按 F7 退出，再进入 Runtime Editor");
    RefreshHud();
}
