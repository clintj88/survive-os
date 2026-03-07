"""Tests for content-addressed blob storage."""

import io
import os

import pytest

from shared.blob.store import (
    delete_blob,
    exists,
    get_metadata,
    hash_content,
    hash_stream,
    list_blobs,
    read_bytes,
    read_stream,
    store_bytes,
    store_stream,
)


@pytest.fixture
def blob_dir(tmp_path):
    return str(tmp_path / "blobs")


class TestHashFunctions:
    def test_hash_content(self):
        h = hash_content(b"hello world")
        assert len(h) == 64
        assert h == hash_content(b"hello world")

    def test_hash_content_different(self):
        assert hash_content(b"a") != hash_content(b"b")

    def test_hash_stream(self):
        stream = io.BytesIO(b"hello world")
        h = hash_stream(stream)
        assert h == hash_content(b"hello world")


class TestStoreBytes:
    def test_store_and_read(self, blob_dir):
        data = b"test content"
        h = store_bytes(blob_dir, data, filename="test.txt", mime_type="text/plain")
        assert exists(blob_dir, h)
        assert read_bytes(blob_dir, h) == data

    def test_deduplication(self, blob_dir):
        data = b"duplicate content"
        h1 = store_bytes(blob_dir, data)
        h2 = store_bytes(blob_dir, data)
        assert h1 == h2

    def test_metadata(self, blob_dir):
        data = b"meta test"
        h = store_bytes(blob_dir, data, filename="doc.pdf", mime_type="application/pdf")
        meta = get_metadata(blob_dir, h)
        assert meta is not None
        assert meta["filename"] == "doc.pdf"
        assert meta["mime_type"] == "application/pdf"
        assert meta["size"] == len(data)
        assert meta["hash"] == h
        assert "created_at" in meta

    def test_storage_layout(self, blob_dir):
        data = b"layout test"
        h = store_bytes(blob_dir, data)
        expected = os.path.join(blob_dir, h[:2], h[2:4], h)
        assert os.path.exists(expected)

    def test_read_missing_raises(self, blob_dir):
        with pytest.raises(FileNotFoundError):
            read_bytes(blob_dir, "nonexistent" * 4)


class TestStoreStream:
    def test_store_stream(self, blob_dir):
        data = b"streamed content"
        stream = io.BytesIO(data)
        h = store_stream(blob_dir, stream, filename="stream.bin")
        assert exists(blob_dir, h)
        assert read_bytes(blob_dir, h) == data
        assert h == hash_content(data)

    def test_stream_deduplication(self, blob_dir):
        data = b"stream dedup"
        store_bytes(blob_dir, data)
        h = store_stream(blob_dir, io.BytesIO(data))
        assert h == hash_content(data)


class TestReadStream:
    def test_read_stream(self, blob_dir):
        data = b"streaming read"
        h = store_bytes(blob_dir, data)
        with read_stream(blob_dir, h) as f:
            assert f.read() == data


class TestDeleteBlob:
    def test_delete(self, blob_dir):
        h = store_bytes(blob_dir, b"delete me")
        assert delete_blob(blob_dir, h) is True
        assert not exists(blob_dir, h)
        assert get_metadata(blob_dir, h) is None

    def test_delete_missing(self, blob_dir):
        assert delete_blob(blob_dir, "abc" * 20) is False


class TestListBlobs:
    def test_list_empty(self, blob_dir):
        assert list_blobs(blob_dir) == []

    def test_list_multiple(self, blob_dir):
        h1 = store_bytes(blob_dir, b"one")
        h2 = store_bytes(blob_dir, b"two")
        h3 = store_bytes(blob_dir, b"three")
        found = list_blobs(blob_dir)
        assert set(found) == {h1, h2, h3}


class TestAtomicWrite:
    def test_no_partial_files_on_success(self, blob_dir):
        store_bytes(blob_dir, b"atomic test")
        for root, dirs, files in os.walk(blob_dir):
            for f in files:
                assert not f.startswith("tmp")
