#include "SceneInteraction/TwinGodViewPawn.h"

#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "GameFramework/FloatingPawnMovement.h"

ATwinGodViewPawn::ATwinGodViewPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    RootComponent = SceneRoot;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(SceneRoot);
    Movement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("Movement"));
    Movement->MaxSpeed = 1800.0f;
    Movement->Acceleration = 5000.0f;
    Movement->Deceleration = 6000.0f;
}

void ATwinGodViewPawn::Configure(float InMoveSpeedCmS, float InLookSensitivity)
{
    Movement->MaxSpeed = FMath::Clamp(InMoveSpeedCmS, 100.0f, 10000.0f);
    LookSensitivity = FMath::Clamp(InLookSensitivity, 0.1f, 5.0f);
}

void ATwinGodViewPawn::MovePlanar(const FVector2D& Input)
{
    const FRotator YawRotation(0.0f, GetActorRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Input.Y);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Input.X);
}

void ATwinGodViewPawn::MoveVertical(float Input)
{
    AddMovementInput(FVector::UpVector, Input);
}

void ATwinGodViewPawn::Look(const FVector2D& Input)
{
    FRotator Rotation = GetActorRotation();
    Rotation.Yaw += Input.X * LookSensitivity;
    Rotation.Pitch = FMath::Clamp(Rotation.Pitch - Input.Y * LookSensitivity, -89.0f, 89.0f);
    SetActorRotation(Rotation);
}

void ATwinGodViewPawn::AdjustSpeed(float Axis)
{
    if (FMath::IsNearlyZero(Axis)) return;
    Movement->MaxSpeed = FMath::Clamp(Movement->MaxSpeed * (Axis > 0.0f ? 1.2f : 0.8f), 100.0f, 10000.0f);
}
