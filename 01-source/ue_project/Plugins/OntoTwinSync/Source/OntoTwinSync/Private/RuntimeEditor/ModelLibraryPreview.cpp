#include "OntoTwinRuntimeEditorPanel.h"
#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "TwinSceneManager.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraTypes.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "ImageUtils.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/LocalPlayer.h"
#include "SceneView.h"
#include "Components/SizeBox.h"
#include "Components/HorizontalBox.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextBlock.h"
#include "Components/Viewport.h"
#include "Engine/Blueprint.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Misc/PackageName.h"

void UOntoTwinRuntimeEditorPanel::EndLibraryPreview()
{
    ClearLibraryPreview();
    UWorld* PreviewWorld = ModelViewport ? ModelViewport->GetViewportWorld() : nullptr;
    if (PreviewWorld && PreviewWorld->GetBegunPlay())
        PreviewWorld->EndPlay(EEndPlayReason::RemovedFromWorld);
}

void UOntoTwinRuntimeEditorPanel::ClearLibraryPreview()
{
    if (AActor* Previous = LibraryPreviewActor.Get()) Previous->Destroy();
    LibraryPreviewActor.Reset();
    if (BlueprintImage) BlueprintImage->SetVisibility(ESlateVisibility::Collapsed);
    if (ModelViewport) ModelViewport->SetVisibility(ESlateVisibility::Hidden);
    if (ModelPreviewMessage) ModelPreviewMessage->SetVisibility(ESlateVisibility::Collapsed);
    if (PlaceModelButton) PlaceModelButton->SetIsEnabled(false);
    if (ModelPreviewBox) ModelPreviewBox->SetVisibility(ESlateVisibility::Collapsed);
    if (ModelControls) ModelControls->SetVisibility(ESlateVisibility::Collapsed);
}

