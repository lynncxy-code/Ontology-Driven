// ============================================================================
// PCBWorkerSyncComponent.h
//
// PCB 车间工人同步组件
//
// 使用说明：
//   1. 将此组件挂载到场景中的 SK_Charactor Actor 上
//   2. 在 Details 面板设置 InstanceId（如 "FW-01"）
//   3. 场景中必须有一个 APCBWorkerManager Actor 负责轮询和分发
//
// 动画驱动策略（v3 直接播放动画序列，绕开 AnimBP 状态机）：
//   - 移动中  → 循环播放 WalkAnim
//   - working → 循环播放 WorkingAnim (Jump_Loop)
//   - idle    → 循环播放 IdleAnim
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TwinEntitySyncBase.h"
#include "TwinLabelComponent.h"     // 统一头顶标签组件
#include "PCBWorkerSyncComponent.generated.h"

class UAnimSequence;

// 状态变化委托（蓝图可绑定）
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPCBWorkerStatusChanged, const FString&, NewStatus);

/**
 * 当前播放的动画阶段
 */
UENUM()
enum class EPCBAnimPhase : uint8
{
    Idle,
    Walking,
    Working,
};

/**
 * UPCBWorkerSyncComponent
 *
 * 实现 ITwinEntitySync 接口，驱动单个工人 Actor 的空间移动和状态切换。
 * 挂载到 SkeletalMeshActor 上使用。
 */
UCLASS(ClassGroup=(PCBDigitalTwin), meta=(BlueprintSpawnableComponent),
       DisplayName="PCB工人同步组件")
