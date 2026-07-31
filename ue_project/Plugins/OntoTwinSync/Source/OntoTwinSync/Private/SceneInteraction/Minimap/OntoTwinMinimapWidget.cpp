#include "SceneInteraction/Minimap/OntoTwinMinimapWidget.h"
#include "UI/OntoTwinGlassRenderer.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Rendering/DrawElementTypes.h"
#include "Styling/CoreStyle.h"

namespace
{
constexpr float ShellPadding = 8.0f;
constexpr float ShellCornerRadius = 20.0f;
constexpr float MapCornerRadius = ShellCornerRadius - ShellPadding;
constexpr float DefaultContentWidth = 320.0f;
constexpr float CollapsedSize = 52.0f;
constexpr float ToggleSize = 44.0f;
constexpr float ExpandDuration = 0.22f;
const FLinearColor ShellFill(0.04f, 0.045f, 0.055f, 0.82f);
const FLinearColor ShellStroke(0.92f, 0.92f, 0.92f, 0.28f);
const FLinearColor MarkerOutline(0.16f, 0.01f, 0.01f, 0.46f);
const FLinearColor MarkerRed(1.0f, 0.035f, 0.025f, 0.70f);
const FLinearColor ToggleFill(0.035f, 0.04f, 0.05f, 0.90f);
const FLinearColor ToggleHover(0.12f, 0.13f, 0.15f, 0.94f);
const FLinearColor TogglePressed(0.19f, 0.20f, 0.22f, 0.96f);
const FLinearColor ToggleStroke(0.92f, 0.92f, 0.92f, 0.32f);
const FLinearColor ToggleIcon(0.96f, 0.96f, 0.96f, 0.94f);
}

TSharedRef<SWidget> UOntoTwinMinimapWidget::RebuildWidget()
{
    if (!WidgetTree)
    {
        WidgetTree = NewObject<UWidgetTree>(this, TEXT("MinimapWidgetTree"), RF_Transient);
    }
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        BuildDefaultLayout();
    }
    TSharedRef<SWidget> Result = Super::RebuildWidget();
    ApplyMapTexture();
    ApplyExpansionVisuals();
    return Result;
}

void UOntoTwinMinimapWidget::NativeTick(
    const FGeometry& MyGeometry,
    float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);

    bool bNeedsPaint = false;
    const bool bReduceMotion = FOntoTwinGlassRenderer::ShouldReduceMotion();
    if (bMarkerVisible && MapTexture && !bReduceMotion)
    {
        MarkerPulsePhase = FMath::Fmod(
            MarkerPulsePhase + InDeltaTime * (2.0f * PI / 1.25f),
            2.0f * PI);
        bNeedsPaint = true;
    }

    const float TargetAlpha = bExpanded ? 1.0f : 0.0f;
    if (!FMath::IsNearlyEqual(ExpandAlpha, TargetAlpha, KINDA_SMALL_NUMBER))
    {
        ExpandAlpha = bReduceMotion
            ? TargetAlpha
            : FMath::FInterpConstantTo(
                ExpandAlpha,
                TargetAlpha,
                InDeltaTime,
                1.0f / ExpandDuration);
        ApplyExpansionVisuals();
        bNeedsPaint = true;
    }

    if (bNeedsPaint) InvalidateLayoutAndVolatility();
}

