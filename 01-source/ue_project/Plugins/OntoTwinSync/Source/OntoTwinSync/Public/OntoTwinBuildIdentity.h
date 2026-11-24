#pragma once
#include "CoreMinimal.h"

// Identity compiled into the actually loaded runtime module.
ONTOTWINSYNC_API FString OntoTwinLoadedSourceHash();

// Platform version this plugin was installed as (NEW-13): read once from OntoTwinRelease.json
// beside the plugin, written by the installer. Empty when the plugin was not installed from a package.
ONTOTWINSYNC_API const FString& OntoTwinInstalledRelease();
