// ============================================================================
// TwinStructureBuilder.cpp
//
// CAD 墙体程序化生成器 — 核心几何拉伸算法实现
//
// 算法说明：
//   对于每段墙体路径 (P0→P1→P2→...):
//   1. 计算每段线段的法线方向（垂直于线段方向，向两侧偏移 thickness/2）
//   2. 在底部和顶部各生成内外两排顶点（共 4 排顶点）
//   3. 将相邻顶点连成三角面片构成封闭的 box-like 墙面
//   4. 顶部和底部用盖面封顶
// ============================================================================

#include "TwinStructureBuilder.h"
#include "RealtimeMeshSimple.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

using namespace RealtimeMesh;

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinStructureBuilder::ATwinStructureBuilder()
{
    PrimaryActorTick.bCanEverTick = false;
}

// ── OnConstruction ───────────────────────────────────────────────────────────

void ATwinStructureBuilder::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    // 编辑器中不自动生成，等用户点击按钮或 BeginPlay 调用
}

// ═══════════════════════════════════════════════════════════════════════════
// 编辑器按钮：从 JSON 文件生成
// ═══════════════════════════════════════════════════════════════════════════

void ATwinStructureBuilder::BuildFromJsonFile()
{
    if (JsonFilePath.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] JSON 文件路径为空！"));
        return;
    }

    FString JsonString;
    if (!FFileHelper::LoadFileToString(JsonString, *JsonFilePath))
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] 无法读取文件: %s"), *JsonFilePath);
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red,
                FString::Printf(TEXT("❌ 无法读取 JSON 文件: %s"), *JsonFilePath));
        }
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("[CAD 生成器] 已加载 JSON 文件，大小: %d 字节"), JsonString.Len());
    BuildWallsFromJsonString(JsonString);
}

// ═══════════════════════════════════════════════════════════════════════════
// JSON 解析
// ═══════════════════════════════════════════════════════════════════════════

bool ATwinStructureBuilder::ParseJsonToWallData(const FString& JsonString, TArray<FTwinWallData>& OutWallData)
{
    TSharedPtr<FJsonObject> RootObj;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);

    if (!FJsonSerializer::Deserialize(Reader, RootObj) || !RootObj.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] JSON 反序列化失败！"));
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* EntitiesArray;
    if (!RootObj->TryGetArrayField(TEXT("entities"), EntitiesArray))
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] JSON 中没有 'entities' 数组！"));
        return false;
    }

    int32 WallCount = 0;
    for (const auto& Val : *EntitiesArray)
    {
        const TSharedPtr<FJsonObject>* EntityObj;
        if (!Val->TryGetObject(EntityObj)) continue;

        FString GenType;
        if (!(*EntityObj)->TryGetStringField(TEXT("generate_type"), GenType)) continue;

        if (GenType != TEXT("PROCEDURAL_WALL")) continue;

        // 读取 data 子对象
        const TSharedPtr<FJsonObject>* DataObj;
        if (!(*EntityObj)->TryGetObjectField(TEXT("data"), DataObj)) continue;

        FTwinWallData WallData;

        // 解析 path 二维数组
        const TArray<TSharedPtr<FJsonValue>>* PathArray;
        if ((*DataObj)->TryGetArrayField(TEXT("path"), PathArray))
        {
            for (const auto& PointVal : *PathArray)
            {
                const TArray<TSharedPtr<FJsonValue>>* PointArr;
                if (PointVal->TryGetArray(PointArr) && PointArr->Num() >= 2)
                {
                    double X = (*PointArr)[0]->AsNumber();
                    double Y = (*PointArr)[1]->AsNumber();
                    WallData.Path.Add(FVector2D(X, Y));
                }
            }
        }

        // 读取 height / thickness
        double H = 4500.0, T = 240.0;
        (*DataObj)->TryGetNumberField(TEXT("height"), H);
        (*DataObj)->TryGetNumberField(TEXT("thickness"), T);
        WallData.Height = static_cast<float>(H);
        WallData.Thickness = static_cast<float>(T);

        if (WallData.Path.Num() >= 2)
        {
            OutWallData.Add(WallData);
            WallCount++;
        }
    }

    UE_LOG(LogTemp, Log, TEXT("[CAD 生成器] 从 JSON 解析出 %d 面墙体"), WallCount);
    return WallCount > 0;
}

