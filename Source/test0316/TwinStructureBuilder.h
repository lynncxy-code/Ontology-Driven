// ============================================================================
// TwinStructureBuilder.h
//
// CAD 墙体程序化生成器 — 基于 RealtimeMeshComponent 的高性能墙面拉伸
//
// 功能说明：
//   1. 接收由 TwinSceneManager 从 JSON 解析出的 PROCEDURAL_WALL 路径坐标
//   2. 将 2D 折线路径按指定厚度和高度转化为 3D 三角面片网格 (Mesh)
//   3. 使用 RMC (RealtimeMeshComponent) 进行渲染，支持大规模场景秒级生成
//
// 使用方式：
//   在关卡中拖入一个 ATwinStructureBuilder Actor，
//   或由 TwinSceneManager 在运行时自动 Spawn 并调用 BuildWallsFromJson()
//
// 依赖模块（.Build.cs）：
//   "RealtimeMeshComponent"
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "RealtimeMeshActor.h"
#include "RealtimeMeshSimple.h"
#include "TwinStructureBuilder.generated.h"

/**
 * 单面墙体的输入数据结构（从 JSON 映射而来）
 */
USTRUCT(BlueprintType)
struct FTwinWallData
{
    GENERATED_BODY()

    /** 墙体 2D 路径点（DXF 坐标，单位 mm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="墙体数据")
    TArray<FVector2D> Path;

    /** 墙体高度（mm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="墙体数据")
    float Height = 4500.0f;

    /** 墙体厚度（mm） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="墙体数据")
    float Thickness = 240.0f;
};

/**
 * ATwinStructureBuilder
 *
 * 程序化建筑结构生成器。接收 JSON 数据后在运行时生成所有墙面几何体。
 * 继承自 ARealtimeMeshActor, 自带 URealtimeMeshComponent。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="CAD 墙体生成器"))
class TEST0316_API ATwinStructureBuilder : public ARealtimeMeshActor
{
    GENERATED_BODY()

public:
    ATwinStructureBuilder();

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** DXF 坐标到 UE 坐标的缩放因子（DXF 单位 mm → UE 单位 cm，默认 0.1） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 生成器|全局",
              meta=(DisplayName="坐标缩放 (mm→cm)"))
    float CoordScale = 0.1f;

    /** 墙面材质 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 生成器|材质",
              meta=(DisplayName="墙面材质"))
    UMaterialInterface* WallMaterial = nullptr;

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器按钮（测试用）
    // ═══════════════════════════════════════════════════════════════════════

    /** 测试按钮：从指定路径的 JSON 文件中加载并生成墙体 */
    UFUNCTION(CallInEditor, Category="CAD 生成器|工具",
              meta=(DisplayName="🏗️ 从 JSON 文件生成墙体"))
    void BuildFromJsonFile();

    /** JSON 文件路径（用于 BuildFromJsonFile 按钮） */
    UPROPERTY(EditAnywhere, Category="CAD 生成器|工具",
              meta=(DisplayName="JSON 文件路径"))
    FString JsonFilePath = TEXT("D:/tmp/twinscene_parse_result.json");

    // ═══════════════════════════════════════════════════════════════════════
    // 公开接口（供 TwinSceneManager 调用）
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * 从已解析的墙体数据数组中生成所有墙面
     * @param WallDataArray  墙体数据数组
     */
    UFUNCTION(BlueprintCallable, Category="CAD 生成器")
    void BuildWalls(const TArray<FTwinWallData>& WallDataArray);

    /**
     * 从 JSON 字符串中解析并生成墙面
     * @param JsonString  符合 twinscene_parse_result.json 格式的 JSON 字符串
     */
    UFUNCTION(BlueprintCallable, Category="CAD 生成器")
    void BuildWallsFromJsonString(const FString& JsonString);

    /**
     * 清除当前生成的所有墙体网格
     */
    UFUNCTION(BlueprintCallable, Category="CAD 生成器")
    void ClearAllWalls();

protected:
    virtual void OnConstruction(const FTransform& Transform) override;

private:
    /**
     * 核心几何算法：将单条 2D 路径拉伸为 3D 墙面 Mesh
     * 将三角面片数据写入 RMC Builder
     */
    void ExtrudeWallSegment(
        RealtimeMesh::TRealtimeMeshBuilderLocal<uint16, FPackedNormal, FVector2DHalf, 1>& Builder,
        const FTwinWallData& WallData,
        int32& PolyGroupIndex);

    /** 从 JSON 字符串中解析出墙体数据数组 */
    bool ParseJsonToWallData(const FString& JsonString, TArray<FTwinWallData>& OutWallData);
};
