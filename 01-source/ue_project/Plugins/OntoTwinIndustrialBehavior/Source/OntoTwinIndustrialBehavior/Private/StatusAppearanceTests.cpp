#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/World.h"
#include "TwinInstance.h"
#include "IndustrialPresentationComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "Engine/StaticMesh.h"

// NEW-07: grey and wireframe replace every model material and restore it afterwards.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStatusAppearanceSwapTest,
    "OntoTwin.Presentation.StatusAppearanceSwap",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FStatusAppearanceSwapTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    auto* Twin = World->SpawnActor<ATwinInstance>();
    Twin->InitializeTwin(TEXT("isolated-status-appearance"), TEXT("/Engine/BasicShapes/Cube.Cube"), TEXT(""), TEXT(""), TEXT("primary"));
    auto MakeSnapshot = [](const FString& VisualBehavior) {
        auto Snapshot = MakeShared<FJsonObject>();
        auto Interfaces = MakeShared<FJsonObject>();
        auto Presentation = MakeShared<FJsonObject>();
        auto Resolution = MakeShared<FJsonObject>();
        auto Channels = MakeShared<FJsonObject>();
        auto Channel = MakeShared<FJsonObject>();
        Channel->SetStringField(TEXT("behavior_id"), VisualBehavior);
        Channel->SetStringField(TEXT("source"), TEXT("platform"));
        Channels->SetObjectField(TEXT("visual"), Channel);
        Resolution->SetObjectField(TEXT("channels"), Channels);
        Presentation->SetObjectField(TEXT("resolution"), Resolution);
        Interfaces->SetObjectField(TEXT("I3D_Presentation"), Presentation);
        Snapshot->SetObjectField(TEXT("interfaces"), Interfaces);
        return Snapshot;
    };
    auto ModelMeshes = [Twin]() {
        TArray<UStaticMeshComponent*> All, Model;
        Twin->GetComponents<UStaticMeshComponent>(All);
        for (auto* Mesh : All) if (!Mesh->ComponentHasTag(TEXT("OntoTwinPresentation"))) Model.Add(Mesh);
        return Model;
    };
    auto* Gray = LoadObject<UMaterialInterface>(nullptr, TEXT("/OntoTwinIndustrialBehavior/Materials/M_StatusGray.M_StatusGray"));
    auto* Wire = LoadObject<UMaterialInterface>(nullptr, TEXT("/OntoTwinIndustrialBehavior/Materials/M_StatusWireframe.M_StatusWireframe"));
    TestNotNull(TEXT("Grey material asset exists"), Gray);
    TestNotNull(TEXT("Wireframe material asset exists"), Wire);
    const TArray<UStaticMeshComponent*> Meshes = ModelMeshes();
    TestTrue(TEXT("Model has a mesh"), Meshes.Num() > 0);
    TArray<UMaterialInterface*> Original;
    for (auto* Mesh : Meshes) Original.Add(Mesh->GetMaterial(0));

    auto ExpectAll = [&](const TCHAR* What, UMaterialInterface* Expected) {
        for (auto* Mesh : Meshes) TestEqual(What, Mesh->GetMaterial(0), Expected);
    };
    Twin->ApplySnapshot(MakeSnapshot(TEXT("industrial.visual.gray")));
    ExpectAll(TEXT("Grey replaces the model material"), Gray);
    if (auto* Component = Twin->FindComponentByClass<UIndustrialPresentationComponent>())
    {
        Component->TickComponent(.1f, LEVELTICK_All, nullptr);
        ExpectAll(TEXT("Tick keeps grey without stacking"), Gray);
    }
    Twin->ApplySnapshot(MakeSnapshot(TEXT("industrial.visual.wireframe")));
    ExpectAll(TEXT("Wireframe replaces grey"), Wire);
    Twin->ApplySnapshot(MakeSnapshot(TEXT("industrial.visual.warning")));
    for (int32 Index = 0; Index < Meshes.Num(); ++Index)
    {
        TestEqual(TEXT("Switching to a highlight restores the original"), Meshes[Index]->GetMaterial(0), Original[Index]);
        TestNotNull(TEXT("Highlight overlay applied"), Meshes[Index]->GetOverlayMaterial());
    }
    Twin->ApplySnapshot(MakeSnapshot(TEXT("industrial.visual.gray")));
    Twin->ApplySnapshot(MakeSnapshot(TEXT("safe.visible")));
    for (int32 Index = 0; Index < Meshes.Num(); ++Index)
    {
        TestEqual(TEXT("Leaving the state restores the original"), Meshes[Index]->GetMaterial(0), Original[Index]);
        TestNull(TEXT("No overlay left"), Meshes[Index]->GetOverlayMaterial());
    }
    // The model is replaced while grey is shown: leaving grey must show the new
    // model's own material, never the previous model's.
    if (Meshes.Num() > 0)
    {
        auto* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
        TestNotNull(TEXT("Replacement model exists"), Sphere);
        Twin->ApplySnapshot(MakeSnapshot(TEXT("industrial.visual.gray")));
        Meshes[0]->SetStaticMesh(Sphere);
        if (auto* Component = Twin->FindComponentByClass<UIndustrialPresentationComponent>())
            Component->TickComponent(.1f, LEVELTICK_All, nullptr);
        TestEqual(TEXT("New model also shown grey"), Meshes[0]->GetMaterial(0), Gray);
        Twin->ApplySnapshot(MakeSnapshot(TEXT("safe.visible")));
        TestTrue(TEXT("New model gets its own material back"), Sphere && Meshes[0]->GetMaterial(0) == Sphere->GetMaterial(0));
    }
    World->DestroyWorld(false);
    return true;
}
#endif
