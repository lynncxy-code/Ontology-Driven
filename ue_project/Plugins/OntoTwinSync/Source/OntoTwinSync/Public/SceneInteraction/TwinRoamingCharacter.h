#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TwinRoamingCharacter.generated.h"

class UCameraComponent;
class UAnimationAsset;
class USkeletalMeshComponent;
class USpringArmComponent;
class UTwinCharacterAsset;
class UTwinCameraModeComponent;
class UTwinRouteFollowerComponent;
class UTwinSkinComponent;

/** 普通观察者，不是 OntoTwin 业务实例。 */
UCLASS(BlueprintType)
class ONTOTWINSYNC_API ATwinRoamingCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ATwinRoamingCharacter();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming")
    USpringArmComponent* NearCameraArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming")
    UCameraComponent* NearCamera;

    /** Hidden Manny/Quinn source pose for project-side runtime retargeting. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming|Animation")
    USkeletalMeshComponent* AnimationSourceMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming")
    UTwinSkinComponent* SkinComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming")
    UTwinRouteFollowerComponent* RouteFollower;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Roaming")
    UTwinCameraModeComponent* CameraMode;

    bool ApplyCharacterAsset(UTwinCharacterAsset* Asset, FString& OutError);
    void ApplyMovementSettings(const FTwinRoamingMovementSettings& Settings);
    void ApplyNearCameraSettings(const FTwinNearCameraSettings& Settings);
    void MoveRelativeToView(const FVector2D& Input, bool bSprint);
    void Look(const FVector2D& Input, float Sensitivity);
    bool SetAutoRouteAnimation(bool bActive, float SpeedCmS = 0.0f);

private:
    UPROPERTY(Transient)
    UAnimationAsset* AutoRouteAnimation = nullptr;

    UPROPERTY(Transient)
    TSubclassOf<UAnimInstance> AnimationSourceAnimClass;

    float AutoRouteAnimationReferenceSpeedCmS = 180.0f;
    bool bAutoRouteAnimationActive = false;
    float WalkSpeedCmS = 250.0f;
    float SprintSpeedCmS = 500.0f;
};
