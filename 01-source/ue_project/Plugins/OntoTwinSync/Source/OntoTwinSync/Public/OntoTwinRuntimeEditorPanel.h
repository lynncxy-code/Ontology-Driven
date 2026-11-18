#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TimerManager.h"
#include "Types/SlateEnums.h"
#include "OntoTwinRuntimeEditorPanel.generated.h"

class ATwinSceneManager;
class SWidget;
class UButton;
class UBorder;
class UCheckBox;
class UComboBoxString;
class UEditableTextBox;
class USizeBox;
class UTextBlock;
class UVerticalBox;
class UWidget;
class UViewport;
class UHorizontalBox;
class UWrapBox;
class UCanvasPanel;
class UImage;
class AActor;

enum class EOntoTwinRuntimePanelConfirmation : uint8
{
    None,
    ExitEditor,
    CancelAll,
    DeleteObjects
};

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
    void ShowExitConfirmation();
    void ShowCancelAllConfirmation();
    bool IsPointerOverPanel() const;
    void EndLibraryPreview();
    void ShowPlacementDetails(const FString& Label, const TSharedPtr<FJsonObject>& Options, const FString& Error);
    void ClosePlacementDetails();
    void SetPlacementFeedback(const FString& Message);
    void ConfirmObjectDeletion(const FString& Message, FSimpleDelegate Accept);
    bool IsConfirmationOpen() const;

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
    virtual void NativeDestruct() override;
    virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

