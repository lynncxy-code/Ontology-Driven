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
#include "Components/TextRenderComponent.h"
#include "Dom/JsonObject.h"
#include "TwinInstance.generated.h"

class UDigitalTwinSyncComponent;

// ============================================================================
// 动画配方结构体（内置库使用）
// ============================================================================
struct FAnimRecipe
{
    FVector  TranslationDelta; // 每次循环相对位移（cm）
    FRotator RotationDelta;    // 每次循环额外旋转度数
    float    Duration;         // 单次时长（秒）
    bool     bLoop;            // 是否循环
    bool     bPingPong;        // 是否来回往返

    FAnimRecipe()
        : TranslationDelta(FVector::ZeroVector)
        , RotationDelta(FRotator::ZeroRotator)
        , Duration(1.0f)
        , bLoop(true)
        , bPingPong(true)
    {}

    FAnimRecipe(FVector InTrans, FRotator InRot, float InDur, bool InLoop, bool InPingPong)
        : TranslationDelta(InTrans)
        , RotationDelta(InRot)
        , Duration(InDur)
        , bLoop(InLoop)
        , bPingPong(InPingPong)
    {}
};

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
    // 视觉特效属性与蓝图接口
    // ═══════════════════════════════════════════════════════════════════════

    /** 灰模材质 (用于 material_variant = gray) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|视觉展示", meta=(DisplayName="灰模通用材质"))
    UMaterialInterface* MatGray = nullptr;

    /** 线框材质 (用于 material_variant = wireframe) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|视觉展示", meta=(DisplayName="线框通用材质"))
    UMaterialInterface* MatWireframe = nullptr;

    /** 缓存加载时的原始材质（以支持从灰模/线框恢复） */
    UPROPERTY()
    TArray<UMaterialInterface*> OriginalMaterials;

    // ── 3D 文字标签配置 ──────────────────────────────────────────────────────

    /** 标签字体（在 Details 面板中拖入已导入的 Font 资产，支持中文） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|文字标签", meta=(DisplayName="标签字体"))
    UFont* LabelFont = nullptr;

    /** 标签文字大小（世界坐标单位，默认 8cm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|文字标签", meta=(DisplayName="文字大小"))
    float LabelWorldSize = 8.0f;

    /** 标签颜色 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|文字标签", meta=(DisplayName="文字颜色"))
    FColor LabelColor = FColor::White;

    /** 相对模型原点的 Z 轴偏移（cm），默认 20cm */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="孪生体|文字标签", meta=(DisplayName="标签高度偏移"))
    float LabelZOffset = 20.0f;

    /** 当从 Web 接收到全新的动画指令（平移/跳跃/翻转）时抛出，供美术在蓝图中实现运镜或 Timeline */
    UFUNCTION(BlueprintImplementableEvent, Category="孪生体|行为事件", meta=(DisplayName="当触发新动画状态时"))
    void OnAnimationStateChanged(const FString& NewAnimState);

    /**
     * 当 Web 端下发的 material_variant 不在 C++ 内置列表中时抛出。
     * 蓝图可在此事件中通过 Map 查找并应用自定义材质。
     * @param VariantName  前端传来的变体名称字符串，如 "metal", "glass", "xray"
     */
    UFUNCTION(BlueprintImplementableEvent, Category="孪生体|视觉事件", meta=(DisplayName="当材质变体变化时"))
    void OnMaterialVariantChanged(const FString& VariantName);

    /**
     * 当 Web 端下发特效触发指令时抛出。
     * 蓝图可在此事件中通过 Map 查找对应的 Niagara/Particle System 并播放。
     * @param FxName  前端传来的特效名称字符串，如 "fire", "smoke", "warning_glow"
     */
    UFUNCTION(BlueprintImplementableEvent, Category="孪生体|行为事件", meta=(DisplayName="当触发特效时"))
    void OnFxTriggered(const FString& FxName);

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
    virtual void Tick(float DeltaTime) override;

    // ── 组件（供蓝图访问） ────────────────────────────────────────────────
    /** 网格体组件 */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="孪生体", meta=(AllowPrivateAccess="true"))
    UStaticMeshComponent* MeshComponent = nullptr;

    /** 3D 文字标签组件（显示 ui_label_content） */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="孪生体", meta=(AllowPrivateAccess="true"))
    UTextRenderComponent* LabelComponent = nullptr;

private:
    // ── 同步组件 ─────────────────────────────────────────────────────────────

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

    /** 把当前的材质全部存下 */
    void CacheOriginalMaterials();

    /** 还原材质 */
    void RestoreOriginalMaterials();

    /** 从 JSON 接口数据中驱动三大能力 */
    void ApplySpatialFromSnapshot(const TSharedPtr<FJsonObject>& SpatialObj);
    void ApplyVisualFromSnapshot(const TSharedPtr<FJsonObject>& VisualObj);
    void ApplyBehavioralFromSnapshot(const TSharedPtr<FJsonObject>& BehaviorObj);
    void ApplyRepresentableFromSnapshot(const TSharedPtr<FJsonObject>& RepObj);

    /** 当前材质变体缓存 */
    FString CurrentMaterialVariant;

    /** 当前动画状态缓存 */
    FString CurrentAnimState;

    /** 当前特效状态缓存 */
    FString CurrentFxTrigger;

    /** 当前标签文字缓存（防止重复刷新）*/
    FString CurrentLabelContent;

    // ── 程序化动画状态 ────────────────────────────────────────────────
    /** 内置动画配方字典（state名 → 执行配方）*/
    TMap<FString, FAnimRecipe> AnimLibrary;

    /** 动画计时器 */
    float  AnimTimer = 0.0f;

    /** 动画各自的基准動画开始时的位置和旋转（用于计算相对偏移） */
    FVector  AnimBaseLocation  = FVector::ZeroVector;
    FRotator AnimBaseRotation  = FRotator::ZeroRotator;

    /** 当前活跃的动画配方 */
    FAnimRecipe ActiveRecipe;

    /** 动画是否正在运行 */
    bool bAnimRunning = false;

    /** 动画内部立即切换动画状态 */
    void PlayAnimationState(const FString& StateName);

    /** 初始化动画配方字典 */
    void InitAnimLibrary();

    /** 插值目标值 */
    FVector TargetLocation = FVector::ZeroVector;
    FRotator TargetRotation = FRotator::ZeroRotator;
    FVector TargetScale = FVector::OneVector;

    /** 位置/旋转插值速度 */
    float LocationInterpSpeed = 5.0f;
    float RotationInterpSpeed = 5.0f;
};
