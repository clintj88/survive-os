"""Tests for backup restore."""

import os

from shared.db import connect, execute

from app.export import create_archive
from app.restore import restore_full, restore_module, verify_archive
from app.snapshot import snapshot_database


def _setup_archive(tmp_path, passphrase=""):
    src = str(tmp_path / "source.db")
    conn = connect(src)
    conn.execute("CREATE TABLE t (val TEXT)")
    conn.commit()
    execute(conn, "INSERT INTO t VALUES (?)", ("data",))
    conn.close()

    snap_dir = str(tmp_path / "snapshots" / "mymod")
    os.makedirs(snap_dir, exist_ok=True)
    snapshot_database(src, os.path.join(snap_dir, "mymod-snap.db"))

    output = str(tmp_path / "archive.enc" if passphrase else tmp_path / "archive.tar.gz")
    create_archive(str(tmp_path / "snapshots"), None, output, passphrase=passphrase)
    return output


def test_verify_valid_archive(tmp_path):
    archive = _setup_archive(tmp_path)
    result = verify_archive(archive)
    assert result["valid"] is True
    assert result["errors"] == []


def test_verify_encrypted_archive(tmp_path):
    archive = _setup_archive(tmp_path, passphrase="key123")
    result = verify_archive(archive, passphrase="key123")
    assert result["valid"] is True


def test_verify_wrong_passphrase(tmp_path):
    archive = _setup_archive(tmp_path, passphrase="correct")
    result = verify_archive(archive, passphrase="wrong")
    assert result["valid"] is False


def test_restore_full(tmp_path):
    archive = _setup_archive(tmp_path)
    restore_dir = str(tmp_path / "restored")
    result = restore_full(archive, restore_dir)
    assert result["files_restored"] > 0
    assert os.path.isdir(restore_dir)


def test_restore_module(tmp_path):
    archive = _setup_archive(tmp_path)
    restore_dir = str(tmp_path / "restored")
    result = restore_module(archive, "mymod", restore_dir)
    assert result["files_restored"] > 0
    assert result["module"] == "mymod"


def test_restore_module_not_in_archive(tmp_path):
    archive = _setup_archive(tmp_path)
    restore_dir = str(tmp_path / "restored")
    result = restore_module(archive, "nonexistent", restore_dir)
    assert result["files_restored"] == 0
