"""Pat/Winlink client integration for email over radio."""

import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger("survive-ham-radio.pat")


class PatClient:
    """Interface with the Pat Winlink client CLI."""

    def __init__(self, binary_path: str, mycall: str) -> None:
        self.binary = binary_path
        self.mycall = mycall

    def _run(self, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
        """Run a pat command and return the result."""
        cmd = [self.binary] + args
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            logger.error("Pat binary not found at %s", self.binary)
            raise
        except subprocess.TimeoutExpired:
            logger.error("Pat command timed out: %s", " ".join(cmd))
            raise

    def compose(self, to: str, subject: str, body: str) -> bool:
        """Compose and queue a Winlink message for sending."""
        try:
            result = self._run([
                "compose",
                "--from", self.mycall,
                "--to", to,
                "--subject", subject,
                "--body", body,
            ])
            if result.returncode != 0:
                logger.error("Pat compose failed: %s", result.stderr)
                return False
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def send(self, transport: str = "telnet") -> bool:
        """Send queued messages via the specified transport."""
        try:
            result = self._run(["connect", transport], timeout=120)
            if result.returncode != 0:
                logger.error("Pat send failed: %s", result.stderr)
                return False
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_inbox(self) -> list[dict[str, Any]]:
        """List messages in the Pat inbox."""
        try:
            result = self._run(["inbox", "--json"])
            if result.returncode != 0:
                logger.error("Pat inbox list failed: %s", result.stderr)
                return []
            return json.loads(result.stdout) if result.stdout.strip() else []
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return []

    def read_message(self, message_id: str) -> dict[str, Any] | None:
        """Read a specific message from the inbox."""
        try:
            result = self._run(["read", message_id, "--json"])
            if result.returncode != 0:
                return None
            return json.loads(result.stdout) if result.stdout.strip() else None
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return None
