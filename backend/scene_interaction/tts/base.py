"""Provider-neutral TTS boundary. Providers return validated-format bytes only."""


class TTSProviderError(RuntimeError):
    def __init__(self, code, message, retryable=False):
        self.code = str(code or "tts_provider_failed")
        self.retryable = bool(retryable)
        super().__init__(message)

    @classmethod
    def unconfigured(cls, provider_id=""):
        return UnconfiguredTTSProvider(provider_id)


class TTSProvider:
    provider_id = "unknown"

    def voice_catalog(self):
        return []

    def readiness(self):
        raise NotImplementedError

    def synthesize(self, text, voice_profile):
        raise NotImplementedError


class UnconfiguredTTSProvider(TTSProvider):
    def __init__(self, provider_id=""):
        self.provider_id = provider_id or "unconfigured"

    def readiness(self):
        return {
            "provider_id": self.provider_id,
            "configured": False,
            "ready": False,
            "message": "语音服务尚未配置",
        }

    def synthesize(self, text, voice_profile):
        raise TTSProviderError("tts_provider_unconfigured", "语音服务尚未配置")
