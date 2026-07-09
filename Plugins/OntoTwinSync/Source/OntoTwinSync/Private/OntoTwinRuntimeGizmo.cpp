#include "OntoTwinRuntimeGizmo.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AOntoTwinRuntimeGizmo::AOntoTwinRuntimeGizmo()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;

    GizmoRoot = CreateDefaultSubobject<USceneComponent>(TEXT("GizmoRoot"));
    RootComponent = GizmoRoot;

    MovePlane = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MoveXY"));
    MovePlane->SetupAttachment(GizmoRoot);

    RotateHandle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RotateYaw"));
    RotateHandle->SetupAttachment(GizmoRoot);

    ForwardArrow = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ForwardArrow"));
    ForwardArrow->SetupAttachment(GizmoRoot);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));

    if (CubeMesh.Succeeded())
    {
        MovePlane->SetStaticMesh(CubeMesh.Object);
        RotateHandle->SetStaticMesh(CubeMesh.Object);
    }
    if (ConeMesh.Succeeded())
    {
        ForwardArrow->SetStaticMesh(ConeMesh.Object);
    }

    MovePlane->SetRelativeLocation(FVector(0.f, 0.f, 8.f));
    MovePlane->SetRelativeScale3D(FVector(1.2f, 1.2f, 0.03f));

    RotateHandle->SetRelativeLocation(FVector(160.f, 0.f, 35.f));
    RotateHandle->SetRelativeScale3D(FVector(0.22f, 0.22f, 0.22f));

    ForwardArrow->SetRelativeLocation(FVector(90.f, 0.f, 65.f));
    ForwardArrow->SetRelativeRotation(FRotator(0.f, 90.f, 0.f));
    ForwardArrow->SetRelativeScale3D(FVector(0.24f, 0.24f, 0.45f));

    ConfigurePart(MovePlane, true);
    ConfigurePart(RotateHandle, true);
    ConfigurePart(ForwardArrow, false);

    SetGizmoEnabled(false);
}

void AOntoTwinRuntimeGizmo::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (bGizmoEnabled)
    {
        DrawRuntimeVisuals();
    }
}

void AOntoTwinRuntimeGizmo::ConfigurePart(UStaticMeshComponent* Component, bool bEnableCollision)
{
    if (!Component) return;

    Component->SetMobility(EComponentMobility::Movable);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCollisionEnabled(bEnableCollision ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(bEnableCollision ? ECR_Block : ECR_Ignore);
    Component->SetCastShadow(false);
    Component->SetRenderInMainPass(false);
}

void AOntoTwinRuntimeGizmo::UpdateForTarget(AActor* TargetActor)
{
    if (!TargetActor)
    {
        SetGizmoEnabled(false);
        return;
    }

    const FTransform TargetTransform = TargetActor->GetActorTransform();
    SetActorLocation(TargetTransform.GetLocation());
    SetActorRotation(FRotator(0.f, TargetActor->GetActorRotation().Yaw, 0.f));

    const FBox Bounds = TargetActor->GetComponentsBoundingBox(true);
    const FVector Extent = Bounds.GetExtent();
    const float Width = FMath::Clamp((Extent.X * 2.f + 80.f) / 100.f, 0.8f, 8.f);
    const float Depth = FMath::Clamp((Extent.Y * 2.f + 80.f) / 100.f, 0.8f, 8.f);
    const float HandleDistance = FMath::Max(Extent.X, Extent.Y) + 110.f;
    MovePlaneHalfSize = FVector2D(Width * 50.f, Depth * 50.f);
    RotateRadius = HandleDistance;
    ForwardArrowLength = FMath::Max(140.f, Extent.X + 130.f);

    MovePlane->SetRelativeScale3D(FVector(Width, Depth, 0.03f));
    RotateHandle->SetRelativeLocation(FVector(HandleDistance, 0.f, 35.f));
    ForwardArrow->SetRelativeLocation(FVector(FMath::Max(90.f, Extent.X + 70.f), 0.f, 65.f));

    SetGizmoEnabled(true);
}

void AOntoTwinRuntimeGizmo::SetGizmoEnabled(bool bEnabled)
{
    bGizmoEnabled = bEnabled;
    SetActorHiddenInGame(false);
    SetActorEnableCollision(bEnabled);
    SetActorTickEnabled(bEnabled);

    if (MovePlane)
    {
        MovePlane->SetVisibility(false, true);
        MovePlane->SetHiddenInGame(true);
        MovePlane->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    if (RotateHandle)
    {
        RotateHandle->SetVisibility(false, true);
        RotateHandle->SetHiddenInGame(true);
        RotateHandle->SetCollisionEnabled(bEnabled ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    }
    if (ForwardArrow)
    {
        ForwardArrow->SetVisibility(false, true);
        ForwardArrow->SetHiddenInGame(true);
    }
}

EOntoTwinRuntimeGizmoPart AOntoTwinRuntimeGizmo::GetPartForComponent(const UPrimitiveComponent* Component) const
{
    if (!Component) return EOntoTwinRuntimeGizmoPart::None;
    if (Component == MovePlane) return EOntoTwinRuntimeGizmoPart::MoveXY;
    if (Component == RotateHandle) return EOntoTwinRuntimeGizmoPart::RotateYaw;
    return EOntoTwinRuntimeGizmoPart::None;
}

void AOntoTwinRuntimeGizmo::DrawRuntimeVisuals() const
{
    UWorld* World = GetWorld();
    if (!World) return;

    const FColor MoveColor(40, 180, 255);
    const FColor RotateColor(255, 170, 40);
    const FColor ForwardColor(255, 230, 80);
    const float Duration = 0.0f;
    const uint8 DepthPriority = 0;

    const FVector BaseLocation = GetActorLocation();
    const FQuat ActorQuat = GetActorQuat();
    const FVector PlaneCenter = MovePlane ? MovePlane->GetComponentLocation() : BaseLocation + FVector(0.f, 0.f, 8.f);
    DrawDebugBox(
        World,
        PlaneCenter,
        FVector(MovePlaneHalfSize.X, MovePlaneHalfSize.Y, 4.f),
        ActorQuat,
        MoveColor,
        false,
        Duration,
        DepthPriority,
        2.0f);

    const FVector RingCenter = BaseLocation + FVector(0.f, 0.f, 35.f);
    const int32 Segments = 64;
    FVector PrevPoint = FVector::ZeroVector;
    for (int32 i = 0; i <= Segments; ++i)
    {
        const float Angle = (static_cast<float>(i) / static_cast<float>(Segments)) * 2.0f * PI;
        const FVector LocalPoint(FMath::Cos(Angle) * RotateRadius, FMath::Sin(Angle) * RotateRadius, 0.f);
        const FVector WorldPoint = RingCenter + ActorQuat.RotateVector(LocalPoint);
        if (i > 0)
        {
            DrawDebugLine(World, PrevPoint, WorldPoint, RotateColor, false, Duration, DepthPriority, 2.5f);
        }
        PrevPoint = WorldPoint;
    }

    const FVector HandleLocation = RotateHandle ? RotateHandle->GetComponentLocation() : RingCenter + GetActorForwardVector() * RotateRadius;
    DrawDebugSphere(World, HandleLocation, 18.f, 12, RotateColor, false, Duration, DepthPriority, 2.5f);

    const FVector ArrowStart = BaseLocation + FVector(0.f, 0.f, 70.f);
    const FVector ArrowEnd = ArrowStart + GetActorForwardVector() * ForwardArrowLength;
    DrawDebugDirectionalArrow(World, ArrowStart, ArrowEnd, 34.f, ForwardColor, false, Duration, DepthPriority, 4.0f);
}
