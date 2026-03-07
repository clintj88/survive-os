"""Vector clock implementation for CRDT ordering.

Each record carries (node_id, sequence_number) pairs to track
causality across nodes in the mesh network.
"""

from __future__ import annotations

import json
from typing import Any


class VectorClock:
    """A vector clock mapping node_id -> sequence_number."""

    __slots__ = ("_clock",)

    def __init__(self, clock: dict[str, int] | None = None) -> None:
        self._clock: dict[str, int] = dict(clock) if clock else {}

    def increment(self, node_id: str) -> int:
        """Increment the sequence number for a node. Returns the new value."""
        self._clock[node_id] = self._clock.get(node_id, 0) + 1
        return self._clock[node_id]

    def get(self, node_id: str) -> int:
        """Get the sequence number for a node (0 if unseen)."""
        return self._clock.get(node_id, 0)

    def merge(self, other: VectorClock) -> VectorClock:
        """Return a new VectorClock with element-wise max of both clocks."""
        all_nodes = set(self._clock) | set(other._clock)
        merged = {n: max(self.get(n), other.get(n)) for n in all_nodes}
        return VectorClock(merged)

    def __le__(self, other: VectorClock) -> bool:
        """True if self is causally before or equal to other (self <= other)."""
        for node_id, seq in self._clock.items():
            if seq > other.get(node_id):
                return False
        return True

    def __lt__(self, other: VectorClock) -> bool:
        """True if self is strictly causally before other."""
        return self <= other and self != other

    def __ge__(self, other: VectorClock) -> bool:
        return other <= self

    def __gt__(self, other: VectorClock) -> bool:
        return other < self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorClock):
            return NotImplemented
        all_nodes = set(self._clock) | set(other._clock)
        return all(self.get(n) == other.get(n) for n in all_nodes)

    def is_concurrent(self, other: VectorClock) -> bool:
        """True if neither clock causally dominates the other."""
        return not (self <= other) and not (other <= self)

    def to_dict(self) -> dict[str, int]:
        """Serialize to a plain dict."""
        return dict(self._clock)

    def to_json(self) -> str:
        """Serialize to a JSON string for database storage."""
        return json.dumps(self._clock, sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> VectorClock:
        """Deserialize from a JSON string."""
        return cls(json.loads(data))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VectorClock:
        """Create from a dict (coercing values to int)."""
        return cls({k: int(v) for k, v in data.items()})

    def __repr__(self) -> str:
        return f"VectorClock({self._clock})"