// ═══════════════════════════════════════════════════════════════════════════
// 从 JSON 字符串生成
// ═══════════════════════════════════════════════════════════════════════════

void ATwinStructureBuilder::BuildWallsFromJsonString(const FString& JsonString)
{
    TArray<FTwinWallData> WallDataArray;
    if (!ParseJsonToWallData(JsonString, WallDataArray))
    {
        UE_LOG(LogTemp, Warning, TEXT("[CAD 生成器] 未解析到任何墙体数据"));
        return;
    }
    BuildWalls(WallDataArray);
}

// ═══════════════════════════════════════════════════════════════════════════
// 清除所有墙体
// ═══════════════════════════════════════════════════════════════════════════

void ATwinStructureBuilder::ClearAllWalls()
{
    URealtimeMeshComponent* RMC_Comp = GetRealtimeMeshComponent();
    if (RMC_Comp)
    {
        URealtimeMeshSimple* RealtimeMesh = RMC_Comp->GetRealtimeMeshAs<URealtimeMeshSimple>();
        if (RealtimeMesh)
        {
            RealtimeMesh->Reset();
            UE_LOG(LogTemp, Log, TEXT("[CAD 生成器] 已清除所有墙体网格"));
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 核心生成入口
// ═══════════════════════════════════════════════════════════════════════════

void ATwinStructureBuilder::BuildWalls(const TArray<FTwinWallData>& WallDataArray)
{
    URealtimeMeshComponent* RMC_Comp = GetRealtimeMeshComponent();
    if (!RMC_Comp)
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] 找不到 RealtimeMeshComponent！"));
        return;
    }

    URealtimeMeshSimple* RealtimeMesh = RMC_Comp->InitializeRealtimeMesh<URealtimeMeshSimple>();
    if (!RealtimeMesh)
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 生成器] 无法初始化 RealtimeMeshSimple！"));
        return;
    }

    // ── 准备流数据 ────────────────────────────────────────────────────────────
    FRealtimeMeshStreamSet StreamSet;
    TRealtimeMeshBuilderLocal<uint16, FPackedNormal, FVector2DHalf, 1> Builder(StreamSet);

    Builder.EnableTangents();
    Builder.EnableTexCoords();
    Builder.EnableColors();
    Builder.EnablePolyGroups();

    int32 PolyGroupIndex = 0;

    // ── 为每面墙生成几何体 ─────────────────────────────────────────────────
    for (const FTwinWallData& WallData : WallDataArray)
    {
        ExtrudeWallSegment(Builder, WallData, PolyGroupIndex);
    }

    UE_LOG(LogTemp, Log, TEXT("[CAD 生成器] 总计生成 %d 面墙体的网格数据"), WallDataArray.Num());

    // ── 创建材质插槽 ──────────────────────────────────────────────────────
    RealtimeMesh->SetupMaterialSlot(0, FName("WallMaterial"), WallMaterial);
    if (WallMaterial)
    {
        RMC_Comp->SetMaterial(0, WallMaterial);
    }

    const FRealtimeMeshSectionGroupKey GroupKey =
        FRealtimeMeshSectionGroupKey::Create(0, FName("CAD_Walls"));

    RealtimeMesh->CreateSectionGroup(GroupKey, StreamSet);

    // 显示指定：将 PolyGroup 0 映射到 Material Slot 0
    RealtimeMesh->UpdateSectionConfig(
        FRealtimeMeshSectionKey::CreateForPolyGroup(GroupKey, 0), 
        FRealtimeMeshSectionConfig(0)
    );

    // 屏幕提示
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green,
            FString::Printf(TEXT("🏗️ 已成功生成 %d 面墙体！"), WallDataArray.Num()));
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 核心几何算法：2D 折线 → 3D 六面体墙面拉伸
// ═══════════════════════════════════════════════════════════════════════════

