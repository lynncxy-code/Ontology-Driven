// ============================================================================
// TwinLabelWidget.cpp
//
// 统一头顶标签 Widget — Slate 实现
//
// 视觉结构：
//
//  ┌─────────────────────────────────────┐  ← OuterBorder（状态色描边，radius=14）
//  │ ╔═════════════════════════════════╗ │  ← InnerBorder（深色背景，radius=11）
//  │ ║  ⚠  S4 对接工位        [P1]  ║ │  ← 主标题行
//  │ ║     扭矩复核窗，待人工复核。   ║ │  ← 副标题行
//  │ ╚═════════════════════════════════╝ │
//  └─────────────────────────────────────┘
//
// 局部更新策略：
//   SetLabelData() 只更新改变了的节点（不重建 Slate 树），
//   保证高频调用时帧率稳定。
// ============================================================================

#include "TwinLabelWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Styling/CoreStyle.h"


// 图标字符已在 TwinLabelWidget.h 中通过 inline 函数定义

// ── 工具函数 ─────────────────────────────────────────────────────────────────

FLinearColor UTwinLabelWidget::GetStatusColor(const FString& Status)
{
    if (Status.Equals(TEXT("working"),  ESearchCase::IgnoreCase)) return TwinLabelStyle::StatusWorking;
    if (Status.Equals(TEXT("idle"),     ESearchCase::IgnoreCase)) return TwinLabelStyle::StatusIdle;
    if (Status.Equals(TEXT("warning"),  ESearchCase::IgnoreCase)) return TwinLabelStyle::StatusWarning;
    if (Status.Equals(TEXT("offline"),  ESearchCase::IgnoreCase)) return TwinLabelStyle::StatusOffline;
    return TwinLabelStyle::StatusDefault;
}

FString UTwinLabelWidget::GetIconCharacter(const FString& IconType)
{
    if (IconType.Equals(TEXT("warning"), ESearchCase::IgnoreCase)) return TwinLabelStyle::IconWarning();
    if (IconType.Equals(TEXT("info"),    ESearchCase::IgnoreCase)) return TwinLabelStyle::IconInfo();
    return TEXT("");
}

FString UTwinLabelWidget::InferIcon(const FString& Status)
{
    if (Status.Equals(TEXT("warning"),  ESearchCase::IgnoreCase)) return TEXT("warning");
    if (Status.Equals(TEXT("offline"),  ESearchCase::IgnoreCase)) return TEXT("warning");
    if (Status.Equals(TEXT("working"),  ESearchCase::IgnoreCase)) return TEXT("none");
    if (Status.Equals(TEXT("idle"),     ESearchCase::IgnoreCase)) return TEXT("none");
    return TEXT("none");
}

// ── RebuildWidget：构建 Slate 树 ─────────────────────────────────────────────

