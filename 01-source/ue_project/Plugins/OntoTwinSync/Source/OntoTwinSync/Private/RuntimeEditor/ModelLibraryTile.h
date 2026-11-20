#pragma once
#include "Components/Button.h"
#include "ModelLibraryTile.generated.h"

UCLASS()
class UModelLibraryTile : public UButton
{
    GENERATED_BODY()
public:
    FSimpleDelegate Select;
    FSimpleDelegate Drag;
    virtual TSharedRef<SWidget> RebuildWidget() override;
    void InitializeTile() { OnClicked.AddDynamic(this, &UModelLibraryTile::SelectTile); }
private:
    UFUNCTION() void SelectTile() { Select.ExecuteIfBound(); }
};
