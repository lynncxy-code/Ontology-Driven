// ============================================================================
// PCBWorkerSyncComponent.cpp
//
// v3 - 直接播放动画序列，彻底绕开 AnimBP 状态机
// ============================================================================

#include "PCBWorkerSyncComponent.h"
#include "TwinLabelComponent.h"
#include "GameFramework/Actor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequence.h"
#include "UObject/ConstructorHelpers.h"
#include "Kismet/KismetMathLibrary.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

UPCBWorkerSyncComponent::UPCBWorkerSyncComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.016f; // ~60fps

    // ── 构造函数内绑定动画资产（最可靠方式，重启/重编译后永久生效）──────────
    // 路径格式：/Game/... 对应 Content/ 目录下的资产，不含扩展名
    // 修改路径后必须完整重新编译（关闭编辑器 → VS Build → 重新打开）
    static ConstructorHelpers::FObjectFinder<UAnimSequence> IdleFinder(
        TEXT("/Game/ani/5/SkeletalMeshes/Standing_Idle_Anim.Standing_Idle_Anim"));
    if (IdleFinder.Succeeded())
        IdleAnimAsset = IdleFinder.Object;

    static ConstructorHelpers::FObjectFinder<UAnimSequence> WalkFinder(
        TEXT("/Game/ani/4/SkeletalMeshes/Walking_Anim.Walking_Anim"));
    if (WalkFinder.Succeeded())
        WalkAnimAsset = WalkFinder.Object;

    static ConstructorHelpers::FObjectFinder<UAnimSequence> WorkingFinder(
        TEXT("/Game/ani/1/SkeletalMeshes/Cards_Anim.Cards_Anim"));
    if (WorkingFinder.Succeeded())
        WorkingAnimAsset = WorkingFinder.Object;
}

void UPCBWorkerSyncComponent::BeginPlay()
{
    Super::BeginPlay();

    if (AActor* Owner = GetOwner())
    {
        CachedMesh = Owner->FindComponentByClass<USkeletalMeshComponent>();
        TargetWorldLocation = Owner->GetActorLocation();
        bHasTargetLocation = false;
    }

    // ── 从软引用加载动画序列（构造函数已绑定，此处直接解引用）────────────────
    // IdleAnimAsset / WalkAnimAsset / WorkingAnimAsset 由构造函数绑定
    // 若在编辑器 Details 面板手动覆盖了某个槽，这里也会加载覆盖后的资产
    IdleAnim    = IdleAnimAsset.LoadSynchronous();
    WalkAnim    = WalkAnimAsset.LoadSynchronous();
    WorkingAnim = WorkingAnimAsset.LoadSynchronous();

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 组件已初始化"), *InstanceId);
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s]   骨骼网格体: %s"),
               *InstanceId, CachedMesh ? TEXT("✓ 找到") : TEXT("✗ 未找到!"));
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s]   IdleAnim:    %s  <- %s"),
               *InstanceId, IdleAnim    ? TEXT("✓") : TEXT("✗ 加载失败"),
               *IdleAnimAsset.ToSoftObjectPath().ToString());
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s]   WalkAnim:    %s  <- %s"),
               *InstanceId, WalkAnim    ? TEXT("✓") : TEXT("✗ 加载失败"),
               *WalkAnimAsset.ToSoftObjectPath().ToString());
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s]   WorkingAnim: %s  <- %s"),
               *InstanceId, WorkingAnim ? TEXT("✓") : TEXT("✗ 加载失败"),
               *WorkingAnimAsset.ToSoftObjectPath().ToString());
    }

    // ── 骨架兼容性强制检测（不依赖bDebugLog，T-Pose根本原因诊断）──────
    // PlayAnimation 骨架不匹配会完全静默失败，这是重启后动画丢失的根本原因
    if (CachedMesh && CachedMesh->GetSkeletalMeshAsset())
    {
        USkeleton* MeshSkeleton = CachedMesh->GetSkeletalMeshAsset()->GetSkeleton();
        FString MeshSkelName = MeshSkeleton ? MeshSkeleton->GetName() : TEXT("nullptr");

        auto CheckSkel = [&](UAnimSequence* Anim, const TCHAR* Name)
        {
            if (!Anim) return;
            USkeleton* AnimSkel = Anim->GetSkeleton();
            if (!AnimSkel)
            {
                UE_LOG(LogTemp, Error,
                    TEXT("[PCBWorker:%s] ✗ [骨架检查] %s 无骨架资产! → 动画不会播放"),
                    *InstanceId, Name);
                return;
            }
            if (!AnimSkel->IsCompatibleForEditor(MeshSkeleton))
            {
                UE_LOG(LogTemp, Error,
                    TEXT("[PCBWorker:%s] ✗ [骨架不匹配] %s → 动画骨架[%s] ≠ 网格骨架[%s]")
                    TEXT(" → 修复: 在编辑器右键该动画→Assign Skeleton，选[%s]后SaveAll"),
                    *InstanceId, Name, *AnimSkel->GetName(), *MeshSkelName, *MeshSkelName);
            }
            else
            {
                UE_LOG(LogTemp, Log,
                    TEXT("[PCBWorker:%s] ✓ [骨架匹配] %s [%s]"),
                    *InstanceId, Name, *AnimSkel->GetName());
            }
        };

        CheckSkel(IdleAnim,    TEXT("IdleAnim"));
        CheckSkel(WalkAnim,    TEXT("WalkAnim"));
        CheckSkel(WorkingAnim, TEXT("WorkingAnim"));
    }

    // 切换到 AnimationCustomMode，完全接管动画播放，不再走 AnimBP 状态机
    if (CachedMesh)
    {
        CachedMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);

        if (IdleAnim)
        {
            CachedMesh->PlayAnimation(IdleAnim, true);
            CurrentAnimPhase = EPCBAnimPhase::Idle;
            UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 初始动画 → Idle"), *InstanceId);
        }
    }

    // ── 创建头顶标签组件 ──────────────────────────────────────────────
    if (AActor* Owner = GetOwner())
    {
        FName CompName = *FString::Printf(TEXT("TwinLabel_%s"), *InstanceId);
        LabelComp = NewObject<UTwinLabelComponent>(Owner, CompName);
        if (LabelComp)
        {
            LabelComp->ZOffset    = 200.f;
            LabelComp->bBillboard = true;
            LabelComp->RegisterComponent();

            // 初始标签数据
            FTwinLabelData InitData;
            InitData.Title  = InstanceId;
            InitData.Status = TEXT("idle");
            LabelComp->SetLabelData(InitData);

            UE_LOG(LogTemp, Warning, TEXT("[PCBWorker:%s] ★ 头顶标签组件已创建"), *InstanceId);
        }
    }
}

void UPCBWorkerSyncComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                             FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    AActor* Owner = GetOwner();
    if (!Owner) return;

    FVector CurrentLoc = Owner->GetActorLocation();

    // ── 位置插值 ────────────────────────────────────────────────────
    if (bHasTargetLocation)
    {
        FVector NewLoc = FMath::VInterpConstantTo(CurrentLoc, TargetWorldLocation, DeltaTime, MoveInterpSpeed);
        Owner->SetActorLocation(NewLoc, false, nullptr, ETeleportType::None);

        // 速度计算
        float DistMoved = FVector::Dist2D(NewLoc, CurrentLoc);
        CurrentSpeed = (DeltaTime > 0.0f) ? (DistMoved / DeltaTime) : 0.0f;
        bIsCurrentlyMoving = true;

        // 旋转朝向目标
        if (RotationInterpSpeed > 0.0f)
        {
            FVector ToTarget = TargetWorldLocation - CurrentLoc;
            ToTarget.Z = 0.0f;
            if (!ToTarget.IsNearlyZero(1.0f))
            {
                FRotator TargetRot = ToTarget.GetSafeNormal().Rotation();
                TargetRot.Yaw -= 90.0f; // 模型正面偏移补偿：逆时针旋转 90°
                FRotator CurrentRot = Owner->GetActorRotation();
                FRotator NewRot = FMath::RInterpConstantTo(CurrentRot, TargetRot, DeltaTime, RotationInterpSpeed * 100.0f);
                Owner->SetActorRotation(NewRot);
            }
        }

        // 到达检测
        if (FVector::Dist(NewLoc, TargetWorldLocation) < ArrivalThreshold)
        {
            bHasTargetLocation = false;
            CurrentSpeed = 0.0f;
            bIsCurrentlyMoving = false;

            // ── 到达后设置工位朝向 ────────────────────────────
            // Y > 0 的工位（pos_1, Y≈290）→ Yaw=0°
            // Y < 0 的工位（pos_2, Y≈-320）→ Yaw=180°
            if (TargetWorldLocation.Y > 0.0f)
            {
                Owner->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
            }
            else
            {
                Owner->SetActorRotation(FRotator(0.0f, 180.0f, 0.0f));
            }

            BP_OnWorkerArrived();

            if (bDebugLog)
            {
                UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 已到达目标 %s, 朝向 Yaw=%s"),
                       *InstanceId, *TargetWorldLocation.ToString(),
                       TargetWorldLocation.Y > 0.0f ? TEXT("180 (Y+)") : TEXT("0 (Y-)"));
            }
        }
    }
    else
    {
        CurrentSpeed = 0.0f;
        bIsCurrentlyMoving = false;
    }

    // ── 每帧更新动画（核心！）──────────────────────────────────────
    UpdateAnimation();
    // 头顶标签朝向由 TwinLabelComponent 自身 Tick 管理
}

