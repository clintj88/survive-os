"""JS8Call API integration for HF keyboard messaging."""

import json
import logging
import socket
from typing import Any

logger = logging.getLogger("survive-ham-radio.js8call")


class JS8CallClient:
    """Interface with JS8Call via its TCP API on port 2442."""

    def __init__(self, host: str = "127.0.0.1", port: int = 2442) -> None:
        self.host = host
        self.port = port

    def _send_command(self, command: dict[str, Any], timeout: float = 5.0) -> dict[str, Any] | None:
        """Send a command to JS8Call and return the response."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.host, self.port))
            payload = json.dumps(command) + "\n"
            sock.sendall(payload.encode("utf-8"))
            response = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if b"\n" in chunk:
                        break
                except socket.timeout:
                    break
            sock.close()
            if response:
                return json.loads(response.decode("utf-8").strip())
            return None
        except (ConnectionRefusedError, OSError) as e:
            logger.warning("Cannot connect to JS8Call at %s:%d: %s", self.host, self.port, e)
            return None
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from JS8Call")
            return None

    def send_message(self, to_call: str, message: str) -> bool:
        """Send a directed message to a specific callsign."""
        command = {
            "type": "TX.SEND_MESSAGE",
            "value": f"{to_call}: {message}",
        }
        result = self._send_command(command)
        return result is not None

    def get_call_activity(self) -> list[dict[str, Any]]:
        """Get recent call activity from JS8Call."""
        command = {"type": "RX.GET_CALL_ACTIVITY", "value": ""}
        result = self._send_command(command)
        if result and isinstance(result.get("value"), dict):
            return [
                {"callsign": k, **v}
                for k, v in result["value"].items()
            ]
        return []

    def get_band_activity(self) -> list[dict[str, Any]]:
        """Get recent band activity from JS8Call."""
        command = {"type": "RX.GET_BAND_ACTIVITY", "value": ""}
        result = self._send_command(command)
        if result and isinstance(result.get("value"), list):
            return result["value"]
        return []

    def get_station_info(self) -> dict[str, Any]:
        """Get the local station callsign and grid."""
        command = {"type": "STATION.GET_CALLSIGN", "value": ""}
        result = self._send_command(command)
        return result if result else {}

    def is_connected(self) -> bool:
        """Check if JS8Call is reachable."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((self.host, self.port))
            sock.close()
            return True
        except (ConnectionRefusedError, OSError):
            return False
