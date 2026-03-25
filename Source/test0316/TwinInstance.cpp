// ============================================================================
// TwinInstance.cpp  (修复版)
//
// 修复点：
//   1. 构造函数移除 SetVisibility(false)，改由 SetActorHiddenInGame 控制
//   2. LoadMeshFromPath 失败时也正确显示占位立方体
//   3. 增加全链路诊断日志，便于 Output Log 排查
// ============================================================================

#include "TwinInstance.h"
#include "DigitalTwinSyncComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"
#include "Kismet/KismetMathLibrary.h"

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinInstance::ATwinInstance()
{
    PrimaryActorTick.bCanEverTick = false; // 不需要 Tick，由 SceneManager 推送状态

    // 创建默认的 StaticMeshComponent 作为根组件
    MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TwinMesh"));
    RootComponent = MeshComponent;

    // ⚠️ 修复：不在构造函数里隐藏组件
    // 可见性由 InitializeTwin / ApplyRepresentableFromSnapshot 控制
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinInstance::BeginPlay()
{
    Super::BeginPlay();
}

// ═══════════════════════════════════════════════════════════════════════════
// 公开接口
// ═══════════════════════════════════════════════════════════════════════════

void ATwinInstance::InitializeTwin(
    const FString& InInstanceId,
    const FString& InAssetPath,
    const FString& InBackendBaseUrl)
{
    InstanceId     = InInstanceId;
    AssetPath      = InAssetPath;
    BackendBaseUrl = InBackendBaseUrl;

    UE_LOG(LogTemp, Log, TEXT("[孪生体] ████ 初始化开始 | ID=%s | 资产路径=%s"), *InstanceId, *AssetPath);

    // ── 1. 加载 StaticMesh ───────────────────────────────────────────────
    if (AssetPath.IsEmpty())
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生体] ⚠️  资产路径为空 (ID=%s)，使用默认立方体"), *InstanceId);
        // 使用引擎内置立方体兜底
        UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(
            nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
        if (CubeMesh)
        {
            MeshComponent->SetStaticMesh(CubeMesh);
            MeshComponent->SetWorldScale3D(FVector(0.5f));
        }
    }
    else
    {
        LoadMeshFromPath(AssetPath);
    }

    // ── 2. 缓存原始材质 ──────────────────────────────────────────────────
    if (MeshComponent->GetStaticMesh() && MeshComponent->GetNumMaterials() > 0)
    {
        CacheOriginalMaterials();
    }

    bInitialized = true;
    UE_LOG(LogTemp, Log, TEXT("[孪生体] ████ 初始化完成 | ID=%s"), *InstanceId);
}

