// ============================================================================
// TwinColumnPlacer.h
//
// 立柱批量实例化摆放器 — 基于 HISM 的高性能实例生成
//
// 功能说明：
//   1. 接收 JSON 中 INSTANCE 类型的坐标和变换数据
//   2. 通过 DataTable 查询 mesh_id → UE 静态网格体路径的映射
//   3. 使用 HISM (UHierarchicalInstancedStaticMeshComponent) 批量生成
//   4. 上千根立柱一帧内全部渲染完毕，零掉帧
//
// 使用方式：
//   由 ATwinCADDispatcher 自动创建并调用
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/DataTable.h"
#include "TwinColumnPlacer.generated.h"

/**
 * DataTable 行结构：mesh_id → UE 资产路径映射
 */
USTRUCT(BlueprintType)
struct FTwinMeshMapping : public FTableRowBase
{
    GENERATED_BODY()

    /** DXF/JSON 中的 mesh_id 标识符（如 "SM_Std_Column_500"） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="映射")
    FString MeshId;

    /** 对应的 UE StaticMesh 资产路径（如 "/Game/Assets/Columns/SM_Column_A"） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="映射")
    TSoftObjectPtr<UStaticMesh> MeshAsset;
};

/**
 * 单个立柱实例的输入数据结构（从 JSON 映射而来）
 */
USTRUCT(BlueprintType)
struct FTwinColumnData
{
    GENERATED_BODY()

    /** DXF 中的 mesh_id，用于查 DataTable */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱数据")
    FString MeshId;

    /** 位置 (DXF 坐标，单位 mm) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱数据")
    FVector Location = FVector::ZeroVector;

    /** 旋转 (度) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱数据")
    FRotator Rotation = FRotator::ZeroRotator;

    /** 缩放 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱数据")
    FVector Scale = FVector::OneVector;
};

/**
 * ATwinColumnPlacer
 *
 * 高性能立柱批量摆放器。使用 HISM 实例化技术批量渲染。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="CAD 立柱摆放器"))
class TEST0316_API ATwinColumnPlacer : public AActor
{
    GENERATED_BODY()

public:
    ATwinColumnPlacer();

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** DXF 坐标到 UE 坐标的缩放因子（mm → cm，默认 0.1） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱摆放器|全局",
              meta=(DisplayName="坐标缩放 (mm→cm)"))
    float CoordScale = 0.1f;

    /** 柱体缩放倍数（当导入的模型太小时，可在此处放大） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱摆放器|全局",
              meta=(DisplayName="柱体整体缩放倍数"))
    FVector ColumnScaleMultiplier = FVector(1.0f, 1.0f, 1.0f);

    /** mesh_id → UE 资产路径映射表 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱摆放器|配置",
              meta=(DisplayName="网格体映射表 (DataTable)"))
    UDataTable* MeshMappingTable = nullptr;

    /** 默认静态网格体（当 DataTable 中没有匹配项时使用） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱摆放器|配置",
              meta=(DisplayName="默认柱体网格"))
    UStaticMesh* DefaultColumnMesh = nullptr;

    /** 立柱材质（可选） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="立柱摆放器|配置",
              meta=(DisplayName="立柱材质"))
    UMaterialInterface* ColumnMaterial = nullptr;

    // ═══════════════════════════════════════════════════════════════════════
    // 公开接口
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * 批量摆放立柱
     * @param ColumnDataArray  立柱数据数组
     */
    UFUNCTION(BlueprintCallable, Category="立柱摆放器")
    void PlaceColumns(const TArray<FTwinColumnData>& ColumnDataArray);

    /** 清除所有已生成的实例 */
    UFUNCTION(BlueprintCallable, Category="立柱摆放器")
    void ClearAllInstances();

    /** 从 JSON 字符串中解析立柱数据 */
    static bool ParseJsonToColumnData(const FString& JsonString, TArray<FTwinColumnData>& OutColumnData);

private:
    /** HISM 组件注册表：MeshId → HISM Component */
    UPROPERTY()
    TMap<FString, UHierarchicalInstancedStaticMeshComponent*> HISMRegistry;

    /** 获取或创建指定 MeshId 对应的 HISM 组件 */
    UHierarchicalInstancedStaticMeshComponent* GetOrCreateHISM(const FString& MeshId);

    /** 从 DataTable 查找 MeshId 对应的 StaticMesh */
    UStaticMesh* ResolveMesh(const FString& MeshId);
};
