"""Tests for schema versioning and migrations."""

from shared.db.engine import connect, query
from shared.db.schema import SchemaManager


def _make_manager():
    conn = connect(":memory:")
    sm = SchemaManager(conn, module="test")
    sm.add_migration(
        version=1,
        description="create items",
        up=lambda c: c.executescript("CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT)"),
        down=lambda c: c.executescript("DROP TABLE items"),
    )
    sm.add_migration(
        version=2,
        description="add price column",
        up=lambda c: c.executescript("ALTER TABLE items ADD COLUMN price REAL DEFAULT 0"),
        down=lambda c: c.executescript(
            "CREATE TABLE items_backup AS SELECT id, name FROM items;"
            "DROP TABLE items;"
            "ALTER TABLE items_backup RENAME TO items;"
        ),
    )
    return conn, sm


def test_initial_version_is_zero():
    conn = connect(":memory:")
    sm = SchemaManager(conn, module="test")
    assert sm.current_version() == 0
    conn.close()


def test_migrate_up_all():
    conn, sm = _make_manager()
    applied = sm.migrate_up()
    assert applied == [1, 2]
    assert sm.current_version() == 2
    # Verify table exists with price column
    conn.execute("INSERT INTO items VALUES ('a', 'apple', 1.50)")
    conn.commit()
    rows = query(conn, "SELECT * FROM items")
    assert rows[0]["price"] == 1.50
    conn.close()


def test_migrate_up_to_target():
    conn, sm = _make_manager()
    applied = sm.migrate_up(target_version=1)
    assert applied == [1]
    assert sm.current_version() == 1
    conn.close()


def test_migrate_down():
    conn, sm = _make_manager()
    sm.migrate_up()
    rolled = sm.migrate_down(target_version=0)
    assert rolled == [2, 1]
    assert sm.current_version() == 0
    conn.close()


def test_migrate_down_partial():
    conn, sm = _make_manager()
    sm.migrate_up()
    rolled = sm.migrate_down(target_version=1)
    assert rolled == [2]
    assert sm.current_version() == 1
    conn.close()


def test_pending_migrations():
    conn, sm = _make_manager()
    pending = sm.pending_migrations()
    assert len(pending) == 2
    sm.migrate_up(target_version=1)
    pending = sm.pending_migrations()
    assert len(pending) == 1
    assert pending[0].version == 2
    conn.close()


def test_idempotent_migrate_up():
    conn, sm = _make_manager()
    sm.migrate_up()
    applied = sm.migrate_up()
    assert applied == []
    conn.close()