void UOntoTwinMinimapWidget::BuildDefaultLayout()
{
    RootBounds = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("MinimapBounds"));
    RootBounds->SetWidthOverride(ContentSize.X + ShellPadding * 2.0f);
    RootBounds->SetHeightOverride(ContentSize.Y + ShellPadding * 2.0f);
    RootBounds->SetClipping(EWidgetClipping::ClipToBoundsAlways);
    RootBounds->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    WidgetTree->RootWidget = RootBounds;

    UOverlay* RootOverlay = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("MinimapRootOverlay"));
    RootOverlay->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    RootBounds->AddChild(RootOverlay);

    MapShell = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("MinimapShell"));
    MapShell->SetPadding(FMargin(ShellPadding));
    MapShell->SetBrush(FSlateRoundedBoxBrush(
        ShellFill, ShellCornerRadius, ShellStroke, 1.0f));
    MapShell->SetRenderTransformPivot(FVector2D(1.0f, 0.0f));
    MapShell->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UOverlaySlot* ShellSlot = RootOverlay->AddChildToOverlay(MapShell);
    ShellSlot->SetHorizontalAlignment(HAlign_Fill);
    ShellSlot->SetVerticalAlignment(VAlign_Fill);

    UOverlay* Content = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("MinimapContent"));
    Content->SetClipping(EWidgetClipping::ClipToBounds);
    Content->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    MapShell->SetContent(Content);

    MapImage = WidgetTree->ConstructWidget<UImage>(
        UImage::StaticClass(), TEXT("MinimapImage"));
    MapImage->SetDesiredSizeOverride(ContentSize);
    MapImage->SetColorAndOpacity(FLinearColor::White);
    MapImage->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    UOverlaySlot* MapSlot = Content->AddChildToOverlay(MapImage);
    MapSlot->SetHorizontalAlignment(HAlign_Fill);
    MapSlot->SetVerticalAlignment(VAlign_Fill);

    ToggleButton = WidgetTree->ConstructWidget<UButton>(
        UButton::StaticClass(), TEXT("MinimapToggleButton"));
    FButtonStyle ToggleStyle;
    ToggleStyle.SetNormal(FSlateRoundedBoxBrush(
        ToggleFill, 14.0f, ToggleStroke, 1.0f));
    ToggleStyle.SetHovered(FSlateRoundedBoxBrush(
        ToggleHover, 14.0f, ToggleStroke, 1.0f));
    ToggleStyle.SetPressed(FSlateRoundedBoxBrush(
        TogglePressed, 14.0f, ToggleStroke, 1.0f));
    ToggleButton->SetStyle(ToggleStyle);
    ToggleButton->SetToolTipText(FText::FromString(TEXT("收起小地图")));
    ToggleButton->OnClicked.AddDynamic(
        this, &UOntoTwinMinimapWidget::OnToggleExpanded);
    USizeBox* ToggleBounds = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("MinimapToggleBounds"));
    ToggleBounds->SetWidthOverride(ToggleSize);
    ToggleBounds->SetHeightOverride(ToggleSize);
    ToggleButton->SetContent(ToggleBounds);
    if (UButtonSlot* ToggleContentSlot = Cast<UButtonSlot>(ToggleBounds->Slot))
    {
        ToggleContentSlot->SetPadding(FMargin(0.0f));
    }
    UOverlaySlot* ToggleSlot = RootOverlay->AddChildToOverlay(ToggleButton);
    ToggleSlot->SetHorizontalAlignment(HAlign_Right);
    ToggleSlot->SetVerticalAlignment(VAlign_Top);
    ToggleSlot->SetPadding(FMargin(4.0f));

    SetVisibility(MapTexture
        ? ESlateVisibility::SelfHitTestInvisible
        : ESlateVisibility::Collapsed);
}

void UOntoTwinMinimapWidget::SetMapTexture(
    UTextureRenderTarget2D* InTexture,
    const FIntPoint& InCaptureSize)
{
    MapTexture = InTexture;
    const float Aspect = InCaptureSize.Y > 0
        ? static_cast<float>(InCaptureSize.X) / static_cast<float>(InCaptureSize.Y)
        : (4.0f / 3.0f);
    ContentSize.X = DefaultContentWidth;
    ContentSize.Y = FMath::Clamp(DefaultContentWidth / FMath::Max(Aspect, 0.1f), 180.0f, 240.0f);
    if (RootBounds)
    {
        RootBounds->SetWidthOverride(ContentSize.X + ShellPadding * 2.0f);
        RootBounds->SetHeightOverride(ContentSize.Y + ShellPadding * 2.0f);
    }
    if (MapImage) MapImage->SetDesiredSizeOverride(ContentSize);
    ApplyMapTexture();
    ApplyExpansionVisuals();
    SetVisibility(MapTexture
        ? ESlateVisibility::SelfHitTestInvisible
        : ESlateVisibility::Collapsed);
}

void UOntoTwinMinimapWidget::ApplyMapTexture()
{
    if (!MapImage) return;
    FSlateRoundedBoxBrush MapBrush(FLinearColor::White, MapCornerRadius);
    MapBrush.ImageType = ESlateBrushImageType::FullColor;
    MapBrush.SetResourceObject(MapTexture);
    MapImage->SetBrush(MapBrush);
}

void UOntoTwinMinimapWidget::ApplyExpansionVisuals()
{
    const float SmoothAlpha = ExpandAlpha * ExpandAlpha * (3.0f - 2.0f * ExpandAlpha);
    const FVector2D FullSize(
        ContentSize.X + ShellPadding * 2.0f,
        ContentSize.Y + ShellPadding * 2.0f);
    if (RootBounds)
    {
        RootBounds->SetWidthOverride(FMath::Lerp(CollapsedSize, FullSize.X, SmoothAlpha));
        RootBounds->SetHeightOverride(FMath::Lerp(CollapsedSize, FullSize.Y, SmoothAlpha));
    }
    if (MapShell)
    {
        if (ExpandAlpha > KINDA_SMALL_NUMBER)
        {
            MapShell->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
        }
        else if (!bExpanded)
        {
            MapShell->SetVisibility(ESlateVisibility::Collapsed);
        }
        MapShell->SetRenderOpacity(FMath::Clamp(
            (SmoothAlpha - 0.08f) / 0.92f, 0.0f, 1.0f));
        const float Scale = FMath::Lerp(0.94f, 1.0f, SmoothAlpha);
        MapShell->SetRenderScale(FVector2D(Scale, Scale));
    }
}

