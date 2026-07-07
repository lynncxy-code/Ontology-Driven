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
#include "Misc/Paths.h"
#include "HAL/PlatformProcess.h"
#include "HAL/FileManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
// HTTP —— ArtStudio glb 经后端代理流式下载（3.3）
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
// glTFRuntime —— 运行时加载磁盘上的 glb/gltf（B2 方案，模型不参与打包）
#include "glTFRuntimeFunctionLibrary.h"
#include "glTFRuntimeAsset.h"

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinInstance::ATwinInstance()
{
    // Tick 默认关闭，只有动画进行时才开启，节省性能
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;

    // 创建默认的 StaticMeshComponent 作为根组件
    MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TwinMesh"));
    RootComponent = MeshComponent;

    // 创建 3D 文字标签组件，默认隐藏
    LabelComponent = CreateDefaultSubobject<UTextRenderComponent>(TEXT("TwinLabel"));
    LabelComponent->SetupAttachment(MeshComponent);
    LabelComponent->SetRelativeLocation(FVector(0.f, 0.f, LabelZOffset)); // 默认 20cm 高
    // 恢复默认朝向 (之前为了测试曾改过 180)
    LabelComponent->SetRelativeRotation(FRotator(0.f, 0.f, 0.f));
    LabelComponent->SetHorizontalAlignment(EHTA_Center);                   // 水平居中

    LabelComponent->SetVerticalAlignment(EVRTA_TextCenter);                // 垂直居中
    LabelComponent->SetWorldSize(LabelWorldSize);                          // 字体大小
    LabelComponent->SetTextRenderColor(LabelColor);                        // 文字颜色
    LabelComponent->SetVisibility(false);                                  // 初始隐藏
    LabelComponent->SetText(FText::GetEmpty());
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinInstance::BeginPlay()
{
    Super::BeginPlay();
    InitAnimLibrary();
}

void ATwinInstance::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    // ── 3D文字始终朝向相机 (Billboarding) ──
    if (LabelComponent && LabelComponent->IsVisible())
    {
        if (APlayerCameraManager* CamManager = GetWorld()->GetFirstPlayerController()->PlayerCameraManager)
        {
            FVector CamLoc = CamManager->GetCameraLocation();
            FVector TextLoc = LabelComponent->GetComponentLocation();
            
            // 计算 LookAt 旋转
            FRotator LookAtRot = UKismetMathLibrary::FindLookAtRotation(TextLoc, CamLoc);
            
            // 只需要水平环绕相机（Yaw），强行把 Pitch 和 Roll 锁定为 0，防止文字趴在地上或者竖直歪曲
            FRotator BillboardRot(0.f, LookAtRot.Yaw, 0.f);
            
            // 如果你发现文字刚好是左右镜像反的，可以改成 BillboardRot.Yaw += 180.f; 但纯 LookAt 一般是正的！
            LabelComponent->SetWorldRotation(BillboardRot);
        }
    }

    if (!bAnimRunning) return;

    AnimTimer += DeltaTime;
    float Duration = ActiveRecipe.Duration;
    if (Duration <= 0.f) return;

    // 计算动画进度 Alpha（0.0−1.0）
    float RawAlpha = FMath::Fmod(AnimTimer, Duration) / Duration;

    // PingPong：偶数循环就反过来
    float Alpha = RawAlpha;
    if (ActiveRecipe.bPingPong)
    {
        int32 CycleIndex = FMath::FloorToInt(AnimTimer / Duration);
        if (CycleIndex % 2 == 1) Alpha = 1.0f - RawAlpha;
    }

    // 平滑曲线（SmoothStep）让动画两端更自然
    float SmoothAlpha = FMath::SmoothStep(0.f, 1.f, Alpha);

    // 应用位移
    if (!ActiveRecipe.TranslationDelta.IsNearlyZero())
    {
        FVector NewLoc = AnimBaseLocation + ActiveRecipe.TranslationDelta * SmoothAlpha;
        SetActorLocation(NewLoc);
    }

    // 应用旋转
    if (!ActiveRecipe.RotationDelta.IsNearlyZero())
    {
        FRotator Delta = ActiveRecipe.RotationDelta * SmoothAlpha;
        FRotator NewRot = AnimBaseRotation + Delta;
        SetActorRotation(NewRot);
    }

    // 如果不循环且时间到达，停止
    if (!ActiveRecipe.bLoop && AnimTimer >= Duration)
    {
        bAnimRunning = false;
        SetActorEnableCollision(true);
        // 如果文字没显示，才真正关闭 Tick
        if (!LabelComponent || !LabelComponent->IsVisible())
        {
            SetActorTickEnabled(false);
        }
    }
}

