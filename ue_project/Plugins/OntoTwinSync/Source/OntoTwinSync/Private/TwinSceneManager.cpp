// ============================================================================
// TwinSceneManager.cpp  (v3 — 数据库驱动，废弃固化)
//
// 职责：
//   1. 运行时轮询后端快照，动态 spawn / 更新 / 销毁 ATwinInstance（DB 唯一真源）
//   2. 编辑器：PullPreviewFromDB() 从数据库临时 spawn 预览（RF_Transient，不写 .umap）
//   3. 编辑器：FR-6 历史 actor 迁移工具（导出 / 清除已迁移）
//
// 已废弃（FR-4）：SnapshotToLevel 固化、TakeOverExistingInstances 接管、
//   bEditorPlaced 保护——孪生实例不再持久化进关卡，一律由数据库驱动。
// ============================================================================

#include "TwinSceneManager.h"
#include "TwinInstance.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
// FR-6 迁移工具用
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/App.h"
#include "HAL/FileManager.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Serialization/JsonWriter.h"
#if WITH_EDITOR
#include "Editor.h"
#endif

namespace
{
FString CleanFolderSegment(FString Segment)
{
    Segment.TrimStartAndEndInline();
    Segment.ReplaceInline(TEXT("\\"), TEXT("_"));
    Segment.ReplaceInline(TEXT("/"), TEXT("_"));
    return Segment;
}

FName BuildTwinFolderPath(const TSharedPtr<FJsonObject>& Snapshot, const TCHAR* RootFolder)
{
    TArray<FString> Segments;
    const TArray<TSharedPtr<FJsonValue>>* Hierarchy = nullptr;
    if (Snapshot.IsValid() && Snapshot->TryGetArrayField(TEXT("hierarchyPath"), Hierarchy))
    {
        for (const TSharedPtr<FJsonValue>& Value : *Hierarchy)
        {
            FString Segment;
            if (Value.IsValid() && Value->TryGetString(Segment))
            {
                Segment = CleanFolderSegment(Segment);
                if (!Segment.IsEmpty())
                {
                    Segments.Add(Segment);
                }
            }
        }
    }

    if (Segments.Num() == 0 && Snapshot.IsValid())
    {
        FString TypeName;
        if (Snapshot->TryGetStringField(TEXT("objectTypeName"), TypeName))
        {
            TypeName = CleanFolderSegment(TypeName);
            if (!TypeName.IsEmpty())
            {
                Segments.Add(TypeName);
            }
        }
    }

    FString Path(RootFolder);
    for (const FString& Segment : Segments)
    {
        Path += TEXT("/");
        Path += Segment;
    }
    return FName(*Path);
}
}

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinSceneManager::ATwinSceneManager()
{
    PrimaryActorTick.bCanEverTick = false;
    UEProjectName = FApp::GetProjectName();
    UEProjectId = FString::Printf(TEXT("ueproj_%s"), *UEProjectName);
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinSceneManager::BeginPlay()
{
    Super::BeginPlay();

    // 启动定时轮询（FR-4：孪生实例全部由数据库驱动动态 spawn，不再接管关卡预置 Actor）
    GetWorldTimerManager().SetTimer(
        PollTimerHandle,
        this,
        &ATwinSceneManager::PollBackend,
        PollInterval,
        true,   // bLoop
        1.0f    // 首次延迟 1 秒
    );

    UE_LOG(LogTemp, Log,
           TEXT("[孪生管理器] 启动完毕 | 后端=%s | 轮询间隔=%.2fs | 预置实例=%d"),
           *BackendBaseUrl, PollInterval, InstanceRegistry.Num());
}

// ── EndPlay ──────────────────────────────────────────────────────────────────

void ATwinSceneManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    GetWorldTimerManager().ClearTimer(PollTimerHandle);

    // 清理全部运行时 spawn 的孪生体（FR-4：不再有编辑器固化 Actor 需要保留）
    for (auto& Pair : InstanceRegistry)
    {
        if (Pair.Value && IsValid(Pair.Value))
        {
            Pair.Value->Destroy();
        }
    }
    InstanceRegistry.Empty();

    Super::EndPlay(EndPlayReason);
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 已清理运行时孪生体并停止轮询"));
}

// ═══════════════════════════════════════════════════════════════════════════
// 快照接口 URL
// ═══════════════════════════════════════════════════════════════════════════

