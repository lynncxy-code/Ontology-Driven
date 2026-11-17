#include "OntoTwinModelLibrarySettings.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetCompilingManager.h"
#include "DetailCategoryBuilder.h"
#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "Engine/Blueprint.h"
#include "Engine/LevelScriptActor.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "Framework/Notifications/NotificationManager.h"
#include "IDetailCustomization.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/ObjectThumbnail.h"
#include "Misc/PackageName.h"
#include "Misc/SecureHash.h"
#include "ObjectTools.h"
#include "PropertyEditorModule.h"
#include "Serialization/JsonSerializer.h"
#include "Settings/ProjectPackagingSettings.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "HAL/IConsoleManager.h"
#include "UObject/Package.h"

namespace
{
const FString LibraryFolder(TEXT("OntoTwinModelLibrary"));
FString Directory() { return FPaths::ProjectContentDir() / LibraryFolder; }

struct FItem
{
    FAssetData Asset;
    FString Key, Label, Kind, Hash, Thumbnail;
};

void Report(const FString& Message, bool bError = false)
{
    if (bError) { UE_LOG(LogTemp, Error, TEXT("[OntoTwin 模型库] %s"), *Message); }
    else { UE_LOG(LogTemp, Display, TEXT("[OntoTwin 模型库] %s"), *Message); }
    if (!IsRunningCommandlet() && FSlateApplication::IsInitialized())
    {
        FNotificationInfo Info(FText::FromString(Message));
        Info.ExpireDuration = 8.f;
        FSlateNotificationManager::Get().AddNotification(Info);
    }
}

bool Gather(TMap<FString, FItem>& Items, TArray<FString>& Roots, bool bUpdate)
{
    const auto* Settings = GetDefault<UOntoTwinModelLibrarySettings>();
    FARFilter Filter;
    for (const FDirectoryPath& D : Settings->Roots)
    {
        if (D.Path != TEXT("/Game") && !D.Path.StartsWith(TEXT("/Game/")))
        {
            Report(FString::Printf(TEXT("请选择 /Game 下的目录：%s"), *D.Path), true);
            return false;
        }
        Roots.AddUnique(D.Path);
        Filter.PackagePaths.AddUnique(*D.Path);
    }
    if (Roots.IsEmpty()) return true;
    Filter.bRecursivePaths = true;
    Filter.ClassPaths = {UStaticMesh::StaticClass()->GetClassPathName(), USkeletalMesh::StaticClass()->GetClassPathName(),
                         UBlueprint::StaticClass()->GetClassPathName()};
    Filter.bRecursiveClasses = true;
    IAssetRegistry& Registry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();
    Registry.ScanPathsSynchronous(Roots);
    TArray<FAssetData> Assets;
    Registry.GetAssets(Filter, Assets);
    TSet<FName> Parts;
    TMap<FName, FString> PackageHashes;
    for (const FAssetData& Asset : Assets)
    {
        FItem Item;
        Item.Asset = Asset;
        Item.Key = Asset.GetSoftObjectPath().ToString();
        Item.Kind = Asset.AssetClassPath.GetAssetName().ToString();
        if (Asset.IsInstanceOf(UBlueprint::StaticClass()))
        {
            const UBlueprint* BP = Cast<UBlueprint>(Asset.GetAsset());
            UClass* Class = BP ? BP->GeneratedClass.Get() : nullptr;
            if (!Class || !Class->IsChildOf(AActor::StaticClass()) || Class->IsChildOf(APawn::StaticClass())
                || Class->IsChildOf(AController::StaticClass()) || Class->IsChildOf(ALevelScriptActor::StaticClass())
                || Class->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated | CLASS_NewerVersionExists)) continue;
            Item.Kind = TEXT("Blueprint");
            TArray<FName> Dependencies;
            Registry.GetDependencies(Asset.PackageName, Dependencies);
            for (FName Dependency : Dependencies) Parts.Add(Dependency);
        }
        Item.Label = Settings->DisplayNames.FindRef(Item.Key).TrimStartAndEnd();
        if (Item.Label.IsEmpty())
        {
            Item.Label = Asset.AssetName.ToString();
            for (const TCHAR* Prefix : {TEXT("SM_"), TEXT("SK_"), TEXT("BP_")})
                if (Item.Label.RemoveFromStart(Prefix)) break;
            Item.Label.ReplaceInline(TEXT("_"), TEXT(" "));
        }
        FString Filename;
        if (!FPackageName::DoesPackageExist(Asset.PackageName.ToString(), &Filename))
        {
            Report(TEXT("请先保存模型：") + Item.Key, true);
            return false;
        }
        // Include material, texture and nested blueprint dependencies in freshness checks.
        TArray<FName> PendingPackages{Asset.PackageName};
        TSet<FName> VisitedPackages;
        TArray<FString> Fingerprints;
        while (!PendingPackages.IsEmpty())
        {
            const FName PackageName = PendingPackages.Pop();
            if (VisitedPackages.Contains(PackageName)) continue;
            VisitedPackages.Add(PackageName);
            const FString PackagePath = PackageName.ToString();
            if (PackagePath.StartsWith(TEXT("/Script/"))) continue;
            if (bUpdate)
            {
                const UPackage* Package = FindPackage(nullptr, *PackagePath);
                if (Package && Package->IsDirty())
                {
                    Report(TEXT("请先保存模型及其依赖：") + PackagePath, true);
                    return false;
                }
            }
            FString* Hash = PackageHashes.Find(PackageName);
            if (!Hash)
            {
                FString DependencyFile;
                const bool bExists = FPackageName::DoesPackageExist(PackagePath, &DependencyFile);
                Hash = &PackageHashes.Add(PackageName,
                    bExists ? LexToString(FMD5Hash::HashFile(*DependencyFile)) : TEXT("missing"));
            }
            Fingerprints.Add(PackagePath + TEXT("=") + *Hash);
            TArray<FName> Dependencies;
            Registry.GetDependencies(PackageName, Dependencies);
            PendingPackages.Append(Dependencies);
            if (Item.Kind == TEXT("Blueprint")) Parts.Append(Dependencies);
        }
        Fingerprints.Sort();
        Item.Hash = FMD5::HashAnsiString(*FString::Join(Fingerprints, TEXT("\n")));
        Item.Thumbnail = FMD5::HashAnsiString(*Item.Key) + TEXT("-") + Item.Hash + TEXT(".png");
        const FString Key = Item.Key;
        Items.Add(Key, MoveTemp(Item));
    }
    for (auto It = Items.CreateIterator(); It; ++It)
        if (It.Value().Kind != TEXT("Blueprint") && Parts.Contains(It.Value().Asset.PackageName)) It.RemoveCurrent();
    return true;
}

