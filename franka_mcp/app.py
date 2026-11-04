"""Builds the FastMCP application: instructions, tools, resources and prompts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from franka_mcp import prompts, resources, tools
from franka_mcp.config import load_config, robot_settings

SERVER_NAME = "franka-real"


def configured_host() -> str:
    """Robot address from config.json for the instructions text; never blocks server start-up."""
    try:
        return robot_settings(load_config())[0]
    except (RuntimeError, ValueError, KeyError):
        return "the address set in config.json"


def build_instructions() -> str:
    return (
        f"Connect to the PHYSICAL Franka FR3 at {configured_host()} through its Desk HTTPS APIs. "
        "Control tools require a local Desk login. Execute only an explicitly requested, locally enabled taught task; inspect it first. "
        "Do not move the robot merely to test this integration. Never force control takeover or clear safety errors. "
        "franka_real_joint_brakes describes brakes; franka_real_robot_state supplies measured joint angles and Cartesian pose. "
        "Always use Franka standard Ready Home, joint degrees [0,-45,0,-135,0,90,45], as workflow start and return. "
        "The current Home-to-Home workflow is chat_backward_x_from_franka_ready_v06 (0_move2dest8). "
        "Check all seven joints, position and complete flange orientation; the earlier workcell start is an intermediate pose. "
        "No table geometry or physical tool verification is available: do not infer safe clearances from TCP height alone. "
        "Never infer motion, a grasp, end-effector pose or hardware qualification from these reads. "
        "FCI motion needs a separately configured real-time Linux control workstation. "
        "The existing franka-sim MCP is a different robot in simulation."
    )


def create_server() -> FastMCP:
    mcp = FastMCP(SERVER_NAME, instructions=build_instructions())
    tools.register_all(mcp)
    resources.register_all(mcp)
    prompts.register_all(mcp)
    return mcp
