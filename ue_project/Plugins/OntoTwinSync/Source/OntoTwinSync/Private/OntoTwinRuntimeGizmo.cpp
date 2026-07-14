#include "OntoTwinRuntimeGizmo.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "SceneTypes.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr int32 RingVisualSegmentCount = 32;
constexpr int32 RingHitSegmentCount = 24;
constexpr float BaseStrokeWidth = 0.032f;
constexpr float BaseStrokeHeight = 0.016f;
constexpr float MoveTopClearance = 16.0f;

FLinearColor ColorFromHex(uint8 R, uint8 G, uint8 B)
{
    return FLinearColor::FromSRGBColor(FColor(R, G, B));
}
}

AOntoTwinRuntimeGizmo::AOntoTwinRuntimeGizmo()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;

    GizmoRoot = CreateDefaultSubobject<USceneComponent>(TEXT("GizmoRoot"));
    RootComponent = GizmoRoot;

    MoveHitPlane = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MoveXYHit"));
    MoveHitPlane->SetupAttachment(GizmoRoot);

    RotateHitHandle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RotateYawHit"));
    RotateHitHandle->SetupAttachment(GizmoRoot);

    for (int32 Index = 0; Index < 4; ++Index)
    {
        UStaticMeshComponent* MoveVisual = CreateDefaultSubobject<UStaticMeshComponent>(
            FName(*FString::Printf(TEXT("MoveVisual_%02d"), Index)));
        MoveVisual->SetupAttachment(GizmoRoot);
        MoveVisuals.Add(MoveVisual);

        UStaticMeshComponent* MoveArrowVisual = CreateDefaultSubobject<UStaticMeshComponent>(
            FName(*FString::Printf(TEXT("MoveArrowVisual_%02d"), Index)));
        MoveArrowVisual->SetupAttachment(GizmoRoot);
        MoveArrowVisuals.Add(MoveArrowVisual);
    }

    ZAxisHit = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MoveZHit"));
    ZAxisHit->SetupAttachment(GizmoRoot);

    ZAxisShaftVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MoveZShaftVisual"));
    ZAxisShaftVisual->SetupAttachment(GizmoRoot);

    ZAxisArrowVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MoveZArrowVisual"));
    ZAxisArrowVisual->SetupAttachment(GizmoRoot);

    for (int32 Index = 0; Index < RingVisualSegmentCount; ++Index)
    {
        UStaticMeshComponent* RingVisual = CreateDefaultSubobject<UStaticMeshComponent>(
            FName(*FString::Printf(TEXT("RotateVisual_%02d"), Index)));
        RingVisual->SetupAttachment(GizmoRoot);
        RotateRingVisuals.Add(RingVisual);
    }

    for (int32 Index = 0; Index < RingHitSegmentCount; ++Index)
    {
        UStaticMeshComponent* RingHit = CreateDefaultSubobject<UStaticMeshComponent>(
            FName(*FString::Printf(TEXT("RotateHit_%02d"), Index)));
        RingHit->SetupAttachment(GizmoRoot);
        RotateHitSegments.Add(RingHit);
    }

    RotateHandleVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RotateHandleVisual"));
    RotateHandleVisual->SetupAttachment(GizmoRoot);

    SnapMarker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SnapMarker"));
    SnapMarker->SetupAttachment(GizmoRoot);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

    BaseGizmoMaterial = BasicMaterial.Succeeded() ? BasicMaterial.Object : nullptr;

    if (CubeMesh.Succeeded())
    {
        MoveHitPlane->SetStaticMesh(CubeMesh.Object);
        ZAxisHit->SetStaticMesh(CubeMesh.Object);
        ZAxisShaftVisual->SetStaticMesh(CubeMesh.Object);
        for (UStaticMeshComponent* MoveVisual : MoveVisuals)
        {
            MoveVisual->SetStaticMesh(CubeMesh.Object);
        }
        for (UStaticMeshComponent* RingVisual : RotateRingVisuals)
        {
            RingVisual->SetStaticMesh(CubeMesh.Object);
        }
        for (UStaticMeshComponent* RingHit : RotateHitSegments)
        {
            RingHit->SetStaticMesh(CubeMesh.Object);
        }
    }
    if (SphereMesh.Succeeded())
    {
        RotateHitHandle->SetStaticMesh(SphereMesh.Object);
        RotateHandleVisual->SetStaticMesh(SphereMesh.Object);
        SnapMarker->SetStaticMesh(SphereMesh.Object);
    }
    if (ConeMesh.Succeeded())
    {
        ZAxisArrowVisual->SetStaticMesh(ConeMesh.Object);
        for (UStaticMeshComponent* MoveArrowVisual : MoveArrowVisuals)
        {
            MoveArrowVisual->SetStaticMesh(ConeMesh.Object);
        }
    }

    MoveHitPlane->SetRelativeLocation(FVector(0.0f, 0.0f, 10.0f));
    MoveHitPlane->SetRelativeScale3D(FVector(0.64f, 0.64f, 0.06f));
    ConfigureHitPart(MoveHitPlane);

    const FVector MoveDirections[4] =
    {
        FVector::ForwardVector,
        -FVector::ForwardVector,
        FVector::RightVector,
        -FVector::RightVector
    };
    for (int32 Index = 0; Index < MoveVisuals.Num(); ++Index)
    {
        UStaticMeshComponent* MoveVisual = MoveVisuals[Index];
        UStaticMeshComponent* MoveArrowVisual = MoveArrowVisuals[Index];
        const FVector Direction = MoveDirections[Index];
        MoveVisual->SetRelativeLocation(Direction * 18.0f + FVector(0.0f, 0.0f, 10.0f));
        MoveVisual->SetRelativeScale3D(FMath::Abs(Direction.X) > 0.5f
            ? FVector(0.32f, 0.04f, 0.015f)
            : FVector(0.04f, 0.32f, 0.015f));
        ConfigureVisualPart(MoveVisual);

        MoveArrowVisual->SetRelativeLocation(Direction * 42.0f + FVector(0.0f, 0.0f, 10.0f));
        MoveArrowVisual->SetRelativeRotation(FQuat::FindBetweenNormals(FVector::UpVector, Direction).Rotator());
        MoveArrowVisual->SetRelativeScale3D(FVector(0.085f, 0.085f, 0.14f));
        ConfigureVisualPart(MoveArrowVisual);
    }

    ZAxisHit->SetRelativeLocation(FVector(0.0f, 0.0f, 55.0f));
    ZAxisHit->SetRelativeScale3D(FVector(0.14f, 0.14f, 0.65f));
    ConfigureHitPart(ZAxisHit);

    ZAxisShaftVisual->SetRelativeLocation(FVector(0.0f, 0.0f, 47.0f));
    ZAxisShaftVisual->SetRelativeScale3D(FVector(0.025f, 0.025f, 0.62f));
    ConfigureVisualPart(ZAxisShaftVisual);

    ZAxisArrowVisual->SetRelativeLocation(FVector(0.0f, 0.0f, 88.0f));
    ZAxisArrowVisual->SetRelativeScale3D(FVector(0.09f, 0.09f, 0.14f));
    ConfigureVisualPart(ZAxisArrowVisual);

    const float VisualSegmentLength = (2.0f * PI * RingRadius / RingVisualSegmentCount) * 0.94f;
    for (int32 Index = 0; Index < RotateRingVisuals.Num(); ++Index)
    {
        const float AngleDeg = (360.0f * Index) / RotateRingVisuals.Num();
        const float AngleRad = FMath::DegreesToRadians(AngleDeg);
        UStaticMeshComponent* Segment = RotateRingVisuals[Index];
        Segment->SetRelativeLocation(FVector(
            FMath::Cos(AngleRad) * RingRadius,
            FMath::Sin(AngleRad) * RingRadius,
            0.0f));
        Segment->SetRelativeRotation(FRotator(0.0f, AngleDeg + 90.0f, 0.0f));
        Segment->SetRelativeScale3D(
            FVector(VisualSegmentLength / 100.0f, BaseStrokeWidth, BaseStrokeHeight));
        ConfigureVisualPart(Segment);
    }

    const float HitSegmentLength = (2.0f * PI * RingRadius / RingHitSegmentCount) * 1.10f;
    for (int32 Index = 0; Index < RotateHitSegments.Num(); ++Index)
    {
        const float AngleDeg = (360.0f * Index) / RotateHitSegments.Num();
        const float AngleRad = FMath::DegreesToRadians(AngleDeg);
        UStaticMeshComponent* Segment = RotateHitSegments[Index];
        Segment->SetRelativeLocation(FVector(
            FMath::Cos(AngleRad) * RingRadius,
            FMath::Sin(AngleRad) * RingRadius,
            0.0f));
        Segment->SetRelativeRotation(FRotator(0.0f, AngleDeg + 90.0f, 0.0f));
        Segment->SetRelativeScale3D(FVector(HitSegmentLength / 100.0f, 0.14f, 0.06f));
        ConfigureHitPart(Segment);
    }

    RotateHitHandle->SetRelativeLocation(FVector(RingRadius, 0.0f, 0.0f));
    RotateHitHandle->SetRelativeScale3D(FVector(0.18f));
    ConfigureHitPart(RotateHitHandle);

    RotateHandleVisual->SetRelativeLocation(FVector(RingRadius, 0.0f, 0.0f));
    RotateHandleVisual->SetRelativeScale3D(FVector(0.075f));
    ConfigureVisualPart(RotateHandleVisual);

    SnapMarker->SetRelativeScale3D(FVector(0.055f));
    ConfigureVisualPart(SnapMarker);

    SetGizmoEnabled(false);
}