// ── ITwinEntitySync 接口实现 ─────────────────────────────────────────────

void UPCBWorkerSyncComponent::ApplySnapshot(const FVector& NewLocation,
                                             const FString& Status,
                                             const FString& DisplayName,
                                             const FString& StationName)
{
    WorkerName = DisplayName;
    WorkstationName = StationName;

    if (AActor* Owner = GetOwner())
    {
        FVector SafeLocation = NewLocation;
        SafeLocation.Z = Owner->GetActorLocation().Z;

        float DistToTarget = FVector::Dist(TargetWorldLocation, SafeLocation);

        // 首次快照：必须瞬移到后端给的初始工位（不管编辑器放在哪里）
        if (!bFirstSnapshotReceived)
        {
            bFirstSnapshotReceived = true;
            Owner->SetActorLocation(SafeLocation);
            TargetWorldLocation = SafeLocation;
            bHasTargetLocation = false;

            // 初始朝向：Y>0 → Yaw=0, Y<0 → Yaw=180
            if (SafeLocation.Y > 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
            else if (SafeLocation.Y < 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 180.0f, 0.0f));
        }
        else if (bHasTargetLocation)
        {
            // ★ 正在走路途中，忽略快照的位置数据，避免和事件数据打架导致抖动
            if (bDebugLog)
                UE_LOG(LogTemp, Verbose, TEXT("[PCBWorker:%s] 正在移动中，跳过快照位置更新"), *InstanceId);
        }
        else if (DistToTarget > 10.0f) // 站着不动时，工位变了就走过去
        {
            TargetWorldLocation = SafeLocation;
            bHasTargetLocation = true;
            BP_OnWorkerStartMove(Owner->GetActorLocation(), SafeLocation);
        }

        // 站立时强制锁定正确朝向（防止被其他逻辑覆盖）
        if (!bHasTargetLocation)
        {
            if (SafeLocation.Y > 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
            else if (SafeLocation.Y < 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 180.0f, 0.0f));
        }
    }

    UpdateStatus(Status, StationName);
    RefreshLabel(); // 快照时也刷新 UI（因为 UpdateStatus 可能被跳过）

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 快照已应用 | 姓名:%s | 状态:%s | 工位:%s | 位置:%s"),
               *InstanceId, *WorkerName, *WorkerStatus, *WorkstationName, *NewLocation.ToString());
    }
}

void UPCBWorkerSyncComponent::ApplyPositionChanged(const FVector& FromLocation,
                                                    const FVector& ToLocation)
{
    FVector SafeTarget = ToLocation;
    if (AActor* Owner = GetOwner())
    {
        SafeTarget.Z = Owner->GetActorLocation().Z;
    }

    TargetWorldLocation = SafeTarget;
    bHasTargetLocation = true;

    FVector SafeFrom = FromLocation;
    if (AActor* Owner = GetOwner())
    {
        SafeFrom.Z = Owner->GetActorLocation().Z;
    }
    BP_OnWorkerStartMove(SafeFrom, SafeTarget);

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 开始移动 → %s"),
               *InstanceId, *SafeTarget.ToString());
    }
}

void UPCBWorkerSyncComponent::ApplyStateChanged(const FString& NewStatus,
                                                  const FString& StationName)
{
    UpdateStatus(NewStatus, StationName);

    // 状态变化时（比如转入工作或休息），如果当前没有在移动，就修正朝向
    if (!bHasTargetLocation)
    {
        if (AActor* Owner = GetOwner())
        {
            FVector Loc = Owner->GetActorLocation();
            if (Loc.Y > 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
            else if (Loc.Y < 0.0f)
                Owner->SetActorRotation(FRotator(0.0f, 180.0f, 0.0f));
        }
    }

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 状态变化 → %s | 工位:%s"),
               *InstanceId, *WorkerStatus, *WorkstationName);
    }
}

// ── 私有辅助 ─────────────────────────────────────────────────────────────

