// ============================================================================
// TwinLabelWidget.h
//
// 统一头顶标签 Widget（纯 Slate C++ 实现）
//
// 设计规格：
//   ● 深色不透明背景板（#0E0F13）
//   ● 大圆角（外 14px / 内 12px）
//   ● 状态色描边（2px，颜色由 FTwinLabelData::Status 驱动）
//   ● 主标题：白色粗体 14pt
//   ● 副标题：白色 65% 透明度 11pt
//   ● 右上角可选 Badge（小圆角标签）
//   ● 左侧可选图标（Unicode 字符）
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TwinLabelWidget.generated.h"

// ============================================================================
// 标签数据结构体 —— 调用方只需填这个结构体，Widget 内部驱动所有视觉
// ============================================================================

USTRUCT(BlueprintType)
struct FTwinLabelData
{
    GENERATED_BODY()

    /** 主标题（粗体大字）例：FW-01 / S4 对接工位 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Title;

    /** 副标题（细体小字）例：工位名称 / 状态描述 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Subtitle;

    /**
     * 右上角 Badge 短文本（留空则不显示）
     * 例："P1" / "WS-04" / "2号"
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Badge;

    /**
     * 状态字符串，驱动描边颜色与左侧图标
     * 内置值："working" | "idle" | "warning" | "offline"
     * 其他值 → 使用 DefaultBorderColor
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString Status;

    /**
     * 左侧图标类型
     * "warning" → ⚠   "info" → ●   "none" / "" → 不显示
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FString IconType = TEXT("none");

    FTwinLabelData() {}

    FTwinLabelData(const FString& InTitle,
                   const FString& InSubtitle,
                   const FString& InBadge = TEXT(""),
                   const FString& InStatus = TEXT(""),
                   const FString& InIcon   = TEXT("none"))
        : Title(InTitle)
        , Subtitle(InSubtitle)
        , Badge(InBadge)
        , Status(InStatus)
        , IconType(InIcon)
    {}
};

// ============================================================================
// 样式常量命名空间 —— 所有视觉参数集中在这里，改一处全局生效
// ============================================================================

namespace TwinLabelStyle
{
    // ── 卡片尺寸（与 DrawSize 保持同比例）───────────────────────────────────
    static constexpr float CardWidth        = 504.f;  // 增加20%（原420）
    static constexpr float CardHeight       = 180.f;  // 高度增加一倍
    static constexpr float OuterRadius      = 30.f;   // 高分辨率下圆角
    static constexpr float InnerRadius      = 24.f;
    static constexpr float BorderThickness  = 3.f;    // 3px 与 140px 厂展到 420px
    static constexpr float PaddingH         = 24.f;
    static constexpr float PaddingV         = 12.f;
    static constexpr float TitleSubtitleGap = 6.f;

    // ── 背景色 ──────────────────────────────────────────────────────
    // 纯黑，80% 不透明
    static const FLinearColor BgColor        = FLinearColor(0.f, 0.f, 0.f, 0.8f);
    static const FLinearColor BadgeBgColor   = FLinearColor(0.13f, 0.14f, 0.17f, 0.6f);

    // ── 文字色 ──────────────────────────────────────────────────────
    static const FLinearColor TitleColor    = FLinearColor(1.f,  1.f,  1.f,  1.0f);
    static const FLinearColor SubtitleColor = FLinearColor(1.f,  1.f,  1.f,  0.65f);
    static const FLinearColor BadgeColor    = FLinearColor(1.f,  1.f,  1.f,  0.85f);

    // ── 状态描边色 ──────────────────────────────────────────────────
    static const FLinearColor StatusWorking  = FLinearColor(0.18f, 0.86f, 0.46f, 1.f); // #2EDC75 绿
    static const FLinearColor StatusIdle     = FLinearColor(0.50f, 0.52f, 0.58f, 1.f); // #808595 灰
    static const FLinearColor StatusWarning  = FLinearColor(1.00f, 0.56f, 0.12f, 1.f); // #FF8F1F 橙
    static const FLinearColor StatusOffline  = FLinearColor(0.90f, 0.22f, 0.22f, 1.f); // #E63838 红
    static const FLinearColor StatusDefault  = FLinearColor(0.30f, 0.36f, 0.50f, 1.f); // #4D5C80 蓝灰

    // ── 字号 ────────────────────────────────────────────────────────────
    static constexpr int32 TitleFontSize    = 36;
    static constexpr int32 SubtitleFontSize = 28;
    static constexpr int32 BadgeFontSize    = 24;
    static constexpr int32 IconFontSize     = 32;

    // ── 图标 Unicode ────────────────────────────────────────────────────
    inline const FString& IconWarning() { static FString S(TEXT("\u26A0")); return S; }  // ⚠
    inline const FString& IconInfo()    { static FString S(TEXT("\u25CF")); return S; }  // ●
}

// ============================================================================
// UTwinLabelWidget —— 统一头顶标签 Widget 类
// ============================================================================

UCLASS()
class TEST0316_API UTwinLabelWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    /** 更新所有显示内容（线程安全：只在 GameThread 调用） */
    void SetLabelData(const FTwinLabelData& InData);

    /** 获取当前数据（用于外部查询） */
    const FTwinLabelData& GetLabelData() const { return CurrentData; }

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    // ── Slate 节点引用（用于局部更新，避免重建整棵树）────────────────────
    TSharedPtr<SWidget>    RootSlate;         // 整棵树的根

    // 外层边框（持有引用以便动态改颜色）
    TSharedPtr<SBorder>    OuterBorder;

    // 内容节点
    TSharedPtr<STextBlock> IconSlate;
    TSharedPtr<STextBlock> TitleSlate;
    TSharedPtr<STextBlock> SubtitleSlate;
    TSharedPtr<STextBlock> BadgeTextSlate;
    TSharedPtr<SBorder>    BadgeContainer;    // Badge 的背景容器（控制显隐）

    // ── 状态缓存 ────────────────────────────────────────────────────────
    FTwinLabelData CurrentData;

    // ── 样式工具 ────────────────────────────────────────────────────────

    /** 根据 Status 字符串返回对应描边颜色 */
    static FLinearColor GetStatusColor(const FString& Status);

    /** 根据 IconType 返回 Unicode 图标字符串（空字符串 = 不显示） */
    static FString GetIconCharacter(const FString& IconType);

    /** 根据 Status 推断默认 IconType（若调用方传入 "none" 则不覆盖） */
    static FString InferIcon(const FString& Status);
};
