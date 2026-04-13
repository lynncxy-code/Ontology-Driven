#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "PCBWorkerManager.generated.h"

class UPCBWorkerSyncComponent;

/**
 * APCBWorkerManager
 *
 * 放置在关卡中的单例管理 Actor。
 *
 * 【重要】放置步骤：
 *   1. Place Actors 面板搜索 "PCBWorkerManager" 拖入场景
 *   2. Details 面板确认 MiddlewareBaseUrl 正确
 *   3. Play 后日志会出现 [PCBManager] 开头的行
 *
 * 位置驱动模式（v2）：
 *   不再使用上游 position 字段，改用 workstationId 查工位位置表。
 *   表数据来自 pos.csv，硬编码在 ResolveWorkerPosition() 中。
 */
UCLASS(DisplayName="PCB工人管理器")
class TEST0316_API APCBWorkerManager : public AActor
{
    GENERATED_BODY()

public:
    APCBWorkerManager();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
    // ── Details 面板配置 ───────────────────────────────────────────

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB|连接",
              meta=(DisplayName="中转站代理基础URL"))
    FString MiddlewareBaseUrl = TEXT("http://127.0.0.1:5000/api/v2/floor_pulse");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB|连接",
              meta=(DisplayName="事件轮询间隔(秒)", ClampMin="0.5", ClampMax="10.0"))
    float EventPollIntervalSeconds = 2.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="PCB|调试",
              meta=(DisplayName="启用调试日志"))
    bool bDebugLog = true;

    // ── 蓝图只读状态 ───────────────────────────────────────────────

    UPROPERTY(BlueprintReadOnly, Category="PCB|状态")
    int32 RegisteredWorkerCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="PCB|状态")
    int32 LastEventId = 0;

    UPROPERTY(BlueprintReadOnly, Category="PCB|状态")
    bool bMiddlewareOnline = false;

    // ── 蓝图可调用 ────────────────────────────────────────────────

    UFUNCTION(BlueprintCallable, Category="PCB|控制",
              meta=(DisplayName="重新拉取快照"))
    void RefreshSnapshot();

private:
    TMap<FString, UPCBWorkerSyncComponent*> WorkerRegistry;
    bool bSnapshotLoaded    = false;
    bool bRequestInFlight   = false;
    FTimerHandle PollTimerHandle;

    // 核心流程
    void ScanAndRegisterWorkers();
    void FetchSnapshot();
    void FetchEvents();
    void StartEventPolling();

    // HTTP 回调
    void OnSnapshotReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);
    void OnEventsReceived  (FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);

    // JSON 处理
    void ProcessSnapshotPayload(const TSharedPtr<FJsonObject>& Root);
    void ProcessEventsPayload  (const TSharedPtr<FJsonObject>& Root);
    void DispatchSnapshotItem  (const TSharedPtr<FJsonObject>& Item);
    void DispatchEvent         (const TSharedPtr<FJsonObject>& Event);

    /**
     * 【核心位置解析 v2】
     * 根据 workstationId（WS-00~WS-05）+ instanceId 查内置工位表，
     * 返回 UE 世界坐标（直接来自 pos.csv，单位 cm）。
     *
     * 分配规则：
     *   FW 奇数号（01/03/05）→ pos_1（工位正面）
     *   FW 偶数号（02/04/06）→ pos_2（工位背面）
     *
     * 已知 workstationId 映射（来自 pos.csv）：
     *   WS-00 / "REST"     → 休息区
     *   WS-01 / "PCB-X100" → X100 主控板工位
     *   WS-02 / "PCB-X200" → X200 传感板工位
     *   WS-03 / "PCB-X300" → X300 驱动板工位
     *   WS-04 / "PCB-X400" → X400 电源板工位
     *   WS-05 / "PCB-X500" → X500 射频板工位
     */
    FVector ResolveWorkerPosition(const FString& InstanceId,
                                   const FString& WorkstationId,
                                   const FString& WorkstationName);

    /**
     * 工位占用表：记录每个工位当前占用该位置（pos_1/pos_2）的工人列表
     * Key   = "WS-04_pos1" / "WS-04_pos2"
     * Value = 占用该位置的 InstanceId 有序列表（按到达顺序）
     * 用于计算 X 方向偶排偏移避免重叠
     */
    TMap<FString, TArray<FString>> StationOccupancy;

    /** 记录每个工人当前占用的槽位 Key（如 "WS-04_pos1"），移动时用于从旧槽位移除 */
    TMap<FString, FString> WorkerSlotMap;

    /**
     * 纯查表辅助：仅返回基准坐标，不更新占用表。
     * 用于 position_changed 事件的 From 位置查询。
     */
    FVector LookupBasePosition(const FString& InstanceId,
                               const FString& WorkstationId,
                               const FString& WorkstationName) const;

    // 辅助
    TSharedPtr<FJsonObject> ParseJsonResponse(FHttpResponsePtr Response);
    UPCBWorkerSyncComponent* FindWorker(const FString& InstanceId) const;
};

