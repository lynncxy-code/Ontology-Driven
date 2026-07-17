#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Dom/JsonObject.h"
#include "Interfaces/IHttpRequest.h"
#include "InputCoreTypes.h"
#include "SceneInteraction/TwinRoamingTypes.h"
#include "TwinInteractionManagerComponent.generated.h"

class APlayerController;
class APawn;
class ATwinGodViewAnchor;
class ATwinInstance;
class ATwinRoamingCharacter;
class ATwinRoamingRoute;
class ATwinRoamingSpawnAnchor;
class ATwinSceneManager;
class UInputAction;
class UInputMappingContext;
class UOntoTwinRoamingHUDWidget;
struct FInputActionValue;

/**
 * Scene Interaction 的 UE 运行入口。
 * 负责运行投影轮询、绑定失败关闭、人物生命周期、输入仲裁、热更新与无位置心跳。
 */
UCLASS(ClassGroup=(OntoTwin), meta=(BlueprintSpawnableComponent))
class ONTOTWINSYNC_API UTwinInteractionManagerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTwinInteractionManagerComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Connection",
        meta=(ClampMin="0.25", ClampMax="10.0"))
    float RuntimePollInterval = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Runtime Route",
        meta=(ClampMin="10.0", ClampMax="1000.0"))
    float RuntimeRouteTraceUpCm = 150.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Runtime Route",
        meta=(ClampMin="10.0", ClampMax="5000.0"))
    float RuntimeRouteTraceDownCm = 300.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Runtime Route",
        meta=(ClampMin="0.0", ClampMax="1.0"))
    float RuntimeRouteMinGroundNormalZ = 0.65f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Connection",
        meta=(ClampMin="1", ClampMax="20"))
    int32 RuntimeOfflineThreshold = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Input")
    FKey ToggleRoamingKey = EKeys::F7;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Input")
    FKey ToggleViewKey = EKeys::V;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Input")
    FKey ToggleHudKey = EKeys::Tab;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Input")
    FKey InteractKey = EKeys::E;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|Input")
    FKey ResumeRouteKey = EKeys::R;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Scene Interaction|UI")
    TSubclassOf<UOntoTwinRoamingHUDWidget> RoamingHUDClass;

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ToggleRoaming();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ExitRoaming();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ToggleCameraMode();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ToggleHudInteraction();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void CycleSkin();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ResumeRoute();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void RestartRoute();

    UFUNCTION(BlueprintCallable, Category="Scene Interaction")
    void ApplyPendingReload();

    bool IsRoamingActive() const { return bRoamingActive; }
    bool IsHudInteractionOpen() const { return bHudInteraction; }
    bool HasPendingReload() const { return bPendingReload; }
    FString GetHudStatusText() const;
    FString GetHudHintText() const;
    FString GetHudDetailText() const;
    void NotifyRuntimeEditorBlocked();

