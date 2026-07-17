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
void ClearRouteAnimationMotion(ACharacter* Character)
{
    if (!Character) return;
    if (ATwinRoamingCharacter* RoamingCharacter = Cast<ATwinRoamingCharacter>(Character))
    {
        RoamingCharacter->SetAutoRouteAnimation(false);
    }
    Character->ConsumeMovementInputVector();
    Character->GetCharacterMovement()->Velocity = FVector::ZeroVector;
}

void SetRouteAnimationMotion(ACharacter* Character, FVector VisualVelocity)
{
    if (!Character) return;
    VisualVelocity.Z = 0.0f;
    if (ATwinRoamingCharacter* RoamingCharacter = Cast<ATwinRoamingCharacter>(Character))
    {
        if (RoamingCharacter->SetAutoRouteAnimation(true, VisualVelocity.Size2D()))
        {
            return;
        }
    }
    Character->GetCharacterMovement()->Velocity = VisualVelocity;
    if (!VisualVelocity.IsNearlyZero())
    {
        // The stock Quinn AnimBP enters locomotion only when it sees both
        // horizontal velocity and acceleration. Route motion is otherwise
        // applied directly to the spline and would leave the pose in Idle.
        Character->AddMovementInput(VisualVelocity.GetSafeNormal2D(), 1.0f, true);
    }
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

    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(TwinRouteJoin), false, Character);
    if (Route) QueryParams.AddIgnoredActor(Route);
    FHitResult VisibilityHit;
    if (World->LineTraceSingleByChannel(VisibilityHit, Start, Target, ECC_Visibility, QueryParams))
    {
        OutError = TEXT("An obstacle blocks the route join path");
        return false;
    }

    const UCapsuleComponent* Capsule = Character->GetCapsuleComponent();
    const FCollisionShape Shape = FCollisionShape::MakeCapsule(
        Capsule->GetScaledCapsuleRadius(), Capsule->GetScaledCapsuleHalfHeight());
    FHitResult SweepHit;
    if (World->SweepSingleByChannel(SweepHit, Start, Target, Character->GetActorQuat(),
        ECC_Pawn, Shape, QueryParams))
    {
        OutError = TEXT("Character capsule cannot safely reach the route");
        return false;
    }
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
    return true;
}

void UTwinRouteFollowerComponent::StopRoute()
{
    RouteState = Route ? ETwinRoamingRouteState::Idle : ETwinRoamingRouteState::Unavailable;
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        ClearRouteAnimationMotion(Character);
    }
}

bool UTwinRouteFollowerComponent::MoveSwept(const FVector& Target, const FVector& FacingDirection)
{
    AActor* Owner = GetOwner();
    if (!Owner) return false;
    FVector ResolvedTarget = Target;
    if (Route && Route->bSplineAtGroundLevel)
    {
        // 4.0 routes are same-floor plans. Let CharacterMovement own floor
        // following instead of competing with it by writing capsule Z each tick.
        ResolvedTarget.Z = Owner->GetActorLocation().Z;
    }
    FHitResult Hit;
    Owner->SetActorLocation(ResolvedTarget, true, &Hit);
    if (!FacingDirection.IsNearlyZero())
    {
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
        const float NewActorYaw = FacingDirection.Rotation().Yaw;
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
    return !Hit.bBlockingHit;
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
        const FVector Next = FMath::VInterpConstantTo(Current, MotionTarget, DeltaTime, SpeedCmS);
        const FVector VisualVelocity = DeltaTime > UE_SMALL_NUMBER
            ? (Next - Current) / DeltaTime : FVector::ZeroVector;
        if (!MoveSwept(Next, JoinTarget - Current))
        {
            RouteState = ETwinRoamingRouteState::Blocked;
            if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
            {
                ClearRouteAnimationMotion(Character);
            }
            return;
        }
        if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
        {
            SetRouteAnimationMotion(Character, VisualVelocity);
        }
        if (Next.Equals(MotionTarget, 2.0f))
        {
            DistanceAlongSpline = JoinTargetDistance;
            RouteState = ETwinRoamingRouteState::AutoRoute;
        }
        return;
    }

    if (RouteState != ETwinRoamingRouteState::AutoRoute) return;
    const float Length = Route->Spline->GetSplineLength();
    float NextDistance = DistanceAlongSpline + SpeedCmS * DeltaTime;
    if (NextDistance >= Length)
    {
        if (bLoop && Route->Spline->IsClosedLoop())
        {
            NextDistance = FMath::Fmod(NextDistance, FMath::Max(1.0f, Length));
        }
        else
        {
            NextDistance = Length;
            RouteState = ETwinRoamingRouteState::Completed;
        }
    }

    const FVector Target = GetCharacterLocationAtDistance(NextDistance);
    const FVector Tangent = Route->Spline->GetDirectionAtDistanceAlongSpline(
        NextDistance, ESplineCoordinateSpace::World);
    const FVector Current = GetOwner()->GetActorLocation();
    const FVector VisualVelocity = DeltaTime > UE_SMALL_NUMBER
        ? (Target - Current) / DeltaTime : FVector::ZeroVector;
    if (!MoveSwept(Target, Tangent))
    {
        RouteState = ETwinRoamingRouteState::Blocked;
        if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
        {
            ClearRouteAnimationMotion(Character);
        }
        return;
    }
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        SetRouteAnimationMotion(Character, VisualVelocity);
    }
    DistanceAlongSpline = NextDistance;
    if (RouteState == ETwinRoamingRouteState::Completed)
    {
        if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
        {
            ClearRouteAnimationMotion(Character);
        }
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
