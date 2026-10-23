#include "OntoTwinCalibrationSnapshot.h"

#include "Editor.h"
#include "Components/PrimitiveComponent.h"
#include "LevelEditorViewport.h"
#include "EngineUtils.h"
#include "GameFramework/Volume.h"
#include "TwinSceneManager.h"
#include "DesktopPlatformModule.h"
#include "IDesktopPlatform.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Docking/TabManager.h"
#include "HAL/FileManager.h"
#include "ImageUtils.h"
#include "InputCoreTypes.h"
#include "Misc/App.h"
#include "Misc/Base64.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "SceneView.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/AutomationTest.h"
#endif

namespace OntoTwinCalibrationSnapshot
{
namespace
{
const FName TabName(TEXT("OntoTwinCalibrationSnapshot"));
TWeakPtr<SDockTab> OpenTab;

struct FPoint
{
	FString Id;
	FVector Position;
	FString ActorLabel;
};

// Orthographic cursor origins lie inside the view volume, not necessarily above
// the floor. Trace through the volume, and ignore editor-hidden roof/floor actors.
constexpr double TraceDistance = 1000000.0;
bool TraceVisible(UWorld* World, const FVector& Start, const FVector& End, FHitResult& Hit)
{
	if (!World) return false;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(OntoTwinCalibrationPick), true);
	for (int32 Attempt = 0; Attempt < 64; ++Attempt)
	{
		if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params)) return false;
		AActor* Actor = Hit.GetActor();
		UPrimitiveComponent* Component = Hit.GetComponent();
		if (Actor && (Actor->IsHiddenEd() || Actor->IsA<AVolume>())) { Params.AddIgnoredActor(Actor); continue; }
		if (Component && !Component->IsVisible()) { Params.AddIgnoredComponent(Component); continue; }
		return true;
	}
	return false;
}

// Bake high-contrast point labels directly into the PNG. No level actors/assets are created.
void DrawMarker(TArray<FColor>& Pixels, FIntPoint Size, FIntPoint Center, const FString& Label)
{
	auto Put = [&](int32 X, int32 Y, FColor Color)
	{
		if (X >= 0 && Y >= 0 && X < Size.X && Y < Size.Y) Pixels[Y * Size.X + X] = Color;
	};
	for (int32 Y = -6; Y <= 6; ++Y)
		for (int32 X = -6; X <= 6; ++X)
			if (X * X + Y * Y <= 36) Put(Center.X + X, Center.Y + Y, FColor::White);
	for (int32 D = -4; D <= 4; ++D)
	{
		Put(Center.X + D, Center.Y, FColor::Black);
		Put(Center.X, Center.Y + D, FColor::Black);
	}
	static const uint8 Glyphs[11][7] = {
		{14,17,19,21,25,17,14}, {4,12,4,4,4,4,14}, {14,17,1,2,4,8,31},
		{30,1,1,14,1,1,30}, {2,6,10,18,31,2,2}, {31,16,16,30,1,1,30},
		{14,16,16,30,17,17,14}, {31,1,2,4,8,8,8}, {14,17,17,14,17,17,14},
		{14,17,17,15,1,1,14}, {30,17,17,30,16,16,16} // P
	};
	const int32 Left = Center.X + 9, Top = Center.Y - 10;
	for (int32 Y = -3; Y < 24; ++Y)
		for (int32 X = -3; X < Label.Len() * 18; ++X)
			Put(Left + X, Top + Y, FColor::Black);
	for (int32 C = 0; C < Label.Len(); ++C)
	{
		const int32 Index = Label[C] == 'P' ? 10 : Label[C] - '0';
		if (Index < 0 || Index > 10) continue;
		for (int32 Y = 0; Y < 7; ++Y)
			for (int32 X = 0; X < 5; ++X)
				if (Glyphs[Index][Y] & (1 << (4 - X)))
					for (int32 DY = 0; DY < 3; ++DY)
						for (int32 DX = 0; DX < 3; ++DX)
							Put(Left + C * 18 + X * 3 + DX, Top + Y * 3 + DY, FColor::White);
	}
}

