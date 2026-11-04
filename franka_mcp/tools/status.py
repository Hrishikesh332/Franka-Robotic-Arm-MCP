"""Read-only observation: system, brakes, safety, measured robot state, events, capabilities."""

from __future__ import annotations

import json
import platform
from typing import Any

import anyio

from franka_mcp.config import connection_mode
from franka_mcp.desk.client import POLICY, STOPPED
from franka_mcp.desk.reader import make_reader
from franka_mcp.tools._common import READ_ANNOTATIONS, read_group, web_client


async def franka_real_observe() -> dict[str, Any]:
    """Read fresh physical robot system, arm type, operating mode, FCI and warnings. No motion or control acquisition."""
    return await anyio.to_thread.run_sync(
        read_group, {"system": "/api/system", "arm": "/api/arm", "fci": "/api/fci", "arm_warnings": "/api/arm/warnings"}
    )


async def franka_real_joint_brakes() -> dict[str, Any]:
    """Read the seven physical joint BRAKE states. This endpoint does not report joint angles or tool pose."""
    return await anyio.to_thread.run_sync(read_group, {"joint_brakes": "/api/arm/joints"})


async def franka_real_safety_status() -> dict[str, Any]:
    """Read recovery indications and periodic self-test status. Does not clear errors or execute tests."""
    return await anyio.to_thread.run_sync(
        read_group, {"recovery": "/api/safety/recovery", "self_tests": "/api/safety/self-tests"}
    )


def franka_real_capabilities() -> dict[str, Any]:
    """Describe this connector's capabilities and the requirements for later physical motion. Local configuration only."""
    reader = make_reader()
    try:
        web_client().session()
        authenticated = True
    except RuntimeError:
        authenticated = False
    # task-policy.json is local; without it nothing is enabled (fails closed). `bash setup.sh` creates it.
    task_policy = json.loads(POLICY.read_text()) if POLICY.exists() else {}
    approved = task_policy.get("approved_tasks", {})
    return {
        "robot_host": reader.host,
        "connection": connection_mode(reader.config),
        "desk_url": f"https://{reader.host}/desk/",
        "api_reference": f"https://{reader.host}/deskapi/",
        "host_platform": platform.system(),
        "read_only": False,
        "authenticated": authenticated,
        "physical_task_execution_configured": authenticated and bool(approved),
        "enabled_task_ids": sorted(approved),
        "default_workflow": task_policy.get("default_workflow"),
        "required_home": task_policy.get("required_home"),
        "task_execution_latched": STOPPED.is_set(),
        "raw_password_stored": False,
        "tls_authentication": "pinned SHA-256 of the robot certificate",
        "robot_state_is_live": False,
        "available": [
            "system status",
            "arm identity",
            "FCI status",
            "brake status",
            "warnings",
            "safety status",
            "measured joint angles and Cartesian pose",
            "configured end-effector profile",
            "taught task listing/preview/start/stop",
            "control token acquisition/release",
            "brake lock/unlock",
        ],
        "not_available": [
            "arbitrary joint/Cartesian targets",
            "table geometry",
            "camera",
            "direct gripper commands",
            "safety reset",
            "FCI activation",
        ],
        "motion_path": "Chat -> franka-real MCP -> Desk HTTPS task API -> robot's onboard task controller",
    }


async def franka_real_robot_state() -> dict[str, Any]:
    """Read fresh physical joint angles, Cartesian pose, estimated forces, robot errors and configured tool profile. No table map or physical tool validation is supplied."""
    return await anyio.to_thread.run_sync(web_client().robot_state)


async def franka_real_diagnostic_events() -> dict[str, Any]:
    """Read and preserve the documented event log and return recent singularity/IK/motion-planning entries. No motion, control takeover, error acknowledgement or recovery."""
    return await anyio.to_thread.run_sync(web_client().diagnostic_events)


READ_TOOLS = (
    franka_real_observe,
    franka_real_joint_brakes,
    franka_real_safety_status,
    franka_real_capabilities,
    franka_real_robot_state,
    franka_real_diagnostic_events,
)
CONTROL_TOOLS = ()


def register(mcp):
    for tool in READ_TOOLS:
        mcp.tool(annotations=READ_ANNOTATIONS)(tool)
