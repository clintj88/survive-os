"""Tests for blob store."""

import io

from shared.blob.store import (
    delete_blob,
    exists,
    get_metadata,
    hash_content,
    list_blobs,
    read_bytes,
    read_stream,
    store_bytes,
    store_stream,
)


def test_store_and_read_bytes(tmp_path):
    base = str(tmp_path / "blobs")
    data = b"hello world"
    h = store_bytes(base, data, filename="hello.txt", mime_type="text/plain")
    assert len(h) == 64  # SHA-256 hex
    assert exists(base, h)
    assert read_bytes(base, h) == data


def test_deduplication(tmp_path):
    base = str(tmp_path / "blobs")
    data = b"duplicate content"
    h1 = store_bytes(base, data)
    h2 = store_bytes(base, data)
    assert h1 == h2
    assert len(list_blobs(base)) == 1


def test_store_stream(tmp_path):
    base = str(tmp_path / "blobs")
    data = b"streamed content" * 1000
    stream = io.BytesIO(data)
    h = store_stream(base, stream, filename="big.bin")
    assert exists(base, h)
    assert read_bytes(base, h) == data


def test_read_stream(tmp_path):
    base = str(tmp_path / "blobs")
    data = b"stream read test"
    h = store_bytes(base, data)
    f = read_stream(base, h)
    try:
        assert f.read() == data
    finally:
        f.close()


def test_metadata(tmp_path):
    base = str(tmp_path / "blobs")
    data = b"meta test"
    h = store_bytes(base, data, filename="doc.pdf", mime_type="application/pdf")
    meta = get_metadata(base, h)
    assert meta is not None
    assert meta["filename"] == "doc.pdf"
    assert meta["mime_type"] == "application/pdf"
    assert meta["size"] == len(data)
    assert meta["hash"] == h


def test_delete_blob(tmp_path):
    base = str(tmp_path / "blobs")
    h = store_bytes(base, b"to delete")
    assert exists(base, h)
    assert delete_blob(base, h)
    assert not exists(base, h)


def test_delete_nonexistent(tmp_path):
    base = str(tmp_path / "blobs")
    assert not delete_blob(base, "nonexistent")


def test_list_blobs(tmp_path):
    base = str(tmp_path / "blobs")
    h1 = store_bytes(base, b"one")
    h2 = store_bytes(base, b"two")
    h3 = store_bytes(base, b"three")
    blobs = list_blobs(base)
    assert set(blobs) == {h1, h2, h3}


def test_hash_content():
    h = hash_content(b"test")
    assert len(h) == 64
    assert h == hash_content(b"test")  # deterministic
    assert h != hash_content(b"other")