void ATwinInstance::ApplySnapshot(const TSharedPtr<FJsonObject>& Snapshot)
{
    if (!Snapshot.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("[孪生体] ApplySnapshot: Snapshot 无效 (ID=%s)"), *InstanceId);
        return;
    }

    const TSharedPtr<FJsonObject>* InterfacesObj;
    if (!Snapshot->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生体] ApplySnapshot: 快照中无 'interfaces' 字段 (ID=%s)"), *InstanceId);
        return;
    }

    UE_LOG(LogTemp, Verbose, TEXT("[孪生体] 应用快照 (ID=%s)"), *InstanceId);

    // ── I3D_Representable ────────────────────────────────────────────────
    const TSharedPtr<FJsonObject>* RepObj;
    if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
    {
        ApplyRepresentableFromSnapshot(*RepObj);
    }

    // ── I3D_Spatial ──────────────────────────────────────────────────────
    const TSharedPtr<FJsonObject>* SpatialObj;
    if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Spatial"), SpatialObj))
    {
        ApplySpatialFromSnapshot(*SpatialObj);
    }

    // ── I3D_Visual ───────────────────────────────────────────────────────
    const TSharedPtr<FJsonObject>* VisualObj;
    if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Visual"), VisualObj))
    {
        ApplyVisualFromSnapshot(*VisualObj);
    }

    // ── I3D_Behavioral ──────────────────────────────────────────────────
    const TSharedPtr<FJsonObject>* BehaviorObj;
    if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Behavioral"), BehaviorObj))
    {
        ApplyBehavioralFromSnapshot(*BehaviorObj);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 资产加载
// ═══════════════════════════════════════════════════════════════════════════

bool ATwinInstance::LoadMeshFromPath(const FString& MeshPath)
{
    // UE 内容路径格式："/Game/WarehouseProps_Bundle/Models/SM_Pallet_01a"
    // LoadObject 需要完整的对象路径："/Game/.../SM_Pallet_01a.SM_Pallet_01a"
    FString FullPath = MeshPath;
    if (!FullPath.Contains(TEXT(".")))
    {
        // 从路径中提取资产名称（最后一段）
        FString AssetName;
        MeshPath.Split(TEXT("/"), nullptr, &AssetName, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
        FullPath = FString::Printf(TEXT("%s.%s"), *MeshPath, *AssetName);
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生体] 尝试加载: %s"), *FullPath);
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *FullPath);

    if (!Mesh)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生体] 路径1加载失败，尝试原始路径: %s"), *MeshPath);
        Mesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
    }

    if (Mesh)
    {
        MeshComponent->SetStaticMesh(Mesh);
        CacheOriginalMaterials();
        UE_LOG(LogTemp, Log, TEXT("[孪生体] ✅ 资产加载成功: %s"), *MeshPath);
        return true;
    }

    // ── 加载失败：使用引擎内置立方体作为占位符 ──────────────────────────
    UE_LOG(LogTemp, Error,
           TEXT("[孪生体] ❌ 资产加载失败: %s\n   完整路径: %s\n   请检查 UE 内容路径是否正确"),
           *MeshPath, *FullPath);

    UStaticMesh* DefaultMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (DefaultMesh)
    {
        MeshComponent->SetStaticMesh(DefaultMesh);
        MeshComponent->SetWorldScale3D(FVector(0.5f));
        UE_LOG(LogTemp, Warning, TEXT("[孪生体] 使用默认立方体占位 (ID=%s)"), *InstanceId);
    }
    return false;
}

// ═══════════════════════════════════════════════════════════════════════════
// I3D_Representable — 存在性与可见性
// ═══════════════════════════════════════════════════════════════════════════

