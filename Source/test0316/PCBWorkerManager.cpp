// ============================================================================
// PCBWorkerManager.cpp  (v2 - 工位表驱动位置)
// ============================================================================

#include "PCBWorkerManager.h"
#include "PCBWorkerSyncComponent.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/World.h"

// ============================================================================
// 工位位置表 (来自 pos.csv，直接用 UE 坐标 cm)
//
//  workstation_id | upstream_key | pos_1                    | pos_2
//  WS-00          | REST         | (1970, -1300, 1)         | (2340,  -760, 1)
//  WS-01          | PCB-X100     | (-1720,  290, 1)         | (-1720, -320, 1)
//  WS-02          | PCB-X200     | ( -950,  290, 1)         | ( -950, -320, 1)
//  WS-03          | PCB-X300     | ( -360,  290, 1)         | ( -360, -320, 1)
//  WS-04          | PCB-X400     | (  170,  290, 1)         | (  170, -320, 1)
//  WS-05          | PCB-X500     | (  680,  290, 1)         | (  680, -320, 1)
//
// 分配规则：FW 奇数号(01/03/05) → pos_1，偶数号(02/04/06) → pos_2
// ============================================================================

struct FWSEntry
{
    FVector Pos1;
    FVector Pos2;
};

// 全局工位表（函数内 static，避免全局构造顺序问题）
static const TMap<FString, FWSEntry>& GetWorkstationTable()
{
    static TMap<FString, FWSEntry> Table;
    if (Table.Num() == 0)
    {
        // REST / WS-00
        FWSEntry Rest  = { FVector(1970,  -1300, 1), FVector(2340,  -760, 1) };
        Table.Add(TEXT("WS-00"),    Rest);
        Table.Add(TEXT("REST"),     Rest);
        // X100 / WS-01
        FWSEntry WS01  = { FVector(-1720,  290, 1), FVector(-1720, -320, 1) };
        Table.Add(TEXT("WS-01"),    WS01);
        Table.Add(TEXT("PCB-X100"), WS01);
        // X200 / WS-02
        FWSEntry WS02  = { FVector(-950,   290, 1), FVector(-950,  -320, 1) };
        Table.Add(TEXT("WS-02"),    WS02);
        Table.Add(TEXT("PCB-X200"), WS02);
        // X300 / WS-03
        FWSEntry WS03  = { FVector(-360,   290, 1), FVector(-360,  -320, 1) };
        Table.Add(TEXT("WS-03"),    WS03);
        Table.Add(TEXT("PCB-X300"), WS03);
        // X400 / WS-04
        FWSEntry WS04  = { FVector(170,    290, 1), FVector(170,   -320, 1) };
        Table.Add(TEXT("WS-04"),    WS04);
        Table.Add(TEXT("PCB-X400"), WS04);
        // X500 / WS-05
        FWSEntry WS05  = { FVector(680,    290, 1), FVector(680,   -320, 1) };
        Table.Add(TEXT("WS-05"),    WS05);
        Table.Add(TEXT("PCB-X500"), WS05);
    }
    return Table;
}

// ── 构造 ─────────────────────────────────────────────────────────────────────

APCBWorkerManager::APCBWorkerManager()
{
    PrimaryActorTick.bCanEverTick = false;
}

// ── 生命周期 ─────────────────────────────────────────────────────────────────

void APCBWorkerManager::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] ===== 初始化 ====="));
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] 中转站地址: %s"), *MiddlewareBaseUrl);

    ScanAndRegisterWorkers();
    FetchSnapshot();
}

void APCBWorkerManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    GetWorldTimerManager().ClearTimer(PollTimerHandle);
    Super::EndPlay(EndPlayReason);
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] 已停止，清理完毕"));
}

// ── 工人扫描与注册 ───────────────────────────────────────────────────────────

