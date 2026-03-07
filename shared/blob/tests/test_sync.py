"""Tests for blob sync adapter."""

from shared.blob.store import store_bytes
from shared.blob.sync import (
    BlobRequest,
    ChunkedReceiver,
    build_manifest,
    find_missing,
    read_chunk,
)


def test_build_manifest(tmp_path):
    base = str(tmp_path / "blobs")
    h1 = store_bytes(base, b"one")
    h2 = store_bytes(base, b"two")
    manifest = build_manifest(base, "node-a")
    assert manifest.node_id == "node-a"
    assert set(manifest.hashes) == {h1, h2}


def test_find_missing(tmp_path):
    base_local = str(tmp_path / "local")
    base_remote = str(tmp_path / "remote")
    h1 = store_bytes(base_local, b"shared")
    h2 = store_bytes(base_remote, b"shared")
    h3 = store_bytes(base_remote, b"remote only")

    manifest = build_manifest(base_remote, "remote")
    missing = find_missing(base_local, manifest)
    assert h3 in missing
    assert h1 not in missing


def test_chunked_transfer(tmp_path):
    base_sender = str(tmp_path / "sender")
    base_receiver = str(tmp_path / "receiver")
    data = b"x" * 1000
    h = store_bytes(base_sender, data)

    # Transfer in 256-byte chunks
    chunk_size = 256
    receiver = None
    offset = 0
    while True:
        req = BlobRequest(blob_hash=h, offset=offset, chunk_size=chunk_size)
        chunk = read_chunk(base_sender, req)
        assert chunk is not None
        if receiver is None:
            receiver = ChunkedReceiver(h, chunk.total_size)
        done = receiver.receive_chunk(chunk)
        if done:
            break
        offset += chunk_size

    assert receiver.finalize(base_receiver)
    from shared.blob.store import read_bytes
    assert read_bytes(base_receiver, h) == data


def test_read_chunk_missing(tmp_path):
    base = str(tmp_path / "blobs")
    req = BlobRequest(blob_hash="nonexistent")
    assert read_chunk(base, req) is None
