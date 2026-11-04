"""Single source of truth for config.json: robot address, certificate pin, Desk tunnel.

config.json and task-policy.json describe one lab (addresses, approvals), so they are local and
Git-ignored. Only config.example.json and task-policy.example.json are committed.

Standard library only, so the launchers and setup.sh can run it with any python3:

    python3 -m franka_mcp.config init         # create the local files from the templates, fill the pin
    python3 -m franka_mcp.config get robot_host
    python3 -m franka_mcp.config get desk_tunnel.bridge_host
    python3 -m franka_mcp.config check        # validate config.json and the pin
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import shutil
import ssl
import sys
from pathlib import Path
from typing import Any

from franka_mcp.paths import CERT_PATH, CONFIG_EXAMPLE_PATH, CONFIG_PATH, POLICY_EXAMPLE_PATH, POLICY_PATH

# "direct": talk to robot_host:443 (machine is on the robot's network, e.g. Ethernet).
# "tunnel": talk to 127.0.0.1:<desk_tunnel.local_port>, an SSH tunnel to the robot via the Raspberry Pi.
CONNECTION_MODES = ("direct", "tunnel")

# Used when config.json has no "desk_tunnel" section (or omits a key).
TUNNEL_DEFAULTS: dict[str, Any] = {"bridge_host": "", "bridge_user": "pi", "local_port": 8443}


def load_config() -> dict[str, Any]:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except FileNotFoundError:
        raise RuntimeError(
            f"{CONFIG_PATH.name} is missing. Run `bash setup.sh` (or `python3 -m franka_mcp.config init`) "
            f"to create it from {CONFIG_EXAMPLE_PATH.name}"
        ) from None
    except ValueError as exc:
        raise RuntimeError(f"{CONFIG_PATH.name} is not valid JSON: {exc}") from None


def robot_settings(config: dict[str, Any]) -> tuple[str, str, float]:
    """Validated (host, certificate pin, timeout seconds). Raises ValueError/KeyError."""
    host = str(ipaddress.ip_address(config["robot_host"]))
    pin = config["certificate_sha256"]
    if len(pin) != 64 or any(c not in "0123456789abcdef" for c in pin):
        raise ValueError("A SHA-256 robot certificate pin is required")
    timeout = float(config.get("timeout_seconds", 5))
    if not 0 < timeout <= 10:
        raise ValueError("Timeout must be in (0, 10] seconds")
    return host, pin, timeout


def tunnel_settings(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Desk SSH-tunnel settings with defaults applied. The local end is always loopback."""
    config = load_config() if config is None else config
    tunnel = {**TUNNEL_DEFAULTS, **config.get("desk_tunnel", {})}
    port = tunnel["local_port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("desk_tunnel.local_port must be an integer from 1024 to 65535")
    return tunnel


def connection_mode(config: dict[str, Any] | None = None) -> str:
    """How this machine reaches Desk: "direct" (default) or "tunnel"."""
    config = load_config() if config is None else config
    mode = config.get("connection", "direct")
    if mode not in CONNECTION_MODES:
        raise ValueError('connection must be "direct" or "tunnel"')
    return mode


def pin_of_pem(path: Path | None = None) -> str:
    """SHA-256 of the DER certificate in a PEM file (default: robot-cert.pem), i.e. the value config.json pins."""
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert((path or CERT_PATH).read_text())).hexdigest()


def check() -> list[str]:
    """Return a list of problems; empty means config.json is usable."""
    problems: list[str] = []
    try:
        config = load_config()
        if not str(config.get("certificate_sha256", "")).strip():
            return [
                "certificate_sha256 is empty. Save the robot's certificate as robot-cert.pem, then run "
                "`python3 -m franka_mcp.config init` (SETUP.md section 6)"
            ]
        _, pin, _ = robot_settings(config)
        tunnel_settings(config)
        connection_mode(config)
    except (RuntimeError, ValueError, KeyError) as exc:
        return [f"config.json: {exc!r}" if isinstance(exc, KeyError) else f"config.json: {exc}"]
    if CERT_PATH.exists():
        try:
            if pin_of_pem() != pin:
                problems.append(
                    "certificate_sha256 does not match robot-cert.pem; verify the robot before changing either"
                )
        except (ValueError, OSError) as exc:
            problems.append(f"robot-cert.pem is unreadable: {exc}")
    return problems


def init() -> list[str]:
    """Create config.json and task-policy.json from the committed templates. Never overwrites a file.

    If robot-cert.pem exists and the pin is empty, the pin is filled in from the certificate, so the
    value you verify is the certificate file itself. Returns a message per action taken.
    """
    notes: list[str] = []
    for local, template in ((CONFIG_PATH, CONFIG_EXAMPLE_PATH), (POLICY_PATH, POLICY_EXAMPLE_PATH)):
        if local.exists():
            continue
        if not template.exists():
            raise RuntimeError(f"{template.name} is missing; restore it from the repository")
        shutil.copyfile(template, local)
        notes.append(f"created {local.name} from {template.name}")
    try:
        config = json.loads(CONFIG_PATH.read_text())
    except ValueError:
        return notes  # check() reports the invalid file
    if not str(config.get("certificate_sha256", "")).strip() and CERT_PATH.exists():
        try:
            config["certificate_sha256"] = pin_of_pem()
        except (ValueError, OSError) as exc:
            notes.append(f"{CERT_PATH.name} is unreadable, pin not set: {exc}")
        else:
            CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
            notes.append(f"set certificate_sha256 from {CERT_PATH.name}; confirm that file is your robot's certificate")
    return notes


def _lookup(path: str) -> Any:
    config = load_config()
    value: Any = {**config, "connection": connection_mode(config), "desk_tunnel": tunnel_settings(config)}
    for part in path.split("."):
        value = value[part]
    return value


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "get":
        try:
            print(_lookup(argv[2]))
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            print(f"cannot read {argv[2]!r} from config.json: {exc}", file=sys.stderr)
            return 1
        return 0
    if len(argv) == 2 and argv[1] == "init":
        try:
            notes = init()
        except RuntimeError as exc:
            print(f"init failed: {exc}", file=sys.stderr)
            return 1
        for note in notes or [f"{CONFIG_PATH.name} and {POLICY_PATH.name} already exist; nothing to create"]:
            print(note)
        return 0
    if len(argv) == 2 and argv[1] == "check":
        problems = check()
        for problem in problems:
            print("PROBLEM:", problem, file=sys.stderr)
        if not problems:
            print("config.json OK (robot address, certificate pin and tunnel settings are valid)")
        return 1 if problems else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
