#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OntoTwinRuntimeGizmo.generated.h"

class UPrimitiveComponent;
class USceneComponent;
class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;

UENUM(BlueprintType)
enum class EOntoTwinRuntimeGizmoPart : uint8
{
    None,
    MoveXY,
    MoveZ,
    RotateYaw
};

UENUM(BlueprintType)
enum class EOntoTwinRuntimeSnapState : uint8
{
    None,
    Grid,
    Wall
};

UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="OntoTwin Runtime Gizmo"))
class ONTOTWINSYNC_API AOntoTwinRuntimeGizmo : public AActor
{
    GENERATED_BODY()

public:
    AOntoTwinRuntimeGizmo();

protected:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

public:
    void UpdateForTarget(AActor* TargetActor);
    void SetGizmoEnabled(bool bEnabled);
    void SetInteractionState(EOntoTwinRuntimeGizmoPart HoverPart, EOntoTwinRuntimeGizmoPart ActivePart);
    void SetSnapFeedback(EOntoTwinRuntimeSnapState SnapState, const FVector& WorldPoint);
    EOntoTwinRuntimeGizmoPart GetPartForComponent(const UPrimitiveComponent* Component) const;
    float GetMoveInteractionPlaneZ() const;
    float GetRotateInteractionPlaneZ() const;

private:
    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    USceneComponent* GizmoRoot = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* MoveHitPlane = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* RotateHitHandle = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    TArray<UStaticMeshComponent*> RotateHitSegments;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    TArray<UStaticMeshComponent*> MoveVisuals;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    TArray<UStaticMeshComponent*> MoveArrowVisuals;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* ZAxisHit = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* ZAxisShaftVisual = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* ZAxisArrowVisual = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    TArray<UStaticMeshComponent*> RotateRingVisuals;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* RotateHandleVisual = nullptr;

    UPROPERTY(VisibleAnywhere, Category="Runtime Editor")
    UStaticMeshComponent* SnapMarker = nullptr;

    UPROPERTY()
    UMaterialInterface* BaseGizmoMaterial = nullptr;

    UPROPERTY(Transient)
    UMaterialInstanceDynamic* MoveMaterial = nullptr;

    UPROPERTY(Transient)
    UMaterialInstanceDynamic* RotateMaterial = nullptr;

    UPROPERTY(Transient)
    UMaterialInstanceDynamic* ZMaterial = nullptr;

    UPROPERTY(Transient)
    UMaterialInstanceDynamic* SnapMaterial = nullptr;

    bool bGizmoEnabled = false;
    EOntoTwinRuntimeGizmoPart CurrentHoverPart = EOntoTwinRuntimeGizmoPart::None;
    EOntoTwinRuntimeGizmoPart CurrentActivePart = EOntoTwinRuntimeGizmoPart::None;
    EOntoTwinRuntimeSnapState CurrentSnapState = EOntoTwinRuntimeSnapState::None;
    FBox TargetBounds = FBox(ForceInit);

    static constexpr float RingRadius = 70.0f;
    static constexpr float BaseGizmoDiameter = 140.0f;
    static constexpr float TargetScreenDiameterPx = 120.0f;

    void ConfigureHitPart(UStaticMeshComponent* Component);
    void ConfigureVisualPart(UStaticMeshComponent* Component);
    void CreateRuntimeMaterials();
    void ApplyInteractionColors();
    void UpdateScreenScale();
    void UpdateComponentLayout();
    void DrawSelectionFootprint() const;
};
