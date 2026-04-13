// ============================================================================
// TwinSceneManager.cpp  (v2 — 编辑器固化 + 本地锁定)
//
// 新增功能：
//   1. SnapshotToLevel()       — 编辑器按钮，拉取后端数据生成持久 Actor
//   2. TakeOverExistingInstances() — BeginPlay 时扫描已有 ATwinInstance
//   3. 编辑器预置 Actor 在 Play 时自动被接管，无需重复 Spawn
// ============================================================================

#include "TwinSceneManager.h"
#include "TwinInstance.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinSceneManager::ATwinSceneManager()
{
    PrimaryActorTick.bCanEverTick = false;
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinSceneManager::BeginPlay()
{
    Super::BeginPlay();

    // ── 1. 接管关卡中已存在的 ATwinInstance（编辑器固化的 Actor）──────────
    TakeOverExistingInstances();

    // ── 2. 启动定时轮询 ──────────────────────────────────────────────────
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

    // 清理运行时 Spawn 的孪生体（编辑器预置的不销毁）
    for (auto& Pair : InstanceRegistry)
    {
        if (Pair.Value && IsValid(Pair.Value))
        {
            if (!Pair.Value->bEditorPlaced)
            {
                Pair.Value->Destroy();
            }
        }
    }
    InstanceRegistry.Empty();

    Super::EndPlay(EndPlayReason);
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 已清理运行时孪生体并停止轮询"));
}

// ═══════════════════════════════════════════════════════════════════════════
// 接管已有实例
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::TakeOverExistingInstances()
{
    UWorld* World = GetWorld();
    if (!World) return;

    int32 Count = 0;
    for (TActorIterator<ATwinInstance> It(World); It; ++It)
    {
        ATwinInstance* Inst = *It;
        if (!Inst || !IsValid(Inst)) continue;

        FString Id = Inst->GetInstanceId();
        if (Id.IsEmpty()) continue;

        // 避免重复注册
        if (InstanceRegistry.Contains(Id)) continue;

        InstanceRegistry.Add(Id, Inst);
        Count++;

        UE_LOG(LogTemp, Log,
               TEXT("[孪生管理器] 接管预置实例: %s (锁定=%s)"),
               *Id, Inst->bLocalOverrideLock ? TEXT("是") : TEXT("否"));
    }

    if (Count > 0)
    {
        UE_LOG(LogTemp, Log,
               TEXT("[孪生管理器] 共接管 %d 个编辑器预置实例"), Count);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 📸 快照固化到关卡（编辑器按钮）
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::SnapshotToLevel()
{
#if WITH_EDITOR
    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 📸 正在从后端拉取实例快照..."));

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
        FHttpModule::Get().CreateRequest();

    FString Url = FString::Printf(TEXT("%s/api/v2/state/snapshots"), *BackendBaseUrl);
    Request->SetURL(Url);
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnSnapshotResponse);

    Request->ProcessRequest();

    // 在编辑器中显示提示
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Cyan,
            TEXT("📸 正在从后端拉取快照..."));
    }
#else
    UE_LOG(LogTemp, Warning, TEXT("[孪生管理器] 快照固化仅在编辑器模式下可用"));
#endif
}