void AOntoTwinRuntimeGizmo::BeginPlay()
{
    Super::BeginPlay();
    CreateRuntimeMaterials();
    ApplyInteractionColors();
}

void AOntoTwinRuntimeGizmo::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (bGizmoEnabled)
    {
        UpdateScreenScale();
        UpdateComponentLayout();
        DrawSelectionFootprint();
    }
}

void AOntoTwinRuntimeGizmo::ConfigureHitPart(UStaticMeshComponent* Component)
{
    if (!Component) return;

    Component->SetMobility(EComponentMobility::Movable);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Block);
    Component->SetCastShadow(false);
    Component->SetRenderInMainPass(false);
}

void AOntoTwinRuntimeGizmo::ConfigureVisualPart(UStaticMeshComponent* Component)
{
    if (!Component) return;

    Component->SetMobility(EComponentMobility::Movable);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetCastShadow(false);
    Component->SetDepthPriorityGroup(SDPG_Foreground);
}

void AOntoTwinRuntimeGizmo::CreateRuntimeMaterials()
{
    if (!BaseGizmoMaterial) return;

    if (!MoveMaterial)
    {
        MoveMaterial = UMaterialInstanceDynamic::Create(BaseGizmoMaterial, this, TEXT("RuntimeMoveMaterial"));
    }
    if (!RotateMaterial)
    {
        RotateMaterial = UMaterialInstanceDynamic::Create(BaseGizmoMaterial, this, TEXT("RuntimeRotateMaterial"));
    }
    if (!ZMaterial)
    {
        ZMaterial = UMaterialInstanceDynamic::Create(BaseGizmoMaterial, this, TEXT("RuntimeZMaterial"));
    }
    if (!SnapMaterial)
    {
        SnapMaterial = UMaterialInstanceDynamic::Create(BaseGizmoMaterial, this, TEXT("RuntimeSnapMaterial"));
    }

    for (UStaticMeshComponent* MoveVisual : MoveVisuals)
    {
        if (MoveVisual && MoveMaterial) MoveVisual->SetMaterial(0, MoveMaterial);
    }
    for (UStaticMeshComponent* MoveArrowVisual : MoveArrowVisuals)
    {
        if (MoveArrowVisual && MoveMaterial) MoveArrowVisual->SetMaterial(0, MoveMaterial);
    }
    for (UStaticMeshComponent* RingVisual : RotateRingVisuals)
    {
        if (RingVisual && RotateMaterial) RingVisual->SetMaterial(0, RotateMaterial);
    }
    if (RotateHandleVisual && RotateMaterial) RotateHandleVisual->SetMaterial(0, RotateMaterial);
    if (ZAxisShaftVisual && ZMaterial) ZAxisShaftVisual->SetMaterial(0, ZMaterial);
    if (ZAxisArrowVisual && ZMaterial) ZAxisArrowVisual->SetMaterial(0, ZMaterial);
    if (SnapMarker && SnapMaterial) SnapMarker->SetMaterial(0, SnapMaterial);
}

