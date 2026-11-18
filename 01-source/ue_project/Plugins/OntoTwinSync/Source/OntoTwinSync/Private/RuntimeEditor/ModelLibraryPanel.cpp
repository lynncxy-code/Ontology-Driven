#include "OntoTwinRuntimeEditorPanel.h"
#include "RuntimeEditor/ModelLibraryTile.h"
#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "TwinSceneManager.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Viewport.h"
#include "Components/WrapBox.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "ImageUtils.h"
#include "UI/OntoTwinGlassTheme.h"

namespace
{
// The library remembers its layout for this program run, including across level changes.
bool bLibraryOpen = false;
int32 LastSource = 0;
const FLinearColor Ink(0.96f, 0.96f, 0.96f);
}
void UOntoTwinRuntimeEditorPanel::BuildModelLibrary(UCanvasPanel* Root)
{
    UTextBlock* Label = nullptr;
    UButton* Open = CreateButton(TEXT("OpenModelLibrary"), TEXT("模型库"), Label, false);
    Open->OnClicked.AddDynamic(this, &UOntoTwinRuntimeEditorPanel::ToggleLibrary);
    SceneContent->AddChildToVerticalBox(Open);
    LibraryBounds = WidgetTree->ConstructWidget<USizeBox>();
    LibraryBounds->SetWidthOverride(448);
    LibraryBounds->SetHeightOverride(550);
    auto* LibrarySlot = Root->AddChildToCanvas(LibraryBounds);
    LibrarySlot->SetAnchors(FAnchors(1.f, 0.f));
    LibrarySlot->SetAlignment(FVector2D(1.f, 0.f));
    LibrarySlot->SetPosition(FVector2D(-20,20));
    LibrarySlot->SetAutoSize(true);
    auto* Frame = WidgetTree->ConstructWidget<UBorder>();
    Frame->SetPadding(FMargin(14));
    Frame->SetBrush(PanelBorder->Background);
    Frame->SetBrushColor(PanelBorder->GetBrushColor());
    LibraryBounds->SetContent(Frame);
    auto* Stack = WidgetTree->ConstructWidget<UVerticalBox>();
    Frame->SetContent(Stack);
    auto AddButton = [&](UHorizontalBox* Row, const TCHAR* Name, const TCHAR* Title) {
        UButton* Button = CreateButton(Name, Title, Label, false);
        Row->AddChildToHorizontalBox(Button)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
        return Button;
    };
    auto* Header = WidgetTree->ConstructWidget<UHorizontalBox>();
    Stack->AddChildToVerticalBox(Header)->SetPadding(FMargin(0, 0, 0, 10));
    Header->AddChildToHorizontalBox(CreateText(TEXT("LibraryTitle"), TEXT("模型库"), 16, Ink, true))
        ->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UButton* Close = CreateButton(TEXT("CloseLibrary"), TEXT("收起"), Label, false);
    Header->AddChildToHorizontalBox(Close);
    auto* Tabs = WidgetTree->ConstructWidget<UHorizontalBox>();
    Stack->AddChildToVerticalBox(Tabs)->SetPadding(FMargin(0, 0, 0, 8));
    auto* Project = AddButton(Tabs,TEXT("ProjectModels"),TEXT("工程模型"));
    auto* Local = AddButton(Tabs,TEXT("LocalModels"),TEXT("本地 Models"));
    auto* Art = AddButton(Tabs,TEXT("ArtModels"),TEXT("Art Studio"));
    ModelSourceTabs = {Project, Local, Art};
    Project->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::ShowProjectModels);
    Local->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::ShowLocalModels);
    Art->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::ShowArtStudioModels);
    Close->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::ToggleLibrary);
    LibrarySearch = WidgetTree->ConstructWidget<UEditableTextBox>();
    LibrarySearch->WidgetStyle = FCoreStyle::Get().GetWidgetStyle<FEditableTextBoxStyle>(TEXT("NormalEditableTextBox"));
    LibrarySearch->WidgetStyle.SetFont(FOntoTwinGlassTheme::Font(11.f)).SetPadding(FMargin(8.f, 5.f))
        .SetForegroundColor(Ink).SetBackgroundColor(FLinearColor(.078f, .078f, .078f, .92f));
    LibrarySearch->SetHintText(FText::FromString(TEXT("搜索模型名称")));
    LibrarySearch->OnTextChanged.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::SearchLibrary);
    Stack->AddChildToVerticalBox(LibrarySearch);
    LocalActions = WidgetTree->ConstructWidget<UHorizontalBox>();
    Stack->AddChildToVerticalBox(LocalActions);
    AddButton(LocalActions,TEXT("RefreshModels"),TEXT("刷新"))->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::RefreshLibrary);
    AddButton(LocalActions,TEXT("OpenModelsFolder"),TEXT("打开文件夹"))->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::OpenModelsFolder);
    ArtStudioPanel = WidgetTree->ConstructWidget<UVerticalBox>();
    Stack->AddChildToVerticalBox(ArtStudioPanel)->SetPadding(FMargin(0, 24, 0, 16));
    ArtStudioPanel->AddChildToVerticalBox(CreateText(TEXT("ArtStudioTitle"),TEXT("Art Studio 模型库"),16,Ink,true));
    auto* ArtStatus = CreateText(TEXT("ArtStudioStatus"),TEXT("服务尚未部署，模型库暂未连接。"),12,Ink);
    ArtStatus->SetAutoWrapText(true);
    ArtStudioPanel->AddChildToVerticalBox(ArtStatus)->SetPadding(FMargin(0,12,0,16));
    UButton* Admin = CreateButton(TEXT("ArtStudioAdmin"),TEXT("管理员入口"),Label,false);
    Admin->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::OpenArtStudioAdmin);
    ArtStudioPanel->AddChildToVerticalBox(Admin);
    ArtStudioAdminInfo = CreateText(TEXT("ArtStudioAdminInfo"),
        TEXT("此入口预留给管理员配置 Art Studio 服务地址和连接账号。\n\n服务部署完成后开放配置与登录，连接后可在这里浏览模型。"),12,Ink);
    ArtStudioAdminInfo->SetAutoWrapText(true);
    ArtStudioPanel->AddChildToVerticalBox(ArtStudioAdminInfo)->SetPadding(FMargin(0,16,0,0));
    ArtStudioAdminInfo->SetVisibility(ESlateVisibility::Collapsed);
    ArtStudioPanel->SetVisibility(ESlateVisibility::Collapsed);
    ModelPreviewBox = WidgetTree->ConstructWidget<USizeBox>();
    ModelPreviewBox->SetHeightOverride(190);
    auto* PreviewLayers = WidgetTree->ConstructWidget<UOverlay>();
    ModelPreviewBox->SetContent(PreviewLayers);
    ModelViewport = WidgetTree->ConstructWidget<UViewport>();
    ModelViewport->SetBackgroundColor(FLinearColor(.078f,.078f,.078f));
    ModelViewport->SetVisibility(ESlateVisibility::HitTestInvisible);
    auto* ViewportSlot = PreviewLayers->AddChildToOverlay(ModelViewport);
    ViewportSlot->SetHorizontalAlignment(HAlign_Fill);
    ViewportSlot->SetVerticalAlignment(VAlign_Fill);
    Stack->AddChildToVerticalBox(ModelPreviewBox);
    BlueprintImage = WidgetTree->ConstructWidget<UImage>();
    BlueprintImage->SetDesiredSizeOverride(FVector2D(180));
    PreviewLayers->AddChildToOverlay(BlueprintImage)->SetHorizontalAlignment(HAlign_Center);
    ModelPreviewMessage = CreateText(TEXT("ModelPreviewMessage"),TEXT("单击模型查看"),11,Ink);
    auto* MessageSlot=PreviewLayers->AddChildToOverlay(ModelPreviewMessage);
    MessageSlot->SetHorizontalAlignment(HAlign_Center);
    MessageSlot->SetVerticalAlignment(VAlign_Center);
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    ModelControls = Row;
    Stack->AddChildToVerticalBox(Row);
    ModelLibraryStatus = CreateText(TEXT("ModelLibraryStatus"),TEXT(""),12,Ink);
    ModelLibraryStatus->SetAutoWrapText(true);
    Row->AddChildToHorizontalBox(ModelLibraryStatus)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    PlaceModelButton = AddButton(Row,TEXT("PlaceModel"),TEXT("放置"));
    PlaceModelButton->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::PlaceSelectedModel);
    auto* Scroll = WidgetTree->ConstructWidget<UScrollBox>();
    Stack->AddChildToVerticalBox(Scroll)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    LibraryGrid = WidgetTree->ConstructWidget<UWrapBox>();
    LibraryGrid->SetInnerSlotPadding(FVector2D(4,4));
    Scroll->AddChild(LibraryGrid);
    ModelSource = static_cast<EModelSource>(LastSource);
    LibraryBounds->SetVisibility(bLibraryOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
}
void UOntoTwinRuntimeEditorPanel::ToggleLibrary()
{
    bLibraryOpen = !LibraryBounds->IsVisible();
    LibraryBounds->SetVisibility(bLibraryOpen ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (bLibraryOpen) PopulateModelLibrary(ModelSource);
    else { ClearLibraryPreview(); SelectedModelKey.Reset(); }
}
void UOntoTwinRuntimeEditorPanel::PopulateModelLibrary(EModelSource Source)
{
    ClearLibraryPreview();
    SelectedModelKey.Reset();
    ModelSource = Source;
    LastSource = static_cast<int32>(Source);
    for (int32 I=0; I<ModelSourceTabs.Num(); ++I) ModelSourceTabs[I]->SetIsEnabled(I!=LastSource);
    ModelLabels.Reset();
    OrderedModelKeys.Reset();
    ModelErrors.Reset();
    ModelImages.Reset();
    ModelKinds.Reset();
    PendingLocalImages.Reset();
    LibraryTextures.Reset();
    LocalActions->SetVisibility(Source == EModelSource::Local ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    const bool bArtStudio = Source == EModelSource::ArtStudio;
    ArtStudioPanel->SetVisibility(bArtStudio ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    LibrarySearch->SetVisibility(bArtStudio ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    ModelPreviewBox->SetVisibility(bArtStudio ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    ModelControls->SetVisibility(bArtStudio ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    LibraryGrid->SetVisibility(bArtStudio ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    if (Source != EModelSource::ArtStudio)
        for (const auto& E : OntoTwinModelLibrary::List(Source == EModelSource::Local))
        {
            OrderedModelKeys.Add(E.Key);
            ModelLabels.Add(E.Key,E.Label);
            ModelKinds.Add(E.Key,E.Kind);
            if (!E.Error.IsEmpty()) ModelErrors.Add(E.Key,E.Error);
            if (!E.Thumbnail.IsEmpty()) ModelImages.Add(E.Key,E.Thumbnail);
            if (E.Kind == TEXT("GLB") && E.Error.IsEmpty()) PendingLocalImages.Add(E.Key);
        }
    ModelLibraryStatus->SetText(FText::GetEmpty());
    ModelPreviewMessage->SetText(FText::FromString(TEXT("单击模型查看")));
    ModelPreviewMessage->SetVisibility(ESlateVisibility::Visible);
    RebuildLibraryGrid();
}
void UOntoTwinRuntimeEditorPanel::RebuildLibraryGrid()
{
    LibraryGrid->ClearChildren();
    LibraryIcons.Reset();
    const FString Query = LibrarySearch->GetText().ToString().TrimStartAndEnd();
    for (const FString& Key : OrderedModelKeys)
    {
        const FString& Name = ModelLabels[Key];
        if (!Name.Contains(Query,ESearchCase::IgnoreCase) && !Query.IsEmpty()) continue;
        auto* Tile = WidgetTree->ConstructWidget<UModelLibraryTile>();
        Tile->SetStyle(PlaceModelButton->GetStyle());
        Tile->Select.BindWeakLambda(this,[this,Key]{SelectLibraryKey(Key);});
        Tile->Drag.BindWeakLambda(this,[this,Key]{
            if (SceneManager && SceneManager->CanPlaceRuntimeModel() && !ModelErrors.Contains(Key))
            {
                SelectLibraryKey(Key);
                SceneManager->BeginModelPlacement(Key, ModelLabels.FindRef(Key), true);
            }
        });
        Tile->InitializeTile();
        Tile->SetToolTipText(FText::FromString(Name));
        auto* Box = WidgetTree->ConstructWidget<USizeBox>();
        Box->SetWidthOverride(110);
        Tile->SetContent(Box);
        auto* Stack = WidgetTree->ConstructWidget<UVerticalBox>();
        Box->SetContent(Stack);
        auto* Icon = WidgetTree->ConstructWidget<UImage>();
        auto* ImageBox = WidgetTree->ConstructWidget<USizeBox>();
        ImageBox->SetWidthOverride(110);
        ImageBox->SetHeightOverride(110);
        ImageBox->SetContent(Icon);
        Icon->SetDesiredSizeOverride(FVector2D(110));
        const FString File = ModelImages.FindRef(Key);
        if (!File.IsEmpty())
        {
            auto& Texture = LibraryTextures.FindOrAdd(Key);
            if (!Texture) Texture = FImageUtils::ImportFileAsTexture2D(File);
            Icon->SetBrushFromTexture(Texture);
        }
        else Icon->SetColorAndOpacity(FLinearColor(.2f,.2f,.2f));
        LibraryIcons.Add(Key,Icon);
        Stack->AddChildToVerticalBox(ImageBox)->SetHorizontalAlignment(HAlign_Center);
        auto* NameText = CreateText(NAME_None,Name,11,Ink);
        NameText->SetWrapTextAt(110.f);
        NameText->SetWrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping);
        Stack->AddChildToVerticalBox(NameText);
        if (const FString* Error = ModelErrors.Find(Key))
        {
            Tile->SetRenderOpacity(.55f);
            auto* ErrorText = CreateText(NAME_None,TEXT("⚠ ") + *Error,10,Ink);
            ErrorText->SetWrapTextAt(110.f);
            Stack->AddChildToVerticalBox(ErrorText);
        }
        LibraryGrid->AddChildToWrapBox(Tile);
    }
    if (!LibraryGrid->GetChildrenCount())
    {
        const FString Message = OrderedModelKeys.IsEmpty() ? TEXT("此来源暂无模型") : TEXT("没有匹配的模型");
        LibraryGrid->AddChildToWrapBox(CreateText(NAME_None,Message,12,Ink));
    }
}
void UOntoTwinRuntimeEditorPanel::RefreshLibrary()
{
    const FString Key = SelectedModelKey;
    PopulateModelLibrary(ModelSource);
    if (ModelLabels.Contains(Key)) SelectLibraryKey(Key);
    else if (!Key.IsEmpty()) ModelPreviewMessage->SetText(FText::FromString(TEXT("选中的文件已删除")));
}
void UOntoTwinRuntimeEditorPanel::SearchLibrary(const FText&) { RebuildLibraryGrid(); }
void UOntoTwinRuntimeEditorPanel::ShowProjectModels() { PopulateModelLibrary(EModelSource::Project); }
void UOntoTwinRuntimeEditorPanel::ShowLocalModels() { PopulateModelLibrary(EModelSource::Local); }
void UOntoTwinRuntimeEditorPanel::ShowArtStudioModels() { PopulateModelLibrary(EModelSource::ArtStudio); }
void UOntoTwinRuntimeEditorPanel::OpenArtStudioAdmin()
{
    ArtStudioAdminInfo->SetVisibility(ESlateVisibility::Visible);
}
void UOntoTwinRuntimeEditorPanel::OpenModelsFolder()
{
    const FString Dir = OntoTwinModelLibrary::ModelsDirectory();
    IFileManager::Get().MakeDirectory(*Dir,true);
    FPlatformProcess::ExploreFolder(*Dir);
}
void UOntoTwinRuntimeEditorPanel::PlaceSelectedModel()
{
    if (SceneManager && ModelLabels.Contains(SelectedModelKey) && !ModelErrors.Contains(SelectedModelKey))
        SceneManager->BeginModelPlacement(SelectedModelKey,ModelLabels[SelectedModelKey]);
}
void UOntoTwinRuntimeEditorPanel::NativeTick(const FGeometry& Geometry, float DeltaSeconds)
{
    Super::NativeTick(Geometry,DeltaSeconds);
    if (!LibraryBounds || !LibraryBounds->IsVisible()) return;
    const bool bWritable = SceneManager && SceneManager->CanPlaceRuntimeModel();
    PlaceModelButton->SetIsEnabled(bWritable && !SelectedModelKey.IsEmpty() && !ModelErrors.Contains(SelectedModelKey));
    PlaceModelButton->SetToolTipText(FText::FromString(bWritable ? TEXT("在场景中选择位置") : TEXT("当前关卡没有可写数据集")));
    if (!PendingLocalImages.IsEmpty())
    {
        const FString Key = PendingLocalImages.Pop();
        FString ImagePath, Error;
        if (OntoTwinModelLibrary::LocalThumbnail(Key,ImagePath,Error))
        {
            ModelImages.Add(Key,ImagePath);
            if (auto* Icon = LibraryIcons.Find(Key))
            {
                UTexture2D* Texture = FImageUtils::ImportFileAsTexture2D(ImagePath);
                LibraryTextures.Add(Key,Texture);
                (*Icon)->SetColorAndOpacity(FLinearColor::White);
                (*Icon)->SetBrushFromTexture(Texture);
            }
        }
        else
        {
            ModelErrors.Add(Key,Error);
            RebuildLibraryGrid();
            if (Key == SelectedModelKey) SelectLibraryKey(Key);
        }
    }
    const FVector2D ScreenSize = Geometry.GetLocalSize();
    const FVector2D Size = PanelBorder->GetCachedGeometry().GetLocalSize();
    if (ScreenSize.X > 40 && ScreenSize.Y > 40)
    {
        LibraryBounds->SetWidthOverride(FMath::Min(448.f, ScreenSize.X - 40.f));
        LibraryBounds->SetHeightOverride(FMath::Min(FMath::Max(Size.Y,550.f), ScreenSize.Y - 40.f));
    }
    if (AActor* Actor = LibraryPreviewActor.Get())
    {
        const FVector Pivot = Actor->GetComponentsBoundingBox().GetCenter();
        const FQuat Spin(FVector::UpVector,FMath::DegreesToRadians(30.0 * DeltaSeconds));
        Actor->SetActorLocationAndRotation(Pivot + Spin.RotateVector(Actor->GetActorLocation()-Pivot),Spin*Actor->GetActorQuat());
    }
}
