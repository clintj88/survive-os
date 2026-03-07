"""Tests for backup status tracking."""

from shared.db import connect

from app.status import (
    get_all_last_backups,
    get_backup_history,
    get_drive_status,
    get_last_backup,
    init_status_db,
    record_backup,
)


def _setup():
    conn = connect(":memory:")
    init_status_db(conn)
    return conn


def test_record_and_get_last():
    conn = _setup()
    record_backup(conn, "bbs", "snapshot", "completed", 1024, 2.5, "/backups/bbs.db")
    last = get_last_backup(conn, "bbs")
    assert last is not None
    assert last["module"] == "bbs"
    assert last["size_bytes"] == 1024


def test_no_backup_returns_none():
    conn = _setup()
    assert get_last_backup(conn, "nonexistent") is None


def test_get_all_last_backups():
    conn = _setup()
    record_backup(conn, "bbs", "snapshot", "completed", 100, 1.0)
    record_backup(conn, "medical", "snapshot", "completed", 200, 1.5)
    record_backup(conn, "bbs", "snapshot", "completed", 150, 1.2)  # newer
    results = get_all_last_backups(conn)
    assert len(results) == 2
    bbs = next(r for r in results if r["module"] == "bbs")
    assert bbs["size_bytes"] == 150


def test_get_history():
    conn = _setup()
    record_backup(conn, "bbs", "snapshot", "completed", 100, 1.0)
    record_backup(conn, "bbs", "snapshot", "failed", 0, 0.5)
    history = get_backup_history(conn, module="bbs")
    assert len(history) == 2


def test_drive_status_nonexistent():
    result = get_drive_status("/nonexistent/mount")
    assert result["mounted"] is False
