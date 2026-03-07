"""Tests for database snapshots."""

import os

from shared.db import connect, execute, query

from app.snapshot import snapshot_all_modules, snapshot_database


def test_snapshot_database(tmp_path):
    # Create source DB with data
    src_path = str(tmp_path / "source.db")
    conn = connect(src_path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    execute(conn, "INSERT INTO t (val) VALUES (?)", ("hello",))
    conn.close()

    # Snapshot
    dest_path = str(tmp_path / "snapshot.db")
    meta = snapshot_database(src_path, dest_path)

    assert os.path.exists(dest_path)
    assert meta["size"] > 0
    assert "created_at" in meta

    # Verify data in snapshot
    snap_conn = connect(dest_path)
    rows = query(snap_conn, "SELECT val FROM t")
    assert rows[0]["val"] == "hello"
    snap_conn.close()


def test_snapshot_all_modules(tmp_path):
    # Create two module DBs
    db1 = str(tmp_path / "mod1.db")
    db2 = str(tmp_path / "mod2.db")
    for p in [db1, db2]:
        c = connect(p)
        c.execute("CREATE TABLE t (id INTEGER)")
        c.commit()
        c.close()

    modules = {
        "mod1": {"db_path": db1},
        "mod2": {"db_path": db2},
    }
    backup_dir = str(tmp_path / "backups")
    results = snapshot_all_modules(modules, backup_dir)
    assert len(results) == 2
    assert all(r["module"] in ("mod1", "mod2") for r in results)


def test_snapshot_skips_missing(tmp_path):
    modules = {
        "missing": {"db_path": "/nonexistent/path.db"},
    }
    results = snapshot_all_modules(modules, str(tmp_path / "backups"))
    assert len(results) == 0
