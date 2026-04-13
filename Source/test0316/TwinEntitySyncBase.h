// ============================================================================
// TwinEntitySyncBase.h
//
// 数字孪生实体同步基类接口
//
// 说明：
//   抽象接口，让工人、AGV 等不同类型的实体组件都能被 Manager 统一调度。
//   子类必须实现三个核心方法。
//
// 已有继承：
//   UPCBWorkerSyncComponent（工人同步）
// 预留扩展：
//   UPCBAGVSyncComponent（AGV 路径调度，待开发）
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "TwinEntitySyncBase.generated.h"

UINTERFACE(MinimalAPI, BlueprintType)
class UTwinEntitySync : public UInterface
{
    GENERATED_BODY()
};

/**
 * ITwinEntitySync
 * Manager 通过此接口驱动任意类型的实体组件，不依赖具体子类。
 */
class TEST0316_API ITwinEntitySync
{
    GENERATED_BODY()

public:
    /** 获取实体的唯一标识（与上游 instanceId 对应） */
    virtual FString GetInstanceId() const = 0;

    /**
     * 应用全量快照初始状态（启动/重连时调用）
     * @param NewLocation   换算后的 UE 世界坐标
     * @param Status        "working" | "idle"
     * @param DisplayName   上游姓名/标签
     * @param StationName   当前工位名称
     */
    virtual void ApplySnapshot(const FVector& NewLocation,
                               const FString& Status,
                               const FString& DisplayName,
                               const FString& StationName) = 0;

    /**
     * 应用位置变化事件（平滑移动）
     * @param FromLocation  变化前位置（可用于动画效果起点）
     * @param ToLocation    变化后位置（目标位置）
     */
    virtual void ApplyPositionChanged(const FVector& FromLocation,
                                      const FVector& ToLocation) = 0;

    /**
     * 应用状态变化事件
     * @param NewStatus     "working" | "idle" | "removed"
     * @param StationName   新工位名称
     */
    virtual void ApplyStateChanged(const FString& NewStatus,
                                   const FString& StationName) = 0;
};
