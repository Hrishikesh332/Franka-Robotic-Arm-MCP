"""Certificate-pinned connections to Desk, and the choice between them.

DeskReader     connects to robot_host:443 (the machine is on the robot's network).
TunnelDeskReader  connects to the local SSH tunnel (127.0.0.1) that leads to the robot via the Raspberry Pi.
Both check the robot's SHA-256 certificate pin before any HTTP request.
"""

from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import ssl
from typing import Any

from franka_mcp.config import connection_mode, load_config, robot_settings, tunnel_settings

READ_PATHS = frozenset(
    {
        "/api/system",
        "/api/arm",
        "/api/arm/joints",
        "/api/fci",
        "/api/arm/warnings",
        "/api/safety/recovery",
        "/api/safety/self-tests",
        "/api/system/control-token",
    }
)
MAX_RESPONSE_BYTES = 262144


class DeskReader:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config if config is not None else load_config()
        self.host, self.pin, self.timeout = robot_settings(self.config)

    def pinned_connection(self):
        # Trust the exact certificate captured from the user's robot, including
        # self-signed certificates. Check its DER hash BEFORE any HTTP request.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connection = http.client.HTTPSConnection(self.host, port=443, timeout=self.timeout, context=context)
        try:
            connection.connect()
            actual = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
            if not hmac.compare_digest(actual, self.pin):
                raise RuntimeError("Robot TLS certificate changed; verify the robot before updating the local pin")
            return connection
        except Exception:
            connection.close()
            raise

    def get(self, path: str) -> dict[str, Any] | list[Any]:
        if path not in READ_PATHS:
            raise ValueError("Only the fixed read-only Desk endpoints are permitted")
        connection = self.pinned_connection()
        try:
            connection.request("GET", path, headers={"Accept": "application/json"})
            response = connection.getresponse()
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise RuntimeError("Desk response exceeded the size limit")
            if response.status != 200:
                raise RuntimeError(f"Desk GET {path} returned HTTP {response.status}; no robot changes were made")
            if response.getheader("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                raise RuntimeError("Desk returned a non-JSON response")
            result = json.loads(body)
            if not isinstance(result, (dict, list)):
                raise RuntimeError("Unexpected Desk response shape")
            return result
        except (OSError, http.client.HTTPException) as exc:
            raise RuntimeError(
                f"Robot read failed at {self.host}: {type(exc).__name__}; check Ethernet and local network access"
            ) from None
        finally:
            connection.close()


class TunnelDeskReader(DeskReader):
    """Use the local Desk tunnel (127.0.0.1, port from config.json) while preserving the robot identity pin."""

    def __init__(self, config=None):
        super().__init__(config)
        self.tunnel_port = tunnel_settings(self.config)["local_port"]

    def pinned_connection(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connection = http.client.HTTPSConnection(
            "127.0.0.1", port=self.tunnel_port, timeout=self.timeout, context=context
        )
        try:
            connection.connect()
            actual = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
            if not hmac.compare_digest(actual, self.pin):
                raise RuntimeError("Desk tunnel presented a different robot certificate")
            return connection
        except OSError as exc:
            connection.close()
            raise RuntimeError(
                f"Could not open the Desk tunnel at 127.0.0.1:{self.tunnel_port} ({type(exc).__name__}). "
                "Start 'Connect Desk over WiFi.command' and keep its window open"
            ) from None
        except Exception:
            connection.close()
            raise


def make_reader(config: dict[str, Any] | None = None) -> DeskReader:
    """Reader for the configured connection mode (config.json "connection").

    "direct" -> robot_host:443.  "tunnel" -> the local SSH tunnel to the robot via the
    Raspberry Pi. Both check the robot's certificate pin before any request.
    """
    config = config if config is not None else load_config()
    if connection_mode(config) == "tunnel":
        return TunnelDeskReader(config)
    return DeskReader(config)
