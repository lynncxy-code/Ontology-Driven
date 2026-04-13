// ============================================================================
// PCBWorkerInfoWidget.cpp
//
// 纯 Slate 构建 — RebuildWidget 直接创建 SWidget 树
// ============================================================================

#include "PCBWorkerInfoWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"

TSharedRef<SWidget> UPCBWorkerInfoWidget::RebuildWidget()
{
    // 静态笔刷避免每次 Tick 重复创建，使用圆角半径为 8.0
    static FSlateRoundedBoxBrush RoundedBgBrush(FLinearColor::White, 8.0f);

    return SNew(SBox)
        .WidthOverride(200.f)
        .HeightOverride(60.f)
        [
            SNew(SBorder)
            .BorderImage(&RoundedBgBrush)
            .BorderBackgroundColor(FLinearColor(0.15f, 0.15f, 0.15f, 0.3f)) // 深灰色，30% 透明度
            .Padding(FMargin(10.f, 5.f))
            .HAlign(HAlign_Center)
            .VAlign(VAlign_Center)
            [
                SNew(SVerticalBox)

                // ── 姓名 / ID ──
                + SVerticalBox::Slot()
                .AutoHeight()
                .HAlign(HAlign_Center)
                .Padding(0, 0, 0, 2)
                [
                    SAssignNew(NameSlate, STextBlock)
                    .Text(FText::FromString(TEXT("ID")))
                    .Font(FCoreStyle::GetDefaultFontStyle("Bold", 19))
                    .ColorAndOpacity(FSlateColor(FLinearColor::White))
                    .Justification(ETextJustify::Center)
                ]

                // ── 状态 ──
                + SVerticalBox::Slot()
                .AutoHeight()
                .HAlign(HAlign_Center)
                .Padding(0, 2, 0, 0)
                [
                    SAssignNew(StatusSlate, STextBlock)
                    .Text(FText::FromString(TEXT("Status")))
                    .Font(FCoreStyle::GetDefaultFontStyle("Bold", 16))
                    .ColorAndOpacity(FSlateColor(FLinearColor::White))
                    .Justification(ETextJustify::Center)
                ]
            ]
        ];
}

void UPCBWorkerInfoWidget::UpdateInfo(const FString& InName, const FString& InStatus, const FString& InStation)
{
    if (NameSlate.IsValid())
    {
        NameSlate->SetText(FText::FromString(InName));
    }

    if (StatusSlate.IsValid())
    {
        FString DisplayStatus;
        FLinearColor StatusColor;

        if (InStatus.Equals(TEXT("working"), ESearchCase::IgnoreCase))
        {
            DisplayStatus = TEXT("Working");
            StatusColor = FLinearColor::Black; // 工作状态改为黑色
        }
        else if (InStatus.Equals(TEXT("idle"), ESearchCase::IgnoreCase))
        {
            DisplayStatus = TEXT("Idle");                     
            StatusColor = FLinearColor(1.f, 1.f, 0.f, 1.f); // 纯黄
        }
        else
        {
            DisplayStatus = InStatus;
            StatusColor = FLinearColor(1.f, 1.f, 1.f, 1.f); // 纯白
        }

        StatusSlate->SetText(FText::FromString(DisplayStatus));
        StatusSlate->SetColorAndOpacity(FSlateColor(StatusColor));
    }
}
