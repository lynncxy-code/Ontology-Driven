#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "RuntimeEditor/OntoTwinWallRules.h"
#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FOntoTwinWallRulesTest, "OntoTwin.RuntimeEditor.WallRules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FOntoTwinWallRulesTest::RunTest(const FString& Parameters)
{
    using namespace OntoTwinWalls;
    for (const TCHAR* Name : { TEXT("Office_Wall"), TEXT("office_wall"), TEXT("SM_Lobby_WALL"),
                               TEXT("Office_Wall2"), TEXT("Office_Wall_3"), TEXT("A_Wall_12") })
        TestTrue(FString::Printf(TEXT("%s is a wall"), Name), NameLooksLikeWall(Name));
    for (const TCHAR* Name : { TEXT("Wall"), TEXT("SM_Walls"), TEXT("Office_Wallpaper"), TEXT("Wall_Office"),
                               TEXT("Office_Wall_Lamp"), TEXT("StaticMeshActor_57"), TEXT("") })
        TestFalse(FString::Printf(TEXT("%s is not a wall"), Name), NameLooksLikeWall(Name));

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    FActorSpawnParameters Params;
    Params.Name = TEXT("Corridor_Wall");
    AActor* Named = World->SpawnActor<AStaticMeshActor>(Params);
    AActor* Tagged = World->SpawnActor<AStaticMeshActor>();
    Tagged->Tags.Add(DefaultTag);
    AActor* Plain = World->SpawnActor<AStaticMeshActor>();
#if WITH_EDITOR
    AActor* Labelled = World->SpawnActor<AStaticMeshActor>();
    Labelled->SetActorLabel(TEXT("Lobby_Wall2"));
    TestTrue(TEXT("Outliner name ending in _Wall counts in the editor"), IsWall(Labelled, DefaultTag));
#endif
    TestTrue(TEXT("Object name ending in _Wall counts"), IsWall(Named, DefaultTag));
    TestTrue(TEXT("Wall tag still counts"), IsWall(Tagged, DefaultTag));
    TestFalse(TEXT("Other objects do not count"), IsWall(Plain, DefaultTag));
    TArray<AActor*> Walls;
    Collect(World, DefaultTag, Walls);
    TestTrue(TEXT("Collect finds named and tagged walls"), Walls.Contains(Named) && Walls.Contains(Tagged) && !Walls.Contains(Plain));
    World->DestroyWorld(false);
    return true;
}
#endif
