#include "SceneInteraction/TwinRouteFollowerComponent.h"

#include "SceneInteraction/TwinRoamingRoute.h"
#include "SceneInteraction/TwinRoamingCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/SplineComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"

namespace
{
constexpr float RouteLookAheadSeconds = 0.8f;
constexpr float RouteMinLookAheadCm = 100.0f;
constexpr float RouteMaxLookAheadCm = 200.0f;
constexpr float RouteMaxYawRateDegS = 100.0f;
constexpr float RouteSteeringLookAheadSeconds = 0.25f;
constexpr float RouteMinSteeringLookAheadCm = 30.0f;
constexpr float RouteMaxSteeringLookAheadCm = 80.0f;
constexpr float RouteArrivalToleranceCm = 20.0f;
constexpr float RouteProgressThresholdCm = 5.0f;
constexpr float RouteBlockedTimeoutSeconds = 2.0f;

void ClearRouteAnimationMotion(ACharacter* Character)
{
    if (!Character) return;
    if (ATwinRoamingCharacter* RoamingCharacter = Cast<ATwinRoamingCharacter>(Character))
    {
        RoamingCharacter->SetAutoRouteCameraSmoothing(false);
        RoamingCharacter->SetAutoRouteAnimation(false);
    }
    Character->ConsumeMovementInputVector();
    Character->GetCharacterMovement()->StopActiveMovement();
    Character->GetCharacterMovement()->StopMovementImmediately();
}

void SetRouteAnimationMotion(ACharacter* Character, FVector VisualVelocity)
{
    if (!Character) return;
    VisualVelocity.Z = 0.0f;
    if (ATwinRoamingCharacter* RoamingCharacter = Cast<ATwinRoamingCharacter>(Character))
    {
        RoamingCharacter->SetAutoRouteCameraSmoothing(true);
        if (RoamingCharacter->SetAutoRouteAnimation(true, VisualVelocity.Size2D()))
        {
            return;
        }
    }
    // CharacterMovement now owns automatic route motion. Its real velocity
    // and acceleration drive ordinary locomotion AnimBPs; do not overwrite
    // Velocity here or StepUp/floor following would be bypassed again.
}
}

UTwinRouteFollowerComponent::UTwinRouteFollowerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UTwinRouteFollowerComponent::Configure(
    ATwinRoamingRoute* InRoute,
    float InSpeedCmS,
    bool bInLoop,
    bool bAutoStart)
{
    Route = InRoute;
    SpeedCmS = FMath::Max(1.0f, InSpeedCmS);
    bLoop = bInLoop && Route && Route->Spline && Route->Spline->IsClosedLoop();
    DistanceAlongSpline = 0.0f;
    RouteState = Route && Route->Spline
        ? (bAutoStart ? ETwinRoamingRouteState::AutoRoute : ETwinRoamingRouteState::Idle)
        : ETwinRoamingRouteState::Unavailable;
    ResetStallDetection();
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        ClearRouteAnimationMotion(Character);
    }
}

void UTwinRouteFollowerComponent::SetSpeed(float InSpeedCmS)
{
    SpeedCmS = FMath::Max(1.0f, InSpeedCmS);
}

void UTwinRouteFollowerComponent::SetLoop(bool bInLoop)
{
    bLoop = bInLoop && Route && Route->Spline && Route->Spline->IsClosedLoop();
}

void UTwinRouteFollowerComponent::PauseByUser()
{
    if (RouteState == ETwinRoamingRouteState::AutoRoute || RouteState == ETwinRoamingRouteState::Joining)
    {
        RouteState = ETwinRoamingRouteState::PausedByUser;
        ResetStallDetection();
        if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
        {
            ClearRouteAnimationMotion(Character);
        }
    }
}

bool UTwinRouteFollowerComponent::IsSafeJoin(const FVector& Target, FString& OutError) const
{
    const ACharacter* Character = Cast<ACharacter>(GetOwner());
    UWorld* World = GetWorld();
    if (!Character || !World)
    {
        OutError = TEXT("Character or world is unavailable");
        return false;
    }

    const FVector Start = Character->GetActorLocation();
    if (FMath::Abs(Start.Z - Target.Z) > 150.0f)
    {
        OutError = TEXT("Route is on another floor or outside the vertical tolerance");
        return false;
    }
    if (FVector::Dist2D(Start, Target) > 1000.0f)
    {
        OutError = TEXT("Route is too far away; restart from the beginning instead");
        return false;
    }

    // Do not pre-sweep the whole straight segment. A stair riser is a valid
    // blocking hit for a raw capsule sweep even though CharacterMovement can
    // StepUp it safely. The real join is collision-aware and times out when a
    // wall or other non-walkable obstacle prevents progress.
    return true;
}

