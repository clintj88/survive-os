"""Tests for backup utilities."""

from shared.db.backup import backup_to_file, restore_from_file
from shared.db.engine import connect, execute, query


def test_backup_and_restore(tmp_path):
    # Create source with data
    source = connect(":memory:")
    source.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    source.commit()
    execute(source, "INSERT INTO t (val) VALUES (?)", ("hello",))

    # Backup
    backup_path = str(tmp_path / "backup.db")
    backup_to_file(source, backup_path)

    # Verify backup has the data
    backup_conn = connect(backup_path)
    rows = query(backup_conn, "SELECT * FROM t")
    assert len(rows) == 1
    assert rows[0]["val"] == "hello"
    backup_conn.close()
    source.close()


def test_restore_into_memory(tmp_path):
    # Create a file DB with data
    file_path = str(tmp_path / "source.db")
    source = connect(file_path)
    source.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    source.commit()
    execute(source, "INSERT INTO t (val) VALUES (?)", ("world",))
    source.close()

    # Restore into a fresh in-memory DB
    dest = connect(":memory:")
    restore_from_file(file_path, dest)
    rows = query(dest, "SELECT * FROM t")
    assert len(rows) == 1
    assert rows[0]["val"] == "world"
    dest.close()
