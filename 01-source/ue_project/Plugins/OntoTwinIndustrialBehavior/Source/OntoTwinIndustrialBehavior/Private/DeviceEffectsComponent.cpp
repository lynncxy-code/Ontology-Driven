#include "DeviceEffectsComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"

namespace
{
float Number(const TSharedPtr<FJsonObject> &P, const TCHAR *Key, float Default, float Min, float Max)
{
    double V;
    return P && P->TryGetNumberField(Key, V) && FMath::IsFinite(V) && V >= Min && V <= Max
               ? static_cast<float>(V)
               : Default;
}
FString Choice(const TSharedPtr<FJsonObject> &P, const TCHAR *Key)
{
    FString V;
    if (P)
        P->TryGetStringField(Key, V);
    return V;
}
template <class T> T *EffectAsset(const TCHAR *Name)
{
    return LoadObject<T>(nullptr,
                         *FString::Printf(TEXT("/OntoTwinIndustrialBehavior/Effects/%s.%s"), Name, Name));
}
} // namespace

void UDeviceScanQueue::Enter(UDeviceEffectsComponent *Request)
{
    Requests.Remove(Request);
    Requests.Add(Request);
    Refresh();
}
void UDeviceScanQueue::Leave(UDeviceEffectsComponent *Request)
{
    Requests.Remove(Request);
    Refresh();
}
void UDeviceScanQueue::Refresh()
{
    Requests.RemoveAll([](const auto &R) { return !R.IsValid(); });
    UDeviceEffectsComponent *Next = nullptr;
    for (int32 I = Requests.Num() - 1; I >= 0; --I)
        if (Requests[I]->CanDisplayScan())
        {
            Next = Requests[I].Get();
            break;
        }
    if (Active.Get() == Next)
        return;
    if (Active.IsValid())
        Active->SetScanVisible(false);
    Active = Next;
    if (Next)
        Next->SetScanVisible(true);
}

