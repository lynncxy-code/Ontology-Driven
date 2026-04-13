// ============================================================================
// TwinLabelComponent.cpp
// ============================================================================

#include "TwinLabelComponent.h"
#include "Components/WidgetComponent.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/KismetMathLibrary.h"
#include "Engine/World.h"

UTwinLabelComponent::UTwinLabelComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.033f; // ~30fps Billboard 刷新，省性能
}

void UTwinLabelComponent::BeginPlay()
{
    Super::BeginPlay();

    AActor* Owner = GetOwner();
    if (!Owner) return;

    // ── 创建 WidgetComponent（不指定显式名称，由 UE 自动生成，避免跨 PIE 会话 GC 时序导致的名称类型冲突）──
    WidgetComp = NewObject<UWidgetComponent>(Owner, UWidgetComponent::StaticClass(), NAME_None);
    if (!WidgetComp) return;

    WidgetComp->SetupAttachment(Owner->GetRootComponent());
    WidgetComp->SetRelativeLocation(FVector(0.f, 0.f, ZOffset));
    WidgetComp->SetWidgetSpace(EWidgetSpace::World);

    // 卡片像素尺寸：与 TwinLabelStyle::CardWidth/CardHeight 保持一致
    // 世界空间尺寸 = DrawSize × Scale = 504×0.2 = 100.8cm 宽，180×0.2 = 36cm 高
    WidgetComp->SetDrawSize(FVector2D(504.f, 180.f));
    WidgetComp->SetRelativeScale3D(FVector(0.2f, 0.2f, 0.2f));

    // 关键：背景透明，否则 WidgetComponent 会渲染一个大白板
    WidgetComp->SetBackgroundColor(FLinearColor::Transparent);
    WidgetComp->SetBlendMode(EWidgetBlendMode::Transparent);

    WidgetComp->SetPivot(FVector2D(0.5f, 0.5f));
    WidgetComp->SetTwoSided(true);
    WidgetComp->RegisterComponent();

    // ── 创建 Widget 实例 ────────────────────────────────────────────────
    LabelWidget = CreateWidget<UTwinLabelWidget>(GetWorld(), UTwinLabelWidget::StaticClass());
    if (LabelWidget)
    {
        WidgetComp->SetWidget(LabelWidget);

        // 应用 Details 面板里设置的默认数据
        if (!DefaultData.Title.IsEmpty())
        {
            CachedData = DefaultData;
            LabelWidget->SetLabelData(CachedData);
        }
    }
}

void UTwinLabelComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                         FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (bBillboard) UpdateBillboard();
}

// ── 公开接口 ─────────────────────────────────────────────────────────────────

void UTwinLabelComponent::SetLabelData(const FTwinLabelData& InData)
{
    CachedData = InData;
    if (LabelWidget) LabelWidget->SetLabelData(InData);
}

void UTwinLabelComponent::SetTitle(const FString& InTitle)
{
    CachedData.Title = InTitle;
    if (LabelWidget) LabelWidget->SetLabelData(CachedData);
}

void UTwinLabelComponent::SetSubtitle(const FString& InSubtitle)
{
    CachedData.Subtitle = InSubtitle;
    if (LabelWidget) LabelWidget->SetLabelData(CachedData);
}

void UTwinLabelComponent::SetStatus(const FString& InStatus)
{
    CachedData.Status = InStatus;
    if (LabelWidget) LabelWidget->SetLabelData(CachedData);
}

void UTwinLabelComponent::SetBadge(const FString& InBadge)
{
    CachedData.Badge = InBadge;
    if (LabelWidget) LabelWidget->SetLabelData(CachedData);
}

void UTwinLabelComponent::SetLabelVisible(bool bVisible)
{
    if (WidgetComp) WidgetComp->SetVisibility(bVisible);
}

FTwinLabelData UTwinLabelComponent::GetLabelData() const
{
    return CachedData;
}

// ── Billboard ────────────────────────────────────────────────────────────────

void UTwinLabelComponent::UpdateBillboard()
{
    if (!WidgetComp || !WidgetComp->IsVisible()) return;

    UWorld* World = GetWorld();
    if (!World) return;

    APlayerController* PC = World->GetFirstPlayerController();
    if (!PC || !PC->PlayerCameraManager) return;

    FVector CamLoc  = PC->PlayerCameraManager->GetCameraLocation();
    FVector TextLoc = WidgetComp->GetComponentLocation();

    FRotator LookAt = UKismetMathLibrary::FindLookAtRotation(TextLoc, CamLoc);
    WidgetComp->SetWorldRotation(FRotator(0.f, LookAt.Yaw, 0.f));  // 仅锁 Yaw
}
