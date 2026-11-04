"""MCP prompts: ready-made instructions for the common checks. They only describe steps; nothing runs."""

from __future__ import annotations

import json

from franka_mcp.config import connection_mode, load_config
from franka_mcp.paths import POLICY_PATH

_FALLBACK_HOME = {
    "joint_angles_deg": [0, -45, 0, -135, 0, 90, 45],
    "position_tolerance_m": 0.005,
    "orientation_tolerance_deg": 1,
    "each_joint_tolerance_deg": 1,
}


def _required_home() -> dict:
    try:
        return {**_FALLBACK_HOME, **json.loads(POLICY_PATH.read_text()).get("required_home", {})}
    except (OSError, ValueError, AttributeError):
        return _FALLBACK_HOME


def preflight(task_id: str) -> str:
    home = _required_home()
    return (
        f"Prepare to run the Franka task '{task_id}'. Do NOT start it; report the result of every check.\n"
        "1. franka_real_capabilities: authenticated is true, task_execution_latched is false; note the connection mode.\n"
        "2. franka_real_robot_state: compare the measured joints with Ready Home "
        f"{home['joint_angles_deg']} deg (each within {home['each_joint_tolerance_deg']} deg), the flange position "
        f"(within {home['position_tolerance_m'] * 1000:g} mm) and orientation (within {home['orientation_tolerance_deg']} deg). "
        "There must be no robot errors and closeToSingularity must be false.\n"
        "3. franka_real_safety_status and franka_real_joint_brakes: no recovery condition, self-tests OK, all seven brakes unlocked.\n"
        f"4. franka_real_preview_task('{task_id}'): show the task name, its SHA-256 and enabled_locally.\n"
        "5. Stop and ask the user to confirm. Only then call franka_real_take_control and franka_real_execute_task "
        "with the previewed hash as expected_task_sha256.\n"
        "Never force control takeover, clear safety errors, or move the robot just to test something."
    )


def connection_help() -> str:
    try:
        mode = connection_mode(load_config())
    except (RuntimeError, ValueError):
        mode = "unknown (config.json is missing or invalid)"
    return (
        f"The configured connection mode is: {mode}.\n"
        "Read the resource franka://docs/connection, then call franka_real_capabilities and report the mode and "
        "whether a Desk login exists. If a tool failed, map its error message to the table in that guide and tell the "
        "user exactly which launcher to run (tunnel, then login). Never ask for or type a password."
    )


def register_all(mcp):
    mcp.prompt(name="franka_preflight", description="Checklist to run before executing a taught task; starts nothing.")(
        preflight
    )
    mcp.prompt(name="franka_connection_help", description="Diagnose how this machine reaches the robot.")(
        connection_help
    )
