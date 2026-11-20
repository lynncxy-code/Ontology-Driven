#pragma once
#include "CoreMinimal.h"
class ATwinSceneManager;
class SWidget;
TSharedRef<SWidget> MakeNumericTransformPanel(TFunction<ATwinSceneManager*()> GetManager);
