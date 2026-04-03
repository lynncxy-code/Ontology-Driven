// ============================================================================
// TwinCADDispatcher.cpp
//
// CAD 一键生成总调度器 — 从后端 HTTP 拉取 JSON 并协调墙体生成器和立柱摆放器
//
// 数据流：
//   [编辑器按钮] → GenerateAll()
//     → HTTP GET ApiUrl
//       → OnHttpResponseReceived()
//         → DispatchFromJsonString()
//           ├─ ATwinStructureBuilder::BuildWallsFromJsonString()
//           └─ ATwinColumnPlacer::PlaceColumns()
// ============================================================================

#include "TwinCADDispatcher.h"
#include "TwinStructureBuilder.h"
#include "TwinColumnPlacer.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

// ── 构造函数 ─────────────────────────────────────────────────────────────────

ATwinCADDispatcher::ATwinCADDispatcher()
{
    PrimaryActorTick.bCanEverTick = false;

    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("RootComponent"));
    SetRootComponent(Root);
}

// ── BeginPlay ────────────────────────────────────────────────────────────────

void ATwinCADDispatcher::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 已就绪 | API = %s"), *ApiUrl);
}

// ═══════════════════════════════════════════════════════════════════════════
// 确保子系统 Actor 存在
// ═══════════════════════════════════════════════════════════════════════════

ATwinStructureBuilder* ATwinCADDispatcher::EnsureStructureBuilder()
{
    if (StructureBuilder && IsValid(StructureBuilder))
        return StructureBuilder;

    UWorld* World = GetWorld();
    if (!World) return nullptr;

    for (TActorIterator<ATwinStructureBuilder> It(World); It; ++It)
    {
        StructureBuilder = *It;
        UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 找到已有的墙体生成器"));
        return StructureBuilder;
    }

    FActorSpawnParameters Params;
    Params.Name = FName(TEXT("CAD_StructureBuilder"));
    StructureBuilder = World->SpawnActor<ATwinStructureBuilder>(
        ATwinStructureBuilder::StaticClass(),
        FVector::ZeroVector, FRotator::ZeroRotator, Params);

#if WITH_EDITOR
    if (StructureBuilder)
    {
        StructureBuilder->SetActorLabel(TEXT("🏗️ CAD 墙体生成器"));
        StructureBuilder->SetFolderPath(TEXT("CAD_Generated"));
    }
#endif

    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 自动创建了墙体生成器"));
    return StructureBuilder;
}

ATwinColumnPlacer* ATwinCADDispatcher::EnsureColumnPlacer()
{
    if (ColumnPlacer && IsValid(ColumnPlacer))
        return ColumnPlacer;

    UWorld* World = GetWorld();
    if (!World) return nullptr;

    for (TActorIterator<ATwinColumnPlacer> It(World); It; ++It)
    {
        ColumnPlacer = *It;
        UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 找到已有的立柱摆放器"));
        return ColumnPlacer;
    }

    FActorSpawnParameters Params;
    Params.Name = FName(TEXT("CAD_ColumnPlacer"));
    ColumnPlacer = World->SpawnActor<ATwinColumnPlacer>(
        ATwinColumnPlacer::StaticClass(),
        FVector::ZeroVector, FRotator::ZeroRotator, Params);

#if WITH_EDITOR
    if (ColumnPlacer)
    {
        ColumnPlacer->SetActorLabel(TEXT("🏛️ CAD 立柱摆放器"));
        ColumnPlacer->SetFolderPath(TEXT("CAD_Generated"));
    }
#endif

    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 自动创建了立柱摆放器"));
    return ColumnPlacer;
}

// ═══════════════════════════════════════════════════════════════════════════
// 🚀 一键生成全部 — 发起 HTTP 请求
// ═══════════════════════════════════════════════════════════════════════════

void ATwinCADDispatcher::GenerateAll()
{
    if (ApiUrl.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 调度器] API 地址为空！请在 Details 面板填入后端地址。"));
        if (GEngine)
            GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Red,
                TEXT("❌ API 地址为空，请先填写后端地址"));
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 🚀 正在从后端拉取 CAD JSON: %s"), *ApiUrl);

    if (GEngine)
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Yellow,
            TEXT("🚀 正在从后端拉取 CAD 数据..."));

    // ── 发起 HTTP GET（与 TwinSceneManager/DigitalTwinSyncComponent 相同模式）──
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
        FHttpModule::Get().CreateRequest();

    Request->SetURL(ApiUrl);
    Request->SetVerb(TEXT("GET"));
    Request->SetHeader(TEXT("Accept"), TEXT("application/json"));

    // 绑定响应回调（UE 保证在 Game Thread 执行）
    Request->OnProcessRequestComplete().BindUObject(
        this, &ATwinCADDispatcher::OnHttpResponseReceived);

    Request->ProcessRequest();
}

