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
    NearCameraArm->bEnableCameraRotationLag = false;
    NearCameraArm->CameraRotationLagSpeed = 7.0f;
    NearCameraArm->bUseCameraLagSubstepping = true;

    NearCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("NearCamera"));
    NearCamera->SetupAttachment(NearCameraArm, USpringArmComponent::SocketName);
    NearCamera->bUsePawnControlRotation = false;

    SkinComponent = CreateDefaultSubobject<UTwinSkinComponent>(TEXT("SkinComponent"));
    RouteFollower = CreateDefaultSubobject<UTwinRouteFollowerComponent>(TEXT("RouteFollower"));
    RouteFollower->PrimaryComponentTick.TickGroup = TG_PrePhysics;
    // Feed spline steering into CharacterMovement before its physics tick so
    // automatic routes use the same floor following and StepUp code as WASD.
    GetCharacterMovement()->AddTickPrerequisiteComponent(RouteFollower);
    AnimationSourceMesh->AddTickPrerequisiteComponent(RouteFollower);
    GetMesh()->AddTickPrerequisiteComponent(AnimationSourceMesh);
    CameraMode = CreateDefaultSubobject<UTwinCameraModeComponent>(TEXT("CameraMode"));
}

void ATwinRoamingCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bPersonCameraTransitioning || !NearCameraArm || !NearCamera) return;

    PersonCameraTransitionElapsed += DeltaSeconds;
    const float Alpha = FMath::Clamp(
        PersonCameraTransitionElapsed / FMath::Max(PersonCameraTransitionDuration, KINDA_SMALL_NUMBER),
        0.0f,
        1.0f);
    const float SmoothedAlpha = FMath::SmoothStep(0.0f, 1.0f, Alpha);
    NearCameraArm->TargetArmLength = FMath::Lerp(
        PersonCameraStartArmLength, PersonCameraTargetArmLength, SmoothedAlpha);
    NearCameraArm->TargetOffset.Z = FMath::Lerp(
        PersonCameraStartHeight, PersonCameraTargetHeight, SmoothedAlpha);
    NearCamera->SetFieldOfView(FMath::Lerp(
        PersonCameraStartFov, PersonCameraTargetFov, SmoothedAlpha));

    if (Alpha >= 1.0f)
    {
        bPersonCameraTransitioning = false;
        SetFirstPersonPresentation(TargetPersonCameraMode == ETwinRoamingCameraMode::FirstPerson);
    }
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
    NearCameraSettings = Settings;
    if (TargetPersonCameraMode != ETwinRoamingCameraMode::FirstPerson
        && !bPersonCameraTransitioning)
    {
        NearCameraArm->TargetArmLength = Settings.DistanceCm;
        NearCameraArm->TargetOffset.Z = Settings.HeightCm;
        NearCameraArm->SocketOffset.Z = 0.0f;
    }
}

void ATwinRoamingCharacter::ConfigurePersonCameras(
    const FTwinFirstPersonCameraSettings& FirstPersonSettings,
    const FTwinNearCameraSettings& NearSettings)
{
    FirstPersonCameraSettings = FirstPersonSettings;
    NearCameraSettings = NearSettings;
    if (!bPersonCameraTransitioning)
    {
        ActivatePersonCamera(TargetPersonCameraMode, 0.0f);
    }
}

void ATwinRoamingCharacter::ActivatePersonCamera(
    ETwinRoamingCameraMode Mode,
    float BlendDurationSeconds)
{
    if (!NearCameraArm || !NearCamera || Mode == ETwinRoamingCameraMode::God) return;

    TargetPersonCameraMode = Mode;
    PersonCameraStartArmLength = NearCameraArm->TargetArmLength;
    PersonCameraStartHeight = NearCameraArm->TargetOffset.Z;
    PersonCameraStartFov = NearCamera->FieldOfView;
    if (Mode == ETwinRoamingCameraMode::FirstPerson)
    {
        const float CapsuleHalfHeight = GetCapsuleComponent()
            ? GetCapsuleComponent()->GetScaledCapsuleHalfHeight()
            : 88.0f;
        PersonCameraTargetArmLength = 0.0f;
        PersonCameraTargetHeight = FirstPersonCameraSettings.EyeHeightCm - CapsuleHalfHeight;
        PersonCameraTargetFov = FirstPersonCameraSettings.FovDeg;
        // Hide before the camera crosses the body on the way into first person.
        SetFirstPersonPresentation(true);
    }
    else
    {
        PersonCameraTargetArmLength = NearCameraSettings.DistanceCm;
        PersonCameraTargetHeight = NearCameraSettings.HeightCm;
        PersonCameraTargetFov = 90.0f;
    }
    NearCameraArm->SocketOffset.Z = 0.0f;

    PersonCameraTransitionDuration = FMath::Max(0.0f, BlendDurationSeconds);
    PersonCameraTransitionElapsed = 0.0f;
    bPersonCameraTransitioning = PersonCameraTransitionDuration > KINDA_SMALL_NUMBER;
    if (!bPersonCameraTransitioning)
    {
        NearCameraArm->TargetArmLength = PersonCameraTargetArmLength;
        NearCameraArm->TargetOffset.Z = PersonCameraTargetHeight;
        NearCamera->SetFieldOfView(PersonCameraTargetFov);
        SetFirstPersonPresentation(Mode == ETwinRoamingCameraMode::FirstPerson);
    }
}

void ATwinRoamingCharacter::SetFirstPersonPresentation(bool bEnabled)
{
    if (USkeletalMeshComponent* VisibleMesh = GetMesh())
    {
        VisibleMesh->SetOwnerNoSee(bEnabled);
        VisibleMesh->SetCastHiddenShadow(bEnabled);
    }
    const bool bRouteOwnsMovement = RouteFollower && RouteFollower->IsFollowing();
    bUseControllerRotationYaw = bEnabled && !bRouteOwnsMovement;
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->bOrientRotationToMovement = !bEnabled && !bRouteOwnsMovement;
    }
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

void ATwinRoamingCharacter::SetAutoRouteCameraSmoothing(bool bEnabled)
{
    if (NearCameraArm)
    {
        // Automatic routes benefit from rotation damping, while manual
        // takeover should keep mouse look immediate and predictable.
        NearCameraArm->bEnableCameraRotationLag = bEnabled;
    }
    const bool bFirstPerson = TargetPersonCameraMode == ETwinRoamingCameraMode::FirstPerson;
    bUseControllerRotationYaw = bFirstPerson && !bEnabled;
    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->bOrientRotationToMovement = !bFirstPerson && !bEnabled;
    }
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
