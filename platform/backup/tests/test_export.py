"""Tests for backup export and archive creation."""

import os

from shared.db import connect, execute

from app.export import create_archive, read_manifest
from app.snapshot import snapshot_database


def _create_test_snapshot(tmp_path):
    """Helper to create a source DB and snapshot it."""
    src = str(tmp_path / "source.db")
    conn = connect(src)
    conn.execute("CREATE TABLE t (val TEXT)")
    conn.commit()
    execute(conn, "INSERT INTO t VALUES (?)", ("test",))
    conn.close()

    snap_dir = str(tmp_path / "snapshots" / "testmod")
    os.makedirs(snap_dir, exist_ok=True)
    snapshot_database(src, os.path.join(snap_dir, "testmod-snap.db"))
    return str(tmp_path / "snapshots")


def test_create_unencrypted_archive(tmp_path):
    snap_dir = _create_test_snapshot(tmp_path)
    output = str(tmp_path / "backup.tar.gz")
    result = create_archive(snap_dir, None, output)
    assert os.path.exists(output)
    assert result["encrypted"] is False
    assert result["entries"] > 0


def test_create_encrypted_archive(tmp_path):
    snap_dir = _create_test_snapshot(tmp_path)
    output = str(tmp_path / "backup.enc")
    result = create_archive(snap_dir, None, output, passphrase="secret")
    assert os.path.exists(output)
    assert result["encrypted"] is True


def test_read_manifest_unencrypted(tmp_path):
    snap_dir = _create_test_snapshot(tmp_path)
    output = str(tmp_path / "backup.tar.gz")
    create_archive(snap_dir, None, output)
    manifest = read_manifest(output)
    assert manifest["version"] == "1.0"
    assert len(manifest["entries"]) > 0


def test_read_manifest_encrypted(tmp_path):
    snap_dir = _create_test_snapshot(tmp_path)
    output = str(tmp_path / "backup.enc")
    create_archive(snap_dir, None, output, passphrase="test-key")
    manifest = read_manifest(output, passphrase="test-key")
    assert manifest["version"] == "1.0"


def test_archive_with_blobs(tmp_path):
    snap_dir = _create_test_snapshot(tmp_path)
    blob_dir = str(tmp_path / "blobs")
    from shared.blob.store import store_bytes
    store_bytes(blob_dir, b"blob data", filename="test.bin")

    output = str(tmp_path / "full-backup.tar.gz")
    result = create_archive(snap_dir, blob_dir, output)
    assert result["entries"] >= 2  # at least 1 db + 1 blob + meta