void AOntoTwinRuntimeGizmo::ApplyInteractionColors()
{
    const FLinearColor MoveBase = ColorFromHex(0, 111, 120);
    const FLinearColor MoveHover = ColorFromHex(0, 147, 158);
    const FLinearColor MoveActive = ColorFromHex(0, 186, 199);
    const FLinearColor RotateBase = ColorFromHex(184, 91, 0);
    const FLinearColor RotateHover = ColorFromHex(220, 116, 0);
    const FLinearColor RotateActive = ColorFromHex(255, 151, 31);
    const FLinearColor ZBase = ColorFromHex(38, 82, 196);
    const FLinearColor ZHover = ColorFromHex(48, 111, 224);
    const FLinearColor ZActive = ColorFromHex(78, 141, 255);

    const FLinearColor MoveColor = CurrentActivePart == EOntoTwinRuntimeGizmoPart::MoveXY
        ? MoveActive
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::MoveXY ? MoveHover : MoveBase);
    const FLinearColor RotateColor = CurrentActivePart == EOntoTwinRuntimeGizmoPart::RotateYaw
        ? RotateActive
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::RotateYaw ? RotateHover : RotateBase);
    const FLinearColor ZColor = CurrentActivePart == EOntoTwinRuntimeGizmoPart::MoveZ
        ? ZActive
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::MoveZ ? ZHover : ZBase);

    if (MoveMaterial) MoveMaterial->SetVectorParameterValue(TEXT("Color"), MoveColor);
    if (RotateMaterial) RotateMaterial->SetVectorParameterValue(TEXT("Color"), RotateColor);
    if (ZMaterial) ZMaterial->SetVectorParameterValue(TEXT("Color"), ZColor);
    if (SnapMaterial) SnapMaterial->SetVectorParameterValue(TEXT("Color"), ColorFromHex(102, 181, 138));

    const float MoveScale = CurrentActivePart == EOntoTwinRuntimeGizmoPart::MoveXY ? 1.20f
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::MoveXY ? 1.10f : 1.0f);
    for (int32 Index = 0; Index < MoveVisuals.Num(); ++Index)
    {
        if (!MoveVisuals[Index]) continue;
        const bool bHorizontal = Index < 2;
        MoveVisuals[Index]->SetRelativeScale3D(bHorizontal
            ? FVector(0.34f, BaseStrokeWidth * MoveScale, BaseStrokeHeight * MoveScale)
            : FVector(BaseStrokeWidth * MoveScale, 0.34f, BaseStrokeHeight * MoveScale));
        if (MoveArrowVisuals.IsValidIndex(Index) && MoveArrowVisuals[Index])
        {
            MoveArrowVisuals[Index]->SetRelativeScale3D(
                FVector(0.085f * MoveScale, 0.085f * MoveScale, 0.14f * MoveScale));
        }
    }

    const float ZScale = CurrentActivePart == EOntoTwinRuntimeGizmoPart::MoveZ ? 1.20f
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::MoveZ ? 1.10f : 1.0f);
    if (ZAxisShaftVisual)
    {
        ZAxisShaftVisual->SetRelativeScale3D(
            FVector(BaseStrokeWidth * ZScale, BaseStrokeWidth * ZScale, 0.62f));
    }
    if (ZAxisArrowVisual)
    {
        ZAxisArrowVisual->SetRelativeScale3D(FVector(0.09f * ZScale, 0.09f * ZScale, 0.14f * ZScale));
    }

    const float RotateScale = CurrentActivePart == EOntoTwinRuntimeGizmoPart::RotateYaw ? 1.20f
        : (CurrentHoverPart == EOntoTwinRuntimeGizmoPart::RotateYaw ? 1.10f : 1.0f);
    const float SegmentLength = (2.0f * PI * RingRadius / RingVisualSegmentCount) * 0.94f;
    for (UStaticMeshComponent* RingVisual : RotateRingVisuals)
    {
        if (RingVisual)
        {
            RingVisual->SetRelativeScale3D(FVector(
                SegmentLength / 100.0f,
                BaseStrokeWidth * RotateScale,
                BaseStrokeHeight * RotateScale));
        }
    }
    if (RotateHandleVisual)
    {
        RotateHandleVisual->SetRelativeScale3D(FVector(0.075f * RotateScale));
    }
}