FString ATwinSceneManager::BuildSnapshotsUrl() const
{
    FString Url = FString::Printf(TEXT("%s/api/v2/state/snapshots"), *BackendBaseUrl);
    // SceneId 非空时锁定场景；留空则由后端用当前激活数据集
    if (!SceneId.IsEmpty())
    {
        Url += FString::Printf(TEXT("?scene=%s"), *SceneId);
    }
    return Url;
}

void ATwinSceneManager::AddUEProjectHeaders(TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest) const
{
    HttpRequest->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), UEProjectId);
    HttpRequest->SetHeader(TEXT("X-OntoTwin-UE-Project-Name"), UEProjectName);
}

void ATwinSceneManager::BindCurrentUEProjectToActiveDataset()
{
#if WITH_EDITOR
    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Body->SetStringField(TEXT("ue_project_name"), UEProjectName);

    FString BodyStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/ue/bind_active_project"), *BackendBaseUrl));
    HttpRequest->SetVerb(TEXT("POST"));
    HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->SetContentAsString(BodyStr);
    HttpRequest->OnProcessRequestComplete().BindLambda([](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
    {
        const int32 Code = Resp.IsValid() ? Resp->GetResponseCode() : -1;
        const bool bSuccess = bOk && Resp.IsValid() && Code == 200;
        if (bSuccess)
        {
            UE_LOG(LogTemp, Log, TEXT("[UE绑定] 绑定当前 UE 工程到激活数据集成功 (code=%d)"), Code);
        }
        else
        {
            UE_LOG(LogTemp, Error, TEXT("[UE绑定] 绑定当前 UE 工程到激活数据集失败 (code=%d)"), Code);
        }
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 8.0f, bSuccess ? FColor::Green : FColor::Red,
                bSuccess ? TEXT("已绑定当前 UE 工程到激活数据集") : TEXT("UE 工程绑定失败，请查看 Output Log"));
        }
    });
    HttpRequest->ProcessRequest();
#else
    UE_LOG(LogTemp, Warning, TEXT("[UE绑定] 仅在编辑器模式下可用"));
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// 轮询逻辑
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::PollBackend()
{
    if (bRequestInFlight) return;

    UE_LOG(LogTemp, Log,
           TEXT("[孪生管理器] 轮询中... 场景=%s | 现有实例数=%d"),
           SceneId.IsEmpty() ? TEXT("(跟随后端)") : *SceneId, InstanceRegistry.Num());

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
        FHttpModule::Get().CreateRequest();

    FString Url = BuildSnapshotsUrl();
    HttpRequest->SetURL(Url);
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);

    HttpRequest->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnPollResponse);

    bRequestInFlight = true;
    HttpRequest->ProcessRequest();
}

