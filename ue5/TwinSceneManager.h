// ============================================================================
// TwinSceneManager.h
//
// 孪生场景管理器 — 关卡级别的全局实例生命周期管理器
//
// 功能说明：
//   1. 启动后自动轮询后端 GET /api/v2/state/snapshots，获取所有实例快照
//   2. 对比本地注册表，自动 Spawn / Destroy ATwinInstance Actor
//   3. 编辑器模式下提供"📸 快照固化到关卡"按钮，一键生成持久 Actor
//   4. Play 时自动接管关卡中已有的 ATwinInstance（编辑器预置 Actor）
//
// 使用方式：
//   在关卡中放置一个 ATwinSceneManager Actor 即可，无需蓝图连接
//
// 依赖模块（.Build.cs）：
//   "Http", "Json", "JsonUtilities"
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "TwinSceneManager.generated.h"

class ATwinInstance;

/**
 * ATwinSceneManager
 *
 * 场景中放置 1 个即可。自动轮询后端、管理所有孪生体 Actor 的生命周期。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="孪生场景管理器"))
class TEST0316_API ATwinSceneManager : public AActor
{
    GENERATED_BODY()

public:
    ATwinSceneManager();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** 后端 API 基础地址 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生管理器|连接",
              meta=(DisplayName="后端基础URL"))
    FString BackendBaseUrl = TEXT("http://127.0.0.1:5000");

    /** 轮询间隔（秒） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生管理器|连接",
              meta=(DisplayName="轮询间隔(秒)", ClampMin="0.1", ClampMax="10.0"))
    float PollInterval = 0.5f;

    /** 连续失败次数阈值，超过后标记离线 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生管理器|连接",
              meta=(DisplayName="离线阈值(次)"))
    int32 OfflineThreshold = 3;

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器按钮
    // ═══════════════════════════════════════════════════════════════════════

    /** 📸 快照固化到关卡：从后端抓取当前全部实例，在编辑器中生成持久 Actor */
    UFUNCTION(CallInEditor, Category="孪生管理器|工具",
              meta=(DisplayName="📸 快照固化到关卡"))
    void SnapshotToLevel();

private:
    // ── 内部状态 ─────────────────────────────────────────────────────────

    /** 轮询定时器句柄 */
    FTimerHandle PollTimerHandle;

    /** 请求锁 */
    bool bRequestInFlight = false;

    /** 连续失败计数 */
    int32 ConsecutiveFailures = 0;

    /** 实例注册表：InstanceId → ATwinInstance* */
    UPROPERTY()
    TMap<FString, ATwinInstance*> InstanceRegistry;

    // ── 内部方法 ─────────────────────────────────────────────────────────

    /** 定时轮询回调 */
    void PollBackend();

    /** HTTP 响应回调 */
    void OnPollResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    /** 📸 编辑器快照 HTTP 回调 */
    void OnSnapshotResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    /** 处理单个实例快照 */
    void ProcessSnapshot(const TSharedPtr<FJsonObject>& Snapshot);

    /** Spawn 新的孪生体 Actor */
    ATwinInstance* SpawnTwinInstance(const FString& InstanceId, const TSharedPtr<FJsonObject>& Snapshot);

    /** 销毁孪生体 Actor */
    void DestroyTwinInstance(const FString& InstanceId);

    /** BeginPlay 时扫描关卡中已有的 ATwinInstance 并注册 */
    void TakeOverExistingInstances();
};
