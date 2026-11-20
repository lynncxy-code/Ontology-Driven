#include "RuntimeEditor/OntoTwinNumericTransform.h"
#include "UI/OntoTwinGlassTheme.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "TwinSceneManager.h"
#include "OntoTwinRuntimeEditorPanel.h"
#include "TwinInstance.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SNumericEntryBox.h"
#include "Widgets/Layout/SExpandableArea.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

using EField = ATwinSceneManager::ENumericField;
TOptional<double> ATwinSceneManager::GetNumericTransform(EField Field) const
{
    if (!IsValid(RuntimeSelectedInstance)) return {};
    const FVector Loc = RuntimeSelectedInstance->GetActorLocation();
    const FVector Scale = RuntimeSelectedInstance->GetActorScale3D();
    const FRotator Rot = RuntimeSelectedInstance->GetActorRotation();
    const bool Multi = IsRuntimeSelectionMultiple();
    switch (Field) {
    case EField::X: return Multi ? 0.0 : Loc.X;
    case EField::Y: return Multi ? 0.0 : Loc.Y;
    case EField::Z: return Multi ? 0.0 : Loc.Z;
    case EField::Yaw: return Multi ? 0.0 : Rot.Yaw;
    case EField::Pitch: return Multi ? 0.0 : Rot.Pitch;
    case EField::Roll: return Multi ? 0.0 : Rot.Roll;
    case EField::ScaleX: return Multi ? 1.0 : Scale.X;
    case EField::ScaleY: return Multi ? 1.0 : Scale.Y;
    case EField::ScaleZ: return Multi ? 1.0 : Scale.Z;
    case EField::Uniform:
        if (Multi) return 1.0;
        if (FMath::IsNearlyEqual(Scale.X, Scale.Y) && FMath::IsNearlyEqual(Scale.X, Scale.Z)) return Scale.X;
        return {};
    default: return {};
    }
}
void ATwinSceneManager::SetNumericTransform(EField Field, double Value)
{
    if (!bRuntimeEditMode || bRuntimeEditSaving || bRuntimeDragging || !HasRuntimeEditSelection() || !FMath::IsFinite(Value)) return;
    if (!CanStageRuntimeSelection()) {RuntimeStatusMessage = TEXT("待保存对象已达上限"); return;}
    const bool IsScale = Field == EField::Uniform || Field == EField::ScaleX || Field == EField::ScaleY || Field == EField::ScaleZ;
    if (IsScale && Value <= 0) { RuntimeStatusMessage = TEXT("缩放必须大于零"); return; }
    const bool Multi = IsRuntimeSelectionMultiple();
    FRuntimeEditCommand Command;
    Command.Label = TEXT("输入变换数值");
    for (ATwinInstance* Actor : RuntimeSelectedInstances) {
        if (!IsValid(Actor)) continue;
        const auto Before = CaptureRuntimeValue(Actor);
        FTransform T = Actor->GetActorTransform();
        FVector Loc = T.GetLocation(), S = T.GetScale3D();
        FRotator R = T.Rotator();
        auto Apply = [Multi,Value](double& V){ V = Multi ? V + Value : Value; };
        auto Scale = [Multi,Value](double& V){ V = Multi ? V * Value : Value; };
        switch (Field) {
        case EField::X: Apply(Loc.X); break;
        case EField::Y: Apply(Loc.Y); break;
        case EField::Z: Apply(Loc.Z); break;
        case EField::Yaw: Apply(R.Yaw); break;
        case EField::Pitch: Apply(R.Pitch); break;
        case EField::Roll: Apply(R.Roll); break;
        case EField::Uniform: Scale(S.X); Scale(S.Y); Scale(S.Z); break;
        case EField::ScaleX: Scale(S.X); break;
        case EField::ScaleY: Scale(S.Y); break;
        case EField::ScaleZ: Scale(S.Z); break;
        case EField::ResetScale: S = FVector::OneVector; break;
        case EField::Level: R.Pitch = R.Roll = 0.0; break;
        }
        T = FTransform(R, Loc, S);
        if (T.Equals(Before.Transform, 0.00001)) continue;
        Actor->SetActorTransform(T, false, nullptr, ETeleportType::TeleportPhysics);
        Command.Before.Add(Before);
        Command.After.Add(CaptureRuntimeValue(Actor));
    }
    if (Field == EField::Level && RuntimeEditorPanel)
        RuntimeEditorPanel->ShowToast(Command.Before.IsEmpty() ? TEXT("所选设备已是直立状态") : TEXT("已摆正，保留水平朝向"),
                                     EOntoTwinRuntimeToastType::Info);
    if (!Command.Before.IsEmpty()) {
        RecordRuntimeCommand(MoveTemp(Command));
        RefreshRuntimeEditDirtyState();
        UpdateRuntimeSelectionGeometry();
    }
}

