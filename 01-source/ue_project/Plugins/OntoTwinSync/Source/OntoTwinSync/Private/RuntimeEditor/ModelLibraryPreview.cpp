#include "OntoTwinRuntimeEditorPanel.h"
#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "TwinSceneManager.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraTypes.h"
#include "Components/Button.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/LocalPlayer.h"
#include "SceneView.h"
#include "Components/SizeBox.h"
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
    if (ModelPreviewBox) ModelPreviewBox->SetVisibility(ESlateVisibility::Collapsed);
    if (ModelPreviewMessage) ModelPreviewMessage->SetVisibility(ESlateVisibility::Collapsed);
    if (PlaceModelButton) PlaceModelButton->SetIsEnabled(false);
}

void UOntoTwinRuntimeEditorPanel::HandleLibrarySelection(FString Label, ESelectInfo::Type)
{
    if (SceneManager) SceneManager->CancelUnconfirmedModelPlacement();
    ClearLibraryPreview();
    const FString* Key = ModelKeys.Find(Label);
    if (!Key || !ModelViewport || !ModelViewport->GetViewportWorld()) return;

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
        // Configured Actor Blueprints keep their existing placement path. Browsing never runs their scripts.
        const UBlueprint* Blueprint = Cast<UBlueprint>(Asset);
        const UClass* ActorClass = Blueprint ? Blueprint->GeneratedClass.Get() : Cast<UClass>(Asset);
        const bool bActorBlueprint = ActorClass && ActorClass->IsChildOf(AActor::StaticClass());
        ModelPreviewMessage->SetText(FText::FromString(bActorBlueprint
            ? TEXT("此蓝图可点击放置后在场景中预览") : TEXT("模型预览加载失败，请检查资源后重新选择")));
        ModelPreviewMessage->SetVisibility(ESlateVisibility::HitTestInvisible);
        PlaceModelButton->SetIsEnabled(bActorBlueprint);
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
    if (Size.X < 1. || Size.Y < 1.) Size = FVector2D(340., ModelPreviewBox->GetHeightOverride());
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
    ModelPreviewBox->SetVisibility(ESlateVisibility::HitTestInvisible);
    PlaceModelButton->SetIsEnabled(true);
}
