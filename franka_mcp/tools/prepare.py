"""Authoring: save checked task revisions into Desk. None of these enables, executes or moves anything."""

from __future__ import annotations

from typing import Any

import anyio

from franka_mcp.tools._common import CONTROL_ANNOTATIONS, web_client


async def franka_real_prepare_ground_relative_transfer() -> dict[str, Any]:
    """Save the checked Ground-relative revision: 150 mm virtual tool, 50 mm tip gap, source +180 deg, X-only transfer, -180 deg, lift and exact start return. Workflow speed 40%, per-app settings 5%. Does not change tool calibration, enable or run it."""
    return await anyio.to_thread.run_sync(web_client().prepare_ground_relative_transfer)


async def franka_real_prepare_ground_y_transfer() -> dict[str, Any]:
    """Save only the checked v02 revision: 100 mm virtual tool, 10 mm tip gap, +180 degree source rotation, +Y 100 mm, lift 50 mm, X-only transfer, descend, -180 degrees, lift and return. Workflow slider 70%, per-motion settings 5%. Does not enable, execute or change the physical TCP/load."""
    return await anyio.to_thread.run_sync(web_client().prepare_ground_y_transfer)


async def franka_real_prepare_no_rotation_transfer() -> dict[str, Any]:
    """Save only checked v03: remove both rotations, retain constant flange orientation and elbow joint 3, +Y 100 mm, lift, X transfer, descend, lift and return. Individual motion speed 50%, acceleration/deceleration 5%, workflow slider 70%. Never enable or execute motion."""
    return await anyio.to_thread.run_sync(web_client().prepare_no_rotation_transfer)


async def franka_real_prepare_no_rotation_speed30() -> dict[str, Any]:
    """Save only checked v04 with no rotations, fixed orientation/elbow, 30% component speeds, 5% acceleration/deceleration and the 70% workflow slider. Never enable or execute motion."""
    return await anyio.to_thread.run_sync(web_client().prepare_no_rotation_speed30)


async def franka_real_prepare_backwards_x_first() -> dict[str, Any]:
    """Save checked v05: source lift, backward base X 573 to 319 mm first, Y shift only at destination X, destination descent, lift and return. All component speeds 30%, workflow 70%, no rotations. Does not enable or execute motion."""
    return await anyio.to_thread.run_sync(web_client().prepare_backwards_x_first)


async def franka_real_prepare_home_tasks() -> dict[str, Any]:
    """Save standard Franka Ready Home as a separate native Joint Motion task and v06 backward-X workflow with explicit Home prerequisite, workcell transition and Home return. Components 30%. Does not enable, execute, clear singularity or change safety settings."""
    return await anyio.to_thread.run_sync(web_client().prepare_home_tasks)


async def franka_real_prepare_flange_inward_test() -> dict[str, Any]:
    """Save only checked 10 mm flange-local -Z inward free-space test and exact Ready Home return. Fixed orientation; component and workflow speeds 30%. Does not enable or start motion."""
    return await anyio.to_thread.run_sync(web_client().prepare_flange_inward_test)


async def franka_real_prepare_tomato_source_fix() -> dict[str, Any]:
    """Save only checked Pick & Place Tomato v2 - Source Approach Fix as a new task. Repairs pose/joint inconsistencies, uses native Joint Motion above source then vertical Cartesian descent, preserves taught targets and safety thresholds, exact Ready Home and 30% speeds. Never enable, run, acknowledge faults or change the original."""
    try:
        from franka_mcp.authoring.tomato_versioning import prepare_tomato_source_fix
    except ImportError:
        raise RuntimeError(
            "franka_mcp/authoring/tomato_versioning.py is not installed here (a local-only, one-off authoring helper); copy it from your packed bundle to use this tool"
        ) from None
    return await anyio.to_thread.run_sync(prepare_tomato_source_fix, web_client())


async def franka_real_prepare_table_transfer() -> dict[str, Any]:
    """Create the separately named, checked v04 bare-flange routine in Desk: Z>=225 mm, positive 180-degree rotation, X-only transfer, 5% speed settings. Does not enable or start it; checks original tasks remain unchanged."""
    return await anyio.to_thread.run_sync(web_client().prepare_table_transfer)


READ_TOOLS = ()
CONTROL_TOOLS = (
    franka_real_prepare_ground_relative_transfer,
    franka_real_prepare_ground_y_transfer,
    franka_real_prepare_no_rotation_transfer,
    franka_real_prepare_no_rotation_speed30,
    franka_real_prepare_backwards_x_first,
    franka_real_prepare_home_tasks,
    franka_real_prepare_flange_inward_test,
    franka_real_prepare_tomato_source_fix,
    franka_real_prepare_table_transfer,
)


def register(mcp):
    for tool in CONTROL_TOOLS:
        mcp.tool(annotations=CONTROL_ANNOTATIONS)(tool)