void UOntoTwinMinimapWidget::OnToggleExpanded()
{
    bExpanded = !bExpanded;
    if (bExpanded && MapShell)
    {
        MapShell->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
    }
    if (ToggleButton)
    {
        ToggleButton->SetToolTipText(FText::FromString(
            bExpanded ? TEXT("收起小地图") : TEXT("展开小地图")));
    }
    InvalidateLayoutAndVolatility();
}

void UOntoTwinMinimapWidget::SetMarker(
    const FVector2D& InUV,
    float InAngleDegrees,
    bool bInOffMap)
{
    MarkerUV.X = FMath::Clamp(InUV.X, 0.0f, 1.0f);
    MarkerUV.Y = FMath::Clamp(InUV.Y, 0.0f, 1.0f);
    MarkerAngleDegrees = InAngleDegrees;
    bMarkerOffMap = bInOffMap;
    bMarkerVisible = MapTexture != nullptr;
    InvalidateLayoutAndVolatility();
}

void UOntoTwinMinimapWidget::HideMarker()
{
    bMarkerVisible = false;
    InvalidateLayoutAndVolatility();
}

void UOntoTwinMinimapWidget::ClearMap()
{
    MapTexture = nullptr;
    bMarkerVisible = false;
    bMarkerOffMap = false;
    ApplyMapTexture();
    SetVisibility(ESlateVisibility::Collapsed);
}

