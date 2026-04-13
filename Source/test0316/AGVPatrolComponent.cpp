#include "AGVPatrolComponent.h"
#include "Math/UnrealMathUtility.h"
#include "GameFramework/Actor.h"

UAGVPatrolComponent::UAGVPatrolComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	RunningTime = 0.0f;
}

void UAGVPatrolComponent::BeginPlay()
{
	Super::BeginPlay();

	AActor* Owner = GetOwner();
	if (Owner)
	{
		// 记录初始位置，以此为基准进行偏移计算
		InitialLocation = Owner->GetActorLocation();
	}
}

void UAGVPatrolComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	AActor* Owner = GetOwner();
	if (!Owner || CycleTime <= 0.0f) return;

	// 累加时间
	RunningTime += DeltaTime;

	// 计算平滑的不匀速偏移缓动 (利用 1 - cos 来达成 0 到 1 到 0 的缓动平滑过渡)
	// (1.0f - cos(Phase)) / 2.0f 范围为 0 到 1
	float Phase = (RunningTime / CycleTime) * PI * 2.0f;
	float OffsetScale = (1.0f - FMath::Cos(Phase)) * 0.5f;

	// 加上偏移
	FVector NewLocation = InitialLocation + (PatrolAxis.GetSafeNormal() * PatrolDistance * OffsetScale);
	
	// 更新AGV Actor位置
	Owner->SetActorLocation(NewLocation);
}
