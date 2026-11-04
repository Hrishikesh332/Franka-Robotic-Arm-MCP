"""Read-only views of the taught Desk tasks and their execution status."""

from __future__ import annotations

from typing import Any

import anyio

from franka_mcp.tools._common import READ_ANNOTATIONS, web_client


async def franka_real_list_tasks() -> dict[str, Any]:
    """List existing taught Desk tasks/groups from the physical robot. Requires local Desk login."""
    return await anyio.to_thread.run_sync(web_client().list_tasks)


async def franka_real_preview_task(task_id: str) -> dict[str, Any]:
    """Read a saved task's actual payload, SHA-256 and local execution eligibility. No motion."""
    return await anyio.to_thread.run_sync(web_client().preview, task_id)


async def franka_real_task_status() -> dict[str, Any]:
    """Read fresh Desk execution status. Never infer grasp or task success from a start response."""
    result = await anyio.to_thread.run_sync(web_client().request, "GET", "/desk/api/execution")
    return {"execution": result, "source": "physical_franka_desk_web_api"}


READ_TOOLS = (
    franka_real_list_tasks,
    franka_real_preview_task,
    franka_real_task_status,
)
CONTROL_TOOLS = ()


def register(mcp):
    for tool in READ_TOOLS:
        mcp.tool(annotations=READ_ANNOTATIONS)(tool)
