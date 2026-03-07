"""Tests for sync protocol messages."""

from sync.engine.protocol import (
    MessageType,
    SyncMessage,
    chunk_message,
    document_ack,
    document_data,
    handshake_request,
    handshake_response,
    reassemble_chunks,
)


def test_message_json_roundtrip():
    msg = SyncMessage(
        msg_type=MessageType.HANDSHAKE_REQUEST,
        sender_id="node-1",
        payload={"vector_clocks": {"doc-1": {"node-1": 3}}},
    )
    json_str = msg.to_json()
    restored = SyncMessage.from_json(json_str)

    assert restored.msg_type == MessageType.HANDSHAKE_REQUEST
    assert restored.sender_id == "node-1"
    assert restored.payload["vector_clocks"]["doc-1"]["node-1"] == 3


def test_message_binary_roundtrip():
    msg = SyncMessage(
        msg_type=MessageType.DOCUMENT_DATA,
        sender_id="node-2",
        payload={"document": {"doc_id": "abc", "data": {"x": 1}}},
    )
    binary = msg.to_binary()
    restored = SyncMessage.from_binary(binary)

    assert restored.msg_type == MessageType.DOCUMENT_DATA
    assert restored.payload["document"]["doc_id"] == "abc"


def test_handshake_request_factory():
    msg = handshake_request("node-1", {"doc-1": {"node-1": 5}})
    assert msg.msg_type == MessageType.HANDSHAKE_REQUEST
    assert msg.sender_id == "node-1"


def test_handshake_response_factory():
    msg = handshake_response("node-1", ["doc-2"], ["doc-1"])
    assert msg.msg_type == MessageType.HANDSHAKE_RESPONSE
    assert msg.payload["needed_docs"] == ["doc-2"]


def test_document_data_factory():
    msg = document_data("node-1", {"doc_id": "doc-1", "data": {}})
    assert msg.msg_type == MessageType.DOCUMENT_DATA


def test_document_ack_factory():
    msg = document_ack("node-1", "doc-1", True)
    assert msg.msg_type == MessageType.DOCUMENT_ACK
    assert msg.payload["success"] is True


def test_chunking_and_reassembly():
    msg = SyncMessage(
        msg_type=MessageType.DOCUMENT_DATA,
        sender_id="node-1",
        payload={"data": "x" * 500},
    )
    chunks = chunk_message(msg, chunk_size=100)
    assert len(chunks) > 1

    reassembled = reassemble_chunks(chunks)
    restored = SyncMessage.from_binary(reassembled)
    assert restored.payload["data"] == "x" * 500
