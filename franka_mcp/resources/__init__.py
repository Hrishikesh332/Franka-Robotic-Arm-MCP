"""MCP resources: read-only documentation an agent can fetch. None of them touches the robot."""

from __future__ import annotations

from franka_mcp.paths import ROOT

# uri -> (file in the project root, resource name, description)
DOCS = {
    "franka://docs/connection": (
        "CONNECTION.md",
        "connection-guide",
        "How this MCP reaches the robot (direct Ethernet or the Raspberry Pi tunnel) and what each connection error means.",
    ),
    "franka://docs/workflow-rules": (
        "AGENTS.md",
        "workflow-rules",
        "Workflow defaults: Franka Ready Home, the default workflow and the pre-execution checks.",
    ),
}


def _reader(filename: str):
    def read() -> str:
        try:
            return (ROOT / filename).read_text()
        except OSError:
            return f"{filename} is not available in this installation."

    return read


def register_all(mcp):
    for uri, (filename, name, description) in DOCS.items():
        mcp.resource(uri, name=name, description=description, mime_type="text/markdown")(_reader(filename))