TSharedRef<SWidget> MakeNumericTransformPanel(TFunction<ATwinSceneManager*()> Get)
{
    const auto Font = FOntoTwinGlassTheme::Font(11.f);
    auto Number = [Get, Font](EField Field, const TCHAR* Hint) {
        return SNew(SNumericEntryBox<double>)
            .Font(Font).AllowSpin(false).MinDesiredValueWidth(44)
            .ToolTipText(FText::FromString(Hint))
            .UndeterminedString(FText::FromString(TEXT("—")))
            .Value_Lambda([Get, Field] {
                auto* Manager = Get();
                return Manager ? Manager->GetNumericTransform(Field) : TOptional<double>();
            })
            .OnValueCommitted_Lambda([Get, Field](double Value, ETextCommit::Type Commit) {
                if (auto* Manager = Get(); Manager && Commit != ETextCommit::OnCleared)
                    Manager->SetNumericTransform(Field, Value);
            });
    };
    const auto Grid = SNew(SGridPanel);
    const TCHAR* AxisNames[] = {TEXT("X"), TEXT("Y"), TEXT("Z")};
    const FLinearColor AxisColors[] = {{0.98f, 0.54f, 0.50f}, {0.55f, 0.84f, 0.62f}, {0.51f, 0.72f, 1.f}};
    const TCHAR* RowNames[] = {TEXT("位移 cm"), TEXT("旋转 °"), TEXT("缩放 ×")};
    const EField Fields[][3] = {
        {EField::X, EField::Y, EField::Z},
        {EField::Roll, EField::Pitch, EField::Yaw},
        {EField::ScaleX, EField::ScaleY, EField::ScaleZ}
    };
    const TCHAR* Hints[][3] = {
        {TEXT("沿 X 轴移动"), TEXT("沿 Y 轴移动"), TEXT("沿 Z 轴移动")},
        {TEXT("绕 X 轴侧倾"), TEXT("绕 Y 轴抬头或低头"), TEXT("绕 Z 轴调整水平朝向")},
        {TEXT("沿 X 轴缩放"), TEXT("沿 Y 轴缩放"), TEXT("沿 Z 轴缩放")}
    };
    for (int32 Axis = 0; Axis < 3; ++Axis) {
        Grid->SetColumnFill(Axis + 1, 1.f);
        Grid->AddSlot(Axis + 1, 0).HAlign(HAlign_Center).Padding(2)
            [SNew(STextBlock).Font(Font).ColorAndOpacity(AxisColors[Axis]).Text(FText::FromString(AxisNames[Axis]))];
    }
    for (int32 Row = 0; Row < 3; ++Row) {
        Grid->AddSlot(0, Row + 1).VAlign(VAlign_Center).Padding(0, 0, 6, 0)
            [SNew(STextBlock).Font(Font).Text(FText::FromString(RowNames[Row]))];
        for (int32 Axis = 0; Axis < 3; ++Axis)
            Grid->AddSlot(Axis + 1, Row + 1).Padding(2, 3)[Number(Fields[Row][Axis], Hints[Row][Axis])];
    }
    auto Action = [Get](const TCHAR* Label, EField Field) {
        return SNew(SButton).Text(FText::FromString(Label)).OnClicked_Lambda([Get, Field] {
            if (auto* Manager = Get()) Manager->SetNumericTransform(Field, 1);
            return FReply::Handled();
        });
    };
    static const FSlateRoundedBoxBrush TransformSurface(FLinearColor(.042f,.047f,.055f,.92f), 6.f);
    return SNew(SExpandableArea).InitiallyCollapsed(true)
        .BorderImage(&TransformSurface).BodyBorderImage(&TransformSurface)
        .AreaTitle(FText::FromString(TEXT("位置、旋转与缩放"))).AreaTitleFont(FOntoTwinGlassTheme::Font(12.f, true))
        .HeaderPadding(FMargin(10, 8)).Padding(FMargin(10, 2, 10, 8))
        .BodyContent()
        [SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().Padding(0, 3)
              [SNew(STextBlock).Font(Font).Text_Lambda([Get] {
                  auto* Manager = Get();
                  if (!Manager || !Manager->HasRuntimeEditSelection()) return FText::FromString(TEXT("先在场景里选择设备"));
                  if (Manager->IsRuntimeSelectionMultiple()) return FText::FromString(TEXT("多选 · 位移和旋转输入增量，缩放输入倍数"));
                  return FText::GetEmpty();
              }).Visibility_Lambda([Get] {
                  auto* Manager = Get();
                  return Manager && Manager->HasRuntimeEditSelection() && !Manager->IsRuntimeSelectionMultiple()
                      ? EVisibility::Collapsed : EVisibility::Visible;
              })]
            + SVerticalBox::Slot().AutoHeight()
              [SNew(SVerticalBox).IsEnabled_Lambda([Get] {
                  auto* Manager = Get();
                  return Manager && Manager->HasRuntimeEditSelection() && !Manager->IsRuntimeEditSaving();
              })
                + SVerticalBox::Slot().AutoHeight()[Grid]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
                  [SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
                      [SNew(STextBlock).Font(Font).Text(FText::FromString(TEXT("统一缩放")))]
                    + SHorizontalBox::Slot().FillWidth(1).Padding(4, 0)[Number(EField::Uniform, TEXT("同时调整三轴"))]
                    + SHorizontalBox::Slot().AutoWidth()[Action(TEXT("重置缩放"), EField::ResetScale)]
                    + SHorizontalBox::Slot().AutoWidth().Padding(4, 0, 0, 0)[Action(TEXT("摆正"), EField::Level)]]]];
}
