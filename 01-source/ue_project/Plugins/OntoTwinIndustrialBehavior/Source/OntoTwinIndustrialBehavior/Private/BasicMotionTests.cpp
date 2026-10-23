#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Engine/World.h"
#include "TwinInstance.h"
#include "BasicMotionComponent.h"
#include "BeltMaterialComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/StaticMeshComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBasicMotionTest, "OntoTwin.Presentation.BasicModelMotion",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBasicMotionTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    auto* Twin = World->SpawnActor<ATwinInstance>();
    Twin->InitializeTwin(TEXT("isolated-motion"), TEXT("/Engine/BasicShapes/Cube.Cube"), TEXT(""), TEXT(""), TEXT("primary"));
    auto* Model = Twin->FindComponentByClass<UStaticMeshComponent>();
    TestNotNull(TEXT("Actual model mesh"), Model);
    if (!Model) { World->DestroyWorld(false); return false; }
    Twin->SetActorLocation(FVector(200,300,400));
    const FTransform Business = Twin->GetActorTransform();
    auto Route = [Twin](const FString& Id, double Value) {
        auto P = MakeShared<FJsonObject>();
        P->SetStringField(TEXT("axis"), TEXT("z"));
        P->SetNumberField(TEXT("speed"), Value);
        P->SetNumberField(TEXT("distance"), 100);
        P->SetNumberField(TEXT("angle"), 90);
        P->SetNumberField(TEXT("duration"), 2);
        auto C = MakeShared<FJsonObject>();
        C->SetStringField(TEXT("behavior_id"), Id);
        C->SetStringField(TEXT("source"), TEXT("platform"));
        C->SetObjectField(TEXT("params"), P);
        auto Channels = MakeShared<FJsonObject>(); Channels->SetObjectField(TEXT("animation"), C);
        auto Resolution = MakeShared<FJsonObject>(); Resolution->SetObjectField(TEXT("channels"), Channels);
        auto Presentation = MakeShared<FJsonObject>(); Presentation->SetObjectField(TEXT("resolution"), Resolution);
        auto Interfaces = MakeShared<FJsonObject>(); Interfaces->SetObjectField(TEXT("I3D_Presentation"), Presentation);
        auto Snapshot = MakeShared<FJsonObject>(); Snapshot->SetObjectField(TEXT("interfaces"), Interfaces);
        Twin->ApplySnapshot(Snapshot);
    };
    Route(TEXT("motion.rotate"), 90);
    auto* Motion = Twin->FindComponentByClass<UBasicMotionComponent>();
    TestNotNull(TEXT("Basic executor loaded"), Motion);
    if (!Motion) { World->DestroyWorld(false); return false; }
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Model itself rotates 90 degrees"), FMath::IsNearlyEqual(Model->GetRelativeRotation().Yaw,90.,.1));
    TestTrue(TEXT("Business root unchanged"), Twin->GetActorTransform().Equals(Business));
    Route(TEXT("motion.rotate"), 45);
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Parameter-only change reaches executor"), FMath::IsNearlyEqual(Model->GetRelativeRotation().Yaw,45.,.1));
    Route(TEXT("motion.rotate"), 45);
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Repeated snapshots do not restart loop"), FMath::IsNearlyEqual(Model->GetRelativeRotation().Yaw,90.,.1));
    Route(TEXT("motion.translate"), 90);
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Model moves half of 100cm in one second"), FMath::IsNearlyEqual(Model->GetRelativeLocation().Z,50.,.1));
    Twin->SetActorLocation(FVector(600,700,800));
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Data position plus display offset"), Model->GetComponentLocation().Equals(FVector(600,700,900),.1));
    Motion->TickComponent(10, LEVELTICK_All, nullptr);
    TestTrue(TEXT("One-shot motion holds destination"), FMath::IsNearlyEqual(Model->GetRelativeLocation().Z,100.,.1));
    Route(TEXT("motion.pingpong"), 90);
    Motion->TickComponent(2, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Pingpong reaches end"), FMath::IsNearlyEqual(Model->GetRelativeLocation().Z,100.,.1));
    Motion->TickComponent(2, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Pingpong returns"), Model->GetRelativeLocation().IsNearlyZero(.1));
    Route(TEXT("motion.rotate_to"), 90);
    Motion->TickComponent(2, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Rotate to reaches angle"), FMath::IsNearlyEqual(Model->GetRelativeRotation().Yaw,90.,.1));
    Route(TEXT("motion.swing"), 90);
    Motion->TickComponent(2, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Swing reaches angle"), FMath::IsNearlyEqual(Model->GetRelativeRotation().Yaw,90.,.1));
    Motion->TickComponent(2, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Swing returns"), Model->GetRelativeRotation().IsNearlyZero(.1));
    Route(TEXT("motion.reset"), 90);
    TestTrue(TEXT("Reset restores model"), Model->GetRelativeTransform().Equals(FTransform::Identity,.1));
    TestTrue(TEXT("Reset preserves latest real position"), Twin->GetActorLocation().Equals(FVector(600,700,800),.1));
    auto Params = MakeShared<FJsonObject>();
    Params->SetStringField(TEXT("target"), TEXT("tagged"));
    Params->SetStringField(TEXT("axis"), TEXT("x"));
    Params->SetNumberField(TEXT("distance"), 60);
    Params->SetNumberField(TEXT("duration"), 1);
    auto* Door = NewObject<UStaticMeshComponent>(Twin, TEXT("Door"));
    Twin->AddInstanceComponent(Door);
    Door->SetupAttachment(Twin->GetRootComponent());
    Door->SetStaticMesh(Model->GetStaticMesh());
    Door->SetMobility(EComponentMobility::Movable);
    Door->ComponentTags.Add(TEXT("OntoTwinMotionTarget"));
    Door->SetRelativeLocation(FVector(20,0,0));
    Door->RegisterComponent();
    Motion->Apply(TEXT("motion.translate"), Params);
    Motion->TickComponent(1, LEVELTICK_All, nullptr);
    TestTrue(TEXT("Tagged door travels its stroke"), Door->GetRelativeLocation().Equals(FVector(80,0,0),.1));
    TestTrue(TEXT("Device body does not move with door"), Model->GetRelativeLocation().IsNearlyZero(.1));
    Motion->ResetMotion();
    TestTrue(TEXT("Door restores original local placement"), Door->GetRelativeLocation().Equals(FVector(20,0,0),.1));
    // Invalid wire parameters must stop existing motion safely.
    Params->SetNumberField(TEXT("duration"), 0);
    TestFalse(TEXT("Invalid duration rejected"), Motion->Apply(TEXT("motion.translate"), Params));
    auto* OriginalMaterial = Model->GetMaterial(0);
    auto BeltParams = MakeShared<FJsonObject>();
    BeltParams->SetNumberField(TEXT("speed"), .5);
    TestTrue(TEXT("Real belt material loads"), Twin->ExecutePresentationRoute(TEXT("visual"), TEXT("material.belt_scroll"), TEXT("status_indicator"), TEXT("platform"), BeltParams));
    auto* Belt = Twin->FindComponentByClass<UBeltMaterialComponent>();
    if (Belt && Belt->Material)
    {
        Belt->TickComponent(.5, LEVELTICK_All, nullptr);
        TestTrue(TEXT("Belt UV offset advances"), FMath::IsNearlyEqual(Belt->Material->K2_GetScalarParameterValue(TEXT("Offset")), .25f));
        TestTrue(TEXT("Belt material applied to actual model"), Model->GetMaterial(0) == Belt->Material);
        Twin->ExecutePresentationRoute(TEXT("visual"), TEXT("safe.visible"), TEXT("status_indicator"));
        TestTrue(TEXT("Belt reset restores original material"), Model->GetMaterial(0) == OriginalMaterial);
    }
    World->DestroyWorld(false);
    return true;
}
#endif