int32 UOntoTwinMinimapWidget::NativePaint(
    const FPaintArgs& Args,
    const FGeometry& AllottedGeometry,
    const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements,
    int32 LayerId,
    const FWidgetStyle& InWidgetStyle,
    bool bParentEnabled) const
{
    const int32 BaseLayer = Super::NativePaint(
        Args,
        AllottedGeometry,
        MyCullingRect,
        OutDrawElements,
        LayerId,
        InWidgetStyle,
        bParentEnabled);
    int32 PaintedLayer = BaseLayer;

    if (bMarkerVisible && MapTexture && ExpandAlpha > 0.12f)
    {
        const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
        const FVector2D MapSize(
            FMath::Max(1.0f, LocalSize.X - ShellPadding * 2.0f),
            FMath::Max(1.0f, LocalSize.Y - ShellPadding * 2.0f));
        const FVector2D Center(
            ShellPadding + MarkerUV.X * MapSize.X,
            ShellPadding + MarkerUV.Y * MapSize.Y);
        const float AngleRadians = FMath::DegreesToRadians(MarkerAngleDegrees);
        const FVector2D Direction(FMath::Cos(AngleRadians), FMath::Sin(AngleRadians));
        const FVector2D Perpendicular(-Direction.Y, Direction.X);
        const float Pulse = FOntoTwinGlassRenderer::ShouldReduceMotion()
            ? 1.0f
            : 0.5f + 0.5f * FMath::Sin(MarkerPulsePhase);
        const float PulseScale = FMath::Lerp(0.92f, 1.10f, Pulse);
        const float TipDistance = (bMarkerOffMap ? 11.0f : 10.0f) * PulseScale;
        const float BackDistance = (bMarkerOffMap ? 8.0f : 7.0f) * PulseScale;
        const float HalfWidth = (bMarkerOffMap ? 7.0f : 6.0f) * PulseScale;
        const FVector2D Tip = Center + Direction * TipDistance;
        const FVector2D Back = Center - Direction * BackDistance;

        FLinearColor PulsedRed = MarkerRed;
        PulsedRed.A *= FMath::Lerp(0.52f, 1.0f, Pulse);

        const FSlateRenderTransform& AccumulatedRenderTransform =
            AllottedGeometry.GetAccumulatedRenderTransform();
        const FVector2f TextureCoordinate(0.0f, 0.0f);
        const FSlateResourceHandle WhiteResource =
            FCoreStyle::Get().GetBrush(TEXT("GenericWhiteBox"))->GetRenderingResource();
        const TArray<SlateIndex> TriangleIndices = {0, 1, 2};
        const auto DrawFilledTriangle = [&OutDrawElements, &AccumulatedRenderTransform,
            &TextureCoordinate, &WhiteResource, &TriangleIndices](
                int32 DrawLayer,
                const FVector2D& DrawTip,
                const FVector2D& DrawLeft,
                const FVector2D& DrawRight,
                const FLinearColor& DrawColor)
        {
            const FColor VertexColor = DrawColor.ToFColor(true);
            const TArray<FSlateVertex> Vertices = {
                FSlateVertex::Make<ESlateVertexRounding::Disabled>(
                    AccumulatedRenderTransform, FVector2f(DrawTip), TextureCoordinate, VertexColor),
                FSlateVertex::Make<ESlateVertexRounding::Disabled>(
                    AccumulatedRenderTransform, FVector2f(DrawLeft), TextureCoordinate, VertexColor),
                FSlateVertex::Make<ESlateVertexRounding::Disabled>(
                    AccumulatedRenderTransform, FVector2f(DrawRight), TextureCoordinate, VertexColor),
            };
            FSlateDrawElement::MakeCustomVerts(
                OutDrawElements,
                DrawLayer,
                WhiteResource,
                Vertices,
                TriangleIndices,
                nullptr,
                0,
                0);
        };

        const float OutlineScale = 1.14f;
        const FVector2D OutlineTip = Center + Direction * TipDistance * OutlineScale;
        const FVector2D OutlineBack = Center - Direction * BackDistance * OutlineScale;
        DrawFilledTriangle(
            BaseLayer + 1,
            OutlineTip,
            OutlineBack + Perpendicular * HalfWidth * OutlineScale,
            OutlineBack - Perpendicular * HalfWidth * OutlineScale,
            MarkerOutline);
        DrawFilledTriangle(
            BaseLayer + 2,
            Tip,
            Back + Perpendicular * HalfWidth,
            Back - Perpendicular * HalfWidth,
            PulsedRed);

        if (bMarkerOffMap)
        {
            TArray<FVector2f> EdgeBar;
            EdgeBar.Add(FVector2f(Back + Perpendicular * (HalfWidth + 2.0f)));
            EdgeBar.Add(FVector2f(Back - Perpendicular * (HalfWidth + 2.0f)));
            FSlateDrawElement::MakeLines(
                OutDrawElements,
                BaseLayer + 2,
                AllottedGeometry.ToPaintGeometry(),
                EdgeBar,
                ESlateDrawEffect::None,
                PulsedRed,
                true,
                2.8f);
        }
        PaintedLayer = BaseLayer + 2;
    }

    if (MapTexture && ToggleButton)
    {
        const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
        const FVector2D Center(LocalSize.X - 26.0f, 26.0f);
        const float HalfWidth = 9.0f;
        const float HalfHeight = 8.0f;
        TArray<FVector2f> MapGlyph;
        MapGlyph.Reserve(9);
        MapGlyph.Add(FVector2f(Center + FVector2D(-HalfWidth, -HalfHeight + 2.0f)));
        MapGlyph.Add(FVector2f(Center + FVector2D(-3.0f, -HalfHeight)));
        MapGlyph.Add(FVector2f(Center + FVector2D(3.0f, -HalfHeight + 2.0f)));
        MapGlyph.Add(FVector2f(Center + FVector2D(HalfWidth, -HalfHeight)));
        MapGlyph.Add(FVector2f(Center + FVector2D(HalfWidth, HalfHeight - 2.0f)));
        MapGlyph.Add(FVector2f(Center + FVector2D(3.0f, HalfHeight)));
        MapGlyph.Add(FVector2f(Center + FVector2D(-3.0f, HalfHeight - 2.0f)));
        MapGlyph.Add(FVector2f(Center + FVector2D(-HalfWidth, HalfHeight)));
        MapGlyph.Add(FVector2f(Center + FVector2D(-HalfWidth, -HalfHeight + 2.0f)));
        const int32 IconLayer = FMath::Max(PaintedLayer + 1, BaseLayer + 3);
        FSlateDrawElement::MakeLines(
            OutDrawElements,
            IconLayer,
            AllottedGeometry.ToPaintGeometry(),
            MapGlyph,
            ESlateDrawEffect::None,
            ToggleIcon,
            true,
            1.6f);

        TArray<FVector2f> LeftFold;
        LeftFold.Add(FVector2f(Center + FVector2D(-3.0f, -HalfHeight)));
        LeftFold.Add(FVector2f(Center + FVector2D(-3.0f, HalfHeight - 2.0f)));
        FSlateDrawElement::MakeLines(
            OutDrawElements,
            IconLayer,
            AllottedGeometry.ToPaintGeometry(),
            LeftFold,
            ESlateDrawEffect::None,
            ToggleIcon,
            true,
            1.2f);
        TArray<FVector2f> RightFold;
        RightFold.Add(FVector2f(Center + FVector2D(3.0f, -HalfHeight + 2.0f)));
        RightFold.Add(FVector2f(Center + FVector2D(3.0f, HalfHeight)));
        FSlateDrawElement::MakeLines(
            OutDrawElements,
            IconLayer,
            AllottedGeometry.ToPaintGeometry(),
            RightFold,
            ESlateDrawEffect::None,
            ToggleIcon,
            true,
            1.2f);
        PaintedLayer = IconLayer;
    }
    return PaintedLayer;
}
