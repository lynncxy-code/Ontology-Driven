#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TwinRouteFollowerComponent.generated.h"

class ATwinRoamingRoute;

/** Spline 展示路线执行器。不会绕障；归线时只做距离、视线和胶囊扫掠。 */
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

    bool IsSafeJoin(const FVector& Target, FString& OutError) const;
    bool MoveSwept(const FVector& Target, const FVector& FacingDirection);
    float FindClosestDistanceOnSpline(const FVector& WorldLocation) const;
    FVector GetCharacterLocationAtDistance(float Distance) const;
};