TSharedRef<SWidget> UTwinLabelWidget::RebuildWidget()
{
    using namespace TwinLabelStyle;

    // 静态笔刷（避免每帧重复构造）
    static FSlateRoundedBoxBrush OuterBrush(FLinearColor::White, OuterRadius);
    static FSlateRoundedBoxBrush InnerBrush(FLinearColor::White, InnerRadius);

    const FLinearColor InitStatusColor = GetStatusColor(CurrentData.Status);
    const FString      InitIcon        = (CurrentData.IconType == TEXT("none") || CurrentData.IconType.IsEmpty())
                                          ? InferIcon(CurrentData.Status)
                                          : CurrentData.IconType;
    const FString      InitIconChar    = GetIconCharacter(InitIcon);

    // ── 构建主标题行 ─────────────────────────────────────────────────────────
    TSharedPtr<SHorizontalBox> TitleRow = SNew(SHorizontalBox);

    // [左侧图标]
    TitleRow->AddSlot()
        .AutoWidth()
        .VAlign(VAlign_Center)
        .Padding(FMargin(0.f, 0.f, InitIconChar.IsEmpty() ? 0.f : 4.f, 0.f))
        [
            SAssignNew(IconSlate, STextBlock)
            .Text(FText::FromString(InitIconChar))
            .Font(FCoreStyle::GetDefaultFontStyle("Regular", IconFontSize))
            .ColorAndOpacity(FSlateColor(InitStatusColor))
            .Visibility(InitIconChar.IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible)
        ];

    // [主标题文字] 居中
    TitleRow->AddSlot()
        .AutoWidth()
        .VAlign(VAlign_Center)
        [
            SAssignNew(TitleSlate, STextBlock)
            .Text(FText::FromString(CurrentData.Title))
            .Font(FCoreStyle::GetDefaultFontStyle("Bold", TitleFontSize))
            .ColorAndOpacity(FSlateColor(TitleColor))
            .Justification(ETextJustify::Center)
            .AutoWrapText(false)
        ];

    // Badge 已移除（用户不需要）

    // ── 构建内容区 VBox（居中）─────────────────────────────────────────────
    TSharedRef<SVerticalBox> ContentBox = SNew(SVerticalBox)

        // 主标题行 居中
        + SVerticalBox::Slot()
        .AutoHeight()
        .HAlign(HAlign_Center)
        [
            TitleRow.ToSharedRef()
        ]

        // 副标题 居中
        + SVerticalBox::Slot()
        .AutoHeight()
        .HAlign(HAlign_Center)
        .Padding(FMargin(0.f, TitleSubtitleGap, 0.f, 0.f))
        [
            SAssignNew(SubtitleSlate, STextBlock)
            .Text(FText::FromString(CurrentData.Subtitle))
            .Font(FCoreStyle::GetDefaultFontStyle("Regular", SubtitleFontSize))
            .ColorAndOpacity(FSlateColor(SubtitleColor))
            .Justification(ETextJustify::Center)
            .AutoWrapText(false)
            .Visibility(CurrentData.Subtitle.IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible)
        ];

    // ── 组装：OuterBorder（描边）→ InnerBorder（背景）→ 内容 ──────────────────────────
    return
        SNew(SBox)
        .WidthOverride(CardWidth)
        .HeightOverride(CardHeight)
        [
            SAssignNew(OuterBorder, SBorder)
            .BorderImage(&OuterBrush)
            .BorderBackgroundColor(InitStatusColor)
            .Padding(BorderThickness)
            .HAlign(HAlign_Fill)      // 修复：必须是 Fill，让内部黑色背景撑满左右，否则剩余区域都会变成绿色描边！
            .VAlign(VAlign_Fill)      // 修复：必须是 Fill
            [
                SNew(SBorder)
                .BorderImage(&InnerBrush)
                .BorderBackgroundColor(BgColor)
                .Padding(FMargin(PaddingH, PaddingV))
                .HAlign(HAlign_Center)
                .VAlign(VAlign_Center)
                [
                    ContentBox
                ]
            ]
        ];
}

// ── SetLabelData：局部更新，不重建 Slate 树 ──────────────────────────────────

void UTwinLabelWidget::SetLabelData(const FTwinLabelData& InData)
{
    using namespace TwinLabelStyle;

    const bool bStatusChanged   = InData.Status   != CurrentData.Status;
    const bool bTitleChanged    = InData.Title     != CurrentData.Title;
    const bool bSubtitleChanged = InData.Subtitle  != CurrentData.Subtitle;
    const bool bBadgeChanged    = InData.Badge     != CurrentData.Badge;
    const bool bIconChanged     = InData.IconType  != CurrentData.IconType;

    CurrentData = InData;

    // 首次（Slate 树可能还未构建）
    if (!OuterBorder.IsValid()) return;

    // ── 状态色描边 ──────────────────────────────────────────────────
    if (bStatusChanged)
    {
        FLinearColor StatusColor = GetStatusColor(InData.Status);
        OuterBorder->SetBorderBackgroundColor(StatusColor);
        if (IconSlate.IsValid() && InData.IconType == TEXT("none"))
            IconSlate->SetColorAndOpacity(FSlateColor(StatusColor));
    }

    // ── 图标 ───────────────────────────────────────────────────────────────
    if (bIconChanged || bStatusChanged)
    {
        FString IconType = (InData.IconType == TEXT("none") || InData.IconType.IsEmpty())
                            ? InferIcon(InData.Status)
                            : InData.IconType;
        FString IconChar = GetIconCharacter(IconType);

        if (IconSlate.IsValid())
        {
            IconSlate->SetText(FText::FromString(IconChar));
            IconSlate->SetVisibility(IconChar.IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible);
            if (!bStatusChanged)
            {
                IconSlate->SetColorAndOpacity(FSlateColor(GetStatusColor(InData.Status)));
            }
        }
    }

    // ── 主标题 ────────────────────────────────────────────────────────────
    if (bTitleChanged && TitleSlate.IsValid())
    {
        TitleSlate->SetText(FText::FromString(InData.Title));
    }

    // ── 副标题 ────────────────────────────────────────────────────────────
    if (bSubtitleChanged && SubtitleSlate.IsValid())
    {
        SubtitleSlate->SetText(FText::FromString(InData.Subtitle));
        SubtitleSlate->SetVisibility(
            InData.Subtitle.IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible);
    }

    // ── Badge ─────────────────────────────────────────────────────────────
    if (bBadgeChanged)
    {
        if (BadgeTextSlate.IsValid())
            BadgeTextSlate->SetText(FText::FromString(InData.Badge));
        if (BadgeContainer.IsValid())
            BadgeContainer->SetVisibility(
                InData.Badge.IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible);
    }
}
