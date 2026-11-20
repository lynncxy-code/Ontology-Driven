#pragma once

#include "CoreMinimal.h"

class AActor;
class UWorld;

/**
 * Which scene objects count as walls for F10 wall snapping.
 *
 * An actor is a wall when it carries the scene manager's wall tag, or when its
 * name ends with "_Wall" (case-insensitive, an optional copy number such as
 * "_Wall2" or "_Wall_3" is allowed).  The editor-only display name is checked
 * in editor builds; packaged builds rely on the tag, which the editor module
 * adds automatically whenever a level is saved or cooked.
 */
namespace OntoTwinWalls
{
    inline const FName DefaultTag(TEXT("OntoTwinWall"));

    ONTOTWINSYNC_API bool NameLooksLikeWall(const FString& Name);
    ONTOTWINSYNC_API bool IsWall(const AActor* Actor, FName Tag);
    ONTOTWINSYNC_API void Collect(UWorld* World, FName Tag, TArray<AActor*>& OutWalls);
}
