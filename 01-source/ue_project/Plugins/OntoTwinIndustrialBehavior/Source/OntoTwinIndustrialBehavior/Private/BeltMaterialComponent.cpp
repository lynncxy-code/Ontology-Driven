#include "BeltMaterialComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "GameFramework/Actor.h"

static FString OTMatName(const UMaterialInterface* M) { return M ? M->GetPathName() : FString(TEXT("(默认)")); }

UBeltMaterialComponent::UBeltMaterialComponent() { PrimaryComponentTick.bCanEverTick = true; }
bool UBeltMaterialComponent::Apply(const TSharedPtr<FJsonObject>& Params)
{
    ResetMaterials();
    Speed = .5;
    FString Target = TEXT("model");
    if (Params)
    {
        if (Params->HasField(TEXT("speed")) && !Params->TryGetNumberField(TEXT("speed"), Speed)) return false;
        if (Params->HasField(TEXT("target")) && !Params->TryGetStringField(TEXT("target"), Target)) return false;
    }
    if (!FMath::IsFinite(Speed) || FMath::Abs(Speed) > 5 || (Target != TEXT("model") && Target != TEXT("tagged"))) return false;
    auto* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/OntoTwinIndustrialBehavior/Materials/M_BeltScroll.M_BeltScroll"));
    if (!Base) return false;
    Material = UMaterialInstanceDynamic::Create(Base, this);
    bActive = true;
    bTaggedOnly = Target == TEXT("tagged");
    Offset = 0;
    Material->SetScalarParameterValue(TEXT("Offset"), 0);
    UE_LOG(LogTemp, Log, TEXT("[OT-Material] %s 启用皮带条纹 target=%s speed=%.2f"), *GetOwner()->GetName(), *Target, Speed);
    FindMeshes();
    return true;
}
void UBeltMaterialComponent::FindMeshes()
{
    TArray<UStaticMeshComponent*> Meshes;
    GetOwner()->GetComponents<UStaticMeshComponent>(Meshes, true);
    for (auto* Mesh : Meshes)
    {
        if (!Mesh || !Mesh->GetStaticMesh() || Mesh->ComponentHasTag(TEXT("OntoTwinPresentation"))
            || (bTaggedOnly && !Mesh->ComponentHasTag(TEXT("OntoTwinBeltTarget")))) continue;
        for (int32 I = 0; I < Mesh->GetNumMaterials(); ++I)
        {
            if (Slots.ContainsByPredicate([Mesh,I](const FSlot& S){ return S.Mesh == Mesh && S.Index == I; })) continue;
            Slots.Add({Mesh, I, Mesh->GetMaterial(I)});
            HeldOriginals.Add(Mesh->GetMaterial(I));
            UE_LOG(LogTemp, Log, TEXT("[OT-Material] %s 换上皮带条纹：%s 槽%d 模型=%s（原 %s）"), *GetOwner()->GetName(),
                *Mesh->GetName(), I, *GetNameSafe(Mesh->GetStaticMesh()), *OTMatName(Mesh->GetMaterial(I)));
            Mesh->SetMaterial(I, Material);
        }
    }
}
void UBeltMaterialComponent::TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta, Type, Function);
    if (!bActive || !Material) return;
    FindMeshes();
    Offset = FMath::Fmod(Offset + FMath::Max(0.f,Delta) * Speed, 1.0);
    Material->SetScalarParameterValue(TEXT("Offset"), Offset);
}
void UBeltMaterialComponent::ResetMaterials()
{
    bActive = false;
    for (auto& Slot : Slots)
        if (Slot.Mesh.IsValid() && Slot.Mesh->GetMaterial(Slot.Index) == Material)
        {
            Slot.Mesh->SetMaterial(Slot.Index, Slot.Original.Get());
            UE_LOG(LogTemp, Log, TEXT("[OT-Material] %s 撤下皮带条纹：%s 槽%d -> %s"), *GetOwner()->GetName(),
                *Slot.Mesh->GetName(), Slot.Index, *OTMatName(Slot.Mesh->GetMaterial(Slot.Index)));
        }
    Slots.Reset();
    HeldOriginals.Reset();
}
void UBeltMaterialComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    ResetMaterials();
    Super::EndPlay(Reason);
}
