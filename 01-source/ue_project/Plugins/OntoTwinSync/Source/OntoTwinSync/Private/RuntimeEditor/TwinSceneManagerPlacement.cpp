#include "TwinSceneManager.h"
#include "TwinInstance.h"
#include "OntoTwinRuntimeEditorPanel.h"
#include "OntoTwinRuntimeGizmo.h"
#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "RuntimeEditor/OntoTwinWallRules.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"
#include "HttpModule.h"
#include "Framework/Application/SlateApplication.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonSerializer.h"

bool ATwinSceneManager::BeginModelPlacement(const FString& ModelKey, const FString& Label, bool bDrag)
{
    if (!CanPlaceRuntimeModel() || bPlacementSending || bRuntimeEditSaving || bRuntimeDragging) return false;
    const auto Entries = OntoTwinModelLibrary::List(ModelKey.StartsWith(TEXT("models:")));
    if (!Entries.ContainsByPredicate([&](const auto& Entry) { return Entry.Key == ModelKey && Entry.Label == Label; }))
        return false;

    CancelModelPlacement();
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.ObjectFlags |= RF_Transient;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    PlacementPreview = GetWorld()->SpawnActor<ATwinInstance>(ATwinInstance::StaticClass(), FTransform::Identity, Params);
    if (!PlacementPreview || !PlacementPreview->InitializePlacementPreview(ModelKey))
    {
        CancelModelPlacement();
        if (RuntimeEditorPanel) RuntimeEditorPanel->ShowToast(TEXT("无法读取模型，请检查文件后重试"), EOntoTwinRuntimeToastType::Error);
        return false;
    }
    const FBox Bounds = PlacementPreview->GetRepresentationWorldBounds(true);
    PlacementRelativeBounds = Bounds.IsValid ? Bounds.ShiftBy(-PlacementPreview->GetActorLocation()) : FBox(FVector::ZeroVector, FVector::ZeroVector);
    PlacementBottomOffset = -PlacementRelativeBounds.Min.Z;
    TArray<AActor*> Walls;
    OntoTwinWalls::Collect(GetWorld(), WallTag, Walls);
    for (AActor* Wall : Walls) PlacementWalls.Add(Wall);
    PlacementPreview->SetActorHiddenInGame(true);
    PlacementModelKey = ModelKey;
    PlacementLabel = Label;
    PlacementProjectId = BoundProjectId;
    bPlacementDrag = bDrag;
    PlacementId = FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphens);
    UWidgetBlueprintLibrary::SetFocusToGameViewport();
    RuntimeStatusMessage = TEXT("移动到放置位置，左键确认，Esc 取消");
    if (RuntimeEditorPanel) RuntimeEditorPanel->ShowToast(RuntimeStatusMessage, EOntoTwinRuntimeToastType::Info);
    return true;
}

void ATwinSceneManager::CancelUnconfirmedModelPlacement()
{
    if (PlacementPreview && !bPlacementSending) CancelModelPlacement();
}

void ATwinSceneManager::CancelModelPlacement()
{
    if (IsValid(PlacementPreview)) PlacementPreview->Destroy();
    PlacementPreview = nullptr;
    PlacementWalls.Reset();
    PlacementId.Reset();
    PlacementProjectId.Reset();
    bPlacementPositionFrozen = false;
    bPlacementDrag = false;
    PlacementBusinessId.Reset();
    PlacementName.Reset();
    PlacementType.Reset();
    if (RuntimeEditorPanel) RuntimeEditorPanel->ClosePlacementDetails();
    bPlacementSending = false;
}

FVector ATwinSceneManager::SnapPlacementLocation(FVector Location, const FHitResult& Hit) const
{
    if (bEnableGridSnap && GridSnapSizeCm > 0.f) {
        Location.X = FMath::GridSnap(Location.X, double(GridSnapSizeCm));
        Location.Y = FMath::GridSnap(Location.Y, double(GridSnapSizeCm));
    }
    if (!bEnableWallSnap) return Location;
    const FVector Center = Location + PlacementRelativeBounds.GetCenter();
    const FVector Extent = PlacementRelativeBounds.GetExtent();
    FVector Snapped = Location;
    double Nearest = WallSnapDistanceCm;
    for (const auto& WeakWall : PlacementWalls) {
        AActor* Wall = WeakWall.Get();
        if (!Wall) continue;
        const FBox Bounds = Wall->GetComponentsBoundingBox(true);
        if (!Bounds.IsValid || Center.Z + Extent.Z < Bounds.Min.Z || Center.Z - Extent.Z > Bounds.Max.Z) continue;
        FVector Surface = Bounds.GetClosestPointTo(Center);
        Surface.Z = Center.Z;
        FVector Normal = (Center - Surface).GetSafeNormal2D();
        const bool HitWallFace = Hit.GetActor() == Wall && FMath::Abs(Hit.ImpactNormal.Z) < 0.35f;
        if (HitWallFace || Normal.IsNearlyZero()) {
            if (!HitWallFace) continue;
            Normal = Hit.ImpactNormal.GetSafeNormal2D();
            Surface = Hit.ImpactPoint;
            Surface.Z = Center.Z;
        }
        const double Radius = FMath::Abs(Normal.X) * Extent.X + FMath::Abs(Normal.Y) * Extent.Y;
        const double Gap = FVector::DotProduct(Center - Surface, Normal) - Radius;
        if (!HitWallFace && FMath::Abs(Gap) > Nearest) continue;
        Nearest = FMath::Abs(Gap);
        Snapped = Location - Normal * Gap;
        if (HitWallFace) break;
    }
    return Snapped;
}