bool HasArea(const TArray<FPoint>& Points)
{
	double Span = 0, Area = 0;
	for (int32 I = 1; I < Points.Num(); ++I)
	{
		const FVector A = Points[I].Position - Points[0].Position;
		Span = FMath::Max(Span, A.X * A.X + A.Y * A.Y);
		for (int32 J = I + 1; J < Points.Num(); ++J)
		{
			const FVector B = Points[J].Position - Points[0].Position;
			const FVector Edge = Points[J].Position - Points[I].Position;
			Span = FMath::Max(Span, Edge.X * Edge.X + Edge.Y * Edge.Y);
			Area = FMath::Max(Area, FMath::Abs(A.X * B.Y - A.Y * B.X));
		}
	}
	return Span > 1 && Area / Span >= 0.05;
}

class SSnapshotPanel;
class FSnapshotInput : public IInputProcessor
{
public:
	TWeakPtr<SSnapshotPanel> Panel;
	virtual void Tick(float, FSlateApplication&, TSharedRef<ICursor>) override {}
	virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override;
};

class SSnapshotPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSnapshotPanel) {}
	SLATE_END_ARGS()

	void Construct(const FArguments&)
	{
		ChildSlot
		[
			SNew(SBox).MinDesiredWidth(390)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(12)
				[
					SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(
						TEXT("用 DX11 启动 UE 后，照常切到顶视图。在同一楼层选取至少 3 个分布较开的参考点：点击视口取得焦点，将鼠标停在参考点上按 F8。只记录命中的可见物体表面；需要时可先隐藏屋顶或其他楼层。插件不切换视角或渲染模式。")))
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(12, 0)
				[
					SNew(SCheckBox).IsChecked_Lambda([this] { return bCollecting ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
					.OnCheckStateChanged_Lambda([this](ECheckBoxState State) { bCollecting = State == ECheckBoxState::Checked; })
					[SNew(STextBlock).Text(FText::FromString(TEXT("启用 F8 采集（点位高度差不超过 5 cm）")))]
				]
				+ SVerticalBox::Slot().FillHeight(1).Padding(12)
				[
					SNew(SScrollBox)
					+ SScrollBox::Slot()[SAssignNew(PointList, SVerticalBox)]
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(12, 0)
				[
					SAssignNew(Status, STextBlock).AutoWrapText(true)
					.Text(FText::FromString(TEXT("启用采集后，在场景视口按 F8 记录第一个点。")))
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(12)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth()
					[SNew(SButton).Text(FText::FromString(TEXT("清空点位")))
						.OnClicked_Lambda([this] { Points.Reset(); World.Reset(); NextPoint = 1; Refresh(); return FReply::Handled(); })]
					+ SHorizontalBox::Slot().FillWidth(1).HAlign(HAlign_Right)
					[SNew(SButton).Text(FText::FromString(TEXT("导出标定快照")))
						.IsEnabled_Lambda([this] { return Points.Num() >= 3; })
						.OnClicked_Lambda([this] { Export(); return FReply::Handled(); })]
				]
			]
		];
		Input = MakeShared<FSnapshotInput>();
		Input->Panel = SharedThis(this);
		FSlateApplication::Get().RegisterInputPreProcessor(Input);
	}

	virtual ~SSnapshotPanel() override
	{
		if (FSlateApplication::IsInitialized() && Input.IsValid())
			FSlateApplication::Get().UnregisterInputPreProcessor(Input);
	}

	void Message(const FString& Text) { Status->SetText(FText::FromString(Text)); }

	bool Collect()
	{
		FLevelEditorViewportClient* Client = GCurrentLevelEditingViewportClient;
		if (!bCollecting || !Client || !Client->Viewport || !Client->Viewport->HasFocus() || GEditor->PlayWorld) return false;
		FIntPoint Mouse;
		Client->Viewport->GetMousePos(Mouse);
		const FIntPoint Size = Client->Viewport->GetSizeXY();
		if (Mouse.X < 0 || Mouse.Y < 0 || Mouse.X >= Size.X || Mouse.Y >= Size.Y) return false;
		UWorld* CurrentWorld = Client->GetWorld();
		if (Points.Num() && World.Get() != CurrentWorld)
		{
			Message(TEXT("场景已切换，请清空旧点位后重新采集。")); return true;
		}
		if (Points.Num() >= 32) { Message(TEXT("最多采集 32 个点，请删除不需要的点。")); return true; }
		const FViewportCursorLocation Cursor = Client->GetCursorWorldLocationFromMousePos();
		FHitResult Hit;
		const FVector Start = Cursor.GetOrigin() - (Client->IsOrtho() ? Cursor.GetDirection() * TraceDistance : FVector::ZeroVector);
		if (!TraceVisible(CurrentWorld, Start, Cursor.GetOrigin() + Cursor.GetDirection() * TraceDistance, Hit))
		{
			Message(TEXT("没有命中物体表面，未记录。请确认该物体有可查询的碰撞，或改选明确的地面参考点。")); return true;
		}
		for (const FPoint& Point : Points)
			if (FVector::Dist(Point.Position, Hit.Location) < 1.0)
			{
				Message(TEXT("该位置已经采集，请选择其他参考点。")); return true;
			}
		World = CurrentWorld;
		Points.Add({FString::Printf(TEXT("P%d"), NextPoint++), Hit.Location,
			Hit.GetActor() ? Hit.GetActor()->GetActorLabel() : TEXT("场景表面")});
		Refresh();
		Message(FString::Printf(TEXT("已记录 %s。继续按 F8 采集；完成后调整画面，让全部点位都可见，再导出。"), *Points.Last().Id));
		return true;
	}

private:
	bool bCollecting = false;
	int32 NextPoint = 1;
	TArray<FPoint> Points;
	TWeakObjectPtr<UWorld> World;
	TSharedPtr<SVerticalBox> PointList;
	TSharedPtr<STextBlock> Status;
	TSharedPtr<FSnapshotInput> Input;

	void Refresh()
	{
		PointList->ClearChildren();
		for (const FPoint& Point : Points)
		{
			const FString Id = Point.Id;
			PointList->AddSlot().AutoHeight().Padding(0, 4)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().FillWidth(1)
				[SNew(STextBlock).AutoWrapText(true).Text(FText::FromString(FString::Printf(
					TEXT("%s  ·  %s\nX %.2f   Y %.2f   Z %.2f cm"), *Point.Id, *Point.ActorLabel,
					Point.Position.X, Point.Position.Y, Point.Position.Z)))]
				+ SHorizontalBox::Slot().AutoWidth()
				[SNew(SButton).Text(FText::FromString(TEXT("删除"))).OnClicked_Lambda([this, Id]
					{ Points.RemoveAll([&](const FPoint& P) { return P.Id == Id; }); Refresh(); return FReply::Handled(); })]
			];
		}
		Message(FString::Printf(TEXT("当前 %d 个点。至少需要 3 个不共线点。"), Points.Num()));
	}

	void Export()
	{
		FLevelEditorViewportClient* Client = GCurrentLevelEditingViewportClient;
		if (!Client || !Client->Viewport || !World.IsValid() || World.Get() != Client->GetWorld() || GEditor->PlayWorld)
		{ Message(TEXT("请回到采集点所在的编辑器场景视口后再导出。")); return; }
		if (Points.Num() < 3 || !HasArea(Points))
		{ Message(TEXT("参考点不足或接近共线，请在平面上选取分布更开的点。")); return; }
		double MinZ = Points[0].Position.Z, MaxZ = MinZ;
		for (const FPoint& P : Points) { MinZ = FMath::Min(MinZ, P.Position.Z); MaxZ = FMath::Max(MaxZ, P.Position.Z); }
		if (MaxZ - MinZ > 5.0)
		{ Message(TEXT("点位高度差超过 5 cm，请选择同一标定平面的参考点，避免混用设备顶面与地面。")); return; }
		FViewport* Viewport = Client->Viewport;
		const FIntPoint Size = Viewport->GetSizeXY();
		if (Size.X < 100 || Size.Y < 100 || int64(Size.X) * Size.Y > 16777216)
		{ Message(TEXT("视口尺寸不适合导出，请调整到普通窗口大小。")); return; }
		Viewport->Draw();
		FSceneViewFamilyContext Family(FSceneViewFamily::ConstructionValues(Viewport, Client->GetScene(), Client->EngineShowFlags));
		FSceneView* View = Client->CalcSceneView(&Family);
		if (!View) { Message(TEXT("无法读取当前视图，请重新打开场景视口。")); return; }
		TArray<FVector2D> Projected;
		for (const FPoint& Point : Points)
		{
			FVector2D Pixel;
			if (!View->WorldToPixel(Point.Position, Pixel) || Pixel.X < 15 || Pixel.Y < 20 || Pixel.X > Size.X - 85 || Pixel.Y > Size.Y - 25)
			{ Message(Point.Id + TEXT(" 不在完整画面内，请调整视角后重新导出。")); return; }
			for (const FVector2D& Other : Projected)
				if (FVector2D::Distance(Other, Pixel) < 70)
				{ Message(TEXT("截图中的点号过近，请放大或调整视角，让点号能清楚区分。")); return; }
			// Use the exact world ray rather than deprojecting rounded screenshot
			// pixels; one pixel in a zoomed-out top view can span many centimetres.
			const FVector RayDirection = Client->IsOrtho()
				? FVector(View->ViewMatrices.GetInvViewMatrix().TransformVector(FVector(0, 0, 1))).GetSafeNormal()
				: (Point.Position - View->ViewMatrices.GetViewOrigin()).GetSafeNormal();
			const FVector RayOrigin = Client->IsOrtho()
				? Point.Position - RayDirection * TraceDistance : View->ViewMatrices.GetViewOrigin();
			FHitResult Hit;
			if (!TraceVisible(World.Get(), RayOrigin, Point.Position + RayDirection * 3.0, Hit)
				|| FVector::Dist(Hit.Location, Point.Position) > 2.0)
			{ Message(Point.Id + TEXT(" 被遮挡或所在物体已移动，请调整视角或重新采集该点。")); return; }
			Projected.Add(Pixel);
		}
		TArray<FColor> Pixels;
		if (!GetViewportScreenShot(Viewport, Pixels) || Pixels.Num() != Size.X * Size.Y)
		{ Message(TEXT("截图失败，尚未导出文件。请确认当前视口正常显示。")); return; }
		for (FColor& Pixel : Pixels) Pixel.A = 255;
		TArray<TSharedPtr<FJsonValue>> JsonPoints;
		for (int32 I = 0; I < Points.Num(); ++I)
		{
			DrawMarker(Pixels, Size, FIntPoint(FMath::RoundToInt(Projected[I].X), FMath::RoundToInt(Projected[I].Y)), Points[I].Id);
			auto Point = MakeShared<FJsonObject>();
			Point->SetStringField(TEXT("id"), Points[I].Id);
			Point->SetStringField(TEXT("actor_label"), Points[I].ActorLabel);
			Point->SetArrayField(TEXT("ue_world_cm"), {MakeShared<FJsonValueNumber>(Points[I].Position.X),
				MakeShared<FJsonValueNumber>(Points[I].Position.Y), MakeShared<FJsonValueNumber>(Points[I].Position.Z)});
			Point->SetArrayField(TEXT("image_xy"), {MakeShared<FJsonValueNumber>(Projected[I].X), MakeShared<FJsonValueNumber>(Projected[I].Y)});
			JsonPoints.Add(MakeShared<FJsonValueObject>(Point));
		}
		TArray64<uint8> Png;
		FImageUtils::PNGCompressImageArray(Size.X, Size.Y, TArrayView64<const FColor>(Pixels.GetData(), Pixels.Num()), Png);
		if (Png.Num() == 0 || Png.Num() > 32 * 1024 * 1024)
		{ Message(TEXT("截图编码失败或文件过大，请缩小视口后重试。")); return; }
		auto Root = MakeShared<FJsonObject>();
		Root->SetStringField(TEXT("schema"), TEXT("ontotwin.calibration-snapshot"));
		Root->SetNumberField(TEXT("version"), 1);
		Root->SetStringField(TEXT("snapshot_id"), FGuid::NewGuid().ToString(EGuidFormats::Digits));
		Root->SetStringField(TEXT("created_at"), FDateTime::UtcNow().ToIso8601());
		Root->SetStringField(TEXT("units"), TEXT("cm"));
		auto Source = MakeShared<FJsonObject>();
		Source->SetStringField(TEXT("project_name"), FApp::GetProjectName());
		Source->SetStringField(TEXT("level"), World->GetOutermost()->GetName());
		FString ProjectId;
		int32 Managers = 0;
		for (TActorIterator<ATwinSceneManager> It(World.Get()); It; ++It) { ++Managers; ProjectId = It->UEProjectId; }
		Source->SetStringField(TEXT("ue_project_id"), Managers == 1 ? ProjectId : TEXT(""));
		Root->SetObjectField(TEXT("source"), Source);
		auto Image = MakeShared<FJsonObject>();
		Image->SetNumberField(TEXT("width"), Size.X);
		Image->SetNumberField(TEXT("height"), Size.Y);
		Image->SetStringField(TEXT("mime_type"), TEXT("image/png"));
		Image->SetStringField(TEXT("data_base64"), FBase64::Encode(Png.GetData(), static_cast<uint32>(Png.Num())));
		Root->SetObjectField(TEXT("image"), Image);
		Root->SetArrayField(TEXT("points"), JsonPoints);
		FString Json;
		if (!FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Json))) return;
		const FString Folder = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("OntoTwinCalibrationSnapshots"));
		IFileManager::Get().MakeDirectory(*Folder, true);
		TArray<FString> Files;
		IDesktopPlatform* Desktop = FDesktopPlatformModule::Get();
		if (!Desktop || !Desktop->SaveFileDialog(FSlateApplication::Get().FindBestParentWindowHandleForDialogs(AsShared()),
			TEXT("导出标定快照"), Folder, TEXT("calibration-") + FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S")) + TEXT(".otcalib.json"),
			TEXT("OntoTwin 标定快照 (*.otcalib.json)|*.otcalib.json"), 0, Files) || Files.IsEmpty())
		{ Message(TEXT("已取消导出，采集点位仍保留。")); return; }
		const FString TempFile = Files[0] + TEXT(".") + FGuid::NewGuid().ToString(EGuidFormats::Digits) + TEXT(".tmp");
		if (!FFileHelper::SaveStringToFile(Json, *TempFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
			|| !IFileManager::Get().Move(*Files[0], *TempFile, true, true))
		{
			IFileManager::Get().Delete(*TempFile);
			Message(TEXT("文件保存失败，请选择可写入的位置重试。")); return;
		}
		bCollecting = false;
		Message(TEXT("已导出：") + Files[0] + TEXT("\n在孪生器 CAD 标定步骤导入此文件，按点号点击对应位置。"));
	}
};