// ═══════════════════════════════════════════════════════════════════════════
// HTTP 响应回调
// ═══════════════════════════════════════════════════════════════════════════

void ATwinCADDispatcher::OnHttpResponseReceived(
    FHttpRequestPtr Request,
    FHttpResponsePtr Response,
    bool bWasSuccessful)
{
    // ── 网络层错误 ────────────────────────────────────────────────────────
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error,
            TEXT("[CAD 调度器] ❌ HTTP 请求失败，请检查后端是否运行 | URL: %s"), *ApiUrl);
        if (GEngine)
            GEngine->AddOnScreenDebugMessage(-1, 6.0f, FColor::Red,
                FString::Printf(TEXT("❌ 无法连接后端: %s"), *ApiUrl));
        return;
    }

    // ── HTTP 状态码 ───────────────────────────────────────────────────────
    const int32 Code = Response->GetResponseCode();
    if (Code == 404)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("[CAD 调度器] ⚠️ 后端 404：尚未上传任何 DXF 图纸"));
        if (GEngine)
            GEngine->AddOnScreenDebugMessage(-1, 6.0f, FColor::Orange,
                TEXT("⚠️ 后端暂无数据，请先在 Web 界面上传 DXF 图纸"));
        return;
    }
    if (Code != 200)
    {
        UE_LOG(LogTemp, Error,
            TEXT("[CAD 调度器] ❌ 后端返回非预期状态码: %d"), Code);
        return;
    }

    // ── 转发给分发函数处理 ────────────────────────────────────────────────
    const FString JsonString = Response->GetContentAsString();
    UE_LOG(LogTemp, Log,
        TEXT("[CAD 调度器] 已收到 JSON (%d bytes)，开始分发生成..."), JsonString.Len());

    DispatchFromJsonString(JsonString);
}

// ═══════════════════════════════════════════════════════════════════════════
// 分发生成：JSON → 墙体 + 立柱
// ═══════════════════════════════════════════════════════════════════════════

void ATwinCADDispatcher::DispatchFromJsonString(const FString& JsonString)
{
    // ── 1. 生成墙体 ─────────────────────────────────────────────────────────
    ATwinStructureBuilder* Builder = EnsureStructureBuilder();
    if (Builder)
    {
        Builder->CoordScale = this->CoordScale;
        if (this->DefaultWallMaterial)
        {
            Builder->WallMaterial = this->DefaultWallMaterial;
        }
        Builder->BuildWallsFromJsonString(JsonString);
        UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] ✅ 墙体生成完毕"));
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 调度器] ❌ 墙体生成器创建失败"));
    }

    // ── 2. 摆放立柱 ─────────────────────────────────────────────────────────
    ATwinColumnPlacer* Placer = EnsureColumnPlacer();
    if (Placer)
    {
        Placer->CoordScale = this->CoordScale;
        Placer->ColumnScaleMultiplier = this->ColumnScaleMultiplier;
        Placer->MeshMappingTable = this->MeshMappingTable;
        Placer->DefaultColumnMesh = this->DefaultColumnMesh;

        // 生成前先清理旧实例，防止重复生成叠加
        Placer->ClearAllInstances();

        TArray<FTwinColumnData> ColumnData;
        if (ATwinColumnPlacer::ParseJsonToColumnData(JsonString, ColumnData))
        {
            Placer->PlaceColumns(ColumnData);
            UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] ✅ 立柱摆放完毕"));
        }
        else
        {
            UE_LOG(LogTemp, Warning,
                TEXT("[CAD 调度器] JSON 中未找到立柱数据（无 INSTANCE 类型实体）"));
        }
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[CAD 调度器] ❌ 立柱摆放器创建失败"));
    }

    // ── 3. 完成通知 ─────────────────────────────────────────────────────────
    if (GEngine)
        GEngine->AddOnScreenDebugMessage(-1, 5.0f, FColor::Green,
            TEXT("🎉 CAD 场景一键生成完毕！"));

    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 🎉 全部生成任务完成"));
}

// ═══════════════════════════════════════════════════════════════════════════
// 🧹 清除已生成内容
// ═══════════════════════════════════════════════════════════════════════════

void ATwinCADDispatcher::ClearAll()
{
    UE_LOG(LogTemp, Log, TEXT("[CAD 调度器] 🧹 清除所有已生成内容..."));

    if (StructureBuilder && IsValid(StructureBuilder))
    {
        // 仅清除墙体网格，不要销毁 Actor
        StructureBuilder->ClearAllWalls();
    }

    if (ColumnPlacer && IsValid(ColumnPlacer))
    {
        // 仅清除实例，不要销毁 Actor，以保留用户在 Details 面板设置的参数
        ColumnPlacer->ClearAllInstances();
    }

    if (GEngine)
        GEngine->AddOnScreenDebugMessage(-1, 3.0f, FColor::Orange,
            TEXT("🧹 已清除所有 CAD 生成内容"));
}
