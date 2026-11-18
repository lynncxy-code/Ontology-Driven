#include "OntoTwinRuntimeEditorPanel.h"
#include "RuntimeEditor/ModelLibraryTile.h"
#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "TwinSceneManager.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/ButtonSlot.h"
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
    LibraryBounds->SetHeightOverride(720);
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
        .SetForegroundColor(Ink).SetBackgroundColor(FLinearColor(.078f, .078f, .078f, .98f));
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
    // A separate canvas child keeps search and model cards stationary while previewing.
    ModelPreviewBounds = WidgetTree->ConstructWidget<USizeBox>();
    ModelPreviewBounds->SetWidthOverride(560);
    ModelPreviewBounds->SetVisibility(ESlateVisibility::Collapsed);
    auto* PreviewSlot = Root->AddChildToCanvas(ModelPreviewBounds);
    PreviewSlot->SetAnchors(FAnchors(1.f, 0.f));
    PreviewSlot->SetAlignment(FVector2D(1.f, 0.f));
    PreviewSlot->SetPosition(FVector2D(-484,20));
    PreviewSlot->SetAutoSize(true);
    auto* PreviewFrame = WidgetTree->ConstructWidget<UBorder>();
    PreviewFrame->SetPadding(FMargin(14));
    PreviewFrame->SetBrush(PanelBorder->Background);
    PreviewFrame->SetBrushColor(PanelBorder->GetBrushColor());
    ModelPreviewBounds->SetContent(PreviewFrame);
    auto* PreviewStack = WidgetTree->ConstructWidget<UVerticalBox>();
    PreviewFrame->SetContent(PreviewStack);
    ModelPreviewBox = WidgetTree->ConstructWidget<USizeBox>();
    ModelPreviewBox->SetHeightOverride(399);
    ModelPreviewBox->SetVisibility(ESlateVisibility::Collapsed);
    auto* PreviewLayers = WidgetTree->ConstructWidget<UOverlay>();
    auto* PreviewBackdrop = WidgetTree->ConstructWidget<UBorder>();
    PreviewBackdrop->SetPadding(FMargin(0));
    PreviewBackdrop->SetBrushColor(FLinearColor::Black);
    PreviewBackdrop->SetContent(PreviewLayers);
    ModelPreviewBox->SetContent(PreviewBackdrop);
    ModelViewport = WidgetTree->ConstructWidget<UViewport>();
    ModelViewport->SetBackgroundColor(FLinearColor::Black);
    ModelViewport->SetVisibility(ESlateVisibility::HitTestInvisible);
    auto* ViewportSlot = PreviewLayers->AddChildToOverlay(ModelViewport);
    ViewportSlot->SetHorizontalAlignment(HAlign_Fill);
    ViewportSlot->SetVerticalAlignment(VAlign_Fill);
    PreviewStack->AddChildToVerticalBox(ModelPreviewBox);
    BlueprintImage = WidgetTree->ConstructWidget<UImage>();
    BlueprintImage->SetDesiredSizeOverride(FVector2D(180));
    auto* BlueprintSlot = PreviewLayers->AddChildToOverlay(BlueprintImage);
    BlueprintSlot->SetHorizontalAlignment(HAlign_Center);
    BlueprintSlot->SetVerticalAlignment(VAlign_Center);
    ModelPreviewMessage = CreateText(TEXT("ModelPreviewMessage"),TEXT("单击模型查看"),11,Ink);
    ModelPreviewMessage->SetAutoWrapText(true);
    auto* MessageSlot=PreviewLayers->AddChildToOverlay(ModelPreviewMessage);
    MessageSlot->SetHorizontalAlignment(HAlign_Center);
    MessageSlot->SetVerticalAlignment(VAlign_Center);
    auto* Row = WidgetTree->ConstructWidget<UHorizontalBox>();
    ModelControls = Row;
    ModelControls->SetVisibility(ESlateVisibility::Collapsed);
    PreviewStack->AddChildToVerticalBox(Row)->SetPadding(FMargin(0, 10, 0, 0));
    ModelLibraryStatus = CreateText(TEXT("ModelLibraryStatus"),TEXT(""),12,Ink);
    ModelLibraryStatus->SetAutoWrapText(true);
    Row->AddChildToHorizontalBox(ModelLibraryStatus)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    UButton* CollapsePreview = CreateButton(TEXT("CollapsePreview"),TEXT("收起预览"),Label,false);
    Row->AddChildToHorizontalBox(CollapsePreview)->SetPadding(FMargin(8,0));
    CollapsePreview->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::CollapseLibraryPreview);
    PlaceModelButton = CreateButton(TEXT("PlaceModel"),TEXT("放置"),Label,false);
    Row->AddChildToHorizontalBox(PlaceModelButton);
    PlaceModelButton->OnClicked.AddDynamic(this,&UOntoTwinRuntimeEditorPanel::PlaceSelectedModel);
    auto* Scroll = WidgetTree->ConstructWidget<UScrollBox>();
    auto* ScrollSlot = Stack->AddChildToVerticalBox(Scroll);
    ScrollSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
    ScrollSlot->SetPadding(FMargin(0,8,0,0));
    Scroll->SetScrollbarThickness(FVector2D(8,8));
    LibraryGrid = WidgetTree->ConstructWidget<UWrapBox>();
    LibraryGrid->SetExplicitWrapSize(true);
    LibraryGrid->SetWrapSize(LibraryGridWidth);
    LibraryGrid->SetInnerSlotPadding(FVector2D(8,8));
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
    RefreshModelSourceTabs();
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
    RebuildLibraryGrid();
}
void UOntoTwinRuntimeEditorPanel::RebuildLibraryGrid()
{
    LibraryGrid->ClearChildren();
    LibraryIcons.Reset();
    const FString Query = LibrarySearch->GetText().ToString().TrimStartAndEnd();
    const int32 Columns = FMath::Clamp(FMath::FloorToInt((LibraryGridWidth + 8.f) / 126.f),1,3);
    const float CardWidth = FMath::FloorToFloat((LibraryGridWidth - (Columns-1)*8.f) / Columns);
    const float ImageSize = FMath::Max(48.f, CardWidth - 16.f);
    for (const FString& Key : OrderedModelKeys)
    {
        const FString& Name = ModelLabels[Key];
        if (!Name.Contains(Query,ESearchCase::IgnoreCase) && !Query.IsEmpty()) continue;
        auto* Tile = WidgetTree->ConstructWidget<UModelLibraryTile>();
        FButtonStyle TileStyle = PlaceModelButton->GetStyle();
        TileStyle.SetNormalPadding(FMargin(8)).SetPressedPadding(FMargin(8));
        Tile->SetStyle(TileStyle);
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
        Box->SetWidthOverride(ImageSize);
        Tile->SetContent(Box);
        // SButton adds style padding to slot padding. Budget it exactly once.
        CastChecked<UButtonSlot>(Box->Slot)->SetPadding(FMargin(0));
        CastChecked<UButtonSlot>(Box->Slot)->SetVerticalAlignment(VAlign_Top);
        auto* Stack = WidgetTree->ConstructWidget<UVerticalBox>();
        Box->SetContent(Stack);
        auto* Icon = WidgetTree->ConstructWidget<UImage>();
        auto* ImageBox = WidgetTree->ConstructWidget<USizeBox>();
        ImageBox->SetWidthOverride(ImageSize);
        ImageBox->SetHeightOverride(ImageSize);
        ImageBox->SetContent(Icon);
        Icon->SetDesiredSizeOverride(FVector2D(ImageSize));
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
        NameText->SetWrapTextAt(ImageSize);
        NameText->SetWrappingPolicy(ETextWrappingPolicy::AllowPerCharacterWrapping);
        auto* NameBox = WidgetTree->ConstructWidget<USizeBox>();
        NameBox->SetMinDesiredHeight(32.f);
        NameBox->SetContent(NameText);
        Stack->AddChildToVerticalBox(NameBox)->SetPadding(FMargin(0,6,0,0));
        if (const FString* Error = ModelErrors.Find(Key))
        {
            Tile->SetRenderOpacity(.55f);
            auto* ErrorText = CreateText(NAME_None,TEXT("⚠ ") + *Error,10,Ink);
            ErrorText->SetWrapTextAt(ImageSize);
            Stack->AddChildToVerticalBox(ErrorText);
        }
        auto* Card = WidgetTree->ConstructWidget<USizeBox>();
        Card->SetWidthOverride(CardWidth);
        Card->SetContent(Tile);
        LibraryGrid->AddChildToWrapBox(Card);
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
    else if (!Key.IsEmpty()) ShowToast(TEXT("选中的文件已删除"), EOntoTwinRuntimeToastType::Info);
}
void UOntoTwinRuntimeEditorPanel::CollapseLibraryPreview()
{
    ClearLibraryPreview();
    SelectedModelKey.Reset();
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
    if (ScreenSize.X > 40 && ScreenSize.Y > 40)
    {
        const float Width = FMath::Min(448.f, ScreenSize.X - 40.f);
        LibraryBounds->SetWidthOverride(Width);
        LibraryBounds->SetHeightOverride(FMath::Min(720.f, ScreenSize.Y - 40.f));
        const float BetweenPanels = ScreenSize.X - Width - 380.f - 84.f;
        const float AvailablePreviewWidth = BetweenPanels >= 280.f
            ? BetweenPanels : ScreenSize.X - Width - 56.f;
        const float PreviewWidth = FMath::Clamp(AvailablePreviewWidth, 160.f, 560.f);
        ModelPreviewBounds->SetWidthOverride(PreviewWidth);
        const float PreviewHeight = FMath::Max(100.f, FMath::Min((PreviewWidth - 28.f) * .75f, ScreenSize.Y - 132.f));
        ModelPreviewBox->SetHeightOverride(PreviewHeight);
        BlueprintImage->SetDesiredSizeOverride(FVector2D(FMath::Min(PreviewHeight, PreviewWidth - 28.f)));
        if (auto* PreviewCanvasSlot = Cast<UCanvasPanelSlot>(ModelPreviewBounds->Slot))
            PreviewCanvasSlot->SetPosition(FVector2D(-(Width + 36.f), 20.f));
        // Frame padding + reserved scroll bar width keep the column count stable.
        const float GridWidth = FMath::Max(80.f, Width - 28.f - 16.f);
        if (!FMath::IsNearlyEqual(GridWidth, LibraryGridWidth, 1.f))
        {
            LibraryGridWidth = GridWidth;
            LibraryGrid->SetWrapSize(GridWidth);
            RebuildLibraryGrid();
        }
    }
    if (AActor* Actor = LibraryPreviewActor.Get())
    {
        const FVector Pivot = Actor->GetComponentsBoundingBox().GetCenter();
        const FQuat Spin(FVector::UpVector,FMath::DegreesToRadians(30.0 * DeltaSeconds));
        Actor->SetActorLocationAndRotation(Pivot + Spin.RotateVector(Actor->GetActorLocation()-Pivot),Spin*Actor->GetActorQuat());
    }
}