UDeviceEffectsComponent::UDeviceEffectsComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
}
void UDeviceEffectsComponent::UpdateTick()
{
    SetComponentTickEnabled(bVisible || (bScanRequested && Wait > 0) || Tint != nullptr);
}
bool UDeviceEffectsComponent::StartScan(const TSharedPtr<FJsonObject> &P)
{
    StopScan();
    bGreen = Choice(P, TEXT("style")) == TEXT("rehearsal");
    auto *Material = EffectAsset<UMaterialInterface>(bGreen ? TEXT("MI_RehearsalFloorScan_Green")
                                                            : TEXT("MI_Go2NativeFloorScan"));
    auto *System = EffectAsset<UNiagaraSystem>(TEXT("N_Scan01"));
    Collection = EffectAsset<UMaterialParameterCollection>(TEXT("MPC_Scan"));
    auto *Queue = GetWorld()->GetSubsystem<UDeviceScanQueue>();
    auto *Owner = GetOwner();
    if (!System || !Material || !Collection || !Queue || !Owner->GetRootComponent())
        return false;
    Radius = 100 * Number(P, TEXT("radius"), 8.5f, 1, 50);
    Sweep = Number(P, TEXT("duration"), 4, .5f, 30);
    Interval = Number(P, TEXT("interval"), 0, 0, 120);
    if (Interval < 2)
        Interval = 0;
    bHold = Choice(P, TEXT("finish")) == TEXT("hold");
    if (!Grid)
    {
        Grid = NewObject<UNiagaraComponent>(Owner, NAME_None, RF_Transient);
        Grid->SetAutoActivate(false);
        Grid->SetupAttachment(Owner->GetRootComponent());
        Grid->SetUsingAbsoluteLocation(true);
        Owner->AddInstanceComponent(Grid);
        Grid->RegisterComponent();
        Filter = NewObject<UPostProcessComponent>(Owner, NAME_None, RF_Transient);
        Filter->SetupAttachment(Owner->GetRootComponent());
        Filter->bUnbound = true;
        Filter->Priority = 100;
        Filter->BlendWeight = 0;
        Owner->AddInstanceComponent(Filter);
        Filter->RegisterComponent();
    }
    Grid->SetAsset(System);
    Grid->SetVariableFloat(TEXT("User.DotsGrid Size"), bGreen ? 8.5f : 8.f);
    Grid->SetVariableFloat(TEXT("User.Lines Size"), 10.f);
    Grid->SetVariableLinearColor(TEXT("User.DotsGrid Color"), bGreen ? FLinearColor(.08f, .98f, .58f, .30f)
                                                                     : FLinearColor(0, .5f, 1, .2f));
    for (const TCHAR *Key :
         {TEXT("User.GridLines ColorX"), TEXT("User.GridLines ColorY"), TEXT("User.GridLines ColorZ")})
        Grid->SetVariableLinearColor(Key, bGreen ? FLinearColor(.05f, .88f, .50f, .038f)
                                                 : FLinearColor(0, .5f, 1, .02f));
    Floor = UMaterialInstanceDynamic::Create(Material, this);
    Filter->Settings.AddBlendable(Floor, 1.f);
    Origin = Owner->GetActorLocation();
    Elapsed = Wait = 0;
    bScanRequested = true;
    Queue->Enter(this);
    return true;
}
void UDeviceEffectsComponent::DrawScan()
{
    const float T = FMath::Min(Elapsed / Sweep, 1.f);
    Floor->SetVectorParameterValue(TEXT("Origin"), FLinearColor(Origin));
    Floor->SetVectorParameterValue(TEXT("FloorMin"), FLinearColor(Origin - FVector(Radius)));
    Floor->SetVectorParameterValue(TEXT("FloorMax"), FLinearColor(Origin + FVector(Radius)));
    Floor->SetScalarParameterValue(TEXT("Radius"), Radius * T);
    auto *M = GetWorld()->GetParameterCollectionInstance(Collection);
    M->SetVectorParameterValue(TEXT("Location"), FLinearColor(Origin));
    M->SetScalarParameterValue(TEXT("Range"), bGreen ? Radius * T : Radius);
    M->SetScalarParameterValue(TEXT("GridCellSize"), bGreen ? 480.f : 500.f);
    M->SetScalarParameterValue(TEXT("PulseSpeed"), bGreen ? .85f : 1.f);
    M->SetScalarParameterValue(TEXT("NormalizedTime"), T);
    M->SetScalarParameterValue(TEXT("FadeIn"), 1);
    M->SetScalarParameterValue(TEXT("FadeOut"), 0);
}
void UDeviceEffectsComponent::SetScanVisible(bool On)
{
    if (On == bVisible)
        return;
    auto *World = GetWorld();
    if (auto *M = World && Collection ? World->GetParameterCollectionInstance(Collection) : nullptr)
    {
        if (On)
        {
            bSavedOrigin = M->GetVectorParameterValue(TEXT("Location"), SavedOrigin);
            for (const TCHAR *Key : {TEXT("Range"), TEXT("GridCellSize"), TEXT("PulseSpeed"),
                                     TEXT("NormalizedTime"), TEXT("FadeIn"), TEXT("FadeOut")})
            {
                float Was = 0;
                if (M->GetScalarParameterValue(Key, Was))
                    SavedScalars.Add(Key, Was);
            }
        }
        else
        {
            if (bSavedOrigin)
                M->SetVectorParameterValue(TEXT("Location"), SavedOrigin);
            for (const auto &Pair : SavedScalars)
                M->SetScalarParameterValue(Pair.Key, Pair.Value);
            SavedScalars.Reset();
            bSavedOrigin = false;
        }
    }
    bVisible = On;
    if (On)
    {
        DrawScan();
        Grid->SetWorldLocation(Origin);
        Grid->Activate(true);
        Filter->BlendWeight = 1;
    }
    else
    {
        if (Grid)
            Grid->DeactivateImmediate();
        if (Filter)
            Filter->BlendWeight = 0;
    }
    UpdateTick();
}
void UDeviceEffectsComponent::StopScan()
{
    bScanRequested = false;
    Wait = 0;
    if (bVisible)
        SetScanVisible(false);
    if (GetWorld())
        if (auto *Q = GetWorld()->GetSubsystem<UDeviceScanQueue>())
            Q->Leave(this);
    if (Filter && Floor)
        Filter->Settings.RemoveBlendable(Floor);
    Floor = nullptr;
    UpdateTick();
}

