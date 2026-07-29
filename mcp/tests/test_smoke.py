"""只读集成冒烟：默认 skip，仅 NEXUS_SMOKE=1 且后端可达时才跑。

打真 `NexusClient(load())` 的 GET /api/v2/instances，断言返回 list。
无 env 时整文件 skip，不依赖真后端，故不影响常规 `pytest`。
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("NEXUS_SMOKE") != "1",
    reason="需 NEXUS_SMOKE=1 + 可达后端",
)


def test_smoke_readonly_list_instances():
    from ontotwin_mcp.config import load
    from ontotwin_mcp.client import NexusClient

    c = NexusClient(load())
    assert isinstance(c.get("list_instances", "/api/v2/instances"), list)