// 初始化动画配方字典
void ATwinInstance::InitAnimLibrary()
{
    AnimLibrary.Empty();

    // idle: 停止，无动画
    AnimLibrary.Add(TEXT("idle"),
        FAnimRecipe(FVector::ZeroVector, FRotator::ZeroRotator, 0.f, false, false));

    // translate: X轴平移 100cm，循环往返，3秒一霿
    AnimLibrary.Add(TEXT("translate"),
        FAnimRecipe(FVector(100.f, 0.f, 0.f), FRotator::ZeroRotator, 3.0f, true, true));

    // jump: Z轴上弹 15cm，循环往返，1秒一霿
    AnimLibrary.Add(TEXT("jump"),
        FAnimRecipe(FVector(0.f, 0.f, 15.f), FRotator::ZeroRotator, 1.0f, true, true));

    // flip: Y轴封转 180°，循环往返，1.5秒一霿
    AnimLibrary.Add(TEXT("flip"),
        FAnimRecipe(FVector::ZeroVector, FRotator(180.f, 0.f, 0.f), 1.5f, true, true));
}

// 立即切换并播放动画状态
void ATwinInstance::PlayAnimationState(const FString& StateName)
{
    const FAnimRecipe* Found = AnimLibrary.Find(StateName);
    if (!Found)
    {
        UE_LOG(LogTemp, Warning, TEXT("[孪生体] 未知动画状态: %s"), *StateName);
        return;
    }

    // idle 返回初始位置并关闭 Tick
    if (StateName == TEXT("idle"))
    {
        bAnimRunning = false;
        if (!LabelComponent || !LabelComponent->IsVisible())
        {
            SetActorTickEnabled(false);
        }
        // 归位
        SetActorLocation(AnimBaseLocation);
        SetActorRotation(AnimBaseRotation);
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 动画归位: %s"), *InstanceId);
        return;
    }

    // 记录当前状态作为基准点
    AnimBaseLocation = GetActorLocation();
    AnimBaseRotation = GetActorRotation();
    AnimTimer        = 0.0f;
    ActiveRecipe     = *Found;
    bAnimRunning     = true;

    // 开启 Tick
    SetActorTickEnabled(true);

    UE_LOG(LogTemp, Log, TEXT("[孪生体] 动画切换: %s → %s"), *InstanceId, *StateName);
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
    // asset_id 三种语义：
    //   0. "artstudio:{id}:v{n}" → ArtStudio 资产，后端代理下载（异步，3.3）
    //   1. "/Game/..." 或 "/Engine/..." → 烘焙进包的资产，走 LoadObject（向后兼容）
    //   2. 其他（如 "forklift.glb"）→ 运行时从固定目录/磁盘加载，不参与打包
    if (MeshPath.StartsWith(TEXT("artstudio:")))
    {
        LoadRemoteGltf(MeshPath);   // 异步接管：命中缓存即时加载，否则占位 Cube + 下载
        return true;                 // 不走下方同步 Cube 兜底
    }
    if (MeshPath.StartsWith(TEXT("/Game/")) || MeshPath.StartsWith(TEXT("/Engine/")))
    {
        FString FullPath = MeshPath;
        if (!FullPath.Contains(TEXT(".")))
        {
            FString AssetName;
            MeshPath.Split(TEXT("/"), nullptr, &AssetName, ESearchCase::IgnoreCase, ESearchDir::FromEnd);
            FullPath = FString::Printf(TEXT("%s.%s"), *MeshPath, *AssetName);
        }

        UE_LOG(LogTemp, Log, TEXT("[孪生体] 尝试加载(烘焙资产): %s"), *FullPath);
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *FullPath);
        if (!Mesh)
        {
            Mesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);
        }
        if (Mesh)
        {
            MeshComponent->SetStaticMesh(Mesh);
            CacheOriginalMaterials();
            UE_LOG(LogTemp, Log, TEXT("[孪生体] ✅ 烘焙资产加载成功: %s"), *MeshPath);
            return true;
        }
    }
    else if (LoadRuntimeGltf(MeshPath))
    {
        return true;
    }

    // ── 加载失败：使用引擎内置立方体作为占位符 ──────────────────────────
    UE_LOG(LogTemp, Error,
           TEXT("[孪生体] ❌ 资产加载失败: %s   请检查路径/glb 文件是否存在"), *MeshPath);
    SetPlaceholderCube();
    UE_LOG(LogTemp, Warning, TEXT("[孪生体] 使用默认立方体占位 (ID=%s)"), *InstanceId);
    return false;
}

