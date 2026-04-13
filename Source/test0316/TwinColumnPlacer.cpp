// ============================================================================
// TwinColumnPlacer.cpp
//
// 立柱批量实例化摆放器 — HISM 实现
// ============================================================================

#include "TwinColumnPlacer.h"
#include "Engine/StaticMesh.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinColumnPlacer::ATwinColumnPlacer()
{
    PrimaryActorTick.bCanEverTick = false;

    // 创建根组件
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("RootComponent"));
    SetRootComponent(Root);
}

// ═══════════════════════════════════════════════════════════════════════════
// 从 DataTable 查找 MeshId 对应的 StaticMesh
// ═══════════════════════════════════════════════════════════════════════════

UStaticMesh* ATwinColumnPlacer::ResolveMesh(const FString& MeshId)
{
    if (MeshMappingTable)
    {
        TArray<FTwinMeshMapping*> AllRows;
        MeshMappingTable->GetAllRows<FTwinMeshMapping>(TEXT("ResolveMesh"), AllRows);

        for (const FTwinMeshMapping* Row : AllRows)
        {
            if (Row && Row->MeshId == MeshId)
            {
                UStaticMesh* Mesh = Row->MeshAsset.LoadSynchronous();
                if (Mesh)
                {
                    UE_LOG(LogTemp, Log, TEXT("[立柱摆放器] DataTable 命中: %s → %s"),
                           *MeshId, *Mesh->GetPathName());
                    return Mesh;
                }
            }
        }

        UE_LOG(LogTemp, Warning,
               TEXT("[立柱摆放器] DataTable 中未找到 MeshId=%s，尝试使用默认网格"), *MeshId);
    }

    // 用户配置的默认网格
    if (DefaultColumnMesh)
        return DefaultColumnMesh;

    // ── 终极 Fallback：使用 FSoftObjectPath 加载 SM_Pole_01 ─────────
    FSoftObjectPath PolePath(TEXT("/Game/WarehouseProps_Bundle/Models/SM_Pole_01.SM_Pole_01"));
    UObject* LoadedObj = PolePath.TryLoad();
    UStaticMesh* FallbackMesh = Cast<UStaticMesh>(LoadedObj);

    if (FallbackMesh)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[立柱摆放器] MeshId=%s 未配置，使用备用网格 SM_Pole_01 占位"),
               *MeshId);
        return FallbackMesh;
    }

    // 再尝试引擎自带的基础圆柱体
    FSoftObjectPath CylinderPath(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    UStaticMesh* EngineCylinder = Cast<UStaticMesh>(CylinderPath.TryLoad());
    if (EngineCylinder)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[立柱摆放器] MeshId=%s 未配置，使用引擎默认圆柱体占位"),
               *MeshId);
        return EngineCylinder;
    }

    UE_LOG(LogTemp, Error, TEXT("[立柱摆放器] 找不到目标 Mesh，所有 Fallback 均失败！请在 Dispatcher 中设置默认立柱网格。"));
    return nullptr;
}

// ═══════════════════════════════════════════════════════════════════════════
// 获取或创建 HISM 组件
// ═══════════════════════════════════════════════════════════════════════════

UHierarchicalInstancedStaticMeshComponent* ATwinColumnPlacer::GetOrCreateHISM(const FString& MeshId)
{
    // 先查缓存
    if (UHierarchicalInstancedStaticMeshComponent** Found = HISMRegistry.Find(MeshId))
    {
        if (*Found && IsValid(*Found))
        {
            return *Found;
        }
    }

    // 创建新的 HISM 组件
    UHierarchicalInstancedStaticMeshComponent* NewHISM =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(this,
            FName(*FString::Printf(TEXT("HISM_%s"), *MeshId)));

    NewHISM->SetupAttachment(GetRootComponent());

    // 查找并设置对应的 StaticMesh
    UStaticMesh* Mesh = ResolveMesh(MeshId);
    if (Mesh)
    {
        NewHISM->SetStaticMesh(Mesh);
    }
    else
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[立柱摆放器] MeshId=%s 无法解析到任何网格体，HISM 组件将无可视内容"),
               *MeshId);
    }

    // 设置材质
    if (ColumnMaterial && Mesh)
    {
        for (int32 i = 0; i < Mesh->GetStaticMaterials().Num(); ++i)
        {
            NewHISM->SetMaterial(i, ColumnMaterial);
        }
    }

    // 优化设置
    NewHISM->SetCullDistances(0, 50000); // 500m 裁剪距离
    NewHISM->bUseAsOccluder = false;

    // **重点修复**：必须在设置完 Mesh 和属性之后，再注册组件！
    NewHISM->RegisterComponent();

    HISMRegistry.Add(MeshId, NewHISM);

    UE_LOG(LogTemp, Log, TEXT("[立柱摆放器] 创建 HISM 组件: %s"), *MeshId);
    return NewHISM;
}

// ═══════════════════════════════════════════════════════════════════════════
// 批量摆放立柱
// ═══════════════════════════════════════════════════════════════════════════

