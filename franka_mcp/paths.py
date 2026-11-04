"""Project locations. ROOT is the Franka_Arm_MCP folder, the parent of this package."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"  # this lab's robot address, certificate pin, connection mode (local, Git-ignored)
CONFIG_EXAMPLE_PATH = ROOT / "config.example.json"  # committed template for config.json
CERT_PATH = ROOT / "robot-cert.pem"  # reference copy of the robot certificate (local only)
SESSION_PATH = ROOT / ".session.json"  # Desk login token (secret, never committed)
POLICY_PATH = ROOT / "task-policy.json"  # enabled tasks, default workflow, required Ready Home (local, Git-ignored)
POLICY_EXAMPLE_PATH = ROOT / "task-policy.example.json"  # committed template for task-policy.json
PLANS_DIR = ROOT / "plans"  # checked task data (local only)
