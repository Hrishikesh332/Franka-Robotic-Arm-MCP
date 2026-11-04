"""Control: ownership of the control token, brakes, task execution, stop/resume, workflow speed."""

from __future__ import annotations

from typing import Any

import anyio

from franka_mcp.tools._common import CONTROL_ANNOTATIONS, web_client


async def franka_real_take_control() -> dict[str, Any]:
    """Request robot control without moving it. Fails if another session owns control; never forces takeover."""
    return await anyio.to_thread.run_sync(web_client().take_control)


async def franka_real_release_control() -> dict[str, Any]:
    """Release the control token owned by this MCP. Does not execute motion."""
    return await anyio.to_thread.run_sync(web_client().release_control)


async def franka_real_unlock_brakes() -> dict[str, Any]:
    """Unlock physical arm brakes only on the user's request, then read measured brake status. Requires local login and owned control."""
    return await anyio.to_thread.run_sync(web_client().brakes, True)


async def franka_real_lock_brakes() -> dict[str, Any]:
    """Request physical arm brake locking, then read measured brake status. Requires local login and owned control."""
    return await anyio.to_thread.run_sync(web_client().brakes, False)


async def franka_real_execute_task(task_id: str, expected_task_sha256: str) -> dict[str, Any]:
    """Start an explicitly requested taught task on the PHYSICAL arm. Requires local task enablement, matching preview hash, login, control and robot readiness. The robot may MOVE. Does not claim completion."""
    return await anyio.to_thread.run_sync(web_client().execute, task_id, expected_task_sha256)


async def franka_real_stop() -> dict[str, Any]:
    """Stop Desk task execution and latch new MCP task starts. Software task stop only; the physical emergency stop remains independent."""
    return await anyio.to_thread.run_sync(web_client().stop)


async def franka_real_resume() -> dict[str, Any]:
    """Explicitly clear this MCP's task-stop latch. Never restarts or replays an interrupted task."""
    return await anyio.to_thread.run_sync(web_client().resume)


async def franka_real_set_workflow_speed(percent: float) -> dict[str, Any]:
    """Set the user-created table-transfer workflow's saved speed to 1–40 percent while stopped. Preserves waypoints and per-app speed settings, verifies read-back, and never restarts the arm."""
    return await anyio.to_thread.run_sync(web_client().set_workflow_speed, percent)


READ_TOOLS = ()
CONTROL_TOOLS = (
    franka_real_take_control,
    franka_real_release_control,
    franka_real_unlock_brakes,
    franka_real_lock_brakes,
    franka_real_execute_task,
    franka_real_stop,
    franka_real_resume,
    franka_real_set_workflow_speed,
)


def register(mcp):
    for tool in CONTROL_TOOLS:
        mcp.tool(annotations=CONTROL_ANNOTATIONS)(tool)
