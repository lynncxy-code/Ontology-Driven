// ============================================================================
// TwinInstance.h
//
// 孪生体实例 Actor — 每个后端实例在 UE 中的渲染载体
//
// 功能说明：
//   1. 根据 asset_id（UE 内容路径）动态加载 StaticMesh
//   2. 接收 ATwinSceneManager 下发的 JSON 快照，驱动空间/材质/行为
//   3. 支持编辑器模式固化：可手动放置到关卡并在编辑器里调整位置
//   4. bLocalOverrideLock：锁定后忽略后端的空间变换数据
//
// 使用方式：
//   ● 自动模式：由 ATwinSceneManager 运行时自动 Spawn
//   ● 固化模式：通过 ATwinSceneManager 的"快照固化"按钮生成编辑器持久 Actor
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "TwinInstance.generated.h"

class UDigitalTwinSyncComponent;

/**
 * ATwinInstance
 *
 * 单个数字孪生体在 UE 场景中的具象化 Actor。
 * 由 ATwinSceneManager 管控生命周期。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="孪生体实例"))
class TEST0316_API ATwinInstance : public AActor
{
    GENERATED_BODY()

public:
    ATwinInstance();

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** 实例 ID（关联后端数据） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|标识",
              meta=(DisplayName="实例ID"))
    FString InstanceId;

    /** UE 资产路径（/Game/...） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|标识",
              meta=(DisplayName="UE资产路径"))
    FString AssetPath;

    /** 🔒 本地锁定：锁定后，后端空间变换数据不会覆盖编辑器中的位置/旋转/缩放 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|同步控制",
              meta=(DisplayName="🔒 锁定本地空间变换"))
    bool bLocalOverrideLock = false;

    /** 是否由编辑器"快照固化"或手动放置（非运行时 Spawn） */
    UPROPERTY(VisibleAnywhere, Category="孪生体|同步控制",
              meta=(DisplayName="编辑器预置"))
    bool bEditorPlaced = false;

    // ═══════════════════════════════════════════════════════════════════════
    // 公开接口（供 ATwinSceneManager 调用）
    // ═══════════════════════════════════════════════════════════════════════

    /** 初始化孪生体：加载资产、配置同步组件 */
    void InitializeTwin(const FString& InInstanceId, const FString& InAssetPath, const FString& InBackendBaseUrl);

    /** 应用后端快照到 Actor（由 SceneManager 每 500ms 调用） */
    void ApplySnapshot(const TSharedPtr<FJsonObject>& Snapshot);

    /** 获取实例 ID */
    FString GetInstanceId() const { return InstanceId; }

protected:
    virtual void BeginPlay() override;

private:
    // ── 组件 ─────────────────────────────────────────────────────────────

    /** 网格体组件 */
    UPROPERTY(VisibleAnywhere, Category="孪生体")
    UStaticMeshComponent* MeshComponent = nullptr;

    /** 同步组件（复用老插件） */
    UPROPERTY()
    UDigitalTwinSyncComponent* SyncComponent = nullptr;

    // ── 属性 ─────────────────────────────────────────────────────────────

    /** 后端 API 基础地址 */
    FString BackendBaseUrl;

    /** 是否已完成初始化 */
    bool bInitialized = false;

    // ── 内部方法 ─────────────────────────────────────────────────────────

    /** 根据 UE 路径加载 StaticMesh */
    bool LoadMeshFromPath(const FString& MeshPath);

    /** 从 JSON 接口数据中驱动三大能力 */
    void ApplySpatialFromSnapshot(const TSharedPtr<FJsonObject>& SpatialObj);
    void ApplyVisualFromSnapshot(const TSharedPtr<FJsonObject>& VisualObj);
    void ApplyBehavioralFromSnapshot(const TSharedPtr<FJsonObject>& BehaviorObj);
    void ApplyRepresentableFromSnapshot(const TSharedPtr<FJsonObject>& RepObj);

    /** 当前材质变体缓存 */
    FString CurrentMaterialVariant;

    /** 动态材质实例 */
    UPROPERTY()
    UMaterialInstanceDynamic* DynMaterial = nullptr;

    /** 材质变体颜色表 */
    FLinearColor ColorNormal  = FLinearColor(0.8f, 0.8f, 0.8f, 1.0f);
    FLinearColor ColorFault   = FLinearColor(1.0f, 0.15f, 0.15f, 1.0f);
    FLinearColor ColorAlarm   = FLinearColor(1.0f, 0.7f, 0.0f, 1.0f);
    FLinearColor ColorOffline = FLinearColor(0.3f, 0.3f, 0.3f, 1.0f);

    /** 插值目标值 */
    FVector TargetLocation = FVector::ZeroVector;
    FRotator TargetRotation = FRotator::ZeroRotator;
    FVector TargetScale = FVector::OneVector;

    /** 位置/旋转插值速度 */
    float LocationInterpSpeed = 5.0f;
    float RotationInterpSpeed = 5.0f;
};
