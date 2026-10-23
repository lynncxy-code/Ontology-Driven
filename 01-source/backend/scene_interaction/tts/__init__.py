"""TTS provider factory for route narration."""

import os

from .alibaba import AlibabaISITTSProvider
from .base import TTSProvider, TTSProviderError


def configured_provider():
    provider_id = (os.environ.get("ONTOTWIN_TTS_PROVIDER") or "alibaba").strip().lower()
    if provider_id in {"alibaba", "alibaba.isi.standard"}:
        return AlibabaISITTSProvider.from_environment()
    return TTSProviderError.unconfigured(provider_id)


__all__ = [
    "AlibabaISITTSProvider",
    "TTSProvider",
    "TTSProviderError",
    "configured_provider",
]