// ─── 运行时 glb/gltf 加载（glTFRuntime，模型不参与打包） ──────────────────────

// 固定模型目录的默认值：编辑器与打包 exe 都读这一份，永不拷贝。
// 可在 项目 Config/DefaultGame.ini 用 [OntoTwinSync] ModelsDir=... 覆盖，无需重编译。
static const TCHAR* kDefaultModelsDir = TEXT("D:/SCC/DigitalFactoryBase_SCC/Models");

FString ATwinInstance::ResolveModelFilePath(const FString& AssetId) const
{
    // 在候选目录里找 <file>，返回第一个存在的；都没有则返回空串。
    // 优先级：① 固定目录（ini 可配，默认 kDefaultModelsDir）—— 编辑器/打包共用，零拷贝；
    //         ②③④ exe 相对的 Models/（兜底，兼容把模型丢在包旁的情况）。
    // 后续若改为后端 HTTP 下发，只需替换本函数（glTFRuntime 亦支持 URL 加载）。
    FString FileName = AssetId;
    if (!FileName.EndsWith(TEXT(".glb")) && !FileName.EndsWith(TEXT(".gltf")))
    {
        FileName += TEXT(".glb");
    }

    // ① 固定目录：先读 ini 配置，没配则用默认
    FString FixedDir;
    if (!GConfig || !GConfig->GetString(TEXT("OntoTwinSync"), TEXT("ModelsDir"), FixedDir, GGameIni) || FixedDir.IsEmpty())
    {
        FixedDir = kDefaultModelsDir;
    }

    const FString ProjDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
    const FString ExeDir  = FPaths::ConvertRelativePathToFull(FPlatformProcess::BaseDir());

    // 候选 1：固定目录直接拼文件名（FixedDir 已是 Models 根，不再追加 Models）
    TArray<FString> Candidates;
    Candidates.Add(FPaths::Combine(FixedDir, FileName));
    // 候选 2~5：exe 相对的 Models/ 兜底
    Candidates.Add(FPaths::Combine(ProjDir, TEXT("Models"), FileName));
    Candidates.Add(FPaths::Combine(ProjDir, TEXT(".."), TEXT("Models"), FileName));
    Candidates.Add(FPaths::Combine(ExeDir, TEXT("Models"), FileName));
    Candidates.Add(FPaths::Combine(ExeDir, TEXT(".."), TEXT(".."), TEXT(".."), TEXT("Models"), FileName));

    for (const FString& Raw : Candidates)
    {
        const FString Candidate = FPaths::ConvertRelativePathToFull(Raw);
        const bool bExists = FPaths::FileExists(Candidate);
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 候选模型路径 %s : %s"),
               bExists ? TEXT("✅命中") : TEXT("✗未找到"), *Candidate);
        if (bExists)
        {
            return Candidate;
        }
    }

    return FString();  // 全部未命中
}

bool ATwinInstance::LoadRuntimeGltf(const FString& AssetId)
{
    const FString FilePath = ResolveModelFilePath(AssetId);
    if (FilePath.IsEmpty())
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生体] 所有候选目录都没找到模型 '%s'，请把 Models/ 放到上面日志列出的任一目录"),
               *AssetId);
        return false;
    }
    return LoadGltfFromFile(FilePath);
}