bool RenderImage(const FItem& Item)
{
    UObject* Asset = Item.Asset.GetAsset();
    if (!Asset) return false;
    FAssetCompilingManager::Get().FinishAllCompilation();
    FObjectThumbnail Thumb;
    ThumbnailTools::RenderThumbnail(Asset, 192, 192, ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush, nullptr, &Thumb);
    // Creating the preview scene can enqueue material shaders on the first draw.
    FAssetCompilingManager::Get().FinishAllCompilation();
    ThumbnailTools::RenderThumbnail(Asset, 192, 192, ThumbnailTools::EThumbnailTextureFlushMode::AlwaysFlush, nullptr, &Thumb);
    const auto& Data = Thumb.GetUncompressedImageData();
    if (Thumb.GetImageWidth() <= 0 || Data.Num() != Thumb.GetImageWidth() * Thumb.GetImageHeight() * 4) return false;
    TArray64<uint8> PNG;
    FImageUtils::PNGCompressImageArray(Thumb.GetImageWidth(), Thumb.GetImageHeight(),
        MakeArrayView(reinterpret_cast<const FColor*>(Data.GetData()), Data.Num() / 4), PNG);
    return !PNG.IsEmpty() && FFileHelper::SaveArrayToFile(PNG, *(Directory() / Item.Thumbnail));
}

bool Covers(const TArray<FDirectoryPath>& Paths, const FString& Root)
{
    return Paths.ContainsByPredicate([&](const FDirectoryPath& P){return P.Path == Root || Root.StartsWith(P.Path + TEXT("/"));});
}

