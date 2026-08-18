#include "UEAssetCatalogSyncComponent.h"

#include "TwinSceneManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Dom/JsonObject.h"
#include "Engine/Blueprint.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "HAL/PlatformMisc.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Misc/App.h"
#include "Misc/Base64.h"
#include "Misc/CommandLine.h"
#include "Misc/ObjectThumbnail.h"
#include "Misc/Parse.h"
#include "Modules/ModuleManager.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

#if WITH_EDITOR
#include "ObjectTools.h"
#endif


namespace
{
FString NormalizeRoot(FString Value)
{
    Value.TrimStartAndEndInline();
    Value.ReplaceInline(TEXT("\\"), TEXT("/"));
    while (Value.EndsWith(TEXT("/")))
    {
        Value.LeftChopInline(1);
    }
    return Value;
}

FString ThumbnailDataUrl(const FAssetData& AssetData, const bool bEnabled)
{
#if WITH_EDITOR
    if (!bEnabled)
    {
        return FString();
    }

    FObjectThumbnail Thumbnail;
    if (!ThumbnailTools::LoadThumbnailFromPackage(AssetData, Thumbnail)
        || !Thumbnail.HasValidImageData())
    {
        return FString();
    }

    Thumbnail.CompressImageData();
    const TArray<uint8>& Compressed = Thumbnail.AccessCompressedImageData();
    if (Compressed.Num() < 4)
    {
        return FString();
    }

    const bool bPng = Compressed[0] == 0x89 && Compressed[1] == 0x50
        && Compressed[2] == 0x4e && Compressed[3] == 0x47;
    const bool bJpeg = Compressed[0] == 0xff && Compressed[1] == 0xd8;
    if (!bPng && !bJpeg)
    {
        return FString();
    }
    return FString::Printf(
        TEXT("data:%s;base64,%s"),
        bPng ? TEXT("image/png") : TEXT("image/jpeg"),
        *FBase64::Encode(Compressed));
#else
    return FString();
#endif
}

FString ResolveBackendUrl(const ATwinSceneManager* Manager)
{
    FString BackendUrl = Manager ? Manager->BackendBaseUrl : TEXT("http://localhost:5000");
    FString Override;
    if (FParse::Value(FCommandLine::Get(), TEXT("OntoTwinBackendBaseUrl="), Override))
    {
        Override.TrimStartAndEndInline();
        if (!Override.IsEmpty())
        {
            BackendUrl = Override;
        }
    }
    BackendUrl.RemoveFromEnd(TEXT("/"));
    return BackendUrl;
}
}


UOntoTwinUEAssetCatalogSyncComponent::UOntoTwinUEAssetCatalogSyncComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    AssetRoots.Add(TEXT("/Game/Art"));
}


void UOntoTwinUEAssetCatalogSyncComponent::BeginPlay()
{
    Super::BeginPlay();
    if (bSyncOnBeginPlay)
    {
        SyncCatalog();
    }
}


