import os
from ontotwin_mcp import config


def test_defaults(monkeypatch):
    for k in ("NEXUS_BASE_URL", "NEXUS_TIMEOUT_READ", "NEXUS_ALLOWED_ROOTS"):
        monkeypatch.delenv(k, raising=False)
    s = config.load()
    assert s.base_url == "http://192.168.88.66:5000"
    assert s.timeout_read == 30.0
    assert s.allowed_roots == []


def test_env_override(monkeypatch):
    monkeypatch.setenv("NEXUS_BASE_URL", "http://127.0.0.1:5000")
    monkeypatch.setenv("NEXUS_TIMEOUT_READ", "5")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", "/data;/tmp/up")
    s = config.load()
    assert s.base_url == "http://127.0.0.1:5000"
    assert s.timeout_read == 5.0
    assert s.allowed_roots == ["/data", "/tmp/up"]


def test_trust_env_default_false(monkeypatch):
    monkeypatch.delenv("NEXUS_TRUST_ENV", raising=False)
    s = config.load()
    assert s.trust_env is False


def test_trust_env_opt_in(monkeypatch):
    monkeypatch.setenv("NEXUS_TRUST_ENV", "1")
    assert config.load().trust_env is True
    monkeypatch.setenv("NEXUS_TRUST_ENV", "true")
    assert config.load().trust_env is True
    monkeypatch.setenv("NEXUS_TRUST_ENV", "0")
    assert config.load().trust_env is False
