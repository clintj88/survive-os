"""Tests for blob sync adapter."""

import pytest

from shared.blob.store import hash_content, store_bytes
from shared.blob.sync import (
    BlobChunk,
    BlobManifest,
    BlobRequest,
    ChunkedReceiver,
    build_manifest,
    find_missing,
    read_chunk,
)


@pytest.fixture
def blob_dir(tmp_path):
    return str(tmp_path / "blobs")


@pytest.fixture
def remote_dir(tmp_path):
    return str(tmp_path / "remote")


class TestManifest:
    def test_build_manifest(self, blob_dir):
        h1 = store_bytes(blob_dir, b"one")
        h2 = store_bytes(blob_dir, b"two")
        manifest = build_manifest(blob_dir, "node-a")
        assert manifest.node_id == "node-a"
        assert set(manifest.hashes) == {h1, h2}

    def test_find_missing(self, blob_dir, remote_dir):
        h1 = store_bytes(remote_dir, b"remote only")
        h2 = store_bytes(blob_dir, b"local too")
        store_bytes(remote_dir, b"local too")
        manifest = build_manifest(remote_dir, "remote-node")
        missing = find_missing(blob_dir, manifest)
        assert h1 in missing
        assert h2 not in missing


class TestChunkedTransfer:
    def test_read_chunk(self, blob_dir):
        data = b"chunk test data"
        h = store_bytes(blob_dir, data)
        req = BlobRequest(blob_hash=h, offset=0, chunk_size=5)
        chunk = read_chunk(blob_dir, req)
        assert chunk is not None
        assert chunk.data == data[:5]
        assert chunk.offset == 0
        assert chunk.total_size == len(data)
        assert chunk.is_last is False

    def test_read_chunk_last(self, blob_dir):
        data = b"short"
        h = store_bytes(blob_dir, data)
        req = BlobRequest(blob_hash=h, offset=0, chunk_size=1024)
        chunk = read_chunk(blob_dir, req)
        assert chunk is not None
        assert chunk.data == data
        assert chunk.is_last is True

    def test_read_chunk_missing(self, blob_dir):
        req = BlobRequest(blob_hash="missing" * 9, offset=0)
        assert read_chunk(blob_dir, req) is None

    def test_chunked_receiver(self, blob_dir):
        data = b"reassemble me please"
        h = hash_content(data)
        receiver = ChunkedReceiver(h, len(data))
        done = receiver.receive_chunk(BlobChunk(
            blob_hash=h, offset=0, data=data[:10],
            total_size=len(data), is_last=False,
        ))
        assert done is False
        done = receiver.receive_chunk(BlobChunk(
            blob_hash=h, offset=10, data=data[10:],
            total_size=len(data), is_last=True,
        ))
        assert done is True
        assert receiver.finalize(blob_dir) is True
        from shared.blob.store import read_bytes
        assert read_bytes(blob_dir, h) == data

    def test_chunked_receiver_bad_hash(self, blob_dir):
        data = b"tampered"
        receiver = ChunkedReceiver("wrong" * 12, len(data))
        receiver.receive_chunk(BlobChunk(
            blob_hash="wrong" * 12, offset=0, data=data,
            total_size=len(data), is_last=True,
        ))
        assert receiver.finalize(blob_dir) is False
