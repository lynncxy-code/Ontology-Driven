// ============================================================================
// AGVSimLogLoader.h
//
// AGV 仿真日志加载器（CSV 回放驱动器）
//
// 使用说明：
//   1. 将此组件挂载到场景中任意一个持久 Actor（如 GameMode / EmptyActor）上
//   2. 在 Details 面板将 CsvPath 指向本地 agv_route_test0316.csv 文件
//   3. BeginPlay 时自动解析 CSV，按 serial 分组帧序列，注入到场景中同名 AgvSerial 的
//      UAGVPatrolComponent，激活 CSV 回放模式
//
// 坐标系策略（本期）：
//   CSV 坐标直接视作 UE cm 单位，不做映射。
//   如需适配其他仿真系统，可调整 CoordScale / CoordOffset 属性。
//
// 版本：OntoTwin 2.8.1
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AGVSimLogLoader.generated.h"

// ─────────────────────────────────────────────────────────────────────────────
// 单帧数据结构体
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 一条 AGV 仿真日志帧，对应 CSV 中的一行记录。
 */
USTRUCT(BlueprintType)
struct FAgvFrame
{
    GENERATED_BODY()

    /** 相对回放时间（秒），从第一条记录起算 */
    UPROPERTY(BlueprintReadOnly, Category="AGV|帧")
    float Time = 0.f;

    /** 世界坐标（cm） */
    UPROPERTY(BlueprintReadOnly, Category="AGV|帧")
    FVector Position = FVector::ZeroVector;

    /** 方向四元数 */
    UPROPERTY(BlueprintReadOnly, Category="AGV|帧")
    FQuat Orientation = FQuat::Identity;

    /** 偏航角（弧度），0=+X，π/2=+Y */
    UPROPERTY(BlueprintReadOnly, Category="AGV|帧")
    float Yaw = 0.f;

    /** 是否有货：cargo_status != "[0]" */
    UPROPERTY(BlueprintReadOnly, Category="AGV|帧")
    bool bHasCargo = false;
};

// ─────────────────────────────────────────────────────────────────────────────
// 加载器组件
// ─────────────────────────────────────────────────────────────────────────────

/**
 * UAGVSimLogLoader
 *
 * 职责：
 *   - 在 BeginPlay 时读取 CSV 文件
 *   - 按 serial 字段分组，建立 TMap<FString, TArray<FAgvFrame>>
 *   - 扫描场景中所有携带 UAGVPatrolComponent 的 Actor，比对 AgvSerial，注入帧序列
 */
UCLASS(ClassGroup=(AGVDigitalTwin), meta=(BlueprintSpawnableComponent),
       DisplayName="AGV仿真日志加载器")
class TEST0316_API UAGVSimLogLoader : public UActorComponent
{
    GENERATED_BODY()

public:
    UAGVSimLogLoader();

protected:
    virtual void BeginPlay() override;

public:
    // ─────────────────────────────────────────────────────────────────────
    // 编辑器可配置属性
    // ─────────────────────────────────────────────────────────────────────

    /**
     * CSV 文件绝对路径
     * 例：D:/tmp/mock_data/agv_route_test0316.csv
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV日志|数据源",
              meta=(DisplayName="CSV 文件路径"))
    FString CsvPath;

    /**
     * 坐标缩放系数（默认 1.0，代表 CSV 坐标已是 UE cm）
     * 若仿真输出为米，填 100.0。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV日志|坐标适配",
              meta=(DisplayName="坐标缩放 (1.0 = cm)", ClampMin="0.01"))
    float CoordScale = 1.0f;

    /**
     * 坐标全局偏置（cm），用于对齐 UE 场景原点
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV日志|坐标适配",
              meta=(DisplayName="坐标偏置 (cm)"))
    FVector CoordOffset = FVector::ZeroVector;

    /** 是否打印调试日志 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AGV日志|调试",
              meta=(DisplayName="启用调试日志"))
    bool bDebugLog = true;

    // ─────────────────────────────────────────────────────────────────────
    // 只读状态
    // ─────────────────────────────────────────────────────────────────────

    /** 解析到的不同 AGV serial 数量 */
    UPROPERTY(BlueprintReadOnly, Category="AGV日志|状态",
              meta=(DisplayName="解析AGV数量"))
    int32 ParsedAgvCount = 0;

    /** 成功注入帧序列的 AGV 数量 */
    UPROPERTY(BlueprintReadOnly, Category="AGV日志|状态",
              meta=(DisplayName="成功注入数量"))
    int32 InjectedAgvCount = 0;

    // ─────────────────────────────────────────────────────────────────────
    // 蓝图可调接口
    // ─────────────────────────────────────────────────────────────────────

    /**
     * 手动重新加载并注入（可在蓝图中热重载无需 PIE 重启）
     */
    UFUNCTION(BlueprintCallable, Category="AGV日志",
              meta=(DisplayName="重新加载CSV并注入"))
    void ReloadAndInject();

    /**
     * 返回指定 serial 的帧序列（供调试蓝图使用）
     */
    UFUNCTION(BlueprintCallable, Category="AGV日志",
              meta=(DisplayName="获取帧序列"))
    const TArray<FAgvFrame>& GetFramesForSerial(const FString& Serial) const;

private:
    /** serial → 帧序列 映射 */
    TMap<FString, TArray<FAgvFrame>> FrameMap;

    /** 空帧序列，GetFramesForSerial 查不到时返回 */
    static const TArray<FAgvFrame> EmptyFrames;

    /** 解析 CSV 文件，填充 FrameMap */
    bool ParseCsv(const FString& FilePath);

    /** 将 FrameMap 中每个 serial 注入到对应的场景 AGV Actor */
    void InjectToScene();

    /**
     * 从 CSV 行中解析指定列名的 float 值，失败返回 DefaultValue
     */
    static float ParseFloat(const TMap<FString, int32>& ColIndex,
                            const TArray<FString>& Row,
                            const FString& ColName,
                            float DefaultValue = 0.f);

    /**
     * 从 CSV 行中解析指定列名的字符串，失败返回空串
     */
    static FString ParseString(const TMap<FString, int32>& ColIndex,
                               const TArray<FString>& Row,
                               const FString& ColName);
};
