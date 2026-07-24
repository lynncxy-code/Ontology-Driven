#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TwinRouteFollowerComponent.generated.h"

class ATwinRoamingRoute;

/** Spline 路线导向器。实际行走由 CharacterMovement 执行，因此保留走楼梯/斜坡能力。 */
UCLASS(ClassGroup=(OntoTwin), meta=(BlueprintSpawnableComponent))
class ONTOTWINSYNC_API UTwinRouteFollowerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTwinRouteFollowerComponent();

    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    void Configure(ATwinRoamingRoute* InRoute, float InSpeedCmS, bool bInLoop, bool bAutoStart);
    void SetSpeed(float InSpeedCmS);
    void SetLoop(bool bInLoop);
    void PauseByUser();
    bool TryStartFromSpawn(FString& OutError);
    bool TryResume(FString& OutError);
    bool RestartFromBeginning(FString& OutError);
    void StopRoute();

    ETwinRoamingRouteState GetRouteState() const { return RouteState; }
    FString GetRouteStateText() const;
    bool IsFollowing() const { return RouteState == ETwinRoamingRouteState::AutoRoute; }

private:
    UPROPERTY()
    ATwinRoamingRoute* Route = nullptr;

    float SpeedCmS = 180.0f;
    float DistanceAlongSpline = 0.0f;
    float JoinTargetDistance = 0.0f;
    bool bLoop = false;
    ETwinRoamingRouteState RouteState = ETwinRoamingRouteState::Unavailable;

    FVector StallReferenceLocation = FVector::ZeroVector;
    float NoProgressSeconds = 0.0f;
    bool bHasStallReference = false;

    bool IsSafeJoin(const FVector& Target, FString& OutError) const;
    bool RequestCharacterMovement(
        const FVector& Target,
        const FVector& FacingDirection,
        float DeltaTime);
    void UpdateFacing(const FVector& FacingDirection, float DeltaTime);
    void ResetStallDetection();
    bool HasTimedOutWithoutProgress(float DeltaTime);
    void MarkBlocked();
    float FindClosestDistanceOnSpline(const FVector& WorldLocation) const;
    FVector GetCharacterLocationAtDistance(float Distance) const;
};