bool UTwinRouteFollowerComponent::TryResume(FString& OutError)
{
    if (!Route || !Route->Spline)
    {
        OutError = TEXT("Default route is unavailable");
        return false;
    }
    JoinTargetDistance = FindClosestDistanceOnSpline(GetOwner()->GetActorLocation());
    const FVector Target = GetCharacterLocationAtDistance(JoinTargetDistance);
    if (!IsSafeJoin(Target, OutError)) return false;
    RouteState = ETwinRoamingRouteState::Joining;
    ResetStallDetection();
    return true;
}

bool UTwinRouteFollowerComponent::TryStartFromSpawn(FString& OutError)
{
    if (!Route || !Route->Spline)
    {
        OutError = TEXT("Default route is unavailable");
        return false;
    }
    JoinTargetDistance = 0.0f;
    const FVector Target = GetCharacterLocationAtDistance(0.0f);
    if (!IsSafeJoin(Target, OutError)) return false;
    RouteState = ETwinRoamingRouteState::Joining;
    ResetStallDetection();
    return true;
}

float UTwinRouteFollowerComponent::FindClosestDistanceOnSpline(const FVector& WorldLocation) const
{
    if (!Route || !Route->Spline) return 0.0f;
    const float Length = Route->Spline->GetSplineLength();
    const int32 Samples = FMath::Clamp(FMath::CeilToInt(Length / 100.0f), 32, 1024);
    const float Step = Length / Samples;
    float BestDistance = 0.0f;
    float BestDistanceSquared = TNumericLimits<float>::Max();
    for (int32 Index = 0; Index <= Samples; ++Index)
    {
        const float Distance = FMath::Min(Length, Index * Step);
        const FVector Point = GetCharacterLocationAtDistance(Distance);
        const float Candidate = FVector::DistSquared(WorldLocation, Point);
        if (Candidate < BestDistanceSquared)
        {
            BestDistanceSquared = Candidate;
            BestDistance = Distance;
        }
    }

    float SearchStep = Step * 0.5f;
    for (int32 Iteration = 0; Iteration < 6; ++Iteration)
    {
        for (int32 DirectionSign = -1; DirectionSign <= 1; DirectionSign += 2)
        {
            const float Direction = static_cast<float>(DirectionSign);
            const float Distance = FMath::Clamp(BestDistance + Direction * SearchStep, 0.0f, Length);
            const FVector Point = GetCharacterLocationAtDistance(Distance);
            const float Candidate = FVector::DistSquared(WorldLocation, Point);
            if (Candidate < BestDistanceSquared)
            {
                BestDistanceSquared = Candidate;
                BestDistance = Distance;
            }
        }
        SearchStep *= 0.5f;
    }
    return BestDistance;
}

FVector UTwinRouteFollowerComponent::GetCharacterLocationAtDistance(float Distance) const
{
    if (!Route || !Route->Spline) return FVector::ZeroVector;
    FVector Location = Route->Spline->GetLocationAtDistanceAlongSpline(
        Distance, ESplineCoordinateSpace::World);
    if (Route->bSplineAtGroundLevel)
    {
        if (const ACharacter* Character = Cast<ACharacter>(GetOwner()))
        {
            Location.Z += Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        }
    }
    return Location;
}

bool UTwinRouteFollowerComponent::RestartFromBeginning(FString& OutError)
{
    ACharacter* Character = Cast<ACharacter>(GetOwner());
    if (!Character || !Route || !Route->Spline || !GetWorld())
    {
        OutError = TEXT("Default route is unavailable");
        return false;
    }

    FVector Start = Route->Spline->GetLocationAtDistanceAlongSpline(0.0f, ESplineCoordinateSpace::World);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(TwinRouteRestart), false, Character);
    if (Route) QueryParams.AddIgnoredActor(Route);
    const float Radius = Character->GetCapsuleComponent()->GetScaledCapsuleRadius();
    const float HalfHeight = Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    // Runtime routes have already projected every spline point to the
    // calibrated floor. Re-tracing from high above would hit the roof first.
    Start += FVector(0.0f, 0.0f, HalfHeight + 2.0f);
    if (GetWorld()->OverlapBlockingTestByChannel(
        Start,
        Character->GetActorQuat(),
        ECC_Pawn,
        FCollisionShape::MakeCapsule(Radius, HalfHeight),
        QueryParams))
    {
        OutError = TEXT("Route start is blocked for the character capsule");
        return false;
    }

    FHitResult MoveHit;
    Character->SetActorLocation(Start, false, &MoveHit, ETeleportType::TeleportPhysics);
    DistanceAlongSpline = 0.0f;
    RouteState = ETwinRoamingRouteState::AutoRoute;
    ResetStallDetection();
    return true;
}