void Process(bool bUpdate)
{
    if (bUpdate && IsRunningCommandlet())
    {
        Report(TEXT("请在 UE 编辑器的项目设置中更新模型库，后台进程仅支持检查清单"), true);
        return;
    }
    TArray<FString> Roots;
    TMap<FString, FItem> Items;
    if (!Gather(Items, Roots, bUpdate)) return;
    const FString IndexPath = Directory() / TEXT("catalog.json");
    if (Roots.IsEmpty() && !bUpdate)
    {
        UE_LOG(LogTemp, Warning, TEXT("[OntoTwin 模型库] 尚未选择工程模型目录"));
        if (!IsRunningCommandlet()) Report(TEXT("尚未选择工程模型文件夹，请在项目设置中更新模型库"));
        return;
    }
    TArray<TSharedPtr<FJsonValue>> Old;
    FString Json;
    const bool bHasIndex = FFileHelper::LoadFileToString(Json, *IndexPath)
        && FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Old);
    TMap<FString, TSharedPtr<FJsonObject>> Previous;
    for (const auto& Value : Old)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        FString Key;
        if (Value->TryGetObject(Object) && (*Object)->TryGetStringField(TEXT("key"), Key)) Previous.Add(Key, *Object);
    }
    auto* Packaging = GetMutableDefault<UProjectPackagingSettings>();
    TArray<FString> Changes;
    if (!bHasIndex) Changes.Add(TEXT("缺少模型清单"));
    for (const auto& Pair : Previous)
        if (!Items.Contains(Pair.Key)) Changes.Add(TEXT("移除或移动 ") + Pair.Key);
    TArray<FString> Keys;
    Items.GetKeys(Keys);
    Keys.Sort();
    TArray<TSharedPtr<FJsonValue>> Result;
    if (bUpdate) IFileManager::Get().MakeDirectory(*Directory(), true);
    for (const FString& Key : Keys)
    {
        const FItem& Item = Items[Key];
        const auto* Prior = Previous.Find(Key);
        FString Hash, Name, Image;
        const bool bImageCurrent = Prior && (*Prior)->TryGetStringField(TEXT("hash"), Hash) && Hash == Item.Hash
            && (*Prior)->TryGetStringField(TEXT("thumbnail"), Image) && Image == Item.Thumbnail
            && FPaths::FileExists(Directory() / Item.Thumbnail);
        if (!bImageCurrent || !(*Prior)->TryGetStringField(TEXT("label"), Name) || Name != Item.Label)
            Changes.Add((Prior ? TEXT("变更 ") : TEXT("新增或移入 ")) + Key);
        if (!bUpdate) continue;
        if (!RenderImage(Item))
        {
            Report(TEXT("缩略图生成失败：") + Key, true);
            return;
        }
        if (GetDefault<UOntoTwinModelLibrarySettings>()->DisplayNames.FindRef(Key).TrimStartAndEnd().IsEmpty())
            UE_LOG(LogTemp, Display, TEXT("[模型库] 未填显示名 %s → %s"), *Key, *Item.Label);
        auto Object = MakeShared<FJsonObject>();
        Object->SetStringField(TEXT("key"), Key);
        Object->SetStringField(TEXT("label"), Item.Label);
        Object->SetStringField(TEXT("kind"), Item.Kind);
        Object->SetStringField(TEXT("thumbnail"), Item.Thumbnail);
        Object->SetStringField(TEXT("hash"), Item.Hash);
        Result.Add(MakeShared<FJsonValueObject>(Object));
    }
    auto Ensure = [&](TArray<FDirectoryPath>& Paths, const FString& Root)
    {
        if (!Covers(Paths, Root))
        {
            Changes.Add(TEXT("缺少打包目录 ") + Root);
            if (bUpdate) { FDirectoryPath D; D.Path = Root; Paths.Add(D); }
        }
    };
    for (const FString& Root : Roots) Ensure(Packaging->DirectoriesToAlwaysCook, Root);
    Ensure(Packaging->DirectoriesToAlwaysStageAsUFS, LibraryFolder);
    if (!bUpdate && Changes.Num())
    {
        Report(TEXT("请更新模型库：") + FString::Join(Changes, TEXT("\n")), IsRunningCookCommandlet());
        return;
    }
    if (!bUpdate) return;
    FString Output;
    const FString Temp = IndexPath + TEXT(".tmp");
    if (!Packaging->TryUpdateDefaultConfigFile() || !FJsonSerializer::Serialize(Result,TJsonWriterFactory<>::Create(&Output))
        || !FFileHelper::SaveStringToFile(Output, *Temp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
        || !IFileManager::Get().Move(*IndexPath, *Temp))
    {
        Report(TEXT("模型库或打包设置保存失败，请检查文件是否可写"), true);
        return;
    }
    Report(FString::Printf(TEXT("模型库已更新，共 %d 项。"), Items.Num()) + FString::Join(Changes, TEXT("\n")));
}

struct FSettingsDetails : IDetailCustomization
{
    virtual void CustomizeDetails(IDetailLayoutBuilder& Builder) override
    {
        Builder.EditCategory(TEXT("模型库")).AddCustomRow(FText::FromString(TEXT("更新模型库")))
            .WholeRowContent()[SNew(SButton).Text(FText::FromString(TEXT("更新模型库")))
                .OnClicked_Lambda([]{Process(true); return FReply::Handled();})];
    }
};
FDelegateHandle Startup;
FAutoConsoleCommand Command(TEXT("OntoTwin.UpdateModelLibrary"),TEXT("更新工程模型清单及缩略图"),
    FConsoleCommandDelegate::CreateLambda([]{Process(true);}));
}
void OntoTwinEditorLibrary::Register()
{
    Startup = FCoreDelegates::OnPostEngineInit.AddLambda([]{
        if (!IsRunningGame() && (!IsRunningCommandlet() || IsRunningCookCommandlet())) Process(false);
    });
    if (!IsRunningCommandlet() && !IsRunningGame())
        FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor").RegisterCustomClassLayout(
            TEXT("OntoTwinModelLibrarySettings"), FOnGetDetailCustomizationInstance::CreateLambda([]{return MakeShared<FSettingsDetails>();}));
}
void OntoTwinEditorLibrary::Unregister()
{
    FCoreDelegates::OnPostEngineInit.Remove(Startup);
    if (auto* Editor = FModuleManager::GetModulePtr<FPropertyEditorModule>("PropertyEditor"))
        Editor->UnregisterCustomClassLayout(TEXT("OntoTwinModelLibrarySettings"));
}
