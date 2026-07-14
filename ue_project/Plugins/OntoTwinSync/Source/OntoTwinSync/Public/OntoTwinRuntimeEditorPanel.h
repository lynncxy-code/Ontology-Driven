#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TimerManager.h"
#include "OntoTwinRuntimeEditorPanel.generated.h"

class ATwinSceneManager;
class SWidget;
class UButton;
class UBorder;
class UCheckBox;
class UTextBlock;

enum class EOntoTwinRuntimeToastType : uint8
{
    Info,
    Success,
    Warning,
    Error
};

UCLASS()
class ONTOTWINSYNC_API UOntoTwinRuntimeEditorPanel : public UUserWidget
{
    GENERATED_BODY()

public:
    void SetSceneManager(ATwinSceneManager* InSceneManager);
    void RefreshFromManager();
    void ShowToast(const FString& Message, EOntoTwinRuntimeToastType Type);
    bool IsPointerOverPanel() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;

private:
    UPROPERTY()
    ATwinSceneManager* SceneManager = nullptr;

    UPROPERTY()
    UBorder* PanelBorder = nullptr;

    UPROPERTY()
    UTextBlock* HeaderStateText = nullptr;

    UPROPERTY()
    UTextBlock* DisplayNameText = nullptr;

    UPROPERTY()
    UTextBlock* InstanceIdText = nullptr;

    UPROPERTY()
    UTextBlock* XValueText = nullptr;

    UPROPERTY()
    UTextBlock* YValueText = nullptr;

    UPROPERTY()
    UTextBlock* ZValueText = nullptr;

    UPROPERTY()
    UTextBlock* YawValueText = nullptr;

    UPROPERTY()
    UBorder* AccessStatusDot = nullptr;

    UPROPERTY()
    UTextBlock* AccessStatusText = nullptr;

    UPROPERTY()
    UButton* AccessActionButton = nullptr;

    UPROPERTY()
    UTextBlock* AccessActionLabel = nullptr;

    UPROPERTY()
    UButton* SaveButton = nullptr;

    UPROPERTY()
    UTextBlock* SaveButtonLabel = nullptr;

    UPROPERTY()
    UButton* CancelButton = nullptr;

    UPROPERTY()
    UButton* CloseButton = nullptr;

    UPROPERTY()
    UCheckBox* WallSnapCheckBox = nullptr;

    UPROPERTY()
    UCheckBox* GridSnapCheckBox = nullptr;

    UPROPERTY()
    UBorder* ToastBorder = nullptr;

    UPROPERTY()
    UBorder* ToastAccent = nullptr;

    UPROPERTY()
    UTextBlock* ToastText = nullptr;

    FTimerHandle ToastTimerHandle;

    void BuildDefaultLayout();
    UTextBlock* CreateText(const FName Name, const FString& InitialText, int32 FontSize,
        const FLinearColor& Color, bool bBold = false) const;
    UButton* CreateButton(const FName Name, const FString& Label, UTextBlock*& OutLabel,
        bool bPrimary) const;
    void HideToast();

    UFUNCTION()
    void HandleAccessActionClicked();

    UFUNCTION()
    void HandleCloseClicked();

    UFUNCTION()
    void HandleSaveClicked();

    UFUNCTION()
    void HandleCancelClicked();

    UFUNCTION()
    void HandleWallSnapChanged(bool bIsChecked);

    UFUNCTION()
    void HandleGridSnapChanged(bool bIsChecked);
};
