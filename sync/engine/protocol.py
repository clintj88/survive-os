"""Sync protocol message types using dataclasses (Protocol Buffers compatible).

These message types define the sync protocol wire format. They can be
serialized to/from JSON for TCP transport or to compact binary for
radio/serial transport.

A full protobuf .proto file is provided at sync/proto/sync.proto for
production use with grpcio-tools code generation.
"""

from __future__ import annotations

import json
import struct
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class MessageType(IntEnum):
    HANDSHAKE_REQUEST = 1
    HANDSHAKE_RESPONSE = 2
    DOCUMENT_OFFER = 3
    DOCUMENT_REQUEST = 4
    DOCUMENT_DATA = 5
    DOCUMENT_ACK = 6
    PEER_ANNOUNCE = 7
    SYNC_COMPLETE = 8


@dataclass
class SyncMessage:
    """Base sync protocol message."""
    msg_type: MessageType
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "msg_type": int(self.msg_type),
            "msg_id": self.msg_id,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        })

    @classmethod
    def from_json(cls, data: str) -> SyncMessage:
        d = json.loads(data)
        return cls(
            msg_type=MessageType(d["msg_type"]),
            msg_id=d["msg_id"],
            sender_id=d["sender_id"],
            timestamp=d["timestamp"],
            payload=d.get("payload", {}),
        )

    def to_binary(self) -> bytes:
        """Compact binary serialization for radio/serial transport.

        Format: [length:4][type:1][json_payload]
        """
        json_bytes = self.to_json().encode("utf-8")
        header = struct.pack("!IB", len(json_bytes), int(self.msg_type))
        return header + json_bytes

    @classmethod
    def from_binary(cls, data: bytes) -> SyncMessage:
        """Deserialize from compact binary format."""
        _length, _msg_type = struct.unpack("!IB", data[:5])
        json_str = data[5:5 + _length].decode("utf-8")
        return cls.from_json(json_str)


def handshake_request(node_id: str, vector_clocks: dict[str, dict[str, int]]) -> SyncMessage:
    """Create a handshake request advertising our document state."""
    return SyncMessage(
        msg_type=MessageType.HANDSHAKE_REQUEST,
        sender_id=node_id,
        payload={"vector_clocks": vector_clocks},
    )


def handshake_response(
    node_id: str,
    needed_docs: list[str],
    offered_docs: list[str],
) -> SyncMessage:
    """Respond to handshake with lists of needed/offered documents."""
    return SyncMessage(
        msg_type=MessageType.HANDSHAKE_RESPONSE,
        sender_id=node_id,
        payload={"needed_docs": needed_docs, "offered_docs": offered_docs},
    )


def document_data(node_id: str, doc_dict: dict[str, Any]) -> SyncMessage:
    """Send a full document snapshot."""
    return SyncMessage(
        msg_type=MessageType.DOCUMENT_DATA,
        sender_id=node_id,
        payload={"document": doc_dict},
    )


def document_ack(node_id: str, doc_id: str, success: bool) -> SyncMessage:
    """Acknowledge receipt and merge of a document."""
    return SyncMessage(
        msg_type=MessageType.DOCUMENT_ACK,
        sender_id=node_id,
        payload={"doc_id": doc_id, "success": success},
    )


def chunk_message(msg: SyncMessage, chunk_size: int = 256) -> list[bytes]:
    """Split a message into chunks for radio/serial transport."""
    full = msg.to_binary()
    total = (len(full) + chunk_size - 1) // chunk_size
    chunks = []
    for i in range(total):
        start = i * chunk_size
        end = min(start + chunk_size, len(full))
        # Header: [msg_id_hash:4][chunk_idx:2][total:2][data]
        header = struct.pack(
            "!IHH",
            hash(msg.msg_id) & 0xFFFFFFFF,
            i,
            total,
        )
        chunks.append(header + full[start:end])
    return chunks


def reassemble_chunks(chunks: list[bytes]) -> bytes:
    """Reassemble chunked message data."""
    sorted_chunks = sorted(chunks, key=lambda c: struct.unpack("!IHH", c[:8])[1])
    return b"".join(c[8:] for c in sorted_chunks)
