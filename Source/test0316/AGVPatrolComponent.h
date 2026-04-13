#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AGVPatrolComponent.generated.h"

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class TEST0316_API UAGVPatrolComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	UAGVPatrolComponent();

protected:
	virtual void BeginPlay() override;

public:	
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** 巡逻总距离 (虚幻单位，30米 = 3000) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AGV巡逻")
    float PatrolDistance = 3000.0f;

    /** 往返一个完整来回所需的时间 (秒) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AGV巡逻")
    float CycleTime = 10.0f;

    /** 巡逻移动的轴向 (默认沿 Y 轴左右移动) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AGV巡逻")
    FVector PatrolAxis = FVector(0.0f, 1.0f, 0.0f);

private:
    FVector InitialLocation;
    float RunningTime;
};
