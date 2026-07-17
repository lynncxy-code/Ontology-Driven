#include "SceneInteraction/TwinSkinComponent.h"

#include "SceneInteraction/TwinRoamingTypes.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/AssetManager.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Character.h"
#include "Materials/MaterialInterface.h"

UTwinSkinComponent::UTwinSkinComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UTwinSkinComponent::Configure(
    const TMap<FString, FString>& InSkinPrimaryAssetIds,
    const FString& InDefaultSkinId)
{
    SkinPrimaryAssetIds = InSkinPrimaryAssetIds;
    DefaultSkinId = InDefaultSkinId;
    AllowedSkinIds.Reset();
    SkinPrimaryAssetIds.GetKeys(AllowedSkinIds);
    AllowedSkinIds.Sort();

    if (!ActiveSkinId.IsEmpty() && !SkinPrimaryAssetIds.Contains(ActiveSkinId))
    {
        ActiveSkinId.Reset();
    }
}

UTwinSkinAsset* UTwinSkinComponent::ResolveSkinAsset(
    const FString& PrimaryAssetId,
    FString& OutError) const
{
    const FPrimaryAssetId AssetId = FPrimaryAssetId::FromString(PrimaryAssetId);
    if (!AssetId.IsValid())
    {
        OutError = FString::Printf(TEXT("Invalid skin Primary Asset ID: %s"), *PrimaryAssetId);
        return nullptr;
    }

    UAssetManager& AssetManager = UAssetManager::Get();
    UObject* AssetObject = AssetManager.GetPrimaryAssetObject(AssetId);
    if (!AssetObject)
    {
        const FSoftObjectPath AssetPath = AssetManager.GetPrimaryAssetPath(AssetId);
        AssetObject = AssetPath.IsValid() ? AssetPath.TryLoad() : nullptr;
    }

    UTwinSkinAsset* SkinAsset = Cast<UTwinSkinAsset>(AssetObject);
    if (!SkinAsset)
    {
        OutError = FString::Printf(
            TEXT("Skin asset %s is missing or is not UTwinSkinAsset. Check Asset Manager scan rules."),
            *PrimaryAssetId);
    }
    return SkinAsset;
}

bool UTwinSkinComponent::ApplySkin(const FString& SkinId, FString& OutError)
{
    const FString* PrimaryAssetId = SkinPrimaryAssetIds.Find(SkinId);
    if (!PrimaryAssetId)
    {
        OutError = FString::Printf(TEXT("Skin is not allowed in this project: %s"), *SkinId);
        return false;
    }

    UTwinSkinAsset* SkinAsset = ResolveSkinAsset(*PrimaryAssetId, OutError);
    ACharacter* Character = Cast<ACharacter>(GetOwner());
    USkeletalMeshComponent* MeshComponent = Character ? Character->GetMesh() : nullptr;
    USkeletalMesh* Mesh = SkinAsset ? SkinAsset->Mesh.LoadSynchronous() : nullptr;
    if (!MeshComponent || !Mesh)
    {
        if (OutError.IsEmpty())
        {
            OutError = FString::Printf(TEXT("Skin mesh cannot be loaded: %s"), *SkinId);
        }
        return false;
    }

    MeshComponent->SetSkeletalMesh(Mesh);
    if (UClass* AnimClass = SkinAsset->AnimInstanceClass.LoadSynchronous())
    {
        MeshComponent->SetAnimInstanceClass(AnimClass);
    }
    for (int32 Index = 0; Index < SkinAsset->MaterialOverrides.Num(); ++Index)
    {
        if (UMaterialInterface* Material = SkinAsset->MaterialOverrides[Index].LoadSynchronous())
        {
            MeshComponent->SetMaterial(Index, Material);
        }
    }

    ActiveSkinId = SkinId;
    return true;
}

bool UTwinSkinComponent::ApplyDefaultSkin(FString& OutError)
{
    if (DefaultSkinId.IsEmpty())
    {
        OutError = TEXT("No default skin is configured");
        return false;
    }
    return ApplySkin(DefaultSkinId, OutError);
}

bool UTwinSkinComponent::CycleSkin(FString& OutError)
{
    if (AllowedSkinIds.Num() == 0)
    {
        OutError = TEXT("No loadable skins are configured");
        return false;
    }
    const int32 CurrentIndex = AllowedSkinIds.IndexOfByKey(ActiveSkinId);
    const int32 NextIndex = CurrentIndex == INDEX_NONE ? 0 : (CurrentIndex + 1) % AllowedSkinIds.Num();
    return ApplySkin(AllowedSkinIds[NextIndex], OutError);
}