void ATwinColumnPlacer::PlaceColumns(const TArray<FTwinColumnData>& ColumnDataArray)
{
    if (ColumnDataArray.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[立柱摆放器] 无立柱数据可用"));
        return;
    }

    int32 PlacedCount = 0;

    for (const FTwinColumnData& ColData : ColumnDataArray)
    {
        UHierarchicalInstancedStaticMeshComponent* HISM = GetOrCreateHISM(ColData.MeshId);
        if (!HISM || !HISM->GetStaticMesh()) continue;

        // DXF mm → UE cm
        FVector ScaledLoc = ColData.Location * CoordScale;
        FRotator Rot = ColData.Rotation;
        FVector Scale = ColData.Scale * ColumnScaleMultiplier;

        FTransform InstanceTransform(Rot, ScaledLoc, Scale);
        HISM->AddInstance(InstanceTransform, /*bWorldSpace=*/true);

        PlacedCount++;
    }

    UE_LOG(LogTemp, Log, TEXT("[立柱摆放器] 已批量摆放 %d 根立柱"), PlacedCount);

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Cyan,
            FString::Printf(TEXT("🏛️ 已摆放 %d 根立柱实例"), PlacedCount));
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 清除所有实例
// ═══════════════════════════════════════════════════════════════════════════

void ATwinColumnPlacer::ClearAllInstances()
{
    for (auto& Pair : HISMRegistry)
    {
        if (Pair.Value && IsValid(Pair.Value))
        {
            // 只清除实例，不销毁组件，保持 Actor 状态完整性以便下次重用
            Pair.Value->ClearInstances();
        }
    }
    // 保留 HISMRegistry 缓存，重新生成时可直接复用已有组件
    UE_LOG(LogTemp, Log, TEXT("[立柱摆放器] 已清除所有立柱实例"));
}

// ═══════════════════════════════════════════════════════════════════════════
// JSON 解析
// ═══════════════════════════════════════════════════════════════════════════

bool ATwinColumnPlacer::ParseJsonToColumnData(const FString& JsonString, TArray<FTwinColumnData>& OutColumnData)
{
    TSharedPtr<FJsonObject> RootObj;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);

    if (!FJsonSerializer::Deserialize(Reader, RootObj) || !RootObj.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[立柱摆放器] JSON 反序列化失败！"));
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* EntitiesArray;
    if (!RootObj->TryGetArrayField(TEXT("entities"), EntitiesArray))
    {
        return false;
    }

    int32 Count = 0;
    for (const auto& Val : *EntitiesArray)
    {
        const TSharedPtr<FJsonObject>* EntityObj;
        if (!Val->TryGetObject(EntityObj)) continue;

        FString GenType;
        if (!(*EntityObj)->TryGetStringField(TEXT("generate_type"), GenType)) continue;
        if (GenType != TEXT("INSTANCE")) continue;

        const TSharedPtr<FJsonObject>* DataObj;
        if (!(*EntityObj)->TryGetObjectField(TEXT("data"), DataObj)) continue;

        FTwinColumnData ColData;

        // mesh_id
        (*DataObj)->TryGetStringField(TEXT("mesh_id"), ColData.MeshId);

        // transform
        const TSharedPtr<FJsonObject>* TransformObj;
        if ((*DataObj)->TryGetObjectField(TEXT("transform"), TransformObj))
        {
            // loc
            const TArray<TSharedPtr<FJsonValue>>* LocArr;
            if ((*TransformObj)->TryGetArrayField(TEXT("loc"), LocArr) && LocArr->Num() >= 3)
            {
                ColData.Location = FVector(
                    (*LocArr)[0]->AsNumber(),
                    (*LocArr)[1]->AsNumber(),
                    (*LocArr)[2]->AsNumber()
                );
            }

            // rot
            const TArray<TSharedPtr<FJsonValue>>* RotArr;
            if ((*TransformObj)->TryGetArrayField(TEXT("rot"), RotArr) && RotArr->Num() >= 3)
            {
                ColData.Rotation = FRotator(
                    (*RotArr)[0]->AsNumber(),  // Pitch
                    (*RotArr)[2]->AsNumber(),  // Yaw (DXF rotation around Z)
                    (*RotArr)[1]->AsNumber()   // Roll
                );
            }

            // scale
            const TArray<TSharedPtr<FJsonValue>>* ScaleArr;
            if ((*TransformObj)->TryGetArrayField(TEXT("scale"), ScaleArr) && ScaleArr->Num() >= 3)
            {
                ColData.Scale = FVector(
                    (*ScaleArr)[0]->AsNumber(),
                    (*ScaleArr)[1]->AsNumber(),
                    (*ScaleArr)[2]->AsNumber()
                );
            }
        }

        OutColumnData.Add(ColData);
        Count++;
    }

    UE_LOG(LogTemp, Log, TEXT("[立柱摆放器] 从 JSON 解析出 %d 根立柱"), Count);
    return Count > 0;
}
