"""FastMCP server 装配 + stdio 入口。"""

from mcp.server.fastmcp import FastMCP

from . import config
from .client import NexusClient
from .tools import register_all


def build_server(client=None) -> FastMCP:
    mcp = FastMCP("ontotwin")
    if client is None:
        client = NexusClient(config.load())
    register_all(mcp, client)
    return mcp


def main():
    build_server().run()  # 默认 stdio


if __name__ == "__main__":
    main()
