// ============================================================================
// AGVSimLogLoader.cpp
// ============================================================================

#include "AGVSimLogLoader.h"
#include "AGVPatrolComponent.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"

// 静态空帧数组
const TArray<FAgvFrame> UAGVSimLogLoader::EmptyFrames;

UAGVSimLogLoader::UAGVSimLogLoader()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UAGVSimLogLoader::BeginPlay()
{
    Super::BeginPlay();
    ReloadAndInject();
}

// ─────────────────────────────────────────────────────────────────────────────
// 公开接口
// ─────────────────────────────────────────────────────────────────────────────

void UAGVSimLogLoader::ReloadAndInject()
{
    // Warning 级别确保在任何日志过滤级别下都能看见
    UE_LOG(LogTemp, Warning, TEXT("[AGVSimLogLoader] ===== ReloadAndInject 开始 ===== CsvPath=%s"), *CsvPath);

    FrameMap.Empty();
    ParsedAgvCount  = 0;
    InjectedAgvCount = 0;

    if (CsvPath.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("[AGVSimLogLoader] CsvPath 未填写，跳过加载。请在 Details 面板填写 CSV 路径。"));
        return;
    }

    if (!ParseCsv(CsvPath))
    {
        UE_LOG(LogTemp, Error, TEXT("[AGVSimLogLoader] CSV 解析失败：%s"), *CsvPath);
        return;
    }

    ParsedAgvCount = FrameMap.Num();
    UE_LOG(LogTemp, Warning, TEXT("[AGVSimLogLoader] 解析完成，共 %d 台 AGV。"), ParsedAgvCount);

    InjectToScene();
}

const TArray<FAgvFrame>& UAGVSimLogLoader::GetFramesForSerial(const FString& Serial) const
{
    if (const TArray<FAgvFrame>* Found = FrameMap.Find(Serial))
    {
        return *Found;
    }
    return EmptyFrames;
}

// ─────────────────────────────────────────────────────────────────────────────
// CSV 解析
// ─────────────────────────────────────────────────────────────────────────────

