#pragma once

#include "CoreMinimal.h"

namespace OntoTwinModelLibrary
{
    struct FEntry
    {
        FString Label;
        FString Key;
    };

    TArray<FEntry> List(bool bLocal);
    FString ResolveLocal(const FString& Key);
}
