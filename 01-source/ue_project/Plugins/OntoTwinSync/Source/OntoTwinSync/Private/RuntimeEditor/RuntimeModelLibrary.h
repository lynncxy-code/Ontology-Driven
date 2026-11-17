#pragma once

#include "CoreMinimal.h"

class UStaticMesh;

namespace OntoTwinModelLibrary
{
    struct FEntry
    {
        FString Label;
        FString Key;
    };

    TArray<FEntry> List(bool bLocal);
    FString ResolveLocal(const FString& Key);
    UStaticMesh* LoadGltfMesh(const FString& FilePath, bool bBuildCollision);
}