void ATwinSceneManager::TickModelPlacement(APlayerController* PC, float DeltaTime)
{
    if (bPlacementSending) return;
    if (PC->WasInputKeyJustPressed(CancelKey))
    {
        CancelModelPlacement();
        return;
    }
    const bool bOverPanel = RuntimeEditorPanel && RuntimeEditorPanel->IsPointerOverPanel();
    if (bPlacementPositionFrozen) return;
    const bool bReleased = bPlacementDrag && !FSlateApplication::Get().GetPressedMouseButtons().Contains(EKeys::LeftMouseButton);
    TickRuntimeEditorCamera(PC, DeltaTime, bOverPanel);
    if (!bPlacementPositionFrozen)
    {
        FVector Origin, Direction;
        FHitResult Hit;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(OntoTwinPlaceModel), true);
        Query.AddIgnoredActor(PlacementPreview);
        Query.AddIgnoredActor(RuntimeGizmo);
        Query.AddIgnoredActor(PC->GetPawn());
        const bool bHit = !bOverPanel && PC->DeprojectMousePositionToWorld(Origin, Direction)
            && GetWorld()->LineTraceSingleByChannel(Hit, Origin, Origin + Direction * 1000000., ECC_Visibility, Query);
        PlacementPreview->SetActorHiddenInGame(!bHit);
        if (!bHit)
        {
            if (bReleased) CancelModelPlacement();
            return;
        }
        FVector Location = Hit.ImpactPoint + FVector(0., 0., PlacementBottomOffset);
        if (bEnableWallSnap && OntoTwinWalls::IsWall(Hit.GetActor(), WallTag)
            && FMath::Abs(Hit.ImpactNormal.Z) < 0.35f) {
            const FVector Edge = Hit.ImpactPoint + Hit.ImpactNormal.GetSafeNormal2D() * 2.;
            FHitResult Floor;
            if (GetWorld()->LineTraceSingleByChannel(Floor, Edge, Edge - FVector(0., 0., 100000.), ECC_Visibility, Query))
                Location.Z = Floor.ImpactPoint.Z + PlacementBottomOffset;
        }
        PlacementPreview->SetActorLocation(SnapPlacementLocation(Location, Hit));
    }
    if (!bOverPanel && (bReleased || (!bPlacementDrag && PC->WasInputKeyJustPressed(EKeys::LeftMouseButton))))
        OpenPlacementDetails();
}

void ATwinSceneManager::OpenPlacementDetails()
{
    bPlacementPositionFrozen = true;
    bPlacementDrag = false;
    const FString Id = PlacementId;
    RuntimeEditorPanel->ShowPlacementDetails(PlacementLabel, nullptr, TEXT("正在读取放置信息…"));
    auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BackendBaseUrl / TEXT("api/v2/runtime-editor/placement-options")
        + TEXT("?expected_project_id=") + FGenericPlatformHttp::UrlEncode(PlacementProjectId)
        + TEXT("&model=") + FGenericPlatformHttp::UrlEncode(PlacementModelKey)
        + TEXT("&label=") + FGenericPlatformHttp::UrlEncode(PlacementLabel));
    Request->SetVerb(TEXT("GET"));
    AddUEProjectHeaders(Request);
    Request->OnProcessRequestComplete().BindWeakLambda(this,[this,Id](FHttpRequestPtr,FHttpResponsePtr Response,bool bOk){
        if (Id != PlacementId || !RuntimeEditorPanel) return;
        TSharedPtr<FJsonObject> Options;
        if (bOk && Response && EHttpResponseCodes::IsOk(Response->GetResponseCode()))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()),Options);
        RuntimeEditorPanel->ShowPlacementDetails(PlacementLabel, Options, Options ? FString() : TEXT("无法读取放置信息，请取消后重试"));
    });
    if (!Request->ProcessRequest()) RuntimeEditorPanel->SetPlacementFeedback(TEXT("无法连接后台，请取消后重试"));
}

