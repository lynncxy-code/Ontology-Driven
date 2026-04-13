// ============================================================================
// PCBWorkerInfoWidget.h
//
// 工人头顶悬浮信息 UI — 纯 Slate 构建，100% C++ 无需任何蓝图资产
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Widgets/Text/STextBlock.h"
#include "PCBWorkerInfoWidget.generated.h"

UCLASS()
class TEST0316_API UPCBWorkerInfoWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    /** 更新显示内容 */
    void UpdateInfo(const FString& InName, const FString& InStatus, const FString& InStation);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;

private:
    TSharedPtr<STextBlock> NameSlate;
    TSharedPtr<STextBlock> StatusSlate;
    TSharedPtr<STextBlock> StationSlate;
};
