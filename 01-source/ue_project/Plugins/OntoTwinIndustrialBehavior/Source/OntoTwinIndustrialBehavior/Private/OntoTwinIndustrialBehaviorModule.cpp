#include "OntoTwinIndustrialBehaviorModule.h"
#include "DeviceEffectsComponent.h"
#include "GameDelegates.h"

#include "GameFramework/Actor.h"
#include "TwinInstance.h"
#include "IndustrialPresentationComponent.h"
#include "BasicMotionComponent.h"
#include "BeltMaterialComponent.h"

void FOntoTwinIndustrialBehaviorModule::StartupModule()
{
#if WITH_EDITOR
    // These six roots are selected at runtime; the cooker follows their package dependencies.
    CookHandle = FGameDelegates::Get().GetModifyCookDelegate().AddLambda(
        [](TConstArrayView<const ITargetPlatform*>, TArray<FName>& Packages, TArray<FName>&){
            for (const TCHAR* Root : {TEXT("N_Scan01"), TEXT("MPC_Scan"), TEXT("MI_Go2NativeFloorScan"),
                TEXT("MI_RehearsalFloorScan_Green"), TEXT("MI_TranslucentOverlay"), TEXT("MI_TranslucentOverlay_2")})
                Packages.AddUnique(FName(*(FString(TEXT("/OntoTwinIndustrialBehavior/Effects/")) + Root)));
        });
#endif
    IModularFeatures::Get().RegisterModularFeature(
        IOntoTwinPresentationExecutor::GetModularFeatureName(), this);
}

void FOntoTwinIndustrialBehaviorModule::ShutdownModule()
{
#if WITH_EDITOR
    FGameDelegates::Get().GetModifyCookDelegate().Remove(CookHandle);
#endif
    if (IModularFeatures::Get().IsModularFeatureAvailable(
        IOntoTwinPresentationExecutor::GetModularFeatureName()))
    {
        IModularFeatures::Get().UnregisterModularFeature(
            IOntoTwinPresentationExecutor::GetModularFeatureName(), this);
    }
}

FString FOntoTwinIndustrialBehaviorModule::GetPresentationExecutorId() const
{
    return TEXT("platform.industrial.default");
}

int32 FOntoTwinIndustrialBehaviorModule::GetPresentationExecutorPriority() const
{
    return 10;
}

bool FOntoTwinIndustrialBehaviorModule::SupportsPresentationRoute(
    const FString& Channel,
    const FString& BehaviorId,
    const FString& Slot,
    const FString& Source) const
{
    // A project route must be handled by the project executor.  The platform
    // library only claims platform-resolved routes, preserving precedence.
    if (Source == TEXT("project"))
    {
        return false;
    }
    if (BehaviorId.StartsWith(TEXT("safe."))) return true;
    if (Channel == TEXT("label")) return BehaviorId == TEXT("industrial.label.demo");
    const bool bKnownSlot = Slot.IsEmpty()
        || Slot == TEXT("primary")
        || Slot == TEXT("motion")
        || Slot == TEXT("status_indicator")
        || Slot == TEXT("alarm")
        || Slot == TEXT("label");
    if (!bKnownSlot)
    {
        return false;
    }

    if (Channel == TEXT("animation"))
    {
        return BehaviorId == TEXT("motion.rotate") || BehaviorId == TEXT("motion.translate")
            || BehaviorId == TEXT("motion.rotate_to") || BehaviorId == TEXT("motion.pingpong")
            || BehaviorId == TEXT("motion.swing") || BehaviorId == TEXT("motion.reset")
            || BehaviorId == TEXT("industrial.machine.idle")
            || BehaviorId == TEXT("industrial.machine.running")
            || BehaviorId == TEXT("industrial.machine.fault")
            || BehaviorId == TEXT("industrial.machine.offline");
    }
    if (Channel == TEXT("visual"))
    {
        return BehaviorId == TEXT("ot.industrial.target_highlight") || BehaviorId == TEXT("material.belt_scroll") || BehaviorId == TEXT("industrial.visual.warning")
            || BehaviorId == TEXT("industrial.visual.critical")
            || BehaviorId == TEXT("industrial.visual.maintenance");
    }
    if (Channel == TEXT("fx") || Channel == TEXT("action"))
    {
        return BehaviorId == TEXT("ot.industrial.region_scan") || BehaviorId == TEXT("industrial.fx.warning_flash")
            || BehaviorId == TEXT("industrial.fx.critical_flash")
            || BehaviorId == TEXT("industrial.fx.start_pulse");
    }
    return false;
}

