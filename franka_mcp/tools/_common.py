"""Shared helpers for the tool modules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mcp.types import ToolAnnotations

from franka_mcp.desk.client import DeskWebClient
from franka_mcp.desk.reader import make_reader

READ_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
CONTROL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True
)


def read_group(paths: dict[str, str]) -> dict[str, Any]:
    reader = make_reader()
    started = datetime.now(timezone.utc).isoformat()
    data = {name: reader.get(path) for name, path in paths.items()}
    return {
        "source": "physical_franka_desk_api",
        "robot_host": reader.host,
        "read_only": True,
        "read_started_at_utc": started,
        "read_finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_is_atomic": False,
        **data,
    }


def web_client():
    return DeskWebClient(make_reader())
