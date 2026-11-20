#include "RuntimeEditor/OntoTwinWallRules.h"

#include "EngineUtils.h"
#include "GameFramework/Actor.h"

bool OntoTwinWalls::NameLooksLikeWall(const FString& Name)
{
    FString Stem = Name;
    int32 End = Stem.Len();
    while (End > 0 && FChar::IsDigit(Stem[End - 1])) --End;
    if (End < Stem.Len() && End > 0 && Stem[End - 1] == TEXT('_')) --End;
    Stem.LeftInline(End);
    return Stem.EndsWith(TEXT("_Wall"), ESearchCase::IgnoreCase);
}

bool OntoTwinWalls::IsWall(const AActor* Actor, FName Tag)
{
    if (!IsValid(Actor)) return false;
    if (!Tag.IsNone() && Actor->ActorHasTag(Tag)) return true;
#if WITH_EDITOR
    if (NameLooksLikeWall(Actor->GetActorLabel(false))) return true;
#endif
    return NameLooksLikeWall(Actor->GetName());
}

void OntoTwinWalls::Collect(UWorld* World, FName Tag, TArray<AActor*>& OutWalls)
{
    OutWalls.Reset();
    if (!World) return;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (IsWall(*It, Tag)) OutWalls.Add(*It);
    }
}