void UPCBWorkerSyncComponent::UpdateStatus(const FString& NewStatus, const FString& StationName)
{
    WorkstationName = StationName;

    if (NewStatus == LastStatus) return;

    WorkerStatus = NewStatus;
    LastStatus = NewStatus;

    OnStatusChanged.Broadcast(NewStatus);
    BP_OnWorkerStatusChanged(NewStatus);

    // 刷新头顶 UI
    RefreshLabel();

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBWorker:%s] 状态更新: %s (将在下帧切换动画)"),
               *InstanceId, *NewStatus);
    }
}

// ══════════════════════════════════════════════════════════════════════════
// v3 动画驱动 — 直接 PlayAnimation，彻底绕开 AnimBP 变量名问题
//
// 优先级：
//   1. bIsCurrentlyMoving == true  → Walk 动画（循环）
//   2. WorkerStatus == "working"   → Working/Jump 动画（循环）
//   3. 其他                         → Idle 动画（循环）
// ══════════════════════════════════════════════════════════════════════════

void UPCBWorkerSyncComponent::UpdateAnimation()
{
    if (!CachedMesh) return;

    EPCBAnimPhase DesiredPhase;

    // 移动状态优先级最高
    if (bIsCurrentlyMoving)
    {
        DesiredPhase = EPCBAnimPhase::Walking;
    }
    else if (WorkerStatus.Equals(TEXT("working"), ESearchCase::IgnoreCase))
    {
        DesiredPhase = EPCBAnimPhase::Working;
    }
    else
    {
        DesiredPhase = EPCBAnimPhase::Idle;
    }

    // 只在阶段切换时才重新播放动画（避免每帧重置导致卡第一帧）
    if (DesiredPhase == CurrentAnimPhase) return;

    CurrentAnimPhase = DesiredPhase;

    switch (DesiredPhase)
    {
    case EPCBAnimPhase::Walking:
        if (WalkAnim)
        {
            CachedMesh->PlayAnimation(WalkAnim, true);
            if (bDebugLog)
                UE_LOG(LogTemp, Warning, TEXT("[PCBWorker:%s] ▶ 动画切换 → Walk"), *InstanceId);
        }
        break;

    case EPCBAnimPhase::Working:
        if (WorkingAnim)
        {
            CachedMesh->PlayAnimation(WorkingAnim, true);
            if (bDebugLog)
                UE_LOG(LogTemp, Warning, TEXT("[PCBWorker:%s] ▶ 动画切换 → Working"), *InstanceId);
        }
        break;

    case EPCBAnimPhase::Idle:
    default:
        if (IdleAnim)
        {
            CachedMesh->PlayAnimation(IdleAnim, true);
            if (bDebugLog)
                UE_LOG(LogTemp, Warning, TEXT("[PCBWorker:%s] ▶ 动画切换 → Idle"), *InstanceId);
        }
        break;
    }
}

// ── 头顶标签刷新（委托给 TwinLabelComponent）─────────────────────────────────

void UPCBWorkerSyncComponent::RefreshLabel()
{
    if (!LabelComp) return;

    // 将状态翻译为中文或拼接
    FString StatusText = TEXT("未知状态");
    if (WorkerStatus.Equals(TEXT("working"), ESearchCase::IgnoreCase))
    {
        StatusText = TEXT("正常工作");
    }
    else if (WorkerStatus.Equals(TEXT("idle"), ESearchCase::IgnoreCase))
    {
        StatusText = TEXT("待机空闲");
    }
    else if (WorkerStatus.Equals(TEXT("warning"), ESearchCase::IgnoreCase))
    {
        StatusText = TEXT("设备警告");
    }
    else if (WorkerStatus.Equals(TEXT("offline"), ESearchCase::IgnoreCase))
    {
        StatusText = TEXT("离线");
    }

    FTwinLabelData Data;
    // 主标题："FW-01 张明"（WorkerName 来自 metadata.name，空时兜底显示 InstanceId）
    const FString DisplayName = WorkerName.IsEmpty() ? InstanceId : WorkerName;
    Data.Title    = FString::Printf(TEXT("%s %s"), *InstanceId, *DisplayName);
    // 副标题：工位 + 状态，如 "X300 驱动板工位, 正常工作"
    Data.Subtitle = FString::Printf(TEXT("%s, %s"), *WorkstationName, *StatusText);
    Data.Status   = WorkerStatus;
    
    LabelComp->SetLabelData(Data);
}

// UpdateLabelBillboard 已由 TwinLabelComponent 内部的 Tick 自动完成，无需在此实现

