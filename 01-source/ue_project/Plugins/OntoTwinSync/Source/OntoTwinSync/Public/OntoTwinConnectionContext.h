#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "Interfaces/IHttpRequest.h"
#include "Misc/ConfigCacheIni.h"

// Optional deployment settings in DefaultGame.ini. No customer identity is compiled in.
namespace OntoTwinConnectionContext
{
inline FString Setting(const TCHAR* Key, const FString& Fallback = FString())
{
    FString Value;
    if (GConfig && GConfig->GetString(TEXT("OntoTwin.Connection"), Key, Value, GGameIni))
    {
        Value.TrimStartAndEndInline();
        if (!Value.IsEmpty()) return Value;
    }
    return Fallback;
}

inline bool IsExplicit()
{
    return !Setting(TEXT("ProjectId")).IsEmpty();
}

inline void Apply(TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request, const UWorld* World)
{
    const FString ProjectId = Setting(TEXT("ProjectId"));
    if (ProjectId.IsEmpty()) return;
    Request->SetHeader(TEXT("X-OntoTwin-Project-Id"), ProjectId);
    const FString UEProjectId = Setting(TEXT("UEProjectId"));
    if (!UEProjectId.IsEmpty()) Request->SetHeader(TEXT("X-OntoTwin-UE-Project-Id"), UEProjectId);
    // Use the actual level; a different level must not borrow this level's binding.
    if (World)
    {
        FString SceneKey = World->GetOutermost()->GetName();
        if (!World->StreamingLevelsPrefix.IsEmpty())
        {
            SceneKey.ReplaceInline(*World->StreamingLevelsPrefix, TEXT(""));
        }
        Request->SetHeader(TEXT("X-OntoTwin-UE-Scene-Id"), SceneKey);
        Request->SetHeader(TEXT("X-OntoTwin-UE-Context"),
            World->WorldType == EWorldType::PIE ? TEXT("pie") :
            (World->WorldType == EWorldType::Editor ? TEXT("editor") : TEXT("runtime")));
    }
}
}
