// OntoTwinSync 插件模块入口。Renderer Spike 必须在首个 World 初始化前预留共享 Slate Postbuffer。

#include "Modules/ModuleManager.h"
#include "UI/OntoTwinGlassRenderer.h"

class FOntoTwinSyncModule final : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		// Slate creates configured processors during pre-world initialization, so reserve the slot now.
		FOntoTwinGlassRenderer::ConfigureSlatePostBuffer();
	}
};

IMPLEMENT_MODULE(FOntoTwinSyncModule, OntoTwinSync)