void UOntoTwinUEAssetCatalogSyncComponent::SyncCatalog()
{
    if (bRequestInFlight)
    {
        UE_LOG(LogTemp, Warning, TEXT("[UE资产目录] 已有同步请求在进行中"));
        return;
    }

    const ATwinSceneManager* Manager = Cast<ATwinSceneManager>(GetOwner());
    const FString UEProjectName = Manager && !Manager->UEProjectName.IsEmpty()
        ? Manager->UEProjectName
        : FString(FApp::GetProjectName());
    const FString UEProjectId = Manager && !Manager->UEProjectId.IsEmpty()
        ? Manager->UEProjectId
        : FString::Printf(TEXT("ueproj_%s"), *UEProjectName);
    const FString BackendUrl = ResolveBackendUrl(Manager);

    FARFilter Filter;
    Filter.bRecursivePaths = true;
    Filter.bRecursiveClasses = true;
    Filter.bIncludeOnlyOnDiskAssets = true;
    for (const FString& RawRoot : AssetRoots)
    {
        const FString Root = NormalizeRoot(RawRoot);
        if (Root.StartsWith(TEXT("/Game")) || Root.StartsWith(TEXT("/Engine")))
        {
            Filter.PackagePaths.Add(FName(*Root));
        }
    }
    if (Filter.PackagePaths.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("[UE资产目录] 没有有效扫描根目录"));
        return;
    }

    Filter.ClassPaths.Add(UStaticMesh::StaticClass()->GetClassPathName());
    if (bIncludeUnsupportedKinds)
    {
        Filter.ClassPaths.Add(USkeletalMesh::StaticClass()->GetClassPathName());
        Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
    }

    FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
    TArray<FAssetData> AssetDataList;
    AssetRegistryModule.Get().GetAssets(Filter, AssetDataList, true);
    AssetDataList.Sort([](const FAssetData& Left, const FAssetData& Right)
    {
        return Left.GetSoftObjectPath().ToString() < Right.GetSoftObjectPath().ToString();
    });

    TArray<TSharedPtr<FJsonValue>> AssetsJson;
    AssetsJson.Reserve(AssetDataList.Num());
    for (const FAssetData& AssetData : AssetDataList)
    {
        const FString AssetKind = AssetData.AssetClassPath.GetAssetName().ToString();
        const bool bStaticMesh = AssetKind.Equals(TEXT("StaticMesh"), ESearchCase::IgnoreCase);
        TSharedPtr<FJsonObject> AssetJson = MakeShared<FJsonObject>();
        AssetJson->SetStringField(TEXT("object_path"), AssetData.GetSoftObjectPath().ToString());
        AssetJson->SetStringField(TEXT("package_name"), AssetData.PackageName.ToString());
        AssetJson->SetStringField(TEXT("asset_name"), AssetData.AssetName.ToString());
        AssetJson->SetStringField(TEXT("display_name"), AssetData.AssetName.ToString());
        AssetJson->SetStringField(TEXT("folder_path"), AssetData.PackagePath.ToString());
        AssetJson->SetStringField(TEXT("asset_kind"), AssetKind);

        if (bStaticMesh && bIncludeStaticMeshBounds)
        {
            if (const UStaticMesh* Mesh = Cast<UStaticMesh>(AssetData.GetAsset()))
            {
                const FVector Size = Mesh->GetBounds().BoxExtent * 2.0;
                TSharedPtr<FJsonObject> SizeJson = MakeShared<FJsonObject>();
                SizeJson->SetNumberField(TEXT("x"), Size.X);
                SizeJson->SetNumberField(TEXT("y"), Size.Y);
                SizeJson->SetNumberField(TEXT("z"), Size.Z);
                AssetJson->SetObjectField(TEXT("size_cm"), SizeJson);
            }
        }

        const FString Thumbnail = ThumbnailDataUrl(AssetData, bIncludeEditorThumbnails);
        if (!Thumbnail.IsEmpty())
        {
            AssetJson->SetStringField(TEXT("thumbnail_data_url"), Thumbnail);
        }
        AssetsJson.Add(MakeShared<FJsonValueObject>(AssetJson));
    }

    TSharedPtr<FJsonObject> Body = MakeShared<FJsonObject>();
    Body->SetStringField(TEXT("ue_project_id"), UEProjectId);
    Body->SetStringField(TEXT("ue_project_name"), UEProjectName);
    TArray<TSharedPtr<FJsonValue>> RootsJson;
    for (const FString& Root : AssetRoots)
    {
        RootsJson.Add(MakeShared<FJsonValueString>(NormalizeRoot(Root)));
    }
    Body->SetArrayField(TEXT("roots"), RootsJson);
    Body->SetArrayField(TEXT("assets"), AssetsJson);

    FString BodyString;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BodyString);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("%s/api/v2/ue/assets/catalog"), *BackendUrl));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), UEProjectId);
    Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Name"), UEProjectName);
    Request->SetContentAsString(BodyString);
    bRequestInFlight = true;

    const TWeakObjectPtr<UOntoTwinUEAssetCatalogSyncComponent> WeakThis(this);
    const int32 AssetCount = AssetDataList.Num();
    Request->OnProcessRequestComplete().BindLambda(
        [WeakThis, AssetCount](FHttpRequestPtr, FHttpResponsePtr Response, bool bOk)
        {
            UOntoTwinUEAssetCatalogSyncComponent* Self = WeakThis.Get();
            if (!Self)
            {
                return;
            }
            Self->bRequestInFlight = false;
            const int32 Code = Response.IsValid() ? Response->GetResponseCode() : -1;
            const bool bSuccess = bOk && Response.IsValid() && Code >= 200 && Code < 300;
            if (bSuccess)
            {
                UE_LOG(LogTemp, Log, TEXT("[UE资产目录] 同步成功 | assets=%d | code=%d"), AssetCount, Code);
            }
            else
            {
                UE_LOG(LogTemp, Error, TEXT("[UE资产目录] 同步失败 | assets=%d | code=%d"), AssetCount, Code);
            }
            if (GEngine)
            {
                GEngine->AddOnScreenDebugMessage(
                    -1, 5.0f, bSuccess ? FColor::Green : FColor::Red,
                    bSuccess
                        ? FString::Printf(TEXT("OntoTwin 资产目录已同步：%d 项"), AssetCount)
                        : FString::Printf(TEXT("OntoTwin 资产目录同步失败：HTTP %d"), Code));
            }
        });
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("[UE资产目录] 开始同步 | project=%s | assets=%d | payload=%.2f MB"),
        *UEProjectId, AssetCount, BodyString.Len() / 1024.0 / 1024.0);
}
