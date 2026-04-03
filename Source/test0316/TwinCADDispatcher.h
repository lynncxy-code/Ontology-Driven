// ============================================================================
// TwinCADDispatcher.h
//
// CAD 一键生成调度器 — 从 JSON 文件读取并分发生成指令
//
// 功能说明：
//   1. 读取由 Web 端导出的 twinscene_parse_result.json
//   2. 将 PROCEDURAL_WALL 类型指令转发给 ATwinStructureBuilder 生成墙体
//   3. 将 INSTANCE 类型指令转发给 ATwinColumnPlacer 批量摆放立柱
//   4. 提供编辑器按钮"🚀 一键生成全部"用于一步到位场景构建
//
// 使用方式：
//   在关卡中拖入一个 ATwinCADDispatcher Actor，
//   配置好 JSON 文件路径后，点击按钮即可一键生成完整场景
//
// 依赖：
//   ATwinStructureBuilder, ATwinColumnPlacer
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Http.h"
#include "TwinCADDispatcher.generated.h"

class ATwinStructureBuilder;
class ATwinColumnPlacer;

/**
 * ATwinCADDispatcher
 *
 * 场景级总调度器。读取 CAD JSON，自动创建或查找 Builder/Placer 并委派生成任务。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(DisplayName="CAD 一键生成调度器"))
class TEST0316_API ATwinCADDispatcher : public AActor
{
    GENERATED_BODY()

public:
    ATwinCADDispatcher();

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器可配置属性
    // ═══════════════════════════════════════════════════════════════════════

    /** 后端 API 地址（解析概览页面会显示此地址，直接复制过来填入即可）
     *  默认值: http://127.0.0.1:5000/api/v2/cad/latest */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|接入",
              meta=(DisplayName="后端 API 地址"))
    FString ApiUrl = TEXT("http://127.0.0.1:5000/api/v2/cad/latest");

    // ═══════════════════════════════════════════════════════════════════════
    // 柱体与映射配置
    // ═══════════════════════════════════════════════════════════════════════

    /** DXF 坐标到 UE 坐标的缩放因子（mm → cm，默认 0.1） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|参数配置", meta=(DisplayName="坐标全局缩放 (mm→cm)"))
    float CoordScale = 0.1f;

    /** 柱体缩放倍数（当导入的模型太小时，可在此处放大） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|参数配置", meta=(DisplayName="柱体整体缩放倍数"))
    FVector ColumnScaleMultiplier = FVector(1.0f, 1.0f, 1.0f);

    /** 默认墙面材质（生成墙体网格时使用的材质包） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|参数配置", meta=(DisplayName="默认墙面材质（如果留空则使用纯色或缺省材质）"))
    class UMaterialInterface* DefaultWallMaterial = nullptr;

    /** mesh_id → UE 资产路径映射表 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|参数配置", meta=(DisplayName="柱体模型映射表 (DataTable)"))
    class UDataTable* MeshMappingTable = nullptr;

    /** 默认静态网格体（当无法映射时使用，建议在此拖入你的 SM_Pole_01） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|参数配置", meta=(DisplayName="默认立柱网格（Fallback）"))
    class UStaticMesh* DefaultColumnMesh = nullptr;

    /** 场景中已有的墙体生成器引用（如果为空则自动 Spawn） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|引用",
              meta=(DisplayName="墙体生成器"))
    ATwinStructureBuilder* StructureBuilder = nullptr;

    /** 场景中已有的立柱摆放器引用（如果为空则自动 Spawn） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="CAD 调度器|引用",
              meta=(DisplayName="立柱摆放器"))
    ATwinColumnPlacer* ColumnPlacer = nullptr;

    // ═══════════════════════════════════════════════════════════════════════
    // 编辑器按钮
    // ═══════════════════════════════════════════════════════════════════════

    /** 🚀 一键生成全部：从后端拉取 JSON → 生成墙体 + 摆放立柱 */
    UFUNCTION(CallInEditor, Category="CAD 调度器|工具",
              meta=(DisplayName="🚀 一键生成全部"))
    void GenerateAll();

    /** 🧹 清除所有已生成的内容 */
    UFUNCTION(CallInEditor, Category="CAD 调度器|工具",
              meta=(DisplayName="🧹 清除已生成内容"))
    void ClearAll();

protected:
    virtual void BeginPlay() override;

private:
    /** 确保场景中存在 StructureBuilder（如无则 Spawn） */
    ATwinStructureBuilder* EnsureStructureBuilder();

    /** 确保场景中存在 ColumnPlacer（如无则 Spawn） */
    ATwinColumnPlacer* EnsureColumnPlacer();

    /** HTTP 响应回调：从 URL 请求到 JSON 后解析并分发生成 */
    void OnHttpResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    /** 从 JSON 字符串分发生成（被 HTTP 回调和本地调用两点共用） */
    void DispatchFromJsonString(const FString& JsonString);
};