void AOntoTwinRuntimeGizmo::UpdateForTarget(AActor* TargetActor)
{
    if (!TargetActor)
    {
        SetGizmoEnabled(false);
        return;
    }

    TargetBounds = TargetActor->GetComponentsBoundingBox(true);
    const FVector TargetLocation = TargetActor->GetActorLocation();
    SetActorLocation(TargetLocation);
    SetActorRotation(FRotator(0.0f, TargetActor->GetActorRotation().Yaw, 0.0f));
    SetGizmoEnabled(true);
    UpdateComponentLayout();
}

void AOntoTwinRuntimeGizmo::SetGizmoEnabled(bool bEnabled)
{
    bGizmoEnabled = bEnabled;
    SetActorHiddenInGame(!bEnabled);
    SetActorEnableCollision(bEnabled);
    SetActorTickEnabled(bEnabled);

    if (MoveHitPlane)
    {
        MoveHitPlane->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    if (ZAxisHit)
    {
        ZAxisHit->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    if (RotateHitHandle)
    {
        RotateHitHandle->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    for (UStaticMeshComponent* RingHit : RotateHitSegments)
    {
        if (RingHit) RingHit->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }

    for (UStaticMeshComponent* MoveVisual : MoveVisuals)
    {
        if (!MoveVisual) continue;
        MoveVisual->SetHiddenInGame(!bEnabled);
        MoveVisual->SetVisibility(bEnabled, true);
    }
    for (UStaticMeshComponent* MoveArrowVisual : MoveArrowVisuals)
    {
        if (!MoveArrowVisual) continue;
        MoveArrowVisual->SetHiddenInGame(!bEnabled);
        MoveArrowVisual->SetVisibility(bEnabled, true);
    }
    for (UStaticMeshComponent* RingVisual : RotateRingVisuals)
    {
        if (!RingVisual) continue;
        RingVisual->SetHiddenInGame(!bEnabled);
        RingVisual->SetVisibility(bEnabled, true);
    }
    if (RotateHandleVisual)
    {
        RotateHandleVisual->SetHiddenInGame(!bEnabled);
        RotateHandleVisual->SetVisibility(bEnabled, true);
    }
    if (ZAxisShaftVisual)
    {
        ZAxisShaftVisual->SetHiddenInGame(!bEnabled);
        ZAxisShaftVisual->SetVisibility(bEnabled, true);
    }
    if (ZAxisArrowVisual)
    {
        ZAxisArrowVisual->SetHiddenInGame(!bEnabled);
        ZAxisArrowVisual->SetVisibility(bEnabled, true);
    }
    if (SnapMarker)
    {
        const bool bShowSnapMarker = bEnabled && CurrentSnapState == EOntoTwinRuntimeSnapState::Wall;
        SnapMarker->SetHiddenInGame(!bShowSnapMarker);
        SnapMarker->SetVisibility(bShowSnapMarker, true);
    }
}

void AOntoTwinRuntimeGizmo::SetInteractionState(
    EOntoTwinRuntimeGizmoPart HoverPart,
    EOntoTwinRuntimeGizmoPart ActivePart)
{
    if (CurrentHoverPart == HoverPart && CurrentActivePart == ActivePart)
    {
        return;
    }

    CurrentHoverPart = HoverPart;
    CurrentActivePart = ActivePart;
    ApplyInteractionColors();
}

void AOntoTwinRuntimeGizmo::SetSnapFeedback(
    EOntoTwinRuntimeSnapState SnapState,
    const FVector& WorldPoint)
{
    CurrentSnapState = SnapState;

    if (!SnapMarker) return;
    const bool bShowMarker = bGizmoEnabled && SnapState == EOntoTwinRuntimeSnapState::Wall;
    if (bShowMarker)
    {
        SnapMarker->SetWorldLocation(WorldPoint + FVector(0.0f, 0.0f, 8.0f));
    }
    SnapMarker->SetHiddenInGame(!bShowMarker);
    SnapMarker->SetVisibility(bShowMarker, true);
}

EOntoTwinRuntimeGizmoPart AOntoTwinRuntimeGizmo::GetPartForComponent(const UPrimitiveComponent* Component) const
{
    if (!Component) return EOntoTwinRuntimeGizmoPart::None;
    if (Component == MoveHitPlane) return EOntoTwinRuntimeGizmoPart::MoveXY;
    if (Component == ZAxisHit) return EOntoTwinRuntimeGizmoPart::MoveZ;
    if (Component == RotateHitHandle)
    {
        return EOntoTwinRuntimeGizmoPart::RotateYaw;
    }
    for (const UStaticMeshComponent* RingHit : RotateHitSegments)
    {
        if (Component == RingHit) return EOntoTwinRuntimeGizmoPart::RotateYaw;
    }
    return EOntoTwinRuntimeGizmoPart::None;
}

float AOntoTwinRuntimeGizmo::GetMoveInteractionPlaneZ() const
{
    return MoveHitPlane ? MoveHitPlane->GetComponentLocation().Z : GetActorLocation().Z;
}

float AOntoTwinRuntimeGizmo::GetRotateInteractionPlaneZ() const
{
    return RotateHitHandle ? RotateHitHandle->GetComponentLocation().Z : GetActorLocation().Z;
}

void AOntoTwinRuntimeGizmo::UpdateScreenScale()
{
    UWorld* World = GetWorld();
    APlayerController* PlayerController = World ? World->GetFirstPlayerController() : nullptr;
    if (!PlayerController || !PlayerController->PlayerCameraManager) return;

    int32 ViewportWidth = 0;
    int32 ViewportHeight = 0;
    PlayerController->GetViewportSize(ViewportWidth, ViewportHeight);
    if (ViewportHeight <= 0) return;

    FVector CameraLocation = FVector::ZeroVector;
    FRotator CameraRotation = FRotator::ZeroRotator;
    PlayerController->GetPlayerViewPoint(CameraLocation, CameraRotation);

    const float Distance = FMath::Max(FVector::Distance(CameraLocation, GetActorLocation()), 1.0f);
    const float HalfFovRadians = FMath::DegreesToRadians(
        FMath::Clamp(PlayerController->PlayerCameraManager->GetFOVAngle(), 30.0f, 140.0f) * 0.5f);
    const float WorldDiameter = 2.0f * Distance * FMath::Tan(HalfFovRadians) *
        (TargetScreenDiameterPx / static_cast<float>(ViewportHeight));
    const float UniformScale = FMath::Clamp(WorldDiameter / BaseGizmoDiameter, 0.35f, 3.0f);
    SetActorScale3D(FVector(UniformScale));
}

void AOntoTwinRuntimeGizmo::UpdateComponentLayout()
{
    if (!TargetBounds.IsValid) return;

    const float UniformScale = FMath::Max(GetActorScale3D().Z, UE_SMALL_NUMBER);
    const float MoveHeight =
        (TargetBounds.Max.Z - GetActorLocation().Z) / UniformScale + MoveTopClearance;
    const float RotateHeight =
        (TargetBounds.GetCenter().Z - GetActorLocation().Z) / UniformScale;

    if (MoveHitPlane)
    {
        MoveHitPlane->SetRelativeLocation(FVector(0.0f, 0.0f, MoveHeight));
    }

    const FVector MoveDirections[4] =
    {
        FVector::ForwardVector,
        -FVector::ForwardVector,
        FVector::RightVector,
        -FVector::RightVector
    };
    for (int32 Index = 0; Index < MoveVisuals.Num(); ++Index)
    {
        const FVector Direction = MoveDirections[Index];
        if (MoveVisuals[Index])
        {
            MoveVisuals[Index]->SetRelativeLocation(Direction * 18.0f + FVector(0.0f, 0.0f, MoveHeight));
        }
        if (MoveArrowVisuals.IsValidIndex(Index) && MoveArrowVisuals[Index])
        {
            MoveArrowVisuals[Index]->SetRelativeLocation(
                Direction * 42.0f + FVector(0.0f, 0.0f, MoveHeight));
        }
    }

    if (ZAxisHit)
    {
        ZAxisHit->SetRelativeLocation(FVector(0.0f, 0.0f, MoveHeight + 45.0f));
    }
    if (ZAxisShaftVisual)
    {
        ZAxisShaftVisual->SetRelativeLocation(FVector(0.0f, 0.0f, MoveHeight + 37.0f));
    }
    if (ZAxisArrowVisual)
    {
        ZAxisArrowVisual->SetRelativeLocation(FVector(0.0f, 0.0f, MoveHeight + 78.0f));
    }

    for (int32 Index = 0; Index < RotateRingVisuals.Num(); ++Index)
    {
        if (!RotateRingVisuals[Index]) continue;
        const float AngleRad = FMath::DegreesToRadians((360.0f * Index) / RotateRingVisuals.Num());
        RotateRingVisuals[Index]->SetRelativeLocation(FVector(
            FMath::Cos(AngleRad) * RingRadius,
            FMath::Sin(AngleRad) * RingRadius,
            RotateHeight));
    }
    for (int32 Index = 0; Index < RotateHitSegments.Num(); ++Index)
    {
        if (!RotateHitSegments[Index]) continue;
        const float AngleRad = FMath::DegreesToRadians((360.0f * Index) / RotateHitSegments.Num());
        RotateHitSegments[Index]->SetRelativeLocation(FVector(
            FMath::Cos(AngleRad) * RingRadius,
            FMath::Sin(AngleRad) * RingRadius,
            RotateHeight));
    }
    if (RotateHitHandle)
    {
        RotateHitHandle->SetRelativeLocation(FVector(RingRadius, 0.0f, RotateHeight));
    }
    if (RotateHandleVisual)
    {
        RotateHandleVisual->SetRelativeLocation(FVector(RingRadius, 0.0f, RotateHeight));
    }
}

void AOntoTwinRuntimeGizmo::DrawSelectionFootprint() const
{
    UWorld* World = GetWorld();
    if (!World || !TargetBounds.IsValid) return;

    const float Z = TargetBounds.Min.Z + 2.0f;
    const float CornerLength = FMath::Clamp(
        FMath::Min(TargetBounds.GetExtent().X, TargetBounds.GetExtent().Y) * 0.28f,
        12.0f,
        42.0f);
    const FVector P0(TargetBounds.Min.X, TargetBounds.Min.Y, Z);
    const FVector P1(TargetBounds.Max.X, TargetBounds.Min.Y, Z);
    const FVector P2(TargetBounds.Max.X, TargetBounds.Max.Y, Z);
    const FVector P3(TargetBounds.Min.X, TargetBounds.Max.Y, Z);
    const FColor SelectionColor = CurrentSnapState == EOntoTwinRuntimeSnapState::None
        ? FColor(121, 147, 166)
        : FColor(102, 181, 138);

    DrawDebugLine(World, P0, P0 + FVector(CornerLength, 0.0f, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P0, P0 + FVector(0.0f, CornerLength, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P1, P1 + FVector(-CornerLength, 0.0f, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P1, P1 + FVector(0.0f, CornerLength, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P2, P2 + FVector(-CornerLength, 0.0f, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P2, P2 + FVector(0.0f, -CornerLength, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P3, P3 + FVector(CornerLength, 0.0f, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
    DrawDebugLine(World, P3, P3 + FVector(0.0f, -CornerLength, 0.0f), SelectionColor, false, 0.0f, 1, 2.5f);
}