private:
    UPROPERTY()
    ATwinSceneManager* SceneManager = nullptr;

    UPROPERTY()
    APlayerController* PlayerController = nullptr;

    UPROPERTY()
    APawn* OriginalPawn = nullptr;

    UPROPERTY()
    ATwinRoamingCharacter* RoamingCharacter = nullptr;

    UPROPERTY()
    ATwinRoamingRoute* ActiveRoute = nullptr;

    UPROPERTY()
    ATwinRoamingRoute* RuntimeRouteActor = nullptr;

    UPROPERTY()
    ATwinGodViewAnchor* GodViewAnchor = nullptr;

    UPROPERTY()
    UOntoTwinRoamingHUDWidget* RoamingHUD = nullptr;

    UPROPERTY()
    UInputMappingContext* ActiveMappingContext = nullptr;

    UPROPERTY()
    UInputMappingContext* DefaultMappingContext = nullptr;

    UPROPERTY()
    UInputAction* ToggleAction = nullptr;
    UPROPERTY()
    UInputAction* MoveAction = nullptr;
    UPROPERTY()
    UInputAction* LookAction = nullptr;
    UPROPERTY()
    UInputAction* VerticalAction = nullptr;
    UPROPERTY()
    UInputAction* ViewAction = nullptr;
    UPROPERTY()
    UInputAction* HudAction = nullptr;
    UPROPERTY()
    UInputAction* InteractAction = nullptr;
    UPROPERTY()
    UInputAction* RouteAction = nullptr;
    UPROPERTY()
    UInputAction* JumpAction = nullptr;
    UPROPERTY()
    UInputAction* CrouchAction = nullptr;
    UPROPERTY()
    UInputAction* SprintAction = nullptr;
    UPROPERTY()
    UInputAction* SelectAction = nullptr;
    UPROPERTY()
    UInputAction* SpeedAction = nullptr;

    FTwinRoamingRuntimeConfig CurrentConfig;
    FTwinRoamingRuntimeConfig PendingConfig;
    int32 AppliedRevision = -1;
    int32 PendingRevision = -1;
    FString RuntimeToken;
    FString PendingRuntimeToken;
    FString CatalogVersion;
    FString RuntimeState = TEXT("disabled");
    FString LastError;
    FString BindingWarning;
    TArray<FString> DegradedFeatures;
    bool bBackendOnline = false;
    bool bRuntimeRequestInFlight = false;
    bool bShuttingDown = false;
    bool bRoamingActive = false;
    bool bHudInteraction = false;
    bool bPendingReload = false;
    bool bEnhancedInputReady = false;
    bool bSprintHeld = false;
    bool bTakeoverEnabled = true;
    bool bDefaultModeApplied = false;
    float PollAccumulator = 1000.0f;
    float HeartbeatAccumulator = 0.0f;
    int32 ConsecutiveFailures = 0;

    void PollRuntimeProjection();
    void HandleRuntimeProjection(const TSharedPtr<FJsonObject>& Payload);
    void RecordBackendFailure(const FString& Error);
    void SendHeartbeat();
    void AddProjectHeaders(const TSharedRef<IHttpRequest, ESPMode::ThreadSafe>& Request) const;
    bool ParseRuntimeConfig(const TSharedPtr<FJsonObject>& Payload,
        FTwinRoamingRuntimeConfig& OutConfig, int32& OutRevision, FString& OutToken,
        FString& OutCatalogVersion, FString& OutBlockedReason) const;
    bool IsStructuralChange(const FTwinRoamingRuntimeConfig& A,
        const FTwinRoamingRuntimeConfig& B) const;
    void ApplyHotConfig(const FTwinRoamingRuntimeConfig& Config);

    bool EnterRoaming(FString& OutError);
    bool ResolveSpawnTransform(class UTwinCharacterAsset* CharacterAsset,
        FTransform& OutTransform, FString& OutError) const;
    class UTwinCharacterAsset* ResolveCharacterAsset(FString& OutError) const;
    UObject* ResolvePrimaryAsset(const FString& PrimaryAssetId) const;
    ATwinRoamingRoute* FindRoute(const FString& RouteId) const;
    ATwinRoamingRoute* BuildRuntimeRoute(FString& OutError);
    void DestroyRuntimeRoute();
    bool ProjectRuntimeRoutePointToGround(
        const FVector& Source, FVector& OutGroundPoint, FString& OutError, int32 PointIndex) const;
    ATwinRoamingSpawnAnchor* FindSpawnAnchor(const FString& SpawnId) const;
    ATwinGodViewAnchor* FindGodViewAnchor(const FString& CameraId) const;
    void CreateHud();
    void DestroyHud();
    void RefreshHud();
    void SetHudInteraction(bool bOpen);
    void RestoreOriginalPawn();

    void SetupInput();
    void RemoveInput();
    void BuildDefaultInputContext();
    void BindEnhancedInput();
    void TickFallbackInput(float DeltaTime);
    void SelectFromView(bool bCursorTrace);
    ATwinInstance* ResolveInteractionInstance(const FHitResult& Hit) const;

    void OnMove(const FInputActionValue& Value);
    void OnLook(const FInputActionValue& Value);
    void OnVertical(const FInputActionValue& Value);
    void OnToggle(const FInputActionValue& Value);
    void OnToggleView(const FInputActionValue& Value);
    void OnToggleHud(const FInputActionValue& Value);
    void OnInteract(const FInputActionValue& Value);
    void OnRoute(const FInputActionValue& Value);
    void OnJump(const FInputActionValue& Value);
    void OnCrouchStarted(const FInputActionValue& Value);
    void OnCrouchEnded(const FInputActionValue& Value);
    void OnSprintStarted(const FInputActionValue& Value);
    void OnSprintEnded(const FInputActionValue& Value);
    void OnSelect(const FInputActionValue& Value);
    void OnAdjustSpeed(const FInputActionValue& Value);
};
