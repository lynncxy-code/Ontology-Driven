#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraActor.h"
#include "GameFramework/Pawn.h"
#include "TwinGodViewPawn.generated.h"

class UCameraComponent;
class UFloatingPawnMovement;
class USceneComponent;

/** 关卡预放置的稳定相机锚点；CameraId 决定开局或漫游上帝视角职责。 */
UCLASS(BlueprintType)
class ONTOTWINSYNC_API ATwinGodViewAnchor : public ACameraActor
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="OntoTwin")
    FString CameraId = TEXT("camera.god.default");
};

/** 与人物解耦的自由观察 Pawn；不提供自动定位人物。 */
UCLASS(BlueprintType)
class ONTOTWINSYNC_API ATwinGodViewPawn : public APawn
{
    GENERATED_BODY()

public:
    ATwinGodViewPawn();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Camera")
    USceneComponent* SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Camera")
    UCameraComponent* Camera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Movement")
    UFloatingPawnMovement* Movement;

    void Configure(float InMoveSpeedCmS, float InLookSensitivity);
    void MovePlanar(const FVector2D& Input);
    void MoveVertical(float Input);
    void Look(const FVector2D& Input);
    void AdjustSpeed(float Axis);

private:
    float LookSensitivity = 1.0f;
};
