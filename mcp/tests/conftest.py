import httpx
import pytest

from ontotwin_mcp.config import Settings
from ontotwin_mcp.client import NexusClient


@pytest.fixture
def make_client():
    def _make(handler):
        s = Settings(base_url="http://test")
        c = NexusClient(s, transport=httpx.MockTransport(handler))
        return c
    return _make