void APCBWorkerManager::ScanAndRegisterWorkers()
{
    WorkerRegistry.Empty();

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), AActor::StaticClass(), AllActors);

    for (AActor* Actor : AllActors)
    {
        if (!Actor || Actor == this) continue;
        UPCBWorkerSyncComponent* Comp = Actor->FindComponentByClass<UPCBWorkerSyncComponent>();
        if (Comp && !Comp->InstanceId.IsEmpty())
        {
            WorkerRegistry.Add(Comp->InstanceId, Comp);
            UE_LOG(LogTemp, Log, TEXT("[PCBManager] 已注册 → %s (%s)"),
                   *Comp->InstanceId, *Actor->GetName());
        }
    }

    RegisteredWorkerCount = WorkerRegistry.Num();
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] 共注册 %d 名工人"), RegisteredWorkerCount);

    if (RegisteredWorkerCount == 0)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[PCBManager] ⚠ 未找到任何工人!请确认 Actor 已挂载 PCBWorkerSyncComponent 并填写 InstanceId"));
    }
}

// ── 快照拉取 ─────────────────────────────────────────────────────────────────

void APCBWorkerManager::FetchSnapshot()
{
    if (bRequestInFlight) return;

    FString Url = MiddlewareBaseUrl + TEXT("/snapshot");
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] GET snapshot: %s"), *Url);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Req = FHttpModule::Get().CreateRequest();
    Req->SetURL(Url);
    Req->SetVerb(TEXT("GET"));
    Req->SetHeader(TEXT("Accept"), TEXT("application/json"));
    Req->OnProcessRequestComplete().BindUObject(this, &APCBWorkerManager::OnSnapshotReceived);
    bRequestInFlight = true;
    Req->ProcessRequest();
}

void APCBWorkerManager::RefreshSnapshot()
{
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] 手动刷新快照"));
    GetWorldTimerManager().ClearTimer(PollTimerHandle);
    bSnapshotLoaded  = false;
    FetchSnapshot();
}

void APCBWorkerManager::OnSnapshotReceived(FHttpRequestPtr Request, FHttpResponsePtr Response,
                                            bool bSuccess)
{
    bRequestInFlight = false;

    if (!bSuccess || !Response.IsValid())
    {
        bMiddlewareOnline = false;
        UE_LOG(LogTemp, Error, TEXT("[PCBManager] 快照请求失败，5s 后重试"));
        GetWorldTimerManager().SetTimer(PollTimerHandle, this,
            &APCBWorkerManager::FetchSnapshot, 5.f, false);
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        bMiddlewareOnline = false;
        UE_LOG(LogTemp, Error, TEXT("[PCBManager] 快照返回 HTTP %d"), Response->GetResponseCode());
        return;
    }

    TSharedPtr<FJsonObject> Root = ParseJsonResponse(Response);
    if (!Root.IsValid()) return;

    bMiddlewareOnline = true;
    ProcessSnapshotPayload(Root);
}

// ── 事件拉取 ─────────────────────────────────────────────────────────────────

void APCBWorkerManager::StartEventPolling()
{
    GetWorldTimerManager().ClearTimer(PollTimerHandle);
    GetWorldTimerManager().SetTimer(
        PollTimerHandle, this, &APCBWorkerManager::FetchEvents,
        EventPollIntervalSeconds, true);
    UE_LOG(LogTemp, Log, TEXT("[PCBManager] 开始事件轮询 %.1fs，lastEventId=%d"),
           EventPollIntervalSeconds, LastEventId);
}

void APCBWorkerManager::FetchEvents()
{
    if (bRequestInFlight) return;

    FString Url = FString::Printf(TEXT("%s/events?afterEventId=%d"),
                                  *MiddlewareBaseUrl, LastEventId);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Req = FHttpModule::Get().CreateRequest();
    Req->SetURL(Url);
    Req->SetVerb(TEXT("GET"));
    Req->SetHeader(TEXT("Accept"), TEXT("application/json"));
    Req->OnProcessRequestComplete().BindUObject(this, &APCBWorkerManager::OnEventsReceived);
    bRequestInFlight = true;
    Req->ProcessRequest();
}

