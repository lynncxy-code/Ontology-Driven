// ============================================================================
// TwinLabelComponent.h
//
// 统一头顶标签独立组件
//
// 使用方式：
//   ● 挂载到任意 Actor 的组件列表
//   ● 调用 SetLabelData() 更新内容
//   ● 或在 Details 面板直接设置 DefaultData 并在 BeginPlay 时自动显示
//
// 已集成：
//   ● 自动 Billboard（始终面向摄像机，仅旋转 Yaw）
//   ● World 空间渲染（始终朝屏幕，不跟随 Actor 旋转）
//   ● 可配置的 Z 偏移高度
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TwinLabelWidget.h"
#include "TwinLabelComponent.generated.h"

class UWidgetComponent;

UCLASS(ClassGroup=(DigitalTwin), meta=(BlueprintSpawnableComponent),
       DisplayName="孪生体标签组件")
class TEST0316_API UTwinLabelComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTwinLabelComponent();

protected:
    virtual void BeginPlay() override;

public:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
                               FActorComponentTickFunction* ThisTickFunction) override;

    // ═══════════════════════════════════════════════════════════════════════
    // Details 面板配置
    // ═══════════════════════════════════════════════════════════════════════

    /** 默认显示数据（BeginPlay 时自动应用） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="标签|内容",
              meta=(DisplayName="默认标签数据"))
    FTwinLabelData DefaultData;

    /** 标签距离 Actor 根组件的 Z 轴偏移（cm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="标签|位置",
              meta=(DisplayName="高度偏移(cm)", ClampMin="0.0", ClampMax="500.0"))
    float ZOffset = 180.f;

    /** 是否启用 Billboard（始终面向摄像机） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="标签|行为",
              meta=(DisplayName="启用 Billboard"))
    bool bBillboard = true;

    // ═══════════════════════════════════════════════════════════════════════
    // 运行时接口（蓝图和 C++ 均可调用）
    // ═══════════════════════════════════════════════════════════════════════

    /** 更新标签完整数据 */
    UFUNCTION(BlueprintCallable, Category="标签",
              meta=(DisplayName="设置标签数据"))
    void SetLabelData(const FTwinLabelData& InData);

    /** 仅更新主标题 */
    UFUNCTION(BlueprintCallable, Category="标签")
    void SetTitle(const FString& InTitle);

    /** 仅更新副标题 */
    UFUNCTION(BlueprintCallable, Category="标签")
    void SetSubtitle(const FString& InSubtitle);

    /** 仅更新状态（同时驱动描边颜色和图标） */
    UFUNCTION(BlueprintCallable, Category="标签")
    void SetStatus(const FString& InStatus);

    /** 仅更新 Badge */
    UFUNCTION(BlueprintCallable, Category="标签")
    void SetBadge(const FString& InBadge);

    /** 显示/隐藏标签 */
    UFUNCTION(BlueprintCallable, Category="标签")
    void SetLabelVisible(bool bVisible);

    /** 获取当前数据（只读） */
    UFUNCTION(BlueprintPure, Category="标签")
    FTwinLabelData GetLabelData() const;

private:
    /** WidgetComponent 载体（自动创建，不需要手动添加） */
    UPROPERTY()
    UWidgetComponent* WidgetComp = nullptr;

    /** Widget 实例 */
    UPROPERTY()
    UTwinLabelWidget* LabelWidget = nullptr;

    /** 当前数据缓存 */
    FTwinLabelData CachedData;

    /** Billboard：每帧对齐摄像机 */
    void UpdateBillboard();
};