class TEST0316_API UPCBWorkerSyncComponent : public UActorComponent, public ITwinEntitySync
{
    GENERATED_BODY()

public:
    UPCBWorkerSyncComponent();

protected:
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction* ThisTickFunction) override;

    // ═══════════════════════════════════════════════════════════════
    // 可在编辑器 Details 面板配置
    // ═══════════════════════════════════════════════════════════════

    /** 对应上游 instanceId，例如 "FW-01"，必须填写 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|身份",
              meta=(DisplayName="工人实例ID (如 FW-01)"))
    FString InstanceId;

    /** Actor 移动到目标位置的匀速移动速度（cm/s） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|移动",
              meta=(DisplayName="移动速度(cm/s)", ClampMin="10.0", ClampMax="1000.0"))
    float MoveInterpSpeed = 150.0f;

    /** Actor 面向目标方向的旋转插值速度，0 = 不自动旋转 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|移动",
              meta=(DisplayName="旋转插值速度 (0=禁用)", ClampMin="0.0", ClampMax="20.0"))
    float RotationInterpSpeed = 5.0f;

    /** 是否在 PIE 启动时打印调试日志 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|调试",
              meta=(DisplayName="启用调试日志"))
    bool bDebugLog = true;

    // ═══════════════════════════════════════════════════════════════
    // 动画资产引用（在编辑器 Details 面板直接拖拽赋值，重启后不会丢失）
    // ═══════════════════════════════════════════════════════════════

    /**
     * Idle 动画序列（待机）
     * 用法：在 Details 面板将 Content Browser 中的 AnimSequence 资产拖到此处
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|动画资产",
              meta=(DisplayName="Idle 动画", AllowedClasses="AnimSequence"))
    TSoftObjectPtr<UAnimSequence> IdleAnimAsset;

    /**
     * Walk 动画序列（移动时播放）
     * 用法：拖拽对应的行走 AnimSequence 资产到此处
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|动画资产",
              meta=(DisplayName="Walk 动画", AllowedClasses="AnimSequence"))
    TSoftObjectPtr<UAnimSequence> WalkAnimAsset;

    /**
     * Working 动画序列（工作中播放）
     * 用法：拖拽对应的工作 AnimSequence 资产到此处
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB工人|动画资产",
              meta=(DisplayName="Working 动画", AllowedClasses="AnimSequence"))
    TSoftObjectPtr<UAnimSequence> WorkingAnimAsset;

    // ═══════════════════════════════════════════════════════════════
    // 只读状态（蓝图可读）
    // ═══════════════════════════════════════════════════════════════

    /** 当前工人姓名 */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|状态", meta=(DisplayName="姓名"))
    FString WorkerName;

    /** 当前工人状态："working" 或 "idle" */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|状态", meta=(DisplayName="当前状态"))
    FString WorkerStatus;

    /** 当前工位名称 */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|状态", meta=(DisplayName="当前工位"))
    FString WorkstationName;

    /** 当前目标世界坐标（调试用） */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|状态", meta=(DisplayName="目标位置"))
    FVector TargetWorldLocation;

    /** 当前实时移动速度（cm/s） */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|动画驱动", meta=(DisplayName="当前速度(cm/s)"))
    float CurrentSpeed = 0.0f;

    /** 是否正在移动 */
    UPROPERTY(BlueprintReadOnly, Category="PCB工人|动画驱动", meta=(DisplayName="正在移动"))
    bool bIsCurrentlyMoving = false;

    // ═══════════════════════════════════════════════════════════════
    // 蓝图事件
    // ═══════════════════════════════════════════════════════════════

    UPROPERTY(BlueprintAssignable, Category="PCB工人|事件")
    FOnPCBWorkerStatusChanged OnStatusChanged;

    UFUNCTION(BlueprintImplementableEvent, Category="PCB工人|动画",
              meta=(DisplayName="当工人状态改变 (Override Me)"))
    void BP_OnWorkerStatusChanged(const FString& NewStatus);

    UFUNCTION(BlueprintImplementableEvent, Category="PCB工人|动画",
              meta=(DisplayName="当工人开始移动 (Override Me)"))
    void BP_OnWorkerStartMove(const FVector& FromLocation, const FVector& ToLocation);

    UFUNCTION(BlueprintImplementableEvent, Category="PCB工人|动画",
              meta=(DisplayName="当工人到达目标 (Override Me)"))
    void BP_OnWorkerArrived();

    // ═══════════════════════════════════════════════════════════════
    // ITwinEntitySync 接口实现
    // ═══════════════════════════════════════════════════════════════

    virtual FString GetInstanceId() const override { return InstanceId; }

    virtual void ApplySnapshot(const FVector& NewLocation,
                               const FString& Status,
                               const FString& DisplayName,
                               const FString& StationName) override;

    virtual void ApplyPositionChanged(const FVector& FromLocation,
                                      const FVector& ToLocation) override;

    virtual void ApplyStateChanged(const FString& NewStatus,
                                   const FString& StationName) override;

private:
    bool bHasTargetLocation = false;
    bool bFirstSnapshotReceived = false;  // 首次快照标志：第一次收到后端数据时必须瞬移
    static constexpr float ArrivalThreshold = 10.0f;
    FString LastStatus;

    /** 缓存骨骼网格体组件 */
    UPROPERTY()
    USkeletalMeshComponent* CachedMesh = nullptr;

    /** 加载好的动画序列资产 */
    UPROPERTY()
    UAnimSequence* IdleAnim = nullptr;
    UPROPERTY()
    UAnimSequence* WalkAnim = nullptr;
    UPROPERTY()
    UAnimSequence* WorkingAnim = nullptr;

    /** 当前正在播放的动画阶段，避免重复切换 */
    EPCBAnimPhase CurrentAnimPhase = EPCBAnimPhase::Idle;

    /** 头顶标签组件（统一样式） */
    UPROPERTY()
    UTwinLabelComponent* LabelComp = nullptr;

    /** 更新状态并触发事件 */
    void UpdateStatus(const FString& NewStatus, const FString& StationName);

    /** 根据当前移动/工作状态直接播放对应动画序列 */
    void UpdateAnimation();

    /** 刷新头顶标签内容 */
    void RefreshLabel();
};
