#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "HAL/FileManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
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

namespace
{
FString ModelsDirectory()
{
    FString Configured;
    GConfig->GetString(TEXT("OntoTwinSync"), TEXT("ModelsDir"), Configured, GGameIni);
    if (!Configured.IsEmpty()) return FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), Configured);
    const FString ProjectModels = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), TEXT("Models"));
    if (!FPlatformProperties::RequiresCookedData()) return ProjectModels;
    const FString LauncherModels = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), TEXT("../Models"));
    return FPaths::DirectoryExists(LauncherModels) ? LauncherModels : ProjectModels;
}
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
        Files.Sort();
        for (const FString& File : Files)
        {
            const FString Key = TEXT("models:") + File;
            if (!ResolveLocal(Key).IsEmpty()) Entries.Add({File, Key});
        }
    }
    else
    {
        TArray<FString> Lines;
        GConfig->GetArray(TEXT("OntoTwinSync"), TEXT("ProjectModels"), Lines, GGameIni);
        for (const FString& Line : Lines)
        {
            FString Label, Key;
            if (Line.Split(TEXT("|"), &Label, &Key) && !Label.IsEmpty() && Key.StartsWith(TEXT("/Game/")))
                Entries.Add({Label, Key});
        }
    }
    return Entries;
}
