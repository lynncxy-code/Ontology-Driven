#pragma once
#include "CoreMinimal.h"
class ATwinSceneManager;
class SWidget;
TSharedRef<SWidget> MakeLocalModelRefresh(TFunction<ATwinSceneManager*()> GetManager);
