#if WITH_DEV_AUTOMATION_TESTS
#include "OntoTwinConnectionContext.h"
#include "Misc/AutomationTest.h"
#include "HttpModule.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "TimerManager.h"
#include "EngineUtils.h"
#include "TwinSceneManager.h"
#include "WebInteraction/OntoTwinWebInteractionComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FOntoTwinConnectionContextTest,
    "OntoTwin.Connection.ExplicitContext", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FOntoTwinConnectionContextTest::RunTest(const FString& Parameters)
{
    const TCHAR* Section = TEXT("OntoTwin.Connection");
    FString PreviousProject;
    const bool bHadProject = GConfig->GetString(Section, TEXT("ProjectId"), PreviousProject, GGameIni);
    GConfig->SetString(Section, TEXT("ProjectId"), TEXT(""), GGameIni);
    auto Legacy = FHttpModule::Get().CreateRequest();
    Legacy->SetHeader(TEXT("X-OntoTwin-Project-Id"), TEXT("existing"));
    OntoTwinConnectionContext::Apply(Legacy, nullptr);
    TestEqual(TEXT("Unconfigured deployments keep existing protocol"),
        Legacy->GetHeader(TEXT("X-OntoTwin-Project-Id")), FString(TEXT("existing")));

    GConfig->SetString(Section, TEXT("ProjectId"), TEXT("ACCEPT48_connection"), GGameIni);
    UPackage* Package = CreatePackage(TEXT("/Game/ACCEPT48/UEDPIE_0_Office"));
    UWorld* World = NewObject<UWorld>(Package, TEXT("Office"));
    World->WorldType = EWorldType::PIE;
    World->StreamingLevelsPrefix = TEXT("UEDPIE_0_");
    auto Request = FHttpModule::Get().CreateRequest();
    OntoTwinConnectionContext::Apply(Request, World);
    TestEqual(TEXT("Explicit project header"), Request->GetHeader(TEXT("X-OntoTwin-Project-Id")), FString(TEXT("ACCEPT48_connection")));
    TestEqual(TEXT("PIE uses stable level path"), Request->GetHeader(TEXT("X-OntoTwin-UE-Scene-Id")), FString(TEXT("/Game/ACCEPT48/Office")));
    TestEqual(TEXT("PIE context"), Request->GetHeader(TEXT("X-OntoTwin-UE-Context")), FString(TEXT("pie")));
    if (bHadProject) GConfig->SetString(Section, TEXT("ProjectId"), *PreviousProject, GGameIni);
    else GConfig->RemoveKey(Section, TEXT("ProjectId"), GGameIni);
    return true;
}

// Opt-in real-map smoke check; exits its own process without saving a level.
static FAutoConsoleCommandWithWorld GConnectionSmoke(
    TEXT("OntoTwin.ConnectionSmoke"), TEXT("Report connection readiness after 30 seconds, then exit."),
    FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
    {
        if (!World || !World->IsGameWorld()) return;
        FTimerHandle Timer;
        World->GetTimerManager().SetTimer(Timer, FTimerDelegate::CreateWeakLambda(World, [World]()
        {
            for (TActorIterator<ATwinSceneManager> It(World); It; ++It)
            {
                UE_LOG(LogTemp, Display, TEXT("ONTOTWIN_CONNECTION_SMOKE backend=%s project=%s web_ready=%d"),
                    *It->BackendBaseUrl, *OntoTwinConnectionContext::Setting(TEXT("ProjectId")),
                    It->WebInteractionManager && It->WebInteractionManager->IsRuntimeReady());
            }
            FPlatformMisc::RequestExit(false);
        }), 30.0f, false);
    }));
#endif