void ATwinStructureBuilder::ExtrudeWallSegment(
    TRealtimeMeshBuilderLocal<uint16, FPackedNormal, FVector2DHalf, 1>& Builder,
    const FTwinWallData& WallData,
    int32& PolyGroupIndex)
{
    const float HalfThick = WallData.Thickness * CoordScale * 0.5f;
    const float WallHeight = WallData.Height * CoordScale;
    const TArray<FVector2D>& Path = WallData.Path;

    if (Path.Num() < 2) return;

    // ── 为每段线段生成墙面 ─────────────────────────────────────────────────
    for (int32 i = 0; i < Path.Num() - 1; ++i)
    {
        // DXF 坐标 → UE 坐标（X=X, Y=Y, Z=up）
        // 注意：DXF 的 Y 轴对应 UE 的 Y 轴，高度在 Z 轴
        FVector2D P0 = Path[i] * CoordScale;
        FVector2D P1 = Path[i + 1] * CoordScale;

        // 线段方向
        FVector2D Dir = (P1 - P0);
        float SegLength = Dir.Size();
        if (SegLength < KINDA_SMALL_NUMBER) continue;
        Dir /= SegLength;

        // 法线方向（左手坐标系中向左的法线）
        FVector2D Normal(-Dir.Y, Dir.X);

        // ── 计算 8 个顶点（底面 4 个 + 顶面 4 个）────────────────────────
        //
        //   外侧 (Outer)                      内侧 (Inner)
        //     6───────7 (Top)                    4───────5 (Top)  
        //     │       │                          │       │
        //     │       │           ← Normal →     │       │
        //     │       │                          │       │
        //     2───────3 (Bottom)                  0───────1 (Bottom)
        //    P0端     P1端                       P0端     P1端
        //

        // 内侧底面
        FVector3f V0(P0.X - Normal.X * HalfThick, P0.Y - Normal.Y * HalfThick, 0.0f);
        FVector3f V1(P1.X - Normal.X * HalfThick, P1.Y - Normal.Y * HalfThick, 0.0f);
        // 外侧底面
        FVector3f V2(P0.X + Normal.X * HalfThick, P0.Y + Normal.Y * HalfThick, 0.0f);
        FVector3f V3(P1.X + Normal.X * HalfThick, P1.Y + Normal.Y * HalfThick, 0.0f);
        // 内侧顶面
        FVector3f V4(V0.X, V0.Y, WallHeight);
        FVector3f V5(V1.X, V1.Y, WallHeight);
        // 外侧顶面
        FVector3f V6(V2.X, V2.Y, WallHeight);
        FVector3f V7(V3.X, V3.Y, WallHeight);

        // ── 法线和UV计算 ──────────────────────────────────────────────────
        FVector3f FaceNormal_Outer(Normal.X, Normal.Y, 0.0f);
        FVector3f FaceNormal_Inner(-Normal.X, -Normal.Y, 0.0f);
        FVector3f FaceNormal_Top(0.0f, 0.0f, 1.0f);
        FVector3f FaceNormal_Bottom(0.0f, 0.0f, -1.0f);
        FVector3f FaceNormal_StartCap(-Dir.X, -Dir.Y, 0.0f);
        FVector3f FaceNormal_EndCap(Dir.X, Dir.Y, 0.0f);

        // 切线方向（沿着墙面方向）
        FVector3f Tangent(Dir.X, Dir.Y, 0.0f);
        FVector3f TangentVert(0.0f, 0.0f, 1.0f);

        float ULen = SegLength / 100.0f; // UV 按 1m 铺满
        float VHeight = WallHeight / 100.0f;

        // ── 外侧面 (4 顶点, 2 三角形) ──────────────────────────────────────
        int32 Idx = Builder.AddVertex(V2).SetNormalAndTangent(FaceNormal_Outer, Tangent)
            .SetTexCoord(FVector2f(0.0f, VHeight)).SetColor(FColor::White);
        Builder.AddVertex(V3).SetNormalAndTangent(FaceNormal_Outer, Tangent)
            .SetTexCoord(FVector2f(ULen, VHeight)).SetColor(FColor::White);
        Builder.AddVertex(V7).SetNormalAndTangent(FaceNormal_Outer, Tangent)
            .SetTexCoord(FVector2f(ULen, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V6).SetNormalAndTangent(FaceNormal_Outer, Tangent)
            .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
        Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
        Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);

        // ── 内侧面 ──────────────────────────────────────────────────────────
        Idx = Builder.AddVertex(V1).SetNormalAndTangent(FaceNormal_Inner, Tangent)
            .SetTexCoord(FVector2f(0.0f, VHeight)).SetColor(FColor::White);
        Builder.AddVertex(V0).SetNormalAndTangent(FaceNormal_Inner, Tangent)
            .SetTexCoord(FVector2f(ULen, VHeight)).SetColor(FColor::White);
        Builder.AddVertex(V4).SetNormalAndTangent(FaceNormal_Inner, Tangent)
            .SetTexCoord(FVector2f(ULen, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V5).SetNormalAndTangent(FaceNormal_Inner, Tangent)
            .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
        Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
        Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);

        // ── 顶面 ────────────────────────────────────────────────────────────
        Idx = Builder.AddVertex(V6).SetNormalAndTangent(FaceNormal_Top, Tangent)
            .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V7).SetNormalAndTangent(FaceNormal_Top, Tangent)
            .SetTexCoord(FVector2f(ULen, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V5).SetNormalAndTangent(FaceNormal_Top, Tangent)
            .SetTexCoord(FVector2f(ULen, 1.0f)).SetColor(FColor::White);
        Builder.AddVertex(V4).SetNormalAndTangent(FaceNormal_Top, Tangent)
            .SetTexCoord(FVector2f(0.0f, 1.0f)).SetColor(FColor::White);
        Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
        Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);

        // ── 底面 ────────────────────────────────────────────────────────────
        Idx = Builder.AddVertex(V0).SetNormalAndTangent(FaceNormal_Bottom, Tangent)
            .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V1).SetNormalAndTangent(FaceNormal_Bottom, Tangent)
            .SetTexCoord(FVector2f(ULen, 0.0f)).SetColor(FColor::White);
        Builder.AddVertex(V3).SetNormalAndTangent(FaceNormal_Bottom, Tangent)
            .SetTexCoord(FVector2f(ULen, 1.0f)).SetColor(FColor::White);
        Builder.AddVertex(V2).SetNormalAndTangent(FaceNormal_Bottom, Tangent)
            .SetTexCoord(FVector2f(0.0f, 1.0f)).SetColor(FColor::White);
        Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
        Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);

        // ── 端面 (P0 端) — 仅在第一段时生成 ─────────────────────────────
        if (i == 0)
        {
            Idx = Builder.AddVertex(V0).SetNormalAndTangent(FaceNormal_StartCap, TangentVert)
                .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
            Builder.AddVertex(V2).SetNormalAndTangent(FaceNormal_StartCap, TangentVert)
                .SetTexCoord(FVector2f(1.0f, 0.0f)).SetColor(FColor::White);
            Builder.AddVertex(V6).SetNormalAndTangent(FaceNormal_StartCap, TangentVert)
                .SetTexCoord(FVector2f(1.0f, VHeight)).SetColor(FColor::White);
            Builder.AddVertex(V4).SetNormalAndTangent(FaceNormal_StartCap, TangentVert)
                .SetTexCoord(FVector2f(0.0f, VHeight)).SetColor(FColor::White);
            Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
            Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);
        }

        // ── 端面 (P1 端) — 仅在最后一段时生成 ───────────────────────────
        if (i == Path.Num() - 2)
        {
            Idx = Builder.AddVertex(V3).SetNormalAndTangent(FaceNormal_EndCap, TangentVert)
                .SetTexCoord(FVector2f(0.0f, 0.0f)).SetColor(FColor::White);
            Builder.AddVertex(V1).SetNormalAndTangent(FaceNormal_EndCap, TangentVert)
                .SetTexCoord(FVector2f(1.0f, 0.0f)).SetColor(FColor::White);
            Builder.AddVertex(V5).SetNormalAndTangent(FaceNormal_EndCap, TangentVert)
                .SetTexCoord(FVector2f(1.0f, VHeight)).SetColor(FColor::White);
            Builder.AddVertex(V7).SetNormalAndTangent(FaceNormal_EndCap, TangentVert)
                .SetTexCoord(FVector2f(0.0f, VHeight)).SetColor(FColor::White);
            Builder.AddTriangle(Idx, Idx+1, Idx+2, 0);
            Builder.AddTriangle(Idx, Idx+2, Idx+3, 0);
        }
    }

    PolyGroupIndex++;
}