private:
    UPROPERTY()
    ATwinSceneManager* SceneManager = nullptr;

    UPROPERTY()
    UBorder* PanelBorder = nullptr;

    UPROPERTY()
    USizeBox* LibraryBounds = nullptr;
    UPROPERTY()
    UTextBlock* ModelLibraryStatus = nullptr;
    UPROPERTY(Transient) UWrapBox* LibraryGrid = nullptr;
    UPROPERTY(Transient) class UNativeWidgetHost* PlacementFormHost = nullptr;
    TSharedPtr<class SRuntimePlacementForm> PlacementForm;
    UPROPERTY(Transient) UEditableTextBox* LibrarySearch = nullptr;
    UPROPERTY(Transient) UImage* BlueprintImage = nullptr;
    UPROPERTY(Transient) UHorizontalBox* LocalActions = nullptr;
    UPROPERTY(Transient) UVerticalBox* ArtStudioPanel = nullptr;
    UPROPERTY(Transient) UTextBlock* ArtStudioAdminInfo = nullptr;
    TMap<FString, FString> ModelLabels, ModelErrors, ModelImages, ModelKinds;
    TArray<FString> OrderedModelKeys;
    TArray<FString> PendingLocalImages;
    float LibraryGridWidth = 404.f;
    UPROPERTY(Transient) TMap<FString, TObjectPtr<UTexture2D>> LibraryTextures;
    UPROPERTY(Transient) TMap<FString, TObjectPtr<UImage>> LibraryIcons;
    FString SelectedModelKey;
    void BuildModelLibrary(UCanvasPanel* Root);
    void RebuildLibraryGrid();
    void SelectLibraryKey(const FString& Key);
    UFUNCTION() void ToggleLibrary();
    UFUNCTION() void RefreshLibrary();
    UFUNCTION() void CollapseLibraryPreview();
    UFUNCTION() void OpenModelsFolder();
    UFUNCTION() void SearchLibrary(const FText& Query);
    enum class EModelSource : uint8 { Project, Local, ArtStudio };
    EModelSource ModelSource = EModelSource::Project;
    UPROPERTY(Transient) UViewport* ModelViewport = nullptr;
    UPROPERTY(Transient) USizeBox* ModelPreviewBox = nullptr;
    UPROPERTY(Transient) UTextBlock* ModelPreviewMessage = nullptr;
    UPROPERTY(Transient) UHorizontalBox* ModelControls = nullptr;
    UPROPERTY(Transient) UButton* PlaceModelButton = nullptr;
    UPROPERTY(Transient) TArray<TObjectPtr<UButton>> ModelSourceTabs;
    TWeakObjectPtr<AActor> LibraryPreviewActor;
    void ClearLibraryPreview();
    void PopulateModelLibrary(EModelSource Source);
    UFUNCTION() void ShowArtStudioModels();
    UFUNCTION() void OpenArtStudioAdmin();
    UFUNCTION() void ShowProjectModels();
    UFUNCTION() void ShowLocalModels();
    UFUNCTION() void PlaceSelectedModel();

    UPROPERTY()
    USizeBox* PanelBounds = nullptr;

    UPROPERTY()
    UTextBlock* HeaderStateText = nullptr;

    UPROPERTY()
    UTextBlock* DisplayNameText = nullptr;

    UPROPERTY()
    UButton* DisplayNameCopyButton = nullptr;

    UPROPERTY()
    UTextBlock* TypeNameText = nullptr;

    UPROPERTY()
    UButton* TypeNameCopyButton = nullptr;

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
    UTextBlock* YawLabelText = nullptr;

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
    UButton* UndoButton = nullptr;

    UPROPERTY()
    UButton* RedoButton = nullptr;

    UPROPERTY()
    UButton* SceneTabButton = nullptr;

    UPROPERTY()
    UButton* BusinessTabButton = nullptr;

    UPROPERTY()
    UTextBlock* SceneTabLabel = nullptr;

    UPROPERTY()
    UTextBlock* BusinessTabLabel = nullptr;

    UPROPERTY()
    UVerticalBox* SceneContent = nullptr;

    UPROPERTY()
    UVerticalBox* BusinessContent = nullptr;

    UPROPERTY()
    UTextBlock* BusinessSelectionText = nullptr;

    UPROPERTY()
    UComboBoxString* BusinessSelector = nullptr;

    // The combo menu owns only Slate rows; retain each generated UTextBlock
    // so its font/brush data remains valid across GC and window focus changes.
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTextBlock>> RetainedComboTextWidgets;

    UPROPERTY()
    UEditableTextBox* BusinessNameInput = nullptr;

    UPROPERTY()
    UButton* CreateBusinessButton = nullptr;

    UPROPERTY()
    UButton* RemoveButton = nullptr;
    UPROPERTY(Transient) UButton* DeleteObjectsButton = nullptr;
    UPROPERTY(Transient) UButton* EditIdentityButton = nullptr;
    UFUNCTION() void DeleteSelectedObjects();
    UFUNCTION() void EditSelectedIdentity();
    FSimpleDelegate PendingDeleteAction;

    UPROPERTY()
    UButton* PendingToggleButton = nullptr;

    UPROPERTY()
    UTextBlock* PendingToggleLabel = nullptr;

    UPROPERTY()
    UVerticalBox* PendingList = nullptr;

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

    UPROPERTY()
    UBorder* ConfirmationOverlay = nullptr;

    UPROPERTY()
    UTextBlock* ConfirmationTitleText = nullptr;

    UPROPERTY()
    UTextBlock* ConfirmationBodyText = nullptr;

    UPROPERTY()
    UButton* ConfirmationPrimaryButton = nullptr;

    UPROPERTY()
    UTextBlock* ConfirmationPrimaryLabel = nullptr;

    UPROPERTY()
    UButton* ConfirmationSecondaryButton = nullptr;

    UPROPERTY()
    UTextBlock* ConfirmationSecondaryLabel = nullptr;

    UPROPERTY()
    UButton* ConfirmationContinueButton = nullptr;

    UTextBlock* ConfirmationContinueLabel = nullptr;

    FTimerHandle ToastTimerHandle;
    EOntoTwinRuntimePanelConfirmation ConfirmationMode = EOntoTwinRuntimePanelConfirmation::None;
    bool bPendingListExpanded = false;
    bool bBusinessTabActive = false;
    bool bRefreshingBusinessSelector = false;
    FString BusinessOptionsSignature;
    TArray<FString> BusinessOptionIds;
    TArray<FString> BusinessOptionLabels;
    TArray<FString> BusinessOptionDisplayLabels;

    void BuildDefaultLayout();
    UTextBlock* CreateText(const FName Name, const FString& InitialText, int32 FontSize,
        const FLinearColor& Color, bool bBold = false) const;
    UButton* CreateButton(const FName Name, const FString& Label, UTextBlock*& OutLabel,
        bool bPrimary) const;
    void HideToast();
    void HideConfirmation();
    void RefreshPendingList();
    void SetActiveTab(bool bBusiness);
    void RefreshModelSourceTabs();
    void RefreshBusinessEditor();

    UFUNCTION()
    void HandleAccessActionClicked();

    UFUNCTION()
    void HandleDisplayNameCopyClicked();

    UFUNCTION()
    void HandleTypeNameCopyClicked();

    UFUNCTION()
    void HandleCloseClicked();

    UFUNCTION()
    void HandleSaveClicked();

    UFUNCTION()
    void HandleCancelClicked();

    UFUNCTION()
    void HandleUndoClicked();

    UFUNCTION()
    void HandleRedoClicked();

    UFUNCTION()
    void HandleSceneTabClicked();

    UFUNCTION()
    void HandleBusinessTabClicked();

    UFUNCTION()
    void HandleBusinessSelected(FString SelectedItem, ESelectInfo::Type SelectionType);

    UFUNCTION()
    UWidget* GenerateSelectorOptionWidget(FString Item);

    UFUNCTION()
    void HandleCreateBusinessClicked();

    UFUNCTION()
    void HandleRemoveClicked();

    UFUNCTION()
    void HandlePendingToggleClicked();

    UFUNCTION()
    void HandleConfirmationPrimaryClicked();

    UFUNCTION()
    void HandleConfirmationSecondaryClicked();

    UFUNCTION()
    void HandleConfirmationContinueClicked();

    UFUNCTION()
    void HandleWallSnapChanged(bool bIsChecked);

    UFUNCTION()
    void HandleGridSnapChanged(bool bIsChecked);
};
