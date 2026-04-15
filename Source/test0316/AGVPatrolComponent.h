// ============================================================================
// AGVPatrolComponent.h
//
// AGV 小车巡逻组件（双模式）
//
// 模式一（余弦缓动算法，默认）：
//   无外部数据时，按本地余弦缓动算法在初始坐标附近往返运动。
//   适用于无仿真日志时的快速预览。
//
// 模式二（CSV 仿真日志回放）：
//   由 UAGVSimLogLoader 注入帧序列后自动切换。
//   按帧时间戳做线性位置插值 + Slerp 旋转插值，忠实还原仿真轨迹。
//
// 版本：OntoTwin 2.8.1
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AGVSimLogLoader.h"   // FAgvFrame 定义
#include "AGVPatrolComponent.generated.h"

/** 组件当前驱动模式 */
UENUM(BlueprintType)
enum class EAGVDriveMode : uint8
{
    /** 本地余弦缓动算法往返 */
    AlgorithmPatrol  UMETA(DisplayName="算法巡逻（余弦缓动）"),
    /** CSV 仿真日志回放 */
    SimLogPlayback   UMETA(DisplayName="仿真日志回放（CSV）"),
};

UCLASS(ClassGroup=(AGVDigitalTwin), meta=(BlueprintSpawnableComponent),
       DisplayName="AGV巡逻组件")
class TEST0316_API UAGVPatrolComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAGVPatrolComponent();

protected:
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction* ThisTickFunction) override;

    // ─────────────────────────────────────────────────────────────────────
    // ── 通用属性
    // ─────────────────────────────────────────────────────────────────────

    /**
     * AGV 唯一编号，与 CSV 中 serial 字段完全匹配。
     * 例：agvfac000000001n01
     * UAGVSimLogLoader 依据此字段注入对应的帧序列。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|身份",
              meta=(DisplayName="AGV 序号 (serial)"))
    FString AgvSerial;

    /** 是否打印调试日志 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|调试",
              meta=(DisplayName="启用调试日志"))
    bool bDebugLog = false;

    // ─────────────────────────────────────────────────────────────────────
    // ── 模式一：算法巡逻参数
    // ─────────────────────────────────────────────────────────────────────

    /** 巡逻总距离（虚幻单位，30 m = 3000 cm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|算法巡逻",
              meta=(DisplayName="巡逻距离(cm)", ClampMin="100.0"))
    float PatrolDistance = 3000.0f;

    /** 完整来回一次所需时间（秒），为 0 时自动防除零跳过 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|算法巡逻",
              meta=(DisplayName="来回周期(秒)", ClampMin="0.1"))
    float CycleTime = 10.0f;

    /** 巡逻轴向（默认 +Y 轴），支持自定义斜向巡逻 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|算法巡逻",
              meta=(DisplayName="巡逻轴向"))
    FVector PatrolAxis = FVector(0.0f, 1.0f, 0.0f);

    // ─────────────────────────────────────────────────────────────────────
    // ── 模式二：CSV 回放参数
    // ─────────────────────────────────────────────────────────────────────

    /**
     * 回放结束后是否循环（从第一帧重新开始）。
     * 关闭后在最后一帧停止，小车保持静止。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|仿真回放",
              meta=(DisplayName="循环回放"))
    bool bLoopPlayback = true;

    /**
     * CSV 回放时是否锁定 Z 轴（使用 Actor 初始放置高度，忽略 CSV 中的 positionZ）。
     * 默认开启：CSV 仿真坐标通常以地面为 0，而 UE 场景中 AGV 模型原点可能偏高。
     * 关闭后将严格按照 CSV 的 positionZ 设置高度。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV|仿真回放",
              meta=(DisplayName="锁定Z轴到初始高度"))
    bool bPreserveActorZ = true;

    // ─────────────────────────────────────────────────────────────────────
    // ── 只读状态（蓝图可读）
    // ─────────────────────────────────────────────────────────────────────

    /** 当前驱动模式（只读，由 InjectSimFrames 自动切换） */
    UPROPERTY(BlueprintReadOnly, Category="AGV|状态",
              meta=(DisplayName="当前驱动模式"))
    EAGVDriveMode DriveMode = EAGVDriveMode::AlgorithmPatrol;

    /** 当前是否有货 */
    UPROPERTY(BlueprintReadOnly, Category="AGV|状态",
              meta=(DisplayName="是否有货"))
    bool bHasCargo = false;

    /** 当前偏航角（弧度） */
    UPROPERTY(BlueprintReadOnly, Category="AGV|状态",
              meta=(DisplayName="偏航角(弧度)"))
    float CurrentYaw = 0.f;

    // ─────────────────────────────────────────────────────────────────────
    // ── 公开接口（供 UAGVSimLogLoader 调用）
    // ─────────────────────────────────────────────────────────────────────

    /**
     * 注入仿真帧序列，并自动切换到 CSV 回放模式。
     * 调用后余弦缓动算法将被禁用。
     * @param Frames  已按时间升序排列的帧数组
     */
    UFUNCTION(BlueprintCallable, Category="AGV|仿真回放",
              meta=(DisplayName="注入仿真帧序列"))
    void InjectSimFrames(const TArray<FAgvFrame>& Frames);

    /**
     * 回到算法巡逻模式，清空已注入的帧序列。
     */
    UFUNCTION(BlueprintCallable, Category="AGV|仿真回放",
              meta=(DisplayName="切换回算法巡逻模式"))
    void ResetToAlgorithmMode();

private:
    // ── 模式一内部状态 ───────────────────────────────────────────────────
    FVector InitialLocation;
    float   RunningTime = 0.f;

    // ── 模式二内部状态 ───────────────────────────────────────────────────
    TArray<FAgvFrame> SimFrames;     // 注入的帧序列
    float             PlaybackTime = 0.f;  // 自回放开始的累计时间

    // ── 内部 Tick 实现 ────────────────────────────────────────────────────

    /** 模式一：执行余弦缓动位移 */
    void TickAlgorithmPatrol(float DeltaTime, AActor* Owner);

    /** 模式二：执行 CSV 帧插值回放 */
    void TickSimLogPlayback(float DeltaTime, AActor* Owner);

    /**
     * 二分查找：返回 SimFrames 中 Time <= TargetTime 的最大索引。
     * 用于 O(logN) 定位当前帧。
     */
    int32 BinarySearchFrame(float TargetTime) const;
};
