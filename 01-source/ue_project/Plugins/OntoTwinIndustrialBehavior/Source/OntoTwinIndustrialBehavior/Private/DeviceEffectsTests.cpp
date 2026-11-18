#if WITH_DEV_AUTOMATION_TESTS
#include "DeviceEffectsComponent.h"
#include "Misc/AutomationTest.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "Materials/Material.h"
#include "Dom/JsonObject.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeviceEffectsTest, "OntoTwin.Presentation.DeviceEffects",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDeviceEffectsTest::RunTest(const FString &)
{
    auto *W = UWorld::CreateWorld(EWorldType::Game, false);
    if (!TestNotNull(TEXT("world"), W))
        return false;
    auto Spawn = [W]() {
        auto *A = W->SpawnActor<AStaticMeshActor>();
        A->GetStaticMeshComponent()->SetStaticMesh(
            LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
        auto *C = NewObject<UDeviceEffectsComponent>(A);
        A->AddInstanceComponent(C);
        C->RegisterComponent();
        return C;
    };
    auto *A = Spawn();
    auto *B = Spawn();
    auto *Mesh = CastChecked<AStaticMeshActor>(A->GetOwner())->GetStaticMeshComponent();
    auto *Initial = UMaterial::GetDefaultMaterial(MD_Surface);
    Mesh->SetOverlayMaterial(Initial);
    auto P = MakeShared<FJsonObject>();
    P->SetStringField(TEXT("color"), TEXT("blocked"));
    P->SetNumberField(TEXT("duration"), .5);
    TestTrue(TEXT("highlight starts"), A->StartHighlight(P));
    TestTrue(TEXT("original overlay covered"), Mesh->GetOverlayMaterial() != Initial);
    P = MakeShared<FJsonObject>();
    P->SetStringField(TEXT("finish"), TEXT("hold"));
    P->SetNumberField(TEXT("duration"), .5);
    TestTrue(TEXT("blue scan starts"), A->StartScan(P));
    auto *FA = A->GetOwner()->FindComponentByClass<UPostProcessComponent>();
    P->SetStringField(TEXT("style"), TEXT("rehearsal"));
    P->SetStringField(TEXT("finish"), TEXT("restore"));
    TestTrue(TEXT("green scan starts"), B->StartScan(P));
    auto *FB = B->GetOwner()->FindComponentByClass<UPostProcessComponent>();
    if (TestNotNull(TEXT("A filter"), FA) && TestNotNull(TEXT("B filter"), FB))
    {
        TestTrue(TEXT("last device owns scan"), FA->BlendWeight == 0 && FB->BlendWeight == 1);
        A->TickComponent(.6f, LEVELTICK_All, nullptr);
        TestTrue(TEXT("highlight expires even while scan suspended"), Mesh->GetOverlayMaterial() == Initial);
        B->TickComponent(.6f, LEVELTICK_All, nullptr);
        TestTrue(TEXT("one-shot releases previous device"), FA->BlendWeight == 1 && FB->BlendWeight == 0);
        A->TickComponent(2, LEVELTICK_All, nullptr);
        TestEqual(TEXT("held grid remains"), FA->BlendWeight, 1.f);
        P->SetNumberField(TEXT("interval"), 2);
        B->StartScan(P);
        B->TickComponent(.6f, LEVELTICK_All, nullptr);
        TestTrue(TEXT("repeating scan yields during cooldown"), FA->BlendWeight == 1 && FB->BlendWeight == 0);
        B->TickComponent(2, LEVELTICK_All, nullptr);
        TestTrue(TEXT("repeat reclaims display"), FA->BlendWeight == 0 && FB->BlendWeight == 1);
        B->StopScan();
        A->StopScan();
        TestTrue(TEXT("all filters off"), FA->BlendWeight == 0 && FB->BlendWeight == 0);
    }
    W->DestroyWorld(false);
    return true;
}
#endif