void APCBWorkerManager::OnEventsReceived(FHttpRequestPtr Request, FHttpResponsePtr Response,
                                          bool bSuccess)
{
    bRequestInFlight = false;

    if (!bSuccess || !Response.IsValid())
    {
        bMiddlewareOnline = false;
        UE_LOG(LogTemp, Warning, TEXT("[PCBManager] 事件请求失败，下次重试"));
        return;
    }

    int32 Code = Response->GetResponseCode();
    if (Code == 409)  // cursor stale
    {
        UE_LOG(LogTemp, Warning, TEXT("[PCBManager] 游标过旧，重拉快照"));
        GetWorldTimerManager().ClearTimer(PollTimerHandle);
        bSnapshotLoaded = false;
        FetchSnapshot();
        return;
    }
    if (Code != 200)
    {
        UE_LOG(LogTemp, Warning, TEXT("[PCBManager] 事件返回 HTTP %d"), Code);
        return;
    }

    TSharedPtr<FJsonObject> Root = ParseJsonResponse(Response);
    if (!Root.IsValid()) return;

    bMiddlewareOnline = true;
    ProcessEventsPayload(Root);
}

// ── JSON 处理 ────────────────────────────────────────────────────────────────

void APCBWorkerManager::ProcessSnapshotPayload(const TSharedPtr<FJsonObject>& Root)
{
    int32 NewId = 0;
    Root->TryGetNumberField(TEXT("latestEventId"), NewId);
    LastEventId = NewId;

    const TArray<TSharedPtr<FJsonValue>>* Items;
    if (Root->TryGetArrayField(TEXT("items"), Items))
    {
        int32 Applied = 0;
        for (const auto& Val : *Items)
        {
            const TSharedPtr<FJsonObject>* Obj;
            if (Val->TryGetObject(Obj))
            {
                DispatchSnapshotItem(*Obj);
                Applied++;
            }
        }
        UE_LOG(LogTemp, Log, TEXT("[PCBManager] 快照应用 %d 工人，latestEventId=%d"),
               Applied, LastEventId);
    }

    bSnapshotLoaded = true;
    StartEventPolling();
}

void APCBWorkerManager::ProcessEventsPayload(const TSharedPtr<FJsonObject>& Root)
{
    const TArray<TSharedPtr<FJsonValue>>* Items;
    if (!Root->TryGetArrayField(TEXT("items"), Items) || Items->Num() == 0)
        return;

    TArray<TSharedPtr<FJsonObject>> Events;
    for (const auto& Val : *Items)
    {
        const TSharedPtr<FJsonObject>* Obj;
        if (Val->TryGetObject(Obj)) Events.Add(*Obj);
    }

    // 按 eventId 升序
    Events.Sort([](const TSharedPtr<FJsonObject>& A, const TSharedPtr<FJsonObject>& B)
    {
        int32 IdA = 0, IdB = 0;
        A->TryGetNumberField(TEXT("eventId"), IdA);
        B->TryGetNumberField(TEXT("eventId"), IdB);
        return IdA < IdB;
    });

    for (const auto& Ev : Events)
    {
        DispatchEvent(Ev);
        int32 EvId = 0;
        Ev->TryGetNumberField(TEXT("eventId"), EvId);
        if (EvId > LastEventId) LastEventId = EvId;
    }

    if (bDebugLog)
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBManager] 处理 %d 条事件，lastEventId → %d"),
               Events.Num(), LastEventId);
    }
}

// ── 事件分发 ─────────────────────────────────────────────────────────────────