bool FSnapshotInput::HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event)
{
	if (Event.GetKey() != EKeys::F8 || Event.IsRepeat() || Event.IsControlDown() || Event.IsAltDown() || Event.IsShiftDown()) return false;
	TSharedPtr<SSnapshotPanel> Pinned = Panel.Pin();
	return Pinned.IsValid() && Pinned->Collect();
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSnapshotFormatTest, "OntoTwin.CalibrationSnapshot.GeometryAndImage",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSnapshotFormatTest::RunTest(const FString&)
{
	if (FApp::CanEverRender() && !IsRunningCommandlet() && !OpenTab.IsValid())
	{
		Open();
		TSharedPtr<SDockTab> Tab = OpenTab.Pin();
		TestTrue(TEXT("Calibration panel opens"), Tab.IsValid());
		if (Tab) { Tab->SetContent(SNullWidget::NullWidget); Tab->RequestCloseTab(); }
	}
	if (UWorld* TestWorld = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr)
	{
		FActorSpawnParameters Spawn;
		Spawn.ObjectFlags |= RF_Transient;
		AActor* TestActor = TestWorld->SpawnActor<AActor>(Spawn);
		if (TestNotNull(TEXT("Temporary collision fixture"), TestActor))
		{
			UStaticMeshComponent* Box = NewObject<UStaticMeshComponent>(TestActor);
			TestActor->SetRootComponent(Box);
			Box->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
			Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
			Box->SetCollisionResponseToAllChannels(ECR_Block);
			Box->RegisterComponent();
			const FVector Center(123456, 123456, 5000);
			Box->SetWorldLocation(Center);
			FHitResult Hit;
			const FVector Start = Center + FVector(0, 0, TraceDistance);
			const FVector End = Center - FVector(0, 0, TraceDistance);
			TestTrue(TEXT("Top-view ray hits real surface"), TraceVisible(TestWorld, Start, End, Hit) && Hit.GetActor() == TestActor);
			TestTrue(TEXT("Top-view hit is on the surface"), FMath::Abs(Hit.Location.Z - (Center.Z + 50)) < 0.01);
			TestActor->SetIsTemporarilyHiddenInEditor(true);
			TraceVisible(TestWorld, Start, End, Hit);
			TestTrue(TEXT("Hidden roof actors are not calibration surfaces"), Hit.GetActor() != TestActor);
			TestWorld->DestroyActor(TestActor);
		}
	}
	TArray<FPoint> TestPoints = {
		{TEXT("P1"), FVector(0, 0, 0), TEXT("Ground")},
		{TEXT("P2"), FVector(100, 0, 0), TEXT("Ground")},
		{TEXT("P3"), FVector(200, 0, 0), TEXT("Ground")}
	};
	TestFalse(TEXT("Collinear XY must be rejected"), HasArea(TestPoints));
	TestPoints[2].Position = FVector(0, 100, 0);
	TestTrue(TEXT("Distributed XY can calibrate"), HasArea(TestPoints));
	TArray<FColor> Pixels;
	Pixels.Init(FColor(210, 210, 210, 255), 640 * 360);
	DrawMarker(Pixels, FIntPoint(640, 360), FIntPoint(80, 260), TEXT("P1"));
	DrawMarker(Pixels, FIntPoint(640, 360), FIntPoint(500, 260), TEXT("P2"));
	DrawMarker(Pixels, FIntPoint(640, 360), FIntPoint(80, 90), TEXT("P3"));
	TestTrue(TEXT("Crosshair marks exact coordinate"), Pixels[260 * 640 + 80] == FColor::Black);
	TestTrue(TEXT("Marker has contrasting outline"), Pixels[265 * 640 + 80] == FColor::White);
	TestTrue(TEXT("Background remains unchanged"), Pixels[0] == FColor(210, 210, 210, 255));
	TArray64<uint8> Png;
	FImageUtils::PNGCompressImageArray(640, 360, TArrayView64<const FColor>(Pixels.GetData(), Pixels.Num()), Png);
	TestTrue(TEXT("PNG encoding succeeds"), Png.Num() > 100);
	if (Png.Num() > 100)
	{
		TestEqual(TEXT("PNG signature"), Png[0], uint8(137));
		const FString File = FPaths::ProjectSavedDir() / TEXT("Automation/OntoTwinCalibrationSnapshot.png");
		IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true);
		TestTrue(TEXT("Reference image written"), FFileHelper::SaveArrayToFile(Png, *File));
	}
	return true;
}
#endif
}

void Register()
{
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(TabName, FOnSpawnTab::CreateLambda([](const FSpawnTabArgs&)
	{
		TSharedRef<SDockTab> Tab = SNew(SDockTab).TabRole(ETabRole::NomadTab)[SNew(SSnapshotPanel)];
		OpenTab = Tab;
		return Tab;
	})).SetDisplayName(FText::FromString(TEXT("OntoTwin 标定快照"))).SetMenuType(ETabSpawnerMenuType::Hidden);
}

void Unregister()
{
	if (TSharedPtr<SDockTab> Tab = OpenTab.Pin()) { Tab->SetContent(SNullWidget::NullWidget); Tab->RequestCloseTab(); }
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(TabName);
}

void Open() { FGlobalTabmanager::Get()->TryInvokeTab(TabName); }
}
