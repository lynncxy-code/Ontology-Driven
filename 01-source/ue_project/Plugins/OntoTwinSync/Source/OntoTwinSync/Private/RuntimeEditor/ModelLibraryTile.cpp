#include "RuntimeEditor/ModelLibraryTile.h"
#include "Widgets/Layout/SBorder.h"

namespace
{
class SDraggableModel : public SBorder
{
public:
    TWeakObjectPtr<UModelLibraryTile> Tile;
    virtual FReply OnPreviewMouseButtonDown(const FGeometry&, const FPointerEvent& Mouse) override
    {
        if (Mouse.GetEffectingButton() == EKeys::LeftMouseButton && Tile.IsValid())
            return FReply::Handled().CaptureMouse(AsShared()).DetectDrag(AsShared(), EKeys::LeftMouseButton);
        return FReply::Unhandled();
    }
    virtual FReply OnMouseButtonUp(const FGeometry& Geo, const FPointerEvent& Mouse) override
    {
        if (!HasMouseCapture()) return FReply::Unhandled();
        if (Geo.IsUnderLocation(Mouse.GetScreenSpacePosition()) && Tile.IsValid())
            Tile->Select.ExecuteIfBound();
        return FReply::Handled().ReleaseMouseCapture();
    }
    virtual FReply OnDragDetected(const FGeometry&, const FPointerEvent&) override
    {
        if (Tile.IsValid()) Tile->Drag.ExecuteIfBound();
        return FReply::Handled().ReleaseMouseCapture();
    }
};
}
TSharedRef<SWidget> UModelLibraryTile::RebuildWidget()
{
    auto Wrapper = SNew(SDraggableModel).Padding(0).BorderImage(FCoreStyle::Get().GetBrush("NoBrush"))[Super::RebuildWidget()];
    Wrapper->Tile = this;
    return Wrapper;
}
