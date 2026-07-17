#include "SceneInteraction/TwinRoamingCharacter.h"

#include "SceneInteraction/TwinRouteFollowerComponent.h"
#include "SceneInteraction/TwinCameraModeComponent.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "SceneInteraction/TwinSkinComponent.h"
#include "Camera/CameraComponent.h"
#include "Animation/AnimationAsset.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/SpringArmComponent.h"

ATwinRoamingCharacter::ATwinRoamingCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = false;
    bUseControllerRotationRoll = false;

    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->bRunPhysicsWithNoController = true;
    GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);

    AnimationSourceMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("AnimationSourceMesh"));
    AnimationSourceMesh->SetupAttachment(GetCapsuleComponent());
    AnimationSourceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    AnimationSourceMesh->SetHiddenInGame(true);
    AnimationSourceMesh->SetCastShadow(false);
    AnimationSourceMesh->VisibilityBasedAnimTickOption =
        EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    GetMesh()->SetupAttachment(AnimationSourceMesh);

    NearCameraArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("NearCameraArm"));
    NearCameraArm->SetupAttachment(GetCapsuleComponent());
    NearCameraArm->TargetArmLength = 120.0f;
    NearCameraArm->SocketOffset = FVector(0.0f, 0.0f, 35.0f);
    NearCameraArm->bUsePawnControlRotation = true;
    NearCameraArm->bEnableCameraLag = true;
    NearCameraArm->CameraLagSpeed = 12.0f;

    NearCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("NearCamera"));
    NearCamera->SetupAttachment(NearCameraArm, USpringArmComponent::SocketName);
    NearCamera->bUsePawnControlRotation = false;

    SkinComponent = CreateDefaultSubobject<UTwinSkinComponent>(TEXT("SkinComponent"));
    RouteFollower = CreateDefaultSubobject<UTwinRouteFollowerComponent>(TEXT("RouteFollower"));
    RouteFollower->PrimaryComponentTick.TickGroup = TG_PrePhysics;
    RouteFollower->AddTickPrerequisiteComponent(GetCharacterMovement());
    AnimationSourceMesh->AddTickPrerequisiteComponent(RouteFollower);
    GetMesh()->AddTickPrerequisiteComponent(AnimationSourceMesh);
    CameraMode = CreateDefaultSubobject<UTwinCameraModeComponent>(TEXT("CameraMode"));
}

bool ATwinRoamingCharacter::ApplyCharacterAsset(UTwinCharacterAsset* Asset, FString& OutError)
{
    if (!Asset)
    {
        OutError = TEXT("Character Primary Data Asset is missing");
        return false;
    }
    USkeletalMesh* BaseMesh = Asset->BaseMesh.LoadSynchronous();
    if (!BaseMesh)
    {
        OutError = TEXT("Base character Skeletal Mesh cannot be loaded");
        return false;
    }

    GetCapsuleComponent()->SetCapsuleSize(Asset->CapsuleRadiusCm, Asset->CapsuleHalfHeightCm);
    GetMesh()->SetRelativeLocationAndRotation(
        Asset->MeshOffsetCm,
        FRotator(0.0f, Asset->MeshYawOffsetDeg, 0.0f));
    GetMesh()->SetSkeletalMesh(BaseMesh);
    if (UClass* AnimClass = Asset->AnimInstanceClass.LoadSynchronous())
    {
        GetMesh()->SetAnimInstanceClass(AnimClass);
    }

    USkeletalMesh* SourceMesh = Asset->AnimationSourceMesh.LoadSynchronous();
    UClass* SourceAnimClass = Asset->AnimationSourceAnimInstanceClass.LoadSynchronous();
    if (SourceMesh || SourceAnimClass)
    {
        if (!SourceMesh || !SourceAnimClass)
        {
            OutError = TEXT("Animation source mesh and Anim Blueprint must be configured together");
            return false;
        }
        AnimationSourceMesh->SetSkeletalMesh(SourceMesh);
        AnimationSourceMesh->SetAnimInstanceClass(SourceAnimClass);
        AnimationSourceAnimClass = SourceAnimClass;
        UE_LOG(LogTemp, Log, TEXT("OntoTwin locomotion source configured: mesh=%s anim=%s"),
            *SourceMesh->GetPathName(), *SourceAnimClass->GetPathName());
    }
    AutoRouteAnimation = Asset->AutoRouteAnimation.LoadSynchronous();
    AutoRouteAnimationReferenceSpeedCmS = FMath::Max(
        1.0f, Asset->AutoRouteAnimationReferenceSpeedCmS);
    return true;
}

void ATwinRoamingCharacter::ApplyMovementSettings(const FTwinRoamingMovementSettings& Settings)
{
    WalkSpeedCmS = Settings.WalkSpeedCmS;
    SprintSpeedCmS = Settings.SprintSpeedCmS;
    GetCharacterMovement()->MaxWalkSpeed = WalkSpeedCmS;
    const float Gravity = FMath::Abs(GetCharacterMovement()->GetGravityZ());
    GetCharacterMovement()->JumpZVelocity = FMath::Sqrt(FMath::Max(0.0f, 2.0f * Gravity * Settings.JumpHeightCm));
    RouteFollower->SetSpeed(Settings.AutoRouteSpeedCmS);
}

void ATwinRoamingCharacter::ApplyNearCameraSettings(const FTwinNearCameraSettings& Settings)
{
    NearCameraArm->TargetArmLength = Settings.DistanceCm;
    NearCameraArm->TargetOffset.Z = Settings.HeightCm;
    NearCameraArm->SocketOffset.Z = 0.0f;
}

void ATwinRoamingCharacter::MoveRelativeToView(const FVector2D& Input, bool bSprint)
{
    if (!Controller || Input.IsNearlyZero()) return;
    GetCharacterMovement()->MaxWalkSpeed = bSprint ? SprintSpeedCmS : WalkSpeedCmS;
    const FRotator ControlRotation = Controller->GetControlRotation();
    const FRotator YawRotation(0.0f, ControlRotation.Yaw, 0.0f);
    const FVector Forward = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
    const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
    AddMovementInput(Forward, Input.Y);
    AddMovementInput(Right, Input.X);
}

void ATwinRoamingCharacter::Look(const FVector2D& Input, float Sensitivity)
{
    AddControllerYawInput(Input.X * Sensitivity);
    AddControllerPitchInput(-Input.Y * Sensitivity);
}

bool ATwinRoamingCharacter::SetAutoRouteAnimation(bool bActive, float SpeedCmS)
{
    if (!AnimationSourceMesh || !AutoRouteAnimation || !AnimationSourceAnimClass)
    {
        return false;
    }
    if (bActive)
    {
        if (!bAutoRouteAnimationActive)
        {
            AnimationSourceMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
            AnimationSourceMesh->SetAnimation(AutoRouteAnimation);
            AnimationSourceMesh->Play(true);
            bAutoRouteAnimationActive = true;
        }
        AnimationSourceMesh->SetPlayRate(FMath::Clamp(
            SpeedCmS / AutoRouteAnimationReferenceSpeedCmS, 0.25f, 3.0f));
    }
    else if (bAutoRouteAnimationActive)
    {
        AnimationSourceMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        AnimationSourceMesh->SetAnimInstanceClass(AnimationSourceAnimClass);
        bAutoRouteAnimationActive = false;
    }
    return true;
}
