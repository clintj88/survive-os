"""Peer discovery via mDNS and manual configuration."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Peer:
    """Represents a known sync peer."""
    peer_id: str
    host: str
    port: int
    role: str = "spoke"
    community: str = "default"
    name: str = ""
    online: bool = False
    last_seen: float = 0.0
    sync_lag: float = 0.0  # seconds behind

    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "host": self.host,
            "port": self.port,
            "role": self.role,
            "community": self.community,
            "name": self.name,
            "online": self.online,
            "last_seen": self.last_seen,
            "sync_lag": self.sync_lag,
        }


class PeerManager:
    """Manages peer discovery and tracking."""

    STALE_TIMEOUT = 120.0  # Mark peer offline after 2 minutes

    def __init__(self, node_id: str, mdns_name: str = "_survive-sync._tcp.local.") -> None:
        self.node_id = node_id
        self.mdns_name = mdns_name
        self._peers: dict[str, Peer] = {}
        self._mdns_browser: Any = None

    def add_static_peer(self, peer_id: str, host: str, port: int, **kwargs: Any) -> Peer:
        peer = Peer(peer_id=peer_id, host=host, port=port, **kwargs)
        peer.last_seen = time.time()
        self._peers[peer_id] = peer
        return peer

    def update_peer(self, peer_id: str, **kwargs: Any) -> Peer | None:
        peer = self._peers.get(peer_id)
        if not peer:
            return None
        for k, v in kwargs.items():
            if hasattr(peer, k):
                setattr(peer, k, v)
        peer.last_seen = time.time()
        peer.online = True
        return peer

    def mark_seen(self, peer_id: str) -> None:
        peer = self._peers.get(peer_id)
        if peer:
            peer.last_seen = time.time()
            peer.online = True

    def get_peer(self, peer_id: str) -> Peer | None:
        return self._peers.get(peer_id)

    def get_online_peers(self) -> list[Peer]:
        now = time.time()
        result = []
        for peer in self._peers.values():
            if now - peer.last_seen > self.STALE_TIMEOUT:
                peer.online = False
            if peer.online:
                result.append(peer)
        return result

    def get_all_peers(self) -> list[Peer]:
        return list(self._peers.values())

    def remove_peer(self, peer_id: str) -> bool:
        return self._peers.pop(peer_id, None) is not None

    async def start_mdns_discovery(self) -> None:
        """Start mDNS-based peer discovery."""
        try:
            from zeroconf import ServiceBrowser, Zeroconf
            from zeroconf import ServiceStateChange

            self._zeroconf = Zeroconf()

            def on_service_state_change(
                zeroconf: Zeroconf,
                service_type: str,
                name: str,
                state_change: ServiceStateChange,
            ) -> None:
                if state_change == ServiceStateChange.Added:
                    info = zeroconf.get_service_info(service_type, name)
                    if info and info.properties:
                        peer_id = info.properties.get(b"node_id", b"").decode()
                        if peer_id and peer_id != self.node_id:
                            host = info.parsed_addresses()[0] if info.parsed_addresses() else ""
                            if host:
                                self.add_static_peer(
                                    peer_id=peer_id,
                                    host=host,
                                    port=info.port or 8101,
                                    role=info.properties.get(b"role", b"spoke").decode(),
                                    community=info.properties.get(b"community", b"default").decode(),
                                    name=info.properties.get(b"name", b"").decode(),
                                )
                                logger.info("Discovered peer %s at %s:%d", peer_id, host, info.port)
                elif state_change == ServiceStateChange.Removed:
                    # Try to find and remove the peer
                    for pid, peer in list(self._peers.items()):
                        if name.startswith(pid[:8]):
                            peer.online = False
                            logger.info("Peer %s went offline", pid)

            self._mdns_browser = ServiceBrowser(
                self._zeroconf, self.mdns_name, handlers=[on_service_state_change]
            )
            logger.info("mDNS discovery started for %s", self.mdns_name)
        except ImportError:
            logger.warning("zeroconf not installed — mDNS discovery disabled")
        except Exception as e:
            logger.warning("mDNS discovery failed to start: %s", e)

    async def stop_mdns_discovery(self) -> None:
        if hasattr(self, "_zeroconf"):
            self._zeroconf.close()