bool UDeviceEffectsComponent::StartHighlight(const TSharedPtr<FJsonObject> &P)
{
    StopHighlight();
    const FString Key = Choice(P, TEXT("color"));
    bBreathing = Key == TEXT("blocked");
    const bool Found = !bBreathing && Key != TEXT("granted");
    auto *Base = EffectAsset<UMaterialInterface>(Found ? TEXT("MI_TranslucentOverlay")
                                                       : TEXT("MI_TranslucentOverlay_2"));
    if (!Base)
        return false;
    Tint = UMaterialInstanceDynamic::Create(Base, this);
    TintColor = Found ? FLinearColor(3, 27, 7.5f)
                      : (bBreathing ? FLinearColor(12, .18f, .05f) : FLinearColor(.08f, 6.2f, 2));
    Tint->SetVectorParameterValue(TEXT("Colour"), TintColor);
    Tint->SetScalarParameterValue(TEXT("Exponent"), Found ? 1.35f : 3.2f);
    TintAge = MeshPoll = 0;
    TintDuration = Number(P, TEXT("duration"), 0, 0, 600);
    AttachOverlay();
    UpdateTick();
    return true;
}
void UDeviceEffectsComponent::AttachOverlay()
{
    TInlineComponentArray<UStaticMeshComponent *> Meshes;
    GetOwner()->GetComponents(Meshes, true);
    for (auto *M : Meshes)
        if (IsValid(M) && M->GetStaticMesh() && !M->ComponentHasTag(TEXT("OntoTwinPresentation")) &&
            !Originals.Contains(M))
        {
            Originals.Add(M, M->GetOverlayMaterial());
            M->SetOverlayMaterial(Tint);
        }
}
void UDeviceEffectsComponent::StopHighlight()
{
    for (auto &Pair : Originals)
        if (IsValid(Pair.Key) && Pair.Key->GetOverlayMaterial() == Tint)
            Pair.Key->SetOverlayMaterial(Pair.Value);
    Originals.Reset();
    Tint = nullptr;
    UpdateTick();
}
void UDeviceEffectsComponent::TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction *Fn)
{
    Super::TickComponent(Dt, Type, Fn);
    if (Tint)
    {
        TintAge += Dt;
        MeshPoll += Dt;
        if (TintDuration > 0 && TintAge >= TintDuration)
            StopHighlight();
        else
        {
            if (MeshPoll >= .25f)
            {
                AttachOverlay();
                MeshPoll = 0;
            }
            if (bBreathing)
                Tint->SetVectorParameterValue(TEXT("Colour"),
                                              TintColor * (.75f + .25f * FMath::Cos(TintAge * PI)));
        }
    }
    if (Wait > 0)
    {
        Wait = FMath::Max(0.f, Wait - Dt);
        if (Wait == 0)
        {
            Elapsed = 0;
            Origin = GetOwner()->GetActorLocation();
            GetWorld()->GetSubsystem<UDeviceScanQueue>()->Refresh();
            if (bVisible)
            {
                Grid->SetWorldLocation(Origin);
                DrawScan();
            }
        }
        return;
    }
    if (!bVisible)
        return;
    Elapsed = FMath::Min(Sweep, Elapsed + Dt);
    DrawScan();
    if (Elapsed >= Sweep)
    {
        if (Interval > 0)
        {
            Wait = Interval;
            if (!bHold)
                GetWorld()->GetSubsystem<UDeviceScanQueue>()->Refresh();
            UpdateTick();
        }
        else if (!bHold)
            StopScan();
    }
}
void UDeviceEffectsComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    StopScan();
    StopHighlight();
    Super::EndPlay(Reason);
}