bool UAGVSimLogLoader::ParseCsv(const FString& FilePath)
{
    FString RawText;
    if (!FFileHelper::LoadFileToString(RawText, *FilePath))
    {
        UE_LOG(LogTemp, Error, TEXT("[AGVSimLogLoader] 无法读取文件：%s"), *FilePath);
        return false;
    }

    TArray<FString> Lines;
    RawText.ParseIntoArrayLines(Lines, false);

    if (Lines.Num() < 2)
    {
        UE_LOG(LogTemp, Error, TEXT("[AGVSimLogLoader] CSV 文件行数不足，至少需要表头 + 1 行数据。"));
        return false;
    }

    // ── 解析表头，建立列名 → 列索引映射 ──────────────────────────────────
    TArray<FString> Headers;
    Lines[0].ParseIntoArray(Headers, TEXT(","), false);

    TMap<FString, int32> ColIndex;
    for (int32 i = 0; i < Headers.Num(); ++i)
    {
        FString ColName = Headers[i].TrimStartAndEnd();
        // 去除 UTF-8 BOM
        ColName.RemoveFromStart(TEXT("\xEF\xBB\xBF"));
        ColName.RemoveFromStart(TEXT("\uFEFF"));
        // 去除 csv.QUOTE_ALL 产生的首尾引号，如 "serial" → serial
        if (ColName.StartsWith(TEXT("\"")) && ColName.EndsWith(TEXT("\"")))
        {
            ColName = ColName.Mid(1, ColName.Len() - 2);
        }
        ColIndex.Add(ColName, i);
    }

    // 打印实际解析到的列名，方便排查格式问题
    UE_LOG(LogTemp, Warning, TEXT("[AGVSimLogLoader] CSV 表头共 %d 列，首列=[%s]"), ColIndex.Num(), *Headers[0]);

    // 必要列检查
    const TArray<FString> RequiredCols = {
        TEXT("serial"), TEXT("time"),
        TEXT("positionX"), TEXT("positionY"), TEXT("positionZ"),
        TEXT("orientationX"), TEXT("orientationY"), TEXT("orientationZ"), TEXT("orientationW"),
        TEXT("yaw"), TEXT("cargo_status")
    };
    for (const FString& Col : RequiredCols)
    {
        if (!ColIndex.Contains(Col))
        {
            UE_LOG(LogTemp, Error,
                   TEXT("[AGVSimLogLoader] CSV 缺少必要列：%s（请检查表头格式）"), *Col);
            return false;
        }
    }

    // ── 逐行解析 ────────────────────────────────────────────────────────────
    for (int32 LineIdx = 1; LineIdx < Lines.Num(); ++LineIdx)
    {
        const FString& Line = Lines[LineIdx];
        if (Line.TrimStartAndEnd().IsEmpty()) continue;

        TArray<FString> Row;
        Line.ParseIntoArray(Row, TEXT(","), false);

        if (Row.Num() < ColIndex.Num()) continue; // 行列数不足，跳过

        // 去掉所有字段中由 csv.QUOTE_ALL 产生的引号
        for (FString& Cell : Row)
        {
            Cell = Cell.TrimStartAndEnd();
            if (Cell.StartsWith(TEXT("\"")) && Cell.EndsWith(TEXT("\"")))
            {
                Cell = Cell.Mid(1, Cell.Len() - 2);
            }
        }

        const FString Serial = ParseString(ColIndex, Row, TEXT("serial"));
        if (Serial.IsEmpty()) continue;

        FAgvFrame Frame;
        Frame.Time = ParseFloat(ColIndex, Row, TEXT("time"), 0.f);

        // 坐标（应用缩放和偏置）
        float px = ParseFloat(ColIndex, Row, TEXT("positionX"));
        float py = ParseFloat(ColIndex, Row, TEXT("positionY"));
        float pz = ParseFloat(ColIndex, Row, TEXT("positionZ"));
        Frame.Position = FVector(px, py, pz) * CoordScale + CoordOffset;

        // 四元数
        float ox = ParseFloat(ColIndex, Row, TEXT("orientationX"));
        float oy = ParseFloat(ColIndex, Row, TEXT("orientationY"));
        float oz = ParseFloat(ColIndex, Row, TEXT("orientationZ"));
        float ow = ParseFloat(ColIndex, Row, TEXT("orientationW"), 1.f);
        Frame.Orientation = FQuat(ox, oy, oz, ow).GetNormalized();

        // 偏航角（弧度）
        Frame.Yaw = ParseFloat(ColIndex, Row, TEXT("yaw"), 0.f);

        // 货物状态
        FString CargoStr = ParseString(ColIndex, Row, TEXT("cargo_status"));
        Frame.bHasCargo = (CargoStr != TEXT("[0]"));

        // 按 serial 分组
        FrameMap.FindOrAdd(Serial).Add(Frame);
    }

    // ── 每个 serial 按 Time 排序，确保回放顺序正确 ──────────────────────────
    for (auto& Pair : FrameMap)
    {
        Pair.Value.Sort([](const FAgvFrame& A, const FAgvFrame& B)
        {
            return A.Time < B.Time;
        });
    }

    if (bDebugLog)
    {
        for (const auto& Pair : FrameMap)
        {
            UE_LOG(LogTemp, Log,
                   TEXT("[AGVSimLogLoader]   serial=%s  帧数=%d  时长=%.1f秒"),
                   *Pair.Key, Pair.Value.Num(),
                   Pair.Value.Last().Time - Pair.Value[0].Time);
        }
    }

    return FrameMap.Num() > 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// 注入场景
// ─────────────────────────────────────────────────────────────────────────────

void UAGVSimLogLoader::InjectToScene()
{
    UWorld* World = GetWorld();
    if (!World) return;

    // 遍历场景所有 Actor，查找携带 UAGVPatrolComponent 的
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        UAGVPatrolComponent* PatrolComp =
            Actor->FindComponentByClass<UAGVPatrolComponent>();
        if (!PatrolComp) continue;

        const FString& Serial = PatrolComp->AgvSerial;
        if (Serial.IsEmpty()) continue;

        TArray<FAgvFrame>* Frames = FrameMap.Find(Serial);
        if (!Frames || Frames->IsEmpty())
        {
            if (bDebugLog)
            {
                UE_LOG(LogTemp, Warning,
                       TEXT("[AGVSimLogLoader] 场景中找到 AgvSerial=%s，但 CSV 中无对应数据，跳过。"),
                       *Serial);
            }
            continue;
        }

        // 注入帧序列，组件内部将自动切换为 CSV 回放模式
        PatrolComp->InjectSimFrames(*Frames);
        InjectedAgvCount++;

        if (bDebugLog)
        {
            UE_LOG(LogTemp, Log,
                   TEXT("[AGVSimLogLoader] 注入成功 → Actor=%s  serial=%s  帧数=%d"),
                   *Actor->GetName(), *Serial, Frames->Num());
        }
    }

    UE_LOG(LogTemp, Warning,
           TEXT("[AGVSimLogLoader] ===== 注入完成：%d / %d 台 AGV 已启动 CSV 回放模式 ====="),
           InjectedAgvCount, ParsedAgvCount);
}

// ─────────────────────────────────────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────────────────────────────────────

float UAGVSimLogLoader::ParseFloat(const TMap<FString, int32>& ColIndex,
                                   const TArray<FString>& Row,
                                   const FString& ColName,
                                   float DefaultValue)
{
    const int32* IdxPtr = ColIndex.Find(ColName);
    if (!IdxPtr || *IdxPtr >= Row.Num()) return DefaultValue;

    float Result = DefaultValue;
    LexFromString(Result, *Row[*IdxPtr].TrimStartAndEnd());
    return Result;
}

FString UAGVSimLogLoader::ParseString(const TMap<FString, int32>& ColIndex,
                                      const TArray<FString>& Row,
                                      const FString& ColName)
{
    const int32* IdxPtr = ColIndex.Find(ColName);
    if (!IdxPtr || *IdxPtr >= Row.Num()) return FString();
    return Row[*IdxPtr].TrimStartAndEnd();
}