void ATwinSceneManager::OnPollResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
    bRequestInFlight = false;

    int32 ResponseCode = Response.IsValid() ? Response->GetResponseCode() : -1;
    if (!bWasSuccessful || !Response.IsValid() || ResponseCode != 200)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[孪生管理器] ❌ 请求失败 | Code=%d | bSuccessful=%s"),
               ResponseCode, bWasSuccessful ? TEXT("true") : TEXT("false"));
        ConsecutiveFailures++;
        if (ConsecutiveFailures >= OfflineThreshold)
        {
            UE_LOG(LogTemp, Warning,
                   TEXT("[孪生管理器] 后端连续 %d 次无响应，标记全部实例离线"),
                   ConsecutiveFailures);
        }
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] ✅ 收到快照响应 Code=200, Body长度=%d"), Response->GetContentLength());

    ConsecutiveFailures = 0;

    // ── 解析 JSON 数组 ───────────────────────────────────────────────────
    FString Body = Response->GetContentAsString();
    TArray<TSharedPtr<FJsonValue>> SnapshotArray;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Body);

    if (!FJsonSerializer::Deserialize(Reader, SnapshotArray))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] ❌ 快照 JSON 数组解析失败:\n%s"), *Body);
        return;
    }

    if (SnapshotArray.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] ⚠️ 收到 200 OK，但快照数组为空 (当前无实例)"));
    }

    // ── 收集后端当前存在的实例 ID ─────────────────────────────────────────
    TSet<FString> BackendInstanceIds;

    for (const auto& Val : SnapshotArray)
    {
        const TSharedPtr<FJsonObject>* SnapObj;
        if (!Val->TryGetObject(SnapObj)) continue;

        FString InstanceId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstanceId)) continue;

        BackendInstanceIds.Add(InstanceId);
        ProcessSnapshot(*SnapObj);
    }

    // ── 检测后端已删除的实例 → 在场景中销毁（FR-4：全部动态 spawn，一律销毁）─────
    TArray<FString> ToRemove;
    for (auto& Pair : InstanceRegistry)
    {
        if (!BackendInstanceIds.Contains(Pair.Key))
        {
            ToRemove.Add(Pair.Key);
        }
    }
    for (const FString& Id : ToRemove)
    {
        DestroyTwinInstance(Id);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 实例处理
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::ProcessSnapshot(const TSharedPtr<FJsonObject>& Snapshot)
{
    FString InstanceId;
    Snapshot->TryGetStringField(TEXT("instanceId"), InstanceId);

    // ── 已存在：更新状态 ─────────────────────────────────────────────────
    ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
    if (Found && *Found && IsValid(*Found))
    {
        (*Found)->ApplySnapshot(Snapshot);
        return;
    }

    // ── 不存在：创建新实例 ───────────────────────────────────────────────
    ATwinInstance* NewInst = SpawnTwinInstance(InstanceId, Snapshot);
    if (NewInst)
    {
        InstanceRegistry.Add(InstanceId, NewInst);
        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 新增实例: %s"), *InstanceId);
    }
}

ATwinInstance* ATwinSceneManager::SpawnTwinInstance(
    const FString& InstanceId,
    const TSharedPtr<FJsonObject>& Snapshot)
{
    UWorld* World = GetWorld();
    if (!World) return nullptr;

    // ── 解析 asset_id（UE 内容路径） ─────────────────────────────────────
    FString AssetPathStr;
    const TSharedPtr<FJsonObject>* InterfacesObj;
    if (Snapshot->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
    {
        const TSharedPtr<FJsonObject>* RepObj;
        if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
        {
            (*RepObj)->TryGetStringField(TEXT("asset_id"), AssetPathStr);
        }
    }

    // ── 解析初始位置 ─────────────────────────────────────────────────────
    FVector SpawnLocation = FVector::ZeroVector;
    if (Snapshot->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
    {
        const TSharedPtr<FJsonObject>* SpatialObj;
        if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Spatial"), SpatialObj))
        {
            double tx = 0, ty = 0, tz = 0;
            (*SpatialObj)->TryGetNumberField(TEXT("translation_x"), tx);
            (*SpatialObj)->TryGetNumberField(TEXT("translation_y"), ty);
            (*SpatialObj)->TryGetNumberField(TEXT("translation_z"), tz);
            SpawnLocation = FVector(tx, ty, tz);
        }
    }

    // ── Spawn ATwinInstance ──────────────────────────────────────────────
    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = FName(*FString::Printf(TEXT("Twin_%s"), *InstanceId));

    UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();

    ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
        SpawnClass,
        SpawnLocation,
        FRotator::ZeroRotator,
        SpawnParams
    );

    if (!Inst)
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] Spawn 失败: %s"), *InstanceId);
        return nullptr;
    }

    // ── 设置标签和名称 ───────────────────────────────────────────────────
    FString DisplayName;
    if (!Snapshot->TryGetStringField(TEXT("displayName"), DisplayName) || DisplayName.IsEmpty())
    {
        DisplayName = InstanceId;
    }
    Inst->SetActorLabel(DisplayName);
    Inst->Tags.Add(FName(*InstanceId));

    // ── 放入世界大纲特定文件夹下 ─────────────────────────────────────────
#if WITH_EDITOR
    Inst->SetFolderPath(BuildTwinFolderPath(Snapshot, TEXT("TwinInstances")));
#endif

    // ── 初始化孪生实例 ───────────────────────────────────────────────────
    Inst->InitializeTwin(InstanceId, AssetPathStr, BackendBaseUrl);

    // ── 首次应用快照 ─────────────────────────────────────────────────────
    Inst->ApplySnapshot(Snapshot);

    return Inst;
}

