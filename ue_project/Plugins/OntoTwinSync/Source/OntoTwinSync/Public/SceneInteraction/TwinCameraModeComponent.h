#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TwinCameraModeComponent.generated.h"

class APlayerController;
class ATwinGodViewAnchor;
class ATwinGodViewPawn;

/** 近身人物与独立上帝视角 Pawn 的 possession 切换。 */
UCLASS(ClassGroup=(OntoTwin), meta=(BlueprintSpawnableComponent))
class ONTOTWINSYNC_API UTwinCameraModeComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTwinCameraModeComponent();

    void Configure(const FTwinNearCameraSettings& InNear, const FTwinGodCameraSettings& InGod);
    bool ActivateNear(APlayerController* PlayerController);
    bool ActivateGod(APlayerController* PlayerController, ATwinGodViewAnchor* StartAnchor, FString& OutError);
    bool Toggle(APlayerController* PlayerController, ATwinGodViewAnchor* StartAnchor, FString& OutError);
    void Shutdown(APlayerController* PlayerController);

    ETwinRoamingCameraMode GetMode() const { return Mode; }
    ATwinGodViewPawn* GetGodPawn() const { return GodPawn; }

private:
    FTwinNearCameraSettings NearSettings;
    FTwinGodCameraSettings GodSettings;
    ETwinRoamingCameraMode Mode = ETwinRoamingCameraMode::NearFollow;

    UPROPERTY()
    ATwinGodViewPawn* GodPawn = nullptr;
};
