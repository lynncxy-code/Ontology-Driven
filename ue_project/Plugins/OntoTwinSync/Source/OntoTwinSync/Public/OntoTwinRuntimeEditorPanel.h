#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "OntoTwinRuntimeEditorPanel.generated.h"

class ATwinSceneManager;
class SWidget;
class UButton;
class UCheckBox;
class UTextBlock;

UCLASS()
class ONTOTWINSYNC_API UOntoTwinRuntimeEditorPanel : public UUserWidget
{
    GENERATED_BODY()

public:
    void SetSceneManager(ATwinSceneManager* InSceneManager);
    void RefreshFromManager();

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;

private:
    UPROPERTY()
    ATwinSceneManager* SceneManager = nullptr;

    UPROPERTY()
    UTextBlock* ModeText = nullptr;

    UPROPERTY()
    UTextBlock* BindingText = nullptr;

    UPROPERTY()
    UTextBlock* SelectionText = nullptr;

    UPROPERTY()
    UTextBlock* TransformText = nullptr;

    UPROPERTY()
    UTextBlock* StatusText = nullptr;

    UPROPERTY()
    UButton* BindButton = nullptr;

    UPROPERTY()
    UButton* SaveButton = nullptr;

    UPROPERTY()
    UButton* CancelButton = nullptr;

    UPROPERTY()
    UCheckBox* WallSnapCheckBox = nullptr;

    UPROPERTY()
    UCheckBox* GridSnapCheckBox = nullptr;

    void BuildDefaultLayout();
    UTextBlock* AddTextLine(class UVerticalBox* Parent, const FName Name, const FString& InitialText) const;
    UButton* AddButton(class UHorizontalBox* Parent, const FName Name, const FString& Label) const;

    UFUNCTION()
    void HandleBindClicked();

    UFUNCTION()
    void HandleSaveClicked();

    UFUNCTION()
    void HandleCancelClicked();

    UFUNCTION()
    void HandleWallSnapChanged(bool bIsChecked);

    UFUNCTION()
    void HandleGridSnapChanged(bool bIsChecked);
};