void ATwinSceneManager::DestroyTwinInstance(const FString& InstanceId)
{
    ATwinInstance** Found = InstanceRegistry.Find(InstanceId);
    if (Found && *Found && IsValid(*Found))
    {
        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 销毁实例: %s"), *InstanceId);
        (*Found)->Destroy();
    }
    InstanceRegistry.Remove(InstanceId);
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-6 历史 actor 迁移工具（编辑器一次性）
// ═══════════════════════════════════════════════════════════════════════════

FString ATwinSceneManager::MigrationExportPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_actors_export.json")));
}

FString ATwinSceneManager::MigrationResultPath() const
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("OntoTwinMigration"), TEXT("ue_migration_result.json")));
}

void ATwinSceneManager::ExportSelectedActorsForMigration()
{
#if WITH_EDITOR
    // 扫描「待迁移文件夹」而非当前选择集：UE 细节面板多选不同类型 Actor 时，
    // 只显示共同按钮，Manager 专属按钮会被隐藏——无法"同时选中 actor + Manager"
    // 再点击本按钮。改用文件夹两步走：先把 actor 移进文件夹，再单独选中 Manager 点击。
    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GetWorld();
    if (!World)
    {
        return;
    }

    const FName TargetFolder = FName(*MigrationFolderName);
    TArray<TSharedPtr<FJsonValue>> ActorsJson;
    int32 Count = 0;

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || A == this) continue;
        // 已受管的孪生体不迁移（它本就来自 DB）
        if (A->IsA(ATwinInstance::StaticClass())) continue;
        // 只导出「待迁移文件夹」下的 actor
        if (A->GetFolderPath() != TargetFolder) continue;

        TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
        Obj->SetStringField(TEXT("ext_guid"),
            A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens));
        Obj->SetStringField(TEXT("name"), A->GetActorLabel());
        Obj->SetStringField(TEXT("actor_label"), A->GetActorLabel());
        Obj->SetStringField(TEXT("actor_name"), A->GetName());
        Obj->SetStringField(TEXT("source_folder_path"), A->GetFolderPath().ToString());
        if (UClass* ActorClass = A->GetClass())
        {
            Obj->SetStringField(TEXT("actor_class"), ActorClass->GetName());
            Obj->SetStringField(TEXT("actor_class_path"), ActorClass->GetPathName());
            if (ActorClass->ClassGeneratedBy)
            {
                Obj->SetStringField(TEXT("blueprint_class_path"), ActorClass->ClassGeneratedBy->GetPathName());
            }
        }

        // 取第一个静态网格组件的资产路径（/Game/... 或引擎资产）
        FString MeshAsset;
        TArray<UStaticMeshComponent*> StaticMeshComponents;
        A->GetComponents<UStaticMeshComponent>(StaticMeshComponents);
        TArray<TSharedPtr<FJsonValue>> StaticMeshAssets;
        if (StaticMeshComponents.Num() > 0)
        {
            for (UStaticMeshComponent* SMC : StaticMeshComponents)
            {
                if (SMC && SMC->GetStaticMesh())
                {
                    const FString Path = SMC->GetStaticMesh()->GetPathName();
                    if (MeshAsset.IsEmpty())
                    {
                        MeshAsset = Path;
                    }
                    StaticMeshAssets.Add(MakeShared<FJsonValueString>(Path));
                }
            }
        }
        Obj->SetStringField(TEXT("mesh_asset"), MeshAsset);
        Obj->SetStringField(TEXT("static_mesh_asset"), MeshAsset);
        Obj->SetArrayField(TEXT("static_mesh_assets"), StaticMeshAssets);

        FString SkeletalMeshAsset;
        TArray<USkeletalMeshComponent*> SkeletalMeshComponents;
        A->GetComponents<USkeletalMeshComponent>(SkeletalMeshComponents);
        TArray<TSharedPtr<FJsonValue>> SkeletalMeshAssets;
        for (USkeletalMeshComponent* SKC : SkeletalMeshComponents)
        {
            if (SKC && SKC->GetSkeletalMeshAsset())
            {
                const FString Path = SKC->GetSkeletalMeshAsset()->GetPathName();
                if (SkeletalMeshAsset.IsEmpty())
                {
                    SkeletalMeshAsset = Path;
                }
                SkeletalMeshAssets.Add(MakeShared<FJsonValueString>(Path));
            }
        }
        Obj->SetStringField(TEXT("skeletal_mesh_asset"), SkeletalMeshAsset);
        Obj->SetArrayField(TEXT("skeletal_mesh_assets"), SkeletalMeshAssets);

        TSharedPtr<FJsonObject> ComponentSummary = MakeShared<FJsonObject>();
        ComponentSummary->SetNumberField(TEXT("static_mesh_components"), StaticMeshComponents.Num());
        ComponentSummary->SetNumberField(TEXT("skeletal_mesh_components"), SkeletalMeshComponents.Num());
        Obj->SetObjectField(TEXT("component_summary"), ComponentSummary);

        const FVector Loc = A->GetActorLocation();
        const FRotator Rot = A->GetActorRotation();
        const FVector Scale = A->GetActorScale3D();
        TSharedPtr<FJsonObject> TF = MakeShared<FJsonObject>();
        TF->SetNumberField(TEXT("tx"), Loc.X);
        TF->SetNumberField(TEXT("ty"), Loc.Y);
        TF->SetNumberField(TEXT("tz"), Loc.Z);
        // 与 ApplySpatialFromSnapshot 的约定对齐：rx=Roll, ry=Pitch, rz=Yaw
        TF->SetNumberField(TEXT("rx"), Rot.Roll);
        TF->SetNumberField(TEXT("ry"), Rot.Pitch);
        TF->SetNumberField(TEXT("rz"), Rot.Yaw);
        TF->SetNumberField(TEXT("sx"), Scale.X);
        TF->SetNumberField(TEXT("sy"), Scale.Y);
        TF->SetNumberField(TEXT("sz"), Scale.Z);
        Obj->SetObjectField(TEXT("transform"), TF);

        ActorsJson.Add(MakeShared<FJsonValueObject>(Obj));
        Count++;
    }

    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Root->SetStringField(TEXT("ue_project_name"), UEProjectName);
    // project_id 留空→后端用当前激活项目；zone_id 用本 Manager 的 SceneId（=分区）
    if (!SceneId.IsEmpty())
    {
        Root->SetStringField(TEXT("zone_id"), SceneId);
    }
    Root->SetArrayField(TEXT("actors"), ActorsJson);

    FString OutStr;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutStr);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);

    const FString Path = MigrationExportPath();
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), /*Tree=*/true);
    const bool bOk = FFileHelper::SaveStringToFile(OutStr, *Path);

    UE_LOG(LogTemp, Log, TEXT("[迁移] 文件夹「%s」导出 %d 个 actor → %s (%s)"),
           *MigrationFolderName, Count, *Path, bOk ? TEXT("成功") : TEXT("写入失败"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.0f,
            bOk ? FColor::Green : FColor::Red,
            Count > 0
                ? FString::Printf(TEXT("导出 %d 个 actor → %s\n把它交给后端 migrate_ue_actors.py"),
                                   Count, *Path)
                : FString::Printf(
                    TEXT("文件夹「%s」下没有 actor\n请先框选历史 actor，右键→移动到文件夹→填「%s」"),
                    *MigrationFolderName, *MigrationFolderName));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[迁移] 导出仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::RemoveMigratedActors()
{
#if WITH_EDITOR
    const FString Path = MigrationResultPath();
    FString Content;
    if (!FFileHelper::LoadFileToString(Content, *Path))
    {
        UE_LOG(LogTemp, Error, TEXT("[迁移] 读不到结果文件: %s"), *Path);
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Red,
                FString::Printf(TEXT("读不到 %s\n请先跑后端迁移脚本产出结果"), *Path));
        }
        return;
    }

    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Content);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[迁移] 结果 JSON 解析失败"));
        return;
    }

    // 结果文件是 {ext_guid: instance_id}，收集已成功迁移的 guid
    TSet<FString> MigratedGuids;
    for (const auto& Pair : Root->Values)
    {
        MigratedGuids.Add(Pair.Key);
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GetWorld();
    if (!World) return;

    TArray<AActor*> ToDelete;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || A == this) continue;
        if (A->IsA(ATwinInstance::StaticClass())) continue;
        const FString Guid = A->GetActorGuid().ToString(EGuidFormats::DigitsWithHyphens);
        if (MigratedGuids.Contains(Guid))
        {
            ToDelete.Add(A);
        }
    }

    int32 Deleted = 0;
    for (AActor* A : ToDelete)
    {
        if (World->EditorDestroyActor(A, /*bShouldModifyLevel=*/true))
        {
            Deleted++;
        }
    }

    UE_LOG(LogTemp, Log, TEXT("[迁移] 已删除 %d 个已收编的原 actor（共匹配 %d）"),
           Deleted, ToDelete.Num());
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Green,
            FString::Printf(TEXT("已清除 %d 个已迁移原 actor\n记得保存关卡(Ctrl+S)"), Deleted));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[迁移] 清除仅在编辑器模式下可用"));
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-4 编辑器预览（从数据库临时 spawn 供查看/微调，绝不写入 .umap）
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::PullPreviewFromDB()
{
#if WITH_EDITOR
    ClearPreview();  // 先清掉上一批，避免重叠

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
        FHttpModule::Get().CreateRequest();
    HttpRequest->SetURL(BuildSnapshotsUrl());
    HttpRequest->SetVerb(TEXT("GET"));
    HttpRequest->SetHeader(TEXT("Accept"), TEXT("application/json"));
    AddUEProjectHeaders(HttpRequest);
    HttpRequest->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnPreviewResponse);
    HttpRequest->ProcessRequest();

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Cyan,
            TEXT("正在从数据库拉取预览..."));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 预览仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::ClearPreview()
{
#if WITH_EDITOR
    int32 Cleared = 0;
    for (ATwinInstance* A : PreviewActors)
    {
        if (A && IsValid(A))
        {
            A->Destroy();
            Cleared++;
        }
    }
    PreviewActors.Empty();
    PreviewBaseline.Empty();
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 已清除 %d 个预览 Actor"), Cleared);
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// FR-5 空间回写：预览 Actor 手动调整后提交回后端真源
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::CommitPreviewChanges()
{
#if WITH_EDITOR
    // ── 1. diff：找出被手动挪动过的预览 Actor ────────────────────────────
    struct FChange { FString Id; FTransform Cur; };
    TArray<FChange> Changes;

    for (ATwinInstance* A : PreviewActors)
    {
        if (!A || !IsValid(A)) continue;
        const FString Id = A->GetInstanceId();
        const FTransform* Base = PreviewBaseline.Find(Id);
        if (!Base) continue;

        const FTransform Cur = A->GetActorTransform();
        if (Cur.Equals(*Base, 0.01f)) continue;   // 没动过（容差 0.01）

        Changes.Add({Id, Cur});
    }

    if (Changes.Num() == 0)
    {
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Yellow,
                TEXT("没有检测到位置变更（先拉取预览、挪动后再提交）"));
        }
        return;
    }

    // ── 2. 逐条 POST /api/v2/state/writeback ────────────────────────────
    PendingWritebacks = Changes.Num();
    SucceededWritebacks = 0;

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Cyan,
            FString::Printf(TEXT("正在提交 %d 处空间变更..."), Changes.Num()));
    }

    for (const FChange& C : Changes)
    {
        TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
        Body->SetStringField(TEXT("instance_id"), C.Id);

        const FVector L = C.Cur.GetLocation();
        const FRotator R = C.Cur.Rotator();
        const FVector S = C.Cur.GetScale3D();
        TSharedPtr<FJsonObject> TF = MakeShared<FJsonObject>();
        TF->SetNumberField(TEXT("tx"), L.X);
        TF->SetNumberField(TEXT("ty"), L.Y);
        TF->SetNumberField(TEXT("tz"), L.Z);
        // 与后端 writeback.py / ApplySpatialFromSnapshot 约定一致：rx=Roll, ry=Pitch, rz=Yaw
        TF->SetNumberField(TEXT("rx"), R.Roll);
        TF->SetNumberField(TEXT("ry"), R.Pitch);
        TF->SetNumberField(TEXT("rz"), R.Yaw);
        TF->SetNumberField(TEXT("sx"), S.X);
        TF->SetNumberField(TEXT("sy"), S.Y);
        TF->SetNumberField(TEXT("sz"), S.Z);
        Body->SetObjectField(TEXT("transform"), TF);

        FString BodyStr;
        TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyStr);
        FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

        TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest =
            FHttpModule::Get().CreateRequest();
        HttpRequest->SetURL(FString::Printf(TEXT("%s/api/v2/state/writeback"), *BackendBaseUrl));
        HttpRequest->SetVerb(TEXT("POST"));
        HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
        AddUEProjectHeaders(HttpRequest);
        HttpRequest->SetContentAsString(BodyStr);

        TWeakObjectPtr<ATwinSceneManager> WeakThis(this);
        const FString Id = C.Id;
        const FTransform Committed = C.Cur;
        HttpRequest->OnProcessRequestComplete().BindLambda(
            [WeakThis, Id, Committed](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bOk)
            {
                ATwinSceneManager* Self = WeakThis.Get();
                if (!Self) return;
                Self->PendingWritebacks--;

                const bool bSuccess = bOk && Resp.IsValid() && Resp->GetResponseCode() == 200;
                if (bSuccess)
                {
                    Self->SucceededWritebacks++;
                    // 基线推进到已提交值：重复点提交不会再发同一条
                    Self->PreviewBaseline.Add(Id, Committed);
                    UE_LOG(LogTemp, Log, TEXT("[回写] %s 提交成功"), *Id);
                }
                else
                {
                    UE_LOG(LogTemp, Error, TEXT("[回写] %s 提交失败 (code=%d)"),
                           *Id, Resp.IsValid() ? Resp->GetResponseCode() : -1);
                    if (GEngine)
                    {
                        GEngine->AddOnScreenDebugMessage(-1, 8.0f, FColor::Red,
                            FString::Printf(TEXT("回写失败: %s（详见 Output Log）"), *Id));
                    }
                }

                // 全部返回后给一条汇总
                if (Self->PendingWritebacks <= 0 && GEngine)
                {
                    GEngine->AddOnScreenDebugMessage(-1, 8.0f,
                        Self->SucceededWritebacks > 0 ? FColor::Green : FColor::Red,
                        FString::Printf(TEXT("回写完成：成功 %d 处"), Self->SucceededWritebacks));
                }
            });

        HttpRequest->ProcessRequest();
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 回写提交仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::OnPreviewResponse(
    FHttpRequestPtr HttpRequest,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
#if WITH_EDITOR
    if (!bWasSuccessful || !Response.IsValid() || Response->GetResponseCode() != 200)
    {
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red,
                TEXT("预览拉取失败，请确认后端在运行"));
        }
        return;
    }

    TArray<TSharedPtr<FJsonValue>> Arr;
    TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(Response->GetContentAsString());
    if (!FJsonSerializer::Deserialize(Reader, Arr))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 预览 JSON 解析失败"));
        return;
    }

    UWorld* World = GetWorld();
    if (!World) return;

    UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();
    int32 Count = 0;

    for (const auto& Val : Arr)
    {
        const TSharedPtr<FJsonObject>* SnapObj;
        if (!Val->TryGetObject(SnapObj)) continue;

        FString InstId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstId)) continue;

        FString AssetPathStr;
        const TSharedPtr<FJsonObject>* InterfacesObj;
        if ((*SnapObj)->TryGetObjectField(TEXT("interfaces"), InterfacesObj))
        {
            const TSharedPtr<FJsonObject>* RepObj;
            if ((*InterfacesObj)->TryGetObjectField(TEXT("I3D_Representable"), RepObj))
            {
                (*RepObj)->TryGetStringField(TEXT("asset_id"), AssetPathStr);
            }
        }

        // 关键：RF_Transient → 保存关卡时绝不写入 .umap（杜绝“误固化”）
        FActorSpawnParameters SpawnParams;
        SpawnParams.ObjectFlags |= RF_Transient;

        ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
            SpawnClass, FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
        if (!Inst) continue;

        FString DisplayName;
        if (!(*SnapObj)->TryGetStringField(TEXT("displayName"), DisplayName) || DisplayName.IsEmpty())
        {
            DisplayName = InstId;
        }
        Inst->SetActorLabel(FString::Printf(TEXT("[预览] %s"), *DisplayName));
        Inst->SetFolderPath(BuildTwinFolderPath(*SnapObj, TEXT("TwinPreview")));
        Inst->InitializeTwin(InstId, AssetPathStr, BackendBaseUrl);
        Inst->ApplySnapshot(*SnapObj);   // 应用位置/材质等，摆到正确位置

        // FR-5：记录回写基线 = 数据库此刻给的 transform（提交时 diff 用）
        PreviewBaseline.Add(InstId, Inst->GetActorTransform());

        PreviewActors.Add(Inst);
        Count++;
    }

    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 预览已生成 %d 个 transient Actor"), Count);
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green,
            FString::Printf(TEXT("预览已生成 %d 个（transient，不会存进关卡）"), Count));
    }
#endif
}
