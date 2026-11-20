#include "RuntimeEditor/RuntimeModelLibrary.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/SecureHash.h"
#include "PreviewScene.h"

bool OntoTwinModelLibrary::LocalThumbnail(const FString& Key, FString& ImagePath, FString& Error)
{
    const FString File = ResolveLocal(Key);
    TUniquePtr<FArchive> Reader(IFileManager::Get().CreateFileReader(*File));
    if (!Reader) { Error = TEXT("文件不可读取"); return false; }
    const FString ContentHash = LexToString(FMD5Hash::HashFileFromArchive(Reader.Get()));
    Reader.Reset();
    const FString Dir = FPaths::ProjectSavedDir() / TEXT("ModelLibrary/Thumbs-v1");
    ImagePath = Dir / (ContentHash + TEXT(".png"));
    if (IFileManager::Get().FileSize(*ImagePath) > 0) return true;
    UStaticMesh* Mesh = LoadGltfMesh(File, false);
    if (!Mesh) { Error = TEXT("文件解析失败"); return false; }

    FPreviewScene Scene(FPreviewScene::ConstructionValues().SetEditor(false).SetCreatePhysicsScene(false)
        .SetTransactional(false).AllowAudioPlayback(false).SetLightBrightness(3.f));
    UStaticMeshComponent* Model = NewObject<UStaticMeshComponent>();
    Model->SetStaticMesh(Mesh);
    Scene.AddComponent(Model,FTransform::Identity);
    UTextureRenderTarget2D* Target = NewObject<UTextureRenderTarget2D>();
    Target->ClearColor = FLinearColor(.03f,.035f,.04f);
    Target->InitCustomFormat(160,160,PF_B8G8R8A8,false);
    Target->UpdateResourceImmediate();
    USceneCaptureComponent2D* Camera = NewObject<USceneCaptureComponent2D>();
    Camera->TextureTarget = Target;
    Camera->bCaptureEveryFrame = false;
    Camera->bCaptureOnMovement = false;
    Camera->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
    Camera->FOVAngle = 40.f;
    const FRotator View = FVector(-1.,1.45,-.85).Rotation();
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    const double Distance = FMath::Max(1.,Bounds.SphereRadius) / FMath::Sin(FMath::DegreesToRadians(18.));
    Scene.AddComponent(Camera,FTransform(View,Bounds.Origin-View.Vector()*Distance));
    Scene.GetWorld()->SendAllEndOfFrameUpdates();
    Camera->CaptureScene();
    TArray<FColor> Pixels;
    if (!Target->GameThread_GetRenderTargetResource()->ReadPixels(Pixels) || Pixels.Num()!=160*160)
    { Error = TEXT("缩略图渲染失败"); return false; }
    for (FColor& Color : Pixels) Color.A = 255;
    TArray64<uint8> Bytes;
    FImageUtils::PNGCompressImageArray(160,160,Pixels,Bytes);
    IFileManager::Get().MakeDirectory(*Dir,true);
    if (!FFileHelper::SaveArrayToFile(Bytes,*ImagePath)) { Error = TEXT("缩略图缓存不可写"); return false; }
    return true;
}
