#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UEAssetCatalogSyncComponent.generated.h"


/**
 * 项目级 UE 资产目录同步工具。
 *
 * 组件只负责枚举与上报，不负责做 CAD 匹配；推荐和人工确认由 OntoTwin Web 端完成。
 */
UCLASS(ClassGroup=(DigitalTwin), meta=(BlueprintSpawnableComponent, DisplayName="UE Asset Catalog Sync"))
class ONTOTWINSYNC_API UOntoTwinUEAssetCatalogSyncComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UOntoTwinUEAssetCatalogSyncComponent();

    virtual void BeginPlay() override;

    /** PIE / 运行时启动时自动同步一次。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="资产目录",
              meta=(DisplayName="启动时同步资产目录"))
    bool bSyncOnBeginPlay = true;

    /** 要递归扫描的 UE 内容根目录。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="资产目录",
              meta=(DisplayName="扫描根目录"))
    TArray<FString> AssetRoots;

    /** 同步 Blueprint / SkeletalMesh 供用户识别，但 Web 端会标记为当前不可绑定。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="资产目录",
              meta=(DisplayName="展示暂不支持的资产类型"))
    bool bIncludeUnsupportedKinds = true;

    /** 读取 UE 编辑器已经缓存到资产包中的缩略图；无缩略图时不阻断同步。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="资产目录",
              meta=(DisplayName="同步编辑器缩略图"))
    bool bIncludeEditorThumbnails = true;

    /** 为 StaticMesh 加载 bounds，供 CAD 尺寸匹配；目录较大时可关闭。 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="资产目录",
              meta=(DisplayName="同步静态网格尺寸"))
    bool bIncludeStaticMeshBounds = true;

    UFUNCTION(CallInEditor, BlueprintCallable, Category="资产目录",
              meta=(DisplayName="同步 UE 资产目录"))
    void SyncCatalog();

private:
    bool bRequestInFlight = false;
};
