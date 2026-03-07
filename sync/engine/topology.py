"""Sync topology manager — hub-spoke within community, gateway between."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NodeRole(str, Enum):
    HUB = "hub"
    SPOKE = "spoke"
    GATEWAY = "gateway"


@dataclass
class SyncState:
    """Tracks sync progress with a specific peer."""
    peer_id: str
    last_sync: float = 0.0
    last_vector_clock: dict[str, int] = field(default_factory=dict)
    sync_count: int = 0
    errors: int = 0
    last_error: str = ""


class TopologyManager:
    """Manages the sync topology for a community.

    Hub-spoke model:
    - Hub coordinates sync for all spokes in a community
    - Spokes sync only with the hub
    - Gateways connect communities (sync with their hub + remote hubs)
    """

    def __init__(
        self,
        node_id: str,
        role: NodeRole = NodeRole.SPOKE,
        community: str = "default",
    ) -> None:
        self.node_id = node_id
        self.role = role
        self.community = community
        self._sync_states: dict[str, SyncState] = {}

    def should_sync_with(self, peer_id: str, peer_role: str, peer_community: str) -> bool:
        """Determine if this node should sync with a given peer."""
        if self.role == NodeRole.HUB:
            # Hub syncs with all spokes and gateways in its community
            if peer_community == self.community:
                return True
            # Hub also syncs with gateways from other communities
            return peer_role == NodeRole.GATEWAY.value

        if self.role == NodeRole.SPOKE:
            # Spoke only syncs with its community's hub
            return peer_role == NodeRole.HUB.value and peer_community == self.community

        if self.role == NodeRole.GATEWAY:
            # Gateway syncs with own hub + remote hubs
            if peer_community == self.community and peer_role == NodeRole.HUB.value:
                return True
            if peer_community != self.community and peer_role in (
                NodeRole.HUB.value, NodeRole.GATEWAY.value
            ):
                return True

        return False

    def get_sync_state(self, peer_id: str) -> SyncState:
        if peer_id not in self._sync_states:
            self._sync_states[peer_id] = SyncState(peer_id=peer_id)
        return self._sync_states[peer_id]

    def record_sync(self, peer_id: str, vector_clock: dict[str, int]) -> None:
        state = self.get_sync_state(peer_id)
        state.last_sync = time.time()
        state.last_vector_clock = vector_clock.copy()
        state.sync_count += 1

    def record_error(self, peer_id: str, error: str) -> None:
        state = self.get_sync_state(peer_id)
        state.errors += 1
        state.last_error = error

    def get_sync_summary(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "community": self.community,
            "peers": {
                pid: {
                    "last_sync": s.last_sync,
                    "sync_count": s.sync_count,
                    "errors": s.errors,
                    "last_error": s.last_error,
                }
                for pid, s in self._sync_states.items()
            },
        }