void APCBWorkerManager::DispatchSnapshotItem(const TSharedPtr<FJsonObject>& Item)
{
    FString InstanceId;
    if (!Item->TryGetStringField(TEXT("instanceId"), InstanceId)) return;

    UPCBWorkerSyncComponent* Worker = FindWorker(InstanceId);
    if (!Worker)
    {
        if (bDebugLog)
            UE_LOG(LogTemp, Warning, TEXT("[PCBManager] 未注册的工人: %s"), *InstanceId);
        return;
    }

    // 解析 state
    const TSharedPtr<FJsonObject>* StateObj;
    if (!Item->TryGetObjectField(TEXT("state"), StateObj)) return;

    FString Status, WorkstationId, WorkstationName;
    (*StateObj)->TryGetStringField(TEXT("status"),          Status);
    (*StateObj)->TryGetStringField(TEXT("workstationId"),   WorkstationId);
    (*StateObj)->TryGetStringField(TEXT("workstationName"), WorkstationName);

    // 解析 metadata
    FString Name = InstanceId;
    const TSharedPtr<FJsonObject>* MetaObj;
    if (Item->TryGetObjectField(TEXT("metadata"), MetaObj))
        (*MetaObj)->TryGetStringField(TEXT("name"), Name);

    // 【v2】用工位表解析位置，完全忽略 position 字段
    FVector Location = ResolveWorkerPosition(InstanceId, WorkstationId, WorkstationName);

    UE_LOG(LogTemp, Log,
           TEXT("[PCBManager] 快照: %s(%s) → 工位=%s 位置=%s 状态=%s"),
           *InstanceId, *Name, *WorkstationId, *Location.ToString(), *Status);

    Worker->ApplySnapshot(Location, Status, Name, WorkstationName);
}

void APCBWorkerManager::DispatchEvent(const TSharedPtr<FJsonObject>& Event)
{
    FString EventType, InstanceId;
    if (!Event->TryGetStringField(TEXT("eventType"), EventType)) return;
    if (!Event->TryGetStringField(TEXT("instanceId"), InstanceId)) return;

    UPCBWorkerSyncComponent* Worker = FindWorker(InstanceId);
    if (!Worker) return;

    // ── position_changed：忽略上游坐标，改用工位表 ───────────────
    // （上游 position 精度不可靠，工位由 state.workstationId 决定）
    if (EventType == TEXT("position_changed"))
    {
        // 读取 to.workstationId 确定目标工位位置
        const TSharedPtr<FJsonObject>* ToState;
        if (!Event->TryGetObjectField(TEXT("to"), ToState)) return;

        FString WsId, WsName;
        (*ToState)->TryGetStringField(TEXT("workstationId"),   WsId);
        (*ToState)->TryGetStringField(TEXT("workstationName"), WsName);

        FString FromWsId;
        const TSharedPtr<FJsonObject>* FromState;
        if (Event->TryGetObjectField(TEXT("from"), FromState))
            (*FromState)->TryGetStringField(TEXT("workstationId"), FromWsId);

        // From 位置：仅做坐标查表，不更新占用表（工人此刻正在离开该工位）
        FVector From = LookupBasePosition(InstanceId, FromWsId, TEXT(""));
        // To 位置：更新占用表，计算错排偏移
        FVector To   = ResolveWorkerPosition(InstanceId, WsId, WsName);

        if (bDebugLog)
            UE_LOG(LogTemp, Log, TEXT("[PCBManager] 移动: %s  %s → %s"),
                   *InstanceId, *From.ToString(), *To.ToString());

        Worker->ApplyPositionChanged(From, To);
    }
    // ── state_changed ────────────────────────────────────────────
    else if (EventType == TEXT("state_changed"))
    {
        const TSharedPtr<FJsonObject>* ToState;
        if (!Event->TryGetObjectField(TEXT("to"), ToState)) return;

        FString Status, WsId, WsName;
        (*ToState)->TryGetStringField(TEXT("status"),          Status);
        (*ToState)->TryGetStringField(TEXT("workstationId"),   WsId);
        (*ToState)->TryGetStringField(TEXT("workstationName"), WsName);

        // 状态变化同时也移动到对应工位
        FVector NewPos = ResolveWorkerPosition(InstanceId, WsId, WsName);

        if (bDebugLog)
            UE_LOG(LogTemp, Log, TEXT("[PCBManager] 状态变: %s → %s @ %s (%s)"),
                   *InstanceId, *Status, *WsId, *NewPos.ToString());

        // 先更新位置（触发平滑移动），再更新状态
        Worker->ApplyPositionChanged(Worker->TargetWorldLocation, NewPos);
        Worker->ApplyStateChanged(Status, WsName);
    }
    // ── created ──────────────────────────────────────────────────
    else if (EventType == TEXT("created"))
    {
        UE_LOG(LogTemp, Log, TEXT("[PCBManager] 工人 %s 上线，重拉快照"), *InstanceId);
        RefreshSnapshot();
    }
    // ── removed ──────────────────────────────────────────────────
    else if (EventType == TEXT("removed"))
    {
        Worker->ApplyStateChanged(TEXT("offline"), TEXT(""));
    }
}

