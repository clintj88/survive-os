"""Tests for the database engine."""

from shared.db.engine import connect, execute, executemany, executescript, query


def test_connect_memory():
    conn = connect(":memory:")
    assert conn is not None
    row = conn.execute("PRAGMA journal_mode").fetchone()
    # :memory: may report "memory" for WAL
    assert row is not None
    conn.close()


def test_foreign_keys_enabled():
    conn = connect(":memory:")
    row = conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1
    conn.close()


def test_query_returns_dicts():
    conn = connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO t VALUES (1, 'alice')")
    conn.commit()
    rows = query(conn, "SELECT * FROM t")
    assert rows == [{"id": 1, "name": "alice"}]
    conn.close()


def test_execute_returns_lastrowid():
    conn = connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    rowid = execute(conn, "INSERT INTO t (name) VALUES (?)", ("bob",))
    assert rowid == 1
    conn.close()


def test_executemany():
    conn = connect(":memory:")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    executemany(conn, "INSERT INTO t (name) VALUES (?)", [("a",), ("b",), ("c",)])
    rows = query(conn, "SELECT * FROM t")
    assert len(rows) == 3
    conn.close()


def test_executescript():
    conn = connect(":memory:")
    executescript(conn, """
        CREATE TABLE t1 (id INTEGER PRIMARY KEY);
        CREATE TABLE t2 (id INTEGER PRIMARY KEY);
    """)
    rows = query(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    names = [r["name"] for r in rows]
    assert "t1" in names
    assert "t2" in names
    conn.close()


def test_connect_file(tmp_path):
    db_path = str(tmp_path / "sub" / "test.db")
    conn = connect(db_path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    # Reopen
    conn2 = connect(db_path)
    rows = query(conn2, "SELECT name FROM sqlite_master WHERE type='table'")
    assert any(r["name"] == "t" for r in rows)
    conn2.close()
