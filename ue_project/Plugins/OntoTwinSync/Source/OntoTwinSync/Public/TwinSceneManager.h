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
#include "InputCoreTypes.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "TwinSceneManager.generated.h"

class ATwinInstance;
class AOntoTwinRuntimeGizmo;
class APlayerController;
class IWebSocket;
class UOntoTwinRuntimeEditorPanel;
class UOntoTwinOverlayWidget;
class UTwinInteractionManagerComponent;

UENUM(BlueprintType)
enum class EOntoTwinRuntimeAccessState : uint8
{
    Checking,
    Ready,
    Unbound,
    Mismatch,
    Error
};

/**
 * ATwinSceneManager
 *
 * 场景中放置 1 个即可。自动轮询后端、管理所有孪生体 Actor 的生命周期。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="Twin Scene Manager"))
class ONTOTWINSYNC_API ATwinSceneManager : public AActor
{
    GENERATED_BODY()

public:
    ATwinSceneManager();

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaTime) override;

public:
    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** 后端 API 基础地址 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="后端基础URL"))
    FString BackendBaseUrl = TEXT("http://127.0.0.1:5000");

    /** UE 工程稳定身份。默认使用 ueproj_<工程名>；后端用它强绑定数据集，防止工程串台。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="UE工程ID"))
    FString UEProjectId;

    /** UE 工程显示名。默认取当前 .uproject 的工程名。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="UE工程名称"))
    FString UEProjectName;

    /**
     * 场景 ID：只拉取该场景的实例。
     * 留空 = 跟随后端当前激活的数据集（单工程常用）。
     * 多个 UE 工程对接同一后端时，各填各的场景名以互不干扰。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="场景ID(留空=跟随后端)"))
    FString SceneId = TEXT("");

    /** 轮询间隔（秒） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="轮询间隔(秒)", ClampMin="0.1", ClampMax="10.0"))
    float PollInterval = 0.5f;

    /** 连续失败次数阈值，超过后标记离线 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接",
              meta=(DisplayName="离线阈值(次)"))
    int32 OfflineThreshold = 3;

    /** 连接 AGV 实时状态流；HTTP 快照仍负责实例建档、模型绑定与非空间属性。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接|WebSocket",
              meta=(DisplayName="启用实时WebSocket"))
    bool bEnableRealtimeWebSocket = true;

    /** OntoTwin 中间层实时目标地址。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接|WebSocket",
              meta=(DisplayName="实时WebSocket URL"))
    FString RealtimeWebSocketUrl = TEXT("ws://10.191.12.40:8080/ws/targets");

    /** WebSocket 断开后的重连间隔。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接|WebSocket",
              meta=(DisplayName="重连间隔(秒)", ClampMin="0.5", ClampMax="60.0"))
    float RealtimeReconnectSeconds = 3.0f;

    /** 收到实时帧后，HTTP 在这段时间内不得覆盖该实例的空间坐标。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="连接|WebSocket",
              meta=(DisplayName="实时空间优先保持(秒)", ClampMin="0.1", ClampMax="10.0"))
    float RealtimeSpatialHoldSeconds = 1.0f;

    // ═══════════════════════════════════════════════════════════════════════
    // 实例配置
    // ═══════════════════════════════════════════════════════════════════════

    /** 运行时自动生成的孪生体蓝图类（请在这里选你的 BP_TwinInstance_Advanced） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="实例配置",
              meta=(DisplayName="孪生体蓝图类"))
    TSubclassOf<ATwinInstance> InstanceClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板",
              meta=(DisplayName="启用顶部信息面板"))
    bool bEnableOverlays = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板",
              meta=(DisplayName="选中面板类"))
    TSubclassOf<UOntoTwinOverlayWidget> OverlayWidgetClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板",
              meta=(DisplayName="常显最大距离(cm)", ClampMin="100.0", ClampMax="1000000.0"))
    float OverlayCullDistanceCm = 50000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板",
              meta=(DisplayName="常显最大数量", ClampMin="1", ClampMax="500"))
    int32 MaxVisibleAlwaysOverlays = 100;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板|可读性",
              meta=(DisplayName="常显目标屏幕宽度(px)", ClampMin="120.0", ClampMax="600.0"))
    float AlwaysOverlayTargetScreenWidthPx = 260.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板|可读性",
              meta=(DisplayName="常显最小世界缩放", ClampMin="0.01", ClampMax="1.0"))
    float AlwaysOverlayMinWorldScale = 0.06f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="顶部信息面板|可读性",
              meta=(DisplayName="常显最大世界缩放", ClampMin="0.01", ClampMax="2.0"))
    float AlwaysOverlayMaxWorldScale = 0.35f;

    /** 4.0 场景交互运行组件。人物、输入、路线和心跳不进入 SceneManager 主体。 */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="场景交互")
    UTwinInteractionManagerComponent* InteractionManager;

    // ═══════════════════════════════════════════════════════════════════════
    // Runtime Editor（打包 exe 内的轻量场景编辑入口）
    // ═══════════════════════════════════════════════════════════════════════

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor",
              meta=(DisplayName="启用Runtime Editor"))
    bool bEnableRuntimeEditor = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor",
              meta=(DisplayName="编辑模式轮询间隔(秒)", ClampMin="0.2", ClampMax="10.0"))
    float EditModePollInterval = 1.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor",
              meta=(DisplayName="Runtime Editor面板类"))
    TSubclassOf<UOntoTwinRuntimeEditorPanel> RuntimeEditorPanelClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor",
              meta=(DisplayName="Runtime Gizmo类"))
    TSubclassOf<AOntoTwinRuntimeGizmo> RuntimeGizmoClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|输入",
              meta=(DisplayName="切换编辑模式键"))
    FKey ToggleEditKey = EKeys::F8;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|输入",
              meta=(DisplayName="备用切换编辑模式键(PIE推荐)"))
    FKey AlternateToggleEditKey = EKeys::F10;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|输入",
              meta=(DisplayName="保存键"))
    FKey SaveKey = EKeys::S;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|输入",
              meta=(DisplayName="取消键"))
    FKey CancelKey = EKeys::Escape;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|吸附",
              meta=(DisplayName="启用靠墙吸附"))
    bool bEnableWallSnap = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|吸附",
              meta=(DisplayName="启用网格吸附"))
    bool bEnableGridSnap = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|吸附",
              meta=(DisplayName="网格吸附步长(cm)", ClampMin="1.0", ClampMax="10000.0"))
    float GridSnapSizeCm = 50.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|吸附",
              meta=(DisplayName="靠墙吸附距离(cm)", ClampMin="1.0", ClampMax="10000.0"))
    float WallSnapDistanceCm = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Runtime Editor|吸附",
              meta=(DisplayName="墙体Tag"))
    FName WallTag = TEXT("OntoTwinWall");

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void ToggleRuntimeEditMode();

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void SaveRuntimeEdit();

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void CancelRuntimeEdit();

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void BindCurrentRuntimeProject();

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void RetryRuntimeBindingStatus();

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void SetRuntimeWallSnapEnabled(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category="Runtime Editor")
    void SetRuntimeGridSnapEnabled(bool bEnabled);

    FString GetRuntimeEditorModeText() const;
    FString GetRuntimeEditorBindingText() const;
    FString GetRuntimeEditorSelectionText() const;
    FString GetRuntimeEditorTransformText() const;
    FString GetRuntimeEditorStatusText() const;
    FString GetRuntimeEditorHeaderStateText() const;
    FString GetRuntimeEditorDisplayName() const;
    FString GetRuntimeEditorInstanceIdText() const;
    bool GetRuntimeEditorTransform(FVector& OutLocation, float& OutYaw) const;
    EOntoTwinRuntimeAccessState GetRuntimeEditorAccessState() const;
    bool CanBindRuntimeProject() const;
    bool CanRetryRuntimeBindingStatus() const;
    bool CanSaveRuntimeEdit() const;
    bool CanCancelRuntimeEdit() const;
    bool HasRuntimeEditSelection() const;
    bool IsRuntimeEditDirty() const { return bRuntimeEditDirty; }
    bool IsRuntimeEditSaving() const { return bRuntimeEditSaving; }
    bool IsRuntimeWallSnapEnabled() const { return bEnableWallSnap; }
    bool IsRuntimeGridSnapEnabled() const { return bEnableGridSnap; }
    bool IsRuntimeEditModeActive() const { return bRuntimeEditMode; }

    /** 共享选择入口：人物模块只产生选择事件，Overlay 仍负责内容与 Widget 生命周期。 */
    void SelectOverlayFromSceneInteraction(ATwinInstance* Instance);
    void ClearOverlayFromSceneInteraction();

    /** 构造不含坐标的 WebSocket 健康快照，随现有 UE 心跳回报后端。 */
    TSharedRef<FJsonObject> BuildRealtimeChannelHealth() const;

    /** 把当前 UE 工程身份绑定到后端当前激活数据集（数据集之后只接受该工程的 UE 请求） */
    UFUNCTION(CallInEditor, Category="连接",
              meta=(DisplayName="绑定当前UE工程到激活数据集"))
    void BindCurrentUEProjectToActiveDataset();

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器预览（FR-4）—— 从数据库临时 spawn 供查看/微调，绝不存进 .umap
    //   已废弃"固化"：孪生实例只存在于数据库，编辑器里看的是 transient 预览。
    // ═══════════════════════════════════════════════════════════════════════

    /** 从数据库拉取本场景实例，生成【临时(transient)】预览 Actor（保存关卡不会写入 .umap） */
    UFUNCTION(CallInEditor, Category="预览",
              meta=(DisplayName="从数据库拉取预览"))
    void PullPreviewFromDB();

    /** 清除所有预览 Actor */
    UFUNCTION(CallInEditor, Category="预览",
              meta=(DisplayName="清除预览"))
    void ClearPreview();

    /**
     * FR-5 回写：把预览 Actor 里被手动挪动过的（当前 transform ≠ 拉取时基线），
     * 逐个 POST /api/v2/state/writeback 提交回后端真源。只提交动过的，一处不多。
     */
    UFUNCTION(CallInEditor, Category="预览",
              meta=(DisplayName="提交空间变更(回写)"))
    void CommitPreviewChanges();

    // ═══════════════════════════════════════════════════════════════════════
    // FR-6 历史 actor 迁移工具（编辑器一次性；配合后端 migrate_ue_actors.py）
    //   流程：① 框选历史 actor → 右键"移动到文件夹"→ 填 MigrationFolderName
    //         → 单独选中本 Manager → 点导出 → ② 跑后端脚本收编入库 →
    //         ③ 清除已迁移的原 actor（之后由 DB 驱动重新 spawn）
    //   （不用"同时选中 actor + Manager"：UE 细节面板多选不同类型时只显示
    //    共同按钮，Manager 专属按钮会被隐藏——改用文件夹分两步选，彻底避开）
    // ═══════════════════════════════════════════════════════════════════════

    /** 待迁移 actor 的 Outliner 文件夹名：框选历史 actor 右键"移动到文件夹"→ 填此名 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="迁移",
              meta=(DisplayName="待迁移文件夹名"))
    FString MigrationFolderName = TEXT("ToMigrate");

    /** ① 导出「待迁移文件夹」下的全部 actor 到 JSON，供后端收编 */
    UFUNCTION(CallInEditor, Category="迁移",
              meta=(DisplayName="① 导出待迁移Actor"))
    void ExportSelectedActorsForMigration();

    /** ③ 读后端迁移结果，删除已成功收编的原 actor（DB 之后重新驱动，勿忘保存关卡） */
    UFUNCTION(CallInEditor, Category="迁移",
              meta=(DisplayName="③ 清除已迁移Actor"))
    void RemoveMigratedActors();

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

    /** AGV 实时状态流。它只更新 InstanceRegistry 中由 HTTP 已创建的 Actor。 */
    TSharedPtr<IWebSocket> RealtimeSocket;
    FTimerHandle RealtimeReconnectTimerHandle;
    int32 RealtimeConnectionGeneration = 0;
    int64 RealtimeFrameCount = 0;
    int64 RealtimeLastSourceTimestampMs = 0;
    double RealtimeLastFramePlatformSeconds = -1.0;
    FString RealtimeConnectionState = TEXT("disabled");
    FString RealtimeLastError;
    TMap<FString, FString> RealtimeTargetStates;
    TSet<FString> RealtimeAppliedInstanceIds;
    bool bRealtimeReconnectScheduled = false;
    bool bRealtimeClosing = false;
    TSet<FString> RealtimeMissingInstanceWarnings;

    /** 编辑器预览 Actor（transient，不入 .umap；由 ClearPreview 清理） */
    UPROPERTY(Transient)
    TArray<ATwinInstance*> PreviewActors;

    /** FR-5 回写基线：InstanceId → 拉取预览时数据库给的 transform（提交时据此 diff） */
    TMap<FString, FTransform> PreviewBaseline;

    /** FR-5 回写在途/成功计数（编辑器单线程回调，无需加锁） */
    int32 PendingWritebacks = 0;
    int32 SucceededWritebacks = 0;

    // Runtime Editor state
    UPROPERTY()
    ATwinInstance* RuntimeSelectedInstance = nullptr;

    UPROPERTY()
    AOntoTwinRuntimeGizmo* RuntimeGizmo = nullptr;

    UPROPERTY()
    UOntoTwinRuntimeEditorPanel* RuntimeEditorPanel = nullptr;

    UPROPERTY()
    ATwinInstance* OverlaySelectedInstance = nullptr;

    UPROPERTY()
    UOntoTwinOverlayWidget* SelectedOverlayWidget = nullptr;

    uint64 SelectedOverlayPayloadSerial = 0;

    bool bOverlayPointerInputActive = false;
    bool bOverlayPreviousMouseCursor = false;

    bool bRuntimeEditMode = false;
    bool bRuntimeEditDirty = false;
    bool bRuntimeEditSaving = false;
    bool bRuntimeBindingRequestInFlight = false;
    bool bRuntimeCanSave = false;
    bool bRuntimeDragging = false;
    bool bRuntimeCameraLookSuppressed = false;
    bool bRuntimeLookInputWasAlreadyIgnored = false;
    bool bRuntimePreviousMouseCursor = false;
    bool bRuntimePreviousAnimRunning = false;
    float RuntimeLastToggleInputTime = -1000.0f;
    FString RuntimePreviousAnimState;
    FString RuntimeBindingMode = TEXT("unknown");
    FString RuntimeStatusMessage = TEXT("F8/F10: Runtime Editor");
    FTransform RuntimeEditBaseline = FTransform::Identity;
    FTransform RuntimeDragStartTransform = FTransform::Identity;
    FVector RuntimeDragStartPoint = FVector::ZeroVector;
    FVector RuntimeZDragStartPoint = FVector::ZeroVector;
    FPlane RuntimeZDragPlane = FPlane(FVector::ZeroVector, FVector::ForwardVector);
    float RuntimeEditPlaneZ = 0.0f;
    float RuntimeDragPlaneZ = 0.0f;
    float RuntimeDragStartAngleDeg = 0.0f;
    float RuntimeDragStartYaw = 0.0f;
    enum class ERuntimeDragPart : uint8 { None, MoveXY, MoveZ, RotateYaw };
    enum class ERuntimeSnapFeedback : uint8 { None, Grid, Wall };
    ERuntimeDragPart RuntimeHoverPart = ERuntimeDragPart::None;
    ERuntimeDragPart RuntimeDragPart = ERuntimeDragPart::None;
    ERuntimeSnapFeedback RuntimeSnapFeedback = ERuntimeSnapFeedback::None;
    FVector RuntimeSnapFeedbackPoint = FVector::ZeroVector;

    // ── 内部方法 ─────────────────────────────────────────────────────────

    /** 拼接快照接口 URL（SceneId 非空时追加 ?scene= 查询参数） */
    FString BuildSnapshotsUrl() const;

    /** 给 UE→后端请求附加 UE 工程身份头（用于数据集强绑定校验） */
    void AddUEProjectHeaders(TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest) const;

    void SetPollTimerInterval(float IntervalSeconds, float FirstDelaySeconds = 0.0f);

    /** 定时轮询回调 */
    void PollBackend();

    /** HTTP 响应回调 */
    void OnPollResponse(FHttpRequestPtr HttpRequest, FHttpResponsePtr Response, bool bWasSuccessful);

    /** 连接、消费并自动重连 AGV 实时状态流。 */
    void ConnectRealtimeWebSocket();
    void ScheduleRealtimeReconnect();
    void HandleRealtimeMessage(const FString& Message);

    /** 编辑器预览 HTTP 回调：把快照 spawn 成 transient 预览 Actor */
    void OnPreviewResponse(FHttpRequestPtr HttpRequest, FHttpResponsePtr Response, bool bWasSuccessful);

    /** 处理单个实例快照 */
    void ProcessSnapshot(const TSharedPtr<FJsonObject>& Snapshot);

    /** Spawn 新的孪生体 Actor */
    ATwinInstance* SpawnTwinInstance(const FString& InstanceId, const TSharedPtr<FJsonObject>& Snapshot);

    /** 销毁孪生体 Actor */
    void DestroyTwinInstance(const FString& InstanceId);

    void TickRuntimeEditor(float DeltaTime);
    void TickOverlays();
    void SelectOverlayInstance(ATwinInstance* Instance, bool bAllowAnyMode = false);
    void ClearOverlaySelection();
    void UpdateAlwaysOverlays(APlayerController* PlayerController);
    void UpdateOverlayPointerInput(APlayerController* PlayerController, bool bShouldOwnPointer);
    void RequestRuntimeEditToggle();
    void EnterRuntimeEditMode();
    void ExitRuntimeEditMode();
    void ShowRuntimeEditorPanel();
    void HideRuntimeEditorPanel();
    void EnsureRuntimeGizmo();
    void UpdateRuntimeEditorPanel();
    void CheckRuntimeBindingStatus();
    void SelectRuntimeInstance(ATwinInstance* Instance);
    void ClearRuntimeSelection(bool bRestoreBaseline);
    bool TraceRuntimeCursor(FHitResult& OutHit) const;
    bool GetRuntimeCursorPointOnPlane(const FPlane& Plane, FVector& OutPoint) const;
    bool GetRuntimeCursorPlanePoint(FVector& OutPoint) const;
    void BeginRuntimeGizmoDrag(ERuntimeDragPart Part);
    void UpdateRuntimeGizmoDrag();
    void EndRuntimeGizmoDrag();
    void SetRuntimeCameraLookSuppressed(bool bSuppress);
    void ApplyRuntimeSnaps(FVector& InOutLocation, FRotator& InOutRotation);
    void MarkRuntimeDirtyFromTransform();
    void ApplyRuntimeSnapshotIfPresent(const TSharedPtr<FJsonObject>& ResponseObj);

    /** FR-6 迁移导出文件绝对路径（Saved/OntoTwinMigration/ue_actors_export.json） */
    FString MigrationExportPath() const;
    /** FR-6 迁移结果文件绝对路径（Saved/OntoTwinMigration/ue_migration_result.json） */
    FString MigrationResultPath() const;
};