void UTwinRouteFollowerComponent::StopRoute()
{
    RouteState = Route ? ETwinRoamingRouteState::Idle : ETwinRoamingRouteState::Unavailable;
    ResetStallDetection();
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        ClearRouteAnimationMotion(Character);
    }
}

void UTwinRouteFollowerComponent::UpdateFacing(
    const FVector& FacingDirection,
    float DeltaTime)
{
    AActor* Owner = GetOwner();
    if (!Owner || FacingDirection.IsNearlyZero()) return;

    const float PreviousActorYaw = Owner->GetActorRotation().Yaw;
    AController* Controller = nullptr;
    float CameraYawOffset = 0.0f;
    if (ACharacter* Character = Cast<ACharacter>(Owner))
    {
        Controller = Character->GetController();
        if (Controller)
        {
            CameraYawOffset = FMath::FindDeltaAngleDegrees(
                PreviousActorYaw,
                Controller->GetControlRotation().Yaw);
        }
    }
    const float DesiredActorYaw = FacingDirection.Rotation().Yaw;
    const float NewActorYaw = FMath::FixedTurn(
        PreviousActorYaw,
        DesiredActorYaw,
        RouteMaxYawRateDegS * FMath::Max(0.0f, DeltaTime));
    Owner->SetActorRotation(FRotator(0.0f, NewActorYaw, 0.0f));
    if (Controller)
    {
        const FRotator ControlRotation = Controller->GetControlRotation();
        Controller->SetControlRotation(FRotator(
            ControlRotation.Pitch,
            NewActorYaw + CameraYawOffset,
            0.0f));
    }
}

bool UTwinRouteFollowerComponent::RequestCharacterMovement(
    const FVector& Target,
    const FVector& FacingDirection,
    float DeltaTime)
{
    ACharacter* Character = Cast<ACharacter>(GetOwner());
    UCharacterMovementComponent* Movement = Character
        ? Character->GetCharacterMovement() : nullptr;
    if (!Character || !Movement) return false;

    FVector Direction = Target - Character->GetActorLocation();
    // The route provides plan direction. CharacterMovement owns capsule Z,
    // floor snapping, slopes and StepUp while walking over real collision.
    Direction.Z = 0.0f;
    const FVector RequestedVelocity = Direction.GetSafeNormal2D() * SpeedCmS;
    Movement->RequestDirectMove(RequestedVelocity, false);
    UpdateFacing(FacingDirection, DeltaTime);

    FVector AnimationVelocity = Movement->Velocity;
    if (AnimationVelocity.SizeSquared2D() < FMath::Square(10.0f))
    {
        AnimationVelocity = RequestedVelocity;
    }
    SetRouteAnimationMotion(Character, AnimationVelocity);
    return true;
}

void UTwinRouteFollowerComponent::ResetStallDetection()
{
    NoProgressSeconds = 0.0f;
    if (const AActor* Owner = GetOwner())
    {
        StallReferenceLocation = Owner->GetActorLocation();
        bHasStallReference = true;
    }
    else
    {
        StallReferenceLocation = FVector::ZeroVector;
        bHasStallReference = false;
    }
}

bool UTwinRouteFollowerComponent::HasTimedOutWithoutProgress(float DeltaTime)
{
    const AActor* Owner = GetOwner();
    if (!Owner) return true;
    const FVector Current = Owner->GetActorLocation();
    if (!bHasStallReference
        || FVector::DistSquared(Current, StallReferenceLocation)
            >= FMath::Square(RouteProgressThresholdCm))
    {
        StallReferenceLocation = Current;
        NoProgressSeconds = 0.0f;
        bHasStallReference = true;
        return false;
    }
    NoProgressSeconds += FMath::Max(0.0f, DeltaTime);
    return NoProgressSeconds >= RouteBlockedTimeoutSeconds;
}

void UTwinRouteFollowerComponent::MarkBlocked()
{
    RouteState = ETwinRoamingRouteState::Blocked;
    ResetStallDetection();
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        ClearRouteAnimationMotion(Character);
    }
}

