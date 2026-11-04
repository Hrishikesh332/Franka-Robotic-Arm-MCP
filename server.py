"""Entry point for MCP clients: `.venv/bin/python server.py` (stdio). The code lives in franka_mcp/.

This path stays stable because clients are registered with it. Options: `--probe`, `--transport`.
"""

from franka_mcp.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
