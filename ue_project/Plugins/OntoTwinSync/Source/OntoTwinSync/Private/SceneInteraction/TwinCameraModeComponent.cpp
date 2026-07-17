#include "SceneInteraction/TwinCameraModeComponent.h"

#include "SceneInteraction/TwinGodViewPawn.h"
#include "SceneInteraction/TwinRoamingCharacter.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

UTwinCameraModeComponent::UTwinCameraModeComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UTwinCameraModeComponent::Configure(
    const FTwinNearCameraSettings& InNear,
    const FTwinGodCameraSettings& InGod)
{
    NearSettings = InNear;
    GodSettings = InGod;
    if (ATwinRoamingCharacter* Character = Cast<ATwinRoamingCharacter>(GetOwner()))
    {
        Character->ApplyNearCameraSettings(NearSettings);
    }
    if (GodPawn)
    {
        GodPawn->Configure(GodSettings.MoveSpeedCmS, GodSettings.LookSensitivity);
    }
}

bool UTwinCameraModeComponent::ActivateNear(APlayerController* PlayerController)
{
    ATwinRoamingCharacter* Character = Cast<ATwinRoamingCharacter>(GetOwner());
    if (!PlayerController || !Character) return false;
    PlayerController->Possess(Character);
    PlayerController->SetControlRotation(FRotator(
        -10.0f,
        Character->GetActorRotation().Yaw,
        0.0f));
    Mode = ETwinRoamingCameraMode::NearFollow;
    return true;
}

bool UTwinCameraModeComponent::ActivateGod(
    APlayerController* PlayerController,
    ATwinGodViewAnchor* StartAnchor,
    FString& OutError)
{
    if (!PlayerController || !GetWorld())
    {
        OutError = TEXT("Player controller is unavailable");
        return false;
    }
    if (!GodPawn)
    {
        if (!StartAnchor)
        {
            OutError = TEXT("Configured god-view CameraActor was not found");
            return false;
        }
        FActorSpawnParameters Params;
        Params.Owner = GetOwner();
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        GodPawn = GetWorld()->SpawnActor<ATwinGodViewPawn>(
            ATwinGodViewPawn::StaticClass(), StartAnchor->GetActorTransform(), Params);
        if (!GodPawn)
        {
            OutError = TEXT("God-view Pawn could not be spawned");
            return false;
        }
    }
    GodPawn->Configure(GodSettings.MoveSpeedCmS, GodSettings.LookSensitivity);
    PlayerController->Possess(GodPawn);
    Mode = ETwinRoamingCameraMode::God;
    return true;
}

bool UTwinCameraModeComponent::Toggle(
    APlayerController* PlayerController,
    ATwinGodViewAnchor* StartAnchor,
    FString& OutError)
{
    return Mode == ETwinRoamingCameraMode::NearFollow
        ? ActivateGod(PlayerController, StartAnchor, OutError)
        : ActivateNear(PlayerController);
}

void UTwinCameraModeComponent::Shutdown(APlayerController* PlayerController)
{
    if (PlayerController && PlayerController->GetPawn() == GodPawn)
    {
        PlayerController->UnPossess();
    }
    if (GodPawn && IsValid(GodPawn))
    {
        GodPawn->Destroy();
    }
    GodPawn = nullptr;
    Mode = ETwinRoamingCameraMode::NearFollow;
}