void UTwinRouteFollowerComponent::TickComponent(
    float DeltaTime,
    ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!Route || !Route->Spline || !GetOwner()) return;

    if (RouteState == ETwinRoamingRouteState::Joining)
    {
        const FVector JoinTarget = GetCharacterLocationAtDistance(JoinTargetDistance);
        const FVector Current = GetOwner()->GetActorLocation();
        FVector MotionTarget = JoinTarget;
        if (Route->bSplineAtGroundLevel) MotionTarget.Z = Current.Z;
        if (FVector::Dist2D(Current, MotionTarget) <= RouteArrivalToleranceCm)
        {
            DistanceAlongSpline = JoinTargetDistance;
            RouteState = ETwinRoamingRouteState::AutoRoute;
            ResetStallDetection();
            return;
        }
        if (!RequestCharacterMovement(MotionTarget, JoinTarget - Current, DeltaTime)
            || HasTimedOutWithoutProgress(DeltaTime))
        {
            MarkBlocked();
        }
        return;
    }

    if (RouteState != ETwinRoamingRouteState::AutoRoute) return;
    const float Length = Route->Spline->GetSplineLength();
    if (Length <= UE_SMALL_NUMBER)
    {
        RouteState = ETwinRoamingRouteState::Completed;
        if (ACharacter* Character = Cast<ACharacter>(GetOwner())) ClearRouteAnimationMotion(Character);
        return;
    }

    const FVector Current = GetOwner()->GetActorLocation();
    const float ClosestKey = Route->Spline->FindInputKeyClosestToWorldLocation(Current);
    const float ClosestDistance = Route->Spline->GetDistanceAlongSplineAtSplineInputKey(ClosestKey);
    if (bLoop && Route->Spline->IsClosedLoop())
    {
        DistanceAlongSpline = ClosestDistance;
    }
    else
    {
        DistanceAlongSpline = FMath::Max(DistanceAlongSpline, ClosestDistance);
        const FVector End = GetCharacterLocationAtDistance(Length);
        if (FVector::Dist(Current, End) <= RouteArrivalToleranceCm)
        {
            DistanceAlongSpline = Length;
            RouteState = ETwinRoamingRouteState::Completed;
            if (ACharacter* Character = Cast<ACharacter>(GetOwner())) ClearRouteAnimationMotion(Character);
            return;
        }
    }

    const float SteeringLookAheadCm = FMath::Clamp(
        SpeedCmS * RouteSteeringLookAheadSeconds,
        RouteMinSteeringLookAheadCm,
        RouteMaxSteeringLookAheadCm);
    float TargetDistance = DistanceAlongSpline + SteeringLookAheadCm;
    if (bLoop && Route->Spline->IsClosedLoop())
    {
        TargetDistance = FMath::Fmod(TargetDistance, Length);
    }
    else
    {
        TargetDistance = FMath::Min(TargetDistance, Length);
    }
    const FVector Target = GetCharacterLocationAtDistance(TargetDistance);
    const FVector Tangent = Route->Spline->GetDirectionAtDistanceAlongSpline(
        TargetDistance, ESplineCoordinateSpace::World);
    const float LookAheadCm = FMath::Clamp(
        SpeedCmS * RouteLookAheadSeconds,
        RouteMinLookAheadCm,
        RouteMaxLookAheadCm);
    float FacingDistance = TargetDistance + LookAheadCm;
    if (bLoop && Route->Spline->IsClosedLoop())
    {
        FacingDistance = FMath::Fmod(FacingDistance, FMath::Max(1.0f, Length));
    }
    else
    {
        FacingDistance = FMath::Min(FacingDistance, Length);
    }
    FVector FacingDirection = GetCharacterLocationAtDistance(FacingDistance) - Target;
    if (FacingDirection.IsNearlyZero()) FacingDirection = Tangent;
    if (!RequestCharacterMovement(Target, FacingDirection, DeltaTime)
        || HasTimedOutWithoutProgress(DeltaTime))
    {
        MarkBlocked();
    }
}

FString UTwinRouteFollowerComponent::GetRouteStateText() const
{
    switch (RouteState)
    {
    case ETwinRoamingRouteState::Idle: return TEXT("idle");
    case ETwinRoamingRouteState::AutoRoute: return TEXT("auto_route");
    case ETwinRoamingRouteState::PausedByUser: return TEXT("paused_by_user");
    case ETwinRoamingRouteState::Joining: return TEXT("joining");
    case ETwinRoamingRouteState::Completed: return TEXT("completed");
    case ETwinRoamingRouteState::Blocked: return TEXT("blocked");
    default: return TEXT("unavailable");
    }
}
