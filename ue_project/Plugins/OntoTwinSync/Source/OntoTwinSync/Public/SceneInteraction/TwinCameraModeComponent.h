#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TimerManager.h"
#include "TwinCameraModeComponent.generated.h"

class APlayerController;
class ATwinGodViewAnchor;
class ATwinGodViewPawn;

/** 第一人称、过肩人物相机与独立全局视角 Pawn 的 possession 切换。 */
UCLASS(ClassGroup=(OntoTwin), meta=(BlueprintSpawnableComponent))
class ONTOTWINSYNC_API UTwinCameraModeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTwinCameraModeComponent();

    void Configure(
        const FTwinFirstPersonCameraSettings& InFirstPerson,
        const FTwinNearCameraSettings& InNear,
        const FTwinGodCameraSettings& InGod);
    bool ActivateMode(
        ETwinRoamingCameraMode NewMode,
        APlayerController* PlayerController,
        ATwinGodViewAnchor* StartAnchor,
        FString& OutError,
        bool bInstant = false);
    bool ActivateNear(APlayerController* PlayerController, bool bInstant = true);
    bool ActivateFirstPerson(APlayerController* PlayerController, bool bInstant = true);
    bool ActivateGod(
        APlayerController* PlayerController,
        ATwinGodViewAnchor* StartAnchor,
        FString& OutError,
        bool bInstant = true);
    bool Cycle(APlayerController* PlayerController, ATwinGodViewAnchor* StartAnchor, FString& OutError);
    void Shutdown(APlayerController* PlayerController);

    ETwinRoamingCameraMode GetMode() const { return Mode; }
    ATwinGodViewPawn* GetGodPawn() const { return GodPawn; }
    bool IsTransitioning() const;

private:
    FTwinFirstPersonCameraSettings FirstPersonSettings;
    FTwinNearCameraSettings NearSettings;
    FTwinGodCameraSettings GodSettings;
    ETwinRoamingCameraMode Mode = ETwinRoamingCameraMode::NearFollow;
    ETwinRoamingCameraMode PendingMode = ETwinRoamingCameraMode::NearFollow;
    bool bViewTargetTransitioning = false;

    UPROPERTY()
    APlayerController* TransitionController = nullptr;

    UPROPERTY()
    ATwinGodViewPawn* GodPawn = nullptr;

    FTimerHandle TransitionTimer;
    bool EnsureGodPawn(ATwinGodViewAnchor* StartAnchor, FString& OutError);
    void FinishViewTargetTransition();
    void ApplyPersonControlRotation(APlayerController* PlayerController, ETwinRoamingCameraMode PersonMode);
};
