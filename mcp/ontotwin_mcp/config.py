import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    base_url: str = "http://192.168.88.66:5000"
    timeout_connect: float = 5.0
    timeout_read: float = 30.0
    timeout_upload: float = 60.0
    timeout_cadparse: float = 120.0
    allowed_roots: list = field(default_factory=list)
    trust_env: bool = False


def _f(name, default):
    v = os.environ.get(name)
    return float(v) if v else default


def load() -> Settings:
    roots = os.environ.get("NEXUS_ALLOWED_ROOTS", "")
    return Settings(
        base_url=os.environ.get("NEXUS_BASE_URL", "http://192.168.88.66:5000").rstrip("/"),
        timeout_connect=_f("NEXUS_TIMEOUT_CONNECT", 5.0),
        timeout_read=_f("NEXUS_TIMEOUT_READ", 30.0),
        timeout_upload=_f("NEXUS_TIMEOUT_UPLOAD", 60.0),
        timeout_cadparse=_f("NEXUS_TIMEOUT_CADPARSE", 120.0),
        allowed_roots=[p for p in roots.split(";") if p],
        trust_env=os.environ.get("NEXUS_TRUST_ENV", "").lower() in ("1", "true", "yes"),
    )
