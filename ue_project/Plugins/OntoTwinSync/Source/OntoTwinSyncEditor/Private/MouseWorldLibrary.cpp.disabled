#include "MouseWorldLibrary.h"

#if WITH_EDITOR
#include "EditorViewportClient.h"
#include "LevelEditorViewport.h"
#endif

bool UMouseWorldLibrary::GetCursorWorldLocation(
	FVector& OutLocation,
	FVector& OutNormal,
	FString& OutHitActorName,
	FString& OutViewTypeName,
	bool& bOutHitObject,
	float DepthAxisValue)
{
	OutLocation = FVector::ZeroVector;
	OutNormal = FVector::ZeroVector;
	OutHitActorName = TEXT("");
	OutViewTypeName = TEXT("Unknown");
	bOutHitObject = false;

#if WITH_EDITOR
	FLevelEditorViewportClient* ViewportClient = GCurrentLevelEditingViewportClient;
	if (!ViewportClient || !ViewportClient->Viewport)
	{
		return false;
	}

	UWorld* World = ViewportClient->GetWorld();
	if (!World)
	{
		return false;
	}

	const FViewportCursorLocation Cursor = ViewportClient->GetCursorWorldLocationFromMousePos();
	const FVector Origin = Cursor.GetOrigin();
	const FVector Direction = Cursor.GetDirection();

	switch (ViewportClient->ViewportType)
	{
	case LVT_Perspective:
		OutViewTypeName = TEXT("Perspective");
		break;
	case LVT_OrthoXY:
		OutViewTypeName = TEXT("Top");
		break;
	case LVT_OrthoNegativeXY:
		OutViewTypeName = TEXT("Bottom");
		break;
	case LVT_OrthoXZ:
		OutViewTypeName = TEXT("Front");
		break;
	case LVT_OrthoNegativeXZ:
		OutViewTypeName = TEXT("Back");
		break;
	case LVT_OrthoYZ:
		OutViewTypeName = TEXT("Left");
		break;
	case LVT_OrthoNegativeYZ:
		OutViewTypeName = TEXT("Right");
		break;
	default:
		OutViewTypeName = TEXT("Unknown");
		break;
	}

	FHitResult Hit;
	FCollisionQueryParams Params;
	Params.bTraceComplex = true;

	const FVector TraceEnd = Origin + Direction * 1000000.f;
	if (World->LineTraceSingleByChannel(Hit, Origin, TraceEnd, ECC_Visibility, Params))
	{
		OutLocation = Hit.Location;
		OutNormal = Hit.Normal;
		OutHitActorName = Hit.GetActor() ? Hit.GetActor()->GetActorLabel() : TEXT("");
		bOutHitObject = true;
		return true;
	}

	if (ViewportClient->IsOrtho())
	{
		OutLocation = Origin;

		switch (ViewportClient->ViewportType)
		{
		case LVT_OrthoXY:
		case LVT_OrthoNegativeXY:
			OutLocation.Z = DepthAxisValue;
			break;
		case LVT_OrthoXZ:
		case LVT_OrthoNegativeXZ:
			OutLocation.Y = DepthAxisValue;
			break;
		case LVT_OrthoYZ:
		case LVT_OrthoNegativeYZ:
			OutLocation.X = DepthAxisValue;
			break;
		default:
			break;
		}

		return true;
	}
#endif

	return false;
}