// ── 工位位置解析（v3 — 同工位多人时 X 方向自动错开）──────────────────────────
//
// 偏移规则（同一槽位内的排名 SlotIndex）：
//   SlotIndex 0 → X 偏移   0  cm（基准位置）
//   SlotIndex 1 → X 偏移 +200 cm
//   SlotIndex 2 → X 偏移 -200 cm
//   SlotIndex 3 → X 偏移 +400 cm  （依此类推）
//
// 工人进入新工位时自动注册进 StationOccupancy，
// 离开旧工位时通过 WorkerSlotMap 找到旧槽位并移除。
// ─────────────────────────────────────────────────────────────────────────────

FVector APCBWorkerManager::ResolveWorkerPosition(const FString& InstanceId,
                                                   const FString& WorkstationId,
                                                   const FString& WorkstationName)
{
    const TMap<FString, FWSEntry>& Table = GetWorkstationTable();

    // ── 1. 确定使用 pos_1 还是 pos_2（奇数工人→pos_1，偶数→pos_2）──────────
    int32 IdNum = 1;
    if (InstanceId.Len() >= 2)
    {
        FString NumStr = InstanceId.Right(2);
        IdNum = FCString::Atoi(*NumStr);
        if (IdNum == 0) IdNum = 1;
    }
    bool bUsePos1 = (IdNum % 2 != 0);

    // ── 2. 查工位表，得到基准坐标 ─────────────────────────────────────────
    FVector BasePos(0, 0, 1);
    FString ResolvedWsId = WorkstationId;   // 记录最终命中的 key，用于 slot key

    auto TryFind = [&](const FString& Key) -> bool
    {
        const FWSEntry* Entry = Table.Find(Key);
        if (!Entry) return false;
        BasePos      = bUsePos1 ? Entry->Pos1 : Entry->Pos2;
        ResolvedWsId = Key;
        return true;
    };

    bool bFound = false;
    if (!WorkstationId.IsEmpty())   bFound = TryFind(WorkstationId);
    if (!bFound && !WorkstationName.IsEmpty()) bFound = TryFind(WorkstationName);
    if (!bFound)
    {
        UE_LOG(LogTemp, Warning,
               TEXT("[PCBManager] ResolvePos: %s 工位未知(wsId=%s wsName=%s)，回退到 REST"),
               *InstanceId, *WorkstationId, *WorkstationName);
        TryFind(TEXT("WS-00"));
        ResolvedWsId = TEXT("WS-00");
    }

    // ── 3. 更新占用表：从旧槽位移除，注册到新槽位 ──────────────────────────
    FString NewSlotKey = ResolvedWsId + (bUsePos1 ? TEXT("_pos1") : TEXT("_pos2"));

    // 移除旧槽位记录
    FString* OldSlotKey = WorkerSlotMap.Find(InstanceId);
    if (OldSlotKey && *OldSlotKey != NewSlotKey)
    {
        TArray<FString>* OldList = StationOccupancy.Find(*OldSlotKey);
        if (OldList)
        {
            OldList->Remove(InstanceId);
            if (OldList->Num() == 0)
                StationOccupancy.Remove(*OldSlotKey);
        }
    }

    // 注册到新槽位（如果尚未在列表里）
    TArray<FString>& SlotList = StationOccupancy.FindOrAdd(NewSlotKey);
    if (!SlotList.Contains(InstanceId))
        SlotList.Add(InstanceId);
    WorkerSlotMap.Add(InstanceId, NewSlotKey);

    // ── 4. 计算该工人在槽位内的排名，得出 X 偏移 ──────────────────────────
    // 排名 0 → 偏移 0，排名 1 → +200，排名 2 → -200，排名 3 → +400 ...
    int32 SlotIndex = SlotList.IndexOfByKey(InstanceId);
    float XOffset = 0.0f;
    if (SlotIndex > 0)
    {
        int32 Sign      = (SlotIndex % 2 == 1) ? 1 : -1;
        int32 Magnitude = (SlotIndex + 1) / 2;
        XOffset = Sign * Magnitude * 200.0f;
    }

    FVector FinalPos = BasePos + FVector(XOffset, 0.0f, 0.0f);

    if (bDebugLog)
        UE_LOG(LogTemp, Log,
               TEXT("[PCBManager] ResolvePos: %s → %s | 槽排名=%d | X偏移=%.0f → %s"),
               *InstanceId, *NewSlotKey, SlotIndex, XOffset, *FinalPos.ToString());

    return FinalPos;
}

