// ============================================================================
// AGVPatrolComponent.cpp
// ============================================================================

#include "AGVPatrolComponent.h"
#include "GameFramework/Actor.h"
#include "Math/UnrealMathUtility.h"

UAGVPatrolComponent::UAGVPatrolComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    RunningTime  = 0.f;
    PlaybackTime = 0.f;
}

void UAGVPatrolComponent::BeginPlay()
{
    Super::BeginPlay();

    AActor* Owner = GetOwner();
    if (Owner)
    {
        InitialLocation = Owner->GetActorLocation();
    }

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log,
               TEXT("[AGVPatrol] BeginPlay → serial=%s  初始坐标=%s"),
               *AgvSerial,
               *InitialLocation.ToString());
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tick 分发
// ─────────────────────────────────────────────────────────────────────────────

void UAGVPatrolComponent::TickComponent(float DeltaTime, ELevelTick TickType,
                                        FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    AActor* Owner = GetOwner();
    if (!Owner) return;

    switch (DriveMode)
    {
    case EAGVDriveMode::AlgorithmPatrol:
        TickAlgorithmPatrol(DeltaTime, Owner);
        break;

    case EAGVDriveMode::SimLogPlayback:
        TickSimLogPlayback(DeltaTime, Owner);
        break;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 模式一：余弦缓动算法巡逻
// ─────────────────────────────────────────────────────────────────────────────

void UAGVPatrolComponent::TickAlgorithmPatrol(float DeltaTime, AActor* Owner)
{
    if (CycleTime <= 0.f) return;

    RunningTime += DeltaTime;

    // (1 - cos(θ)) / 2：0→1→0 的平滑缓动，归一化到 [0, 1]
    const float Phase       = (RunningTime / CycleTime) * PI * 2.0f;
    const float OffsetScale = (1.0f - FMath::Cos(Phase)) * 0.5f;

    const FVector NewLocation =
        InitialLocation + (PatrolAxis.GetSafeNormal() * PatrolDistance * OffsetScale);

    Owner->SetActorLocation(NewLocation);
}

// ─────────────────────────────────────────────────────────────────────────────
// 模式二：CSV 仿真日志回放
// ─────────────────────────────────────────────────────────────────────────────

void UAGVPatrolComponent::TickSimLogPlayback(float DeltaTime, AActor* Owner)
{
    if (SimFrames.Num() == 0) return;

    const float StartTime  = SimFrames[0].Time;
    const float EndTime    = SimFrames.Last().Time;
    const float TotalDur   = EndTime - StartTime;

    PlaybackTime += DeltaTime;

    // ── 循环或停止处理 ────────────────────────────────────────────────────
    if (TotalDur > 0.f && PlaybackTime > TotalDur)
    {
        if (bLoopPlayback)
        {
            PlaybackTime = FMath::Fmod(PlaybackTime, TotalDur);
        }
        else
        {
            PlaybackTime = TotalDur;
        }
    }

    const float QueryTime = StartTime + PlaybackTime;

    // ── 二分查找当前帧索引 ────────────────────────────────────────────────
    const int32 LoIdx = BinarySearchFrame(QueryTime);

    // 只有一帧或已到末尾
    if (LoIdx < 0)
    {
        FVector Pos0 = SimFrames[0].Position;
        if (bPreserveActorZ) Pos0.Z = InitialLocation.Z;
        Owner->SetActorLocationAndRotation(Pos0, SimFrames[0].Orientation.Rotator());
        bHasCargo  = SimFrames[0].bHasCargo;
        CurrentYaw = SimFrames[0].Yaw;
        return;
    }

    if (LoIdx >= SimFrames.Num() - 1)
    {
        const FAgvFrame& Last = SimFrames.Last();
        FVector PosLast = Last.Position;
        if (bPreserveActorZ) PosLast.Z = InitialLocation.Z;
        Owner->SetActorLocationAndRotation(PosLast, Last.Orientation.Rotator());
        bHasCargo  = Last.bHasCargo;
        CurrentYaw = Last.Yaw;
        return;
    }

    // ── 相邻帧插值 ────────────────────────────────────────────────────────
    const FAgvFrame& FrameA = SimFrames[LoIdx];
    const FAgvFrame& FrameB = SimFrames[LoIdx + 1];

    const float SegDur = FrameB.Time - FrameA.Time;
    const float Alpha  = (SegDur > SMALL_NUMBER)
                       ? FMath::Clamp((QueryTime - FrameA.Time) / SegDur, 0.f, 1.f)
                       : 0.f;

    // 位置：线性插值，bPreserveActorZ 时忽略 CSV 的 Z，保留 Actor 初始高度
    FVector InterpPos = FMath::Lerp(FrameA.Position, FrameB.Position, Alpha);
    if (bPreserveActorZ) InterpPos.Z = InitialLocation.Z;

    // 旋转：球面线性插值（Slerp）
    const FQuat InterpRot = FQuat::Slerp(FrameA.Orientation, FrameB.Orientation, Alpha);

    Owner->SetActorLocationAndRotation(InterpPos, InterpRot.Rotator());

    // 货物状态取最近帧（无需插值）
    bHasCargo  = FrameA.bHasCargo;
    CurrentYaw = FMath::Lerp(FrameA.Yaw, FrameB.Yaw, Alpha);

    if (bDebugLog && FMath::IsNearlyZero(FMath::Fmod(PlaybackTime, 5.f), 0.05f))
    {
        UE_LOG(LogTemp, Log,
               TEXT("[AGVPatrol] serial=%s  T=%.1fs  Pos=%s  HasCargo=%d"),
               *AgvSerial, PlaybackTime, *InterpPos.ToString(), (int32)bHasCargo);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 公开接口
// ─────────────────────────────────────────────────────────────────────────────

void UAGVPatrolComponent::InjectSimFrames(const TArray<FAgvFrame>& Frames)
{
    if (Frames.IsEmpty())
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[AGVPatrol] InjectSimFrames：注入帧为空，忽略。serial=%s"), *AgvSerial);
        return;
    }

    SimFrames    = Frames;
    PlaybackTime = 0.f;
    DriveMode    = EAGVDriveMode::SimLogPlayback;

    UE_LOG(LogTemp, Log,
           TEXT("[AGVPatrol] 切换为 CSV 回放模式 → serial=%s  帧数=%d"),
           *AgvSerial, SimFrames.Num());
}

void UAGVPatrolComponent::ResetToAlgorithmMode()
{
    SimFrames.Empty();
    PlaybackTime = 0.f;
    RunningTime  = 0.f;
    DriveMode    = EAGVDriveMode::AlgorithmPatrol;

    UE_LOG(LogTemp, Log,
           TEXT("[AGVPatrol] 切换回算法巡逻模式 → serial=%s"), *AgvSerial);
}

// ─────────────────────────────────────────────────────────────────────────────
// 内部工具
// ─────────────────────────────────────────────────────────────────────────────

int32 UAGVPatrolComponent::BinarySearchFrame(float TargetTime) const
{
    if (SimFrames.IsEmpty()) return -1;
    if (TargetTime <= SimFrames[0].Time) return -1;
    if (TargetTime >= SimFrames.Last().Time) return SimFrames.Num() - 1;

    int32 Lo = 0;
    int32 Hi = SimFrames.Num() - 1;

    while (Lo < Hi - 1)
    {
        const int32 Mid = (Lo + Hi) / 2;
        if (SimFrames[Mid].Time <= TargetTime)
        {
            Lo = Mid;
        }
        else
        {
            Hi = Mid;
        }
    }
    return Lo;
}
