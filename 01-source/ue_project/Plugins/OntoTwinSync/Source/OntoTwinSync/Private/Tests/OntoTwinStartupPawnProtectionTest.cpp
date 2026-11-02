#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneInteraction/TwinInteractionManagerComponent.h"
#include "TwinSceneManager.h"
#include "Engine/World.h"
#include "GameFramework/DefaultPawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpectatorPawn.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FOntoTwinStartupPawnProtectionTest,
    "OntoTwin.SceneInteraction.StartupPreservesDerivedPawns",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FOntoTwinStartupPawnProtectionTest::RunTest(const FString& Parameters)
{
    // No BeginPlay, backend connection, saved map or business data.
    const auto Settings = UWorld::InitializationValues().AllowAudioPlayback(false)
        .CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(false);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, NAME_None,
        nullptr, true, ERHIFeatureLevel::Num, &Settings);
    auto* Scene = World->SpawnActor<ATwinSceneManager>();
    auto* Controller = World->SpawnActor<APlayerController>();
    auto* NativePawn = World->SpawnActor<ADefaultPawn>();
    auto* DerivedPawn = World->SpawnActor<ASpectatorPawn>();
    DerivedPawn->SetActorHiddenInGame(false);
    DerivedPawn->SetActorEnableCollision(true);
    auto* Manager = NewObject<UTwinInteractionManagerComponent>(Scene);
    Manager->SceneManager = Scene;
    Manager->PlayerController = Controller;
    Manager->ApplyStartupView(true);
    TestTrue(TEXT("Home camera takes possession"), Controller->GetPawn() != nullptr);
    TestTrue(TEXT("Native default sphere hidden"), NativePawn->IsHidden());
    TestFalse(TEXT("Native default sphere collision disabled"), NativePawn->GetActorEnableCollision());
    TestFalse(TEXT("Derived pawn remains visible"), DerivedPawn->IsHidden());
    TestTrue(TEXT("Derived pawn collision preserved"), DerivedPawn->GetActorEnableCollision());
    World->DestroyWorld(false);
    return true;
}
#endif
