#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Subsystems/WorldSubsystem.h"
#include "DeviceEffectsComponent.generated.h"

class UDeviceEffectsComponent;
class UNiagaraComponent;
class UPostProcessComponent;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class UStaticMeshComponent;
class FJsonObject;

/** One scan owns the shared material parameters in each world, including across PIE worlds. */
UCLASS()
class UDeviceScanQueue : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    void Enter(UDeviceEffectsComponent* Request);
    void Leave(UDeviceEffectsComponent* Request);
    void Refresh();
private:
    TArray<TWeakObjectPtr<UDeviceEffectsComponent>> Requests;
    TWeakObjectPtr<UDeviceEffectsComponent> Active;
};

UCLASS()
class UDeviceEffectsComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UDeviceEffectsComponent();
    bool StartScan(const TSharedPtr<FJsonObject>& Params);
    bool StartHighlight(const TSharedPtr<FJsonObject>& Params);
    void StopScan();
    void StopHighlight();
    bool CanDisplayScan() const { return bScanRequested && (Wait <= 0.f || bHold); }
    void SetScanVisible(bool bVisible);
    virtual void TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Fn) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    void DrawScan();
    void AttachOverlay();
    void UpdateTick();
    UPROPERTY(Transient) TObjectPtr<UNiagaraComponent> Grid;
    UPROPERTY(Transient) TObjectPtr<UPostProcessComponent> Filter;
    UPROPERTY(Transient) TObjectPtr<UMaterialParameterCollection> Collection;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Floor;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Tint;
    UPROPERTY(Transient) TMap<UStaticMeshComponent*, UMaterialInterface*> Originals;
    TMap<FName,float> SavedScalars;
    FLinearColor SavedOrigin;
    bool bSavedOrigin=false;
    FVector Origin = FVector::ZeroVector;
    FLinearColor TintColor = FLinearColor::White;
    float Radius=850, Sweep=4, Elapsed=0, Interval=0, Wait=0;
    float TintDuration=0, TintAge=0, MeshPoll=0;
    bool bScanRequested=false, bVisible=false, bHold=false, bGreen=false, bBreathing=false;
};