void UOntoTwinRuntimeEditorPanel::SelectLibraryKey(const FString& Selected)
{
    if (SceneManager) SceneManager->CancelUnconfirmedModelPlacement();
    SelectedModelKey = Selected;
    ClearLibraryPreview();
    ModelPreviewBox->SetVisibility(ESlateVisibility::Visible);
    ModelControls->SetVisibility(ESlateVisibility::Visible);
    ModelLibraryStatus->SetText(FText::FromString(ModelLabels.FindRef(Selected)));
    const FString* Key = &SelectedModelKey;
    if (const FString* Error = ModelErrors.Find(*Key))
    {
        ModelPreviewMessage->SetText(FText::FromString(*Error + TEXT("。请检查原文件，然后刷新模型库。")));
        ModelPreviewMessage->SetVisibility(ESlateVisibility::Visible);
        return;
    }
    if (ModelKinds.FindRef(*Key) == TEXT("Blueprint"))
    {
        BlueprintImage->SetBrushFromTexture(FImageUtils::ImportFileAsTexture2D(ModelImages.FindRef(*Key)));
        BlueprintImage->SetVisibility(ESlateVisibility::Visible);
        ModelPreviewMessage->SetText(FText::FromString(TEXT("放置后可查看完整效果")));
        ModelPreviewMessage->SetVisibility(ESlateVisibility::Visible);
        PlaceModelButton->SetIsEnabled(true);
        return;
    }
    if (!ModelViewport || !ModelViewport->GetViewportWorld()) return;
    UObject* Asset = nullptr;
    if (Key->StartsWith(TEXT("models:")))
    {
        const FString File = OntoTwinModelLibrary::ResolveLocal(*Key);
        if (!File.IsEmpty()) Asset = OntoTwinModelLibrary::LoadGltfMesh(File, false);
    }
    else
    {
        const FString Path = Key->Contains(TEXT(".")) ? *Key : *Key + TEXT(".") + FPackageName::GetShortName(*Key);
        Asset = LoadObject<UObject>(nullptr, *Path);
    }

    UMeshComponent* Component = nullptr;
    if (UStaticMesh* Mesh = Cast<UStaticMesh>(Asset))
    {
        if (auto* Actor = Cast<AStaticMeshActor>(ModelViewport->Spawn(AStaticMeshActor::StaticClass())))
        {
            Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
            Actor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
            Component = Actor->GetStaticMeshComponent();
        }
    }
    else if (USkeletalMesh* SkeletalMesh = Cast<USkeletalMesh>(Asset))
    {
        if (auto* Actor = Cast<ASkeletalMeshActor>(ModelViewport->Spawn(ASkeletalMeshActor::StaticClass())))
        {
            Actor->GetSkeletalMeshComponent()->SetSkeletalMesh(SkeletalMesh);
            Component = Actor->GetSkeletalMeshComponent();
        }
    }

    if (!Component)
    {
        ModelErrors.Add(Selected, TEXT("加载失败"));
        ModelPreviewMessage->SetText(FText::FromString(TEXT("加载失败。请检查资源并刷新模型库。")));
        ModelPreviewMessage->SetVisibility(ESlateVisibility::Visible);
        RebuildLibraryGrid();
        return;
    }

    AActor* Actor = Component->GetOwner();
    LibraryPreviewActor = Actor;
    Actor->SetActorEnableCollision(false);
    Actor->SetActorScale3D(FVector(100. / FMath::Max(Component->Bounds.SphereRadius, 0.01)));
    Component->UpdateBounds();
    const FBox Bounds = Component->Bounds.GetBox();
    const FVector Center = Bounds.GetCenter();
    const FRotator ViewRotation = FVector(-1., 1.45, -0.85).Rotation();
    const FRotationMatrix Axes(ViewRotation);
    const FVector Forward = Axes.GetUnitAxis(EAxis::X);
    const FVector Right = Axes.GetUnitAxis(EAxis::Y);
    const FVector Up = Axes.GetUnitAxis(EAxis::Z);
    // Match the UMG viewport's projection, including host projects which maintain vertical FOV.
    FVector2D Size = ModelViewport->GetCachedGeometry().GetLocalSize();
    if (Size.X < 1. || Size.Y < 1.) Size = FVector2D(LibraryBounds->GetWidthOverride()-28.f, ModelPreviewBox->GetHeightOverride());
    const FIntRect Rect(0, 0, FMath::RoundToInt(Size.X), FMath::RoundToInt(Size.Y));
    FSceneViewProjectionData Projection;
    Projection.SetViewRectangle(Rect);
    FMinimalViewInfo ViewInfo;
    FMinimalViewInfo::CalculateProjectionMatrixGivenViewRectangle(ViewInfo,
        GetDefault<ULocalPlayer>()->AspectRatioAxisConstraint, Rect, Projection);
    double Distance = 0.;
    for (int32 Corner = 0; Corner < 8; ++Corner)
    {
        const FVector Relative(Corner & 1 ? Bounds.Max.X - Center.X : Bounds.Min.X - Center.X,
                               Corner & 2 ? Bounds.Max.Y - Center.Y : Bounds.Min.Y - Center.Y,
                               Corner & 4 ? Bounds.Max.Z - Center.Z : Bounds.Min.Z - Center.Z);
        const double HalfExtent = FMath::Max(FMath::Abs(Relative.Dot(Right)) * Projection.ProjectionMatrix.M[0][0],
                                              FMath::Abs(Relative.Dot(Up)) * Projection.ProjectionMatrix.M[1][1]);
        Distance = FMath::Max(Distance, HalfExtent - Relative.Dot(Forward));
    }
    ModelViewport->SetViewRotation(ViewRotation);
    ModelViewport->SetViewLocation(Center - Forward * (Distance * 1.05 + 8.));
    UDirectionalLightComponent* Fill = NewObject<UDirectionalLightComponent>(Actor);
    Actor->AddInstanceComponent(Fill);
    Fill->SetWorldRotation(ViewRotation);
    Fill->SetIntensity(2.4f);
    Fill->SetSpecularScale(0.14f);
    Fill->SetCastShadows(false);
    Fill->RegisterComponent();
    ModelViewport->SetLightIntensity(1.8f);
    ModelViewport->SetSkyIntensity(1.5f);
    ModelViewport->SetVisibility(ESlateVisibility::HitTestInvisible);
    PlaceModelButton->SetIsEnabled(true);
}
