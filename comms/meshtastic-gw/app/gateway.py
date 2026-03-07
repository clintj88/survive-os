"""Meshtastic radio connection manager."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .database import execute, query

logger = logging.getLogger("meshtastic-gw.gateway")

# Meshtastic library is optional at import time for testing
try:
    import meshtastic
    import meshtastic.serial_interface
    import meshtastic.ble_interface
    from pubsub import pub
    HAS_MESHTASTIC = True
except ImportError:
    HAS_MESHTASTIC = False


class MeshtasticGateway:
    """Manages connection to a Meshtastic radio and message routing."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.interface: Any = None
        self.connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._on_message_callback: Optional[Any] = None

    async def connect(self) -> bool:
        """Connect to the Meshtastic radio."""
        if not HAS_MESHTASTIC:
            logger.warning("meshtastic library not installed, running in stub mode")
            return False

        try:
            conn_type = self.config["radio"]["connection"]
            if conn_type == "serial":
                self.interface = meshtastic.serial_interface.SerialInterface(
                    devPath=self.config["radio"]["serial_port"]
                )
            elif conn_type == "ble":
                self.interface = meshtastic.ble_interface.BLEInterface(
                    address=self.config["radio"]["ble_address"]
                )
            else:
                logger.error("Unknown connection type: %s", conn_type)
                return False

            pub.subscribe(self._on_receive, "meshtastic.receive")
            pub.subscribe(self._on_connection, "meshtastic.connection.established")
            pub.subscribe(self._on_disconnect, "meshtastic.connection.lost")

            self.connected = True
            logger.info("Connected to Meshtastic radio via %s", conn_type)
            return True
        except Exception:
            logger.exception("Failed to connect to Meshtastic radio")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the Meshtastic radio."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self.interface:
            try:
                self.interface.close()
            except Exception:
                logger.exception("Error closing interface")
        self.connected = False
        logger.info("Disconnected from Meshtastic radio")

    def set_message_callback(self, callback: Any) -> None:
        """Set callback for incoming messages."""
        self._on_message_callback = callback

    def _on_receive(self, packet: dict, interface: Any = None) -> None:
        """Handle incoming mesh packet."""
        try:
            decoded = packet.get("decoded", {})
            if decoded.get("portnum") != "TEXT_MESSAGE_APP":
                return

            msg = {
                "sender": packet.get("fromId", ""),
                "recipient": packet.get("toId", "^all"),
                "content": decoded.get("text", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": packet.get("channel", 0),
                "mesh_id": str(packet.get("id", "")),
            }

            execute(
                """INSERT INTO messages (sender, recipient, content, timestamp, channel, mesh_id, direction)
                   VALUES (?, ?, ?, ?, ?, ?, 'rx')""",
                (msg["sender"], msg["recipient"], msg["content"],
                 msg["timestamp"], msg["channel"], msg["mesh_id"]),
            )

            # Update node info
            from_id = packet.get("fromId", "")
            if from_id:
                snr = packet.get("rxSnr", 0)
                existing = query("SELECT id FROM radios WHERE node_id = ?", (from_id,))
                if existing:
                    execute(
                        "UPDATE radios SET snr = ?, last_seen = ? WHERE node_id = ?",
                        (snr, msg["timestamp"], from_id),
                    )

            if self._on_message_callback:
                self._on_message_callback(msg)

        except Exception:
            logger.exception("Error processing received packet")

    def _on_connection(self, interface: Any = None, topic: Any = None) -> None:
        """Handle connection established."""
        self.connected = True
        logger.info("Meshtastic connection established")

    def _on_disconnect(self, interface: Any = None, topic: Any = None) -> None:
        """Handle connection lost - trigger reconnect."""
        self.connected = False
        logger.warning("Meshtastic connection lost, will attempt reconnect")

    async def send_message(self, text: str, destination: str = "^all", channel: int = 0) -> bool:
        """Send a text message over the mesh."""
        if not self.connected or not self.interface:
            logger.warning("Cannot send message - not connected")
            return False

        try:
            self.interface.sendText(text, destinationId=destination, channelIndex=channel)

            execute(
                """INSERT INTO messages (sender, recipient, content, timestamp, channel, direction)
                   VALUES ('local', ?, ?, ?, ?, 'tx')""",
                (destination, text, datetime.now(timezone.utc).isoformat(), channel),
            )
            return True
        except Exception:
            logger.exception("Failed to send message")
            return False

    def get_node_list(self) -> list[dict[str, Any]]:
        """Get list of known nodes from the radio."""
        if not self.connected or not self.interface:
            return []

        nodes = []
        try:
            node_db = self.interface.nodes or {}
            for node_id, node in node_db.items():
                user = node.get("user", {})
                position = node.get("position", {})
                metrics = node.get("deviceMetrics", {})
                nodes.append({
                    "node_id": node_id,
                    "long_name": user.get("longName", ""),
                    "short_name": user.get("shortName", ""),
                    "hw_model": user.get("hwModel", ""),
                    "battery_level": metrics.get("batteryLevel", 0),
                    "snr": node.get("snr", 0),
                    "last_seen": node.get("lastHeard", ""),
                    "latitude": position.get("latitude"),
                    "longitude": position.get("longitude"),
                    "altitude": position.get("altitude"),
                })
        except Exception:
            logger.exception("Error getting node list")
        return nodes

    def get_channels(self) -> list[dict[str, Any]]:
        """Get channel configuration from the radio."""
        if not self.connected or not self.interface:
            return []

        channels = []
        try:
            for ch in self.interface.localNode.channels or []:
                if ch.role != 0:  # Skip disabled channels
                    channels.append({
                        "index": ch.index,
                        "name": ch.settings.name if ch.settings else "",
                        "role": str(ch.role),
                    })
        except Exception:
            logger.exception("Error getting channels")
        return channels

    async def auto_reconnect(self, interval: int = 30) -> None:
        """Periodically attempt reconnection if disconnected."""
        while True:
            await asyncio.sleep(interval)
            if not self.connected:
                logger.info("Attempting reconnection...")
                await self.connect()