bool FOntoTwinIndustrialBehaviorModule::ExecutePresentationRoute(
    ATwinInstance* Twin,
    const FString& Channel,
    const FString& BehaviorId,
    const FString& Slot,
    const FString& Source,
    const TSharedPtr<FJsonObject>& Params)
{
    if (!Twin || !SupportsPresentationRoute(Channel, BehaviorId, Slot, Source))
    {
        return false;
    }
    // BUG-29 diagnostics: every route that can change model materials.
    if (Channel == TEXT("visual"))
        UE_LOG(LogTemp, Log, TEXT("[OT-Material] 收到外观路由 instance=%s actor=%s behavior=%s"),
            *Twin->GetInstanceId(), *Twin->GetName(), *BehaviorId);

    auto* Effects = Twin->FindComponentByClass<UDeviceEffectsComponent>();
    const bool Scan = Channel == TEXT("fx") && BehaviorId == TEXT("ot.industrial.region_scan");
    const bool Highlight = Channel == TEXT("visual") && BehaviorId == TEXT("ot.industrial.target_highlight");
    if (Scan || Highlight)
    {
        if (auto* Previous = Twin->FindComponentByClass<UIndustrialPresentationComponent>())
            Previous->Apply(Channel, Scan ? TEXT("safe.none") : TEXT("safe.visible"));
        if (Highlight) if (auto* Previous = Twin->FindComponentByClass<UBeltMaterialComponent>()) Previous->ResetMaterials();
        if (!Effects)
        {
            Effects = NewObject<UDeviceEffectsComponent>(Twin, NAME_None, RF_Transient);
            Twin->AddInstanceComponent(Effects);
            Effects->RegisterComponent();
        }
        return Scan ? Effects->StartScan(Params) : Effects->StartHighlight(Params);
    }
    if (Effects && Channel == TEXT("fx")) Effects->StopScan();
    if (Effects && Channel == TEXT("visual")) Effects->StopHighlight();

    auto* Belt = Twin->FindComponentByClass<UBeltMaterialComponent>();
    if (Channel == TEXT("visual"))
    {
        if (BehaviorId == TEXT("material.belt_scroll"))
        {
            if (auto* Old = Twin->FindComponentByClass<UIndustrialPresentationComponent>()) Old->Apply(Channel, TEXT("safe.visible"));
            if (!Belt)
            {
                Belt = NewObject<UBeltMaterialComponent>(Twin, TEXT("OT_BeltMaterial"), RF_Transient);
                Twin->AddInstanceComponent(Belt);
                Belt->RegisterComponent();
            }
            return Belt->Apply(Params);
        }
        if (Belt) Belt->ResetMaterials();
    }
    auto* Motion = Twin->FindComponentByClass<UBasicMotionComponent>();
    if (Channel == TEXT("animation"))
    {
        if (BehaviorId.StartsWith(TEXT("motion.")))
        {
            if (auto* Old = Twin->FindComponentByClass<UIndustrialPresentationComponent>()) Old->Apply(Channel, TEXT("safe.idle"));
            if (!Motion)
            {
                Motion = NewObject<UBasicMotionComponent>(Twin, TEXT("OT_BasicMotion"), RF_Transient);
                Twin->AddInstanceComponent(Motion);
                Motion->RegisterComponent();
            }
            const bool bApplied = Motion->Apply(BehaviorId, Params);
            UE_LOG(LogTemp, Log, TEXT("[OT-Motion] instance=%s behavior=%s accepted=%d"), *Twin->GetInstanceId(), *BehaviorId, bApplied);
            return bApplied;
        }
        if (Motion) Motion->ResetMotion();
    }
    auto* Component = Twin->FindComponentByClass<UIndustrialPresentationComponent>();
    if (!Component && BehaviorId.StartsWith(TEXT("safe."))) return true;
    if (!Component)
    {
        Component = NewObject<UIndustrialPresentationComponent>(Twin, TEXT("OT_IndustrialPresentation"), RF_Transient);
        Twin->AddInstanceComponent(Component);
        Component->RegisterComponent();
    }
    const bool bApplied = Component->Apply(Channel, BehaviorId);
    UE_LOG(LogTemp, Log, TEXT("[OT-Presentation] instance=%s channel=%s behavior=%s applied=%d"),
        *Twin->GetInstanceId(), *Channel, *BehaviorId, bApplied);
    return bApplied;
}

IMPLEMENT_MODULE(FOntoTwinIndustrialBehaviorModule, OntoTwinIndustrialBehavior)
