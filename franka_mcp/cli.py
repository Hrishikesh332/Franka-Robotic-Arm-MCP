"""Command line: run the server (stdio by default) or read the robot status once."""

from __future__ import annotations

import argparse
import json
import os
import sys

from franka_mcp import __version__
from franka_mcp.app import create_server
from franka_mcp.tools._common import read_group

PROBE_PATHS = {
    "system": "/api/system",
    "arm": "/api/arm",
    "fci": "/api/fci",
    "joint_brakes": "/api/arm/joints",
    "recovery": "/api/safety/recovery",
    "self_tests": "/api/safety/self-tests",
}
LOCAL_HOST = "127.0.0.1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="franka-mcp", description="MCP server for the physical Franka FR3's Desk API."
    )
    parser.add_argument("--version", action="version", version=f"franka-mcp {__version__}")
    parser.add_argument("--probe", action="store_true", help="Read current physical robot status once and exit")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="stdio (default, for MCP clients) or a local HTTP transport for the inspector",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("FRANKA_MCP_PORT", "3001")),
        help="Port for the HTTP transports (env FRANKA_MCP_PORT, default 3001)",
    )
    options = parser.parse_args(argv)
    if options.probe:
        print(json.dumps(read_group(PROBE_PATHS), indent=2))
        return 0
    mcp = create_server()
    if options.transport != "stdio":
        # The tools can move a physical robot and there is no authentication: loopback only.
        mcp.settings.host, mcp.settings.port = LOCAL_HOST, options.port
        print(
            f"franka-real listening on http://{LOCAL_HOST}:{options.port} ({options.transport}); "
            "no authentication, local use only",
            file=sys.stderr,
        )
    mcp.run(transport=options.transport)
    return 0
