#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OntoTwinRuntimeGizmo.generated.h"

class UPrimitiveComponent;
class USceneComponent;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EOntoTwinRuntimeGizmoPart : uint8
{
    None,
    MoveXY,
    RotateYaw
};

UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="OntoTwin Runtime Gizmo"))
class ONTOTWINSYNC_API AOntoTwinRuntimeGizmo : public AActor
{
    GENERATED_BODY()

public:
    AOntoTwinRuntimeGizmo();

protected:
    virtual void Tick(float DeltaSeconds) override;

public:
    void UpdateForTarget(AActor* TargetActor);
    void SetGizmoEnabled(bool bEnabled);
    EOntoTwinRuntimeGizmoPart GetPartForComponent(const UPrimitiveComponent* Component) const;

private:
    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    USceneComponent* GizmoRoot = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* MovePlane = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* RotateHandle = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* ForwardArrow = nullptr;

    bool bGizmoEnabled = false;
    FVector2D MovePlaneHalfSize = FVector2D(80.f, 80.f);
    float RotateRadius = 160.f;
    float ForwardArrowLength = 140.f;

    void ConfigurePart(UStaticMeshComponent* Component, bool bEnableCollision);
    void DrawRuntimeVisuals() const;
};