bool ATwinInstance::LoadGltfFromFile(const FString& FilePath)
{
    UE_LOG(LogTemp, Log, TEXT("[孪生体] 运行时加载 glb: %s"), *FilePath);

    // glTF 以米为单位，UE 以厘米，SceneScale=100 做单位换算
    FglTFRuntimeConfig LoaderConfig;
    LoaderConfig.TransformBaseType = EglTFRuntimeTransformBaseType::Default;
    LoaderConfig.SceneScale = 100.0f;

    UglTFRuntimeAsset* Asset =
        UglTFRuntimeFunctionLibrary::glTFLoadAssetFromFilename(FilePath, false, LoaderConfig);
    if (!Asset)
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生体] glb 解析失败: %s"), *FilePath);
        return false;
    }

    // 把整个默认场景的所有静态网格递归合并成一个 StaticMesh
    FglTFRuntimeStaticMeshConfig MeshConfig;
    MeshConfig.bBuildSimpleCollision = true;
    MeshConfig.NormalsGenerationStrategy = EglTFRuntimeNormalsGenerationStrategy::IfMissing;
    MeshConfig.TangentsGenerationStrategy = EglTFRuntimeTangentsGenerationStrategy::IfMissing;

    UStaticMesh* Mesh = Asset->LoadStaticMeshRecursive(FString(), TArray<FString>(), MeshConfig);
    if (!Mesh)
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生体] glb 网格生成失败: %s"), *FilePath);
        return false;
    }

    MeshComponent->SetStaticMesh(Mesh);
    MeshComponent->SetWorldScale3D(FVector(1.0f));  // 清掉占位 Cube 可能留下的 0.5 缩放
    CacheOriginalMaterials();

    // ── 材质诊断（定位打包后灰白无贴图）─────────────────────────────
    // 槽0 基材若是 M_glTFRuntime* → 材质正常,问题在贴图;若是默认/BasicShape → 材质回退(shader没编)
    const int32 NumMats = MeshComponent->GetNumMaterials();
    UE_LOG(LogTemp, Warning, TEXT("[材质诊断] %s 材质槽数=%d"),
           *FPaths::GetCleanFilename(FilePath), NumMats);
    for (int32 i = 0; i < NumMats && i < 4; ++i)
    {
        UMaterialInterface* M = MeshComponent->GetMaterial(i);
        UMaterialInterface* Base = M ? M->GetBaseMaterial() : nullptr;
        UE_LOG(LogTemp, Warning, TEXT("[材质诊断]   槽%d 材质=%s 基材=%s"),
               i,
               M ? *M->GetName() : TEXT("NULL"),
               Base ? *Base->GetName() : TEXT("?"));
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生体] ✅ glb 加载成功: %s"), *FilePath);
    return true;
}

void ATwinInstance::SetPlaceholderCube()
{
    UStaticMesh* DefaultMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (DefaultMesh)
    {
        MeshComponent->SetStaticMesh(DefaultMesh);
        MeshComponent->SetWorldScale3D(FVector(0.5f));
    }
}

void ATwinInstance::PurgeOldCacheVersions(const FString& AssetId, const FString& KeepFile)
{
    const FString CacheDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("ModelCache"));
    const FString KeepName = FPaths::GetCleanFilename(KeepFile);
    TArray<FString> Found;
    IFileManager::Get().FindFiles(Found, *FPaths::Combine(CacheDir, AssetId + TEXT("_v*.glb")), true, false);
    for (const FString& F : Found)
    {
        if (F != KeepName)
        {
            IFileManager::Get().Delete(*FPaths::Combine(CacheDir, F));
            UE_LOG(LogTemp, Log, TEXT("[孪生体] 清理旧版本缓存: %s"), *F);
        }
    }
}

