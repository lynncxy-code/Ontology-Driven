#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "HAL/FileManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "glTFRuntimeFunctionLibrary.h"
#include "glTFRuntimeAsset.h"

UStaticMesh* OntoTwinModelLibrary::LoadGltfMesh(const FString& FilePath, bool bBuildCollision)
{
    FglTFRuntimeConfig Loader;
    Loader.TransformBaseType = EglTFRuntimeTransformBaseType::Default;
    Loader.SceneScale = 100.f; // metres to UE centimetres
    auto* Asset = UglTFRuntimeFunctionLibrary::glTFLoadAssetFromFilename(FilePath, false, Loader);
    if (!Asset) return nullptr;

    FglTFRuntimeStaticMeshConfig Config;
    Config.bBuildSimpleCollision = bBuildCollision;
    Config.NormalsGenerationStrategy = EglTFRuntimeNormalsGenerationStrategy::IfMissing;
    Config.TangentsGenerationStrategy = EglTFRuntimeTangentsGenerationStrategy::IfMissing;
    return Asset->LoadStaticMeshRecursive(FString(), TArray<FString>(), Config);
}

FString OntoTwinModelLibrary::ModelsDirectory()
{
    FString Configured;
    GConfig->GetString(TEXT("OntoTwinSync"), TEXT("ModelsDir"), Configured, GGameIni);
    if (!Configured.IsEmpty()) return FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), Configured);
    const FString ProjectModels = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), TEXT("Models"));
    if (!FPlatformProperties::RequiresCookedData()) return ProjectModels;
    const FString LauncherModels = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), TEXT("../Models"));
    return FPaths::DirectoryExists(LauncherModels) ? LauncherModels : ProjectModels;
}

FString OntoTwinModelLibrary::ResolveLocal(const FString& Key)
{
    FString Name = Key;
    if (!Name.RemoveFromStart(TEXT("models:")) || !Name.EndsWith(TEXT(".glb"))
        || Name != FPaths::GetCleanFilename(Name) || Name.Contains(TEXT(":"))
        || Name.Contains(TEXT("\\"))) return {};
    const FString File = ModelsDirectory() / Name;
    return FPaths::FileExists(File) ? File : FString();
}

TArray<OntoTwinModelLibrary::FEntry> OntoTwinModelLibrary::List(bool bLocal)
{
    TArray<FEntry> Entries;
    if (bLocal)
    {
        TArray<FString> Files;
        IFileManager::Get().FindFiles(Files, *(ModelsDirectory() / TEXT("*")), true, false);
        for (const FString& File : Files)
        {
            const FString Key = TEXT("models:") + File;
            const FString Path = ResolveLocal(Key);
            if (Path.IsEmpty()) continue;
            FEntry Entry{FPaths::GetBaseFilename(File), Key, TEXT("GLB")};
            TUniquePtr<FArchive> Reader(IFileManager::Get().CreateFileReader(*Path));
            uint32 Magic = 0, Version = 0, Length = 0;
            if (Reader && Reader->TotalSize() >= 12)
            {
                *Reader << Magic << Version << Length;
            }
            if (!Reader || Magic != 0x46546c67 || Version != 2 || Length != Reader->TotalSize())
                Entry.Error = TEXT("文件损坏");
            Entries.Add(MoveTemp(Entry));
        }
    }
    else
    {
        TArray<FString> Roots;
        GConfig->GetArray(TEXT("/Script/OntoTwinSyncEditor.OntoTwinModelLibrarySettings"), TEXT("Roots"), Roots, GGameIni);
        if (Roots.IsEmpty()) return Entries;
        const FString Directory = FPaths::ProjectContentDir() / TEXT("OntoTwinModelLibrary");
        FString Json;
        TArray<TSharedPtr<FJsonValue>> Items;
        if (FFileHelper::LoadFileToString(Json, *(Directory / TEXT("catalog.json"))) &&
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Items))
        {
            for (const auto& Item : Items)
            {
                const TSharedPtr<FJsonObject>* Object = nullptr;
                FEntry Entry;
                FString Image;
                if (Item->TryGetObject(Object) && (*Object)->TryGetStringField(TEXT("label"), Entry.Label)
                    && (*Object)->TryGetStringField(TEXT("key"), Entry.Key) && Entry.Key.StartsWith(TEXT("/Game/"))
                    && (*Object)->TryGetStringField(TEXT("kind"), Entry.Kind)
                    && (*Object)->TryGetStringField(TEXT("thumbnail"), Image) && FPaths::GetCleanFilename(Image) == Image)
                {
                    Entry.Thumbnail = Directory / Image;
                    Entries.Add(MoveTemp(Entry));
                }
            }
        }
    }
    Entries.Sort([](const FEntry& A, const FEntry& B) {
        const int32 Order = A.Label.Compare(B.Label, ESearchCase::IgnoreCase);
        return Order ? Order < 0 : A.Key < B.Key;
    });
    return Entries;
}
