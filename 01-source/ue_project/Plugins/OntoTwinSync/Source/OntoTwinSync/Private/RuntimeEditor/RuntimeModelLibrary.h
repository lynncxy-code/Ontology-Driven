#pragma once

#include "CoreMinimal.h"

class UStaticMesh;

namespace OntoTwinModelLibrary
{
    struct FEntry
    {
        FString Label;
        FString Key;
        FString Kind;
        FString Thumbnail;
        FString Error;
    };

    TArray<FEntry> List(bool bLocal);
    FString ModelsDirectory();
    bool LocalThumbnail(const FString& Key, FString& ImagePath, FString& Error);
    FString ResolveLocal(const FString& Key);
    UStaticMesh* LoadGltfMesh(const FString& FilePath, bool bBuildCollision);
}
