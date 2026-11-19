#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "IndustrialPresentationComponent.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMeshComponent;
class UMaterialInterface;
class UTextRenderComponent;
class UStaticMesh;

/** Executable example resources. All motion stays on owned indicator components. */
UCLASS()
class ONTOTWININDUSTRIALBEHAVIOR_API UIndustrialPresentationComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UIndustrialPresentationComponent();
    bool Apply(const FString& Channel, const FString& Behavior);
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Motion;
    UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Beacon;
    UPROPERTY(Transient) TObjectPtr<UTextRenderComponent> StatusLabel;
    FString Animation;
    FString Effect;
    FString Visual;
private:
    UStaticMeshComponent* CreateIndicator(FName Name);
    bool UpdateVisual();
    void ClearOverlays();
    // NEW-07: grey / wireframe swap the model materials and restore them afterwards.
    void RestoreSwappedMaterials();
    bool ApplySwappedMaterial(const TCHAR* AssetPath);
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> SwapMaterial;
    FString SwapPath;
    struct FSwappedMesh
    {
        /** The model the originals belong to; a different model must not get them back. */
        TWeakObjectPtr<UStaticMesh> Asset;
        TArray<TWeakObjectPtr<UMaterialInterface>> Originals;
    };
    TMap<TWeakObjectPtr<UMeshComponent>, FSwappedMesh> PreviousMaterials;
    /** Keeps replaced runtime (GLB) materials alive until they are put back. */
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInterface>> HeldOriginals;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Overlay;
    TMap<TWeakObjectPtr<UMeshComponent>, TWeakObjectPtr<UMaterialInterface>> PreviousOverlays;
    float Phase = 0.f;
};