// ── 辅助 ─────────────────────────────────────────────────────────────────────

TSharedPtr<FJsonObject> APCBWorkerManager::ParseJsonResponse(FHttpResponsePtr Response)
{
    if (!Response.IsValid()) return nullptr;

    TSharedPtr<FJsonObject> Root;
    TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(Response->GetContentAsString());

    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("[PCBManager] JSON 解析失败: %s"),
               *Response->GetContentAsString().Left(200));
        return nullptr;
    }
    return Root;
}

UPCBWorkerSyncComponent* APCBWorkerManager::FindWorker(const FString& InInstanceId) const
{
    UPCBWorkerSyncComponent* const* Found = WorkerRegistry.Find(InInstanceId);
    return Found ? *Found : nullptr;
}

// ── 纯查表：仅返回基准坐标，不更新占用表 ─────────────────────────────────────
// 用于 position_changed 事件的 From 位置，工人此刻正在离开，不应更新占用表

FVector APCBWorkerManager::LookupBasePosition(const FString& InstanceId,
                                               const FString& WorkstationId,
                                               const FString& WorkstationName) const
{
    const TMap<FString, FWSEntry>& Table = GetWorkstationTable();

    int32 IdNum = 1;
    if (InstanceId.Len() >= 2)
    {
        FString NumStr = InstanceId.Right(2);
        IdNum = FCString::Atoi(*NumStr);
        if (IdNum == 0) IdNum = 1;
    }
    bool bUsePos1 = (IdNum % 2 != 0);

    auto TryGet = [&](const FString& Key, FVector& Out) -> bool
    {
        const FWSEntry* Entry = Table.Find(Key);
        if (!Entry) return false;
        Out = bUsePos1 ? Entry->Pos1 : Entry->Pos2;
        return true;
    };

    FVector Result(0, 0, 1);
    if (!WorkstationId.IsEmpty()   && TryGet(WorkstationId,   Result)) return Result;
    if (!WorkstationName.IsEmpty() && TryGet(WorkstationName, Result)) return Result;

    // 回退 REST
    TryGet(TEXT("WS-00"), Result);
    return Result;
}
