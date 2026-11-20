#include "OntoTwinWallAutoTag.h"

#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "RuntimeEditor/OntoTwinWallRules.h"
#include "TwinSceneManager.h"
#include "UObject/ObjectSaveContext.h"
#include "UObject/UObjectGlobals.h"

// The display name an artist types in the Outliner ("Office_Wall") is editor-only
// and is stripped from packaged builds.  Copy the wall rule onto the actor as a
// tag whenever it is saved or cooked, so packaged F10 wall snapping finds the
// same walls the editor does.  Only the tag is added; nothing else changes.
namespace
{
    FDelegateHandle PreSaveHandle;

    FName WallTagFor(const AActor* Actor)
    {
        if (UWorld* World = Actor->GetWorld())
        {
            for (TActorIterator<ATwinSceneManager> It(World); It; ++It)
            {
                if (!It->WallTag.IsNone()) return It->WallTag;
            }
        }
        return OntoTwinWalls::DefaultTag;
    }

    void HandlePreSave(UObject* Object, FObjectPreSaveContext Context)
    {
        AActor* Actor = Cast<AActor>(Object);
        if (!Actor || Actor->HasAnyFlags(RF_ClassDefaultObject | RF_ArchetypeObject)) return;
        if (!OntoTwinWalls::NameLooksLikeWall(Actor->GetActorLabel(false))) return;
        const FName Tag = WallTagFor(Actor);
        if (Actor->Tags.Contains(Tag)) return;
        Actor->Tags.Add(Tag);
        UE_LOG(LogTemp, Log, TEXT("[OntoTwin] 墙体自动补标签 %s -> %s%s"),
            *Actor->GetActorLabel(false), *Tag.ToString(), Context.IsCooking() ? TEXT("（打包）") : TEXT(""));
    }
}

void OntoTwinWallAutoTag::Register()
{
    if (!PreSaveHandle.IsValid())
        PreSaveHandle = FCoreUObjectDelegates::OnObjectPreSave.AddStatic(&HandlePreSave);
}

void OntoTwinWallAutoTag::Unregister()
{
    if (PreSaveHandle.IsValid())
    {
        FCoreUObjectDelegates::OnObjectPreSave.Remove(PreSaveHandle);
        PreSaveHandle.Reset();
    }
}