void ATwinSceneManager::OnSnapshotResponse(
    FHttpRequestPtr Request,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
#if WITH_EDITOR
    if (!bWasSuccessful || !Response.IsValid() || Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Error,
               TEXT("[孪生管理器] 📸 快照拉取失败 | Code=%d"),
               Response.IsValid() ? Response->GetResponseCode() : -1);

        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red,
                TEXT("❌ 快照拉取失败！请确认后端正在运行"));
        }
        return;
    }

    FString Body = Response->GetContentAsString();
    TArray<TSharedPtr<FJsonValue>> SnapshotArray;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Body);

    if (!FJsonSerializer::Deserialize(Reader, SnapshotArray))
    {
        UE_LOG(LogTemp, Error, TEXT("[孪生管理器] 📸 JSON 解析失败"));
        return;
    }

    UWorld* World = GetWorld();
    if (!World) return;

    int32 Created = 0;
    int32 Updated = 0;

    for (const auto& Val : SnapshotArray)
    {
        const TSharedPtr<FJsonObject>* SnapObj;
        if (!Val->TryGetObject(SnapObj)) continue;

        FString InstId;
        if (!(*SnapObj)->TryGetStringField(TEXT("instanceId"), InstId)) continue;

        // ── 解析 asset_id ────────────────────────────────────────────────
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

        // ── 检查是否已存在 ────────────────────────────────────────────────
        // 扫描关卡中所有 ATwinInstance 看是否有同 ID 的
        bool bExists = false;
        for (TActorIterator<ATwinInstance> It(World); It; ++It)
        {
            if ((*It)->GetInstanceId() == InstId)
            {
                // 已有：仅更新资产路径（不改位置，不改锁定状态）
                (*It)->AssetPath = AssetPathStr;
                bExists = true;
                Updated++;
                break;
            }
        }

        if (bExists) continue;

        // ── Spawn 新的编辑器持久 Actor ────────────────────────────────────
        FActorSpawnParameters SpawnParams;
        SpawnParams.Name = FName(*FString::Printf(TEXT("Twin_%s"), *InstId));

        UClass* SpawnClass = InstanceClass ? InstanceClass.Get() : ATwinInstance::StaticClass();

        ATwinInstance* Inst = World->SpawnActor<ATwinInstance>(
            SpawnClass,
            FVector::ZeroVector,
            FRotator::ZeroRotator,
            SpawnParams
        );

        if (!Inst) continue;

        // 配置属性
        Inst->InstanceId = InstId;
        Inst->AssetPath = AssetPathStr;
        Inst->bEditorPlaced = true;
        Inst->bLocalOverrideLock = false;  // 默认不锁定，用户可手动勾选

        Inst->SetActorLabel(FString::Printf(TEXT("🔹 %s"), *InstId));
        Inst->Tags.Add(FName(*InstId));

#if WITH_EDITOR
        Inst->SetFolderPath(TEXT("TwinInstances"));
#endif

        // 立即加载 Mesh（在编辑器中可见）
        Inst->InitializeTwin(InstId, AssetPathStr, BackendBaseUrl);

        Created++;
        UE_LOG(LogTemp, Log, TEXT("[孪生管理器] 📸 固化实例: %s → %s"), *InstId, *AssetPathStr);
    }

    FString Msg = FString::Printf(
        TEXT("📸 快照固化完成！新建 %d | 更新 %d | 总计 %d 个实例"),
        Created, Updated, SnapshotArray.Num());

    UE_LOG(LogTemp, Log, TEXT("[孪生管理器] %s"), *Msg);

    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green, Msg);
    }
#endif
}

// ═══════════════════════════════════════════════════════════════════════════
// 轮询逻辑
// ═══════════════════════════════════════════════════════════════════════════

void ATwinSceneManager::PollBackend()
{
    if (bRequestInFlight) return;

    UE_LOG(LogTemp, Log,
           TEXT("[孪生管理器] 轮询中... URL=%s/api/v2/state/snapshots | 现有实例数=%d"),
           *BackendBaseUrl, InstanceRegistry.Num());

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
        FHttpModule::Get().CreateRequest();

    FString Url = FString::Printf(TEXT("%s/api/v2/state/snapshots"), *BackendBaseUrl);
    Request->SetURL(Url);
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

    Request->OnProcessRequestComplete().BindUObject(
        this, &ATwinSceneManager::OnPollResponse);

    bRequestInFlight = true;
    Request->ProcessRequest();
}

void ATwinSceneManager::OnPollResponse(
    FHttpRequestPtr Request,
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

    // ── 检测已删除的实例 → 在场景中销毁（但保留编辑器预置的）─────────────
    TArray<FString> ToRemove;
    for (auto& Pair : InstanceRegistry)
    {
        if (!BackendInstanceIds.Contains(Pair.Key))
        {
            // 编辑器预置的 Actor 不销毁，仅从注册表移除（停止接收数据）
            if (Pair.Value && Pair.Value->bEditorPlaced)
            {
                UE_LOG(LogTemp, Log,
                       TEXT("[孪生管理器] 编辑器预置实例 %s 不在后端，跳过销毁"),
                       *Pair.Key);
                continue;
            }
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
    // 不设置 SpawnParams.Name —— 让 UE 自动生成 UObject 名称，
    // 避免上次 PIE 结束后 GC 待销毁 Actor 导致的同名冲突崩溃。
    // Actor 的可读标识通过下方 SetActorLabel 提供。
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

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
    Inst->SetActorLabel(FString::Printf(TEXT("🔹 %s"), *InstanceId));
    Inst->Tags.Add(FName(*InstanceId));

    // ── 放入世界大纲特定文件夹下 ─────────────────────────────────────────
#if WITH_EDITOR
    Inst->SetFolderPath(TEXT("TwinInstances"));
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