// ─── ArtStudio 远程加载：命中缓存即时加载，否则占位 Cube + 异步下载（3.3）──────
void ATwinInstance::LoadRemoteGltf(const FString& StableId)
{
    // 解析 artstudio:{id}:v{n}
    FString Rest = StableId;
    Rest.RemoveFromStart(TEXT("artstudio:"));
    FString AssetIdPart, VersionPart;
    if (!Rest.Split(TEXT(":v"), &AssetIdPart, &VersionPart))
    {
        AssetIdPart = Rest;           // 容错：无版本段
        VersionPart = TEXT("0");
    }

    // 缓存文件：Saved/ModelCache/{id}_v{n}.glb —— 版本进文件名，升版自动失效重下
    const FString CacheDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("ModelCache"));
    const FString CacheFile = FPaths::Combine(
        CacheDir, FString::Printf(TEXT("%s_v%s.glb"), *AssetIdPart, *VersionPart));

    // ① 命中缓存 → 直接加载
    if (FPaths::FileExists(CacheFile))
    {
        UE_LOG(LogTemp, Log, TEXT("[孪生体] ArtStudio 缓存命中: %s"), *CacheFile);
        if (!LoadGltfFromFile(CacheFile))
        {
            SetPlaceholderCube();
        }
        return;
    }

    // ② 缓存缺失 → 占位 Cube + 异步下载
    if (PendingRemoteId == StableId)
    {
        return;  // 同一标识已在下载中，避免轮询重复发请求
    }
    SetPlaceholderCube();
    PendingRemoteId = StableId;

    IFileManager::Get().MakeDirectory(*CacheDir, /*Tree=*/true);

    const FString Url = FString::Printf(
        TEXT("%s/api/v2/assets/download?id=%s"), *BackendBaseUrl, *AssetIdPart);
    UE_LOG(LogTemp, Log, TEXT("[孪生体] ArtStudio 下载: %s"), *Url);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(Url);
    Request->SetVerb(TEXT("GET"));

    // 弱引用保护：实例可能在回调前被销毁
    TWeakObjectPtr<ATwinInstance> WeakThis(this);
    const FString ExpectId = StableId;
    const FString AssetIdForPurge = AssetIdPart;
    Request->OnProcessRequestComplete().BindLambda(
        [WeakThis, CacheFile, ExpectId, AssetIdForPurge](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
        {
            ATwinInstance* Self = WeakThis.Get();
            if (!Self)
            {
                return;  // 实例已销毁
            }
            Self->PendingRemoteId.Empty();

            // 期间资产又被改绑/升版 → 本次结果已过期，丢弃
            if (Self->AssetPath != ExpectId)
            {
                UE_LOG(LogTemp, Log, TEXT("[孪生体] 下载结果已过期，丢弃: %s"), *ExpectId);
                return;
            }

            if (!bOk || !Resp.IsValid() || Resp->GetResponseCode() != 200)
            {
                UE_LOG(LogTemp, Error, TEXT("[孪生体] ArtStudio 下载失败 (code=%d)，保持占位 Cube"),
                       Resp.IsValid() ? Resp->GetResponseCode() : -1);
                return;  // 占位 Cube 已在位
            }

            // 落盘缓存 → 加载
            if (!FFileHelper::SaveArrayToFile(Resp->GetContent(), *CacheFile))
            {
                UE_LOG(LogTemp, Error, TEXT("[孪生体] 缓存写入失败: %s"), *CacheFile);
                return;
            }
            if (!Self->LoadGltfFromFile(CacheFile))
            {
                Self->SetPlaceholderCube();
            }
            else
            {
                Self->PurgeOldCacheVersions(AssetIdForPurge, CacheFile);
            }
        });

    Request->ProcessRequest();
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
        // C++ 直接驱动程序化动画，不再依赖蓝图
        PlayAnimationState(AnimState);
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 动画状态: %s → %s"), *InstanceId, *AnimState);
    }

    FString FxTrigger;
    if (BehaviorObj->TryGetStringField(TEXT("fx_trigger"), FxTrigger) && FxTrigger != CurrentFxTrigger)
    {
        CurrentFxTrigger = FxTrigger;
        OnFxTriggered(FxTrigger);  // 抛出给蓝图实现
        UE_LOG(LogTemp, Log, TEXT("[孪生体] 特效触发: %s → %s"), *InstanceId, *FxTrigger);
    }

    FString LabelContent;
    if (BehaviorObj->TryGetStringField(TEXT("ui_label_content"), LabelContent) && LabelContent != CurrentLabelContent)
    {
        CurrentLabelContent = LabelContent;

        if (LabelComponent)
        {
            if (LabelContent.IsEmpty())
            {
                // 空内容就隐藏标签
                LabelComponent->SetVisibility(false);
                LabelComponent->SetText(FText::GetEmpty());
                if (!bAnimRunning)
                {
                    SetActorTickEnabled(false);
                }
            }
            else
            {
                // 应用最新字体配置（用户在编辑器设置后生效）
                LabelComponent->SetRelativeLocation(FVector(0.f, 0.f, LabelZOffset));
                LabelComponent->SetWorldSize(LabelWorldSize);
                LabelComponent->SetTextRenderColor(LabelColor);

                // 如果用户指定了字体，就应用它（支持中文）
                if (LabelFont)
                {
                    LabelComponent->SetFont(LabelFont);
                }

                LabelComponent->SetText(FText::FromString(LabelContent));
                LabelComponent->SetVisibility(true);
                
                // 开启 Tick 以便每帧更新朝向
                SetActorTickEnabled(true);
            }
        }

        UE_LOG(LogTemp, Log, TEXT("[孪生体] UI标签更新: %s → \"%s\""), *InstanceId, *LabelContent);
    }
}