void ATwinInstance::ApplyRepresentableFromSnapshot(const TSharedPtr<FJsonObject>& RepObj)
{
    // ── 依 PRD 规范：控制场景存在性（加载/卸载资源） ────────────
    bool bVisible = true;
    RepObj->TryGetBoolField(TEXT("is_visible"), bVisible);
    
    if (!bVisible && MeshComponent->GetStaticMesh() != nullptr)
    {
        // 从场景卸载不占内存资源
        MeshComponent->SetStaticMesh(nullptr);
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 已卸载资产: %s"), *InstanceId);
    }
    else if (bVisible && MeshComponent->GetStaticMesh() == nullptr && bInitialized)
    {
        // 重新加载并进入场景
        LoadMeshFromPath(AssetPath);
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 重新加载进入场景: %s"), *InstanceId);
    }
    // 强制把原先在这的 SetActorHiddenInGame 移除，交由 I3D_Visual 去处理纯粹的显隐

    // ── 资产热更换检测 ────────────────────────────────────────────────────
    FString NewAssetId;
    if (RepObj->TryGetStringField(TEXT("asset_id"), NewAssetId))
    {
        if (!NewAssetId.IsEmpty() && NewAssetId != AssetPath && bInitialized)
        {
            UE_LOG(LogTemp, Log,
                   TEXT("[孪生体] 资产热更换: %s → %s"), *AssetPath, *NewAssetId);
            AssetPath = NewAssetId;
            LoadMeshFromPath(AssetPath);
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// I3D_Spatial — 空间变换
// ═══════════════════════════════════════════════════════════════════════════

void ATwinInstance::ApplySpatialFromSnapshot(const TSharedPtr<FJsonObject>& SpatialObj)
{
    // 🔒 本地锁定模式：保持编辑器中设置的空间变换，忽略后端数据
    if (bLocalOverrideLock)
    {
        return;
    }

    double tx = 0, ty = 0, tz = 0;
    SpatialObj->TryGetNumberField(TEXT("translation_x"), tx);
    SpatialObj->TryGetNumberField(TEXT("translation_y"), ty);
    SpatialObj->TryGetNumberField(TEXT("translation_z"), tz);

    double rx = 0, ry = 0, rz = 0;
    SpatialObj->TryGetNumberField(TEXT("rotation_x"), rx);
    SpatialObj->TryGetNumberField(TEXT("rotation_y"), ry);
    SpatialObj->TryGetNumberField(TEXT("rotation_z"), rz);

    // [PRD B.3] 严格校验与钳位：Rotation 兜底取模，防止前端脏数据浮点溢出
    rx = FMath::Fmod(rx, 360.0);
    ry = FMath::Fmod(ry, 360.0);
    rz = FMath::Fmod(rz, 360.0);

    double sx = 1, sy = 1, sz = 1;
    SpatialObj->TryGetNumberField(TEXT("scale_x"), sx);
    SpatialObj->TryGetNumberField(TEXT("scale_y"), sy);
    SpatialObj->TryGetNumberField(TEXT("scale_z"), sz);

    FVector NewLoc = FVector(tx, ty, tz);
    FRotator NewRot = FRotator(ry, rz, rx);   // Pitch=Y, Yaw=Z, Roll=X
    
    // [PRD B.3] 严格校验与钳位：Scale 下限死锁为 0.001，防止纯 0 导致负体积断言崩溃
    FVector NewScale = FVector(
        FMath::Max(0.001, sx),
        FMath::Max(0.001, sy),
        FMath::Max(0.001, sz)
    );

    SetActorLocation(NewLoc);
    SetActorRotation(NewRot);
    SetActorScale3D(NewScale);
}

// ═══════════════════════════════════════════════════════════════════════════
// 视觉表达与行为表现
// ═══════════════════════════════════════════════════════════════════════════

void ATwinInstance::CacheOriginalMaterials()
{
    if (!MeshComponent) return;
    OriginalMaterials.Empty();
    for (int32 i = 0; i < MeshComponent->GetNumMaterials(); ++i)
    {
        OriginalMaterials.Add(MeshComponent->GetMaterial(i));
    }
}

void ATwinInstance::RestoreOriginalMaterials()
{
    if (!MeshComponent) return;
    for (int32 i = 0; i < OriginalMaterials.Num(); ++i)
    {
        if (i < MeshComponent->GetNumMaterials())
        {
            MeshComponent->SetMaterial(i, OriginalMaterials[i]);
        }
    }
}

void ATwinInstance::ApplyVisualFromSnapshot(const TSharedPtr<FJsonObject>& VisualObj)
{
    // ── 材质变体 (material_variant) ──────────────────────────────────────
    FString MaterialVariant;
    if (VisualObj->TryGetStringField(TEXT("material_variant"), MaterialVariant) && MaterialVariant != CurrentMaterialVariant)
    {
        CurrentMaterialVariant = MaterialVariant;
        
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 改变视觉状态: %s → %s"), *InstanceId, *MaterialVariant);
        
        if (MaterialVariant == TEXT("normal"))
        {
            RestoreOriginalMaterials();
        }
        else
        {
            // 交给蓝图处理字典映射
            OnMaterialVariantChanged(MaterialVariant);
        }
    }

    // ── 可见性 (is_visible) 控制纯渲染显隐 ────────────────────────────
    bool bVisualVisible = true;
    if (VisualObj->TryGetBoolField(TEXT("is_visible"), bVisualVisible))
    {
        SetActorHiddenInGame(!bVisualVisible);
    }
}

void ATwinInstance::ApplyBehavioralFromSnapshot(const TSharedPtr<FJsonObject>& BehaviorObj)
{
    FString AnimState;
    if (BehaviorObj->TryGetStringField(TEXT("animation_state"), AnimState) && AnimState != CurrentAnimState)
    {
        CurrentAnimState = AnimState;
        OnAnimationStateChanged(AnimState); // 抛出给蓝图实现
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 触发蓝图动画状态: %s"), *AnimState);
    }

    FString FxTrigger;
    if (BehaviorObj->TryGetStringField(TEXT("fx_trigger"), FxTrigger) && FxTrigger != CurrentFxTrigger)
    {
        CurrentFxTrigger = FxTrigger;
        OnFxTriggered(FxTrigger);  // 抛出给蓝图实现
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 特效触发: %s → %s"), *InstanceId, *FxTrigger);
    }

    FString LabelContent;
    if (BehaviorObj->TryGetStringField(TEXT("ui_label_content"), LabelContent))
    {
        UE_LOG(LogTemp, Verbose, TEXT("[孪生体] UI标签: %s → %s"), *InstanceId, *LabelContent);
    }
}