bool ATwinSceneManager::LocatePlacementConflict(const FString& Id)
{
    ATwinInstance* Instance = InstanceRegistry.FindRef(Id);
    if (!IsValid(Instance)) return false;
    CancelModelPlacement();
    SelectRuntimeInstance(Instance,false);
    FocusManagedInstance(Instance);
    return true;
}

void ATwinSceneManager::SavePlacementDetails(const FString& Id, const FString& Name, const FString& Rid)
{
    if (!bPlacementPositionFrozen || bPlacementSending) return;
    PlacementBusinessId = Id;
    PlacementName = Name;
    PlacementType = Rid;
    ConfirmModelPlacement();
}

void ATwinSceneManager::ConfirmModelPlacement()
{
    if (!PlacementPreview || bPlacementSending) return;
    if (!bRuntimeCanSave || BoundProjectId.IsEmpty() || BoundProjectId != PlacementProjectId)
    {
        if (RuntimeEditorPanel) RuntimeEditorPanel->ShowToast(TEXT("请先为当前关卡绑定可写数据集，再选择模型放置"), EOntoTwinRuntimeToastType::Warning);
        return;
    }
    auto Payload = MakeShared<FJsonObject>();
    Payload->SetStringField(TEXT("placement_id"), PlacementId);
    Payload->SetStringField(TEXT("expected_project_id"), PlacementProjectId);
    Payload->SetStringField(TEXT("model"), PlacementModelKey);
    Payload->SetStringField(TEXT("label"), PlacementLabel);
    Payload->SetStringField(TEXT("instance_id"), PlacementBusinessId);
    Payload->SetStringField(TEXT("display_name"), PlacementName);
    Payload->SetStringField(TEXT("object_type_rid"), PlacementType);
    const FVector Location = PlacementPreview->GetActorLocation();
    auto Position = MakeShared<FJsonObject>();
    Position->SetNumberField(TEXT("x"), Location.X);
    Position->SetNumberField(TEXT("y"), Location.Y);
    Position->SetNumberField(TEXT("z"), Location.Z);
    Payload->SetObjectField(TEXT("position"), Position);
    FString Body;
    FJsonSerializer::Serialize(Payload, TJsonWriterFactory<>::Create(&Body));
    auto Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(BackendBaseUrl / TEXT("api/v2/runtime-editor/placements"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddUEProjectHeaders(Request);
    Request->SetContentAsString(Body);
    bPlacementSending = true;
    bPlacementPositionFrozen = true;
    Request->SetTimeout(15.f);
    Request->OnProcessRequestComplete().BindWeakLambda(this,
        [this, Id = PlacementId](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            if (Id != PlacementId) return;
            bPlacementSending = false;
            TSharedPtr<FJsonObject> Root;
            if (Response) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Response->GetContentAsString()), Root);
            const TSharedPtr<FJsonObject>* Snapshot = nullptr;
            if (!bOk || !Response || !EHttpResponseCodes::IsOk(Response->GetResponseCode())
                || !Root || !Root->TryGetObjectField(TEXT("snapshot"), Snapshot))
            {
                FString Reason;
                if (Root) Root->TryGetStringField(TEXT("message"), Reason);
                if (Reason.IsEmpty()) Reason = TEXT("未收到保存确认，请点确定重试，或点取消退出");
                if (RuntimeEditorPanel) RuntimeEditorPanel->SetPlacementFeedback(Reason);
                return;
            }
            const bool bSameProject = BoundProjectId == PlacementProjectId;
            CancelModelPlacement();
            if (!bSameProject || !bRuntimeEditMode) return;
            const FString InstanceId = Root->GetStringField(TEXT("instance_id"));
            ProcessSnapshot(*Snapshot);
            FRuntimeEditCommand History;
            History.Label = PlacementLabel;
            if (const auto* Instance = InstanceRegistry.FindRef(InstanceId))
                History.Label = Instance->GetTwinDisplayName();
            History.SavedObjectIds.Add(InstanceId);
            History.bCreatedObjects = true;
            RecordRuntimeCommand(MoveTemp(History));
            if (auto* Instance = InstanceRegistry.FindRef(InstanceId))
                SelectRuntimeInstance(Instance, false);
            if (RuntimeEditorPanel) RuntimeEditorPanel->ShowToast(TEXT("模型已放置并保存"), EOntoTwinRuntimeToastType::Success);
        });
    if (!Request->ProcessRequest())
    {
        bPlacementSending = false;
        if (RuntimeEditorPanel) RuntimeEditorPanel->SetPlacementFeedback(TEXT("无法连接后台，请重试"));
    }
}
